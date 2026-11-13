"""DBL service: building occurrences, installation context and as-built records.

Milestone: PR 1. Endpoints are declared now so the OpenAPI surface is visible; they return 501 until implemented.
"""

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/dbl", tags=["dbl"])


def _todo() -> None:
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/occurrences", status_code=201)
def create_occurrence(body: dict) -> dict:
    _todo()


@router.get("/building/{building_id:path}")
def building(building_id: str) -> dict:
    _todo()
