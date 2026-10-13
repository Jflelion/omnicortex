from pydantic import BaseModel


class AskRequest(BaseModel):
    question: str
    limit: int = 5


class AskSource(BaseModel):
    chunk_id: int
    document_id: int
    chunk_index: int
    content: str
    distance: float


class AskResponse(BaseModel):
    answer: str
    sources: list[AskSource]