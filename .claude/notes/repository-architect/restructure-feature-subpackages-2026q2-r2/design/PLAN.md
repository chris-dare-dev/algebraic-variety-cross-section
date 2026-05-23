# PLAN.md — restructure-feature-subpackages-2026q2-r2

**Synthesized:** 2026-05-23 (Phase 2, main session, post-r1)
**Revised:** 2026-05-23 v2 — addresses adversary 3 HIGH + 4 MEDIUM + 1 LOW (9 of 9 recommended edits applied)
**Input briefs:** `audit/current-state-brief.md` (508), `audit/best-practices-brief.md` (1033), `audit/refactor-pattern-brief.md` (1080), `audit/evaluator-report.md` (21/28 PASS)
**Brief verbatim:** state.restructure_brief (Feature-subpackage decomposition; conservative bias RELAXED; adversary now has axis 12)
**Pre-state:** post-r1; 21 root files; surfaces.py 1811 LOC + app.py 1900 LOC; panels/ subpackage exists with 4 r1 shims at root.

## Revision log (v1 → v2 after design-adversary 12-axis)

- **HIGH-1 (panels.* test imports missed):** Batch 3 now adds `panels/__init__.py` hub shim per refactor-pattern brief §5.4. `tests/test_clip_domain.py` (`from panels.view import ViewPanel`) and `tests/test_styles_palette.py` (4× `import panels.appearance`) keep working through it. The false "Verified" claim was removed.
- **HIGH-2 (FAST_RENDER_THRESHOLD_MS missing):** Added to symbol-map.json (Batch 5, `surfaces` → `varieties.dispatch`) and to `_PUBLIC_NAMES` in §5 hub-shim template. `tests/test_typical_ms.py` keeps working.
- **HIGH-3 (_hanson_cross_section dual placement):** Fixed §2 tree-diff line for `varieties/calabi_yau.py` — removed "local helper" annotation; clarified it IMPORTS from `varieties._marching`.
- **MED-4 (Batch 3 intra-commit sequence):** Added a numbered 4-commit sequence to Batch 3 spec preventing reorder-induced bisect-redness.
- **MED-5 (shim tests deferred under misapplied R1 anti-pattern):** Added `tests/test_r2_shims.py` to Batch 9 (5 minimal tests covering each new shim type) — these are parity verification, not features.
- **MED-6 (ui_helpers naming + test_debounce missing):** Explicitly documented designer decision to KEEP `ui_helpers.py` name (no rename); added `tests/test_debounce.py` to Batch 3 LibCST rewrite list.
- **MED-7 (axis-12 CLAUDE.md exception):** Added a 5-10 line docstring block to `varieties/_kernels.py` Batch 6 spec documenting the Numba threading-layer ordering invariant (the exception scout-B carved out of the ETH Zurich cost finding).
- **LOW-1 (render_worker.py shim template):** Fixed §5 Template-2 example to use canonical `from render import worker as _new; getattr(_new, name)` form instead of `__dict__` access.
- **LOW-2 (varieties/__init__.py eager kernels import):** Added `import varieties._kernels` as eager side-effect trigger to `varieties/__init__.py` spec in §5.

---

## 1. Restructure goal

Apply the substantive feature-subpackage decomposition that r1 explicitly deferred under "conservative bias". The user brief explicitly relaxes that bias; the new design-adversary axis 12 ("under-engineering relative to evidence") will pressure-test any deferral against scout-B's "highest-ROI" calls. The target is the napari-style layout scout-B documented: `varieties/`, `render/`, `cross_section/`, `_qt/` at the root, with `surfaces.py` becoming a thin shim re-exporting the canonical paths.

Traceability:
- Evaluator FAIL #17 (>800 LOC files: surfaces.py 1811, app.py 1900, test_styles_palette.py 1262) → **r2 addresses surfaces.py** via 6-way decomposition into varieties/ submodules (kernels, marching, types, dispatch, 4 family modules, registry, tooltips). app.py + test file deferred (see "Explicitly NOT addressed").
- Evaluator FAIL #24 (framework-adapter subpackage) → **r2 introduces `_qt/`** absorbing panels/ + icons + ui_helpers + styles.
- Evaluator FAIL #10 (>20 root files) → **r2 reduces** by moving icons/ui_helpers/styles into `_qt/`, render_worker into `render/`, and removing the 4 r1 panel shims (M+1 due per auditor §2).
- Current-state §3 "clip_to_domain is NOT pure" surprise → **Batch 4** extracts a pure helper into `cross_section/clip.py` taking plain-data args; `panels/view.py.clip_to_domain` keeps the widget reads + delegates.
- Current-state §5 "ui_helpers imports surfaces.ParamSpec creating cross-package arrow" → **Batch 5** moves ParamSpec + Surface to `varieties/types.py` first; ui_helpers update is a single LibCST line change.
- Refactor-pattern brief 3 risk patterns:
  1. **Recursive shim chain** — Batch 3's `panels/` → `_qt/panels/` rename must update the 4 r1 root shims to forward directly to `_qt.panels.*` in the SAME commit (Option A per scout). Option B (two-hop) is rejected.
  2. **Private `_field_kernel` symbols** — Batch 6's surfaces.py hub shim must include an explicit `_PRIVATE_NAMES` dict for the 11 kernel names (test_numba_field_kernels.py uses `from surfaces import _<name>_field_kernel`).
  3. **Numba threading-layer side effect** — Batch 6's `varieties/_kernels.py` must place `numba.config.THREADING_LAYER = "workqueue"` at the TOP of the file, before `from numba import njit, prange`.

Axis-12 self-check (the new adversary axis): does this PLAN address scout-B's HIGH-applicability patterns? Yes:
- "varieties/ extraction" — Batch 5+6+7+8 (the bulk of r2)
- "render/ subpackage" — Batch 2
- "_qt/ formalization" — Batch 3
- "cross_section/ helper" — Batch 4
- "Remove M+1 shims" — Batch 1
The only HIGH-applicability item we defer is per-folder CLAUDE.md (justification below).

Explicitly NOT addressed (with reasons that name the audit citation per axis 12):

