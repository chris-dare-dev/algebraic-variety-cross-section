# lessons -- milestone-researcher

## panel-refresh-2026q2-e2 (2026-05-20) [merged]
- For palette-token refactors: grep ALL 5 source files first (`styles.py`, `appearance_panel.py`, `view_panel.py`, `parameters_panel.py`, `app.py`) — `view_panel.py` / `parameters_panel.py` had zero hex literals, saving false scope; `appearance_panel.py:48` `#888` and `app.py` carried untracked hex `styles.py` didn't cover. Grep `#[0-9a-fA-F]{3,6}` for both 3- and 6-digit forms.
- AI-13 (6-digit hex) violations can hide in Qt stylesheet strings that never touch PyVista — still worth fixing for ambiguity removal; the `appearance_panel.py:48` `#888` case is canonical (resolve via `SWATCH_BORDER = "#888888"`).
- External naming conventions (qt-material, napari, ParaView, QPalette) all confirm semantic role names beat CSS-hex-variable names: `BG_VIEWPORT` not `viewport_background_hex`, `TEXT_MUTED` not `muted_color_hex`. `styles.py` (not `palette.py`) is right at AVC scale.
- AI-11 violations in existing code (`Qt.AA_ShareOpenGLContexts` at `app.py:429`) should be noted as out-of-scope pre-existing, neither silently fixed nor ignored.
- WCAG `TEXT_DISABLED = #aaaaaa` correctly uses the WCAG disabled exception; don't flag intentional low-contrast disabled text as a bug.
- When the milestone requires a `PALETTE_LIGHT` dict, the backward-compat pattern (old named constants become `= PALETTE_LIGHT["TOKEN"]`) is the zero-call-site-change migration.
- Plan downstream API: map every downstream milestone (UPL-4 dark-mode, UPL-5 per-variety color, UPL-11 overlay) to dict key reads BEFORE writing the brief so token names are stable across the sprint.

## graph-and-window-2026q2-e1 (2026-05-21)
- For XS-effort tooling milestones (3 candidates, 1-day sprint), keep the brief proportionate: skip arXiv/OSS web searches entirely. Value is in precise file:line attach points, not external triangulation.
- `clearFocus()` is the correct Qt primitive to suppress focus-ring artifacts in offscreen widget grabs — `setFocusPolicy(Qt.FocusPolicy.NoFocus)` on a container widget does NOT prevent child tab-stops from receiving focus.
- Bare `QDockWidget` outside `QMainWindow` is explicitly cleared by AI-3's clarifying paragraph — safe for offscreen panel grabs. The QSS `QDockWidget::title` rule fires on standalone dock widgets.
- For `add_mesh` lighting kwargs (ambient/diffuse), check whether `appearance_panel.apply_to_actor()` overrides VTK actor properties post-add — if it calls `SetAmbient`/`SetDiffuse` the `add_mesh` kwargs would be overwritten.
- When a milestone touches `render-panel-chrome.py` and `agent-prompts.md` in the same PR, sequence the agent-prompts.md edit first.

## variety-palette-2026q2-e1 (2026-05-21)
- For pure palette/wiring milestones, skip arXiv and OSS web searches entirely — all signal is in repo-local files + numerically-computed contrast ratios.
- WCAG contrast for variety colors: "surface color on dark viewport" uses 4.5:1 text threshold (not 3:1 non-text) because the surface-family name appears as rendered status-bar text in the same color token.
- Unicode key identity is a silent failure mode for VARIETY_DEFAULT_COLOR: "Calabi–Yau 3-fold" uses U+2013 en-dash (not ASCII hyphen); "Fano 3-fold (ρ=1)" uses U+03C1. Copy-paste from surfaces.py — confirmed at `surfaces.py:968, 986`.
- Hue separation ≥25° (HSV) between variety color pairs is the minimum for perceptual distinguishability. Don't mistake near-equal luminance for near-equal appearance.
- The stub test `test_variety_default_color_is_stub_for_upl5` asserts `== {}` and must be DELETED (not supplemented) when the dict is populated.
- `set_default_color` on AppearancePanel must NOT call render — the caller flows into `_render_current` → `apply_to_actor`.
- `BG_SURFACE_DEFAULT` is the correct fallback in `VARIETY_DEFAULT_COLOR.get(name, BG_SURFACE_DEFAULT)` — already exported from styles.py but may not be imported at the call site.

## dark-mode-2026q2-e1 (2026-05-22)
- For dark-mode stylesheet milestones, compute WCAG ratios numerically before writing a single token — ratio(candidate, BG_PANEL_DARK) must be explicit; "passes qualitatively" is not sufficient.
- `BG_PANEL_DARK = #252526` is the right anchor: dark but not pitch-black, leaves room for structural separation, in the Quanta/3Blue1Brown/VS Code dark register.
- Structural background tokens (`BG_DOCK_HEADER`, etc.) do NOT need 3:1 vs `BG_PANEL` — they are not UI component boundaries; the BORDER token carries the WCAG 1.4.11 obligation.
- `QGuiApplication.styleHints().colorScheme()` (Qt 6.5+) provides native follow-system detection with `colorSchemeChanged` signal — no `darkdetect` dep needed.
- `APP_STYLESHEET_DARK` naming is load-bearing: `render-panel-chrome.py` detects it via `getattr(styles, "APP_STYLESHEET_DARK", None)` (`styles.py:151-157`). Do NOT rename.
- `_render_stylesheet(palette: dict)` approach avoids drift risk from duplicate f-string templates. Every palette token referenced as `palette["TOKEN"]`, not via named constants.
- `VARIETY_DEFAULT_COLOR_DARK` identical to light: all four colors clear 3:1 (swatch) and 4.5:1 (canvas) against `BG_PANEL_DARK`/`BG_VIEWPORT`. Reuse verbatim — close MF1 with a test assertion, not new hex.
- Pattern A (`styles.get_variety_default_colors(theme)` in app.py) keeps AppearancePanel decoupled from theme state.
- `TEXT_DISABLED_DARK` must NOT have a WCAG test — uses WCAG §1.4.3 disabled exception. Document in the dict comment.
- Dark-mode LOC splits: ~270 total (styles.py ~75, app.py ~55, appearance_panel.py ~5, tests ~110, CONTEXT.md ~25) — fits the inline (non-delegated) path.

