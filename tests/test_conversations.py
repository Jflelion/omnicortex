from unittest.mock import MagicMock

import pytest
import requests

from app.core.config import settings
from app.models.conversation import Conversation, Message
from app.services import rag_service
from app.services.retrieval_service import RetrievedChunk
from tests.conftest import auth_headers


CHUNKS = [
    RetrievedChunk(1, 10, 0, "La gerente es Ana Pérez.", 0.20, 0.20, "equipo.pdf"),
    RetrievedChunk(2, 10, 1, "Teléfono de Ana: 555-0101.", 0.30, 0.30, "equipo.pdf"),
]


@pytest.fixture
def retrieval(monkeypatch):
    mock = MagicMock(return_value=CHUNKS)
    monkeypatch.setattr(rag_service, "search_relevant_chunks", mock)

    return mock


@pytest.fixture
def ollama(monkeypatch):
    answers = iter(["Ana Pérez.", "555-0101.", "Tercera.", "Cuarta."])

    def _post(*_args, **_kwargs):
        response = MagicMock()
        response.json.return_value = {
            "response": next(answers),
            "model": "qwen2.5:3b",
            "done_reason": "stop",
            "eval_count": 10,
            "eval_duration": 1_000_000_000,
        }
        return response

    mock = MagicMock(side_effect=_post)
    monkeypatch.setattr("app.ai.llm.client.requests.post", mock)

    return mock


def create_conversation(client, headers, **body):
    return client.post("/conversations/", json=body, headers=headers)


def send(client, headers, conversation_id, question):
    return client.post(
        f"/conversations/{conversation_id}/messages",
        json={"question": question},
        headers=headers
    )


def test_create_and_list_conversations(client, create_user):
    headers = auth_headers(create_user("alice"))

    first = create_conversation(client, headers).json()
    second = create_conversation(client, headers, title="Contratos").json()

    assert first["title"] == "Nueva conversación"
    assert second["title"] == "Contratos"

    listed = client.get("/conversations/", headers=headers).json()
    assert [conversation["id"] for conversation in listed] == [second["id"], first["id"]]


def test_send_message_stores_question_answer_and_sources(
    client, db, create_user, retrieval, ollama
):
    headers = auth_headers(create_user("alice"))
    conversation_id = create_conversation(client, headers).json()["id"]

    response = send(client, headers, conversation_id, "¿Quién es la gerente?")

    assert response.status_code == 201
    turn = response.json()
    assert turn["user_message"]["role"] == "user"
    assert turn["user_message"]["content"] == "¿Quién es la gerente?"
    assert turn["assistant_message"]["role"] == "assistant"
    assert turn["assistant_message"]["content"] == "Ana Pérez."
    assert turn["assistant_message"]["sources"][0]["filename"] == "equipo.pdf"

    # The first question becomes the title.
    assert turn["conversation"]["title"] == "¿Quién es la gerente?"

    detail = client.get(f"/conversations/{conversation_id}", headers=headers).json()
    assert [message["role"] for message in detail["messages"]] == ["user", "assistant"]
    assert len(detail["messages"][1]["sources"]) == 2


def test_follow_up_uses_conversation_history(client, create_user, retrieval, ollama):
    headers = auth_headers(create_user("alice"))
    conversation_id = create_conversation(client, headers).json()["id"]

    send(client, headers, conversation_id, "¿Quién es la gerente?")
    send(client, headers, conversation_id, "¿Y su teléfono?")

    # The retrieval query carries the previous question for context.
    query = retrieval.call_args.kwargs["query"]
    assert "¿Quién es la gerente?" in query
    assert "¿Y su teléfono?" in query

    prompt = ollama.call_args.kwargs["json"]["prompt"]
    assert "HISTORIAL DE LA CONVERSACIÓN" in prompt
    assert "Usuario: ¿Quién es la gerente?" in prompt
    assert "Asistente: Ana Pérez." in prompt
    assert prompt.index("HISTORIAL") < prompt.index("PREGUNTA:\n¿Y su teléfono?")


def test_history_is_limited_to_recent_messages(
    client, create_user, retrieval, ollama, monkeypatch
):
    monkeypatch.setattr(settings, "CONVERSATION_HISTORY_MESSAGES", 2)
    headers = auth_headers(create_user("alice"))
    conversation_id = create_conversation(client, headers).json()["id"]

    send(client, headers, conversation_id, "primera pregunta")
    send(client, headers, conversation_id, "segunda pregunta")
    send(client, headers, conversation_id, "tercera pregunta")

    prompt = ollama.call_args.kwargs["json"]["prompt"]
    assert "primera pregunta" not in prompt
    assert "Usuario: segunda pregunta" in prompt


def test_first_question_does_not_override_custom_title(client, create_user, retrieval, ollama):
    headers = auth_headers(create_user("alice"))
    conversation_id = create_conversation(client, headers, title="Contratos").json()["id"]

    turn = send(client, headers, conversation_id, "¿Quién es la gerente?").json()

    assert turn["conversation"]["title"] == "Contratos"


def test_long_question_title_is_truncated(client, create_user, retrieval, ollama):
    headers = auth_headers(create_user("alice"))
    conversation_id = create_conversation(client, headers).json()["id"]

    turn = send(client, headers, conversation_id, "palabra " * 30).json()

    assert len(turn["conversation"]["title"]) <= 61
    assert turn["conversation"]["title"].endswith("…")


def test_failed_answer_does_not_store_messages(
    client, db, create_user, retrieval, monkeypatch
):
    monkeypatch.setattr(
        "app.ai.llm.client.requests.post",
        MagicMock(side_effect=requests.ConnectionError())
    )
    headers = auth_headers(create_user("alice"))
    conversation_id = create_conversation(client, headers).json()["id"]

    response = send(client, headers, conversation_id, "hola")

    assert response.status_code == 503
    assert db.query(Message).count() == 0


def test_rename_and_delete_conversation(client, db, create_user, retrieval, ollama):
    headers = auth_headers(create_user("alice"))
    conversation_id = create_conversation(client, headers).json()["id"]
    send(client, headers, conversation_id, "hola")

    renamed = client.patch(
        f"/conversations/{conversation_id}",
        json={"title": "Renombrada"},
        headers=headers
    )
    assert renamed.json()["title"] == "Renombrada"

    assert client.delete(f"/conversations/{conversation_id}", headers=headers).status_code == 204
    db.expire_all()
    assert db.query(Conversation).count() == 0
    assert db.query(Message).count() == 0


def test_cannot_access_other_users_conversations(client, create_user, retrieval, ollama):
    owner_headers = auth_headers(create_user("alice"))
    intruder_headers = auth_headers(create_user("mallory"))
    conversation_id = create_conversation(client, owner_headers).json()["id"]

    assert client.get(f"/conversations/{conversation_id}", headers=intruder_headers).status_code == 404
    assert send(client, intruder_headers, conversation_id, "hola").status_code == 404
    assert client.delete(f"/conversations/{conversation_id}", headers=intruder_headers).status_code == 404
    assert client.get("/conversations/", headers=intruder_headers).json() == []


def test_empty_question_is_rejected(client, create_user):
    headers = auth_headers(create_user("alice"))
    conversation_id = create_conversation(client, headers).json()["id"]

    assert send(client, headers, conversation_id, "").status_code == 422


def test_conversations_require_authentication(client):
    assert client.get("/conversations/").status_code == 401