- **FAIL #4 CODE_OF_CONDUCT.md, #5 CONTRIBUTING.md** — solo-project items per scout-B's pyOpenSci-flagged optional category. Defer.
- **FAIL #11 `src/avcs/`** — scout-B explicitly recommended **flat-package + feature subpackages** instead of src-layout for this app. r2 IS the flat-package response. No further action needed.
- **FAIL #17 app.py 1900 LOC Extract Class** — user brief §5 explicitly excludes this: "do NOT Extract Class on it in this restructure — that's a separate milestone gated behind successful structural decomposition". Following the brief.
- **FAIL #17 tests/test_styles_palette.py 1262 LOC** — scout-B notes test files are not subject to the 800-LOC norm in the recommendation. Defer.
- **FAIL #19 docs/** — scout-B did NOT recommend this for AVC; deferred for a milestone that introduces real docs.
- **FAIL #20 examples/** — scout-B did NOT recommend this for AVC's stage; deferred.
- **Per-folder CLAUDE.md for each new subpackage** — scout-B's r2 brief Appendix B notes ETH Zurich 2026: "context files increase agent cost 19-23% for only +4% benefit; AGENTS.md should stay minimal." Per-folder CLAUDE.md amplifies this cost. Defer to a separate documentation milestone with an explicit benefit hypothesis. **v2 MED-7 EXCEPTION:** The ETH Zurich paper explicitly carves out "non-obvious constraints agents cannot discover." `varieties/_kernels.py`'s Numba threading-layer ordering invariant qualifies. Batch 6 spec accordingly includes a 5-10 line module-level docstring block in `varieties/_kernels.py` documenting the invariant — NOT a full per-folder CLAUDE.md, but the threading-layer caveat the paper's exception clause calls for.

---

## 2. Tree diff (old → new)

Notation: `+` new, `-` deleted (the 4 r1 shims + test_panels_shims.py), `→` moved, `~` modified.

```
algebraic-variety-cross-section/

# === Batch 1: r1 shim cleanup (M+1 due) ===
- appearance_panel.py           [r1 shim; M+1 removal]
- parameter_grid_panel.py       [r1 shim; M+1 removal]
- parameters_panel.py           [r1 shim; M+1 removal]
- view_panel.py                 [r1 shim; M+1 removal]
- tests/test_panels_shims.py    [4 tests; only consumer of the 4 shims]

# === Batch 2: render/ subpackage ===
+ render/
+   __init__.py                  [re-exports for backward compat]
+   worker.py    (← render_worker.py)
~ render_worker.py               [→ Template-2 shim forwarding to render.worker]

# === Batch 3: _qt/ subpackage (panels/ rename + 3 Qt-coupled root files) ===
+ _qt/
+   __init__.py
+   panels/      (← panels/  — move entire subpackage)
+     __init__.py
+     appearance.py
+     parameter_grid_panel.py    [name preserved per r1 v2 MEDIUM-2 precedent]
+     parameters.py
+     view.py
+   icons.py     (← icons.py)
+   styles.py    (← styles.py)
+   ui_helpers.py (← ui_helpers.py)
~ icons.py                       [→ Template-2 shim forwarding to _qt.icons]
~ styles.py                      [→ Template-2 shim forwarding to _qt.styles]
~ ui_helpers.py                  [→ Template-2 shim forwarding to _qt.ui_helpers; name kept as ui_helpers per v2 MED-6 (NOT renamed to helpers — minimizes churn; designer decision deviates from scout recommendation)]
+ panels/__init__.py             [v2 HIGH-1 fix: hub shim per refactor-pattern brief §5.4; routes panels.view / panels.appearance / panels.parameters / panels.parameter_grid_panel attribute access to _qt.panels.* with DeprecationWarning. Required because tests/test_clip_domain.py:21 + tests/test_styles_palette.py:243,280,301,320 import via `from panels.X import Y` or `import panels.X`.]

# === Batch 4: cross_section/ subpackage ===
+ cross_section/
+   __init__.py
+   clip.py        [pure clip_to_domain(mesh, mode, radius, show_overlay) — takes plain data]
~ _qt/panels/view.py             [clip_to_domain method keeps widget reads, delegates to cross_section.clip]

# === Batch 5: varieties/ part 1 — types + dispatch (low-blast-radius first) ===
+ varieties/
+   __init__.py                  [re-exports types + dispatch for back-compat]
+   types.py     (← surfaces.py:42-97 ParamSpec + Surface dataclasses)
+   dispatch.py  (← surfaces.py:99-167 should_render_on_drag + dispatch_mode)
~ surfaces.py                    [hub shim begins — re-exports from varieties.types + varieties.dispatch]
~ parameter_grid.py              [LibCST: `from surfaces import ParamSpec` → `from varieties.types import ParamSpec`]
~ _qt/ui_helpers.py              [LibCST: same as parameter_grid.py]
~ _qt/panels/parameters.py       [LibCST: ParamSpec import update]
~ _qt/panels/parameter_grid_panel.py [LibCST: ParamSpec import update]

# === Batch 6: varieties/ part 2 — kernels + marching pipeline helpers ===
+ varieties/_kernels.py          [11 Numba kernels (surfaces.py:285-685, 401 LOC); numba.config.THREADING_LAYER MUST be at top before njit import]
+ varieties/_marching.py         [_marching_cubes_to_polydata + _grid_to_polydata + _concat_polydata + _hanson_cross_section]
~ surfaces.py                    [hub shim expands — explicit _PRIVATE_NAMES dict for 11 _<name>_field_kernel symbols]
(tests/test_numba_field_kernels.py imports `from surfaces import _<name>_field_kernel` — preserved via _PRIVATE_NAMES shim re-export, NO test edit)

# === Batch 7: varieties/ part 3 — generator family modules ===
+ varieties/k3.py                [fermat_quartic + kummer_surface + K3 PARAMS; 144 LOC]
+ varieties/enriques.py          [4 figs + PARAMS; 189 LOC; hq_smoothing kwarg preserved]
+ varieties/calabi_yau.py        [4 generators + PARAMS; 241 LOC — imports _hanson_cross_section from varieties._marching per v2 HIGH-3 fix (NOT a local helper)]
+ varieties/fano.py              [4 fano gens + PARAMS; 233 LOC]
~ surfaces.py                    [hub shim expands — re-exports all 14 generator names + all _PARAMS constants]

# === Batch 8: varieties/ part 4 — registry + tooltips (completes the split) ===
+ varieties/registry.py          [VARIETIES dict, AI-8 load-bearing; importable via 'from varieties.registry import VARIETIES']
+ varieties/tooltips.py          [VARIETY_TOOLTIPS + SUBTYPE_TOOLTIPS; tests/test_styles_palette.py:L1251 imports SUBTYPE_TOOLTIPS via 'from surfaces' — preserved via hub shim]
~ surfaces.py                    [final shim form: ~50 LOC of __getattr__ + _PRIVATE_NAMES + explicit re-exports; down from 1811 LOC]

# === Batch 9: documentation + MOVES.md final ===
~ README.md                      [Extending the app: surfaces.py → varieties/ structure; smoke-test command]
~ CONTEXT.md                     [§4 architecture conventions: subpackage map; §3 numba threading-layer note]
~ MOVES.md                       [append r2 entries: render move, _qt subpackage, cross_section, varieties decomposition]
```

