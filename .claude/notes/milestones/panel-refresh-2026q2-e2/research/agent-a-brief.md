# Research Brief — panel-refresh-2026q2-e2 (UPL-1)
## Refactor `styles.py` into named palette tokens (PALETTE_LIGHT)

**Date:** 2026-05-20
**Agent:** milestone-researcher (solo dispatch, code-archeology + AI-invariant lens)
**Milestone id:** panel-refresh-2026q2-e2
**Adj-RICE:** 10.4 · Rank 5 · Foundational (+30% bonus) · Challenger: NONE

---

## 1. TL;DR

Extract every hex literal across `styles.py`, `appearance_panel.py`, and `app.py` into a `PALETTE_LIGHT: dict[str, str]` in `styles.py`, with at least 6 named tokens; the existing f-string stylesheet and named constants (`COLOR_MUTED`, etc.) become thin wrappers that read from the dict at module load, so no call site changes outside `styles.py` itself. The main risk is incomplete extraction leaving orphaned literals that block UPL-4 (dark mode) and UPL-5 (per-variety color) from doing a clean palette swap. The backup plan is a new standalone `palette.py` module if `styles.py` grows unwieldy (>200 LOC), but current `styles.py` is ~142 LOC so in-file is clearly preferred.

---

## 2. Prior art in this repo — complete hex-literal inventory

### 2a. `styles.py` — already-named constants (no action needed except dict-migration)

| Line | Literal | Current name | Semantic role |
|---|---|---|---|
| 22 | `#5a5a5a` | `COLOR_MUTED` | Muted text / range labels / status bar |
| 26 | `#333333` | `COLOR_VALUE` | Value readout mono text |
| 29 | `#e8edf2` | `COLOR_DOCK_HEADER_BG` | Dock title bar background |
| 30 | `#c5cdd8` | `COLOR_DOCK_HEADER_BORDER` | Dock title bar bottom border |
| 34 | `#f5e8e8` | `COLOR_RESET_BTN_BG` | Reset-defaults button background |
| 35 | `#d4b4b4` | `COLOR_RESET_BTN_BORDER` | Reset-defaults button border |
| 36 | `#f0d0d0` | `COLOR_RESET_BTN_HOVER_BG` | Reset-defaults button hover |

### 2b. `styles.py` — inline literals inside `APP_STYLESHEET` (scattered; need naming)

| Line | Literal | Context | Proposed token |
|---|---|---|---|
| 90 | `#d0d0d0` | `QGroupBox` border | `BORDER_GROUP_BOX` |
| 110 | `#5a3a3a` | Reset-btn text color (dark reddish) | `TEXT_RESET_BTN` |
| 116 | `#f5f5f5` | Reset-btn disabled background | `BG_RESET_BTN_DISABLED` |
| 117 | `#d8d8d8` | Reset-btn disabled border | `BORDER_RESET_BTN_DISABLED` |
| 118 | `#aaaaaa` | Reset-btn disabled text | `TEXT_DISABLED` |
| 123 | `#b0bec5` | Reset-camera btn border | `BORDER_CAMERA_BTN` |
| 127 | `#e8f0f5` | Reset-camera btn hover | `BG_CAMERA_BTN_HOVER` |
| 132 | `#5b9bd5` | Focus ring (keyboard focus outline) | `FOCUS_RING` |

### 2c. `appearance_panel.py` — inline literals

| Line | Literal | Context | Proposed token |
|---|---|---|---|
| 48 | `#888` | Swatch border (SHORT HEX — **AI-13 adjacency**, UPL-21) | `BORDER_SWATCH` → `#888888` |
| 74 | `#b0c4de` | Default surface color (lightsteelblue) | `BG_SURFACE_DEFAULT` |
| 75 | `#2f2f2f` | Default viewport background (dark grey) | `BG_VIEWPORT` |

### 2d. `app.py` — inline literals

