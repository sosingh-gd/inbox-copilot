from enum import StrEnum
from typing import Annotated, Literal

from pydantic import AwareDatetime, Field

from app.core.schemas import ApiModel


class ModelChoice(StrEnum):
    sonnet = "sonnet"
    haiku = "haiku"


class ReasoningLevel(StrEnum):
    fast = "fast"
    balanced = "balanced"
    deep = "deep"


MessageRole = Literal["user", "assistant"]


class ChatSettings(ApiModel):
    model: ModelChoice = ModelChoice.sonnet
    reasoning: ReasoningLevel = ReasoningLevel.balanced


class ConversationCreate(ChatSettings):
    """Start an empty conversation. Its first message gives it a title."""


class ChatRunRequest(ApiModel):
    """Send one user message. Model and reasoning may change from message to message."""

    content: str = Field(min_length=1, max_length=20_000)
    model: ModelChoice = ModelChoice.sonnet
    reasoning: ReasoningLevel = ReasoningLevel.balanced


class Usage(ApiModel):
    """Tokens spent on one message, sub-agents included. `input_tokens` excludes cached
    input, which is counted in the two cache fields."""

    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int


class TextPart(ApiModel):
    """A stretch of Claude's thinking, answer text, or a progress note (text written just
    before a tool call)."""

    type: Literal["thinking", "text", "note"]
    text: str


class ToolPart(ApiModel):
    """A tool Claude called while replying."""

    type: Literal["tool"] = "tool"
    agent: str
    tool: str
    ok: bool | None = None  # None while it is running
    duration_ms: int | None = None


MessagePart = Annotated[TextPart | ToolPart, Field(discriminator="type")]


class InputSection(ApiModel):
    """One piece of what a Claude call sent: the system prompt, a tool definition, or a
    block of a message. `tokens` is an estimate: the call's real input tokens, shared out
    by each section's size."""

    kind: Literal["system", "tool_definition", "text", "thinking", "tool_use", "tool_result"]
    label: str
    text: str  # very long sections are cut short; `chars` is the full length
    chars: int
    tokens: int


class ModelCall(ApiModel):
    """One request to Claude while replying, by the orchestrator or a specialist agent."""

    agent: str
    turn: int
    model: str
    input_tokens: int  # all input, cached included
    cache_read_tokens: int
    output_tokens: int
    sections: list[InputSection]


class MessageRead(ApiModel):
    id: str
    role: MessageRole
    content: str
    # Assistant messages only: thinking, notes, tool calls and text in the order they happened.
    # `content` holds just the text, for the conversation history.
    parts: list[MessagePart] | None = None
    # Set on assistant messages only: how long the reply took and the tokens it used.
    duration_ms: int | None = None
    usage: Usage | None = None
    # Assistant messages only: every Claude call made for the reply, with what it sent.
    calls: list[ModelCall] | None = None
    created_at: AwareDatetime


class ConversationSummary(ChatSettings):
    id: str
    title: str
    updated_at: AwareDatetime


class ConversationDetail(ConversationSummary):
    messages: list[MessageRead]
