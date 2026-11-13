"""EPM gateway: raw observations, process runs, device metadata, evidence quality (envelope + payload as received).

Milestone: PR 1. Endpoints are declared now so the OpenAPI surface is visible; they return 501 until implemented.
"""

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/epm", tags=["epm"])


def _todo() -> None:
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/observations", status_code=201)
def create_observation(body: dict) -> dict:
    _todo()
