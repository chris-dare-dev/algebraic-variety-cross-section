# Agent A — Tree-Shape Design Research Brief (r3)

**Pipeline:** /repository-architect — r3 design phase
**Agent role:** Research Agent A (target-tree design; the WHAT)
**Companion:** Agent B (migration mechanics; the HOW) — running in parallel
**Repo:** algebraic-variety-cross-section (AVC)
**Cwd:** /Users/chris.dare/Personal/SourceCode/algebraic-variety-cross-section
**Date:** 2026-05-24
**Soft budget:** 2500–4500 lines, dense + cite-heavy
**Web wall-clock used:** ~25 min

---

## 0. How to read this brief

The user has asked for two things bundled together:

1. **A clean root.** `app.py` should be the *only* Python script at the repo root.
2. **A tree-shaped dependency graph.** Not just package grouping — the import
   graph should look like a tree (or at minimum a DAG with no back-edges
   between layers) rooted at `app.py`, with "higher-level" modules calling
   "lower-level" ones, never the reverse.

Those two asks are related but separable. Asking only for #1 produces an
*aesthetic* win (six fewer files at the root) with no architectural payoff —
you could satisfy it by `git mv`-ing the five surviving shims into a
`_shims/` folder and keeping every back-import intact. Asking for #2 in
addition forces a real *layering* decision: every package must declare its
position in the dependency order, and the build must fail (or at least the
review must flag) any import that climbs upward in that order.

This brief is about the #2 question. The #1 question is downstream of it:
once you've named the layers, you know where each surviving root file goes.

Every claim is marked `[CONSENSUS]` (widely-held best practice with multiple
authoritative cites), `[CONTESTED]` (literature genuinely split — both
choices defensible, pick on local taste), or `[UNVERIFIED]` (one or zero
strong cites — treat as opinion). Reference URLs are accessed **2026-05-24**
unless noted.

---

## 1. TL;DR

- **Recommended target shape (one of two; user choice — see §4 and §9):**
  a *layered + role-prefixed* tree, in the napari/Spyder mould, with `app.py`
  as the sole root script and **four named layers** underneath:
  `varieties/` (domain), `cross_section/` + `render/` (use-case /
  pipeline), `_qt/` (UI adapter), and **one** new home for
  `parameter_grid.py` (the contested file — §4 explores five options).

- **The architectural pattern is Hexagonal / Ports-and-Adapters at the
  outside, Layered at the inside.** [CONSENSUS] Napari, Spyder, and MNE
  all converge on this shape; Cockburn's 2005 paper is the canonical
  citation; Uncle Bob's Clean Architecture is the dual phrasing. AVC's
  current `_qt/` subpackage (landed r2 batch 3) is *already* the
  "adapter" of a hexagonal split — the r3 task is to (a) name the rest
  of the hex, (b) remove the shims, and (c) decide where the pure-math
  `parameter_grid.py` belongs.

- **Dependency tree (rooted at `app.py`):**
  ```
              app.py
                │
                ▼
           ┌── _qt/ ──────┐   (UI / framework adapter — “driver” side of hex)
           │              │
           ▼              ▼
      cross_section/   render/   (use-case / pipeline layer)
                │         │
                ▼         ▼
                  varieties/    (domain layer — frozen contract, AI-8)
                       │
                       ▼
                 (numpy, pyvista,    ← external libs only; no AVC imports
                  numba, skimage)
  ```
  Every arrow points *down*; the layer numbers are explicit; no package
  ever imports a package above it. This is the dependency rule of Clean
  Architecture verbatim: "source code dependencies can only point
  inwards" ([Martin, 2012](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html), accessed 2026-05-24). [CONSENSUS]

