"""Build results/results.md: the T1-T11 results table plus the stakeholder-question indicators."""

import ast
import json
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def doc(path: Path) -> tuple[str, str, str]:
    d = ast.get_docstring(ast.parse(path.read_text(encoding="utf-8"))) or ""
    lines = [x.strip() for x in d.splitlines() if x.strip()]
    title = lines[0].rstrip(".")
    crit = " ".join(lines[1:]).split("Pass criterion:")[1].split("Paper link")[0].strip()
    tail = d.split("Paper link")[1] if "Paper link" in d else ""
    paper = (tail.split("):", 1)[1] if "):" in tail else tail.split(":", 1)[-1]).strip().rstrip(".")
    return title, crit[:1].upper() + crit[1:], paper[:1].upper() + paper[1:]


def main() -> None:
    junit = ET.parse(ROOT / "results" / "junit.xml").getroot()
    outcome = {}
    for tc in junit.iter("testcase"):
        failed = tc.find("failure") is not None or tc.find("error") is not None
        skipped = tc.find("skipped") is not None
        outcome[tc.get("classname").split(".")[-1]] = "FAIL" if failed else "skipped" if skipped else "pass"
    rows = ["| # | Test | Pass criterion | Paper link | Result |", "|---|---|---|---|---|"]
    for p in sorted((ROOT / "tests").glob("test_t*_*.py")):
        title, crit, paper = doc(p)
        tid, name = title.split(" ", 1)
        rows.append(f"| {tid} | {name} | {crit} | {paper} | **{outcome.get(p.stem, 'not run')}** |")
    res = json.loads((ROOT / "results" / "results.json").read_text(encoding="utf-8"))
    q = ["| Question | Answer | Client requests | Manual look-ups (est.) |", "|---|---|---|---|"]
    for item in res["questions"]:
        ans = item["answer"]
        if isinstance(ans, dict):
            ans = f"instance found; storey {ans['storey']}; {ans['state']}; custody complete: {ans['custody_complete']}"
        elif ans and isinstance(ans[0], dict):
            ans = "; ".join(f"values {a['values']} ({a['status']})" for a in ans)
        else:
            ans = ", ".join(ans) or "none"
        q.append(f"| {item['question']} | {ans} | {item['api_calls']} | {item['manual_lookups_estimate']} |")
    total = len(rows) - 2
    passed = sum("**pass**" in r for r in rows)
    text = (f"# PoC results (seed {res['dataset']['seed']})\n\n{passed} of {total} tests pass.\n\n" + "\n".join(rows)
            + "\n\n## Stakeholder questions (illustrative, synthetic)\n\n" + "\n".join(q)
            + f"\n\nAssembly state: {res['summary']}. Replay ingest: {res['ingest']['api_calls']} API calls.\n")
    (ROOT / "results" / "results.md").write_text(text, encoding="utf-8")
    (ROOT / "docs" / "results.md").write_text(text, encoding="utf-8")  # committed snapshot
    print(text)


if __name__ == "__main__":
    main()