## qtawesome-icons-2026q2-e1+e2 (2026-05-22) [merged]
- `qta.icon()` requires running QApplication — confirmed from `iconic_font.py` source. Returns empty QIcon + UserWarning (no exception) if called without one. Panel `_build_ui()` constructors must NOT call icon functions; defer to a `refresh_icons(theme)` method called from `MainWindow.__init__` after widget construction.
- Lazy `import qtawesome` at module level does NOT trigger font loading. Font loading fires on first `qta.icon()` call. Both deferred-import AND deferred first-call are needed to avoid the ~150-200 ms cold-boot cost.
- The `global _qta = None` pattern with per-function import is the canonical fix for qtawesome module-level issue #144. `functools.cache` is wrong here because it would pin the first theme's icon color across theme swaps.
- MDI icon picks: `mdi6.camera-retake` (Reset Camera), `mdi6.camera` (Screenshot), `mdi6.restore` (Reset Defaults). All in MDI 1.x-3.x, safely in mdi6 6.9.96. Verify at install-time via `qta-browser` OR parse `.venv/lib/python3.12/site-packages/qtawesome/fonts/materialdesignicons6-webfont-charmap-6.9.96.json` directly with Python (7,367 icons in qtawesome 1.4.2).
- qtawesome `color=` accepts "#rrggbb" hex strings — AI-13 compliance is automatic via `PALETTE_*["TEXT_VALUE"]`.
- For XS/S icon-adoption milestones, skip arXiv and OSS web searches entirely. Web research budget: 15 min on PyPI + icon catalog pages only.
- Instance-attribute storage gap: `view_panel.py` `_make_camera_group()` / `_make_screenshot_group()` create buttons as locals; implementer must add `self._reset_camera_btn`, `self._shot_btn` (or `self._preset_btns: dict[str, QPushButton]`) for `refresh_icons()` to reach them. Initialize the dict BEFORE `_build_ui()`.
- `rotated=N` IS supported in qtawesome 1.4.2: `iconic_font.py:143` (valid options) and `:232-233` (`QTransform.rotate`). Use `rotated=180` for directional reversals.
- `axis-x-arrow`, `axis-y-arrow`, `axis-z-arrow`, `axis-arrow` all exist in mdi6 6.9.96 — correct picks for camera-preset buttons.
- `mdi6.grid` (open lattice) vs `mdi6.border-outside` (heavy outer border + inner lines) for Wireframe vs Show-edges. `border-all` is too similar to `grid` at 16px.
- `QCheckBox.setIcon()` inherited from `QAbstractButton` — no `QToolButton` migration needed for icon-on-checkbox.
- Spinner deferral rationale: `QMovie.updated` can fire during `processEvents()` in `_render_current`. Existing `self._computing` guard blocks `_render_current` re-entry but NOT `QMovie.updated → label.update()`. Safe spinner needs QTimer-stepper that checks `_computing`, or QThread.
- `appearance_panel.py` had NO `refresh_icons` method after e1 (e1 had no icons in AppearancePanel). Adding for e2 requires the method + 3 new call sites in app.py.

## enriques-backface-2026q2-e1 (2026-05-22)
- For backface-culling milestones, ALWAYS run per-family off-screen renders before declaring "XS safe". Enriques has open-sheet double-curve geometry; Hanson has AI-7 winding-per-patch normals. Both break catastrophically under global `culling='back'`. Fermat quartic (closed convex) is the only safe family.
- The Hanson AI-7 conflict with culling is confirmed by render: 50% of cells face away from any camera position; `culling='back'` hides entire far-side patches on rotation.
- The Enriques canonical sextic `enriques_figure_1` default is `c=1.0` (min 0.1 per ParamSpec), NOT `c=0`. `c=0` raises ValueError. Any brief referencing "Enriques default c=0" contains a documentation error.
- Per-family actor property gating belongs in `AppearancePanel.apply_to_actor()` via a stored override field (e.g. `self._culling = None`), set by `set_culling(value)` called from `_on_variety_changed` / `_on_subtype_changed`.
- Challenger NONE ratings for single-kwarg rendering changes can be wrong when the kwarg's effect depends on per-family mesh topology. Always render first.
- PyVista `culling=True` is equivalent to `culling='back'` — confirmed via `actor.prop.culling == 'back'` check after `add_mesh(mesh, culling=True)`. Default `culling=None` maps to `'none'`.

## status-bar-bbox-2026q2-e1+e2 (2026-05-22) [merged]
- For XS UI-feedback milestones (~3 LOC), skip all external web searches. Signal is: exact insertion point in app.py, symmetry audit of generator sampling boxes, roadmap spec for the format string.
- `mesh.bounds` symmetry audit: grep `surfaces.py` for `np.linspace`. Any generator using `np.linspace(-bounds, bounds, n)` produces symmetric bbox and `±max` is exact. Hanson parametric is the only asymmetric case.
- Insertion point pattern: the `base_msg` f-string in `app.py:_render_current` is built in the SUCCESS branch (after `_apply_domain_and_render`). Any bbox metric reading `self._raw_mesh` must be read here, not earlier. ValueError/except branches already isolated.
- A dedicated `tests/test_status_bar_bbox.py` is cleaner than appending to `test_mesh_generators.py` — mesh-gen tests are smoke tests; bbox is a format-contract test.
- AI-14 + bbox: ValueError path clears `self._raw_mesh = None` and returns before `base_msg`. No extra guard needed.
- For deferred-finding closure milestones (prior critique already decided the format), skip ALL external searches. Brief value: (a) exact insertion points, (b) all 3 consuming sites for the variable rename, (c) exact `BBOX_REGEX` fix (use `\d{3}` not `\d+` to enforce `.3f`), (d) extending `math.isfinite` Hanson guard from 3 to all 6 bounds indices.
- When renaming a variable in only 2-3 places (e.g. `bbox_suffix` → `size_suffix`), ALWAYS recommend the rename if the old name/new semantics mismatch — cost trivial, git-blame clarity permanent.
- `view_panel.py`'s `_bbox_actor`/`_bbox_cb` are a separate VTK wireframe overlay, NOT the status-bar text readout. Cosmetic naming collision — do not rename.

