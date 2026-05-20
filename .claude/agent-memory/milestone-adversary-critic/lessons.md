# lessons -- milestone-adversary-critic

2026-05-20 | milestone-pipeline-port | Pipeline ports drift fastest at the sub-agent contract boundary (memory-bootstrap section, JSON return shape, scope-bounds breadth) - always compare side-by-side against the FRESHEST local convention (the most recently ported peer pipeline), not the source repo, before declaring drift.

## panel-refresh-2026q2-e2 (2026-05-20)
- Pure palette-refactor diffs are low AI-invariant-violation risk (AI-1..AI-10, AI-14, AI-15 all N/A); concentrate the scan on AI-11 (shorthand Qt enums in new UI code), AI-12/AI-13 (color token discipline), and Axis 7 (test scope gaps).
- Incomplete extraction is the dominant failure mode for tokenization milestones: two structurally identical call sites in the same function (early-return branch vs. normal-return branch) where only one was migrated. Always grep the source file for the old literal after reviewing the diff — `grep -n '"#888888"' app.py` would have surfaced this immediately.
- Test scope gap pattern: a new regression guard that scans a rendered string (APP_STYLESHEET) passes even when an orphaned raw literal exists in the source file (app.py:364). Guard tests for PyVista color call sites must scan source text, not the rendered stylesheet string.
