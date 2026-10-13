from sqlalchemy.orm import Session

from app.core.exceptions import AIServiceUnavailableError
from app.database.database import SessionLocal
from app.models.document import Document, DocumentStatus
from app.models.document_chunk import DocumentChunk
from app.observability.logger import get_logger
from app.services.embedding_service import generate_embedding


logger = get_logger(__name__)

EMBEDDING_UNAVAILABLE_MESSAGE = (
    "The embedding service was unavailable. Retry with "
    "POST /documents/{id}/reindex."
)
UNEXPECTED_ERROR_MESSAGE = "Unexpected error while indexing the document."


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


def index_document(db: Session, document_id: int) -> None:
    """
    Embed the pending chunks of a document and record the outcome in
    ``Document.status``: ``ready`` on success, ``failed`` (with an
    ``error_message``) otherwise. Embeddings already stored are kept, so
    a retry only processes what is missing.
    """

    try:
        embedded = embed_document_chunks(db, document_id)

    except AIServiceUnavailableError:
        db.rollback()

        logger.exception(
            "Embedding service unavailable while indexing document %s",
            document_id
        )

        _set_status(
            db,
            document_id,
            DocumentStatus.FAILED,
            EMBEDDING_UNAVAILABLE_MESSAGE
        )
        return

    except Exception:
        db.rollback()

        logger.exception("Unexpected error indexing document %s", document_id)

        _set_status(
            db,
            document_id,
            DocumentStatus.FAILED,
            UNEXPECTED_ERROR_MESSAGE
        )
        return

    _set_status(db, document_id, DocumentStatus.READY)

    logger.info(
        "Document %s indexed: %s chunks embedded",
        document_id,
        embedded
    )


def index_document_in_background(document_id: int) -> None:
    """
    Background task entry point. Opens its own session because the
    request session is closed once the response is sent.
    """

    db = SessionLocal()

    try:
        index_document(db, document_id)

    finally:
        db.close()


def _set_status(
    db: Session,
    document_id: int,
    status: DocumentStatus,
    error_message: str | None = None
) -> None:
    document = db.get(Document, document_id)

    # The document may have been deleted while it was being indexed.
    if document is None:
        return

    document.status = status
    document.error_message = error_message
    db.commit()
