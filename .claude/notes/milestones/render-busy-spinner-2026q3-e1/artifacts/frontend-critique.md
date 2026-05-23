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