## focus-ring-contrast-2026q2-e1 (2026-05-22)
- For pure-palette WCAG fix milestones, skip ALL external web searches — only signal is repo-local arithmetic. The WCAG formula is in `tests/test_styles_palette.py:26-41`; just run it inline.
- The "dual-pass feasibility check" (single hex clearing 3:1 on BOTH panel backgrounds simultaneously) is the first computation for any `FOCUS_RING`-style shared-palette token fix.
- Structural border tokens are ~1.1-1.4:1 on light panel — intentionally below 3:1 per structural-contrast pattern. Symmetric light non-text test should assert ONLY on `FOCUS_RING`.
- When the brief names a specific candidate hex, verify it first with arithmetic before sweeping broader space.
- The "key-identical palettes" Option A constraint is almost always satisfiable for medium-blue focus rings.

## realtime-variety-render-e6 (2026-05-22) [merged]
- For VTK/PyVista pipeline-replacement milestones, run small `.venv/Scripts/python.exe -c "..."` probes first — they resolve disputed API questions in <30 s and eliminate speculation.
- Run `python -c "import pyvista as pv; import inspect; print(inspect.signature(pv.ImageData.contour))"` first to confirm the `method=` kwarg exists in the pinned version — don't assume API availability.
- **Flying Edges `compute_normals`**: `pv.ImageData.contour([level], method='flying_edges', compute_normals=True)` produces gradient-based normals in the `Normals` point array (unit-length, verified). Challenger "normals lost" objections are moot. Accepted by PyVista 0.48.4 + VTK 9.6.2.
- **Ravel-order critical bug**: `indexing='ij'` meshgrid + `pv.ImageData` requires `field.ravel(order='F')` (Fortran/column-major). `order='C'` silently transposes x and z axes. Verify with an asymmetric ellipsoid (`x_radius ≠ z_radius`).
- **Flying Edges speedup (Windows 11, VTK 9.6.2)**: MC-only: 7-11× at n=220-260. Full-pipeline (with Taubin): ~2.5× at n=220. Kitware's "1-2 orders of magnitude" is multi-thread Intel x86; single-thread Windows is 7-10× on MC step but full pipeline dilutes to ~2.5×.
- The "gradient normals from skimage" doc in CONTEXT.md §3 / `_marching_cubes_to_polydata` docstring is a dead letter — overwritten by `compute_normals()` later in the same function. Code wins over docstrings.
- `pv.ImageData.contour(...)` returns `pv.PolyData` directly (no manual vertex/face assembly); never produces duplicate vertices (`.clean()` is a no-op); returns `n_points=0` on a field with no zero crossing (pre-existing guard MUST remain).
- For pipeline-swap milestones affecting N generators via one shared helper, count ALL generators before writing "N" in the brief. Repo has 11 implicit generators at e6 time (K3×2, Enriques×4, Dwork×1, Fano×4) — brief template said "8" (older count before Fano added).
- `calabi_yau_dwork` at `surfaces.py:711` uses `n=260` (not capped at 220 by e1) — in implicit pipeline, benefits directly from FE.
- `test_marching_cubes_empty.py` tests call `_marching_cubes_to_polydata` directly; pass unchanged because the ValueError guard is before the contour call.
- Baseline on Windows 11 Python 3.12: skimage MC for fermat n=220 = 170 ms; Flying Edges = 15 ms → 11× on MC step. Total `generate()` speedup ≈ 4-5× for Fermat (MC ~45% of total).
- For S-effort pipeline-replacement milestones where the implementation path is well-specified, agent-b brief (VTK/PyVista lens) is more valuable than agent-a (math lens) — consider single-agent (`--single`) mode for purely mechanical replacements.

## realtime-variety-render-e4 (2026-05-22) [merged]
- For Qt-threading-refactor milestones, the predecessor SPIKE script (`spike-thread-test.py`) IS the production blueprint — read its `WorkerSignals`/`MeshWorker` classes and recommend porting them verbatim rather than re-deriving QRunnable.
- The e1 queue-latest guard (`_computing` / `_pending_render`) does NOT need replacing — semantics flip from "blocking compute window" to "worker in flight." Catch-up `QTimer.singleShot(0)` MOVES from dispatch `finally` into the worker-result slot's `finally`.
- TWO distinct refs needed for VTK #18782 (not just the spike's one): (1) worker-side `self._result = mesh` before emit, AND (2) `MainWindow.self._active_worker` holding the worker for its whole flight — a local var is GC'd the instant dispatch returns, killing the worker mid-run.
- Supersede/cancel-and-resubmit race needs a monotonic generation counter ON TOP of queue-latest: a superseded worker that already finished `run()` can still deliver a queued `finished` signal after `_computing` was cleared. Slot must drop any result whose `generation_id != self._generation`. Extract `is_stale_result(result_gen, current_gen) -> bool` as a free function for AI-2 unit test.
- `warnings.catch_warnings(record=True)` and `except ValueError/Exception` blocks MUST move INTO worker `run()` — a main-thread `catch_warnings` cannot see a warning raised on a worker thread. Ship warning text + error kind/msg + `perf_counter` duration as fields of the result payload.
- Removing `processEvents()` for a worker design is AI-9-POSITIVE: deletes the only synchronous event-queue drain in the render path. New (benign) re-entrancy surface is the QueuedConnection slot, which cannot re-enter itself.
- The e1 `_computing` bool + `_pending_render` flag is NOT extensible to a worker — worked only because render was synchronous. A worker needs a monotonic job-id counter. Frame this to the implementer as a redesign, not an extension.
- AI-2 Qt-free test gap: CAN test = worker's pure compute call + extracted `is_latest_job(id, current)` free function (mirror `clipped_cache_is_valid`/`should_render_on_drag`); CANNOT = live QThreadPool dispatch, QueuedConnection delivery, cancel-resubmit timing, closeEvent teardown.
- WaitCursor leak is the classic worker-refactor footgun: `setOverrideCursor` on dispatch must pair with exactly one `restoreOverrideCursor` per dispatch, including for superseded jobs whose slot returns early on the id-check.
- The RuntimeWarning capture (Dwork conifold, CONTEXT.md §4.6) must move INTO the worker's `run()` since `surface.generate()` runs there — emit the warning text alongside the mesh in the finished signal.

