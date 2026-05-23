import logging
from typing import AsyncIterator

from backend.ingestion import youtube
from backend.ingestion.chunker import ffmpeg_segmenter, watch_segments
from backend.schemas import Chunk

log = logging.getLogger(__name__)


async def stream_live(
    url: str,
    session_id: str,
    chunk_seconds: int,
) -> AsyncIterator[tuple[Chunk, bytes]]:
    """Ingest a YouTube livestream's HLS manifest as rolling audio chunks.

    Same ffmpeg segmenter as the recorded path; the only difference is the
    URL points at an HLS manifest and ffmpeg streams indefinitely.
    """
    _, info = await youtube.classify(url)
    hls_url = youtube.manifest_url(info)
    if not hls_url:
        raise RuntimeError(f"could not resolve HLS manifest for {url}")

    log.info("live HLS manifest: %s", hls_url[:120])
    proc, out_dir = await ffmpeg_segmenter(hls_url, session_id, chunk_seconds)
    try:
        async for chunk, data in watch_segments(out_dir, session_id, chunk_seconds, proc):
            yield chunk, data
    finally:
        if proc.returncode is None:
            proc.kill()
            await proc.wait()
