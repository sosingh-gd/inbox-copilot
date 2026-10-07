import asyncio
import logging
import time
from collections.abc import AsyncIterator, Sequence
from dataclasses import asdict, dataclass
from typing import Any, Literal

from anthropic.types import MessageParam
from sqlalchemy.orm import Session, sessionmaker

from app.agents.events import (
    ReplyPart,
    RunFinished,
    TextDelta,
    ThinkingDelta,
    ToolFinished,
    ToolPart,
    ToolStarted,
    UsageUpdated,
)
from app.agents.models import HAIKU, SONNET, AgentError, Effort
from app.agents.registry import AgentRegistry
from app.agents.trace import ModelCall
from app.core.errors import NotFoundError
from app.core.schemas import ApiModel

from .events import (
    RunCompletedEvent,
    RunFailedEvent,
    RunStartedEvent,
    TextDeltaEvent,
    ThinkingDeltaEvent,
    ToolFinishedEvent,
    ToolStartedEvent,
    UsageUpdatedEvent,
)
from .models import ChatMessage, Conversation
from .repository import ChatRepository
from .schemas import (
    ChatRunRequest,
    ConversationCreate,
    ConversationDetail,
    ConversationSummary,
    ModelChoice,
    ReasoningLevel,
    Usage,
)

logger = logging.getLogger(__name__)

TITLE_LENGTH = 60
NEW_CONVERSATION_TITLE = "New conversation"

# The settings bar's choices, in the agents' terms.
MODEL_IDS = {ModelChoice.sonnet: SONNET, ModelChoice.haiku: HAIKU}
EFFORTS: dict[ReasoningLevel, Effort] = {
    ReasoningLevel.fast: "low",
    ReasoningLevel.balanced: "medium",
    # Sonnet rarely thinks before a tool call below "xhigh", so Deep is where thinking shows.
    ReasoningLevel.deep: "xhigh",
}


@dataclass(frozen=True)
class LlmMessage:
    role: Literal["user", "assistant"]
    content: str


@dataclass(frozen=True)
class ChatTurn:
    """Everything the stream needs, loaded before streaming starts."""

    conversation_id: str
    user_message_id: str
    model: ModelChoice
    reasoning: ReasoningLevel
    history: list[LlmMessage]


class ChatService:
    def __init__(
        self,
        repo: ChatRepository,
        agents: AgentRegistry,
        new_session: sessionmaker[Session],
    ) -> None:
        self.repo = repo
        self.agents = agents
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
        logger.info(
            "message_received conversation=%s message=%s chars=%d history_messages=%d "
            "model=%s reasoning=%s",
            conversation.id,
            message.id,
            len(request.content),
            len(conversation.messages),
            request.model.value,
            request.reasoning.value,
        )

        return ChatTurn(
            conversation_id=conversation.id,
            user_message_id=message.id,
            model=request.model,
            reasoning=request.reasoning,
            history=[LlmMessage(role=m.role, content=m.content) for m in conversation.messages],  # type: ignore[arg-type]
        )

    async def stream_reply(self, turn: ChatTurn) -> AsyncIterator[ApiModel]:
        started = time.perf_counter()
        yield RunStartedEvent(
            conversation_id=turn.conversation_id, user_message_id=turn.user_message_id
        )

        history: list[MessageParam] = [
            {"role": m.role, "content": m.content} for m in _merge_consecutive(turn.history)
        ]
        finished: RunFinished | None = None
        usage: Usage | None = None
        calls: list[ModelCall] = []
        try:
            async for event in self.agents.stream(
                history, MODEL_IDS[turn.model], EFFORTS[turn.reasoning]
            ):
                match event:
                    case TextDelta(text=text):
                        yield TextDeltaEvent(text=text)
                    case ThinkingDelta(text=text):
                        yield ThinkingDeltaEvent(text=text)
                    case ToolStarted(agent=agent, tool=tool):
                        yield ToolStartedEvent(agent=agent, tool=tool)
                    case ToolFinished(agent=agent, tool=tool, ok=ok, duration_ms=duration_ms):
                        yield ToolFinishedEvent(
                            agent=agent, tool=tool, ok=ok, duration_ms=duration_ms
                        )
                    case UsageUpdated(usage=totals):
                        usage = Usage.model_validate(totals, from_attributes=True)
                        calls = totals.calls
                        yield UsageUpdatedEvent(usage=usage)
                    case RunFinished():
                        finished = event
        except AgentError as exc:
            logger.warning("run_failed code=%s", exc.code)
            yield RunFailedEvent(code=exc.code, message=exc.message)
            return

        if finished is None:
            logger.warning("run_failed code=incomplete (the agent ended without a reply)")
            yield RunFailedEvent(code="incomplete", message="The reply ended unexpectedly.")
            return

        duration_ms = int((time.perf_counter() - started) * 1000)
        message_id = await asyncio.to_thread(
            self._save_assistant_message,
            turn.conversation_id,
            finished,
            duration_ms,
            usage,
            calls,
        )
        logger.info(
            "run_completed saved_message=%s duration_ms=%d parts=%s %s",
            message_id,
            duration_ms,
            [p.type if isinstance(p, ReplyPart) else f"tool:{p.tool}" for p in finished.parts],
            _usage_summary(usage),
        )
        yield RunCompletedEvent(message_id=message_id, duration_ms=duration_ms, usage=usage)

    def _owned_conversation(self, user_id: int, conversation_id: str) -> Conversation:
        conversation = self.repo.get_conversation(conversation_id, user_id)
        if conversation is None:
            raise NotFoundError("Conversation not found.")
        return conversation

    def _save_assistant_message(
        self,
        conversation_id: str,
        finished: RunFinished,
        duration_ms: int,
        usage: Usage | None,
        calls: list[ModelCall],
    ) -> str:
        with self.new_session() as session:
            repo = ChatRepository(session)
            message = repo.add_message(
                ChatMessage(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=finished.text,
                    parts=[_part_dict(p) for p in finished.parts],
                    duration_ms=duration_ms,
                    usage=usage.model_dump() if usage else None,
                    calls=[asdict(c) for c in calls],
                )
            )
            repo.commit()
            return message.id


def _usage_summary(usage: Usage | None) -> str:
    """Token totals for the log, sub-agents included."""
    if usage is None:
        return "usage=none"
    return (
        f"input_tokens={usage.input_tokens} output_tokens={usage.output_tokens} "
        f"cache_read={usage.cache_read_tokens} cache_write={usage.cache_write_tokens}"
    )


def _part_dict(part: ReplyPart | ToolPart) -> dict[str, Any]:
    """A reply part as stored in the database, in `MessagePart` shape."""
    if isinstance(part, ToolPart):
        return {"type": "tool", **asdict(part)}
    return asdict(part)


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
