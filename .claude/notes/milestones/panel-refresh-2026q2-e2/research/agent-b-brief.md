# Research Brief — panel-refresh-2026q2-e2 (Agent B)

**Lens:** External patterns + downstream API implications
**Date:** 2026-05-20
**Milestone:** UPL-1 — Extract scattered hex literals into `PALETTE_LIGHT` dict (≥6 named tokens)

---

## 1. TL;DR

Add a `PALETTE_LIGHT: dict[str, str]` module-level dict to the existing `styles.py` (NOT a new `palette.py`); keep all existing constants as aliases that read from it; replace the four inline hex literals that do not yet flow through `styles.py` (`appearance_panel.py:74–75`, `appearance_panel.py:48`, `app.py:364,386`). The main risk is that downstream candidates UPL-4, UPL-5, and UPL-11 each need a specific API surface from this dict — get the token names right now to avoid a rename in the next sprint. The backup plan is to land the dict with the six required tokens first, then follow up with additional variety-color placeholders in the same PR after confirming downstream token names.

---

## 2. Prior art in this repo

**`styles.py` — the primary surface (all 142 lines):**
- `styles.py:22` — `COLOR_MUTED = "#5a5a5a"` — exists as a module-level constant, not in a dict.
- `styles.py:26` — `COLOR_VALUE = "#333333"` — same.
- `styles.py:29–30` — `COLOR_DOCK_HEADER_BG = "#e8edf2"`, `COLOR_DOCK_HEADER_BORDER = "#c5cdd8"`.
- `styles.py:34–36` — `COLOR_RESET_BTN_BG = "#f5e8e8"`, `COLOR_RESET_BTN_BORDER = "#d4b4b4"`, `COLOR_RESET_BTN_HOVER_BG = "#f0d0d0"`.
- `styles.py:52` — `MUTED_TEXT_STYLE` references `COLOR_MUTED` via f-string. Pattern: typography constants already reference color constants.
- `styles.py:55` — `VALUE_MONO_STYLE` references `COLOR_VALUE`.
- `styles.py:58` — `RANGE_LABEL_STYLE` references `COLOR_MUTED`.
- `styles.py:90` — **RAW HEX in QSS:** `border: 1px solid #d0d0d0` (QGroupBox border — not yet tokenized).
- `styles.py:110` — **RAW HEX in QSS:** `color: #5a3a3a` (reset-btn danger text — not yet tokenized).
- `styles.py:116–118` — **RAW HEX in QSS:** `#f5f5f5`, `#d8d8d8`, `#aaaaaa` (disabled-state colors — not yet tokenized).
- `styles.py:123–127` — **RAW HEX in QSS:** `#b0bec5`, `#e8f0f5` (reset-camera btn — not yet tokenized).
- `styles.py:132` — **RAW HEX in QSS:** `#5b9bd5` (focus ring — not yet tokenized; this is `FOCUS_RING`).
- `styles.py:139` — `color: {COLOR_MUTED}` — already tokenized.
- `APP_STYLESHEET` is an f-string that substitutes from module-level color constants. Pattern already established; the refactor extends it, does not break it.

**`appearance_panel.py` — the secondary surface:**
- `appearance_panel.py:48` — **SHORT HEX (AI-13 adjacency):** `border: 1px solid #888;` in `_apply_swatch_color()`. This is in a Qt stylesheet context (acceptable to Qt) but flagged as UPL-21's "AI-13-adjacency" finding. Milestone brief explicitly requires resolving it.
- `appearance_panel.py:74` — `self._surface_color = QColor("#b0c4de")` — the default surface color (lightsteelblue). This is NOT in `styles.py` at all. Must flow through the new palette as `SURFACE_DEFAULT`.
- `appearance_panel.py:75` — `self._bg_color = QColor("#2f2f2f")` — the default viewport background. Must flow through palette as `BG_VIEWPORT`.
- `appearance_panel.py:32` — imports only `VALUE_MONO_STYLE` from styles. Will need to import `PALETTE_LIGHT` (or specific named tokens) after this milestone.

**`app.py` — two hex literals NOT in styles:**
- `app.py:364` — `color="#888888"` — passed directly to `plotter.add_mesh()` for domain-clip wireframe overlay. This flows into PyVista (AI-13 applies — 6-digit, already compliant, but not tokenized).
- `app.py:386` — `color="#888888"` — same pattern, second overlay mesh. Both should become `PALETTE_LIGHT["OVERLAY_WIRE"]`.
- `app.py:144` — comment references the background-flash fix from UPL-3 (already landed as dc328d7). The background is now set from `self._bg_color` in `appearance_panel.py:75`.

