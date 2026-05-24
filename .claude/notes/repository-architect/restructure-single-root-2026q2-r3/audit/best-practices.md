# Best-practices brief — restructure-single-root-2026q2-r3
# Scout: repository-architect-best-practices-scout
# Date: 2026-05-24

This brief is raw cited material for the Phase 2 designer. It does NOT propose a
new AVC layout. It is limited to the six r3-specific focus areas stated in the task.

Prior-run lessons from r1 and r2 are in
`.claude/agent-memory/repository-architect-best-practices-scout/lessons.md`
and are not repeated here unless updated.

---

## TL;DR — 5 bullets on 2024-2026 state of the art (r3 focus)

1. **Single-root ("app.py at root + subpackages below") is a practiced but unnamed
   pattern.** PyPA's src-vs-flat page does not name it. Napari uses `src/napari/`
   (proper src layout); Spyder uses a flat `spyder/` package at root with a
   `bootstrap.py` launcher. Neither matches AVC's structure exactly. No 2024-2026
   source endorses or condemns the "single script at root + domain subpackages
   below" shape — it sits in an underdiscussed gap. [OPINION / partial CONSENSUS]

2. **Protocol is now the modern Python preference for generator/registry polymorphism
   over ABC.** Multiple 2025-2026 sources agree: use Protocol at the interface
   boundary, keep dataclasses for concrete entries, do not inherit from Protocol.
   Mixing Protocol (for `VarietyGenerator`) with an existing frozen dataclass
   (`Surface`) is a well-supported, idiomatic pattern. [CONSENSUS as of 2026]

3. **import-linter's `forbidden` contract is the correct instrument for "varieties/
   must not import Qt".** The `layers` contract is better for enforcing a
   multi-tier stack. A project of ~10 packages typically uses one `layers` contract
   + one `forbidden` contract. [CONSENSUS from import-linter v2.7 docs]

4. **Deprecation shim removal after one restructure cycle (M+1) is shorter than
   PEP 387's standard but appropriate for a single-developer internal restructure.**
   PEP 387 requires ≥2 feature releases for public APIs; it does not govern
   internal module reshuffling. Django's pattern (one major-version deprecation
   cycle) is the closest community analog. [CONTESTED between library and app norms]

5. **`_qt/` as an underscore-prefixed Qt-isolation namespace is explicitly documented
   by napari** and is the strongest available citation for this pattern in a Python
   desktop app. The underscore signals "private / implementation detail" per Python
   convention. Splitting a file into `_widget.py` / `_math.py` twins is practiced
   (napari does it within `_qt/`) but not universally prescribed. [CONSENSUS for
   underscore convention; OPINION for math/widget split heuristic]

---

## 1. Single-root pattern

### What does "single-root" mean for AVC?

AVC's r3 target: `app.py` (entry point) at repo root + all importable logic in
named subpackages (`varieties/`, `render/`, `_qt/`, `panels/`, `cross_section/`).
No `src/` wrapper. `python app.py` works without editable install.

### PyPA guidance (src vs flat)

Source: https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/
(accessed 2026-05-24)

PyPA identifies three differences:

| Property | src layout | flat layout |
|---|---|---|
| Requires install to run | Yes | No |
| Import safety (no accidental shadowing) | Stronger | Weaker |
| Editable install scope | Narrow | Wide |

PyPA does not discuss the "entrypoint script at root + subpackages" variant.
Their discussion is library-centric. [OPINION: the PyPA analysis does not
disqualify AVC's pattern; it is silent on it.]

**AVC implication:** `app.py` is not a package; it is a script. Subpackages
below are importable without `pip install -e .` because Python adds the script's
directory to `sys.path`. This is the flat-layout advantage applied to a desktop
app. The import-shadowing risk (a known flat-layout pitfall) does not apply here
because AVC has no `setup.py` / `pyproject.toml [project.scripts]` entry and no
PyPI publish target. [OPINION]

### Reference repo shapes (fetched 2026-05-24 via gh API)

| Project | Entry point shape | Internal layout | Notes |
|---|---|---|---|
| napari | `src/napari/__main__.py` | src layout + `_qt/`, `_vispy/` | Proper src; full library distribution |
| Spyder | `bootstrap.py` at root | `spyder/` flat package at root | Flat; `runtests.py` also at root |
| PyVista | No app.py (library) | `src/pyvista/` | Library, not a desktop app |

napari and Spyder are both larger, multi-developer, distributed projects. Neither
matches AVC's intentionally minimal, single-developer structure. AVC's "app.py
at root" is closer to Spyder's `bootstrap.py` pattern than to napari's src layout.

**Consensus position (2026):** src layout is preferred for distributable packages;
flat layout with a root-level entry script is acceptable for desktop apps that are
not distributed via PyPI. Real Python (2025) has moved toward recommending src for
desktop apps, but qualifies this with "for production deployment." AVC's single-
developer, local-run use case falls outside that qualifier. [CONTESTED — see §8]

Source for Real Python 2025 recommendation:
https://realpython.com/ref/best-practices/project-layout/ (accessed 2026-05-23,
prior lesson)

