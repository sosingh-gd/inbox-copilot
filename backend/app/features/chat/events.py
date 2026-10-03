"""Typed SSE contract for chat runs. ChatEvent is registered in scripts/export_openapi.py so
the frontend gets it as a TypeScript discriminated union.

Every stream starts with run_started and ends with exactly one terminal event
(run_completed or run_failed).
"""

from typing import Annotated, Literal

from pydantic import Field, RootModel

from app.core.schemas import ApiModel


class RunStartedEvent(ApiModel):
    type: Literal["run_started"] = "run_started"
    conversation_id: str
    user_message_id: str


class TextDeltaEvent(ApiModel):
    type: Literal["text_delta"] = "text_delta"
    text: str


class Usage(ApiModel):
    input_tokens: int
    output_tokens: int


class RunCompletedEvent(ApiModel):
    type: Literal["run_completed"] = "run_completed"
    message_id: str
    usage: Usage | None = None


class RunFailedEvent(ApiModel):
    type: Literal["run_failed"] = "run_failed"
    code: str
    message: str


ChatEventUnion = Annotated[
    RunStartedEvent | TextDeltaEvent | RunCompletedEvent | RunFailedEvent,
    Field(discriminator="type"),
]


class ChatEvent(RootModel[ChatEventUnion]):
    """Every SSE `data:` payload on the chat stream is one of these."""
