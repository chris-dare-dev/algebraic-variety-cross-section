# lessons -- milestone-frontend-ux-critic

## DEEP ARCHIVE — Evergreen rules (compacted 2026-05-23)

- **AI-13 fast gate:** "does this color arg reach `pv.Plotter.add_mesh`?" QPainter / QSS is NOT PyVista.
- **Fast token dispose:** diff adds no QColor / Qt.AlignmentFlag / processEvents / pv.add_mesh() → dispose AI-9/AI-11/AI-12/AI-13 in one sentence.
- **Status-bar overflow:** empirical clip ~120 chars; hoist load-bearing tokens LEFT of any `|` separator. Cannot safely append a note to a >60-char base message without measuring combined length. Hoist-before-CTA fix: put new token before `"Now choose a model."` not after.
- **Append-to-long-base overflow trap:** base >60 chars + suffix >60 chars = overflow risk. The named-variety branches (CY3/Fano/Enriques) are the overflow risk; generic fallback branches are usually safe.
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
- **Bool sentinel polarity:** `_pending_is_coarse = True` (AND-identity init) reads as "IS coarse" to maintainers. Flag whenever True is used as "no signal" sentinel.
- **Dual-handler double-toast check:** verify first handler's state-clear prevents the second from double-firing. Trace the state-clear chain.
- **ParaView status-bar discipline:** ParaView never composes a multi-clause >120-char message into a single status bar string. High-severity anchor for overflow findings.
- **VS Code notification vs status-bar:** VS Code uses floating banners for "setting X auto-disabled". AVC has no notification framework; `showMessage` is correct.
- **Ghost-button unchecked state:** Blender 4.x / 3D Slicer / ParaView all give off-state toggles visible chrome. Flag MEDIUM.
- **Border-width jitter:** 1px→2px checked QSS causes content shift. Fix: compensate padding by -1px or use `outline:`. Always LOW.
- **Status-bar measurement-type signal:** renamed status-bar token loses MEASUREMENT TYPE signal. Check renaming `bbox:` → `size:` type.
- **`BG_TOGGLE_CHECKED` flows into QSS only** — AI-13 clear. WCAG: text-on-fill contrast, not fill-vs-ground when border carries the non-text obligation.
- **Qt macOS disabled-widget tooltip gap:** `QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableToolTipsOnDisabledWidgets, True)` in `main()`.
- **ParaView OSPRay status label:** canonical model for attributing render-time overhead to a quality toggle. Flag absence of mode indicator in computing/success status as MEDIUM.
- **Blender 4.x icon uniformity:** icon on ALL or NONE in same group. Plain-text button between two icon+text buttons = alignment fracture. Flag MEDIUM.
- **Performance-disclosure precision:** relative overhead (%) is hardware-independent; absolute (ms) is hardware-specific. Flag absolute-ms claims in tooltips as HIGH if dev-machine-only.
- **State-reset-on-navigate UX:** unconditional `setChecked(False)` with no status-bar feedback = LOW when the user cannot observe the reset happened.
- **Dispatch/result branch asymmetry:** when `result.is_coarse` drives a visually-distinct status-bar label, BOTH dispatch-time AND in-flight busy-branch `showMessage` must match.
- **Panel scope check:** `git diff --stat <range> -- appearance_panel.py view_panel.py parameters_panel.py styles.py` returning empty = legitimate empty-panel-scope critique.
- **MeshLab "Render Mode":** display-pipeline only — NOT a valid precedent for groups containing mesh-regeneration toggles.
- **ParaView 5.13** separates "Representation" (display) from "Advanced" (quality/generation) — concrete peer model for splitting mixed-category groups.
- **QSS `text-align` canonical fix:** `background: transparent` in the rule forces full-QSS-paint mode and bypasses native Aqua renderer. Always required alongside `text-align`.
- **Group-label precision pattern:** enumerate group children, classify each as label-category-compliant or outlier. One outlier at a functionally different latency class = MEDIUM.
- **MeshLab "TwoStep Smooth" / Blender "Corrective Smooth":** noun-first labeling in all sci-viz peers. Adjective-noun compounds are the odd pattern.
- **Qt tooltip verb convention:** Imperative or noun-phrase is Qt/Apple HIG standard. Third-person singular ("Applies…") = MEDIUM.
- **Status-bar suffix length math:** always count full rendered string length against 120-char empirical clip limit.
- **Dual busy indicator:** Blender 4.x and ParaView both use cursor (pointer-proximity) + spinner (peripheral vision). NOT redundant — flag removal as regression.
- **`setIconSize(QSize(16,16))` gap pattern:** any new QPushButton with icon must have companion `setIconSize` call. HIGH if missing.
- **VS Code spinner tooltip in hidden state:** `setToolTip` on `setEnabled(False)` widget fires even when `setVisible(False)`. Flag misleading idle-state tooltip.
- **`closeEvent` save-before-teardown:** `settings.sync()` at TOP of `closeEvent` must be in `try/except` if teardown below is non-optional (thread drain, VTK close). Flag as HIGH.
- **`QKeySequence("Ctrl+E")` string form:** AI-11 does NOT apply — AI-11 targets `Qt.*`/`QSizePolicy.*` enum symbols, not `QKeySequence` string constructors.
- **`getSaveFileName` `_selected_filter` unused:** canonical missed-auto-append bug. On macOS/Linux, Qt does NOT auto-append extensions. Fix: read the selected_filter return and append extension if path lacks one.
- **Coarse-LOD × export action enable:** `setEnabled(True)` on export action in `_on_mesh_ready` must gate on `not result.is_coarse`.
- **Internal tag jargon in tooltips:** grep tooltip strings for "AI-[0-9]" — any hit is a jargon leak.
- **MeshLab export uses `Ctrl+Shift+E`** (not `Ctrl+E`). GIMP/Inkscape also use `Ctrl+Shift+E`. AVC `Ctrl+E` is atypical but not conflicting.
- **ParaView "Save Data":** shows only filename in status bar after save — canonical pattern to avoid deep-path overflow. Use `os.path.basename(path)`.
- **EN DASH in sanitised filenames:** `surface.label` may contain U+2013 EN DASH. VTK legacy C FILE* writer on Windows may fail. Flag non-ASCII chars in default filenames.
- **`&&` escape in QGroupBox header:** any future compound `QGroupBox` header with `&` — verify `&&` used.
- **Single-noun vs compound-header rhythm:** when all peer dock headers are single-noun and one gains a compound label, flag MEDIUM (rhythm break). Check peer headers in the SAME dock.
- **Spinner rebind QTimer accumulation:** `qta.Spin(widget)` creates `QTimer(parent_widget)` lazily. N theme-swaps leave N QTimers firing at 10ms. Visually correct (latest QIcon always shows); real-world impact near-zero. Document at all 3 rebind sites.
- **QSettings shorthand enum pre-check:** grep BASE commit before filing `Qt.AA_ShareOpenGLContexts` as AI-11 — it's pre-existing.
- **hoist-before-CTA fix pattern:** if message is `"Noun — desc. Now choose a model."`, new token goes BEFORE the CTA not after.
- **Dual-call-site toast analysis:** dual variety+subtype handlers — trace state-clear chain: variety handler clears `_hq_smoothing`, so subtype handler sees `_prior_hq = False` → silent.

