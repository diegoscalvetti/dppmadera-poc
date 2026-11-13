"""Resolver: identifier mappings with validity intervals and conflict records. The core of the PoC.

Milestone: PR 2. Endpoints are declared now so the OpenAPI surface is visible; they return 501 until implemented.
"""

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/resolver", tags=["resolver"])


def _todo() -> None:
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/mappings", status_code=201)
def create_mapping(body: dict) -> dict:
    _todo()


@router.get("/{any_id:path}")
def resolve(any_id: str) -> dict:
    _todo()
