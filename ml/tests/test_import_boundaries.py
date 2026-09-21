"""Enforces the one-way dependency rule: `inference` (production) must never import
`training` (training-only) or `data` (dataset-build-only), directly or transitively, so a
production deployment can skip installing anything training-only needs.
"""

from __future__ import annotations

import ast
from pathlib import Path

INFERENCE_DIR = Path(__file__).resolve().parents[1] / "src" / "copilot_ml" / "inference"
FORBIDDEN_PREFIXES = ("copilot_ml.training", "copilot_ml.data")


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text("utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_inference_does_not_import_training_or_data() -> None:
    violations: dict[str, set[str]] = {}
    for path in INFERENCE_DIR.rglob("*.py"):
        forbidden = {
            m
            for m in _imported_modules(path)
            if any(m == p or m.startswith(p + ".") for p in FORBIDDEN_PREFIXES)
        }
        if forbidden:
            violations[str(path)] = forbidden

    assert not violations, f"inference/ imports training-only or data-only modules: {violations}"
