# `/repository-architect` anti-patterns

Restructure-specific rationalizations to refuse. The architect (and every sub-agent) should cite these by number when refusing.

## Cross-cutting anti-patterns (inherited from milestone-pipeline + scout-A blueprint)

| # | Pattern | Why It Breaks | Guard |
|---|---|---|---|
| X1 | Critic elevates severity to look productive | Artificial inflation masks real risk | Severity calibration rule: CRITICAL requires invariant violation or design dead-end |
| X2 | Implementer writes critique sections | Phases must not overlap; critic independence is required | Scope-bounds forbid implementer from reading/writing critique.md |
| X3 | Concurrent agent dispatch in same phase | Race conditions on state.json | Orchestrator enforces one dispatch per phase except documented parallel fan-outs |
| X4 | Skipping init-state.sh | state.json doesn't exist; validators crash | init-state.sh MUST be called once per {ID} |
| X5 | Phase transition without checkpoint.py | State machine desync; resume logic breaks | Only checkpoint.py may transition phases |

## Restructure-specific anti-patterns (scout-C §10)

| # | Tempting belief | Reality + violated source | Refusal |
|---|---|---|---|
| R1 | "We can refactor and add features in the same PR." | Defeats `git bisect`, breaks rollback. Violates small-step discipline (Fowler) and clean-baseline rule (scout-C §1). | "Land the restructure; merge; then land the feature in a follow-up." |
| R2 | "The tests will catch any regression." | Green tests prove the suite passes — not that it exercises the same paths. Collection count, coverage shape, fixture visibility all matter. | "Run the Phase 4 parity-verifier after every batch." |
| R3 | "We can fix the imports later." | Violates "the system runs at all times" (Branch by Abstraction). Every commit must be green. | "Imports are part of green. There is no 'later' that is safer than 'now.'" |
| R4 | "Let's just delete the old file, no shim needed." | Breaks `.claude/notes/**`, agent memory, in-flight feature branches. Violates expand-contract (Parallel Change). | "Shim it for one milestone. Removal is a separate commit referencing this one's hash." |
| R5 | "Let's do it in one big-bang commit." | Unreviewable and unbisectable. Violates strangler-fig "small, lower-risk replacements." | "Reviewers see the whole thing via PLAN.md and the commit chain." |
| R6 | "Sed will be fine for these import rewrites." | Python lexical structure: regex cannot distinguish `from foo import bar` from `"from foo import bar"`. | "Use libcst (rewrite-imports.py). Sed cannot tell strings apart from imports." |
| R7 | "Star-imports keep the shim shorter." | Defeats stacklevel-based DeprecationWarning pinpointing; defeats static analysis. | "Use the `__getattr__` shim from shim-templates.md." |
| R8 | "We don't need a rollback plan; we have git." | Without a pre-documented and pre-tested rollback, a panicked revert can take down adjacent unrelated work. | "Write ROLLBACK.md in Phase 3. Test it in a scratch worktree." |
| R9 | "The CLAUDE.md / .claude/notes update can wait." | Stale path references actively mislead the next agent session. | "Phase 4 step 4c is part of every batch, not a follow-up." |
| R10 | "We're internal-only; no deprecation needed." | Internal != no callers. Notebooks, scratch scripts, agent memory, in-flight branches all count. | "One milestone of shim is the cost of safety." |
| R11 | "Skipping the design-adversary saves time." | Pre-execution adversary is the cheapest safety gate; post-execution rollback is far more expensive. | "The design-adversary is mandatory; budget ~5 min." |
| R12 | "We can auto-execute Phase 4 if dry-run is GREEN." | Restructures are user-authorized, not orchestrator-authorized. | "GATE 3 is a hard user `[y]`. Always." |
| R13 | "The anchor-updater can run once at the end." | Per-batch anchor work is cheap and catches stale references batch-by-batch. End-of-restructure runs leave many batches' worth of breakage in `.claude/notes/`. | "Run per batch. The end-of-restructure run is a cleanup, not a substitute." |
| R14 | "We don't need a parity-verifier — pytest already tells us if things broke." | The parity-verifier checks collection count, coverage shape, cycle set, import-time, shim integrity, and star-imports. Plain pytest catches none of these except a true test failure. | "Parity-verifier runs after every batch. Period." |
| R15 | "Bowler is the safe-refactor tool we need." | Bowler is archived and lib2to3 is deprecated. | "Use LibCST. Bowler is dead." |

## When to add a new anti-pattern

Append a new row to the appropriate table above when:
1. The execution-critic catches the same anti-pattern in two consecutive restructure runs (so it's a recurring rationalization, not a one-off).
2. A user-gate override at GATE 3 or GATE 4 turns out to have been a mistake (in the next restructure's audit, document the rationalization that was accepted).
3. A new tool deprecation or pattern shift in 2026+ Python practice (the refactor-pattern-scout's brief surfaces it).

## Memory append protocol

Anti-patterns are sticky. When a sub-agent encounters one, append to its `lessons.md` so future runs of that agent recognize it instantly. See `memory-update-protocol.md` for format.
