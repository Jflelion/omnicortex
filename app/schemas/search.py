from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from app.schemas.ask import MAX_RESULTS


class SearchRequest(BaseModel):
    query: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)
    ]
    limit: int = Field(default=5, ge=1, le=MAX_RESULTS)


class SearchResult(BaseModel):
    chunk_id: int
    document_id: int
    chunk_index: int
    content: str
    distance: float