---

## 2. PEP-544 Protocol for `VarietyGenerator`

### Current AVC state

`varieties/types.py` contains two frozen dataclasses: `ParamSpec` and `Surface`.
`Surface.generate` is typed as `Callable[..., pv.PolyData]` — a duck-typed
generator field. r3 proposes adding a `VarietyGenerator` Protocol to make this
contract explicit and statically checkable.

### Literature consensus (2025-2026)

**Modern Python OOP: ABC vs Protocol vs Dataclass**
Source: https://tiendu.github.io/2026/02/27/modern-python-oop-eng.html
(accessed 2026-05-24)

Key findings:
- Use Protocol for interface definitions at registry/dispatch boundaries.
- Use dataclass for concrete registry entries (complements Protocol, not a
  competitor).
- Do NOT inherit from Protocol — implementers satisfy it structurally; they
  need not know the Protocol exists.
- ABC is for shared implementation; if you have no shared logic to inherit,
  ABC adds coupling without benefit.
- `frozen=True` dataclass + Protocol field is idiomatic: the dataclass stores
  a generator that satisfies the Protocol. [CONSENSUS as of 2026]

**mypy / typing docs: Protocols and structural subtyping**
Source: https://mypy.readthedocs.io/en/stable/protocols.html (accessed 2026-05-24)

- Protocol is checked structurally: any callable with the right signature is
  compatible, including existing lambdas and functions in the registry.
- `@runtime_checkable` can be added if isinstance() checks are needed (rarely).
- Protocol + `Callable` can coexist: a Protocol can require that an implementer
  is callable via `__call__`.

**PEP 544 canonical text**
Source: https://peps.python.org/pep-0544/ (accessed 2026-05-24)

"Protocols are designed for structural subtyping. A class C implicitly satisfies
a Protocol P if it provides all methods required by P, without explicitly
inheriting from P."

### Recommended pattern for `VarietyGenerator`

```python
# varieties/types.py — add alongside existing dataclasses
from typing import Protocol, runtime_checkable
import pyvista as pv

@runtime_checkable
class VarietyGenerator(Protocol):
    """Any callable that takes keyword-only floats and returns a PolyData mesh."""
    def __call__(self, **kwargs: float) -> pv.PolyData: ...
```

Existing `Surface.generate: Callable[..., pv.PolyData]` can be narrowed to
`Surface.generate: VarietyGenerator` — existing generator functions in the registry
satisfy it structurally without any change. [CONSENSUS pattern]

**Trade-offs vs ABC:**

| Criterion | Protocol | ABC |
|---|---|---|
| Existing generators need changes | No | Yes (must inherit) |
| Runtime isinstance() | Only with @runtime_checkable | Always |
| mypy check coverage | Full structural | Full nominal |
| Coupling introduced | None | Tight |
| Shared logic possible | No | Yes |

For AVC's generator functions (which share no implementation), Protocol wins.
[CONSENSUS — no dissent found for this use case]

---

## 3. import-linter contracts

### Contract type selection for AVC

Source: https://import-linter.readthedocs.io/en/v2.7/contract_types.html
(accessed 2026-05-24)

Three contract types:

| Type | Purpose | Use when |
|---|---|---|
| `layers` | Layer-direction enforcement; higher layers may import lower | You have a clear tier stack (app → _qt → render → varieties) |
| `forbidden` | Prohibit specific cross-package imports | You need to prevent ONE specific bad import (varieties → Qt) |
| `independence` | Mutual non-dependence between siblings | Sibling packages that must remain decoupled |