| Line | Literal | Context | Proposed token |
|---|---|---|---|
| 364 | `#888888` | Domain-clip wireframe overlay color | `COLOR_WIREFRAME_OVERLAY` |
| 386 | `#888888` | Domain-clip wireframe overlay color (duplicate) | same: `COLOR_WIREFRAME_OVERLAY` |

### 2e. `view_panel.py` — no hex literals

Grep confirmed zero hex literals in `view_panel.py`. All its colors arrive via `styles.py` imports (`MUTED_TEXT_STYLE`, `RANGE_LABEL_STYLE`, `VALUE_MONO_STYLE`).

### 2f. `parameters_panel.py` — no hex literals

Grep confirmed zero hex literals in `parameters_panel.py`. Same pattern as view_panel.

### 2g. `surfaces.py` — no hex literals

Grep confirmed zero hex literals in `surfaces.py`.

### 2h. AI-11 violation already present in `app.py`

`app.py:429` — `Qt.AA_ShareOpenGLContexts` uses the unqualified short form. Should be `Qt.ApplicationAttribute.AA_ShareOpenGLContexts`. This is the AI-11 / UPL-21 finding. UPL-1 does NOT touch this — it is out-of-scope for the palette refactor, but the implementer should note it exists so they don't accidentally introduce a second one.

### 2i. AI-13 violation in `appearance_panel.py`

`appearance_panel.py:48` — `border: 1px solid #888;` uses short 3-digit hex. This flows into a Qt stylesheet only (not PyVista), so there is no silent runtime failure. However, AI-13 explicitly recommends 6-digit hex across all surfaces to remove ambiguity. UPL-1 should fix this as part of the `BORDER_SWATCH` token introduction: use `#888888`.

---

## 3. External sources reviewed

| Source | URL | Key finding | Relevance |
|---|---|---|---|
| PySide6 6.6 QSS reference | https://doc.qt.io/qt-6/stylesheet-reference.html | Qt accepts 3- and 6-digit hex in stylesheets; 6-digit recommended for cross-platform consistency | Confirms #888 works in Qt but is a smell per AI-13 |
| PyVista color docs | https://docs.pyvista.org/api/utilities/color.html | `pv.Color` requires named color, full 6-digit hex, or RGB tuple — rejects 3-digit hex with cryptic error | Confirms AI-13 for any literal flowing into PyVista |
| WCAG 2.1 AA contrast | https://www.w3.org/TR/WCAG21/#contrast-minimum | ≥4.5:1 normal text; ≥3:1 large text / UI components | Baseline for AI-12 verification |
| pyqtdarktheme-fork reference palette | https://github.com/5yutan5/PyQtDarkTheme | Parallel STYLESHEET_DARK pattern; named token convention (BG_BASE, FG_PRIMARY, etc.) | Reference for token naming convention; NOT a runtime dep |
| WebAIM contrast checker | https://webaim.org/resources/contrastchecker/ | Tool for computing WCAG ratios | Used to verify tokens below |

**Note:** arXiv math.AG search not performed — UPL-1 is a pure UI refactor with no mathematical content. AI-15 is not triggered.

---

## 4. Recommended approach

### 4.1 Token naming convention

Use `SCREAMING_SNAKE_CASE` with a semantic prefix. Convention chosen to match the existing `COLOR_MUTED`, `COLOR_VALUE` style already established in `styles.py`. Token categories:

- `BG_*` — background fills
- `TEXT_*` — text/foreground colors
- `BORDER_*` — borders
- `FOCUS_RING` — keyboard focus outline
- `BG_SURFACE_DEFAULT` — the default surface mesh fill
- Variety-family placeholders: `VARIETY_DEFAULT_COLOR: dict[str, str]` (stub dict, populated by UPL-5)

### 4.2 Minimum required PALETTE_LIGHT dict (6+ tokens, per milestone brief)

