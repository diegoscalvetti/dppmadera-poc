"""Minimal DTw: derived assembly state only (planned, delivered, installed, inspected, flagged).

Milestone: PR 3. Endpoints are declared now so the OpenAPI surface is visible; they return 501 until implemented.
"""

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/dtw", tags=["dtw"])


def _todo() -> None:
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/assembly-state")
def assembly_state() -> dict:
    _todo()
