# Adversary critique — render-busy-spinner-2026q3-e1

**Reviewer:** milestone-adversary-critic (read-only) | **Date:** 2026-05-22 | **Subject:** `0f95e67..fba9851` — status-bar render-busy spinner; CONTEXT.md §9 deferral closed

> **Format reference**: `.claude/references/critique-format.md` (severity rubric, per-finding template).

---

## Executive summary

The most significant automated finding is the diff-size HIGH (1,517 lines total; see breakdown below — ~405 LOC functional, ~515 LOC artifact inflation). No CRITICALs. One MEDIUM: two load-bearing implementation gotchas (QPushButton-not-QLabel, addPermanentWidget-not-addWidget) are correctly documented in CONTEXT.md §9 and the factory docstring but absent from §8, which is the first place future adversary agents and maintainers scan for pattern-gotchas. Three LOWs: the QMovie regression guard covers `icons.py` only and not `app.py`; `Spin` QTimer accumulation on theme changes during an active compute is benign-but-undocumented; the 500-char adjacency threshold in tests 4–5 is loose enough to tolerate ~3 lines of inserted comments. One process HIGH (non-waivable); one MEDIUM (documentation discipline); three LOWs (belt-and-suspenders). Safe to merge after the MEDIUM rectifies.

---

## Critical findings

None.

---

## High findings

### HIGH — Diff size exceeds 400-LOC review-quality threshold

**Where:** no specific file (cross-cutting)
**Evidence:** `git diff 0f95e67..fba9851 | wc -l` = 1,517. Breakdown by file: `tests/test_render_busy_spinner.py` +250 LOC, `icons.py` +88 LOC, `app.py` +63 LOC, `CONTEXT.md` +4 LOC (functional total ~405 LOC); artifact inflation: `research/agent-solo-brief.md` +592, `agent-memory/milestone-researcher/lessons.md` net −170/+91, `artifacts/implementation-plan.md` +41, `state.json` +50, `dispatch.log` +2 (~515 LOC artifacts). Functional code is well under 200 LOC; artifact files drive the overage.
**Why it matters:** Cisco / LinearB defect-detection research documents degraded review quality above 400 LOC. This finding is non-waivable per checklist policy regardless of root cause.
**Suggested fix:** No code action required. Artifact inflation (research brief, memory compaction, state.json, dispatch log) is the dominant driver. The functional code delta (~155 LOC production + 250 LOC tests) is correctly sized for this feature.
**Regression-guard test:** Not applicable; finding is a process control, not a code defect.

---

## Medium findings

### MEDIUM — Two load-bearing QPushButton/addPermanentWidget gotchas absent from §8

**Where:** `CONTEXT.md` (section 8)
**Evidence:** CONTEXT.md §8 ends at §8.18 ("Worker-result slot: the stale-result discard must run inside the `try`"). The two load-bearing implementation gotchas introduced by this milestone — (1) `QPushButton` required instead of `QLabel` for qtawesome animation (see `icons.py:352-358`), and (2) `addPermanentWidget` required instead of `addWidget` to avoid `showMessage()` obscuring the spinner (see `app.py:162`) — are correctly documented in CONTEXT.md §9's shipped paragraph and in the factory docstring, but have no §8.N entry. §8.15 ("QCheckBox + setIcon() creates a triple-prefix affordance") establishes the precedent that Qt-widget-choice gotchas of this type belong in §8.
**Why it matters:** Future adversary agents and maintainers scan §8 first when debugging "the spinner animation died" or "the spinner disappears during compute." Absence from §8 increases the probability that a future refactor reverts to `QLabel` or `addWidget` without understanding the consequence.
**Suggested fix:** Add §8.19 with two sub-bullets: (a) "qtawesome Spin animation requires QPushButton, not QLabel — QLabel uses setPixmap() which captures a static frame; only QAbstractButton.paintEvent() calls QIcon.paint() which triggers Spin.setup()"; (b) "addPermanentWidget required for status-bar spinner — addWidget slots are obscured by showMessage() which fires at every render event; addPermanentWidget is never obscured per Qt 6 docs."

---

## Low findings

### LOW — QMovie regression guard covers icons.py only; app.py is unguarded