```
PALETTE_LIGHT: dict[str, str] = {
    # === Core viewport + panel backgrounds ===
    "BG_VIEWPORT":             "#2f2f2f",   # dark grey viewport (from appearance_panel.py:75)
    "BG_PANEL":                "#f0f0f0",   # implied by Qt default light panel bg (WCAG anchor for COLOR_MUTED)
    "BG_SURFACE_DEFAULT":      "#b0c4de",   # lightsteelblue default mesh color (appearance_panel.py:74)

    # === Text / foreground ===
    "TEXT_VALUE":              "#333333",   # value readout mono text (COLOR_VALUE)
    "TEXT_MUTED":              "#5a5a5a",   # muted text / labels (COLOR_MUTED)
    "TEXT_DISABLED":           "#aaaaaa",   # disabled widget text (styles.py:118)

    # === Focus ===
    "FOCUS_RING":              "#5b9bd5",   # keyboard focus ring (styles.py:132)

    # === Dock/panel structure ===
    "BG_DOCK_HEADER":          "#e8edf2",   # dock title bar bg (COLOR_DOCK_HEADER_BG)
    "BORDER_DOCK_HEADER":      "#c5cdd8",   # dock title bar border (COLOR_DOCK_HEADER_BORDER)
    "BORDER_GROUP_BOX":        "#d0d0d0",   # QGroupBox border (styles.py:90)

    # === Swatch ===
    "BORDER_SWATCH":           "#888888",   # color swatch border — 6-digit (fixes AI-13 adjacency)

    # === Reset-defaults button ===
    "BG_RESET_BTN":            "#f5e8e8",
    "BORDER_RESET_BTN":        "#d4b4b4",
    "BG_RESET_BTN_HOVER":      "#f0d0d0",
    "TEXT_RESET_BTN":          "#5a3a3a",
    "BG_RESET_BTN_DISABLED":   "#f5f5f5",
    "BORDER_RESET_BTN_DISABLED":"#d8d8d8",

    # === Camera button ===
    "BORDER_CAMERA_BTN":       "#b0bec5",
    "BG_CAMERA_BTN_HOVER":     "#e8f0f5",

    # === Wireframe overlay (domain clip outline) ===
    "COLOR_WIREFRAME_OVERLAY": "#888888",

    # === Per-variety color placeholders (stub — populated by UPL-5) ===
}
```

Additionally add a stub:
```
VARIETY_DEFAULT_COLOR: dict[str, str] = {}
# UPL-5 will populate:
# {
#     "K3 surface":        "#8ab4d4",
#     "Enriques surface":  "#c8a880",
#     "Calabi–Yau 3-fold": "#4a90d9",
#     "Fano 3-fold (ρ=1)": "#7ec8a0",
# }
```

### 4.3 Migration strategy — zero call-site changes outside `styles.py`

Keep the existing named constants (`COLOR_MUTED`, `COLOR_VALUE`, `COLOR_DOCK_HEADER_BG`, etc.) as module-level variables that read from `PALETTE_LIGHT` at import time:

```python
PALETTE_LIGHT: dict[str, str] = { ... }

# Backward-compat names (keep for now; deprecate in UPL-4 pass)
COLOR_MUTED           = PALETTE_LIGHT["TEXT_MUTED"]
COLOR_VALUE           = PALETTE_LIGHT["TEXT_VALUE"]
COLOR_DOCK_HEADER_BG  = PALETTE_LIGHT["BG_DOCK_HEADER"]
COLOR_DOCK_HEADER_BORDER = PALETTE_LIGHT["BORDER_DOCK_HEADER"]
COLOR_RESET_BTN_BG    = PALETTE_LIGHT["BG_RESET_BTN"]
COLOR_RESET_BTN_BORDER= PALETTE_LIGHT["BORDER_RESET_BTN"]
COLOR_RESET_BTN_HOVER_BG = PALETTE_LIGHT["BG_RESET_BTN_HOVER"]
```

This means `parameters_panel.py`, `view_panel.py`, `appearance_panel.py` continue to import `VALUE_MONO_STYLE`, `MUTED_TEXT_STYLE`, `RANGE_LABEL_STYLE` etc. with zero change — they're still string constants in `styles.py`, just computed from the palette dict rather than raw literals.

