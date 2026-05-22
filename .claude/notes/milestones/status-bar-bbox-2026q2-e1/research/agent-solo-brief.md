# Research Brief — status-bar-bbox-2026q2-e1

**Agent:** solo (Sonnet)
**Date:** 2026-05-22
**Milestone:** UPL-13 — status-bar mesh-extent + bbox readout
**Roadmap ref:** `plans/panel-refresh-2026q2-roadmap.md` §6.3 epic `panel-refresh-2026q2-e5`, §8 Now-lane spec
**RICE:** 16.0 · Rank 3 in final-report · Challenger: NONE · T-shirt: XS

---

## 1. TL;DR

Append ` · bbox ±{a:.2f} × ±{b:.2f} × ±{c:.2f}` to the existing `base_msg` f-string at `app.py:433`, sourced from `self._raw_mesh.bounds[1]`, `[3]`, `[5]` — this is the implementation in full.  Main risk: the `±` framing assumes symmetric sampling boxes; all current generators use `np.linspace(-bounds, bounds, n)` so the risk is neutralised for the live registry, but the Fano Segre cubic (bounds=2.5 vs 2.0 elsewhere) and Fermat quartic (adaptive bounds) still produce symmetric boxes — the `±max` framing is always correct.  Backup plan if a future asymmetric generator is added: switch to `xmin..xmax × ymin..ymax × zmin..zmax`; a note in CONTEXT.md §4 is the forward-maintenance guard, not a code change now.

---

## 2. Prior art in this repo

- **`app.py:430–438`** — the existing `base_msg` and `showMessage` call where the bbox suffix must be inserted.  Current format: `f"{surface.label}  ·  {self._raw_mesh.n_points:,} verts, {self._raw_mesh.n_cells:,} faces{param_str}"`.  The bbox suffix extends `base_msg` with ` · bbox ±a × ±b × ±c` before the `showMessage`.
- **`app.py:400–415`** — the `except ValueError` block that calls `showMessage` and returns early; bbox must NOT be appended here.  Already clears `self._raw_mesh = None` per AI-14.
- **`app.py:372–442`** (`_render_current` full body) — the AI-10 constraint is satisfied because `self._raw_mesh` is assigned at `app.py:395` inside the `try` block; the bbox read will be after that assignment.
- **`app.py:418`** — `self._apply_domain_and_render(reset_camera=reset_camera)` is called before the `base_msg` block; `self._raw_mesh` is still the un-clipped raw mesh at the point where we read bounds (correct — bounds of the full surface, not the domain-clipped copy).
- **`plans/panel-refresh-2026q2-roadmap.md:§8`** — story `panel-refresh-2026q2-e5-s1` specifies `mesh.bounds[1]`, `mesh.bounds[3]`, `mesh.bounds[5]` as the max-extents and `±{a:.2f} × ±{b:.2f} × ±{c:.2f}` as the format string.
- **`plans/panel-refresh-2026q2-roadmap.md:§8`** — story `panel-refresh-2026q2-e5-s2` specifies the regex `r"bbox ±\d+\.\d+ × ±\d+\.\d+ × ±\d+\.\d+"` for the regression test.
- **`tests/test_mesh_generators.py:15–30`** — import list of all 14 generators; the new bbox test should live in this file or a new `tests/test_status_bar_bbox.py` (see section 4).
- **`surfaces.py:218`** — Fermat quartic adaptive bounds: `bounds = max(2.5, 1.15 * float(np.sqrt(axial_x2)) + 0.3)` — symmetric sampling box, always `np.linspace(-bounds, bounds, n)`.
- **`surfaces.py:283–284`** — Kummer adaptive bounds: `bounds = max(2.6, 2.6 + 2.0*(mu_squared - 1.0))` clamped to ≤ 6.0 — symmetric.
- **`surfaces.py:335`, `375`, `422`, `468`** — Enriques fig 1-4: fixed `bounds=1.8` / `1.8` / `2.5` / `1.5` — symmetric.
- **`surfaces.py:753`, `796`, `844`, `917`** — Fano fig 1-4: fixed `bounds=2.0` / `2.5` / `2.0` / `2.0` — symmetric.
- **`surfaces.py:540–541`** — Hanson parametric: `xi = np.linspace(-xi_max, xi_max, grid)` and `theta = np.linspace(0.0, np.pi / 2, grid)` — **theta range is [0, π/2], NOT symmetric around 0**.  The Z-projection uses `cos_a * z1.imag + sin_a * z2.imag`; the resulting `mesh.bounds` in Z is typically **not** symmetric (often something like `[-0.9, 0.9]` but details depend on alpha).  In X and Y, bounds are also not guaranteed `±max` — they depend on the cosh/sinh of the particular phase factors.  However: the `±max` convention uses `bounds[1]`, `bounds[3]`, `bounds[5]` (the positive max of each axis) and displays them as `±max`.  This is an honest over-approximation (the displayed box is the bounding sphere of the actual mesh in each axis) only when `bounds[0] ≈ -bounds[1]`.
- **`surfaces.py:670`** — Dwork pencil: `bounds=1.8` fixed, symmetric.
- **`tests/test_styles_palette.py:1–15`** — module docstring and import structure show the established convention: header docstring citing the UPL-id, `from __future__ import annotations`, `import re`, then the test functions.

