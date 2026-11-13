"""Seeded generator for one fictional four-storey CLT building.

Writes, under data/synthetic/:
  components.json    20 components with all identifiers and planned sequence
  ifc_elements.json  IFC GUID list with element type and storey (stands in for an IFC file)
  events.json        all events in replay (record_time) order, each tagged with its owning domain
  ground_truth.json  expected assembly state per component and the five injected faults
  manifest.json      seed, counts and SHA-256 of each file (for T11)

Everything is fictional. Sources are system roles, never people.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .models import ID_BASE, ComponentKind, gtin14, ifc_guid_from_uuid

DEFAULT_SEED = 4411
COMPANY_PREFIX = "7800001"  # fictional
BUILDING_ID = f"{ID_BASE}/dbl/building/ESM-01"
START = datetime(2027, 1, 4, 8, 0, tzinfo=timezone.utc)

# Fault anchors (component codes). Kept here so tests read them from ground_truth, not from code.
F1_DUPLICATE_GUID = ("P08", "P07")  # P08's as-built record claims P07's IFC GUID
F2_MOISTURE_CONFLICT = "P03"
F3_OUT_OF_SEQUENCE = ("P11", "P10")  # P11 installed before its planned predecessor P10
F4_CUSTODY_GAP = "G02"  # no shipping (dispatch) event
F5_LATE_EVENT = "C03"  # site inspection recorded two days late

# Snapshot state at the end of the replay (building still under construction)
NOT_INSPECTED = {"P05"}  # installed, inspection pending
NOT_INSTALLED = {"P12"}  # delivered, waiting on site


def _iso(t: datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def _layout() -> list[dict]:
    """Planned components per storey, in planned installation order."""
    plan: list[tuple[str, ComponentKind, int]] = []
    p = g = c = 0
    for storey in range(1, 5):
        c += 1
        plan.append((f"C{c:02d}", ComponentKind.CONNECTOR_SET, storey))
        if storey in (1, 3):
            g += 1
            plan.append((f"G{g:02d}", ComponentKind.GLULAM_COLUMN, storey))
            g += 1
            plan.append((f"G{g:02d}", ComponentKind.GLULAM_BEAM, storey))
        for _ in range(2):
            p += 1
            plan.append((f"P{p:02d}", ComponentKind.CLT_WALL, storey))
        p += 1
        plan.append((f"P{p:02d}", ComponentKind.CLT_FLOOR, storey))
    return [
        {"code": code, "kind": kind.value, "storey": storey, "planned_seq": i + 1}
        for i, (code, kind, storey) in enumerate(plan)
    ]


def generate(seed: int = DEFAULT_SEED) -> dict[str, object]:
    rng = random.Random(seed)
    uid = lambda: uuid.UUID(int=rng.getrandbits(128), version=4)  # noqa: E731

    components = []
    ifc_elements = []
    kind_item = {k.value: i + 1 for i, k in enumerate(ComponentKind)}
    for comp in _layout():
        code, storey = comp["code"], comp["storey"]
        gtin = gtin14(COMPANY_PREFIX, kind_item[comp["kind"]])
        batch = f"L27-{storey:02d}{rng.randint(100, 999)}"
        serial = f"{code}-{rng.randint(10000, 99999)}"
        guid = ifc_guid_from_uuid(uid())
        comp["ids"] = {
            "product_id": f"{ID_BASE}/01/{gtin}",
            "instance_id": f"{ID_BASE}/01/{gtin}/21/{serial}",
            "batch_id": f"{ID_BASE}/01/{gtin}/10/{batch}",
            "ifc_guid": guid,
            "occurrence_id": f"{BUILDING_ID}/occ/{code}",
            "process_run_ids": [f"{ID_BASE}/run/cnc/{batch}-{code}"],
        }
        comp["certification_ref"] = "CERT-EX-CoC-0001"  # fictional chain-of-custody certificate
        comp["zone"] = f"L{storey}-{'NSEW'[rng.randrange(4)]}"
        components.append(comp)
        ifc_elements.append(
            {
                "ifc_guid": guid,
                "ifc_class": "IfcWall" if "wall" in comp["kind"] else
                "IfcSlab" if "floor" in comp["kind"] else
                "IfcColumn" if "column" in comp["kind"] else
                "IfcBeam" if "beam" in comp["kind"] else "IfcMechanicalFastener",
                "storey": f"Level {storey}",
                "name": code,
            }
        )

    by_code = {c["code"]: c for c in components}
    events: list[dict] = []

    def add(domain: str, etype: str, t: datetime, source: str, code: str, payload: dict, delay_h: float = 0.0) -> None:
        events.append(
            {
                "id": f"urn:uuid:{uid()}",
                "domain": domain,
                "type": etype,
                "event_time": _iso(t),
                "record_time": _iso(t + timedelta(hours=delay_h, seconds=rng.randint(5, 90))),
                "source": source,
                "asset_id": by_code[code]["ids"]["instance_id"] if code else None,
                "component": code,
                "payload": payload,
            }
        )

    # Factory: one working day per storey
    for comp in components:
        code, ids = comp["code"], comp["ids"]
        t = START + timedelta(days=comp["storey"] - 1, hours=comp["planned_seq"] % 6)
        add("dpp", "ObjectEvent", t, "factory_mes", code,
            {"action": "ADD", "bizStep": "commissioning", "batch": ids["batch_id"],
             "processRun": ids["process_run_ids"][0], "certification": comp["certification_ref"]})
        mc = round(rng.uniform(10.5, 13.0), 1) if comp["kind"].startswith(("clt", "glulam")) else None
        add("epm", "Observation", t + timedelta(hours=1), "factory_qa", code,
            {"schema": "qa_inspection/v1", "length_dev_mm": round(rng.uniform(-1.5, 1.5), 1),
             "moisture_pct": mc, "result": "pass"})

    # Transport: one truck per storey, two days after production
    for storey in range(1, 5):
        load = [c for c in components if c["storey"] == storey]
        t0 = START + timedelta(days=storey + 1, hours=6)
        truck = f"{ID_BASE}/00/sscc/78000010{storey:09d}"
        events.append({"id": f"urn:uuid:{uid()}", "domain": "dpp", "type": "AggregationEvent",
                       "event_time": _iso(t0), "record_time": _iso(t0 + timedelta(seconds=30)),
                       "source": "dispatch_yard", "asset_id": truck, "component": None,
                       "payload": {"action": "ADD", "bizStep": "loading", "parentID": truck,
                                   "childEPCs": [c["ids"]["instance_id"] for c in load]}})
        for comp in load:
            if comp["code"] != F4_CUSTODY_GAP:
                add("dpp", "ObjectEvent", t0 + timedelta(hours=1), "dispatch_yard", comp["code"],
                    {"action": "OBSERVE", "bizStep": "shipping", "disposition": "in_transit", "parentID": truck})
            add("dpp", "ObjectEvent", t0 + timedelta(hours=5), "site_gate", comp["code"],
                {"action": "OBSERVE", "bizStep": "receiving", "disposition": "in_progress",
                 "readPoint": "site-gate-qr", "parentID": truck})

    # Fault 2: two site systems report incompatible moisture for the same panel within the hour
    p3 = by_code[F2_MOISTURE_CONFLICT]
    t_arr = START + timedelta(days=p3["storey"] + 1, hours=11, minutes=20)
    add("epm", "Observation", t_arr, "site_gate_meter", p3["code"],
        {"schema": "moisture_check/v1", "moisture_pct": 11.8})
    add("epm", "Observation", t_arr + timedelta(minutes=35), "contractor_qa", p3["code"],
        {"schema": "moisture_check/v1", "moisture_pct": 18.5})

    # Assembly: one storey per two days, in planned order except Fault 3
    actual_order = [c["code"] for c in components]
    a, b = actual_order.index(F3_OUT_OF_SEQUENCE[0]), actual_order.index(F3_OUT_OF_SEQUENCE[1])
    actual_order[a], actual_order[b] = actual_order[b], actual_order[a]
    for i, code in enumerate(actual_order):
        comp = by_code[code]
        if code in NOT_INSTALLED:
            continue
        t = START + timedelta(days=8 + 2 * (comp["storey"] - 1), hours=1 + 0.5 * i)
        add("epm", "Observation", t, "site_crane", code, {"schema": "lift/v1", "hook_load_kg": rng.randint(150, 2400)})
        add("epm", "Observation", t + timedelta(minutes=10), "site_total_station", code,
            {"schema": "placement/v1", "dev_mm": round(rng.uniform(0, 4), 1)})
        add("epm", "Observation", t + timedelta(minutes=20), "site_fixing_log", code,
            {"schema": "fixing/v1", "fasteners": rng.randint(8, 40)})
        claimed_guid = by_code[F1_DUPLICATE_GUID[1]]["ids"]["ifc_guid"] if code == F1_DUPLICATE_GUID[0] \
            else comp["ids"]["ifc_guid"]
        add("dbl", "InstallationRecord", t + timedelta(minutes=25), "site_bim", code,
            {"occurrence_id": comp["ids"]["occurrence_id"], "ifc_guid": claimed_guid,
             "storey": comp["storey"], "zone": comp["zone"], "building_id": BUILDING_ID,
             "actual_seq": i + 1})
        if code not in NOT_INSPECTED:
            delay = 48.0 if code == F5_LATE_EVENT else 0.0
            add("epm", "Observation", t + timedelta(hours=2), "site_qa", code,
                {"schema": "installation_inspection/v1", "result": "pass"}, delay_h=delay)

    events.sort(key=lambda e: (e["record_time"], e["id"]))

    expected_state = {}
    for comp in components:
        code = comp["code"]
        expected_state[code] = (
            "delivered" if code in NOT_INSTALLED else "installed" if code in NOT_INSPECTED else "inspected"
        )

    ground_truth = {
        "building_id": BUILDING_ID,
        "expected_state": expected_state,
        "faults": {
            "F1_ifc_guid_clash": {"components": list(F1_DUPLICATE_GUID), "test": "T7"},
            "F2_moisture_conflict": {"components": [F2_MOISTURE_CONFLICT], "values": [11.8, 18.5], "test": "T5"},
            "F3_out_of_sequence": {"components": list(F3_OUT_OF_SEQUENCE), "test": "T8"},
            "F4_custody_gap": {"components": [F4_CUSTODY_GAP], "missing": "shipping", "test": "T4"},
            "F5_late_event": {"components": [F5_LATE_EVENT], "delay_hours": 48, "test": "T6"},
        },
    }
    return {
        "components": components,
        "ifc_elements": ifc_elements,
        "events": events,
        "ground_truth": ground_truth,
    }


def write(out_dir: Path, seed: int = DEFAULT_SEED) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    data = generate(seed)
    hashes = {}
    for name, content in data.items():
        text = json.dumps(content, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
        (out_dir / f"{name}.json").write_text(text, encoding="utf-8")
        hashes[f"{name}.json"] = hashlib.sha256(text.encode()).hexdigest()
    manifest = {
        "seed": seed,
        "counts": {"components": len(data["components"]), "events": len(data["events"])},
        "sha256": hashes,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--out", type=Path, default=Path("data/synthetic"))
    args = ap.parse_args()
    m = write(args.out, args.seed)
    print(json.dumps(m["counts"]))


if __name__ == "__main__":
    main()
