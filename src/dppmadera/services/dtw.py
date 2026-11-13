"""Minimal DTw: derived assembly state only.

Holds no source data. Every call derives the state of each building occurrence from the DBL
(planned and as-built), the resolver (occurrence -> instance), the DPP (custody) and the EPM
(inspections), using event time, not arrival order, so late events are reconciled (T6).
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from . import _client as api

router = APIRouter(prefix="/dtw", tags=["dtw"])

ORDER = ["planned", "produced", "dispatched", "delivered", "installed", "inspected"]
STEP_STATE = {"commissioning": "produced", "loading": "dispatched", "shipping": "dispatched", "receiving": "delivered"}
LATE_HOURS = 24


def _hours(a: str, b: str) -> float:
    from datetime import datetime

    f = "%Y-%m-%dT%H:%M:%SZ"
    return (datetime.strptime(b, f) - datetime.strptime(a, f)).total_seconds() / 3600


def component_state(occ: dict) -> dict:
    status, res = api.get(f"/resolver/{api.q(occ['occurrence_id'])}")
    ids = res["ids"] if status == 200 else {}
    instance = (ids.get("instance_id") or [None])[0]
    state, flags, history, late = "planned", [], [], []
    if instance:
        s, lin = api.get(f"/dpp/lineage/{api.q(instance)}")
        if s == 200:
            for e in lin["events"]:
                st = STEP_STATE.get(e["payload"].get("bizStep"))
                if st:
                    history.append({"state": st, "at": e["event_time"], "source": e["source"]})
            if lin["custody_gaps"]:
                flags.append({"flag": "custody_gap", "missing": lin["custody_gaps"]})
        s, obs = api.get("/epm/observations", asset_id=instance, schema="installation_inspection/v1")
        for o in obs["observations"] if s == 200 else []:
            history.append({"state": "inspected", "at": o["event_time"], "source": o["source"]})
            if _hours(o["event_time"], o["record_time"]) > LATE_HOURS:
                late.append({"id": o["id"], "event_time": o["event_time"], "record_time": o["record_time"]})
    if occ.get("installed_at"):
        history.append({"state": "installed", "at": occ["installed_at"], "source": occ.get("source")})
    history.sort(key=lambda h: (h["at"], ORDER.index(h["state"])))
    for h in history:
        if ORDER.index(h["state"]) > ORDER.index(state):
            state = h["state"]
    if res and res.get("disputed"):
        flags.append({"flag": "identifier_dispute", "detail": res["disputed"]})
    if late:
        flags.append({"flag": "late_event_reconciled", "events": late})
    return {"occurrence_id": occ["occurrence_id"], "instance_id": instance, "ifc_guid": occ["ifc_guid"],
            "name": occ.get("name"), "storey": occ["storey"], "planned_seq": occ.get("planned_seq"),
            "actual_seq": occ.get("actual_seq"), "state": state, "history": history, "flags": flags}


def sequence_flags(items: list[dict]) -> None:
    """Flag a component installed before a component planned earlier (installed later or not yet)."""
    for x in items:
        if x["actual_seq"] is None:
            continue
        before = [y for y in items if y["planned_seq"] < x["planned_seq"]
                  and (y["actual_seq"] is None or y["actual_seq"] > x["actual_seq"])]
        if before:
            x["flags"].append({"flag": "out_of_sequence",
                               "installed_before": [y["name"] or y["occurrence_id"] for y in before]})


@router.get("/assembly-state")
def assembly_state(building_id: str) -> dict:
    s, b = api.get(f"/dbl/building/{api.q(building_id)}")
    if s != 200:
        raise HTTPException(404, "unknown building")
    items = [component_state(o) for o in b["occurrences"]]
    sequence_flags(items)
    s, cs = api.get("/conflicts")
    for c in cs["conflicts"] if s == 200 else []:
        if c["kind"] == "value_conflict":
            for i in items:
                if i["instance_id"] == c["asset_id"]:
                    i["flags"].append({"flag": "value_conflict", "property": c["property"], "status": c["status"]})
    summary: dict[str, int] = {}
    for i in items:
        summary[i["state"]] = summary.get(i["state"], 0) + 1
    return {"building_id": building_id, "summary": summary,
            "flagged": sum(1 for i in items if i["flags"]), "components": items}