## display-toggles-checkable-button-2026q3-e1 (2026-05-22)
- For pure QSS-design milestones (no math, no new variety), skip ALL web searches. Signal is 100% in repo-local files + WCAG arithmetic.
- `QCheckBox` vs `QPushButton(checkable=True)`: both inherit `toggled(bool)`, `setIcon()`, `setIconSize()`, `setChecked()` from `QAbstractButton` — zero API change in signal wiring or icon management. Migration is purely widget construction + QSS.
- WCAG 1.4.11 non-text: for a checked-state indicator, the BORDER (not fill) is the "state indicator" per spec. Reusing `FOCUS_RING` for the border avoids a new `BORDER_TOGGLE_CHECKED` token — `FOCUS_RING` already passes 3:1 on both panel backgrounds.
- New `BG_TOGGLE_CHECKED` fill token: light `#d4e6f5` / dark `#1a3048`. Hover tint vs checked fill is ~1.10:1 — acceptable when the border is the WCAG indicator.
- `test_palette_dark_has_minimum_tokens` asserts key set equality. New token in `PALETTE_LIGHT` MUST be simultaneously added to `PALETTE_DARK`.
- `test_app_stylesheet_substitutes_no_raw_hex_outside_palette` enforces that all hex in rendered stylesheet comes from palette tokens. New QSS rules must reference `palette["TOKEN"]` not literals.
- AI-2 for widget tests: `QPushButton`/`QCheckBox` construction requires `QApplication` — can't test in Qt-free suite. Use source-text grep tests instead (assert `QCheckBox("Wireframe")` not in source, `setCheckable(True)` in source). Weaker but AI-2 compliant.
- `setProperty("role", "display-toggle")` for the checked button — NOT a widget-level `setStyleSheet` (which would override the QApplication cascade and break dark mode).
- `text-align: left` essential in the QPushButton QSS for a vertical panel — without it, QPushButton defaults to center-aligned content.
- `setFlat(True)` should NOT be called alongside transparent QSS styling — may interfere with border rendering.

## enriques-taubin-spike + hq-smoothing-2026q3-e1 (2026-05-22) [merged]
- For SPIKE milestones, researcher's primary job is the measurement protocol and pre-committed decision rule — NOT predicting the outcome.
- `_marching_cubes_to_polydata` uses `smooth_iter: int = 20` (`surfaces.py:91`). Adding `second_smooth_iter: int = 0` is the correct architectural extension — do NOT add a hard-coded second call inside the helper. Zero default preserves all non-Enriques surfaces unchanged.
- Per-figure Taubin benefit: figs 1+2 (double curves) YES; figs 3+4 (A₁ nodes) NO. Maps from CONTEXT.md §8.13 culling audit to the Taubin question.
- `smooth_taubin` signature: `inplace=False` default — always returns new PolyData. Stacking: `mesh = mesh.smooth_taubin(n1, pb1); mesh = mesh.smooth_taubin(n2, pb2)`.
- Bounds-padding AI-14 safety: with n=220-240, 5% bounds increase raises voxel spacing by ~5% — still 0.014-0.022 side, above the marching-cubes practical floor. Verify spacing = `2*bounds_new/(n-1)` stays below 0.03.
- The 500 ms budget is generate-ONLY (`time.perf_counter()` around `surface.generate()`). CONTEXT.md §4.4 "~0.5 s mesh generation", §9 "~0.5 s window", roadmap §4 [MUST] "~500ms single-render budget" — all consistent.
- Spike scripts go at `.claude/scripts/<spike-name>.py` NOT in `tests/` (side-effects: writes files, prints timings). Tests must be AI-2 compliant.
- For "close a deferred spike" milestones, the architecture decision IS the entire deliverable — spend time on the decision matrix (Options a/b/c), not external search.
- Pattern-A discipline (state on AppearancePanel, MainWindow sets via `set_X(value)`, `apply_to_actor` reads it) is the canonical home for per-variety rendering state. HQ smoothing follows Pattern-A for STORAGE but DIFFERS for TRIGGERING: culling changes ACTOR PROPERTIES (no mesh regen; `actor.prop.*` + `plotter.render()`); HQ smoothing changes MESH GENERATION (requires `_invalidate_clipped_mesh()` + `_render_current()`).
- AI-8 "no bimodal ParamSpec" directly blocks Option (a) for a boolean opt-in. Check AI-8 BEFORE enumerating bool-as-float coercion paths.
- `hq_smoothing_changed = Signal(bool)` on AppearancePanel keeps the panel's signal contract independent of MainWindow internals.
- Cache invalidation is second-most-important concern after architecture choice: any toggle changing raw mesh generation MUST trigger `_invalidate_clipped_mesh()` before `_render_current()`.
- Per-subtype enable/disable requires TWO gating sites: `_on_variety_changed` AND `_on_subtype_changed`.
- For boolean quality opts-in, hardcode the parameter value (`n_iter=40`) at the generator level — avoids `IntParamSpec` surface.