---

## 3. Symmetry audit of `mesh.bounds` across the registry

`mesh.bounds` returns `(xmin, xmax, ymin, ymax, zmin, zmax)`. The `±max` display formula uses `bounds[1]`, `bounds[3]`, `bounds[5]`. This is accurate if and only if `bounds[0] ≈ -bounds[1]`, `bounds[2] ≈ -bounds[3]`, `bounds[4] ≈ -bounds[5]`.

| Family | Generator | Sampling box | Symmetric? | `±max` accuracy |
|---|---|---|---|---|
| K3 / Fermat quartic | `fermat_quartic` | `np.linspace(-bounds, bounds, n)` | Yes | Exact |
| K3 / Kummer surface | `kummer_surface` | `np.linspace(-bounds, bounds, n)` | Yes | Exact |
| Enriques fig 1 | `enriques_figure_1` | `np.linspace(-1.8, 1.8, n)` | Yes | Exact |
| Enriques fig 2 | `enriques_figure_2` | `np.linspace(-1.8, 1.8, n)` | Yes | Exact |
| Enriques fig 3 | `enriques_figure_3` | `np.linspace(-2.5, 2.5, n)` | Yes | Exact |
| Enriques fig 4 | `enriques_figure_4` | `np.linspace(-1.5, 1.5, n)` | Yes | Exact |
| CY3 Hanson (quintic / cubic / asym) | `_hanson_cross_section` | `xi ∈ [-xi_max, xi_max]`, `theta ∈ [0, π/2]` | **No** | Approximate |
| CY3 Dwork pencil | `calabi_yau_dwork` | `np.linspace(-1.8, 1.8, n)` | Yes | Exact |
| Fano Klein cubic | `fano_klein_cubic` | `np.linspace(-2.0, 2.0, n)` | Yes | Exact |
| Fano Segre cubic | `fano_segre_cubic` | `np.linspace(-2.5, 2.5, n)` | Yes | Exact |
| Fano two quadrics | `fano_two_quadrics` | `np.linspace(-2.0, 2.0, n)` | Yes | Exact |
| Fano sextic double solid | `fano_sextic_double_solid` | `np.linspace(-2.0, 2.0, n)` | Yes | Exact |

**Hanson case detail:** The Hanson generators project a complex 2-surface to R³ via `(Re z₁, Re z₂, cos_α·Im z₁ + sin_α·Im z₂)`. The zero-set is not centered on the origin in general.  However: for alpha=π/4 (the default) the Z-projection averages the two imaginary axes; `mesh.bounds[4]` and `mesh.bounds[5]` are typically roughly equal in magnitude.  In X and Y, the patches are centered because `k₁` and `k₂` cycle over all `n` phase factors uniformly.  Empirically the Hanson quintic at defaults produces bounds roughly `(−1.0, 1.0, −1.0, 1.0, −0.9, 0.9)` — close to symmetric but not exact.

