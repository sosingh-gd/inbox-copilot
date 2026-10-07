from enum import StrEnum
from typing import Annotated, Literal

from pydantic import AwareDatetime, Field, computed_field

from app.agents.pricing import CallCost, call_cost
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
    # Ask Claude to cache the unchanged start of each prompt. Off: every call pays full price.
    prompt_caching: bool = True


class MemorySettings(ApiModel):
    # Replies see the facts remembered from earlier conversations. Fixed at creation.
    use_memory: bool = True
    # This conversation's facts are remembered for later ones. Can change at any time.
    save_to_memory: bool = True


class ConversationCreate(ChatSettings, MemorySettings):
    """Start an empty conversation. Its first message gives it a title."""


class ConversationUpdate(ApiModel):
    """Turning `save_to_memory` off forgets the facts this conversation added."""

    save_to_memory: bool


class ChatRunRequest(ApiModel):
    """Send one user message. Model, reasoning and prompt caching may change from message
    to message."""

    content: str = Field(min_length=1, max_length=20_000)
    model: ModelChoice = ModelChoice.sonnet
    reasoning: ReasoningLevel = ReasoningLevel.balanced
    prompt_caching: bool = True


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
    by each section's size. The cache is a prefix, so the first `cacheReadTokens` of the
    call were read from the cache and the next `cacheWriteTokens` were written to it; each
    section's two cache fields are its share of those, estimated the same way."""

    kind: Literal[
        "system", "memory", "tool_definition", "text", "thinking", "tool_use", "tool_result"
    ]
    label: str
    text: str  # very long sections are cut short; `chars` is the full length
    chars: int
    tokens: int
    cache_read_tokens: int = 0  # replies saved before caching was tracked have neither
    cache_write_tokens: int = 0


class ModelCall(ApiModel):
    """One request to Claude while replying, by the orchestrator or a specialist agent."""

    agent: str
    turn: int
    model: str
    input_tokens: int  # all input, cached included
    cache_read_tokens: int
    cache_write_tokens: int = 0
    output_tokens: int
    # Whether the call asked Claude to cache its prompt.
    prompt_caching: bool = False
    sections: list[InputSection]

    # Estimates from list prices, worked out when read so earlier replies get them too.
    @computed_field  # type: ignore[prop-decorator]
    @property
    def billed_input_tokens(self) -> int:
        """The input as if every token were charged at the normal input price: cache reads
        count for a fraction of a token, cache writes for 1.25."""
        return self._cost().billed_input_tokens

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cost_usd(self) -> float | None:
        """Estimated US dollars for this call. None for a model without known prices."""
        return self._cost().cost_usd

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cost_without_cache_usd(self) -> float | None:
        """What the same call would have cost with every input token at full price."""
        return self._cost().cost_without_cache_usd

    def _cost(self) -> CallCost:
        return call_cost(
            self.model,
            self.input_tokens,
            self.cache_read_tokens,
            self.cache_write_tokens,
            self.output_tokens,
        )


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


class ConversationSummary(ChatSettings, MemorySettings):
    id: str
    title: str
    updated_at: AwareDatetime


class ConversationDetail(ConversationSummary):
    messages: list[MessageRead]
