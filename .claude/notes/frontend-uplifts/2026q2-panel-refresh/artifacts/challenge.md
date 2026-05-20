# Challenge — 2026q2-panel-refresh

**Date:** 2026-05-20
**Role:** CHALLENGER (Phase 3)
**Input:** synthesis.md (22 candidates, UPL-1 through UPL-22 + UPL-23)
**Adversarial lens:** feasibility, cost honesty, accessibility regression, app-invariant compatibility, anti-pattern detection, sequencing correctness

---

## 1. Executive Summary

Of the 22 synthesis candidates (UPL-1 through UPL-22 + UPL-23), **0 are BLOCKERs, 5 are MAJOR, 9 are MINOR, and 9 are NONE**. No candidate violates the hard AI-1/AI-3/AI-4 tripwires or proposes a GPL-3.0 library in a redistributable surface — the synthesis already pre-filtered the obvious landmines (PyQt-Fluent-Widgets, pymeshfix, trame) before the challenger pass. The two dominant cost-underestimation themes are: (1) **UPL-9 (KaTeX tooltip) carries a non-trivial startup-latency footgun** that the synthesis dismisses too quickly — `QWebEngineView` initialization is a cold-start cost that isn't "already paid" in the sense the library scout claims; and (2) **UPL-15 (QSettings persistence) and UPL-22 (parameter sweep) both have re-entrancy and signal-cascade risks** that the synthesis sketches around but doesn't cost honestly, making their "M" size estimates too optimistic. The Enriques mesh-quality pair (UPL-18/19) remains the highest-urgency candidates regardless of challenge findings — the CRITICAL visual artifact is real and render-evidenced.

---

## 2. BLOCKER Findings

None. Every candidate survives the AI-1/AI-3/AI-4/GPL gauntlet.

---

## 3. MAJOR Findings

### MAJOR — UPL-9 / KaTeX-rendered equation tooltip popover

**Candidate id:** UPL-9
**Title:** KaTeX-rendered equation tooltip popover
**Severity:** MAJOR

**Objections:**

- **Performance impact (Axis 5) — startup latency undercosted.** The synthesis asserts `QtWebEngineWidgets` is "zero marginal cost" because it's already in PySide6-Addons. This is true for disk footprint, but it is NOT true for process startup time. `QWebEngineView` spins up a Chromium sub-process (the QtWebEngine renderer process) on first instantiation. On macOS Apple Silicon (primary target) this cold-start is typically 300–600ms for the first `QWebEngineView()` call — NOT the ~10ms the synthesis implies for KaTeX rendering. If the popover's `QDialog` is lazily constructed on first hover, the user experiences a multi-hundred-millisecond freeze on first equation hover. If the dialog is eagerly constructed at `MainWindow.__init__()`, that latency is paid unconditionally at launch, increasing perceived startup time noticeably for a single feature.

- **macOS Qt+VTK GL offscreen segfault risk (Axis 4).** `QWebEngineView` requires its own OpenGL context. On macOS, mixing VTK's OpenGL context (in `QtInteractor`) with QtWebEngine's Chromium GPU process has historically produced GL context conflicts. The synthesis correctly notes AI-3 (no `MainWindow()` under offscreen), but the interaction between VTK's `QT_QPA_PLATFORM` setup and QtWebEngine's GPU process initialization on macOS is a known footgun with no explicit mitigant in the sketch. The library scout brief (§F) mentions this only in passing ("a live QWebEngineView; the rendering is in a Qt path that the existing test infrastructure already skips") — not a real risk analysis.

- **Cross-platform (Axis 7).** On Windows, `QWebEngineView` requires `QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts, True)` to be called BEFORE `QApplication(sys.argv)`. The `app.py:main()` already calls `QApplication.setAttribute(Qt.AA_ShareOpenGLContexts, True)` (line 425, AI-11 drift aside), but that call uses the unqualified enum — a cosmetic issue. The real concern is that the QtWebEngine renderer process on Windows requires the `chromium_child` subprocess to be findable on PATH; this fails silently under some virtualenv configurations, producing an empty white WebView with no error. The synthesis proposes no fallback.

- **Effort honesty (Axis 8).** The synthesis sizes this "M" (4–10 days). The actual scope: a new `equation_popover.py` module, a new `VARIETY_TOOLTIPS_TEX` dict populated with LaTeX strings for all 14 surfaces (this alone is ~1 day of math-authoring work to verify correctness), a `QTimer` hover dwell per combo, and GL context validation across three platforms. A more honest estimate is M+ (upper end of M, with a spike day before committing).

- **Anti-pattern (Axis 9) — INT-NO-2 adjacency.** The synthesis says "AI-2 (Qt-free tests) — the TeX-source dict is Qt-free and testable; the rendering is in a Qt path that the existing test infrastructure already skips." This is correct as a statement of current test scope, but the TeX-source accuracy (e.g., correct LaTeX for the Enriques canonical sextic degree-6 equation) has no test path at all unless the team writes pure-string tests, which the synthesis doesn't propose.

