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


class ChatRunRequest(ChatSettings):
    """Send one user message. Omit conversationId to start a new conversation.

    For an existing conversation the agent stays fixed; model and reasoning may change.
    """

    conversation_id: str | None = None
    content: str = Field(min_length=1, max_length=20_000)


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
