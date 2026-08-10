from __future__ import annotations

import ast
from pathlib import Path


SERVICES_DIR = Path(__file__).resolve().parents[3] / "backend" / "services"


def test_services_do_not_import_api_modules() -> None:
    violations: list[str] = []

    for path in sorted(SERVICES_DIR.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("backend.api"):
                        violations.append(
                            f"{path.name}:{node.lineno}: import {alias.name}"
                        )

            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                imports_api = module.startswith("backend.api") or (
                    node.level > 0 and module.startswith("api")
                )
                if imports_api:
                    violations.append(
                        f"{path.name}:{node.lineno}: from {module}"
                    )

    assert violations == []
