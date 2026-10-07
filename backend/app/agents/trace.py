"""A record of what each Claude call sent, so the UI can show where the input tokens go.

The API reports one input token count per call, not per section. Each section's share is
estimated from its size in characters, scaled so the sections add up to the real count.
The prompt cache works on a prefix, so the cached part of a call is its first sections:
walking them in the order Claude reads them shows which ones came from the cache.
"""

import json
from dataclasses import dataclass, field
from typing import Any, Literal

from anthropic.types import MessageParam, ToolUnionParam

SectionKind = Literal[
    "system", "memory", "tool_definition", "text", "thinking", "tool_use", "tool_result"
]

MAX_SECTION_CHARS = 50_000  # keeps one huge tool result from bloating the database


@dataclass
class InputSection:
    kind: SectionKind
    label: str  # e.g. "user", "assistant → ask_email_agent", "search_emails"
    text: str
    chars: int  # of the full text, before any truncation
    tokens: int = 0  # estimated share of the call's input tokens
    cache_read_tokens: int = 0  # the part of `tokens` read from the prompt cache
    cache_write_tokens: int = 0  # the part of `tokens` written to the prompt cache


@dataclass
class ModelCall:
    """One request to Claude: which agent sent it, what went in, and what it cost."""

    agent: str
    turn: int
    model: str
    input_tokens: int  # all input, cached or not
    cache_read_tokens: int
    output_tokens: int
    cache_write_tokens: int = 0
    prompt_caching: bool = False  # whether the call asked Claude to cache its prompt
    sections: list[InputSection] = field(default_factory=list)


def describe_input(
    system: str,
    tools: list[ToolUnionParam],
    messages: list[MessageParam],
    memory: str | None = None,
) -> list[InputSection]:
    """Split one request's input into sections, in the order Claude reads them: tools,
    then system, then messages."""
    sections = [
        _section("tool_definition", str(tool.get("name", "tool")), json.dumps(tool, indent=2))
        for tool in tools
    ]
    sections.append(_section("system", "system prompt", system))
    if memory:
        sections.append(_section("memory", "remembered facts", memory))
    tool_names: dict[str, str] = {}  # tool_use id -> tool name, to label the results
    for message in messages:
        role = message["role"]
        content = message["content"]
        if isinstance(content, str):
            sections.append(_section("text", role, content))
            continue
        for block in content:
            sections.append(_block_section(role, _as_dict(block), tool_names))
    return sections


def assign_tokens(
    sections: list[InputSection],
    input_tokens: int,
    cache_read_tokens: int = 0,
    cache_write_tokens: int = 0,
) -> None:
    """Give each section a share of the call's real input tokens, in proportion to its size.

    `input_tokens` is all of the call's input. The first `cache_read_tokens` of it were read
    from the cache and the next `cache_write_tokens` written to it, so each section's cache
    fields are how much of it falls inside those two stretches.
    """
    total_chars = sum(s.chars for s in sections) or 1
    read_end = cache_read_tokens
    write_end = cache_read_tokens + cache_write_tokens
    start = 0
    for section in sections:
        section.tokens = round(input_tokens * section.chars / total_chars)
        end = start + section.tokens
        section.cache_read_tokens = _overlap(start, end, 0, read_end)
        section.cache_write_tokens = _overlap(start, end, read_end, write_end)
        start = end


def _overlap(start: int, end: int, range_start: int, range_end: int) -> int:
    """How many tokens of [start, end) fall inside [range_start, range_end)."""
    return max(0, min(end, range_end) - max(start, range_start))


def _block_section(role: str, block: dict[str, Any], tool_names: dict[str, str]) -> InputSection:
    match block.get("type"):
        case "text":
            return _section("text", role, block.get("text", ""))
        case "thinking":
            return _section("thinking", role, block.get("thinking", ""))
        case "tool_use":
            name = block.get("name", "tool")
            tool_names[block.get("id", "")] = name
            return _section(
                "tool_use", f"{role} → {name}", json.dumps(block.get("input"), indent=2)
            )
        case "tool_result":
            content = block.get("content", "")
            if not isinstance(content, str):  # a list of content blocks
                content = "\n".join(_as_dict(c).get("text", "") for c in content)
            name = tool_names.get(block.get("tool_use_id", ""), "tool")
            return _section("tool_result", f"{name} result", content)
        case other:
            return _section("text", f"{role} ({other})", json.dumps(block, default=str))


def _section(kind: SectionKind, label: str, text: str) -> InputSection:
    shown = text if len(text) <= MAX_SECTION_CHARS else text[:MAX_SECTION_CHARS] + "\n…(cut)"
    return InputSection(kind=kind, label=label, text=shown, chars=len(text))


def _as_dict(block: Any) -> dict[str, Any]:
    """Blocks are plain dicts when we build them and SDK models when Claude returned them."""
    return block if isinstance(block, dict) else block.model_dump()
