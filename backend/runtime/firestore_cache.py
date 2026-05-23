"""Cross-session verdict cache. Firestore on Cloud Run, in-memory dict locally."""
from __future__ import annotations

import logging
import time

from backend.config import get_settings
from backend.runtime.dedupe import claim_hash
from backend.schemas import Verdict

log = logging.getLogger(__name__)

_TTL_SECONDS = 24 * 3600


class VerdictCache:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._local: dict[str, tuple[Verdict, float]] = {}
        self._client = None
        if not self.settings.local_mode:
            try:
                from google.cloud import firestore

                self._client = firestore.AsyncClient(project=self.settings.google_cloud_project)
            except Exception as exc:
                log.warning("firestore client init failed; falling back to local: %s", exc)
                self._client = None

    async def get(self, claim_text: str) -> Verdict | None:
        h = claim_hash(claim_text)
        if self._client is None:
            entry = self._local.get(h)
            if not entry:
                return None
            verdict, ts = entry
            if time.time() - ts > _TTL_SECONDS:
                self._local.pop(h, None)
                return None
            return verdict
        doc = await self._client.collection(self.settings.firestore_collection).document(h).get()
        if not doc.exists:
            return None
        data = doc.to_dict() or {}
        if time.time() - data.get("ts", 0) > _TTL_SECONDS:
            return None
        try:
            return Verdict(**data["verdict"])
        except Exception:
            return None

    async def put(self, claim_text: str, verdict: Verdict) -> None:
        h = claim_hash(claim_text)
        if self._client is None:
            self._local[h] = (verdict, time.time())
            return
        await self._client.collection(self.settings.firestore_collection).document(h).set(
            {"ts": time.time(), "verdict": verdict.model_dump()}
        )
