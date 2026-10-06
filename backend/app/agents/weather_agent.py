from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import Settings
from app.features.weather.sources import WeatherSource
from app.features.weather.tools import weather_tools

from .models import HAIKU, AgentDefinition
from .prompts import render_prompt


def build_weather_agent(
    source: WeatherSource, settings: Settings, now: datetime | None = None
) -> AgentDefinition:
    now = now or datetime.now(ZoneInfo(settings.weather_timezone))
    return AgentDefinition(
        name="weather",
        description="Answers weather questions and judges whether the weather suits a plan.",
        system_prompt=render_prompt(
            "weather",
            # The weekday helps resolve relative dates such as "Thursday".
            current_datetime=now.strftime("%A, %Y-%m-%d %H:%M"),
            home_location=settings.weather_home_location,
            user_timezone=settings.weather_timezone,
            units=settings.weather_units,
        ),
        tools=weather_tools(source, settings.weather_home_location),
        model=HAIKU,
    )
