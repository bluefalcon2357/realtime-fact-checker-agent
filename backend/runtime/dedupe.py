from __future__ import annotations

import hashlib
import re
import time
from collections import OrderedDict

from backend.config import get_settings

_PUNCT_RE = re.compile(r"[^a-z0-9\s]")
_WS_RE = re.compile(r"\s+")
_STOPWORDS = {
    "the", "a", "an", "of", "in", "on", "at", "is", "are", "was", "were",
    "and", "or", "but", "to", "for", "with", "as", "by", "that", "this",
    "it", "its", "be", "been", "being", "from",
}


def normalize(text: str) -> str:
    lowered = text.lower()
    no_punct = _PUNCT_RE.sub(" ", lowered)
    words = [w for w in _WS_RE.split(no_punct) if w and w not in _STOPWORDS]
    return " ".join(words)


def claim_hash(text: str) -> str:
    return hashlib.sha1(normalize(text).encode("utf-8")).hexdigest()


class ClaimDeduper:
    """Per-session LRU with TTL. Returns True from `seen()` if the claim was
    encountered within the TTL window."""

    def __init__(self, ttl_seconds: int | None = None, max_size: int = 200) -> None:
        self.ttl = ttl_seconds if ttl_seconds is not None else get_settings().dedupe_ttl_seconds
        self.max_size = max_size
        self._items: OrderedDict[str, float] = OrderedDict()

    def seen(self, text: str) -> bool:
        h = claim_hash(text)
        now = time.monotonic()
        prev = self._items.get(h)
        if prev is not None and now - prev < self.ttl:
            self._items.move_to_end(h)
            return True
        self._items[h] = now
        self._items.move_to_end(h)
        while len(self._items) > self.max_size:
            self._items.popitem(last=False)
        return False
