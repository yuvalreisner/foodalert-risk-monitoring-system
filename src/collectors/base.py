"""Base class for source-specific collectors."""
from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Iterator


class BaseCollector(ABC):
    """A collector pulls raw records from one source and yields normalized alert dicts."""

    source_id: str = ""

    @abstractmethod
    def fetch_raw(self, since: datetime | None = None, limit: int | None = None) -> Iterator[dict]:
        """Yield raw records from the source as-is."""

    @abstractmethod
    def normalize(self, raw: dict) -> dict:
        """Map a raw source record onto the unified schema."""

    def collect(self, since: datetime | None = None, limit: int | None = None) -> Iterator[dict]:
        for raw in self.fetch_raw(since=since, limit=limit):
            try:
                yield self.normalize(raw)
            except Exception as e:
                # Skip malformed records, surface in pipeline log.
                yield {"_error": str(e), "_source_id": self.source_id, "_raw": raw}
