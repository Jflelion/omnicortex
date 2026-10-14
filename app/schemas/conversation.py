from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.conversation import MessageRole
from app.schemas.ask import AskRequest, AskSource


class ConversationCreate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)


class ConversationUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class ConversationSummary(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    id: int
    role: MessageRole
    content: str
    sources: list[AskSource] | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationDetail(ConversationSummary):
    messages: list[MessageResponse]


class MessageCreate(AskRequest):
    pass


class ConversationTurn(BaseModel):
    """
    Result of sending a message: the stored question and its answer.
    """

    conversation: ConversationSummary
    user_message: MessageResponse
    assistant_message: MessageResponse
