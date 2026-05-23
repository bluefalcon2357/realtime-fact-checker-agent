from backend.schemas import (
    Claim,
    OverlayEvent,
    SearchEvidence,
    SessionRequest,
    StreamKind,
    Verdict,
)


def test_claim_roundtrip():
    c = Claim(
        claim_id="c1", chunk_id="ch1", text="x", t_start=0.0, t_end=5.0,
    )
    assert Claim(**c.model_dump()) == c


def test_verdict_status_constrained():
    v = Verdict(claim_id="c1", status="green", summary="ok")
    assert v.status == "green"


def test_overlay_event_minimal():
    e = OverlayEvent(event="session_started", session_id="s1")
    assert e.model_dump(exclude_none=True) == {"event": "session_started", "session_id": "s1"}


def test_session_request_kind_optional():
    r = SessionRequest(youtube_url="https://youtu.be/abc")
    assert r.kind is None


def test_evidence_default_supports():
    e = SearchEvidence(source="trusted", snippet="x")
    assert e.supports == "unclear"


def test_stream_kind_values():
    assert StreamKind("recorded") == StreamKind.RECORDED
    assert StreamKind("live") == StreamKind.LIVE
