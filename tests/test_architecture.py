"""Guardrail for federated ownership: a domain service never imports another domain's module."""

import ast
from pathlib import Path

SERVICES = Path(__file__).resolve().parents[1] / "src" / "dppmadera" / "services"
DOMAINS = {"dpp", "epm", "dbl", "resolver", "dtw", "conflicts"}


def test_services_do_not_import_each_other():
    for path in SERVICES.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                last = node.module.split(".")[-1]
                names = {a.name for a in node.names}
                assert last not in DOMAINS - {path.stem}, f"{path.name} imports {node.module}"
                assert not (names & (DOMAINS - {path.stem})), f"{path.name} imports {names}"
