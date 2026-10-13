from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    UploadFile,
    status,
    HTTPException
)

from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.database import get_db

from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.user import User

from app.routers.auth import get_current_active_user

from app.schemas.document import DocumentResponse
from app.schemas.document_chunk import DocumentChunkResponse

from app.schemas.search import SearchRequest, SearchResult
from app.services.retrieval_service import semantic_search

from app.services.document_text_extractor import (
    extract_text_from_pdf
)

from app.services.document_indexing_service import (
    index_document_in_background
)

from app.services.text_chunker import (
    chunk_text
)

from app.schemas.ask import AskRequest, AskResponse, AskSource
from app.services.rag_service import ask_question


UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

MAX_UPLOAD_SIZE_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
UPLOAD_READ_CHUNK_BYTES = 1024 * 1024
PDF_MAGIC_BYTES = b"%PDF-"


router = APIRouter(
    prefix="/documents",
    tags=["documents"]
)


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED
)
def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if Path(file.filename or "").suffix.lower() != ".pdf":

        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF files are allowed"
        )

    stored_filename = f"{uuid4()}.pdf"

    file_path = (
        UPLOAD_DIR / stored_filename
    )

    _save_upload(file, file_path)

    try:
        extracted_text = extract_text_from_pdf(
            str(file_path)
        )

    except Exception:
        file_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The PDF file could not be read"
        )

    document = Document(
        filename=file.filename
        or stored_filename,

        filepath=str(file_path),

        content_type="application/pdf",

        extracted_text=extracted_text or None,

        owner_id=current_user.id
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    if extracted_text:

        chunks = chunk_text(
            extracted_text,
            chunk_size=settings.CHUNK_SIZE,
            overlap=settings.CHUNK_OVERLAP
        )

        for index, chunk in enumerate(
            chunks
        ):

            document_chunk = (
                DocumentChunk(
                    document_id=document.id,
                    chunk_index=index,
                    content=chunk
                )
            )

            db.add(document_chunk)

        db.commit()

        background_tasks.add_task(
            index_document_in_background,
            document.id
        )

    return document


def _save_upload(
    file: UploadFile,
    file_path: Path
) -> None:
    """
    Stream the upload to disk in fixed-size blocks, rejecting files that
    exceed MAX_UPLOAD_SIZE_BYTES or do not start with the PDF signature.
    """

    total_bytes = 0

    try:
        with file_path.open("wb") as buffer:

            while block := file.file.read(UPLOAD_READ_CHUNK_BYTES):

                if total_bytes == 0 and not block.startswith(
                    PDF_MAGIC_BYTES
                ):
                    raise HTTPException(
                        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                        detail="The file is not a valid PDF"
                    )

                total_bytes += len(block)

                if total_bytes > MAX_UPLOAD_SIZE_BYTES:
                    raise HTTPException(
                        status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                        detail=(
                            "File exceeds the maximum size of "
                            f"{settings.MAX_UPLOAD_SIZE_MB} MB"
                        )
                    )

                buffer.write(block)

        if total_bytes == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The file is empty"
            )

    except HTTPException:
        file_path.unlink(missing_ok=True)
        raise


@router.get(
    "/",
    response_model=list[DocumentResponse]
)
def get_my_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_active_user
    )
):
    documents = (
        db.query(Document)
        .filter(
            Document.owner_id
            == current_user.id
        )
        .all()
    )

    return documents

@router.post(
    "/ask",
    response_model=AskResponse
)
def ask_documents(
    ask_request: AskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    answer, chunks = ask_question(
        question=ask_request.question,
        user_id=current_user.id,
        db=db,
        limit=ask_request.limit
    )

    return AskResponse(
    answer=answer,
    sources=[
        AskSource(
            chunk_id=chunk.chunk_id,
            document_id=chunk.document_id,
            chunk_index=chunk.chunk_index,
            content=chunk.content,
            distance=chunk.distance
        )
        for chunk in chunks
    ]
)

@router.get(
    "/{document_id}/chunks",
    response_model=list[
        DocumentChunkResponse
    ]
)
def get_document_chunks(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_active_user
    )
):
    document = (
        db.query(Document)
        .filter(
            Document.id
            == document_id,

            Document.owner_id
            == current_user.id
        )
        .first()
    )

    if not document:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    chunks = (
        db.query(DocumentChunk)
        .filter(
            DocumentChunk.document_id
            == document_id
        )
        .order_by(
            DocumentChunk.chunk_index
        )
        .all()
    )

    return chunks


@router.get(
    "/{document_id}",
    response_model=DocumentResponse
)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_active_user
    )
):
    document = (
        db.query(Document)
        .filter(
            Document.id
            == document_id,

            Document.owner_id
            == current_user.id
        )
        .first()
    )

    if not document:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    return document


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_active_user
    )
):
    document = (
        db.query(Document)
        .filter(
            Document.id
            == document_id,

            Document.owner_id
            == current_user.id
        )
        .first()
    )

    if not document:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    file_path = Path(document.filepath)

    db.query(DocumentChunk).filter(
        DocumentChunk.document_id
        == document_id
    ).delete(synchronize_session=False)

    db.delete(document)
    db.commit()

    file_path.unlink(missing_ok=True)

    return None


@router.post(
    "/search",
    response_model=list[SearchResult]
)
def search_documents(
    search_request: SearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    results = semantic_search(
        query=search_request.query,
        user_id=current_user.id,
        db=db,
        limit=search_request.limit
    )

    return [
        SearchResult(
            chunk_id=result.chunk_id,
            document_id=result.document_id,
            chunk_index=result.chunk_index,
            content=result.content,
            distance=result.distance
        )
        for result in results
    ]
