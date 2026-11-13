"""T9 Unified view.

Pass criterion: GET /assets/{id} returns DPP + EPM + DBL + DTw links for each component.
Paper link (Calvetti & Méndez 2026, Buildings 16:4411): Table 14.
"""

from conftest import by_code


def test_unified_view(replayed):
    client, _, data = replayed
    for code, comp in by_code(data).items():
        for q in (comp["ids"]["instance_id"], comp["ids"]["ifc_guid"]):
            view = client.get(f"/assets/{q}").json()
            for domain in ("dpp", "epm", "dbl", "dtw"):
                assert view[domain] and view[domain]["href"].startswith(f"/{domain}"), (code, q, domain)
            assert view["ids"]["instance_id"] == [comp["ids"]["instance_id"]]
