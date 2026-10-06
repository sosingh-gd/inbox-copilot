"""Where weather forecasts come from. The service only knows the WeatherSource protocol, so
Open-Meteo can be swapped for local fake data without touching it.
"""

import json
import logging
from typing import Any, Protocol
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from app.core.errors import ExternalServiceError, NotFoundError

from .schemas import DailyForecast, Units, WeatherForecast

logger = logging.getLogger(__name__)

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
TIMEOUT_SECONDS = 10

# WMO weather interpretation codes, as documented by Open-Meteo.
WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


class WeatherSource(Protocol):
    def get_forecast(self, city: str, days: int) -> WeatherForecast: ...


class OpenMeteoWeatherSource:
    """Daily forecasts from Open-Meteo (free, no API key). Up to 16 days ahead."""

    def __init__(self, units: Units) -> None:
        self._units: Units = units

    def get_forecast(self, city: str, days: int) -> WeatherForecast:
        place = self._geocode(city)
        imperial = self._units == "imperial"
        data = _get_json(
            FORECAST_URL,
            {
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "daily": "weather_code,temperature_2m_max,temperature_2m_min,"
                "precipitation_probability_max,wind_speed_10m_max",
                "timezone": "auto",
                "forecast_days": days,
                "temperature_unit": "fahrenheit" if imperial else "celsius",
                "wind_speed_unit": "mph" if imperial else "kmh",
            },
        )
        return WeatherForecast(
            location=_place_name(place),
            latitude=place["latitude"],
            longitude=place["longitude"],
            timezone=data.get("timezone", ""),
            units=self._units,
            temperature_unit="°F" if imperial else "°C",
            wind_speed_unit="mph" if imperial else "km/h",
            days=_to_days(data.get("daily", {})),
        )

    def _geocode(self, city: str) -> dict[str, Any]:
        data = _get_json(GEOCODING_URL, {"name": city, "count": 1, "format": "json"})
        results = data.get("results") or []
        if not results:
            raise NotFoundError(f"No place called {city!r} was found.", code="city_not_found")
        place: dict[str, Any] = results[0]
        return place


def _get_json(url: str, params: dict[str, Any]) -> dict[str, Any]:
    full_url = f"{url}?{urlencode(params)}"
    try:
        # The URL is always one of the fixed https endpoints above.
        with urlopen(full_url, timeout=TIMEOUT_SECONDS) as response:  # noqa: S310
            data: dict[str, Any] = json.load(response)
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        logger.warning("Open-Meteo request failed: %s", exc)
        raise ExternalServiceError(
            "The weather service could not be reached.", code="weather_api_error"
        ) from exc
    return data


def _place_name(place: dict[str, Any]) -> str:
    parts = [place.get("name"), place.get("admin1"), place.get("country")]
    return ", ".join(p for p in parts if p)


def _to_days(daily: dict[str, Any]) -> list[DailyForecast]:
    return [
        DailyForecast(
            date=day,
            summary=WEATHER_CODES.get(daily["weather_code"][i], "Unknown"),
            temperature_max=daily["temperature_2m_max"][i],
            temperature_min=daily["temperature_2m_min"][i],
            precipitation_probability_max=daily["precipitation_probability_max"][i],
            wind_speed_max=daily["wind_speed_10m_max"][i],
        )
        for i, day in enumerate(daily.get("time", []))
    ]
