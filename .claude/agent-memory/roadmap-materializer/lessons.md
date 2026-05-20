# lessons — roadmap-materializer

Accumulates 2-5-bullet lessons per roadmap run.  Appended via heredoc, never overwritten.  Compact only when exceeding 200 lines.

## panel-refresh-2026q2 (2026-05-20)
- S002 (placeholder remains) was the primary blocker on first validator pass: `{{FIRST_MILESTONE}}` was left in the handoff section; always substitute it with `<slug>-e1` before running the validator.
- S005 (epic id pattern) produced a false positive for `/tmp/check-enriques-post.png` in backticks inside section 6.3 acceptance signals — the validator scans the entire `decompose` body for backtick-quoted strings containing `-e`; use double-quotes for file path references in acceptance signal prose to avoid false positives.
- The roadmap arrived at Phase 4 in excellent shape: all 8 canonical sections populated, MoSCoW cap exact at 60%, RICE scores and DAG validated by Phase 3; only the two trivial validator fixups above were needed.
- Now lane contains 2 epics (e1: background flash fix, 2 stories; e5: bbox readout, 2 stories); first epic is e1 — use this for the CONTEXT.md §6 handoff offer text.
