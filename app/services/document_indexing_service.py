from sqlalchemy.orm import Session

from app.core.exceptions import AIServiceUnavailableError
from app.database.database import SessionLocal
from app.models.document_chunk import DocumentChunk
from app.observability.logger import get_logger
from app.services.embedding_service import generate_embedding


logger = get_logger(__name__)


def embed_document_chunks(
    db: Session,
    document_id: int
) -> int:
    """
    Generate embeddings for every chunk of a document that has none yet.

    Returns:
        Number of chunks embedded.
    """

    chunks = (
        db.query(DocumentChunk)
        .filter(
            DocumentChunk.document_id == document_id,
            DocumentChunk.embedding.is_(None)
        )
        .order_by(DocumentChunk.chunk_index)
        .all()
    )

    for chunk in chunks:
        chunk.embedding = generate_embedding(chunk.content)

    db.commit()

    return len(chunks)


def index_document_in_background(document_id: int) -> None:
    """
    Background task entry point. Opens its own session because the
    request session is closed once the response is sent.

    If Ollama is unavailable the chunks stay without embedding and can be
    processed later with ``python -m app.database.embed_chunks``.
    """

    db = SessionLocal()

    try:
        embedded = embed_document_chunks(db, document_id)

        logger.info(
            "Document %s indexed: %s chunks embedded",
            document_id,
            embedded
        )

    except AIServiceUnavailableError:
        db.rollback()

        logger.exception(
            "Embedding service unavailable while indexing document %s",
            document_id
        )

    finally:
        db.close()
