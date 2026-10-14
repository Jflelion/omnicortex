from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.database import get_db
from app.models.conversation import (
    DEFAULT_CONVERSATION_TITLE,
    Conversation,
    Message,
    MessageRole,
)
from app.models.user import User
from app.routers.auth import get_current_active_user
from app.schemas.ask import AskSource
from app.schemas.conversation import (
    ConversationCreate,
    ConversationDetail,
    ConversationSummary,
    ConversationTurn,
    ConversationUpdate,
    MessageCreate,
    MessageResponse,
)
from app.services.prompt_builder import HistoryTurn
from app.services.rag_service import ask_question


TITLE_MAX_LENGTH = 60


router = APIRouter(
    prefix="/conversations",
    tags=["conversations"]
)


@router.post(
    "/",
    response_model=ConversationSummary,
    status_code=status.HTTP_201_CREATED
)
def create_conversation(
    conversation_in: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    conversation = Conversation(
        title=conversation_in.title or DEFAULT_CONVERSATION_TITLE,
        owner_id=current_user.id
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return conversation


@router.get(
    "/",
    response_model=list[ConversationSummary]
)
def list_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return (
        db.query(Conversation)
        .filter(Conversation.owner_id == current_user.id)
        .order_by(Conversation.updated_at.desc(), Conversation.id.desc())
        .all()
    )


@router.get(
    "/{conversation_id}",
    response_model=ConversationDetail
)
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return _get_owned_conversation(db, conversation_id, current_user)


@router.patch(
    "/{conversation_id}",
    response_model=ConversationSummary
)
def rename_conversation(
    conversation_id: int,
    conversation_in: ConversationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    conversation = _get_owned_conversation(db, conversation_id, current_user)

    conversation.title = conversation_in.title

    db.commit()
    db.refresh(conversation)

    return conversation


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    conversation = _get_owned_conversation(db, conversation_id, current_user)

    # Messages are removed by ON DELETE CASCADE.
    db.delete(conversation)
    db.commit()

    return None


@router.post(
    "/{conversation_id}/messages",
    response_model=ConversationTurn,
    status_code=status.HTTP_201_CREATED
)
def send_message(
    conversation_id: int,
    message_in: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Ask a question inside a conversation. The last messages are sent to
    the RAG pipeline as context. The question and the answer are stored
    together only once the answer is generated, so a failed call (e.g.
    Ollama down) leaves the conversation untouched.
    """

    conversation = _get_owned_conversation(db, conversation_id, current_user)

    answer, chunks = ask_question(
        question=message_in.question,
        user_id=current_user.id,
        db=db,
        limit=message_in.limit,
        history=_recent_history(conversation)
    )

    sources = [
        AskSource(
            chunk_id=chunk.chunk_id,
            document_id=chunk.document_id,
            filename=chunk.filename,
            chunk_index=chunk.chunk_index,
            content=chunk.content,
            distance=chunk.distance
        ).model_dump()
        for chunk in chunks
    ]

    user_message = Message(
        role=MessageRole.USER,
        content=message_in.question
    )

    assistant_message = Message(
        role=MessageRole.ASSISTANT,
        content=answer,
        sources=sources
    )

    if (
        not conversation.messages
        and conversation.title == DEFAULT_CONVERSATION_TITLE
    ):
        conversation.title = _title_from_question(message_in.question)

    conversation.messages.extend([user_message, assistant_message])
    conversation.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(conversation)
    db.refresh(user_message)
    db.refresh(assistant_message)

    return ConversationTurn(
        conversation=ConversationSummary.model_validate(conversation),
        user_message=MessageResponse.model_validate(user_message),
        assistant_message=MessageResponse.model_validate(assistant_message)
    )


def _get_owned_conversation(
    db: Session,
    conversation_id: int,
    current_user: User
) -> Conversation:
    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.owner_id == current_user.id
        )
        .first()
    )

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    return conversation


def _recent_history(conversation: Conversation) -> list[HistoryTurn]:
    limit = settings.CONVERSATION_HISTORY_MESSAGES

    if limit <= 0:
        return []

    return [
        HistoryTurn(role=message.role, content=message.content)
        for message in conversation.messages[-limit:]
    ]


def _title_from_question(question: str) -> str:
    """
    Use the first question as the title, cut at a word boundary.
    """

    title = " ".join(question.split())

    if len(title) <= TITLE_MAX_LENGTH:
        return title

    cut = title[:TITLE_MAX_LENGTH].rsplit(" ", 1)[0]

    return f"{cut}…"
