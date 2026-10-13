from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector  # pyright: ignore[reportMissingTypeStubs]
from app.database.database import Base


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False
    )

    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    document = relationship(
        "Document",
        back_populates="chunks"
    )
    
    embedding: Mapped[list[float] | None] = mapped_column(
    Vector(768),
    nullable=True
    )