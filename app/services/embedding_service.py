import requests

from app.core.config import settings
from app.core.exceptions import AIServiceUnavailableError


def generate_embedding(text: str) -> list[float]:
    try:
        response = requests.post(
            f"{settings.OLLAMA_BASE_URL}/api/embeddings",
            json={
                "model": settings.EMBEDDING_MODEL,
                "prompt": text,
                "keep_alive": settings.OLLAMA_KEEP_ALIVE,
            },
            timeout=settings.EMBEDDING_TIMEOUT_SECONDS
        )

        response.raise_for_status()

    except requests.RequestException as error:
        raise AIServiceUnavailableError(
            "Embedding service is unavailable"
        ) from error

    data = response.json()

    embedding = data["embedding"]

    return embedding