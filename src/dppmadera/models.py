"""Shared data model: identifiers, event envelope and enums.

Every domain service may import this module. No service may import another domain's store.
"""

from __future__ import annotations

import base64
import uuid
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

ID_BASE = "https://id.dppmadera.example"


class Domain(str, Enum):
    DPP = "dpp"
    EPM = "epm"
    DBL = "dbl"
    DTW = "dtw"


class ComponentKind(str, Enum):
    CLT_WALL = "clt_wall_panel"
    CLT_FLOOR = "clt_floor_panel"
    GLULAM_BEAM = "glulam_beam"
    GLULAM_COLUMN = "glulam_column"
    CONNECTOR_SET = "connector_set"


class AssemblyState(str, Enum):
    PLANNED = "planned"
    PRODUCED = "produced"
    DISPATCHED = "dispatched"
    DELIVERED = "delivered"
    INSTALLED = "installed"
    INSPECTED = "inspected"


class Identifiers(BaseModel):
    """The identifiers that T1 must resolve to each other."""

    product_id: str = Field(description="Product class (GS1 Digital Link style, GTIN only)")
    instance_id: str = Field(description="Serialised product instance")
    batch_id: str = Field(description="Production batch / lot")
    ifc_guid: str = Field(description="IFC GlobalId, 22 characters")
    occurrence_id: str = Field(description="Building occurrence in the DBL")
    process_run_ids: list[str] = Field(default_factory=list, description="Factory process runs")


class Envelope(BaseModel):
    """Envelope-plus-payload rule (paper §4): the envelope is normalised, the payload is kept as received."""

    id: str
    event_time: str = Field(description="When it happened (ISO 8601, UTC)")
    record_time: str = Field(description="When the gateway received it (ISO 8601, UTC)")
    source: str = Field(description="Role of the emitting system, never a person")
    asset_id: str = Field(description="Any identifier of the asset; resolved by the resolver")
    schema_: str = Field(alias="schema", description="Payload schema name")
    payload: dict[str, Any]

    model_config = {"populate_by_name": True}


_IFC_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_$"


def ifc_guid_from_uuid(u: uuid.UUID) -> str:
    """Compress a UUID into the 22-character IFC GlobalId encoding."""
    n = u.int
    chars = []
    for _ in range(22):
        chars.append(_IFC_CHARS[n % 64])
        n //= 64
    return "".join(reversed(chars))


def gtin14(company_prefix: str, item_ref: int) -> str:
    """Build a GTIN-14 with a valid check digit (fictional prefix)."""
    body = f"0{company_prefix}{item_ref:0{12 - len(company_prefix)}d}"
    total = sum(int(d) * (3 if i % 2 == 0 else 1) for i, d in enumerate(reversed(body)))
    return body + str((10 - total % 10) % 10)


def short_hash(text: str) -> str:
    return base64.b32encode(uuid.uuid5(uuid.NAMESPACE_URL, text).bytes).decode()[:8].lower()
