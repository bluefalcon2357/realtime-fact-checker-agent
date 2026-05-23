"""End-to-end agent graph smoke test with all LLM calls stubbed.

Runs `root.run_session()` against a synthetic chunk generator and asserts the
event sequence is well-formed.
"""
import asyncio
from typing import AsyncIterator

import pytest

from backend.agents import claim_extractor, search, transcriber, trusted_source, verdict
from backend.agents.root import run_session
from backend.schemas import Chunk, Claim, SearchEvidence, Verdict


@pytest.fixture
def stub_pipeline(monkeypatch):
    async def fake_transcribe(audio_bytes, mime_type="audio/ogg"):
        return transcriber.Transcription(
            text="The unemployment rate fell to 3.5% last month.",
            speaker="speaker_1",
        )

    async def fake_extract_claims(*, chunk_id, transcript, t_start, t_end, speaker):
        return [
            Claim(
                claim_id=f"{chunk_id}:c0",
                chunk_id=chunk_id,
                text="Unemployment rate fell to 3.5% last month.",
                t_start=t_start,
                t_end=t_end,
                check_worthy=True,
                confidence=0.9,
                speaker=speaker,
            )
        ]

    async def fake_search_claim(claim_text):
        return SearchEvidence(
            source="google_search",
            url="https://reuters.com/x",
            domain="reuters.com",
            snippet="BLS reported unemployment at 3.5%.",
            supports="supports",
        )

    async def fake_check_trusted(claim_text):
        return SearchEvidence(
            source="trusted", snippet="No trusted source matched.", supports="unclear"
        )

    async def fake_adjudicate(claim, evidence):
        return Verdict(
            claim_id=claim.claim_id,
            status="green",
            summary="Supported by BLS.",
            citations=evidence,
        )

    monkeypatch.setattr(transcriber, "transcribe", fake_transcribe)
    monkeypatch.setattr(claim_extractor, "extract_claims", fake_extract_claims)
    monkeypatch.setattr(search, "search_claim", fake_search_claim)
    monkeypatch.setattr(trusted_source, "check_trusted", fake_check_trusted)
    monkeypatch.setattr(verdict, "adjudicate", fake_adjudicate)


async def _gen() -> AsyncIterator[tuple[Chunk, bytes]]:
    for i in range(2):
        yield (
            Chunk(
                chunk_id=f"smoke:{i}",
                session_id="smoke",
                t_start=i * 5.0,
                t_end=(i + 1) * 5.0,
            ),
            b"\x00\x00\x00",
        )


@pytest.mark.asyncio
async def test_run_session_emits_expected_events(stub_pipeline):
    queue: asyncio.Queue = asyncio.Queue()
    await run_session(
        session_id="smoke",
        chunks=_gen(),
        out_queue=queue,
        max_claims=10,
    )

    events = []
    while not queue.empty():
        events.append(queue.get_nowait())

    kinds = [e.event for e in events]
    # First chunk produces claim_detected + verdict; second chunk dedupes (same claim text).
    assert "claim_detected" in kinds
    assert "verdict" in kinds
    assert kinds[-1] == "session_ended"
    assert sum(1 for e in events if e.event == "verdict") == 1, (
        "dedup should suppress repeat claim"
    )
