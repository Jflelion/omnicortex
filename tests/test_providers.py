from unittest.mock import MagicMock

import pytest
import requests
from pydantic import ValidationError

from app.ai.llm import gemini_client
from app.ai.llm.gemini_client import BLOCKED_TEXT, GeminiClient
from app.core.config import Settings, settings
from app.core.exceptions import AIServiceUnavailableError
from app.services import embedding_service
from app.services.embedding_service import (
    GEMINI_BATCH_SIZE,
    GEMINI_DOCUMENT_PREFIX,
    GEMINI_QUERY_PREFIX,
    generate_document_embeddings,
    generate_embedding,
)


def gemini_reply(*texts: str, finish_reason: str = "STOP") -> dict:
    return {
        "candidates": [{
            "content": {"parts": [{"text": text} for text in texts]},
            "finishReason": finish_reason,
        }],
        "usageMetadata": {"promptTokenCount": 120, "candidatesTokenCount": 15},
        "modelVersion": "gemini-3.1-flash-lite",
    }


@pytest.fixture
def gemini_llm(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "g-test")
    post = MagicMock()
    monkeypatch.setattr(gemini_client.requests, "post", post)

    def _reply(payload: dict) -> None:
        post.return_value = MagicMock(json=MagicMock(return_value=payload))

    return GeminiClient(), post, _reply


def test_gemini_llm_returns_text_and_usage(gemini_llm):
    client, post, reply = gemini_llm
    reply(gemini_reply("Laura ", "Gomez"))

    response = client.generate("PREGUNTA")

    assert response.text == "Laura Gomez"
    assert response.prompt_eval_count == 120
    assert response.eval_count == 15

    assert post.call_args.args[0].endswith(f"/models/{settings.GEMINI_LLM_MODEL}:generateContent")
    assert post.call_args.kwargs["headers"] == {"x-goog-api-key": "g-test"}
    body = post.call_args.kwargs["json"]
    assert body["contents"][0]["parts"][0]["text"] == "PREGUNTA"
    assert body["generationConfig"]["maxOutputTokens"] == settings.GEMINI_MAX_TOKENS


def test_gemini_llm_ignores_thought_parts(gemini_llm):
    client, _, reply = gemini_llm
    payload = gemini_reply("Laura Gomez")
    payload["candidates"][0]["content"]["parts"].insert(
        0, {"text": "razonamiento interno", "thought": True}
    )
    reply(payload)

    assert client.generate("x").text == "Laura Gomez"


def test_gemini_llm_blocked_prompt_returns_fixed_text(gemini_llm):
    client, _, reply = gemini_llm
    reply({"promptFeedback": {"blockReason": "SAFETY"}})

    response = client.generate("x")

    assert response.text == BLOCKED_TEXT
    assert response.done_reason == "SAFETY"


@pytest.mark.parametrize("error", [requests.ConnectionError(), requests.Timeout(), requests.HTTPError()])
def test_gemini_llm_errors_become_unavailable(gemini_llm, error):
    client, post, _ = gemini_llm
    post.side_effect = error

    with pytest.raises(AIServiceUnavailableError):
        client.generate("x")


@pytest.fixture
def gemini(monkeypatch):
    monkeypatch.setattr(settings, "EMBEDDING_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "g-test")

    def _post(url, headers, json, timeout):
        response = MagicMock()
        response.json.return_value = {
            "embeddings": [{"values": [float(i)] * 768} for i, _ in enumerate(json["requests"])]
        }
        return response

    post = MagicMock(side_effect=_post)
    monkeypatch.setattr(embedding_service.requests, "post", post)

    return post


def sent_texts(call) -> list[str]:
    return [request["content"]["parts"][0]["text"] for request in call.kwargs["json"]["requests"]]


def test_gemini_query_embedding_uses_query_prefix(gemini):
    assert len(generate_embedding("hola")) == 768

    call = gemini.call_args
    assert call.args[0].endswith("/models/gemini-embedding-2:batchEmbedContents")
    assert call.kwargs["headers"] == {"x-goog-api-key": "g-test"}
    assert sent_texts(call) == [GEMINI_QUERY_PREFIX + "hola"]
    assert call.kwargs["json"]["requests"][0]["outputDimensionality"] == 768


def test_gemini_document_embeddings_are_batched_in_order(gemini):
    texts = [f"chunk {i}" for i in range(GEMINI_BATCH_SIZE + 3)]

    embeddings = generate_document_embeddings(texts)

    assert len(embeddings) == len(texts)
    assert gemini.call_count == 2
    assert sent_texts(gemini.call_args_list[1]) == [
        GEMINI_DOCUMENT_PREFIX + text for text in texts[GEMINI_BATCH_SIZE:]
    ]
    # Second batch restarts its index: order within each batch is preserved.
    assert embeddings[GEMINI_BATCH_SIZE][0] == 0.0
    assert embeddings[GEMINI_BATCH_SIZE + 2][0] == 2.0


def test_gemini_wrong_dimensions_are_rejected(gemini):
    response = MagicMock()
    response.json.return_value = {"embeddings": [{"values": [0.1] * 3072}]}
    gemini.side_effect = None
    gemini.return_value = response

    with pytest.raises(AIServiceUnavailableError):
        generate_embedding("hola")


def test_gemini_errors_become_unavailable(gemini):
    gemini.side_effect = requests.ConnectionError()

    with pytest.raises(AIServiceUnavailableError):
        generate_embedding("hola")


@pytest.mark.parametrize("overrides", [{"LLM_PROVIDER": "gemini"}, {"EMBEDDING_PROVIDER": "gemini"}])
def test_gemini_provider_requires_api_key(overrides):
    with pytest.raises(ValidationError, match="GEMINI_API_KEY"):
        Settings(_env_file=None, DATABASE_URL="sqlite://", SECRET_KEY="x", **overrides)


def test_health_skips_ollama_when_demo_providers_are_used(client, monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "EMBEDDING_PROVIDER", "gemini")
    get = MagicMock()
    monkeypatch.setattr("app.routers.health.requests.get", get)

    response = client.get("/health")

    assert response.status_code == 200
    assert set(response.json()["checks"]) == {"database", "gemini"}
    get.assert_not_called()
