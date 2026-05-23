# Scout B — Repository Structure Best Practices (2024–2026)

**Scope:** raw material for the `/repository-architect` slash command design phase. Focus: Python desktop scientific-viz apps (AVC = PyQt + PyVista + VTK), with cross-language reference where the pattern transfers.

**Access date for all sources:** 2026-05-23.

**Honesty conventions:**
- `[CONSENSUS]` — multiple independent reputable sources agree.
- `[CONTESTED]` — credible sources disagree.
- `[OPINION]` — single author's well-reasoned position; treat as input not verdict.
- `[UNVERIFIED]` — could not fetch primary source; included only when widely cross-referenced.

---

## 1. TL;DR — 5 bullets

1. **The src-layout vs flat-layout war is essentially over for libraries — src/ wins by default — but it's not settled for apps.** [CONSENSUS for libraries] PyPA, pyOpenSci, ionel, NASA's flight code, and the Scientific Python development guide all push `src/<package>/`. The flat-layout holdouts (uv's default since Aug 2024) are deliberately optimizing for "new project runs without install." Poetry flipped to src as default in Feb 2025. ([packaging.python.org](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/), [pyOpenSci](https://www.pyopensci.org/python-package-guide/package-structure-code/python-package-structure.html), [ionelmc 2014](https://blog.ionelmc.ro/2014/05/25/python-packaging/), [lawwu TIL 2025-03-18](https://lawwu.github.io/til/posts/2025-03-18-flat-vs-src-layouts/index.html))

2. **Package-by-feature is winning over package-by-layer for modular monoliths**, especially as AI agents enter the picture. Kraken Technologies' very-large Python monolith (publicly documented, Import-Linter enforced) layers by *domain* (clients → territories → core), not by Controller/Service/Repository. ([Kraken / EuroPython blog](https://blog.europython.eu/kraken-technologies-how-we-organize-our-very-large-pythonmonolith/), [Sahibinden Tech 2024](https://medium.com/sahibinden-technology/package-by-layer-vs-package-by-feature-7e89cde2ae3a))

3. **AGENTS.md is the emerging 2025/2026 standard** for agent-readable repo orientation. Pandas and Kubernetes both ship one at root. The spec is now under the Agentic AI Foundation (Linux Foundation), with 60k+ adopting repos and 20+ supported tools. Claude Code still doesn't natively read it — the field convention is `ln -s AGENTS.md CLAUDE.md` or maintain both. ([agents.md](https://agents.md/), [pandas/AGENTS.md](https://github.com/pandas-dev/pandas/blob/main/AGENTS.md), [kubernetes/AGENTS.md](https://github.com/kubernetes/kubernetes/blob/master/AGENTS.md), [deployhq guide](https://www.deployhq.com/blog/ai-coding-config-files-guide))

4. **For Qt+VTK+PyVista desktop apps specifically:** napari is the closest reference and uses a clear *role-based subpackage discipline* — `components/`, `layers/`, `plugins/`, `_qt/`, `_vispy/`, `settings/`, `utils/`. Spyder uses `api/`, `plugins/`, `widgets/`, `app/`. Both keep the GUI framework prefix (`_qt`, `_vispy`) as a *private underscore-prefixed* subpackage — a transferable pattern for AVC's PyQt+PyVista split. ([napari src tree via GitHub API](https://github.com/napari/napari), [spyder repo](https://github.com/spyder-ide/spyder))

5. **The under-cited but operationally critical rules** are (a) two-deep nesting max, (b) CLAUDE.md under 300 lines, (c) no grab-bag `utils.py` larger than ~200 LOC, (d) one job per module, (e) tests *parallel to* but not *inside* the package. These convert directly into evaluator checklist items (see §9). ([Software Carpentry](https://intermediate-and-advanced-software-carpentry.readthedocs.io/en/latest/structuring-python.html), [HumanLayer CLAUDE.md guide](https://www.humanlayer.dev/blog/writing-a-good-claude-md), [Matti Lehtinen "Dunghill"](https://mattilehtinen.com/articles/dunghill-anti-pattern-why-utility-classes-and-modules-smell/))

**Open debates worth flagging for the design phase:**
- src vs flat for *applications* (not libraries) — genuinely unsettled.
- Whether tests should be inside `src/<pkg>/tests/` (so they ship in the wheel and run on user installs) or sibling to `src/` (pyOpenSci default, smaller wheel).
- Whether private subpackages should use `_` prefix (napari yes; SciPy mixes; PyVista no — uses public `core/`).

---

## 2. Canonical layouts (Tier 1)

### 2.1 The Hitchhiker's Guide to Python — flat layout, anti-src

Source: <https://docs.python-guide.org/writing/structure/> (Kenneth Reitz lineage, accessed 2026-05-23)

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

Key quote: *"Your library does not belong in an ambiguous src or python subdirectory."* Explicitly rejects src/. This is the **dissenting** but historically influential position. [OPINION — single source, but cited millions of times]

### 2.2 pyOpenSci Python Packaging Guide — src layout, scientific Python

Source: <https://www.pyopensci.org/python-package-guide/package-structure-code/python-package-structure.html>

```
myPackageRepoName
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

Key quote: *"We strongly suggest, but do not require, that you use the **src/** layout."* Reasoning: *"tests are run against the installed version of your package rather than the files in your package working directory."* Lists CHANGELOG, CODE_OF_CONDUCT, CONTRIBUTING, LICENSE, README, pyproject.toml as **required** top-level files for scientific Python packages. [CONSENSUS within scientific Python.]

### 2.3 PyPA (Python Packaging Authority) — neutral but src-leaning

Source: <https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/>

Doesn't formally pick a winner, but presents src layout's import-isolation advantages as decisive for projects where it matters: *"the Python interpreter includes the current working directory as the first item on the import path"* (the flat-layout shadowing trap). Notes the trade-off: *"The src layout requires installation of the project to be able to run its code, and the flat layout does not."* [CONSENSUS that PyPA leans src.]

### 2.4 Scientific Python Development Guide / SPECs

Sources: <https://learn.scientific-python.org/development/>, <https://scientific-python.org/specs/>

The SPECs (Scientific Python Ecosystem Coordination) endorse cross-project standards. As of 2026-05-23:

| SPEC | Title                                          | Status   |
|------|------------------------------------------------|----------|
| 0    | Minimum Supported Dependencies                 | Endorsed |
| 1    | Lazy Loading of Submodules and Functions       | Endorsed |
| 2    | API Dispatch                                   | Draft    |
| 3    | Accessibility                                  | Draft    |
| 4    | Using and Creating Nightly Wheels              | Endorsed |
| 5    | CI Best Practices                              | Draft    |
| 6    | Keys to the Castle                             | Endorsed |
| 7    | Seeding Pseudo-Random Number Generation        | Endorsed |
| 8    | Securing the Release Process                   | Endorsed |
| 9    | Governance                                     | Draft    |

**Most relevant to AVC:** SPEC 1 (lazy loading) is the key architectural pattern for keeping import-time costs bounded in a Qt app that imports VTK/PyVista. [CONSENSUS within scientific Python.]

The companion `sp-repo-review` tool runs check categories: General (PY), PyProject (PP), Ruff (RF), MyPy (MY), pre-commit (PC), GitHub Actions (GH), ReadTheDocs (RTD). [UNVERIFIED at the level of individual check IDs — repo-review page wouldn't render server-side; only category list is well-attested.]

### 2.5 Cookiecutter Data Science v2

Source: <https://cookiecutter-data-science.drivendata.org/>

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
├── setup.cfg
└── {{ module_name }}/
    ├── __init__.py
    ├── config.py
    ├── dataset.py
    ├── features.py
    ├── modeling/
    ├── plots.py
    └── predict.py
```

Note: **flat layout** (no `src/`). Their philosophy: *"A logical, flexible, and reasonably standardized project structure for doing and sharing data science work."* The `data/{raw,interim,processed,external}` quadrant has become canon for ML/data — *not* directly applicable to AVC, but the `references/` (papers, manuals) and `notebooks/` (exploratory) directories are a good cross-pollination target.

### 2.6 Ionel's classic src argument

Source: <https://blog.ionelmc.ro/2014/05/25/python-packaging/> (still cited in 2025+)

Key claim: *"The current directory is implicitly included in sys.path; but not so when installing & importing from site-packages. Users will never have the same current working directory as you do."* Forces dev to test the installed copy → catches packaging bugs early. Also notes: without src, `setup.py` and other config files *"will unwittingly become importable"*. [CONSENSUS — most-cited single-author piece on this debate.]

### 2.7 The jcheng.org 2024 dissent-from-the-default

Source: <https://www.jcheng.org/post/python-and-the-src-vs-flat-layout-debate/>

Argues uv's flat default (chosen ~Aug 2024) is wrong: *"a significant number of projects moved to src since this article has been published… 2021: NASA landed another robot on Mars, and they use src directories."* Position: src layout, even with uv. [OPINION but well-reasoned.]

---

## 3. Reference orgs analyzed

| Org | URL | Top-level shape | Exemplary | Outdated / quirky |
|-----|-----|-----------------|-----------|-------------------|
| **napari** (Qt+VTK desktop) | <https://github.com/napari/napari> | `src/napari/{_qt,_vispy,components,layers,plugins,settings,utils,...}` + `examples/`, `resources/`, `tools/`, `binder/` | Role-prefixed private subpackages (`_qt`, `_vispy`) cleanly separate framework adapters from domain logic. `view_layers.py`, `viewer.py`, `window.py` as top-level entry points. Has `experimental/` and `_vendor/` directories — explicit naming for special-status code. | No `AGENTS.md` or `CLAUDE.md` yet (as of fetch). Docs in a separate `napari/docs` repo — works for them, would be overkill for AVC. |
| **PyVista** (AVC's render dep) | <https://github.com/pyvista/pyvista> | `pyvista/{core,plotting,utilities,jupyter,trame,demos,examples,typing,_cli,ext}` + `doc/`, `tests/`, `examples/`, `joss/` | Flat layout but disciplined: `core/` (data model), `plotting/` (render), `utilities/` (genuinely shared low-level). `_cli/`, `_vtk.py`, `_plot.py` privately-prefixed. Ships `context7.json` (LLM context manifest — emerging pattern). | Has both `examples/` (top-level user-facing) AND `pyvista/examples/` (programmatic) — duplicate-name confusion. Top-level file count is 25+ (CITATION.cff, CITATION.rst, README.md, multiple lockfiles) — heavy. |
| **Spyder** (Qt IDE) | <https://github.com/spyder-ide/spyder> | `spyder/{api,app,config,plugins,utils,widgets,windows,tests,fonts,images,locale}` + many root files | Clear separation: `api/` (public extension surface), `plugins/` (extension impls), `widgets/` (reusable Qt), `app/` (entry/launcher), `windows/` (top-level windows). Static assets (`fonts/`, `images/`, `locale/`) live with the package. | `tests/` *inside* the package (atypical — but rationalized by being a desktop IDE that bundles tests for self-diagnosis). 40+ root-level files including `bootstrap.py`, `runtests.py`, `install_dev_repos.py` — high noise. |
| **pandas** | <https://github.com/pandas-dev/pandas> | flat: `pandas/{api,arrays,core,errors,io,plotting,tseries,util,tests,_libs,_config,_testing}` + `AGENTS.md`, `doc/`, `scripts/`, `web/` | **Ships AGENTS.md at root** — directly relevant precedent. `core/` (compute), `api/` (public surface), `io/` (boundary), `_libs/` (compiled), `plotting/` (viz boundary). `_typing.py` and `testing.py` as top-level conveniences. | Has `tests/` *inside* pandas/ — divergent from pyOpenSci recommendation. Reflects the size: a 1M-LOC project can pay the wheel cost. |
| **SciPy** | <https://github.com/scipy/scipy> | flat: `scipy/{cluster,constants,datasets,fft,integrate,interpolate,io,linalg,...,_lib,_build_utils}` + `benchmarks/`, `doc/`, `tools/`, `subprojects/` | Textbook **subpackage discipline by mathematical domain**: each subpackage is a coherent unit with its own `__init__.py` API. `_lib/` for cross-subpackage shared internals. Ships `tach.toml` (module-boundary linter). | Build complexity (`meson.build`, `pixi.toml`, `mypy.ini`, `pyrefly.toml`) is necessary for a project this size but a *cargo-cult risk* for smaller apps. |
| **Django** | <https://github.com/django/django> | flat: `django/{apps,conf,contrib,core,db,dispatch,forms,http,middleware,tasks,template,test,urls,utils,views}` + `docs/`, `tests/` at root | Feature-clean subpackages (`forms/`, `http/`, `views/`, `middleware/`, `template/`) — package-by-feature. `tests/` sibling to `django/` — pyOpenSci-shaped. `contrib/` as "official-but-optional" namespace is a great pattern for AVC plugins later. | `utils/` at the top of a major project — a *deliberate* utility namespace, but only justifiable because it has internal subpackages (`utils/translation`, `utils/dateparse`), not a grab-bag file. |
| **OpenSSL** (C, but instructive) | <https://github.com/openssl/openssl> | `apps/`, `crypto/`, `ssl/`, `providers/`, `doc/`, `test/`, `include/`, `demos/`, `fuzz/`, `external/` + many `NOTES-*.md` | The `crypto/`, `ssl/`, `providers/` split is **textbook deep-modules-by-domain**. `apps/` for CLIs. `external/` for third-party. `NOTES-WINDOWS.md`, `NOTES-ANDROID.md`, etc. — platform-specific docs as first-class root files. | 40+ root-level files, many platform-specific notes. The notes pattern is good; the count is intimidating. |
| **Kubernetes** (Go, but the *de facto* monorepo template) | <https://github.com/kubernetes/kubernetes> | `cmd/`, `pkg/`, `staging/`, `vendor/`, `hack/`, `api/`, `build/`, `cluster/`, `docs/`, `plugin/`, `test/`, `third_party/` + `AGENTS.md` | **Ships AGENTS.md.** `cmd/` = entry points (one binary per subdir), `pkg/` = library code, `hack/` = dev scripts, `staging/` = vendored-but-owned. The `cmd/` vs `pkg/` split (Go-idiomatic) maps cleanly to Python's "scripts in a `bin/` or `tools/` dir" vs "library code in `src/<pkg>/`". | `vendor/` is a Go-specific anti-pattern by Python standards. Don't copy. |
| **ParaView** (scientific viz desktop, our family) | <https://gitlab.kitware.com/paraview/paraview> (mirror via `gh api github.com/Kitware/ParaView`) | `Qt/`, `Plugins/`, `Clients/`, `Remoting/`, `VTKExtensions/`, `Web/`, `Wrapping/`, `Adaptors/`, `Documentation/`, `Examples/`, `Testing/`, `ThirdParty/`, `Utilities/`, `Kits/`, `Incubator/` | **Mirrors AVC's domain at scale.** `Qt/` (GUI), `Plugins/` (extensions), `Web/` (Trame/web client), `Wrapping/` (Python bindings), `VTKExtensions/` (their VTK additions), `Incubator/` (experimental). The `Incubator/` namespace is gold for an "in flux, not yet promoted" zone. | C++/CMake-heavy; capitalized directory names break Python import convention. The *partitioning* transfers; the *names* don't. |

[CONSENSUS] across these 9 orgs: domain-or-role-based subpackage split, README at root, LICENSE at root, separate docs/, separate tests/ (or inside-package only if you have a *stated* reason).

---

## 4. Patterns to adopt (with citations & applicability to AVC)

For each: name → 1-2 sentence description → source → applicability rating + why.

1. **src/ layout for the importable package**
   Place importable code in `src/<pkg>/` so dev workflow forces `pip install -e .` and tests run against installed code. ([PyPA](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/), [pyOpenSci](https://www.pyopensci.org/python-package-guide/package-structure-code/python-package-structure.html), [ionelmc](https://blog.ionelmc.ro/2014/05/25/python-packaging/))
   **Applicability to AVC: MEDIUM.** AVC is currently a flat-but-no-package layout (loose .py files at root). Moving to `src/avcs/` is a real refactor but eliminates the shadowing risk and is the modern default. AVC is a desktop *app*, not a library — the src argument is weaker here, but the "force `pip install -e .`" discipline still pays off when CI/packaging matters. Flat-with-package (`avcs/` at root) is the acceptable compromise.

2. **AGENTS.md at root**
   Single agent-readable file telling AI tools "where things live, what to run, what conventions to follow." Universal across Codex, Cursor, Jules, GitHub Copilot, JetBrains Junie, etc. ([agents.md](https://agents.md/), [pandas](https://github.com/pandas-dev/pandas/blob/main/AGENTS.md), [kubernetes](https://github.com/kubernetes/kubernetes/blob/master/AGENTS.md))
   **Applicability to AVC: HIGH.** Cheap, becoming standard. Symlink to CLAUDE.md (or vice versa) per HumanLayer's recommendation. Pandas's structure (Project Overview, Persona/Tone, Project Guidelines, Decision Heuristics, Type Hints, Docstring Guidance, Pull Requests) is a workable template.

3. **CLAUDE.md under 300 lines, ideally under 100**
   Spare, universally-applicable instructions only. Use `@imports` for detailed guidance. *"Every line in CLAUDE.md competes for attention with the actual work."* ([HumanLayer](https://www.humanlayer.dev/blog/writing-a-good-claude-md), [data-science-collective Medium guide](https://medium.com/data-science-collective/the-complete-guide-to-ai-agent-memory-files-claude-md-agents-md-and-beyond-49ea0df5c5a9))
   **Applicability to AVC: HIGH.** AVC's CONTEXT.md is excellent at orientation but at risk of becoming the kitchen sink. Pair: short CLAUDE.md for context-window discipline, CONTEXT.md for full architecture, `@import` between them.

4. **Two-deep package nesting max**
   *"Hierarchies of packages more than two deep are annoying to develop on: you spend a lot of your time browsing around between directories."* ([Software Carpentry, intermediate Python](https://intermediate-and-advanced-software-carpentry.readthedocs.io/en/latest/structuring-python.html)) [OPINION but well-established heuristic; the Python stdlib follows it.]
   **Applicability to AVC: HIGH.** AVC is currently 0-deep (no package at all). When packaging, aim for `avcs/<subpackage>/file.py` and resist a third level except for genuinely large subsystems (e.g. `avcs/varieties/generators/sextic.py` would be the only justifiable third level).

5. **Role-prefixed private subpackages for framework adapters (`_qt/`, `_vispy/`)**
   Napari's pattern: pure-Python domain logic in `components/`, `layers/`; framework-specific renderers in `_qt/`, `_vispy/`. Underscore = "internal contract, may break." ([napari](https://github.com/napari/napari))
   **Applicability to AVC: HIGH.** AVC has PyQt widgets and PyVista rendering bleeding through every panel file. A `_qt/` for Qt widgets and `_pyvista/` (or `_render/`) for rendering could enforce the dependency direction (domain → adapter, never the reverse).

6. **Package-by-feature for the modular monolith**
   Group code by *what it is* (a feature, a domain) not by *what it does* (controllers/services/models). Cohesion up, navigation cost down, AI-agent change-blast-radius down. ([Kraken / EuroPython](https://blog.europython.eu/kraken-technologies-how-we-organize-our-very-large-pythonmonolith/), [Sahibinden Tech](https://medium.com/sahibinden-technology/package-by-layer-vs-package-by-feature-7e89cde2ae3a)) [CONSENSUS for modular monoliths.]
   **Applicability to AVC: HIGH.** AVC's natural features are varieties, cross-section, rendering, parameter UI, export. A `varieties/`, `cross_section/`, `render/`, `ui/`, `export/` split is more navigable than `models/`, `views/`, `controllers/` would be.

7. **Import-Linter or Tach for enforced module boundaries**
   Kraken uses Import-Linter contracts; SciPy ships `tach.toml`. Define layer rules (e.g. `ui` may import `varieties`, never the reverse) and fail CI on violations. ([Kraken EuroPython](https://blog.europython.eu/kraken-technologies-how-we-organize-our-very-large-pythonmonolith/), [SciPy root tree])
   **Applicability to AVC: MEDIUM.** Worth adopting *once* a package layer exists. Premature for a flat layout.

8. **Lazy submodule loading (SPEC 1)**
   For scientific Python packages with heavy deps (VTK!), expose subpackages via lazy import to bound import time. ([scientific-python.org SPEC 1](https://scientific-python.org/specs/))
   **Applicability to AVC: MEDIUM-HIGH.** Desktop app cold-start matters. PyQt + PyVista + VTK is already heavy; lazy-loading subpackages (e.g. `avcs.export` not loaded until used) is a free win.

9. **`docs/`, `tests/`, `examples/` as siblings of `src/`**
   ([pyOpenSci], [Django], [Scientific Python guide]) [CONSENSUS]
   **Applicability to AVC: HIGH.** AVC has `tests/` already. Add `examples/` for runnable demo scripts (cf. PyVista, napari).

10. **CHANGELOG.md (Keep a Changelog format) at root**
    Required by pyOpenSci review. Better than burying in git log; better than no record at all. ([pyOpenSci])
    **Applicability to AVC: HIGH.** Currently nothing equivalent; CONTEXT.md changelog blocks are project-level not user-level.

11. **`scripts/` or `tools/` for dev helpers**
    Kubernetes `hack/`, scipy `tools/`, spyder `scripts/`, django `scripts/` — universal naming for "things that run, not things that get imported." [CONSENSUS]
    **Applicability to AVC: MEDIUM.** AVC's `.claude/scripts/` covers the agent side. A repo-root `scripts/` or `tools/` for one-off maintenance scripts would help when those appear.

12. **Public `api/` subpackage as the documented surface**
    Pandas `pandas.api`, spyder `spyder.api`. Everything else is implementation detail subject to change. ([pandas src tree], [spyder src tree])
    **Applicability to AVC: LOW for now, MEDIUM later.** Only valuable if AVC ever exposes a plugin API or programmatic-use surface. Premature now.

13. **`examples/` directory with runnable demos**
    PyVista, napari, scipy. Doubles as documentation and as regression-discovery. [CONSENSUS in viz packages]
    **Applicability to AVC: HIGH.** AVC already screenshots variety/subtype combinations for CONTEXT.md updates — a few of those become `examples/` scripts naturally.

14. **`resources/` for non-code assets (icons, shaders, locale)**
    Spyder `fonts/`, `images/`, `locale/`; napari `resources/`; PyVista `assets/`. [CONSENSUS]
    **Applicability to AVC: HIGH.** AVC's `icons.py` generates icons in code — fine, but if it ever loads bundled files, they belong in a sibling `resources/` not at root.

15. **Per-subpackage CLAUDE.md / AGENTS.md in monorepos**
    *"The closest AGENTS.md to the edited file wins."* OpenAI's repo has 88 AGENTS.md files. ([agents.md])
    **Applicability to AVC: LOW now, MEDIUM after refactor.** AVC is single-package; one root AGENTS.md is enough. After splitting into `varieties/`, `render/`, `ui/`, subpackage CLAUDE.md becomes useful.

---

## 5. Patterns to AVOID (with citations)

1. **Grab-bag `utils.py` — the "dunghill" anti-pattern.**
   *"Large, generic utility files are a very bad practice… By dumping unrelated functions into a single file, you're essentially creating a tangled web that hinders proper code organization."* ([Matti Lehtinen](https://mattilehtinen.com/articles/dunghill-anti-pattern-why-utility-classes-and-modules-smell/), [Hitchhiker's Guide](https://docs.python-guide.org/writing/structure/)) **How to spot:** any file named `utils.py`, `helpers.py`, `common.py`, `misc.py` over ~200 LOC, or containing functions that operate on more than 2 unrelated domain types. Fix: split into `<domain>_utils.py` files next to their domain (e.g. `mesh_utils.py` inside `render/`), or promote each cluster into its own deep module. [CONSENSUS as anti-pattern; CONTESTED whether `utils.py` is ever acceptable — Django keeps one but as a *package* with subdirs, not a file.]

2. **Wildcard imports (`from foo import *`).**
   *"makes the code harder to read and makes dependencies less compartmentalized"* — Hitchhiker's Guide. Also kills static analysis and AI agent comprehension. **How to spot:** `grep -r "import \*" src/`. [CONSENSUS]

3. **Tests inside the importable package by default.**
   pyOpenSci: *"we do not recommend including tests as part of your package wheel by default."* **How to spot:** `src/<pkg>/tests/` or `<pkg>/tests/`. Exception: if you ship tests for users to run (Spyder, pandas — large projects with a stated reason). [CONTESTED — pyOpenSci default vs pandas/spyder practice.]

4. **Flat layout where `setup.py` and `conftest.py` accidentally become importable.**
   ([ionelmc](https://blog.ionelmc.ro/2014/05/25/python-packaging/), [PyPA](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/)) **How to spot:** `python -c "import setup"` succeeds. [CONSENSUS]

5. **Package-by-layer (`controllers/`, `services/`, `repositories/`) for non-web Python apps.**
   *"causes low cohesion within packages because packages contain classes that are not closely related to each other"* — Sahibinden Tech 2024. Failure mode for AI agents: *"The agent confidently made changes across multiple layers, touched files it probably didn't need to touch, and ended up breaking parts of the system it never even looked at"* ([Nitin Gavhane 2026](https://nitingavhane.medium.com/ai-coding-agents-are-hitting-a-wall-and-the-wall-is-your-architecture-a57ec11d20ce)). **How to spot:** top-level subpackages named after architectural roles, not domain concepts. [CONSENSUS for modular monoliths; layered architecture still defensible at *intra-feature* level.]

6. **Three-or-more-deep nesting.**
   Software Carpentry's two-deep heuristic. **How to spot:** any file path with 4+ `/` after the package root. [OPINION but widely shared.]

7. **Mixing dev-helper scripts with importable code at root.**
   Spyder's `bootstrap.py`, `runtests.py`, `install_dev_repos.py` at root is *not* exemplary — it's a legacy compromise. Better: put them in `scripts/` or `tools/`. [CONSENSUS via Kubernetes/SciPy.]

8. **Stuffing CLAUDE.md with everything.**
   *"frontier LLMs can reliably follow 150-200 instructions. Since Claude Code's system prompt already contains ~50 instructions, your CLAUDE.md should be spare"* ([HumanLayer](https://www.humanlayer.dev/blog/writing-a-good-claude-md)). **How to spot:** CLAUDE.md > 300 lines, or contains lint rules a linter could enforce. [CONSENSUS in 2025/2026 AI-coding literature.]

9. **Top-level file sprawl.**
   PyVista's 25+ and Spyder's 40+ root files are intimidating to humans and agents alike. **How to spot:** `ls | wc -l` > 20 at repo root. Move what can move: lockfiles to subdir, platform notes to `docs/notes/`, CI configs to `.github/`. [OPINION — not unanimously shared, but the trend in 2025+ is toward fewer root files.]

10. **Capitalized directory names for Python projects.**
    ParaView's `Qt/`, `Plugins/`, `Clients/` work for CMake-driven C++ but break Python import idiom and confuse case-sensitive vs case-insensitive filesystems. ([Software Carpentry](https://intermediate-and-advanced-software-carpentry.readthedocs.io/en/latest/structuring-python.html): *"use lowercase, \_-separated names for module and function names"*) [CONSENSUS for Python.]

11. **`vendor/` directory.**
    Go pattern. Python's equivalent is publishing dependencies on PyPI and pinning versions. Napari has a `_vendor/` for genuinely-vendored deps but it's underscore-prefixed and small. [CONSENSUS.]

12. **Auto-generated CLAUDE.md.**
    *"CLAUDE.md is the highest leverage point of the harness, deserving careful manual crafting"* ([HumanLayer](https://www.humanlayer.dev/blog/writing-a-good-claude-md)). [OPINION but strongly held.]

---

## 6. AI-navigability layer (2026 state of the art)

The new dimension since ~mid-2024: codebases now have two audiences, humans and AI agents. The patterns that work for both:

### Markers / orientation files

- **`AGENTS.md` at root** — universal, [agents.md](https://agents.md/) spec, Linux-Foundation stewarded. Sections (per spec): Project overview · Build & test commands · Code style guidelines · Testing instructions · Security considerations. Optional: Dev environment tips, PR instructions.
- **`CLAUDE.md`** — Claude Code reads this. Under 300 lines (under 100 with `@imports`). Sections that empirically work ([HumanLayer], [data-science-collective Medium]): Project context (one line) · Code style preferences · Commands (exact strings) · Architecture decisions (where things live).
- **`CLAUDE.local.md`** — gitignored, per-developer preferences.
- **Per-subdirectory CLAUDE.md / AGENTS.md** — nearest-wins precedence ([agents.md]). OpenAI's repo runs 88 of them.
- **Symlink convention** — `ln -s AGENTS.md CLAUDE.md` if maintaining one canonical file. ([deployhq guide](https://www.deployhq.com/blog/ai-coding-config-files-guide))
- **`context7.json`** — emerging pattern; PyVista ships it. [UNVERIFIED on what consumes it broadly.]

### Naming conventions that help AI

- Lowercase, underscore-separated module names (universal Python convention).
- Directory names that *describe what's inside*: `render/`, `varieties/`, `cross_section/` beats `core/`, `lib/`, `common/`. ([propelcode AI-tools guide](https://www.propelcode.ai/blog/structuring-codebases-for-ai-tools-2025-guide))
- Underscore-prefix for "internal contract, may break without warning" (napari, scipy `_lib`).
- File name = module's job. `parameter_grid.py` good; `helpers.py` bad. ([Lehtinen "dunghill"])

### File-size norms

No source gives a hard limit, but converging informal practice in the 2025/2026 AI-coding literature:
- Files under ~500 LOC ideally, under ~800 acceptably. ([CONTESTED — no single authority]; the implicit rationale is fitting a module in a single agent context window pass + comprehension cost.)
- `utils.py` style files: under ~200 LOC or split. ([Lehtinen, Hitchhiker's Guide])
- A 1000+ LOC file should be a yellow flag, 2000+ a red flag.

### Import-graph shape

- **Layered/feature-package with enforced direction** — Kraken's `clients` → `territories` → `core` model. Tools: Import-Linter, Tach. ([Kraken EuroPython 2024])
- **Vertical-slice / feature-owned imports** — Each feature owns its API endpoint + business logic + data access. *"An AI agent can understand it, change it, and test it within a manageable context window."* ([Mike Mason 2026](https://mikemason.ca/writing/ai-coding-agents-jan-2026/) — cited via search; URL fetched on date).
- **Avoid circular imports** — caught by Tach / Import-Linter. ([CONSENSUS])

### Docstring discipline

- NumPy/numpydoc style for scientific Python ([pandas AGENTS.md]).
- Modern: docstrings double as agent-readable interface descriptions; type hints close the gap.
- pyOpenSci requires public-API docstrings for peer review.

### What hurts AI

From [propelcode 2025] and [Nitin Gavhane 2026]:
- "Context rot" — 65% of devs report missing context during refactor when codebase is fragmented across repos.
- Multi-repo fragmentation (limits cross-component understanding).
- Layered architecture in monoliths (agent edits cascade across layers).
- No `AGENTS.md` / `CLAUDE.md` — agent starts from zero context every session.

### What's contested

- File-size hard limits — no authority.
- Whether per-feature mini-READMEs are worth the maintenance cost vs a single CLAUDE.md. ([CONTESTED])
- Whether to commit per-developer CLAUDE.local.md → universal "no, gitignore it" position. ([CONSENSUS])

---

## 7. Special considerations for Qt+VTK+PyVista desktop apps

Reference family: napari, Spyder, ParaView, PyVista.

### What this family does well that small-team apps should borrow

1. **Renderer-vs-domain separation enforced by directory.** Napari's `_vispy/` keeps render backend swappable. PyVista's `core/` vs `plotting/` split is the same idea. ParaView's `Remoting/` and `VTKExtensions/` factor out where VTK-specific code lives. **Pattern for AVC:** `avcs/_pyvista/` (or `avcs/render/`) for everything that touches VTK/PyVista; pure domain (variety math, cross-section algorithms) in `avcs/varieties/` and `avcs/cross_section/` with no VTK imports.

2. **Qt subpackage marked private with underscore (`_qt/`).** Napari's pattern. Says "the Qt parts are not contracts to external callers" while still being a coherent module. **Pattern for AVC:** `avcs/_qt/` (panels, dialogs, custom widgets) or `avcs/ui/` if you prefer public.

3. **`plugins/` subpackage when extensibility is even slightly anticipated.** Napari, Spyder, ParaView all have one. **Pattern for AVC:** probably premature, but reserve the name — don't put a `plugin.py` in `utils/` today and have to rename later.

4. **`experimental/` or `incubator/` namespace for in-flux code.** Napari `experimental/`, ParaView `Incubator/`. Tells humans *and* agents "expect this to move." **Pattern for AVC:** useful if you build features by promoting them from a sandbox.

5. **`resources/` for shaders, icons, locale, fonts.** Spyder splits `fonts/`, `images/`, `locale/`. Napari uses `resources/`. **Pattern for AVC:** `avcs/resources/` for any bundled non-code asset.

6. **`examples/` at the root.** Doubles as user-facing demo and integration test seed. PyVista's is exemplary.

### What naturally tends to go monolithic in this family

Every one of these projects has, at some point, suffered:

1. **Giant generator/model modules.** A single `varieties.py` that grows to 1000+ LOC because each new variety adds a function. **Recognize by:** file growth log, lots of similar functions with slightly different parameter sets. **Fix:** package-by-feature — `varieties/sextic.py`, `varieties/clebsch.py`, each ~100 LOC, with a thin `varieties/__init__.py` registry.

2. **Panel files that grow 500+ LOC** as widgets accumulate, signals are wired in-place, validation logic creeps in. (AVC's `parameter_grid_panel.py`, `view_panel.py`, `appearance_panel.py` are at risk if not already there.) **Recognize by:** scrolling fatigue, multiple distinct UI sections in one file. **Fix:** split per-section into `avcs/_qt/parameters/grid.py`, `avcs/_qt/parameters/sliders.py`, etc.; or extract pure-logic helpers out of the panel into `avcs/parameters/`.

3. **Render-worker code that becomes the bus for everything.** Anything called `render_worker.py` tends to grow because every feature needs it. **Recognize by:** import count, signal/slot count. **Fix:** keep the worker thin (transport + lifecycle); push computation into `avcs/render/` modules; push state into a model class.

4. **Style / theme / appearance modules entangled with widget construction.** Spyder's `config/` and napari's `settings/` give a precedent for splitting. **Recognize by:** color literals in widget code, repeated stylesheet strings. **Fix:** `avcs/_qt/styles.py` or `avcs/resources/styles/` separate from panels.

5. **A single `app.py` that does init, window assembly, signal wiring, menu construction, file dialogs.** Napari splits `window.py`, `viewer.py`, `view_layers.py`. Spyder has `app/` as a *subpackage*. **Recognize by:** `app.py` over 300 LOC. **Fix:** factor into `avcs/app/main_window.py`, `avcs/app/launcher.py`, etc.

### Things specific to AVC's stack to be careful of

- **VTK is import-heavy.** Lazy loading (SPEC 1) is worth more than for a pure-Python lib. Don't `import pyvista` at module top-level in modules that might be imported during tests of unrelated subsystems.
- **Threading is non-negotiable.** PyQt + render thread + worker thread — keep the boundary explicit. A `threading/` or `concurrency/` subpackage is justified once you have more than one worker pattern.
- **Numpy arrays as the lingua franca.** SPEC-style "use standard data types": cross-section math should return numpy arrays / dataclasses, not PyVista objects, so the math is testable without VTK initialized.

---

## 8. Honest assessment — where the literature is contradictory or unsettled

1. **src vs flat for *applications*.** [CONTESTED] PyPA, pyOpenSci, ionel push src for libraries. uv defaults to flat. Pandas, scipy, django are all flat at their scale. Cookiecutter Data Science is flat. The honest answer: src is *better-defended for libraries shipped to PyPI*; for an in-house desktop app, flat-with-package is acceptable and removes one install-step from contributor onboarding. The repository-architect should *flag* this as a deliberate choice rather than enforce one.

2. **Tests inside vs outside the package.** [CONTESTED] pyOpenSci says outside (smaller wheel). Pandas, spyder, scipy all put tests inside. Reasonable rule: outside by default; inside only if you have a stated reason (e.g. tests are shipped for user-level diagnosis).

3. **`utils/` as a subpackage with subdirectories** (Django) vs **`utils/` is always a smell** (Lehtinen, most modern voices). [CONTESTED] Pragmatic synthesis: a `utils/` *subpackage* with named subdirs (`utils/parsing.py`, `utils/timing.py`) is OK; a single `utils.py` *file* is a smell once it crosses ~200 LOC or covers >2 domains.

4. **Two-deep nesting limit.** [OPINION but well-established] Software Carpentry, Python stdlib convention. Some large projects (scipy's `scipy/linalg/lapack/`) violate it for good reason. Treat as a guideline, not a rule.

5. **CLAUDE.md size cap.** [OPINION, fast-moving] HumanLayer says <300 lines, ideally <60. Data-science-collective Medium says <300 with @imports, <100 ideal. No formal source. The 300-line ceiling is empirically holding as the upper bound across 2025/2026 best-practice writing.

6. **AGENTS.md vs CLAUDE.md.** [CONSENSUS that both have a place, CONTESTED on which to prefer]. AGENTS.md is the cross-tool standard (Linux Foundation, 60k+ repos, 20+ tools). CLAUDE.md is Claude-Code-specific and more powerful (it has `@imports`, hierarchical loading, local override). Pragma: AGENTS.md for universality; CLAUDE.md for Claude-specific extras; symlink one to the other to avoid drift, or have CLAUDE.md `@import AGENTS.md`.

7. **Lazy loading (SPEC 1).** [CONSENSUS in scientific Python, CONTESTED elsewhere] — has real costs (debugger / IDE confusion, harder static analysis). Only worth it for heavy deps.

8. **Whether a top-level `src/` is needed for an *app* like AVC.** I count this as #1 above, but worth restating: there is no authoritative source telling a Python desktop app whether to use `src/avcs/` or `avcs/` at root. Both are defensible.

---

## 9. File-by-file evaluator checklist (the operational deliverable)

A repository-architect could run this against AVC or any peer project. Each item is binary or trivially measurable. Ordered roughly by importance.

### Top-level files

1. **README.md present at root?** ([CONSENSUS, all sources])
2. **LICENSE present at root?** ([CONSENSUS])
3. **CHANGELOG.md present at root (Keep-a-Changelog style)?** ([pyOpenSci])
4. **CODE_OF_CONDUCT.md present at root?** ([pyOpenSci, optional for solo projects])
5. **CONTRIBUTING.md present at root?** ([pyOpenSci, scales with team size])
6. **pyproject.toml present at root?** ([PyPA, universal in 2026])
7. **AGENTS.md present at root?** ([agents.md spec, 60k+ adopting repos])
8. **CLAUDE.md present at root (or symlinked to AGENTS.md)?** ([HumanLayer, deployhq])
9. **No `setup.py` unless there's a stated reason** (pyproject.toml is canonical in 2026). [CONSENSUS]
10. **Top-level file count under 20** (excluding directories). ([OPINION — modern trend])

### Package layout

11. **Importable code under a *named package*** (either `src/<pkg>/` or `<pkg>/` at root) rather than loose `.py` files at root. ([PyPA, pyOpenSci, all references])
12. **No `utils.py` file over 200 LOC OR no `utils.py` *file* at all (a `utils/` *package* is acceptable).** ([Lehtinen, Hitchhiker's Guide])
13. **No directory more than 2 levels deep under the package root** (e.g. `pkg/a/b/file.py` OK; `pkg/a/b/c/file.py` is a yellow flag). ([Software Carpentry])
14. **Module names lowercase with underscores, no hyphens.** ([Software Carpentry, Hitchhiker's Guide])
15. **Subpackages reflect *domain* or *role*, not architectural layer** (e.g. `varieties/`, `render/`, not `controllers/`, `services/`). ([Sahibinden Tech, Kraken EuroPython])
16. **No `from foo import *` anywhere in the package.** ([Hitchhiker's Guide, quantifiedcode anti-patterns])
17. **No file in the package over ~800 LOC** (yellow at 500, red at 800). ([CONTESTED but converging informal practice])

### Tests / docs / examples

18. **`tests/` directory exists as a sibling of the package (or inside if there's a stated reason).** ([pyOpenSci])
19. **`docs/` directory exists at root for projects with > ~5 contributors or > 1k LOC.** ([pyOpenSci, Scientific Python])
20. **`examples/` directory exists for any project with a UI or visible output.** ([PyVista, napari precedent])

### AI-friendliness

21. **AGENTS.md (or CLAUDE.md) under 300 lines.** ([HumanLayer])
22. **CLAUDE.md doesn't contain lint rules a linter could enforce.** ([HumanLayer])
23. **No directory or file named `temp/`, `tmp/`, `misc/`, `stuff/`, `old/`, `backup/` in version control.** ([OPINION — common-sense; emerges from quantifiedcode patterns])
24. **Framework-adapter code lives in named subpackages** (e.g. `_qt/`, `_vispy/`, `_pyvista/`) — not interleaved with domain logic. ([napari precedent])
25. **`.gitignore` covers `__pycache__/`, `.pytest_cache/`, `*.pyc`, build artifacts, IDE files.** ([CONSENSUS])

### Bonus diagnostics worth running

26. **Import-graph has no cycles** (run `tach check` or `import-linter`). ([Kraken, scipy])
27. **`python -c "import setup"` fails** (means src layout is working, or flat layout has no `setup.py`). ([ionelmc, PyPA])
28. **Every top-level subpackage has a one-paragraph docstring in its `__init__.py`.** ([SPEC-ish convention, pandas, scipy])

---

## Source citations (consolidated, accessed 2026-05-23)

### Tier 1 — Python packaging guidance
- Hitchhiker's Guide to Python — structure: <https://docs.python-guide.org/writing/structure/>
- pyOpenSci package structure: <https://www.pyopensci.org/python-package-guide/package-structure-code/python-package-structure.html>
- PyPA src vs flat: <https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/>
- Scientific Python Development Guide: <https://learn.scientific-python.org/development/>
- Scientific Python SPECs: <https://scientific-python.org/specs/>
- Cookiecutter Data Science v2: <https://cookiecutter-data-science.drivendata.org/>
- Ionel — packaging a Python library (src): <https://blog.ionelmc.ro/2014/05/25/python-packaging/>
- jcheng — src vs flat 2024: <https://www.jcheng.org/post/python-and-the-src-vs-flat-layout-debate/>
- lawwu TIL src vs flat (2025-03-18): <https://lawwu.github.io/til/posts/2025-03-18-flat-vs-src-layouts/index.html>

### Tier 2 — reference repositories
- napari: <https://github.com/napari/napari>
- PyVista: <https://github.com/pyvista/pyvista>
- Spyder: <https://github.com/spyder-ide/spyder>
- pandas: <https://github.com/pandas-dev/pandas> · AGENTS.md: <https://github.com/pandas-dev/pandas/blob/main/AGENTS.md>
- SciPy: <https://github.com/scipy/scipy>
- Django: <https://github.com/django/django>
- OpenSSL: <https://github.com/openssl/openssl>
- Kubernetes: <https://github.com/kubernetes/kubernetes> · AGENTS.md: <https://github.com/kubernetes/kubernetes/blob/master/AGENTS.md>
- ParaView: <https://gitlab.kitware.com/paraview/paraview> (mirror: <https://github.com/Kitware/ParaView>)

### Tier 3 — modular architecture & AI-friendly codebases
- Kraken Technologies — large Python monolith: <https://blog.europython.eu/kraken-technologies-how-we-organize-our-very-large-pythonmonolith/>
- Sahibinden Tech — package by layer vs feature: <https://medium.com/sahibinden-technology/package-by-layer-vs-package-by-feature-7e89cde2ae3a>
- agents.md spec: <https://agents.md/>
- HumanLayer — writing a good CLAUDE.md: <https://www.humanlayer.dev/blog/writing-a-good-claude-md>
- Complete guide to AI agent memory files: <https://medium.com/data-science-collective/the-complete-guide-to-ai-agent-memory-files-claude-md-agents-md-and-beyond-49ea0df5c5a9>
- Structuring codebases for AI tools 2025 (Propel Code): <https://www.propelcode.ai/blog/structuring-codebases-for-ai-tools-2025-guide>
- DeployHQ — AI coding config files guide: <https://www.deployhq.com/blog/ai-coding-config-files-guide>
- Nitin Gavhane — AI coding agents and architecture (2026): <https://nitingavhane.medium.com/ai-coding-agents-are-hitting-a-wall-and-the-wall-is-your-architecture-a57ec11d20ce>
- vld-bc — Claude Code best practices: <https://vld-bc.com/blog/cli-agents-part2-claude-code-best-practices>

### Tier 4 — anti-patterns & heuristics
- Matti Lehtinen — Dunghill anti-pattern: <https://mattilehtinen.com/articles/dunghill-anti-pattern-why-utility-classes-and-modules-smell/>
- Software Carpentry — structuring Python (two-deep heuristic): <https://intermediate-and-advanced-software-carpentry.readthedocs.io/en/latest/structuring-python.html>
- The Little Book of Python Anti-Patterns: <https://docs.quantifiedcode.com/python-anti-patterns/>

### Could not fetch / unverified
- `https://learn.scientific-python.org/development/guides/repo/` — 404 at fetch time (2026-05-23). [UNVERIFIED] for any specific claim attributed.
- `https://scientific-python.github.io/repo-review/` — page rendered as "Loading…"; only category list is well-attested. [UNVERIFIED] for individual check IDs.
- `https://gitlab.kitware.com/paraview/paraview` — 403 Access Denied at fetch time; ParaView tree pulled from the github.com/Kitware/ParaView mirror via `gh api`.
- Mark Seemann package-by-feature direct article — gist URL not found; argument is well-cross-referenced in the Sahibinden Tech and Felix Njenga pieces.
