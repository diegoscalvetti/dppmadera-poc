"""DPP service: product and instance identity, composition, provenance, certification, custody and transformation events.

Milestone: PR 1. Endpoints are declared now so the OpenAPI surface is visible; they return 501 until implemented.
"""

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/dpp", tags=["dpp"])


def _todo() -> None:
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/products", status_code=201)
def create_product(body: dict) -> dict:
    _todo()


@router.post("/events", status_code=201)
def create_event(body: dict) -> dict:
    _todo()


@router.get("/lineage/{asset_id:path}")
def lineage(asset_id: str) -> dict:
    _todo()
