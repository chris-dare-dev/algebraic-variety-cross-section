# B5 Source Log — restructure-single-root-2026q2-r3
**Date:** 2026-05-24  
**Batch:** B5 source (1/2) — import-linter setup + test_import_smoke.py  
**Commit:** 003c155

---

## Step 0 — Brownfield pre-flight

**pip install:** `import-linter==2.11` installed (grimp-3.14, click-8.4.1 also installed as deps). Exit 0.

**Empty-contracts lint-imports:**
```
Analyzed 25 files, 39 dependencies.
Contracts: 0 kept, 0 broken.
```
Exit 0. Tooling confirmed working.

---

## (a) pyproject.toml [tool.importlinter] section

```toml
[tool.importlinter]
root_packages = ["varieties", "_qt", "render", "cross_section"]
include_external_packages = true

[[tool.importlinter.contracts]]
name = "varieties is pure-math (forbidden from importing app, _qt, panels, Qt)"
type = "forbidden"
source_modules = ["varieties"]
forbidden_modules = ["app", "_qt", "panels", "PySide6", "PyQt5", "PyQt6"]

[[tool.importlinter.contracts]]
name = "cross_section is pure-pipeline (forbidden from Qt)"
type = "forbidden"
source_modules = ["cross_section"]
forbidden_modules = ["_qt", "PySide6", "PyQt5", "PyQt6"]
```

No `render` contract added per FIX-FIRST-3 (render/worker.py:39 legitimately imports PySide6.QtCore for QRunnable).

**lint-imports with full contracts:**
```
Analyzed 38 files, 103 dependencies.

varieties is pure-math (forbidden from importing app, _qt, panels, Qt) KEPT
cross_section is pure-pipeline (forbidden from Qt) KEPT

Contracts: 2 kept, 0 broken.
```
Exit 0.

---

## requirements.txt diff

Added 1 line (alphabetically between `coverage` and `libcst`):
```
import-linter>=2.0,<3
```

---

## (b) tests/test_import_smoke.py

5 parametrized entries: `varieties`, `render`, `_qt`, `cross_section`, `app`.
Subprocess pattern per refactor-pattern-scout Topic 3. AI-2 compliant (no QApplication in test process).
File: `tests/test_import_smoke.py` (~42 LOC).

**pytest tests/test_import_smoke.py -v:**
```
tests/test_import_smoke.py::test_import_subprocess[varieties] PASSED
tests/test_import_smoke.py::test_import_subprocess[render] PASSED
tests/test_import_smoke.py::test_import_subprocess[_qt] PASSED
tests/test_import_smoke.py::test_import_subprocess[cross_section] PASSED
tests/test_import_smoke.py::test_import_subprocess[app] PASSED

5 passed in 1.66s
```

**Full pytest run:**
```
504 passed in 7.21s
```
Expected: 504 (499 + 5 new smoke tests). OK.

---

## Commit

- SHA: `003c155`
- Subject: `feat(restructure-single-root-2026q2-r3): add import-linter layer contract + cyclic-import smoke (B5 source 1/2)`
- Files: `pyproject.toml`, `requirements.txt`, `tests/test_import_smoke.py` (3 files, 62 insertions)
- Pushed: `fc6b15a..003c155 main -> main`

---

## Deviations

None. All steps matched the spec exactly.
- import-linter 2.11 satisfies `>=2.0,<3`.
- Both contracts KEPT at HEAD (no pre-existing violations).
- 504 collected matches PLAN.md §9 expected count.
- `app` subprocess test passed (QApplication is guarded behind `if __name__ == "__main__"` in main()).
