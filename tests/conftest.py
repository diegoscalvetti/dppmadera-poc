import json
from pathlib import Path

import pytest

DATA = Path(__file__).resolve().parents[1] / "data" / "synthetic"


@pytest.fixture(scope="session")
def dataset() -> dict:
    return {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in DATA.glob("*.json")}


@pytest.fixture(scope="module")
def replayed():
    """Run the full replay once per test module; returns (client, results, dataset)."""
    from fastapi.testclient import TestClient

    from dppmadera.app import app
    from dppmadera.replay import load, run

    results = run()
    return TestClient(app), results, load()


def by_code(data: dict) -> dict:
    return {c["code"]: c for c in data["components"]}
