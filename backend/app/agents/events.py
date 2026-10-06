"""What a running agent reports. The chat service turns these into SSE events."""

from dataclasses import dataclass
from typing import Literal

from .models import TokenUsage

PartType = Literal["thinking", "text"]  # what Claude streams


@dataclass
class ReplyPart:
    """One stretch of thinking or text in a reply. A reply that uses tools can switch between
    them several times, so its parts are kept in the order Claude produced them. Text written
    just before a tool call becomes a "note": progress, not part of the answer."""

    type: Literal["thinking", "text", "note"]
    text: str


@dataclass
class ToolPart:
    """A tool the agent called, in its place among the reply's other parts."""

    agent: str
    tool: str
    ok: bool | None = None  # None while the tool is running
    duration_ms: int | None = None


@dataclass(frozen=True)
class TextDelta:
    text: str


@dataclass(frozen=True)
class ThinkingDelta:
    text: str


@dataclass(frozen=True)
class ToolStarted:
    agent: str
    tool: str


@dataclass(frozen=True)
class ToolFinished:
    agent: str
    tool: str
    ok: bool
    duration_ms: int


@dataclass(frozen=True)
class UsageUpdated:
    """Running token totals for the whole message, sent after each Claude call and tool call."""

    usage: TokenUsage


@dataclass(frozen=True)
class RunFinished:
    text: str  # the text parts only, which is what goes back into the conversation history
    input_tokens: int
    output_tokens: int
    parts: list[ReplyPart | ToolPart]


AgentEvent = TextDelta | ThinkingDelta | ToolStarted | ToolFinished | UsageUpdated | RunFinished
