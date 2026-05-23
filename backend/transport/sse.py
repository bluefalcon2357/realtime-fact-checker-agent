from __future__ import annotations

import asyncio
import json
import logging
from typing import AsyncIterator

from backend.runtime.session_manager import Session

log = logging.getLogger(__name__)

_KEEPALIVE_SECONDS = 15.0


async def event_stream(session: Session) -> AsyncIterator[bytes]:
    """Yield SSE-formatted byte chunks for a session's OverlayEvent stream."""
    while True:
        try:
            event = await asyncio.wait_for(session.queue.get(), timeout=_KEEPALIVE_SECONDS)
        except asyncio.TimeoutError:
            yield b": keepalive\n\n"
            if session.ended:
                return
            continue
        payload = json.dumps(event.model_dump(mode="json", exclude_none=True))
        yield f"event: {event.event}\ndata: {payload}\n\n".encode("utf-8")
        if event.event == "session_ended":
            return
