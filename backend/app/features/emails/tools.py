import asyncio
import json
import logging

from pydantic import BaseModel, Field

from app.agents.models import Tool

from .sources import EmailSource

logger = logging.getLogger(__name__)


class ListRecentEmailsArgs(BaseModel):
    max_results: int = Field(
        default=10, ge=1, le=50, description="How many recent emails to return."
    )


def email_tools(source: EmailSource) -> tuple[Tool, ...]:
    async def list_recent_emails(args: ListRecentEmailsArgs) -> str:
        emails = await asyncio.to_thread(source.list_recent, args.max_results)
        logger.info(
            "list_recent_emails source=%s max_results=%d returned=%d",
            type(source).__name__,
            args.max_results,
            len(emails),
        )
        data = json.dumps([e.model_dump(mode="json") for e in emails])
        return f"<untrusted_emails>\n{data}\n</untrusted_emails>"

    return (
        Tool(
            name="list_recent_emails",
            description="List the user's most recent emails: id, sender, subject, date and snippet.",
            input_model=ListRecentEmailsArgs,
            handler=list_recent_emails,
        ),
    )
