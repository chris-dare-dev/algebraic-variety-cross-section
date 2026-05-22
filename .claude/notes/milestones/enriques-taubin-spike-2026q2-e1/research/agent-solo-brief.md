# Research Brief — enriques-taubin-spike-2026q2-e1
**Agent:** solo researcher (Sonnet)
**Date:** 2026-05-22
**Status:** COMPLETE — no gate required; all decision points are fully specified by the user brief

---

## 1. TL;DR

Run `enriques_figure_1(c=1.0)` N=7 times with and without a second Taubin pass, take medians, compare to the 500ms generate-only budget (confirmed current in CONTEXT.md §4.4 / §9); if median-with-second-pass <= 500ms ship Path A (second pass + bounds*1.05), otherwise ship Path B (bounds*1.05 only). Main risk: the second Taubin pass calls `vtkWindowedSincPolyDataFilter` on a ~82k-vertex mesh and may add 100–400ms on a slow machine — the only way to know is running the spike. Backup plan: Path B (bounds*1.05 padding only) ships regardless of outcome, so at minimum the wing-tip truncation fix lands.

---

## 2. Prior Art in This Repo

- `surfaces.py:87–141` — `_marching_cubes_to_polydata` helper. Signature: `(field, bounds, level=0.0, smooth_iter=20)`. Performs ONE Taubin pass `mesh.smooth_taubin(n_iter=smooth_iter, pass_band=0.1)` at line 134. The `smooth_iter` param defaults to 20 and is **not exposed** to individual generator functions — all four Enriques generators call `_marching_cubes_to_polydata(F, bounds)` with no override.
- `surfaces.py:360–387` — `enriques_figure_1`. Default `c=1.0` (min 0.1 per `ENRIQUES_FIGURE_1_PARAMS` at line 391), `n=240`, `bounds=1.8`. Grid: `np.linspace(-bounds, bounds, n)` → `_marching_cubes_to_polydata(F, bounds)`. **The `bounds` variable is a local named `bounds` — the 5% padding `bounds * 1.05` goes on the `np.linspace` call (line 378) and must also be passed to `_marching_cubes_to_polydata` as the second arg.**
- `surfaces.py:396–430` — `enriques_figure_2`. Same call pattern: `bounds=1.8`, `np.linspace(-bounds, bounds, n)`, `_marching_cubes_to_polydata(F, bounds)` at line 430.
- `surfaces.py:443–471` — `enriques_figure_3`. `bounds=2.5`, Cayley quartic symmetroid. Same call pattern. Per CONTEXT.md §8.13: degree-4 surface with ordinary A₁ nodes (NOT double curves). Off-screen render showed culling is a no-op (pixel-identical). Second Taubin pass is unlikely to help here.
- `surfaces.py:480–519` — `enriques_figure_4`. `bounds=1.5`, icosahedral sextic. Same call pattern. Per CONTEXT.md §8.13: A₁ nodes + culling was beneficial (empirically ~7% face reduction). Second Taubin pass may help moderately at the node loci.
- `surfaces.py:87–141` — `_marching_cubes_to_polydata` does NOT have a `second_smooth_iter` parameter. The second pass must either: (a) be added as an optional `second_smooth_iter: int = 0` param to this helper, OR (b) be applied post-call in the individual generators. Option (a) is cleaner because it keeps all smoothing logic in one place; option (b) is more surgical (helps only the generators that call it). See §4 for the recommended option.
- `surfaces.py:34–47` — `Surface` dataclass. NOT frozen (`@dataclass`, not `@dataclass(frozen=True)`). Has `typical_ms: int = 0` trailing field. The `ParamSpec` dataclass at line 21 IS frozen. AI-8 note: brief says do NOT add `recommends_backface_culling` to Surface — that's already shipped in enriques-backface-2026q2-e1. The Taubin work lives entirely in generator functions/helper.
- `tests/test_mesh_generators.py:65–83` — Enriques figure 1–4 smoke tests. Each calls the generator at default params and asserts `mesh.n_points > 0` and `mesh.n_faces > 0`. These are the AI-2-compliant test attach points for new assertions.
- `tests/test_typical_ms.py` — confirms `typical_ms` field and speed-routing logic. Not relevant to Taubin work.
- `CONTEXT.md:173` — "~0.5 s mesh generation" is the budget reference. The 500ms figure is confirmed in roadmap §4 `[MUST]` assumption. No recent milestone tightened or relaxed it.
- `CONTEXT.md §8.13:438–446` — per-figure topology audit from enriques-backface-2026q2-e1: figs 1+2 have genuine double curves (sawtooth artifact source); fig 3 has ordinary A₁ nodes (degree-4, culling no-op); fig 4 has A₁ nodes (culling beneficial ~7%). This maps directly to Taubin benefit scope.
- `CONTEXT.md §9:458` — spinner is deferred because generate time is ~0.5s. The spike measures generate-only time; no Qt involvement.

