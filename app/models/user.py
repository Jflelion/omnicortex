from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    username: Mapped[str] = mapped_column(
        String,
        unique=True,
        index=True,
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String,
        unique=True,
        index=True,
        nullable=False
    )

    full_name: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    hashed_password: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id")
    )

    role = relationship(
        "Role",
        back_populates="users"
    )
    
    # Documents (and their chunks) are removed by the database
    # (ON DELETE CASCADE).
    documents = relationship(
        "Document",
        back_populates="owner",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    conversations = relationship(
        "Conversation",
        back_populates="owner",
        cascade="all, delete-orphan",
        passive_deletes=True
    )