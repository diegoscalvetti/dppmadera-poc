"""DBL service: building occurrences, installation context and as-built records.

Authoritative for: where a component sits in the building and when it was installed.
Holds the product instance only as a reference.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ._common import make_store

router = APIRouter(prefix="/dbl", tags=["dbl"])
STORE = make_store("dbl")


class Occurrence(BaseModel):
    """A planned occurrence (from the design model) or its as-built update (installation record)."""

    occurrence_id: str
    building_id: str
    ifc_guid: str
    storey: int
    zone: str | None = None
    ifc_class: str | None = None
    planned_seq: int | None = None
    # as-built fields, set by an installation record
    instance_id: str | None = None
    installed_at: str | None = None
    actual_seq: int | None = None
    source: str | None = None
    record_id: str | None = None


def reset() -> None:
    STORE.clear()


@router.post("/occurrences", status_code=201)
def create_occurrence(occ: Occurrence) -> dict:
    current = STORE.get("occurrences", occ.occurrence_id) or {}
    incoming = occ.model_dump(exclude_none=True)
    if current and "installed_at" in incoming:
        # keep the design-model GUID; record the as-built claim alongside it
        incoming["as_built_ifc_guid"] = incoming.pop("ifc_guid")
    merged = {**current, **incoming}
    STORE.put("occurrences", occ.occurrence_id, merged)
    buildings = STORE.get("buildings", occ.building_id) or {"building_id": occ.building_id, "occurrences": []}
    if occ.occurrence_id not in buildings["occurrences"]:
        buildings["occurrences"].append(occ.occurrence_id)
        STORE.put("buildings", occ.building_id, buildings)
    return {"occurrence_id": occ.occurrence_id, "installed": "installed_at" in merged}


@router.get("/occurrences/{occurrence_id:path}")
def get_occurrence(occurrence_id: str) -> dict:
    occ = STORE.get("occurrences", occurrence_id)
    if not occ:
        raise HTTPException(404, "unknown occurrence")
    return occ


@router.get("/building/{building_id:path}")
def building(building_id: str) -> dict:
    b = STORE.get("buildings", building_id)
    if not b:
        raise HTTPException(404, "unknown building")
    occs = [STORE.get("occurrences", o) for o in b["occurrences"]]
    occs.sort(key=lambda o: (o.get("planned_seq") or 0, o["occurrence_id"]))
    return {"building_id": building_id, "count": len(occs), "occurrences": occs}
