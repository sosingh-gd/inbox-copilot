import asyncio
import logging
import time
from collections.abc import AsyncIterator, Sequence
from dataclasses import asdict, dataclass, replace
from datetime import date, datetime
from typing import Any

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
from app.db.base import utc_now
from app.features.memory.service import CompactionResult, MemoryService

from .compaction import (
    ContextEstimate,
    HistoryMessage,
    estimate_context,
    fits_after,
    needs_compaction,
    plan_compaction,
    summary_for_prompt,
    summary_words,
    transcript,
    worth_folding,
)
from .events import (
    ContextCompactedEvent,
    MemoryUpdatedEvent,
    RunCompletedEvent,
    RunFailedEvent,
    RunStartedEvent,
    TextDeltaEvent,
    ThinkingDeltaEvent,
    ToolFinishedEvent,
    ToolStartedEvent,
    UsageUpdatedEvent,
)
from .llm import ConversationSummarizer
from .models import ChatMessage, Conversation
from .repository import ChatRepository
from .schemas import (
    ChatRunRequest,
    ConversationCreate,
    ConversationDetail,
    ConversationSummary,
    ConversationUpdate,
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
class ChatTurn:
    """Everything the stream needs, loaded before streaming starts."""

    user_id: int
    conversation_id: str
    user_message_id: str
    model: ModelChoice
    reasoning: ReasoningLevel
    prompt_caching: bool
    # The messages Claude sees word for word (those after the summary), ending with the new one.
    history: list[HistoryMessage]
    summary: str | None
    context_cap: int
    context: ContextEstimate  # the prompt's estimated size, the new message included
    use_memory: bool
    # Lazy compaction: a conversation's first message first turns the user's other saved
    # conversations into facts, so this one starts with an up-to-date memory.
    compact_memory: bool


class ChatService:
    def __init__(
        self,
        repo: ChatRepository,
        agents: AgentRegistry,
        memory: MemoryService,
        summarizer: ConversationSummarizer,
        new_session: sessionmaker[Session],
    ) -> None:
        self.repo = repo
        self.agents = agents
        self.memory = memory
        self.summarizer = summarizer
        # Streams outlive the request, so writes after streaming use their own short session.
        self.new_session = new_session

    def list_conversations(self, user_id: int) -> list[ConversationSummary]:
        return [
            ConversationSummary.model_validate(c) for c in self.repo.list_conversations(user_id)
        ]

    def get_conversation(self, user_id: int, conversation_id: str) -> ConversationDetail:
        conversation = self._owned_conversation(user_id, conversation_id)
        detail = ConversationDetail.model_validate(conversation)
        detail.context_tokens = estimate_context(
            _unsummarized(conversation), conversation.summary, conversation.summarized_at
        ).tokens
        return detail

    def create_conversation(self, user_id: int, request: ConversationCreate) -> ConversationSummary:
        conversation = self.repo.add_conversation(
            Conversation(
                user_id=user_id,
                title=NEW_CONVERSATION_TITLE,
                model=request.model,
                reasoning=request.reasoning,
                prompt_caching=request.prompt_caching,
                context_cap=request.context_cap,
                use_memory=request.use_memory,
                save_to_memory=request.save_to_memory,
            )
        )
        self.repo.commit()
        return ConversationSummary.model_validate(conversation)

    def update_conversation(
        self, user_id: int, conversation_id: str, request: ConversationUpdate
    ) -> ConversationSummary:
        """Turning saving off forgets the facts this conversation added. Either way the
        whole conversation is compacted again the next time it is saved to memory."""
        conversation = self._owned_conversation(user_id, conversation_id)
        if request.save_to_memory != conversation.save_to_memory:
            if not request.save_to_memory:
                self.memory.forget_conversation(conversation.id)
            conversation.save_to_memory = request.save_to_memory
            conversation.compacted_at = None
            self.repo.commit()
        return ConversationSummary.model_validate(conversation)

    def start_turn(self, user_id: int, conversation_id: str, request: ChatRunRequest) -> ChatTurn:
        """Validate and save the user's message. Errors here become normal 4xx responses."""
        conversation = self._owned_conversation(user_id, conversation_id)
        is_first_message = not conversation.messages
        if is_first_message:
            conversation.title = _title_from(request.content)
        conversation.model = request.model
        conversation.reasoning = request.reasoning
        conversation.prompt_caching = request.prompt_caching
        conversation.context_cap = request.context_cap

        message = self.repo.add_message(
            ChatMessage(conversation_id=conversation.id, role="user", content=request.content)
        )
        self.repo.commit()
        self.repo.session.refresh(conversation)
        history = _unsummarized(conversation)
        context = estimate_context(history, conversation.summary, conversation.summarized_at)
        logger.info(
            "message_received conversation=%s message=%s chars=%d history_messages=%d "
            "summarized_messages=%d context_tokens~%d fixed_tokens~%d chars_per_token=%.2f "
            "context_cap=%d model=%s reasoning=%s "
            "prompt_caching=%s",
            conversation.id,
            message.id,
            len(request.content),
            len(history),
            len(conversation.messages) - len(history),
            context.tokens,
            context.fixed_tokens,
            1 / context.tokens_per_char,
            request.context_cap,
            request.model.value,
            request.reasoning.value,
            request.prompt_caching,
        )

        return ChatTurn(
            user_id=user_id,
            conversation_id=conversation.id,
            user_message_id=message.id,
            model=request.model,
            reasoning=request.reasoning,
            prompt_caching=request.prompt_caching,
            history=history,
            summary=conversation.summary,
            context_cap=request.context_cap,
            context=context,
            use_memory=conversation.use_memory,
            compact_memory=conversation.use_memory and is_first_message,
        )

    async def stream_reply(self, turn: ChatTurn) -> AsyncIterator[ApiModel]:
        started = time.perf_counter()
        yield RunStartedEvent(
            conversation_id=turn.conversation_id, user_message_id=turn.user_message_id
        )

        finished: RunFinished | None = None
        usage: Usage | None = None
        calls: list[ModelCall] = []
        notes: list[str] = []  # shown above the reply, never sent to Claude

        memory: str | None = None
        if turn.use_memory:
            if turn.compact_memory:
                totals = self.agents.usage
                compaction = await self.memory.compact_pending(
                    turn.user_id, turn.conversation_id, totals
                )
                if compaction.conversations:
                    notes.append(_memory_note(compaction))
                    yield MemoryUpdatedEvent(
                        conversations=compaction.conversations,
                        added=compaction.added,
                        updated=compaction.updated,
                        deleted=compaction.deleted,
                        summary=notes[-1],
                    )
                if totals.calls:
                    usage = Usage.model_validate(totals, from_attributes=True)
                    calls = list(totals.calls)
                    yield UsageUpdatedEvent(usage=usage)
            memory = await asyncio.to_thread(self.memory.facts_for_prompt, turn.user_id)

        history, summary = turn.history, turn.summary
        if needs_compaction(turn.context, turn.context_cap):
            compacted = await self._compact_context(turn)
            if compacted is not None:
                history, summary, compacted_event = compacted
                notes.append(compacted_event.summary)
                yield compacted_event
                totals = self.agents.usage
                usage = Usage.model_validate(totals, from_attributes=True)
                calls = list(totals.calls)
                yield UsageUpdatedEvent(usage=usage)

        messages: list[MessageParam] = [
            {"role": m.role, "content": m.content} for m in _merge_consecutive(history)
        ]
        try:
            async for event in self.agents.stream(
                messages,
                MODEL_IDS[turn.model],
                EFFORTS[turn.reasoning],
                memory,
                turn.prompt_caching,
                summary_for_prompt(summary),
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
            notes,
        )
        logger.info(
            "run_completed saved_message=%s duration_ms=%d parts=%s %s",
            message_id,
            duration_ms,
            [p.type if isinstance(p, ReplyPart) else f"tool:{p.tool}" for p in finished.parts],
            _usage_summary(usage),
        )
        yield RunCompletedEvent(message_id=message_id, duration_ms=duration_ms, usage=usage)

    async def _compact_context(
        self, turn: ChatTurn
    ) -> tuple[list[HistoryMessage], str, ContextCompactedEvent] | None:
        """Fold the oldest messages into the summary. Returns the messages still sent word for
        word, the new summary and the event announcing it, or None when nothing was folded:
        then the reply goes ahead with the whole history, over the cap or not."""
        context, cap = turn.context, turn.context_cap
        plan = plan_compaction(turn.history, context, cap)
        if plan is None:
            logger.warning(
                "context_over_cap context_tokens~%d cap=%d: only the newest exchange is left",
                context.tokens,
                cap,
            )
            return None
        if not worth_folding(plan, cap):
            # Typically right after a compaction that could not get under the cap: wait until
            # enough has built up, rather than paying for a summary every message.
            logger.info(
                "context_compaction_skipped fold_tokens~%d cap=%d: too little to fold yet",
                plan.fold_tokens,
                cap,
            )
            return None
        if not fits_after(plan, context, cap):
            logger.warning(
                "context_cap_too_small cap=%d fixed_tokens~%d keep_tokens~%d: the prompt stays "
                "over the cap's trigger after compacting; pick a larger cap for this chat",
                cap,
                context.fixed_tokens,
                plan.keep_tokens,
            )
        try:
            summary = await self.summarizer.summarize(
                turn.summary,
                transcript(plan.fold),
                summary_words(context, cap),
                date.today(),
                self.agents.usage,
            )
        except AgentError as exc:
            logger.warning("context_compaction_failed code=%s", exc.code)
            return None

        await asyncio.to_thread(
            self._save_summary, turn.conversation_id, summary, plan.fold[-1].created_at
        )
        tokens_after = (
            context.fixed_tokens + context.of(summary_for_prompt(summary)) + plan.keep_tokens
        )
        folded = len(plan.fold)
        note = (
            f"Context compacted: {folded} earlier message{'s' if folded > 1 else ''} summarized, "
            f"prompt ~{_thousands(context.tokens)} → ~{_thousands(tokens_after)} tokens "
            f"(cap {_thousands(cap)})."
        )
        logger.info(
            "context_compacted folded_messages=%d kept_messages=%d summary_chars=%d "
            "context_tokens~%d->%d cap=%d",
            folded,
            len(plan.keep),
            len(summary),
            context.tokens,
            tokens_after,
            cap,
        )
        event = ContextCompactedEvent(
            messages=folded,
            tokens_before=context.tokens,
            tokens_after=tokens_after,
            summary=note,
        )
        return plan.keep, summary, event

    def _save_summary(self, conversation_id: str, summary: str, through: datetime) -> None:
        with self.new_session() as session:
            conversation = session.get(Conversation, conversation_id)
            if conversation is None:
                return  # deleted while the summary was written
            conversation.summary = summary
            conversation.summarized_through = through
            conversation.summarized_at = utc_now()
            session.commit()

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
        notes: list[str],
    ) -> str:
        with self.new_session() as session:
            repo = ChatRepository(session)
            message = repo.add_message(
                ChatMessage(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=finished.text,
                    # Memory and compaction notes are shown with the reply but kept out of
                    # `content`, so Claude never sees them in the history.
                    parts=[{"type": "note", "text": note} for note in notes]
                    + [_part_dict(p) for p in finished.parts],
                    duration_ms=duration_ms,
                    usage=usage.model_dump() if usage else None,
                    calls=[asdict(c) for c in calls],
                )
            )
            repo.commit()
            return message.id


