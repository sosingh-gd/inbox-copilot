"""The chat service talks to an LLM only through the ChatModel protocol.

ClaudeChatModel is the real implementation; tests use a fake. Provider-specific details
(model IDs, effort, thinking, fallbacks, SDK errors) stay in this file.
"""

from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
from typing import Any, Literal, Protocol

import anthropic
from anthropic import AsyncAnthropic

from .schemas import ModelChoice, ReasoningLevel


@dataclass(frozen=True)
class LlmMessage:
    role: Literal["user", "assistant"]
    content: str


@dataclass(frozen=True)
class TextChunk:
    text: str


@dataclass(frozen=True)
class Completion:
    """Always the last item of a stream."""

    refused: bool
    input_tokens: int
    output_tokens: int


LlmEvent = TextChunk | Completion


class LlmError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class ChatModel(Protocol):
    def stream(
        self,
        *,
        system: str,
        messages: Sequence[LlmMessage],
        model: ModelChoice,
        reasoning: ReasoningLevel,
    ) -> AsyncIterator[LlmEvent]: ...


MODEL_IDS: dict[ModelChoice, str] = {
    ModelChoice.sonnet: "claude-sonnet-5-5",
    ModelChoice.haiku: "claude-haiku-4-5",
}
MAX_TOKENS = 64_000

# Sonnet 5.5 always uses adaptive thinking; effort controls how much it thinks.
SONNET_EFFORT: dict[ReasoningLevel, Literal["low", "medium", "high"]] = {
    ReasoningLevel.fast: "low",
    ReasoningLevel.balanced: "medium",
    ReasoningLevel.deep: "high",
}
# Haiku 4.5 has no effort setting; "deep" turns on extended thinking with a token budget.
HAIKU_DEEP_THINKING_BUDGET = 8_000


def _request_options(model: ModelChoice, reasoning: ReasoningLevel) -> dict[str, Any]:
    if model is ModelChoice.sonnet:
        return {
            "output_config": {"effort": SONNET_EFFORT[reasoning]},
            # If a safety classifier declines, the API retries on a recommended fallback
            # model inside the same stream instead of returning the refusal.
            "betas": ["server-side-fallback-2026-07-01"],
            "fallbacks": "default",
        }
    if reasoning is ReasoningLevel.deep:
        return {"thinking": {"type": "enabled", "budget_tokens": HAIKU_DEEP_THINKING_BUDGET}}
    return {}


class ClaudeChatModel:
    def __init__(self, client: AsyncAnthropic) -> None:
        self._client = client

    async def stream(
        self,
        *,
        system: str,
        messages: Sequence[LlmMessage],
        model: ModelChoice,
        reasoning: ReasoningLevel,
    ) -> AsyncIterator[LlmEvent]:
        try:
            async with self._client.beta.messages.stream(
                model=MODEL_IDS[model],
                max_tokens=MAX_TOKENS,
                system=system,
                messages=[{"role": m.role, "content": m.content} for m in messages],
                cache_control={"type": "ephemeral"},  # cache the growing conversation prefix
                **_request_options(model, reasoning),
            ) as stream:
                async for text in stream.text_stream:
                    yield TextChunk(text)
                final = await stream.get_final_message()
        except anthropic.RateLimitError as exc:
            raise LlmError("rate_limited", "Claude is busy right now. Try again shortly.") from exc
        except anthropic.APIStatusError as exc:
            raise LlmError("llm_error", f"Claude returned an error ({exc.status_code}).") from exc
        except anthropic.APIConnectionError as exc:
            raise LlmError("llm_unreachable", "Claude could not be reached.") from exc

        yield Completion(
            refused=final.stop_reason == "refusal",
            input_tokens=final.usage.input_tokens,
            output_tokens=final.usage.output_tokens,
        )
