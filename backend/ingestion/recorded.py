import logging
from typing import AsyncIterator

from backend.ingestion import youtube
from backend.ingestion.chunker import ffmpeg_segmenter, watch_segments
from backend.schemas import Chunk

log = logging.getLogger(__name__)


async def stream_recorded(
    url: str,
    session_id: str,
    chunk_seconds: int,
) -> AsyncIterator[tuple[Chunk, bytes]]:
    """Ingest a recorded YouTube video as rolling audio chunks.

    yt-dlp resolves the direct media URL, ffmpeg downloads + segments in one pass.
    """
    _, info = await youtube.classify(url)
    media_url = youtube.manifest_url(info)
    if not media_url:
        raise RuntimeError(f"could not resolve media URL for {url}")

    proc, out_dir = await ffmpeg_segmenter(media_url, session_id, chunk_seconds)
    try:
        async for chunk, data in watch_segments(out_dir, session_id, chunk_seconds, proc):
            yield chunk, data
    finally:
        if proc.returncode is None:
            proc.kill()
            await proc.wait()
