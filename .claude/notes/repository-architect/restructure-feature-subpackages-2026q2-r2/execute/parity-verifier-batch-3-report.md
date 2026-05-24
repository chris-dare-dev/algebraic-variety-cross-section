# Parity-verifier report — restructure-feature-subpackages-2026q2-r2 batch 3

**Run at:** 2026-05-23T23:30:00Z (inline by main session per agent-timeout fallback)
**Verdict:** PASS (after iterative fix-cycle on 5 test files)

## Mechanical checks

| # | Check | Result | Detail |
|---|---|---|---|
| 1 | Test collection | PASS | 499 collected, 0 delta vs B2 (no test count changes; B3 doesn't add or remove tests) |
| 2 | Coverage XML | INFORMATIONAL/SKIPPED | pyvistaqt path issue persists |
| 3 | Pydeps cycles | INFORMATIONAL/SKIPPED | hyphenated repo name |
| 4 | Import-time | PASS (informal) | `import app` succeeds without delay |
| 5 | Shim validation | PASS | 4 new shims verified by smoke-test: panels/__init__.py hub forwards to _qt.panels.* with DeprecationWarning; 3 root shims (icons, styles, ui_helpers) each emit Template-2 DeprecationWarning |
| 6 | Star-imports | PASS | grep count unchanged (still 3 pre-existing) |

## Iterative fixes during B3 (inline debugging)

The biggest batch hit a cluster of `rewrite-imports.py` partial-rewrite issues. Each test failure required a targeted fix:

1. `tests/test_styles_palette.py:646-649` panel_files tuple → updated to `_qt/panels/*.py` paths
2. `tests/test_styles_palette.py:134,816,869,921,1116` — `"panels"/"appearance.py"` Path-construction → updated to `"_qt"/"panels"/"appearance.py"`
3. `tests/test_styles_palette.py:12 import _qt.styles` → added `import _qt.styles as styles` AND `import _qt` for partial-rewritten `_qt.styles.X` references
4. `tests/test_icons.py:32` — same alias pattern + added `import _qt.icons as icons`
5. `tests/test_enriques_hq_smoothing.py:168,280,326,362,377` — same `"panels"/"appearance.py"` → `"_qt"/"panels"/"appearance.py"` pattern
6. `tests/test_render_busy_spinner.py:36` — `"icons.py"` → `"_qt"/"icons.py"` path-string
7. `tests/test_render_busy_spinner.py:218` — function-local `import _qt.icons` → `import _qt + import _qt.icons as icons` for bare `icons.X` references

These are LibCST-tool-gap recoveries, NOT source-level changes. The `rewrite-imports.py` script needs fixing in a future tooling milestone (recorded as a Phase 5 finding).

## Notes

11 files changed across 2 commits (B3 commit 1 = 2fdf808; B3 commit 2 = 321610f):
- 4 panels/* files renamed via git mv to _qt/panels/* (rename detection preserved)
- 3 new files copied + Template-2 shims at root (icons/styles/ui_helpers)
- 1 panels/__init__.py hub shim (NEW; per adversary v2 HIGH-1)
- 1 _qt/__init__.py (NEW)
- 15 files with LibCST import rewrites (including 5 test files needing manual fixup)
- 5 test files with manual path-string fixes (LibCST cannot rewrite string literals)

Tag `refactor-r2-batch3-end` at 321610f. Tree at 3/9 batches landed; 499 tests passing.
