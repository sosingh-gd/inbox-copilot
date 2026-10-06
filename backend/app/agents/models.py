"""Building blocks shared by every agent."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from anthropic.types import ToolUnionParam
from pydantic import BaseModel

SONNET = "claude-sonnet-5-5"
HAIKU = "claude-haiku-4-5"


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


class AgentError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
