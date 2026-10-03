from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.features.calendar.deps import get_calendar_source
from app.features.calendar.schemas import CalendarEvent


class FakeCalendarSource:
    def list_upcoming(self, days: int) -> list[CalendarEvent]:
        return [
            CalendarEvent(
                id="e1",
                summary=f"Planning ({days} days)",
                start="2026-10-05T09:00:00Z",
                end="2026-10-05T10:00:00Z",
                location="",
            )
        ]


def test_lists_upcoming_events(app: FastAPI, signed_in_client: TestClient) -> None:
    app.dependency_overrides[get_calendar_source] = FakeCalendarSource

    response = signed_in_client.get("/api/v1/calendar/events", params={"days": 3})

    assert response.status_code == 200
    assert response.json()[0]["summary"] == "Planning (3 days)"


def test_requires_sign_in(client: TestClient) -> None:
    assert client.get("/api/v1/calendar/events").status_code == 401