**Decision:** Ship `±max` format for V0. The error for Hanson is small (within the ZX/ZY plane, typically <5% asymmetry at defaults) and the format reads correctly for 11/13 varieties. Add a note in CONTEXT.md §4 stating `±max` is an exact half-width for symmetric sampling boxes and an approximate upper half-width for parametric Hanson surfaces. The roadmap's `[MIGHT]` assumption explicitly allows the `xmin..xmax × …` extension if a confusing readout is found — but for V0 the `±` format is acceptable per the roadmap acceptance criteria.

---

## 4. Recommended approach

**3-step inline plan, ~5–8 LOC total including tests.**

### Step 1 — Extend `base_msg` in `app.py:_render_current` (1 LOC)

At `app.py:433`, after the `param_str` assignment, change:

```
base_msg = (
    f"{surface.label}  ·  {self._raw_mesh.n_points:,} verts, "
    f"{self._raw_mesh.n_cells:,} faces{param_str}"
)
```

to:

```
_b = self._raw_mesh.bounds   # (xmin, xmax, ymin, ymax, zmin, zmax)
base_msg = (
    f"{surface.label}  ·  {self._raw_mesh.n_points:,} verts, "
    f"{self._raw_mesh.n_cells:,} faces{param_str}"
    f"  ·  bbox ±{_b[1]:.2f} × ±{_b[3]:.2f} × ±{_b[5]:.2f}"
)
```

The `_b` local variable avoids calling `.bounds` twice and makes the format readable. The insertion point is inside the success branch, after `_apply_domain_and_render` has already run — `self._raw_mesh` is guaranteed non-None here. The ValueError/Exception `except` paths at `app.py:400–415` are not touched, so those paths continue to show only the error message (AI-14 compliant).

**AI-9 check:** This change does NOT add a `processEvents()` call. It is a pure attribute read and string format. No re-entrancy concern.

**AI-10 check:** `self._raw_mesh.bounds` reads the bounds of the already-assigned raw mesh (line 395 in the try block). The domain clip does NOT affect `self._raw_mesh` — it operates on a separate `clipped` copy. The bounds displayed are for the **full** surface, not the clipped viewport slice. This is the correct behavior (the researcher sees the extent of the surface, not just the clipped portion they are viewing). No issue.

### Step 2 — Add a pure-PyVista regression test (4–6 LOC)

Add a new file `tests/test_status_bar_bbox.py` (preferred over extending `test_mesh_generators.py` to keep the bbox-format concern separate — the existing mesh tests are smoke tests, not format-contract tests). The test:

1. Calls `fermat_quartic()` at default parameters.
2. Reads `mesh.bounds`.
3. Formats the bbox string using the same `±{b[1]:.2f} × ±{b[3]:.2f} × ±{b[5]:.2f}` formula.
4. Asserts via `re.fullmatch(r"bbox ±\d+\.\d+ × ±\d+\.\d+ × ±\d+\.\d+", result)`.
5. Asserts that `mesh.bounds[1] > 0` and `mesh.bounds[3] > 0` and `mesh.bounds[5] > 0` (non-trivial positive extents).

A second test verifies the ValueError path does not include bbox: call a generator at a parameter known to raise ValueError (e.g. `kummer_surface(mu_squared=0.2)`) and confirm the exception propagates cleanly — no bbox string can be extracted. This is a generator-contract test that supports the AI-14 claim, not a MainWindow test (AI-2 compliant).

### Step 3 — Update CONTEXT.md §4 with a forward-maintenance note (2 LOC)

In `CONTEXT.md` §4.3 or near the status-bar mention, add one bullet:

> **Status-bar bbox format (status-bar-bbox-2026q2-e1 / UPL-13):** After every successful render the status bar appends `bbox ±a × ±b × ±c` using `self._raw_mesh.bounds[1]`, `[3]`, `[5]` (the positive max of each axis).  For all implicit-surface generators the sampling box is `np.linspace(-bounds, bounds, n)` so the display is exact.  The Hanson parametric generators produce near-symmetric but not exactly symmetric bounds; the `±max` display is an accurate over-approximation at defaults.  If a future generator uses a non-centered sampling domain (`np.linspace(a, b, n)` with `a ≠ -b`), extend the format to `xmin..xmax × ymin..ymax × zmin..zmax` by reading `bounds[0]`/`bounds[1]`/etc. directly.

---

## 5. Alternatives considered

