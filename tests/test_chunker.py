"""Smoke test for the ffmpeg segmenter. Requires ffmpeg on PATH.

We generate a 10s sine-wave audio in-process via ffmpeg, then segment it.
"""
import asyncio
import shutil

import pytest

from backend.ingestion.chunker import (
    CHUNK_DIR_ROOT,
    cleanup_session,
    ffmpeg_segmenter,
    watch_segments,
)


@pytest.fixture(autouse=True)
def _ffmpeg_available():
    if shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg not installed")


@pytest.mark.asyncio
async def test_segmenter_produces_5s_chunks(tmp_path):
    session_id = "chunker-test"
    cleanup_session(session_id)

    # Generate a 10s mono audio file via ffmpeg's lavfi sine source.
    src = tmp_path / "tone.wav"
    gen = await asyncio.create_subprocess_exec(
        "ffmpeg", "-hide_banner", "-loglevel", "error",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=10",
        "-ar", "16000", "-ac", "1", str(src),
    )
    await gen.wait()
    assert src.exists()

    proc, out_dir = await ffmpeg_segmenter(str(src), session_id, chunk_seconds=5)
    chunks = []
    async for chunk, data in watch_segments(out_dir, session_id, 5, proc):
        chunks.append((chunk, data))

    assert len(chunks) >= 2
    assert chunks[0][0].t_start == 0.0
    assert chunks[0][0].t_end == 5.0
    assert chunks[1][0].t_start == 5.0
    assert all(len(c[1]) > 0 for c in chunks)

    cleanup_session(session_id)
    assert not (CHUNK_DIR_ROOT / session_id).exists()
