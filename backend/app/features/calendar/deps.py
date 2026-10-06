from app.features.auth.deps import GoogleCredentialsDep

from .sources import CalendarSource, GoogleCalendarSource


def get_calendar_source(credentials: GoogleCredentialsDep) -> CalendarSource:
    return GoogleCalendarSource(credentials)
