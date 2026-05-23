import asyncio
import logging

import yt_dlp

from backend.schemas import StreamKind

log = logging.getLogger(__name__)

_YDL_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "skip_download": True,
    "extract_flat": False,
}


def _probe_sync(url: str) -> dict:
    with yt_dlp.YoutubeDL(_YDL_OPTS) as ydl:
        return ydl.extract_info(url, download=False)


async def probe(url: str) -> dict:
    """Return yt-dlp metadata for a YouTube URL. Runs sync yt-dlp in a thread."""
    return await asyncio.to_thread(_probe_sync, url)


async def classify(url: str) -> tuple[StreamKind, dict]:
    """Detect whether the URL is live or recorded, and return (kind, metadata)."""
    info = await probe(url)
    is_live = bool(info.get("is_live")) or info.get("live_status") in {
        "is_live",
        "is_upcoming",
    }
    kind = StreamKind.LIVE if is_live else StreamKind.RECORDED
    log.info("classified %s as %s", url, kind.value)
    return kind, info


def manifest_url(info: dict) -> str | None:
    """Pull the best audio HLS/HTTP URL out of yt-dlp metadata."""
    if "url" in info and info["url"]:
        return info["url"]
    formats = info.get("formats") or []
    audio_only = [f for f in formats if f.get("vcodec") == "none" and f.get("url")]
    if audio_only:
        audio_only.sort(key=lambda f: f.get("abr") or 0, reverse=True)
        return audio_only[0]["url"]
    if formats:
        return formats[-1].get("url")
    return None
