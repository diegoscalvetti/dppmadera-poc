"""Federated unified view: brokers DPP, EPM, DBL and DTw through their APIs; holds no copy.

The answer carries identifiers, links and a few derived values; the facts stay with their owners.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from . import _client as api

router = APIRouter(prefix="/assets", tags=["assets"])


@router.get("/{asset_id:path}")
def asset(asset_id: str) -> dict:
    s, res = api.get(f"/resolver/{api.q(asset_id)}")
    if s != 200:
        raise HTTPException(404, "identifier not known to the resolver")
    ids = res["ids"]
    instance = (ids.get("instance_id") or [None])[0]
    occurrence = (ids.get("occurrence_id") or [None])[0]
    out: dict = {"query": asset_id, "ids": ids, "disputed": res["disputed"], "dpp": None, "epm": None, "dbl": None, "dtw": None}
    if instance:
        s, lin = api.get(f"/dpp/lineage/{api.q(instance)}")
        if s == 200:
            out["dpp"] = {"href": f"/dpp/lineage/{instance}", "custody_complete": lin["complete"],
                          "custody_gaps": lin["custody_gaps"], "events": len(lin["events"])}
        s, obs = api.get("/epm/observations", asset_id=instance)
        if s == 200:
            out["epm"] = {"href": f"/epm/observations?asset_id={instance}", "observations": obs["count"],
                          "schemas": sorted({o["schema"] for o in obs["observations"]})}
    if occurrence:
        s, occ = api.get(f"/dbl/occurrences/{api.q(occurrence)}")
        if s == 200:
            out["dbl"] = {"href": f"/dbl/occurrences/{occurrence}", "building_id": occ["building_id"],
                          "storey": occ["storey"], "installed": bool(occ.get("installed_at"))}
            s, dtw = api.get("/dtw/assembly-state", building_id=occ["building_id"])
            if s == 200:
                mine = next((c for c in dtw["components"] if c["occurrence_id"] == occurrence), None)
                if mine:
                    out["dtw"] = {"href": f"/dtw/assembly-state?building_id={occ['building_id']}",
                                  "state": mine["state"], "flags": [f["flag"] for f in mine["flags"]]}
    return out