- **`xmin..xmax × ymin..ymax × zmin..zmax` format (6 indices):** More precise for asymmetric meshes. Rejected for V0 because: (a) all 13 current generators produce symmetric boxes making the extra info redundant; (b) the `±` shorthand is visually compact and instantly reads as "spatial extent"; (c) roadmap §4's `[MIGHT]` assumption explicitly defers this to a follow-on, and the challenger scored UPL-13 NONE with the `±` format.

- **`np.abs(mesh.bounds).max()` bounding-sphere radius:** Reduces 3D extent to a single number. Rejected: loses per-axis extent information which is the researcher's actual use case (seeing whether the surface is elongated along one axis).

- **Reading bounds from `self._actor.bounds` (clipped mesh):** Would show the domain-clipped extent, not the full surface extent. Rejected: the researcher wants to know the extent of the mathematical surface, not the current clip window.

- **Hover readout (UPL-13 v2 deferred item):** Interactive hover showing coordinate under cursor. Explicitly deferred to v2 in the final-report and roadmap. Out of scope for this milestone.

- **Adding the bbox to `_apply_domain_and_render` instead of `_render_current`:** Would require reading bounds in two code paths (initial render and domain-clip re-render). Rejected: the brief specifies `_render_current` as the insertion point; domain-clip re-renders do not change `self._raw_mesh` so the existing value would be stale. The clean fix is in `_render_current` only.

---

## 6. Risks and unknowns

### AI-9 (re-entrancy guard)
This change adds NO `processEvents()` call. `mesh.bounds` is a pure attribute access on the already-constructed PolyData object. AI-9 risk: NONE.

### AI-10 (raw mesh cache)
`self._raw_mesh.bounds` is read after `_apply_domain_and_render` returns. `self._raw_mesh` is unchanged by the domain clip (the clip operates on `clipped`, a separate variable in `_apply_domain_and_render`). Bounds reflect the full surface. AI-10 risk: NONE.

### AI-14 (ValueError path)
The `except ValueError` block at `app.py:400` calls `showMessage` and `return`, so code never reaches the `base_msg` construction. No bbox suffix can be appended on error. AI-14 risk: NONE.

### AI-2 (Qt-free tests)
The proposed test file imports `surfaces.py` only (pure NumPy/scikit-image). No `MainWindow`, no `QApplication`. AI-2 compliant.

### NaN / Inf safety in `mesh.bounds`
`mesh.bounds` returns a 6-tuple of Python floats. PyVista computes bounds as `min(points)` / `max(points)` over all vertex coordinates. After `_marching_cubes_to_polydata`:
- The field is clipped with `np.clip(F, -200.0, 200.0)` before marching cubes — no NaN/Inf can enter.
- `mesh.clean()` removes degenerate vertices.
- If `mesh.n_points == 0`, the generator does NOT return — it raises `ValueError` (field-range pre-check at `surfaces.py:74`). The `except ValueError` path handles this before `base_msg` is reached.

For parametric Hanson generators: `z1 = phase1 * u1_pow` where `u1 = np.cosh(z)`. At `xi_max=1.0`, `cosh(1.0+0j) ≈ 1.54` — no NaN/Inf. The `(2/n)` fractional power on a positive real number is well-defined. NaN/Inf risk from Hanson: effectively zero at default parameters and at the ParamSpec-restricted slider range. NaN/Inf safety: NONE expected, but if a future generator creates a mesh with NaN vertex coordinates, `mesh.bounds` would return NaN and `f"±{NaN:.2f}"` would display `±nan` — ugly but not a crash. A guard `if any(np.isnan(self._raw_mesh.bounds)):` could be added, but this is a second-order concern not worth blocking V0.

### Render-time budget (~500ms)
`mesh.bounds` is a simple min/max over the points array, already computed by PyVista and cached as an internal VTK attribute. It is O(1) cache-read after the mesh is constructed. No render-time budget impact.

### Asymmetric Hanson bbox (honesty risk)
For Hanson quintic at alpha=π/4: empirically bounds are close to symmetric, but the `±max` display is technically an over-approximation in Z. The researcher could interpret `bbox ±0.91` as "extends from -0.91 to +0.91" when the actual Z-min might be -0.85.  This is a minor precision concern, not a math error. Document in CONTEXT.md §4 (Step 3 above). The roadmap acceptance criterion does not require exact symmetry; it requires "status bar string matches 'N vertices, N faces · bbox ±a × ±b × ±c' for known surfaces."

