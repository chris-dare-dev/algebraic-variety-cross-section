# Test suggester suggestions — restructure-full-audit-2026q2-r1

**Commit range:** c7b2bd869aaea9b1d6c50ab199dd7f65ed48e95c..5f38db3df2b85694f7903542c002ab6efae2f46b
**Categories reviewed:** 10
**Suggestions:** 2

---

## Why these are SUGGESTIONS, not tests

Per scout-C §10.1, restructure PRs do not introduce new feature work or new tests beyond the shim-safety net that shipped with Batch 4. These tests should be considered for a follow-up milestone. The architect surfaces them now so the user can scope a `post-restructure-full-audit-2026q2-r1-test-hardening-2026q3-e1` milestone if desired.

---

## Suggested test set

### Suggestion 1: entrypoint cyclic-import smoke (subprocess)

**Gap category:** #10 — cyclic-import-under-entrypoint smoke (scout-C §8, row 10)

**Why now:** Batch 4 introduced the `panels/` subpackage and four root-level `__getattr__` shim files. The import graph around `app.py` now has a new layer: `app.py → panels.appearance / panels.parameters / panels.view` (direct, post-LibCST rewrite) while the four shim files at `appearance_panel.py`, `view_panel.py`, `parameters_panel.py`, and `parameter_grid_panel.py` each re-import from `panels.*` on attribute access. A cycle would arise if any module in the `panels.*` tree imported back to a shim or to `app.py`; pytest's module-import order can paper over such a cycle (modules are partially cached), but `python -c "import app"` under a clean process exposes it. The implementer confirmed `python -c "import app"` passed at Op 6 of Batch 4, but that confirmation is currently undocumented as a pytest test — it exists only in the batch log. Encoding it as a test means future refactors (especially `app.py` Extract Class or the `surfaces-split` milestone) will get a free regression guard.

**Test outline:**
```python
# tests/test_entrypoint_smoke.py — SUGGESTION ONLY, not yet written
"""Smoke test: `import app` must succeed in a clean subprocess.

Regression guard for cyclic-import chains introduced or made possible by:
  - panels/ subpackage (restructure-full-audit-2026q2-r1 batch 4)
  - any future app.py Extract Class milestone
  - any future surfaces-split milestone

Why subprocess: pytest's in-process sys.modules cache can paper over cycles
(a partially-initialised module is already present when the cycle is
encountered). A fresh subprocess catches cycles the test runner misses.

AI-2 compliant: never constructs QApplication / MainWindow; does not import
PySide6 directly. The subprocess does — but the test process itself is Qt-free.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VENV_PYTHON = REPO_ROOT / ".venv" / "bin" / "python"


def _python() -> str:
    return str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable


def test_import_app_no_cycle() -> None:
    """python -c 'import app; print("OK")' must exit 0 with no ImportError."""
    result = subprocess.run(
        [_python(), "-c", "import app; print('OK')"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        f"'import app' failed (exit {result.returncode}).\n"
        f"stdout: {result.stdout.strip()}\n"
        f"stderr: {result.stderr.strip()[:500]}"
    )
    assert "OK" in result.stdout


def test_import_panels_subpackage_no_cycle() -> None:
    """python -c 'import panels' must exit 0 — panels/__init__.py must be cycle-free."""
    result = subprocess.run(
        [_python(), "-c", "import panels; print('OK')"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        f"'import panels' failed (exit {result.returncode}).\n"
        f"stdout: {result.stdout.strip()}\n"
        f"stderr: {result.stderr.strip()[:500]}"
    )
    assert "OK" in result.stdout
```

**AI-invariant constraint:** AI-2-compliant. The TEST process never imports PySide6, never constructs a QApplication, never constructs MainWindow. A subprocess handles `import app` (which does import PySide6). The test only checks process exit code and stdout — this is the same pattern used by `test_qsettings_persistence.py`'s source-text-grep pattern for AI-2/AI-3 compliance, extended to subprocess-level.

**Estimated effort:** S (30–45 min including CI plumbing check)