**Prior milestone e1 (UPL-3):**
- Commit `dc328d7` moved the background init to `MainWindow.__init__` via `appearance_panel.apply_background()`. The background color value lives at `appearance_panel.py:75` as `"#2f2f2f"`. This is the `BG_VIEWPORT` token.

---

## 3. External sources reviewed

| Source | URL | Key finding | Relevance |
|---|---|---|---|
| PyQtDarkTheme-fork (PyPI / docs) | https://pypi.org/project/PyQtDarkTheme-fork/ | Uses a `custom_colors` dict with semantic keys like `"primary"`, `"[dark]"`, `"[light]"`. QSS substitution through template strings. No separate palette module — colors live inside the library's own dict, not an app-level file. | Reference for dark vs light token separation convention. Shows semantic-role naming beats hex-suffix naming (e.g. `"primary"` not `"primary_hex"`). |
| Qt QPalette ColorRole enum | https://doc.qt.io/qtforpython-6/PySide6/QtGui/QPalette.html | Canonical semantic roles: `Window`, `WindowText`, `Button`, `ButtonText`, `Base`, `AlternateBase`, `Highlight`, `HighlightedText`, `Text`, `BrightText`, `Link`, `LinkVisited`, `ToolTipBase`, `ToolTipText`. These are widget-state-aware (Active/Inactive/Disabled groups). | Vocabulary source for token names. `Window` ≈ `BG_PANEL`, `Base` ≈ `BG_VIEWPORT` (input area), `Text` ≈ `TEXT_VALUE`, `WindowText` ≈ `TEXT_MUTED`. AVC doesn't subclass QPalette but the names are industry-standard. |
| qt-material (GitHub) | https://github.com/UN-GCPDS/qt-material | Android Material XML format: 7 named tokens (`primaryColor`, `primaryLightColor`, `secondaryColor`, `secondaryLightColor`, `secondaryDarkColor`, `primaryTextColor`, `secondaryTextColor`). Python extra dict uses functional role names (`danger`, `warning`, `success`). MIT license. | Shows that scientific/viz apps favor functional-role names over CSS-variable names. The `secondary` slot is the background; `primary` is the accent — maps loosely to AVC's `BG_PANEL` / `FOCUS_RING`. |
| napari theming system | https://napari.org/dev/gallery/new_theme.html | Class-based theme with named attributes: `background`, `foreground`, `primary`, `icon`, `current`, `font_size`. Structurally identical between light and dark themes — only values differ. Theme registered via `register_theme(name, obj, 'custom')`. | Confirms that leading scientific-viz Qt apps use semantic role names (not CSS-hex-variable names). Also confirms same token structure for light/dark — AVC's downstream UPL-4 can add `PALETTE_DARK` with identical keys. |
| ParaView color palette | https://docs.paraview.org/en/latest/Tutorials/ClassroomTutorials/beginningColorMapsAndPalettes.html | Palette categories: `Surface`, `Foreground`, `Edges`, `Background`, `Text`, `Selection`. `LoadPalette()` accepts named presets (`WarmGrayBackground`, `DarkGrayBackground`, `WhiteBackground`, etc.). Role-name convention, not hex-suffix. | Confirms that "Background" and "Foreground" are the standard large-surface token names in scientific visualization. AVC's `BG_VIEWPORT` / `BG_PANEL` are correct analogues. |
| superqt docs | https://pyapp-kit.github.io/superqt/ | `QCollapsible`, `QLabeledDoubleSlider` are available. Both are vanilla Qt widgets that inherit QSS from the application stylesheet — no custom palette/token system. They pick up whatever the `QApplication.setStyleSheet()` applies. | Confirms that UPL-4's `STYLESHEET_DARK` will automatically style downstream superqt widgets if the QSS token substitution is done at `APP_STYLESHEET` level. No superqt-specific token plumbing needed. |

---

## 4. Recommended approach

### 4.1 Where the new tokens live: `styles.py` (module-level dict)

**Verdict: `styles.py`, not a new `palette.py`.**

Tradeoffs:

