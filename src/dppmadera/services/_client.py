"""In-process client for cross-domain calls.

Brokers (DTw, federation, conflicts) reach other domains only through their public HTTP API,
never through their stores. In this PoC the call stays inside one process; swapping this for a
real HTTP client would not change any service code.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

_client = None


def _get():
    global _client
    if _client is None:
        from fastapi.testclient import TestClient

        from ..app import app  # lazy: avoids a circular import at start-up

        _client = TestClient(app)
    return _client


def get(path: str, **params: Any) -> tuple[int, Any]:
    r = _get().get(path, params={k: v for k, v in params.items() if v is not None})
    return r.status_code, (r.json() if r.content else None)


def q(identifier: str) -> str:
    """Quote an identifier for use in a path segment (keeps '/' so URIs stay readable)."""
    return quote(identifier, safe="/:")
