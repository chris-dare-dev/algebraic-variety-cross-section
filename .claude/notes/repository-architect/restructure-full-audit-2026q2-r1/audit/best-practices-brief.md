# Best-Practices Scout Brief
## Restructure ID: restructure-full-audit-2026q2-r1
## Generated: 2026-05-23
## Agent: Best-Practices Scout (Phase 1)

**Scope.** Raw material for the Phase 2 designer. This brief covers 2024-2026 industry best
practices for Python desktop / scientific-viz repository structure, with focus on AVC's
stack (PySide6 + PyVista + VTK). No new AVC layout is proposed here.

**Honesty conventions:**
- `[CONSENSUS]` — multiple independent reputable sources agree.
- `[CONTESTED]` — credible sources disagree.
- `[OPINION]` — single author's well-reasoned position; treat as input not verdict.
- `[UNVERIFIED]` — could not fetch primary source; included only when widely cross-referenced.

All URLs verified live on 2026-05-23 unless marked `[UNVERIFIED]`.

---

## 1. TL;DR — 5 bullets on 2024-2026 state of the art

1. **The src-layout vs flat-layout war is essentially settled for libraries (src wins), but
   genuinely unsettled for desktop apps.** PyPA, pyOpenSci, ionelmc, and the Scientific Python
   Development Guide all push `src/<pkg>/` for code intended for PyPI. uv defaulted to flat in
   Aug 2024; Poetry flipped to src as default in Feb 2025. Real Python (2025) now recommends src
   for desktop apps too when `pyproject.toml` packaging is desired. The pragmatic answer for AVC:
   **moving from 11 loose files at root to an `avcs/` flat package is the highest-ROI change**;
   migrating further to `src/avcs/` is defensible but adds onboarding friction.
   [CONTESTED for apps; CONSENSUS for libraries]
   ([packaging.python.org](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/),
   [pyOpenSci](https://www.pyopensci.org/python-package-guide/package-structure-code/python-package-structure.html),
   [Real Python 2025](https://realpython.com/ref/best-practices/project-layout/))

2. **AGENTS.md is the cross-tool standard for AI-agent repo orientation (Linux Foundation,
   60k+ repos, 20+ tools including OpenAI Codex, Google Jules, GitHub Copilot, Cursor, Devin,
   and Aider).** Claude Code reads CLAUDE.md hierarchically (nearest wins); both can coexist.
   Neither napari, PyVista, nor Spyder ships either file as of 2026-05-23, meaning AVC could be
   ahead of its reference peers by adding one.
   [CONSENSUS as emerging standard]
   ([agents.md](https://agents.md/), [HumanLayer](https://www.humanlayer.dev/blog/writing-a-good-claude-md))

3. **Package-by-feature beats package-by-layer for AI-agent-navigable codebases.** The most
   common AI-agent failure mode is a layer-packaged codebase: the agent edits code across
   `controllers/`, `services/`, `models/` simultaneously and introduces blast-radius bugs.
   AVC's natural features — varieties, cross-section math, rendering, parameter UI, export —
   map cleanly to feature subpackages.
   [CONSENSUS for modular monoliths; CONTESTED whether applicable to single-file apps that aren't
   yet packages at all]
   ([Kraken EuroPython 2024](https://blog.europython.eu/kraken-technologies-how-we-organize-our-very-large-pythonmonolith/),
   [Sahibinden Tech 2024](https://medium.com/sahibinden-technology/package-by-layer-vs-package-by-feature-7e89cde2ae3a))

4. **For Qt+VTK+PyVista desktop apps, napari is the canonical reference layout.** It uses
   src-layout, role-prefixed private subpackages (`_qt/`, `_vispy/`), a public `components/`
   + `layers/` + `plugins/` feature split, and `window.py` / `viewer.py` as top-level entry
   points (splitting the 1900-LOC `app.py` problem). Spyder uses an `app/` subpackage for the
   launcher — also directly applicable to AVC.
   [CONSENSUS within this project family]
   ([napari src tree](https://github.com/napari/napari),
   [spyder repo](https://github.com/spyder-ide/spyder))

5. **The under-cited but operationally critical rules for AVC specifically:** (a) 800 LOC is
   the informal red line per file — AVC's `app.py` at 1900 LOC and `surfaces.py` at 1811 LOC are
   both 2× over; (b) dual implementations are a navigation hazard: `parameters_panel.py` (368 LOC,
   1 class) and `parameter_grid_panel.py` (713 LOC, 2 classes) are imported by the same
   `parameters_panel.py` — one is the container, one is the content; their relationship should be
   explicit in the file names; (c) `pyproject.toml` is missing and is now PyPA-canonical in 2026.
   [CONSENSUS on LOC as signal; CONTESTED on exact thresholds]
   ([HumanLayer CLAUDE.md guide](https://www.humanlayer.dev/blog/writing-a-good-claude-md),
   [Matti Lehtinen "Dunghill"](https://mattilehtinen.com/articles/dunghill-anti-pattern-why-utility-classes-and-modules-smell/))

**What's contested (flagged for the designer):**
- src vs flat for *applications* (not libraries) — no authoritative source resolves this.
- Whether tests should live in `src/<pkg>/tests/` or as a sibling to `src/`.
- File-size hard limits — no formal standard; 800 LOC is informal practice.
- Whether per-subpackage CLAUDE.md is worth the maintenance cost vs a single root CLAUDE.md.

---

## 2. Canonical layouts (Tier 1 sources)

### 2.1 The Hitchhiker's Guide to Python — flat layout (anti-src)

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
    conf.py
    index.rst
tests/
    test_basic.py
    test_advanced.py
```

Key quote: *"Your library does not belong in an ambiguous src or python subdirectory."*
Explicitly rejects src/. This is the **dissenting** but historically influential position.
Still widely cited but increasingly a minority view. [OPINION — single source lineage.]

### 2.2 pyOpenSci Python Packaging Guide — src layout for scientific Python

Source: <https://www.pyopensci.org/python-package-guide/package-structure-code/python-package-structure.html>
(accessed 2026-05-23)

```
myPackageRepoName/
├── CHANGELOG.md
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── docs/
│   └── index.md
├── LICENSE
├── README.md
├── pyproject.toml
├── src/
│   └── myPackage/
│       ├── __init__.py
│       ├── moduleA.py
│       └── moduleB.py
└── tests/
    └── ...
```

Key quote: *"We strongly suggest, but do not require, that you use the src/ layout."* Reasoning:
*"tests are run against the installed version of your package rather than the files in your
package working directory."* Lists CHANGELOG, CODE_OF_CONDUCT, CONTRIBUTING, LICENSE, README,
pyproject.toml as **required** top-level files for scientific Python packages. [CONSENSUS within
scientific Python community.]

### 2.3 PyPA (Python Packaging Authority) — src-leaning neutral

Source: <https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/>
(accessed 2026-05-23 — confirmed live)

Three stated advantages of src layout:
1. *"requires installation of the project to be able to run its code"* (forces correctness)
2. *"helps prevent accidental usage of the in-development copy of the code"* (import isolation)
3. *"helps enforce that an editable installation is only able to import files that were meant
   to be importable"* (prevents setup.py/conftest.py from becoming importable)

Does not formally declare a winner; presents trade-offs. [CONSENSUS that PyPA leans src.]

### 2.4 Scientific Python Development Guide / SPECs

Sources: <https://learn.scientific-python.org/development/>, <https://scientific-python.org/specs/>
(accessed 2026-05-23)

Most relevant SPEC for AVC:

| SPEC | Title                                     | Status   | AVC Relevance |
|------|-------------------------------------------|----------|---------------|
| 0    | Minimum Supported Dependencies            | Endorsed | MEDIUM        |
| 1    | Lazy Loading of Submodules and Functions  | Endorsed | HIGH — VTK import cost |
| 4    | Using and Creating Nightly Wheels         | Endorsed | LOW           |
| 7    | Seeding Pseudo-Random Number Generation   | Endorsed | LOW           |

**SPEC 1 (lazy loading) is the key architectural pattern** for keeping import-time costs bounded
in a Qt app that imports VTK/PyVista at startup. Don't `import pyvista` at module top-level in
modules that might be imported during tests of unrelated subsystems. [CONSENSUS within scientific
Python.]

### 2.5 Cookiecutter Data Science v2 — flat layout for data projects

Source: <https://cookiecutter-data-science.drivendata.org/> (accessed 2026-05-23)

```
├── LICENSE
├── Makefile
├── README.md
├── data/
│   ├── external/
│   ├── interim/
│   ├── processed/
│   └── raw/
├── docs/
├── models/
├── notebooks/
├── pyproject.toml
├── references/
├── reports/
│   └── figures/
├── requirements.txt
└── {{ module_name }}/
    ├── __init__.py
    └── config.py
```

Flat layout (no `src/`). Philosophy: *"A logical, flexible, and reasonably standardized project
structure for doing and sharing data science work."* The `references/` (papers, manuals) and
`notebooks/` (exploratory analysis) directories are a good cross-pollination target for a
research-facing app like AVC. The data quadrant is not applicable. [OPINION for AVC; CONSENSUS
for ML/data workflows.]

### 2.6 Ionelmc's src argument — the foundational case

Source: <https://blog.ionelmc.ro/2014/05/25/python-packaging/> (still canonical, accessed
2026-05-23)

Key claim: *"The current directory is implicitly included in sys.path; but not so when installing
and importing from site-packages. Users will never have the same current working directory as you
do."* Forces dev to test the installed copy. Also: without src, `setup.py` and config files
*"will unwittingly become importable"*. [CONSENSUS — most-cited single-author piece on this
debate; still holds in 2026.]

---

## 3. Reference orgs analyzed

| Org | URL | Top-level shape | Exemplary | Outdated / quirky |
|-----|-----|-----------------|-----------|-------------------|
| **napari** (Qt+VTK, AVC analog) | <https://github.com/napari/napari> | `src/napari/{_qt,_vispy,_vendor,_app_model,components,layers,plugins,settings,utils,resources,...}` + `examples/`, `resources/`, `tools/` | Role-prefixed private subpackages (`_qt`, `_vispy`) separate framework from domain. `window.py`, `viewer.py`, `view_layers.py` as top-level entry points. Has `experimental/` for in-flux code. src layout. | No AGENTS.md or CLAUDE.md (404 confirmed). Has `_tests/` inside the package — inside-package choice. 24 root-level files. |
| **PyVista** (AVC's render dep) | <https://github.com/pyvista/pyvista> | `pyvista/{core,plotting,utilities,jupyter,trame,demos,examples,typing,_cli,_vtk.py,...}` + `doc/`, `tests/`, `examples/` | Flat layout but disciplined: `core/` (data model), `plotting/` (render), `utilities/` (shared). Ships `context7.json` (Context7 LLM manifest — emerging pattern). | No AGENTS.md (404 confirmed). Still has `setup.py` alongside `pyproject.toml` (legacy overlap). 33 root-level files — heavy. |
| **Spyder** (Qt IDE) | <https://github.com/spyder-ide/spyder> | `spyder/{api,app,config,plugins,utils,widgets,windows,tests}` + many root files | Clear separation: `api/` (public extension surface), `plugins/` (impls), `widgets/` (reusable Qt), `app/` (launcher entry). `app/` subpackage is directly applicable to AVC's `app.py` split. | No AGENTS.md (404 confirmed). 40+ root-level files including `bootstrap.py`, `runtests.py` — high noise. Tests inside package. |
| **pandas** | <https://github.com/pandas-dev/pandas> | flat: `pandas/{api,arrays,core,errors,io,plotting,tseries,...}` + **AGENTS.md** at root | **Ships AGENTS.md at root — the clearest available template.** Structured as: Project Overview, Persona/Tone, Project Guidelines, Decision Heuristics, Type Hints Guidance, Docstring Guidance, Pull Requests. Links to contributing docs by local path reference. | Tests inside package — diverges from pyOpenSci recommendation. Build complexity is cargo-cult risk for smaller apps. |
| **SciPy** | <https://github.com/scipy/scipy> | flat: `scipy/{cluster,constants,datasets,fft,integrate,...,_lib}` + `benchmarks/`, `doc/`, `tools/` | Subpackage discipline by mathematical domain. Ships `tach.toml` (module-boundary linter) and `meson.build`. `_lib/` for cross-subpackage shared internals. | Build complexity (meson, pixi, mypy.ini, pyrefly.toml) is project-size-appropriate but a cargo-cult risk for small apps. |
| **Django** | <https://github.com/django/django> | flat: `django/{apps,conf,contrib,core,db,dispatch,forms,http,...,utils,views}` + `docs/`, `tests/` at root | Feature-clean subpackages — package-by-feature. `tests/` sibling to `django/` (pyOpenSci shape). `contrib/` as official-but-optional namespace. The `utils/` *subpackage* with subdirs is a good pattern (not a grab-bag file). | `utils/` is only justifiable because it has internal subpackages — a single `utils.py` file at this size would be the Dunghill anti-pattern. |
| **Kubernetes** (Go, cross-language) | <https://github.com/kubernetes/kubernetes> | `cmd/`, `pkg/`, `staging/`, `hack/`, `api/`, `build/` + **AGENTS.md** | **Ships AGENTS.md.** `cmd/` = entry points (one binary per subdir) maps to Python's `__main__.py` or `scripts/` entry points. `hack/` = dev scripts maps to `scripts/` or `tools/`. | `vendor/` is Go-specific — do not copy to Python projects. |
| **ParaView** (scientific viz desktop) | <https://github.com/Kitware/ParaView> | `Qt/`, `Plugins/`, `Clients/`, `Remoting/`, `VTKExtensions/`, `Web/`, `Wrapping/`, `Documentation/`, `Examples/`, `Testing/`, `Incubator/` | **Mirrors AVC's domain at scale.** `Qt/` (GUI), `Plugins/` (extensions), `VTKExtensions/` (VTK additions), `Incubator/` (experimental/in-flux). The `Incubator/` namespace is excellent for "not yet promoted" code. | C++/CMake-heavy; capitalized directory names break Python import convention. The *partitioning* transfers; the *names* and *casing* don't. |

[CONSENSUS] across all 8 orgs: domain-or-role-based subpackage split, README at root, LICENSE at
root, separate tests/ (or inside-package only if there's a stated reason).

---

## 4. Patterns to adopt (with AVC applicability ratings)

Rating: HIGH = clear win for AVC now; MEDIUM = worth doing after initial restructure;
LOW = premature for AVC's current size.

### P1. Named flat package (`avcs/` at root) — HIGH

Move all 11 loose `.py` files under a named package directory `avcs/` with an `__init__.py`.
This is the minimum necessary step to pass checklist item 11 and is prerequisite to any further
subpackage work. Cheaper than `src/avcs/` migration; eliminates the "no package" state.
([PyPA](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/),
[pyOpenSci](https://www.pyopensci.org/python-package-guide/package-structure-code/python-package-structure.html))

**AVC note:** Given AVC is a desktop app (not a library), the flat-package form (`avcs/` at root)
is the pragmatic first step. The `src/avcs/` migration can follow if/when CI packaging becomes
important. The brief's restructure bias ("conservative, low-risk-first") supports flat-package
first.

### P2. AGENTS.md at root — HIGH

Single agent-readable file covering: Project overview, Build & test commands, Code style
guidelines, Testing instructions, Architecture orientation. Universal across Codex, Cursor, Jules,
Copilot, Devin, Aider, JetBrains Junie (20+ tools confirmed, 60k+ adopting repos).
Symlink `CLAUDE.md -> AGENTS.md` or have CLAUDE.md `@import AGENTS.md`.
([agents.md](https://agents.md/), [pandas AGENTS.md](https://github.com/pandas-dev/pandas/blob/main/AGENTS.md),
[Kubernetes AGENTS.md](https://github.com/kubernetes/kubernetes/blob/master/AGENTS.md))

**AVC note:** Pandas's structure (Project Overview, Persona/Tone, Project Guidelines, Decision
Heuristics, Type Hints Guidance, Docstring Guidance, Pull Requests) is a workable template.
Link to CONTEXT.md and app-invariants.md via local path references rather than duplicating them.

### P3. CLAUDE.md under 200 lines (Anthropic's current recommendation) — HIGH

Keep CLAUDE.md spare: Project context (one line), Code style preferences, Commands (exact
strings), Architecture decisions (where things live). Use `@import` for detailed guidance rather
than inlining. *"Frontier LLMs can reliably follow 150-200 instructions; Claude Code's system
prompt already contains ~50"* — your CLAUDE.md budget is ~100-150 instructions.
([HumanLayer](https://www.humanlayer.dev/blog/writing-a-good-claude-md),
[Anthropic Claude Code best practices](https://code.claude.com/docs/en/best-practices))

**AVC note:** AVC's CONTEXT.md is the right *reference* document. CLAUDE.md should be a short
index that points at it, not a copy of it. Anthropic now recommends under 200 lines (updated from
the HumanLayer 300-line figure).

### P4. `panels/` subpackage for the four panel files — HIGH

Move `appearance_panel.py`, `view_panel.py`, `parameters_panel.py`, `parameter_grid_panel.py`
into `avcs/panels/` (or `avcs/ui/`). This is the "four panel files at root that could group"
item from the brief and directly addresses the napari `_qt/` pattern. Low-risk because it's a
mechanical move + import-path update with no semantic change.
([napari src/napari/_qt/](https://github.com/napari/napari),
[spyder spyder/widgets/](https://github.com/spyder-ide/spyder))

**AVC note:** Use `avcs/ui/` (public) or `avcs/_qt/` (private) depending on whether panel APIs
are meant to be stable. Given AVC is single-developer, `avcs/ui/` is cleaner. The four panel
files are 738, 713, 503, 368 LOC respectively — large but not individually oversized once
`app.py` is split.

### P5. `pyproject.toml` at root — HIGH

PyPA canonical in 2026. Required by pyOpenSci peer review. Required for `pip install -e .`
without `setup.py`. Replaces requirements.txt as the source of truth for dependencies.
([PyPA writing pyproject.toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/))

**AVC note:** AVC currently has only `requirements.txt`. A minimal `pyproject.toml` with
`[project]` table, `[project.scripts]` entry point (`avcs-viewer = "avcs.app:main"`), and
`[tool.pytest.ini_options]` (absorbing `pytest.ini`) is a low-risk first step.

### P6. `CHANGELOG.md` at root (Keep-a-Changelog format) — HIGH

Required by pyOpenSci review. Supplements git log with a human/agent-readable history.
CONTEXT.md carries some of this history but in a technical decision log format, not a
user-visible changelog.
([pyOpenSci](https://www.pyopensci.org/python-package-guide/package-structure-code/python-package-structure.html),
[keepachangelog.com](https://keepachangelog.com/))

**AVC note:** Low-risk addition. Can be bootstrapped from git log + CONTEXT.md milestones.

### P7. `LICENSE` at root — HIGH

Currently missing (checklist item 2 FAIL). Required for any open-source project; required by
pyOpenSci. MIT is the natural choice for a research tool.
([pyOpenSci], [CONSENSUS across all reference orgs])

**AVC note:** Zero-risk. Cheapest possible checklist fix.

### P8. Package-by-feature within `avcs/` — MEDIUM (after P4)

Once the flat package exists, organize subpackages by feature/domain rather than architectural
layer: `avcs/varieties/` (mesh generators from surfaces.py), `avcs/render/` (render_worker.py +
any VTK helpers), `avcs/ui/` (panel files). Each subpackage owns its own imports.
([Kraken EuroPython 2024](https://blog.europython.eu/kraken-technologies-how-we-organize-our-very-large-pythonmonolith/),
[Sahibinden Tech 2024](https://medium.com/sahibinden-technology/package-by-layer-vs-package-by-feature-7e89cde2ae3a))

**AVC note:** The import graph (from cache) already points in this direction: `surfaces.py` has no
UI imports; `render_worker.py` imports `surfaces` + `pyvista` but no panel files; the panel files
import `surfaces` and `styles`. The dependency direction is already right — the subpackage split
would make it explicit.

### P9. Resolve the dual parameter_panel implementations — HIGH

`parameters_panel.py` (368 LOC, 1 class `ParametersPanel`) imports and wraps
`parameter_grid_panel.py` (713 LOC, 2 classes `_DraggableDot`, `ParameterGridPanel`). The naming
is a navigation hazard: a human or agent looking for "the parameter panel" has to guess which file
is authoritative. Options: (a) rename to `parameter_container.py` + `parameter_grid.py`, or
(b) merge into one `parameters.py`, or (c) leave as-is but add a CLAUDE.md note explaining the
relationship.
([Lehtinen "Dunghill"](https://mattilehtinen.com/articles/dunghill-anti-pattern-why-utility-classes-and-modules-smell/))

**AVC note:** The brief specifically flags this as "dead code consolidation if
parameter_grid_panel.py supersedes parameters_panel.py." The import graph shows
`parameters_panel.py` imports `parameter_grid_panel` — so `parameter_grid_panel.py` is the
implementation, `parameters_panel.py` is the container. They're not duplicates; they're coupled.
The fix is naming clarity, not deletion.

### P10. `app.py` Extract-Class for `MainWindow` — MEDIUM (gated behind low-risk batches)

`app.py` at 1900 LOC with a single `MainWindow(QMainWindow)` class is the primary monolith
hotspot. Napari's split: `window.py` (main window assembly), `viewer.py` (viewer-specific logic),
`view_layers.py` (layer wiring). Spyder's split: `app/` subpackage with `launcher.py`,
`mainwindow.py`, `restart.py`. The direct AVC analog: `avcs/app/main_window.py` (Qt window
assembly, signal wiring), `avcs/app/render_pipeline.py` (the `_render_current` + mesh lifecycle),
`avcs/app/__main__.py` (entry point).
([napari window.py](https://github.com/napari/napari), [spyder app/](https://github.com/spyder-ide/spyder))

**AVC note:** This is the HIGH-risk Extract-Class operation the brief specifically says to gate
behind successful low-risk batches. The AI-9 re-entrancy guard around `processEvents()` and the
complex render pipeline (§4.3 of CONTEXT.md) mean any split must preserve signal wiring integrity.

### P11. `surfaces.py` Extract-Module for variety generators — MEDIUM (gated)

`surfaces.py` at 1811 LOC contains: 2 dataclasses, 2 utility predicates, 2 private pipeline
helpers (`_marching_cubes_to_polydata`, `_grid_to_polydata`), 11 Numba JIT field kernels, and
14 generator functions. The natural split: `avcs/varieties/k3.py`, `avcs/varieties/enriques.py`,
`avcs/varieties/calabi_yau.py`, `avcs/varieties/fano.py`, with a thin `avcs/varieties/__init__.py`
re-exporting `VARIETIES`, `VARIETY_TOOLTIPS`, `SUBTYPE_TOOLTIPS`, `Surface`, `ParamSpec`.
([napari layers/](https://github.com/napari/napari))

**AVC note:** HIGH-risk because the Numba JIT kernels have process-global side effects
(`numba.config.THREADING_LAYER = "workqueue"` set at import time in surfaces.py — AI invariant).
Any split must keep this side-effect-at-import in a single location that runs before any kernel
is called. Also: 45 tests in `test_numba_field_kernels.py` pin numerical equivalence at
`rtol=atol=1e-9` — a regression target for any generator move.

### P12. `.gitignore` — add `.pytest_cache/` — HIGH (trivial)

Current `.gitignore` covers `__pycache__/`, `*.pyc`, `.DS_Store`, `.idea/`, `.vscode/` but is
missing `.pytest_cache/` (checklist item 25 FAIL). Zero-risk, one-line fix.

### P13. SPEC 1 lazy loading for heavy imports — MEDIUM

For scientific Python packages with heavy deps (VTK is the heaviest), expose subpackages via
lazy import to bound import time and cold-start cost. Don't `import pyvista` at module top-level
in modules that might be imported during tests of unrelated subsystems.
([scientific-python.org SPEC 1](https://scientific-python.org/specs/))

**AVC note:** The test suite already avoids Qt imports (AI-2 invariant). Once surfaces.py is
split, guard any VTK import behind a lazy load in `avcs/__init__.py` so pure-math tests don't
trigger VTK initialization.

### P14. `context7.json` for LLM context manifest — LOW

PyVista ships a `context7.json` that registers the project with the Context7 MCP server
(context7.com), telling LLMs which documentation folders to index and which to exclude. An
emerging but not yet standardized pattern. [UNVERIFIED as a broadly adopted standard beyond
Context7's own ecosystem.]
([PyVista context7.json](https://github.com/pyvista/pyvista/blob/main/context7.json),
[Context7](https://context7.com/))

**AVC note:** LOW priority. AGENTS.md + CLAUDE.md provide more value per-effort for AVC's
single-developer workflow.

### P15. `examples/` directory with runnable demos — MEDIUM

PyVista, napari, scipy all have `examples/` at root. Doubles as documentation and
regression-discovery. AVC already generates screenshots for CONTEXT.md updates — a few of those
become `examples/` scripts naturally.
([PyVista examples/](https://github.com/pyvista/pyvista/tree/main/examples),
[napari examples/](https://github.com/napari/napari/tree/main/examples))

**AVC note:** Useful after the package split. Before that, running `python app.py` is the
example.

---

## 5. Patterns to AVOID (with how-to-spot)

### A1. Loose .py files at root (the "no-package" layout) [CONSENSUS]

11 `.py` files at root is the AVC's primary structural problem. It prevents packaging, makes
`pip install -e .` impossible, and means imports work only when the CWD is the repo root.
**How to spot:** `ls *.py` at root returns >0 results where any of those files are meant to be
the importable library.
([PyPA](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/),
[ionelmc](https://blog.ionelmc.ro/2014/05/25/python-packaging/))

### A2. Grab-bag `utils.py` — the "Dunghill" anti-pattern [CONSENSUS]

Large, generic utility files are a bad practice: *"By dumping unrelated functions into a single
file, you're essentially creating a tangled web that hinders proper code organization."* AVC's
`ui_helpers.py` (264 LOC) is currently below the 200-LOC warning threshold but should be watched.
**How to spot:** any file named `utils.py`, `helpers.py`, `common.py`, `misc.py` over ~200 LOC,
or containing functions that operate on more than 2 unrelated domain types.
([Matti Lehtinen](https://mattilehtinen.com/articles/dunghill-anti-pattern-why-utility-classes-and-modules-smell/),
[Hitchhiker's Guide](https://docs.python-guide.org/writing/structure/))

### A3. Package-by-layer in monoliths [CONSENSUS for modular monoliths]

Top-level subpackages named after architectural roles (`controllers/`, `services/`, `repositories/`)
instead of domain concepts. AI-agent failure mode: agent edits cascade across layers with
unexpected blast radius.
**How to spot:** subpackage names are architectural roles, not business/domain names.
([Sahibinden Tech 2024](https://medium.com/sahibinden-technology/package-by-layer-vs-package-by-feature-7e89cde2ae3a),
[Kraken EuroPython 2024](https://blog.europython.eu/kraken-technologies-how-we-organize-our-very-large-pythonmonolith/))

### A4. Monolith files over 800 LOC [CONTESTED threshold, CONSENSUS on the problem]

AVC's `app.py` (1900 LOC) and `surfaces.py` (1811 LOC) are both 2× over the informal 800-LOC
red line. The test file `tests/test_styles_palette.py` (1261 LOC) is also over. Files this large
exceed a single agent context window pass for comfortable comprehension.
**How to spot:** `wc -l *.py | sort -n` — any file >800 LOC is a yellow flag, >1500 is red.
([Informal 2025-2026 AI-coding literature convergence, no formal source])

### A5. Missing `pyproject.toml` [CONSENSUS in 2026]

`setup.py` + `requirements.txt` without `pyproject.toml` is now legacy. PyPA canonical since
PEP 517/518/621. pyOpenSci requires it for peer review.
**How to spot:** no `pyproject.toml` at root; presence of `setup.py` as the primary build script.

### A6. Missing `LICENSE` [CONSENSUS]

Without a LICENSE file, code is legally "all rights reserved" by default, even if published on
GitHub. Required by pyOpenSci. Required for any fork, contribution, or commercial use.
**How to spot:** `ls LICENSE*` returns nothing.

### A7. Stuffing CLAUDE.md with everything [OPINION — strongly held]

*"frontier LLMs can reliably follow 150-200 instructions. Since Claude Code's system prompt
already contains ~50 instructions, your CLAUDE.md should be spare"*.
**How to spot:** CLAUDE.md > 200 lines (Anthropic's current recommendation), or contains lint
rules a linter could enforce, or duplicates information already in referenced documents.
([HumanLayer](https://www.humanlayer.dev/blog/writing-a-good-claude-md),
[Anthropic Claude Code best practices](https://code.claude.com/docs/en/best-practices))

### A8. Wildcard imports (`from foo import *`) [CONSENSUS]

*"makes the code harder to read and makes dependencies less compartmentalized"*.
Kills static analysis and AI agent comprehension.
**How to spot:** `grep -r "import \*" .`
([Hitchhiker's Guide](https://docs.python-guide.org/writing/structure/),
[quantifiedcode anti-patterns](https://docs.quantifiedcode.com/python-anti-patterns/))
**AVC status:** PASS — no wildcard imports found in the current tree (checklist item 16).

### A9. Top-level file sprawl [OPINION — modern trend]

PyVista's 33 and Spyder's 40+ root files are intimidating to humans and agents alike. Target:
under 20 files at root.
**How to spot:** `ls | wc -l` > 20 at repo root.
AVC currently has 15 root files (PASS), but adding AGENTS.md, CLAUDE.md, LICENSE, CHANGELOG.md,
pyproject.toml would bring it to 20 — still within range.

### A10. Three-or-more-deep package nesting [OPINION but widely shared]

Software Carpentry's two-deep heuristic: hierarchies of packages more than two deep are annoying
to develop on.
**How to spot:** any file path with 4+ path separators after the package root
(e.g. `avcs/varieties/k3/surfaces/fermat.py` — three levels deep).
([Software Carpentry](https://intermediate-and-advanced-software-carpentry.readthedocs.io/en/latest/structuring-python.html))

### A11. Framework-adapter code interleaved with domain logic [CONSENSUS in reference Qt apps]

Napari's `_qt/` + `_vispy/` pattern specifically exists to prevent this: pure-Python domain logic
(components, layers) shouldn't have PyQt or VTK imports; only the adapter subpackages should.
**How to spot:** domain model files that directly import `PySide6` or `pyvista`.
Currently: `surfaces.py` imports `pyvista` (domain model file with render dep) — a soft violation.
([napari architecture](https://github.com/napari/napari))

### A12. Capitalized directory names for Python projects [CONSENSUS for Python]

ParaView's `Qt/`, `Plugins/`, `Clients/` work for CMake-driven C++ but break Python import
idiom and confuse case-sensitive vs case-insensitive filesystems.
**How to spot:** any `import MyModule` or directory named with capital letter that's meant to be
importable.
([Software Carpentry](https://intermediate-and-advanced-software-carpentry.readthedocs.io/en/latest/structuring-python.html))
**AVC status:** PASS — all modules are lowercase.

---

## 6. AI-navigability layer (2026 state of the art)

### Orientation files hierarchy

The 2026 consensus across the AI-coding tool ecosystem:

```
repo-root/
├── AGENTS.md          # Universal (20+ tools, Linux Foundation, 60k+ repos)
├── CLAUDE.md          # Claude Code-specific (nearest-wins precedence, @imports)
├── CLAUDE.local.md    # Gitignored, per-developer preferences
└── avcs/
    ├── ui/
    │   └── CLAUDE.md  # Subpackage-specific (after restructure)
    └── varieties/
        └── CLAUDE.md  # Subpackage-specific (after restructure)
```

**Root AGENTS.md** — Recommended sections (per agents.md spec, confirmed live 2026-05-23):
- Project overview
- Build and test commands
- Code style guidelines
- Testing instructions
- Security considerations
- Commit message / PR guidelines

**Root CLAUDE.md** — Under 200 lines (Anthropic's current recommendation). Sections that work
empirically:
- Project context (one line)
- Code style preferences
- Commands (exact strings — `pytest`, `.venv/bin/python app.py`)
- Architecture decisions (where things live, with local-path references to CONTEXT.md)

The Anthropic Claude Code best practices documentation updated the line count recommendation from
the HumanLayer-cited 300 lines down to 200 lines as of the current live page (accessed 2026-05-23).

**Per-subdirectory CLAUDE.md** — *"The closest AGENTS.md to the edited file wins"* (agents.md spec,
Issue #53 confirmed this behavior). Useful for monorepos; for single-package AVC, one root file
is sufficient until after a subpackage split.

**Symlink convention** — `CLAUDE.md -> AGENTS.md` or `AGENTS.md -> CLAUDE.md` to avoid drift.
DeployHQ guide and Datadog frontend guide both recommend the symlink approach.
([deployhq.com](https://www.deployhq.com/blog/ai-coding-config-files-guide),
[Datadog Monorepo guide](https://dev.to/datadog-frontend-dev/steering-ai-agents-in-monorepos-with-agentsmd-13g0))

### Naming conventions that help AI navigate

- Lowercase, underscore-separated module names (universal Python convention).
- Directory names that *describe what's inside*: `render/`, `varieties/`, `ui/` beats `core/`,
  `lib/`, `common/`.
- Underscore-prefix for "internal contract, may break without warning" (napari `_qt/`, scipy
  `_lib/`).
- File name = module's job: `parameter_grid.py` good; `helpers.py` bad.
([Lehtinen "dunghill"](https://mattilehtinen.com/articles/dunghill-anti-pattern-why-utility-classes-and-modules-smell/),
[propelcode 2025](https://www.propelcode.ai/blog/structuring-codebases-for-ai-tools-2025-guide))

### File-size norms

No formal authority; converging informal practice in 2025-2026 AI-coding literature:
- Under ~500 LOC ideally, under ~800 acceptably. [CONTESTED]
- `utils.py`-style files: under ~200 LOC or split. [Lehtinen, Hitchhiker's Guide]
- 1000+ LOC: yellow flag. 1500+ LOC: orange flag. 2000+ LOC: red flag.
- AVC's `app.py` (1900) and `surfaces.py` (1811) are both at the red line.
- `tests/test_styles_palette.py` (1261 LOC) is a test file — the threshold is more lenient for
  parametrized test files but 1261 LOC of test setup is a signal of a complex subsystem.

### Import-graph shape (AVC-specific analysis)

From the cached import graph (`imports-rough.json`):

```
surfaces.py → [dataclasses, numba, numpy, pyvista, warnings]       # pure domain, no Qt
render_worker.py → [pyvista, surfaces, dataclasses]                 # render pipeline, no Qt
parameter_grid.py → [surfaces, dataclasses]                         # data model, no Qt
styles.py → [styles]  (self-import artifact — likely init-only)
icons.py → [PySide6, styles, qtawesome]                             # pure Qt
parameter_grid_panel.py → [PySide6, surfaces, parameter_grid, styles, ui_helpers]
parameters_panel.py → [PySide6, surfaces, icons, parameter_grid, parameter_grid_panel, ui_helpers]
view_panel.py → [PySide6, numpy, pyvista, icons]
appearance_panel.py → [PySide6, styles, icons]
ui_helpers.py → [PySide6, surfaces, parameter_grid, styles]
app.py → [PySide6, pyvistaqt, surfaces, render_worker, styles, icons, appearance_panel,
          parameters_panel, view_panel]
```

**Key structural observation:** The dependency direction is already domain-first:
- `surfaces.py` imports no Qt — clean domain layer.
- `render_worker.py` imports `surfaces` but no Qt — clean render worker.
- `parameter_grid.py` imports `surfaces` but no Qt — clean data model.
- All Qt imports are confined to the panel files, `icons.py`, `ui_helpers.py`, and `app.py`.

This is an excellent foundation. The import graph already has the right direction; the subpackage
split would just make it structural rather than informal.

**Note on `surfaces.py` importing `pyvista`:** surfaces.py is the domain model but imports pyvista
for `pv.PolyData` as the return type. Per AI-6 invariant, this is the correct design for AVC
(generators return PolyData). Splitting VTK out of the domain model would require a separate
geometry type — out of scope and against the invariants.

### Docstring discipline

- NumPy/numpydoc style for scientific Python ([pandas AGENTS.md]).
- Docstrings double as agent-readable interface descriptions; type hints close the gap.
- Every variety function in `surfaces.py` should have a docstring with: mathematical definition,
  parameter ranges, cross-reference to ≥2 sources (per AI-15 invariant).

---

## 7. Qt+VTK+PyVista special considerations

### What napari/Spyder/ParaView do well that AVC should borrow

1. **Renderer-vs-domain separation enforced by directory.** Napari's `_vispy/` keeps render
   backend swappable. PyVista's `core/` vs `plotting/` split is the same idea. **Pattern for AVC:**
   if `avcs/` grows beyond its current size, a `render/` subpackage (containing `render_worker.py`
   and any VTK helpers) separate from `varieties/` (domain math) would make the boundary explicit.
   Current state: already respected informally via imports.

2. **Qt subpackage marked private with underscore (`_qt/`).** Napari's pattern says "the Qt parts
   are not contracts to external callers." **Pattern for AVC:** `avcs/_qt/` (panels, dialogs,
   custom widgets) or `avcs/ui/` if you prefer public. Given single-developer ownership,
   `avcs/ui/` is cleaner than `avcs/_qt/`.

3. **`app/` subpackage for the launcher.** Spyder's pattern: `spyder/app/` contains `main.py`,
   `mainwindow.py`, `restart.py`. Directly applicable to AVC's 1900-LOC `app.py`. Split into
   `avcs/app/__main__.py` (entry point), `avcs/app/main_window.py` (Qt assembly + signal wiring),
   `avcs/app/render_pipeline.py` (the `_render_current` + mesh lifecycle logic).

4. **`resources/` for non-code assets.** AVC's `icons.py` generates icons in code (qtawesome),
   which is fine and doesn't need a `resources/` dir. But if AVC ever loads bundled shader files,
   color themes, or locale strings, they belong in `avcs/resources/` not at root.

5. **`experimental/` or `incubator/` namespace.** Napari `experimental/`, ParaView `Incubator/`.
   If AVC adds new variety families under active development, `avcs/varieties/experimental/` says
   "expect this to move" to both humans and agents.

### What naturally tends to go monolithic in this project family

Every reference project has suffered from these failure modes — AVC is in early stages of the
same patterns:

1. **Giant generator/model modules.** `surfaces.py` at 1811 LOC is the canonical example —
   a single file with 14 generators, 11 Numba kernels, 2 dataclasses, 2 utility predicates, and
   2 pipeline helpers. **Recognize by:** file growth log, lots of similar functions with slightly
   different parameter sets. **Fix:** package-by-variety — `varieties/k3.py`,
   `varieties/enriques.py`, `varieties/calabi_yau.py`, `varieties/fano.py`, each ~100-450 LOC.

2. **Panel files that grow 500+ LOC as widgets accumulate.** `appearance_panel.py` (738 LOC),
   `parameter_grid_panel.py` (713 LOC), `view_panel.py` (503 LOC) are all at or over the
   orange line. **Fix:** move into `avcs/ui/` as a subpackage; consider per-section splits
   (e.g. `avcs/ui/clip_controls.py` factored from `view_panel.py`).

3. **`app.py` as the bus for everything.** AVC's `app.py` at 1900 LOC handles: init, window
   assembly, signal wiring, menu construction, theme switching, file dialogs, and the entire
   render pipeline. Napari splits `window.py`, `viewer.py`, `view_layers.py`. **Recognize by:**
   `app.py` over 300 LOC; method count over 20 in `MainWindow`.

4. **Style / theme / appearance modules entangled with widget construction.** AVC's `styles.py`
   (692 LOC) is actually well-structured — palette constants, stylesheet template function,
   variety default colors. It's a clean separation *already*. The risk is adding more to it.
   **Recognize by:** color literals appearing in panel files rather than in `styles.py`.

### Things specific to AVC's stack

- **Numba JIT kernel import side effect.** `surfaces.py` sets `numba.config.THREADING_LAYER =
  "workqueue"` as a process-global side effect at import time (AI invariant). Any split of
  `surfaces.py` must keep this side effect in a single `__init__.py` or top-level module that is
  guaranteed to import before any kernel is called. The 45-test numerical equivalence suite
  (`test_numba_field_kernels.py`) is the regression guard.

- **VTK is import-heavy.** Don't `import pyvista` at module top-level in modules that might be
  imported during tests of unrelated subsystems. The test suite already respects this (AI-2
  invariant: tests are Qt-free; VTK imports are guarded by `pytest` fixture machinery).

- **Threading boundary is explicit.** The `_computing` single-flight guard (AI-9 invariant) must
  be preserved across any `app.py` split. If the render pipeline is factored into a
  `render_pipeline.py` module, the guard must travel with it.

- **AI-1..AI-15 invariants are inviolable.** Any restructure that crosses a module boundary
  (e.g. moving `render_worker.py` imports or splitting `surfaces.py`) must preserve all 15
  invariants. The invariants are in `.claude/references/app-invariants.md` and the cache card
  at `.claude/notes/repository-architect/restructure-full-audit-2026q2-r1/cache/ai-invariants-card.md`.

---

## 8. Honest assessment — where the literature is contradictory or unsettled

1. **src vs flat for *applications*.** [CONTESTED] PyPA, pyOpenSci, ionelmc push src for
   libraries. uv defaults to flat. Pandas, scipy, django are all flat at their scale. Cookiecutter
   Data Science is flat. Real Python (2025) now recommends src for desktop apps with pyproject.toml.
   **Honest answer for AVC:** moving from "no package" to `avcs/` (flat-package) is unambiguously
   correct and low-risk. Moving from `avcs/` to `src/avcs/` is a second, optional step with real
   tradeoffs (adds `pip install -e .` requirement for contributors). The designer should declare
   this as a deliberate choice.

2. **Tests inside vs outside the package.** [CONTESTED] pyOpenSci says outside (smaller wheel,
   preferred default). Pandas, spyder, scipy, napari all put tests inside. AVC currently has
   `tests/` as a sibling (pyOpenSci shape) with no dependency on a package install. This is
   correct given AI-2 (tests are Qt-free, run via path manipulation). **Do not change this unless
   the package structure changes significantly.**

3. **`utils/` as a subpackage with subdirectories** (Django) vs **`utils/` is always a smell**
   (Lehtinen). [CONTESTED] AVC's `ui_helpers.py` (264 LOC) is at the edge. It contains
   debounce logic (a `QTimer`-based utility) and possibly other Qt helpers. A `avcs/ui/helpers.py`
   within the `ui/` subpackage is cleaner than a top-level `ui_helpers.py`.

4. **Two-deep nesting limit.** [OPINION but well-established] Software Carpentry heuristic. Fine
   to violate once if there's a genuine reason (e.g. `avcs/varieties/experimental/` as a
   three-level path is acceptable if `experimental` is a genuine staging zone).

5. **CLAUDE.md size cap.** [OPINION, fast-moving] HumanLayer says <300 lines; Anthropic's current
   documentation says <200 lines (confirmed live 2026-05-23); the empirical ceiling in 2025-2026
   best-practice writing is 200-300 lines. Use 200 as the target.

6. **AGENTS.md vs CLAUDE.md.** [CONSENSUS that both have a place; CONTESTED on which to prefer]
   AGENTS.md is the cross-tool standard (Linux Foundation, 60k+ repos, 20+ tools). CLAUDE.md is
   Claude-Code-specific and more powerful (@imports, hierarchical loading, local override).
   **Pragma:** AGENTS.md for universality; CLAUDE.md for Claude-specific extras; have CLAUDE.md
   `@import` or symlink to AGENTS.md to avoid drift.

7. **Whether per-subpackage CLAUDE.md is worth the maintenance cost.** [CONTESTED] For AVC as a
   single-developer project, one root AGENTS.md + CLAUDE.md is sufficient. Per-subpackage files
   add value after the subpackage split and when AI agents are routinely editing subpackage code
   independently.

8. **Parameter panel naming.** [OPINION] The `parameters_panel.py` / `parameter_grid_panel.py`
   dual naming is a navigation hazard but not a classical anti-pattern — it's a consequence of
   iterative feature development. The "correct" fix is contested: merge vs rename vs document.
   The brief's "conservative bias" suggests documenting first, restructuring second.

---

## 9. File-by-file evaluator checklist — 28 items

Run by `evaluate-checklist.py restructure-full-audit-2026q2-r1` on 2026-05-23.
Overall result: **14/28 PASS**.

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | README.md present at root | **PASS** | README.md exists |
| 2 | LICENSE present at root | **FAIL** | MISSING — no LICENSE, LICENSE.md, or COPYING |
| 3 | CHANGELOG.md present at root | **FAIL** | MISSING |
| 4 | CODE_OF_CONDUCT.md present at root | **FAIL** | MISSING (optional for solo project) |
| 5 | CONTRIBUTING.md present at root | **FAIL** | MISSING (scales with team size) |
| 6 | pyproject.toml present at root | **FAIL** | MISSING — canonical in 2026 |
| 7 | AGENTS.md present at root | **FAIL** | MISSING — 60k+ adopting repos |
| 8 | CLAUDE.md present at root | **FAIL** | MISSING — AVC uses CONTEXT.md but no CLAUDE.md |
| 9 | No setup.py unless stated reason | **PASS** | absent (correct) |
| 10 | Top-level file count under 20 | **PASS** | 15 files at root (within range; adding 5 missing files reaches 20) |
| 11 | Importable code under a named package | **FAIL** | NO PACKAGE — 11 loose .py files at root |
| 12 | No utils.py over 200 LOC | **PASS** | `ui_helpers.py` (264 LOC) is a borderline case — no file named `utils.py`; `ui_helpers.py` is near the threshold |
| 13 | No directory more than 2 levels deep | **PASS** | max depth: 0 (no subpackages) |
| 14 | Module names lowercase with underscores | **PASS** | all lowercase |
| 15 | Subpackages reflect domain/role, not layer | **PASS** | no layered subpackages (vacuously true) |
| 16 | No `from foo import *` | **PASS** | no wildcard imports |
| 17 | No file over ~800 LOC | **FAIL** | `app.py` (1900 LOC), `surfaces.py` (1811 LOC), `tests/test_styles_palette.py` (1261 LOC) |
| 18 | tests/ directory exists as sibling of package | **PASS** | tests/ exists |
| 19 | docs/ directory exists at root | **FAIL** | MISSING |
| 20 | examples/ directory exists | **FAIL** | MISSING (AVC has visible UI output) |
| 21 | AGENTS.md or CLAUDE.md under 300 lines | **FAIL** | neither file exists |
| 22 | CLAUDE.md doesn't contain lint rules | **PASS** | vacuously true (no CLAUDE.md) |
| 23 | No temp/tmp/misc/stuff/old/backup dirs | **PASS** | clean |
| 24 | Framework-adapter code in named subpackages | **FAIL** | no `_qt/`, `_vispy/`, `render/`, `ui/` subpackage; framework adapters interleaved at root |
| 25 | .gitignore covers __pycache__, .pytest_cache, etc. | **FAIL** | `.pytest_cache/` MISSING from .gitignore |
| 26 | Import graph has no cycles | **PASS** | [UNVERIFIED — needs pydeps or import-linter; no obvious cycles in import graph] |
| 27 | `python -c "import setup"` fails | **PASS** | no setup.py (vacuously true) |
| 28 | Every top-level subpackage has __init__.py docstring | **PASS** | vacuously true (no subpackages) |

### Checklist analysis by priority for this restructure brief

**High-value FAILs matching the brief (address in this restructure):**
- Item 2 (LICENSE) — zero-risk, 1 minute.
- Item 6 (pyproject.toml) — low-risk, replaces requirements.txt as packaging source.
- Item 7 (AGENTS.md) — low-risk, high AI-navigability payoff.
- Item 8 (CLAUDE.md) — low-risk, high AI-navigability payoff.
- Item 11 (named package) — medium-risk, prerequisite for subpackage work.
- Item 17 (file over 800 LOC) — high-risk, gated behind low-risk batches.
- Item 24 (framework adapters in subpackages) — medium-risk, requires item 11 first.
- Item 25 (.gitignore) — zero-risk, 1 line.

**FAILs outside the brief scope (note but don't pull into scope):**
- Items 3-5 (CHANGELOG, CODE_OF_CONDUCT, CONTRIBUTING) — single-developer project; add later.
- Items 19-20 (docs/, examples/) — out of brief scope; note for future.

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
- [jcheng — src vs flat 2024](https://www.jcheng.org/post/python-and-the-src-vs-flat-layout-debate/)
- [lawwu TIL src vs flat 2025-03-18](https://lawwu.github.io/til/posts/2025-03-18-flat-vs-src-layouts/index.html)
- [Real Python — project layout best practices 2025](https://realpython.com/ref/best-practices/project-layout/)

### Tier 2 — Reference repositories

- [napari](https://github.com/napari/napari) — src layout confirmed; no AGENTS.md (404)
- [PyVista](https://github.com/pyvista/pyvista) — flat layout; ships context7.json; no AGENTS.md (404)
- [Spyder](https://github.com/spyder-ide/spyder) — `app/` subpackage pattern; no AGENTS.md (404)
- [pandas](https://github.com/pandas-dev/pandas) — ships AGENTS.md at root (live, content verified)
- [pandas AGENTS.md](https://github.com/pandas-dev/pandas/blob/main/AGENTS.md) — content fetched via gh API
- [SciPy](https://github.com/scipy/scipy)
- [Django](https://github.com/django/django)
- [Kubernetes](https://github.com/kubernetes/kubernetes) — ships AGENTS.md at root
- [ParaView (Kitware)](https://github.com/Kitware/ParaView) — mirror; GitLab primary at 403

### Tier 3 — Modular architecture & AI-navigability

- [Kraken Technologies — large Python monolith (EuroPython)](https://blog.europython.eu/kraken-technologies-how-we-organize-our-very-large-pythonmonolith/)
- [Sahibinden Tech — package-by-layer vs package-by-feature (2024)](https://medium.com/sahibinden-technology/package-by-layer-vs-package-by-feature-7e89cde2ae3a)
- [agents.md spec (Linux Foundation / Agentic AI Foundation)](https://agents.md/) — confirmed live; 60k+ repos, 20+ tools
- [HumanLayer — writing a good CLAUDE.md](https://www.humanlayer.dev/blog/writing-a-good-claude-md) — confirmed live; key quotes verified
- [Anthropic Claude Code best practices](https://code.claude.com/docs/en/best-practices) — <200 lines recommendation
- [Complete guide to AI agent memory files (data-science-collective)](https://medium.com/data-science-collective/the-complete-guide-to-ai-agent-memory-files-claude-md-agents-md-and-beyond-49ea0df5c5a9)
- [Structuring codebases for AI tools 2025 (Propel Code)](https://www.propelcode.ai/blog/structuring-codebases-for-ai-tools-2025-guide)
- [DeployHQ — AI coding config files guide](https://www.deployhq.com/blog/ai-coding-config-files-guide)
- [Datadog Frontend — Steering AI agents in monorepos with AGENTS.md](https://dev.to/datadog-frontend-dev/steering-ai-agents-in-monorepos-with-agentsmd-13g0)
- [agents.md GitHub — per-folder precedence (Issue #53)](https://github.com/agentsmd/agents.md/issues/53)
- [Context7](https://context7.com/) and [Upstash Context7 blog](https://upstash.com/blog/context7-llmtxt-cursor)

### Tier 4 — Anti-patterns & heuristics

- [Matti Lehtinen — Dunghill anti-pattern](https://mattilehtinen.com/articles/dunghill-anti-pattern-why-utility-classes-and-modules-smell/)
- [Software Carpentry — structuring Python (two-deep heuristic)](https://intermediate-and-advanced-software-carpentry.readthedocs.io/en/latest/structuring-python.html)
- [The Little Book of Python Anti-Patterns (quantifiedcode)](https://docs.quantifiedcode.com/python-anti-patterns/)
- [Keep a Changelog](https://keepachangelog.com/)

### Could not fetch / unverified

- `https://learn.scientific-python.org/development/guides/repo/` — 404 at fetch time. [UNVERIFIED]
- `https://scientific-python.github.io/repo-review/` — page rendered as "Loading…"; only category
  list is well-attested. [UNVERIFIED] for individual check IDs.
- `https://gitlab.kitware.com/paraview/paraview` — 403 Access Denied; ParaView tree pulled from
  github.com/Kitware/ParaView mirror.
- context7.json as a "broadly adopted standard" — only confirmed in PyVista; no evidence of
  widespread Python package adoption. [UNVERIFIED as standard]