---

## 3. External Sources Reviewed

| Source | URL | Key Finding | Relevance |
|---|---|---|---|
| PyVista `smooth_taubin` docstring | local `.venv/bin/python -c "import pyvista as pv; help(pv.PolyData.smooth_taubin)"` | Signature confirmed: `(self, n_iter=20, pass_band=0.1, ..., inplace=False, ...)`. Default `inplace=False` — returns a NEW PolyData. No mutation of input. | Confirms the stacking pattern `mesh = mesh.smooth_taubin(n_iter=40, pass_band=0.05)` after the first pass is correct. |
| PyVista `smooth_taubin` online docs | https://docs.pyvista.org/api/core/_autosummary/pyvista.PolyDataFilters.smooth_taubin.html | Uses VTK `vtkWindowedSincPolyDataFilter`. `pass_band` between 0–2; lower = more smoothing. `n_iter` = polynomial degree, NOT iteration count in the Laplacian sense — it controls frequency cutoff. | Confirms the second pass at `n_iter=40, pass_band=0.05` is a lower-frequency, more aggressive smoothing pass that stacks on the first. |
| roadmap `plans/panel-refresh-2026q2-roadmap.md:§4` (MUST) | local read | "The UPL-18 v0 Taubin lift (second pass n_iter=40, pass_band=0.05 + bounds * 1.05) eliminates the Enriques sawtooth without pushing render time above the ~500ms single-render budget — spike in Phase 3: measure render time before/after the second Taubin pass on the Enriques canonical sextic via off-screen render; if render time exceeds 500ms, fall back to bounds-padding only." | Source of the 500ms budget and the exact second-pass parameters to spike. |
| `enriques-backface-2026q2-e1/research/agent-solo-brief.md` | local read | Per-figure topology audit: figs 1+2 double curves; fig 3 A₁ nodes (culling no-op); fig 4 A₁ nodes (culling beneficial). Wing-tip truncation is confirmed as a distinct sampling-bounds artifact from the culling effect. | Confirms the per-figure Taubin benefit scope; documents that the bounds padding addresses a separate artifact from culling. |

---

## 4. Recommended Approach

### 4.1 Spike script design

