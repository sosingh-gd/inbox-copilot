from typing import Annotated

from fastapi import APIRouter, Query

from .deps import EmailServiceDep
from .schemas import EmailSummary

router = APIRouter(prefix="/emails", tags=["emails"])


@router.get("")
def list_emails(
    service: EmailServiceDep,
    max_results: Annotated[int, Query(alias="maxResults", ge=1, le=100)] = 10,
) -> list[EmailSummary]:
    """Most recent messages in the signed-in user's mailbox (metadata and snippet only)."""
    return service.list_recent(max_results)