**Suggested scope adjustment:**
- **v0:** Allocate a spike day to benchmark `QWebEngineView()` cold-start on macOS Apple Silicon under the app's VTK GL context. If latency exceeds 200ms, adopt the fallback path: use `matplotlib.mathtext` (via Agg backend) to render equations to `QPixmap` and display as `QLabel` — no subprocess, no GL conflict. The synthesis correctly flags this as the lighter alternative.
- **v1 (if spike passes):** Build the KaTeX popover with a `QTimer`-gated lazy construction (delay the `QWebEngineView()` call until first hover dwell triggers, so launch is not penalized). Add a platform guard that falls back to the `matplotlib.mathtext` path on systems where the QtWebEngine subprocess fails to initialize. Document the 300-600ms first-hover cold-start as expected behavior.

---

### MAJOR — UPL-15 / QSettings cross-launch state persistence

**Candidate id:** UPL-15
**Title:** QSettings cross-launch state persistence
**Severity:** MAJOR

**Objections:**

- **Re-entrancy / threading discipline (Axis 6).** The synthesis sketch says: "AI-9 (re-entrancy) — the restore flow must set `_computing = True` so the cascade of variety/subtype/param signals doesn't re-render N times." This is the right instinct but the execution is underspecified and risky. The problem: `restore_state(window)` calls `window.variety_combo.setCurrentText(last_variety)` → `_on_variety_changed` fires → rebuilds the subtype combo → `_on_subtype_changed` fires → `_render_current` fires. This is the normal cascade. If `_computing = True` is set before this cascade, `_render_current` returns immediately (re-entrancy guard). Then who triggers the final render? The restore logic must manually call `_render_current(reset_camera=True)` AFTER clearing `_computing`. Getting this wrong either produces no render on restore (silent failure) or causes double-render (wasted ~0.5s on launch). Neither is handled in the sketch.