def _memory_note(compaction: CompactionResult) -> str:
    """E.g. "Memory updated from 2 earlier chats: 3 added, 1 changed." """
    chats = f"{compaction.conversations} earlier chat{'s' if compaction.conversations > 1 else ''}"
    changes = [
        f"{count} {label}"
        for count, label in (
            (compaction.added, "added"),
            (compaction.updated, "changed"),
            (compaction.deleted, "removed"),
        )
        if count
    ]
    if not changes:
        return f"Checked {chats} for memory: nothing new to remember."
    return f"Memory updated from {chats}: {', '.join(changes)}."


def _thousands(tokens: int) -> str:
    """E.g. 6800 -> "6.8k"."""
    return f"{tokens / 1000:.1f}k"


def _unsummarized(conversation: Conversation) -> list[HistoryMessage]:
    """The messages after the summary: the ones Claude sees word for word."""
    through = conversation.summarized_through
    return [
        HistoryMessage(
            role=m.role,  # type: ignore[arg-type]
            content=m.content,
            created_at=m.created_at,
            calls=m.calls,
        )
        for m in conversation.messages
        if through is None or m.created_at > through
    ]


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


def _merge_consecutive(history: Sequence[HistoryMessage]) -> list[HistoryMessage]:
    """A failed reply leaves two user messages in a row; join them into one turn."""
    merged: list[HistoryMessage] = []
    for message in history:
        if merged and merged[-1].role == message.role:
            merged[-1] = replace(message, content=f"{merged[-1].content}\n\n{message.content}")
        else:
            merged.append(message)
    return merged