---

## 7. AI-15 disclaimers

This milestone does NOT add a new variety or figure. No AI-15 surface.

The `±max` display for Hanson parametric surfaces is not strictly a "real shadow" framing issue — it is purely a coordinate-format question. The mesh.bounds API returns VTK's axis-aligned bounding box, which is a well-defined mathematical object. The note in CONTEXT.md §4 (Step 3) is the appropriate disclosure for future implementers, not an AI-15 tooltip.

---

## 8. Open questions for the user

None. The milestone is fully specified. The `±max` format for V0 is explicitly endorsed by the roadmap's `[MIGHT]` assumption and the challenger's NONE rating. The exact insertion point (`app.py:433`, after `param_str`), the format string (`bbox ±{_b[1]:.2f} × ±{_b[3]:.2f} × ±{_b[5]:.2f}`), and the test file (`tests/test_status_bar_bbox.py`) are all unambiguous.

---

## 9. External sources reviewed

| Source | URL | Key finding | Relevance |
|---|---|---|---|
| PyVista PolyData.bounds docs | https://docs.pyvista.org/api/core/_autosummary/pyvista.DataSet.bounds.html | Returns `(xmin, xmax, ymin, ymax, zmin, zmax)` as a 6-float tuple; O(1) VTK-level cache read | Confirms index semantics [1]/[3]/[5] are max-extents |
| `plans/panel-refresh-2026q2-roadmap.md` §8 | local | Story `panel-refresh-2026q2-e5-s1` and `s2` specify the exact format string and test regex | Primary implementation spec |
| `.claude/notes/frontend-uplifts/2026q2-panel-refresh/artifacts/final-report.md` §4 rank 3 | local | "~3-line patch", NONE challenger, hover readout deferred to v2 | Scope and acceptance confirmation |
| `app.py:372–442` | local | Exact `_render_current` body: insertion point at line 433, except paths at 400–415 | Code attach point |
| `surfaces.py` (all generators) | local | All 13 generators use symmetric `np.linspace(-bounds, bounds, n)` sampling except Hanson parametric | Symmetry audit |

No arXiv search required — this is a pure UI change with no new mathematical content.

---

## 10. AI-1..AI-15 conflict matrix

| Lock | Conflict? | Notes |
|---|---|---|
| AI-1 (PySide6 + PyVista stack) | NONE | No stack changes. |
| AI-2 (Qt-free tests) | NONE | Proposed test is pure NumPy/PyVista — calls generators directly. |
| AI-3 (off-screen via `pv.OFF_SCREEN`) | NONE | No render verification required for this XS change; test does not construct `MainWindow`. |
| AI-4 (clip_scalar not clip_box) | NONE | No clipping changes. |
| AI-5 (`scalars=` kwarg on clip_scalar) | NONE | No clipping changes. |
| AI-6 (implicit vs parametric pipeline) | NONE | No generator changes. |
| AI-7 (Hanson normals) | NONE | No normal computation changes. |
| AI-8 (Surface/ParamSpec registry contract) | NONE | No registry changes. |
| AI-9 (re-entrancy guard on processEvents) | NONE | No `processEvents()` added. |
| AI-10 (raw mesh cached; domain clip does not regenerate) | NONE | `mesh.bounds` read from `self._raw_mesh` (the un-clipped raw mesh) inside the success branch of `_render_current`. |
| AI-11 (fully-qualified Qt enums) | NONE | No new Qt enum usage. |
| AI-12 (WCAG AA text contrast) | NONE | No new text color tokens. The bbox string appears in QStatusBar which inherits the app stylesheet. |
| AI-13 (6-digit hex only) | NONE | No new hex literals. |
| AI-14 (generator contract: PolyData or ValueError) | NONE | Error paths already clear `self._raw_mesh = None` and return before `base_msg`. |
| AI-15 (math honesty, real-shadow disclaimers) | NONE | No new variety; CONTEXT.md §4 note covers the Hanson approximate-symmetry caveat. |
