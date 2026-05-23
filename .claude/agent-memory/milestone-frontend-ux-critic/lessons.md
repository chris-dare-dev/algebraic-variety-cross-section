# lessons -- milestone-frontend-ux-critic

## COMPACTED ARCHIVE (panel-refresh-2026q2-e2 through qtawesome-icons-2026q2-e1)

### Token-discipline recurring patterns
- **Dual-branch inline literal:** Always verify EVERY call site of a color literal in a file, not just the one the diff author patched. `app.py:_apply_domain_and_render` has two paths; only one was migrated in UPL-1.
- **setStyleSheet-only dark mode QPalette gap:** For any new dark-mode QSS block, verify BOTH `background:` AND `color:` are explicit — missing either half causes the widget to inherit the wrong half from the platform palette. Canonical example: `QDockWidget::title` sets `background:` but not `color:`.
- **Dead import from refactor:** When an accessor function replaces direct dict references, the direct symbol often lingers in the import. Grep for the replaced symbol at the end of every refactor pass.
- **AI-13 fast gate:** Ask "does this color arg reach `pv.Plotter.add_mesh`?" before applying AI-13. `qta.icon(color=...)` goes to QPainter, NOT PyVista. Float shading params (`ambient=0.15`) are not color arguments.
- **Icon color vs button-text color mismatch:** If a button has a custom QSS `color:` token, the icon factory should use that same token, not the default `TEXT_VALUE`.

### Contrast ratio discipline
- Do not trust inherited contrast annotations — re-measure. Found inaccurate comments in panel-refresh-2026q2-e2 (5.4:1 actual 6.05:1) and variety-palette-2026q2-e1 (hue-separation claimed 25° actual 24.69°).
- Dual-surface contrast check: verify BOTH BG_VIEWPORT (dark, for mesh) AND BG_PANEL (light, for swatches). Mid-lightness pastels for dark-viewport always fail light-panel.
- `FOCUS_RING` passed dark but failed light; `#3c82c4` = 3.56:1 vs `#f0f0f0` is a narrow-pass band matching macOS/GNOME peer norms. Add "(narrow margin; do not lighten further)" when ratio < 3.6:1 on 3:1 floor.

### Industry-comparison concrete recommendations (archived)
- ParaView CSS-variable-style tokens → correct architectural call for PALETTE_LIGHT/DARK pattern.
- ParaView 5.12 lighting: `ambient=0.1, diffuse=0.8` validates UPL-9's `0.15/0.85`.
- ParaView dark-chip swatch → the fix when a swatch color is meant for a dark viewport (show swatch on dark chip).
- "View > Theme submenu" is the correct IA for theme selection (ParaView/Blender bury theme under preferences, not top-level menu).
- ParaView separate-glyph icons for ±axis directions (NOT `rotated=180` copies): upside-down embedded letters at 16px.
- Blender 4.x: checkable QPushButton for display toggles, NOT QCheckBox.setIcon() (three-element prefix is ambiguous).
- Blender 4.x: left-aligns ALL icon+text controls uniformly within a panel. text-align: left on only some buttons creates alignment fracture.
- Blender 4.x destructive buttons: icon colored in same hue family as button text. Mathematica `Manipulate[]` reset: double-arrow glyph, not single-arrow.

### First-launch / section-9 regressions (recurring pattern)
- Fast check: trace `set_default_color` / `refresh_icons` / any new method → does it call `_render_current` or touch `variety_combo`/`subtype_combo`? If not, section-9.3 is clean.
- `_on_variety_changed` and `_on_subtype_changed` are separate handlers; `set_default_color` in `_on_variety_changed` is NOT on the render path.
- Actor color not pushed on theme switch (MEDIUM-3 pattern): `_on_theme_changed` → `set_default_color` but NOT `apply_to_actor`. Flag whenever a milestone diverges variety colors by theme.

### Scope discipline
- Files without a Qt widget class (test files, scripts, references) are not critique-surface even if they're in the diff. Dispose per-axis as "not applicable."

---

