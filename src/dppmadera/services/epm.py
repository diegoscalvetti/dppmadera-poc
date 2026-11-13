"""EPM gateway: raw observations, process runs, device metadata, evidence quality.

Envelope-plus-payload rule: the envelope is validated and normalised; the payload is stored exactly as received.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ._common import make_store

router = APIRouter(prefix="/epm", tags=["epm"])
STORE = make_store("epm")


class Observation(BaseModel):
    id: str
    event_time: str
    record_time: str
    source: str = Field(description="System role, never a person")
    asset_id: str
    schema_: str = Field(alias="schema")
    payload: dict[str, Any]

    model_config = {"populate_by_name": True}


def reset() -> None:
    STORE.clear()


@router.post("/observations", status_code=201)
def create_observation(obs: Observation) -> dict:
    duplicate = STORE.get("observations", obs.id) is not None
    if not duplicate:
        STORE.put("observations", obs.id, obs.model_dump(by_alias=True))
    return {"id": obs.id, "duplicate": duplicate}


@router.get("/observations")
def list_observations(asset_id: str | None = None, schema: str | None = None) -> dict:
    items = [
        o for o in STORE.all("observations").values()
        if (asset_id is None or o["asset_id"] == asset_id) and (schema is None or o["schema"] == schema)
    ]
    items.sort(key=lambda o: (o["event_time"], o["record_time"]))
    return {"count": len(items), "observations": items}
