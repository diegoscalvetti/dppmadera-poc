"""T4 Custody gap detection.

Pass criterion: fault F4 is detected and reported.
Paper link (Calvetti & Méndez 2026, Buildings 16:4411): custody events.
"""


def test_custody_gap(replayed):
    _, results, data = replayed
    fault = data["ground_truth"]["faults"]["F4_custody_gap"]
    with_gap = {name for name, s in results["assembly_state"].items() if "custody_gap" in s["flags"]}
    assert with_gap == set(fault["components"])
    comp = next(c for c in data["components"] if c["code"] in fault["components"])
    client = replayed[0]
    assert client.get(f"/dpp/lineage/{comp['ids']['instance_id']}").json()["custody_gaps"] == [fault["missing"]]