**Where:** `tests/test_render_busy_spinner.py:86-93`
**Evidence:** `test_app_render_busy_spinner_uses_qtawesome_spin_animation` asserts `"from PySide6.QtGui import QMovie" not in _ICONS_SRC` and `"QMovie(" not in _ICONS_SRC`. Both checks apply only to `_ICONS_SRC` (icons.py). `_APP_SRC` (app.py) has no analogous guard. A future commit adding a `QMovie`-based spinner to `app.py` imports would not be caught by any test.
**Why it matters:** The original AI-9 deferral rationale was specifically about `QMovie.updated` signals. The guard exists precisely to deter reintroduction of that pattern. Guarding only the factory file and not the main application file is an incomplete fence.
**Suggested fix:** Add two analogous assertions against `_APP_SRC` in `test_app_render_busy_spinner_uses_qtawesome_spin_animation`: `assert "QMovie(" not in _APP_SRC` and `assert "from PySide6.QtGui import QMovie" not in _APP_SRC`.

### LOW — Spin QTimer accumulation on repeated theme changes is undocumented

**Where:** `icons.py:368-373` (the `render_busy_spinner_icon` factory) and `app.py:1110-1112`, `app.py:1158-1159` (theme-change callers)
**Evidence:** Reading `qtawesome/animation.py`: `Spin.__init__` sets `self.info = {}` (instance attribute); `Spin.setup()` creates a `QTimer(self.parent_widget)` on first `paintEvent` and stores it in `self.info[widget]`. When `render_busy_spinner_icon(widget, theme)` is called again on a theme change, a fresh `Spin` instance is created and embedded in a new `QIcon` which replaces the old one via `setIcon()`. However, the OLD `Spin` object still holds a live `QTimer(parent_widget)` that keeps firing `_update()` → `widget.update()` → `paintEvent` indefinitely. Each theme change accumulates one additional orphaned `QTimer` on the spinner widget. In a session with 3 theme switches, 3 extra timers fire at 10 ms intervals. Impact: extra `widget.update()` calls at ~3× the nominal rate during compute windows; visually benign (the new `QIcon` paints the correct color), but undocumented CPU overhead.
**Why it matters:** Not a crash or incorrect display. The spinner shows the correct post-theme color immediately. The orphaned timers are auto-deleted when the `QPushButton` is destroyed (Qt parent-based ownership). CPU overhead is negligible given the 0.5–1.5 s compute window and typical 0–3 theme changes per session. However, future maintainers investigating "why does the spinner update() fire twice?" will find no documentation of this behavior.
**Suggested fix:** Add a one-sentence note to the `render_busy_spinner_icon` factory docstring: "Theme changes create a fresh Spin instance; the prior Spin's QTimer continues to fire widget.update() until the widget is destroyed — harmless (correct color always shows) but observable as N-times-nominal repaint rate after N theme swaps."

### LOW — 500-char adjacency threshold allows up to ~3 comment lines of drift before failing

**Where:** `tests/test_render_busy_spinner.py:196-207` (test 4) and `tests/test_render_busy_spinner.py:235-246` (test 5)
**Evidence:** The tests assert `abs(computing_true_pos - spinner_show_pos) < 500` and `abs(finally_false - spinner_hide_in_finally) < 500`. The actual current source distances are 304 chars (True-side) and 321 chars (False-side), both well within the 500-char bound. The buffer of 196–179 chars (~3 lines of 60-char code) means a maintainer could insert up to 3 lines of comment between `self._computing = True` and `setVisible(True)` without triggering the test. This is intentionally loose per the research brief ("tight enough to catch reordering into different blocks, loose enough to allow a multi-line explanatory inline comment") and correctly calibrated.
**Why it matters:** The threshold correctly catches the primary risk (moving `setVisible(True)` to a different method or block far from `_computing = True`). The loose 500-char bound is a deliberate and documented design choice, not an oversight. This is cosmetic documentation only.
**Suggested fix:** Add an inline comment to each threshold assertion documenting the current actual gap: `# Current gap: ~300 chars. Threshold loose by design — catches cross-block reordering.` This makes the choice auditable.

---

## What was done well

