import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.features.emails.deps import get_email_source
from app.features.emails.schemas import EmailSummary


class FakeEmailSource:
    def __init__(self) -> None:
        self.requested: int | None = None

    def list_recent(self, max_results: int) -> list[EmailSummary]:
        self.requested = max_results
        return [
            EmailSummary(
                id="m1",
                sender="Ada <ada@example.com>",
                subject="Quarterly report",
                date="Fri, 2 Oct 2026 09:00:00 +0000",
                snippet="Please review by Monday",
            )
        ]


@pytest.fixture
def source(app: FastAPI) -> FakeEmailSource:
    fake = FakeEmailSource()
    app.dependency_overrides[get_email_source] = lambda: fake
    return fake


def test_lists_emails_from_the_source(
    signed_in_client: TestClient, source: FakeEmailSource
) -> None:
    response = signed_in_client.get("/api/v1/emails", params={"maxResults": 5})

    assert response.status_code == 200
    assert response.json()[0]["sender"] == "Ada <ada@example.com>"
    assert source.requested == 5


def test_rejects_out_of_range_max_results(
    signed_in_client: TestClient, source: FakeEmailSource
) -> None:
    response = signed_in_client.get("/api/v1/emails", params={"maxResults": 500})

    assert response.status_code == 422
    assert response.json()["errors"][0]["field"] == "maxResults"


def test_requires_sign_in(client: TestClient) -> None:
    assert client.get("/api/v1/emails").status_code == 401
