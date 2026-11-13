"""Minimal JSON-backed store. Each domain owns exactly one instance; no domain reads another's store."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any


class JsonStore:
    def __init__(self, domain: str, path: Path | None = None) -> None:
        self.domain = domain
        self.path = path  # None keeps the store in memory (tests)
        self._lock = threading.Lock()
        self._data: dict[str, dict[str, Any]] = {}
        if path and path.exists():
            self._data = json.loads(path.read_text(encoding="utf-8"))

    def put(self, collection: str, key: str, value: Any) -> None:
        with self._lock:
            self._data.setdefault(collection, {})[key] = value
            self._flush()

    def get(self, collection: str, key: str) -> Any | None:
        return self._data.get(collection, {}).get(key)

    def all(self, collection: str) -> dict[str, Any]:
        return dict(self._data.get(collection, {}))

    def clear(self) -> None:
        with self._lock:
            self._data = {}
            self._flush()

    def _flush(self) -> None:
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(self._data, indent=2, sort_keys=True), encoding="utf-8")
