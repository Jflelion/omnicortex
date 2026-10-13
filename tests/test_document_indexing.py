import pytest

from app.core.exceptions import AIServiceUnavailableError
from app.models.document import Document, DocumentStatus
from app.models.document_chunk import DocumentChunk
from app.services import document_indexing_service
from app.services.document_indexing_service import index_document


@pytest.fixture
def document(db, create_user) -> Document:
    user = create_user("alice")

    document = Document(
        filename="a.pdf",
        filepath="uploads/a.pdf",
        content_type="application/pdf",
        extracted_text="uno dos",
        owner_id=user.id
    )
    db.add(document)
    db.commit()

    for index, content in enumerate(["uno", "dos"]):
        db.add(DocumentChunk(
            document_id=document.id,
            chunk_index=index,
            content=content
        ))

    db.commit()

    return document


def test_new_documents_start_processing(document):
    assert document.status == DocumentStatus.PROCESSING


def test_successful_indexing_marks_document_ready(db, document, monkeypatch):
    monkeypatch.setattr(
        document_indexing_service,
        "generate_embedding",
        lambda _text: [0.1] * 768
    )

    index_document(db, document.id)

    db.refresh(document)
    assert document.status == DocumentStatus.READY
    assert document.error_message is None
    assert all(chunk.embedding is not None for chunk in document.chunks)


@pytest.mark.parametrize(
    "error",
    [AIServiceUnavailableError("Embedding service unavailable"), RuntimeError("boom")]
)
def test_failed_indexing_marks_document_failed(db, document, monkeypatch, error):

    def _raise(_text):
        raise error

    monkeypatch.setattr(document_indexing_service, "generate_embedding", _raise)

    index_document(db, document.id)

    db.refresh(document)
    assert document.status == DocumentStatus.FAILED
    assert document.error_message
    # The internal exception text is not leaked to the user.
    assert "boom" not in document.error_message


def test_indexing_a_deleted_document_is_a_no_op(db, monkeypatch):
    monkeypatch.setattr(
        document_indexing_service,
        "generate_embedding",
        lambda _text: [0.1] * 768
    )

    index_document(db, 999)