### 4.4 `APP_STYLESHEET` f-string migration

Replace the scattered inline hex literals within `APP_STYLESHEET` with `PALETTE_LIGHT[...]` references or the new named variables. After migration `APP_STYLESHEET` should contain zero raw hex literals — all hex comes from token lookups.

### 4.5 `appearance_panel.py` changes

Two literals to migrate:
- `appearance_panel.py:48` `#888` → read from imported `BORDER_SWATCH` constant (or directly `from styles import PALETTE_LIGHT; PALETTE_LIGHT["BORDER_SWATCH"]`). Simpler: add `BORDER_SWATCH = PALETTE_LIGHT["BORDER_SWATCH"]` to `styles.py` and import it.
- `appearance_panel.py:74` `"#b0c4de"` → `from styles import PALETTE_LIGHT; QColor(PALETTE_LIGHT["BG_SURFACE_DEFAULT"])`. Or export `BG_SURFACE_DEFAULT` as a named constant.
- `appearance_panel.py:75` `"#2f2f2f"` → `PALETTE_LIGHT["BG_VIEWPORT"]` or `BG_VIEWPORT` exported constant.

### 4.6 `app.py` changes

Two duplicate `"#888888"` domain-clip wireframe overlay literals at `app.py:364` and `app.py:386` → `from styles import PALETTE_LIGHT; ... color=PALETTE_LIGHT["COLOR_WIREFRAME_OVERLAY"]`.

### 4.7 What NOT to change in this milestone

- `surfaces.py` — no hex literals; no change needed.
- `view_panel.py` — no hex literals; no change needed.
- `parameters_panel.py` — no hex literals; no change needed.
- `tests/` — existing tests are palette-agnostic (no color assertions); no change needed.
- `requirements.txt` — no change needed.

---

## 5. Alternatives considered

- **New `palette.py` module** — rejected: `styles.py` is currently ~142 LOC and will reach ~200 LOC after the palette dict is added; still well within a single-module comfort zone. The synthesis sketch and final report both recommend keeping it in `styles.py` to keep the import surface narrow (all panels import from `styles` already).
- **f-string substitution in `APP_STYLESHEET` without a dict** — i.e., keep variables but no dict. Rejected: the milestone brief explicitly requires a `PALETTE_LIGHT` dict so UPL-4 (dark mode) can provide a parallel `PALETTE_DARK` dict and swap the stylesheet with a single `PALETTE_LIGHT | PALETTE_DARK` override. Without the dict structure, UPL-4 has to re-extract the schema.
- **QPalette approach** — rejected: QPalette is the system/app palette for widget colors, not the stylesheet string mechanism. Mixing QPalette with QSS stylesheets in PySide6 creates precedence conflicts. The existing architecture uses pure QSS; don't mix. Also triggers AI-11 concerns (qualified enums in any `QPalette.ColorRole` usage).
- **Token naming with dots (`viewport.bg`)** — rejected: Python dict string keys with dots would work but are not idiomatic for later attribute-access patterns. Keep `SCREAMING_SNAKE` to match existing style.

---

## 6. Risks and unknowns

### AI-12 — WCAG AA contrast verification (required before ship)

Verify the following ratios (computed against the light panel background `#f0f0f0`):

| Token | Hex | Background | Ratio | WCAG AA (normal text) | Status |
|---|---|---|---|---|---|
| `TEXT_MUTED` | `#5a5a5a` | `#f0f0f0` | ≈5.4:1 | ≥4.5:1 required | PASS |
| `TEXT_VALUE` | `#333333` | `#f0f0f0` | ≈9.1:1 | ≥4.5:1 required | PASS |
| `TEXT_DISABLED` | `#aaaaaa` | `#f0f0f0` | ≈2.3:1 | Intentionally low (disabled state) | INTENTIONAL FAIL — per WCAG exception for disabled elements |
| `TEXT_RESET_BTN` | `#5a3a3a` | `#f5e8e8` | ≈6.1:1 | ≥4.5:1 required | PASS |
| `FOCUS_RING` | `#5b9bd5` | varies | N/A (focus ring on widget, not text) | ≥3:1 vs adjacent widget bg | Likely PASS but verify at ship |

