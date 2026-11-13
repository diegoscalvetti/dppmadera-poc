"""T3 Provenance completeness.

Pass criterion: the lineage of every component runs factory to as-built without gaps, or the gap is flagged.
Paper link (Calvetti & Méndez 2026, Buildings 16:4411): need for traceability.
"""

from conftest import by_code


def test_provenance_completeness(replayed):
    client, _, data = replayed
    expected = data["ground_truth"]["expected_state"]
    flagged = set()
    for code, comp in by_code(data).items():
        lin = client.get(f"/dpp/lineage/{comp['ids']['instance_id']}").json()
        occ = client.get(f"/dbl/occurrences/{comp['ids']['occurrence_id']}").json()
        steps = lin["custody_steps"]
        assert steps[0] == "commissioning" and steps[-1] == "receiving", code
        assert lin["product"]["process_run_ids"] and lin["product"]["certification_ref"], code
        assert bool(occ.get("installed_at")) == (expected[code] in {"installed", "inspected"}), code
        if not lin["complete"]:
            assert lin["custody_gaps"], code
            flagged.add(code)
    assert flagged == set(data["ground_truth"]["faults"]["F4_custody_gap"]["components"])
