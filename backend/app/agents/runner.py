"""The one tool-use loop every agent runs on."""

import logging
import time
from collections.abc import AsyncIterator
from dataclasses import replace
from typing import Any

import anthropic
from anthropic import AsyncAnthropic, Omit, omit
from anthropic.lib.streaming import ParsedMessageStreamEvent
from anthropic.types import (
    MessageParam,
    OutputConfigParam,
    ThinkingConfigParam,
    ToolResultBlockParam,
)
from pydantic import BaseModel, Field

from .events import (
    AgentEvent,
    PartType,
    ReplyPart,
    RunFinished,
    TextDelta,
    ThinkingDelta,
    ToolFinished,
    ToolPart,
    ToolStarted,
    UsageUpdated,
)
from .models import HAIKU, AgentDefinition, AgentError, Effort, TokenUsage, Tool

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT_SECONDS = 60
MAX_RETRIES = 2
TOKEN_BUDGET = 60_000  # per user message, summed over all turns (thinking counts as output)

# Haiku 4.5 has no `effort` setting; it thinks within a fixed token budget instead.
HAIKU_THINKING_BUDGETS: dict[Effort, int] = {"medium": 2_048, "high": 8_192, "xhigh": 8_192}


class DelegateArgs(BaseModel):
    """Input schema for the tool created by `AgentRunner.as_tool`."""

    task: str = Field(description="A complete, self-contained task, including any dates.")


