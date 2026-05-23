# lessons -- milestone-frontend-ux-critic

## DEEP ARCHIVE — Evergreen rules (compacted 2026-05-23)

- **AI-13 fast gate:** "does this color arg reach `pv.Plotter.add_mesh`?" QPainter / QSS is NOT PyVista.
- **Fast token dispose:** diff adds no QColor / Qt.AlignmentFlag / processEvents / pv.add_mesh() → dispose AI-9/AI-11/AI-12/AI-13 in one sentence.
- **Status-bar overflow:** empirical clip ~120 chars; hoist load-bearing tokens LEFT of any `|` separator. Cannot safely append a note to a >60-char base message without measuring combined length. Hoist-before-CTA fix: put new token before `"Now choose a model."` not after.
- **Append-to-long-base overflow trap:** base message 100+ chars + suffix 60+ chars = 160+ total, clipping the suffix. Measure base length first; if base > 60 chars, any suffix > 60 will overflow. The fallback/generic branch is usually short enough; the named-variety branches (CY3/Fano/Enriques) are the overflow risk.
- **Early-return-before-try trap:** any `return` above `try/finally` skips cursor restore + `_computing` clear → soft-freeze. Flag MEDIUM.
- **First-launch fast check:** does new method call `_render_current` or touch `variety_combo`/`subtype_combo`? No → section-9.3 clean.
- **QSS `text-align` on macOS Aqua:** silently ignored unless `background:` also set. Flag any QPushButton QSS `text-align` without `background:`.
- **`&&` in QGroupBox titles:** escapes literal `&` to suppress Alt-key accelerator binding.
- **`QSize(16,16)` is a plain constructor** — AI-11 does not apply. AI-11 = `Qt.*` / `QSizePolicy.*` enum symbols only.
- **setIconSize must follow setIcon** on every new QPushButton with icon — HIGH if missing (platform clipping).
- **`refresh_icons` must have 3 symmetric call sites:** `__init__`, `_on_theme_changed`, `_apply_system_theme`.
- **Group-label precision:** when a QGroupBox gains a new child categorically different from its label, flag MEDIUM.
- **Pre-existing shorthand in context lines** (not `+` lines) is NOT a new AI-11 violation. Grep BASE commit before filing.
- **Persistence milestones:** check BOTH first-launch path (schema_version=0 → no-op) AND second-launch path (schema_version=1 + valid variety → render trigger).
- **Disabled-widget tooltip on macOS:** `AA_EnableToolTipsOnDisabledWidgets` at `app.py:1675` is the canonical fix. Confirm it's set before filing "tooltip invisible on greyed button" findings.
- **Dead `_inflight_*` fields:** grep for the NAME; if only hits are init + set, it's dead code. Always LOW.
- **Bool sentinel polarity:** `_pending_is_coarse = True` (AND-identity init) reads as "IS coarse" to maintainers. Flag whenever True is used as "no signal" sentinel. Prefer `Optional[bool] = None` or rename to OR-natural polarity.
- **Dual-handler double-toast check:** when two event handlers (variety + subtype) both fire toasts, verify the first handler's state-clear prevents the second from double-firing. If handler A calls `set_eligible(False)` (which clears `_hq_smoothing`), handler B reads `_prior_hq = False` → silent. No double toast. Always trace the state-clear chain.
- **ParaView status-bar discipline:** ParaView never composes a multi-clause >120-char message into a single status bar string. Peer convention = single-concept messages that fit the visible band. Use this as the HIGH-severity anchor for overflow findings on feature-purpose messages (not cosmetic ones).
- **VS Code notification vs status-bar:** VS Code uses floating banners for "setting X auto-disabled". AVC has no notification framework; `showMessage` is correct. This distinction prevents an over-engineered "add a notification system" recommendation.

---

## qtawesome-icons + status-bar-bbox — 2026-05-22 (compacted)

