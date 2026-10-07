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
        self._today = today or date.today()
        self._specialists = [
            build_email_agent(email_source, self._today),
            build_calendar_agent(calendar_source, self._today),
            build_weather_agent(weather_source, settings),
        ]
        self._runner = runner
        self._usage = TokenUsage()  # one registry per request, so one total per message

    @property
    def usage(self) -> TokenUsage:
        """This message's token totals. Work done before the agents run (memory compaction)
        adds to it too, so the reply's totals include it."""
        return self._usage

    def stream(
        self,
        messages: list[MessageParam],
        model: str,
        effort: Effort,
        memory: str | None = None,
        prompt_caching: bool = False,
        summary: str | None = None,
    ) -> AsyncIterator[AgentEvent]:
        """Run the orchestrator with the model and effort chosen for this message, the
        facts remembered from earlier conversations, and the summary of this conversation's
        older messages. The specialists keep their own fixed model and effort and never see
        memory or the summary. Prompt caching applies to every agent, so a
        reply's token counts can be compared with caching on and off."""
        specialists = [replace(s, prompt_caching=prompt_caching) for s in self._specialists]
        orchestrator = replace(
            build_orchestrator(self._runner, specialists, self._today, self._usage),
            model=model,
            effort=effort,
            memory=memory,
            summary=summary,
            prompt_caching=prompt_caching,
        )
        return self._runner.stream(orchestrator, messages, self._usage)
