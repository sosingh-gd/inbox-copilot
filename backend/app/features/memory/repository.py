from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session, joinedload

from app.features.chat.models import ChatMessage, Conversation

from .models import MemoryFact


class MemoryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def commit(self) -> None:
        self.session.commit()

    def list_facts(self, user_id: int) -> list[MemoryFact]:
        """Most recently changed first, with the conversation each fact came from."""
        stmt = (
            select(MemoryFact)
            .where(MemoryFact.user_id == user_id)
            .options(joinedload(MemoryFact.source_conversation))
            .order_by(MemoryFact.updated_at.desc(), MemoryFact.id.desc())
        )
        return list(self.session.scalars(stmt))

    def get_fact(self, fact_id: int, user_id: int) -> MemoryFact | None:
        """Returns None for facts that don't exist or belong to someone else."""
        return self.session.scalar(
            select(MemoryFact).where(MemoryFact.id == fact_id, MemoryFact.user_id == user_id)
        )

    def add_fact(self, fact: MemoryFact) -> None:
        self.session.add(fact)

    def delete_fact(self, fact: MemoryFact) -> None:
        self.session.delete(fact)

    def delete_facts_from(self, conversation_id: str) -> int:
        result = self.session.execute(
            delete(MemoryFact).where(MemoryFact.source_conversation_id == conversation_id)
        )
        return result.rowcount  # type: ignore[attr-defined, no-any-return]

    def pending_conversations(
        self, user_id: int, exclude_id: str, limit: int
    ) -> list[Conversation]:
        """Conversations saved to memory that have messages compaction hasn't seen yet,
        oldest first so facts change in the order things were said."""
        has_new_messages = (
            select(ChatMessage.id)
            .where(
                ChatMessage.conversation_id == Conversation.id,
                or_(
                    Conversation.compacted_at.is_(None),
                    ChatMessage.created_at > Conversation.compacted_at,
                ),
            )
            .exists()
        )
        stmt = (
            select(Conversation)
            .where(
                Conversation.user_id == user_id,
                Conversation.save_to_memory.is_(True),
                Conversation.id != exclude_id,
                has_new_messages,
            )
            .order_by(Conversation.updated_at)
            .limit(limit)
        )
        return list(self.session.scalars(stmt))
