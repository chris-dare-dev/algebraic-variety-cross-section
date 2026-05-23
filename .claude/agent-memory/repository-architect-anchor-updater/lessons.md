
## Lesson from restructure-full-audit-2026q2-r1 batch 1 (2026-05-23)
- Anchor surface previously missed: none — Batch 1 is zero-move; verify-anchors.py confirmed "no symbol-map entries (batch=1); nothing to verify"
- MOVES.md format adjustment: MOVES.md creation is deferred to the batch that introduces the first file move (Batch 4 in this restructure). Do not create MOVES.md for zero-move batches even though it is listed in the tree diff — the tree diff entry explicitly annotates "Batch 4; created by anchor-updater on Batch 4's run".
- Agent-memory old-path references for a FUTURE batch's moves are NOT stale until that batch runs. When grepping agent-memory for old paths, cross-check symbol-map to confirm the moves have actually happened yet; if not, the references are currently-correct and should not receive CORRECTION blocks.
- CORRECTION block placement: add CORRECTION blocks in the batch N anchor-updater run whose symbol-map lists the move, not in any earlier batch's run.

## Lesson from restructure-full-audit-2026q2-r1 batch 2 (2026-05-23)
- Anchor surface previously missed: none — Batch 2 is zero-move (adds AGENTS.md, CLAUDE.md symlink, pyproject.toml only); verify-anchors.py confirmed "no symbol-map entries (batch=2); nothing to verify".
- New surface added by Batch 2: AGENTS.md is a new agent-orientation file. It contains no file:line references (uses symbol-name and section-name anchors per scout-C §7 strategy A), so it creates zero anchor-rot surface at creation time.
- CLAUDE.md as symlink: when CLAUDE.md is a symlink to AGENTS.md (not a standalone file), verify via `readlink` + `cat` first line — both checks are needed. A valid symlink with wrong target is a silent failure.
- pyproject.toml alignment check: always cross-check `[project].dependencies` specifiers against `requirements.txt` at creation time. Run a base-name normalization (lowercase + replace - with _) before set-comparison — PySide6 vs pyside6 would otherwise cause false mismatches.
- Historical milestone lessons referencing panel paths (appearance_panel, view_panel, etc.) are pre-move artifacts. Do not treat them as stale until batch=4 (the move batch) has run. Confirmed correct behavior in this batch run.

## Lesson from restructure-full-audit-2026q2-r1 batch 3 (2026-05-23)
- Anchor surface previously missed: none — Batch 3 is zero-move (in-place BG_GRID_SCENE fix); verify-anchors.py confirmed "no symbol-map entries (batch=3); nothing to verify".
- In-place bug-fix batches can still produce CORRECTION-worthy agent-memory updates: the current-state-auditor lesson described BG_GRID_SCENE as a live gap. When a batch closes a gap that was recorded as open in agent-memory, always append a CORRECTION block — even for zero-move batches.
- CONTEXT.md authorization scope: PLAN.md §2 tree diff is the authoritative list of per-batch CONTEXT.md edit authorization. Batch 3 introduced a new QSS role (`grid-scene`) but PLAN.md only authorized CONTEXT.md edits in Batch 1 and Batch 4. Surfaced as OUTSTANDING; the Batch 4 anchor-updater should fold the `grid-scene` role mention into §4.3b during its authorized CONTEXT.md pass.
- Stale fact vs. missing fact: a CONTEXT.md section that lacks a new pattern introduced by the current batch is a "missing fact", not a "stale reference". Only stale references (pointing to old paths/line-numbers that no longer exist) justify an out-of-authorization edit. Missing facts are flagged in the report and deferred to an authorized batch.
