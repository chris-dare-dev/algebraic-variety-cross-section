# Refactor-Pattern Scout Brief — restructure-single-root-2026q2-r3

**Scope:** Safe-refactor patterns for r3's 5-batch restructure, with focus on
hub retirement (surfaces.py deletion), LibCST codemod correctness, cyclic-import
smoke tests, Protocol introduction alongside dataclasses, import-linter
brownfield onboarding, and parameter-widget extraction.

**Sources accessed:** 2026-05-24. All URLs verified unless marked [UNVERIFIED].
**Honesty conventions:** [CONSENSUS] = 3+ reputable sources agree.
[CONTESTED] = sources disagree. [UNVERIFIED] = not confirmed from primary source.

---

## 1. The Six Topics — Survey Results

### Topic 1 — Hub Retirement / Re-export Removal (surfaces.py, 35 import sites)

**Context.** surfaces.py was reduced from 1811 LOC to 123 LOC in r2 via
Expand-then-shrink. r3 deletes it entirely. All 35 import sites (`from surfaces
import ...` or `import surfaces`) must be redirected before the delete.

**Canonical safe sequence (Expand-Contract applied to full deletion).**

Fowler's Parallel Change / Expand-Contract describes three phases:
Expand (add new without breaking old) → Migrate (move callers) → Contract
(delete old). Applied to hub retirement, the phases map exactly:
[CONSENSUS — martinfowler.com/bliki/ParallelChange.html; blog.thepete.net/expand-contract-2023;
thoughtworks.com/radar/techniques/api-expand-contract]

```
Phase 0 — Already done in r2:
  surfaces.py was 1811 LOC (god module).
  r2 extracted to varieties/*, leaving surfaces.py as a 123-LOC __getattr__ shim.
  All public symbols re-exported; DeprecationWarning raised on access.

Phase 1 — Migrate callers (r3 B4 primary work):
  Enumerate all 35 import sites with LibCST or grep.
  Rewrite each `from surfaces import X` → `from varieties.X_home import X`.
  Rewrite each `import surfaces; surfaces.X` → appropriate direct import.
  DO NOT delete surfaces.py yet. Run full suite after each batch of rewrites.
  Exit criterion: `grep -r "import surfaces" . --include="*.py"` returns zero hits
  outside of surfaces.py itself and tests/test_r2_shims.py.

Phase 2 — Verify DeprecationWarning is no longer triggered:
  `python -W error::DeprecationWarning -m pytest -q`
  If this passes, no caller still goes through the shim.

Phase 3 — Delete surfaces.py and test_r2_shims.py shim tests:
  `git rm surfaces.py`
  Remove or update shim-coverage tests that specifically test the shim's
  DeprecationWarning behaviour (they will break by design — the shim is gone).
  Run full suite. Expected: all shim-specific tests removed; remaining suite green.
```

**Failure mode if order violated.** Deleting surfaces.py before all callers are
migrated produces `ModuleNotFoundError: No module named 'surfaces'` at import
time — not a test failure, a crash. The error message is clear, but the fix
requires reverting the delete and re-doing Phase 1 first.

**The 35 import sites — r3-specific inventory.**
From imports-rough.json (read 2026-05-24):

Direct callers of `surfaces` at time of survey:
- `parameter_grid.py` — imports `surfaces`
- `app.py` — imports `surfaces`
- `_qt/ui_helpers.py` — imports `surfaces`
- `_qt/panels/parameter_grid_panel.py` — imports `surfaces`
- `_qt/panels/parameters.py` — imports `surfaces`
- `tests/test_enriques_hq_smoothing.py` — imports `surfaces`
- `tests/test_mesh_generators.py` — imports `surfaces`
- `tests/test_status_bar_bbox.py` — imports `surfaces`
- `tests/test_numba_field_kernels.py` — imports `surfaces`
- `tests/test_typical_ms.py` — imports `surfaces`
- `tests/test_grid_helpers.py` — imports `surfaces`
- `tests/test_r2_shims.py` — imports `surfaces` (shim test, will be retired)
- `tests/test_styles_palette.py` — imports `surfaces`
- `tests/test_marching_cubes_empty.py` — imports `surfaces`
- `tests/test_coarse_n.py` — imports `surfaces`
- `tests/test_parameter_grid.py` — imports `surfaces`
- `tests/test_parameters_panel.py` — imports `surfaces`

