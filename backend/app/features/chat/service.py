import asyncio
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass

from sqlalchemy.orm import Session, sessionmaker

from app.core.errors import NotFoundError
from app.core.schemas import ApiModel

from .events import RunCompletedEvent, RunFailedEvent, RunStartedEvent, TextDeltaEvent, Usage
from .llm import ChatModel, Completion, LlmError, LlmMessage, TextChunk
from .models import ChatMessage, Conversation
from .prompts import system_prompt
from .repository import ChatRepository
from .schemas import (
    AgentKind,
    ChatRunRequest,
    ConversationCreate,
    ConversationDetail,
    ConversationSummary,
    ModelChoice,
    ReasoningLevel,
)

TITLE_LENGTH = 60
NEW_CONVERSATION_TITLE = "New conversation"


@dataclass(frozen=True)
class ChatTurn:
    """Everything the stream needs, loaded before streaming starts."""

    conversation_id: str
    user_message_id: str
    agent: AgentKind
    model: ModelChoice
    reasoning: ReasoningLevel
    history: list[LlmMessage]


class ChatService:
    def __init__(
        self,
        repo: ChatRepository,
        llm: ChatModel,
        new_session: sessionmaker[Session],
    ) -> None:
        self.repo = repo
        self.llm = llm
        # Streams outlive the request, so writes after streaming use their own short session.
        self.new_session = new_session

    def list_conversations(self, user_id: int) -> list[ConversationSummary]:
        return [
            ConversationSummary.model_validate(c) for c in self.repo.list_conversations(user_id)
        ]

    def get_conversation(self, user_id: int, conversation_id: str) -> ConversationDetail:
        return ConversationDetail.model_validate(self._owned_conversation(user_id, conversation_id))

    def create_conversation(self, user_id: int, request: ConversationCreate) -> ConversationSummary:
        conversation = self.repo.add_conversation(
            Conversation(
                user_id=user_id,
                title=NEW_CONVERSATION_TITLE,
                agent=request.agent,
                model=request.model,
                reasoning=request.reasoning,
            )
        )
        self.repo.commit()
        return ConversationSummary.model_validate(conversation)

    def start_turn(self, user_id: int, conversation_id: str, request: ChatRunRequest) -> ChatTurn:
        """Validate and save the user's message. Errors here become normal 4xx responses."""
        conversation = self._owned_conversation(user_id, conversation_id)
        if not conversation.messages:
            conversation.title = _title_from(request.content)
        conversation.model = request.model
        conversation.reasoning = request.reasoning

        message = self.repo.add_message(
            ChatMessage(conversation_id=conversation.id, role="user", content=request.content)
        )
        self.repo.commit()
        self.repo.session.refresh(conversation)

        return ChatTurn(
            conversation_id=conversation.id,
            user_message_id=message.id,
            agent=AgentKind(conversation.agent),
            model=request.model,
            reasoning=request.reasoning,
            history=[LlmMessage(role=m.role, content=m.content) for m in conversation.messages],  # type: ignore[arg-type]
        )

    async def stream_reply(self, turn: ChatTurn) -> AsyncIterator[ApiModel]:
        yield RunStartedEvent(
            conversation_id=turn.conversation_id, user_message_id=turn.user_message_id
        )

        parts: list[str] = []
        completion: Completion | None = None
        try:
            async for event in self.llm.stream(
                system=system_prompt(turn.agent),
                messages=_merge_consecutive(turn.history),
                model=turn.model,
                reasoning=turn.reasoning,
            ):
                if isinstance(event, TextChunk):
                    parts.append(event.text)
                    yield TextDeltaEvent(text=event.text)
                else:
                    completion = event
        except LlmError as exc:
            yield RunFailedEvent(code=exc.code, message=exc.message)
            return

        if completion is None:
            yield RunFailedEvent(code="incomplete", message="The reply ended unexpectedly.")
            return
        if completion.refused:
            yield RunFailedEvent(code="refused", message="Claude declined to answer this request.")
            return

        message_id = await asyncio.to_thread(
            self._save_assistant_message, turn.conversation_id, "".join(parts)
        )
        yield RunCompletedEvent(
            message_id=message_id,
            usage=Usage(
                input_tokens=completion.input_tokens, output_tokens=completion.output_tokens
            ),
        )

    def _owned_conversation(self, user_id: int, conversation_id: str) -> Conversation:
        conversation = self.repo.get_conversation(conversation_id, user_id)
        if conversation is None:
            raise NotFoundError("Conversation not found.")
        return conversation

    def _save_assistant_message(self, conversation_id: str, content: str) -> str:
        with self.new_session() as session:
            repo = ChatRepository(session)
            message = repo.add_message(
                ChatMessage(conversation_id=conversation_id, role="assistant", content=content)
            )
            repo.commit()
            return message.id


def _title_from(content: str) -> str:
    line = " ".join(content.split())
    return line if len(line) <= TITLE_LENGTH else line[: TITLE_LENGTH - 1].rstrip() + "…"


def _merge_consecutive(history: Sequence[LlmMessage]) -> list[LlmMessage]:
    """A failed reply leaves two user messages in a row; join them into one turn."""
    merged: list[LlmMessage] = []
    for message in history:
        if merged and merged[-1].role == message.role:
            merged[-1] = LlmMessage(
                role=message.role, content=f"{merged[-1].content}\n\n{message.content}"
            )
        else:
            merged.append(message)
    return merged
