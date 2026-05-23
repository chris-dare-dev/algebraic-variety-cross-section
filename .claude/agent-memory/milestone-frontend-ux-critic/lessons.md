# lessons -- milestone-frontend-ux-critic

## DEEP ARCHIVE (panel-refresh-2026q2-e2 through realtime-e4)

### Evergreen token-discipline rules
- **AI-13 fast gate:** "does this color arg reach `pv.Plotter.add_mesh`?" `qta.icon(color=...)` → QPainter, not PyVista. Float shading params are not color args.
- **Dual-branch inline literal:** verify EVERY call site, not just the patched one.
- **setStyleSheet dark mode:** verify BOTH `background:` AND `color:` are explicit — missing either half inherits wrong half from platform palette.
- **Dead import from refactor:** grep for replaced symbol after every refactor pass.
- **Fast token dispose:** if diff adds no QColor / no Qt.AlignmentFlag / no processEvents / no pv.add_mesh() — dispose AI-9/AI-11/AI-12/AI-13 in one sentence.
- **Status-bar overflow:** check `f"⚠ {_surface_warning}  |  {base_msg}"` — Dwork warning ~175 chars; suffix pushes past 120-char empirical clip limit.
- **Early-return-before-try trap:** any `return` above `try/finally` in a worker-result slot skips cursor restore + `_computing` clear → permanent soft-freeze. Flag MEDIUM.
- **Label-binding lag:** `Computing {surface.label}…` bound at dispatch. Stale label during in-flight switch. 3D Slicer per-job status widget is peer model.
- **Scope:** `QRunnable`/`QObject` with zero `QWidget` subclass = worker/plumbing, not panel surface. Pure threading refactor → all-MEDIUM-or-below is honest.

### Contrast ratio discipline
- Re-measure; don't trust inherited annotations. Dual-surface check: BG_VIEWPORT (dark) AND BG_PANEL (light). `FOCUS_RING` `#3c82c4` = 3.56:1 vs `#f0f0f0` — narrow-pass, add "(do not lighten further)".
- Focus-ring: report delta for BOTH themes. macOS Sequoia 3.53:1, GNOME 3.31:1 — peer-calibrated narrow-pass.

### Industry-comparison archive
- ParaView: CSS-var tokens → PALETTE_LIGHT/DARK; `ambient=0.1, diffuse=0.8` (validates UPL-9); dark-chip swatch; "View > Theme submenu" IA; separate ±axis glyphs (not rotated=180); "Display" tab separates display from quality.
- Blender 4.x: checkable QPushButton for toggles; uniform icon footprint (ALL or NONE in group); noun-first labels; destructive icon = same hue family as text.
- 3D Slicer: per-job status widget for lagging-label fix; CLI state machine (Idle→Scheduled→Running→Completed).
- ParaView status-bar progress + Abort = canonical follow-on for text-only "Computing…". QThreadPool does NOT cancel running QRunnable — needs cooperative flag.
- MeshLab "Render Mode" = display-pipeline only (no regeneration toggles). "Bounding Box" qualifies measurements; bare "size:" is a regression.

### First-launch / section-9 regressions (recurring)
- Fast check: does new method call `_render_current` or touch `variety_combo`/`subtype_combo`? No → section-9.3 clean.
- `set_default_color` in `_on_variety_changed` is NOT on the render path.
- Actor color not pushed on theme switch: `_on_theme_changed` → `set_default_color` but NOT `apply_to_actor`. Flag whenever milestone diverges variety colors by theme.

### QSS platform traps
- `text-align: left` silently ignored on macOS Aqua unless `background:` also set (forces QSS paint mode). Fast check: any `QPushButton` QSS rule with `text-align` must have `background:`.
- `&&` escapes literal `&` in QGroupBox titles to suppress unintended Alt-key accelerator binding.

### Misc patterns
- `QSize(16,16)` is a plain constructor — AI-11 does not apply (AI-11 = Qt.* / QSizePolicy.* enum symbols only).
- Ghost-button unchecked transparent = Material Design web convention, NOT desktop sci-viz norm. Flag MEDIUM.
- Border-width change (1px → 2px) in checked QSS = 1px content shift. Compensate padding or use `outline:`. Always LOW.
- setIconSize must follow setIcon on every new QPushButton with an icon — HIGH if missing (platform-dependent clipping).
- `refresh_icons` must have 3 symmetric call sites: `__init__`, `_on_theme_changed`, `_apply_system_theme`.
- ParaView OSPRay "OSPRay rendering..." label = canonical model for attributing quality-toggle overhead in status bar.
- Performance claims in tooltips: relative % is hardware-independent; absolute ms is dev-machine-specific — cite both with caveat.

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