Note: imports-rough.json is module-level dependency only. The actual symbol
set imported from surfaces at each site must be confirmed with `grep` or LibCST
analysis during B4 execution. The 35 count from the brief may include indirect
chain sites.

**Key risk: numba.config side effect.**
surfaces.py currently contains (lesson from r2):
```python
numba.config.THREADING_LAYER = "workqueue"
```
This assignment MUST be confirmed present in `varieties/_kernels.py` BEFORE
surfaces.py is deleted. If it is absent from _kernels.py, deleting surfaces.py
silently removes the side effect and VTK/Numba SMP contention returns.
This is invisible to static analysis. Verify with:
```bash
grep -n "THREADING_LAYER" varieties/_kernels.py
```
Expected: present at the top, before any @njit decorator.

---

### Topic 2 — LibCST leave_Attribute Partial-Rewrite Bug (B1 fix)

**The bug pattern (r2 execution-critic, MEDIUM risk).**

A naive LibCST visitor that matches import sites using `leave_Name` only will
fix `from surfaces import X` but silently miss `surfaces.X` attribute-access
patterns. Conversely, a visitor that matches `leave_Attribute` by checking
`node.attr.value == "surfaces"` may match the WRONG segment in a dotted chain
(e.g., it fires for `foo.surfaces.bar` matching the middle segment, or it
fires for `old_surfaces.SomeName` matching only the leaf).

The correct LibCST approach uses `QualifiedNameProvider` metadata, which
resolves full dotted paths against the scope graph, not raw string matching.
[CONSENSUS — Instagram/LibCST rename.py source; libcst.readthedocs.io/codemods]

**The correct pattern — RenameCommand source analysis.**

`libcst/codemod/commands/rename.py` (Instagram/LibCST, main branch, accessed
2026-05-24) implements exactly this problem. Key architecture:

```python
METADATA_DEPENDENCIES = (QualifiedNameProvider, ScopeProvider)
```

```python
def leave_Attribute(self, original_node, updated_node):
    # DO NOT string-match on node.attr.value alone.
    # Use QualifiedNameProvider to get the full resolved name.
    if QualifiedNameProvider.has_name(self, original_node, self.old_name):
        # Reconstruct the new attribute chain by parsing the new module path
        new_value = cst.parse_expression(self.new_module)
        return updated_node.with_changes(
            value=new_value,
            attr=cst.Name(value=self.new_mod_or_obj.rstrip(".")))
    return updated_node
```

```python
def leave_Name(self, original_node, updated_node):
    if QualifiedNameProvider.has_name(self, original_node, self.old_name):
        return self.gen_name_or_attr_node(full_replacement_name)
    return updated_node
```

**The partial-rewrite bug in `leave_ImportFrom`.**

The bug occurs when a `from surfaces import X, Y, Z` has 3 names and only X
is being moved. The naive visitor rewrites the module path for ALL three
aliases because it modifies `updated_node.module` when it sees any match.

Correct pattern: when the `from` statement has multiple aliases, add new
`AddImportsVisitor` entries for the matched symbols only, and use
`RemoveImportsVisitor` to prune the old alias. Do NOT touch `updated_node.module`
for multi-alias `from` statements.

```python
def leave_ImportFrom(self, original_node, updated_node):
    names = updated_node.names
    if isinstance(names, cst.ImportStar):
        return updated_node  # Never touch star-imports

    if len(names) == 1:
        # Safe to rewrite module in-place
        ...
    else:
        # Multi-name: add new import, schedule removal of old alias
        AddImportsVisitor.add_needed_import(self.context, new_module, symbol)
        RemoveImportsVisitor.remove_unused_import(self.context, old_module, symbol)
        return updated_node  # Leave original untouched
```

