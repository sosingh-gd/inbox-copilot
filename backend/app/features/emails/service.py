from .schemas import EmailSummary
from .sources import EmailSource


class EmailService:
    """Email use cases. Classification and summarization will live here."""

    def __init__(self, source: EmailSource) -> None:
        self.source = source

    def list_recent(self, max_results: int) -> list[EmailSummary]:
        return self.source.list_recent(max_results)
