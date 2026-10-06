"""The one tool-use loop every agent runs on."""

import logging
import time
from collections.abc import AsyncIterator
from typing import Any

import anthropic
from anthropic import AsyncAnthropic
from anthropic.types import MessageParam, ToolResultBlockParam
from pydantic import BaseModel, Field

from .events import AgentEvent, RunFinished, TextDelta, ToolFinished, ToolStarted
from .models import AgentDefinition, AgentError, Tool

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT_SECONDS = 60
MAX_RETRIES = 2
TOKEN_BUDGET = 12_000  # per user message, summed over all turns


class DelegateArgs(BaseModel):
    """Input schema for the tool created by `AgentRunner.as_tool`."""

    task: str = Field(description="A complete, self-contained task, including any dates.")


class AgentRunner:
    """Runs any `AgentDefinition` through Claude's tool-use loop."""

    def __init__(self, client: AsyncAnthropic) -> None:
        """Keep a copy of the client with this runner's timeout and retry settings."""
        self._client = client.with_options(timeout=REQUEST_TIMEOUT_SECONDS, max_retries=MAX_RETRIES)

    async def stream(
        self, agent: AgentDefinition, messages: list[MessageParam]
    ) -> AsyncIterator[AgentEvent]:
        """Run the agent's tool-use loop and yield events as they happen.

        Each turn sends the conversation to Claude and streams its text out as
        `TextDelta` events. If Claude asks for tools, they are run (emitting
        `ToolStarted`/`ToolFinished`), their results are added to the
        conversation, and the loop goes round again. When Claude answers without
        asking for a tool, a single `RunFinished` with the full text and token
        totals ends the run. Raises `AgentError` on API failures, refusals, an
        exceeded token budget, or when `agent.max_turns` runs out.
        """
        tools = {t.name: t for t in agent.tools}  # lookup by the name Claude uses
        messages = list(messages)  # copy so the caller's list is not modified
        texts: list[str] = []
        input_tokens = output_tokens = 0
        run_started = time.perf_counter()
        logger.info(
            "agent=%s run_started model=%s max_turns=%d max_tokens=%d tools=%s messages=%d",
            agent.name,
            agent.model,
            agent.max_turns,
            agent.max_tokens,
            [t.name for t in agent.tools],
            len(messages),
        )

        for turn in range(1, agent.max_turns + 1):
            turn_started = time.perf_counter()
            try:
                async with self._client.messages.stream(
                    model=agent.model,
                    max_tokens=agent.max_tokens,
                    system=agent.system_prompt,
                    tools=[t.to_api() for t in agent.tools],
                    messages=messages,
                ) as stream:
                    async for text in stream.text_stream:
                        texts.append(text)
                        yield TextDelta(text)
                    response = await stream.get_final_message()
                    request_id = stream.request_id  # only the stream has it, not the message
            except anthropic.APIError as exc:
                logger.exception("Claude call failed for agent=%s", agent.name)
                raise AgentError("llm_error", "Claude could not be reached.") from exc

            usage = response.usage
            logger.info(
                "agent=%s turn=%d/%d model=%s stop_reason=%s input_tokens=%d output_tokens=%d "
                "cache_read=%s cache_write=%s tool_calls=%s duration_ms=%d request_id=%s",
                agent.name,
                turn,
                agent.max_turns,
                response.model,
                response.stop_reason,
                usage.input_tokens,
                usage.output_tokens,
                usage.cache_read_input_tokens,
                usage.cache_creation_input_tokens,
                [b.name for b in response.content if b.type == "tool_use"],
                int((time.perf_counter() - turn_started) * 1000),
                request_id,
            )

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
                logger.warning("agent=%s refused turn=%d", agent.name, turn)
                raise AgentError("refused", "Claude declined to answer this request.")
            # Any stop reason other than tool_use means Claude has given its answer.
            if response.stop_reason != "tool_use":
                logger.info(
                    "agent=%s run_finished turns=%d input_tokens=%d output_tokens=%d "
                    "answer_chars=%d duration_ms=%d",
                    agent.name,
                    turn,
                    input_tokens,
                    output_tokens,
                    len("".join(texts)),
                    int((time.perf_counter() - run_started) * 1000),
                )
                yield RunFinished("".join(texts), input_tokens, output_tokens)
                return
            # If we reach here, it means the loop will continue for another turn.
            # The loop will continue for another turn, so we don't return here.

            # Claude asked for tools: record its turn, run each requested tool,
            # and send all results back together in one user message.
            messages.append({"role": "assistant", "content": response.content})
            results: list[ToolResultBlockParam] = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                yield ToolStarted(agent.name, block.name)
                result, ok, duration_ms = await self._call_tool(
                    agent.name, tools.get(block.name), block
                )
                yield ToolFinished(agent.name, block.name, ok, duration_ms)
                results.append(result)
            messages.append({"role": "user", "content": results})

        logger.warning("agent=%s too_many_turns max_turns=%d", agent.name, agent.max_turns)
        raise AgentError("too_many_turns", f"The {agent.name} agent did not finish in time.")

    async def run(self, agent: AgentDefinition, messages: list[MessageParam]) -> str:
        """Run without streaming and return only the final text (used for sub-agents).

        Consumes `stream` and ignores every event except `RunFinished`.
        """
        async for event in self.stream(agent, messages):
            if isinstance(event, RunFinished):
                return event.text
        raise AgentError("incomplete", f"The {agent.name} agent ended unexpectedly.")

    def as_tool(self, agent: AgentDefinition) -> Tool:
        """Let another agent call this agent like any other tool.

        The returned tool is named `ask_<name>_agent` and takes one `task`
        string. Calling it starts a fresh conversation with this agent (it does
        not see the caller's history) and returns the agent's final answer.
        """

        async def handler(args: DelegateArgs) -> str:
            logger.info("delegating to agent=%s task=%r", agent.name, args.task)
            return await self.run(agent, [{"role": "user", "content": args.task}])

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
        # Log only the result size: tool results hold email/calendar content.
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
