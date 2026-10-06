from typing import Annotated

from fastapi import Depends

from app.core.config import Settings, get_settings

from .sources import OpenMeteoWeatherSource, WeatherSource


def get_weather_source(settings: Annotated[Settings, Depends(get_settings)]) -> WeatherSource:
    return OpenMeteoWeatherSource(settings.weather_units)
