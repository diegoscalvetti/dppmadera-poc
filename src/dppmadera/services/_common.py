"""Helpers shared by all services. Holds no domain data."""

from __future__ import annotations

import os
from pathlib import Path

from ..store import JsonStore


def make_store(domain: str) -> JsonStore:
    """In memory by default; set DPPMADERA_VAR=<dir> to persist each domain to its own JSON file."""
    root = os.environ.get("DPPMADERA_VAR")
    return JsonStore(domain, Path(root) / f"{domain}.json" if root else None)
