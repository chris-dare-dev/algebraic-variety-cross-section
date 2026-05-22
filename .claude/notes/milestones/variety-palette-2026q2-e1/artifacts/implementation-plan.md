# Implementation plan — variety-palette-2026q2-e1

**Inline path.** ~50 LOC across 4 files. Researcher's sequencing.

1. **styles.py** — Populate `VARIETY_DEFAULT_COLOR` with 4 WCAG-verified hex values (K3 `#8e9ed4`, Enriques `#c4a882`, CY3 `#85b5d0`, Fano `#8fbe85`). Keys copy-pasted verbatim from `surfaces.py` (Unicode en-dash + rho). Fix the misleading "ASCII hyphen" comment at styles.py:102. Add `VARIETY_DEFAULT_COLOR_DARK` forward-compat comment hook for UPL-4 (comment only — do NOT populate).

2. **appearance_panel.py** — Add public `set_default_color(hex_str)` method mirroring the `_pick_surface_color` pattern. Mutates `self._surface_color` + refreshes `_surf_swatch` via `_apply_swatch_color`. Does NOT trigger render (caller is `_on_*_changed` which flows naturally into `_render_current` → `apply_to_actor`).

3. **app.py** — Extend import line at app.py:31 with `VARIETY_DEFAULT_COLOR, BG_SURFACE_DEFAULT`. Add `set_default_color()` calls in both `_on_variety_changed` (after `_set_subtype_enabled(True)`) and `_on_subtype_changed` (after `surface = VARIETIES[variety][name]`). Both wired symmetrically so swatch reflects the family color whether the user changes only Variety or also picks a Subtype.

4. **tests/test_styles_palette.py** — Replace the stub test `test_variety_default_color_is_stub_for_upl5` (lines 133-138) with 4 new test functions: (a) exact-keys-match-VARIETIES, (b) all-6-digit-hex, (c) WCAG 4.5:1 against BG_VIEWPORT, (d) keys-match-surfaces.VARIETIES forward-compat guard. Extract `luminance()`/`ratio()` helpers to module top to avoid duplication.

5. **Verify** — `.venv/bin/python -m pytest tests/ -q` must pass (175 + 3 net = 178 expected; stub removed, 4 added). Manually verify by running app.py and switching K3 → Enriques → CY3 → Fano — each family shows a distinct color (researcher: hue separation ≥25° pairwise).

6. **Commit** — Single conventional commit: `feat(variety-palette-2026q2-e1): populate VARIETY_DEFAULT_COLOR with per-family hex tokens`.
