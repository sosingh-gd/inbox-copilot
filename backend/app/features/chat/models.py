from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UTCDateTime, utc_now


def new_id() -> str:
    return str(uuid4())


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    model: Mapped[str] = mapped_column(String(32))
    reasoning: Mapped[str] = mapped_column(String(32))
    # Memory: whether replies see the facts from earlier conversations (fixed once the
    # conversation exists), and whether this conversation's own facts are remembered.
    use_memory: Mapped[bool] = mapped_column(Boolean, default=True)
    save_to_memory: Mapped[bool] = mapped_column(Boolean, default=True)
    # Prompt caching for the next message; like model and reasoning, it can change per message.
    prompt_caching: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    # The created_at of the last message turned into facts. None: nothing compacted yet.
    compacted_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now, index=True)

    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(16))  # "user" | "assistant"
    content: Mapped[str] = mapped_column(Text)
    parts: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON)  # schemas.MessagePart dicts
    duration_ms: Mapped[int | None] = mapped_column(Integer)  # assistant replies only
    usage: Mapped[dict[str, int] | None] = mapped_column(JSON)  # a schemas.Usage, as a dict
    calls: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON)  # schemas.ModelCall dicts
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now)

    conversation: Mapped[Conversation] = relationship(back_populates="messages")
