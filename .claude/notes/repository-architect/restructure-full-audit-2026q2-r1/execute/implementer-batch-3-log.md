# Implementer Batch 3 Log — restructure-full-audit-2026q2-r1

**Batch:** 3/4
**Operation:** "Dark-mode regression fix in parameter_grid_panel.py L232 BG_GRID_SCENE hardcoding + add parameter_grid_panel.py to inline-style guard tuple"
**Date:** 2026-05-23
**Status:** complete

---

## Pre-flight checks

- `git status`: clean source tree (`.claude/notes/dispatch.log` had an unstaged edit — non-blocking per lessons.md; outside source scope).
- HEAD at entry: `f989b9d` (Batch 2 pipeline metadata commit — correct previous batch tip).
- RESTRUCTURE_BASE: `c7b2bd8` — all commits since base are Batch 1 + Batch 2 ops, as expected.
- Symbol map: no Batch 3 entries (Batches 1-3 have no file moves per PLAN.md §3).
- Shims: none required (in-place fix only).
- Import rewrites: none required.

---

## Op 1: Fix BG_GRID_SCENE dark-mode regression in parameter_grid_panel.py + styles.py

### Diagnosis (preflight check per PLAN.md v2 LOW-1)

- Checked `styles.py:_render_stylesheet()` for any existing `QGraphicsView[role="grid-scene"]` or BG_GRID_SCENE-equivalent role selector: **none found**.
- BG_GRID_SCENE values confirmed: PALETTE_LIGHT = `#fbfbfb`, PALETTE_DARK = `#2a2a2b`.
- In `parameter_grid_panel.py`, `BG_GRID_SCENE` was imported at L37 and used ONLY at L232. Safe to remove import after fix.
- `SMALL_LABEL_STYLE` uses at L184/L209/L328 are `"font-size: 11px;"` — font-only, no color. Not a dark-mode regression. Not touched per batch 3 instructions.

### Changes made

**styles.py** — added `QGraphicsView[role="grid-scene"]` block inside `_render_stylesheet()`, inserted after the role-based label block (QLabel[role="range-label"]) and before the Dock widget title bar block:

```qss
QGraphicsView[role="grid-scene"] {
    background: {palette["BG_GRID_SCENE"]};
    border: none;
}
```

Both `APP_STYLESHEET` (light, `#fbfbfb`) and `APP_STYLESHEET_DARK` (dark, `#2a2a2b`) are generated correctly from the single template. Rule preserves `border: none` from the original inline call.

**parameter_grid_panel.py** — two changes:
1. Removed `BG_GRID_SCENE` from the `from styles import (...)` block (now unused).
2. L232: replaced `self._view.setStyleSheet(f"background: {BG_GRID_SCENE}; border: none;")` with `self._view.setProperty("role", "grid-scene")` plus an explanatory comment.

### SMALL_LABEL_STYLE decision

The `setStyleSheet(SMALL_LABEL_STYLE)` calls at L184/L209/L328 use `SMALL_LABEL_STYLE = "font-size: 11px;"` — font-only, no color. They are NOT a dark-mode regression (per current-state §5.3 and batch 3 instructions). No action taken. The inline-style guard (Op 2) does NOT flag them because `setStyleSheet(SMALL_LABEL_STYLE)` is not in the `forbidden` tuple.

- Files modified: `parameter_grid_panel.py`, `styles.py`
- Shim path: N/A
- Imports rewritten: 0 (removed 1 unused import from the import block)
- Tests run: 499 passed in 7.27s
- Commit: `1a92515` "refactor(restructure-full-audit-2026q2-r1): fix BG_GRID_SCENE dark-mode regression (batch 3/4 op 1/2)"

---

## Op 2: Add parameter_grid_panel.py to inline-style guard tuple

### Guard analysis

`test_no_inline_color_styles_in_panel_files` in `tests/test_styles_palette.py` checks `panel_files` tuple against `forbidden = ("setStyleSheet(MUTED_TEXT_STYLE)", "setStyleSheet(VALUE_MONO_STYLE)", "setStyleSheet(RANGE_LABEL_STYLE)")`.

After Op 1, `parameter_grid_panel.py` no longer contains the BG_GRID_SCENE inline call. The 3 SMALL_LABEL_STYLE uses are not in the forbidden tuple — confirmed by running the test. Choice: (a) the guard's pattern only flags color literals (the 3 specific constants); SMALL_LABEL_STYLE is font-only and not flagged. No additional setProperty migration needed.

### Change made

`tests/test_styles_palette.py` — added `"parameter_grid_panel.py"` to the `panel_files` tuple (4th entry, after `parameters_panel.py`).

- Files modified: `tests/test_styles_palette.py`
- Shim path: N/A
- Imports rewritten: 0
- Tests run: 499 passed in 6.50s (count unchanged — no new parametrize added; existing test expanded its loop by 1 iteration)
- Commit: `5d5a5bc` "refactor(restructure-full-audit-2026q2-r1): add parameter_grid_panel.py to inline-style guard (batch 3/4 op 2/2)"

---

## Post-batch summary

- All 2 operations committed, each as a separate commit.
- Full suite: 499 passed in 6.51s (post-batch run).
- Tag `refactor-batch3-end` created at `5d5a5bc`.
- Commit chain from RESTRUCTURE_BASE:
  ```
  5d5a5bc  refactor: add parameter_grid_panel.py to inline-style guard (batch 3/4 op 2/2)
  1a92515  refactor: fix BG_GRID_SCENE dark-mode regression (batch 3/4 op 1/2)
  f989b9d  chore: Batch 2 pipeline metadata
  ...
  ```

## Lessons appended to agent memory

See `.claude/agent-memory/repository-architect-implementer/lessons.md` — batch 3 entry.