- **Ghost-button unchecked state:** Blender 4.x / 3D Slicer / ParaView all give off-state toggles visible chrome. Transparent-unchecked is a Material Design web convention, not desktop sci-viz. Flag as MEDIUM.
- **Border-width jitter:** 1px→2px checked QSS causes content shift. Fix: compensate padding by -1px or use `outline:`. Always LOW.
- **Status-bar measurement-type signal:** renaming `bbox:` → `size:` drops type qualifier. MeshLab "Bounding Box", ParaView "Bounds", Blender "Dimensions". Fast flag: renamed status-bar token loses MEASUREMENT TYPE signal.
- `BG_TOGGLE_CHECKED` flows into QSS only, NOT PyVista — AI-13 clear. WCAG: text-on-fill contrast (9.89:1 / 10.20:1), not fill-vs-ground when border carries the non-text obligation.

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

## realtime-variety-render-e4b (CAND-3 coarse-preview LOD) — 2026-05-22 (compacted)

- Token-discipline: `coarse` kwarg is DATA not a locking primitive. AI-9/AI-11/AI-12/AI-13 clear in one sentence.
- **Dispatch/result branch asymmetry (HIGH-1 here):** when `result.is_coarse` drives a visually-distinct status-bar label, BOTH dispatch-time AND in-flight busy-branch `showMessage` must match — otherwise ~25 Hz drag burst flickers between "Computing X…" and "Preview — X — NNN ms". Fast check: any `if result.<flag>: showMessage(<flag-specific>)` must have an equivalent dispatch-time interpolation.
- **Coarse overflow composite:** Dwork 175-char RuntimeWarning + 55-char Preview badge + " | " ≈ 233 chars. Hoist badge LEFT of pipe, same as bbox hoist pattern.
- **Panel scope check:** `git diff --stat <range> -- appearance_panel.py view_panel.py parameters_panel.py styles.py` returning empty = legitimate empty-panel-scope critique. Axes 1–4, 7–9, 11 dispose in one sentence.

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

---

## mesh-export-stl-obj-ply-2026q3-e1 — 2026-05-23

### Token-discipline near-misses
- No short-hex, no shorthand-enum, no processEvents, no pv.add_mesh() color args. `QKeySequence("Ctrl+E")` is the string form — Qt documents this as the portable cross-platform shortcut syntax; AI-11 does NOT apply (AI-11 targets `Qt.*` / `QSizePolicy.*` enum symbols, not `QKeySequence` string constructors). Fast dispose: entire diff is a menu + handler, all four AI-9/AI-11/AI-12/AI-13 axes clear in one sentence.

### File-dialog _selected_filter unused — recurring trap
- `QFileDialog.getSaveFileName` returns `(path, selected_filter)`. Assigning to `_selected_filter` (with underscore = "unused") and NOT reading it is the canonical missed-auto-append bug. On macOS/Linux, Qt does NOT auto-append extensions from the selected filter; on Windows it does. The fix is `re.search(r'\(\*(\.\w+)\)', selected_filter)` to get the extension and append it if path lacks one. Fast check: any `getSaveFileName` call site — look for whether the second return value is read. If it's `_, selected_filter = ...` that's a warning sign; if it's `path, _selected_filter = ...` that's the exact pattern.

### Coarse-LOD × export action enable — cross-milestone interaction
- `_on_mesh_ready` enables the export action in the success branch, unconditionally, BEFORE the `if result.is_coarse: return` branch. This is the pattern: a feature added in milestone N interacts with a coarse-LOD path added in milestone N-1, and the interaction is not analyzed in the new milestone's AI-15 scan. Fast check: any `setEnabled(True)` on an export-class action inside `_on_mesh_ready` — verify it gates on `not result.is_coarse`.

### Internal tag jargon in user-facing tooltips
- "AI-15: the mathematical caveats..." leaked an internal invariant label into a user-facing QAction tooltip. The fix is trivial ("Note:"), but the pattern recurs whenever a developer adds an app-invariants.md reference as UI copy. Fast flag: grep tooltip strings for "AI-[0-9]" — any hit is a jargon leak.

### Industry-comparison concrete findings (export)
- **MeshLab "File > Export Mesh As"** uses `Ctrl+Shift+E` (not `Ctrl+E`). GIMP and Inkscape also use `Ctrl+Shift+E` for "Export As". ParaView uses `Ctrl+S` for "Save Data" (closest equivalent). The tri-tool consensus on `Ctrl+Shift+E` makes `Ctrl+E` an atypical choice, though not conflicting within AVC.
- **ParaView "Save Data"** shows only the filename in the status bar after save ("Saved mesh.stl"), not the full path. This is the canonical pattern that avoids the deep-path overflow. Always recommend `os.path.basename(path)` for export success messages.
- **MeshLab format filter:** uses bare "Stereolithography (*.stl)" format without the "files" qualifier. Qt docs use "Images (*.png)" — noun-first without "files". Always recommend removing the redundant "files" word from filter strings.

