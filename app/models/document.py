from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


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

    filepath: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    chunks = relationship(
    "DocumentChunk",
    back_populates="document"
    )

    content_type: Mapped[str] = mapped_column(
        String,
        nullable=False
    )
    
    extracted_text: Mapped[str | None] = mapped_column(
    Text,
    nullable=True
    )

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    owner = relationship(
        "User",
        back_populates="documents"
    )