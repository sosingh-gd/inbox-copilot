"""Typed SSE contract for chat runs. ChatEvent is registered in scripts/export_openapi.py so
the frontend gets it as a TypeScript discriminated union.

Every stream starts with run_started and ends with exactly one terminal event
(run_completed or run_failed).
"""

from typing import Annotated, Literal

from pydantic import Field, RootModel

from app.core.schemas import ApiModel

from .schemas import Usage


class RunStartedEvent(ApiModel):
    type: Literal["run_started"] = "run_started"
    conversation_id: str
    user_message_id: str


class TextDeltaEvent(ApiModel):
    type: Literal["text_delta"] = "text_delta"
    text: str


class ThinkingDeltaEvent(ApiModel):
    """A piece of Claude's summarized reasoning. It can arrive before the text and again
    between pieces of text, around tool calls."""

    type: Literal["thinking_delta"] = "thinking_delta"
    text: str


class UsageUpdatedEvent(ApiModel):
    type: Literal["usage_updated"] = "usage_updated"
    usage: Usage


class RunCompletedEvent(ApiModel):
    type: Literal["run_completed"] = "run_completed"
    message_id: str
    duration_ms: int
    usage: Usage | None = None


class RunFailedEvent(ApiModel):
    type: Literal["run_failed"] = "run_failed"
    code: str
    message: str


class ToolStartedEvent(ApiModel):
    type: Literal["tool_started"] = "tool_started"
    agent: str
    tool: str


class ToolFinishedEvent(ApiModel):
    type: Literal["tool_finished"] = "tool_finished"
    agent: str
    tool: str
    ok: bool
    duration_ms: int


ChatEventUnion = Annotated[
    RunStartedEvent
    | TextDeltaEvent
    | ThinkingDeltaEvent
    | UsageUpdatedEvent
    | RunCompletedEvent
    | RunFailedEvent
    | ToolStartedEvent
    | ToolFinishedEvent,
    Field(discriminator="type"),
]


class ChatEvent(RootModel[ChatEventUnion]):
    """Every SSE `data:` payload on the chat stream is one of these."""