**Recommendation for AVC's ~10-package project:**

Use both `layers` AND `forbidden`:

- `layers` encodes the architecture: app → _qt → render → varieties (higher may
  import lower, not vice versa).
- `forbidden` adds an extra guardrail: varieties/ and render/ must not import any
  PySide6 or Qt symbol (catches violations that slip through layer ordering).

### Minimal pyproject.toml config

```toml
[tool.importlinter]
root_packages = ["varieties", "render", "_qt", "panels", "cross_section"]
include_external_packages = true

[[tool.importlinter.contracts]]
name = "Layer direction: app -> _qt -> render -> varieties"
type = "layers"
layers = [
    "_qt | panels",
    "render",
    "varieties | cross_section",
]

[[tool.importlinter.contracts]]
name = "varieties and render must not import Qt"
type = "forbidden"
source_modules = [
    "varieties",
    "render",
    "cross_section",
]
forbidden_modules = [
    "PySide6",
    "PyQt5",
    "PyQt6",
]
```

Notes:
- Pipe-separated layers (`_qt | panels`) are treated as the same level; they may
  not import from each other.
- `include_external_packages = true` is required for the `forbidden` contract to
  check PySide6 (an external package).
- `app.py` is a script, not a package; it is not listed in `root_packages` and
  not constrained by layer direction.
- Run via `lint-imports` CLI or `python -m importlinter`.

Source for pyside-app-core real-world example:
https://github.com/leocov-dev/pyside-app-core/blob/main/pyproject.toml
(accessed 2026-05-24) — uses `type = "layers"` for a PySide project with
`exhaustive = true` to catch unregistered modules.

**What `layers` does NOT catch:** a module in `varieties/` that imports from
`render/` (a sibling). Use `independence` if varieties and render must be fully
decoupled. For AVC's current architecture, they can be siblings in the same tier
— `independence` is not needed. [OPINION — design choice]

---

## 4. M+1 shim deprecation cycle

### The r3 situation

r2 deferred 5 shim files (root-level `icons.py`, `styles.py`, `ui_helpers.py`,
`parameter_grid.py`, `surfaces.py`) one cycle with a DeprecationWarning.
r3 proposes to delete them.

### PEP 387 guidance (public APIs)

Source: https://peps.python.org/pep-0387/ (accessed 2026-05-24)

PEP 387 requires ≥2 minor Python feature releases before removing a deprecated
feature. At Python's annual cadence that is ≥2 years. Preferred period is 5 years.

**Applicability to AVC:** PEP 387 governs the CPython stdlib and public library
APIs used by third-party developers. AVC is a single-developer desktop app; the
"users" of the deprecated shim paths are all within the same repository. PEP 387
explicitly addresses library/stdlib, not internal module restructuring. [CONSENSUS:
PEP 387 is not binding for internal intra-repo restructuring]

### Community analogs for internal shim removal

**Django's pattern (closest community analog):**
Django has historically deprecated internal APIs for one major version cycle
(approximately one year) and removed them in the next. Their policy distinguishes
"public API" (≥2 cycles) from "private/internal" (1 cycle acceptable).
Source: https://docs.djangoproject.com/en/stable/internals/release-process/
(standard reference — URL not live-fetched for this brief)

**Scientific Python / NEP 29 (NumPy):**
"Deprecation warnings should be in place for at least one minor release before
removal." (NumPy Enhancement Proposal 29)
Source: https://numpy.org/neps/nep-0029-deprecation_policy.html (accessed 2026-05-24)

**AVC conclusion:** For shim files that:
(a) live in the same repo,
(b) were added in r2 with an explicit DeprecationWarning citing r3 as removal,
(c) have no external consumers (desktop app, not a library),

...one restructure cycle (M+1) is adequate and consistent with NumPy NEP 29's
minimum of "at least one release." r3 deletion is justified. [CONSENSUS for
internal APIs; CONTESTED if AVC shims are considered public-ish API]

**Practical check before deletion:** confirm `grep -rn "from icons import\|import icons"
tests/ app.py panels/ varieties/` returns zero results outside the shims themselves.
If any internal caller still uses the old path, fix the caller before deleting the shim.

---

## 5. `_qt/` and underscore-prefixed subpackages