## realtime-variety-render-e2 (2026-05-22)
- Pre-implementation detection: always `git log --oneline --all | grep -i "e{N}"` BEFORE diving into a research pass. State.json stuck at `research-running` is a pipeline state artifact, not a signal that work remained.
- Milestone state divergence heuristic: if `state.json.phase == "research-running"` but `tests/test_<milestone>.py` exists AND all tests pass AND commit appears in `git log`, the milestone is complete.
- CAND-8/e2 dataclass pattern: trailing `typical_ms: int = 0` on a non-frozen `@dataclass` is the clean pattern for surface-speed hints. `should_render_on_drag` free-function predicate (not a method) required by AI-2.
- Grep for `params_preview_changed` to find e2-class drag-tick wiring: `params_changed` (release, always renders) vs `params_preview_changed` (drag-tick, speed-routed).
- AI-9 analysis for async dispatch: after e4 (background worker), the re-entrancy concern is `_computing` single-flight + `_pending_render` queue-latest, NOT `processEvents`.

## realtime-variety-render-e5+e5b (2026-05-22 / 2026-05-23) [merged]
- For Numba-JIT-swap milestones, math-lens job is mostly transcription: read the exact NumPy field expression with file:line and confirm the kernel is term-by-term copy — surfaces.py fields are pure scalar arithmetic (`+ - *`, `x2*x2` not `x**4`), the easiest possible `@njit` shape.
- For Numba v1 "extend-to-the-remaining-N-generators" milestones (mechanical transcription with passed v0 + spike), brief value is entirely: (a) per-generator field expression + clip cap + ValueError/RuntimeWarning pre-check file:line, (b) per-generator e4b `coarse_n` value (drives composition test design), (c) explicit "don't write `x**N`, write `x*x*...*x`" callouts for any power operator v0 didn't exercise. Skip arXiv/OSS entirely.
- Numba numerical-equivalence tests must NOT keep the spike's `rtol=1e-12` — held only for the spike's 2-term toy field. Real 6-7-term fields with a post-`np.clip` need `rtol=atol=1e-9`: loose enough for fused-scalar-vs-broadcast drift, tight enough that a real transcription bug (wrong sign / missing term) fails loudly.
- `prange` adds NO extra float error when every output cell is an independent write (pure map, no cross-iteration reduction) — parallel is bit-identical to serial. Only `prange` *reductions* reorder sums.
- `np.clip(F, lo, hi)` JITs fine but the scalar `min(hi, max(lo, F))` form inside the prange loop is cleaner and folds the clip into the kernel.
- When a spike report exists, it SUPERSEDES the roadmap epic text — the e5 spike corrected a stale version pin (`numba>=0.60,<0.62` → `>=0.65,<0.66`) and an unachievable acceptance signal (eager warm-up ≤500 ms → "JIT off the GUI thread + cache=True").
- AI-14 for a compute-swap milestone: confirm the kernel only changes how the field `np.ndarray` is built; the `ValueError` zero-crossing guard in `_marching_cubes_to_polydata` is untouched. State the file:line so the implementer can see it is downstream.
- Numba license is BSD-2-Clause (permissive, redistribution-safe) — always cite for an OSS compute dep.
- For a Numba kernel inside a VTK-SMP app, headline risk is thread oversubscription: kernel and Flying Edges run back-to-back on SAME e4 QThreadPool worker. Mitigation is `numba.config.THREADING_LAYER = "workqueue"` at module top + (optional) `numba.set_num_threads(~half core count)`. Backup: serial `@njit` already clears ≥5×.
- `numba.config.THREADING_LAYER = "workqueue"` goes at TOP of surfaces.py right after `import numba`, BEFORE `from numba import njit, prange` and before any `@njit` decorator.
- CAND-12 telemetry capture point for before/after perf signals: the `[render] <label>: <ms>` stdout line at `app.py:636` (driven by `MeshResult.gen_ms`, measured by `perf_counter` in `render_worker.MeshWorker._compute`). Don't add new telemetry to MeshWorker.
- The e5 spike's working test script (`spike-numba-test.py`) IS the implementer's kernel template — point at `_field_njit_parallel` (out-array param, `prange` outer i, plain `range` inner, scalar `g[i]` reads) verbatim.
- The `np.clip(F, lo, hi)` post-step in the NumPy expression MUST move INSIDE the kernel as a per-voxel `if/elif`. Keeping it outside re-introduces a full-array NumPy temp pass AND a kernel omitting it fails the `allclose` reference test.
- `cache=True` IS supported for `@njit(parallel=True)` in modern numba (the old "no cache for parallel" limitation is long gone). Cache lives in source module's `__pycache__`; per-machine; auto-invalidates on source/version/CPU change. Read-only install dir silently degrades to per-process recompile.
- `@njit(cache=True)` cache files are per-function-keyed (function source hash + numba version + llvmlite version + CPU features). 11 kernels = 22 cache files in module's `__pycache__/`; no cross-kernel collision. Stating this defuses "cache stacking risk" reviewer concerns.
- CONTEXT.md §8.20 `workqueue` single-flight constraint scales identically for 11 kernels vs 2 — the `_computing` guard at `app.py:613` already serializes all `surface.generate` calls process-wide. v1's 9-kernel addition does NOT widen the constraint.
- Per-kernel JIT cold-cache cost (~300-400 ms for typical `@njit(parallel=True)` polynomial kernel) is BOUNDED by the surface's typical generate budget (Kummer/Enriques baseline ~450 ms) — first-touch latency disappears INSIDE the surface's normal compute window. "9 × 300 ms = 2.7 s cold-cache cost" framing is misleading: 9 separate first-touches spread across user clicks, each absorbed inside its own generate() window.
- For RuntimeWarning preservation across Numba kernel migration: grep confirms `warnings.warn(...)` calls fire BEFORE the field block (not inside meshgrid + broadcast section). Dwork at `surfaces.py:979-990` (before line 991 field build) and two_quadrics at `:1137-1142` (before `:1146` field build) both pass.
- For Dwork `x**5` (only e5b kernel with non-perfect-power form not in v0 template): per-voxel transcription should be `x2 = x*x; x4 = x2*x2; x5 = x4*x` for IEEE-754 op-order reproducibility. Same for Segre's `**3` and sextic double solid's `**6`. State the explicit-multiply rule even when Numba would internally fold the power.