| | `styles.py` (dict added) | `palette.py` (new module) |
|---|---|---|
| Import surface | Stays narrow: every consumer already imports from `styles` | Requires updating every importer to `from palette import PALETTE_LIGHT` AND updating `styles.py` to `from palette import PALETTE_LIGHT` |
| Circular import risk | None (styles has no intra-app imports) | None IF palette.py has no intra-app imports, but adds a module |
| Downstream UPL-4/5 usage | `from styles import PALETTE_LIGHT, PALETTE_DARK` — one import | Same, but one extra file to maintain |
| AI invariant fit | `styles.py` is the centralized stylesheet per CONTEXT.md §2 | Violates the "centralized in styles.py" convention without a new CONTEXT.md update |
| Real-world pattern | PyQtDarkTheme-fork: all colors in one module, not split | napari: Theme class is a separate object, but napari is much larger |

The existing architecture already establishes `styles.py` as the single source of truth. At AVC's scale (142-line styles.py, 5 modules), a separate `palette.py` adds navigation cost with no benefit. The rule `.claude/references/app-invariants.md` AI-12 already refers to `styles.py` as the centralized stylesheet. Use `styles.py`.

### 4.2 Token inventory (≥6 required, full set recommended)

The following tokens are needed by the milestone brief AND the downstream candidates:

**Tier 1 — Required by brief:**
```
BG_VIEWPORT    = "#2f2f2f"   # Viewport/plotter background (appearance_panel.py:75, AI-13: 6-digit)
BG_PANEL       = "#e8edf2"   # Dock header / panel background (styles.py:29 = COLOR_DOCK_HEADER_BG)
TEXT_VALUE     = "#333333"   # Strong readable text for value readouts (styles.py:26 = COLOR_VALUE)
TEXT_MUTED     = "#5a5a5a"   # Muted text / secondary labels (styles.py:22 = COLOR_MUTED)
FOCUS_RING     = "#5b9bd5"   # Keyboard focus ring (styles.py:132 — currently raw hex in QSS)
OVERLAY_WIRE   = "#888888"   # Domain-clip wireframe color (app.py:364,386 — currently raw hex)
```

**Tier 2 — Required by downstream UPL-4 (dark mode) — add as placeholders with light values:**
```
BG_VIEWPORT_DARK  = None     # Placeholder — UPL-4 fills: "#1e222e"
BG_PANEL_DARK     = None     # Placeholder — UPL-4 fills: "#2a2f3d"
TEXT_VALUE_DARK   = None     # Placeholder — UPL-4 fills: "#dde3ee"
TEXT_MUTED_DARK   = None     # Placeholder — UPL-11 needs: "#9aabb8" (4.7:1 on #2f2f2f)
```
**Implementation decision:** Do NOT include None-valued keys in `PALETTE_LIGHT`. Instead, add inline comments in `styles.py` documenting the future `PALETTE_DARK` key names so UPL-4 knows exactly what to add. This keeps `PALETTE_LIGHT` clean and consistent (all values are valid hex strings).

**Tier 3 — Required by downstream UPL-5 (per-variety color) — add as named tokens:**
```
VARIETY_COLOR_K3       = "#8ab4d4"   # Cool slate — K3 surface family
VARIETY_COLOR_ENRIQUES = "#c8a880"   # Warm sand — Enriques surface
VARIETY_COLOR_CY3      = "#4a90d9"   # Cobalt — Calabi-Yau 3-fold (Hanson identity)
VARIETY_COLOR_FANO     = "#7ec8a0"   # Muted forest — Fano 3-fold (ρ=1)
SURFACE_DEFAULT        = "#b0c4de"   # Lightsteelblue — pre-UPL-5 default (appearance_panel.py:74)
```
All five new variety tokens are 6-digit hex (AI-13 compliant). All four family tokens pass ≥3:1 luminance ratio against `BG_VIEWPORT = "#2f2f2f"` (verified in challenge.md §4, MINOR finding on UPL-5).

**Tier 4 — QSS-only hex literals to tokenize (improve coverage):**
```
BORDER_GROUP   = "#d0d0d0"   # QGroupBox border (styles.py:90 raw hex)
BORDER_DOCK    = "#c5cdd8"   # Dock header border (styles.py:30 = COLOR_DOCK_HEADER_BORDER)
SWATCH_BORDER  = "#888888"   # Color-swatch border (appearance_panel.py:48 — AI-13 adjacency fix)
```

### 4.3 Implementation steps

1. **Add `PALETTE_LIGHT` dict to `styles.py`** — before the existing `COLOR_MUTED` line. Include Tier 1 + 3 + 4 tokens. Add comments for future `PALETTE_DARK` keys alongside each token that has a dark analogue.