---

## qsettings-persistence-v1-2026q3-e1 — 2026-05-23

- **Persistence milestones inverted risk:** danger is NOT code firing at first launch but CORRECTLY on SECOND launch. Trace both paths: (a) schema_version=0 → no-op, (b) schema_version=1 + valid variety → render trigger.
- `_restore_settings()` inside `__init__` (not `showEvent`) keeps intermediate status-bar messages invisible — forward-compat note if ever moved to `showEvent`.
- VS Code workspace restore: missing extension shows notification banner, not silent fallback. Applied to MEDIUM-2 (removed-variety silent fallback).

---

## mesh-export-stl-obj-ply-2026q3-e1 — 2026-05-23

- **File-dialog `_selected_filter` unused:** `getSaveFileName` returns `(path, selected_filter)`. If second return is `_selected_filter` (underscore = unused) and NOT read → missed-auto-append bug on macOS/Linux.
- **Coarse-LOD × export cross-milestone interaction:** `setEnabled(True)` on export action in success branch must gate on `not result.is_coarse`. Pattern: feature in milestone N interacts with coarse-LOD from milestone N-1.
- **EN DASH in `surface.label` filenames:** U+2013 passes sanitisation but VTK C FILE* writer on Windows may fail with non-ASCII.
- **Status-bar overflow for export success:** `"Mesh exported: {path}"` with deep iCloud Drive path = 131–165 chars. Use `os.path.basename(path)`.

---

## cleanup-deferred-findings-2026q3-e1 — 2026-05-23

### Token-discipline near-misses
- No short-hex, no shorthand-enum, no processEvents, no pv.add_mesh() color args. All four axes clear in one sentence.
- **BORDER_SWATCH theme-split fast gate:** when a palette token is split per-theme, measure the NEW value against BOTH adjacent surfaces in EACH theme. `#333333` on dark `BG_PANEL` = 1.21:1 (would collapse border) — the split is correct.
- **Dark-theme fill-vs-border WCAG 1.4.11:** `#888888` in dark mode fails vs variety fills (1.35–1.67:1), but fills achieve 5.83–7.20:1 vs dark `BG_PANEL` — component identity satisfied via fill contrast alone. Boundary rule requires 3:1 against adjacent surfaces; when fill provides it, border is optional reinforcement.

### Industry-comparison concrete findings
- **QMenu::item:checked omission (MEDIUM-1):** any new `QMenu` QSS block containing checkable actions requires `QMenu::item:checked` or `QMenu::indicator:checked` rule. Qt's `PE_IndicatorMenuCheckMark` on a custom-background QMenu may produce invisible indicator on macOS dark theme. ParaView and GIMP both provide explicit checked-state styling.
- **Apple HIG menu-item height (LOW-1):** macOS standard menu items at 13pt = ~29px. `QMenu::item { padding: 4px; }` yields ~25px. 4px deficit is noticeable adjacent to native macOS menus. Comment intentional compact density if deliberate.

### Debounce precision in tooltip copy
- `"every drag tick"` in `_LOD_NOTE_HANSON` means "80ms debounced fire", NOT mouse-move granularity. Whenever a tooltip says "every X tick" in an app with a visible debounce interval, audit the language matches actual firing frequency. Prefer "at each drag step (~80 ms)" or "at each debounced drag event."

### Single-source-of-truth for tooltip strings
- `_LOD_NOTE_*` constants in `surfaces.py` serve SUBTYPE_TOOLTIPS. `VARIETY_TOOLTIPS` uses independent prose with the same semantic intent. A future wording fix requires two edits. Pattern: when a milestone adds module-level string constants as tooltip suffix templates, check whether existing free-prose in related dicts duplicates the semantic — if yes, wire to the same constant or flag as MEDIUM.