class AgentRunner:
    """Runs any `AgentDefinition` through Claude's tool-use loop."""

    def __init__(self, client: AsyncAnthropic) -> None:
        """Keep a copy of the client with this runner's timeout and retry settings."""
        self._client = client.with_options(timeout=REQUEST_TIMEOUT_SECONDS, max_retries=MAX_RETRIES)

    async def stream(
        self,
        agent: AgentDefinition,
        messages: list[MessageParam],
        usage: TokenUsage | None = None,
    ) -> AsyncIterator[AgentEvent]:
        """Run the agent's tool-use loop and yield events as they happen.

        Each turn sends the conversation to Claude and streams its thinking and
        text out as `ThinkingDelta` and `TextDelta` events. If Claude asks for tools, they are run (emitting
        `ToolStarted`/`ToolFinished`), their results are added to the
        conversation, and the loop goes round again. When Claude answers without
        asking for a tool, a single `RunFinished` with the full text and token
        totals ends the run. Raises `AgentError` on API failures, refusals, an
        exceeded token budget, or when `agent.max_turns` runs out.

        Tokens are added to `usage` (shared with any sub-agents this run calls)
        and its totals are reported as `UsageUpdated` events.
        """
        usage = usage if usage is not None else TokenUsage()
        tools = {t.name: t for t in agent.tools}  # lookup by the name Claude uses
        messages = list(messages)  # copy so the caller's list is not modified
        parts: list[ReplyPart | ToolPart] = []
        thinking, output_config, max_tokens = _reasoning_params(agent)
        input_tokens = output_tokens = 0
        run_started = time.perf_counter()
        logger.info(
            "agent=%s run_started model=%s effort=%s max_turns=%d max_tokens=%d tools=%s "
            "messages=%d",
            agent.name,
            agent.model,
            agent.effort,
            agent.max_turns,
            max_tokens,
            [t.name for t in agent.tools],
            len(messages),
        )

        for turn in range(1, agent.max_turns + 1):
            turn_started = time.perf_counter()
            try:
                async with self._client.messages.stream(
                    model=agent.model,
                    max_tokens=max_tokens,
                    thinking=thinking,
                    output_config=output_config,
                    system=agent.system_prompt,
                    tools=[t.to_api() for t in agent.tools],
                    messages=messages,
                ) as stream:
                    async for event in stream:
                        piece = _reply_piece(event, parts)
                        if piece is None:
                            continue
                        kind, text = piece
                        _add_to_parts(parts, kind, text)
                        yield ThinkingDelta(text) if kind == "thinking" else TextDelta(text)
                    response = await stream.get_final_message()
                    request_id = stream.request_id  # only the stream has it, not the message
            except anthropic.APIError as exc:
                logger.exception("Claude call failed for agent=%s", agent.name)
                raise AgentError("llm_error", "Claude could not be reached.") from exc

            turn_usage = response.usage
            logger.info(
                "agent=%s turn=%d/%d model=%s stop_reason=%s blocks=[%s] input_tokens=%d "
                "output_tokens=%d cache_read=%s cache_write=%s duration_ms=%d request_id=%s",
                agent.name,
                turn,
                agent.max_turns,
                response.model,
                response.stop_reason,
                _describe_blocks(response.content),
                turn_usage.input_tokens,
                turn_usage.output_tokens,
                turn_usage.cache_read_input_tokens,
                turn_usage.cache_creation_input_tokens,
                int((time.perf_counter() - turn_started) * 1000),
                request_id,
            )

            # With LOG_LEVEL=DEBUG, show what each block said. Off by default: it is email content.
            if logger.isEnabledFor(logging.DEBUG):
                for index, block in enumerate(response.content):
                    if block.type in ("thinking", "text"):
                        text = block.thinking if block.type == "thinking" else block.text
                        logger.debug(
                            "agent=%s turn=%d block=%d %s: %s",
                            agent.name,
                            turn,
                            index,
                            block.type,
                            _preview(text),
                        )

            usage.add(turn_usage)
            yield UsageUpdated(replace(usage))  # a copy, since `usage` keeps changing

            # Stop runaway loops: tokens are summed across every turn of this run.
            input_tokens += response.usage.input_tokens
            output_tokens += response.usage.output_tokens
            if input_tokens + output_tokens > TOKEN_BUDGET:
                logger.warning(
                    "agent=%s budget_exceeded total_tokens=%d budget=%d",
                    agent.name,
                    input_tokens + output_tokens,
                    TOKEN_BUDGET,
                )
                raise AgentError("budget_exceeded", "This request used too many tokens.")
            if response.stop_reason == "refusal":
                logger.warning(
                    "agent=%s refused turn=%d details=%s", agent.name, turn, response.stop_details
                )
                raise AgentError("refused", "Claude declined to answer this request.")
            if response.stop_reason == "max_tokens":
                logger.warning(
                    "agent=%s turn=%d hit max_tokens=%d: the answer is cut off",
                    agent.name,
                    turn,
                    max_tokens,
                )
            # Any stop reason other than tool_use means Claude has given its answer.
            if response.stop_reason != "tool_use":
                logger.info(
                    "agent=%s run_finished turns=%d input_tokens=%d output_tokens=%d "
                    "answer_chars=%d duration_ms=%d",
                    agent.name,
                    turn,
                    input_tokens,
                    output_tokens,
                    sum(
                        len(p.text)
                        for p in parts
                        if isinstance(p, ReplyPart) and p.type != "thinking"
                    ),
                    int((time.perf_counter() - run_started) * 1000),
                )
                # Notes stay in the history too, so the reply is never empty there.
                answer = "\n\n".join(
                    p.text for p in parts if isinstance(p, ReplyPart) and p.type != "thinking"
                )
                yield RunFinished(answer, input_tokens, output_tokens, parts)
                return

            # Claude asked for tools: record its turn (thinking blocks included, unchanged), run each requested tool,
            # and send all results back together in one user message.
            messages.append({"role": "assistant", "content": response.content})
            results: list[ToolResultBlockParam] = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                yield ToolStarted(agent.name, block.name)
                # Text just before a tool call was progress ("I'll check your calendar"), not answer.
                if parts and isinstance(parts[-1], ReplyPart) and parts[-1].type == "text":
                    parts[-1].type = "note"
                tool_part = ToolPart(agent.name, block.name)
                parts.append(tool_part)
                result, ok, duration_ms = await self._call_tool(
                    agent.name, tools.get(block.name), block
                )
                tool_part.ok, tool_part.duration_ms = ok, duration_ms
                yield ToolFinished(agent.name, block.name, ok, duration_ms)
                yield UsageUpdated(replace(usage))  # now includes any sub-agent's tokens
                results.append(result)
            messages.append({"role": "user", "content": results})

        logger.warning("agent=%s too_many_turns max_turns=%d", agent.name, agent.max_turns)
        raise AgentError("too_many_turns", f"The {agent.name} agent did not finish in time.")

    async def run(
        self,
        agent: AgentDefinition,
        messages: list[MessageParam],
        usage: TokenUsage | None = None,
    ) -> str:
        """Run without streaming and return only the final text (used for sub-agents).

        Consumes `stream` and ignores every event except `RunFinished`.
        """
        async for event in self.stream(agent, messages, usage):
            if isinstance(event, RunFinished):
                return event.text
        raise AgentError("incomplete", f"The {agent.name} agent ended unexpectedly.")

    def as_tool(self, agent: AgentDefinition, usage: TokenUsage | None = None) -> Tool:
        """Let another agent call this agent like any other tool.

        The returned tool is named `ask_<name>_agent` and takes one `task`
        string. Calling it starts a fresh conversation with this agent (it does
        not see the caller's history) and returns the agent's final answer. Its
        tokens are added to `usage`, so the caller's totals include them.
        """

        async def handler(args: DelegateArgs) -> str:
            logger.info("delegating to agent=%s task=%r", agent.name, args.task)
            return await self.run(agent, [{"role": "user", "content": args.task}], usage)

        return Tool(
            name=f"ask_{agent.name}_agent",
            description=agent.description,
            input_model=DelegateArgs,
            handler=handler,
        )

    async def _call_tool(
        self, agent_name: str, tool: Tool | None, block: Any
    ) -> tuple[ToolResultBlockParam, bool, int]:
        """Run one tool Claude asked for and build the `tool_result` block to send back.

        Validates Claude's input against the tool's Pydantic model, then calls
        the handler. Any failure (unknown tool, bad input, handler error) is
        caught and returned to Claude as an error result instead of crashing
        the run. Returns the result block, whether it succeeded, and how long
        it took in milliseconds.
        """
        started = time.perf_counter()
        logger.info(
            "agent=%s tool_started tool=%s tool_use_id=%s input=%s",
            agent_name,
            block.name,
            block.id,
            block.input,
        )
        try:
            if tool is None:
                raise ValueError(f"Unknown tool: {block.name}")
            args = tool.input_model.model_validate(block.input)
            content, is_error = await tool.handler(args), False
        except Exception as exc:  # tell Claude what went wrong so it can recover
            logger.warning("Tool %s.%s failed: %s", agent_name, block.name, exc)
            content, is_error = f"Error: {exc}", True
        duration_ms = int((time.perf_counter() - started) * 1000)
        # Log only the result size by default: tool results hold email/calendar content.
        logger.debug("tool=%s.%s result: %s", agent_name, block.name, _preview(content))
        logger.info(
            "tool=%s.%s ok=%s duration_ms=%d result_chars=%d",
            agent_name,
            block.name,
            not is_error,
            duration_ms,
            len(content),
        )
        result: ToolResultBlockParam = {
            "type": "tool_result",
            "tool_use_id": block.id,
            "content": content,
            "is_error": is_error,
        }
        return result, not is_error, duration_ms


