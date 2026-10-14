from unittest.mock import MagicMock

import pytest
import requests

from app.ai import gemini_http
from app.ai.gemini_http import MAX_RETRY_WAIT_SECONDS, post_gemini
from app.core.config import settings
from app.core.exceptions import AIRateLimitError, AIServiceUnavailableError


def http_error(status_code: int, body: dict | None = None, headers: dict | None = None):
    response = requests.Response()
    response.status_code = status_code
    response.reason = "Error"
    response.headers.update(headers or {})
    response._content = (
        b"" if body is None else requests.models.complexjson.dumps(body).encode()
    )

    return MagicMock(raise_for_status=MagicMock(
        side_effect=requests.HTTPError(response=response)
    ))


def ok():
    return MagicMock(raise_for_status=MagicMock(return_value=None))


@pytest.fixture
def post(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "g-test")
    monkeypatch.setattr(settings, "GEMINI_MAX_RETRIES", 2)
    mock = MagicMock()
    monkeypatch.setattr(gemini_http.requests, "post", mock)

    return mock


@pytest.fixture
def sleeps(monkeypatch):
    waits: list[float] = []
    monkeypatch.setattr(gemini_http.time, "sleep", waits.append)

    return waits


def call():
    return post_gemini("https://example/x", {"a": 1}, timeout=5, unavailable_message="LLM down")


@pytest.mark.parametrize("status_code", [429, 500, 503])
def test_transient_errors_are_retried(post, sleeps, status_code):
    success = ok()
    post.side_effect = [http_error(status_code), success]

    assert call() is success
    assert post.call_count == 2
    assert sleeps == [1.0]


def test_network_errors_are_retried(post, sleeps):
    success = ok()
    post.side_effect = [requests.ConnectionError(), requests.Timeout(), success]

    assert call() is success
    assert sleeps == [1.0, 2.0]


def test_google_retry_delay_is_honoured(post, sleeps):
    body = {"error": {"status": "RESOURCE_EXHAUSTED", "details": [{"retryDelay": "3s"}]}}
    post.side_effect = [http_error(429, body), ok()]

    call()

    assert sleeps == [3.0]


def test_long_retry_delay_fails_fast_as_rate_limit(post, sleeps, caplog):
    delay = f"{int(MAX_RETRY_WAIT_SECONDS) + 30}s"
    body = {
        "error": {
            "status": "RESOURCE_EXHAUSTED",
            "message": "Quota exceeded for metric generate_content_free_tier_requests",
            "details": [{"retryDelay": delay}],
        }
    }
    post.side_effect = [http_error(429, body)]

    with pytest.raises(AIRateLimitError):
        call()

    assert post.call_count == 1
    assert sleeps == []
    # The real cause reaches the logs; the API key never does.
    assert "status=429" in caplog.text
    assert "Quota exceeded" in caplog.text
    assert "g-test" not in caplog.text


def test_exhausted_retries_on_429_raise_rate_limit(post):
    post.side_effect = [http_error(429)] * 3

    with pytest.raises(AIRateLimitError):
        call()

    assert post.call_count == 3


@pytest.mark.parametrize("status_code", [400, 403, 404])
def test_permanent_errors_are_not_retried(post, sleeps, status_code):
    post.side_effect = [http_error(status_code, {"error": {"message": "model not found"}})]

    with pytest.raises(AIServiceUnavailableError) as raised:
        call()

    assert not isinstance(raised.value, AIRateLimitError)
    assert str(raised.value) == "LLM down"
    assert post.call_count == 1
    assert sleeps == []


def test_rate_limit_returns_429_to_the_client(client, create_user, monkeypatch):
    from app.services import rag_service
    from tests.conftest import auth_headers

    def exhausted(**kwargs):
        raise AIRateLimitError("The AI provider's free quota is exhausted")

    monkeypatch.setattr(rag_service, "search_relevant_chunks", exhausted)
    user = create_user("alice")

    response = client.post(
        "/documents/ask", json={"question": "hola"}, headers=auth_headers(user)
    )

    assert response.status_code == 429
    assert "free quota" in response.json()["detail"]
    assert response.headers["Retry-After"] == "60"
