"""T1 Identity resolution.

Pass criterion: any of the identifiers of a component resolves to all the others.
Paper link (Calvetti & Méndez 2026, Buildings 16:4411): §4, identity resolution.
"""

from conftest import by_code

QUERY_TYPES = ("instance_id", "batch_id", "ifc_guid", "occurrence_id")


def test_identity_resolution(replayed):
    client, _, data = replayed
    for code, comp in by_code(data).items():
        ids = comp["ids"]
        expected = {ids["product_id"], ids["instance_id"], ids["batch_id"], ids["ifc_guid"],
                    ids["occurrence_id"], *ids["process_run_ids"]}
        for q in [ids[t] for t in QUERY_TYPES] + ids["process_run_ids"]:
            r = client.get(f"/resolver/{q}").json()
            found = {i for group in r["ids"].values() for i in group}
            assert found == expected, (code, q)
            assert not r["ambiguous"], (code, q)
