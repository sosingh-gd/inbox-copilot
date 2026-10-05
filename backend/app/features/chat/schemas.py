from enum import StrEnum
from typing import Literal

from pydantic import AwareDatetime, Field

from app.core.schemas import ApiModel


class AgentKind(StrEnum):
    inbox = "inbox"
    calendar = "calendar"
    general = "general"


class ModelChoice(StrEnum):
    sonnet = "sonnet"
    haiku = "haiku"


class ReasoningLevel(StrEnum):
    fast = "fast"
    balanced = "balanced"
    deep = "deep"


MessageRole = Literal["user", "assistant"]


class ChatSettings(ApiModel):
    agent: AgentKind = AgentKind.inbox
    model: ModelChoice = ModelChoice.sonnet
    reasoning: ReasoningLevel = ReasoningLevel.balanced


class ConversationCreate(ChatSettings):
    """Start an empty conversation. Its first message gives it a title."""


class ChatRunRequest(ApiModel):
    """Send one user message. The agent is fixed per conversation; model and reasoning may
    change from message to message."""

    content: str = Field(min_length=1, max_length=20_000)
    model: ModelChoice = ModelChoice.sonnet
    reasoning: ReasoningLevel = ReasoningLevel.balanced


class MessageRead(ApiModel):
    id: str
    role: MessageRole
    content: str
    created_at: AwareDatetime


class ConversationSummary(ChatSettings):
    id: str
    title: str
    updated_at: AwareDatetime


class ConversationDetail(ConversationSummary):
    messages: list[MessageRead]
