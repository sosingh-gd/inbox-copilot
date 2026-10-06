from datetime import date

from .models import SONNET, AgentDefinition
from .prompts import render_prompt
from .runner import AgentRunner


def build_orchestrator(
    runner: AgentRunner, specialists: list[AgentDefinition], today: date
) -> AgentDefinition:
    """The `general` agent: plans the answer and delegates to each specialist as a tool."""
    return AgentDefinition(
        name="general",
        description="General-purpose assistant that plans and combines the specialists' work.",
        system_prompt=render_prompt("orchestrator", today=today.isoformat()),
        tools=tuple(runner.as_tool(agent) for agent in specialists),
        model=SONNET,
    )