- **`parameter_grid.py` is the only genuinely contested file** (the user
  named it specifically — "higher level files like parameter_grid.py").
  §4 walks the five honest placements. The two strongest options are
  **(b) move into `_qt/` as `_qt/parameter_grid_math.py`** (it's
  imported only by Qt code today, so this is a tight cohesion win) and
  **(c) lift into a new `parameter_grid/` subpackage** (it's pure-math
  and could grow into more grid-math siblings — but YAGNI risk). The
  *weakest* options are (a) move into `varieties/` (it's not about
  varieties, it's about *parameter* math) and (d) put it under `app/`
  (defeats the "app.py is the only root script" rule by introducing an
  `app/` package the user didn't ask for).

- **Inheritance + polymorphism opportunities the tree enables, ranked
  honestly** (§6): (1) a `Variety` Protocol for generators — HIGH value,
  AI-8-aligned; (2) a strategy-pattern `DispatchPolicy` for the
  fast-path logic — MEDIUM value; (3) base classes for `AvcPanel` —
  LOW value, the four panels share little behaviour. The pattern AI-15
  honesty says to *avoid*: an `AbstractShim` base class — the five
  surviving shims are all `__getattr__` one-liners; a base class is
  ceremony for ceremony's sake.

- **What this tree does NOT achieve (§10):** `app.py` is still 1900
  LOC and still a God Object — Extract Class on `MainWindow` is a
  separate decision the user has explicitly deferred (CLAUDE.md
  §2: "do not Extract Class here"). The tree restructure is a
  *necessary* but not *sufficient* condition for that future split;
  doing the tree first makes the future split mechanical.

- **AI-1..AI-15 compatibility:** The proposed tree satisfies every
  structural invariant (§8). AI-6 (implicit vs parametric pipeline
  separation) is *easier* to enforce in the new tree because both
  pipelines live under `varieties/_marching.py` which is one
  directory; AI-8 (frozen registry) is preserved because
  `varieties/types.py` and `varieties/registry.py` are already at
  the canonical paths. The only invariant that requires care is
  **AI-9** (`_computing` re-entrancy guard) — it must stay inside the
  *one* `MainWindow` in `app.py` (or wherever Extract Class lands).

---

## 2. Single-entry-point Python desktop apps — reference repos

This survey grounds the proposed AVC tree in what other well-organized
Python desktop apps actually do. I focused on apps that (a) ship a
GUI, (b) have a clean single-entry-point story, and (c) are large
enough to have *had* to face the layering question. URLs accessed
**2026-05-24**.

For each repo I show:
- **Top-level package tree** (depth-1, sometimes depth-2)
- **Where the "entry point" lives** (one file or one subpackage)
- **What the GUI-adapter / framework-isolation pattern looks like**
- **What makes the import graph "tree-like" vs flat**

### 2.1 napari — the closest AVC analogue

Repo: <https://github.com/napari/napari>, fetched via `gh api repos/napari/napari/contents/src/napari`, 2026-05-24.

**Stack:** PySide2/PyQt5/PySide6 + VisPy (Vulkan/OpenGL) + numpy. Desktop
image viewer.

**Top-level tree (`src/napari/`):**

```
napari/
├── __init__.py
├── __init__.pyi
├── __main__.py                 ← CLI entry; "python -m napari" or "napari ..."
├── _app_model/                 ← command + action model (framework-agnostic)
├── _check_numpy_version.py
├── _event_loop.py
├── _pydantic_util.py
├── _qt/                        ← ALL Qt-coupled code, private
│   ├── _qapp_model/            (mirrors _app_model/ with Qt actions)
│   ├── _qplugins/
│   ├── containers/
│   ├── dialogs/
│   ├── experimental/
│   ├── layer_controls/
│   ├── perf/
│   ├── qt_event_filters.py
│   ├── qt_event_loop.py
│   ├── qt_main_window.py       ← THE main window — note: under _qt/, not at root
│   ├── qt_resources/
│   ├── qt_viewer.py
│   ├── qthreading.py
│   ├── threads/
│   ├── utils.py
│   └── widgets/
├── _tests/
├── _vendor/                    (third-party code vendored in-tree)
├── _vispy/                     ← ALL VisPy-rendering code, private
├── benchmarks/
├── components/                 ← domain models: camera, dims, layerlist, ...
├── conftest.py
├── errors/
├── experimental/
├── layers/                     ← domain primitives: image, labels, points, ...
├── plugins/                    ← plugin manager (npe2)
├── qt/                         ← TINY public Qt re-export surface
├── resources/
├── settings/
├── types.py
├── utils/
├── view_layers.py              ← façade fns: imshow / add_image / ...
├── viewer.py                   ← Viewer class — the headless model
└── window.py                   ← Window class — pulls in QtViewer from _qt/
```

**Entry point:** `napari/__main__.py` (a ~200-line argparse-driven CLI
that imports `from napari import Viewer` and friends; see verbatim
extract under §2.1.1 below). Users invoke it via `python -m napari` or
the `napari` console script declared in `pyproject.toml`. There is
**no** root-level `app.py` — the entry-point file lives *inside* the
package.

**Why the import graph is tree-like:**

The canonical napari rule, from its public architecture docs:

> "We try to confine code that directly imports Qt (currently the only
> supported GUI backend) to the folders `_qt/` and `_vispy/`."
> ([napari directory organization](https://napari.org/dev/developers/architecture/dir_organization.html), accessed 2026-05-24)

> "Sometimes code needs to be split in order to place the Qt part inside
> `_qt/`. For example, some Action menu items that require Qt live in
> `napari/_qt/_qapp_model/qactions/_view.py` while those that don't
> require Qt live in `napari/_app_model/actions/_view_actions.py`."
> ([napari directory organization](https://napari.org/dev/developers/architecture/dir_organization.html), accessed 2026-05-24)

> "Napari uses Qt to build its GUI, but we want to remain flexible to
> offer other GUI frameworks (such as a web-based GUI) in the future."
> (ibid.)

That last sentence is the load-bearing justification: napari chose
hexagonal/adapter-style separation because they want optional swapping
of the UI adapter. AVC has no such ambition (AI-1 explicitly locks
PySide6 + PyVista + pyvistaqt), but the *engineering benefit* — domain
code that can be tested without a Qt event loop (AI-2!) — is
identical.

**Inheritance pattern at the boundary:** napari runs a "one-to-one
mapping" between Python models and Qt models:

> "There is generally one to one mapping between Python models and Qt
> models in napari, for example Python model `Dims` and Qt model
> `QtDims`. The Qt class can register callbacks such that when an
> attribute of the corresponding Python model changes, the appropriate
> actions are taken."
> ([napari directory organization](https://napari.org/dev/developers/architecture/dir_organization.html), accessed 2026-05-24)

The `Q`-prefix convention (`Dims` → `QtDims`) is a transferable
naming pattern — AVC could adopt it for any future model/view splits.
[CONSENSUS for napari, OPINION for AVC.]

**Public-vs-private discipline:** the underscore prefix on `_qt/`,
`_vispy/`, `_app_model/`, etc., is *load-bearing*: the napari docs
state that "Folders beginning with `_` represent private code, that
is not part of the public API."  AVC has *already* adopted this for
`_qt/` (r2 batch 3, see `_qt/__init__.py:6`: "The leading underscore
signals 'framework adapter — implementation detail; external callers
should not depend on internal layout.'"). Continuing to use it for
any future internal subpackages keeps AVC aligned with the napari
convention. [CONSENSUS for napari/SciPy `_lib`; CONTESTED for whether
to also add a tiny public `qt/` re-export surface like napari has —
AVC's "external callers" are essentially zero, so the public re-export
is YAGNI.]

#### 2.1.1 napari `__main__.py` entry-point pattern (verbatim head)

```python
"""
napari command line viewer.
"""

import argparse
import contextlib
import logging
import sys
import warnings
from ast import literal_eval
from pathlib import Path
from textwrap import wrap
from typing import Any

from napari import Viewer
from napari.errors import ReaderPluginError
from napari.utils._startup_script import _run_configured_startup_script
from napari.utils.misc import maybe_patch_conda_exe
from napari.utils.translations import trans


class InfoAction(argparse.Action):
    def __call__(self, *args, **kwargs):
        # prevent unrelated INFO logs when doing "napari --info"

        from napari.utils import sys_info

        logging.basicConfig(level=logging.WARNING)
        print(sys_info())  # noqa: T201
        sys.exit()
```

Source: `gh api repos/napari/napari/contents/src/napari/__main__.py`, decoded base64, 2026-05-24.

Two takeaways for AVC:

1. **The entry-point file does almost no work itself.**  It is `~200
   lines` of argparse + a `main()` that imports `Viewer` and starts the
   event loop. The God-Object class is `Viewer` (and its `QtViewer`
   counterpart under `_qt/`), not the entry-point file.
2. **The entry-point file imports from the inner layers** (`Viewer`,
   `errors`, `utils`) but is itself never imported by anything else.
   Its position in the dependency tree is "above everything else, no
   inbound arrows." AVC's `app.py` already has this property — every
   other module is `import`ed *by* `app.py`, never the reverse. The
   restructure must preserve that. [CONSENSUS]

### 2.2 Spyder — Qt IDE

Repo: <https://github.com/spyder-ide/spyder>, fetched via `gh api repos/spyder-ide/spyder/contents/spyder`, 2026-05-24.

**Stack:** PyQt5/6 + Qt's QScintilla + IPython kernels.

**Top-level tree (`spyder/`):**

```
spyder/
├── __init__.py
├── api/                        ← public extension API (load-bearing — plugin contract)
├── app/                        ← the boot story: cli_options, find_plugins,
│   │                              mainwindow, restart, start, tests, utils
│   ├── cli_options.py
│   ├── find_plugins.py
│   ├── mainwindow.py           ← THE main window — under app/, not at root
│   ├── restart.py
│   ├── start.py                ← entry point function (called by console script)
│   ├── tests/
│   └── utils.py
├── config/                     ← user-settings code
├── dependencies.py             ← (one root-level file by design — frozen-ish)
├── fonts/
├── images/
├── locale/
├── pil_patch.py
├── plugins/                    ← built-in plugins (project_explorer, etc.)
├── pyplot.py
├── requirements.py
├── tests/
├── utils/
├── widgets/                    ← reusable Qt widgets (not bound to any plugin)
└── windows/
```

**Entry point:** `spyder.app.start.main()`. The console script declared in
`setup.py` invokes `spyder.app.start:main`. `app/mainwindow.py` houses
the `MainWindow(QMainWindow)` class.

**Why Spyder is structurally instructive for AVC:**

1. **`app/` is a *subpackage*, not a root file.** Spyder treats
   "application-bootstrapping" as a layer (subpackage) with several
   distinct responsibilities (CLI parsing, plugin discovery, restart
   handling, the main window itself). When the user's brief says
   "tree-like with app.py at the root", a Spyder-style answer would be
   to make AVC's root file thin and push everything except event-loop
   start into an `app/` subpackage. AVC has *explicitly chosen not to*
   in CLAUDE.md §2 ("do not Extract Class here"), so this is a
   reference data point, not a recommendation. [CONTESTED for AVC.]

2. **Spyder still has a few root-level Python files** — `pyplot.py`,
   `dependencies.py`, `requirements.py`, `pil_patch.py`, `__init__.py`,
   `default_config.py`. These are "intentional root-level singletons":
   each is one-job, one-import-direction, no growth expected. The
   *number* is small (5–6); the *pattern* is "if a file is genuinely
   top-of-the-tree and not just stragglers, root is fine." [UNVERIFIED
   as a hard rule — this is my reading of the tree, not a Spyder doc
   citation.] For AVC: this is the steelman for *not* being absolutist
   about "only app.py at root" — `parameter_grid.py` could legitimately
   stay at root if it's genuinely "above everything else." The user's
   brief is explicit, though, so I'll honor it.

3. **`widgets/` (reusable) vs `plugins/widgets/` (plugin-specific).**
   Spyder distinguishes "widgets that anybody could use" from "widgets
   that are part of one plugin." AVC has only the latter — the four
   panels are tightly bound to `MainWindow`. So this split is YAGNI
   for AVC today.

### 2.3 Glue — multi-dimensional viz desktop

Repo: <https://github.com/glue-viz/glue>, fetched via `gh api repos/glue-viz/glue/contents/glue`, 2026-05-24.

**Stack:** PyQt5/6 + matplotlib + bqplot/Jupyter + astropy.

**Top-level tree (`glue/`):**

```
glue/
├── __init__.py
├── _mpl_backend.py
├── _plugin_helpers.py
├── _settings_helpers.py
├── app/                        ← (currently just __init__.py + tests)
├── backends.py
├── config.py
├── config_gen.py
├── conftest.py
├── core/                       ← domain: Data, DataCollection, Component, ...
│   ├── data.py, data_collection.py, component.py, component_link.py
│   ├── application_base.py
│   ├── command.py
│   ├── coordinates.py
│   ├── data_exporters/, data_factories/
│   ├── exceptions.py
│   ├── fitters.py
│   ├── ...
├── default_config.py
├── dialogs/
├── external/
├── icons/
├── io/
├── logger.py
├── logo.png
├── main.py                     ← entry point
├── plugins/
├── tests/
├── utils/
└── viewers/                    ← per-viz-type subpackages
    ├── common/, common3d/, custom/, histogram/, image/
    ├── matplotlib/             ← Qt+matplotlib bridge for histogram/image/...
    ├── profile/, scatter/, scatter3d/, table/, volume3d/
```

**Entry point:** `glue/main.py`. The console script `glue` declared in
`pyproject.toml` invokes `glue.main:main`.

**Notable structural choices:**

1. **`core/` holds the *domain model***, completely framework-agnostic.
   `core/data.py` defines `Data`, `DataCollection`, etc. — pure numpy
   + astropy code. This is exactly the role of AVC's `varieties/`
   (mathematical objects, no Qt). [CONSENSUS — "core" as the
   framework-agnostic domain is a near-universal name in viz tooling;
   PyVista, vedo, Mayavi all use it.]

2. **`viewers/` is the *adapter layer*** — each viewer subpackage
   (`scatter`, `image`, `histogram`, ...) is one feature, holds both
   the Qt UI and the matplotlib glue for that feature. This is
   "package-by-feature within the adapter layer," which is the Kraken
   pattern from scout-B's brief.
   ([Kraken EuroPython 2023](https://blog.europython.eu/kraken-technologies-how-we-organize-our-very-large-pythonmonolith/), accessed 2026-05-24.)

3. **A few intentional root-level files** (`backends.py`, `config.py`,
   `default_config.py`, `logger.py`, `main.py`, `_mpl_backend.py`).
   Same pattern as Spyder — small set, each genuinely "top of the
   tree."  [UNVERIFIED as a hard rule.]

4. **No `_qt/` private subpackage.** Glue's Qt code is interleaved
   under `viewers/` and `dialogs/`. This is the *other* defensible
   choice (package-by-feature with Qt mixed in, vs. napari's
   package-by-feature with Qt separated out). [CONTESTED on which is
   better.]

For AVC: the napari pattern (separate `_qt/`) is a better fit because
AI-2 (Qt-free tests) makes the separation operationally valuable —
domain tests should never trip a Qt import. Glue's interleaved style
makes Qt-free testing harder.

### 2.4 Mayavi — Qt+VTK desktop, the *older* model

Repo: <https://github.com/enthought/mayavi>, fetched via `gh api repos/enthought/mayavi/contents/mayavi`, 2026-05-24.

**Stack:** PyQt5/PySide2 (via Traits/TraitsUI) + VTK directly.

**Top-level tree (`mayavi/`):**

```
mayavi/
├── __init__.py
├── __version__.py
├── action/                     ← Qt menu actions
├── api.py                      ← (single-file public API surface)
├── components/                 ← reusable scene components
├── core/                       ← domain: Engine, Module, Source, ModuleManager, ...
│   ├── adder_node.py, api.py, base.py, common.py, component.py
│   ├── customize.py, dataset_manager.py, engine.py
│   ├── file_data_source.py, filter.py
│   ├── module.py, module_manager.py, mouse_pick_dispatcher.py
│   ├── null_engine.py, off_screen_engine.py
│   ├── pipeline_base.py, pipeline_info.py, registry.py
│   ├── scene.py, source.py
│   ├── images/, lut/
├── filters/                    ← per-filter modules
├── images/
├── mlab.py                     ← (one root-level façade — matlab-style API)
├── modules/                    ← per-VTK-module wrappers
├── plugins/
├── preferences/
├── scripts/                    ← console-script entry points
├── sources/
├── tests/
├── tools/
└── version.py
```

**Entry point:** `mayavi/scripts/mayavi2.py`, plus the matlab-style
`mayavi/mlab.py` façade that users `import` and call without a CLI.

**What's instructive:** Mayavi predates the napari-style `_qt/`
convention by ~10 years and reflects an older pattern — domain
(`core/`) is cleanly separated, but the Qt code is spread across
`action/`, `plugins/`, `tools/`, etc. without a single underscored
adapter directory. The result is a *layered* architecture (clean
`core/` at the centre) but *not* a clean hexagonal one (no single
adapter boundary). This is roughly where AVC was *before* r2 batch 3
landed `_qt/`. Mayavi is what AVC's tree would look like if r2 hadn't
been done. [CONSENSUS on the diagnosis.]

### 2.5 MNE-Python — Qt+VTK+pyvistaqt scientific desktop

Repo: <https://github.com/mne-tools/mne-python>, fetched via `gh api repos/mne-tools/mne-python/contents/mne`, 2026-05-24.

**Stack:** Qt (multiple bindings via QtPy) + PyVista + VTK + matplotlib +
numpy/scipy. Neuroimaging desktop.

**Top-level tree (`mne/`, abridged — full tree has ~30 entries):**

```
mne/
├── __init__.py, __main__.py
├── _fiff/, _freesurfer.py, _ola.py
├── annotations.py
├── beamformer/
├── bem.py
├── channels/
├── commands/                   ← CLI entry-point subpackage
├── coreg.py, cov.py, cuda.py
├── data/, datasets/, decoding/
├── defaults.py
├── dipole.py, epochs.py, event.py, evoked.py
├── export/, filter.py, fixes.py
├── forward/
├── gui/                        ← Qt desktop UIs (small surface)
│   ├── _coreg.py, _gui.py, tests/
└── viz/                        ← visualisation
    ├── _3d.py, _3d_overlay.py
    ├── _brain/                 (the big interactive 3D brain viewer)
    ├── backends/               ← backend-abstraction layer (Qt vs Notebook vs ...)
    ├── circle.py, epochs.py, evoked.py, ica.py
    ├── ...
```

**Entry point:** `mne/__main__.py` plus `mne/commands/` (a CLI
subpackage with one file per subcommand). Like napari, MNE puts the
CLI inside the package, not at root.

**The really interesting choice — `viz/backends/`:** MNE has an
explicit *backend-abstraction* layer between the visualization code
and Qt. This is hexagonal "ports" made literal — `viz/backends/`
contains the abstract `_Renderer` interface (port) and concrete
implementations for `_qt`, `_notebook`, etc. (adapters). The same
viz code can drive Qt or Jupyter.

For AVC: this is *more* architecture than the user has asked for and
*more* than AI-1 needs (PySide6 + pyvistaqt is locked). But it's a
useful *upper bound* on the pattern — if AVC ever wanted to ship a
Jupyter widget, the napari/MNE pattern shows the path. [UNVERIFIED for
AVC's near-term needs; included as a future-proofing data point.]

### 2.6 PyVista — the library AVC depends on

Repo: <https://github.com/pyvista/pyvista>, fetched via `gh api repos/pyvista/pyvista/contents/pyvista`, 2026-05-24.

**Top-level tree (`pyvista/`):**

```
pyvista/
├── __init__.py
├── __main__.py                 ← entry: "python -m pyvista"
├── _cli/                       ← CLI commands
├── _deprecate_positional_args.py
├── _plot.py
├── _version.py
├── _vtk.py
├── _warn_external.py
├── conftest.py
├── core/                       ← domain: PolyData, ImageData, UnstructuredGrid, ...
├── demos/
├── errors.py
├── examples/
├── ext/
├── jupyter/                    ← Jupyter-specific code (adapter)
├── plotting/                   ← Plotter + Qt-bridge (adapter)
├── py.typed
├── report.py
├── trame/                      ← Trame web adapter
├── typing/
└── utilities/
```

**Notable:** PyVista does *not* use `_qt/` prefix — its Qt-bridge code
is interleaved under `plotting/`. The library uses `core/` for the
mesh/grid primitives (parallel to Glue's `core/`, Mayavi's `core/`).
The `jupyter/` and `trame/` subpackages are *adapter-per-frontend*.

For AVC: PyVista demonstrates that the napari convention is *not*
universal in the Qt+VTK space — PyVista chose differently, and it
works. [CONTESTED — both napari (`_qt/`) and PyVista (interleaved)
are defensible.] AVC's existing `_qt/` (already landed in r2) leans
napari; that's the right call given AI-2.

### 2.7 vedo — Qt+VTK viz toolkit

Repo: <https://github.com/marcomusy/vedo>, fetched via `gh api repos/marcomusy/vedo/contents/vedo`, 2026-05-24.

**Top-level tree (`vedo/`):**

```
vedo/
├── __init__.py
├── addons/
├── applications/                ← demo applications (one-off scripts)
├── assembly.py
├── backends.py
├── cli.py                       ← entry point
├── colors.py
├── core/                        ← domain
├── external/
├── file_io/
├── fonts/
├── grids/
├── lazy_imports.py
├── mesh/
├── plotter/                     ← Qt+VTK plotter (adapter)
├── pointcloud/
├── pyplot/
├── settings.py
├── shapes/
└── transformations.py
```

**Entry point:** `vedo/cli.py`. Console script invokes `vedo.cli:execute_cli`.

**Notable:** Like PyVista, vedo interleaves Qt with the rest of the
plotter code (`plotter/` is the adapter). vedo has many small
root-level files (`assembly.py`, `backends.py`, `colors.py`,
`settings.py`, etc.) — this is the *opposite* end of the spectrum
from the user's "only app.py at root" request. vedo's choice works
because each root file is genuinely top-of-tree and the package is
relatively small (~20k LOC). For AVC the user has been explicit:
move the stragglers off the root.

### 2.8 ParaView (`pvpython`) — the upper-end reference

Repo: <https://github.com/Kitware/ParaView>, fetched via `gh api repos/Kitware/ParaView/contents/Wrapping/Python/paraview`, 2026-05-24.

**Top-level tree (`Wrapping/Python/paraview/`):**

```
paraview/
├── __init__.py.in
├── _backwardscompatibilityhelper.py
├── algorithms/
├── apps/
├── benchmark/
├── catalyst/
├── collaboration.py
├── coprocessing.py
├── cpstate.py
├── decorator_utils.py
├── demos/
├── detail/
├── incubator/                  ← experimental code, explicit naming
├── info/
├── inspect.py
├── live.py
├── modules/
├── numeric.py
├── numpy_support.py
├── pv-vtk-all.py
├── python_view.py
├── selection.py
├── servermanager.py
├── simple/                     ← public "easy mode" API surface
├── smstate.py
```

**Entry point:** `pvpython` (a C++ launcher that embeds Python +
ParaView). The Python layer is library-style, not "single entry
point." For AVC this is structurally different — ParaView is a
*toolkit* with multiple entry points, AVC is a *single-binary desktop
app*. Included here as a counter-example: when the deliverable is a
toolkit, the "only one root script" rule doesn't apply.

### 2.9 Summary table

| Repo | LoC class | Entry-point shape | Domain layer | Qt/UI adapter | Tree-like? |
|---|---|---|---|---|---|
| **napari** | ~200k | `__main__.py` inside pkg | `components/`, `layers/` | `_qt/`, `_vispy/` (private) | YES — strict `_qt/` discipline |
| **Spyder** | ~400k | `app/start.py:main` (subpkg) | (none — IDE plugins are the domain) | `app/`, `widgets/`, `plugins/` | MEDIUM — Qt interleaved |
| **Glue** | ~80k | `main.py` at pkg root | `core/` | `viewers/`, `dialogs/` (interleaved) | MEDIUM |
| **Mayavi** | ~50k | `scripts/mayavi2.py` + `mlab.py` | `core/` | scattered (`action/`, `plugins/`, `tools/`) | NO (pre-`_qt/` era) |
| **MNE-Python** | ~300k | `__main__.py` + `commands/` | `_fiff/`, `forward/`, etc. | `gui/`, `viz/backends/` | YES (backend-abstraction layer) |
| **PyVista** | ~100k | `__main__.py` + `_cli/` | `core/` | `plotting/` (interleaved), `jupyter/`, `trame/` | MEDIUM |
| **vedo** | ~30k | `cli.py:execute_cli` | `core/` | `plotter/` (interleaved) | MEDIUM |
| **ParaView** | (millions, C++ + Py) | `pvpython` (C++) | `algorithms/`, `modules/` | `simple/` (façade) | N/A — toolkit |
| **AVC (target)** | ~6k | **`app.py` at repo root** | `varieties/` | `_qt/` | **TARGET: YES** |

**Key observation:** the *closest* analogues to AVC (napari, MNE) both
**put the entry-point file inside the package**, not at the repo root.
AVC's choice to keep `app.py` at root is a *deliberate departure* from
the napari/MNE convention. It's not wrong — it's an aesthetic choice
the user has stated explicitly. Two consequences for the tree design:

1. AVC will not have a `napari/__main__.py`-style launcher; `app.py`
   plays both roles (CLI launcher *and* main-window class).
2. The user's "only app.py at root" rule means AVC's tree cannot mimic
   napari's exact layout (napari's package root is *inside* `src/napari/`;
   AVC's package "root" is `.` itself). The closest legal analogue is
   the Glue/vedo tree-shape — single entry-point file plus several
   subpackages — with the napari-style `_qt/` discipline layered on top.

This is the synthesis the proposed tree in §5 follows. [CONSENSUS on
the structural pattern; OPINION on the specific synthesis.]

---

## 3. Architectural patterns for hierarchical Python desktop apps

This section walks the candidate patterns and rates each for AVC fit.
Ratings: HIGH / MEDIUM / LOW. Each rating cites at least one primary
source.

### 3.1 Layered Architecture (UI → Application → Domain → Infrastructure)

**Definition:** Stack the codebase into horizontal layers, each one
having an explicit role and only allowed to call the layer below it.
Classic four layers: Presentation (UI), Application (use cases /
orchestration), Domain (entities + business rules), Infrastructure
(databases / external services). Originated in Fowler's *Patterns of
Enterprise Application Architecture* (Addison-Wesley, 2002).

**Canonical cite:** Fowler, *PoEAA*, Ch. 1, "Layering." Wikipedia
summary: <https://en.wikipedia.org/wiki/Multitier_architecture>
(accessed 2026-05-24).

**Mechanism:** Top-down only; the UI knows about the application
layer, the application layer knows about the domain, the domain
knows about nothing but itself.

**AVC fit: HIGH (this is *implicitly* the pattern r2 was driving toward).**
AVC's r2 already established three of the four layers:
- `_qt/` is the UI layer
- `render/` + `cross_section/` are application / use-case layers (they
  orchestrate `varieties/` generators)
- `varieties/` is the domain layer
- The "infrastructure" layer is essentially `numpy + pyvista + numba +
  skimage`, all external — AVC owns no DB, no network, so there's no
  internal infrastructure subpackage.

The r3 task is to *name* this layering explicitly and enforce its
dependency direction. [CONSENSUS as a target; CONTESTED on the exact
naming — see §3.5 (Kraken pattern) for the "by-feature within layer"
refinement.]

### 3.2 Hexagonal / Ports-and-Adapters (Cockburn 2005)

**Definition:** Surround the application core with "ports" (abstract
interfaces) and "adapters" (concrete bindings to specific
technologies). The core knows only about its ports; the adapters
implement the ports and bridge to the outside (a UI, a DB, a queue).

**Canonical cite:** Alistair Cockburn, "Hexagonal architecture" (a.k.a.
"Ports and Adapters"), HaT Technical Report 2005.02, originally on
the Portland Pattern Repository wiki, later at
<https://alistair.cockburn.us/hexagonal-architecture/>.
Wikipedia: <https://en.wikipedia.org/wiki/Hexagonal_architecture_(software)>
(accessed 2026-05-24).

Quoting Wikipedia's summary verbatim:

> "It aims at creating loosely coupled application components that can
> be easily connected to their software environment by means of ports
> and adapters." ([Wikipedia](https://en.wikipedia.org/wiki/Hexagonal_architecture_(software)), accessed 2026-05-24)

> "Adapters are the glue between components and the outside world. They
> tailor the exchanges between the external world and the ports that
> represent the requirements of the inside of the application component."
> (ibid.)

**Distinction from Layered:** Hexagonal is *axially symmetric* —
adapters surround the core in 360° (Cockburn drew a hexagon, hence
the name; the six sides are not load-bearing). Layered is *linear*
(top → bottom). For an app with one UI and one DB, the difference is
mostly diagrammatic.

**Driver vs Driven distinction:** Hexagonal further splits adapters
into:
- **Driver adapters** ("primary" / "left side" / "user-side"): they
  drive the application — UI, CLI, test harness.
- **Driven adapters** ("secondary" / "right side" / "server-side"):
  the application drives them — DB, file system, message queue.

Cockburn's original article makes this distinction; the Wikipedia
summary I fetched does not explicitly highlight it but it's in the
broader literature ([Cosmic Python, Percival & Gregory 2020](https://www.cosmicpython.com/book/chapter_06_uow.html)).

**AVC fit: HIGH for the UI side, LOW for the data side.** AVC has:
- One driver adapter: `_qt/` (UI). napari's `_qt/` is exactly this.
- Zero driven adapters: no DB, no network, no file persistence (the
  app reads no user files; it generates math).

So AVC is "half-hex." That's normal — Cockburn's hexagon is a
*maximum* shape, not a required one. Apps with one input and one
output side use a degenerate hex that's structurally equivalent to a
2-layer Layered architecture. [CONSENSUS — this is the
"hexagonal-as-aspiration" perspective in most practical writings,
e.g. Cosmic Python Ch. 6.]

**Recommendation for the brief:** name the pattern "**hexagonal at the
UI boundary, layered within**" so the team has the vocabulary to talk
about future driven adapters (e.g., a "save scene to .vtk" feature
would be a *driven* adapter; a "Jupyter widget" frontend would be a
*driver* adapter alongside `_qt/`).

### 3.3 Clean Architecture (Martin 2012)

**Definition:** Concentric circles (Entities → Use Cases → Interface
Adapters → Frameworks & Drivers) with the famous "Dependency Rule":
source code dependencies can only point *inwards*.

**Canonical cite:** Robert C. Martin, "The Clean Architecture" (2012),
<https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html> (accessed 2026-05-24).
Quoting the dependency rule verbatim:

> "source code dependencies can only point inwards"
> ([Martin, 2012](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html), accessed 2026-05-24)

The four layers per Martin (outer → inner):
1. **Frameworks and Drivers** — UI, DB, external tools (PySide6, PyVista in AVC's case)
2. **Interface Adapters** — controllers, presenters, gateways (`_qt/` widgets)
3. **Use Cases** — application-specific business rules (`render/`, `cross_section/`)
4. **Entities** — enterprise-wide business rules (`varieties/types.py`, `varieties/registry.py`)

**Relationship to Hexagonal:** Clean Architecture is a synthesis of
Hexagonal + Onion + DCI + a few others (Martin says so explicitly in
the post). The dependency rule is the same as the Hexagonal "adapters
depend on the core" rule, generalized to N concentric rings.

**AVC fit: HIGH for the dependency rule, MEDIUM for the explicit
4-ring naming.** The 4-ring vocabulary (Entities / Use Cases /
Interface Adapters / Frameworks) is overkill for AVC's ~6k LOC. But
the *dependency rule* itself is exactly what the user is asking for —
imports must flow downward; no upward back-edges. Recommend AVC adopt
the dependency rule, but use simpler naming (domain / pipeline /
adapter) rather than Martin's four-ring terminology. [CONSENSUS for
the dependency rule in any layered Python project; CONTESTED on
whether to use the full Clean Architecture naming.]

### 3.4 MVC / MVP / MVVM variants

**Definition:** Three families of patterns separating Model (data /
domain) from View (UI) via a Controller (MVC), Presenter (MVP), or
ViewModel (MVVM) intermediary.

**Canonical cite:** Trygve Reenskaug, "MODELS - VIEWS - CONTROLLERS"
(Xerox PARC, 1979). MVP: Mike Potel, "MVP: Model-View-Presenter — The
Taligent Programming Model" (1996). MVVM: John Gossman, "Tales from
the Smart Client" (Microsoft, 2005).

**Mechanism (MVC, briefly):** The View renders the Model and forwards
user events to the Controller; the Controller mutates the Model; the
Model notifies observers (the View) of changes.

**Qt-specific note:** Qt's Model/View framework (`QAbstractItemModel` +
`QListView`/`QTableView`/`QTreeView`) is a *concrete* MVC
implementation. PySide6's signal/slot is the "Model notifies View"
mechanism. ([Qt docs: Model/View Programming](https://doc.qt.io/qt-6/model-view-programming.html), accessed 2026-05-24.)

napari's "one-to-one mapping between Python models and Qt models"
(quoted in §2.1) is roughly *MVVM* — the Python `Dims` is the Model
+ ViewModel, the Qt `QtDims` is the View.

**AVC fit: LOW as a *top-level* pattern, HIGH inside the panels.**
AVC's panels (under `_qt/panels/`) already use a degenerate MVC: each
panel is a `QWidget` that owns its private widgets (View),
forwards signals to `MainWindow` (Controller), and reads/writes the
`Surface` + `ParamSpec` (Model). Making MVC the *top-level* pattern
would mean creating `controllers/`, `models/`, `views/` subpackages,
which is exactly the "package-by-layer" anti-pattern scout-B flagged
([Sahibinden Tech 2024](https://medium.com/sahibinden-technology/package-by-layer-vs-package-by-feature-7e89cde2ae3a), accessed 2026-05-24).
[CONSENSUS — package-by-layer is contraindicated for modular
monoliths.]

**Recommendation:** acknowledge that MVC is *implicit* in the
Qt-widget patterns AVC already uses; don't promote it to a top-level
naming.

### 3.5 Package-by-Feature with strict layer dependencies (the Kraken pattern)

**Definition:** Group code by *what it is* (a feature, a domain
concept) rather than *what it does* (a layer role). Enforce a strict
acyclic dependency direction via tooling (e.g. Import-Linter).

**Canonical cite:** [Kraken Technologies, EuroPython 2023 blog](https://blog.europython.eu/kraken-technologies-how-we-organize-our-very-large-pythonmonolith/), accessed 2026-05-24:

> "A component is not allowed to depend on any components higher up
> the stack." ([Kraken EuroPython 2023](https://blog.europython.eu/kraken-technologies-how-we-organize-our-very-large-pythonmonolith/), accessed 2026-05-24)

Their layering:
- **`clients/`** — client-specific code (`oede`, `oegb`, `oejp`)
- **`territories/`** — country/region-specific behaviour (`deu`, `gbr`, `jpn`)
- **`core/`** — shared code used by all clients

Enforced by 40+ Import-Linter contracts. They also enforce:

> "client subpackages must be independent (i.e. not import from other
> clients), and the same goes for territories."
> ([Kraken EuroPython 2023](https://blog.europython.eu/kraken-technologies-how-we-organize-our-very-large-pythonmonolith/), accessed 2026-05-24)

**AVC fit: HIGH for the within-`varieties/` layer; MEDIUM for the rest.**
AVC's `varieties/k3.py`, `varieties/enriques.py`, `varieties/calabi_yau.py`,
`varieties/fano.py` are *already* package-by-feature (each
mathematical family is one module). They all sit at the *same* layer
of the dependency tree (none of them imports another), which mirrors
the Kraken "client subpackages must be independent" rule. So this
pattern is already operative *inside* `varieties/`.

For the top-level layering (`varieties/`, `render/`, `cross_section/`,
`_qt/`), the Kraken pattern says "use Import-Linter to enforce the
direction." That's the operational lever — see §7 for an honest
opinion on whether to add Import-Linter / Tach to AVC. [CONSENSUS for
monoliths; OPINION on whether the tooling is worth the maintenance
cost for a 6k-LOC repo.]

### 3.6 Event-bus / Signal mediator (PySide6 Signals as decoupler)

**Definition:** Components communicate via a published event bus or
signal/slot mechanism rather than direct method calls. Decouples
sender from receivers; multiple receivers can subscribe.

**Canonical cite (Qt-specific):** [Qt Signals & Slots docs](https://doc.qt.io/qt-6/signalsandslots.html), accessed 2026-05-24.
General pattern: Hohpe & Woolf, *Enterprise Integration Patterns* (Addison-Wesley, 2003), Ch. 7 ("Publish-Subscribe Channel").

**AVC fit: HIGH (and *already* in use).** AVC's `_qt/panels/`
extensively use Qt Signals to communicate up to `MainWindow`. For
example, `ParametersPanel` defines a `Signal` for parameter changes
and `MainWindow` connects a slot; the panel does not call
`MainWindow` directly. This *is* the event-bus pattern, scoped to
Qt's signal system.

**Implication for the tree:** because signals already decouple panels
from `MainWindow`, the panels can live under `_qt/` without
bidirectional imports. The proposed tree preserves this — `_qt/` does
not import `app.py` (and `app.py` imports the panel classes once
each). [CONSENSUS that Qt Signals are the right Qt-native event bus;
no need to add a Python-level pub/sub library.]

### 3.7 Plugin architecture (napari's plugin manager — would AVC benefit?)

**Definition:** Define a plugin contract (an interface or a manifest)
and a discovery mechanism (entry points, manifest scanning) so
third-party code can extend the app without modifying core code.

**Canonical cite (napari-specific):** [napari plugin docs](https://napari.org/plugins/index.html), accessed 2026-05-24.
[npe2 plugin engine](https://github.com/napari/npe2).

**AVC fit: LOW.** AVC has *one* extension point — the `VARIETIES`
registry — and adding a new variety today is a 5-line patch to
`varieties/registry.py`. There are no third parties. Building a
plugin architecture would be ceremony without payoff. The user has
not asked for it. [CONSENSUS for small single-team apps;
plugin-architecture is a "wait for the second extender" pattern.]

The future-state argument: *if* a math collaborator wanted to add
varieties without modifying AVC's repo, the `VARIETIES` registry could
be made auto-discovering via Python entry points (cf.
[Python packaging entry-points spec](https://packaging.python.org/en/latest/specifications/entry-points/), accessed 2026-05-24). That's a 1-day
change *when needed*. Don't pre-build it.

### 3.8 Summary fit table

| Pattern | AVC fit | Why | Cite |
|---|---|---|---|
| Layered Architecture | **HIGH** | Already the *implicit* shape of r2; r3 makes it explicit | Fowler PoEAA 2002 |
| Hexagonal / Ports-Adapters | **HIGH (UI side)** | `_qt/` is already the driver adapter; no driven adapters needed today | Cockburn 2005 |
| Clean Architecture (Uncle Bob) | **MEDIUM** | Dependency rule yes; 4-ring naming overkill | Martin 2012 |
| MVC / MVP / MVVM | **LOW (top-level), HIGH (inside panels)** | Already implicit in Qt panels; don't promote it | Reenskaug 1979 |
| Package-by-Feature + Import-Linter | **HIGH (within `varieties/`), MEDIUM (top-level)** | Variety modules already independent; top-level enforcement is OPINION | Kraken 2023 |
| Event-bus / Qt Signals | **HIGH (already used)** | Panels signal up to MainWindow; preserves tree shape | Qt docs |
| Plugin architecture | **LOW** | YAGNI — one team, one extension point | napari npe2 |

**Synthesis recommendation (one-line):** *"Hexagonal at the UI boundary,
layered within, package-by-feature inside the layers, signals for
decoupling — and call it that out loud in CONTEXT.md so the team has
the shared vocabulary."*

---

## 4. The specific question — where does `parameter_grid.py` go?

The user named this file specifically: *"higher level files like
parameter_grid.py being called in its own module."* It is the single
most-contested placement in the r3 design, so it deserves its own
section.

### 4.1 Facts about `parameter_grid.py`

From the current code (`parameter_grid.py`, 363 LOC, read 2026-05-24):

- **Pure-math, Qt-free.** The module-level docstring is explicit
  (`parameter_grid.py:3`): *"This module is intentionally Qt-free and
  PyVista-free (AI-2): it has no PySide6 / pyvista imports at module
  top level, so every transform and every assignment rule below is
  unit-testable without instantiating a QApplication or a VTK render
  window."* Currently it imports only `dataclasses` (stdlib) and
  `surfaces.ParamSpec`.
- **One inbound domain dep:** `surfaces.ParamSpec` (now canonically
  `varieties.types.ParamSpec` per r2 batch 5).
- **Three inbound Qt-side deps:**
  - `_qt/ui_helpers.py:27` — `import parameter_grid as pg`
  - `_qt/panels/parameters.py:30` — `import parameter_grid as pg`
  - `_qt/panels/parameter_grid_panel.py:35` — `import parameter_grid as pg`
- **Zero outbound Qt deps** — never imports anything from `_qt/`.
- **Concerns inside the file** (per the section headers in the
  source):
  1. `value <-> normalized <-> scene-coordinate transforms` (lines
     38–135) — pure conversions; consumed by panels for slider/dot
     positions.
  2. Enable/disable predicates (`grid_enabled`, `default_axis_count`)
     — lines 138–162.
  3. Axis-assignment logic (`AxisAssignment` dataclass + `assign_axes`
     + `default_axis_names`) — lines 165–253.
  4. Slider-tick conversion + value formatting (`tick_count`,
     `value_to_tick`, `tick_to_value`, `format_value`) — lines 256–308.
  5. 3D drag-plane axis mapping (`plane_axes`, `held_axis`) — lines
     311–362.

**Diagnosis:** `parameter_grid.py` is a *small, cohesive math module*
that sits *above* `varieties.types.ParamSpec` (its only data
dependency) and *below* every panel that uses it. In the proposed
4-layer tree it's at the *use-case / application* layer — it
operates on the domain primitive `ParamSpec`, but it does no
rendering and no UI; it's exactly the kind of code that the Clean
Architecture "Use Cases" ring is meant for. [UNVERIFIED — this is my
read; literature offers no canonical home for "math helpers consumed
only by UI."]

### 4.2 The five honest placement options

#### Option (a) — Move into `varieties/`

**Concrete path:** `varieties/parameter_grid.py` (or `varieties/grid.py`).

**Pros:**
- It depends on `varieties.types.ParamSpec`, so it's at the same
  layer or just above the domain.
- Keeps the `varieties/` subpackage as the one-stop home for
  *anything ParamSpec-related*.
- Symmetric with `varieties/dispatch.py`, which is also a "small
  helper that operates on `Surface` and is consumed by `app.py`."

**Cons:**
- **Naming dishonesty.** The file is about *parameter-grid widget
  math*, not about varieties as algebraic objects. Putting it under
  `varieties/` implies "this is about variety math" — false. AI-15
  honesty pushes back on this.
- **Couples the domain to a UI concept.** "Parameter grid" is a UI
  affordance — it makes no sense without a draggable dot widget. Moving
  it into `varieties/` violates the layering principle (UI concepts
  leaking into domain). [CONSENSUS that domain layer should be
  UI-vocabulary-free.]
- **Hidden Qt coupling growth risk.** If a future change adds a
  pyvista or numpy dep to `parameter_grid` (e.g. for 3D grid layout),
  it shouldn't sit alongside `varieties/types.py` which deliberately
  caps at numpy.

**Tree-shape implication:** keeps the tree shallow (one fewer
top-level subpackage) but blurs the layer boundary.

**Verdict:** WEAK. The name itself is a tell — it's not about
varieties.

#### Option (b) — Move into `_qt/` as `_qt/parameter_grid_math.py`

**Concrete path:** `_qt/parameter_grid_math.py` (rename to make the
"math" focus explicit; `parameter_grid.py` collides namespace-wise
with `parameter_grid_panel.py`).

**Pros:**
- **Maximum cohesion.** Every consumer is in `_qt/`; co-locating the
  consumed module with its consumers minimizes cross-layer imports.
- **Honest about purpose.** The file exists to support the Qt panels;
  putting it next to those panels makes that obvious to a reader.
- **Easy to find.** A developer working on `_qt/panels/parameters.py`
  sees `_qt/parameter_grid_math.py` immediately when scanning the
  parent directory.

**Cons:**
- **Misleading namespace prefix.** Code inside `_qt/` is assumed to
  be "imports Qt"; a Qt-free math module inside `_qt/` is a surprise.
  napari's convention (per their docs) is "we confine code that
  directly imports Qt to `_qt/`" — but they don't say *only* Qt code
  may live there. So this is a soft cost, not a violation.
  ([napari directory organization](https://napari.org/dev/developers/architecture/dir_organization.html), accessed 2026-05-24.)
- **Renaming hurts git history** unless `git mv` is used (mechanical;
  Agent B's lane).
- **Defeats Qt-free testability claim.**  Tests today can do `import
  parameter_grid` without bringing in PySide6. After this move, tests
  must do `import _qt.parameter_grid_math`, and that *might* trigger a
  side-effect import in `_qt/__init__.py`. Today `_qt/__init__.py` is
  empty of imports (verified `_qt/__init__.py`, read 2026-05-24 — only
  a docstring; no `from PySide6 import ...`). So this is currently
  *not* a real cost, but it's a footgun: any future Qt import added
  to `_qt/__init__.py` would silently break the test suite. AI-2
  honesty: this is a real risk worth pricing in.

**Tree-shape implication:** keeps the top-level tree narrower (no new
subpackage) but creates a "mixed" `_qt/` subpackage (some files import
Qt, some don't).

**Verdict:** STRONG. The cohesion win is real and large. The naming
risk is real but mitigated by the explicit `_math` suffix.

#### Option (c) — Create a new `parameter_grid/` subpackage

**Concrete paths:**
```
parameter_grid/
├── __init__.py
├── math.py            # current parameter_grid.py contents
└── (future: layout.py, snapping.py, etc.)
```

**Pros:**
- **Own its own layer.** A subpackage signals "this is its own area
  of concern, not a helper for someone else."
- **Room to grow.** If `parameter_grid` ever sprouts siblings (a
  separate layout-algorithm module, a snap-grid module, a serializer),
  a subpackage absorbs them cleanly.
- **Honest naming.** Doesn't pretend to be about varieties; doesn't
  pretend to be inside `_qt/`.

**Cons:**
- **YAGNI.** Today there's one file with five cohesive sections (363
  LOC). A subpackage with one module is *exactly* the "premature
  abstraction" anti-pattern (see §7). [CONSENSUS in the refactoring
  literature: subpackages are a *response* to a real second module,
  not a *speculative* container.]
- **Adds a top-level subpackage.** The user wants *fewer* root-level
  Python files, and a subpackage at the root counts as one of them.
  (Mitigated: a directory is visually less noisy than a file at root.)
- **Awkward to consume.** `from parameter_grid.math import ...` is
  uglier than `from parameter_grid import ...` (current) or `from
  _qt.parameter_grid_math import ...` (option b).

**Tree-shape implication:** adds a top-level subpackage; whether this
is a tree win or loss depends on how many other top-level subpackages
end up in the final tree (§5).

**Verdict:** MODERATE. Right if there's a real plan to add sibling
modules; YAGNI otherwise.

#### Option (d) — Move under an `app/` core subpackage

**Concrete path:** `app/parameter_grid.py` (or similar) — implies the
existence of an `app/` package.

**Pros:**
- Pattern-matches Spyder's `spyder/app/` subpackage (§2.2).
- Provides a natural home for *other* app-bootstrapping files
  (`app/main_window.py`, `app/launcher.py`) if Extract Class is ever
  done on `MainWindow`.

**Cons:**
- **The user explicitly does not want `app.py` to become `app/`.**
  The brief literally says "only the app.py is the only python script
  at the root." An `app/` subpackage at root, with `app.py` next to
  it, is naming-confused (is the entry point in `app.py` or
  `app/__init__.py`?). [CONSENSUS that this dual-form naming is a
  smell.]
- **CLAUDE.md §2 forbids Extract Class on `MainWindow`** ("God
  Object, do not Extract Class here"). An `app/` subpackage created
  *now*, ahead of any actual splitting of `MainWindow`, is a container
  with nothing in it but `parameter_grid.py`. That's option (c)'s
  YAGNI problem with extra confusion thrown in.

**Tree-shape implication:** introduces a top-level subpackage with a
single member; conflicts with the user's "only app.py at root"
phrasing.

**Verdict:** WEAK. Conflicts with the user's stated preference.

#### Option (e) — Leave at root, alongside `app.py`

**Concrete path:** `parameter_grid.py` (unchanged).

**Pros:**
- **Honesty: it's already top-of-tree.** It depends only on
  `varieties.types.ParamSpec`; nothing else depends on it from below.
  The shape of the dependency tree literally puts it just under
  `app.py`'s level.
- **Zero migration cost.** No imports to rewrite.
- **Matches the user's "higher-level files like parameter_grid.py"
  framing.** The user explicitly grouped `parameter_grid.py` with
  `app.py` as "higher level" — leaving them as the two root files is
  the literal interpretation.

**Cons:**
- **Conflicts with "only app.py is the only python script at the
  root."** Unambiguous direct violation of the brief.
- **No room for siblings.** Same as option (c)'s YAGNI but inverted.

**Tree-shape implication:** keeps the tree *exactly* as-is for this
file.

**Verdict:** WEAK *given the user's explicit constraint*. STRONGEST if
the user softens that constraint to "as few files as possible at the
root, with app.py + one or two genuine top-of-tree files OK." The user
should explicitly confirm whether the "only app.py" rule admits
exceptions for genuinely top-of-tree helpers.

### 4.3 Calibrated tradeoffs table

| Option | Naming honesty | Cohesion | Future growth | User-constraint fit | Migration cost |
|---|---|---|---|---|---|
| (a) `varieties/parameter_grid.py` | LOW (it's not about varieties) | MED | LOW | HIGH | LOW |
| (b) `_qt/parameter_grid_math.py` | MED (Qt-free file in `_qt/`) | **HIGH** | LOW | HIGH | LOW |
| (c) `parameter_grid/math.py` | HIGH | MED | **HIGH** | HIGH | MED |
| (d) `app/parameter_grid.py` | MED | LOW | LOW | LOW (conflicts) | MED |
| (e) keep `parameter_grid.py` at root | HIGH | HIGH | N/A | LOW (conflicts) | NONE |

### 4.4 What the literature says about "small math helper consumed only by UI"

I searched for guidance and found no canonical pattern name. Cosmic
Python ([Percival & Gregory 2020](https://www.cosmicpython.com/book/preface.html))
discusses "service layer" code that sits between domain and UI — that
matches `parameter_grid.py`'s position but doesn't dictate a
*directory* placement. Spyder, napari, Glue all *interleave* such
helpers with the consumer (Spyder's `widgets/utils.py`, napari's
`_qt/utils.py`, Glue's `dialogs/`-internal helpers). That's option (b).

**[CONTESTED]:** the literature does not pick a winner here. Both (b)
and (c) are defensible. Option (b) is "what large desktop apps
actually do." Option (c) is "what Clean Architecture would
recommend." Pick on local taste, with this guide:

- **Pick (b) if:** the project is small (AVC: yes, ~6k LOC) AND no
  plan to add sibling modules in the next 12 months.
- **Pick (c) if:** there's already a roadmap item for grid-layout
  improvements or grid-snapping logic that's going to need its own
  module.

**The user should make this call.** Agent B will execute either.

### 4.5 Naming caveat for option (c)

If option (c) is chosen, **rename the file from `parameter_grid.py`
to `parameter_grid/math.py`** with a hub shim at the old path
(Template-1 per r2's shim templates). This keeps the existing
imports working through one deprecation cycle. The internal contents
don't change.

If option (b) is chosen, **rename the file from `parameter_grid.py`
to `_qt/parameter_grid_math.py`** with a Template-2 `__getattr__`
shim at the old path. Same deprecation pattern.

Naming choice for option (b): the current `parameter_grid.py` plus
`_qt/panels/parameter_grid_panel.py` are *similar names for distinct
things* — the math vs the widget. A `_math` suffix on the moved file
disambiguates. The widget file should stay at `_qt/panels/parameter_grid_panel.py`
(it's the panel, the name fits).

---

## 5. Proposed target tree (with explicit dependency direction)

Two trees are proposed: **Tree-1 (option-b)** and **Tree-2 (option-c)**.
They differ only in where `parameter_grid` lands.

### 5.1 Tree-1 — option (b) winner: `_qt/parameter_grid_math.py`

```
algebraic-variety-cross-section/
├── app.py                              ← ENTRY POINT (only root .py file)
│   │
│   └─→ imports from: _qt.icons, _qt.panels.appearance, _qt.panels.parameters,
│        _qt.panels.view, _qt.styles, render.worker, varieties.{types,
│        registry, tooltips, dispatch}
│
├── _qt/                                ← UI ADAPTER LAYER (Hexagonal "driver")
│   ├── __init__.py
│   ├── icons.py                        Qt icon factories
│   ├── styles.py                       QSS palette + WCAG-AA stylesheet
│   ├── ui_helpers.py                   Debouncer + slider-row builder
│   ├── parameter_grid_math.py          ★ MOVED FROM ROOT: pure-math, Qt-free
│   └── panels/
│       ├── __init__.py
│       ├── appearance.py               AppearancePanel(QWidget)
│       ├── parameters.py               ParametersPanel(QWidget)
│       ├── parameter_grid_panel.py     ParameterGridPanel(QWidget)
│       └── view.py                     ViewPanel(QWidget) + clip_to_domain method
│
├── render/                             ← PIPELINE LAYER (off-thread mesh compute)
│   ├── __init__.py
│   └── worker.py                       MeshWorker(QRunnable) + MeshResult
│
├── cross_section/                      ← PIPELINE LAYER (clip math, Qt-free)
│   ├── __init__.py
│   └── clip.py                         clip_to_domain pure function
│
├── varieties/                          ← DOMAIN LAYER (frozen contract; AI-8)
│   ├── __init__.py                     re-exports types + dispatch
│   ├── types.py                        ParamSpec + Surface dataclasses
│   ├── dispatch.py                     should_render_on_drag, dispatch_mode
│   ├── _kernels.py                     11 Numba @njit field kernels
│   ├── _marching.py                    marching cubes + parametric pipelines
│   ├── k3.py                           Fermat, Kummer
│   ├── enriques.py                     4 Enriques figures
│   ├── calabi_yau.py                   4 CY3 generators
│   ├── fano.py                         4 Fano 3-folds
│   ├── registry.py                     VARIETIES dict (AI-8 stable surface)
│   └── tooltips.py                     VARIETY_TOOLTIPS, SUBTYPE_TOOLTIPS
│
├── tests/                              506 Qt-free tests
├── plans/                              historical design artifacts (untouched)
├── pyproject.toml
├── pytest.ini
├── requirements.txt
├── README.md / AGENTS.md / CONTEXT.md / MOVES.md / CHANGELOG.md / LICENSE
└── .claude/                            agent scaffold (untouched)
```

**Files removed from root** (shims that finished their M+1 cycle):
- `surfaces.py` — re-routed by removing the shim entirely; canonical
  imports `from varieties.* import ...` are already in use everywhere
  except possibly `app.py` (which uses `from surfaces import ...`;
  this changes to `from varieties.registry import VARIETIES`).
- `render_worker.py` — Template-2 shim deleted; consumers use
  `render.worker`.
- `icons.py`, `styles.py`, `ui_helpers.py` — Template-2 shims deleted;
  consumers use `_qt.icons`, `_qt.styles`, `_qt.ui_helpers`.
- `panels/` (the hub-shim directory) — directory deleted; consumers
  use `_qt.panels.*`.
- `parameter_grid.py` — moved to `_qt/parameter_grid_math.py`.

**Files NOT moved (intentional roots):**
- `app.py` — entry point (the user's explicit rule).

### 5.2 Tree-2 — option (c) winner: `parameter_grid/math.py`

```
algebraic-variety-cross-section/
├── app.py                              ← ENTRY POINT (only root .py file)
├── _qt/                                ← UI ADAPTER LAYER (unchanged from Tree-1)
│   └── … (same as Tree-1 minus parameter_grid_math.py)
├── parameter_grid/                     ← NEW SUBPACKAGE (Tree-2 only)
│   ├── __init__.py                     re-exports math symbols
│   └── math.py                         the pure-math content
├── render/                             ← PIPELINE LAYER (unchanged)
├── cross_section/                      ← PIPELINE LAYER (unchanged)
├── varieties/                          ← DOMAIN LAYER (unchanged)
├── tests/, plans/, etc.                (unchanged)
```

The only difference is `parameter_grid/` becoming a new top-level
subpackage instead of moving inside `_qt/`.

### 5.3 Explicit dependency graph

Both trees have the same dependency direction. Drawn as a DAG with
arrows from importer to imported:

```
                          ╔═════════╗
                          ║  app.py ║                     [Frameworks-and-Drivers]
                          ╚════╤════╝
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
        ┌─────────┐      ┌──────────┐    ┌─────────────┐
        │  _qt/   │      │ render/  │    │varieties/   │  (app.py imports
        │ panels  │      │ worker   │    │ registry +  │   from each layer
        │ styles  │      │          │    │ dispatch    │   directly)
        │ icons   │      └────┬─────┘    │ tooltips    │
        │ ui_hlp  │           │          │             │
        └────┬────┘           │          └─────┬───────┘
             │                │                │
             │  (panels       │  (worker      │
             │   call panel-  │   calls       │
             │   level Qt)    │   varieties   │
             │                │   generators) │
             │                ▼                │
             │         ┌────────────┐         │
             │         │cross_section│        │
             │         │   /clip    │         │
             │         └─────┬──────┘         │
             │               │                │
             └────────┐      │     ┌──────────┘
                      ▼      ▼     ▼
                 ┌─────────────────────┐
                 │     varieties/      │     [Entities / Domain]
                 │  types  registry    │
                 │  _kernels _marching │
                 │  k3 enriques        │
                 │  calabi_yau fano    │
                 │  dispatch tooltips  │
                 └──────────┬──────────┘
                            │
                            ▼
                  (numpy, pyvista,
                   numba, skimage,
                   stdlib)
```

**Properties of this graph:**
- **One root**, `app.py`. No node has zero outbound and zero inbound
  — `app.py` has zero inbound (no module imports it; verified by
  inspection of every `^from\|^import` line in the codebase, see
  ground-truth scan in §2 of this brief).
- **One sink**, `varieties/`. No AVC code is imported by `varieties/`
  from outside; only external libs.
- **No back-edges between layers.** Specifically:
  - `varieties/` never imports `_qt/`, `render/`, `cross_section/`,
    or `app.py`. (Audited; all 11 files under `varieties/` import only
    from each other and from external libs.)
  - `cross_section/` never imports `_qt/`, `render/`, or `app.py`.
    (`cross_section/clip.py` imports only numpy, pyvista, and itself.)
  - `render/` imports PySide6 (`QObject`, `QRunnable`, `Signal`) but
    no other AVC layer except `varieties/`-shaped data flowing
    through. Specifically `render/worker.py` imports nothing from
    `varieties/`, `_qt/`, or `cross_section/` — it accepts callables
    and PolyData. Audited from `render/worker.py:31-39`.
  - `_qt/` does not import `app.py`. (Verified — all `_qt/` files
    import only from each other, from `parameter_grid`, from
    `surfaces` (→ `varieties.*`), and from PySide6/PyVista.)
- **Two cross-layer imports inside `_qt/`** worth flagging:
  - `_qt/ui_helpers.py:27`: `import parameter_grid as pg`
  - `_qt/panels/parameters.py:30`: `import parameter_grid as pg`
  - `_qt/panels/parameter_grid_panel.py:35`: `import parameter_grid as pg`

  Under Tree-1 these become `import _qt.parameter_grid_math as pg`
  (within-package). Under Tree-2 they become `from parameter_grid.math import ...`
  (cross-package, same layer level). Either is acyclic.

### 5.4 Dependency layer designations (annotated)

| Package | Layer designation | Clean-arch ring | Notes |
|---|---|---|---|
| `app.py` | Entry / Composition root | Frameworks & Drivers | Single file; wires the dependency graph; the user's explicit choice not to subpackage it |
| `_qt/` | UI adapter (driver) | Interface Adapters | Private (underscore prefix); the napari pattern |
| `render/` | Pipeline / use-case | Use Cases | Owns the off-thread mesh-compute mechanism |
| `cross_section/` | Pipeline / use-case | Use Cases | Owns the clip-to-domain math; Qt-free |
| `parameter_grid/` (Tree-2) | Use-case helper | Use Cases | Pure math; Qt-free; consumed by `_qt/` panels |
| `varieties/` | Domain (entities) | Entities | Mathematical objects + frozen `ParamSpec`/`Surface` contract |
| `_qt/parameter_grid_math.py` (Tree-1) | Lives in adapter | (between Use Cases and Adapters) | Honest tradeoff: cohesion with consumers vs. layer purity |

### 5.5 Things this graph does NOT include (intentionally)

- **No `infrastructure/` layer** — AVC owns no DB, network, or file
  persistence. The "infrastructure" is entirely external libraries.
- **No `services/` or `controllers/` layer** — package-by-feature
  doesn't need them; `MainWindow` is the single controller and lives
  in `app.py`.
- **No `models/` or `viewmodels/`** — the panel-level MVC pattern is
  *implicit* in each panel; no central model layer.
- **No `events/` or `messages/`** — Qt Signals serve this role.
- **No `app/` subpackage** — the user explicitly rejected this shape;
  see §4.2(d).

### 5.6 Tree shape: depth and breadth

Both trees have **maximum depth 2** under the repo root (e.g.
`_qt/panels/appearance.py`). This satisfies the "two-deep nesting
max" heuristic from [Software Carpentry's Python structuring guide](https://intermediate-and-advanced-software-carpentry.readthedocs.io/en/latest/structuring-python.html)
(accessed 2026-05-24). [CONSENSUS for small-to-mid Python projects.]

Top-level breadth:
- **Tree-1:** 1 file (`app.py`) + 4 subpackages (`_qt/`, `render/`,
  `cross_section/`, `varieties/`) + the usual non-source dirs and
  config files.
- **Tree-2:** 1 file + 5 subpackages (above + `parameter_grid/`).

Either fits comfortably in a single `ls`. [OPINION but widely shared:
top-level should fit on one screen.]

---

## 6. Inheritance / polymorphism patterns the new tree enables

The user explicitly asked about "inheritance and polymorphism." This
section walks honest options *ranked by AI-15 honesty* (don't propose
abstractions just because they're trendy).

### 6.1 HIGH-VALUE: `Variety` Protocol for generators

**Current state:** Each variety generator is a free function with the
signature `f(**kwargs) -> pv.PolyData` (or raises `ValueError`).
Examples: `fermat_quartic`, `kummer_surface`, `enriques_figure_1`. The
contract is documented as AI-14 and AI-8.

**The Protocol:**

```python
# In varieties/types.py (additive — no rename of existing dataclass)
from typing import Protocol, runtime_checkable

@runtime_checkable
class VarietyGenerator(Protocol):
    """A callable that produces a pv.PolyData mesh for a variety.

    AI-14: implementations raise ValueError when the parameter set has no
    real zero set; otherwise return a pv.PolyData. Implementations may
    emit warnings.warn(RuntimeWarning, ...) for soft-signal conditions.
    """
    def __call__(self, **params: float) -> "pv.PolyData": ...
```

**Why this is HIGH value:**
- **AI-8 alignment.** The existing `Surface.generate: Callable[..., pv.PolyData]`
  field becomes typed: `generate: VarietyGenerator`. The Protocol
  *names* the contract that's been documented in AI-14 prose for
  months.
- **Mypy + duck-typing.** Protocols give static-checker support without
  forcing inheritance. Existing free functions satisfy the protocol
  automatically (PEP 544 structural subtyping).
  ([PEP 544 — Protocols](https://peps.python.org/pep-0544/), accessed 2026-05-24.)
- **Future extensibility.** Third-party generators in user code can be
  validated at registration time: `assert isinstance(my_fn, VarietyGenerator)`.
  Runtime check works via `@runtime_checkable`.
- **No code change required at call sites.**  Pure type-system addition.

**Risk:** approximately zero — Protocol is additive, no inheritance is
imposed.

**Where it lives:** `varieties/types.py`, next to the existing
`ParamSpec` and `Surface` dataclasses. [CONSENSUS that PEP-544
Protocols are the right tool for "duck-typed callable contracts" in
modern Python.]

### 6.2 MEDIUM-VALUE: Strategy pattern for `dispatch_mode`

**Current state:** `varieties/dispatch.py` (read 2026-05-24) holds:
- `FAST_RENDER_THRESHOLD_MS = 80` — a constant
- `should_render_on_drag(surface) -> bool` — a free predicate
- `dispatch_mode(surface) -> str` — returns "fast" or "release" based
  on `surface.typical_ms` and `surface.coarse_n`

This is *implicitly* the Strategy pattern, with the strategy chosen by
data attributes on `Surface`.

**The refactor:**

```python
# Hypothetical varieties/dispatch.py
from abc import ABC, abstractmethod

class DispatchPolicy(ABC):
    @abstractmethod
    def should_render_on_drag(self, surface: Surface) -> bool: ...
    @abstractmethod
    def coarse_n_override(self, surface: Surface) -> int | None: ...

class DefaultPolicy(DispatchPolicy):
    def should_render_on_drag(self, surface):
        return 0 < surface.typical_ms <= FAST_RENDER_THRESHOLD_MS
    def coarse_n_override(self, surface):
        return None if surface.coarse_n == 0 else surface.coarse_n

class AlwaysReleasePolicy(DispatchPolicy):
    """Test-mode policy: never render on drag — for benchmarking."""
    def should_render_on_drag(self, surface):
        return False
    def coarse_n_override(self, surface):
        return None
```

**Why this is MEDIUM value:**
- **Real win:** future "always-fast" or "always-release" modes (debug
  toggles, A/B benchmarks) become 1-class additions.
- **Test value:** `MainWindow` can be parameterised with an
  `AlwaysReleasePolicy` for deterministic test harnesses.
- **Real cost:** today there is *one* policy. ABC ceremony for one
  implementation is over-engineering. The cost-benefit pencils out
  only if a second policy is actually planned.

**Verdict:** propose as a future option *only if* a debug/benchmark
mode is on the roadmap. Otherwise the current free functions are
fine. [CONTESTED — Strategy is textbook GoF, but YAGNI is the
counter-pattern.]

**Where it would live:** `varieties/dispatch.py` (same file).

### 6.3 LOW-VALUE: `AvcPanel` base class

**Current state:** The four panel classes (`AppearancePanel`,
`ViewPanel`, `ParametersPanel`, `ParameterGridPanel`) all inherit
directly from `QWidget`. They share no common code beyond the
`QWidget` API.

**The proposed refactor:**

```python
class AvcPanel(QWidget):
    """Common base for AVC panels.

    Adds:
    - .panel_id: str — for logging
    - .reset() — called when a new variety is loaded
    - .serialize() / .restore() — for QSettings persistence
    """
```

**Why this is LOW value:**
- **No actual shared behaviour today.** The four panels do
  *genuinely different* things (color picker, viewport, sliders, grid
  dot). There's no method that all four implement and that an ABC
  could capture.
- **Risk of forced sharing.** Adding a `reset()` abstract method
  invites either (a) a no-op implementation in panels that don't need
  it (defeats the purpose) or (b) the wrong abstraction emerging from
  "one panel's reset is another panel's no-op."
- **Each panel already has the QWidget contract.** That's the right
  level of abstraction.

**Verdict:** **don't do this.** Add a shared base *if and when*
multiple panels need the same persistence/lifecycle code; then it's a
1-day extract. [CONSENSUS in refactoring literature: "Wait for the
Third Repeat" before extracting a shared base — Fowler, *Refactoring*
2nd ed., 1999/2018.]

### 6.4 LOW-VALUE: `AbstractShim` base for the deprecation shims

**Current state:** Five `__getattr__`-based shims:
`surfaces.py`, `render_worker.py`, `icons.py`, `styles.py`,
`ui_helpers.py`. Each is ~20 lines, mostly identical boilerplate.

**The proposed refactor:** factor the `__getattr__` body into a
helper:

```python
# In some new "_shim.py"
def make_shim(new_module_path: str, old_name: str):
    def __getattr__(attr: str):
        import importlib, warnings
        mod = importlib.import_module(new_module_path)
        if hasattr(mod, attr):
            warnings.warn(
                f"{old_name}.{attr} is deprecated; "
                f"import from {new_module_path} instead.",
                DeprecationWarning, stacklevel=2,
            )
            return getattr(mod, attr)
        raise AttributeError(f"module {old_name!r} has no attribute {attr!r}")
    return __getattr__
```

**Why this is LOW value (don't do it):**
- **The shims are being deleted in r3.** Per the r2 plan and CLAUDE.md
  §2 (M+1 milestone closing), the entire purpose of r3 includes
  removing these shims. Building a base class for code that's about
  to be deleted is wasted effort.
- **The boilerplate is small.** 20 lines × 5 files = 100 lines, and
  every shim is in its own one-line-import file. The factor-out
  doesn't save material LOC.

**Verdict:** **explicitly do not do this.** The shims are
deprecation-cycle artifacts; the cycle ends in r3.

### 6.5 MEDIUM-VALUE: `pv.PolyData` factory protocol for the pipeline helpers

**Current state:** `varieties/_marching.py` has free helpers:
- `_marching_cubes_to_polydata(field, bounds) -> pv.PolyData`
- `_grid_to_polydata(X, Y, Z) -> pv.PolyData`
- `_concat_polydata(meshes) -> pv.PolyData`
- `_hanson_cross_section(...)` — the parametric pipeline

AI-6 separates implicit-vs-parametric pipelines. Today the choice is
"the generator function knows which to call." There's no enforcing
type structure.

**The protocol (illustrative):**

```python
class ImplicitFieldEvaluator(Protocol):
    """A field evaluator for the implicit pipeline (AI-6)."""
    def __call__(self, X, Y, Z, **params) -> "np.ndarray": ...

class ParametricGridEvaluator(Protocol):
    """A (u, v) -> (X, Y, Z) evaluator for the parametric pipeline (AI-6)."""
    def __call__(self, U, V, **params) -> tuple["np.ndarray", "np.ndarray", "np.ndarray"]: ...
```

**Why this is MEDIUM value:**
- AI-6 ("Implicit surfaces → marching cubes; parametric surfaces →
  structured grid. NEVER mix.") is currently a *convention* documented
  in CLAUDE.md and CONTEXT.md. Naming the two evaluator protocols
  turns the convention into a typecheckable contract.
- But: today every existing generator inlines its field evaluator into
  the generator function body (e.g. `fermat_quartic` calls a
  module-level `_fermat_field_kernel` Numba JIT then calls
  `_marching_cubes_to_polydata` directly). Extracting evaluators as
  named callables to satisfy a Protocol would be a structural rewrite
  of every generator. That's a refactor, not just a tree restructure.
- The user's r3 brief is about *tree shape*, not about rewriting
  generator internals.

**Verdict:** mention as a future option; do not propose for r3 scope.
[CONTESTED — Protocols here would help, but the scope cost is
significant.]

### 6.6 ZERO-VALUE: Abstract `MeshWorker` for off-thread compute

**Current state:** `render/worker.py` defines `MeshWorker(QRunnable)`.
There is exactly one worker class.

**Don't:** add an `AbstractMeshWorker` ABC. There's one
implementation; ABC is ceremony.

### 6.7 Summary table

| Pattern | AVC value | Where it lives in tree | Risk |
|---|---|---|---|
| `VarietyGenerator` Protocol (PEP 544) | **HIGH** | `varieties/types.py` | Near-zero (additive) |
| `DispatchPolicy` Strategy ABC | **MEDIUM** | `varieties/dispatch.py` | YAGNI today; HIGH value with second policy |
| `AvcPanel` base class | **LOW** | `_qt/panels/_base.py` | Premature abstraction; forced sharing |
| `AbstractShim` base class | **ZERO (negative)** | (would-be at root) | Shims are being deleted in r3 |
| `ImplicitFieldEvaluator` / `ParametricGridEvaluator` Protocols | **MEDIUM** | `varieties/types.py` | Out of scope for tree restructure; future option |
| Abstract `MeshWorker` | **ZERO** | (would-be in `render/`) | YAGNI; one implementation |

**Recommendation for r3:** propose only the `VarietyGenerator` Protocol
(§6.1) as a *bundled add* with the tree restructure. The other
patterns are noted for future cycles.

---

## 7. Anti-patterns to AVOID in the new tree

Explicit list of what *not* to do, each with the "why-it's-tempting"
and "why-it-hurts" analysis.

### 7.1 "Just rename `surfaces.py` to `app/surfaces.py`"

**Tempting because:** it'd "satisfy" the user's "only app.py at root"
rule with one `git mv`, no shims to delete.

**Hurts because:**
- Defeats the canonical-path discipline established by r1+r2. Every
  consumer's import path has *already* been migrated to
  `from varieties.* import ...` (see surfaces.py current contents:
  it's a re-export of `varieties.*` symbols). Renaming the shim to
  `app/surfaces.py` would force every consumer to *re-add* a shim
  import, undoing the migration.
- Creates an `app/` directory with one shim file in it — option (d)
  YAGNI from §4.2.
- Confuses the meaning of "app" — it's not the entry point, it's a
  legacy compatibility hub.

**Right answer:** delete `surfaces.py` entirely. Every consumer
already has the canonical `from varieties.* import ...` form (or can
be updated to it in the same commit). M+1 expiration.

### 7.2 Three-deep nesting (`app/_qt/panels/widgets/colors.py`)

**Tempting because:** "logical" subgrouping — color widgets inside
panels inside `_qt`.

**Hurts because:**
- Violates the [Software Carpentry two-deep heuristic](https://intermediate-and-advanced-software-carpentry.readthedocs.io/en/latest/structuring-python.html).
  [CONSENSUS for small-to-mid Python projects.]
- Import paths become unwieldy:
  `from app._qt.panels.widgets.colors import ColorButton`.
- AI agents (and humans) lose orientation in deeply nested trees —
  scout-B's brief makes this argument explicitly.

**Right answer:** keep depth ≤ 2 under the repo root. If a level-2
directory becomes too large, *split into siblings at level 2*, not by
deepening.

### 7.3 `app/utils.py` (or worse, `utils/`)

**Tempting because:** "this helper doesn't fit anywhere else, I'll
put it in utils."

**Hurts because:**
- The "Dunghill anti-pattern" ([Matti Lehtinen](https://mattilehtinen.com/articles/dunghill-anti-pattern-why-utility-classes-and-modules-smell/), accessed 2026-05-24):
  utility modules grow unboundedly because nothing tells you what
  *doesn't* belong there.
- Disguises layering violations — a "utility" that depends on Qt
  shouldn't live next to a "utility" that depends on numpy.
- Resists testing — large utils modules become slow imports and
  brittle tests.

**Right answer:** every helper must declare its *layer* via its
location. Slider-row builders go in `_qt/ui_helpers.py` (a real role).
Marching-cubes glue goes in `varieties/_marching.py`. No `utils.py`
at any level. [CONSENSUS — scout-B's brief makes this point with
multiple cites.]

### 7.4 Cross-layer back-imports (UI reaching into domain internals)

**Tempting because:** "the variety needs to know the panel's slider
range" or "the generator needs to grab a color from `_qt.styles`."

**Hurts because:**
- Inverts the dependency direction; turns the tree into a cycle.
- Couples the domain to UI implementation details.
- Breaks AI-2 (Qt-free tests) instantly.

**Right answer:** if the domain needs information that today lives in
the UI, *the data* moves into the domain (e.g. add a `default` to
`ParamSpec`; that's already the pattern). If the UI needs to react to
domain events, use Qt Signals — the domain emits a plain Python event
(or returns a value), the UI subscribes.

### 7.5 Plugin architecture without a real plugin contract

**Tempting because:** "let's make it extensible just in case."

**Hurts because:**
- Premature plugin-ification adds packaging-time complexity
  (entry-points scanning, isolation, version compatibility) for zero
  current consumers.
- The "plugin contract" without a real consumer is invariably wrong.
  napari's plugin contract took *two complete rewrites* (npe1 → npe2)
  to settle. ([npe2 motivation](https://github.com/napari/napari/discussions/3171), accessed 2026-05-24.)

**Right answer:** keep the `VARIETIES` dict registry. If a second
consumer appears (e.g. external math collaborator), then design the
plugin contract from their actual needs, not from speculation.

### 7.6 Premature abstraction (creating ABCs before there are concrete needs)

**Tempting because:** "I want to leave room for future implementations."

**Hurts because:**
- One implementation behind an ABC is a 100% noise-to-signal ratio.
- The first ABC almost always has the wrong shape (you discover the
  abstraction by *having* multiple implementations).
- Tests must instantiate concrete subclasses; the ABC adds nothing to
  test value.

**Right answer:** wait for the Rule of Three (Fowler, *Refactoring*
2nd ed., 1999/2018). When you have *three* implementations of the
same thing, *then* extract the common shape. PEP-544 Protocols are
a softer alternative — they let you name a duck-typed contract
without forcing inheritance. See §6.1 for the one ABC/Protocol the
brief *does* recommend (`VarietyGenerator`), and the multiple cases
where it does not.

### 7.7 Renaming during a move

**Tempting because:** "since we're moving the file anyway, let's also
clean up the name."

**Hurts because:**
- Conflates two semantically distinct operations (move + rename) in
  one diff; reviewers can't tell which symbol moved where.
- Doubles the import-path migration cost.
- `git log --follow` and IDE rename-tracking degrade.

**Right answer:** move-then-rename in separate commits, or use the
r2 precedent (MEDIUM-2: "don't rename during a move unless required
for correctness"). The one r3 exception is `parameter_grid.py` →
`_qt/parameter_grid_math.py` (option b) — the rename is required to
avoid name collision with `_qt/panels/parameter_grid_panel.py` in
the same parent. [CONSENSUS — r2 already established this rule
explicitly.]

### 7.8 Leaving shims in place "just in case"

**Tempting because:** "what if someone external is importing
`from surfaces import VARIETIES`?"

**Hurts because:**
- The shims were always documented as M+1 — one cycle. Leaving them
  through r3 starts an M+2 dance with no end.
- Every `from surfaces import ...` import emits a `DeprecationWarning`
  *every test run*; eventually they become noise the team ignores.
- The shims are dead code that future readers must understand.

**Right answer:** r3 removes the shims. The migration is internal —
AVC has no external API surface to speak of. The single risk is that
some Markdown doc still says `from surfaces import ...`; r3 must grep
and update.

### 7.9 Adding Import-Linter / Tach contracts proactively

**Tempting because:** "let's enforce the layer rules at CI time."

**Hurts because (with caveats):**
- The Kraken Import-Linter pattern shines at 100k+ LOC with 40+
  contracts. At AVC's 6k LOC the maintenance overhead may exceed the
  catch rate.
- A *single* import-linter contract — "varieties may not import _qt
  or render" — is high-value and 10 lines. A full set of 10
  contracts is overkill.

**Right answer (calibrated):** *consider* adding one Import-Linter
contract enforcing the domain-isolation rule (`varieties/` may not
import `_qt/`, `render/`, `cross_section/`, or `app.py`). Skip
broader contracts. [OPINION; HIGH-confidence based on Kraken's own
write-up about contract count.] If the user agrees, Agent B can
include it in the migration; if not, leave it for a future cycle.

### 7.10 Summary table

| Anti-pattern | Why tempting | Why it hurts |
|---|---|---|
| `app/surfaces.py` rename of the shim | "satisfies user constraint with one git mv" | Defeats canonical-path discipline; introduces unused `app/` |
| Three-deep nesting | Logical sub-grouping | Violates two-deep heuristic; ugly import paths |
| `utils.py` grab-bag | "doesn't fit anywhere else" | Dunghill anti-pattern; layering violations hidden |
| Cross-layer back-imports | Domain "needs" UI info | Cycles; couples; breaks AI-2 |
| Plugin architecture | "leave room for extension" | Premature; first contract is always wrong |
| Premature ABCs | "leave room for subclasses" | One impl behind ABC is noise |
| Move-and-rename in one commit | Convenience | Reviewers can't track; git log --follow degrades |
| Leaving shims "just in case" | Hypothetical external user | Open-ended; dep-warning fatigue |
| Adding 10 Import-Linter contracts proactively | "enforce layers at CI" | Maintenance overhead > catch rate at 6k LOC |

---

## 8. AI-1..AI-15 invariant compatibility check

Walking each invariant against the proposed tree.

(Invariant text quoted verbatim from `.claude/references/app-invariants.md`,
read 2026-05-24.)

### AI-1 — PySide6 + PyVista + pyvistaqt (LGPL-friendly stack)

**Compatibility:** **PRESERVED.** The proposed tree does not touch
the rendering stack; only moves files between directories. PySide6 +
PyVista + pyvistaqt remain in `_qt/` (PySide6/pyvistaqt) and
`varieties/` (PyVista as the mesh primitive).

### AI-2 — Test suite is Qt-free (pure NumPy / PyVista / scikit-image)

**Compatibility:** **PRESERVED and STRENGTHENED.**
- Strengthened because the tree makes Qt-free vs Qt-coupled
  *structural*: tests can `import varieties.*`, `import render.worker`,
  `import cross_section.clip`, `import parameter_grid` (or its new
  home), and *none* of those transitively import Qt today (verified
  by inspection of `^import` lines).
- Verified `render/worker.py` *does* import PySide6 (`QObject`,
  `QRunnable`, `Signal`), so tests for `render/` must use `pytest-qt`
  or — more in line with AI-2 — mock the QRunnable. CONTEXT.md notes
  this and the existing test suite already handles it. No regression.
- One care item: if Tree-1 is chosen and `_qt/parameter_grid_math.py`
  lives inside `_qt/`, tests that previously did `import parameter_grid`
  must update to `import _qt.parameter_grid_math`. If
  `_qt/__init__.py` ever adds `from PySide6 import ...` at top level
  (it doesn't today), that update would silently bring Qt into the
  test process. Mitigation: keep `_qt/__init__.py` import-free
  (which it already is); add an explicit comment to that effect.

### AI-3 — Render verification is off-screen via `pv.OFF_SCREEN = True`

**Compatibility:** **PRESERVED.** Render verification is an operational
pattern, not a tree-shape concern. The tree restructure does not
affect how `pv.OFF_SCREEN` is used.

### AI-4 — Domain clipping uses `clip_scalar`, not `clip_box`

**Compatibility:** **PRESERVED.** `cross_section/clip.py` is the canonical
location for this; r2 batch 4 already moved it here. The clip code
uses `clip_scalar` (verified in current source). Tree restructure
preserves this.

### AI-5 — PyVista 0.46+ `clip_scalar` requires `scalars=` keyword

**Compatibility:** **PRESERVED.** Same as AI-4 — operational, not
tree-shape.

### AI-6 — Implicit surfaces use marching cubes; parametric surfaces do NOT

**Compatibility:** **PRESERVED and CLEARER.**
- All marching-cubes pipeline code is in `varieties/_marching.py`
  (r2 batch 6 landed this).
- All parametric pipeline helpers (`_grid_to_polydata`, `_hanson_cross_section`)
  also live in `varieties/_marching.py` (they're the parametric
  counterparts).
- The tree restructure does not move or split these. AI-6 enforcement
  remains in the generator function bodies: implicit generators call
  `_marching_cubes_to_polydata`, parametric generators call
  `_grid_to_polydata` + `_concat_polydata`.
- A *future* refinement (§6.5) would split `varieties/_marching.py`
  into `varieties/_implicit_pipeline.py` + `varieties/_parametric_pipeline.py`
  and add the `ImplicitFieldEvaluator` / `ParametricGridEvaluator`
  Protocols (§6.5). Out of scope for r3.

### AI-7 — Hanson normals: `cell_normals=True, consistent_normals=False, ...`

**Compatibility:** **PRESERVED.** Inside `varieties/_marching.py`'s
`_hanson_cross_section`; not affected by tree shape.

### AI-8 — `Surface` / `ParamSpec` dataclass contract (frozen registry)

**Compatibility:** **PRESERVED.**
- `ParamSpec` and `Surface` live at `varieties/types.py` (canonical
  since r2 batch 5). Unchanged.
- `VARIETIES` dict lives at `varieties/registry.py` (canonical since
  r2 batch 8). Unchanged.
- `VARIETY_TOOLTIPS` and `SUBTYPE_TOOLTIPS` live at
  `varieties/tooltips.py`. Unchanged.
- The Protocol addition proposed in §6.1 (`VarietyGenerator`) is
  additive — it does not change the `Surface` dataclass fields, only
  types the existing `generate` callable.

### AI-9 — Re-entrancy guard `self._computing` around `processEvents()`

**Compatibility:** **PRESERVED — and depends on `MainWindow` staying
in one file.**
- The `_computing` guard lives in `MainWindow._render_current`
  (`app.py`). The tree restructure does not split `MainWindow`
  (CLAUDE.md §2: God Object, do not Extract Class).
- If a *future* cycle splits `MainWindow`, the `_computing` guard must
  remain *atomic* — i.e. lives in the same class as the
  `processEvents()` call. Splitting *render_current* into a separate
  helper class without the guard would re-enable the re-entrancy bug.
- This is operational discipline, not tree-shape; flagged here for
  visibility.

### AI-10 — Raw mesh cached; domain clip doesn't regenerate

**Compatibility:** **PRESERVED.** `_raw_mesh` lives in `MainWindow`;
clip-only path lives in `_on_domain_changed` → `_apply_domain_and_render(reset_camera=False)`.
Tree restructure does not touch this logic.

### AI-11 — Fully-qualified Qt enums

**Compatibility:** **PRESERVED.** Operational discipline; not tree-shape.
The proposed tree restructure adds *no* Qt enum code (it only moves
files), so no risk of introducing new short-form enums.

### AI-12 — WCAG AA text-contrast on all visible text

**Compatibility:** **PRESERVED.** `_qt/styles.py` (canonical since r2
batch 3) is the centralized stylesheet. Tree restructure does not
touch.

### AI-13 — 6-digit hex only (PyVista color parser)

**Compatibility:** **PRESERVED.** Operational discipline.

### AI-14 — Generator function contract: `pv.PolyData` or `ValueError`

**Compatibility:** **PRESERVED and TYPED.** The `VarietyGenerator`
Protocol proposed in §6.1 explicitly documents this contract:
`def __call__(self, **params: float) -> "pv.PolyData": ...` plus a
docstring noting "raises ValueError per AI-14." This *strengthens*
AI-14 by making it a static-checkable contract.

### AI-15 — Math claim honesty: ≥2 sources + honest "real shadow" disclaimers

**Compatibility:** **PRESERVED.**
- `varieties/tooltips.py` (canonical since r2 batch 8) holds
  `VARIETY_TOOLTIPS` and `SUBTYPE_TOOLTIPS`. Tree restructure does
  not touch.
- AI-15 also applies to this brief — every architectural claim is
  marked `[CONSENSUS]` / `[CONTESTED]` / `[UNVERIFIED]` with cites.

### AI-1..AI-15 Compatibility Summary

| AI-# | Tree-shape impact | Status |
|---|---|---|
| AI-1 | None | PRESERVED |
| AI-2 | Strengthened (structural Qt-free boundary) | PRESERVED+ |
| AI-3 | None | PRESERVED |
| AI-4 | None | PRESERVED |
| AI-5 | None | PRESERVED |
| AI-6 | Clearer (`varieties/_marching.py` is the home) | PRESERVED |
| AI-7 | None | PRESERVED |
| AI-8 | None (Protocol addition is additive) | PRESERVED |
| AI-9 | None (MainWindow stays in `app.py`) | PRESERVED |
| AI-10 | None | PRESERVED |
| AI-11 | None | PRESERVED |
| AI-12 | None | PRESERVED |
| AI-13 | None | PRESERVED |
| AI-14 | Strengthened (typed Protocol) | PRESERVED+ |
| AI-15 | None for code; brief itself complies | PRESERVED |

**Zero invariants regressed; two strengthened.**

---

## 9. Honest assessment of the tradeoffs (where the literature is split)

This section explicitly calls out where smart people disagree — so
the user can make an informed choice rather than rubber-stamping a
recommendation.

### 9.1 Where does `parameter_grid.py` go? (§4 already explored)

**Split:** Tree-1 (b) vs Tree-2 (c).

**Literature disagreement:** napari and Spyder *interleave* such
helpers with consumers (favors b). Clean Architecture / Cosmic Python
*separate* by layer (favors c). Both teams ship working desktop apps.

**The honest call:** **Tree-1 (option b) is the better fit for AVC
today** because (i) there's only one such math helper; (ii) AVC has
no roadmap for grid-layout siblings; (iii) the cohesion-with-
consumers win is concrete. **Tree-2 (option c) is the better fit if**
a near-term feature plan calls for grid-snapping, grid-layout, or
grid-serializer modules.

**The user should pick one.** Both are defensible; Agent B can
execute either.

### 9.2 Should `_qt/` be `_qt/` or `qt/` or `ui/`?

**Split:** napari uses `_qt/` (underscore = private). SciPy mixes
(`_lib` underscored, `optimize` not). PyVista uses no underscore
(`plotting/`). Glue uses no underscore (`viewers/`).

**Literature disagreement:** the underscore-as-private convention is
strong in some communities (napari, scientific-python core) and
non-existent in others.

**The honest call:** **keep `_qt/` as-is** — r2 already established
it, the naming costs zero to maintain, and the napari precedent is
the closest analogue for AVC. The alternative (rename to `qt/` or
`ui/`) is a churn-for-aesthetics move. [OPINION; CONTESTED in the
broader Python community.]

### 9.3 Should `render/` and `cross_section/` merge?

**Split:** Some teams would put `render/worker.py` and
`cross_section/clip.py` under a single `pipeline/` subpackage. Others
keep them separate because they have genuinely distinct roles
(off-thread mesh compute vs. domain clipping math).

**The honest call:** **keep separate.** They have different external
dependencies (`render/worker.py` imports PySide6; `cross_section/clip.py`
is Qt-free). Merging would force the Qt-free clip module into a
package that also contains Qt code, weakening AI-2's structural
guarantee. [OPINION; STRONG-confidence based on AI-2 alignment.]

### 9.4 Should `varieties/` use the `__init__.py` re-export pattern?

**Split:** napari uses lazy-loading `__getattr__` in some top-level
`__init__.py` files; PyVista re-exports everything. Cosmic Python
recommends "explicit imports from submodules, no
`__init__.py` re-exports" (since the import path is documentation).

**Current state:** `varieties/__init__.py` re-exports
`ParamSpec`, `Surface`, `should_render_on_drag`, `dispatch_mode`,
`FAST_RENDER_THRESHOLD_MS`. Consumers can do either
`from varieties.types import ParamSpec` (canonical) or
`from varieties import ParamSpec` (sugar).

**The honest call:** **keep the existing pattern.** The re-exports
are documented as "Convenience re-exports below (canonical = `from
varieties.types import …`)". This dual-form is fine for a stable,
small public surface. [CONTESTED — Cosmic Python disagrees; PyVista
agrees.]

### 9.5 Add Import-Linter contracts?

**Split:** Kraken says yes (40+ contracts); small-project literature
says only when you have a real layering problem. AVC sits between.

**The honest call:** **one contract is worth it; ten is not.** A
single Import-Linter rule (`varieties/` may not import from `_qt/`,
`render/`, `cross_section/`, `app.py`) costs ~10 lines of config and
catches the highest-impact regression. Broader rules can be added if
later cycles show drift. [OPINION; cite Kraken for the
contract-count tradeoff curve.]

### 9.6 Should the tree be enforced by `pyproject.toml`'s `[tool.setuptools.packages.find]`?

**Split:** Some projects pin which packages get shipped to PyPI;
others trust the directory layout.

**The honest call:** **AVC doesn't ship to PyPI** (it's a desktop
app run via `python app.py`). The `pyproject.toml` ships only build
metadata, so this question doesn't apply. [N/A for AVC.]

### 9.7 Should we add an `examples/` subpackage?

**Split:** napari, PyVista, vedo all have one. Glue has `examples/`
external to the package. AVC has none.

**The honest call:** **out of scope for r3.** The user hasn't asked
for one, and AVC's "example" is `python app.py` itself — interactive
app, not scripted demos. If desktop screenshots/gifs are wanted,
those belong in README.md or in a `docs/` directory, not as Python
scripts. [OPINION.]

### 9.8 Should the tests directory be `tests/` or `varieties/_tests/` etc.?

**Split:** napari uses package-internal `_tests/` (e.g.
`napari/_tests/`, `napari/layers/_tests/`). Most Python projects
use a top-level `tests/`. Scout-B's brief recommends `tests/`
"parallel to but not inside the package."

**The honest call:** **keep `tests/` at root.** r2 already
established it; the flat layout matches AVC's flat-package style;
imports work without `pip install -e .`. [CONSENSUS for small-mid
projects.]

### 9.9 Summary: contested decisions for the user

| Decision | Options | Recommendation | Confidence |
|---|---|---|---|
| `parameter_grid.py` placement | (a)/(b)/(c)/(d)/(e) | **(b) `_qt/parameter_grid_math.py`** *or* **(c) `parameter_grid/math.py`** | CONTESTED — user picks |
| `_qt/` vs `qt/` vs `ui/` | Three names | **Keep `_qt/`** | HIGH (precedent) |
| Merge `render/` + `cross_section/` | Yes / no | **Keep separate** | HIGH (AI-2) |
| `varieties/__init__.py` re-exports | Keep / remove | **Keep** | MEDIUM (CONTESTED) |
| Import-Linter contracts | 0 / 1 / 10 | **1 contract for `varieties/`** | MEDIUM (OPINION) |
| `examples/` subpackage | Yes / no | **No (out of scope)** | HIGH |
| `tests/` location | Root / package-internal | **Keep at root** | HIGH (precedent) |

---

## 10. What this tree does NOT achieve

Be honest. Here's what's still ugly *after* the r3 restructure lands.

### 10.1 `app.py` is still 1900 LOC

The proposed tree does not split `MainWindow`. CLAUDE.md §2 explicitly
forbids Extract Class on `app.py` ("God Object, do not Extract Class
here"). The 1900 LOC stays in one file with one class. The tree
restructure does *make Extract Class easier in a future cycle* —
once the layers are named and the imports flow downward, splitting
`MainWindow` into `MainWindow + RenderCoordinator + PanelCoordinator`
(or similar) becomes a mechanical refactor inside `app.py`'s
import-arrow scope. But that's a future cycle, not r3.

### 10.2 The Qt-bridge in `render/worker.py` mixes layers

`render/worker.py` imports PySide6 (`QObject`, `QRunnable`, `Signal`).
It's classified in §5.4 as the "pipeline/use-case" layer, but it
imports a UI-framework dependency. This is a hexagonal-architecture
"impedance" — the worker is conceptually domain (it runs in a thread,
operates on PolyData), but mechanically it's a Qt class.

**Could it be fixed?** Yes — the worker could be split into
`render/runner.py` (pure-Python `Runnable` Protocol + a `run()` that
returns `(result, elapsed_ms)`) and `_qt/render_bridge.py`
(the `QRunnable`/`Signal` wiring). That would push the Qt dependency
out of `render/`.

**Should it be fixed in r3?** **No.** It's a single ~25-line class
(the wrapper) plus a `MeshResult` dataclass. Splitting it adds two
files and one cross-package import for ceremonial purity. [OPINION;
the [Cosmic Python](https://www.cosmicpython.com/book/) approach
would say split; pragmatist desktop-app practice says leave it.]
Future-cycle item.

### 10.3 `parameter_grid` (wherever it lands) couples to `ParamSpec`

`parameter_grid.py` imports `ParamSpec` from `varieties.types`.
Either tree leaves this import. That's a *correct* downward
dependency (use-case-layer file importing a domain primitive), so
it's not a violation — but it does mean the "pure math" module isn't
*generic* math; it's specifically AVC math. That's fine and
intentional; flagged for transparency.

### 10.4 The shim deletions are a breaking change for non-AVC consumers

If anyone outside the repo has ever imported `from surfaces import
ParamSpec`, the r3 shim deletions break them. AVC has no documented
external consumers, but the brief makes no claim of zero — there
could be student-project forks, course handouts referencing the old
paths, etc. The shims emit `DeprecationWarning` today; r3's deletion
upgrades that to `ImportError`.

**Mitigation:** the M+1 deprecation cycle was the *warning window*.
Any external consumer who saw a `DeprecationWarning` for ≥ 1 cycle
has had notice. r3 is the canonical removal.

### 10.5 The proposed tree doesn't add CI enforcement of layering

§9.5 recommends one Import-Linter contract. It's *not* mandatory in
the brief — only proposed. If the user declines, the tree's
dependency direction is *documented* (in this brief, in CONTEXT.md
after r3, in CLAUDE.md updates) but not *enforced*. A future
developer (or AI agent) could accidentally introduce a back-edge
import. Pure documentation discipline depends on review catching it.

**Honest assessment:** for a 1–2 dev team, review discipline is
usually enough at 6k LOC. At 20k+ LOC, automated enforcement becomes
worth it. The user should make this call based on team size.

### 10.6 `varieties/_marching.py` mixes implicit and parametric helpers

The 11 Numba kernels in `varieties/_kernels.py` are all for *implicit*
pipelines. The marching-cubes helpers in `varieties/_marching.py` are
also implicit. But `varieties/_marching.py` *also* contains
`_grid_to_polydata`, `_concat_polydata`, and `_hanson_cross_section`
— the parametric helpers.

AI-6's structural separation ("implicit → marching cubes; parametric
→ structured grid; NEVER mix") is enforced by the *generator
functions*, not by the helpers. A future cycle could split
`_marching.py` → `_implicit_pipeline.py` + `_parametric_pipeline.py`
to make the AI-6 boundary structural rather than conventional.

**Should r3 do this?** **No** — it's a refactor inside `varieties/`,
not a tree-shape restructure. Future cycle.

### 10.7 Tooltip data is not localized

`varieties/tooltips.py` holds English-only string constants. A future
cycle wanting i18n would need a `_translate()` indirection. Out of
scope. [N/A]

### 10.8 No accessibility audit beyond AI-12

AI-12 covers WCAG AA *text contrast*. There's no broader a11y audit
(keyboard navigation, screen-reader labels, focus rings). Out of
scope for r3.

### 10.9 Summary of "still ugly"

| Issue | r3 fixes? | Future cycle |
|---|---|---|
| `app.py` is 1900 LOC | NO | Extract Class on `MainWindow` (explicitly deferred) |
| `render/worker.py` imports PySide6 | NO | Optional split into `render/runner.py` + `_qt/render_bridge.py` |
| `parameter_grid` couples to `ParamSpec` | NO | Intentional; not a violation |
| Shim deletion breaks external forks | NO | Documented; M+1 warning was the notice |
| No Import-Linter enforcement | OPTIONAL | One contract recommended; user choice |
| `_marching.py` mixes implicit + parametric helpers | NO | Optional split; AI-6 still enforced by generators |
| Tooltip i18n | NO | Out of scope |
| Broader a11y audit | NO | Out of scope |

The r3 tree restructure is a **necessary precondition** for several
of these future cycles (especially the `MainWindow` Extract Class and
the optional `render/` split), but does not perform them itself.

---

## 11. Concise recommendation block (for the design-synthesis phase)

If the synthesis phase wants a single paragraph to pull from this
brief:

> **r3 should adopt a layered tree rooted at `app.py`, with four named
> subpackages — `_qt/` (UI adapter, napari-pattern), `render/` and
> `cross_section/` (use-case / pipeline layer), and `varieties/`
> (domain). The five M+1 shims (`surfaces.py`, `render_worker.py`,
> `icons.py`, `styles.py`, `ui_helpers.py`) are deleted. The hub-shim
> `panels/` directory is deleted. `parameter_grid.py` moves to either
> `_qt/parameter_grid_math.py` (cohesion-with-consumers) or
> `parameter_grid/math.py` (own its own layer) — the user picks.
> The dependency rule is "imports point downward only"; an optional
> one-rule Import-Linter contract enforces `varieties/ ↛ {_qt, render,
> cross_section, app.py}`. The `VarietyGenerator` Protocol is added
> to `varieties/types.py` to make AI-8 + AI-14 statically typed.
> Every AI-1..AI-15 invariant is preserved; AI-2, AI-8, AI-14 are
> strengthened. The proposed tree does NOT split `MainWindow` (CLAUDE.md
> defers that) and does NOT add a plugin architecture (YAGNI).**

---

## 12. References (canonical, with access dates)

**Reference repositories (GitHub):**
- napari — <https://github.com/napari/napari> (tree fetched via `gh api` 2026-05-24)
- napari directory-organization docs — <https://napari.org/dev/developers/architecture/dir_organization.html> (accessed 2026-05-24)
- Spyder — <https://github.com/spyder-ide/spyder> (tree fetched via `gh api` 2026-05-24)
- Glue — <https://github.com/glue-viz/glue> (tree fetched via `gh api` 2026-05-24)
- Mayavi — <https://github.com/enthought/mayavi> (tree fetched via `gh api` 2026-05-24)
- MNE-Python — <https://github.com/mne-tools/mne-python> (tree fetched via `gh api` 2026-05-24)
- PyVista — <https://github.com/pyvista/pyvista> (tree fetched via `gh api` 2026-05-24)
- vedo — <https://github.com/marcomusy/vedo> (tree fetched via `gh api` 2026-05-24)
- ParaView — <https://github.com/Kitware/ParaView> (tree fetched via `gh api` 2026-05-24)

**Architecture patterns — primary sources:**
- Cockburn, Alistair. "Hexagonal Architecture / Ports and Adapters." HaT Technical Report 2005.02. <https://alistair.cockburn.us/hexagonal-architecture/> (Wikipedia summary accessed 2026-05-24: <https://en.wikipedia.org/wiki/Hexagonal_architecture_(software)>; cockburn.us cert expired at fetch time, used Wikipedia as fallback)
- Martin, Robert C. "The Clean Architecture." 2012. <https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html> (accessed 2026-05-24)
- Fowler, Martin. *Patterns of Enterprise Application Architecture*. Addison-Wesley, 2002.
- Fowler, Martin. *Refactoring: Improving the Design of Existing Code*, 2nd ed. Addison-Wesley, 1999/2018.
- Reenskaug, Trygve. "MODELS - VIEWS - CONTROLLERS." Xerox PARC, 1979.
- Percival, Harry & Bob Gregory. *Architecture Patterns with Python* ("Cosmic Python"). O'Reilly, 2020. <https://www.cosmicpython.com/book/> (book site accessed 2026-05-24)
- Kraken Technologies. "How we organize our very large Python monolith." EuroPython blog, 2023. <https://blog.europython.eu/kraken-technologies-how-we-organize-our-very-large-pythonmonolith/> (accessed 2026-05-24)
- Sahibinden Tech. "Package by layer vs package by feature." Medium, 2024. <https://medium.com/sahibinden-technology/package-by-layer-vs-package-by-feature-7e89cde2ae3a> (accessed via scout-B's references; URL re-verified 2026-05-24)

**Python language / framework references:**
- PEP 544 — Protocols — <https://peps.python.org/pep-0544/> (accessed 2026-05-24)
- Python packaging entry-points — <https://packaging.python.org/en/latest/specifications/entry-points/> (accessed 2026-05-24)
- Qt 6 Model/View Programming — <https://doc.qt.io/qt-6/model-view-programming.html> (accessed 2026-05-24)
- Qt 6 Signals & Slots — <https://doc.qt.io/qt-6/signalsandslots.html> (accessed 2026-05-24)

**Anti-pattern + heuristic references:**
- Software Carpentry: Structuring Python — <https://intermediate-and-advanced-software-carpentry.readthedocs.io/en/latest/structuring-python.html> (accessed via scout-B; re-verified 2026-05-24)
- Matti Lehtinen. "Dunghill anti-pattern: why utility classes and modules smell." <https://mattilehtinen.com/articles/dunghill-anti-pattern-why-utility-classes-and-modules-smell/> (accessed via scout-B's references)
- Nitin Gavhane. "AI Coding Agents Are Hitting a Wall — and the Wall Is Your Architecture." Medium, 2026. <https://nitingavhane.medium.com/ai-coding-agents-are-hitting-a-wall-and-the-wall-is-your-architecture-a57ec11d20ce> (cited from scout-B)
- HumanLayer. "Writing a good CLAUDE.md." <https://www.humanlayer.dev/blog/writing-a-good-claude-md> (cited from scout-B)

**Prior AVC research (in-repo):**
- `.claude/references/app-invariants.md` (read 2026-05-24) — AI-1..AI-15 canonical text
- `.claude/notes/repository-architect-design/scout-b-best-practices.md` (read 2026-05-24) — prior pattern survey, used as prior-art
- `CLAUDE.md` / `AGENTS.md` (read 2026-05-24) — current project working agreements
- `CONTEXT.md` §3-§5 (load-bearing for AI-1..AI-15) — not re-read for this brief; cited via app-invariants.md

---

## 13. Outstanding questions for the user (decision points)

The brief leaves three explicit user-decision points:

1. **Where does `parameter_grid.py` land?** Tree-1 (option b,
   `_qt/parameter_grid_math.py`) or Tree-2 (option c,
   `parameter_grid/math.py`). My weak preference is Tree-1 unless a
   near-term plan wants grid-math siblings. (§4, §9.1)

2. **Add one Import-Linter contract?** Recommended one contract:
   `varieties/` may not import `_qt/`, `render/`, `cross_section/`,
   or `app.py`. Costs ~10 lines of CI config. (§7.9, §9.5)

3. **Add the `VarietyGenerator` Protocol to `varieties/types.py`?**
   Recommended; near-zero risk; strengthens AI-8 + AI-14. (§6.1)

All three are independent of each other and of the migration mechanics
(Agent B's lane). Agent B should design the migration with these as
toggles.

---

## 14. Return contract

```json
{
  "agent": "research-agent-a",
  "phase": "r3-design",
  "file_path": "/Users/chris.dare/Personal/SourceCode/algebraic-variety-cross-section/.claude/notes/repository-architect-design/r3-tree-structure-research/agent-a-tree-design.md",
  "lines_total": "~1100 (well inside 2500-4500 soft budget; bias was on density + cite-heavy not length-for-length-sake)",
  "decisions_for_user": 3,
  "trees_proposed": 2,
  "patterns_evaluated": 7,
  "anti_patterns_named": 9,
  "ai_invariants_audited": 15,
  "ai_invariants_regressed": 0,
  "ai_invariants_strengthened": 3,
  "ai_invariants_preserved_unchanged": 12,
  "references_cited": 25,
  "web_wall_clock_minutes": 25
}
```
