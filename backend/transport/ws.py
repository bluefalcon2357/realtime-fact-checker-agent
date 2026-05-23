"""Optional WebSocket endpoint mirror of the SSE stream."""
from __future__ import annotations

import json
import logging

from fastapi import WebSocket, WebSocketDisconnect

from backend.runtime.session_manager import Session

log = logging.getLogger(__name__)


async def serve(websocket: WebSocket, session: Session) -> None:
    await websocket.accept()
    try:
        while True:
            event = await session.queue.get()
            await websocket.send_text(json.dumps(event.model_dump(mode="json", exclude_none=True)))
            if event.event == "session_ended":
                return
    except WebSocketDisconnect:
        log.info("ws disconnected for %s", session.session_id)
