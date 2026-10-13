from app.services.embedding_service import (
    generate_embedding
)


embedding = generate_embedding(
    "Kelly Dayana Gómez Vélez estudia medicina"
)

print(type(embedding))
print(len(embedding))
print(embedding[:10])