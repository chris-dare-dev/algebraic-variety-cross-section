# lessons -- milestone-adversary-critic

2026-05-20 | milestone-pipeline-port | Pipeline ports drift fastest at the sub-agent contract boundary (memory-bootstrap section, JSON return shape, scope-bounds breadth) - always compare side-by-side against the FRESHEST local convention (the most recently ported peer pipeline), not the source repo, before declaring drift.

## panel-refresh-2026q2-e2 (2026-05-20)
- Pure palette-refactor diffs are low AI-invariant-violation risk (AI-1..AI-10, AI-14, AI-15 all N/A); concentrate the scan on AI-11 (shorthand Qt enums in new UI code), AI-12/AI-13 (color token discipline), and Axis 7 (test scope gaps).
- Incomplete extraction is the dominant failure mode for tokenization milestones: two structurally identical call sites in the same function (early-return branch vs. normal-return branch) where only one was migrated. Always grep the source file for the old literal after reviewing the diff — `grep -n '"#888888"' app.py` would have surfaced this immediately.
- Test scope gap pattern: a new regression guard that scans a rendered string (APP_STYLESHEET) passes even when an orphaned raw literal exists in the source file (app.py:364). Guard tests for PyVista color call sites must scan source text, not the rendered stylesheet string.

## graph-and-window-2026q2-e1 (2026-05-21)
- AI-3 analysis: vanilla QMainWindow (no QtInteractor) is safe under offscreen per AI-3's one-line rule. The ban is specifically on MainWindow (the app's class which hosts QtInteractor). Check zero-QtInteractor condition explicitly when a vanilla QMainWindow appears in a diff.
- Tool-parity gap pattern: when a milestone adds lighting params to app.py (e.g., ambient/diffuse), check whether the visual-scout template in agent-prompts.md was also updated to match. UPL-9 fixed the live app but the scout template only got the background fix (UPL-28), missing the lighting delta. Grep: `grep -A3 "add_mesh" .claude/references/frontend-uplift/agent-prompts.md` and compare params against app.py's add_mesh call.
- QDockWidget ownership: QDockWidget.setWidget() transfers C++ ownership. QDockWidget has no takeWidget() (unlike QMainWindow.takeCentralWidget()). The correct workaround is panel.setParent(None) in a finally block before the host goes out of scope. If this pattern appears, flag absence from CONTEXT.md §8 as a LOW.
- Severity calibration: a 241-LOC tooling/script diff (no new generators, no new ParamSpecs, no new surfaces) is unlikely to produce more than 1 MEDIUM. Axis 7 (test coverage) and Axis 1 (AI invariants) are both N/A for render-script changes — concentrate scan on Axis 8 (offscreen correctness) and Axis 5 (color token discipline).