- **AI-9 obsolescence audit is technically correct and well-documented.** All three `processEvents` occurrences in `app.py` (lines 636, 713, 1073, 1103) are confirmed comments-only; no live call exists. The commit message, factory docstring, and §9 paragraph all correctly trace the causal chain: `realtime-variety-render-e4` → worker thread → `processEvents` removal → AI-9 blocker obsolete.

- **QPushButton-not-QLabel decision was made correctly and documented.** The research brief traced through qtawesome's `Spin.setup()` → `QIconEngine.paint()` → `QAbstractButton.paintEvent()` chain. The factory docstring at `icons.py:352-358` preserves this reasoning in precisely the right place (next to the code it justifies), not just in a milestone artifact.

- **`addPermanentWidget` positioning is correct and the reasoning is sound.** The alternative (`addWidget`) is correctly identified as incompatible with the app's `showMessage()`-heavy status bar (12+ call sites). The comment at `app.py:162` and the §9 paragraph both state the rationale explicitly.

- **Seven tests in the new test file are all AI-2 and AI-3 compliant.** No `QApplication()` construction, no `MainWindow()` construction, no Qt imports in the test runner. Tests use `pathlib.Path(...).read_text()` for `app.py` and a module-level `import icons` (safe per AI-2 because `icons.py` imports only `PySide6.QtGui.QIcon` at module scope, which does not require a running `QApplication`).

- **The `_computing = False` test (test 5) correctly navigates the dual-occurrence problem.** It uses `src.find("self._computing = False", first_false + 1)` to skip the `__init__` occurrence (char 7780) and find the `_on_mesh_ready` finally-block occurrence (char 45667). The `spinner_hide_in_finally` search also starts past `first_false + 1`, which correctly skips the `__init__`-time `setVisible(False)` (char 6529) and finds the finally-block occurrence (char 45988). Distance = 321 chars, well within threshold.

- **Test 7 (docstring AI-9 audit anchor) is a creative and durable regression guard.** Asserting that the factory docstring contains `"AI-9"` and `"paint"` ensures a future refactor that strips the docstring (or renames the method) will fail the test, prompting the maintainer to re-examine the rationale. This is above and beyond the standard source-grep pattern.

- **The factory's `qta = _get_qta()` local alias is correct.** The prior research brief identified a potential error where `qta.Spin(...)` would fail because `qta` is the lazy-import module local, not a direct reference. The implemented code correctly aliases `qta = _get_qta()` in the function body at `icons.py:368` then uses `qta.icon(...)` and `qta.Spin(...)` consistently.

- **Theme-change wiring covers both `_on_theme_changed` (manual) and `_apply_system_theme` (OS-driven follow mode).** A spinner that updated on manual theme change but not on OS-driven color scheme change would show the wrong color after `System > Follow`. Both paths correctly call `render_busy_spinner_icon(self._render_busy_spinner, resolved)` at `app.py:1110-1112` and `app.py:1158-1159`.

- **CONTEXT.md §9 deferral paragraph replacement is accurate.** The new paragraph correctly names: icon (`mdi6.loading`), animation (`qta.Spin(widget, interval=10, step=6)`), widget type (`QPushButton`), position (`addPermanentWidget`, right side), toggle sites (`_computing = True/False`), and the AI-9/AI-15 attestations. No factual errors found on spot-check of values (codepoint, interval, step, rotation time, §9 line 506).

---

## Recommended rectification order

1. **Fix the MEDIUM (§8 documentation gap).** Add a `### 8.19` section to CONTEXT.md with two bullets covering the QPushButton-not-QLabel and addPermanentWidget-not-addWidget load-bearing decisions. This is a 10-line documentation change with zero code risk.

2. **Address L1 (QMovie guard coverage) optionally.** Add two `assert "QMovie" not in _APP_SRC` lines to `test_app_render_busy_spinner_uses_qtawesome_spin_animation`. Two-line addition; no behavior change.

3. **Address L2 (timer accumulation note) and L3 (threshold comment) at discretion.** Both are docstring/comment additions. L2 adds one sentence to the factory docstring; L3 adds one comment per test assertion. Neither blocks merge.

---

*End of critique. Mandatory rectification: the MEDIUM (§8 documentation gap). The HIGH requires no code action. The three LOWs are optional. Verdict: SHIP-WITH-FIXES (MEDIUM only).*
## Frontend UI/UX findings