## realtime-variety-render-e4b (2026-05-22) [merged]
- For coarse-LOD milestones, the n-sweep timing+topology probe is the critical research deliverable — run `.venv/Scripts/python.exe -c "..."` first (probe all 11 implicit generators at `[60, 80, 100, 120, prod_n]` for time + n_points + bbox + topology-honesty signature). Without numbers the floor table is speculation.
- For a coarse-LOD milestone built on top of e4-style worker dispatch, the cleanest plumbing is `params["n"] = surface.coarse_n` injected at dispatch time — NOT a new worker constructor kwarg for n. Worker's existing `dict[str, float]` params API carries the kwarg vehicle.
- The `is_coarse: bool` flag MUST be a worker constructor arg + `MeshResult` field — worker is mode-agnostic by design (run() doesn't change behavior on coarse), but result slot needs to know how to format the status bar.
- AI-15 Preview-badge "state machine" is really 2 states (IDLE / PREVIEW) and 5 transitions. Clean impl: badge IS the status-bar text; coarse-result writes `"Preview — {label} — NNN ms"`; full-result writes the standard base_msg; "clear" is by replacement (`showMessage` replaces, not appends).
- AI-6 Hanson-skip in coarse-LOD: THREE-LAYER guard — (1) `dispatch_mode` predicate returns "full" not "coarse" for `typical_ms > 0`; (2) `Surface.coarse_n = 0` default makes params injection a no-op; (3) worker stays mode-agnostic so even if both (1) and (2) fail the worker can't violate AI-6.
- `Surface.coarse_n` as a trailing defaulted dataclass field (mirroring `typical_ms`) is cleaner than a free-standing `COARSE_N: dict[Callable, int]` registry — no second source of truth.
- `_pending_render` semantics under per-tick coarse + late full-release: add `_pending_is_coarse` and use AND-promote rule (`_pending_is_coarse = _pending_is_coarse AND new_coarse`). Mirrors existing `_pending_reset_camera` OR-promote at `app.py:620`.
- Extract `dispatch_mode(surface, in_drag) -> Literal["coarse","full","skip"]` free function — mirrors `should_render_on_drag` / `clipped_cache_is_valid` / `is_stale_result`.
- 8-octant vertex-count symmetry is the cheapest mechanical Kummer-16-node honesty probe: octant counts equal within 1% at n=60 → S₄ tetrahedral structure preserved → 16 nodes distinguishable.
- Dwork conifold at ψ=1: d_min to (1,1,1) is `n`-invariant (≈2.4 at n=60/80/120/260; 0.0 at n=100 by grid alignment coincidence). Marching cubes misses the node at ALL n; smooth complement preserved. Test should assert smooth-complement bbox stability, not "conifold visible".
- `fano_two_quadrics` is the ε-tube fragility surface — voxel-spacing-vs-ε arithmetic (`2*bounds/(n-1)` vs ε) shows coarse_n would push spacing toward ε. Opt out at v0 (`coarse_n = 0`).
- For LOD milestones, propose `coarse_n: int = 0` field on `Surface` dataclass over a module-level dict. Two-line precedent + discoverability beats DRY refactoring opportunity.
- AI-6 implicit-vs-parametric gating: better predicate is `coarse_n > 0` opt-in (positive predicate, correctly excludes future opt-outs). Mutual exclusion with `should_render_on_drag(surface)` partitions all surfaces into {Hanson-fast, coarse-eligible, opt-out}.
- AI-15 badge wording: "Preview — {label} — NNN ms" follows Mathematica `ControlActive[ ]` / ParaView "Interactive" / Blender "Material Preview" peer conventions.
- Worker dispatch for coarse-LOD kwarg injection: mirror e1's `hq_smoothing=True` injection at `app.py:647-652`.
- `MeshResult` gains `is_coarse: bool = False` (trailing defaulted field). Slot reads `result.is_coarse` for branching — self-describing.
- Status-bar bbox readout (`app.py:789-792` reads `_raw_mesh.bounds`) MUST be suppressed during coarse renders — coarse bbox would have ~1% drift; reading 3-decimal-place "honest" numbers from a transient approximation is AI-15-dishonest.

## appearance-panel-layout-pass-2026q3-e2 (2026-05-22)
- "Close deferred F-M2 + F-L2" briefs are pure QSS/widget-property milestones — architecture decision (option 1 vs 2 vs 3) is the central question.
- "Layout consistency" briefs resolve to role-property narrowing (Option 2) when broader fix (Option 1, global rule) has documented regression risk.
- `render-panel-chrome.py` captures essential for layout milestones. Run immediately, Read the PNG to confirm alignment fracture is real before code analysis.
- For header rename milestones, grep `QGroupBox(` in target panel for the current name. MeshLab "Render Mode" was the exact peer-tool match for wireframe+edges+quality.
- macOS QSS footgun: when a QSS fix needs to force `QStyleSheetStyle` (for `text-align: left` to be honored), the rule MUST include at least one box-model property (padding, border, or background).
- AI-11: `setProperty("role", "string-value")` is NEVER an AI-11 concern. AI-11 covers fully-qualified Qt enum forms only.
- AI-13: text-align changes have zero PyVista color-flow impact.
- AI-2: New tests for QSS/role-property changes are always source-text grep tests (count `setProperty` calls, grep rendered stylesheet). Use `count >= N` not `in` for multi-instance checks.

## realtime-variety-render-e5b agent-a (2026-05-23)
- For per-generator math-transcription briefs in mechanical-extension milestones (v1-extends-v0), the load-bearing structure is the **per-generator transcription TABLE** (one row per kernel) with columns: file:line, field expression, scalar pre-compute, clip cap, kernel signature, JIT-incompat risk, operator-order rule, 3 test parameter points. Anything not in the table is filler.
- **Operator-order grouping discipline** is the per-kernel test-design choice that matters: for 4+-way products (Kummer's `lam*p*q*r*s`, fig 4's `4*t0*t1*t2`), pick ONE grouping (e.g. `((p*q)*r)*s`) and use the SAME grouping in both kernel AND the test's NumPy reference function — the contract is "kernel ≡ reference," not "kernel ≡ original broadcast." If the test fails at the chosen grouping, switch grouping in BOTH places.
- For RuntimeWarning generators in transcription milestones, the test design should AVOID parameter points that trigger the warning (e.g. for Dwork pick ψ=2.5 not ψ=1.0; for two_quadrics pick ε=0.40 not ε<0.08) — keeps the kernel-equivalence test deterministic without needing `pytest.warns(...)` or `warnings.catch_warnings` plumbing. The warning is generator-scope, not kernel-scope, so the kernel test never sees it anyway.
- For Kummer's `sqrt(2.0)` scalar pre-compute, BOTH "pass as kernel scalar arg" AND "write literal `1.4142135623730951` inside kernel" compile fine — the e5 template style passes scalars in, which keeps the kernel symbolic and avoids magic numbers. Recommend the arg-pass form for consistency.
- Enriques fig 1 has `n = int(round(n))` at `surfaces.py:614`; figs 2/3/4 do NOT (plain `n: int` kwarg). Optional defensive AI-8 add for figs 2/3/4 is one-line, zero risk, future-proofs against the same caller patterns the e5 brief flagged — recommend including in v1 as bundled hygiene.
- Asymmetric-field kernels (Klein cubic `x + x²y + y²z + z₀z² + z₀²` is the only one of the 9 v1 kernels that is asymmetric in `(x,y,z)`) — the symmetry-bug coverage note in the test file `:18-26` does NOT apply: an axis-transpose bug WOULD be caught by the equivalence test for Klein, unlike the 8 symmetric kernels. This is a positive: Klein is the canary that proves axis-mapping is correct, and the 8 symmetric kernels coast on the "transpose is harmless because the contour is identical" argument.

## hq-smoothing-label-rename-2026q3-e1 (2026-05-22)
- Bucket structure: USER-VISIBLE (rename), TEST ASSERTION (rename), SYMBOL/COMMENT (stays), DOC PROSE (rename with note). Honor brief's "internal symbols stay" opt-out.
- Grep pattern: `"HQ\|hq_smoothing\|\[HQ\]\|Double.pass"`. Read adversary-critique.md first. Source-grep tests with `src.find(` must be updated when user-visible strings change.
- AI-15 label check: "Double-pass" = exactly 2 Taubin passes (surfaces.py:558,605). Button fit: setMinimumWidth(200) at appearance_panel.py:127; 18 chars at 8px = 144px — fits.

## appearance-panel-render-mode-split-2026q3-e3 (2026-05-22)
- QGroupBox title `&` activates keyboard accelerator. Use `&&` for literal `&` with no shortcut. "Display && Quality" is the correct source literal.
- Pure label-rename scope: user-visible string, test assertions, inline comments, styles.py comments, CONTEXT.md prose (add "renamed from X by milestone-id"). Historical artifacts STAY.
- Rename test function when adding negative regression guard — `render_mode_group_header` asserting "Display & Quality" is semantically misleading.

## render-busy-spinner-2026q3-e1 (2026-05-22)
- "Lift §9 deferral" briefs: (1) audit blocker obsolescence with file:line, (2) implement. Blocker audit first.
- QStatusBar addWidget() IS hidden by showMessage() temporary messages. Since AVC uses showMessage() at every render event (12+ call sites), use addPermanentWidget() (RIGHT side, never obscured) for spinner. When brief says "left" AND "permanent-widget", the never-hidden invariant overrides position preference.
- qtawesome Spin animation requires QIcon.paint() in paintEvent — only QAbstractButton subclasses do this. QLabel.setPixmap() is static. Use QPushButton(flat=True, enabled=False) for status-bar spinner host widget.
- qta.Spin default step=1 → 3.6s/rotation (too slow for 0.5-1.5s window). Use step=6 → 600ms/rotation.
- mdi6.loading (0xf0772) IS in MDI6 6.9.96. AI-9 for spinner: QTimer.timeout → _update() → widget.update() → paintEvent = pure paint path, no re-entry. Toggle at the two _computing=True/False sites directly (app.py:670, 829) — no property setter needed.

## qsettings-persistence-v1-2026q3-e1 (2026-05-23)
- "Lift §9 non-goal" pattern: audit the exact §9 text to confirm it is a deferral ("doesn't do X"), not a principled rejection ("decided against X"). The §9 "shipped" spinner entry is a precedent that §9 items are closeable.
- QSettings restore must go at the END of `__init__`, AFTER ALL `addDockWidget`/`splitDockWidget` calls. `restoreState()` before `addDockWidget()` is silently overridden by the subsequent dock calls.
- Global singleton form preferred: `QApplication.setOrganizationName("AVC") + setApplicationName("AlgebraicVarietyCrossSection")` in `main()` before `QApplication(sys.argv)`; then `QSettings()` no-arg at every call site. Per-call `QSettings("AVC", "...")` works but repeats the string literal.
- Application name: CamelCase `"AlgebraicVarietyCrossSection"` (not hyphenated `"algebraic-variety-cross-section"`) per Qt convention; produces readable plist/INI filenames.
- schema_version key costs 1 LOC and enables V2 migration; add it in V1.
- Live write-back of LastSession/variety+subtype in `_on_variety_changed`/_on_subtype_changed survives SIGKILL; the write-back is a no-op when fired from `_restore_settings()` setCurrentText — QSettings.setValue is synchronous, no signal re-entry.
- `closeEvent` save ordering: `_save_settings()` FIRST, then signal disconnect, then `waitForDone(30000)`, then `plotter.close()`, then `super().closeEvent(event)`.
- AI-2 compliant tests: pure source-text greps; `QSettings()` is never constructed in tests. Pattern: `_APP_SRC.find("...")` for positional checks, `assert "..." in _APP_SRC` for presence.
- AI-9 audit note: `setCurrentText()` fires handlers that call `_render_current` (correct), and also write-back `setValue()` (safe no-op). The write-back does NOT call `processEvents` and does NOT re-enter `_on_variety_changed`.

## mesh-export-stl-obj-ply-2026q3-e1 (2026-05-23)
- "Lift §9 non-goal" pattern confirmed: the §9 deferral text itself contains the implementation recipe ("one line: mesh.save(...)") — quote it in the brief to anchor the authorization.
- `_clear_actor()` does NOT reset `_raw_mesh`. When the user reverts to "-- Select --" placeholder, `_clear_actor()` is called but `_raw_mesh` remains non-None. Any feature guarded on `_raw_mesh is not None` needs an additional explicit disable in the `_on_variety_changed` else branch (line 524) to match user expectation.
- `mesh.save()` raises: `ValueError` for unsupported extension, `PermissionError` for denied I/O, `FileNotFoundError` for missing parent dir. The `OSError` precedent from qsettings closeEvent is too narrow here — use broad `except Exception` for export handlers that call `mesh.save`.
- macOS and Linux QFileDialog.getSaveFileName does NOT auto-append extensions from the selected filter when the user types a name manually. Pre-validate the extension in the handler before calling save.
- PyVista PLY preserves the `Normals` point array through round-trip save/reload (verified 0.48.0). STL and OBJ recompute face normals at save time (`recompute_normals=True` default).
- Export action lifecycle: disable at construction (in `_build_file_menu`), enable in `_on_mesh_ready` success, disable in `_on_mesh_ready` error, disable in `_on_variety_changed` else branch. Four sites total.
- `QAction` is already imported in app.py (line 14); only `QFileDialog` needs adding to the PySide6.QtWidgets import block.
- File menu position: calling `_build_file_menu()` BEFORE `_build_theme_menu()` in `__init__` automatically places File left of Theme (Qt addMenu order = left-to-right).
- Diff size for a simple File menu + handler + tests: ~141 LOC, 3 files. Inline (no new module). The 8 tests are all source-text greps (AI-2 compliant).

## hq-disable-toast-2026q3-e1 (2026-05-23)
- **Brief F-L2 cross-citation was partially wrong.** The brief claimed qtawesome-icons-2026q2-e2 "re-flagged F-L2" but that milestone's F-L2 was a completely different finding (tooltip accessibility for rotated axis glyphs). Always read the OTHER milestone's adversary-critique before accepting a cross-citation as fact.
- **Dual-call-site requirement from trigger analysis.** When a prior-state capture + toast must fire on "HQ was on, now isn't eligible", variety-only scope misses the Enriques Fig.1 → Fig.3 subtype-only transition (variety combo unchanged; `_on_variety_changed` does NOT fire). Always trace BOTH `_on_variety_changed` and `_on_subtype_changed` for any feature that gates on variety+subtype combination.
- **Capture prior state BEFORE the clear call.** `set_hq_smoothing_eligible(False)` sets `_hq_smoothing = False` AFTER the `setChecked(False)` call (appearance_panel.py:614). Read `self.appearance_panel.hq_smoothing` BEFORE calling `set_hq_smoothing_eligible(False)` — reading after always yields False.
- **Option B (timeout showMessage) is wrong for "append to existing variety message".** `showMessage(text, timeout_ms)` replaces the current message immediately; the timeout just auto-clears after N ms. Using it after a variety-branch `showMessage` would REPLACE, not append, the variety message. Option A (build combined string with `_hq_note` variable) is the correct approach.
- **Option C (currentMessage + append) is fragile.** Reading `currentMessage()` after `showMessage(variety_text)` works but races any intervening signal-chain `showMessage`. Option A (pre-build the combined string) is cleaner.
- **4 source-grep tests cover the lifecycle.** One test verifies idx_read < idx_clear (ordering guarantee). One verifies the `if _prior_hq` guard. One verifies the message text references the eligibility scope. One verifies dual-method presence (count >= 2).
- **Diff size estimate: ~78 LOC** (app.py ~20 LOC, new test file ~55 LOC, CONTEXT.md ~3 LOC). Inline only, no new module.

## cleanup-deferred-findings-2026q3-e1 (2026-05-23)
- **Pre-research "already-fixed" scan is mandatory for batch-cleanup milestones.** For each deferred item, grep the target file AND check the rectification-status section at the bottom of the adversary-critique before writing any brief section. Items 2, 4, 6 of this batch were already closed in prior rect passes (focus-ring-contrast-2026q2-e1, e4b rect, e5b rect respectively). Skipping the already-fixed check wastes an implementer's time.
- **Deferred-finding IDs in state.json don't always match the critique section labels.** `M_menu_nest` in dark-mode's state.json was the FRONTEND critique's MEDIUM-1 (Theme menu nesting under View), not a QMenu OS-palette finding. The cleanup brief's description "Qt right-click context menus inherit OS palette" is the brief author's characterization of a DIFFERENT real problem (QMenu QSS gap), not a verbatim finding quote. Always read the full adversary + frontend critique text rather than relying on the state.json finding IDs.
- **WCAG 1.4.11 swatch chip: boundary color must clear 3:1 vs BOTH adjacent surfaces.** The swatch chip's existing #888888 border cleared 3.11:1 vs BG_PANEL but only 1.35-1.67:1 vs the variety fill colors (FAIL on the "body fill" side). The 3:1 requirement is met only when the boundary indicator achieves the ratio against the component interior AND the background. Upgrade to TEXT_VALUE (#333333) for the light-theme BORDER_SWATCH token — passes both sides (11.09:1 vs bg_panel, 4.81-5.94:1 vs variety fills).
- **VARIETY_TOOLTIPS vs SUBTYPE_TOOLTIPS: the e4b rect added LOD note to VARIETY (family-level) but not SUBTYPE.** For item 3 (M7), verify both dicts. The M-front-2 rectification note in e4b says "added to VARIETY_TOOLTIPS" — users who hover an individual subtype combo item see SUBTYPE_TOOLTIPS, not VARIETY_TOOLTIPS. Check BOTH before declaring a tooltip finding closed.
- **Icon rebind site count for QTimer/Spin comment: THREE sites in app.py** (init in `_build_ui` ~line 390, `_on_theme_changed` ~line 1615, `_apply_system_theme` ~line 1663). All three need the comment; the init site can use a shorter cross-reference to the theme-changed site where the full rationale appears.