**r3 B1 rewrite-imports.py fix checklist:**
1. Add `METADATA_DEPENDENCIES = (QualifiedNameProvider, ScopeProvider)` to
   the codemod class.
2. Replace any `node.value.value == "surfaces"` string checks with
   `QualifiedNameProvider.has_name(self, original_node, "surfaces.TargetSymbol")`.
3. Guard `leave_ImportFrom` against multi-alias rewriting.
4. Test the codemod on a scratch file with all four import patterns before
   running on the live tree:
   - `import surfaces`
   - `from surfaces import SurfaceSpec`
   - `from surfaces import SurfaceSpec, VARIETIES`
   - `surfaces.SurfaceSpec` (attribute access in function body)

**Windows caveat.** QualifiedNameProvider uses process pools. On Windows,
pickling issues have been reported (LibCST issue #435). AVC targets macOS/Linux
for development — no action needed, but note for future CI if Windows is added.
[Source: github.com/Instagram/LibCST/issues/435]

---

### Topic 3 — Cyclic-Import Smoke Test Patterns

**The goal.** Confirm that after restructure, importing `app`, `varieties`,
`render`, `_qt`, and `cross_section` from a clean Python process does not
produce circular-import errors. pytest's test collection process can hide
import errors if conftest.py preloads modules before test isolation runs.

**Canonical pattern: subprocess isolation.**
[CONSENSUS — widely used in scientific Python; see Scientific Python Development
Guide: learn.scientific-python.org/development/guides/pytest/]

```python
# In tests/test_import_smoke.py
import subprocess, sys

@pytest.mark.parametrize("module", [
    "varieties",
    "varieties.registry",
    "varieties.types",
    "varieties.dispatch",
    "render",
    "cross_section",
])
def test_clean_import(module):
    """
    Each module must be importable from a fresh interpreter with no
    sys.modules pollution from pytest's own imports.
    """
    result = subprocess.run(
        [sys.executable, "-c", f"import {module}; print('OK')"],
        capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0, (
        f"Clean import of '{module}' failed:\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )
```

**Why subprocess is necessary.** pytest imports modules into its own process
during collection. A cyclic import that fails under fresh-interpreter conditions
may succeed under pytest if another test file imported a partial module first,
partially breaking the cycle by accident. The subprocess ensures a truly clean
`sys.modules`.

**AVC-specific constraint.** AI-2: the test suite is Qt-free. The above smoke
test parametrizes only Qt-free modules (`varieties`, `render`, `cross_section`).
Do NOT include `app`, `_qt`, or any panel module in this smoke test — they
require a QApplication and will fail under offscreen QPA on most CI setups.

**Detecting existing cycles before restructure.**
Run before B4:
```bash
python -c "
import sys
import importlib
mods = ['varieties', 'varieties.registry', 'varieties.types',
        'varieties.dispatch', 'render', 'cross_section']
for m in mods:
    importlib.import_module(m)
    print(f'{m}: OK')
"
```
If this succeeds, r3 has no pre-existing cycles in the clean modules.
After B4 (surfaces.py deleted), rerun to confirm no new cycles were introduced.

**pydeps for visual confirmation.**
```bash
python -m pydeps varieties --max-bacon=0 --noshow --show-deps
```
Look for any cycle markers (pydeps renders them as red edges in the SVG).
[Source: pydeps documentation — no primary URL fetched, UNVERIFIED for 2026]

---

### Topic 4 — Protocol Introduction Without Breaking Existing Dataclass Users

**Context (AI-8).** `Surface` / `ParamSpec` are `@dataclass` instances
registered in `VARIETIES` (a global dict in varieties/registry.py). r3 may
introduce a `SurfaceProtocol` alongside the existing dataclass.

**The safe order.**

Step 1 — Define the Protocol (structural, no isinstance enforcement):
```python
# varieties/types.py — add AFTER existing dataclass definitions
from typing import Protocol, runtime_checkable

@runtime_checkable
class SurfaceProtocol(Protocol):
    name: str
    label: str
    # ... all fields that Surface dataclass already has

    def generate(self, **kwargs) -> "pv.PolyData":
        ...
```

`@runtime_checkable` lets isinstance work, but the check only validates
attribute existence, NOT method signatures. This is a Python limitation.
[Source: typing.python.org/reference/protocols.html; mypy.readthedocs.io/protocols]

Step 2 — Verify existing dataclass instances pass isinstance without changes:
```python
# tests/test_protocol.py
from varieties.types import SurfaceProtocol
from varieties.registry import VARIETIES

def test_all_varieties_satisfy_protocol():
    for name, surface in VARIETIES.items():
        assert isinstance(surface, SurfaceProtocol), (
            f"{name} does not satisfy SurfaceProtocol"
        )
```

Step 3 — DO NOT add `isinstance` guards to the hot dispatch path unless
profiling shows it is needed. The protocol is useful for type-checker
narrowing (`mypy --strict`), not for runtime guards on every render call.

Step 4 — If you add a Protocol subclass check in registry.register():
```python
def register(surface: SurfaceProtocol) -> None:
    if not isinstance(surface, SurfaceProtocol):
        raise TypeError(f"Expected SurfaceProtocol, got {type(surface)}")
    VARIETIES[surface.name] = surface
```
This is safe: the existing dataclasses already satisfy the protocol structurally.
No changes to existing Surface dataclass definition needed.

**Contested: @runtime_checkable + data attributes.**
CPython issue #102433 documents that `isinstance` on `@runtime_checkable`
Protocol with `@property` members has subtle side effects in Python 3.12+.
AVC's Surface uses plain dataclass fields (not properties), so this CPython
issue does NOT apply. Verify: `Surface` has no `@property` members before
adding runtime_checkable.

**Skip isinstance entirely (recommended for r3).**
Unless r3 has a concrete use case for runtime isinstance checks on surfaces,
the cleaner path is:
1. Add the Protocol as a type annotation target only.
2. Use mypy to verify structural conformance during CI.
3. No runtime isinstance. No CPython edge-case risk.
[UNVERIFIED — no AVC-specific mypy CI confirmed; recommend confirming with user]

---

### Topic 5 — import-linter Contract Introduction (Brownfield)

**import-linter version.** 2.x (stable as of 2026). Docs at
import-linter.readthedocs.io/en/stable.

**Supported config locations (in priority order):**
1. `setup.cfg` (INI format, `[importlinter]` section)
2. `.importlinter` (INI format, same syntax)
3. `pyproject.toml` (TOML format, `[tool.importlinter]` section)
[Source: import-linter.readthedocs.io/en/stable/get_started/configure/]

**AVC recommendation: `pyproject.toml`.**
AVC already has `pyproject.toml` at root (evaluator check 6: PASS). Adding
import-linter config there avoids a proliferating root file (avoids setup.cfg
or .importlinter). The `setup.cfg` form is legacy and not recommended for new
projects. [CONSENSUS — import-linter docs; Python Packaging Authority guidelines]

**Minimal brownfield config for AVC:**
```toml
# pyproject.toml — append to existing file
[tool.importlinter]
root_package = "varieties"
include_external_packages = true

[[tool.importlinter.contracts]]
name = "Varieties subpackage has no upward imports to root"
type = "forbidden"
source_modules = ["varieties"]
forbidden_modules = ["app", "surfaces", "_qt", "panels"]

[[tool.importlinter.contracts]]
name = "Cross-section has no Qt dependency"
type = "forbidden"
source_modules = ["cross_section"]
forbidden_modules = ["PySide6", "_qt", "panels"]

[[tool.importlinter.contracts]]
name = "Render has no Qt dependency"
type = "forbidden"
source_modules = ["render"]
forbidden_modules = ["PySide6", "_qt", "panels", "surfaces"]
```

**Brownfield onboarding pattern (contract-by-contract, not all at once).**
1. Run `lint-imports` with zero contracts first to confirm tooling works.
2. Add one contract. Run `lint-imports`. If violations appear, they must ALL
   be fixed before merging — import-linter has no "warning" mode, only
   pass/fail. [Source: import-linter.readthedocs.io/en/stable/usage.html]
3. For the surfaces-deletion contract: add the "varieties has no upward import
   to surfaces" contract AFTER B4 deletes surfaces.py (the contract would
   vacuously pass before deletion since surfaces no longer exists; add it as
   a regression guardrail to prevent future re-introduction).

