from app.core.schemas import ApiModel


class EmailSummary(ApiModel):
    id: str
    sender: str
    subject: str
    date: str  # raw RFC 2822 Date header, as sent by the mail client
    snippet: str
