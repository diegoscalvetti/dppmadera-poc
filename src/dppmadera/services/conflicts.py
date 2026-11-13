"""Conflicts: retained source assertions plus the authority rule applied, or a needs-review flag.

Two kinds: identifier clashes (from the resolver) and value conflicts between observations of the
same property of the same asset within a short window. Every assertion is kept with its source and
time; nothing is overwritten.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter

from . import _client as api

router = APIRouter(prefix="/conflicts", tags=["conflicts"])

# property -> (schemas that carry it, tolerance, window in hours, source authority ranking)
RULES = {
    "moisture_pct": {
        "schemas": ["moisture_check/v1"],
        "tolerance": 2.0,
        "window_h": 6,
        # No ranking between site sources in the PoC: a disagreement needs human review.
        "authority": {},
    }
}


def _t(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")


def value_conflicts() -> list[dict]:
    out = []
    for prop, rule in RULES.items():
        for schema in rule["schemas"]:
            s, obs = api.get("/epm/observations", schema=schema)
            by_asset: dict[str, list[dict]] = {}
            for o in obs["observations"] if s == 200 else []:
                if o["payload"].get(prop) is not None:
                    by_asset.setdefault(o["asset_id"], []).append(o)
            for asset, items in by_asset.items():
                for i, a in enumerate(items):
                    for b in items[i + 1:]:
                        close = abs((_t(b["event_time"]) - _t(a["event_time"])).total_seconds()) <= rule["window_h"] * 3600
                        if close and a["source"] != b["source"] and abs(a["payload"][prop] - b["payload"][prop]) > rule["tolerance"]:
                            ranked = sorted((a, b), key=lambda o: rule["authority"].get(o["source"], 99))
                            decided = rule["authority"].get(ranked[0]["source"], 99) < rule["authority"].get(ranked[1]["source"], 99)
                            out.append({
                                "kind": "value_conflict", "property": prop, "asset_id": asset,
                                "assertions": [{"value": o["payload"][prop], "source": o["source"],
                                                "event_time": o["event_time"], "observation": o["id"]} for o in (a, b)],
                                "rule": f"tolerance {rule['tolerance']} within {rule['window_h']} h",
                                "status": "resolved_by_authority" if decided else "needs_review",
                                "authoritative_value": ranked[0]["payload"][prop] if decided else None,
                            })
    return out


@router.get("")
def list_conflicts() -> dict:
    s, ids = api.get("/resolver/conflicts")
    items = (ids["conflicts"] if s == 200 else []) + value_conflicts()
    return {"count": len(items), "conflicts": items}
