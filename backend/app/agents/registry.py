from collections.abc import AsyncIterator
from datetime import date

from anthropic.types import MessageParam

from app.core.config import Settings
from app.features.calendar.sources import CalendarSource
from app.features.emails.sources import EmailSource
from app.features.weather.sources import WeatherSource

from .calendar_agent import build_calendar_agent
from .email_agent import build_email_agent
from .events import AgentEvent
from .models import AgentDefinition, AgentError
from .orchestrator import build_orchestrator
from .runner import AgentRunner
from .weather_agent import build_weather_agent


class AgentRegistry:
    """The agents for one request. Built per request because the tools use the
    signed-in user's Google credentials."""

    def __init__(
        self,
        runner: AgentRunner,
        email_source: EmailSource,
        calendar_source: CalendarSource,
        weather_source: WeatherSource,
        settings: Settings,
        today: date | None = None,
    ) -> None:
        today = today or date.today()
        specialists = [
            build_email_agent(email_source, today),
            build_calendar_agent(calendar_source, today),
            build_weather_agent(weather_source, settings),
        ]
        general = build_orchestrator(runner, specialists, today)
        self._runner = runner
        self._agents = {a.name: a for a in (*specialists, general)}

    def get(self, name: str) -> AgentDefinition:
        try:
            return self._agents[name]
        except KeyError:
            raise AgentError("unknown_agent", f"No agent named {name}.") from None

    def stream(self, name: str, messages: list[MessageParam]) -> AsyncIterator[AgentEvent]:
        return self._runner.stream(self.get(name), messages)
