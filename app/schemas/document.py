from datetime import datetime

from pydantic import BaseModel

from app.schemas.user import UserResponse


class DocumentBase(BaseModel):
    filename: str
    content_type: str


class DocumentResponse(DocumentBase):
    id: int
    filepath: str
    uploaded_at: datetime
    owner: UserResponse

    class Config:
        from_attributes = True