"""
Re-index tool: embeds every chunk still missing an embedding and updates
each affected document's status. Run with
``python -m app.database.embed_chunks`` once Ollama is available.
"""

from sqlalchemy.orm import Session

from app.database.database import SessionLocal
from app.models.document import Document  # pyright: ignore[reportUnusedImport]
from app.models.document_chunk import DocumentChunk
from app.models.role import Role  # pyright: ignore[reportUnusedImport]
from app.models.user import User  # pyright: ignore[reportUnusedImport]
from app.services.document_indexing_service import index_document


def embed_pending_chunks(db: Session) -> None:
    document_ids = [
        document_id
        for (document_id,) in (
            db.query(DocumentChunk.document_id)
            .filter(DocumentChunk.embedding.is_(None))
            .distinct()
            .order_by(DocumentChunk.document_id)
            .all()
        )
    ]

    print(f"Documents pending: {len(document_ids)}")

    for document_id in document_ids:
        index_document(db, document_id)

        document = db.get(Document, document_id)
        status = document.status if document else "deleted"

        print(f"Document {document_id}: {status}")

    print("Embedding process completed")


def run() -> None:
    db = SessionLocal()

    try:
        embed_pending_chunks(db)
    finally:
        db.close()


if __name__ == "__main__":
    run()
