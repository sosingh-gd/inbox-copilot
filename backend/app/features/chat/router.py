import asyncio
import logging
from collections.abc import AsyncIterator

from fastapi import APIRouter, Request

from app.api.deps import CurrentUser
from app.core.sse import EventStreamResponse, format_sse, with_heartbeat

from .deps import ChatServiceDep
from .events import RunFailedEvent
from .schemas import ChatRunRequest, ConversationDetail, ConversationSummary

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/conversations")
def list_conversations(user: CurrentUser, service: ChatServiceDep) -> list[ConversationSummary]:
    return service.list_conversations(user.id)


@router.get("/conversations/{conversation_id}")
def get_conversation(
    conversation_id: str, user: CurrentUser, service: ChatServiceDep
) -> ConversationDetail:
    return service.get_conversation(user.id, conversation_id)


@router.post(
    "/runs/stream",
    response_class=EventStreamResponse,
    responses={
        200: {
            "description": "SSE stream; each data payload is a ChatEvent",
            "content": {
                "text/event-stream": {"schema": {"$ref": "#/components/schemas/ChatEvent"}}
            },
        }
    },
)
def stream_chat_run(
    body: ChatRunRequest, request: Request, user: CurrentUser, service: ChatServiceDep
) -> EventStreamResponse:
    """Save the user's message and stream Claude's reply.

    Auth, validation and unknown-conversation errors happen before streaming starts and
    return normal Problem Details. After the 200, failures arrive as a run_failed event.
    """
    turn = service.start_turn(user.id, body)

    async def events() -> AsyncIterator[str]:
        seq = 0
        try:
            async for item in with_heartbeat(service.stream_reply(turn), interval=15):
                if await request.is_disconnected():
                    break
                if isinstance(item, str):  # heartbeat comment
                    yield item
                    continue
                seq += 1
                yield format_sse(item, event_id=str(seq))
        except asyncio.CancelledError:
            raise  # client went away; let cleanup run
        except Exception:
            logger.exception("chat run failed")
            yield format_sse(RunFailedEvent(code="chat_failed", message="The reply failed."))

    return EventStreamResponse(events())
