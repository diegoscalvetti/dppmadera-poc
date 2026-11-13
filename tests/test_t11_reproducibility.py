"""T11 Reproducibility.

Pass criterion: a clean checkout plus one command reproduces all results.
Paper link: none (good practice for the TRL 3 evidence).
"""

import json
import subprocess
import sys
from pathlib import Path

from dppmadera.generator import write
from dppmadera.replay import run

ROOT = Path(__file__).resolve().parents[1]


def _stable(res: dict) -> dict:
    res = json.loads(json.dumps(res))
    res.pop("ingest")
    for q in res["questions"]:
        q.pop("ms")
    return res


def test_reproducibility(tmp_path):
    manifest = json.loads((ROOT / "data" / "synthetic" / "manifest.json").read_text())
    assert write(tmp_path / "data", manifest["seed"])["sha256"] == manifest["sha256"]
    assert _stable(run(tmp_path / "data")) == _stable(run())
    # the one command used in the report
    out = subprocess.run([sys.executable, "scripts/replay.py"], cwd=ROOT, capture_output=True, text=True,
                         env={"PYTHONPATH": str(ROOT / "src"), "PATH": ""})
    assert out.returncode == 0, out.stderr
    assert (ROOT / "results" / "results.json").exists()
