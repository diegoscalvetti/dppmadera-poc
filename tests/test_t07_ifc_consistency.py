"""T7 IFC consistency.

Pass criterion: fault F1 is detected.
Paper link (Calvetti & Méndez 2026, Buildings 16:4411): IFC GUID mapping.
"""

from conftest import by_code


def test_ifc_consistency(replayed):
    client, results, data = replayed
    claimant, owner = data["ground_truth"]["faults"]["F1_ifc_guid_clash"]["components"]
    comps = by_code(data)
    clashes = [c for c in client.get("/conflicts").json()["conflicts"] if c["kind"] == "identifier_clash"]
    assert len(clashes) == 1
    rejected = clashes[0]["rejected_mapping"]
    assert {rejected["a"], rejected["b"]} == {comps[claimant]["ids"]["occurrence_id"], comps[owner]["ids"]["ifc_guid"]}
    # the owner's GUID still resolves to the owner only
    r = client.get(f"/resolver/{comps[owner]['ids']['ifc_guid']}").json()
    assert r["ids"]["instance_id"] == [comps[owner]["ids"]["instance_id"]]
    disputed = {n for n, s in results["assembly_state"].items() if "identifier_dispute" in s["flags"]}
    assert disputed == {claimant, owner}
