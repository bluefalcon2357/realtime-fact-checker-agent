import asyncio
import logging
import shutil
import uuid
from pathlib import Path
from typing import AsyncIterator

from backend.schemas import Chunk

log = logging.getLogger(__name__)

CHUNK_DIR_ROOT = Path("/tmp/factcheck")


def _session_dir(session_id: str) -> Path:
    d = CHUNK_DIR_ROOT / session_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def cleanup_session(session_id: str) -> None:
    d = CHUNK_DIR_ROOT / session_id
    if d.exists():
        shutil.rmtree(d, ignore_errors=True)


async def ffmpeg_segmenter(
    input_url: str,
    session_id: str,
    chunk_seconds: int,
) -> tuple[asyncio.subprocess.Process, Path]:
    """Spawn ffmpeg to write rolling audio segments to a temp dir. Returns (process, dir)."""
    out_dir = _session_dir(session_id)
    pattern = str(out_dir / "chunk_%05d.ogg")

    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "warning",
        "-i",
        input_url,
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-c:a",
        "libopus",
        "-b:a",
        "24k",
        "-f",
        "segment",
        "-segment_time",
        str(chunk_seconds),
        "-segment_format",
        "ogg",
        "-reset_timestamps",
        "1",
        pattern,
    ]
    log.info("spawning ffmpeg: %s", " ".join(cmd))
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE
    )
    return proc, out_dir


async def watch_segments(
    out_dir: Path,
    session_id: str,
    chunk_seconds: int,
    proc: asyncio.subprocess.Process,
    poll_interval: float = 0.25,
) -> AsyncIterator[tuple[Chunk, bytes]]:
    """Yield finalized chunks from ffmpeg's segment directory.

    A segment is considered finalized when a *later* segment file appears,
    or when the ffmpeg process has exited.
    """
    yielded: set[str] = set()
    while True:
        existing = sorted(out_dir.glob("chunk_*.ogg"))
        finalized: list[Path] = []
        if proc.returncode is not None:
            finalized = [p for p in existing if p.name not in yielded]
        elif len(existing) >= 2:
            finalized = [p for p in existing[:-1] if p.name not in yielded]

        for path in finalized:
            try:
                data = path.read_bytes()
            except FileNotFoundError:
                continue
            idx = int(path.stem.split("_")[1])
            t_start = idx * chunk_seconds
            t_end = t_start + chunk_seconds
            chunk = Chunk(
                chunk_id=f"{session_id}:{uuid.uuid4().hex[:8]}",
                session_id=session_id,
                t_start=float(t_start),
                t_end=float(t_end),
                mime_type="audio/ogg",
            )
            yielded.add(path.name)
            path.unlink(missing_ok=True)
            yield chunk, data

        if proc.returncode is not None and not finalized:
            return
        await asyncio.sleep(poll_interval)