## realtime-variety-render-e4b (CAND-3 coarse-preview LOD) — 2026-05-22

### Token-discipline near-misses
- No short-hex, no shorthand-enum, no new QColor, no new processEvents in the diff. Pure dispatcher / status-bar f-string change. All four AI-9/AI-11/AI-12/AI-13 axes dispose in one sentence. AI-9 check: the new `coarse` kwarg is DATA — not a new locking primitive — and the existing `_computing` single-flight latch is unchanged.

### The "Computing… vs Preview" flicker — the dispatch/result message-pair asymmetry
- When a result-time slot BRANCHES on `result.is_coarse` to choose between two visually-distinct status-bar labels, the corresponding DISPATCH-time `showMessage` MUST also branch — otherwise the user sees rapid flicker between the two label styles during a drag burst (each dispatch shows the un-attributed "Computing…" and each result shows the attributed "Preview — …"). For e4b at ~25 Hz this is a real flicker that undercuts the AI-15 disclosure the result-time branch was built to provide. Fast check: any milestone that adds a result-time `if result.<flag>: showMessage(<flag-specific>)` branch should have an equivalent dispatch-time `f"Computing{flag_label} {label}…"` interpolation. The busy-branch `showMessage` at the in-flight queue-latest path is a THIRD copy that needs the same treatment — it currently reads `self._current_surface.label` but not the queued coarse-vs-full mode (which is now stored in `_pending_is_coarse`).
- Flag this kind of asymmetry as HIGH (math-honesty consequence, not just paper-cut) when the user-visible label drives an AI invariant disclosure.

### `True` as AND-identity is mathematically correct but doc-confusing for booleans
- e4b's `_pending_is_coarse = True` init relies on `True` being the boolean-AND identity element, then explains it in a 6-line truth-table comment. Mathematically correct, but the sister field `_pending_reset_camera = False` (OR-identity) is *better* because `False` reads naturally as "no signal pending." A future maintainer skimming `_pending_is_coarse = True` (at init) may read it as "the pending render IS coarse" rather than "no pending render yet."
- Flag whenever a boolean uses `True` as a "no signal" sentinel (AND-identity polarity). Suggest either (a) rename to the OR-natural polarity (`_pending_render_is_full = False`) or (b) use `Optional[bool]` with `None` as the explicit "no signal" sentinel. Pattern repeats whenever a queue-latest flag is added with AND-promote semantics.

### Status-bar overflow recurring risk extended to coarse-path warning composites
- The Dwork conifold 175-char RuntimeWarning + the 55-char Preview badge + the " | " separator = ~233 chars, well over QStatusBar's ~120-char visible window. The full-result equivalent dodges this by hoisting `bbox_suffix` to the LEFT of the pipe (status-bar-bbox-2026q2-e1 lesson); the coarse-result branch suppresses bbox (correctly per AI-15) so the equivalent hoist must move the BADGE to the left of the pipe. Same recurring pattern as the e1/e2 bbox-overflow issue.
- Fix-side preference: shortening the source RuntimeWarning text is cleaner than rearranging the composite — runtime warnings on the worker thread should be ≤80 chars per peer convention.

### AI-15 disclosure is structural, not just transient
- A status-bar Preview badge satisfies AI-15 ONLY for status-bar-watching users. A user who hovers the subtype combo box reads SUBTYPE_TOOLTIPS but never sees the badge. New AI-15 line 170 says "A new render-mode candidate that lacks a comparable user-visible fidelity disclosure is an AI-15 conflict" — *comparable* covers tooltip-level disclosure that the variety is opt-in for coarse-preview LOD. Always flag the absence of a per-surface tooltip mention of a new render mode as MEDIUM.
- Mathematica `Manipulate[ControlActive[...]]` puts the disclosure in the tooltip of its mode toggle, not just in a transient status-bar line — the peer pattern.

