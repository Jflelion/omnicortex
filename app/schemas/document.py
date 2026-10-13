from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.user import UserResponse


class DocumentBase(BaseModel):
    filename: str
    content_type: str


class DocumentResponse(DocumentBase):
    id: int
    filepath: str
    uploaded_at: datetime
    owner: UserResponse

    model_config = ConfigDict(from_attributes=True)