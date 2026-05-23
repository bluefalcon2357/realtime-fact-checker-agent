"""Pub/Sub shim. In LOCAL_MODE this is an in-process asyncio.Queue, on Cloud Run
it can be backed by real Pub/Sub topics. Not load-bearing for the MVP — kept
behind this interface so the runner doesn't need to change later."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from backend.config import get_settings

log = logging.getLogger(__name__)


class PubSubShim:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._queues: dict[str, asyncio.Queue] = {}
        self._publisher = None

    def _local_queue(self, topic: str) -> asyncio.Queue:
        return self._queues.setdefault(topic, asyncio.Queue())

    async def publish(self, topic: str, payload: dict[str, Any]) -> None:
        if self.settings.local_mode:
            await self._local_queue(topic).put(payload)
            return
        # Cloud Run path: lazy import + publish. Not used by current MVP loop.
        from google.cloud import pubsub_v1

        if self._publisher is None:
            self._publisher = pubsub_v1.PublisherClient()
        path = self._publisher.topic_path(self.settings.google_cloud_project, topic)
        self._publisher.publish(path, data=str(payload).encode("utf-8"))


shim = PubSubShim()
