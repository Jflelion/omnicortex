print("embed_chunks.py started")

from sqlalchemy.orm import Session

from app.database.database import SessionLocal
from app.models.document import Document  # pyright: ignore[reportUnusedImport]
from app.models.document_chunk import DocumentChunk
from app.models.role import Role  # pyright: ignore[reportUnusedImport]
from app.models.user import User  # pyright: ignore[reportUnusedImport]
from app.services.embedding_service import generate_embedding


def embed_pending_chunks(db: Session) -> None:
    chunks = db.query(DocumentChunk).filter(
        DocumentChunk.embedding.is_(None)
    ).all()

    print(f"Chunks pending: {len(chunks)}")

    for chunk in chunks:
        print(f"Embedding chunk {chunk.id}")

        embedding = generate_embedding(chunk.content)

        print(f"Embedding dimensions: {len(embedding)}")

        chunk.embedding = embedding

    db.commit()

    print("Embedding process completed")


def run() -> None:
    db = SessionLocal()

    try:
        embed_pending_chunks(db)
    finally:
        db.close()


if __name__ == "__main__":
    run()