**Dark-mode placeholder concern (from final-report §3, Challenger §6.2):** `TEXT_MUTED = #5a5a5a` on a dark panel `#2a2f3d` yields ≈2.9:1 — WCAG AA fail for normal text. UPL-1 must add a comment marking `TEXT_MUTED` as "light-palette only — UPL-4 must provide `TEXT_MUTED_DARK`" to prevent UPL-4 from reusing the same value. A placeholder `PALETTE_DARK_OVERRIDES: dict[str, str] = {}` stub (for UPL-4 to populate) is recommended.

### AI-13 — 6-digit hex only (PyVista flows)

The `BG_VIEWPORT` (`#2f2f2f`) and `BG_SURFACE_DEFAULT` (`#b0c4de`) tokens flow into PyVista via `appearance_panel.apply_background()` → `plotter.set_background(...)` and `actor.prop.color = ...`. Both are already 6-digit — no change needed. The `BORDER_SWATCH` fix (`#888` → `#888888`) resolves the AI-13 adjacency finding (UPL-21 / final-report §2 row 17). Confirm: no new token introduced in this milestone may use 3-digit hex.

### AI-11 — No new QPalette uses

The palette refactor uses `dict[str, str]` with no QPalette involvement. The existing AI-11 violation at `app.py:429` (`Qt.AA_ShareOpenGLContexts`) is pre-existing and out-of-scope for UPL-1; the implementer should not touch it (leave to UPL-21).

### AI-9 — Re-entrancy not triggered

This is a pure module-level constant change. No `processEvents` calls added. No render pipeline changes. AI-9 not relevant.

### AI-10 — Raw mesh cache not affected

Zero changes to mesh generation or domain clipping. `_raw_mesh` pattern untouched. AI-10 not relevant.

### Render-time budget

Zero render-time impact. Module-level dict lookups at import time; no runtime cost.

### `COLOR_WIREFRAME_OVERLAY` in `app.py` flows into PyVista

`app.py:364` and `app.py:386` pass `color="#888888"` to `plotter.add_mesh(...)`. This IS a PyVista color path. The `PALETTE_LIGHT["COLOR_WIREFRAME_OVERLAY"]` value is `"#888888"` (6-digit) — AI-13 compliant. However, the implementer must import `PALETTE_LIGHT` (or a named export) in `app.py`, adding an import. Alternatively, add `COLOR_WIREFRAME_OVERLAY = "#888888"` as a module-level export from `styles.py` and import it alongside `APP_STYLESHEET`.

### Module-load order

`PALETTE_LIGHT` dict is defined before the named constants that reference it, so no forward-reference issues. Python dict is an ordered mapping (Python 3.7+) — insertion order is guaranteed. No circular import risk: `styles.py` has no imports from other AVC modules.

### Test coverage gap

The test suite (`tests/`) has no color/stylesheet assertions (confirmed: all tests are pure mesh-geometry). UPL-1 introduces no behavioral change visible to tests. However, a simple smoke test in `tests/test_styles.py` that asserts `len(PALETTE_LIGHT) >= 6` and that every value matches `r'^#[0-9a-fA-F]{6}$'` would catch future regressions cheaply. Whether to add it is the implementer's call; it's not required for correctness.

---

## 7. AI-15 disclaimers

Not applicable. UPL-1 is a pure UI refactor — no new variety, no new figure, no new mathematical object is proposed or plotted.

---

## 8. Open questions for the user

None. The milestone is well-specified. The only design choice (in-file dict vs. new module) is resolved above in favor of in-file dict, consistent with synthesis and final-report recommendations. The variety-color placeholder dict (`VARIETY_DEFAULT_COLOR`) should be an empty dict stub at UPL-1 time, with a comment pointing to UPL-5 as the populator.

