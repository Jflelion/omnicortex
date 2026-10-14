"""
Embedding generation behind a provider switch (``EMBEDDING_PROVIDER``):

- ``ollama``: local ``nomic-embed-text`` (development).
- ``gemini``: Google's ``gemini-embedding-2`` reduced to the same 768
  dimensions, so the schema does not change (public demo).

Documents and queries are embedded through separate functions because
retrieval models are trained with different instructions for each side.
Ollama keeps the original behaviour (no prefix) so existing local vectors
stay comparable.
"""

import requests

from app.core.config import settings
from app.core.exceptions import AIServiceUnavailableError


GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta"
EMBEDDING_DIMENSIONS = 768

# Texts sent per request to the hosted API.
GEMINI_BATCH_SIZE = 32

# gemini-embedding-2 takes the task as a text prefix instead of task_type.
GEMINI_QUERY_PREFIX = "task: search result | query: "
GEMINI_DOCUMENT_PREFIX = "title: none | text: "


def generate_embedding(text: str) -> list[float]:
    """
    Embed a search query.
    """

    if settings.EMBEDDING_PROVIDER == "gemini":
        return _gemini_embeddings([GEMINI_QUERY_PREFIX + text])[0]

    return _ollama_embedding(text)


def generate_document_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Embed document chunks, preserving order.
    """

    if settings.EMBEDDING_PROVIDER == "gemini":
        embeddings: list[list[float]] = []

        for start in range(0, len(texts), GEMINI_BATCH_SIZE):
            embeddings.extend(
                _gemini_embeddings([
                    GEMINI_DOCUMENT_PREFIX + text
                    for text in texts[start:start + GEMINI_BATCH_SIZE]
                ])
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


def _gemini_embeddings(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    model = f"models/{settings.GEMINI_EMBEDDING_MODEL}"

    try:
        response = requests.post(
            f"{GEMINI_API_URL}/{model}:batchEmbedContents",
            headers={"x-goog-api-key": settings.GEMINI_API_KEY or ""},
            json={
                "requests": [
                    {
                        "model": model,
                        "content": {"parts": [{"text": text}]},
                        "outputDimensionality": EMBEDDING_DIMENSIONS,
                    }
                    for text in texts
                ]
            },
            timeout=settings.EMBEDDING_TIMEOUT_SECONDS
        )

        response.raise_for_status()

    except requests.RequestException as error:
        raise AIServiceUnavailableError(
            "Embedding service is unavailable"
        ) from error

    embeddings = [
        item["values"]
        for item in response.json().get("embeddings", [])
    ]

    # A silent change of size would corrupt the vector(768) column.
    if len(embeddings) != len(texts) or any(
        len(embedding) != EMBEDDING_DIMENSIONS for embedding in embeddings
    ):
        raise AIServiceUnavailableError(
            "Embedding service returned unexpected vectors"
        )

    return embeddings
