"""Cyclic-import + side-effect smoke tests for r3's tree-like structure.

Per restructure-single-root-2026q2-r3 PLAN.md §7 row 10 + refactor-pattern-scout
Topic 3: subprocess pattern catches subtle cycles that pytest's sys.modules
cache would otherwise paper over.

AI-2 compliant: subprocess.run isolates each import in a fresh interpreter,
so no QApplication is constructed in the test process itself.

The 5 parametrized modules cover the post-r3 tree:
  - varieties  (pure math, no Qt)
  - render     (Qt thread worker)
  - _qt        (Qt adapter layer)
  - cross_section  (clip pipeline, no Qt)
  - app        (entry point — QApplication is inside main(), guarded by __name__)
"""
from __future__ import annotations

import subprocess
import sys

import pytest


@pytest.mark.parametrize(
    "module_name",
    ["varieties", "render", "_qt", "cross_section", "app"],
)
def test_import_subprocess(module_name: str) -> None:
    """`python -c 'import MODULE'` must succeed in a fresh subprocess.

    Catches cyclic-import bugs that pytest's collection-time sys.modules
    caching would hide.
    """
    result = subprocess.run(
        [sys.executable, "-c", f"import {module_name}"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        f"`import {module_name}` failed in fresh subprocess.\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )
