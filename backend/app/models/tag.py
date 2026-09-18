import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Table, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.todo import Todo
    from app.models.user import User

# Association table for many-to-many relationship between Todo and Tag
todo_tags = Table(
    "todo_tags",
    Base.metadata,
    Column(
        "todo_id",
        ForeignKey("todos.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Index("idx_todo_tags_todo_id", "todo_id"),
    Index("idx_todo_tags_tag_id", "tag_id"),
)


class Tag(Base):
    """Tag model."""

    __tablename__ = "tags"

    __table_args__ = (
        Index("idx_tags_user_id", "user_id"),
        Index(
            "uq_user_tag_name_lower",
            "user_id",
            func.lower(text("name")),
            unique=True,
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    color: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="tags")
    todos: Mapped[list["Todo"]] = relationship(
        "Todo",
        secondary=todo_tags,
        back_populates="tags",
    )

    def __repr__(self) -> str:
        return f"<Tag {self.name}>"