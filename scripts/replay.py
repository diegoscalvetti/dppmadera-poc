"""Run the end-to-end replay and write results/results.json."""

import json
from pathlib import Path

from dppmadera.replay import run

res = run(out_dir=Path("results"))
print(json.dumps({"ingest": res["ingest"], "summary": res["summary"], "conflicts": res["conflicts"]["count"]}, indent=2))
for name, s in res["assembly_state"].items():
    if s["flags"]:
        print(f"  {name}: {s['state']:<10} {', '.join(s['flags'])}")
for q in res["questions"]:
    print(f"- {q['question']}\n    {q['answer']}  ({q['api_calls']} API calls vs ~{q['manual_lookups_estimate']} manual look-ups)")