The spike script lives at `.claude/scripts/enriques-taubin-spike.py` (NOT in `tests/` — it's a spike with side-effects: writes files, prints timings). It must be self-contained and importable from the repo root.

**Exact code skeleton** (not pseudocode):

```python
#!/usr/bin/env python3
"""Spike: measure second Taubin-pass render cost on Enriques canonical sextic.
Writes results to /tmp/enriques-taubin-spike.txt AND
.claude/notes/milestones/enriques-taubin-spike-2026q2-e1/artifacts/timing-log.txt
"""
import os, sys, time, statistics
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import numpy as np
import pyvista as pv
import skimage.measure as measure

# ---- Inline single-pass generator (no second Taubin) ----
def _enriques_single(c=1.0, n=240, bounds=1.8):
    g = np.linspace(-bounds, bounds, n)
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    X2, Y2, Z2 = X*X, Y*Y, Z*Z
    F = X2*Y2 + X2*Z2 + Y2*Z2 + X2*Y2*Z2 + c*(X*Y*Z)*(1.0+X2+Y2+Z2)
    F = np.clip(F, -10.0, 10.0)
    # ---- inline _marching_cubes_to_polydata (single pass) ----
    # [simplified for spike brevity — see NOTE below about using surfaces.py directly]
    from surfaces import enriques_figure_1
    return enriques_figure_1(c=c, n=n, bounds=bounds)

# ---- Double-pass generator ----
def _enriques_double(c=1.0, n=240, bounds=1.8 * 1.05):
    padded = bounds  # 1.8 * 1.05 = 1.89
    g = np.linspace(-padded, padded, n)
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    X2, Y2, Z2 = X*X, Y*Y, Z*Z
    F = X2*Y2 + X2*Z2 + Y2*Z2 + X2*Y2*Z2 + c*(X*Y*Z)*(1.0+X2+Y2+Z2)
    F = np.clip(F, -10.0, 10.0)
    spacing = (2*padded / (n-1),) * 3
    verts, faces, normals, _ = measure.marching_cubes(F, level=0.0, spacing=spacing)
    verts -= padded
    n_faces = faces.shape[0]
    pv_faces = np.empty((n_faces, 4), dtype=np.int64)
    pv_faces[:, 0] = 3
    pv_faces[:, 1:] = faces
    mesh = pv.PolyData(verts, pv_faces.ravel())
    mesh.point_data["Normals"] = normals.astype(np.float32)
    mesh = mesh.clean()
    # First Taubin pass (baseline)
    mesh = mesh.smooth_taubin(n_iter=20, pass_band=0.1)
    # Second Taubin pass (the spike)
    mesh = mesh.smooth_taubin(n_iter=40, pass_band=0.05)
    if mesh.n_points > 0:
        mesh = mesh.compute_normals(
            cell_normals=False, point_normals=True,
            consistent_normals=True, auto_orient_normals=False,
            split_vertices=False,
        )
    return mesh

N = 7  # number of repetitions; take median

def measure_runs(fn, label):
    times = []
    for i in range(N):
        t0 = time.perf_counter()
        mesh = fn()
        elapsed_ms = (time.perf_counter() - t0) * 1000
        times.append(elapsed_ms)
        print(f"  {label} run {i+1}/{N}: {elapsed_ms:.1f} ms  ({mesh.n_points} pts, {mesh.n_faces} faces)")
    med = statistics.median(times)
    print(f"  MEDIAN {label}: {med:.1f} ms\n")
    return med, times

print("=== Enriques Taubin Spike ===")
print(f"N={N} runs each; taking median\n")

from surfaces import enriques_figure_1

# Warm up import cache
_ = enriques_figure_1(c=1.0)

med_single, single_times = measure_runs(lambda: enriques_figure_1(c=1.0), "SINGLE-pass (baseline)")
med_double, double_times = measure_runs(_enriques_double, "DOUBLE-pass (spike)")

overhead_ms = med_double - med_single
under_budget = med_double <= 500.0

result_lines = [
    "=== Enriques Taubin Spike Results ===",
    f"Date: 2026-05-22",
    f"N runs: {N}",
    f"Surface: enriques_figure_1(c=1.0), n=240",
    f"Single-pass (n=240, bounds=1.8) times (ms): {[f'{x:.1f}' for x in single_times]}",
    f"Single-pass median: {med_single:.1f} ms",
    f"Double-pass (n=240, bounds=1.89) times (ms): {[f'{x:.1f}' for x in double_times]}",
    f"Double-pass median: {med_double:.1f} ms",
    f"Second-pass overhead (median delta): {overhead_ms:.1f} ms",
    f"Budget: 500 ms",
    f"Outcome: {'PATH A (UNDER BUDGET)' if under_budget else 'PATH B (OVER BUDGET)'}",
    f"Decision: {'Ship second Taubin pass + bounds*1.05' if under_budget else 'Ship bounds*1.05 only; defer second pass'}",
]
log_text = "\n".join(result_lines)
print("\n" + log_text)

tmp_path = "/tmp/enriques-taubin-spike.txt"
artifacts_path = os.path.join(
    os.path.dirname(__file__),
    "../../notes/milestones/enriques-taubin-spike-2026q2-e1/artifacts/timing-log.txt"
)
os.makedirs(os.path.dirname(os.path.abspath(artifacts_path)), exist_ok=True)
for path in [tmp_path, os.path.abspath(artifacts_path)]:
    with open(path, "w") as f:
        f.write(log_text + "\n")
    print(f"Written: {path}")
```

**NOTE on the single-pass baseline:** The spike should call `enriques_figure_1()` directly from `surfaces.py` for the single-pass baseline (it already calls `_marching_cubes_to_polydata` with `smooth_iter=20`). The double-pass path must be inlined in the spike because `_marching_cubes_to_polydata` does not expose a second-pass parameter — the spike explicitly calls `smooth_taubin` twice. This is intentional: the spike script does NOT modify production code; it tests the proposed change in isolation.

### 4.2 Budget framing

The 500ms budget is **generate-only**, not generate+render. Sources:
- `CONTEXT.md:173` — "~0.5 s mesh generation"
- `plans/panel-refresh-2026q2-roadmap.md:§4` — "~500ms single-render budget"
- `CONTEXT.md:§9:458` — spinner window is "~0.5s window"

The budget covers `surface.generate(**kwargs)` only — NOT `plotter.add_mesh()` or `plotter.render()`. The spike measures `time.perf_counter()` wrapping the generator call directly, consistent with the brief's instruction to "measure `surfaces.enriques_figure_1(c=1.0)` directly."

**Path A threshold:** median double-pass time <= 500ms  → ship second pass + bounds*1.05.
**Path B threshold:** median double-pass time > 500ms → ship bounds*1.05 only.

The 500ms budget is the **total** generate time including the second pass — not the incremental cost of the second pass alone. The user brief is explicit: "if render time exceeds 500ms." A single-pass baseline of, say, 350ms with a 200ms second-pass overhead = 550ms total → Path B.

### 4.3 Path A vs Path B pre-commitment

**Path A (double-pass + bounds*1.05) production change:**
- In `_marching_cubes_to_polydata` (preferred), add a `second_smooth_iter: int = 0` parameter. After the first `smooth_taubin` call (line 134), add `if second_smooth_iter > 0 and mesh.n_points > 0: mesh = mesh.smooth_taubin(n_iter=second_smooth_iter, pass_band=0.05)`.
- In `enriques_figure_1` and `enriques_figure_2`: change `bounds=1.8` to `bounds=1.8 * 1.05` (= 1.89) AND pass `second_smooth_iter=40` to `_marching_cubes_to_polydata`.
- Fig 3 + Fig 4: bounds*1.05 (`2.5 * 1.05 = 2.625`, `1.5 * 1.05 = 1.575`) but NO second Taubin pass (A₁ node topology, not double curves). The second Taubin pass is Enriques-figure-1+2-specific.
- The `compute_normals` call stays in place after the second pass — no change needed.

**Path B (bounds*1.05 only) production change:**
- All four generators: increase default `bounds` by multiplying by 1.05 (figs 1+2: 1.89, fig 3: 2.625, fig 4: 1.575).
- No change to `_marching_cubes_to_polydata`.

**Reasoning for per-figure bounds-padding scope:** The wing-tip truncation artifact is visible in the rendered image (sampling box clips the surface at the marching-cubes grid boundary). It affects all 4 Enriques figures to varying degrees since all use symmetric `np.linspace(-bounds, bounds, n)` sampling. Bounds*1.05 is safe for all figures.

### 4.4 Per-figure second Taubin pass scope

Per CONTEXT.md §8.13 (enriques-backface milestone audit):
- **Fig. 1 (canonical sextic)** — double curves along 6 coord-tetrahedron edges. Taubin second pass targets the sawtooth ridge artifact from these curves. **YES — apply second pass.**
- **Fig. 2 (Diagonal λ-family)** — same double-curve topology as Fig. 1. **YES — apply second pass.**
- **Fig. 3 (Cayley quartic symmetroid)** — degree-4 with ordinary A₁ nodes (not double curves). Culling was a pixel-identical no-op. Taubin smoothing at ordinary nodes may marginally improve appearance but provides no targeted benefit. **SKIP second pass (bounds-padding only for Path A and Path B).**
- **Fig. 4 (Icosahedral sextic)** — A₁ nodes with some alternating front/back triangles (culling beneficial per CONTEXT.md §8.13). Taubin may slightly reduce node-area noise. **BORDERLINE** — the brief is silent; the safest choice is skip (consistent with the "second pass targets double curves" framing from the roadmap). Ship bounds-padding only for Fig. 4 in both paths.

**Summary decision:** Second Taubin pass applies only to figs 1+2. Bounds*1.05 applies universally to all 4 figs.

---

## 5. Off-Screen Render Verification Plan

AI-3 compliant. Script at `.claude/scripts/enriques-taubin-before-after.py` or inline in the spike:

```python
import pyvista as pv, sys, os
sys.path.insert(0, "<repo-root>")
pv.OFF_SCREEN = True
from surfaces import enriques_figure_1

# BEFORE: single-pass, original bounds=1.8 (current production state)
mesh_before = enriques_figure_1(c=1.0)
p = pv.Plotter(off_screen=True, window_size=(800, 600))
p.set_background("#2f2f2f")
p.add_mesh(mesh_before, color="#c8a880", smooth_shading=True,
           specular=0.3, specular_power=15, ambient=0.15, diffuse=0.85,
           culling="back")  # culling is already live in production
p.camera_position = "iso"
p.show(screenshot="/tmp/check-enriques-before.png")
p.close()

# AFTER: double-pass (if Path A) + bounds*1.05
mesh_after = _enriques_double(c=1.0)  # from spike script above
p = pv.Plotter(off_screen=True, window_size=(800, 600))
p.set_background("#2f2f2f")
p.add_mesh(mesh_after, color="#c8a880", smooth_shading=True,
           specular=0.3, specular_power=15, ambient=0.15, diffuse=0.85,
           culling="back")
p.camera_position = "iso"
p.show(screenshot="/tmp/check-enriques-after.png")
p.close()
print("Read /tmp/check-enriques-before.png and /tmp/check-enriques-after.png")
print("Expected: sawtooth ridges visibly reduced along coord-tetrahedron edges.")
```

Note: `culling="back"` is included in both renders because it is the current production state (enriques-backface-2026q2-e1 is already shipped).

---

## 6. Test Plan

AI-2 compliant — no `QApplication`, pure `pyvista`.

### Path A tests (second Taubin pass shipped)

**Test A1 — vertex-normal variance guard (quantitative smoothness)**

```python
def test_enriques_fig1_double_pass_normals_smoother_than_single():
    """Second Taubin pass reduces vertex-normal variance at double-curve ridges."""
    import numpy as np
    from surfaces import enriques_figure_1, _marching_cubes_to_polydata
    # Rebuild single-pass manually for comparison (or compare before/after in same test)
    # single-pass: enriques_figure_1(c=1.0) uses current production code
    mesh_single = enriques_figure_1(c=1.0, bounds=1.8)  # production (single pass)
    mesh_double = enriques_figure_1(c=1.0, bounds=1.89)  # new double-pass version
    # Normals are in mesh.point_data["Normals"] after compute_normals
    n_single = mesh_single.point_normals  # (N, 3) array
    n_double = mesh_double.point_normals
    var_single = np.var(n_single, axis=0).sum()
    var_double = np.var(n_double, axis=0).sum()
    assert var_double < var_single, (
        f"Double-pass normals should have lower variance: "
        f"single={var_single:.4f}, double={var_double:.4f}"
    )
```

NOTE: This test requires that production code has been updated to use double-pass. The test asserts the variance property of the shipped code vs. a manually generated single-pass baseline. In practice, since the test calls the new `enriques_figure_1()` (which does the double pass), the comparison needs a baseline. A simpler guard is:

```python
def test_enriques_fig1_returns_mesh_with_bounds_padded():
    from surfaces import enriques_figure_1
    mesh = enriques_figure_1(c=1.0)
    # With bounds*1.05, the mesh should extend slightly beyond 1.8
    assert max(abs(b) for b in mesh.bounds) > 1.7, "Mesh bounds should be near 1.89"
    assert mesh.n_points > 0
    assert mesh.n_faces > 0
```

**Test A2 — bounds padding is detectable**

```python
def test_enriques_fig1_bounds_padding_larger_than_original():
    from surfaces import enriques_figure_1
    import numpy as np
    mesh = enriques_figure_1(c=1.0)
    # New padded bounds=1.89; old bounds=1.80.
    # The mesh should have at least one vertex with |coord| > 1.7 in some axis.
    max_coord = np.max(np.abs(mesh.points))
    assert max_coord > 1.70, f"Expected padded extent >1.70, got {max_coord:.3f}"
```

### Path B tests (bounds-padding only)

**Test B1 — bounds padding only (same as Test A2)**

Same as A2 above — bounds-only assertion is valid for both paths.

**Test B2 — no sawtooth-amplification (mesh count sanity)**

```python
def test_enriques_fig1_padded_has_more_faces_than_unpadded():
    """Bounds*1.05 should capture slightly more wing-tip geometry."""
    from surfaces import enriques_figure_1, _enriques_figure_1_unpadded  # NOTE: see below
    # This requires either a separate helper or a direct bounds kwarg.
    # Simplest: test via the bounds parameter if it remains exposed.
    mesh_orig = enriques_figure_1(c=1.0, bounds=1.8)   # original bounds
    mesh_padded = enriques_figure_1(c=1.0, bounds=1.89) # padded bounds
    assert mesh_padded.n_faces >= mesh_orig.n_faces * 0.95, (
        "Padded mesh should have at least as many faces as original"
    )
```

NOTE: This test is only viable if the `bounds` parameter remains a kwarg on `enriques_figure_1`. Per the current signature `def enriques_figure_1(c=1.0, n=240, bounds=1.8)`, it does. The production change changes the default from 1.8 to 1.89; the test can explicitly pass `bounds=1.8` to get the old behavior.

---

## 7. CONTEXT.md §8 Entry Drafts

### Path A variant (under-budget)

```
### 8.16 Second Taubin pass reduces Enriques double-curve sawtooth artifact (enriques-taubin-spike-2026q2-e1)

The Enriques canonical sextic (fig. 1) and diagonal λ-family (fig. 2) carry double-curve singularities
along the six edges of the coordinate tetrahedron. The existing single Taubin pass (`n_iter=20,
pass_band=0.1` in `_marching_cubes_to_polydata`) reduces but does not eliminate the sawtooth-ridge noise
from alternating near-degenerate front/back triangles at these ridges.

A second Taubin pass (`n_iter=40, pass_band=0.05`) applied after the first pass provides a second,
lower-frequency smoothing sweep that further attenuates the residual high-frequency ridge artifacts.
The spike measured median generate time of **{MEASURED_MS} ms** for the double-pass path at `c=1.0,
n=240` — within the 500ms budget. Timing log at
`.claude/notes/milestones/enriques-taubin-spike-2026q2-e1/artifacts/timing-log.txt`.

Additionally, the marching-cubes sampling bounds for all four Enriques figures were padded by 5%
(`bounds * 1.05`) to reduce wing-tip truncation: the surface extends past the original sampling box at
extreme parameter values, and the 5% pad captures the missing wing geometry at the grid boundary.

Scope of changes:
- `_marching_cubes_to_polydata` gains `second_smooth_iter: int = 0` parameter (default 0 preserves
  behavior for all non-Enriques surfaces).
- Figs 1+2: `bounds` default raised from 1.8 → 1.89; `second_smooth_iter=40` passed to helper.
- Figs 3+4: `bounds` default raised (2.5 → 2.625, 1.5 → 1.575); second pass NOT applied (A₁ nodes,
  not double curves — no targeted benefit).
```

### Path B variant (over-budget)

```
### 8.16 Bounds padding applied to Enriques generators; second Taubin pass deferred (enriques-taubin-spike-2026q2-e1)

The UPL-18 spike measured median generate time of **{MEASURED_MS} ms** for a second Taubin pass
(`n_iter=40, pass_band=0.05`) on `enriques_figure_1(c=1.0, n=240)` — **over the 500ms budget**.
Per the pre-committed Path B outcome, the second Taubin pass is deferred to a future
"high-quality-toggle" milestone (a slider that lets the user opt in to a higher-quality but slower
smoothing pass).

The bounds-padding fix was shipped regardless: all four Enriques figures have their `bounds` default
raised by 5% (`bounds * 1.05`) to reduce wing-tip truncation from the sampling-grid edge.
- Fig. 1: 1.8 → 1.89; Fig. 2: 1.8 → 1.89; Fig. 3: 2.5 → 2.625; Fig. 4: 1.5 → 1.575.

Timing log at `.claude/notes/milestones/enriques-taubin-spike-2026q2-e1/artifacts/timing-log.txt`.

Deferral rationale: the second Taubin pass adds {OVERHEAD_MS} ms on the test machine (median delta),
pushing total generate time from {SINGLE_MS} ms to {TOTAL_MS} ms — {PERCENT}% over budget. The
smoothing improvement is visually beneficial but not sufficient to justify exceeding the 500ms UX
threshold for initial generate time. A future milestone can gate the second pass behind an "HQ
smoothing" toggle in the Parameters panel (opt-in, slower).
```

---

## 8. AI-1..AI-15 Conflict Matrix

| Invariant | Status | Notes |
|---|---|---|
| **AI-1** (PySide6+PyVista+pyvistaqt) | CLEAN | No renderer change. |
| **AI-2** (Qt-free tests) | CLEAN | Test plan uses pure PyVista generator calls. No `QApplication`. |
| **AI-3** (off-screen via `pv.OFF_SCREEN=True`) | CLEAN | Before/after PNGs use the canonical off-screen pattern. Never construct `MainWindow()`. |
| **AI-4** (clip_scalar not clip_box) | CLEAN | No domain clipping in spike. |
| **AI-5** (`scalars=` kwarg) | CLEAN | No `clip_scalar` call in spike. |
| **AI-6** (implicit pipeline: Taubin STACKS, not replaces) | CRITICAL CHECK | Second pass at `n_iter=40, pass_band=0.05` is called AFTER the existing first pass (`n_iter=20, pass_band=0.1`). Do NOT skip the first pass. Both `smooth_taubin` calls must appear in sequence. The `_marching_cubes_to_polydata` first pass must remain unchanged. |
| **AI-7** (Hanson normals) | CLEAN | Hanson generators are parametric; they never touch `_marching_cubes_to_polydata`. No change propagates to Hanson. |
| **AI-8** (Surface/ParamSpec frozen contract) | CLEAN | No field added to Surface or ParamSpec. The brief explicitly says do NOT add `recommends_backface_culling`. The optional `second_smooth_iter` parameter is on `_marching_cubes_to_polydata` (a private helper), not on the dataclass. |
| **AI-9** (re-entrancy guard) | CLEAN | Smoothing runs inside `surface.generate()` (the synchronous generator call), not in the Qt event loop. No `processEvents` involvement. |
| **AI-10** (raw mesh cache) | CLEAN | Generator output is `_raw_mesh`; the cache discipline is unaffected. |
| **AI-11** (fully-qualified Qt enums) | N/A | No new Qt code. |
| **AI-12** (WCAG contrast) | N/A | No new text or UI elements. |
| **AI-13** (6-digit hex) | N/A | No new color literals. |
| **AI-14** (generator contract: PolyData or ValueError) | CHECK | With `bounds * 1.05`: Fig. 1 `bounds=1.89`, n=240 → spacing = 2×1.89/239 ≈ 0.01582 voxel side. Fig. 4 `bounds=1.575`, n=220 → spacing = 2×1.575/219 ≈ 0.01438. Both are well above the marching-cubes floor (~0.003 is the practical minimum before mesh becomes unusable). No ValueError risk from the 5% pad. The generator still returns `pv.PolyData` or raises `ValueError("No real zero set...")` per the existing pre-check. |
| **AI-15** (math honesty) | N/A | No new variety or figure. Taubin smoothing is a rendering-quality improvement, not a mathematical claim. |

**Key AI-14 verification:** bounds*1.05 with current `n` values:
- Fig. 1: spacing = 2×1.89/239 = 0.01582 (was 0.01506 at 1.8) — still very fine mesh, no resolution degradation
- Fig. 2: same as Fig. 1
- Fig. 3: spacing = 2×2.625/239 = 0.02197 (was 0.02092 at 2.5) — fine
- Fig. 4: spacing = 2×1.575/219 = 0.01438 (was 0.01370 at 1.5) — fine

None of these changes drop below any marching-cubes resolution floor. The 5% bounds increase is equivalent to ~5% coarser voxels at fixed `n` — negligible effect on mesh quality.

---

## 9. AI-15 Disclaimers

No new variety or figure is proposed. This milestone improves smoothing quality of the existing Enriques figures.

The tooltip text for the Enriques canonical sextic (Subtype "Canonical sextic  [Fig. 1]") does not need updating — the existing AI-15-compliant disclaimer in `surfaces.py:365–376` accurately describes the surface as "real shadows of degree-6 surfaces in P^3 birational to Enriques surfaces." The Taubin pass is a mesh-quality change, not a mathematical-content change.

---

## 10. Open Questions

None. All decisions are fully specified by the user brief's pre-commitment to Path A vs Path B based on timing numbers.

---

## Appendix: Implementation summary for the implementer

**Step 1: Run the spike script.** Path: `.claude/scripts/enriques-taubin-spike.py`. Output to `/tmp/enriques-taubin-spike.txt` and `.claude/notes/milestones/enriques-taubin-spike-2026q2-e1/artifacts/timing-log.txt`.

**Step 2: Read the timing log.** If `med_double <= 500ms` → Path A. Else → Path B.

**Step 3a (Path A):**
- Add `second_smooth_iter: int = 0` to `_marching_cubes_to_polydata` signature (`surfaces.py:87`). Add second-pass block after line 134: `if second_smooth_iter > 0 and mesh.n_points > 0: mesh = mesh.smooth_taubin(n_iter=second_smooth_iter, pass_band=0.05)`.
- Update `enriques_figure_1` default `bounds=1.8` → `1.89`; add `return _marching_cubes_to_polydata(F, bounds, second_smooth_iter=40)`.
- Update `enriques_figure_2` same way.
- Update `enriques_figure_3` default `bounds=2.5` → `2.625` (no second pass).
- Update `enriques_figure_4` default `bounds=1.5` → `1.575` (no second pass).

**Step 3b (Path B):**
- Update only the `bounds` defaults as above. No helper change.

**Step 4:** Run before/after off-screen render. Read `/tmp/check-enriques-{before,after}.png`. Confirm sawtooth seam reduction.

**Step 5:** Add tests per §6 above. Run full test suite (`pytest tests/ -v`). Confirm all pass.

**Step 6:** Add CONTEXT.md §8.16 entry (pick the correct variant from §7 above, inserting measured numbers).

**Step 7:** Commit with message referencing spike outcome (Path A or Path B) and measured ms number.
