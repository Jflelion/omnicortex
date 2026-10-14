from types import SimpleNamespace
from unittest.mock import MagicMock

import anthropic
import httpx2
import pytest
from pydantic import ValidationError

from app.ai.llm.anthropic_client import REFUSAL_TEXT, AnthropicClient
from app.core.config import Settings, settings
from app.core.exceptions import AIServiceUnavailableError
from app.services import embedding_service
from app.services.embedding_service import (
    NOMIC_BATCH_SIZE,
    generate_document_embeddings,
    generate_embedding,
)


def claude_message(*texts: str, stop_reason: str = "end_turn") -> SimpleNamespace:
    return SimpleNamespace(
        content=[SimpleNamespace(type="thinking", thinking="")]
        + [SimpleNamespace(type="text", text=text) for text in texts],
        model="claude-haiku-5-5",
        stop_reason=stop_reason,
        usage=SimpleNamespace(input_tokens=120, output_tokens=15),
    )


@pytest.fixture
def claude(monkeypatch):
    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "test-key")
    client = AnthropicClient()
    create = MagicMock()
    monkeypatch.setattr(client._client.messages, "create", create)

    return client, create


def test_anthropic_client_returns_text_and_usage(claude):
    client, create = claude
    create.return_value = claude_message("Laura ", "Gomez")

    response = client.generate("PREGUNTA")

    assert response.text == "Laura Gomez"
    assert response.prompt_eval_count == 120
    assert response.eval_count == 15

    kwargs = create.call_args.kwargs
    assert kwargs["model"] == settings.ANTHROPIC_MODEL
    assert kwargs["output_config"] == {"effort": settings.ANTHROPIC_EFFORT}
    assert kwargs["messages"] == [{"role": "user", "content": "PREGUNTA"}]


def test_anthropic_refusal_returns_fixed_text(claude):
    client, create = claude
    create.return_value = claude_message("parcial", stop_reason="refusal")

    assert client.generate("x").text == REFUSAL_TEXT


def test_anthropic_connection_error_becomes_unavailable(claude):
    client, create = claude
    create.side_effect = anthropic.APIConnectionError(
        request=httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    )

    with pytest.raises(AIServiceUnavailableError):
        client.generate("x")


@pytest.fixture
def nomic(monkeypatch):
    monkeypatch.setattr(settings, "EMBEDDING_PROVIDER", "nomic")
    monkeypatch.setattr(settings, "NOMIC_API_KEY", "nk-test")

    def _post(url, headers, json, timeout):
        response = MagicMock()
        response.json.return_value = {
            "embeddings": [[float(i)] * 768 for i, _ in enumerate(json["texts"])]
        }
        return response

    post = MagicMock(side_effect=_post)
    monkeypatch.setattr(embedding_service.requests, "post", post)

    return post


def test_nomic_query_embedding_uses_search_query(nomic):
    assert len(generate_embedding("hola")) == 768

    body = nomic.call_args.kwargs["json"]
    assert body["task_type"] == "search_query"
    assert body["dimensionality"] == 768
    assert nomic.call_args.kwargs["headers"] == {"Authorization": "Bearer nk-test"}


def test_nomic_document_embeddings_are_batched_in_order(nomic):
    texts = [f"chunk {i}" for i in range(NOMIC_BATCH_SIZE + 3)]

    embeddings = generate_document_embeddings(texts)

    assert len(embeddings) == len(texts)
    assert nomic.call_count == 2
    assert all(call.kwargs["json"]["task_type"] == "search_document" for call in nomic.call_args_list)
    # Second batch restarts its index: order within each batch is preserved.
    assert embeddings[NOMIC_BATCH_SIZE][0] == 0.0
    assert embeddings[NOMIC_BATCH_SIZE + 2][0] == 2.0


def test_nomic_errors_become_unavailable(nomic):
    import requests

    nomic.side_effect = requests.ConnectionError()

    with pytest.raises(AIServiceUnavailableError):
        generate_embedding("hola")


@pytest.mark.parametrize(
    ("overrides", "missing"),
    [
        ({"LLM_PROVIDER": "anthropic"}, "ANTHROPIC_API_KEY"),
        ({"EMBEDDING_PROVIDER": "nomic"}, "NOMIC_API_KEY"),
    ],
)
def test_hosted_providers_require_api_keys(overrides, missing):
    with pytest.raises(ValidationError, match=missing):
        Settings(_env_file=None, DATABASE_URL="sqlite://", SECRET_KEY="x", **overrides)


def test_health_skips_ollama_when_demo_providers_are_used(client, monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "anthropic")
    monkeypatch.setattr(settings, "EMBEDDING_PROVIDER", "nomic")
    get = MagicMock()
    monkeypatch.setattr("app.routers.health.requests.get", get)

    response = client.get("/health")

    assert response.status_code == 200
    assert set(response.json()["checks"]) == {"database", "anthropic", "nomic"}
    get.assert_not_called()
