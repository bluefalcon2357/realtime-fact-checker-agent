"""ContextAgent: tracks rolling speaker + topic state across a session.

Stubbed: returns a fixed context until ADK session.state wiring is upgraded.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SessionContext:
    speakers: list[str] = field(default_factory=lambda: ["speaker_1"])
    topic: str = "general"
    last_claims: list[str] = field(default_factory=list)


_CONTEXT: dict[str, SessionContext] = {}


def get_context(session_id: str) -> SessionContext:
    return _CONTEXT.setdefault(session_id, SessionContext())


def update_context(session_id: str, *, speaker: str | None, claim_text: str | None) -> None:
    ctx = get_context(session_id)
    if speaker and speaker not in ctx.speakers:
        ctx.speakers.append(speaker)
    if claim_text:
        ctx.last_claims.append(claim_text)
        ctx.last_claims = ctx.last_claims[-20:]


def reset_context(session_id: str) -> None:
    _CONTEXT.pop(session_id, None)
