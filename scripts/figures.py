"""Draw the assembly-state figure from results/results.json (run scripts/replay.py first)."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Patch  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
COLOURS = {"planned": "#d9d9d9", "produced": "#c6dbef", "dispatched": "#9ecae1", "delivered": "#fdd49e",
           "installed": "#fc8d59", "inspected": "#74c476"}
FLAG_LABEL = {"custody_gap": "custody gap", "value_conflict": "moisture conflict", "identifier_dispute": "IFC GUID clash",
              "out_of_sequence": "out of sequence", "late_event_reconciled": "late event reconciled"}


def main() -> None:
    res = json.loads((ROOT / "results" / "results.json").read_text(encoding="utf-8"))
    comps = json.loads((ROOT / "data" / "synthetic" / "components.json").read_text(encoding="utf-8"))
    state = res["assembly_state"]
    fig, ax = plt.subplots(figsize=(11, 5.6), dpi=200)
    for storey in range(1, 5):
        row = sorted((c for c in comps if c["storey"] == storey), key=lambda c: c["planned_seq"])
        y = storey - 1
        ax.text(-0.25, y + 0.4, f"Level {storey}", ha="right", va="center", fontsize=10, weight="bold")
        for x, c in enumerate(row):
            s = state[c["code"]]
            ax.add_patch(FancyBboxPatch((x + 0.05, y + 0.08), 0.9, 0.64, boxstyle="round,pad=0.02",
                                        fc=COLOURS[s["state"]], ec="#b30000" if s["flags"] else "#555555",
                                        lw=2.2 if s["flags"] else 0.8))
            ax.text(x + 0.5, y + 0.52, c["code"], ha="center", va="center", fontsize=10, weight="bold")
            ax.text(x + 0.5, y + 0.3, f"#{c['planned_seq']}", ha="center", va="center", fontsize=7, color="#333333")
            if s["flags"]:
                ax.text(x + 0.5, y + 0.0, "\n".join(FLAG_LABEL.get(f, f) for f in s["flags"]),
                        ha="center", va="top", fontsize=6.2, color="#b30000")
    ax.set_xlim(-1.3, 6.2)
    ax.set_ylim(-0.45, 4.0)
    ax.axis("off")
    handles = [Patch(fc=v, ec="#555555", label=k) for k, v in COLOURS.items() if k in {s["state"] for s in state.values()}]
    handles.append(Patch(fc="white", ec="#b30000", lw=2, label="flagged"))
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 1.07), ncol=len(handles), frameon=False, fontsize=9)
    ax.set_title("Synthetic CLT building: derived assembly state after replay (#n = planned sequence)", fontsize=11, pad=24)
    out = ROOT / "docs" / "figures" / "assembly_state.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, bbox_inches="tight")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
