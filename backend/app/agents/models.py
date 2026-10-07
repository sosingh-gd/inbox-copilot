"""Building blocks shared by every agent."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Literal

from anthropic.types import ToolUnionParam, Usage
from pydantic import BaseModel

from .trace import ModelCall

SONNET = "claude-sonnet-5-5"
HAIKU = "claude-haiku-4-5"

# How hard Claude thinks before answering. None keeps the model's own default.
Effort = Literal["low", "medium", "high", "xhigh"]


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    input_model: type[BaseModel]  # validates Claude's arguments and produces the JSON schema
    handler: Callable[[Any], Awaitable[str]]

    def to_api(self) -> ToolUnionParam:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_model.model_json_schema(),
        }


@dataclass(frozen=True)
class AgentDefinition:
    name: str
    description: str  # shown to the orchestrator when this agent is used as a tool
    system_prompt: str
    tools: tuple[Tool, ...]
    model: str
    max_turns: int = 8
    max_tokens: int = 4096
    effort: Effort | None = None
    # Facts remembered from earlier conversations, sent as a second system block.
    memory: str | None = None
    # Mark the prompt for Claude's prompt cache, so unchanged input is read back cheaply.
    prompt_caching: bool = False


@dataclass
class TokenUsage:
    """Tokens spent on one user message, sub-agents included. Every run that works on the
    message adds to the same instance, along with a record of each Claude call it made."""

    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    calls: list[ModelCall] = field(default_factory=list)

    def add(self, usage: Usage) -> None:
        self.input_tokens += usage.input_tokens
        self.output_tokens += usage.output_tokens
        self.cache_read_tokens += usage.cache_read_input_tokens or 0
        self.cache_write_tokens += usage.cache_creation_input_tokens or 0


class AgentError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
