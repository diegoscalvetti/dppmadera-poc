"""Conflicts: retained source assertions plus the authority rule applied, or a needs-review flag.

Milestone: PR 2. Endpoints are declared now so the OpenAPI surface is visible; they return 501 until implemented.
"""

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/conflicts", tags=["conflicts"])


def _todo() -> None:
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("")
def list_conflicts() -> dict:
    _todo()
