# Implementation plan — panel-refresh-2026q2-e2 (UPL-1)

**Path:** Inline · **Effort:** ~1 day · **Base commit:** `dc328d7`

## Five-bullet plan

1. **Add `PALETTE_LIGHT: dict[str, str]` at the top of `styles.py`** with all 18 distinct token values inventoried by Researcher A. Include category-grouping comments (`# === Core viewport + panel backgrounds ===`, `# === Text / foreground ===`, etc.). Also add an empty `VARIETY_DEFAULT_COLOR: dict[str, str] = {}` stub with a comment pointing to UPL-5 as populator, and a `# UPL-4: dark-mode parallel goes here as PALETTE_DARK` placeholder marker.

2. **Rewrite the existing module-level named constants** (`COLOR_MUTED`, `COLOR_VALUE`, `COLOR_DOCK_HEADER_BG`, etc.) as thin aliases that read from `PALETTE_LIGHT[...]` at import time. Zero call-site changes in `view_panel.py` / `parameters_panel.py` / `appearance_panel.py` — they continue importing the same names. Add new module-level exports (`BG_VIEWPORT`, `BG_SURFACE_DEFAULT`, `BORDER_SWATCH`, `COLOR_WIREFRAME_OVERLAY`) for use by `appearance_panel.py` and `app.py`.

3. **Replace all raw hex inside `APP_STYLESHEET`** (lines 90, 110, 116–118, 123, 127, 132) with `{PALETTE_LIGHT[...]}` f-string lookups. After this, `grep -E '#[0-9a-fA-F]{3,6}' styles.py | grep -v PALETTE_LIGHT` should match zero raw hex outside the canonical dict.

4. **Migrate the 3 hex literals in `appearance_panel.py`** (lines 48, 74, 75) and **the 2 duplicates in `app.py`** (lines 364, 386). Each becomes an import from `styles` of the relevant named constant. The `#888` short-hex at `appearance_panel.py:48` becomes `#888888` via the `BORDER_SWATCH` token — this resolves the AI-13-adjacency finding cataloged as UPL-21.

5. **Verify, commit, and run smoke tests.** Run pytest (must stay 165 passing). Grep all five touched files for leftover raw hex (expect zero outside `PALETTE_LIGHT`). Optionally add a Qt-free test at `tests/test_styles_palette.py` that asserts `len(styles.PALETTE_LIGHT) >= 6` and every value matches `^#[0-9a-fA-F]{6}$` — cheap regression guard against future short-hex drift. Single commit message: `feat(panel-refresh-2026q2-e2): tokenize palette into PALETTE_LIGHT dict (UPL-1, UPL-21)`.

## Files touched

- `styles.py` — adds dict + aliases + new exports (~50 LOC added; existing inline hex replaced)
- `appearance_panel.py` — 3 literal substitutions (~3 LOC changed) + 1 import line
- `app.py` — 2 literal substitutions (~2 LOC changed) + 1 import line
- `tests/test_styles_palette.py` — NEW Qt-free regression guard (~15 LOC)

## Out of scope (NOT touched)

- `surfaces.py`, `view_panel.py`, `parameters_panel.py` — no hex literals; no change needed
- `CONTEXT.md`, `README.md`, `requirements.txt` — no change
- `app.py:429` `Qt.AA_ShareOpenGLContexts` AI-11 drift — UPL-21 scope, not UPL-1
- `PALETTE_DARK` / dark-mode tokens — UPL-4 scope; leave only a comment placeholder
- Per-variety color values — UPL-5 scope; leave empty `VARIETY_DEFAULT_COLOR` dict

## Acceptance signals

- `pytest tests/ -q` passes (165/165)
- `grep -rE '#[0-9a-fA-F]{3,6}' styles.py app.py appearance_panel.py view_panel.py parameters_panel.py | grep -v PALETTE_LIGHT | grep -v '#'` returns only matches inside the palette dict or comments
- No 3-digit hex anywhere outside comments
- App still launches; viewport background still `#2f2f2f` on first frame (UPL-3 fix preserved); all 9 surfaces still render with default `#b0c4de` slate (UPL-5 will change this per-variety later)
