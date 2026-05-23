"""TrustedSourceAgent: checks claims against an allowlist of high-credibility domains.

Initially stubbed — the FunctionTool returns a "no trusted match" stub for most
claims. Wire real fetches per domain (Reuters/AP/.gov/PubMed APIs) post-MVP.
"""
from __future__ import annotations

import logging

import httpx

from backend.config import get_settings
from backend.schemas import SearchEvidence
from backend.tools.trusted_fetch import fetch_trusted_snippet

log = logging.getLogger(__name__)


async def check_trusted(claim_text: str) -> SearchEvidence:
    settings = get_settings()
    if settings.stub_llm:
        return SearchEvidence(
            source="trusted",
            snippet="[stub] trusted-source agent not active.",
            supports="unclear",
        )

    try:
        async with httpx.AsyncClient(timeout=4.0) as http:
            snippet, url, domain = await fetch_trusted_snippet(
                http, claim_text, settings.trusted_domain_list
            )
    except Exception as exc:
        log.warning("trusted fetch failed: %s", exc)
        return SearchEvidence(
            source="trusted",
            snippet="No trusted source matched.",
            supports="unclear",
        )

    return SearchEvidence(
        source="trusted",
        url=url,
        domain=domain,
        snippet=snippet or "No trusted source matched.",
        supports="unclear",
    )
