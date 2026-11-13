import json
from pathlib import Path

from fastapi.testclient import TestClient

from dppmadera.app import app

client = TestClient(app)
SPEC_PATHS = {
    "/dpp/products", "/dpp/events", "/dpp/lineage/{instance_id}", "/epm/observations",
    "/dbl/occurrences", "/dbl/building/{building_id}", "/resolver/mappings", "/resolver/{any_id}",
    "/assets/{asset_id}", "/dtw/assembly-state", "/conflicts",
}


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_openapi_covers_spec_endpoints():
    assert SPEC_PATHS <= set(app.openapi()["paths"])


def test_committed_openapi_is_current():
    committed = json.loads((Path(__file__).resolve().parents[1] / "docs" / "openapi.json").read_text())
    assert committed == json.loads(json.dumps(app.openapi()))


def test_assembly_state_view_renders(replayed):
    c, _, data = replayed
    page = c.get("/view", params={"building_id": data["ground_truth"]["building_id"]})
    assert page.status_code == 200 and "out of sequence" in page.text and page.text.count("class='c'") == 20