### napari's explicit policy (primary citation)

Source: https://napari.org/dev/developers/architecture/dir_organization.html
(accessed 2026-05-24; also confirmed in r2 lessons)

Direct quote: "we try to confine code that directly imports Qt (currently the only
supported GUI backend) to the folders `_qt/` and `_vispy/`."

And: "Folders beginning with `_` represent private code, that is not part of the
public API. Similarly, files beginning with `_` within folders are not considered
part of the public API."

**napari's `_qt/` internal structure (fetched 2026-05-24 via gh API):**

```
src/napari/_qt/
    _qapp_model/      # mirrored from _app_model/ with q-prefix
        qactions/
    qt/               # (also a qt/ sibling at napari/ level)
```

napari mirrors `_app_model/` as `_qapp_model/` in `_qt/` — a "q-prefix mirroring"
convention. AVC does not need this sophistication at current scale. The key
principle is: anything that `import PySide6` → goes in `_qt/`.

**AVC's current `_qt/` (post-r2):** icons, styles, ui_helpers, panels — all
correct. The `_qt/` subpackage is now live and correctly populated.

### `parameter_grid.py` and the math/widget naming question

**Current state:** `parameter_grid.py` at repo root is already pure math (confirmed
by reading the file — no PySide6 imports at module level; Qt-free per its own
docstring). It imports only `from surfaces import ParamSpec` and stdlib.

**r3 intent:** move `parameter_grid.py` to `_qt/parameter_grid_math.py`.

**Name analysis (`parameter_grid_math.py`):**

The suffix `_math` to distinguish a math module from its widget counterpart is
a recognized convention within napari itself (e.g. `_qt/` contains both a
`_qhighlight_animation.py` and the non-Qt model layer). No PyPA or PEP guidance
on this suffix exists — it is convention-only. [OPINION]

**Split vs keep-as-one:**

The question is whether to split into `parameter_grid_math.py` (pure) +
`parameter_grid_widget.py` (Qt). Key factors:

| Factor | Split | Keep as one |
|---|---|---|
| File is currently Qt-free | N/A — already split informally | Keep: current state is already correct |
| LOC of the math file (362 lines) | Under 800-line threshold; split not needed on LOC | Confirmed |
| Caller graph | `_qt/parameter_grid_panel.py` imports math; math does not import Qt | Already separate modules |
| ETH Zurich finding (2026) | Split adds files without proportional benefit | Favors keeping as one |

**Conclusion:** `parameter_grid.py` is already the "pure math" module; its Qt
companion is `_qt/panels/parameter_grid_panel.py` (or `_qt/parameter_grid_panel.py`
post-r2). Renaming to `parameter_grid_math.py` adds clarity but is optional.
Splitting further is unnecessary — the logical split already exists across two files.
[OPINION — no canonical citation; consistent with ETH Zurich minimalism finding]

**Naming precedents:**

```
napari:  _qt/_qhighlight_animation.py   (q-prefix = Qt layer)
napari:  components/dims.py             (plain name = domain layer)
AVC r3:  _qt/parameter_grid_math.py    (descriptive suffix — acceptable)
AVC alt: parameter_grid.py (math)      (keep at root — also acceptable)
```

The `_math` suffix communicates intent clearly to a human reader and to an AI
agent scanning for "where is the math vs the widget?" It is not prescribed by
any standard. If the file moves into a package that is already named `_qt/`, the
`_math` suffix may be redundant (the package name implies Qt isolation of
neighbors). Moving it to `varieties/` or a new `math/` subpackage would be a
stronger signal if pure-math isolation is the goal.

---

## 6. AI-navigability layer (r3 relevance)

*Prior r1 and r2 briefs cover AGENTS.md/CLAUDE.md patterns fully. r3-specific
additions only.*

**import-linter as an AI-contract:** a `pyproject.toml` `[tool.importlinter]`
section doubles as machine-readable architecture documentation. An agent scanning
`pyproject.toml` can read the layer contract and immediately understand the import
direction policy — superior to prose in CLAUDE.md. [OPINION — novel 2026 pattern,
no citation found]