### Status-bar overflow for export success message
- `"Mesh exported: {path}"` is the AVC export success pattern. A deep Mac iCloud Drive path reaches 131–165 chars, over the 120-char clip limit. The load-bearing token "Mesh exported:" is at the LEFT (first ~15 chars), so the user knows the export succeeded even when the path clips. But for confirmability, use `os.path.basename(path)`. This is the same overflow pattern as the `f"⚠ {warning} | {base_msg}"` lesson, now applied to file-operation success messages.

### EN DASH in sanitised filenames — VTK Windows path risk
- `"Dwork pencil (Calabi–Yau) [Fig. 4]"` → `"Dwork_pencil_(Calabi–Yau)_Fig._4.stl"`. The U+2013 EN DASH passes sanitisation. VTK's legacy C FILE* writer on Windows may fail with non-ASCII filenames. Fast check: grep `surface.label` entries in `surfaces.py` for non-ASCII chars; any that reach default-filename logic need Unicode-to-ASCII sanitisation.

---

## hq-disable-toast-2026q3-e1 — 2026-05-23

### Token-discipline near-misses
- Pure `showMessage` + bool-read diff: no QColor literals, no Qt.Align* shorthands, no processEvents. All four AI-9/AI-11/AI-12/AI-13 axes clear in one sentence. Fast dispose: if the entire diff is `_prior_hq = bool_property` + conditional `showMessage` strings with no renderer/color/enum additions, all axes are trivially clean.
- `f"…{_hq_note}"` in a status-bar f-string is a Python interpolation, NOT a hex color or Qt enum. AI-13 gate: "does this reach PyVista color=?" — answer is no. AI-11 gate: "is this a Qt.* / QSizePolicy.* enum call?" — no, it's a str. Both clear.

### Status-bar overflow — append-to-long-base pattern
- When a short suffix is appended to an already-long (~100 char) base message, the COMBINED length easily exceeds the 120-char clip band even if the suffix alone is short (68 chars here). Fast check: measure BASE message length first, then add suffix length. If base > 60 chars, any suffix > 60 chars will overflow. The lesson: **you cannot safely append a UX-disclosure note to a pre-existing > 60-char status bar message without measuring the combined length.**
- The hoist-before-CTA fix pattern: if a message is `"Noun — description.  Now choose a model."`, rewrite as `"Noun — description.{note}  Now choose a model."` so the new token appears before the generic call-to-action rather than after. This keeps the note in the visible band while preserving variety context before and CTA after.
- The fallback/generic branch (`"Variety: K3. Now choose a model."` = 40 chars) can safely absorb the 68-char note; only the CY3/Fano/Enriques branches (100-106 chars) cannot.

### Industry-comparison concrete findings
- **ParaView status-bar discipline:** ParaView never composes a multi-clause >120-char message into a single status bar string. It either truncates deliberately (summary-only) or uses a two-line status area. The 174-char variety+note composite is outside all peer conventions. This peer reference directly justified HIGH severity for the overflow finding.
- **VS Code notification vs status-bar:** VS Code uses floating notification banners for "setting X was auto-disabled" messages (a dedicated notification framework). AVC has no notification framework — status bar is the only ephemeral channel. Using `showMessage` is the correct architectural choice for this scope. This distinction prevents an over-engineered "add a notification system" recommendation.

### First-launch / section-9 regressions
- Clean by fast check: new code paths (`_prior_hq` capture + conditional `showMessage`) contain no calls to `_render_current`, `variety_combo`, or `subtype_combo`. Section 9.3 safe.
- The dual-call-site pattern (variety + subtype handlers) does NOT cause double-toasting: the variety handler clears `_hq_smoothing` via `set_hq_smoothing_eligible(False)`, so when `_on_subtype_changed` fires next, `_prior_hq = False` and the subtype guard stays silent. This is a recurring pattern to verify: "does handler A's state-clear prevent handler B's toast from double-firing?"
