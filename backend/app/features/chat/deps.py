from typing import Annotated

from fastapi import Depends, Request

from app.agents.registry import AgentRegistry
from app.api.deps import SessionDep
from app.core.config import Settings, get_settings
from app.db.session import session_factory
from app.features.calendar.deps import get_calendar_source
from app.features.calendar.sources import CalendarSource
from app.features.emails.deps import get_email_source
from app.features.emails.sources import EmailSource
from app.features.memory.deps import MemoryServiceDep
from app.features.weather.deps import get_weather_source
from app.features.weather.sources import WeatherSource

from .llm import ClaudeSummarizer
from .repository import ChatRepository
from .service import ChatService


def get_agent_registry(
    request: Request,
    email_source: Annotated[EmailSource, Depends(get_email_source)],
    calendar_source: Annotated[CalendarSource, Depends(get_calendar_source)],
    weather_source: Annotated[WeatherSource, Depends(get_weather_source)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AgentRegistry:
    # The AgentRunner (and its AsyncAnthropic client) is created once in the app lifespan.
    return AgentRegistry(
        request.app.state.agent_runner, email_source, calendar_source, weather_source, settings
    )


def get_chat_service(
    request: Request,
    session: SessionDep,
    agents: Annotated[AgentRegistry, Depends(get_agent_registry)],
    memory: MemoryServiceDep,
) -> ChatService:
    # The AsyncAnthropic client is created once in the app lifespan.
    summarizer = ClaudeSummarizer(request.app.state.anthropic)
    return ChatService(ChatRepository(session), agents, memory, summarizer, session_factory())


ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]
