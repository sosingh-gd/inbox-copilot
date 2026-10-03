from .schemas import CalendarEvent
from .sources import CalendarSource


class CalendarService:
    """Calendar use cases. Scheduling logic and (confirmed) event creation will live here."""

    def __init__(self, source: CalendarSource) -> None:
        self.source = source

    def list_upcoming(self, days: int) -> list[CalendarEvent]:
        return self.source.list_upcoming(days)
