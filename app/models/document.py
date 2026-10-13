from datetime import datetime, timezone
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class DocumentStatus(StrEnum):
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    filename: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    # Internal storage path. Never exposed through the API.
    filepath: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    # Chunks are removed by the database (ON DELETE CASCADE).
    chunks = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    content_type: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    extracted_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=DocumentStatus.PROCESSING,
        server_default=DocumentStatus.PROCESSING.value
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    owner = relationship(
        "User",
        back_populates="documents"
    )
