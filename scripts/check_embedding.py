"""
Quick manual check that the embedding model in Ollama responds.

Usage:
    python -m scripts.check_embedding
"""

from app.services.embedding_service import (
    generate_embedding
)


embedding = generate_embedding(
    "OmniCortex procesa documentos PDF"
)

print(type(embedding))
print(len(embedding))
print(embedding[:10])
