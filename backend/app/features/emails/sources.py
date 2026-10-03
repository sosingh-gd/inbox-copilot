"""Where emails come from. The service only knows the EmailSource protocol, so Gmail can be
swapped for local fake data (tests, evals, offline development) without touching it.
"""

from typing import Any, Protocol

from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.core.errors import ExternalServiceError, GoogleReauthRequiredError

from .schemas import EmailSummary


class EmailSource(Protocol):
    def list_recent(self, max_results: int) -> list[EmailSummary]: ...


class GmailEmailSource:
    """Read-only Gmail access (gmail.readonly scope)."""

    def __init__(self, credentials: Credentials) -> None:
        self._credentials = credentials

    def list_recent(self, max_results: int) -> list[EmailSummary]:
        try:
            service = build("gmail", "v1", credentials=self._credentials, cache_discovery=False)
            messages = service.users().messages()
            listing = messages.list(userId="me", maxResults=max_results).execute()
            return [
                _to_summary(
                    messages.get(
                        userId="me",
                        id=item["id"],
                        format="metadata",
                        metadataHeaders=["From", "Subject", "Date"],
                    ).execute()
                )
                for item in listing.get("messages", [])
            ]
        except RefreshError as exc:
            raise GoogleReauthRequiredError() from exc
        except HttpError as exc:
            raise ExternalServiceError(
                "Gmail could not be reached.", code="google_api_error"
            ) from exc


def _to_summary(message: dict[str, Any]) -> EmailSummary:
    headers = {
        header["name"].lower(): header["value"]
        for header in message.get("payload", {}).get("headers", [])
    }
    return EmailSummary(
        id=message["id"],
        sender=headers.get("from", ""),
        subject=headers.get("subject", ""),
        date=headers.get("date", ""),
        snippet=message.get("snippet", ""),
    )
