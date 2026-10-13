import requests

from app.core.exceptions import AIServiceUnavailableError


OLLAMA_EMBEDDING_URL = "http://localhost:11434/api/embeddings"
OLLAMA_EMBEDDING_MODEL = "nomic-embed-text"


def generate_embedding(text: str) -> list[float]:
    try:
        response = requests.post(
            OLLAMA_EMBEDDING_URL,
            json={
                "model": OLLAMA_EMBEDDING_MODEL,
                "prompt": text,
                "keep_alive": "30m",
            },
            timeout=60
        )

        response.raise_for_status()

    except requests.RequestException as error:
        raise AIServiceUnavailableError(
            "Embedding service is unavailable"
        ) from error

    data = response.json()

    embedding = data["embedding"]

    return embedding