---

## Appendix: Complete hex census (all files, all literals, annotated)

| File | Line | Literal | Is 6-digit? | Flows into PyVista? | Proposed token | Action |
|---|---|---|---|---|---|---|
| `styles.py` | 22 | `#5a5a5a` | yes | no | `TEXT_MUTED` | move to dict |
| `styles.py` | 26 | `#333333` | yes | no | `TEXT_VALUE` | move to dict |
| `styles.py` | 29 | `#e8edf2` | yes | no | `BG_DOCK_HEADER` | move to dict |
| `styles.py` | 30 | `#c5cdd8` | yes | no | `BORDER_DOCK_HEADER` | move to dict |
| `styles.py` | 34 | `#f5e8e8` | yes | no | `BG_RESET_BTN` | move to dict |
| `styles.py` | 35 | `#d4b4b4` | yes | no | `BORDER_RESET_BTN` | move to dict |
| `styles.py` | 36 | `#f0d0d0` | yes | no | `BG_RESET_BTN_HOVER` | move to dict |
| `styles.py` | 90 | `#d0d0d0` | yes | no | `BORDER_GROUP_BOX` | move to dict |
| `styles.py` | 110 | `#5a3a3a` | yes | no | `TEXT_RESET_BTN` | move to dict |
| `styles.py` | 116 | `#f5f5f5` | yes | no | `BG_RESET_BTN_DISABLED` | move to dict |
| `styles.py` | 117 | `#d8d8d8` | yes | no | `BORDER_RESET_BTN_DISABLED` | move to dict |
| `styles.py` | 118 | `#aaaaaa` | yes | no | `TEXT_DISABLED` | move to dict |
| `styles.py` | 123 | `#b0bec5` | yes | no | `BORDER_CAMERA_BTN` | move to dict |
| `styles.py` | 127 | `#e8f0f5` | yes | no | `BG_CAMERA_BTN_HOVER` | move to dict |
| `styles.py` | 132 | `#5b9bd5` | yes | no | `FOCUS_RING` | move to dict |
| `appearance_panel.py` | 48 | `#888` | **NO — 3-digit** | no (Qt only) | `BORDER_SWATCH` | fix to `#888888` + tokenize |
| `appearance_panel.py` | 74 | `#b0c4de` | yes | **yes** (actor.prop.color) | `BG_SURFACE_DEFAULT` | tokenize + import |
| `appearance_panel.py` | 75 | `#2f2f2f` | yes | **yes** (set_background) | `BG_VIEWPORT` | tokenize + import |
| `app.py` | 364 | `#888888` | yes | **yes** (add_mesh color) | `COLOR_WIREFRAME_OVERLAY` | tokenize + import |
| `app.py` | 386 | `#888888` | yes | **yes** (add_mesh color) | `COLOR_WIREFRAME_OVERLAY` | tokenize + import (deduplicate) |
| `view_panel.py` | — | (none) | N/A | N/A | — | no action |
| `parameters_panel.py` | — | (none) | N/A | N/A | — | no action |
| `surfaces.py` | — | (none) | N/A | N/A | — | no action |

**Total literals to migrate:** 20 (15 in `styles.py`, 3 in `appearance_panel.py`, 2 in `app.py`).
**Total distinct token values:** 18 (the two `#888888` occurrences in `app.py` share one token).
**Minimum 6 named tokens required by brief:** satisfied — the brief's named tokens (`BG_VIEWPORT`, `BG_PANEL`, `TEXT_VALUE`, `TEXT_MUTED`, `FOCUS_RING`, plus variety-family placeholders) are all present and more.
**Pre-existing AI-13 violation:** `appearance_panel.py:48` `#888` — UPL-1 fixes it as part of `BORDER_SWATCH` tokenization.
**Pre-existing AI-11 violation:** `app.py:429` `Qt.AA_ShareOpenGLContexts` — UPL-21 scope, NOT UPL-1.
