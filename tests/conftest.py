import json
from pathlib import Path

import pytest

DATA = Path(__file__).resolve().parents[1] / "data" / "synthetic"


@pytest.fixture(scope="session")
def dataset() -> dict:
    return {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in DATA.glob("*.json")}