2. **Alias existing constants from the dict** — replace `COLOR_MUTED = "#5a5a5a"` with `COLOR_MUTED = PALETTE_LIGHT["TEXT_MUTED"]`. Same for `COLOR_VALUE`, `COLOR_DOCK_HEADER_BG`, `COLOR_DOCK_HEADER_BORDER`, `COLOR_RESET_BTN_*`. This preserves every consumer of the old constant names at zero change cost.

3. **Tokenize raw QSS hex in `APP_STYLESHEET`** — replace `#d0d0d0`, `#b0bec5`, `#e8f0f5`, `#5b9bd5` with f-string substitutions using the new token names. `#5a3a3a` (danger text) and `#f5f5f5`/`#d8d8d8`/`#aaaaaa` (disabled states) are tertiary UI-state colors that can remain raw hex in this PR — they have no downstream UPL candidate that needs them tokenized.

4. **Update `appearance_panel.py`** — import `PALETTE_LIGHT` from styles; replace `"#b0c4de"` with `PALETTE_LIGHT["SURFACE_DEFAULT"]`; replace `"#2f2f2f"` with `PALETTE_LIGHT["BG_VIEWPORT"]`; replace `#888` in `_apply_swatch_color()` with `PALETTE_LIGHT["SWATCH_BORDER"]` (6-digit — also resolves UPL-21).

5. **Update `app.py`** — import `PALETTE_LIGHT` from styles; replace both `color="#888888"` overlay wire calls with `color=PALETTE_LIGHT["OVERLAY_WIRE"]`.

6. **No functional changes** — every rendered color value is preserved. `PALETTE_LIGHT` values are the exact hex strings currently in the code. The test suite (pure NumPy/PyVista, no Qt) will pass unchanged.

### 4.4 API surface that downstream candidates need