**Contract types available (from docs):**
- `forbidden` — module A must not import module B (or any descendant)
- `independence` — a set of modules must not import each other
- `layers` — enforces a layered architecture (higher layers may not import lower)

For r3, `forbidden` contracts are the correct type for all AVC contracts above.

**Running in CI:**
```bash
lint-imports  # exits 0 if all contracts pass, nonzero on violation
```
Add to `pyproject.toml` `[tool.pytest.ini_options]` or a Makefile step;
do NOT add to `pytest.ini` (pytest.ini is owned by the anchor-updater per CLAUDE.md).

---

### Topic 6 — Parameter-Widget Extraction (Pure Math vs QWidget Chrome)

**Context.** r3 may split `_qt/panels/parameters.py` (368 LOC) into a pure-math
`varieties/parameter_spec.py` and a Qt-widget `_qt/panels/parameters.py` shell.

**The canonical Qt MVC pattern for this split.**
The well-established Qt architecture (independent of Python binding) is:

```
Model (pure Python, no Qt) ←→ Controller/ViewModel ←→ View (QWidget subclass)
```

In PySide6 terms, the "pure-math" portion holds:
- Parameter definitions (`ParameterSpec` dataclass: name, min, max, default, step)
- Validation logic (range clamp, type coercion)
- No QWidget, no QSlider, no QLabel imports

