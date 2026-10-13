from unittest.mock import MagicMock

import pytest
import requests

from app.services import rag_service
from app.services.retrieval_service import RetrievedChunk
from tests.conftest import auth_headers


CHUNKS = [
    RetrievedChunk(1, 10, 0, "El horario es de 8 a 17 horas.", 0.20, 0.20),
    RetrievedChunk(2, 10, 1, "Contacto: soporte@omnicortex.dev", 0.30, 0.30),
    RetrievedChunk(3, 10, 2, "Texto irrelevante.", 0.50, 0.50),
]


@pytest.fixture
def retrieval(monkeypatch):
    # Vector search needs pgvector; return fixed candidates instead.
    mock = MagicMock(return_value=CHUNKS)
    monkeypatch.setattr(rag_service, "search_relevant_chunks", mock)

    return mock


@pytest.fixture
def ollama(monkeypatch):
    response = MagicMock()
    response.json.return_value = {
        "response": "El correo es soporte@omnicortex.dev",
        "model": "qwen2.5:3b",
        "done_reason": "stop",
        "eval_count": 10,
        "eval_duration": 1_000_000_000,
    }

    mock = MagicMock(return_value=response)
    monkeypatch.setattr("app.ai.llm.client.requests.post", mock)

    return mock


def test_ask_returns_answer_and_sources(client, create_user, retrieval, ollama):
    user = create_user("alice")

    response = client.post(
        "/documents/ask",
        json={"question": "¿Cuál es el correo de contacto?", "limit": 2},
        headers=auth_headers(user)
    )

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "El correo es soporte@omnicortex.dev"

    # The reranker promotes the chunk with the email to first place.
    assert [source["chunk_id"] for source in body["sources"]] == [2, 1]

    retrieval.assert_called_once()
    assert retrieval.call_args.kwargs["user_id"] == user.id
    assert retrieval.call_args.kwargs["limit"] == 6

    prompt = ollama.call_args.kwargs["json"]["prompt"]
    assert "soporte@omnicortex.dev" in prompt
    assert "¿Cuál es el correo de contacto?" in prompt
    assert "Texto irrelevante." not in prompt


@pytest.mark.parametrize(
    "error",
    [requests.ConnectionError(), requests.Timeout(), requests.HTTPError()]
)
def test_ask_returns_503_when_ollama_fails(client, create_user, retrieval, monkeypatch, error):
    monkeypatch.setattr(
        "app.ai.llm.client.requests.post",
        MagicMock(side_effect=error)
    )
    user = create_user("alice")

    response = client.post(
        "/documents/ask",
        json={"question": "hola"},
        headers=auth_headers(user)
    )

    assert response.status_code == 503
    assert "Ollama" in response.json()["detail"]


def test_ask_requires_authentication(client):
    assert client.post("/documents/ask", json={"question": "hola"}).status_code == 401
