"""Resolver: identifier mappings with validity intervals and conflict records. The core of the PoC.

Mappings are edges between two identifiers. Resolving an identifier walks the accepted edges and
returns every linked identifier with its validity interval. Some pairs are one-to-one (an IFC GUID
belongs to one building occurrence; an occurrence holds one product instance). A mapping that would
break that rule is kept, marked disputed, excluded from resolution and recorded as a conflict.
"""

from __future__ import annotations

from collections import deque

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ._common import make_store

router = APIRouter(prefix="/resolver", tags=["resolver"])
STORE = make_store("resolver")

ONE_TO_ONE = {frozenset({"ifc_guid", "occurrence_id"}), frozenset({"instance_id", "occurrence_id"})}
SINGLE_VALUED = {"instance_id": {"product_id", "batch_id"}}  # an instance has one product class and one batch
CLASS_LEVEL = {"product_id", "batch_id"}  # shared by many instances: returned, never traversed


class Mapping(BaseModel):
    a: str
    a_type: str
    b: str
    b_type: str
    valid_from: str
    valid_to: str | None = None
    source: str


def reset() -> None:
    STORE.clear()


def _edges(identifier: str) -> list[dict]:
    return STORE.get("edges", identifier) or []


def _overlaps(e: dict, m: Mapping) -> bool:
    return (e["valid_to"] is None or e["valid_to"] > m.valid_from) and (m.valid_to is None or m.valid_to > e["valid_from"])


def _clashes(m: Mapping) -> list[dict]:
    """Accepted edges that the new mapping would contradict."""
    pair = frozenset({m.a_type, m.b_type})
    out = []
    for this, this_type, other, other_type in ((m.a, m.a_type, m.b, m.b_type), (m.b, m.b_type, m.a, m.a_type)):
        single = pair in ONE_TO_ONE or other_type in SINGLE_VALUED.get(this_type, set())
        if not single:
            continue
        for e in _edges(this):
            if e["status"] == "accepted" and e["other_type"] == other_type and e["other"] != other and _overlaps(e, m):
                out.append({"id": this, "id_type": this_type, "already_linked_to": e["other"],
                            "asserted_by": e["source"], "since": e["valid_from"]})
    return out


@router.post("/mappings", status_code=201)
def create_mapping(m: Mapping) -> dict:
    for e in _edges(m.a):
        if e["other"] == m.b:
            return {"status": e["status"], "duplicate": True}
    clashes = _clashes(m)
    status = "disputed" if clashes else "accepted"
    for this, this_type, other, other_type in ((m.a, m.a_type, m.b, m.b_type), (m.b, m.b_type, m.a, m.a_type)):
        STORE.put("edges", this, _edges(this) + [{
            "type": this_type, "other": other, "other_type": other_type, "valid_from": m.valid_from,
            "valid_to": m.valid_to, "source": m.source, "status": status}])
        STORE.put("types", this, this_type)
    if clashes:
        cid = f"idc-{len(STORE.all('conflicts')) + 1:03d}"
        STORE.put("conflicts", cid, {
            "id": cid, "kind": "identifier_clash", "rule": "one-to-one mapping",
            "rejected_mapping": m.model_dump(), "existing": clashes, "status": "needs_review"})
    return {"status": status, "duplicate": False, "clashes": clashes}


@router.get("/conflicts")
def conflicts() -> dict:
    items = list(STORE.all("conflicts").values())
    return {"count": len(items), "conflicts": items}


@router.get("/{any_id:path}")
def resolve(any_id: str) -> dict:
    if STORE.get("types", any_id) is None:
        raise HTTPException(404, "identifier not known to the resolver")
    seen = {any_id}
    links: list[dict] = []
    queue = deque([any_id])
    while queue:
        cur = queue.popleft()
        if cur != any_id and STORE.get("types", cur) in CLASS_LEVEL:
            continue
        for e in _edges(cur):
            if e["status"] != "accepted" or e["other"] in seen:
                continue
            seen.add(e["other"])
            queue.append(e["other"])
            links.append({"id": e["other"], "type": e["other_type"], "via": cur,
                          "valid_from": e["valid_from"], "valid_to": e["valid_to"], "source": e["source"]})
    by_type: dict[str, list[str]] = {}
    for item in [{"id": any_id, "type": STORE.get("types", any_id)}] + links:
        by_type.setdefault(item["type"], []).append(item["id"])
    disputed = [
        {"id": i, "other": e["other"], "other_type": e["other_type"], "source": e["source"]}
        for i in seen if STORE.get("types", i) not in CLASS_LEVEL or i == any_id
        for e in _edges(i) if e["status"] == "disputed"
    ]
    return {"query": any_id, "type": STORE.get("types", any_id), "ids": by_type, "links": links,
            "ambiguous": any(len(v) > 1 for k, v in by_type.items() if k in {"instance_id", "occurrence_id", "ifc_guid"}),
            "disputed": disputed}
