"""T10 Needs coverage.

Pass criterion: each of the 14 LOIN needs is mapped to the endpoint(s)/fields that serve it, or marked
"not covered in PoC".
Paper link (Calvetti & Méndez 2026, Buildings 16:4411): LOIN needs (§3, Table 8).
"""

import json
import re
from pathlib import Path

from dppmadera.app import app

ROOT = Path(__file__).resolve().parents[1]


def _template(path: str) -> str:
    return re.sub(r"\{[^}]+\}", "{}", path.split("?")[0])


def test_needs_coverage():
    needs = json.loads((ROOT / "docs" / "loin_needs.json").read_text(encoding="utf-8"))["needs"]
    assert len(needs) == 14
    spec = {(m.upper(), _template(p)) for p, ops in app.openapi()["paths"].items() for m in ops}
    exercised = 0
    for n in needs:
        if n["poc_status"] == "not covered in PoC":
            assert n["comment"], n["id"]
            continue
        exercised += 1
        for ep in n["served_by"]:
            method, path = ep.split(" ", 1)
            assert (method, _template(path)) in spec, (n["id"], ep)
        for t in n["tested_in"]:
            assert list((ROOT / "tests").glob(f"test_t{int(t[1:]):02d}_*.py")), (n["id"], t)
    assert exercised >= 6