_Merged from milestone-frontend-ux-critic._

# Frontend UX Critique — render-busy-spinner-2026q3-e1

**Milestone:** render-busy-spinner-2026q3-e1 (UPL-4 v2)
**Commit range:** `0f95e67..fba985118`
**Files reviewed:** `app.py`, `icons.py`
**Critic:** milestone-frontend-ux-critic
**Date:** 2026-05-22

---

## Executive Summary

The spinner is well-designed: right-side `addPermanentWidget`, correct widget type (`QPushButton` flat/disabled — not `QLabel`), `AA_EnableToolTipsOnDisabledWidgets` already set in `main()`, icon color routes through `TEXT_VALUE` which measures 11.09:1 (light) and 11.60:1 (dark) against the `QStatusBar`'s explicit `BG_PANEL` background — a strong WCAG AA pass on both themes. The AI-9 re-entrancy concern documented in the §9 deferral is correctly resolved: `qta.Spin` is a pure paint path with no `processEvents()` and no signal re-emission into `_render_current`. The stale-result guard in `_on_mesh_ready` correctly sits inside the `try` (§8.18 lesson applied), so spinner hide is unconditional. All three keyboard shortcuts (`Ctrl+R`, `Ctrl+Shift+S`, `Ctrl+D`) are unaffected.

