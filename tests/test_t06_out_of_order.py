"""T6 Out-of-order events.

Pass criterion: fault F5: correct state after timestamp-ordered reconciliation.
Paper link (Calvetti & Méndez 2026, Buildings 16:4411): timestamp ordering.
"""


def test_out_of_order(replayed):
    client, results, data = replayed
    fault = data["ground_truth"]["faults"]["F5_late_event"]
    code = fault["components"][0]
    late = next(e for e in data["events"] if e["component"] == code
                and e["payload"].get("schema") == "installation_inspection/v1")
    # it really arrived after events that happened later
    later_but_earlier_arrival = [e for e in data["events"]
                                 if e["event_time"] > late["event_time"] and e["record_time"] < late["record_time"]]
    assert later_but_earlier_arrival
    state = client.get("/dtw/assembly-state", params={"building_id": data["ground_truth"]["building_id"]}).json()
    comp = next(c for c in state["components"] if c["name"] == code)
    assert comp["state"] == data["ground_truth"]["expected_state"][code] == "inspected"
    inspected = next(h for h in comp["history"] if h["state"] == "inspected")
    assert inspected["at"] == late["event_time"]  # event time, not arrival time
    assert [h["at"] for h in comp["history"]] == sorted(h["at"] for h in comp["history"])
    assert any(f["flag"] == "late_event_reconciled" for f in comp["flags"])
