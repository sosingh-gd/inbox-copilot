"""What a running agent reports. The chat service turns these into SSE events."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TextDelta:
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
class RunFinished:
    text: str
    input_tokens: int
    output_tokens: int


AgentEvent = TextDelta | ToolStarted | ToolFinished | RunFinished
