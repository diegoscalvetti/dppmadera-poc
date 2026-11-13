"""Federated unified view: brokers DPP, EPM, DBL and DTw through their APIs; holds no copy.

Milestone: PR 2. Endpoints are declared now so the OpenAPI surface is visible; they return 501 until implemented.
"""

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/assets", tags=["assets"])


def _todo() -> None:
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/{asset_id:path}")
def asset(asset_id: str) -> dict:
    _todo()
