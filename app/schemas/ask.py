from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    limit: int = Field(default=5, ge=1, le=20)


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
