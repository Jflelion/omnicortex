from typing import Any, NamedTuple
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.embedding_service import generate_embedding


class RetrievedChunk(NamedTuple):
    chunk_id: int
    document_id: int
    chunk_index: int
    content: str
    distance: float
    score: float


def _to_retrieved_chunk(result: Any) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=int(result.chunk_id),
        document_id=int(result.document_id),
        chunk_index=int(result.chunk_index),
        content=str(result.content),
        distance=float(result.distance),
        score=float(result.distance)
    )

def search_relevant_chunks(
    query: str,
    user_id: int,
    db: Session,
    limit: int = 5
) -> list[RetrievedChunk]:
    query_embedding = generate_embedding(query)

    semantic_rows = (
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
            Document.owner_id == user_id,
            DocumentChunk.embedding.is_not(None)
        )
        .order_by(
            DocumentChunk.embedding.cosine_distance(
                query_embedding
            )
        )
        .limit(limit * 2)
        .all()
    )

    semantic_results = [
        _to_retrieved_chunk(row)
        for row in semantic_rows
    ]

    query_words = [
        word.strip().lower()
        for word in query.split()
        if len(word.strip()) >= 4
    ]

    keyword_filters = [
        DocumentChunk.content.ilike(f"%{word}%")
        for word in query_words
    ]

    keyword_results: list[RetrievedChunk] = []

    if keyword_filters:
        keyword_rows = (
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
                Document.owner_id == user_id,
                DocumentChunk.embedding.is_not(None),
                or_(*keyword_filters)
            )
            .order_by(
                DocumentChunk.embedding.cosine_distance(
                    query_embedding
                )
            )
            .limit(limit * 2)
            .all()
        )

        keyword_results = [
            _to_retrieved_chunk(row)
            for row in keyword_rows
        ]

    combined: dict[int, RetrievedChunk] = {}

    for result in semantic_results:
        combined[result.chunk_id] = result

    for result in keyword_results:
        combined[result.chunk_id] = result

    sorted_results = sorted(
        combined.values(),
        key=lambda result: result.distance
    )

    return sorted_results[:limit]