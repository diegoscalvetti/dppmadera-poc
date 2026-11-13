"""Structure of the LOIN needs mapping used by T10."""

import json
from pathlib import Path

NEEDS = json.loads((Path(__file__).resolve().parents[1] / "docs" / "loin_needs.json").read_text(encoding="utf-8"))


def test_fourteen_needs_from_table_8():
    ids = [n["id"] for n in NEEDS["needs"]]
    assert ids == ["PB1", "CD1", "CD2", "SC1", "SC2", "SC3", "TD1", "TD2", "TD3", "TD4", "TD5", "TD6", "MC1", "MC2"]


def test_every_need_is_mapped_or_marked_not_covered():
    for n in NEEDS["needs"]:
        assert n["poc_status"] in {"covered", "partial", "not covered in PoC"}
        if n["poc_status"] != "not covered in PoC":
            assert n["served_by"] and n["fields"] and n["tested_in"], n["id"]
