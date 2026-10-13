from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentChunkResponse(BaseModel):
    id: int
    document_id: int
    chunk_index: int
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)