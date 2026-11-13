"""Unit tests for the resolver (milestone 2)."""

import pytest
from fastapi.testclient import TestClient

from dppmadera.app import app
from dppmadera.services import resolver

client = TestClient(app)


@pytest.fixture(autouse=True)
def _reset():
    resolver.reset()


def m(a, at, b, bt, t="2027-01-01T00:00:00Z", src="s"):
    return client.post("/resolver/mappings", json={"a": a, "a_type": at, "b": b, "b_type": bt,
                                                    "valid_from": t, "source": src}).json()


def test_transitive_resolution_with_validity():
    m("occ1", "occurrence_id", "G1", "ifc_guid")
    m("i1", "instance_id", "occ1", "occurrence_id", t="2027-01-05T00:00:00Z")
    m("i1", "instance_id", "prod", "product_id")
    r = client.get("/resolver/G1").json()
    assert r["ids"] == {"ifc_guid": ["G1"], "occurrence_id": ["occ1"], "instance_id": ["i1"], "product_id": ["prod"]}
    assert next(link for link in r["links"] if link["id"] == "i1")["valid_from"] == "2027-01-05T00:00:00Z"


def test_class_level_ids_are_not_traversed():
    m("i1", "instance_id", "prod", "product_id")
    m("i2", "instance_id", "prod", "product_id")
    assert client.get("/resolver/i1").json()["ids"]["instance_id"] == ["i1"]
    assert sorted(client.get("/resolver/prod").json()["ids"]["instance_id"]) == ["i1", "i2"]


def test_one_to_one_clash_is_disputed_and_recorded():
    m("occ1", "occurrence_id", "G1", "ifc_guid")
    m("occ2", "occurrence_id", "G2", "ifc_guid")
    out = m("occ2", "occurrence_id", "G1", "ifc_guid", src="site_bim")
    assert out["status"] == "disputed"
    assert client.get("/resolver/G1").json()["ids"]["occurrence_id"] == ["occ1"]
    assert client.get("/resolver/conflicts").json()["count"] == 1


def test_unknown_identifier_404():
    assert client.get("/resolver/nope").status_code == 404
