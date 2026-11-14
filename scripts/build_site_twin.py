"""Write a static snapshot of the live assembly-state view (GET /view) into site/twin/.

The website must work offline and on any static host, so instead of the running server we
replay the synthetic building in-process, save the view as twin/index.html and each
component's federated record (GET /assets/{id}) as twin/records/<code>.json.
Run: PYTHONPATH=src python3 scripts/build_site_twin.py
"""

import json
import re
from pathlib import Path

from fastapi.testclient import TestClient

from dppmadera.app import app
from dppmadera.replay import load, run

OUT = Path(__file__).resolve().parents[1] / "site" / "twin"
BANNER = (
    "<div style='background:#fff4e5;border:1px solid #f0b46a;padding:10px 14px;border-radius:8px;margin-bottom:16px'>"
    "<b>Static snapshot.</b> This is the PoC's live assembly-state page, saved after replaying the invented "
    "building (seed 4411). Click a component to see its joined record as raw JSON. "
    "<a href='../index.html'>Back to the site</a></div>"
)


def safe(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", name)


def main() -> None:
    run()
    bid = load()["ground_truth"]["building_id"]
    c = TestClient(app)
    page = c.get("/view", params={"building_id": bid}).text
    (OUT / "records").mkdir(parents=True, exist_ok=True)
    state = c.get("/dtw/assembly-state", params={"building_id": bid}).json()
    for comp in state["components"]:
        iid, code = comp["instance_id"], safe(comp["name"])
        if not iid:
            continue
        rec = c.get(f"/assets/{iid}").json()
        (OUT / "records" / f"{code}.json").write_text(json.dumps(rec, indent=2, ensure_ascii=False), encoding="utf-8")
        page = page.replace(f"href='/assets/{iid}'", f"href='records/{code}.json'")
    page = page.replace("<body>", "<body>" + BANNER, 1)
    (OUT / "index.html").write_text(page, encoding="utf-8")
    print(f"wrote {OUT/'index.html'} and {len(list((OUT/'records').glob('*.json')))} records")


if __name__ == "__main__":
    main()