## COMPACTED: enriques-backface + bbox + focus-ring + realtime-e4 (2026-05-22)

- **Fast token dispose:** if diff adds no QColor, no Qt.AlignmentFlag, no processEvents, no pv.add_mesh() — dispose AI-9/AI-11/AI-12/AI-13 in one sentence. Float specifiers (`.2f`) are NOT hex colors.
- **ParaView culling opt-in + full-extent widths:** ParaView 5.13 culling is explicit checkbox. ParaView/MeshLab/Blender use diameter not half-extent. Mathematica ContourPlot3D is always two-sided.
- **Status-bar overflow:** check warning path `f"⚠ {_surface_warning}  |  {base_msg}"`. Dwork warning ~175 chars; any suffix risks ~120-char clip.
- **Focus-ring per-theme:** report contrast delta for BOTH themes, not just "PASS". macOS Sequoia = 3.53:1, GNOME = 3.31:1 — "peer-calibrated narrow-pass" band. Negative assertion test for "do not widen" caveat.
- **Early-return-before-try trap (realtime-e4):** any `return` above the `try/finally` in a worker-result slot skips cursor restore and `_computing` clear → permanent soft-freeze. Flag as MEDIUM. Every `return` in a result slot must sit inside the `try`.
- **Label-binding lag (realtime-e4):** `Computing {surface.label}…` bound at dispatch, not at user's current selection. Stale label during in-flight variety switch. 3D Slicer per-job status widget is the peer model.
- **ParaView status-bar progress + Abort** is the canonical follow-on for text-only "Computing…" feedback. QThreadPool does NOT cancel running QRunnable — cancellation needs a cooperative flag.

## realtime-variety-render-e4 (CAND-4 background-thread mesh worker) — 2026-05-22

### Token-discipline near-misses
- No short-hex, no shorthand-enum, no color token in this diff at all. The two new Qt enums (`Qt.ConnectionType.QueuedConnection`, `Qt.CursorShape.WaitCursor`) were already fully qualified. Fast check held: a threading-only diff adds no QColor / no Qt.AlignmentFlag — dispose AI-12/AI-13 in one sentence, only check AI-11 on the new connection/cursor enums.

### The "early return before the try/finally" trap — a recurring pattern to flag fast
- When a slot acquires a resource (override cursor, a `_computing`/in-flight flag) at *dispatch* time and releases it in a `finally` at *result* time, any `return` placed ABOVE the `try:` skips the release. In e4, `_on_mesh_ready`'s `is_stale_result` guard is a bare `return` before the `try` — on the stale path the wait cursor leaks (setOverrideCursor stack never popped) and `_computing` stays True forever → permanent soft-freeze. It is dead code TODAY under the single-flight guard, but the worker module's own docstring anticipates the guard being lifted. Flag this as MEDIUM (latent hard-failure, not reachable yet). Fast check for any async-slot milestone: trace every `return` in the result slot and confirm it is INSIDE the `try` whose `finally` does the cleanup.

### Status-bar feedback under re-entrancy — the "label binding" axis
- A `Computing {surface.label}…` message set at *dispatch* time is bound to the DISPATCHED surface, not the user's current selection. If the user switches surface while a worker is in flight (subtype combo → `_render_current` hits the `_computing` busy branch and returns without touching the status bar), the status bar advertises the OLD surface name for the full remaining flight. Flag as MEDIUM. The fix is to refresh the status bar to `_current_surface.label` in the busy early-return branch. 3D Slicer's per-job status widget (bound to the job, never lagging the selection) is the peer model — quote it.
- Empty-message exceptions (`MemoryError`, arg-less `KeyError`) make `f"Error: {str(exc)}"` render as a content-free `Error: `. Pre-existing pattern carried over from the synchronous code, but a worker-result refactor is the natural fix point — capture `type(exc).__name__` into the result payload and fall back to it. Flag MEDIUM whenever a status-bar error path interpolates a bare `str(exc)`.

