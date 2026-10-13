from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.document import DocumentStatus
from app.schemas.user import UserResponse


class DocumentBase(BaseModel):
    filename: str
    content_type: str


class DocumentResponse(DocumentBase):
    id: int
    status: DocumentStatus
    error_message: str | None
    uploaded_at: datetime
    owner: UserResponse

    model_config = ConfigDict(from_attributes=True)