**Note on macOS CI:** `import app` triggers PySide6 and pyvistaqt imports but does NOT construct a QApplication or a VTK render context (those happen inside `if __name__ == "__main__"`), so there is no macOS Qt+VTK offscreen segfault risk (per AI-3's clarifying scope note). The subprocess exits after the module-level import completes.

---

### Suggestion 2: shim `__getattr__` round-trip coverage — all four canonical symbols

**Gap category:** #3 — import-time side effects (scout-C §8, row 3)

**Why now:** The existing `tests/test_panels_shims.py` (4 tests, shipped in Batch 4) verifies that each shim emits a `DeprecationWarning` when a named symbol is fetched via `__getattr__`. What it does NOT verify is that the returned object is actually the *same* class as the canonical `panels.*` import. If a shim's `_ns` lookup fetches from `panels.appearance.__dict__` but `AppearancePanel` has been redefined or shadowed between the shim's `import` and the lookup (e.g. by a future `panels/__init__.py` re-export), the shim would emit the warning but return the wrong class. This is an import-time side-effect gap: the shim's `__getattr__` lazy-imports `panels.appearance.__dict__` on every call, so its correctness depends on `panels/appearance.py` not having module-scope mutations that alter the class between first and second lookup. A round-trip identity test (`old_path.Class is canonical_path.Class`) closes this.

**Test outline:**
```python
# tests/test_panels_shims.py (additions) — SUGGESTION ONLY, not yet written
# These would extend the existing test_panels_shims.py (or live in a new file).
"""Round-trip identity: shim must return the *same object* as the canonical import."""
import sys
import importlib
import warnings


def _flush(name: str) -> None:
    sys.modules.pop(name, None)


def test_appearance_panel_shim_identity() -> None:
    """appearance_panel.AppearancePanel is panels.appearance.AppearancePanel (same object)."""
    import panels.appearance as canonical

    _flush("appearance_panel")
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        from appearance_panel import AppearancePanel as via_shim  # noqa: F401

    assert via_shim is canonical.AppearancePanel, (
        "Shim returned a different object than the canonical import; "
        "panels/__init__.py or panels/appearance.py may shadow the class."
    )


def test_view_panel_shim_identity() -> None:
    """view_panel.ViewPanel is panels.view.ViewPanel (same object)."""
    import panels.view as canonical

    _flush("view_panel")
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        from view_panel import ViewPanel as via_shim  # noqa: F401

    assert via_shim is canonical.ViewPanel


def test_parameters_panel_shim_identity() -> None:
    """parameters_panel.ParametersPanel is panels.parameters.ParametersPanel (same object)."""
    import panels.parameters as canonical

    _flush("parameters_panel")
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        from parameters_panel import ParametersPanel as via_shim  # noqa: F401

    assert via_shim is canonical.ParametersPanel


def test_parameter_grid_panel_shim_identity() -> None:
    """parameter_grid_panel.ParameterGridPanel is panels.parameter_grid_panel.ParameterGridPanel."""
    import panels.parameter_grid_panel as canonical

    _flush("parameter_grid_panel")
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        from parameter_grid_panel import ParameterGridPanel as via_shim  # noqa: F401

    assert via_shim is canonical.ParameterGridPanel
```

**AI-invariant constraint:** AI-2-compliant. Import-only tests. The identity check (`is`) operates on class objects, not instances — no QApplication, no widget construction, no event loop. Same compliance level as the existing `test_panels_shims.py`.

**Estimated effort:** S (15–20 min; these are 4 near-identical stubs that extend the existing test file)

---

## Note on validate-shims.py tooling gap (NOT a test suggestion)

The implementer batch log and PLAN.md §5 note that `scripts/repository-architect/validate-shims.py` is used to smoke-test shims. Inspection of `validate-shims.py` (lines 71–74) reveals a bug: when `e["kind"] == "module"`, the script uses `stmt = f"import {old_mod}"` instead of `f"from {old_mod} import {symbol}"`. A bare `import appearance_panel` does NOT trigger `__getattr__` — Python loads the module object itself without accessing any attribute. The shim's `__getattr__` only fires on attribute access (e.g. `from appearance_panel import AppearancePanel`). This means `validate-shims.py` would report a false PASS for all 4 panel shims when called with `--batch 4`, because `import appearance_panel` exits 0 without ever emitting a DeprecationWarning.

This is a **script bug, not a project test gap** — the `tests/test_panels_shims.py` tests added in Batch 4 use `from <old_module> import <Class>` and correctly catch the warning. The gap is that `validate-shims.py` (an architect tooling script) gives a false green for module-kind shims. This should be fixed in a future `/repository-architect` tooling pass. It is noted here so the user is aware, not proposed as a new test.

---

## Categories with NO suggestions

| # | Category | Verdict | Reason |
|---|---|---|---|
| 1 | conftest scope drift | NO GAP | AVC has no conftest.py. The flat `tests/` layout is preserved. No test files were moved across conftest scopes. |
| 2 | Implicit fixture sharing | NO GAP | No conftest, no shared fixtures in the repo. Cannot introduce implicit fixture sharing without a conftest. |
| 3 | Import-time side effects | PARTIAL — see Suggestion 2 | The shim `__getattr__` pattern has a lazy import-time side effect: `panels.appearance` is imported inside `__getattr__` the first time a symbol is requested. This is deliberate and correct per Template-2. Suggestion 2 adds identity verification to guard against future shadow regressions. |
| 4 | Plugin discovery | NO GAP | No `pytest_plugins` declarations anywhere. `pytest.ini` has `testpaths = tests` only. No plugin rescoping occurred. |
| 5 | Seam tests between newly-split modules | NO GAP (Batch 5 deferred) | Would apply to `surfaces.py → _field_kernels.py` split. DEFERRED per PLAN.md v2 HIGH-1. The panels/ subpackage is a grouping move, not a logic split — no new internal seam between panel classes was introduced. |
| 6 | GUI / Qt event-loop integration | NO GAP | AI-2 explicitly forbids pytest-qt. Panel class bodies are unchanged; only their module paths moved. No signal wiring was touched. No suggestion is valid without lifting AI-2 (which would require a separate user decision). |
| 7 | VTK pipeline wiring | NO GAP | Zero VTK code was touched in any batch. `surfaces.py`, `_marching_cubes_to_polydata`, and `_grid_to_polydata` are unchanged. |
| 8 | Settings persistence boundary | NO GAP | `app.py`'s QSettings calls are unchanged (Batch 4's LibCST rewrite was import-only; QSettings code is in the class body, not at module scope). Key namespace unchanged. The existing `tests/test_qsettings_persistence.py` source-text-grep tests are sufficient. |
| 9 | Star-import shadow | NO GAP | Post-restructure `post.starimports.txt` confirms zero star-imports in production code (consistent with evaluator c16 PASS from the audit). `panels/__init__.py` uses no star-imports (13-line docstring file only). The 4 shim files use no star-imports. |
| 10 | Cyclic-import-under-entrypoint smoke | GAP — see Suggestion 1 | New `panels/` subpackage creates a new import-path graph layer. A subprocess-based smoke test encodes the implementer's manual verification as a repeatable assertion. |

---

## Recommended follow-up milestone

- **Name suggestion:** `post-restructure-full-audit-2026q2-r1-test-hardening-2026q3-e1`
- **Estimated total effort:** S (under 2 hours combined for both suggestions)
- **Priority:** M (medium)
  - Suggestion 1 (cyclic-import smoke) is **H** priority if the `app.py` Extract Class or `surfaces-split` milestone is scheduled soon — those restructures are exactly where import cycles could be introduced, and the test would catch them on the first CI run rather than in a post-deploy smoke.
  - Suggestion 2 (shim identity round-trip) is **L** priority — it catches a class-shadow regression that is unlikely before the shims are removed in M+1, but cheap to add.
- **AI-invariant proximity:** both suggestions are AI-2-clean by construction. No invariant lift required.

---

## Tooling recommendation (out of scope for this milestone, noted for the next `/repository-architect` run)

Fix `validate-shims.py` lines 71–74: for `kind == "module"` entries, use `from {old_mod} import {symbol}` (not `import {old_mod}`) so the bare-module `import` path does not silently skip `__getattr__`. This is an architect-tooling issue, not a project test gap.
