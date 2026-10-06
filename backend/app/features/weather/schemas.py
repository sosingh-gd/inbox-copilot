from typing import Literal

from app.core.schemas import ApiModel

Units = Literal["metric", "imperial"]


class DailyForecast(ApiModel):
    date: str  # YYYY-MM-DD in the location's own timezone
    summary: str  # e.g. "Light rain", from the WMO weather code
    temperature_max: float
    temperature_min: float
    precipitation_probability_max: int | None  # percent; missing for some places and days
    wind_speed_max: float


class WeatherForecast(ApiModel):
    location: str  # resolved place, e.g. "Paris, Île-de-France, France"
    latitude: float
    longitude: float
    timezone: str
    units: Units
    temperature_unit: str  # "°C" or "°F"
    wind_speed_unit: str  # "km/h" or "mph"
    days: list[DailyForecast]
