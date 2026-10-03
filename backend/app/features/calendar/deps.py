from typing import Annotated

from fastapi import Depends

from app.features.auth.deps import GoogleCredentialsDep

from .service import CalendarService
from .sources import CalendarSource, GoogleCalendarSource


def get_calendar_source(credentials: GoogleCredentialsDep) -> CalendarSource:
    return GoogleCalendarSource(credentials)


def get_calendar_service(
    source: Annotated[CalendarSource, Depends(get_calendar_source)],
) -> CalendarService:
    return CalendarService(source)


CalendarServiceDep = Annotated[CalendarService, Depends(get_calendar_service)]
