from datetime import date

from app.features.calendar.sources import CalendarSource
from app.features.calendar.tools import calendar_tools

from .models import HAIKU, AgentDefinition
from .prompts import render_prompt


def build_calendar_agent(source: CalendarSource, today: date) -> AgentDefinition:
    return AgentDefinition(
        name="calendar",
        description="Looks up the user's upcoming calendar events and free time.",
        system_prompt=render_prompt("calendar", today=today.isoformat()),
        tools=calendar_tools(source),
        model=HAIKU,
    )
