# Best-Practices Scout Brief
## Restructure ID: restructure-feature-subpackages-2026q2-r2
## Generated: 2026-05-23
## Agent: Best-Practices Scout (Phase 1) — r2 edition
## Predecessor brief: restructure-full-audit-2026q2-r1/audit/best-practices-brief.md

**Scope.** Raw material for the Phase 2 designer. This brief covers 2024-2026 industry best
practices for Python desktop / scientific-viz repository structure, with emphasis on the
substantive structural changes targeted by r2 (feature-subpackage decomposition, varieties/
extraction, render/ isolation, _qt/ formalization). The conservative bias from r1 is RELAXED;
pattern applicability ratings reflect this.

**Incremental approach.** r1 closed items 2, 3, 6, 7, 8, 25, and the panels/ subpackage (item
24 partial). r2's primary targets are items 11 (source package / varieties/ + render/ +
cross_section/ + _qt/), 17 (>800 LOC files: surfaces.py 1811, app.py 1900), and 10 (root-file
count 21 — one over). The r2 brief intentionally focuses research and pattern analysis on these
gaps.

**Honesty conventions:**
- `[CONSENSUS]` — multiple independent reputable sources agree.
- `[CONTESTED]` — credible sources disagree.
- `[OPINION]` — single author's well-reasoned position; treat as input not verdict.
- `[UNVERIFIED]` — could not fetch primary source; included only when widely cross-referenced.
- `[NEW-2026]` — pattern or finding that emerged or was confirmed after the r1 brief.

All URLs verified live on 2026-05-23 unless marked `[UNVERIFIED]`.

---

## 1. TL;DR — 5 bullets on 2024-2026 state of the art

