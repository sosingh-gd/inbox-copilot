from collections.abc import AsyncIterator
from dataclasses import replace
from datetime import date

from anthropic.types import MessageParam

from app.core.config import Settings
from app.features.calendar.sources import CalendarSource
from app.features.emails.sources import EmailSource
from app.features.weather.sources import WeatherSource

from .calendar_agent import build_calendar_agent
from .email_agent import build_email_agent
from .events import AgentEvent
from .models import Effort, TokenUsage
from .orchestrator import build_orchestrator
from .runner import AgentRunner
from .weather_agent import build_weather_agent


class AgentRegistry:
    """The agents for one request. Built per request because the tools use the
    signed-in user's Google credentials. Every chat goes to the orchestrator, which
    decides which specialists to call."""

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
        self._runner = runner
        self._usage = TokenUsage()  # one registry per request, so one total per message
        self._orchestrator = build_orchestrator(runner, specialists, today, self._usage)

    @property
    def usage(self) -> TokenUsage:
        """This message's token totals. Work done before the agents run (memory compaction)
        adds to it too, so the reply's totals include it."""
        return self._usage

    def stream(
        self, messages: list[MessageParam], model: str, effort: Effort, memory: str | None = None
    ) -> AsyncIterator[AgentEvent]:
        """Run the orchestrator with the model and effort chosen for this message, and the
        facts remembered from earlier conversations. The specialists keep their own fixed
        settings and never see memory."""
        orchestrator = replace(self._orchestrator, model=model, effort=effort, memory=memory)
        return self._runner.stream(orchestrator, messages, self._usage)
