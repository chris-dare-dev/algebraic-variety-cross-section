# lessons -- milestone-researcher

## panel-refresh-2026q2-e2 (2026-05-20) [MERGED]
- For palette-token refactors: scan ALL 5 files (styles.py, appearance_panel.py, view_panel.py, parameters_panel.py, app.py) for `#[0-9a-fA-F]{3,6}` first — view_panel.py and parameters_panel.py had zero hex literals (false scope avoided). appearance_panel.py and app.py both had untracked hex that styles.py did not cover.
- Backward-compat pattern: old named constants become `= PALETTE_LIGHT["TOKEN"]` — zero call-site-change migration. Recommend proactively so implementer doesn't break 5 import sites.
- Semantic role names win over CSS-hex-variable names: BG_VIEWPORT not viewport_background_hex. External refs (qt-material, napari, ParaView, QPalette) all confirm this.
- Map downstream milestones to specific dict key reads BEFORE writing brief — renaming tokens after UPL-1 ships invalidates downstream sketches.
- AI-11 violations in existing code (Qt.AA_ShareOpenGLContexts at app.py:429) — note as out-of-scope pre-existing, not silently fix. WCAG disabled-state exception: TEXT_DISABLED=#aaaaaa is intentionally low-contrast — don't flag.

## graph-and-window-2026q2-e1 (2026-05-21)
- For XS tooling milestones, skip arXiv/OSS searches entirely. `clearFocus()` suppresses focus-ring artifacts; `setFocusPolicy(NoFocus)` on a container does NOT prevent child tab-stops from receiving focus.
- Bare QDockWidget outside QMainWindow is AI-3 safe for offscreen panel grabs. Check `appearance_panel.apply_to_actor()` for `SetAmbient`/`SetDiffuse` before implementing any lighting-param candidate.

## variety-palette-2026q2-e1 (2026-05-21)
- For pure palette milestones, skip all external searches. WCAG threshold: 4.5:1 text (not 3:1 non-text) for variety colors because the color appears as status-bar text.
- Unicode key identity: "Calabi–Yau 3-fold" uses U+2013 en-dash; "Fano 3-fold (ρ=1)" uses U+03C1. Copy-paste from surfaces.py only. Hue separation ≥25° HSV between all variety color pairs required.
- Delete (not supplement) the stub `test_variety_default_color_is_stub_for_upl5` test when the dict is populated. `set_default_color` must NOT call render — caller flows naturally to `_render_current`.

## dark-mode-2026q2-e1 (2026-05-22)
- Compute WCAG ratios numerically first. BG_PANEL_DARK=#252526. APP_STYLESHEET_DARK naming is load-bearing (render-panel-chrome.py detects via getattr). `_render_stylesheet(palette: dict)` avoids drift from duplicate f-string templates.
- QGuiApplication.styleHints().colorScheme() (Qt 6.5+) — no darkdetect dep. VARIETY_DEFAULT_COLOR_DARK identical to light (all 4 clear 3:1/4.5:1 on dark backgrounds). TEXT_DISABLED_DARK: no WCAG test (§1.4.3 disabled exception).
- LOC estimate: ~270 total (styles.py ~75, app.py ~55, appearance_panel.py ~5, tests ~110, CONTEXT.md ~25).

## qtawesome-icons-2026q2-e1 (2026-05-22)
- `qta.icon()` requires live QApplication — returns empty QIcon + UserWarning without one. Defer all calls to `refresh_icons(theme)` called AFTER widget construction. Lazy import defers ~150-200ms font-load to first icon paint.
- `global _qta = None` pattern is canonical fix for issue #144. `functools.cache` wrong (pins first theme color). `color=` accepts "#rrggbb" 6-digit hex — AI-13 automatic with PALETTE["TEXT_VALUE"].
- For XS/S icon milestones, skip arXiv/OSS. Instance-attribute storage gap: `_make_camera_group()` creates buttons as locals — promoter must add `self._reset_camera_btn`, `self._shot_btn`.

## qtawesome-icons-2026q2-e2 (2026-05-22)
- MDI6 charmap JSON at `.venv/lib/python3.12/site-packages/qtawesome/fonts/materialdesignicons6-webfont-charmap-6.9.96.json` is ground-truth for icon name verification (7,367 icons). Parse directly vs qta-browser.
- `rotated=N` supported in qtawesome 1.4.2. axis-x/y/z-arrow and axis-arrow all exist in mdi6 6.9.96. Wireframe/show-edges: mdi6.grid (open lattice) vs mdi6.border-outside (filled outer border) — mdi6.border-all too similar at 16px.
- QCheckBox.setIcon() inherited from QAbstractButton — no QToolButton needed. When factory creates buttons in a loop as locals, promote to dict (`self._preset_btns: dict[str, QPushButton] = {}`).
- Spinner deferral (OBSOLETE as of render-busy-spinner-2026q3-e1): QMovie.updated signal raced processEvents(). Now mooted by e4 worker move.
- AppearancePanel lacked refresh_icons after e1. Adding for e2 requires method + 3 call sites in app.py (_init_, _on_theme_changed, _apply_system_theme).

