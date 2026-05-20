# Phase 4 -- Rectify

**Goal:** convert the critic's findings into shipped fixes (CRITICAL+HIGH
mandatory, MEDIUM when cheap, LOW deferred), with `pytest tests/ -q` green,
on a single rectification commit.

This phase formalizes CONTEXT.md section 6 Phase 4 ("Remediation Sonnet --
MUST/SHOULD/SKIP, new tests, single commit") -- but defaults to running
in the main session because the main session can pause for user input on
unresolved blockers, and sub-agents cannot.

## Why this phase runs in the main session (not a sub-agent)

- Needs full repo write access and the ability to commit.
- Needs the user's review surface (the user is in the main session).
- Needs to call out unresolved blockers and pause for input -- sub-agents return one bundle and can't pause.
- The Implementer is biased toward defending its design; the Critic is biased toward escalation.  The main session sits between them and is the natural rectifier.

If the user explicitly says "delegate rectification to a sub-agent",
that's allowed — but the sub-agent must NOT be the one that did the
implementation.  Dispatch a fresh agent (any general-purpose Sonnet) with
explicit inputs `{ID}` and `{CRITIQUE_PATH}`, plus the explicit invariant
"abort if you wrote the implementation".  Phase 4 rectification has no
dedicated sub-agent body — it lives in the main session because it needs
to commit and pause for user input.  If you must delegate, write the
fresh agent's instructions inline at dispatch time; do NOT carry a stale
agent-prompts file.

## Re-verification protocol (REQUIRED -- runs before any fix)

The critic worked from a snapshot of the diff.  Between Phase 3 emit and
Phase 4 start, the repo state may have shifted (e.g. a parallel commit).
Every CRITICAL and HIGH must be re-verified against the live code:

For each finding:
1. Read the cited `file:line` end-to-end (not just the line -- the surrounding 30 lines).
2. Confirm the issue is still present.
3. If the issue is no longer present (already fixed, or the cited line moved): mark the finding as **invalidated** in `state.invalidated_findings` with a one-line reason.  Do NOT silently drop it.
4. If still present: proceed to fix.

Use `--append` (NOT `--set`) when recording invalidations one at a time —
`--set` replaces the entire list, which would clobber prior entries:
```bash
.venv/Scripts/python.exe .claude/scripts/milestone-pipeline/checkpoint.py {ID} --append invalidated_findings='"H3"'
```
The same applies to `fixed_findings` and `deferred_findings` below.

A finding-invalidation rate >40% means the critic prompt is broken (or the
critic was fed a stale diff).  Log this as a meta-issue but do not block
the pipeline; tune the prompt next iteration.

## Fix priority

| Severity | Action | Block ship? |
|---|---|---|
| CRITICAL | Fix this commit.  Add a regression-guard test. | YES |
| HIGH | Fix this commit.  Add a regression-guard test if the critic proposed one. | YES |
| MEDIUM | Fix this commit if the fix is <=30 LOC AND the test surface is small.  Otherwise defer with a one-line rationale in `state.deferred_findings`. | NO |
| LOW | Defer.  Record in `state.deferred_findings` for the next milestone planning session. | NO |

Deferred findings become research input for the next milestone -- that's
the institutional memory loop.

## Regression-guard tests

For every CRITICAL + HIGH finding that proposed a regression-guard test,
write that test BEFORE writing the fix.  The test should fail on `main`
pre-fix and pass on `main` post-fix.  Test placement follows the file the
bug is in:

| Bug location | Test location |
|---|---|
| `surfaces.py` (generator math) | `tests/test_mesh_generators.py` |
| `surfaces.py` (helper -- `_marching_cubes_to_polydata`, `_grid_to_polydata`) | `tests/test_grid_helpers.py` |
| `parameters_panel.py` (slider tick<->value) | `tests/test_parameters_panel.py` |
| `view_panel.py` (clip math) | `tests/test_clip_domain.py` |
| `app.py` / `appearance_panel.py` (Qt wiring) | No test path -- AI-2 explicitly forbids pytest-qt.  Document the manual verification step in the commit body. |
| `surfaces.py` (marching-cubes empty-field error) | `tests/test_marching_cubes_empty.py` |

If a new test would need Qt, it does NOT go in.  Manual launch is the only
verification for Qt-wired logic (CONTEXT.md section 9, AI-2).

## The fix loop

1. Pick the highest-severity unaddressed finding.
2. Read `file:line` end-to-end (re-verification already did this -- re-use that read).
3. Write the regression-guard test (if applicable).
4. Make the fix.
5. Run only the affected tests: `.venv/Scripts/python.exe -m pytest tests/test_<area>.py -v`.
6. If green, move to next finding.  If red, fix.  Capped at 3 inner iterations per finding -- beyond that, escalate to the user.
7. After all CRITICAL + HIGH + chosen MEDIUM are fixed: `.venv/Scripts/python.exe -m pytest tests/ -q` (full suite, currently 165 tests).
8. If the full suite is red, fix until green.  Capped at 3 outer iterations -- beyond that, escalate.
9. **Off-screen render verification** per CONTEXT.md section 10 if the fix touched a generator or render path: re-render the affected surface(s) to `/tmp/check-*.png` and Read each PNG to visually confirm.

## The rectification commit

Single commit (NOT amended onto Phase 2 -- separate commit so the
rectification work is auditable).  Subject:

```
rect({ID}): close C1, H1, H2, M1
```

(Replace `C1, H1, H2, M1` with the actual severity-id list of fixes in this
commit.)

Body (optional but encouraged):
```
- C1: <one-line summary> (file:line)
- H1: <one-line summary> (file:line)
- H2: <one-line summary> (file:line)
- M1: <one-line summary> (file:line)

Deferred to next milestone:
- M2: <reason>
- L1, L2, L3: deferred (cosmetic)

Invalidated:
- H3: <reason for invalidation>
```

## After commit

1. `.venv/Scripts/python.exe .claude/scripts/milestone-pipeline/checkpoint.py {ID} complete`.  State terminal.
2. Print a final 5-line summary to the user: milestone id, total findings, fixed/deferred counts, link to the critique, link to the rectification commit.

**Do NOT auto-push.**  This repo works directly on `main` per CONTEXT.md
section 12, but `git push` is a manual user step (single-developer
cadence).  The pipeline never pushes -- the user pushes when ready.

## Update the critique file

Append a footer to the critique:

```
---

## Rectification status (filled in Phase 4)

- **Commit:** {sha}
- **Fixed:** C1, H1, H2, M1
- **Invalidated on re-verification:** H3 (reason: <one line>)
- **Deferred to next milestone:** M2, L1, L2, L3
- **Test additions:** {file:line list}
```

This footer is the only modification allowed to the critique
post-creation.

## Don'ts

- **Don't fix all LOWs.**  They're deferred deliberately; the deferral list is the input to the next milestone's research phase.
- **Don't bundle unrelated cleanups into the rectification commit.**  Scope is the critique findings.  Other cleanups go on a separate commit BEFORE or AFTER.
- **Don't `git commit --amend`** the Phase 2 commit.  The rectification audit trail requires a fresh commit.
- **Don't skip the full suite.**  Per-file test runs miss cross-module breakage.
- **Don't push before all CRITICALs are closed.**  If a CRITICAL escalates and can't be closed, the pipeline stays in `rectify-running` state and the user resolves the blocker.
- **Don't lift CONTEXT.md section 9 non-goals silently.**  If a finding says "the app needs QSettings persistence", note it and defer -- adding QSettings is its own milestone, not a sneak-in fix.
