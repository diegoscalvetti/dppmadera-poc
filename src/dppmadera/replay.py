"""End-to-end replay of the synthetic CLT building.

1. Clears every domain store.
2. Imports the design model into the DBL (planned occurrences) and maps occurrence <-> IFC GUID.
3. Feeds every event in arrival (record_time) order to its owning domain, acting as the
   integration adapters would: the factory MES registers products and their identifiers, site BIM
   posts installation records and the occurrence <-> instance mapping.
4. Runs the verification queries and five stakeholder questions, and returns the results.

All writes and reads go through the public API.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from fastapi.testclient import TestClient

from .app import app
from .services import dbl, dpp, epm, resolver

DATA = Path(__file__).resolve().parents[2] / "data" / "synthetic"
DESIGN_TIME = "2026-12-01T00:00:00Z"


def load(data_dir: Path = DATA) -> dict:
    return {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in data_dir.glob("*.json")}


class Replay:
    def __init__(self, data: dict) -> None:
        self.data = data
        self.c = TestClient(app)
        self.by_code = {c["code"]: c for c in data["components"]}
        self.building_id = data["ground_truth"]["building_id"]
        self.calls = 0

    def post(self, path: str, body: dict) -> dict:
        self.calls += 1
        r = self.c.post(path, json=body)
        if r.status_code >= 400:
            raise RuntimeError(f"{path} -> {r.status_code}: {r.text}")
        return r.json()

    def get(self, path: str, **params) -> dict:
        self.calls += 1
        r = self.c.get(path, params=params)
        r.raise_for_status()
        return r.json()

    def map(self, a: str, a_type: str, b: str, b_type: str, valid_from: str, source: str) -> dict:
        return self.post("/resolver/mappings", {"a": a, "a_type": a_type, "b": b, "b_type": b_type,
                                                "valid_from": valid_from, "source": source})

    def run(self) -> None:
        for m in (dpp, epm, dbl, resolver):
            m.reset()
        ifc = {e["ifc_guid"]: e for e in self.data["ifc_elements"]}
        for comp in self.data["components"]:
            ids = comp["ids"]
            self.post("/dbl/occurrences", {
                "occurrence_id": ids["occurrence_id"], "building_id": self.building_id,
                "ifc_guid": ids["ifc_guid"], "storey": comp["storey"], "zone": comp["zone"],
                "ifc_class": ifc[ids["ifc_guid"]]["ifc_class"], "planned_seq": comp["planned_seq"],
                "name": comp["code"]})
            self.map(ids["occurrence_id"], "occurrence_id", ids["ifc_guid"], "ifc_guid", DESIGN_TIME, "design_model")
        for ev in self.data["events"]:
            getattr(self, f"_{ev['domain']}")(ev)

    def _dpp(self, ev: dict) -> None:
        if ev["payload"].get("bizStep") == "commissioning":
            comp = self.by_code[ev["component"]]
            ids = comp["ids"]
            self.post("/dpp/products", {"instance_id": ids["instance_id"], "product_id": ids["product_id"],
                                        "batch_id": ids["batch_id"], "kind": comp["kind"],
                                        "certification_ref": comp["certification_ref"],
                                        "process_run_ids": ids["process_run_ids"]})
            t = ev["event_time"]
            self.map(ids["instance_id"], "instance_id", ids["product_id"], "product_id", t, ev["source"])
            self.map(ids["instance_id"], "instance_id", ids["batch_id"], "batch_id", t, ev["source"])
            # produced to order for one design element
            self.map(ids["instance_id"], "instance_id", ids["occurrence_id"], "occurrence_id", t, ev["source"])
            for run in ids["process_run_ids"]:
                self.map(ids["instance_id"], "instance_id", run, "process_run_id", t, ev["source"])
        self.post("/dpp/events", {k: ev[k] for k in ("id", "type", "event_time", "record_time", "source", "asset_id", "payload")})

    def _epm(self, ev: dict) -> None:
        self.post("/epm/observations", {"id": ev["id"], "event_time": ev["event_time"], "record_time": ev["record_time"],
                                        "source": ev["source"], "asset_id": ev["asset_id"],
                                        "schema": ev["payload"]["schema"], "payload": ev["payload"]})

    def _dbl(self, ev: dict) -> None:
        p = ev["payload"]
        comp = self.by_code[ev["component"]]
        self.post("/dbl/occurrences", {
            "occurrence_id": p["occurrence_id"], "building_id": p["building_id"], "ifc_guid": p["ifc_guid"],
            "storey": p["storey"], "zone": p["zone"], "instance_id": ev["asset_id"], "installed_at": ev["event_time"],
            "actual_seq": p["actual_seq"], "source": ev["source"], "record_id": ev["id"], "name": comp["code"]})
        self.map(p["occurrence_id"], "occurrence_id", ev["asset_id"], "instance_id", ev["event_time"], ev["source"])
        self.map(p["occurrence_id"], "occurrence_id", p["ifc_guid"], "ifc_guid", ev["event_time"], ev["source"])


def stakeholder_questions(r: Replay) -> list[dict]:
    """Five typical questions. 'manual' counts the separate look-ups a person would make across
    files and systems without a resolver (illustrative, synthetic)."""
    out = []

    def ask(question: str, fn, manual: int) -> None:
        before, t0 = r.calls, time.perf_counter()
        answer = fn()
        out.append({"question": question, "answer": answer, "api_calls": r.calls - before,
                    "manual_lookups_estimate": manual, "ms": round((time.perf_counter() - t0) * 1000, 1)})

    comps = r.data["components"]
    lvl2_panels = [c for c in comps if c["storey"] == 2 and c["kind"].startswith("clt")]

    def q1():
        s = r.get("/dtw/assembly-state", building_id=r.building_id)
        return sorted(c["name"] for c in s["components"]
                      if c["storey"] == 2 and c["name"].startswith("P") and c["state"] == "installed")

    def q2():
        guid = r.by_code["P06"]["ids"]["ifc_guid"]
        a = r.get(f"/assets/{guid}")
        return {"ifc_guid": guid, "instance_id": a["ids"]["instance_id"], "custody_complete": a["dpp"]["custody_complete"],
                "storey": a["dbl"]["storey"], "state": a["dtw"]["state"]}

    def q3():
        s = r.get("/dtw/assembly-state", building_id=r.building_id)
        return sorted(c["name"] for c in s["components"] if any(f["flag"] == "custody_gap" for f in c["flags"]))

    def q4():
        cs = r.get("/conflicts")["conflicts"]
        return [{"asset_id": c["asset_id"], "values": [a["value"] for a in c["assertions"]], "status": c["status"]}
                for c in cs if c["kind"] == "value_conflict"]

    def q5():
        s = r.get("/dtw/assembly-state", building_id=r.building_id)
        return sorted(c["name"] for c in s["components"] if any(f["flag"] == "out_of_sequence" for f in c["flags"]))

    ask("Which level 2 panels are installed but not inspected?", q1, manual=3 * len(lvl2_panels))
    ask("Where is the element with IFC GUID of P06, and is its custody chain complete?", q2, manual=4)
    ask("Which components reached site without a complete custody chain?", q3, manual=2 * len(comps))
    ask("Which moisture readings disagree, and who reported them?", q4, manual=2 * len(comps))
    ask("Which components were installed out of the planned sequence?", q5, manual=2 * len(comps))
    return out


def run(data_dir: Path = DATA, out_dir: Path | None = None) -> dict:
    data = load(data_dir)
    r = Replay(data)
    t0 = time.perf_counter()
    r.run()
    ingest_s = time.perf_counter() - t0
    feed_calls = r.calls
    state = r.get("/dtw/assembly-state", building_id=r.building_id)
    conflicts = r.get("/conflicts")
    results = {
        "dataset": data["manifest"],
        "ingest": {"api_calls": feed_calls, "seconds": round(ingest_s, 2)},
        "assembly_state": {c["name"]: {"state": c["state"], "flags": [f["flag"] for f in c["flags"]]}
                           for c in state["components"]},
        "summary": state["summary"],
        "conflicts": conflicts,
        "questions": stakeholder_questions(r),
    }
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return results