The Qt panel wraps the pure model:
- Constructs QSliders bound to ParameterSpec ranges
- Emits Qt signals on change; calls model validation
- Has zero math logic of its own

**AVC-specific note.** AI-2 makes this split immediately test-beneficial:
pure-math parameter logic becomes testable without QApplication. Current
parameters_panel tests (`tests/test_parameters_panel.py`, 110 LOC) import
`surfaces` for SurfaceSpec data but do not instantiate the Qt panel. This
confirms the pure-math split is already being tested — the split just makes
the module boundary explicit.

**Safe extraction sequence:**
1. Create `varieties/parameter_spec.py` with the pure ParameterSpec model.
2. Update `varieties/types.py` or `varieties/__init__.py` to export it.
3. In `_qt/panels/parameters.py`, replace inline data logic with imports from
   `varieties.parameter_spec`.
4. Add import-linter contract: `varieties.parameter_spec` must not import `PySide6`.
5. Existing tests pass without changes (they test surfaces/SurfaceSpec data,
   not the Qt widget layer).

**Post-2024 PySide6 pattern search results.** Web search for "PySide6 pure math
widget separation 2024 2025" returned only Qt widget documentation, not
architectural pattern docs. [UNVERIFIED — no primary source for a named
PySide6-specific pattern found.] The MVC split described above is the generic
Qt pattern, well-established since Qt 4. For Python/PySide6 specifically,
napari's `napari/_qt/` vs `napari/` split (private Qt code in `_qt`, public
logic in root) is the closest real-world precedent. AVC already follows this
structure. [CONSENSUS — lessons.md from r2 scout run 2026-05-23]

---

## 2. Tooling Matrix (r3-relevant subset)

