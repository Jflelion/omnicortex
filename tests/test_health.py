from unittest.mock import MagicMock

import pytest
import requests

from app.core.config import settings


def ollama_tags(*names: str) -> MagicMock:
    response = MagicMock()
    response.json.return_value = {"models": [{"name": name} for name in names]}

    return MagicMock(return_value=response)


@pytest.fixture
def ollama_get(monkeypatch):
    def _set(mock: MagicMock) -> None:
        monkeypatch.setattr("app.routers.health.requests.get", mock)

    return _set


def test_health_ok(client, ollama_get):
    ollama_get(ollama_tags(settings.LLM_MODEL, f"{settings.EMBEDDING_MODEL}:latest"))

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "checks": {"database": {"status": "ok"}, "ollama": {"status": "ok"}},
    }


def test_health_reports_ollama_down(client, ollama_get):
    ollama_get(MagicMock(side_effect=requests.ConnectionError()))

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json()["status"] == "degraded"
    assert response.json()["checks"]["database"]["status"] == "ok"
    assert response.json()["checks"]["ollama"]["status"] == "error"


def test_health_reports_missing_models(client, ollama_get):
    ollama_get(ollama_tags(settings.LLM_MODEL))

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json()["checks"]["ollama"]["missing_models"] == [settings.EMBEDDING_MODEL]


def test_health_reports_database_down(client, db, ollama_get):
    ollama_get(ollama_tags(settings.LLM_MODEL, settings.EMBEDDING_MODEL))
    db.execute = MagicMock(side_effect=Exception("db down"))

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json()["checks"]["database"]["status"] == "error"


def test_cors_allows_configured_origin(client):
    origin = settings.cors_origins_list[0]

    response = client.options(
        "/auth/login",
        headers={"Origin": origin, "Access-Control-Request-Method": "POST"}
    )

    assert response.headers["access-control-allow-origin"] == origin


def test_cors_rejects_unknown_origin(client):
    response = client.options(
        "/auth/login",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"}
    )

    assert "access-control-allow-origin" not in response.headers
