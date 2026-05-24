# Anchor-updater report — restructure-feature-subpackages-2026q2-r2 batch 1

**Run at:** 2026-05-23T22:53:00Z (inline by main session — dispatched anchor-updater agent socket-timed-out at ~43m wall-clock; main session completed the remaining work)
**Verdict:** PASS

## Updates applied

- **MOVES.md** — appended r2 batch 1 section (lines 57-66) documenting the M+1 shim cleanup. Each of the 4 deleted shims is mapped to its canonical `panels.*` path, plus the deleted test file. (Edit landed before agent socket timeout; verified in git status.)
- **Root CLAUDE.md (symlink to AGENTS.md)**: no `file:line` references to the 4 deleted shim files exist in AGENTS.md (the shims were never primary code; they were not referenced by name in agent-orientation docs).
- **CONTEXT.md, README.md**: NOT edited in batch 1 per PLAN.md §6 — those are reserved for batch 9.
- **Agent-memory CORRECTION blocks**: NOT appended in this batch — the 10+ agent-memory references to the deleted shims are HISTORICAL records of r1's shim mechanism. They correctly describe what the shims DID; future agents reading them will see them as r1-era documentation. The MOVES.md batch 1 entry is the authoritative record that the shims are now gone. Per scout-C §7, historical lessons.md content is append-only — no CORRECTION block is needed for "this thing was removed" because the future state (MOVES.md) is the authoritative answer.

## verify-anchors.py output

```
no symbol-map entries (batch=1); nothing to verify
```

Correct behavior — batch 1 is deletion-only with no symbol-map entries.

## Note on agent socket timeout

The originally-dispatched `repository-architect-anchor-updater` agent ran ~43 minutes before its socket closed unexpectedly. The MOVES.md edit (the substantive work) landed before timeout. Main session completed the remaining items (verify-anchors run + this report) inline. Lesson recorded for the anchor-updater agent's `lessons.md`: a deletion-only batch with M+1 shim cleanup involves walking ALL agent-memory files for historical references; this walk is large in repos with many prior pipeline runs. Consider a fast-path optimization for batches with zero symbol-map entries (verify-anchors PASS + minimal MOVES.md edit + skip the agent-memory walk).

## Outstanding for batch 9 anchor-updater (recorded for future)

- README.md "Extending the app" section will still reference `parameter_grid_panel.py` import path — but this is the panels/ canonical path (`panels/parameter_grid_panel.py`), so it's CORRECT. No action needed for batch 9 specifically related to batch 1's deletions.
- CONTEXT.md references to "the 4 root shims" if any will need updating to past-tense documenting r1+r2 history. Verify in batch 9.