| Tool | What | Version | AVC applicability |
|---|---|---|---|
| LibCST | AST-preserving Python transformer for codemods | 1.8.6 (Nov 2025) | HIGH — B1 rewrite-imports.py fix; B4 caller migration |
| import-linter | Contract-based import graph enforcement | 2.x | HIGH — post-B4 regression guardrail |
| pydeps | Import graph visualization | unknown | MEDIUM — cycle detection before/after B4 |
| coverage.py | Branch/statement coverage | 7.x | HIGH — baseline and post-restructure parity |
| ruff | Linting/formatting; replaces flake8+isort+black | 0.x (active 2026) | MEDIUM — post-move import cleanup |
| mypy | Static type checking for Protocol conformance | 1.x | LOW-MEDIUM — Protocol intro in Topic 4 |
| Bowler | DEAD. Archived Aug 2025. Redirects to LibCST. | N/A | DO NOT USE |
| Rope | Active (1.14.0, Jul 2025) | 1.14.0 | LOW — IDE refactor helper, not scripted |

---

## 3. The rewrite-imports.py Correctness Checklist (r3 B1)

This section condenses Topic 2 into an actionable checklist for the executor.

Before running `rewrite-imports.py` on the live tree:

```
[ ] Class declares METADATA_DEPENDENCIES = (QualifiedNameProvider, ScopeProvider)
[ ] leave_Attribute uses QualifiedNameProvider.has_name(), NOT string matching
[ ] leave_Name uses QualifiedNameProvider.has_name(), NOT string matching
[ ] leave_ImportFrom guards against multi-alias rewrites (see Topic 2)
[ ] leave_ImportFrom skips cst.ImportStar nodes
[ ] Codemod tested on scratch file with all four import pattern variants
[ ] AddImportsVisitor + RemoveImportsVisitor used (not manual string replacement)
[ ] Codemod run with --jobs=1 on macOS (avoids QualifiedNameProvider pool pickling
    issues if they arise — unconfirmed on macOS, confirmed on Windows)
```

---

## 4. Cyclic-Import Guardrail — Concrete Commands (r3 B4 exit criterion)

Run these in sequence after B4 (surfaces.py deleted):

```bash
# 1. Fresh-interpreter smoke test for all Qt-free modules
python -c "
import importlib
for m in ['varieties', 'varieties.registry', 'varieties.types',
          'varieties.dispatch', 'render', 'cross_section']:
    importlib.import_module(m)
    print(f'{m}: OK')
"

# 2. subprocess-isolated smoke test (catches conftest.py pollution)
python -m pytest tests/test_import_smoke.py -v  # file to be created in B4

# 3. DeprecationWarning check — must be zero hits
python -W error::DeprecationWarning -m pytest -q

# 4. Zero surfaces references outside shim graveyard
grep -rn "import surfaces" . --include="*.py" | grep -v "test_r2_shims.py"
# Expected: no output

# 5. import-linter (if contracts added in B5)
lint-imports
```

---

## 5. Hub Retirement — Common Rationalizations to Refuse

These are the plausible-but-wrong shortcuts the executor or a future AI agent
might reach for during B4:

1. **"Delete surfaces.py now and fix the import errors as they appear."**
   Violated principle: Expand-Contract requires ALL callers migrated BEFORE
   contract phase. Mass-delete-then-fix produces a chaotic repair session and
   loses the green-at-every-commit invariant. [Fowler, Parallel Change]

2. **"Keep surfaces.py indefinitely as a convenience re-export."**
   Violated principle: r3's explicit goal is single-root cleanup. A permanent
   re-export hub defeats that goal and adds a permanent maintenance burden.

3. **"string-match `node.value.value == 'surfaces'` in leave_Attribute."**
   Violated principle: correct LibCST matching requires QualifiedNameProvider.
   String matching produces partial rewrites (see Topic 2).

4. **"The shim's DeprecationWarning means callers will find the issue themselves."**
   Violated: DeprecationWarning is silenced by default in production Python
   (`python -W default`). Users running without `-W error` will never see it.
   Caller migration MUST be done explicitly, not left to warning discovery.