- **Effort honesty (Axis 8).** The synthesis sizes this "M." The actual scope includes: QSettings namespace design and schema versioning (the sketch correctly raises this — "varietyviewer/2026q2/v1" is the right answer, but migration from schema v0 adds a day); per-subtype param dict serialization and deserialization (JSON dict keyed by `(variety, subtype)` tuple — tuples aren't JSON keys, needs a repr or stringify); dock geometry save/restore (`QMainWindow.saveState()`/`restoreState()` is one call, but the dock's floating/locked state on different screen configs needs a guard for when the saved geometry doesn't fit the current display); the "Restored last session" status-bar confirmation with a 3-second fade. A thorough M (upper end) is accurate; the sketch makes it sound like a tight M.

- **App-invariant compatibility (Axis 1) — AI-8 adjacency.** The restore flow sets variety + subtype + param values. If the persisted subtype key no longer exists in `VARIETIES` (e.g., a variety was renamed between sessions), the restore silently fails. The sketch says "on schema mismatch, fall back to defaults silently" but the mismatch check is only for schema version, not for key existence. The real guard needed is: `if last_variety not in VARIETIES or last_model not in VARIETIES[last_variety]: skip restore`. Missing this produces a `KeyError` on the next launch after any variety rename.

- **Sequencing dependency (Axis 10).** The synthesis correctly identifies UPL-15 as a dependency for UPL-8 (collapse state) and UPL-4 (dark-mode toggle). However, UPL-15's param-values key structure assumes `ParamSpec.name` values are stable across sessions. If UPL-7 (spin-box companion) renames a `ParamSpec.name` value, persisted param values silently get dropped. The synthesis doesn't flag this cross-candidate coupling risk.

**Suggested scope adjustment:**
- **v0:** Persist only `(last_variety, last_model, dock_geometry)` — no param values. This removes the JSON serialization complexity, the schema migration concern, and the per-subtype dict entirely. The user gets variety/model restoration with a single launch. Param values default to their spec defaults.
- **v1:** Add per-subtype param dict once the param structure is stable (i.e., after UPL-7 lands and any name changes are settled). Add schema migration when the structure changes.

---

### MAJOR — UPL-22 / Parameter sweep play button

**Candidate id:** UPL-22
**Title:** Parameter sweep play button (single slider sweep at v1)
**Severity:** MAJOR

**Objections:**

- **Re-entrancy / threading discipline (Axis 6).** The synthesis sketch: "AI-9 (re-entrancy) — each sweep step must check `_computing`; if `True`, skip the step (don't queue)." Skipping steps silently is not a safe sweep policy: if the marching-cubes step for each keyframe takes ~500ms and the QTimer interval is also ~500ms, the `_computing` guard will skip roughly half the keyframes unpredictably. The user sees a stutter-sweep rather than a smooth progression. The synthesis doesn't propose a skip strategy (e.g., dropping to the next unrendered keyframe), only "skip the step." A production sweep needs a "render-complete callback → advance keyframe" pattern, not a fire-and-forget timer.

- **Re-entrancy / threading discipline (Axis 6), second issue.** Each sweep step calls the render path, which calls `QApplication.processEvents()`. Under AI-9, any UI event that fires during `processEvents()` (e.g., the user clicking another slider) can re-enter `_render_current`. The synthesis guard "if `_computing`: skip" protects `_render_current` itself but does NOT prevent the sweep QTimer from firing a new step while the previous step's `processEvents()` is still draining. The timer step and the `processEvents()` re-entrant path can interleave unexpectedly unless the timer is paused during each render step.

- **Anti-pattern check (Axis 9).** The synthesis checks INT-NO-1 (real-time render during drag): "the sweep is discrete keyframes, not continuous slider drag." Technically correct — but if the timer interval is shorter than the render time, the effective behavior IS real-time continuous rendering from the user's perspective. The synthesis doesn't specify the minimum inter-frame interval or how it relates to the render budget. INT-NO-1 says `valueChanged` (every tick) is forbidden; a 50ms QTimer is functionally equivalent for the marching-cubes pipeline (~500ms per render).

- **Effort honesty (Axis 8).** Synthesis sizes this "M." The real scope, accounting for the re-entrancy issues above, is M to M+ (could easily become a week of hardening if the timer/re-entrancy interaction is fought through robustly). The "add a QTimer" sketch is misleading — a production-quality sweep needs an explicit state machine (IDLE → SWEEPING → step-done → next-step / ABORTED).

- **Sequencing dependency (Axis 10).** UPL-22 depends on UPL-7 (spin-box companion) landing first so the sweep endpoint can be the spinbox's value, not just the slider's tick. Without UPL-7, the sweep can only target tick-resolution values, not exact ones. The synthesis doesn't call this out.

**Suggested scope adjustment:**
- **v0:** One play button per slider that fires a single `QTimer.singleShot` chain: render step N → on completion (via a callback or signal), advance to step N+1. Each step checks `_computing` before firing. Pause the sweep automatically if the user touches any other slider. Minimum inter-frame interval = max(user-speed-setting, last_render_time + 50ms). No global speed control in v0.
- **v1:** Global speed control. Sweep-abort on any UI event outside the sweep button itself.

---

### MAJOR — UPL-18 / Enriques sextic: mitigate sawtooth tears (resolution + Taubin)

**Candidate id:** UPL-18
**Title:** Enriques sextic: mitigate sawtooth tears (resolution + Taubin)
**Severity:** MAJOR

**Objections:**

- **Performance impact (Axis 5).** The synthesis correctly says "target render time stays ≤500ms per AI-imposed budget" but underestimates the cost of adaptive resolution. Sub-option (a) — "increase the grid step from `0.04` to `0.025` near the singular locus via an adaptive sampler" — requires implementing adaptive grid sampling, which does not exist in the codebase today (`_marching_cubes_to_polydata` takes a uniform grid step). An adaptive sampler is a multi-day implementation in itself, separate from the smoothing fix. The synthesis bundles these as equal-effort alternatives ("spike both (a) and (b)") but they are not equal: (b) (second Taubin pass) is a 2-line change; (a) (adaptive sampling) is a 3–5 day implementation. This effort gap needs surfacing before Phase 4 RICE scoring.

- **Performance impact (Axis 5), second concern.** Sub-option (a) with a uniform resolution increase from `0.04` to `0.025` (not adaptive) roughly triples the vertex count (3^3 = 27× for 3D uniform refinement on a factor-of-1.6 step reduction), pushing render time for the Enriques sextic from ~500ms to potentially 2–4 seconds. The synthesis doesn't quantify this and treats the spike as a formality rather than a gate. For Phase 4 RICE scoring, "CRITICAL fix that might make render time 5× worse" has very different impact than "CRITICAL fix with negligible render overhead."

- **App-invariant compatibility (Axis 1) — AI-6 note.** The synthesis correctly notes "AI-6 (implicit pipeline correctness) — neither option changes the implicit field, only the post-extraction smoothing." This is accurate. No violation.

- **Effort honesty (Axis 8).** The synthesis sizes this "M." This is correct for sub-option (b) (second Taubin pass) alone. Sub-option (a) with adaptive sampling is more like L (>10 days). The synthesis must commit to one before Phase 4 can score it accurately. Recommend: size the candidate around sub-option (b) only, treat (a) as a v2.

**Suggested scope adjustment:**
- **v0 (ship fast):** Second Taubin pass (`smooth_taubin(n_iter=40, pass_band=0.05)`) on the Enriques sextic only, gated by a surface-type check. ~2-line change. Also add `bounds * 1.05` padding to the Enriques sampling box (GAP-H2 from the visual scout) to eliminate perimeter serration — another 1-line change. Together these address both visual complaints without adaptive sampling.
- **v1 (if v0 insufficient):** Uniform resolution increase (measure render time impact first). Adaptive sampling only if uniform increase is too slow.

---

### MAJOR — UPL-8 / Collapsible group boxes in Appearance + View docks

**Candidate id:** UPL-8
**Title:** Collapsible group boxes in Appearance + View docks
**Severity:** MAJOR

**Objections:**

- **Accessibility regression risk (Axis 3).** `superqt.QCollapsible` uses a disclosure-arrow header as the collapse trigger. The APP_STYLESHEET focus ring (`outline: 2px solid #5b9bd5` on `QAbstractButton:focus`) applies to `QAbstractButton`, but `QCollapsible`'s disclosure arrow may not be a `QAbstractButton` subclass — it's a `QToolButton` (confirmed from superqt source). The `QSS` rule `QAbstractButton:focus` covers `QToolButton` (it is a subclass), so the focus ring should apply. However, `QCollapsible` also installs its own header stylesheet internally, which may override the focus ring if it sets a conflicting `outline`. The synthesis says "verify focus-ring visibility on the disclosure arrow after adoption" but doesn't make this a v0 acceptance criterion. Until verified, this is a real AI-12 / WCAG AA regression risk: keyboard users navigating with Tab would lose the focus ring on the collapse control.

- **Accessibility regression risk (Axis 3), second concern.** When sections are collapsed, their child widgets become invisible to the layout. Screen readers (VoiceOver, Qt accessibility API) may not correctly report the collapsed state to assistive technology, potentially confusing keyboard-only users who Tab through the panel and skip large sections silently. The synthesis doesn't mention screen-reader behavior at all.

- **Sequencing dependency (Axis 10).** The synthesis notes UPL-8 depends on UPL-2 (dep landing). That dependency is correct and explicit. But there's an additional implicit dependency: UPL-8 replaces `QGroupBox` with `QCollapsible`, which has a different title styling API. UPL-1 (palette token refactor) adds token-based colors to `APP_STYLESHEET`; those tokens may not automatically flow into `QCollapsible`'s internal header widget because `QCollapsible` renders its header with its own QSS injection. If UPL-1 lands before UPL-8, the UPL-8 implementation must re-verify that palette tokens flow through correctly — an extra integration step the synthesis doesn't surface.

- **Effort honesty (Axis 8).** Synthesis sizes this "S." The widget-swap is S; the accessibility verification (focus ring on disclosure arrow, screen-reader collapse-state announcement, keyboard Tab-order through collapsed sections) is an additional day of testing. Total is M-low, not S. The synthesis sizes it as purely mechanical.

**Suggested scope adjustment:**
- **v0:** Replace `QGroupBox` with `QCollapsible` in Appearance dock only (4 groups). Write a manual accessibility checklist: (a) Tab-navigate to a disclosure arrow, (b) press Space/Enter, (c) verify section collapses, (d) verify focus ring remains visible, (e) verify Tab continues to the next visible control. Only ship if checklist passes.
- **v1:** Apply to View dock. Add persistence via UPL-15 (if landed).

---

## 4. MINOR Findings

### MINOR — UPL-2 / Adopt `superqt` + `qtawesome` as panel-modernization dep base

**Candidate id:** UPL-2
**Title:** Adopt `superqt` + `qtawesome` as panel-modernization dep base
**Severity:** MINOR

**Objections:**

- **Performance impact (Axis 5).** The synthesis documents the `qtawesome` cold-boot icon-font caching cost as "~150–200ms one-time per launch." This is accurate for the font parse step. However, `qtawesome` also lazily initializes `qtpy`'s backend detection on first import — if `qtpy` hasn't cached the Qt-binding selection yet (first run in a new `.venv`), this can add another 50–100ms. Not a blocker, but it should be logged in CONTEXT.md §8 as documented startup overhead, not just in CONTEXT.md §3.

- **Effort honesty (Axis 8).** Synthesis sizes this "S." Correct — this is purely a `requirements.txt` + `CONTEXT.md` edit with no code changes. No objection to the size.

**Suggested scope adjustment:** Add a note to CONTEXT.md §8 (not just §3) quantifying the measured cold-boot cost on the primary hardware (Apple Silicon). This ensures the next developer doesn't accidentally add another `qtawesome`-dependent candidate that stacks cold-boot costs unexpectedly.

---

### MINOR — UPL-4 / Dark-mode toggle + parallel `STYLESHEET_DARK`

**Candidate id:** UPL-4
**Title:** Dark-mode toggle + parallel `STYLESHEET_DARK`
**Severity:** MINOR

**Objections:**

- **Accessibility regression risk (Axis 3).** The synthesis proposes new dark palette tokens: `BG_PANEL_DARK = "#2a2f3d"`, `TEXT_VALUE_DARK = "#dde3ee"`. The stated contrast check is "`TEXT_VALUE_DARK` on `BG_PANEL_DARK`" — `#dde3ee` on `#2a2f3d` computes to approximately 8.1:1 (passes AA). However, the synthesis does not check the dark equivalent of `COLOR_MUTED` (`#5a5a5a` on light — 5.4:1 on `#f0f0f0`). On the dark panel background `#2a2f3d`, the existing `COLOR_MUTED = #5a5a5a` has a contrast ratio of approximately 2.9:1 — an AA **fail** for small text. The synthesis must specify a `COLOR_MUTED_DARK` token (e.g., `#9aabb8`, which gives ~4.7:1 on `#2a2f3d`) and ensure all uses of `COLOR_MUTED` in the dark stylesheet substitute it.

- **Sequencing dependency (Axis 10).** UPL-4 depends on UPL-1 (palette tokens) and UPL-3 (background init fix). The synthesis calls this out correctly. The additional MINOR concern: the `STYLESHEET_DARK` toggle writes `plotter.set_background(BG_VIEWPORT_DARK)` synchronously. If `_computing` is `True` at that moment (a slow mesh is generating), the background changes in the live plotter mid-render, potentially producing a flash. The toggle handler should check `_computing` and defer the plotter background change to the next render cycle if `_computing` is active.

**Suggested scope adjustment:** Before shipping UPL-4, add `COLOR_MUTED_DARK` to the dark token set and verify all muted-text surfaces in the dark theme pass ≥4.5:1.

---

### MINOR — UPL-5 / Per-variety default surface color

**Candidate id:** UPL-5
**Title:** Per-variety default surface color
**Severity:** MINOR

**Objections:**

- **Accessibility regression risk (Axis 3) — AI-12.** The synthesis proposes the following tokens and claims "all verified for ≥3:1 luminance contrast against `BG_VIEWPORT_DARK = #1e222e`": `#8ab4d4` (K3), `#c8a880` (Enriques), `#4a90d9` (CY3), `#7ec8a0` (Fano). Verifying:
  - `#8ab4d4` on `#1e222e`: relative luminance L1=0.444, L2=0.016 → ratio ≈ **9.9:1** — pass.
  - `#c8a880` on `#1e222e`: L1=0.376, L2=0.016 → ratio ≈ **8.5:1** — pass.
  - `#4a90d9` on `#1e222e`: L1=0.256, L2=0.016 → ratio ≈ **5.9:1** — pass.
  - `#7ec8a0` on `#1e222e`: L1=0.461, L2=0.016 → ratio ≈ **10.4:1** — pass.
  All four pass the ≥3:1 large-surface threshold. The AI-12 claim is correct. However, **surface color is not text** — WCAG AA's 3:1 rule applies to large UI elements (>18pt text or 24×24px icons) not to rendered mesh surfaces against a 3D viewport background. The synthesis is applying the wrong WCAG rule. The correct standard for surface readability is subjective (sufficient luminance contrast for depth perception), and the four proposed tokens are visually adequate. No violation, but the synthesis's WCAG framing is inaccurate.

- **Effort honesty (Axis 8).** The synthesis sizes this "S" (~1 day). The sketch requires adding `set_default_color(hex: str)` to `AppearancePanel`, wiring `_on_variety_changed` (or `_on_subtype_changed`) to call it, and populating a dict. This is genuinely S. No cost objection.

**Suggested scope adjustment:** Remove the WCAG framing from the implementation notes (surface color is not text contrast), but verify the four tokens visually against the light background too (for users who haven't enabled UPL-4 dark mode).

---

### MINOR — UPL-6 / Named color-map preset menu in Appearance dock

**Candidate id:** UPL-6
**Title:** Named color-map preset menu in Appearance dock
**Severity:** MINOR

**Objections:**

- **Performance impact (Axis 5).** The synthesis says "Computing the scalar at render time (`mesh.compute_normals(); mesh["Mean_Curvature"] = mesh.curvature()`) costs ~50–100ms per surface — within AI-12 / INT-2 latency budget." `mesh.curvature()` is not free: for the Enriques sextic (~400k verts) it runs a VTK curvature filter that computes per-vertex mean or Gaussian curvature. On Apple Silicon this typically takes 150–300ms for dense meshes, not 50–100ms. For the Hanson quintic (25 patches, ~50k verts), it is faster (~20–50ms). The synthesis's latency estimate may be accurate for the Hanson family but not for the Enriques family at high grid resolution (especially after UPL-18 increases resolution). This adds to the already-~500ms render pipeline.

- **Anti-pattern check (Axis 9).** The sketch says `add_mesh(..., scalars="Mean_Curvature", cmap=preset, ...)` — the `scalars=` kwarg is correctly used (AI-5 preserved). However, the synthesis doesn't address the interaction with the existing `appearance_panel.apply_to_actor` path. Today `apply_to_actor` sets `actor.GetProperty().SetColor(r, g, b)` after `add_mesh`. If the colormap path is active, calling `apply_to_actor` afterward would overwrite the colormap with a flat color. The synthesis says "mutual-exclusive UI in appearance_panel.py" but the `apply_to_actor` method itself must also branch on `_color_mode` — otherwise every opacity or shading change will accidentally flatten the colormap. This interaction between color mode and the existing apply path is a MINOR implementation footgun the synthesis doesn't resolve.

**Suggested scope adjustment:** Before implementing, define the clear contract: in colormap mode, `apply_to_actor` does NOT call `actor.GetProperty().SetColor(...)`. Add `_color_mode: Literal["flat", "cmap"]` as an explicit branch guard in `apply_to_actor`.

---

### MINOR — UPL-7 / Spin-box companion alongside parameter sliders

**Candidate id:** UPL-7
**Title:** Spin-box companion alongside parameter sliders
**Severity:** MINOR

**Objections:**

- **App-invariant compatibility (Axis 1) — AI-9 adjacency.** The synthesis sketch says "the existing `_computing` guard covers it." But the spinbox introduces a new emit path: `spinbox.editingFinished → slider.setValue(...) → slider.valueChanged → _on_value_changed → [live update label]`. The `slider.setValue(...)` call from the spinbox does NOT emit `sliderReleased`, only `valueChanged`. If the spinbox sync path emits `params_changed` directly (as the synthesis proposes), and if `params_changed` is wired to `_render_current`, then the spinbox path bypasses the `sliderReleased` throttle. The synthesis acknowledges this should use `editingFinished → same render path` but the exact signal wiring needs care to avoid accidentally wiring `valueChanged` (which fires on slider.setValue too) as the render trigger. Implementation needs: `spinbox.editingFinished` → call `_on_slider_released()` directly (or emit `params_changed`); `slider.setValue(...)` from spinbox sync must `blockSignals(True)` during the setValue call to avoid double-emit.

- **Effort honesty (Axis 8).** Synthesis proposes using `superqt.QLabeledDoubleSlider` as implementation (B). This is genuinely S for that path. However, if `QLabeledDoubleSlider` doesn't support the exact ParamSpec step/range/tick semantics that the existing custom slider uses (e.g., the `value_to_tick` / `tick_to_value` mapping for non-integer ranges), the team may need to fall back to implementation (A) (hand-rolled), which is closer to M-low. The synthesis should make the dep on superqt's API contract explicit.

**Suggested scope adjustment:** Spike `QLabeledDoubleSlider` against one slider row before committing to (B). Verify it supports float step with the existing ParamSpec range and correctly emits on edit-complete (not on every keypress).

---

### MINOR — UPL-9 sequencing note (already MAJOR above; this note is separate)

*(See MAJOR finding for UPL-9.)*

---

### MINOR — UPL-11 / First-launch viewport hint overlay

**Candidate id:** UPL-11
**Title:** First-launch viewport hint overlay
**Severity:** MINOR

**Objections:**

- **Accessibility regression risk (Axis 3).** The synthesis proposes a `QLabel` with `setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)`. This is the correct mouse-event suppression. However, the label is a child widget overlaid on the `QtInteractor` viewport. On macOS, the VTK render window sits inside a native OS window handle; overlaying a Qt widget on top of a native window child is a z-order hazard — the label may render BEHIND the VTK window rather than in front of it, making it invisible. The synthesis doesn't address this platform-specific z-order risk. Verifying this on macOS Apple Silicon is a v0 acceptance criterion.

- **AI-12 check.** The synthesis says "confirm contrast on both `BG_VIEWPORT` and `BG_VIEWPORT_DARK`." `TEXT_MUTED` / `COLOR_MUTED = #5a5a5a` on `BG_VIEWPORT = #2f2f2f` gives approximately 2.5:1 — an AI-12 / WCAG AA **fail** for small text (14px as proposed). The synthesis specifies "Text color = palette `TEXT_MUTED`" — this will fail the AI-12 check. A lighter muted color is needed for the dark viewport (e.g., `#9aabb8` gives ~4.7:1 on `#2f2f2f`). This is not a BLOCKER but it's a concrete violation of AI-12 that the synthesis missed.

**Suggested scope adjustment:** Use a viewport-specific hint color (e.g., `#9aabb8` or similar ≥4.5:1 on `#2f2f2f`) rather than `COLOR_MUTED`. Add a macOS z-order test (manual, since AI-2 forbids Qt tests) before merging.

---

### MINOR — UPL-17 / Iconic camera presets + reset-with-margin

**Candidate id:** UPL-17
**Title:** Iconic camera presets + reset-with-margin
**Severity:** MINOR

**Objections:**

- **Effort honesty (Axis 8) — Hanson preset specifically.** The synthesis says "exact angles from Hanson's published Mathematica notebook; values TBD via spike." This is honest, but the spike cost is non-trivial: Hanson's 1994 paper gives camera angles in terms of the projection parameter α, not VTK azimuth/elevation/roll. Mapping the iconic (α=π/4) Mathematica projection to a VTK camera pose requires an alignment step that may take a day of iterative visual verification. The synthesis sizes this "XS" — appropriate for the `reset_camera(bounds=...)` margin fix, but the Hanson iconic preset alone is more like S.

**Suggested scope adjustment:** Split into two XS sub-candidates: (a) reset-camera margin (`bounds * 1.05`) — XS, ship first; (b) Hanson iconic preset — S, requires a spike.

---

### MINOR — UPL-19 / Enriques sextic: back-face culling toggle

**Candidate id:** UPL-19
**Title:** Enriques sextic: back-face culling toggle in Appearance dock
**Severity:** MINOR

**Objections:**

- **App-invariant compatibility (Axis 1) — interaction with `apply_to_actor`.** The synthesis proposes passing `backface_culling=True` to `plotter.add_mesh()`. However, `apply_to_actor` currently calls PyVista actor-property setters (`actor.GetProperty().SetOpacity(...)`, `actor.GetProperty().SetRepresentationToWireframe()`). In PyVista, `backface_culling` is an `add_mesh` argument that sets `actor.GetProperty().BackfaceCullingOn()` during construction. If `apply_to_actor` later resets the actor properties via `SetColor` or `SetRepresentation`, it does NOT reset `BackfaceCullingOn` — so the backface culling state persists through appearance changes correctly. This is fine. However, Option (b) — a user-toggleable checkbox — would need to call `actor.GetProperty().BackfaceCullingOn()` / `BackfaceCullingOff()` directly through `apply_to_actor`, which is an undocumented PyVista property access. Verify the PyVista API supports this call path before wiring the toggle.

**Suggested scope adjustment:** Ship Option (a) first (per-surface `recommends_backface_culling` flag in `surfaces.py`, applied at `add_mesh` time). Option (b) (user toggle) is v1. The per-surface flag approach is 5 lines and the only risk is AI-8 extension (`Surface` dataclass gains a new field — confirm `frozen=True` allows default field addition).

---

### MINOR — UPL-20 / HiDPI workaround baked into `app.py:main()`

**Candidate id:** UPL-20
**Title:** HiDPI workaround baked into `app.py:main()`
**Severity:** MINOR

**Objections:**

- **Cross-platform (Axis 7).** The synthesis says "Recommend `setHighDpiScaleFactorRoundingPolicy` — more idiomatic in PySide6 6.6+." Correct. However, `setHighDpiScaleFactorRoundingPolicy` must be called BEFORE `QApplication(sys.argv)` is instantiated. The synthesis sketch says "add `os.environ.setdefault(...)` before `QApplication(sys.argv)` in `main()`" for one option and "call `QApplication.setHighDpiScaleFactorRoundingPolicy`" for the other — but `setHighDpiScaleFactorRoundingPolicy` is a static method that CAN be called before QApplication is constructed in PySide6 (unlike in PyQt5 where you needed a QCoreApplication first). Confirm this is valid before implementing. If it works, it's cleaner than env var injection.

- **Cross-platform (Axis 7), second concern.** The env var `QT_AUTO_SCREEN_SCALE_FACTOR=1` has different effects on Linux (X11 vs Wayland) — on Wayland it can cause double-scaling. If Windows and Linux CI are ever added, this one-liner could cause regressions on non-macOS. The `setHighDpiScaleFactorRoundingPolicy(PassThrough)` call is safer across platforms.

**Suggested scope adjustment:** Use `setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)` before the `QApplication(sys.argv)` call. Remove the README workaround paragraph once this lands.

---

### MINOR — UPL-21 / AI-11 + AI-13 cleanup sweep

**Candidate id:** UPL-21
**Title:** AI-11 + AI-13 cleanup sweep
**Severity:** MINOR

**Objections:**

- **Effort honesty (Axis 8).** The synthesis says "Two `Edit` calls." Correct — this is genuinely XS. No cost objection.
- **AI-11 scope.** The current-state critic confirms these are the only two violations in the codebase. The synthesis and the critic agree. The fix is straightforward. MINOR only because the synthesis labels the `#888` in `appearance_panel.py:48` as "AI-13 adjacency" — it's technically a Qt stylesheet string, not a PyVista color argument, so it's not strictly an AI-13 violation. The CONTEXT.md §8.3 explicitly says "AI-13 adjacency" for Qt stylesheet hex. The synthesis inherits this framing correctly. No violation; cosmetic inconsistency only.

**No scope adjustment needed.** Ship as stated.

---

## 5. Clean Candidates

The following candidates survive the gauntlet with no significant objections:

- **UPL-1** — Refactor `styles.py` into named palette tokens: clean. The scope is well-defined, the risk is localized to `styles.py`, and it unblocks downstream candidates as stated.
- **UPL-3** — Initialize plotter background in `MainWindow.__init__`: clean. Two-line fix with well-understood scope. The implementation note (use the existing `#2f2f2f` literal if UPL-1 hasn't landed yet) is correct.
- **UPL-10** — Help menu with About + Keyboard Shortcuts + Citations: clean. ~30 lines, no AI conflicts, `qtawesome` dep is covered by UPL-2. AI-11 note in the sketch (use `QKeySequence.StandardKey` for cross-platform shortcuts) is the right call.
- **UPL-12** — Persistent surface-warning badge: clean. ~5-line patch. The scope is precisely described. No re-entrancy concern (no new `processEvents` call).
- **UPL-13** — Status-bar mesh-extent + bounding-box readout: clean. ~3-line patch. Hover readout correctly deferred to v2. No performance concern for the bbox-only version.
- **UPL-14** — Mesh export (STL / OBJ / PLY): clean. The `get_mesh` callback pattern mirrors `get_actor`. `mesh.save()` is PyVista native (no new dep needed for v1). The `meshio` deferral is correct.
- **UPL-16** — Three-point lighting rig: clean. `plotter.add_light()` / `plotter.remove_lights()` at `MainWindow.__init__()` is the right scope. `ambient=0.2` in `add_mesh` is a straightforward addition. No re-entrancy risk.
- **UPL-23** — Widen pyvista pin to `<0.50`: clean. One-character edit. Correctly scoped as forward-compatibility insurance, not a current upgrade.

---

## 6. Cross-Cutting Concerns

### 6.1 Five candidates assume `superqt` / `qtawesome` are already deps

UPL-7, UPL-8, UPL-10, UPL-14 (icon only), and UPL-16 (icon only) all reference `qtawesome` icons or `superqt` widgets. The synthesis correctly designates UPL-2 as the foundational dep candidate that must land first. **Risk:** if UPL-2 is deprioritized or split from the others in Phase 4, the five dependent candidates carry a hidden dep cost. Phase 4 MUST treat UPL-2 as a strict prerequisite for these five and factor its one-time cold-boot cost into the combined startup overhead.

### 6.2 AI-12 (WCAG AA) verification is underspecified across three candidates

UPL-4 (dark-mode `COLOR_MUTED` equivalent), UPL-5 (surface color WCAG framing error), and UPL-11 (overlay label on dark viewport) all have AI-12 concerns. The synthesis asserts "AI-12 preserved" or "verify ≥4.5:1" without providing the actual computed ratios or nominating who runs the verification. The pattern across these three candidates: the synthesis checks the primary token but misses the secondary (muted-text-on-dark) case. **Recommendation:** Phase 4 should require that every new dark-palette token includes a computed contrast ratio in the PR description before merge.

### 6.3 QSettings namespace must be stable before UPL-15 lands

UPL-15 proposes `"varietyviewer/2026q2/v1"` as the QSettings namespace. Any rename of a variety in `VARIETIES` (e.g., "Fano 3-fold (ρ=1)" shortened for display) or any `ParamSpec.name` change from UPL-7 will silently break persisted state. If UPL-7 lands after UPL-15, the persisted param dict becomes stale without warning. **Recommendation:** UPL-15's v0 (variety/model only, no param values) must land BEFORE or SIMULTANEOUSLY with UPL-7, and the v1 (param values) must land AFTER UPL-7's param names are frozen.

### 6.4 Enriques mesh quality candidates (UPL-18 + UPL-19) should be spiked together

The synthesis correctly proposes spiking both in parallel. The challenge reinforces: UPL-19 (backface culling) is a 5-line change that can be verified in one session; UPL-18 (Taubin/resolution) requires a render-time benchmark. **Recommendation:** merge UPL-19 first (no risk, immediate improvement) while the UPL-18 spike runs. Don't gate UPL-19 on UPL-18's outcome.

### 6.5 UPL-22 (parameter sweep) is the highest re-entrancy risk candidate in the catalog

The existing re-entrancy guard (`self._computing`) was designed for a single render triggered by a user gesture. UPL-22 converts `_render_current` into a repeated call from an automated timer — a fundamentally different use pattern. The `_computing` guard behavior (early return if already computing) was never designed to handle a sweep queue. **Recommendation:** UPL-22 should be the LAST candidate to land, after UPL-7 (spinbox) and UPL-15 (state persistence) have stabilized the render pipeline. A sweep on top of unstable state persistence or spinbox wiring is hard to debug.

---

## 7. Recommended Kill List

No candidates are recommended for outright kill before Phase 4 prioritization. The MAJOR findings for UPL-9, UPL-15, UPL-22, UPL-18, and UPL-8 are scope-adjustment recommendations, not kill recommendations. All 22 candidates are viable with the adjustments noted above.

The one candidate the challenger flags for **deprioritization** (not kill) in Phase 4:

- **UPL-22 (parameter sweep)** — the re-entrancy complexity is real, the effort is M+ with a non-trivial state-machine requirement, and the dependencies (UPL-7 spinbox, stable render pipeline) mean it should not be attempted until all foundational and S-sized candidates have landed. Phase 4 RICE scoring should reflect a low Confidence multiplier.

---

*Challenge written by CHALLENGER agent. All objections are anchored to specific synthesis claims, source code locations (file:line), or documented app invariants (AI-1..AI-15). No objections are manufactured to pad severity counts.*
