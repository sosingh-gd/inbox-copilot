from typing import Annotated

from fastapi import APIRouter, Query

from .deps import CalendarServiceDep
from .schemas import CalendarEvent

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/events")
def list_calendar_events(
    service: CalendarServiceDep,
    days: Annotated[int, Query(ge=1, le=365)] = 7,
) -> list[CalendarEvent]:
    """Upcoming events on the signed-in user's primary calendar."""
    return service.list_upcoming(days)
