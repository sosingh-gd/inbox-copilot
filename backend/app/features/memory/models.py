from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UTCDateTime, utc_now

if TYPE_CHECKING:
    from app.features.chat.models import Conversation


class MemoryFact(Base):
    """One thing remembered about the user, extracted from a conversation saved to memory."""

    __tablename__ = "memory_facts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    text: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(16))  # a schemas.FactCategory
    # The conversation that last added or changed this fact. Deleting the conversation, or
    # turning off "save to memory" on it, removes the fact.
    source_conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now, index=True)

    source_conversation: Mapped["Conversation"] = relationship()