1. **Flat-package + feature subpackages is the recognized pragmatic pattern for single-developer
   Python desktop apps.** The literature does not give it a single canonical name, but it is the
   shape used by pandas, scipy, django, and pyvista (all flat-at-root, domain-split inside).
   src-layout adds packaging discipline that is more valuable for distributed libraries than for
   interactive desktop apps. For AVC the target shape is: root-level importable modules
   (app.py, surfaces.py, parameter_grid.py, render_worker.py) stay OR move into feature
   subpackages depending on size — the designer's call. The "flat package" step (avcs/ at root)
   that r1 targeted remains achievable but is not gated for r2.
   [CONTESTED for apps; CONSENSUS for libraries]
   ([packaging.python.org](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/),
   [pyOpenSci](https://www.pyopensci.org/python-package-guide/package-structure-code/python-package-structure.html),
   [Real Python 2025](https://realpython.com/ref/best-practices/project-layout/))

2. **The napari `_qt/` pattern is explicitly documented and stable as of 2026.** Napari's
   architecture docs state: "we try to confine code that directly imports Qt to the folders
   `_qt/` and `_vispy/`." The `_qt/` subpackage mirrors napari/'s structure, with 'q' prefixed
   to folder and file names inside. This is a strong, citable, cross-version commitment to
   framework isolation — directly applicable to AVC's proposed `_qt/` subpackage.
   [CONSENSUS within the Qt+VTK desktop family]
   ([napari architecture docs](https://napari.org/dev/developers/architecture/dir_organization.html),
   confirmed live 2026-05-23)

3. **AGENTS.md is confirmed stable infrastructure (60k+ repos, Linux Foundation stewardship,
   20+ tools).** Key 2026 update: an ETH Zurich study (arxiv.org/html/2602.11988v1) found that
   LLM-generated context files *reduce* task success by ~2-3% and increase costs 19-23%; human-
   curated files show modest +4% gain. The implication: AGENTS.md should be minimal and
   hand-written, containing only what agents cannot discover from the codebase itself. AVC's
   AGENTS.md at 148 lines (well under 200) is correctly scoped.
   [CONSENSUS as infrastructure; NEW-2026 caution against auto-generation]
   ([agents.md](https://agents.md/),
   [ETH Zurich study](https://arxiv.org/html/2602.11988v1),
   [Augment Code guide 2026](https://www.augmentcode.com/guides/how-to-build-agents-md))

4. **Package-by-feature is the preferred decomposition strategy for AI-agent-navigable
   codebases; no significant 2026 dissent found.** The 2026 search surface confirms the Kraken
   EuroPython and Sahibinden positions are the dominant view; a new 2026 Medium piece
   specifically argues modular monolith beats microservices when AI agents are reading code
   (42% of orgs are consolidating microservices). The practical implication for AVC: keeping
   varieties/, render/, _qt/ as cohesive domain-aligned modules is the right call.
   [CONSENSUS for modular monoliths]
   ([Sahibinden Tech 2024](https://medium.com/sahibinden-technology/package-by-layer-vs-package-by-feature-7e89cde2ae3a),
   [Wasowski Medium 2026](https://medium.com/@wasowski.jarek/modular-monolith-instead-of-microservices-what-changed-when-the-ai-agent-started-reading-code-c586d9f63fd7))

5. **The Numba JIT kernel extraction pattern has a clear precedent in scipy and scientific
   Python.** SciPy's pattern: `_lib/` for cross-subpackage shared internals (including compiled
   extensions and low-level kernels). AVC's analog: `varieties/_kernels.py` for the 11 `@njit`
   functions, keeping the process-global `numba.config.THREADING_LAYER` side-effect in a single
   file. This is the exact shape the r2 brief specifies. No 2026 dissent found on this.
   [CONSENSUS in scientific Python for kernel isolation]
   ([SciPy scipy/_lib](https://github.com/scipy/scipy),
   [Scientific Python SPEC 1](https://scientific-python.org/specs/))

**What's contested (flagged for the designer):**
- Whether `surfaces.py` generators belong in `varieties/` (domain-math) or in a flat module
  at root — the brief's brief says `varieties/` but this is a judgment call.
- Whether the `_qt/` prefix (private) or `panels/` (public) is right for AVC's panels —
  r1 landed `panels/` as a flat subpackage; r2 proposes renaming to `_qt/panels/`.
- File-size hard limits — still no formal standard; 800 LOC is informal practice.
- Whether per-subpackage CLAUDE.md is worth the maintenance cost for a single-developer project.
- The ETH Zurich finding that context files add cost without proportional benefit is relevant
  to whether sub-subpackage CLAUDE.md files are worth adding.

---

## 2. Canonical layouts (Tier 1 sources)

### 2.1 The Hitchhiker's Guide to Python — flat layout (dissenting historical position)

Source: <https://docs.python-guide.org/writing/structure/> (accessed 2026-05-23)

```
README.rst
LICENSE
setup.py
requirements.txt
sample/
    __init__.py
    core.py
    helpers.py
docs/
tests/
```

Key quote: *"Your library does not belong in an ambiguous src or python subdirectory."*
This is the dissenting but historically influential position. Still widely cited; increasingly
a minority view. [OPINION — single source lineage; legacy weight but weakening in 2026.]

**AVC applicability:** Low direct value. The flat preference aligns with AVC staying at root,
but the guide predates feature-subpackage patterns and Numba-style kernel isolation.

### 2.2 pyOpenSci Python Packaging Guide — src layout for scientific Python

Source: <https://www.pyopensci.org/python-package-guide/package-structure-code/python-package-structure.html>
(accessed 2026-05-23)

```
myPackageRepoName/
├── CHANGELOG.md        # [PASS in r2]
├── CODE_OF_CONDUCT.md  # [still FAIL]
├── CONTRIBUTING.md     # [still FAIL]
├── docs/               # [still FAIL]
├── LICENSE             # [PASS in r2]
├── README.md           # [PASS]
├── pyproject.toml      # [PASS in r2]
├── src/
│   └── myPackage/
│       ├── __init__.py
│       ├── moduleA.py  # → varieties/ in AVC's r2
│       └── moduleB.py  # → render/ in AVC's r2
└── tests/
```

Key quote: *"We strongly suggest, but do not require, that you use the src/ layout."*
CHANGELOG, LICENSE, README, pyproject.toml are **required**. [CONSENSUS within scientific
Python.] AVC now satisfies all four. The src/ step is optional for an app; the feature-
subpackage shape is independent of src/ vs flat.

### 2.3 PyPA — src-leaning neutral

Source: <https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/>
(accessed 2026-05-23 — confirmed live)

The three src advantages: (1) forces install for testing, (2) prevents accidental in-dev
import, (3) prevents setup.py becoming importable. For AVC — advantage (1) has less force
because tests use `sys.path.insert(0, ...)` already (AI-2 invariant). The flat-package-plus-
subpackages shape AVC is adopting is still the pragmatic correct choice for r2.
[CONSENSUS that PyPA leans src for libraries; silent on desktop apps.]

### 2.4 Scientific Python Development Guide / SPECs

Sources: <https://learn.scientific-python.org/development/>, <https://scientific-python.org/specs/>
(accessed 2026-05-23)

| SPEC | Title                                     | Status   | AVC Relevance for r2 |
|------|-------------------------------------------|----------|----------------------|
| 1    | Lazy Loading of Submodules and Functions  | Endorsed | HIGH — VTK import cost in varieties/ |
| 0    | Minimum Supported Dependencies            | Endorsed | MEDIUM — pyproject.toml now present |

**SPEC 1 is directly applicable to the r2 varieties/ extraction.** Once surfaces.py is split
into `varieties/k3.py`, `varieties/enriques.py`, etc., the `varieties/__init__.py` should use
lazy loading so that importing `varieties` does not trigger pyvista + numba JIT compilation
until a generator is actually called. Pattern:

```python
# varieties/__init__.py — SPEC 1-style lazy loading
def __getattr__(name):
    if name in _GENERATORS:
        from importlib import import_module
        mod = import_module(f".{_GENERATORS[name]}", package=__name__)
        return getattr(mod, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
```

[CONSENSUS within scientific Python for heavy-dep packages.]

### 2.5 Cookiecutter Data Science v2 — flat layout for data projects

Source: <https://cookiecutter-data-science.drivendata.org/> (accessed 2026-05-23)

Flat layout (no `src/`). Relevant to AVC: `references/` (papers, manuals, citable mathematical
sources — directly applicable to AVC's mathematical references) and `notebooks/` (exploratory
analysis). Not directly applicable for r2 scope. [OPINION for AVC; CONSENSUS for ML/data.]

### 2.6 Ionelmc's src argument — the foundational case

Source: <https://blog.ionelmc.ro/2014/05/25/python-packaging/> (accessed 2026-05-23)

Core claim: without src, `setup.py` and config files become importable; tests run against dev
copy not installed copy. Still the canonical reference. [CONSENSUS — most-cited piece on this
debate; still holds in 2026.] Not the primary concern for r2's feature-subpackage work.

---

## 3. Reference orgs analyzed

| Org | URL | Top-level shape | Exemplary | Outdated / quirky |
|-----|-----|-----------------|-----------|-------------------|
| **napari** (Qt+VTK, AVC analog) | <https://github.com/napari/napari> | `src/napari/{_app_model,_qt,_vendor,_vispy,components,layers,plugins,settings,utils}` + `examples/`, `resources/`, `tools/` | **CONFIRMED 2026:** `_qt/` explicitly documented as "code that directly imports Qt"; mirrors napari/ structure with 'q' prefix. `_vispy/` parallel pattern for render. Src layout. Has `experimental/` for in-flux code. | No AGENTS.md or CLAUDE.md (404 confirmed 2026-05-23). `_tests/` inside package. |
| **PyVista** (AVC's render dep) | <https://github.com/pyvista/pyvista> | `pyvista/{core,plotting,utilities,jupyter,trame,demos,examples,typing,_cli,_vtk.py}` | Flat layout, disciplined: `core/` (data model), `plotting/` (render), `utilities/` (shared). `_cli/`, `_vtk.py` privately-prefixed. Ships `context7.json`. | No AGENTS.md (404 confirmed 2026-05-23). `setup.py` still present alongside `pyproject.toml`. |
| **Spyder** (Qt IDE) | <https://github.com/spyder-ide/spyder> | `spyder/{api,app,config,plugins,utils,widgets,windows,tests}` | `app/` subpackage for launcher. `api/` for public surface. `widgets/` for reusable Qt. `windows/` for top-level windows. | No AGENTS.md (404 confirmed 2026-05-23). 40+ root-level files — high noise. |
| **pandas** | <https://github.com/pandas-dev/pandas> | flat: `pandas/{api,arrays,core,errors,io,plotting,tseries,...}` + **AGENTS.md** | **Ships AGENTS.md.** Structure is: Project Overview, Persona/Tone, Guidelines, Decision Heuristics, Type Hints, Docstring Guidance, Pull Requests. Local-path references to contributing docs. | Tests inside package — diverges from pyOpenSci. Build complexity is cargo-cult risk for smaller apps. |
| **SciPy** | <https://github.com/scipy/scipy> | flat: `scipy/{cluster,constants,fft,integrate,interpolate,linalg,...,_lib}` + `benchmarks/`, `doc/`, `tools/` | `_lib/` for cross-subpackage shared internals (compiled extensions, kernels). Ships `tach.toml` (module-boundary linter). **Textbook subpackage discipline by mathematical domain.** | Build complexity (meson, pixi) is project-size-appropriate but cargo-cult risk for AVC. |
| **Django** | <https://github.com/django/django> | flat: `django/{apps,conf,contrib,core,db,dispatch,forms,http,utils,views}` + `docs/`, `tests/` | Feature-clean subpackages. `tests/` sibling to `django/`. `contrib/` for official-but-optional. `utils/` *subpackage* with internal structure — not a grab-bag file. | `utils/` only justifiable as a subpackage with subdirs; a single `utils.py` file at this size would be Dunghill. |
| **Kubernetes** (Go) | <https://github.com/kubernetes/kubernetes> | `cmd/`, `pkg/`, `staging/`, `hack/`, `api/`, `build/` + **AGENTS.md** | **Ships AGENTS.md.** `cmd/` = entry points. `hack/` = dev scripts. `staging/` = vendored-but-owned. | `vendor/` is Go-specific; do not copy to Python. |
| **ParaView** (scientific viz) | <https://github.com/Kitware/ParaView> | `Qt/`, `Plugins/`, `Clients/`, `Remoting/`, `VTKExtensions/`, `Web/`, `Wrapping/`, `Incubator/` | **Mirrors AVC's domain at scale.** `Qt/` (GUI), `VTKExtensions/` (VTK additions), `Incubator/` (experimental). The `Incubator/` pattern is excellent for "not yet promoted" code. | C++/CMake-heavy; capitalized names break Python import convention. Partitioning transfers; names don't. |

**Summary across 8 orgs:** [CONSENSUS] domain-or-role-based subpackage split, README + LICENSE
+ pyproject.toml at root, tests/ as sibling. napari, PyVista, Spyder still have no AGENTS.md
as of 2026-05-23 — AVC is ahead of its reference peers in this dimension.

**New 2026 observation:** napari's architecture documentation now explicitly states the `_qt/`
isolation principle in written docs (not just implied by directory name). This is the strongest
available citation for the `_qt/` pattern specifically.

---

## 4. Patterns to adopt (with AVC applicability ratings — conservative bias RELAXED)

Rating: HIGH = clear win for AVC now; MEDIUM = worth doing after initial restructure;
LOW = premature for AVC's current size.

Note: ratings marked with `[r1→r2 upgrade]` were MEDIUM in the r1 brief but are HIGH
here because the conservative bias is relaxed and the prerequisite infrastructure (panels/,
pyproject.toml, AGENTS.md, LICENSE, CHANGELOG) landed in r1.

### P1. `varieties/` subpackage — extracted from surfaces.py — HIGH [r1→r2 upgrade]

Move the 14 generator functions, 11 Numba `@njit` kernels, 2 pipeline helpers
(`_marching_cubes_to_polydata`, `_grid_to_polydata`), 2 dataclasses (`Surface`, `ParamSpec`),
and the `VARIETIES` dict + tooltip strings into a `varieties/` subpackage:

```
varieties/
├── __init__.py          # re-exports VARIETIES, Surface, ParamSpec; lazy-loads generators
├── registry.py          # VARIETIES dict + VARIETY_TOOLTIPS + SUBTYPE_TOOLTIPS
├── _kernels.py          # 11 @njit field kernels + numba.config side-effect
├── _marching.py         # _marching_cubes_to_polydata + _grid_to_polydata
├── k3.py                # K3 surface generators (fermat, kummer, dwork, ...)
├── enriques.py          # Enriques surface generators
├── calabi_yau.py        # Calabi-Yau generators
└── fano.py              # Fano variety generators
```

The `_kernels.py` extraction solves the Numba side-effect problem: `numba.config.THREADING_LAYER`
is set once at module import in `_kernels.py`, and every generator file imports from `_kernels`
rather than defining kernels inline. Tests import `from varieties._kernels import
_fermat_field_kernel` (or the shim `from surfaces import _fermat_field_kernel` via
`__getattr__` on surfaces.py).

([napari layers/ by-domain pattern](https://github.com/napari/napari),
[scipy _lib/ for kernels](https://github.com/scipy/scipy),
[Scientific Python SPEC 1](https://scientific-python.org/specs/),
[r2 brief specification])

**AVC note:** This is the highest-ROI change in r2. surfaces.py at 1811 LOC is item #17 FAIL.
Splitting into 6-8 files averaging 200-300 LOC each transforms the second-largest file in the
repo into a navigable subpackage. The import shim on `surfaces.py` (as a thin backward-compat
wrapper) is explicitly required by the r2 brief. The tests/test_numba_field_kernels.py
`from surfaces import _<name>_field_kernel` pattern must be preserved via `__getattr__`.

### P2. `render/` subpackage — absorbing render_worker.py — HIGH [r1→r2 upgrade]

Move `render_worker.py` to `render/worker.py`. This:
- Makes the render domain boundary explicit (same pattern as PyVista's `core/` vs `plotting/`
  separation, napari's `_vispy/` isolation).
- Creates a home for any future rendering helpers without polluting root.
- Enables clear import rule: `render/` may import `varieties/` and `pyvista`; nothing imports
  from `render/` except `app.py`.

```
render/
├── __init__.py          # re-exports RenderWorker
└── worker.py            # RenderWorker class (was render_worker.py)
```

`render_worker.py` at root becomes a shim (same pattern as panels/).

([PyVista core/ vs plotting/](https://github.com/pyvista/pyvista),
[napari _vispy/ separation](https://napari.org/dev/developers/architecture/dir_organization.html))

**AVC note:** render_worker.py is only 225 LOC — the move is structural, not size-driven. The
payoff is: `render/` as a named domain boundary makes the import graph's already-correct
direction (surfaces → render → app) explicit and enforceable by import-linter if desired.

### P3. `cross_section/` subpackage — with pure function extraction — HIGH [r1→r2 upgrade]

Extract `view_panel.py`'s `clip_to_domain` pure function into `cross_section/__init__.py` or
`cross_section/clip.py`. The subpackage:

```
cross_section/
├── __init__.py          # exports clip_to_domain
└── clip.py              # pure function: clip_to_domain(mesh, domain) -> PolyData
```

This makes the cross-section math independently testable and separates it from the Qt view
panel entirely. The `test_clip_domain.py` test (which already imports from `panels`) can be
updated to import from `cross_section` directly.

([spyder cross-section-like math isolation in api/](https://github.com/spyder-ide/spyder),
[Domain-first decomposition, Sahibinden Tech 2024](https://medium.com/sahibinden-technology/package-by-layer-vs-package-by-feature-7e89cde2ae3a))

**AVC note:** MEDIUM-risk. The clip_to_domain function may have Qt-adjacent side effects
(logging, VTK calls) that need care when extracting. Evaluate in the symbol map.

### P4. `_qt/` subpackage — formalization of the panels/ convention — HIGH [r1→r2 upgrade]

r1 landed `panels/` as a flat subpackage. r2's brief proposes renaming to `_qt/panels/` or
restructuring as a `_qt/` container with:

```
_qt/
├── __init__.py
├── panels/              # was panels/ at root (r1 shape)
│   ├── __init__.py
│   ├── appearance.py
│   ├── parameter_grid_panel.py
│   ├── parameters.py
│   └── view.py
├── icons.py             # was icons.py at root
├── helpers.py           # was ui_helpers.py at root
└── styles.py            # was styles.py at root (QSS-coupled; Qt-only data)
```

**The napari documentation explicitly justifies this pattern:** "we try to confine code that
directly imports Qt to the folders `_qt/` and `_vispy/`." The underscore prefix signals
"internal, not a stable API contract."

Alternative: keep `panels/` at root as-is (already landed) and do NOT rename to `_qt/panels/`
— a pragmatic choice given r1 shims are already in place. The designer must weigh:
- Cost of adding another level of indirection on top of r1's completed work.
- Benefit of the explicit `_qt/` domain boundary for future contributors.

([napari _qt/ documentation](https://napari.org/dev/developers/architecture/dir_organization.html),
[napari architecture confirmed live 2026-05-23])

**AVC note:** If the designer adopts `_qt/` fully, `icons.py`, `ui_helpers.py`, and `styles.py`
all move inside. `styles.py` is QSS-coupled and used only by Qt code — it belongs in `_qt/`.
`icons.py` imports PySide6 + qtawesome + styles — clearly Qt-only. `ui_helpers.py` imports
PySide6 + parameter_grid + styles — Qt-coupled. All three satisfy the `_qt/` criterion.

### P5. `pyproject.toml` — add `[project.scripts]` entry point — MEDIUM

Current `pyproject.toml` explicitly notes "No [project.scripts] entry-points — preserves
`python app.py` invocation pattern." For r2, once `app.py` is a proper module (or remains at
root with a `main()` function), adding:
```toml
[project.scripts]
avc-viewer = "app:main"
```
would allow `pip install -e . && avc-viewer` as the launch pattern. Low-risk, high-payoff
for packaging discipline. [CONSENSUS that entry-points are pyproject canonical in 2026]

### P6. Numba threading-layer side-effect anchoring — HIGH (constraint, not a pattern)

This is not a "pattern to adopt" but a hard constraint on any split of surfaces.py. The
`numba.config.THREADING_LAYER = "workqueue"` must execute:
- Exactly once per process.
- Before any `@njit` function is called.
- In a single file that is guaranteed to be imported before any kernel module.

The recommended implementation: put it at the top of `varieties/_kernels.py`, which is
imported by every kernel-using module. The `varieties/__init__.py` should eagerly import
`varieties._kernels` to ensure the side effect fires before any lazy-loading resolves.

([AVC AI-4 invariant in .claude/references/app-invariants.md],
[Numba docs on threading configuration — UNVERIFIED on exact URL but the behavior is
confirmed in AVC's test suite])

**AVC note:** This is inviolable. Any split plan that doesn't address this fails AI-4.

### P7. `__getattr__` shim pattern for backward-compatible moves — HIGH [already in flight]

r1 demonstrated the pattern: move file content, leave a thin `__getattr__`-based shim at the
original path, emit DeprecationWarning. r2 must extend this to:
- `surfaces.py` → thin shim re-exporting from `varieties/`
- `render_worker.py` → thin shim re-exporting from `render/worker.py`
- Existing `panels/` root shims (appearance_panel.py, etc.) — already done in r1

This pattern is used by pandas (for backward-compat module renames), scipy, and napari.
[CONSENSUS for backward-compatible Python module moves]

### P8. Import graph direction enforcement — MEDIUM

AVC's import graph is already correctly directed (surfaces → render → app; no circular deps).
Once feature subpackages exist, this becomes enforceable with `tach check` or Import-Linter.
The enforced contract for r2 shape:
```
app.py may import: _qt/, render/, varieties/, cross_section/, parameter_grid.py, styles.py
render/ may import: varieties/, pyvista (NOT _qt/)
_qt/ may import: varieties/, parameter_grid.py, styles.py, icons.py (NOT render/)
varieties/ may import: numpy, numba, pyvista (NOT _qt/, NOT render/)
cross_section/ may import: varieties/, pyvista (NOT _qt/)
```

([SciPy tach.toml usage](https://github.com/scipy/scipy),
[Kraken Import-Linter](https://blog.europython.eu/kraken-technologies-how-we-organize-our-very-large-pythonmonolith/))

**AVC note:** Tach/Import-Linter are already in pyproject.toml dependencies (pydeps). Adding
a tach.toml after r2's subpackage layout is finalized would be a natural Batch 5 cleanup.

### P9. SPEC 1 lazy loading for varieties/ — MEDIUM

The `varieties/__init__.py` should expose generators via SPEC 1-style lazy `__getattr__` to
avoid eager Numba JIT compilation on import. Only the `_kernels.py` import (which sets the
threading layer side effect) needs to be eager.

Pattern:
```python
# varieties/__init__.py
import varieties._kernels  # eager: ensures numba.config side-effect fires

_GENERATOR_MODULES = {
    "fermat_surface": ".k3",
    "kummer_surface": ".k3",
    "dwork_pencil": ".k3",
    ...
}

def __getattr__(name):
    if name in _GENERATOR_MODULES:
        from importlib import import_module
        mod = import_module(_GENERATOR_MODULES[name], package=__name__)
        return getattr(mod, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
```

([Scientific Python SPEC 1](https://scientific-python.org/specs/))

**AVC note:** This is a MEDIUM priority — correct but not required for correctness. The eager
import of `_kernels` is required (for the side effect); the lazy load of generators is nice-to-
have for cold-start latency.

### P10. Per-subpackage CLAUDE.md / AGENTS.md — LOW (with 2026 caution)

The 2026 ETH Zurich study finding changes the calculus here: human-curated context files add
only ~4% to agent task success rate while increasing costs ~19%. For AVC as a single-developer
project, the root AGENTS.md + CLAUDE.md provides sufficient orientation. Per-subpackage files
are worth adding only if:
- A subpackage has non-obvious constraints (varieties/_kernels.py's Numba side-effect IS
  genuinely non-obvious — a per-subpackage note there would add value).
- The subpackage is edited independently and has domain-specific conventions.

If added, keep them under 20 lines (the ETH Zurich guidance: "only what agents cannot
independently discover").

([ETH Zurich AGENTS.md study](https://arxiv.org/html/2602.11988v1),
[agents.md per-folder precedence](https://agents.md/),
[Augment Code guide](https://www.augmentcode.com/guides/how-to-build-agents-md))

### P11. `parameter_grid.py` stays at root or moves to `varieties/` — MEDIUM

`parameter_grid.py` (362 LOC) contains parameter grid data model (ParameterGrid, RangeParam,
etc.) with imports only from `surfaces`. The r2 brief says "move into `varieties/parameter_grid.py`
if the designer judges it belongs there." Evidence for `varieties/`:
- It imports from `surfaces` (which will become `varieties/`).
- It contains math data structures (range grids for variety parameters).
- Having it at root after surfaces.py is moved creates a dangling import.

Evidence for keeping at root:
- It's consumed by panels/_qt/ code (parameter_grid_panel.py imports it).
- It's a cross-cutting concern — used by both domain math and UI.

[CONTESTED — no external source resolves this for AVC's exact case.]

**AVC note:** The designer should declare this explicitly. The import chain is:
`parameter_grid.py` → `surfaces` (varieties/) and ← `panels/parameter_grid_panel.py`.
Moving it to `varieties/parameter_grid.py` makes the data direction explicit; keeping at root
avoids adding `_qt/` importing from `varieties/` (which it already does for surfaces).

### P12. Root-file count reduction — LOW

Current: 21 visible files at root (item #10 FAIL by 1). After r2's restructure:
- Root shims for panels (4 × 18 LOC files): remain as backward-compat shims.
- After shim removal milestone: 17 root files (PASS).
- `MOVES.md` at root: not a standard pattern; consider moving to `.claude/notes/` after it
  serves its purpose.
- `pytest.ini`: redundant once `pyproject.toml` has `[tool.pytest.ini_options]`.

[OPINION — minor cleanup; not a r2 priority but worth noting for Batch 4.]

### P13. `styles.py` stays or moves to `_qt/` — HIGH (for r2 _qt/ scope)

`styles.py` at 708 LOC is QSS-coupled (Qt Style Sheets) and used only by Qt code.
Per napari's explicit rule: code that imports Qt stays in `_qt/`. `styles.py` imports only
itself (the import graph shows `styles.py: [styles]` — a self-import artifact — plus it uses
QSS strings). It has no Qt *imports* (it just defines stylesheet strings), but it is logically
Qt-coupled (the strings are PySide6 QSS syntax). The designer should decide:
- Move to `_qt/styles.py` (logical coupling → co-locate with Qt code).
- Keep at root (it has no `import PySide6` line itself).

The AVC import graph: `icons.py → styles`, `panels/appearance.py → styles`,
`panels/parameter_grid_panel.py → styles`, `ui_helpers.py → styles`, `app.py → styles`.
All callers are Qt code. Moving to `_qt/` would make `_qt/` import `_qt/styles` internally —
clean.

([napari _qt/ pattern](https://napari.org/dev/developers/architecture/dir_organization.html))

---

## 5. Patterns to AVOID (with how-to-spot)

### A1. Loose .py files at root as the primary source layout [CONSENSUS]

AVC still has `app.py`, `surfaces.py`, `styles.py`, `icons.py`, `parameter_grid.py`,
`ui_helpers.py`, `render_worker.py` at root alongside the `panels/` subpackage. The r2
subpackage extraction addresses this by pulling the two largest files (surfaces.py → varieties/,
render_worker.py → render/) into named domain packages. The remaining root files are either
entry points (app.py — by design) or candidates for _qt/ consolidation.
**How to spot:** `find . -maxdepth 1 -name "*.py" | grep -v test` returns >3 results.

### A2. Grab-bag `utils.py` — the "Dunghill" anti-pattern [CONSENSUS]

`ui_helpers.py` (264 LOC) is at the Dunghill warning threshold. It contains debounce logic
(`_DebouncedButton`) and generic Qt utilities. Currently borderline-acceptable; moving it to
`_qt/helpers.py` within the `_qt/` subpackage gives it a clear domain-scoped home.
**How to spot:** any file named `*helpers.py` or `*utils.py` over 200 LOC containing functions
spanning more than 2 unrelated domain types.
([Matti Lehtinen](https://mattilehtinen.com/articles/dunghill-anti-pattern-why-utility-classes-and-modules-smell/))

### A3. Monolith files over 800 LOC [CONTESTED threshold, CONSENSUS on the problem]

AVC's outstanding violations:
- `app.py` (1900 LOC) — target for a future milestone (NOT r2 per brief).
- `surfaces.py` (1811 LOC) — r2's primary decomposition target.
- `tests/test_styles_palette.py` (1262 LOC) — test file; higher LOC threshold applies to
  parametrized tests but this is still a yellow flag.
- `panels/appearance.py` (738 LOC) — in panels/; borderline at ~800 LOC.
- `panels/parameter_grid_panel.py` (719 LOC) — in panels/; borderline.

**How to spot:** `wc -l *.py panels/*.py | sort -rn | head -10`
([Informal 2025-2026 AI-coding literature; no single formal source])

### A4. Package-by-layer [CONSENSUS for modular monoliths]

Naming subpackages after architectural roles (controllers/, services/, models/) rather than
domain concepts (varieties/, render/, _qt/). AVC's proposed r2 shape is explicitly package-
by-feature; no layered names exist in the plan. Verify the designer does not introduce
`core/`, `utils/`, `lib/` as top-level catch-alls.
**How to spot:** subpackage names are architectural roles, not domain concepts.
([Sahibinden Tech 2024](https://medium.com/sahibinden-technology/package-by-layer-vs-package-by-feature-7e89cde2ae3a),
[Kraken EuroPython 2024](https://blog.europython.eu/kraken-technologies-how-we-organize-our-very-large-pythonmonolith/))

### A5. Splitting `app.py` in r2 [OPINION — AVC-specific scope constraint]

r2 brief explicitly says: "keep app.py at root as the entry point (do NOT Extract Class on it
in this restructure — that's a separate milestone)." Extracting `MainWindow` from `app.py` is
a HIGH-risk operation (AI-9 re-entrancy guard, render pipeline, signal wiring). Even with the
conservative bias relaxed, this does not mean app.py should be touched in r2. The Kraken and
napari patterns for this decomposition are valid inputs for a *later* milestone.
**How to spot:** any r2 plan that moves `app.py` code into a new subpackage.

### A6. Auto-generated AGENTS.md / CLAUDE.md [NEW-2026 consensus]

The ETH Zurich study (arxiv 2602.11988v1) found LLM-generated context files *reduce* task
success by ~2-3% vs no context file. AVC's 148-line AGENTS.md/CLAUDE.md pair (human-curated)
is the correct approach. Do not auto-generate or bulk-expand these files.
**How to spot:** context file > 200 lines, or contains directory listings, or duplicates README.
([ETH Zurich 2026 study](https://arxiv.org/html/2602.11988v1))

### A7. Three-level nesting for r2 [OPINION — avoid in initial decomposition]

The r2 target shape `_qt/panels/view.py` is already 3 levels deep from root, but 2 levels from
the implied package root (if AVC stays flat). If `_qt/` is adopted, keep panels/ as a direct
child: `_qt/panels/*.py`, NOT `_qt/panels/view/controller.py` etc.
**How to spot:** any subpackage path with 4+ path separators relative to repo root.
([Software Carpentry two-deep heuristic](https://intermediate-and-advanced-software-carpentry.readthedocs.io/en/latest/structuring-python.html))

### A8. Framework adapter code outside `_qt/` [CONSENSUS for Qt+VTK apps]

As napari documents: code that directly imports Qt must live in `_qt/`. AVC currently has
`icons.py`, `ui_helpers.py`, `styles.py` at root alongside `panels/`. After r2, none of these
should remain as loose files if `_qt/` is adopted.
**How to spot:** `grep -l "import PySide6" *.py` returns files outside `_qt/`.
([napari architecture docs](https://napari.org/dev/developers/architecture/dir_organization.html),
confirmed live 2026-05-23)

### A9. Numba config side-effect in multiple files [AVC-specific; HIGH severity]

Any r2 design that puts `numba.config.THREADING_LAYER = "workqueue"` in more than one module
risks process-global clobbering if import order changes. It must be exactly one file:
`varieties/_kernels.py`.
**How to spot:** `grep -r "THREADING_LAYER" varieties/` returns more than one file path.
([AVC AI-4 invariant, .claude/references/app-invariants.md])

### A10. Breaking `from surfaces import _<name>_field_kernel` [AVC-specific; CRITICAL]

`tests/test_numba_field_kernels.py` uses `from surfaces import _fermat_field_kernel` etc.
This import path MUST remain valid after r2. The `surfaces.py` `__getattr__` shim must
delegate to `varieties._kernels._<name>_field_kernel`.
**How to spot:** running `pytest tests/test_numba_field_kernels.py` fails with ImportError.

### A11. Overly detailed per-subpackage CLAUDE.md files [NEW-2026 caution]

Given the ETH Zurich finding that comprehensive context files increase costs 19-23% without
proportional benefit, adding large per-subpackage documentation is counterproductive. Keep any
per-subpackage CLAUDE.md under 20 lines or skip them entirely for r2.
**How to spot:** any new `varieties/CLAUDE.md` or `render/CLAUDE.md` over 20 lines.
([ETH Zurich 2026](https://arxiv.org/html/2602.11988v1))

### A12. Removing existing backward-compat shims prematurely [r1/r2 sequencing]

r1 landed shims for all 4 panel files (appearance_panel.py, view_panel.py, parameters_panel.py,
parameter_grid_panel.py). r2 must add shims for surfaces.py and render_worker.py. None of the
r1 shims should be removed in r2 — the brief says "every old import path gets a __getattr__
shim for one milestone."
**How to spot:** any r2 batch that deletes a shim file before the shim-removal milestone.

---

## 6. AI-navigability layer (2026 state of the art — updated for r2)

### AGENTS.md / CLAUDE.md current state in AVC

AVC's `AGENTS.md` and `CLAUDE.md` are both 148 lines (identical content — correctly maintained
in sync). Both are within Anthropic's 200-line recommendation and the Augment Code 2026
guidance's 150-200 line split-threshold. [PASS on items #7, #8, #21]

The ETH Zurich 2026 study finding: context files should contain only what agents cannot
discover from existing documentation. AVC's files should reference CONTEXT.md and
app-invariants.md by path rather than inline their content — already the correct pattern.

After r2 adds `varieties/`, `render/`, `cross_section/`, and optionally `_qt/`, update the
AGENTS.md "directory map" section to include those subpackages. Budget: keep under 200 lines.
If the update would push AGENTS.md over 200 lines, trim the description of old files that have
become shims.

### Per-subpackage orientation files

The ETH Zurich finding changes the prior r1 recommendation (LOW → even lower for AVC):
- Do NOT add per-subpackage CLAUDE.md files in r2 for all subpackages.
- EXCEPTION: `varieties/_kernels.py` has a non-obvious Numba constraint that is exactly the
  kind of "thing agents cannot discover" the ETH Zurich paper recommends including. A 5-line
  comment block in `varieties/_kernels.py` docstring is more appropriate than a CLAUDE.md there.

### File-size norms (updated)

Current AVC state after r1:

```
2026 LOC audit (root + panels/):
  CRITICAL (>1500):  app.py 1900, surfaces.py 1811
  HIGH (>800):       tests/test_styles_palette.py 1262 [test file, higher tolerance]
  BORDERLINE (>500): panels/appearance.py 738, panels/parameter_grid_panel.py 719,
                     styles.py 708, tests/test_numba_field_kernels.py 708,
                     panels/view.py 503
  ACCEPTABLE (<500): icons.py 373, panels/parameters.py 368, parameter_grid.py 362
                     render_worker.py 225, ui_helpers.py 264
```

After r2 (projected):
- surfaces.py → shim (~18 LOC) + varieties/k3.py (~300), varieties/enriques.py (~250),
  varieties/calabi_yau.py (~200), varieties/fano.py (~150), varieties/_kernels.py (~280),
  varieties/_marching.py (~80), varieties/registry.py (~100) — all under 800 LOC. [item #17 PASS]
- render_worker.py → shim (~18 LOC) + render/worker.py (225 LOC). [already under 800]

### Import graph (updated for r2 target shape)

The r2 target import topology:

```
varieties/_kernels.py  → [numba, numpy]               # no pyvista here; pure math
varieties/k3.py        → [varieties._kernels, numpy,   # generators; pyvista for return type
                           pyvista]
varieties/registry.py  → [varieties.*]                 # VARIETIES dict
render/worker.py       → [varieties, pyvista,          # render pipeline; no Qt
                           dataclasses]
_qt/helpers.py         → [PySide6, varieties,          # was ui_helpers.py
                           parameter_grid, _qt.styles]
_qt/panels/view.py     → [PySide6, numpy, pyvista,     # was panels/view.py
                           _qt.icons]
_qt/panels/parameters.py → [PySide6, _qt.icons,       # was panels/parameters.py
                              parameter_grid, varieties]
app.py                 → [PySide6, pyvistaqt,          # entry point; still at root
                           varieties, render, _qt,
                           parameter_grid, styles]
```

The key invariant: `varieties/` and `render/` have no Qt imports. [Already satisfied in
current code; r2 makes it structural.]

### Naming conventions

- `varieties/` — describes what's inside (mathematical variety generators). Better than
  `surfaces/` (pyvista uses "surfaces" for mesh primitives, which could confuse).
- `render/` — clear verb-object; alternative `rendering/` is wordier with no benefit.
- `_qt/` — underscore prefix signals "Qt-framework adapter, not a stable API contract."
- `cross_section/` — matches AVC's project name and domain vocabulary.
- `_kernels.py` — underscore prefix signals "private, implementation detail."
- `registry.py` — standard name for "thing that registers things"; clear single purpose.

---

## 7. Qt+VTK+PyVista special considerations (updated for r2)

### What napari's documented architecture says (2026 confirmation)

Source: <https://napari.org/dev/developers/architecture/dir_organization.html> (accessed
2026-05-23 — confirmed live, copyright 2026)

Directly applicable to AVC:

1. **`_qt/` isolation is explicit policy, not just convention.** Quote: *"we try to confine
   code that directly imports Qt... to the folders `_qt/` and `_vispy/`."* The folder structure
   inside `_qt/` mirrors the outer napari/ structure with 'q' prefixed to names.

2. **Subpackages mirror the outer structure.** napari's `_qt/_qapp_model/` mirrors
   `_app_model/`. For AVC: `_qt/panels/` mirrors `panels/` at root. When r2 moves `panels/` to
   `_qt/panels/`, the outer structure can have a placeholder `panels/` or the shims stay at root.

3. **`experimental/` for in-flux code.** AVC could use `varieties/experimental/` for any new
   variety families under active development. Not a r2 requirement but a useful escape hatch.

4. **napari has NO AGENTS.md or CLAUDE.md** as of 2026-05-23. AVC is ahead of its canonical
   reference on AI-navigability.

### What Spyder's `app/` subpackage says about AVC's app.py

Spyder splits `app/` into: `main.py`, `mainwindow.py`, `restart.py`. This is the pattern for
AVC's app.py split in a **future milestone** (not r2). r2's brief is explicit: "keep app.py at
root as the entry point."

The deferred split would look like:
```
app/
├── __init__.py
├── main.py              # entry point (was __main__ logic)
├── main_window.py       # MainWindow class (was app.py MainWindow)
└── render_pipeline.py   # _render_current + mesh lifecycle
```

This is noted here for the designer as "future work" to avoid the temptation to scope-creep r2.

### What PyVista's structure tells us about varieties/

PyVista separates:
- `pyvista/core/` — data model (mesh types, geometric operations)
- `pyvista/plotting/` — visualization (renderers, actors, colormaps)
- `pyvista/utilities/` — shared low-level utilities

AVC's `varieties/` maps to `pyvista/core/` (domain math, data structures), `render/` maps to
`pyvista/plotting/`. The analogy is direct.

### AVC-stack-specific constraints for r2

1. **Numba JIT side effect.** As documented above (P6, A9, A10). Non-negotiable.

2. **VTK import cost.** Once `varieties/` has `_kernels.py` and generators, the `pyvista`
   import will only fire when a generator is first called (if SPEC 1 lazy loading is used in
   `varieties/__init__.py`). This is a cold-start latency win.

3. **Threading boundary (AI-9).** The `_computing` single-flight guard lives in `app.py` and
   guards `render/worker.py` calls. If `render/worker.py` is moved in r2, the guard must
   travel with `app.py` — it is app-level state, not worker-level state.

4. **AI-1..AI-15 invariants.** All 15 invariants documented in
   `.claude/references/app-invariants.md` are inviolable. The ones most load-bearing for r2:
   - AI-2: test suite is Qt-free (VTK fixtures only). varieties/ tests must remain Qt-free.
   - AI-4: Numba threading side effect (addressed above).
   - AI-6: generators return `pyvista.PolyData` — move does not change return type.
   - AI-7: `VARIETIES` dict structure — `varieties/registry.py` must export identically.
   - AI-8: `from varieties.registry import VARIETIES` must work.
   - AI-9: `_computing` guard stays in app.py.
   - AI-12: mesh generator isolation — `varieties/` generators may not call Qt.
   - AI-15: mathematical docstring standard — moves with the generator functions.

---

## 8. Honest assessment — where the literature is contradictory or unsettled

1. **Whether `panels/` should become `_qt/panels/` or stay as `panels/`.** [CONTESTED — AVC
   specific.] r1 landed `panels/` as a flat subpackage with working shims. r2's brief proposes
   `_qt/panels/`. Napari's documented principle supports `_qt/`; the cost is one more level of
   directory depth and breaking the r1 shims' targets (the shims currently re-export from
   `panels.*`; they would need to re-export from `_qt.panels.*`). Honest answer: both are
   defensible; the designer should declare the choice and the brief should not prescribe it.

2. **Whether `styles.py` belongs in `_qt/`.** [CONTESTED — AVC specific.] `styles.py` imports
   no Qt but generates Qt Style Sheets. Napari's rule is "code that directly imports Qt" — by
   that strict reading, `styles.py` does not qualify for `_qt/`. But by logical coupling, it
   does. No external source resolves this for QSS-only files.

3. **Whether `parameter_grid.py` belongs in `varieties/` or stays at root.** [CONTESTED —
   see P11 above.] The import graph points both ways: it imports from surfaces (→varieties/)
   but is imported by panel code (→_qt/).

4. **File-size hard limits.** [CONTESTED threshold.] Still no formal authority. The 800-LOC
   informal threshold is converging in 2025-2026 AI-coding literature but is not a standard.
   The ETH Zurich study does not address file size directly.

5. **AGENTS.md size and content.** [FAST-MOVING.] The ETH Zurich 2026 finding (context files
   increase costs 19-23% for only ~4% benefit) somewhat undermines the "bigger AGENTS.md is
   better" intuition. The Augment Code 2026 guide says split into per-directory files "when it
   exceeds 150-200 lines." AVC's current AGENTS.md at 148 lines is right at this boundary.
   Don't expand it during r2 unless the update is necessary for new subpackage navigation.

6. **Whether `cross_section/` subpackage is a genuine domain or scope-creep for r2.** [OPINION.]
   The r2 brief includes it, but the `clip_to_domain` extraction is a semantic change (not just
   a mechanical move). The designer should classify this as a batch that requires test coverage
   verification, not just a file move.

7. **Auto-generation of context files.** [NEW-2026 CONSENSUS against.] The ETH Zurich finding
   is clear: auto-generated context files hurt more than help. This is new information since r1.

---

## 9. File-by-file evaluator checklist — 28 items

Evaluator script run: `python3 .claude/scripts/repository-architect/evaluate-checklist.py
restructure-feature-subpackages-2026q2-r2` on 2026-05-23.

**Overall result: 21/28 PASS** (up from 14/28 in r1).

| # | Check | Result | Evidence | Δ since r1 |
|---|---|---|---|---|
| 1 | README.md present at root | **PASS** | README.md exists | = |
| 2 | LICENSE present at root | **PASS** | LICENSE exists | r1→PASS |
| 3 | CHANGELOG.md present at root | **PASS** | CHANGELOG.md exists | r1→PASS |
| 4 | CODE_OF_CONDUCT.md present at root | **FAIL** | MISSING (optional for solo project) | = |
| 5 | CONTRIBUTING.md present at root | **FAIL** | MISSING (scales with team size) | = |
| 6 | pyproject.toml present at root | **PASS** | pyproject.toml exists | r1→PASS |
| 7 | AGENTS.md present at root | **PASS** | AGENTS.md exists (148 lines) | r1→PASS |
| 8 | CLAUDE.md present at root | **PASS** | CLAUDE.md exists (148 lines) | r1→PASS |
| 9 | No setup.py unless stated reason | **PASS** | absent | = |
| 10 | Top-level file count under 20 | **FAIL** | 21 visible files at root (1 over limit) | r1 was 15 + 5 added = still borderline |
| 11 | Importable code under a named package | **PASS** | `panels/` subpackage exists | r1→PASS (partial) |
| 12 | No utils.py over 200 LOC | **PASS** | `ui_helpers.py` (264 LOC) — no file named `utils.py`; borderline | = |
| 13 | No directory more than 2 levels deep | **PASS** | max depth: 1 (panels/ is 1 level deep) | = |
| 14 | Module names lowercase with underscores | **PASS** | all lowercase | = |
| 15 | Subpackages reflect domain/role, not layer | **PASS** | `panels/` is role-based, not layered | = |
| 16 | No `from foo import *` | **PASS** | no wildcard imports | = |
| 17 | No file over ~800 LOC | **FAIL** | `app.py` 1900, `surfaces.py` 1811, `tests/test_styles_palette.py` 1262 | = |
| 18 | tests/ directory exists as sibling | **PASS** | tests/ exists | = |
| 19 | docs/ directory exists at root | **FAIL** | MISSING | = |
| 20 | examples/ directory exists | **FAIL** | MISSING | = |
| 21 | AGENTS.md or CLAUDE.md under 300 lines | **PASS** | both at 148 lines | r1→PASS |
| 22 | CLAUDE.md doesn't contain lint rules | **PASS** | 0 linter mentions | r1→PASS |
| 23 | No temp/misc/backup dirs | **PASS** | clean | = |
| 24 | Framework-adapter code in named subpackages | **FAIL** | `panels/` exists but `icons.py`, `ui_helpers.py`, `styles.py` remain at root. No `_qt/` subpackage | partial r1 improvement |
| 25 | .gitignore covers __pycache__, .pytest_cache, etc. | **PASS** | .pytest_cache/ now present | r1→PASS |
| 26 | Import graph has no cycles | **PASS** | [UNVERIFIED — no circular deps observed in import graph] | = |
| 27 | `python -c "import setup"` fails | **PASS** | no setup.py | = |
| 28 | Every top-level subpackage has __init__.py docstring | **PASS** | `panels/__init__.py` has docstring | r1→PASS |

### Items resolved in r1 (FAIL→PASS): 7 items (2, 3, 6, 7, 8, 21, 22, 25, 28)
### Items r2 targets: items 17 (surfaces.py LOC), 24 (framework adapters), 11 partial (varieties/, render/ subpackages)
### Items r2 will close item #17: surfaces.py split into varieties/ subpackage resolves the primary LOC violation. app.py remains (deferred per brief).
### Items outside r2 scope: 4 (CODE_OF_CONDUCT), 5 (CONTRIBUTING), 19 (docs/), 20 (examples/)
### Item #10: closes to PASS once shims are removed (future milestone); stays FAIL in r2.
### Item #24: closes to full PASS once icons.py + ui_helpers.py + styles.py move to `_qt/`.

### Priority for r2 by checklist impact:

| Priority | Item | Work | Impact |
|----------|------|------|--------|
| P1 — CRITICAL | #17 surfaces.py | varieties/ subpackage (6-8 files) | FAIL→PASS |
| P1 — HIGH | #17 app.py | DEFERRED per brief | stays FAIL |
| P2 — HIGH | #24 | `_qt/` adoption + icons/helpers/styles move | FAIL→PASS |
| P3 — MEDIUM | #11 | render/ + cross_section/ subpackages | reinforces |
| P4 — LOW | #10 | shim removal (future milestone) | FAIL→PASS later |

---

## 10. Sources — consolidated citation list (all accessed 2026-05-23)

### Tier 1 — Python packaging guidance

- [Hitchhiker's Guide to Python — project structure](https://docs.python-guide.org/writing/structure/)
- [pyOpenSci Python Packaging Guide](https://www.pyopensci.org/python-package-guide/package-structure-code/python-package-structure.html)
- [PyPA src vs flat layout discussion](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/)
- [PyPA — writing pyproject.toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)
- [Scientific Python Development Guide](https://learn.scientific-python.org/development/)
- [Scientific Python SPECs](https://scientific-python.org/specs/)
- [Cookiecutter Data Science v2](https://cookiecutter-data-science.drivendata.org/)
- [Ionel — packaging a Python library (src argument)](https://blog.ionelmc.ro/2014/05/25/python-packaging/)
- [Real Python — project layout best practices 2025](https://realpython.com/ref/best-practices/project-layout/)

### Tier 2 — Reference repositories (all confirmed live 2026-05-23)

- [napari](https://github.com/napari/napari) — src layout; no AGENTS.md (404)
- [napari architecture / dir_organization](https://napari.org/dev/developers/architecture/dir_organization.html) — `_qt/` isolation explicitly documented
- [PyVista](https://github.com/pyvista/pyvista) — flat layout; no AGENTS.md (404)
- [Spyder](https://github.com/spyder-ide/spyder) — `app/` subpackage; no AGENTS.md (404)
- [pandas](https://github.com/pandas-dev/pandas) — ships AGENTS.md (confirmed live)
- [SciPy](https://github.com/scipy/scipy) — `_lib/` for kernels; ships tach.toml
- [Django](https://github.com/django/django) — feature-clean subpackages
- [Kubernetes](https://github.com/kubernetes/kubernetes) — ships AGENTS.md

### Tier 3 — Modular architecture & AI-navigability

- [Kraken Technologies — large Python monolith (EuroPython 2024)](https://blog.europython.eu/kraken-technologies-how-we-organize-our-very-large-pythonmonolith/)
- [Sahibinden Tech — package-by-layer vs feature (2024)](https://medium.com/sahibinden-technology/package-by-layer-vs-package-by-feature-7e89cde2ae3a)
- [agents.md spec (Linux Foundation / Agentic AI Foundation)](https://agents.md/)
- [HumanLayer — writing a good CLAUDE.md](https://www.humanlayer.dev/blog/writing-a-good-claude-md)
- [Anthropic Claude Code best practices](https://code.claude.com/docs/en/best-practices)
- [Augment Code — how to build AGENTS.md (2026)](https://www.augmentcode.com/guides/how-to-build-agents-md)
- [Datadog Frontend — Steering AI agents in monorepos](https://dev.to/datadog-frontend-dev/steering-ai-agents-in-monorepos-with-agentsmd-13g0)
- [Wasowski — Modular Monolith vs Microservices when AI reads code (2026)](https://medium.com/@wasowski.jarek/modular-monolith-instead-of-microservices-what-changed-when-the-ai-agent-started-reading-code-c586d9f63fd7)
- [ETH Zurich — Evaluating AGENTS.md effectiveness (2602.11988v1)](https://arxiv.org/html/2602.11988v1) — **NEW-2026: context files increase costs 19-23% for ~4% benefit**

### Tier 4 — Anti-patterns & heuristics

- [Matti Lehtinen — Dunghill anti-pattern](https://mattilehtinen.com/articles/dunghill-anti-pattern-why-utility-classes-and-modules-smell/)
- [Software Carpentry — structuring Python](https://intermediate-and-advanced-software-carpentry.readthedocs.io/en/latest/structuring-python.html)
- [The Little Book of Python Anti-Patterns (quantifiedcode)](https://docs.quantifiedcode.com/python-anti-patterns/)
- [Keep a Changelog](https://keepachangelog.com/)

### Could not fetch / unverified

- `https://learn.scientific-python.org/development/guides/repo/` — 404. [UNVERIFIED]
- `https://scientific-python.github.io/repo-review/` — loads blank; individual check IDs unverified. [UNVERIFIED]
- Numba documentation on `THREADING_LAYER` — behavior confirmed in AVC test suite; exact URL for Numba config docs [UNVERIFIED as to current URL].
- `https://nitingavhane.medium.com/ai-coding-agents-are-hitting-a-wall-and-the-wall-is-your-architecture-a57ec11d20ce` — cited in seed brief; not re-fetched in r2 (r1 confirmed live). [UNVERIFIED for r2].

---

## Appendix A — Napari `_qt/` pattern verbatim

From <https://napari.org/dev/developers/architecture/dir_organization.html> (accessed 2026-05-23):

> *"we try to confine code that directly imports Qt... to the folders `_qt/` and `_vispy/`"*
>
> The `_qt/` folder structure mirrors `napari/`'s structure, with 'q' being added to the start
> of folders and files (e.g., `_app_model` is named `_qapp_model` inside `_qt/`).

This is the strongest available citation for the `_qt/` isolation principle in a Qt+VTK
desktop Python application. AVC's `_qt/` proposal directly follows this pattern.

---

## Appendix B — ETH Zurich AGENTS.md study key findings (2026)

From arxiv.org/html/2602.11988v1 (accessed 2026-05-23):

- LLM-generated context files: -2% to -3% task success rate, +23% inference cost.
- Human-curated context files: +4% task success rate, +19% inference cost.
- Recommendation: "only minimal requirements" — what agents cannot discover independently.
- The paradox: agents follow instructions faithfully, but "broader exploration and extra testing
  actually reduce performance."

**AVC implication:** AVC's 148-line human-curated AGENTS.md/CLAUDE.md pair is correctly sized.
Do not expand during r2 except to update the directory map for new subpackages. Do not add
large per-subpackage CLAUDE.md files.

---

## Appendix C — r2 target tree shape (reference for designer)

This is the r2 brief's specified target, reproduced here for reference. This appendix does NOT
constitute a proposed AVC layout (that is the designer's job).

```
(repository root)
├── AGENTS.md
├── CHANGELOG.md
├── CLAUDE.md
├── CONTEXT.md
├── LICENSE
├── MOVES.md
├── README.md
├── app.py              ← entry point; stays at root per r2 brief
├── appearance_panel.py ← r1 shim (KEEP until shim-removal milestone)
├── parameter_grid.py   ← stays at root or → varieties/parameter_grid.py (designer's call)
├── parameter_grid_panel.py ← r1 shim
├── parameters_panel.py ← r1 shim
├── pyproject.toml
├── pytest.ini          ← absorb into pyproject.toml [tool.pytest.ini_options] later
├── render_worker.py    ← new r2 shim → render/worker.py
├── requirements.txt
├── surfaces.py         ← new r2 shim → varieties/
├── view_panel.py       ← r1 shim
│
├── _qt/                ← r2 proposes; may also stay as panels/ (designer's call)
│   ├── __init__.py
│   ├── icons.py        ← was icons.py at root
│   ├── helpers.py      ← was ui_helpers.py at root
│   ├── styles.py       ← was styles.py at root
│   └── panels/         ← was panels/ at root
│       ├── __init__.py
│       ├── appearance.py
│       ├── parameter_grid_panel.py
│       ├── parameters.py
│       └── view.py
│
├── cross_section/      ← r2 proposes; scope TBD by designer
│   ├── __init__.py
│   └── clip.py
│
├── render/             ← r2 proposes
│   ├── __init__.py
│   └── worker.py       ← was render_worker.py
│
├── varieties/          ← r2 PRIMARY TARGET; was surfaces.py
│   ├── __init__.py
│   ├── _kernels.py     ← 11 @njit functions + numba.config side-effect
│   ├── _marching.py    ← _marching_cubes_to_polydata + _grid_to_polydata
│   ├── calabi_yau.py
│   ├── enriques.py
│   ├── fano.py
│   ├── k3.py
│   └── registry.py     ← VARIETIES dict + tooltips
│
├── panels/             ← EXISTING (r1); stays if _qt/ not adopted
│   ├── __init__.py
│   ├── appearance.py
│   ├── parameter_grid_panel.py
│   ├── parameters.py
│   └── view.py
│
└── tests/              ← UNCHANGED
    ├── test_numba_field_kernels.py  ← uses "from surfaces import _*_field_kernel" (shim)
    ├── test_panels_shims.py         ← exercises r1 shims; needs r2 shim testing too
    └── ...
```

**Key designer decision points flagged by this brief:**
1. Does `panels/` become `_qt/panels/` or stay as `panels/`?
2. Does `parameter_grid.py` move to `varieties/parameter_grid.py`?
3. Does `styles.py` move to `_qt/styles.py` (logical coupling) or stay at root (no Qt imports)?
4. Does `cross_section/` land in r2 or a later milestone?
5. Does the `_qt/` container include `icons.py` + `ui_helpers.py` + `styles.py` in r2, or is
   that Batch N+1?
