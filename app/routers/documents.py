from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    UploadFile,
    status,
    HTTPException
)

from sqlalchemy.orm import Session

from app.database.database import get_db

from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.user import User

from app.routers.auth import get_current_active_user

from app.schemas.document import DocumentResponse
from app.schemas.document_chunk import DocumentChunkResponse

from app.schemas.search import SearchRequest, SearchResult
from app.services.embedding_service import generate_embedding

from app.services.document_text_extractor import (
    extract_text_from_pdf
)

from app.services.text_chunker import (
    chunk_text
)

from app.schemas.ask import AskRequest, AskResponse, AskSource
from app.services.rag_service import ask_question


UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


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
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    file_extension = Path(
        file.filename or ""
    ).suffix

    stored_filename = (
        f"{uuid4()}{file_extension}"
    )

    file_path = (
        UPLOAD_DIR / stored_filename
    )

    with file_path.open("wb") as buffer:
        buffer.write(
            file.file.read()
        )

    extracted_text: str | None = None

    if file.content_type == "application/pdf":

        extracted_text = (
            extract_text_from_pdf(
                str(file_path)
            )
        )

    document = Document(
        filename=file.filename
        or stored_filename,

        filepath=str(file_path),

        content_type=file.content_type
        or "application/octet-stream",

        extracted_text=extracted_text,

        owner_id=current_user.id
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    if extracted_text:

        chunks = chunk_text(
            extracted_text
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

    return document


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


@router.post(
    "/search",
    response_model=list[SearchResult]
)
def search_documents(
    search_request: SearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query_embedding = generate_embedding(
        search_request.query
    )

    results = (
        db.query(
            DocumentChunk.id.label("chunk_id"),
            DocumentChunk.document_id,
            DocumentChunk.chunk_index,
            DocumentChunk.content,
            DocumentChunk.embedding.cosine_distance(
                query_embedding
            ).label("distance")
        )
        .join(Document)
        .filter(
            Document.owner_id == current_user.id,
            DocumentChunk.embedding.is_not(None)
        )
        .order_by(
            DocumentChunk.embedding.cosine_distance(
                query_embedding
            )
        )
        .limit(search_request.limit)
        .all()
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