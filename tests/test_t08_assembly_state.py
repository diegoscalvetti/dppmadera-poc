"""T8 Assembly-state view.

Pass criterion: DTw state matches the ground truth for all 20 components; fault F3 flagged.
Paper link (Calvetti & Méndez 2026, Buildings 16:4411): minimal DTw.
"""


def test_assembly_state(replayed):
    _, results, data = replayed
    gt = data["ground_truth"]
    assert {n: s["state"] for n, s in results["assembly_state"].items()} == gt["expected_state"]
    late, early = gt["faults"]["F3_out_of_sequence"]["components"]
    oos = {n for n, s in results["assembly_state"].items() if "out_of_sequence" in s["flags"]}
    assert oos == {late}
    client = replayed[0]
    state = client.get("/dtw/assembly-state", params={"building_id": gt["building_id"]}).json()
    flag = next(f for c in state["components"] if c["name"] == late for f in c["flags"] if f["flag"] == "out_of_sequence")
    assert flag["installed_before"] == [early]
