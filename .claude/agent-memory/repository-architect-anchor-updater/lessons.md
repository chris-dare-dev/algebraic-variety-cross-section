
## Lesson from restructure-full-audit-2026q2-r1 batch 1 (2026-05-23)
- Anchor surface previously missed: none — Batch 1 is zero-move; verify-anchors.py confirmed "no symbol-map entries (batch=1); nothing to verify"
- MOVES.md format adjustment: MOVES.md creation is deferred to the batch that introduces the first file move (Batch 4 in this restructure). Do not create MOVES.md for zero-move batches even though it is listed in the tree diff — the tree diff entry explicitly annotates "Batch 4; created by anchor-updater on Batch 4's run".
- Agent-memory old-path references for a FUTURE batch's moves are NOT stale until that batch runs. When grepping agent-memory for old paths, cross-check symbol-map to confirm the moves have actually happened yet; if not, the references are currently-correct and should not receive CORRECTION blocks.
- CORRECTION block placement: add CORRECTION blocks in the batch N anchor-updater run whose symbol-map lists the move, not in any earlier batch's run.