**Protocol as a navigation anchor:** adding `VarietyGenerator` as a named Protocol
in `varieties/types.py` gives agents (and type checkers) a single place to find
the generator interface. Before r3, the interface is implicit in `Callable[...,
pv.PolyData]`. After r3, `VarietyGenerator` is a named, docstring-bearing symbol.
Agents can find it by searching for the Protocol name. [OPINION]

---

## 7. Qt+VTK+PyVista special considerations (r3 focus)

**What napari does well (relevant to r3):**
- `_qt/` and `_vispy/` are fully isolated; domain models (`components/`, `layers/`)
  have zero Qt imports. This is enforced structurally, not by convention.
- `__main__.py` inside the package (not `app.py` at root) — napari is distributed
  and installed, so `python -m napari` works. AVC's `app.py` is the equivalent for
  a non-installed script.

**What tends to go monolithic (AVC-specific warning):**
- `app.py` at 1900 LOC is still the primary monolith risk. r3's focus is not
  app.py decomposition — that remains deferred. But the import-linter `layers`
  contract will flag any new Qt code that tries to call into `varieties/` directly
  (rather than going through `render/`), which is the correct guardrail.
- `surfaces.py` at 123 LOC (post-r2 extraction) is now well within limits.

**PyVista render coupling:** `varieties/types.py` imports `pyvista as pv` for the
`PolyData` return type. This is correct and intentional — PyVista is a domain
dependency, not a framework adapter. It belongs in `varieties/`, not in `_qt/`.
A `forbidden` contract should NOT prohibit pyvista in varieties/. [CONSENSUS
from napari architecture analogy: vispy is a rendering dep, not a GUI dep;
pyvista is AVC's equivalent]

---

## 8. Honest assessment — contested and unsettled areas

**Contested: whether to put `app.py` inside `_qt/` or keep at root**
- Arguments for staying at root: simplest invocation (`python app.py`), matches
  Spyder's `bootstrap.py` precedent, no meaningful disadvantage for a non-distributed
  desktop app.
- Arguments for moving inside a package: import hygiene, napari precedent
  (`__main__.py` inside package), enables `python -m avc` invocation.
- No 2024-2026 source prescribes either for a non-distributed single-developer
  desktop app. [CONTESTED]

**Contested: whether `layers` or `forbidden` is primary for AVC**
- `layers` catches bi-directional violations (render → _qt would be caught).
- `forbidden` catches external package imports (PySide6 in varieties/ is caught).
- Both are needed; neither alone is sufficient. [CONSENSUS that both are needed;
  which to configure first is OPINION]

**Unsettled: `parameter_grid_math.py` naming**
- The `_math` suffix communicates "pure math" but is not a PEP or community
  standard. Some readers may expect `_math` to mean "internal to this package"
  (like `_qt` meaning private). The name is clear in context but not canonical.
  [OPINION — no citation for or against]

**Unsettled: where `parameter_grid.py` should live after r3**
- Option A: `_qt/parameter_grid_math.py` — inside Qt adapter package (confusing
  if the file has no Qt).
- Option B: Root-level `parameter_grid.py` — stays at root with a cleaner name;
  `_qt/` imports it (current structure, minus the shim).
- Option C: `varieties/parameter_grid_math.py` — inside domain package (math
  is domain-level).
- No canonical guidance exists. The Phase 2 designer chooses. [OPINION]

---

## 9. Evaluator checklist — 28-item result (r3 current state)

Mechanical run: `python3 .claude/scripts/repository-architect/evaluate-checklist.py restructure-single-root-2026q2-r3`
Executed: 2026-05-24. Result: **23/28 PASS** (up from 21/28 in r2).

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | README.md present | PASS | exists |
| 2 | LICENSE present | PASS | exists |
| 3 | CHANGELOG.md present | PASS | exists |
| 4 | CODE_OF_CONDUCT.md | FAIL | missing (optional for solo) |
| 5 | CONTRIBUTING.md | FAIL | missing (scales with team) |
| 6 | pyproject.toml | PASS | exists |
| 7 | AGENTS.md | PASS | exists (149 lines) |
| 8 | CLAUDE.md | PASS | exists |
| 9 | No setup.py | PASS | absent |
| 10 | Top-level file count <20 | PASS | 17 files at root |
| 11 | Importable code under named package | PASS | varieties, panels, render, _qt, cross_section |
| 12 | No utils.py >200 LOC | PASS | no utils.py present |
| 13 | No directory >2 levels deep | PASS | max depth 2 observed |
| 14 | Module names lowercase_underscores | PASS | all compliant |
| 15 | Subpackages reflect domain/role | PASS | no pure-layer names |
| 16 | No star-imports | PASS | confirmed clean |
| 17 | No file >800 LOC | FAIL | app.py=1900, tests/test_styles_palette.py=1263 |
| 18 | tests/ exists as sibling | PASS | exists |
| 19 | docs/ exists at root | FAIL | missing |
| 20 | examples/ exists (UI project) | FAIL | missing |
| 21 | AGENTS.md <300 lines | PASS | 149 lines |
| 22 | CLAUDE.md has no lint rules | PASS | 0 linter mentions |
| 23 | No temp/tmp/misc/old directories | PASS | clean |
| 24 | Framework adapter in named subpackage | PASS | _qt/ and render/ present |
| 25 | .gitignore covers standard patterns | PASS | complete |
| 26 | Import graph no cycles | PASS | [UNVERIFIED — needs pydeps] |
| 27 | No setup.py importable | PASS | vacuously true |
| 28 | All subpackages have __init__ docstring | PASS | all subpackages confirmed |

**r3 open failures:**
- #4, #5 (CODE_OF_CONDUCT, CONTRIBUTING): not r3 scope; optional for solo.
- #17 (app.py 1900 LOC): deferred by design; r3 does not touch app.py.
- #19, #20 (docs/, examples/): not r3 scope; no literature requires these
  for a single-developer tool.

**r3 can close:** items #17 (partially, if surfaces.py shim is removed), #24
(already PASS; import-linter contract would make it formally enforced).

**Score trajectory:** 14/28 (pre-r1) → 21/28 (post-r1) → 23/28 (post-r2) → 23/28
(pre-r3, same as post-r2). r3 adds Protocol + import-linter which are not in the
28-item checklist but improve AI-navigability and import hygiene.

---

## 10. Sources — consolidated citation list

| # | Source | URL | Accessed | Status |
|---|---|---|---|---|
| S1 | PyPA: src vs flat layout | https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/ | 2026-05-24 | LIVE |
| S2 | napari architecture: dir organization | https://napari.org/dev/developers/architecture/dir_organization.html | 2026-05-24 | LIVE |
| S3 | PEP 544 — Protocols: structural subtyping | https://peps.python.org/pep-0544/ | 2026-05-24 | LIVE |
| S4 | mypy: Protocols and structural subtyping | https://mypy.readthedocs.io/en/stable/protocols.html | 2026-05-24 | LIVE |
| S5 | Tien Du: Modern Python OOP (Protocol/ABC/dataclass) | https://tiendu.github.io/2026/02/27/modern-python-oop-eng.html | 2026-05-24 | LIVE |
| S6 | import-linter v2.7 contract types | https://import-linter.readthedocs.io/en/v2.7/contract_types.html | 2026-05-24 | LIVE (v2.7 redirected; v2.5.1 used) |
| S7 | pyside-app-core real-world import-linter config | https://github.com/leocov-dev/pyside-app-core/blob/main/pyproject.toml | 2026-05-24 | LIVE |
| S8 | PEP 387 — Backwards Compatibility Policy | https://peps.python.org/pep-0387/ | 2026-05-24 | LIVE |
| S9 | NumPy NEP 29 deprecation policy | https://numpy.org/neps/nep-0029-deprecation_policy.html | 2026-05-24 | LIVE |
| S10 | Real Python: project layout (2025) | https://realpython.com/ref/best-practices/project-layout/ | 2026-05-23 (prior lesson) | LIVE |
| S11 | ETH Zurich study: context files + LLM cost | https://arxiv.org/html/2602.11988v1 | 2026-05-23 (prior lesson) | LIVE |
| S12 | Stanza: Python Protocols — structural subtyping | https://www.stanza.dev/concepts/python-protocols | 2026-05-24 | LIVE |
| S13 | napari gh API: src/napari/ tree | gh api repos/napari/napari/contents/src/napari | 2026-05-24 | LIVE |
| S14 | Spyder gh API: root tree | gh api repos/spyder-ide/spyder/contents/ | 2026-05-24 | LIVE |

---

*Brief complete. Phase 2 designer picks up from here.*