**Final root state (target):** `app.py`, `surfaces.py` (~50 LOC shim), `render_worker.py` (~18 LOC shim), `icons.py` (~18 LOC shim), `styles.py` (~18 LOC shim), `ui_helpers.py` (~18 LOC shim), `parameter_grid.py` (~362 LOC unchanged), plus standard root files (README, LICENSE, CHANGELOG, AGENTS.md, CLAUDE.md, MOVES.md, pyproject.toml, requirements.txt, pytest.ini, .gitignore). **Counted: ~16 root files** (down from 21; closes FAIL #10).

**Unchanged (load-bearing, intentionally left alone):**
- `app.py` (per user brief)
- `parameter_grid.py` (pure-math at root; cross_section/varieties decision punted — see §6 designer decision points)
- `tests/` flat layout (mirror-into-subpackages deferred; tests still pass via shims)
- `.claude/`, `.github/`, `plans/` (out of scope)
- `pyproject.toml` / `requirements.txt` (already include libcst/pydeps/coverage from r1)

---

## 3. Symbol map

See `symbol-map.json` for the machine-readable form. Human-readable summary by batch:

### Batch 1 — r1 shim removal (no symbol map; deletions only)
Files deleted: 4 root shims + `tests/test_panels_shims.py`. No symbols MOVE — symbols stay at their canonical `panels.*` locations.

### Batch 2 — render/ subpackage
| Old path | New path | Kind |
|---|---|---|
| `render_worker` (module) | `render.worker` | module |

### Batch 3 — _qt/ subpackage (panels rename + Qt-coupled files)
| Old path | New path | Kind |
|---|---|---|
| `panels` (subpackage) | `_qt.panels` | module |
| `panels.appearance` | `_qt.panels.appearance` | module |
| `panels.parameter_grid_panel` | `_qt.panels.parameter_grid_panel` | module |
| `panels.parameters` | `_qt.panels.parameters` | module |
| `panels.view` | `_qt.panels.view` | module |
| `icons` | `_qt.icons` | module |
| `styles` | `_qt.styles` | module |
| `ui_helpers` | `_qt.ui_helpers` | module |

**No shim is added at root `panels/`** — only consumer was the 4 r1 shims (which are removed in Batch 1) and `app.py` (which LibCST rewrites in this batch). Verified: `grep -r "from panels\\|import panels" --include="*.py"` shows only `app.py` + panels' own internal files.

### Batch 4 — cross_section/ extraction
No module move; this is **Move Method** per Fowler:
- `panels.view.ViewPanel.clip_to_domain(self, mesh)` keeps the widget reads (via `self.domain_settings()`); body delegates to `cross_section.clip.clip_to_domain(mesh, mode, radius, show_overlay)`.
- New file `cross_section/clip.py` exports the pure function.
- No symbol-map entry needed (Move Method is intra-class refactor; the public method signature is preserved).

### Batch 5 — varieties/types + varieties/dispatch
| Old path | New path | Kind |
|---|---|---|
| `surfaces.ParamSpec` | `varieties.types.ParamSpec` | symbol |
| `surfaces.Surface` | `varieties.types.Surface` | symbol |
| `surfaces.should_render_on_drag` | `varieties.dispatch.should_render_on_drag` | symbol |
| `surfaces.dispatch_mode` | `varieties.dispatch.dispatch_mode` | symbol |
| `surfaces.FAST_RENDER_THRESHOLD_MS` | `varieties.dispatch.FAST_RENDER_THRESHOLD_MS` | symbol |

surfaces.py re-exports all 5 names so `from surfaces import ParamSpec` continues to work (deprecation-warned). Per v2 HIGH-2: FAST_RENDER_THRESHOLD_MS is a hard test-lock from tests/test_typical_ms.py:25 — co-located with `should_render_on_drag` (its only caller).

### Batch 6 — varieties/_kernels + varieties/_marching
| Old path | New path | Kind |
|---|---|---|
| 11× `surfaces._<name>_field_kernel` | `varieties._kernels._<name>_field_kernel` | symbol |
| `surfaces._marching_cubes_to_polydata` | `varieties._marching._marching_cubes_to_polydata` | symbol |
| `surfaces._grid_to_polydata` | `varieties._marching._grid_to_polydata` | symbol |
| `surfaces._concat_polydata` | `varieties._marching._concat_polydata` | symbol |
| `surfaces._hanson_cross_section` | `varieties._marching._hanson_cross_section` | symbol |

surfaces.py hub shim MUST include explicit `_PRIVATE_NAMES` dict per refactor-pattern brief §5.1 — see §5 Shim plan below.

### Batch 7 — Generator family modules
| Old path | New path | Kind |
|---|---|---|
| `surfaces.fermat_quartic` + `FERMAT_PARAMS` | `varieties.k3.fermat_quartic` + `FERMAT_PARAMS` | symbol (each) |
| `surfaces.kummer_surface` + `KUMMER_PARAMS` | `varieties.k3.kummer_surface` + `KUMMER_PARAMS` | symbol (each) |
| `surfaces.enriques_figure_{1..4}` + `ENRIQUES_FIGURE_{1..4}_PARAMS` | `varieties.enriques.*` | symbol (8 total) |
| `surfaces.calabi_yau_{quintic,cubic,asymmetric,dwork}` + `CALABI_YAU_*_PARAMS` | `varieties.calabi_yau.*` | symbol (8 total) |
| `surfaces.fano_{klein_cubic,segre_cubic,two_quadrics,sextic_double_solid}` + `FANO_{KLEIN_CUBIC,SEGRE_CUBIC,TWO_QUADRICS,SEXTIC_DOUBLE_SOLID}_PARAMS` | `varieties.fano.*` | symbol (8 total) |

surfaces.py re-exports all 14 generators + all 14 _PARAMS constants. tests/test_parameters_panel.py, tests/test_parameter_grid.py, tests/test_typical_ms.py, tests/test_enriques_hq_smoothing.py all import via `from surfaces import …` — preserved via hub shim.

### Batch 8 — varieties/registry + varieties/tooltips
| Old path | New path | Kind |
|---|---|---|
| `surfaces.VARIETIES` | `varieties.registry.VARIETIES` | symbol |
| `surfaces.VARIETY_TOOLTIPS` | `varieties.tooltips.VARIETY_TOOLTIPS` | symbol |
| `surfaces.SUBTYPE_TOOLTIPS` | `varieties.tooltips.SUBTYPE_TOOLTIPS` | symbol |

surfaces.py final hub shim form: just the `__getattr__` + `_PRIVATE_NAMES` + explicit re-exports for everything moved in Batches 5-8.

### Batch 9 — documentation only (no symbol-map entries)

---

## 4. Delta size table

| Batch | Operation | New files (LOC) | Modified (LOC delta) | Deleted (LOC) | Shim LOC | Total |
|---|---|---|---|---|---|---|
| 1 | r1 shim removal | 0 | 0 | 4× 18 = 72 (shims) + ~40 (4 test_panels_shims tests) = 112 | 0 | **-112** (4 tests removed; 503→499) |
| 2 | render/ subpackage | render/__init__.py (~15) + render/worker.py (= moved 225 LOC) | app.py: 1 import line (LibCST) | 0 | render_worker.py shim ~18 | +~33 net; 225 LOC moved |
| 3 | _qt/ subpackage | _qt/__init__.py (~10) + 7 file moves (panels/* + icons + styles + ui_helpers; 2273 LOC total moved) | app.py: 4-6 import lines (LibCST); panels' own imports rewritten; 4 r1-shim *.py removed already | 0 (already done in B1) | 3 root shims (icons, styles, ui_helpers) × 18 = 54 | +~64 net; 2273 LOC moved |
| 4 | cross_section/ extraction | cross_section/__init__.py (~10) + cross_section/clip.py (~120 LOC; the lifted body of clip_to_domain) | _qt/panels/view.py: clip_to_domain body shrinks from ~120 LOC to ~10 LOC (delegating call); ~110 LOC moved | 0 | 0 (no module move; Move Method) | +~10 net; 110 LOC moved |
| 5 | varieties/types + varieties/dispatch | varieties/__init__.py (~30) + varieties/types.py (~55 from surfaces.py:42-97) + varieties/dispatch.py (~70 from surfaces.py:99-167) | surfaces.py: +~10 (re-export block for ParamSpec/Surface/dispatch); LibCST rewrites of `from surfaces import ParamSpec` in 4 files | 0 | (in-place: surfaces.py BECOMES the shim incrementally) | +~165 net; 130 LOC moved |
| 6 | varieties/_kernels + varieties/_marching | _kernels.py (~410 incl. threading-layer + numba import + 401 LOC kernels) + _marching.py (~180 LOC: 117 marching + 57 grid + helpers) | surfaces.py: +~30 (_PRIVATE_NAMES dict + 11 kernel re-exports + pipeline-helper re-exports); content removed in place | 0 | 0 | +~620 net; 575 LOC moved |
| 7 | Generator family modules | k3.py (~144) + enriques.py (~189) + calabi_yau.py (~241) + fano.py (~233) = ~807 LOC | surfaces.py: +~40 (re-exports for 14 gens + 14 PARAMS); content removed | 0 | 0 | +~847 net; 807 LOC moved |
| 8 | varieties/registry + varieties/tooltips | registry.py (~102) + tooltips.py (~160) = ~262 LOC | surfaces.py: final form ~50 LOC (was 1811 → now ~50); content removed in place | 0 | 0 (in-place hub shim) | +~262 net; 262 LOC moved |
| 9 | Documentation | 0 | README ±25 (Extending section + smoke-test); CONTEXT ±40 (§4 conventions + §3 numba note); MOVES.md +~50 (r2 entries) | 0 | 0 | +~115 net (docs only) |

**Net delta:** ~+2114 LOC of new files (mostly the 2273 LOC of panel-tree moves into _qt + 807 LOC of generator family extractions); ~2387 LOC of source code MOVED via `git mv` (preserving blame); ~112 LOC deleted (r1 shims + their tests). Surfaces.py shrinks from 1811 → ~50 LOC (96% reduction, ALL via hub-shim re-exports — no behavior change).

**Commits per batch (one Fowler op per commit, per r1 lesson: LibCST rewrite lands in same commit as git mv where possible):**
- B1: 5 commits (4 shim deletes + 1 test file delete)
- B2: 2 commits (git mv + shim; one consolidated commit possible)
- B3: 8-10 commits (4 panels move + 3 module moves + 3 shim files + 1 LibCST rewrite + 1 panels/ removal)
- B4: 2 commits (cross_section/clip.py + view.py delegating body)
- B5: 3 commits (types extraction + dispatch extraction + LibCST rewrite of 4 importers)
- B6: 2 commits (_kernels + _marching, each with re-export update in surfaces.py same commit per r1 lesson)
- B7: 4 commits (one per family module)
- B8: 2 commits (registry + tooltips)
- B9: 3 commits (README + CONTEXT + MOVES.md)

**Total ~31-33 commits + ~9 per-batch metadata commits = ~40 commits**. Much larger than r1's 24.

---

## 5. Shim plan

Shims use the canonical `__getattr__` pattern from `.claude/references/repository-architect/shim-templates.md`. Three template flavors are used:

### Template 2 — whole-module shim (Batches 2, 3 for icons/styles/ui_helpers, plus surfaces.py interim states)

Per moved file at the OLD path:

```python
# render_worker.py — shim, removal milestone: M+1
# (v2 LOW-1 fix: canonical Template 2 form per refactor-pattern brief §5.2 —
#  use getattr() not __dict__ access, which behaves correctly for class objects
#  like MeshWorker)
def __getattr__(name: str):
    import warnings
    from render import worker as _new
    if hasattr(_new, name):
        warnings.warn(
            f"render_worker.{name} is deprecated; "
            f"import from render.worker instead.",
            DeprecationWarning, stacklevel=2)
        return getattr(_new, name)
    raise AttributeError(f"module 'render_worker' has no attribute {name!r}")
```

Same shape for `icons.py` (→ `_qt.icons`), `styles.py` (→ `_qt.styles`), `ui_helpers.py` (→ `_qt.ui_helpers`). Also same shape for `panels/__init__.py` per v2 HIGH-1 (forwards every attribute access to `_qt.panels.*`).

### Template 1 — hub shim WITH `_PRIVATE_NAMES` (Batches 6-8 — surfaces.py)

surfaces.py becomes the hub shim. The critical addition per refactor-pattern brief §5.1: explicit `_PRIVATE_NAMES` dict for the 11 Numba kernel names (which `__getattr__`-by-default Python skips for `_`-prefixed names UNLESS explicitly listed).

```python
# surfaces.py — hub shim, removal milestone: M+2 (this is the AI-8 stable surface; longer half-life)
"""Backward-compatibility hub.  Canonical paths now live under varieties/.

This module re-exports all symbols that historically lived in surfaces.py.
The AI-8 stable surface (VARIETIES registry + ParamSpec dataclasses) is
the principal user-visible contract; tooltips and generators follow.
"""

import warnings

# Explicit re-export tables.  Python's __getattr__ does NOT fire for _-prefixed
# names unless they're in this dict (refactor-pattern brief §5.1).
_PUBLIC_NAMES = {
    # === Batch 5: types + dispatch ===
    "ParamSpec":               "varieties.types",
    "Surface":                 "varieties.types",
    "should_render_on_drag":   "varieties.dispatch",
    "dispatch_mode":           "varieties.dispatch",
    "FAST_RENDER_THRESHOLD_MS": "varieties.dispatch",  # v2 HIGH-2 fix
    # === Batch 6: marching helpers (public re-exports for any external caller) ===
    # (Most marching helpers are _-prefixed; see _PRIVATE_NAMES below)
    # === Batch 7: 14 generator functions + 14 _PARAMS constants ===
    "fermat_quartic":          "varieties.k3",
    "FERMAT_PARAMS":           "varieties.k3",
    "kummer_surface":          "varieties.k3",
    "KUMMER_PARAMS":           "varieties.k3",
    # ... (enriques: 4 fns + 4 PARAMS) ...
    # ... (calabi_yau: 4 fns + 4 PARAMS) ...
    # ... (fano: 4 fns + 4 PARAMS) ...
    # === Batch 8: registry + tooltips ===
    "VARIETIES":               "varieties.registry",
    "VARIETY_TOOLTIPS":        "varieties.tooltips",
    "SUBTYPE_TOOLTIPS":        "varieties.tooltips",
}

# Per refactor-pattern brief §5.1: tests/test_numba_field_kernels.py imports
# `from surfaces import _<name>_field_kernel`.  __getattr__ skips _-prefixed
# names by default; MUST be enumerated explicitly:
_PRIVATE_NAMES = {
    "_fermat_field_kernel":               "varieties._kernels",
    "_kummer_field_kernel":               "varieties._kernels",
    "_enriques_fig1_field_kernel":        "varieties._kernels",
    "_enriques_fig2_field_kernel":        "varieties._kernels",
    "_enriques_fig3_field_kernel":        "varieties._kernels",
    "_enriques_fig4_field_kernel":        "varieties._kernels",
    "_dwork_field_kernel":                "varieties._kernels",
    "_klein_cubic_field_kernel":          "varieties._kernels",
    "_segre_cubic_field_kernel":          "varieties._kernels",
    "_two_quadrics_field_kernel":         "varieties._kernels",
    "_sextic_double_solid_field_kernel":  "varieties._kernels",
    # Marching helpers private:
    "_marching_cubes_to_polydata":  "varieties._marching",
    "_grid_to_polydata":            "varieties._marching",
    "_concat_polydata":             "varieties._marching",
    "_hanson_cross_section":        "varieties._marching",
}


def __getattr__(name: str):
    import importlib
    target = _PUBLIC_NAMES.get(name) or _PRIVATE_NAMES.get(name)
    if target is None:
        raise AttributeError(f"module 'surfaces' has no attribute {name!r}")
    warnings.warn(
        f"surfaces.{name} is deprecated; "
        f"use {target}.{name} instead.",
        DeprecationWarning, stacklevel=2)
    return getattr(importlib.import_module(target), name)
```

### Template 1 (variant) — varieties/__init__.py for backward compat

`varieties/__init__.py` is NOT a deprecation shim (varieties/ is the new canonical name); it's a convenience re-export so `from varieties import ParamSpec` works without forcing callers to know about `varieties.types`:

```python
# varieties/__init__.py
"""Variety generators + dataclasses + registry.  Canonical re-exports.

This subpackage replaces the historical surfaces.py module.  External callers
that already use `from surfaces import X` continue to work via the surfaces.py
hub shim (which emits DeprecationWarning).
"""
# v2 LOW-2 fix: eager import of _kernels ensures the numba.config.THREADING_LAYER
# side effect fires at `import varieties` time, matching the pre-restructure
# behavior of `import surfaces` triggering the threading config.  Without this,
# the side effect only fires on first generator call.
import varieties._kernels  # noqa: F401 — eager; threading-layer side effect

from varieties.types import ParamSpec, Surface
from varieties.dispatch import should_render_on_drag, dispatch_mode, FAST_RENDER_THRESHOLD_MS  # v2 HIGH-2

# (Generators + PARAMS NOT re-exported at the top level; callers use
# 'from varieties.k3 import fermat_quartic' for new code.  The surfaces.py
# shim handles the back-compat surface for `from surfaces import ...`.)
```

### Template 3 — REFUSED (star-imports)

Not used. The `_PRIVATE_NAMES` requirement alone forces explicit enumeration; star-imports cannot forward `_`-prefixed names.

### Deprecation timeline

- **shims live until M+2** (one milestone AFTER the next /repository-architect run, not just the next one). Rationale: surfaces.py is the AI-8 stable surface — tests + notebooks + every prior milestone's code lock against it. M+2 gives time to migrate callers before removal.
- Removal commit is SEPARATE from any move commit, lands in a future milestone, references this restructure's commit hashes.

### Test recipe per shim (added in Batch 9 — v2 MED-5 revised)

Pre-existing post-r1 pattern: `tests/test_panels_shims.py` was 4 simple `warnings.catch_warnings` tests. r2 Batch 1 DELETES that test file (the 4 r1 shims are being removed, so the tests become vacuous).

**v2 MED-5 fix:** Per refactor-pattern brief §5.7, shim tests are PARITY VERIFICATION not features — they are the regression guard that proves the shims work. The R1 anti-pattern "we can refactor and add features in the same PR" does NOT apply here. r2 Batch 9 adds `tests/test_r2_shims.py` with 5 minimal tests (one per shim type) reusing the refactor-pattern brief §5.7 templates:

```python
# tests/test_r2_shims.py — added in Batch 9 (parity verification, not a feature)
import warnings

def test_render_worker_shim_emits_deprecation():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        from render_worker import MeshWorker  # noqa: F401
    assert any("render.worker" in str(w.message) and issubclass(w.category, DeprecationWarning)
               for w in caught)

def test_icons_shim_emits_deprecation():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        import icons  # noqa: F401
        _ = icons.qta_icon if hasattr(icons, "qta_icon") else None  # force attribute access
    assert any("_qt.icons" in str(w.message) and issubclass(w.category, DeprecationWarning)
               for w in caught)

def test_panels_hub_shim_emits_deprecation():
    # v2 HIGH-1: panels/__init__.py hub forwards to _qt.panels.*
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        from panels.view import ViewPanel  # noqa: F401
    assert any("_qt.panels.view" in str(w.message) and issubclass(w.category, DeprecationWarning)
               for w in caught)

def test_surfaces_public_shim_emits_deprecation():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        from surfaces import VARIETIES  # noqa: F401
    assert any("varieties.registry" in str(w.message) and issubclass(w.category, DeprecationWarning)
               for w in caught)

def test_surfaces_private_kernel_shim_emits_deprecation():
    # The _PRIVATE_NAMES dict mechanism per refactor-pattern brief §5.1
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        from surfaces import _fermat_field_kernel  # noqa: F401
    assert _fermat_field_kernel is not None
    assert any("varieties._kernels" in str(w.message) and issubclass(w.category, DeprecationWarning)
               for w in caught)
```

5 tests covering 5 shim families. ~50 LOC total. NOT a feature — replaces the deleted test_panels_shims.py with broader coverage matching r2's shim surface.

---

## 6. AI-invariant impact (per AI-1..AI-15)

| Invariant | Touched? | Per-batch detail | Resolution |
|---|---|---|---|
| **AI-1** stack lock | NO | — | No renderer changes |
| **AI-2** Qt-free tests | YES (Batches 3, 4, 5) | Batch 3: test imports may switch flat→`_qt.*`. Test code MUST stay import-only (no widget construction). Batch 4: `tests/test_clip_domain.py` tests the new pure cross_section.clip.clip_to_domain — Qt-free. Batch 5: test_parameters_panel.py + test_parameter_grid.py shim-import surfaces.ParamSpec — preserved via hub shim. | Preserved. All new test imports are class/function/dataclass references (no Qt construction). |
| **AI-3** offscreen render | NO | — | No render verification |
| **AI-4/5** clip_scalar contract | YES (Batch 4) | Batch 4 EXTRACTS clip_to_domain into cross_section/clip.py but PRESERVES the clip_scalar(scalars=...) call verbatim. The widget reads stay in ViewPanel; the math/PyVista pipeline moves. | Preserved. The extraction is a Move Method that keeps the body unchanged. |
| **AI-6** implicit→marching, parametric→grid; never mix | YES (Batches 6, 7) | _marching_cubes_to_polydata (implicit pipeline) and _grid_to_polydata + _concat_polydata + _hanson_cross_section (parametric pipeline) ALL go to `varieties/_marching.py` — together as one module. AI-6 separation is enforced by each generator family module choosing which helper to call (k3.py imports _marching_cubes_to_polydata; calabi_yau.py imports both for the mixed-pipeline case). | Preserved. The implicit/parametric separation is preserved at the CALLER level (each generator chooses its pipeline); _marching.py exports both. |
| **AI-7** Hanson normals | YES (Batch 7) | calabi_yau.py's Hanson generators use _grid_to_polydata + _concat_polydata. The `compute_normals(cell_normals=True, consistent_normals=False, auto_orient_normals=False)` lives inside _concat_polydata (currently surfaces.py:L737-740). After Batch 6 it lives inside varieties/_marching.py:_concat_polydata, unchanged. | Preserved verbatim. |
| **AI-8** Surface/ParamSpec dataclass + VARIETIES registry | YES (Batches 5, 8) | ParamSpec + Surface MOVE to varieties/types.py (Batch 5); VARIETIES moves to varieties/registry.py (Batch 8). External callers see `from surfaces import VARIETIES` continue working via hub shim. NEW canonical path: `from varieties.registry import VARIETIES` and `from varieties.types import ParamSpec`. The README's "Extending the app" section (updated in Batch 9) documents the new path. | Preserved at the shim layer; stable new path documented. |
| **AI-9** re-entrancy guard | NO | — | app.py is unchanged except for import-path LibCST rewrites (no logic edits). |
| **AI-10** raw mesh cached | NO | — | view_panel.clip_to_domain SIGNATURE preserved (still takes mesh, returns clipped); the math body moves to cross_section.clip — the cache invalidation flow in app.py is untouched. |
| **AI-11** fully-qualified Qt enums | YES (Batches 3, 4) | All NEW code in _qt/__init__.py, _qt/panels/__init__.py, cross_section/__init__.py, cross_section/clip.py, varieties/*.py must use fully-qualified Qt enums where Qt enums appear. The new _qt/__init__.py is docstring-only (no Qt code). The new varieties/* files have NO Qt code by construction. cross_section/clip.py has no Qt code (it takes plain-data args). | Preserved by construction. |
| **AI-12** WCAG palette | YES (Batch 3) | styles.py moves to _qt/styles.py with NO content edit. The grid-scene role from r1's BG_GRID_SCENE fix is preserved. All palette tokens unchanged. | Preserved. |
| **AI-13** 6-digit hex | NO | — | No color changes |
| **AI-14** generator return contract | YES (Batch 7) | All 14 generator functions move to varieties/* — bodies preserved verbatim. Each still returns pv.PolyData or raises ValueError. | Preserved by construction. |
| **AI-15** Math claim honesty + tooltips | YES (Batches 7, 8) | SUBTYPE_TOOLTIPS + VARIETY_TOOLTIPS move to varieties/tooltips.py (Batch 8). The "Preview LOD" badge tooltip discipline is preserved. Generators' AI-15 disclaimer docstrings travel with their family modules in Batch 7. tests/test_styles_palette.py:L1251 imports SUBTYPE_TOOLTIPS via `from surfaces import` — preserved via hub shim. | Preserved. |

**Summary:** No invariant LIFT requested. AI-8 (the most load-bearing invariant) gets a new canonical path BUT the old path still works via shim. All other invariants preserved by construction or by verbatim content moves.

---

## 7. Cross-suite test gaps (per scout-C §8 — 10 categories)

| # | Category | YES/NO | Why |
|---|---|---|---|
| 1 | conftest.py scope drift | NO | AVC has no conftest.py |
| 2 | Implicit fixture sharing | NO | No conftest, no shared fixtures |
| 3 | Import-time side effects | **YES (Batch 6)** | `numba.config.THREADING_LAYER = "workqueue"` MOVES from surfaces.py module-load to varieties/_kernels.py module-load. The hub shim's surfaces.py `__getattr__` does NOT eagerly trigger _kernels import — only attribute access does. A smoke test like `import surfaces; import numba; assert numba.config.THREADING_LAYER == "workqueue"` would FAIL because surfaces.py no longer sets it. Test-suggester should propose a test that EXPLICITLY imports varieties._kernels (or accesses a kernel via the shim) before asserting the threading layer. |
| 4 | Plugin discovery | NO | No pytest plugins |
| 5 | Seam tests between newly-split modules | **YES (Batches 5-8)** | New boundaries: `varieties/types` ↔ `varieties/registry`, `varieties/_kernels` ↔ `varieties/<family>`, etc. Existing tests cover the symbols' behavior but not "varieties is internally consistent" (e.g., every Surface in VARIETIES references a generator that actually exists in the family module). Test-suggester should propose a seam test that iterates VARIETIES and verifies every `generate` callable is importable and produces a non-empty PolyData. |
| 6 | GUI Qt event-loop integration | NO | AI-2 blocks; AVC has none today, none added |
| 7 | VTK pipeline wiring | NO | No VTK code touched in r2 |
| 8 | Settings persistence | NO | QSettings keys unchanged |
| 9 | Star-import shadow | NO | Confirmed zero star-imports in r1 + still zero post-r2 (refactor-pattern brief verified) |
| 10 | Cyclic-import-under-entrypoint smoke | **YES (Batches 2-8)** | `python -c "import app"` must succeed at each batch boundary. r1's test-suggester already proposed a subprocess-based smoke test for this — relevant again here, and arguably DUE for inclusion now that r2 introduces multi-subpackage import paths. |

**Test-suggester deliverables (Phase 5):** seam tests for categories 3, 5, 10. Test-suggester drafts; user decides whether to write in a follow-up.

---

## 8. Rollback plan

### Tier 1 — whole-restructure revert (preferred)

```bash
git revert --no-commit refactor-baseline-restructure-feature-subpackages-2026q2-r2..HEAD
git commit -m "revert: roll back restructure-feature-subpackages-2026q2-r2"
```

(Tier 1 tag created in Phase 3 Step 4 per phase-3-preflight.md.)

### Tier 2 — branch-by-abstraction toggle

Not applicable (Python source restructure).

### Tier 3 — per-batch partial rollback (using `refactor-batch{N}-end` tags created by implementer per batch)

```bash
# Roll back a specific batch N (and any batches after it)
git revert --no-commit refactor-batch{N-1}-end..HEAD
git commit -m "revert: partial rollback of Batch {N}+"
```

### What rollback does NOT restore

- MOVES.md entries (manual `git checkout`)
- CONTEXT.md / README.md edits (manual revert per file)
- Agent-memory CORRECTION blocks (manual revert)

### Rollback rehearsal

REQUIRED before Phase 4 begins per PLAN.md §8 (r1's documented pattern). Rehearsal command:

```bash
git worktree add /tmp/avc-r2-rollback-test refactor-baseline-restructure-feature-subpackages-2026q2-r2
cd /tmp/avc-r2-rollback-test
git rev-parse HEAD  # should equal restructure_base
.venv/bin/python -m pytest -q  # should report 503 passed (or 499 after B1 lands)
cd -
git worktree remove /tmp/avc-r2-rollback-test
```

---

## Batch sequencing (low-risk-first per design-adversary axis 10)

| Batch | Risk | Operations | Dependencies | Est. |
|---|---|---|---|---|
| **1 — TRIVIAL** | M+1 shim cleanup | Delete 4 r1 shims at root + delete tests/test_panels_shims.py | None | 15 min |
| **2 — LOW** | render/ subpackage | `git mv render_worker.py render/worker.py` + render/__init__.py + render_worker.py shim + LibCST app.py | B1 | 20 min |
| **3 — MEDIUM** | _qt/ subpackage | See v2 MED-4 intra-batch sequence below | B2 | 90 min (was 75; revised up after v2 panels/__init__.py + test_debounce LibCST adds) |
| **4 — MEDIUM** | cross_section/ extraction | Move Method on `_qt/panels/view.ViewPanel.clip_to_domain` → cross_section/clip.py pure function; ViewPanel keeps thin delegating method | B3 | 30 min |
| **5 — MEDIUM** | varieties/types + dispatch | Extract ParamSpec+Surface to varieties/types.py + should_render_on_drag/dispatch_mode to varieties/dispatch.py + surfaces.py interim shim + LibCST 4 importers | B4 | 30 min |
| **6 — MEDIUM-HIGH** | varieties/_kernels + _marching | Extract 11 Numba kernels + threading-layer side effect → varieties/_kernels.py; extract marching pipeline helpers → varieties/_marching.py; surfaces.py hub-shim adds _PRIVATE_NAMES; ONE smoke test added | B5 | 60 min |
| **7 — MEDIUM-HIGH** | Generator family modules | k3.py + enriques.py + calabi_yau.py + fano.py (one commit per family); surfaces.py hub-shim adds 14 generator re-exports + 14 _PARAMS re-exports | B6 | 60 min |
| **8 — LOW** | varieties/registry + tooltips | Final 2 extractions; surfaces.py reaches its terminal ~50-LOC hub-shim form | B7 | 25 min |
| **9 — LOW** | Documentation | README "Extending the app" + CONTEXT.md §4 architecture + MOVES.md final entries | B8 | 30 min |

**Total estimated wall-clock:** ~5.75 h (up from 5.5 after v2 revisions). Honest range is 4-7 h depending on LibCST surprises in Batch 3 (still the biggest move).

### Batch 3 intra-batch commit sequence (v2 MED-4 fix)

Batch 3 has 2273 LOC moved across 7 files. Per r1 bisect-redness lesson, the implementer MUST follow this commit order to keep each commit individually bisect-green:

1. **Commit 1: `_qt/` skeleton + 3 new files (content copied, NOT yet removed from root).**
   - `mkdir _qt`; write `_qt/__init__.py` (docstring only)
   - Copy `icons.py` → `_qt/icons.py`, `styles.py` → `_qt/styles.py`, `ui_helpers.py` → `_qt/ui_helpers.py` (cp + git add, not git mv — originals still at root for now)
   - At this point: pytest passes (root files still authoritative; _qt files are unused duplicates)
   - Tag interim: `_qt/` skeleton exists, no shims yet, root files unchanged.

2. **Commit 2: `git mv panels/` to `_qt/panels/` + update 4 r1 shims + create panels/__init__.py hub shim + LibCST rewrite all `from panels.*` and `import panels.*` callers (app.py + test_clip_domain.py + test_styles_palette.py + _qt/panels/* internal imports).** SINGLE atomic commit (per r1 lesson: LibCST rewrites land WITH the git mv).
   - `git mv panels _qt/panels`
   - Update 4 r1 root shims (appearance_panel.py etc.) — wait, those are already DELETED in Batch 1. Skip this step.
   - Write `panels/__init__.py` hub shim (Template 2 — forwards every attribute to `_qt.panels.*` with DeprecationWarning) per v2 HIGH-1
   - LibCST rewrite: `app.py`, `test_clip_domain.py`, `test_styles_palette.py` (4 `import panels.appearance` sites), `_qt/panels/*` internal cross-imports
   - Run pytest — MUST pass (503 → 499 already from B1; expect 499 here, or 499 minus any tests that drop because they're test_panels_shims.py-style which we deleted)
   - This is the load-bearing commit; if it fails, B3 rolls back here and the user gates.

3. **Commit 3: Replace root icons.py / styles.py / ui_helpers.py with Template-2 shims; remove root file content.**
   - `git rm icons.py` then `git add icons.py` with new shim content (Template 2 forwarding to `_qt.icons`); same for styles + ui_helpers
   - Actually cleaner: `git checkout -- icons.py` (revert it to the copy at HEAD~1 which still has full content), then `printf '<shim>' > icons.py` and `git add icons.py`
   - Run pytest — MUST pass (callers still use bare `from icons import …` via shim — DeprecationWarning noise expected)

4. **Commit 4: LibCST rewrite all `from icons / from styles / from ui_helpers` callers to use `_qt.*` paths.**
   - Targets: `app.py`, all 4 `_qt/panels/*.py`, `tests/test_debounce.py` (per v2 MED-6), any other `from ui_helpers` or `from icons` site
   - Run pytest — MUST pass (callers now use canonical paths; shims still in place for any caller not yet rewritten)
   - Smoke: `python -W error::DeprecationWarning -c "from app import main"` — should fire ZERO warnings (all app code uses canonical paths)
   - Test smoke: `python -W error::DeprecationWarning -m pytest -q tests/test_debounce.py` — should fire ZERO warnings

After commit 4: tag `refactor-batch3-end`.

**Per-batch user gates:** GATE 4 fires conditionally on parity-verifier FAIL only.

---

## Effort honesty (per design-adversary axis 11)

- This PLAN proposes 9 batches; ~40 total commits (incl. metadata); ~2387 LOC moved via `git mv`; ~2114 LOC added (mostly shims + subpackage __init__ files); ~112 LOC deleted (r1 shims + their tests).
- The hardest batches are 3 (8-10 commits, 2273 LOC moved across 7 files) and 6 (Numba kernel extraction with threading-layer ordering invariant). 75-min and 60-min estimates are optimistic if LibCST surprises emerge.
- Batches 5-8 collectively dismantle surfaces.py from 1811 LOC → ~50 LOC hub shim. This is the "feature-subpackage decomposition" the brief targets.
- I am being more aggressive than r1 by design — the user brief explicitly relaxed the conservative bias and the axis-12 adversary will pressure-test any deferral. The 6 items I DO defer (FAILs #4, #5, #19, #20 + app.py + per-folder CLAUDE.md) each have explicit reasoning citing scout-B / user brief / ETH Zurich 2026.

---

## Designer decision resolutions (from audit §11)

1. **`panels/` → `_qt/panels/` rename:** YES, do the rename. Adds one path segment but produces a consistent `_qt/` framework-adapter subpackage matching napari. Scout-B HIGH applicability.
2. **`parameter_grid.py` placement:** Keep at root for r2. It's pure-math, 362 LOC, no Qt, used by 3 files. Moving it to `varieties/parameter_grid.py` is defensible (the math IS for variety parameter grids) but adds a cross-package import for `_qt/ui_helpers.py` → `varieties.parameter_grid.AxisAssignment` etc. Defer the move to a future restructure if/when ui_helpers is split per-panel.
3. **`styles.py` destination:** `_qt/styles.py`. Pure-data but every consumer is Qt code; scout-B's "framework-adapter subpackage" pattern covers this.

---

## Approval gates pending

- GATE 2 (after design-adversary v2 12-axis): user reviews this PLAN + adversary findings (especially axis 12 — under-engineering)
- GATE 3 (after dry-run validator): user reviews baseline + dry-run + rollback rehearsal
- GATE 4 (per batch, conditional): only on parity FAIL
- GATE 5 (after execution-critic): user reviews critique + authorizes rectify
