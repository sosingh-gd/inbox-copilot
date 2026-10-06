import asyncio
import json
import logging

from pydantic import BaseModel, Field

from app.agents.models import Tool

from .sources import CalendarSource

logger = logging.getLogger(__name__)


class ListUpcomingEventsArgs(BaseModel):
    days: int = Field(default=7, ge=1, le=30, description="How many days ahead to look.")


def calendar_tools(source: CalendarSource) -> tuple[Tool, ...]:
    async def list_upcoming_events(args: ListUpcomingEventsArgs) -> str:
        events = await asyncio.to_thread(source.list_upcoming, args.days)
        logger.info(
            "list_upcoming_events source=%s days=%d returned=%d",
            type(source).__name__,
            args.days,
            len(events),
        )
        data = json.dumps([e.model_dump(mode="json") for e in events])
        return f"<untrusted_events>\n{data}\n</untrusted_events>"

    return (
        Tool(
            name="list_upcoming_events",
            description="List the user's calendar events from now until the given number of days ahead.",
            input_model=ListUpcomingEventsArgs,
            handler=list_upcoming_events,
        ),
    )
