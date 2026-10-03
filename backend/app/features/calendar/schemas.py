from app.core.schemas import ApiModel


class CalendarEvent(ApiModel):
    id: str
    summary: str
    # ISO 8601 datetime for timed events, or a YYYY-MM-DD date for all-day events.
    start: str | None
    end: str | None
    location: str