| Downstream | What they read from `PALETTE_LIGHT` |
|---|---|
| UPL-4 (dark mode) | Adds `PALETTE_DARK: dict[str, str]` with same key set; `APP_STYLESHEET` becomes `_build_stylesheet(palette)` function |
| UPL-5 (per-variety color) | Reads `PALETTE_LIGHT["VARIETY_COLOR_K3"]` etc.; `appearance_panel.set_default_color(hex)` already takes a hex str |
| UPL-11 (first-launch overlay) | Needs `TEXT_MUTED` (light: 5.4:1 on #f0f0f0 — pass) and a `TEXT_MUTED_DARK` for the viewport background (4.7:1 on #2f2f2f — challenge.md §4 MINOR finding) |
| UPL-21 (AI-13 cleanup) | Resolved by this milestone — `SWATCH_BORDER = "#888888"` in `PALETTE_LIGHT` + used in `_apply_swatch_color()` |

**Critical API decision for UPL-4:** If `APP_STYLESHEET` is a module-level f-string constant today, UPL-4 will need it refactored into a `_build_stylesheet(palette: dict)` function that both `STYLESHEET_LIGHT` and `STYLESHEET_DARK` call. This UPL-1 implementation should not do the function refactor itself (that is UPL-4's scope), but should use token references consistently enough that the refactor is mechanical. Recommendation: add a one-line comment above `APP_STYLESHEET`: `# UPL-4 will refactor this into _build_stylesheet(palette) — keep all hex references tokenized.`

---

## 5. Alternatives considered

- **New `palette.py` module** — Rejected: AVC's scale doesn't justify a separate module; breaks the established `styles.py`-is-authoritative convention; requires updating CONTEXT.md §2 to describe the new module; adds import surface without benefit. See §4.1 tradeoff table.

- **Nested dict `PALETTE_LIGHT = {"bg": {"viewport": "#2f2f2f", "panel": "#e8edf2"}, ...}`** — Rejected: nested access (`PALETTE_LIGHT["bg"]["viewport"]`) is more verbose than flat (`PALETTE_LIGHT["BG_VIEWPORT"]`) with no organizational benefit at this scale. Qt-material's XML nesting is needed because it maps to CSS variable hierarchy; AVC's QSS is flat f-string substitution.

- **QPalette subclass** — Rejected: QPalette is a widget-state-aware system (Active/Inactive/Disabled groups) that requires instantiating inside a Qt event loop. `styles.py` is imported at module load before `QApplication` exists. A plain dict is the correct structure.

- **dataclass or TypedDict for type safety** — Rejected for now: adds boilerplate with no consumer benefit before UPL-4 introduces `PALETTE_DARK`. When `PALETTE_DARK` is added, consider a `@dataclass class Palette` at that point. Out of scope for UPL-1.

- **napari-style Theme class** — Rejected: napari's Theme class with `register_theme()` is appropriate for a plugin ecosystem where third parties define themes. AVC has no plugin API; a plain dict is less infrastructure for the same result.

- **Adopt `pyqtdarktheme-fork` as runtime dep** — Rejected (synthesis + challenge both reject this): the app's centralized stylesheet would have to thread a third-party QSS through it. AVC hand-rolls `APP_STYLESHEET`; using pyqtdarktheme-fork as a reference only (not runtime dep) is the correct call per synthesis §4.

---

## 6. Risks and unknowns

- **AI-13 compliance (CRITICAL path):** `PALETTE_LIGHT` values that flow into `plotter.add_mesh(color=...)` MUST be 6-digit hex. All proposed tokens are 6-digit. Verify that no `PALETTE_LIGHT` value is accidentally passed to PyVista as a short-hex alias (none are, since all values are being converted FROM existing literals that are already 6-digit in most cases). The `SWATCH_BORDER = "#888888"` token is used only in Qt stylesheet context (`setStyleSheet()`) — not in PyVista — so no AI-13 violation risk there.

- **AI-12 compliance (secondary):** The existing `TEXT_MUTED = "#5a5a5a"` passes 5.4:1 on `#f0f0f0` (panel background). It fails 2.5:1 on `BG_VIEWPORT = "#2f2f2f"` — but `TEXT_MUTED` is only used in panel QSS, never overlaid on the viewport. No regression. The challenge.md §4 MINOR finding (UPL-11) flags that UPL-11's overlay hint needs a brighter token; document this in the comment for `TEXT_MUTED`: `# NOTE: on dark BG_VIEWPORT, use TEXT_MUTED_DARK="#9aabb8" (UPL-11/UPL-4 add this)`.

- **No functional color changes:** Every hex value in `PALETTE_LIGHT` must exactly match the current literal in the code. A mistake here silently changes rendered colors. Implementer should diff the before/after hex values manually before committing.

- **Import order:** `appearance_panel.py` imports from `styles`. `styles.py` has no intra-app imports. The new `from styles import PALETTE_LIGHT` in `appearance_panel.py` and `app.py` is safe and circular-import-free.

- **AI-9 (re-entrancy) — NOT affected:** This refactor is pure constant substitution. No `processEvents()` changes. No render pipeline changes.

- **AI-8 (frozen dataclass) — NOT affected:** `PALETTE_LIGHT` is a plain dict, not a `ParamSpec` or `Surface`. No registry changes.

- **`SURFACE_DEFAULT = "#b0c4de"` must survive UPL-5:** When UPL-5 lands, `appearance_panel.py` will read `PALETTE_LIGHT["VARIETY_COLOR_K3"]` etc. instead of `PALETTE_LIGHT["SURFACE_DEFAULT"]`. `SURFACE_DEFAULT` becomes the pre-UPL-5 fallback and can be kept or removed at UPL-5's discretion. Do not remove it in this PR.

---

## 7. AI-15 disclaimers

Not applicable. This milestone proposes no new variety or figure. It is a pure code-organization refactor with no changes to mathematical objects or rendered geometry.

---

## 8. Open questions for the user

None. The milestone brief is fully specified:
- Required token names: `BG_VIEWPORT`, `BG_PANEL`, `TEXT_VALUE`, `TEXT_MUTED`, `FOCUS_RING`, plus variety-family color placeholders. All are defined above.
- "Preserve every existing rendered color" — verified: all `PALETTE_LIGHT` values are the exact current literals.
- "Resolve UPL-21 (#888 short-hex finding)" — handled by `SWATCH_BORDER = "#888888"` in Tier 4.
- "Preserve dock-size" — no layout changes; no `setMinimumWidth` / `setFixedWidth` changes proposed.

---

*Brief written by milestone-researcher agent (Agent B). Lens: external patterns + downstream API implications. Sources: pyqtdarktheme-fork docs, Qt QPalette reference, qt-material GitHub (MIT), napari theming docs, ParaView color palette docs, superqt docs. Codebase read: styles.py (full), appearance_panel.py (full), app.py (lines 1–50, 350–400), requirements.txt, app-invariants.md (full), synthesis.md, challenge.md, final-report.md.*
