"""The Claude call that turns conversations into facts. The service only knows the
FactExtractor protocol, so a fake can stand in for Claude without touching it.
"""

import logging
from datetime import date
from typing import Protocol

import anthropic
from anthropic import AsyncAnthropic
from anthropic.types import MessageParam

from app.agents.models import HAIKU, AgentError, TokenUsage
from app.agents.prompts import render_prompt
from app.agents.trace import ModelCall, assign_tokens, describe_input

from .schemas import FactOperation, FactOperations

logger = logging.getLogger(__name__)

AGENT_NAME = "memory"  # how compaction calls are labelled in a reply's token breakdown
REQUEST_TIMEOUT_SECONDS = 60
MAX_RETRIES = 2
MAX_TOKENS = 4096


class FactExtractor(Protocol):
    async def extract(
        self, known_facts: str, transcript: str, today: date, usage: TokenUsage
    ) -> list[FactOperation]:
        """Decide how the facts change after a conversation. Adds the tokens spent, and a
        record of the call, to `usage`. Raises AgentError when the call fails."""
        ...


class ClaudeFactExtractor:
    def __init__(self, client: AsyncAnthropic) -> None:
        self._client = client.with_options(timeout=REQUEST_TIMEOUT_SECONDS, max_retries=MAX_RETRIES)

    async def extract(
        self, known_facts: str, transcript: str, today: date, usage: TokenUsage
    ) -> list[FactOperation]:
        system = render_prompt("memory_compactor", today=today.isoformat())
        messages: list[MessageParam] = [
            {
                "role": "user",
                "content": f"<known_facts>\n{known_facts}\n</known_facts>\n\n"
                f"<conversation>\n{transcript}\n</conversation>",
            }
        ]
        sections = describe_input(system, [], messages)
        try:
            response = await self._client.messages.parse(
                model=HAIKU,
                max_tokens=MAX_TOKENS,
                system=system,
                messages=messages,
                output_format=FactOperations,
            )
        except anthropic.APIError as exc:
            logger.exception("memory compaction call failed")
            raise AgentError("llm_error", "Claude could not be reached.") from exc

        usage.add(response.usage)
        cache_read = response.usage.cache_read_input_tokens or 0
        cache_write = response.usage.cache_creation_input_tokens or 0
        call_input = response.usage.input_tokens + cache_read + cache_write
        assign_tokens(sections, call_input, cache_read, cache_write)
        usage.calls.append(
            ModelCall(
                agent=AGENT_NAME,
                turn=len([c for c in usage.calls if c.agent == AGENT_NAME]) + 1,
                model=response.model,
                input_tokens=call_input,
                cache_read_tokens=cache_read,
                cache_write_tokens=cache_write,
                output_tokens=response.usage.output_tokens,
                sections=sections,
            )
        )

        parsed = response.parsed_output
        if parsed is None:
            logger.warning("memory compaction returned no operations stop=%s", response.stop_reason)
            raise AgentError("memory_failed", "Memory could not be updated.")
        return parsed.operations
