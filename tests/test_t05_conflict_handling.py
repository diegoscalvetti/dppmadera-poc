"""T5 Conflict handling.

Pass criterion: fault F2: both assertions retained with source and time; authority rule or review flag.
Paper link (Calvetti & Méndez 2026, Buildings 16:4411): conflict rule.
"""

from conftest import by_code


def test_conflict_handling(replayed):
    client, _, data = replayed
    fault = data["ground_truth"]["faults"]["F2_moisture_conflict"]
    instance = by_code(data)[fault["components"][0]]["ids"]["instance_id"]
    values = [c for c in client.get("/conflicts").json()["conflicts"] if c["kind"] == "value_conflict"]
    assert len(values) == 1
    c = values[0]
    assert c["asset_id"] == instance
    assert sorted(a["value"] for a in c["assertions"]) == sorted(fault["values"])
    assert all(a["source"] and a["event_time"] and a["observation"] for a in c["assertions"])
    assert c["status"] in {"needs_review", "resolved_by_authority"} and c["rule"]
    # nothing overwritten: both observations are still in the EPM, payloads as received
    obs = client.get("/epm/observations", params={"asset_id": instance, "schema": "moisture_check/v1"}).json()
    assert sorted(o["payload"]["moisture_pct"] for o in obs["observations"]) == sorted(fault["values"])