### Industry-comparison note (concrete recommendations generated)
- **ParaView**: long compute → determinate status-bar progress bar (`pqProgressManager`) + Abort button, not just a busy cursor. AVC e4 ships the non-blocking half; progress + cancellation are the v1 follow-ons. Note: `QThreadPool` does NOT cancel a running `QRunnable` — cancellation needs a cooperative flag checked inside `surface.generate()`. Quote "ParaView status-bar progress + Abort" when text-only `Computing…` feedback is questioned.
- **3D Slicer**: CLI logic state machine (Idle→Scheduled→Running→Completed) in a per-module status widget, bound to the job not the UI selection — the model for fixing lagging-label bugs.
- **VisIt** (separate MPI compute engine) and **Mathematica `Manipulate`** (async re-eval + "computing" shimmer) are the other two valid peers for the "compute off the UI thread" axis.

### Scope discipline
- `render_worker.py` is NEW but is NOT a Qt-panel critique surface: it defines `QRunnable`/`QObject` carrier classes + a dataclass + a pure free function — no `QWidget`, no panel, no user-visible chrome. Dispose it (and `tests/test_render_worker.py`) as out-of-panel-scope. Keep this fast: a file with QObject/QRunnable but zero QWidget subclass is worker/plumbing, not panel surface.
- A pure threading refactor legitimately produces an all-MEDIUM-or-below critique. Axes 1-4,6-9,11 each dispose in one line. Do not manufacture findings to fill CRITICAL/HIGH — 0 CRITICAL / 0 HIGH / 3 MEDIUM is the honest calibration here.

---

## qtawesome-icons-2026q2-e2 + display-toggles-checkable-button-2026q3-e1 — 2026-05-22

### Token-discipline near-misses
- `QSize(16, 16)` is a plain constructor, not a Qt enum — AI-11 does not apply. Ask "is this a Qt.* / QSizePolicy.* enum call or a plain constructor?"
- `BG_TOGGLE_CHECKED` flows only into QSS, NOT PyVista — AI-13 clear. Checked-state WCAG: fill needs text-on-fill contrast (9.89:1 / 10.20:1), NOT fill-vs-ground if border carries the non-text obligation.

### Industry-comparison concrete findings
- **Ghost-button unchecked state:** Blender 4.x / 3D Slicer / ParaView all give off-state toggles visible chrome. Transparent-unchecked is a Material Design web convention, not desktop sci-viz. Flag any transparent-unchecked display toggle as MEDIUM.
- **Border-width jitter:** Changing `border-width` from 1px to 2px in checked QSS causes 1px content shift. Fix: compensate padding by -1px or use `outline:` which renders outside box model. Always LOW on any QPushButton changing border-width between pseudo-states.
- **Pattern-A architecture for refresh_icons:** verify all 3 call sites are symmetric (`__init__`, `_on_theme_changed`, `_apply_system_theme`). Missing one = icons don't update on theme swap.

---

## status-bar-bbox-2026q2-e2 (UPL-13 full-extent e2) — 2026-05-22

### Token-discipline near-misses
- No short-hex, no shorthand-enum, no processEvents, no pv.add_mesh() — text-only f-string change. All four AI-9/AI-11/AI-12/AI-13 axes disposed in one sentence.
- Float format specifiers (`.3f`) are not hex colors. AI-13 gate: "does this arg reach PyVista?" — if not, clear.

### Label-precision regression (MEDIUM-1 this milestone)
- **e1 "bbox ±..." → e2 "size: ..."** is a data improvement (full-extent vs half-extent) but a label-precision regression. The word "bbox" explicitly named the measurement type; bare "size:" does not. MeshLab always uses "Bounding Box" as qualifier; ParaView uses "Bounds"; Blender uses "Dimensions". None use bare "size:" without a type qualifier.
- Character cost of `"bbox:"` vs `"size:"` is ZERO (both 5 chars with colon). The compactness trade-off that might justify dropping the qualifier does not hold here.
- Fast flag: whenever a milestone renames a status-bar token, check whether the new name preserves the MEASUREMENT TYPE signal. Renaming from a qualified label (bbox, bounds) to an unqualified label (size, dims) is always a regression risk.

