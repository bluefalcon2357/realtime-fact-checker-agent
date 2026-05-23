"""Gated FunctionTool that fetches snippets only from allowlisted domains.

MVP: queries Google's news.google.com for a claim and follows the first result
that's on the allowlist. Hackathon-friendly; swap in proper APIs (Reuters/AP)
post-MVP.
"""
from __future__ import annotations

import logging
from urllib.parse import quote_plus, urlparse

import httpx
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)


def _domain_of(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().lstrip("www.")
    except Exception:
        return ""


def _is_allowed(url: str, allowlist: list[str]) -> bool:
    d = _domain_of(url)
    return any(d == ad or d.endswith("." + ad) for ad in allowlist)


async def fetch_trusted_snippet(
    client: httpx.AsyncClient, claim: str, allowlist: list[str]
) -> tuple[str, str | None, str | None]:
    """Return (snippet, url, domain) — empty snippet if no allowlist match."""
    query = quote_plus(claim[:200])
    search_url = f"https://www.bing.com/search?q={query}"
    try:
        resp = await client.get(
            search_url,
            headers={"User-Agent": "Mozilla/5.0 (factcheck-overlay)"},
            follow_redirects=True,
        )
    except httpx.HTTPError as exc:
        log.warning("search HTTP error: %s", exc)
        return "", None, None

    soup = BeautifulSoup(resp.text, "html.parser")
    for link in soup.select("li.b_algo h2 a"):
        href = link.get("href") or ""
        if _is_allowed(href, allowlist):
            target = href
            domain = _domain_of(target)
            try:
                page = await client.get(target, follow_redirects=True, timeout=4.0)
                page_soup = BeautifulSoup(page.text, "html.parser")
                paras = page_soup.find_all("p")
                snippet = " ".join(p.get_text(strip=True) for p in paras[:3])[:600]
                return snippet, target, domain
            except httpx.HTTPError:
                continue
    return "", None, None
