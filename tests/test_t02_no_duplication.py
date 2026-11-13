"""T2 No duplication.

Pass criterion: each fact is stored once, in its authoritative domain; others hold references only.
Paper link (Calvetti & Méndez 2026, Buildings 16:4411): federated ownership.
"""

import json

from dppmadera.services import conflicts, dbl, dpp, dtw, epm, federation, resolver

OWNER = {"dpp": dpp, "epm": epm, "dbl": dbl}


def test_no_duplication(replayed):
    client, _, data = replayed
    dumps = {name: json.dumps(m.STORE._data) for name, m in {**OWNER, "resolver": resolver}.items()}
    for ev in data["events"]:
        holders = [name for name, text in dumps.items() if ev["id"] in text]
        # installation records are owned by the DBL (record_id); everything else by its domain
        assert holders == [ev["domain"]], (ev["id"], ev["domain"], holders)
    # brokers keep no store of their own
    for broker in (dtw, federation, conflicts):
        assert not hasattr(broker, "STORE"), broker.__name__
    # the DBL holds the product instance as a reference only, never product data
    for occ in dbl.STORE.all("occurrences").values():
        assert not {"batch_id", "product_id", "kind", "process_run_ids", "certification_ref"} & set(occ)
    # the unified view carries links and derived values, not source payloads
    any_instance = data["components"][0]["ids"]["instance_id"]
    view = json.dumps(client.get(f"/assets/{any_instance}").json())
    assert "moisture_pct" not in view and "payload" not in view and "href" in view