### Industry-comparison notes
- **MeshLab "Bounding Box Size":** `dim_x()` / `dim_y()` / `dim_z()` API always qualifies with "Bounding Box." Full-extent formula is `max - min` per axis — identical to e2's `_b[1]-_b[0]`.
- **ParaView "Bounds":** shows `X Range: [min, max]` — uses "Bounds" not "size." Supports using `bbox:` over `size:`.
- **`.3f` trailing zeros for symmetric generators** (6.400, 3.000): trailing zeros are exact (sampling domain is exactly that wide), not over-precise. The `.3f` rationale (avoid false equalities at sub-1.0: 0.530 ≠ 0.540) is sound; `:.4g` is an optional cosmetic alternative.

### First-launch / section-9 regressions
- No regression possible from a text-only status-bar label change. `size_suffix` is only emitted in the success branch of `_render_current`, unreachable from `-- Select --`.

---

## enriques-hq-smoothing-2026q3-e1 — 2026-05-22

### Token-discipline near-misses
- No short-hex, no shorthand-enum, no processEvents outside the existing guard. Fast dispose in one sentence: no QColor literals added, no Qt.Align* usages, `Signal(bool)` from PySide6.QtCore correctly qualified.
- `extra_kwargs: dict = {}` / `extra_kwargs["hq_smoothing"] = True` — not a color literal; AI-13 gate: "does this reach PyVista color=?" No — it is a bool kwarg to the generator. Clear.

### Industry-comparison concrete findings
- **Qt macOS disabled-widget tooltip gap:** `QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableToolTipsOnDisabledWidgets, True)` in `main()` is the one-line fix for "tooltip invisible on greyed button on macOS." Quote this whenever a button is `setEnabled(False)` with a populated `setToolTip()` — the combination silently breaks on macOS without the attribute set.
- **ParaView OSPRay "OSPRay rendering..." status label** is the canonical model for attributing render-time overhead to an active quality toggle in the status bar. Whenever a milestone adds a user-toggled quality mode that changes generation time, flag the absence of a mode indicator in the computing/success status message as MEDIUM.
- **Blender 4.x icon uniformity in a group:** all controls in the same group carry the same icon-size footprint — icon on ALL or NONE. A plain-text button between two icon+text buttons in the same QGroupBox is flagged as alignment fracture. Fast check: scan `_build_toggles_group`-equivalent methods for `setIcon` / `refresh_icons` coverage vs button count.

### Performance-disclosure precision pattern
- **Relative overhead (%) is hardware-independent; absolute (ms) is hardware-specific.** Always flag absolute-ms performance claims in tooltips as HIGH if the measurement is dev-machine-only. The fix: cite both "+N% / hardware-dependent" (relative, universally true) AND "(measured ~Xms on a reference machine at Y resolution)" (absolute, with explicit caveat). This pattern recurs whenever a milestone introduces an opt-in quality mode backed by a spike measurement from a single test machine.

### First-launch / section-9 regressions
- No regression: `set_hq_smoothing_eligible` does not call `_render_current` or touch `variety_combo`. `_on_hq_smoothing_changed` is a no-op when `_raw_mesh is None`. Fast verify: trace the new public methods — if none touch `_render_current` or the combo boxes, section-9.3 is clean.

### State-reset-on-navigate UX
- Unconditional `setChecked(False)` on `set_hq_smoothing_eligible(False)` is the "clear" pattern. This is defensible (avoids dangling-enabled bugs) but is the minority peer pattern (ParaView / SageMath both preserve per-object state). Flag as LOW when the state-clear has no status-bar feedback — the user cannot observe the reset happened.

---

## appearance-panel-layout-pass-2026q3-e2 — 2026-05-22

