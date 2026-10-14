"""
Embedding generation behind a provider switch (``EMBEDDING_PROVIDER``):

- ``ollama``: local ``nomic-embed-text`` (development).
- ``nomic``: Nomic's hosted API with the same model family and the same 768
  dimensions, so the schema does not change (public demo).

Documents and queries are embedded through separate functions because
Nomic models are trained with a task prefix (``search_document`` vs
``search_query``). Ollama keeps the original behaviour (no prefix) so
existing local vectors stay comparable.
"""

import requests

from app.core.config import settings
from app.core.exceptions import AIServiceUnavailableError


NOMIC_EMBEDDING_URL = "https://api-atlas.nomic.ai/v1/embedding/text"
EMBEDDING_DIMENSIONS = 768

# Texts sent per request to the hosted API.
NOMIC_BATCH_SIZE = 32


def generate_embedding(text: str) -> list[float]:
    """
    Embed a search query.
    """

    if settings.EMBEDDING_PROVIDER == "nomic":
        return _nomic_embeddings([text], task_type="search_query")[0]

    return _ollama_embedding(text)


def generate_document_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Embed document chunks, preserving order.
    """

    if settings.EMBEDDING_PROVIDER == "nomic":
        embeddings: list[list[float]] = []

        for start in range(0, len(texts), NOMIC_BATCH_SIZE):
            embeddings.extend(
                _nomic_embeddings(
                    texts[start:start + NOMIC_BATCH_SIZE],
                    task_type="search_document"
                )
            )

        return embeddings

    return [_ollama_embedding(text) for text in texts]


def _ollama_embedding(text: str) -> list[float]:
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

    return response.json()["embedding"]


def _nomic_embeddings(
    texts: list[str],
    task_type: str
) -> list[list[float]]:
    if not texts:
        return []

    try:
        response = requests.post(
            NOMIC_EMBEDDING_URL,
            headers={"Authorization": f"Bearer {settings.NOMIC_API_KEY}"},
            json={
                "model": settings.NOMIC_EMBEDDING_MODEL,
                "texts": texts,
                "task_type": task_type,
                "dimensionality": EMBEDDING_DIMENSIONS,
                "long_text_mode": "truncate",
            },
            timeout=settings.EMBEDDING_TIMEOUT_SECONDS
        )

        response.raise_for_status()

    except requests.RequestException as error:
        raise AIServiceUnavailableError(
            "Embedding service is unavailable"
        ) from error

    embeddings = response.json()["embeddings"]

    if len(embeddings) != len(texts):
        raise AIServiceUnavailableError(
            "Embedding service returned an unexpected number of vectors"
        )

    return embeddings
