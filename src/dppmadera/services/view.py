"""Assembly-state web view: a read-only HTML page over GET /dtw/assembly-state (for demos and the Delphi panel)."""

from __future__ import annotations

import html

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from . import _client as api

router = APIRouter(tags=["view"])

COLOURS = {"planned": "#d9d9d9", "produced": "#c6dbef", "dispatched": "#9ecae1", "delivered": "#fdd49e",
           "installed": "#fc8d59", "inspected": "#74c476"}
LABEL = {"custody_gap": "custody gap", "value_conflict": "moisture conflict", "identifier_dispute": "IFC GUID clash",
         "out_of_sequence": "out of sequence", "late_event_reconciled": "late event reconciled"}


@router.get("/view", response_class=HTMLResponse)
def view(building_id: str | None = None) -> str:
    if building_id is None:
        raise HTTPException(400, "add ?building_id=<id>; after `make demo` use the link printed in the terminal")
    s, st = api.get("/dtw/assembly-state", building_id=building_id)
    if s != 200:
        raise HTTPException(404, "unknown building; run the replay first (make demo)")
    rows = []
    for storey in sorted({c["storey"] for c in st["components"]}, reverse=True):
        cells = []
        for c in sorted((c for c in st["components"] if c["storey"] == storey), key=lambda c: c["planned_seq"]):
            flags = "".join(f"<div class='f'>{html.escape(LABEL.get(f['flag'], f['flag']))}</div>" for f in c["flags"])
            border = "3px solid #b30000" if c["flags"] else "1px solid #666"
            title = html.escape(f"{c['instance_id']}\nIFC {c['ifc_guid']}\nstate: {c['state']}")
            cells.append(f"<a class='c' href='/assets/{html.escape(c['instance_id'] or '')}' title='{title}' "
                         f"style='background:{COLOURS[c['state']]};border:{border}'><b>{html.escape(c['name'] or '')}</b>"
                         f"<span>#{c['planned_seq']} · {c['state']}</span>{flags}</a>")
        rows.append(f"<div class='r'><div class='l'>Level {storey}</div>{''.join(cells)}</div>")
    legend = "".join(f"<span class='k' style='background:{v}'>{k}</span>" for k, v in COLOURS.items())
    summary = ", ".join(f"{v} {k}" for k, v in st["summary"].items())
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Assembly state</title><style>
body{{font-family:system-ui,sans-serif;margin:24px;background:#fff;color:#222}}
.r{{display:flex;gap:8px;margin:10px 0;align-items:flex-start;overflow-x:auto}}.l{{flex:0 0 64px;font-weight:600;padding-top:18px}}
.c{{display:block;flex:0 0 104px;min-height:64px;padding:8px;border-radius:8px;color:#111;text-decoration:none}}
.c span{{display:block;font-size:12px;color:#333}}.f{{font-size:11px;color:#b30000;font-weight:600;margin-top:4px}}
.k{{display:inline-block;padding:2px 8px;margin-right:6px;border-radius:4px;font-size:12px}}
</style></head><body><h1>Synthetic CLT building: assembly state</h1>
<p>Derived live from the DPP, EPM and DBL services. {html.escape(summary)}; {st['flagged']} flagged. Synthetic data only.
Click a component for its federated record.</p><p>{legend}<span class='k' style='border:3px solid #b30000'>flagged</span></p>
{''.join(rows)}</body></html>"""
