"""DPP service: product and instance identity, composition, provenance, certification, custody and transformation events.

Authoritative for: what the product instance is and where it has been (custody chain).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ._common import make_store

router = APIRouter(prefix="/dpp", tags=["dpp"])
STORE = make_store("dpp")

# Expected custody chain from factory to site (EPCIS bizStep values)
CUSTODY_CHAIN = ["commissioning", "loading", "shipping", "receiving"]


class Product(BaseModel):
    instance_id: str
    product_id: str
    batch_id: str
    kind: str
    certification_ref: str | None = None
    process_run_ids: list[str] = Field(default_factory=list)
    composition: dict[str, Any] = Field(default_factory=dict)


class EpcisEvent(BaseModel):
    id: str
    type: str = Field(description="ObjectEvent, AggregationEvent or TransformationEvent")
    event_time: str
    record_time: str
    source: str
    asset_id: str | None = Field(None, description="Instance ID, or parent ID for an AggregationEvent")
    payload: dict[str, Any]


def reset() -> None:
    STORE.clear()


@router.post("/products", status_code=201)
def create_product(product: Product) -> dict:
    STORE.put("products", product.instance_id, product.model_dump())
    return {"instance_id": product.instance_id, "links": {"lineage": f"/dpp/lineage/{product.instance_id}"}}


@router.get("/products/{instance_id:path}")
def get_product(instance_id: str) -> dict:
    product = STORE.get("products", instance_id)
    if not product:
        raise HTTPException(404, "unknown product instance")
    return product


@router.post("/events", status_code=201)
def create_event(event: EpcisEvent) -> dict:
    duplicate = STORE.get("events", event.id) is not None
    if not duplicate:
        STORE.put("events", event.id, event.model_dump())
    return {"id": event.id, "duplicate": duplicate}


def _events_for(instance_id: str) -> list[dict]:
    out = []
    for e in STORE.all("events").values():
        children = e["payload"].get("childEPCs") or []
        if e["asset_id"] == instance_id or instance_id in children:
            out.append(e)
    return sorted(out, key=lambda e: (e["event_time"], e["record_time"]))


def custody_gaps(events: list[dict]) -> list[str]:
    seen = {e["payload"].get("bizStep") for e in events}
    last = max((CUSTODY_CHAIN.index(s) for s in seen if s in CUSTODY_CHAIN), default=-1)
    return [step for step in CUSTODY_CHAIN[: last + 1] if step not in seen]


@router.get("/lineage/{instance_id:path}")
def lineage(instance_id: str) -> dict:
    product = STORE.get("products", instance_id)
    if not product:
        raise HTTPException(404, "unknown product instance; resolve other identifiers through /resolver first")
    events = _events_for(instance_id)
    gaps = custody_gaps(events)
    return {
        "instance_id": instance_id,
        "product": product,
        "events": events,
        "custody_steps": [e["payload"].get("bizStep") for e in events],
        "custody_gaps": gaps,
        "complete": not gaps,
    }
