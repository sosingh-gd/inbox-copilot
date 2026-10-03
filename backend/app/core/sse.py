"""Server-Sent Events helpers shared by every streaming endpoint."""

import asyncio
from collections.abc import AsyncIterator, Mapping
from typing import Any

from starlette.responses import StreamingResponse

from app.core.schemas import ApiModel

SSE_PING = ": ping\n\n"  # SSE comment line: ignored by parsers, keeps proxies from timing out


class EventStreamResponse(StreamingResponse):
    """StreamingResponse preset for Server-Sent Events. Also sets the OpenAPI media type."""

    media_type = "text/event-stream"

    # Keep `status_code` explicit: FastAPI inspects this signature when building OpenAPI.
    def __init__(
        self,
        content: Any,
        status_code: int = 200,
        headers: Mapping[str, str] | None = None,
        **kwargs: Any,
    ) -> None:
        merged = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no", **(headers or {})}
        super().__init__(content, status_code=status_code, headers=merged, **kwargs)


def format_sse(event: ApiModel, *, event_id: str | None = None) -> str:
    data = event.model_dump_json(by_alias=True)  # single line, so one `data:` field suffices
    head = f"id: {event_id}\n" if event_id else ""
    return f"{head}event: {getattr(event, 'type', 'message')}\ndata: {data}\n\n"


async def with_heartbeat[T](
    source: AsyncIterator[T], interval: float = 15.0
) -> AsyncIterator[T | str]:
    """Yield items from source, inserting SSE ping comments during silences.

    On cancellation (client disconnect) the source is closed, which propagates into the
    service so the upstream LLM call stops.
    """
    it = aiter(source)
    pending: asyncio.Future[T] = asyncio.ensure_future(anext(it))
    try:
        while True:
            done, _ = await asyncio.wait({pending}, timeout=interval)
            if not done:
                yield SSE_PING
                continue
            try:
                item = pending.result()
            except StopAsyncIteration:
                return
            yield item
            pending = asyncio.ensure_future(anext(it))
    finally:
        pending.cancel()
        aclose = getattr(it, "aclose", None)
        if aclose is not None:
            await aclose()
