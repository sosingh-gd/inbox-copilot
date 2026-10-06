import asyncio
import logging

from pydantic import BaseModel, Field

from app.agents.models import Tool

from .sources import WeatherSource

logger = logging.getLogger(__name__)


class GetWeatherArgs(BaseModel):
    city: str | None = Field(
        default=None,
        description="City name, optionally with country (e.g. 'Paris, France'). "
        "Omit to use the user's home location.",
    )
    days: int = Field(default=7, ge=1, le=7, description="How many days ahead, from today.")


def weather_tools(source: WeatherSource, home_location: str) -> tuple[Tool, ...]:
    async def get_weather(args: GetWeatherArgs) -> str:
        city = args.city or home_location
        forecast = await asyncio.to_thread(source.get_forecast, city, args.days)
        logger.info(
            "get_weather source=%s city=%r days=%d location=%r",
            type(source).__name__,
            args.city,
            args.days,
            forecast.location,
        )
        return forecast.model_dump_json()

    return (
        Tool(
            name="get_weather",
            description="Daily forecast (summary, max/min temperature, max precipitation "
            "probability, max wind speed) for a city, from today up to 7 days ahead.",
            input_model=GetWeatherArgs,
            handler=get_weather,
        ),
    )