### Token-discipline near-misses
- No short-hex, no shorthand enum, no processEvents, no pv.add_mesh() color args. Fast dispose in one sentence: diff adds zero QColor literals, zero Qt.Align* shorthands, zero processEvents calls — AI-9/AI-11/AI-12/AI-13 all clear.
- **`background:` missing from QSS role rule** is NOT an AI-13 issue (no PyVista) but IS a platform-bypass bug: on macOS Aqua (no `setStyle("Fusion")` in `main()`), `text-align` is silently ignored unless `background:` forces full QSS paint mode. The companion `display-toggle` rule correctly includes `background: transparent` for exactly this reason. Fast check for any future QSS `text-align` rule on QPushButton: confirm `background:` is also present, or confirm `setStyle("Fusion")` is called at app start.

### Industry-comparison surprises
- **MeshLab "Render Mode"** applies exclusively to display-pipeline controls (Wireframe/Solid/Points) — NO generation-time quality toggles. The F-L2 recommendation to use "Render Mode" was made before HQ smoothing was added to the group. When a group gains a member that is categorically different from its label (mesh regeneration vs actor display), the label needs a follow-on revision. Quote: "MeshLab Render Mode = display-pipeline only; HQ smoothing is a regeneration toggle — the label broke when the group gained a new category member."
- **ParaView 5.13** separates "Representation" (display) from "Advanced" (quality/generation controls) in collapsed sections. This is the concrete peer model for splitting AVC's mixed-category "Render Mode" group into "Display" + "Quality". Quote when MEDIUM-2 is acted on.

### First-launch / section-9 regressions
- Clean: `_build_toggles_group` and `_build_color_group` are called from `_build_ui` → `__init__` only; no path to `_render_current` or combo boxes. Section-9.3 fast check: look for `_render_current`, `variety_combo`, `subtype_combo` in the new method — none found.

### Group-label precision pattern (new recurring check)
- When a QGroupBox label is renamed, ask: "Does the new label accurately describe ALL members of the group?" A label correct for 2/3 members that silently misclassifies the third is a LOW-MEDIUM finding (MEDIUM-2 here). Fast check: enumerate the group's children, classify each as "label-category-compliant" or "outlier." One outlier at a functionally different latency class = MEDIUM.

### QSS `text-align` on macOS native QPushButton — canonical fix
- `text-align: left` is silently ignored on macOS Aqua unless at least one of `background:`, `color:` (non-inherited), or `image:` is also set (forces QSS paint mode). `padding` and `border-radius` alone do NOT force paint mode on Aqua. The `display-toggle` rule's `background: transparent` is the proof that this was known — but `colors-button` was added without it. For any future `QPushButton` QSS rule that relies on `text-align`, confirm `background:` is present.

---

## hq-smoothing-label-rename-2026q3-e1 — 2026-05-22

