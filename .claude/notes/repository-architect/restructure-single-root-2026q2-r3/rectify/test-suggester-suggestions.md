# Test-suggester suggestions — restructure-single-root-2026q2-r3

**Commit range:** `7cb2a78..1419d03` (9 source commits, 5 batches B1-B5)
**Categories reviewed:** 10 (scout-C §8) + 4 r3-specific (A-D)
**Suggestions:** 5
**Status:** complete

---

## Why these are SUGGESTIONS, not tests

Per scout-C §10.1, restructure PRs do not introduce new feature work or new
tests beyond what B5 already landed (`test_import_smoke.py`). These tests
should be considered for the follow-on
`post-restructure-single-root-2026q2-r3-test-hardening` milestone. The
architect surfaces them now so the user can scope that milestone.

---

## r2 deferral disposition (confirm first)

| r2 Suggestion | r3 disposition |
|---|---|
| **Suggestion 1** — Numba threading-layer subprocess smoke | STILL DEFERRED. `test_import_smoke.py` imports `varieties` (which transitively imports `varieties._kernels`) but asserts only that `import varieties` exits 0 — it does NOT assert `THREADING_LAYER == "workqueue"`. Gap confirmed open. |
| **Suggestion 2** — cyclic-import smoke | LANDED. `tests/test_import_smoke.py` (B5, commit 003c155) — 5 parametrized entries cover `varieties`, `render`, `_qt`, `cross_section`, `app`. Closed. |
| **Suggestion 3** — varieties.registry consistency | STILL DEFERRED. No test in the 504-test suite asserts that each `VARIETIES` entry has a callable `.generate` that returns a non-empty mesh. Gap confirmed open. |

---

## Suggested test set

### Suggestion 1: Numba threading-layer side-effect assertion (CARRIED FROM r2)

**Gap category:** Scout-C §8 #3 — import-time side effects
**Status:** DEFERRED-TO-POST-R3-TEST-HARDENING
**Why now:** `varieties/_kernels.py` sets `numba.config.THREADING_LAYER = "workqueue"`
at module scope, before `from numba import njit`. This ordering is the critical
invariant documented in the `_kernels.py` docstring (HIGH-2 in the design-adversary
review). `test_import_smoke.py` verifies that `import varieties` succeeds but does NOT
assert the threading-layer value. A future restructure that moves `_kernels.py` or
reorders its imports could silently set the wrong threading layer, producing subtle
VTK/Numba threading conflicts on macOS at runtime — invisible to the test suite.

**Test outline:**
```python
# tests/test_numba_threading_layer.py — SUGGESTION ONLY, not yet written
def test_threading_layer_is_workqueue_after_kernels_import():
    """varieties._kernels must set THREADING_LAYER='workqueue' before @njit compile.

    Subprocess isolates the import to a clean sys.modules — no other test's
    transitive import of numba can pre-empt the side-effect check.
    """
    import subprocess, sys
    result = subprocess.run(
        [sys.executable, "-c",
         "import varieties._kernels; import numba; "
         "print(numba.config.THREADING_LAYER)"],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "workqueue", (
        f"Expected THREADING_LAYER='workqueue', got: {result.stdout.strip()!r}"
    )
```

**AI-invariant constraint:** AI-2 compliant — subprocess keeps no QApplication in
the test process. Numba is a pure-math dependency; no Qt involved.
**Estimated effort:** S (20 LOC, 1 test)
**Priority:** HIGH — this invariant is explicitly documented in `_kernels.py` as a
VTK-compatibility hard requirement. It is the only load-bearing import-ordering
constraint in the repo with no test coverage.

---

### Suggestion 2: varieties.registry consistency (CARRIED FROM r2, NOW MORE URGENT)

**Gap category:** Scout-C §8 #5 — seam tests between newly-split modules
**Status:** DEFERRED-TO-POST-R3-TEST-HARDENING
**Why now (r3-specific):** B4 retired `surfaces.py` and rewrote all 23 import sites
to `varieties.*`. The registry is now the SOLE authoritative source for `VARIETIES`.
Before r3, a broken generator reference would have been detected through the shim
path during `test_r2_shims.py`. That shim test was deleted in B3. The seam between
`varieties/registry.py` (which names generators) and `varieties/{k3,enriques,
calabi_yau,fano}.py` (which define them) is now naked — no test exercises it
end-to-end. VarietyGenerator Protocol was added in B2, but it is not yet used in
any `isinstance` check.

