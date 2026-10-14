import requests
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.database import get_db


router = APIRouter(
    tags=["health"]
)


def _check_database(db: Session) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1"))

        return {"status": "ok"}

    except Exception as error:
        return {"status": "error", "detail": type(error).__name__}


def _check_ollama() -> dict[str, str | list[str]]:
    # Only the models of the providers actually set to Ollama are required.
    required = [
        model
        for provider, model in (
            (settings.LLM_PROVIDER, settings.LLM_MODEL),
            (settings.EMBEDDING_PROVIDER, settings.EMBEDDING_MODEL),
        )
        if provider == "ollama"
    ]

    try:
        response = requests.get(
            f"{settings.OLLAMA_BASE_URL}/api/tags",
            timeout=settings.HEALTH_CHECK_TIMEOUT_SECONDS
        )

        response.raise_for_status()

    except requests.RequestException as error:
        return {"status": "error", "detail": type(error).__name__}

    available = {
        model["name"]
        for model in response.json().get("models", [])
    }

    # Ollama lists untagged models as "<name>:latest".
    missing = [
        model
        for model in required
        if model not in available and f"{model}:latest" not in available
    ]

    if missing:
        return {"status": "error", "missing_models": missing}

    return {"status": "ok"}


@router.get("/health")
def health(db: Session = Depends(get_db)) -> JSONResponse:
    """
    Report whether the API can reach its dependencies.
    Returns 503 if any of them is unavailable.
    """

    checks = {"database": _check_database(db)}

    if "ollama" in (settings.LLM_PROVIDER, settings.EMBEDDING_PROVIDER):
        checks["ollama"] = _check_ollama()

    # Hosted providers are not called here (each call costs money); the
    # settings already refuse to start without their API keys.
    if "gemini" in (settings.LLM_PROVIDER, settings.EMBEDDING_PROVIDER):
        checks["gemini"] = {
            "status": "ok",
            "llm": settings.GEMINI_LLM_MODEL if settings.LLM_PROVIDER == "gemini" else None,
            "embeddings": (
                settings.GEMINI_EMBEDDING_MODEL
                if settings.EMBEDDING_PROVIDER == "gemini"
                else None
            ),
        }

    healthy = all(
        check["status"] == "ok"
        for check in checks.values()
    )

    return JSONResponse(
        status_code=(
            status.HTTP_200_OK
            if healthy
            else status.HTTP_503_SERVICE_UNAVAILABLE
        ),
        content={
            "status": "ok" if healthy else "degraded",
            "checks": checks,
        }
    )