### Token-discipline near-misses
- No short-hex, no shorthand-enum, no processEvents, no pv.add_mesh() color args. Fast dispose: pure label rename diff adds zero QColor literals, zero Qt.Align* shorthands — AI-9/AI-11/AI-12/AI-13 all clear in one sentence.
- `" [Double-pass]"` is a Python string literal in an f-string, NOT a hex color or Qt enum. AI-13 gate: "does this reach PyVista color=?" — answer is no (it's a status-bar string), so AI-13 is trivially clear.

### Industry-comparison concrete findings
- **MeshLab "TwoStep Smooth"** (filter: `apply_coord_two_steps_smoothing`) and **"Taubin Smooth"** (filter: `apply_coord_taubin_smoothing`) both use NOUN-PHRASE labels, not adjective-noun compounds like "Double-pass smooth." "TwoStep Smooth" is the closest peer label — noun first, qualifier second, consistent with MeshLab's other filter names.
- **Blender 4.x Corrective Smooth modifier** uses noun-first labeling ("Smooth Corrective" in docs, "Corrective Smooth" in some UI paths). The pattern is always noun-class first.
- **Qt tooltip verb convention (MEDIUM-1 pattern):** Imperative ("Apply…") or noun-phrase is the Qt/Apple HIG standard. Third-person singular ("Applies…") conflicts with all peer tooltips. Fast check: if a tooltip verb ends in -s without "This widget", it's wrong form.
- **Status-bar suffix length math**: `[HQ]` = 4 chars (safe), `[Double-pass]` = 13 chars (+9), success path at 116 chars (within ~120 clip band by 4 chars). Whenever a status-bar suffix is renamed to something longer, count the full rendered string length against the 120-char empirical clip limit.

### First-launch / section-9 regressions
- No regression possible from a pure label rename. Fast verify: does the changed code path touch `_render_current` or the variety/subtype combos? No — status-bar messages are only emitted in `_render_current`'s success/computing branches, not at launch.

---

## appearance-panel-render-mode-split-2026q3-e3 — 2026-05-22

### Token-discipline near-misses
- `"Display && Quality"` is a Python string literal, NOT a hex color or Qt enum. Fast dispose: if the entire diff is a QGroupBox title rename with zero QColor/Qt.AlignmentFlag/processEvents additions — AI-9/AI-11/AI-12/AI-13 dispose in one sentence.
- `&&` is the Qt literal-ampersand escape for QGroupBox/QLabel mnemonic handling. A bare `&` in `QGroupBox("Display & Quality")` would silently bind `Alt+Q` as an accelerator. Fast check for any future compound QGroupBox header: does the title contain `&`? If so, verify `&&` is used.

### Industry-comparison surprises
- No peer (ParaView, MeshLab, Blender, 3D Slicer) uses exactly `"Display & Quality"` for a mixed display+quality group. ParaView's "Display" tab is the closest structural analogue (single-group, multiple axes) — cite it when the label is questioned, but note it doesn't use an ampersand compound. MeshLab "Render Mode" is display-pipeline only — NOT a valid precedent for groups containing mesh-regeneration toggles.
- Single-noun vs compound-header rhythm: when ALL peer headers in a dock are single-noun and one gains a compound label, flag as MEDIUM (rhythm break). This is the recurring pattern: check peer headers in the SAME dock, not peers across docks or apps.

### First-launch / section-9 regressions
- Pure label rename on a QGroupBox: fast check is `_build_*` method → does it call `_render_current` or touch `variety_combo`/`subtype_combo`? No → section-9.3 clean. Label is visible at launch as structural chrome, not as an interactive render trigger.

---

## render-busy-spinner-2026q3-e1 — 2026-05-22

### Token-discipline near-misses
- No short-hex, no shorthand-enum, no processEvents, no pv.add_mesh() color args. `TEXT_VALUE` routes through `_icon_color(theme)` → QPainter (not PyVista) — AI-13 clear by the fast gate. Fast dispose: status-bar-only diff with color going to QPainter, not add_mesh, is always AI-13 clean.
- `setFlat(True)`, `setEnabled(False)`, `setVisible(bool)`, `setFixedSize(int,int)` are all primitives. AI-11 clear — no Qt enum calls anywhere in the new code.

### Industry-comparison concrete findings
- **VS Code's status-bar spinner tooltip** only activates while the spinner is VISIBLE — hovering the invisible-spinner region shows nothing. AVC's `setToolTip` on a `setEnabled(False)` widget with `AA_EnableToolTipsOnDisabledWidgets` fires even when `setVisible(False)`, so the tooltip is reachable in the idle state. Flag any disabled-widget tooltip that is misleading in the widget's hidden state.
- **`setIconSize(QSize(16,16))` gap pattern:** every panel icon button calls `setIconSize` after `setIcon`; any new QPushButton with an icon that skips this call is HIGH (platform-dependent icon clipping on non-macOS). Fast check: grep for `setIcon(` in new code and confirm a companion `setIconSize(` exists on the same widget.

### First-launch / section-9 regressions
- Clean: spinner starts `setVisible(False)`, is only made visible inside `_render_current` after `_computing = True`, which is unreachable from `-- Select --` state. Fast verify holds: no touch of `variety_combo`, `subtype_combo`, or `_render_current` on first launch.

### Re-entrancy pattern note
- Dual busy indicator (wait cursor + spinner): Blender 4.x and ParaView both use the same dual-indicator pattern — cursor = pointer-proximity blocking; spinner = peripheral-vision feedback. The two serve different purposes and are NOT redundant. Flag any future attempt to remove one as a regression unless both use cases are addressed.