**Test outline:**
```python
# tests/test_varieties_registry_consistency.py — SUGGESTION ONLY, not yet written
import pytest

def test_every_variety_generator_callable():
    """Every VARIETIES entry must have a callable .generate."""
    from varieties.registry import VARIETIES
    for family, subtypes in VARIETIES.items():
        for subtype, surface in subtypes.items():
            assert callable(surface.generate), (
                f"VARIETIES[{family!r}][{subtype!r}].generate is not callable"
            )

def test_every_variety_generator_satisfies_protocol():
    """Every registered generator must satisfy VarietyGenerator Protocol."""
    from varieties.registry import VARIETIES
    from varieties.types import VarietyGenerator
    for family, subtypes in VARIETIES.items():
        for subtype, surface in subtypes.items():
            assert isinstance(surface.generate, VarietyGenerator), (
                f"VARIETIES[{family!r}][{subtype!r}].generate does not satisfy "
                f"VarietyGenerator Protocol"
            )

def test_every_variety_generator_returns_nonempty_mesh():
    """Each generator must return a non-empty PolyData at its default params."""
    from varieties.registry import VARIETIES
    for family, subtypes in VARIETIES.items():
        for subtype, surface in subtypes.items():
            mesh = surface.generate(**surface.defaults())
            assert mesh.n_points > 0, (
                f"VARIETIES[{family!r}][{subtype!r}] returned empty mesh at defaults"
            )
```

**AI-invariant constraint:** AI-2 compliant — no Qt. The generator functions are
pure-math; `pv.PolyData` has no Qt dependency.
**Note:** `test_every_variety_generator_returns_nonempty_mesh` runs all 14
generators and will take ~5-10 s. Consider marking it `@pytest.mark.slow` and
configuring `pytest -m "not slow"` as the default fast-path run.
**Estimated effort:** M (40 LOC, 3 tests)
**Priority:** HIGH — seam between registry and generator modules is now naked;
this was AI-8-adjacent in r2 and more exposed after B3 deleted the shim tests.

---

### Suggestion 3: import-linter contract regression smoke (r3-NEW gap A)

**Gap category:** Scout-C §8 #3 — import-time side effects (enforcement boundary)
**Status:** DEFERRED-TO-POST-R3-TEST-HARDENING
**Why now:** r3 B5 added two import-linter contracts to `pyproject.toml` and
confirmed both pass at HEAD (`lint-imports` exits 0). But `lint-imports` is NOT
run by `pytest` — it is only run by the architect's B5 verification step and by
developers who remember to run it manually. A future PR that adds
`from PySide6 import Something` to `varieties/*.py` (violating the
"varieties is pure-math" contract) will not fail `python -m pytest -q`. It will
only fail `lint-imports`, which is not in the CI test matrix. A thin subprocess
wrapper integrates this into the normal `pytest` run.

**Test outline:**
```python
# tests/test_import_linter_contracts.py — SUGGESTION ONLY, not yet written
import shutil, subprocess, sys

def test_lint_imports_contracts_pass():
    """lint-imports must exit 0 (both layer-direction contracts KEPT).

    Integrates import-linter into the pytest run so a future PR that
    introduces a cross-layer import (e.g. PySide6 into varieties/) fails CI
    rather than only failing a developer's manual lint step.
    """
    if shutil.which("lint-imports") is None:
        pytest.skip("import-linter not installed in this environment")
    result = subprocess.run(
        ["lint-imports"],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, (
        f"lint-imports reported broken contracts:\n{result.stdout}\n{result.stderr}"
    )
```

**AI-invariant constraint:** AI-2 compliant — no Qt. `lint-imports` is a pure
static-analysis tool; subprocess is used only to capture exit code.
**Estimated effort:** S (20 LOC, 1 test)
**Priority:** MEDIUM — the contracts exist; this test would close the gap between
"contracts exist in pyproject.toml" and "contracts are enforced on every `pytest`
run." Lower priority than Suggestions 1-2 because the contracts are new and stable
at HEAD; the risk accrues as the codebase evolves.

---

### Suggestion 4: single-root invariant test (r3-NEW gap C)

**Gap category:** Scout-C §8 #9 — star-import shadow (structurally closest;
more precisely: a "layout invariant" category not in the standard 10)
**Status:** DEFERRED-TO-POST-R3-TEST-HARDENING
**Why now:** r3's primary goal was `ls *.py | wc -l == 1`. The B5 verification
step confirmed this at HEAD. But no test guards it going forward. A future PR
that adds a convenience script at the repo root (e.g. `run_tests.py`,
`generate_docs.py`) would silently re-violate the single-root invariant without
any test failure. Given the effort that went into r3, a 10-LOC guard is cheap
insurance.

