# lessons -- milestone-researcher

## panel-refresh-2026q2-e2 (2026-05-20) [merged]

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

## CORRECTION 2026-05-23 (restructure-full-audit-2026q2-r1 batch 4)
Panel file locations changed. Old path → new path:
- `appearance_panel.py` (root) → `panels/appearance.py`; module `appearance_panel` → `panels.appearance`
- `view_panel.py` (root) → `panels/view.py`; module `view_panel` → `panels.view`
- `parameters_panel.py` (root) → `panels/parameters.py`; module `parameters_panel` → `panels.parameters`
- `parameter_grid_panel.py` (root) → `panels/parameter_grid_panel.py`; module `parameter_grid_panel` → `panels.parameter_grid_panel`
Lessons that cite `appearance_panel.py:48`, `appearance_panel.py:614`, etc.: line-number references should be
re-verified against `panels/appearance.py` (line numbers may differ slightly if any edits landed during the move).
Symbol names (AppearancePanel, ParametersPanel, etc.) are unchanged. Root-level shims remain (DeprecationWarning).