def _describe_blocks(content: list[Any]) -> str:
    """The blocks of one response in order, e.g. "thinking(84) text(126) tool_use:get_events"."""
    described = []
    for block in content:
        if block.type == "thinking":
            described.append(f"thinking({len(block.thinking)})")
        elif block.type == "text":
            described.append(f"text({len(block.text)})")
        elif block.type == "tool_use":
            described.append(f"tool_use:{block.name}")
        else:
            described.append(block.type)
    return " ".join(described)


def _preview(text: str, limit: int = 200) -> str:
    """One line of at most `limit` characters, for DEBUG logs."""
    line = " ".join(text.split())
    return repr(line if len(line) <= limit else line[:limit] + "…")


def _reply_piece(
    event: "ParsedMessageStreamEvent[None]",  # quoted: the SDK alias only subscripts for type checkers
    parts: list[ReplyPart | ToolPart],
) -> tuple[PartType, str] | None:
    """The thinking or text that a stream event adds to the reply, if any."""
    if event.type == "thinking":
        return "thinking", event.thinking
    if event.type == "text":
        return "text", event.text
    # A new block of the same kind as the last part (say, text before and after a tool call)
    # continues that part after a blank line, so the two don't run together.
    last = parts[-1] if parts else None
    if (
        event.type == "content_block_start"
        and isinstance(last, ReplyPart)
        and last.type in ("thinking", "text")
        and event.content_block.type == last.type
    ):
        return event.content_block.type, "\n\n"
    return None


def _add_to_parts(parts: list[ReplyPart | ToolPart], kind: PartType, text: str) -> None:
    """Extend the last part if it is the same kind, otherwise start a new one."""
    last = parts[-1] if parts else None
    if isinstance(last, ReplyPart) and last.type == kind:
        last.text += text
    else:
        parts.append(ReplyPart(kind, text))


def _reasoning_params(
    agent: AgentDefinition,
) -> tuple[ThinkingConfigParam | Omit, OutputConfigParam | Omit, int]:
    """Turn the agent's effort into the API's thinking settings and a max_tokens that fits them.

    Sonnet thinks adaptively and takes `effort` directly; "summarized" makes the thinking
    readable instead of empty. Haiku needs a fixed thinking budget, and "low" means no thinking.
    """
    if agent.effort is None:
        return omit, omit, agent.max_tokens
    if agent.model == HAIKU:
        budget = HAIKU_THINKING_BUDGETS.get(agent.effort)
        if budget is None:
            return omit, omit, agent.max_tokens
        # Haiku 4.5 already returns summarized thinking, so `display` is left out.
        return {"type": "enabled", "budget_tokens": budget}, omit, agent.max_tokens + budget
    return (
        {"type": "adaptive", "display": "summarized"},
        {"effort": agent.effort},
        agent.max_tokens,
    )
