"""The Claude call that folds a conversation's older messages into its summary. The service only
knows the ConversationSummarizer protocol, so a fake can stand in for Claude without touching it.
"""

import logging
from datetime import date
from typing import Protocol

import anthropic
from anthropic import AsyncAnthropic
from anthropic.types import MessageParam

from app.agents.models import HAIKU, AgentError, TokenUsage
from app.agents.prompts import render_prompt
from app.agents.trace import describe_input

logger = logging.getLogger(__name__)

AGENT_NAME = "context"  # how compaction calls are labelled in a reply's token breakdown
REQUEST_TIMEOUT_SECONDS = 60
MAX_RETRIES = 2
MAX_TOKENS = 2048


class ConversationSummarizer(Protocol):
    async def summarize(
        self,
        previous_summary: str | None,
        transcript: str,
        max_words: int,
        today: date,
        usage: TokenUsage,
    ) -> str:
        """Fold the transcript into the previous summary and return the new summary, of at most
        about `max_words` words. Adds the tokens spent, and a record of the call, to `usage`.
        Raises AgentError when it fails."""
        ...


class ClaudeSummarizer:
    def __init__(self, client: AsyncAnthropic) -> None:
        self._client = client.with_options(timeout=REQUEST_TIMEOUT_SECONDS, max_retries=MAX_RETRIES)

    async def summarize(
        self,
        previous_summary: str | None,
        transcript: str,
        max_words: int,
        today: date,
        usage: TokenUsage,
    ) -> str:
        system = render_prompt(
            "context_compactor", today=today.isoformat(), max_words=str(max_words)
        )
        messages: list[MessageParam] = [
            {
                "role": "user",
                "content": f"<previous_summary>\n{previous_summary or '(none yet)'}\n"
                f"</previous_summary>\n\n<messages_to_fold>\n{transcript}\n</messages_to_fold>",
            }
        ]
        sections = describe_input(system, [], messages)
        try:
            response = await self._client.messages.create(
                model=HAIKU, max_tokens=MAX_TOKENS, system=system, messages=messages
            )
        except anthropic.APIError as exc:
            logger.exception("context compaction call failed")
            raise AgentError("llm_error", "Claude could not be reached.") from exc

        usage.record(AGENT_NAME, response.model, response.usage, sections)
        summary = "".join(b.text for b in response.content if b.type == "text").strip()
        if not summary or response.stop_reason not in ("end_turn", "max_tokens"):
            logger.warning("context compaction returned no summary stop=%s", response.stop_reason)
            raise AgentError("compaction_failed", "The conversation could not be summarized.")
        return summary
