"""Where calendar events come from. The service only knows the CalendarSource protocol, so
Google Calendar can be swapped for local fake data without touching it.
"""

from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.core.errors import ExternalServiceError, GoogleReauthRequiredError

from .schemas import CalendarEvent


class CalendarSource(Protocol):
    def list_upcoming(self, days: int) -> list[CalendarEvent]: ...


class GoogleCalendarSource:
    """Read-only Google Calendar access (calendar.readonly scope)."""

    def __init__(self, credentials: Credentials) -> None:
        self._credentials = credentials

    def list_upcoming(self, days: int) -> list[CalendarEvent]:
        now = datetime.now(UTC)
        try:
            service = build("calendar", "v3", credentials=self._credentials, cache_discovery=False)
            result = (
                service.events()
                .list(
                    calendarId="primary",
                    timeMin=now.isoformat(),
                    timeMax=(now + timedelta(days=days)).isoformat(),
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
        except RefreshError as exc:
            raise GoogleReauthRequiredError() from exc
        except HttpError as exc:
            raise ExternalServiceError(
                "Google Calendar could not be reached.", code="google_api_error"
            ) from exc
        return [_to_event(item) for item in result.get("items", [])]


def _when(value: dict[str, Any]) -> str | None:
    return value.get("dateTime") or value.get("date")


def _to_event(event: dict[str, Any]) -> CalendarEvent:
    return CalendarEvent(
        id=event["id"],
        summary=event.get("summary", "(No title)"),
        start=_when(event.get("start", {})),
        end=_when(event.get("end", {})),
        location=event.get("location", ""),
    )