**Test outline:**
```python
# tests/test_single_root.py — SUGGESTION ONLY, not yet written
from pathlib import Path

def test_only_app_py_at_root():
    """Exactly one .py file must exist at the repo root: app.py.

    Guards the single-root invariant established by r3. Any new *.py added
    at root violates the layer-direction architecture and should be placed
    in the appropriate subpackage instead.
    """
    repo_root = Path(__file__).parent.parent  # tests/ -> repo root
    root_py_files = sorted(repo_root.glob("*.py"))
    assert root_py_files == [repo_root / "app.py"], (
        f"Expected only app.py at root; found: {[f.name for f in root_py_files]}"
    )
```

**AI-invariant constraint:** AI-2 compliant — no Qt. Pure filesystem check using
`pathlib`.
**Estimated effort:** S (15 LOC, 1 test)
**Priority:** LOW-MEDIUM — the invariant is stable at HEAD; the test is trivial to
add and cheap to run. Recommended as the first item in the hardening milestone
because it's the simplest and most directly tied to r3's stated goal.

---

### Suggestion 5: VarietyGenerator Protocol structural conformance (r3-NEW gap B)

**Gap category:** Scout-C §8 #5 — seam tests
**Status:** DEFERRED-TO-POST-R3-TEST-HARDENING
**Why now:** `VarietyGenerator` was added in B2 as `@runtime_checkable`. It is
never checked at runtime, and the existing test suite contains zero references to
it (confirmed by grep). This means the Protocol is currently documentation-only:
a new generator added by a contributor that happens to return `None` instead of
`pv.PolyData`, or that uses positional args instead of `**kwargs: float`, would
pass every existing test. The `isinstance` check is what makes `@runtime_checkable`
useful.

This suggestion is partially subsumed by Suggestion 2's
`test_every_variety_generator_satisfies_protocol` test. If Suggestion 2 is adopted,
Suggestion 5 is automatically covered. Listed separately to flag the Protocol's
current zero-test state explicitly.

**Test outline:** (see Suggestion 2 — `test_every_variety_generator_satisfies_protocol`)

**AI-invariant constraint:** AI-2 compliant — no Qt.
**Estimated effort:** COVERED by Suggestion 2 (no separate file needed)
**Priority:** HIGH — but only if Suggestion 2 is NOT adopted. If Suggestion 2
lands, close this suggestion as resolved.

---

## Categories with NO suggestions

| # | Category | r3 verdict |
|---|---|---|
| 1 | conftest scope drift | No `conftest.py` exists in `tests/`. No test files moved between conftest scopes. No gap. |
| 2 | implicit fixture sharing | No new fixtures introduced. No test files crossed scope boundaries. No gap. |
| 4 | plugin discovery | No `pytest_plugins` declarations in any conftest. B5 added a test file; no plugin rescoping. No gap. |
| 6 | GUI / Qt event-loop integration | AI-2 blocks pytest-qt per CLAUDE.md. No panel classes moved in r3 (they were moved in r2). No gap. |
| 7 | VTK pipeline wiring | No generator functions moved in r3. `varieties/{k3,enriques,calabi_yau,fano}.py` are unchanged. Pipeline ownership unchanged. No gap. |
| 8 | settings persistence | No `QSettings` keys moved or renamed. `test_qsettings_persistence.py` continues to cover the existing keys. No gap. |
| 9 | star-import shadow | Confirmed: zero `from X import *` in production code (checked: no star imports in any `varieties/`, `_qt/`, `render/`, `cross_section/` file). `surfaces.py` deletion removed the last re-export hub. No gap. |
| 10 | cyclic-import smoke | LANDED in B5 as `tests/test_import_smoke.py` (5 tests, 504 total). Closed. |

---

## Recommended follow-up milestone

- **Name suggestion:** `post-restructure-single-root-2026q2-r3-test-hardening-2026q3-e1`
- **Ordered by priority:**
  1. Suggestion 1 — Numba threading-layer (S, HIGH) — unique gap, no partial coverage exists
  2. Suggestion 2 — registry consistency + Protocol conformance (M, HIGH) — closes seam left naked by B3 shim deletion
  3. Suggestion 4 — single-root invariant (S, LOW-MEDIUM) — cheap, directly defends r3's goal
  4. Suggestion 3 — lint-imports in pytest (S, MEDIUM) — integrates existing tooling into CI loop
  5. Suggestion 5 — Protocol structural conformance (covered by #2)
- **Estimated total effort:** M (1 new test file for Suggestion 1 + 1 for Suggestion 2 + 1 for Suggestion 3 + 1 for Suggestion 4 = 4 files, ~95 LOC)
- **Priority:** HIGH for items 1-2; MEDIUM for items 3-4
- **AI-invariant proximity:** Suggestion 1 is adjacent to a macOS-only runtime crash
  (VTK/Numba threading conflict); Suggestion 2 is adjacent to AI-8 (VARIETIES
  contract). Both are in the HIGH tier.