## enriques-backface-2026q2-e1 (2026-05-22)
- Always run per-family off-screen renders before declaring "XS safe." Enriques double-curve + Hanson AI-7 normals both break catastrophically under global culling='back'. Fermat quartic (closed convex) is the only safe family.
- Enriques canonical sextic default c=1.0 (min 0.1 per ParamSpec), NOT c=0. Per-family culling via AppearancePanel.set_culling() + _on_variety_changed gating. PyVista culling=True == culling='back'.

## status-bar-bbox-2026q2-e1/e2 (2026-05-22) [MERGED]
- For XS UI milestones (~3 LOC), skip external searches. Insertion point: `base_msg` f-string in SUCCESS branch of _render_current after _apply_domain_and_render returns.
- BBOX_REGEX precision guard: `\d{3}` (not `\d+`) enforces `.3f` contract. When switching ±max to full-extent, isfinite guards must extend from 3 to all 6 bounds indices (b[0],b[2],b[4] also matter).
- Dedicated test file cleaner than appending to mesh smoke tests. `view_panel.py`'s `_bbox_actor` is VTK wireframe overlay, NOT the status-bar text — naming collision is cosmetic.

## focus-ring-contrast-2026q2-e1 (2026-05-22)
- Skip ALL external searches — WCAG formula already in test_styles_palette.py:26-41. Run dual-pass feasibility check FIRST: single hex clearing 3:1 on BOTH panel backgrounds.
- Structural borders (BORDER_GROUP_BOX etc.) are ~1.1-1.4:1 intentionally — assert ONLY on FOCUS_RING, not structural tokens. Medium-blue sweet spot almost always satisfies dual-pass.

## realtime-variety-render-e6 (2026-05-22) [MERGED]
- Run API probes first. `pv.ImageData.contour([level], method='flying_edges', compute_normals=True)` produces gradient-based normals (unit-length, verified). `indexing='ij'` meshgrid + pv.ImageData requires `field.ravel(order='F')` — wrong order scrambles geometry silently.
- Flying Edges speedup (macOS Apple Silicon): ~4-5× total pipeline. No clean() after FE (collapses cells → inside-out shading; CONTEXT.md §8.17). 7,367 icons in mdi6 6.9.96 charmap JSON.
- Check ALL generators before writing count in brief — repo had 11 implicit generators at e6 time (K3×2, Enriques×4, Dwork×1, Fano×4). The docstring normals text is a dead letter if code overwrites it downstream — code wins.

## realtime-variety-render-e4 (2026-05-22) [MERGED]
- Predecessor SPIKE script IS the blueprint — port verbatim. e1 `_computing`/`_pending_render` guard flips semantics: now "worker in flight." Catch-up QTimer.singleShot(0) MOVES from dispatch finally into result-slot finally.
- Monotonic generation counter needed ON TOP of single-flight guard. Worker exceptions must be caught ON THE WORKER THREAD (catch_warnings + except ValueError/Exception in worker.run()). Removing processEvents() is AI-9-POSITIVE.
- WaitCursor must pair restoreOverrideCursor for EVERY exit including stale-result discard (inside try, not above it). AI-2: only pure pieces testable Qt-free.

## realtime-variety-render-e5 (2026-05-22) [MERGED]
- Math-lens job is transcription: confirm the kernel is term-by-term copy of NumPy expression. Test tolerance `rtol=atol=1e-9` (not 1e-12; float drift from fused-scalar vs broadcast). prange adds NO extra float error for pure-map kernels.
- `np.clip` inside kernel as per-voxel min/max: no temp array, folds clip into kernel. `cache=True` supported for `@njit(parallel=True)`. Thread oversubscription risk: Numba + VTK SMP — use workqueue + set_num_threads(~half).
- Roadmap dep pins can be STALE: verify against installed numpy. numba+llvmlite both BSD-2-Clause. Telemetry: `[render] <label>: <ms>` at app.py:636 via MeshResult.gen_ms — don't add new telemetry.

## enriques-hq-smoothing-2026q3-e1 (2026-05-22)
- Architecture decision IS the deliverable. Pattern-A storage; TRIGGERING differs: culling/wireframe → actor props only; HQ smoothing → mesh regen via _invalidate_clipped_mesh() + _render_current(). AI-8 blocks bool-as-float coercion directly.
- `hq_smoothing_changed = Signal(bool)` for proper decoupling. Two gating sites: _on_variety_changed (clear) AND _on_subtype_changed (enable/disable per eligible subtype). Hardcode n_iter=40 inside generator, not via slider.

## appearance-panel-layout-pass-2026q3-e2 (2026-05-22)
- Capture render-panel-chrome.py PNG first — alignment fracture visible immediately. QGroupBox grep gives current name in one search. macOS QSS footgun: role rule MUST include box-model property (padding/border/background) for text-align to fire.
- AI-11: setProperty("role", "string-value") is never an AI-11 concern. AI-2: use source-text grep tests with `count >= N` for multi-instance checks.

## realtime-variety-render-e2 (2026-05-22)
- Pre-implementation: check `git log --oneline --all | grep -i milestone-id` BEFORE research — state.json stuck at research-running can be a state management artifact.
- CAND-8/e2: `should_render_on_drag` must be a free function (AI-2). After e4, re-entrancy is _computing + _pending_render, NOT processEvents.

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
