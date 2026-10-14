from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints


MAX_RESULTS = 20


class AskRequest(BaseModel):
    question: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)
    ]
    limit: int = Field(default=5, ge=1, le=MAX_RESULTS)


class AskSource(BaseModel):
    chunk_id: int
    document_id: int
    filename: str = ""
    chunk_index: int
    content: str
    distance: float


class AskResponse(BaseModel):
    answer: str
    sources: list[AskSource]