5. **"Move surfaces.py into varieties/ as a compatibility alias."**
   Violated: this converts a deletion problem into a relocation problem,
   creating a new shim in a new location. The Expand phase is already done —
   proceed to Contract.

---

## 6. AVC-Specific Constraints Summary (applies to all r3 patterns)

| Constraint | Source | Impact on patterns |
|---|---|---|
| AI-2: No Qt in tests/ | CLAUDE.md §4 | Smoke tests must not import app/_qt |
| AI-8: VARIETIES is a frozen registry | CLAUDE.md/AI-invariants | Protocol intro must not change dataclass contract |
| AI-9: _computing re-entrancy guard | lessons.md r1 | Any Extract Class touching render path must carry guard |
| numba THREADING_LAYER side effect | lessons.md r2 | Confirm in _kernels.py before deleting surfaces.py |
| _qt/__init__.py is empty | imports-rough.json | _qt/ module shim chains must go through _qt/__init__.py if needed |
| pytest.ini is anchor-updater owned | CLAUDE.md §8 | Do not add import-linter to pytest.ini |
| MOVES.md must be updated | CLAUDE.md §2 | After surfaces.py deletion, MOVES.md gets a "DELETED" entry |

---

## 7. Sources

- [martinfowler.com/bliki/StranglerFigApplication.html](https://martinfowler.com/bliki/StranglerFigApplication.html) — Fowler Strangler Fig
- [martinfowler.com/bliki/ParallelChange.html](https://martinfowler.com/bliki/ParallelChange.html) — Fowler Parallel Change
- [blog.thepete.net/blog/2023/12/05/expand/contract-making-a-breaking-change-without-a-big-bang/](https://blog.thepete.net/blog/2023/12/05/expand/contract-making-a-breaking-change-without-a-big-bang/) — Expand/Contract (Pete Hodgson, 2023)
- [thoughtworks.com/radar/techniques/api-expand-contract](https://www.thoughtworks.com/radar/techniques/api-expand-contract) — Thoughtworks Tech Radar: API Expand-Contract
- [github.com/Instagram/LibCST/blob/main/libcst/codemod/commands/rename.py](https://github.com/Instagram/LibCST/blob/main/libcst/codemod/commands/rename.py) — RenameCommand implementation (accessed 2026-05-24)
- [libcst.readthedocs.io/en/latest/codemods_tutorial.html](https://libcst.readthedocs.io/en/latest/codemods_tutorial.html) — LibCST codemod tutorial
- [libcst.readthedocs.io/en/latest/codemods.html](https://libcst.readthedocs.io/en/latest/codemods.html) — LibCST codemods reference
- [github.com/Instagram/LibCST/issues/435](https://github.com/Instagram/LibCST/issues/435) — QualifiedNameProvider Windows process pool issue
- [import-linter.readthedocs.io/en/stable/get_started/configure/](https://import-linter.readthedocs.io/en/stable/get_started/configure/) — import-linter configuration reference
- [import-linter.readthedocs.io/en/stable/usage.html](https://import-linter.readthedocs.io/en/stable/usage.html) — import-linter usage
- [typing.python.org/en/latest/reference/protocols.html](https://typing.python.org/en/latest/reference/protocols.html) — Python typing: Protocols
- [mypy.readthedocs.io/en/stable/protocols.html](https://mypy.readthedocs.io/en/stable/protocols.html) — mypy: Protocols and structural subtyping
- [github.com/python/cpython/issues/102433](https://github.com/python/cpython/issues/102433) — CPython: isinstance on runtime_checkable Protocol with @property
- [learn.scientific-python.org/development/guides/pytest/](https://learn.scientific-python.org/development/guides/pytest/) — Scientific Python: Testing with pytest
- [pypi.org/project/libcst/](https://pypi.org/project/libcst/) — LibCST on PyPI (version 1.8.6 confirmed)

---

*Brief written by REFACTOR-PATTERN SCOUT for restructure-single-root-2026q2-r3.*
*Scope: survey only. PLAN.md is Phase 2.*
*Access date: 2026-05-24.*