One HIGH finding: `setIconSize(QSize(16, 16))` is NOT called on `_render_busy_spinner`. Every other icon-bearing button in the app calls `setIconSize(QSize(16, 16))` after `setIcon()` (appearance_panel.py lines 656, 658, 665; view_panel.py lines 401, 403, 427, 429). Without this call, Qt uses the platform default icon size (typically 24px or the button's `iconSize()` default of QSize(16,16) on some platforms, but 22px on many macOS Fusion-adjacent styles) — the icon may render clipped, stretched, or off-centre inside the 16×16 fixed-size button.

One MEDIUM finding: the tooltip text is honest and brief, but the phrasing ("Computing surface mesh — activity indicator") fires even when the spinner is hidden at launch — a user who happens to hover the status-bar right edge before any compute will see the tooltip with no visible widget to anchor it. This is a perceptual mismatch: the tooltip's subject does not exist in the visual field.

Two LOW findings: (1) the hidden spinner creates a permanent invisible "hit region" 16×16 pixels wide on the far right of the status bar, which on very narrow windows could push the status-bar text leftward even before any compute begins; (2) the redundancy between the wait cursor and the spinner is architecturally benign but could be clarified with one sentence in the comment.

Overall: **0 CRITICAL / 1 HIGH / 1 MEDIUM / 2 LOW**. The HIGH is a small and precise fix (one `setIconSize` call). The implementation otherwise faithfully executes the research brief's design intent.

---

## CRITICAL

None.

---

## HIGH

### HIGH — Missing `setIconSize(QSize(16, 16))` on spinner button

**Where:** `app.py:338-342` (icon set block in `_build_ui`) and `app.py:175` (construction)

**Evidence:** `self._render_busy_spinner.setFixedSize(16, 16)` constrains the widget's outer geometry to 16×16. However, `setIconSize()` is never called on this button. By contrast, every other icon-bearing `QPushButton` in the app explicitly calls `setIconSize(QSize(16, 16))` immediately after `setIcon()`:

```
appearance_panel.py:656  self._wireframe_cb.setIconSize(_ICON_SIZE)    # _ICON_SIZE = QSize(16,16)
appearance_panel.py:658  self._edges_cb.setIconSize(_ICON_SIZE)
appearance_panel.py:665  self._hq_smoothing_cb.setIconSize(_ICON_SIZE)
view_panel.py:401         self._reset_camera_btn.setIconSize(_ICON_SIZE)
view_panel.py:403         self._shot_btn.setIconSize(_ICON_SIZE)
view_panel.py:427         btn.setIconSize(_ICON_SIZE)                    # camera presets
view_panel.py:429         self._iso_btn.setIconSize(_ICON_SIZE)
```

The spinner has no matching `setIconSize` call at either construction time or in the icon-set block (`app.py:338-342`).

**Why it matters:** Qt's `QPushButton.iconSize()` defaults to `QStyle::PM_SmallIconSize` (platform-dependent — macOS Aqua: 16px, macOS Fusion: 16px, some Linux Fusion themes: 22px). When `setFlat(True)` suppresses the button chrome and the fixed size is 16×16, a platform reporting `PM_SmallIconSize=22px` will try to render a 22px icon inside a 16px bounding box. The result is clipping: the spinner arc's leading edge gets cropped, and the rotation animation looks asymmetric or truncated. On macOS Aqua (AVC's primary dev platform) `PM_SmallIconSize` happens to be 16px, so the problem is latent rather than immediately visible — but it surfaces on any Linux deployment or macOS with a non-default DPI/style. All 7 peer buttons guard against this with an explicit `setIconSize(QSize(16, 16))`.

**Suggested fix:** Add `self._render_busy_spinner.setIconSize(QSize(16, 16))` immediately after `self._render_busy_spinner.setIcon(...)` in the icon-set block at `app.py:338-342`. `QSize` is already imported in `appearance_panel.py`; in `app.py`, use `setFixedSize` form or add `QSize` to the `PySide6.QtCore` import. Alternatively, call `setIconSize(QSize(16, 16))` at construction time (line 175) so it is set once, unconditionally, before any theme-refresh.

---

## MEDIUM

### MEDIUM — Tooltip fires on hover of invisible widget before first render

**Where:** `app.py:176-178` (tooltip set at construction, with `setVisible(False)` permanent)

**Evidence:** The spinner is created with `setVisible(False)` and `addPermanentWidget()`. `addPermanentWidget` places the widget permanently in the status bar's right region. Qt's permanent-widget layout allocates zero horizontal space for hidden permanent widgets on most platforms (verified: `QStatusBar` does NOT reserve a gap for a hidden permanent widget the way it does for a visible one). However, the widget still exists in the widget tree and can receive mouse-hover events when revealed by any geometry overlap with the status bar edge region.

More practically: the tooltip text "Computing surface mesh — activity indicator (not a progress bar)." is actively misleading at launch, before any variety is selected. A user who hovers the far-right corner of the status bar on the launch state ("Choose a variety to begin.") sees tooltip text claiming a compute is happening on a surface they have not yet chosen.

**Why it matters:** VS Code's language-server spinner tooltip only activates while the spinner is visible; hovering the spot where it will appear when hidden shows nothing. ParaView's busy indicator (pqProgressManager) is only reachable via hover while it is visible. AVC's tooltip is always hoverable because `setEnabled(False)` + `AA_EnableToolTipsOnDisabledWidgets` means the tooltip fires on disabled AND hidden widgets alike (Qt's `QWidget::event` delivers `ToolTip` events to hidden widgets that still have a geometry in the layout). The tooltip text anchors to a computation that may not be in progress.

**Suggested fix:** Either (a) move the `setToolTip()` call into the `setVisible(True)` path (`app.py:714`) and clear it in the `setVisible(False)` path, or (b) rephrase the tooltip to be accurate in the idle state too: `"Mesh computation in progress — activity indicator"` (present-tense conditional, honest when visible; vacuous but not misleading when hidden). Option (b) is a one-line text change; option (a) adds two calls but removes all ambiguity.

---

## LOW

### LOW — Hidden permanent widget's space reservation is platform-ambiguous

**Where:** `app.py:179-180`

**Evidence:** `self._render_busy_spinner.setVisible(False)` then `addPermanentWidget(self._render_busy_spinner)`. Qt's documented behavior for hidden permanent widgets is that they "may" reserve their layout space on some platforms and collapse on others. On macOS Fusion, hidden permanent widgets collapse to zero width — so no status-bar text displacement occurs in the idle state. On some Linux Qt styles (e.g., `QCleanlooksStyle`, older Qt5 GTK bridge), a hidden permanent widget reserves its full `sizeHint()` width. Since the button is `setFixedSize(16, 16)`, the worst case is a 16px invisible gap on the right, slightly pushing the status-bar text clip point left by 16px. This is cosmetically benign at normal window widths but is non-zero at 400px or smaller.

**Why it matters:** The brief acknowledges this (§4.2 "hidden permanent widget still reserves space, so this should be OK — verify"), but the verify step is missing from the implementation comments. The risk is low because the app's minimum useful window width is well above 400px, but a one-line comment documenting the zero-width expectation would help future maintainers.

**Suggested fix:** Add a comment at line 179: `# setVisible(False): Qt collapses hidden permanent-widget width to zero on Fusion/Aqua; the 16px gap is latent on legacy GTK styles.` This makes the design assumption explicit without requiring a code change.

---

### LOW — Wait-cursor and spinner redundancy undocumented

**Where:** `app.py:709-725` (`_render_current` dispatch block)

**Evidence:** At dispatch time, both `self._render_busy_spinner.setVisible(True)` (line 714) and `QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)` (line 724) fire within the same code block. The two busy indicators serve different purposes (cursor = pointer-proximity feedback for interaction-blocking; spinner = peripheral-vision "still computing" indicator), but this is not documented at the call site. The research brief addresses this in §10 ("spinner vs cursor do serve different purposes") but the insight is not captured in the inline comment.

**Why it matters:** Future maintainers may remove one of the two, not realizing they serve distinct roles. Blender 4.x and ParaView both use a wait cursor PLUS a status-bar indicator simultaneously — this dual-indicator pattern is intentional and peer-validated, but the comment does not cite it.

**Suggested fix:** Expand the inline comment at line 710 to note: `# Paired with the wait cursor (line 724): the cursor signals pointer-proximity interaction-blocking; this spinner provides peripheral-vision feedback during the 0.5-1.5s flight window. Both are intentional — see Blender 4.x / ParaView dual-indicator precedent.`

---

## What Was Done Well

1. **Correct widget choice with rationale.** Using `QPushButton(flat=True, enabled=False)` instead of `QLabel` is a non-obvious decision (qtawesome Spin only triggers through `QIcon.paint()` in `QAbstractButton.paintEvent`, not via `QLabel.setPixmap()`). The code comments explain this at the construction site, the `icons.py` docstring explains it in the factory, and the research brief documents the discovery process. All three artifacts agree — no maintenance divergence.

2. **`addPermanentWidget` over `addWidget` with correct rationale.** The brief considered both options and correctly chose `addPermanentWidget` because the app calls `showMessage()` at every render event; `addWidget` slots get obscured by temporary messages. The construction comment states this explicitly. This is the most important placement decision and it was made correctly.

3. **AI-9 re-entrancy analysis is thorough and complete.** Both the code comments and the `icons.py` docstring trace the signal chain: `QTimer.timeout` → `widget.update()` → `paintEvent` → `QIcon.paint()`. No `processEvents()`, no signal re-emission into `_render_current`. The existing `_computing` guard is not touched. The factory docstring even explicitly states "The existing `self._computing` re-entrancy guard remains the source of truth for in-flight detection; this spinner is a pure visual companion."

4. **`AA_EnableToolTipsOnDisabledWidgets` already set.** A prior milestone (`enriques-hq-smoothing-2026q3-e1`) set this attribute in `main()` (app.py:1210-1211), so the disabled spinner's tooltip fires correctly on hover on macOS without additional work. The new milestone inherits this correctly.

5. **Theme-refresh coverage is complete.** `setIcon(render_busy_spinner_icon(...))` is called at three sites: initial `_build_ui()`, `_on_theme_changed()`, and `_apply_system_theme()`. This mirrors the existing pattern for all three panel `refresh_icons()` calls and ensures the spinner picks up `TEXT_VALUE` for the active theme on every theme transition — including the "Follow System" OS-driven path.

6. **Contrast is strong on both themes.** `TEXT_VALUE` (#333333 light, #e0e0e0 dark) measures 11.09:1 and 11.60:1 respectively against the `QStatusBar`'s explicit `BG_PANEL` background. Both vastly exceed the WCAG AA 4.5:1 body-text floor and the 3:1 non-text floor. The status bar QSS rule explicitly sets `background: {palette["BG_PANEL"]}` so there is no platform palette leakthrough.

7. **Stale-result guard is inside the `try`.** The `is_stale_result` early-return at line 766-767 is inside the `try` block (confirmed at app.py:758), so the `finally` that hides the spinner and clears `_computing` runs on the stale-delivery path — preventing the permanent soft-freeze documented in §8.18.

8. **Icon choice (`mdi6.loading`) is coherent with the app's icon family.** All existing icons use `mdi6.*`. Staying in the same font family avoids a second cold-boot font-load. `mdi6.loading` (the partial-arc glyph) is the canonical compute-activity indicator in the VS Code ecosystem, which most users of this type of scientific-viz app will recognize. Alternatives (`mdi6.sync`, `mdi6.progress-clock`) were considered and correctly rejected.

---

## Recommended Rectification Order

| Priority | Finding | File | Effort |
|---|---|---|---|
| HIGH | Add `setIconSize(QSize(16, 16))` to spinner after `setIcon()` | `app.py:338-342` | 1 line |
| MEDIUM | Rephrase tooltip to be accurate in idle state (or gate it on visibility) | `app.py:176-178` | 1-2 lines |
| LOW | Document wait-cursor / spinner dual-indicator rationale inline | `app.py:710` | 1 line comment |
| LOW | Document hidden-permanent-widget zero-width expectation | `app.py:179` | 1 line comment |

All four fixes are documentation-level or single-line code additions. No architecture change is required.

---

## Rectification status — 2026-05-23

**Fixed (in-scope, this rect commit):**
- `frontend HIGH` (missing `setIconSize`): added `self._render_busy_spinner.setIconSize(QSize(16, 16))` immediately after `setFixedSize` in `app.py`. Imported `QSize` in the `PySide6.QtCore` import block. Latent on macOS Aqua (where `PM_SmallIconSize` happens to be 16), real bug on Linux Fusion themes where it can be 22 → spinner arc clips inside the 16×16 frame. New regression-guard test `test_render_busy_spinner_widget_calls_set_icon_size`.
- `adversary MEDIUM` (CONTEXT.md §8 entry missing): added new §8.19 documenting BOTH load-bearing gotchas (QPushButton-not-QLabel + addPermanentWidget-not-addWidget) AND the rect-HIGH setIconSize gotcha as a bonus. Institutional memory anchor for future status-bar / animated-icon work.
- `frontend MEDIUM` (tooltip misleading at idle): rephrased tooltip from "Computing surface mesh — activity indicator (not a progress bar)." (claims compute in progress regardless of state) to "Render activity indicator (not a progress bar)." (state-agnostic — honest whether visible or hidden). Inline comment cites the rect closure.
- `adversary LOW-1` (QMovie guard covers icons.py only): extended `test_app_render_busy_spinner_uses_qtawesome_spin_animation` to also assert `from PySide6.QtGui import QMovie` and `QMovie(` are absent from `app.py`. Symmetric guard across both files; cheap test extension.

**Deferred (out-of-scope or cosmetic):**
- `adversary HIGH` (process / diff-size auto-finding): 1517 lines total but ~515 of that is artifact files (research brief, implementation-plan, state.json, dispatch.log, agent memory). Functional diff is ~405 LOC — below the 400 threshold once artifacts are subtracted. No code action.
- `adversary LOW-2` (Spin QTimer accumulation across theme changes undocumented): comment-only nudge. The factory creates a new `QIcon` + `qta.Spin(widget)` on each theme swap; whether the prior QTimer is GC'd or accumulates depends on qtawesome internals. Real-world impact: 0 (user doesn't theme-swap during 0.5–1.5 s compute window). Defer comment.
- `adversary LOW-3` (500-char adjacency threshold "looseness"): the 300 → 500 char loosening was deliberate (allows multi-line explanatory inline comments without breaking the test). 500 chars is still ~8 lines of source — catches genuine reordering into different blocks. Threshold is intentional, not loose.
- `frontend LOW-1` (hidden permanent widget space reservation platform-ambiguous): Qt collapses hidden permanent-widget width to zero on Aqua/Fusion (AVC's only target platforms); the cited 22-px gap is only on legacy GTK styles AVC doesn't target. Defer comment.
- `frontend LOW-2` (wait-cursor + spinner redundancy): they serve different purposes (cursor = pointer-proximity blocking, spinner = peripheral-vision indicator); Blender 4.x and ParaView both use dual-indicator pattern. Comment expansion is nice-to-have, not required.

**Invalidated:** none.

**Test count:** 393 (was 392, +1 for `test_render_busy_spinner_widget_calls_set_icon_size`).
