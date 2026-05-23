# Agent memory update protocol

All 10 `repository-architect-*` agents have `memory: project` and a dedicated `.claude/agent-memory/<agent-name>/` directory.

## Bootstrap (every dispatch)

Before doing any work, the agent reads its `lessons.md` IF AND ONLY IF the lessons are relevant to the current restructure's scope. Skip if unrelated — don't load memory for its own sake.

If `lessons.md` exceeds 200 lines, load only the first 50 lines + the most-recent 5 lessons. Leave a `## TODO: compact` marker at the top so the user knows to compact during a non-pipeline session.

## Append (end of every dispatch)

Use Bash heredoc, NOT the Write tool:

```bash
cat >> .claude/agent-memory/<agent-name>/lessons.md <<'LESSON'

## Lesson from {ID} ({ISO_DATE})
- Observation 1
- Observation 2
- Suggested guard / rule for future runs
LESSON
```

Why heredoc not Write: Write would clobber the file; heredoc appends atomically (POSIX `>>`).

## What's worth a lesson

Good lessons:
- New anti-pattern that escaped the audit (refactor-pattern-scout doesn't know it yet).
- AVC-specific shim quirk (VTK lazy-import, numba threading layer, qtawesome cold-boot).
- False-positive pattern from a verification check (so the parity-verifier doesn't re-flag it).
- A surprising AI-1..AI-15 subtlety that needed clarification mid-restructure.
- An import-graph cycle that only appears under a specific entry point.

Not worth a lesson:
- Generic Python best practices ("use type hints").
- Things already documented in CONTEXT.md or app-invariants.md.
- Single-restructure noise that wouldn't repeat.

## Compaction protocol

When `lessons.md` exceeds 200 lines:
1. The agent leaves a `## TODO: compact` marker at the top.
2. During a non-pipeline session, the user (or a dedicated compactor) runs:
   ```bash
   # Manual compaction:
   #   1. Read lessons.md end-to-end.
   #   2. Move pre-compaction content to archive/lessons-YYYY-MM-DD.md (preserve verbatim).
   #   3. Rewrite lessons.md as: 30-line summary + most recent 5 lesson entries.
   ```
3. The archive directory is `.claude/agent-memory/<agent-name>/archive/`.

This pipeline does NOT auto-compact during execution — compaction is a separate, user-supervised activity.

## CORRECTION blocks (anchor-updater only)

The anchor-updater agent is the only one permitted to MODIFY other agents' `lessons.md` files, and only by APPENDING `## CORRECTION` blocks:

```bash
cat >> .claude/agent-memory/<other-agent>/lessons.md <<'CORR'

## CORRECTION 2026-05-23 (from restructure-panels-2026q3-r1 batch 1)
- The path `appearance_panel.py:340` referenced in a prior lesson moved to `panels/appearance.py:340` as part of this restructure.
- See MOVES.md @ section "2026-05-23 — restructure-panels-2026q3-r1 batch 1".
CORR
```

NEVER rewrite or delete existing lesson lines. The CORRECTION block is appended; future reads see both the original lesson AND the correction.

## Memory directories

```
.claude/agent-memory/
+-- repository-architect-current-state-auditor/lessons.md
+-- repository-architect-best-practices-scout/lessons.md
+-- repository-architect-refactor-pattern-scout/lessons.md
+-- repository-architect-design-adversary/lessons.md
+-- repository-architect-dry-run-validator/lessons.md
+-- repository-architect-implementer/lessons.md
+-- repository-architect-parity-verifier/lessons.md
+-- repository-architect-anchor-updater/lessons.md
+-- repository-architect-execution-critic/lessons.md
+-- repository-architect-test-suggester/lessons.md
```

Each directory may contain an `archive/` subdirectory once compaction has occurred.

## Cross-agent memory sharing

Agents do NOT read each other's `lessons.md`. The orchestrator (this slash command) passes context between phases via state.json and artifact files (PLAN.md, parity-diff.md, etc.), not via cross-agent memory peeking.

Exception: the anchor-updater MAY append CORRECTION blocks to other agents' `lessons.md` (see above).
