from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from backend.config import get_settings
from backend.ingestion import youtube
from backend.runtime import runner
from backend.runtime.session_manager import manager
from backend.schemas import SessionRequest, SessionResponse, StreamKind
from backend.transport import sse, ws

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("factcheck")

app = FastAPI(title="Live Reality Fact-Check Overlay")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/sessions", response_model=SessionResponse)
async def create_session(req: SessionRequest) -> SessionResponse:
    if not req.youtube_url:
        raise HTTPException(status_code=400, detail="youtube_url is required")

    if req.kind is None:
        kind, info = await youtube.classify(req.youtube_url)
    else:
        kind = req.kind
        _, info = await youtube.classify(req.youtube_url)

    session = manager.create(req.youtube_url, kind)
    session.task = asyncio.create_task(runner.run(session))

    return SessionResponse(
        session_id=session.session_id,
        kind=kind,
        title=info.get("title"),
        duration=info.get("duration"),
    )


@app.get("/api/sessions/{session_id}/stream")
async def stream(session_id: str) -> StreamingResponse:
    session = manager.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="session not found")
    return StreamingResponse(
        sse.event_stream(session),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.websocket("/api/sessions/{session_id}/ws")
async def ws_endpoint(websocket: WebSocket, session_id: str) -> None:
    session = manager.get(session_id)
    if session is None:
        await websocket.close(code=4404)
        return
    await ws.serve(websocket, session)


@app.delete("/api/sessions/{session_id}")
async def end_session(session_id: str) -> dict[str, str]:
    session = manager.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="session not found")
    if session.task and not session.task.done():
        session.task.cancel()
    manager.remove(session_id)
    return {"status": "ended"}


if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    async def root_index() -> FileResponse:
        return FileResponse(FRONTEND_DIR / "index.html")


@app.on_event("startup")
async def on_startup() -> None:
    s = get_settings()
    log.info(
        "starting | model=%s local_mode=%s stub_llm=%s chunk_seconds=%d",
        s.gemini_model, s.local_mode, s.stub_llm, s.chunk_seconds,
    )