### Industry-comparison concrete findings
- **Mathematica `Manipulate[..., ControlActive[low_res, full]]`** is the canonical peer for two-pass coarse-vs-full UX (since v6.0, 2007). Indicator location: small "computing..." shimmer at bottom-right of the CANVAS, NOT in a status-bar text label. AVC's status-bar approach is a deliberate divergence.
- **ParaView "Interactive Render" / "Still Render"** explicit toggle for the same trade-off. Indicator: small label at bottom-right of the RENDER VIEW. Also canvas-adjacent, not status-bar.
- Both peers locate the indicator AT THE RENDER VIEW. AVC's status-bar location is defensible BECAUSE the status bar already carries the load-bearing render metadata (verts/faces/bbox/ms) — the eye is trained there — but the divergence should be documented in CONTEXT.md §8.19.
- ParaView's "Interactive Render" status string stays "Interactive (preview)" CONTINUOUSLY across both phases of the same drag (dispatch + result both say "preview"). AVC's e4b currently flickers between "Computing X…" and "Preview — X — N ms." Fix is the HIGH-1 finding.

### Dead "in-flight mirror" fields are a smell
- `_inflight_is_coarse` is set at dispatch but never read (the slot uses `result.is_coarse`). Its docstring claims "defensive symmetry with the rest of the `_inflight_*` family" but that family DOES have consumers (`_inflight_surface`, `_inflight_params`, `_inflight_reset_camera`, `_inflight_hq_label` are all read in the slot). Pure dead code. Fast check on any new `_inflight_*` field: grep for its NAME, not its definition site — if the only hits are init + set, it's dead.

### Scope discipline
- Pure dispatcher / status-bar branch + math/worker plumbing changes — `appearance_panel.py`, `view_panel.py`, `parameters_panel.py`, `styles.py` are byte-identical. `git diff --stat 4db5c12..601612c -- <panel_files>` returning empty IS the canonical panel-scope check; run it first. A milestone with no panel-widget diff legitimately produces a critique focused on dispatcher + status-bar f-strings (axes 1-4, 7-9, 11 dispose in one sentence as "out-of-panel-scope" or "no relevant change").
- `render_worker.py` and `surfaces.py` are worker / math, not panel surfaces — same dispose pattern as e4 (CAND-4) for `render_worker.py`.

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

---

## qsettings-persistence-v1-2026q3-e1 — 2026-05-23

### Token-discipline near-misses
- `Qt.AA_ShareOpenGLContexts` (shorthand, not `Qt.ApplicationAttribute.AA_ShareOpenGLContexts`) is at `app.py:1323` — pre-existing, NOT introduced by this milestone. Fast dispose: grep the BASE commit for a shorthand before filing it as a finding. A shorthand in the diff's context lines but NOT in the `+` lines is not a new violation.
- `QSettings.value(..., type=int)` and `type=str` use Python built-in types, not Qt enums. AI-11 does not apply. Fast check: AI-11 targets `Qt.*` / `QSizePolicy.*` enum symbols, not Python `type=` keyword arguments.

### First-launch / section-9 regressions
- Persistence milestones have an inverted first-launch risk: the danger is NOT that code fires at first launch but that it fires CORRECTLY on SECOND launch. Trace both paths: (a) schema_version=0 → no-op (verified), (b) schema_version=1 + valid variety → render trigger (verified). Both must be checked explicitly.
- `_restore_settings()` inside `__init__` (not `showEvent`) keeps intermediate status-bar messages invisible since the window isn't shown yet. This is a forward-compat note: if ever moved to `showEvent`, the message sequence degrades visibly.

### Industry-comparison notes
- VS Code workspace restore: missing extension shows a notification banner, not a silent fallback. Applied directly to MEDIUM-2 (removed-variety silent fallback). VS Code / ParaView both use silent fallback only for invisible state; for visible session items they surface a message.
- Blender, VS Code, ParaView all wrap their settings-write in teardown (quit handler) with a guard; the pattern is near-universal. The `try/except Exception: pass` in `closeEvent` around `_save_settings` is the canonical form — not a code smell.

### closeEvent save-before-teardown pattern
- Any `settings.sync()` / `saveGeometry()` call at the TOP of `closeEvent` MUST be in a `try/except` if ANYTHING below it is non-optional teardown (signal disconnect, thread drain, plotter close). Unguarded settings save = potential teardown abort. Flag as HIGH whenever the teardown chain below the save includes thread-pool drain or VTK context close.
