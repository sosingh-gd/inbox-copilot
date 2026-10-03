from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import utc_now

from .models import ChatMessage, Conversation


class ChatRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def commit(self) -> None:
        self.session.commit()

    def list_conversations(self, user_id: int) -> list[Conversation]:
        stmt = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
        )
        return list(self.session.scalars(stmt))

    def get_conversation(self, conversation_id: str, user_id: int) -> Conversation | None:
        """Returns None for conversations that don't exist or belong to someone else."""
        return self.session.scalar(
            select(Conversation).where(
                Conversation.id == conversation_id, Conversation.user_id == user_id
            )
        )

    def add_conversation(self, conversation: Conversation) -> Conversation:
        self.session.add(conversation)
        self.session.flush()  # assigns conversation.id
        return conversation

    def add_message(self, message: ChatMessage) -> ChatMessage:
        """Add a message and bump its conversation to the top of the list."""
        self.session.add(message)
        conversation = self.session.get(Conversation, message.conversation_id)
        if conversation is not None:
            conversation.updated_at = utc_now()
        self.session.flush()
        return message
