"""Unit tests for the DPP, EPM and DBL services (milestone 1)."""

import pytest
from fastapi.testclient import TestClient

from dppmadera.app import app
from dppmadera.services import dbl, dpp, epm

client = TestClient(app)
INST = "https://id.dppmadera.example/01/07800001000015/21/P01-1"


@pytest.fixture(autouse=True)
def _reset():
    for m in (dpp, epm, dbl):
        m.reset()


def _product():
    return {"instance_id": INST, "product_id": "https://id.dppmadera.example/01/07800001000015",
            "batch_id": "b1", "kind": "clt_wall_panel", "process_run_ids": ["run1"]}


def _ev(i, step, t, asset=INST, **extra):
    return {"id": f"e{i}", "type": "ObjectEvent", "event_time": t, "record_time": t, "source": "s",
            "asset_id": asset, "payload": {"bizStep": step, **extra}}


def test_dpp_lineage_complete_chain():
    client.post("/dpp/products", json=_product())
    client.post("/dpp/events", json=_ev(1, "commissioning", "2027-01-01T00:00:00Z"))
    client.post("/dpp/events", json={"id": "agg", "type": "AggregationEvent", "event_time": "2027-01-02T00:00:00Z",
                                     "record_time": "2027-01-02T00:00:00Z", "source": "s", "asset_id": "truck",
                                     "payload": {"bizStep": "loading", "childEPCs": [INST]}})
    client.post("/dpp/events", json=_ev(3, "shipping", "2027-01-02T01:00:00Z"))
    client.post("/dpp/events", json=_ev(4, "receiving", "2027-01-02T05:00:00Z"))
    lin = client.get(f"/dpp/lineage/{INST}").json()
    assert lin["custody_steps"] == ["commissioning", "loading", "shipping", "receiving"]
    assert lin["complete"] and lin["custody_gaps"] == []


def test_dpp_lineage_flags_missing_shipping():
    client.post("/dpp/products", json=_product())
    client.post("/dpp/events", json=_ev(1, "commissioning", "2027-01-01T00:00:00Z"))
    client.post("/dpp/events", json=_ev(4, "receiving", "2027-01-02T05:00:00Z"))
    lin = client.get(f"/dpp/lineage/{INST}").json()
    assert lin["custody_gaps"] == ["loading", "shipping"] and not lin["complete"]


def test_dpp_events_are_idempotent_and_unknown_ids_404():
    assert client.post("/dpp/events", json=_ev(1, "commissioning", "t")).json()["duplicate"] is False
    assert client.post("/dpp/events", json=_ev(1, "commissioning", "t")).json()["duplicate"] is True
    assert client.get("/dpp/lineage/unknown").status_code == 404


def test_epm_keeps_payload_as_received():
    payload = {"moisture_pct": 18.5, "vendor_field": {"x": [1, 2]}}
    obs = {"id": "o1", "event_time": "t1", "record_time": "t2", "source": "contractor_qa",
           "asset_id": INST, "schema": "moisture_check/v1", "payload": payload}
    assert client.post("/epm/observations", json=obs).status_code == 201
    got = client.get("/epm/observations", params={"asset_id": INST}).json()["observations"]
    assert got[0]["payload"] == payload and got[0]["schema"] == "moisture_check/v1"


def test_epm_rejects_incomplete_envelope():
    assert client.post("/epm/observations", json={"id": "o1", "payload": {}}).status_code == 422


def test_dbl_planned_then_installed_keeps_design_guid():
    planned = {"occurrence_id": "occ1", "building_id": "b1", "ifc_guid": "G-DESIGN", "storey": 1, "planned_seq": 1}
    client.post("/dbl/occurrences", json=planned)
    client.post("/dbl/occurrences", json={**planned, "ifc_guid": "G-CLAIMED", "instance_id": INST,
                                          "installed_at": "2027-01-10T00:00:00Z", "actual_seq": 2})
    occ = client.get("/dbl/occurrences/occ1").json()
    assert occ["ifc_guid"] == "G-DESIGN" and occ["as_built_ifc_guid"] == "G-CLAIMED"
    assert client.get("/dbl/building/b1").json()["count"] == 1
