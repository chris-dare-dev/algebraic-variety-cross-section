# Phase 2 -- Implement

**Goal:** turn the merged research synthesis into committed code on `main`
(or a parallel-explorer branch), with `pytest tests/ -q` green.

This phase is the formalization of CONTEXT.md section 6 Phase 2
("Synthesize, implement, verify with off-screen renders").

## Read first

The main session reads BOTH briefs end-to-end before deciding execution
path.  Do NOT read partial briefs.  The "Recommended approach" sections are
often complementary, not redundant -- agreement is the strongest signal;
disagreement is the most informative.

## Capture pre-milestone HEAD BEFORE any commits

Phase 3 frontend-detect uses `implementation_base` as the diff base.  If
you skip this step, the frontend critic silently never fires.

```bash
.venv/Scripts/python.exe .claude/scripts/milestone-pipeline/checkpoint.py {ID} --set implementation_base="\"$(git rev-parse HEAD)\""
```

## Inline vs Delegated decision

| Predicate | Path | Notes |
|---|---|---|
| Merged plan <=500 LOC across <=5 files **AND** no novel-pipeline scaffolding (e.g. introducing a new mesh helper class) **AND** no new variety family being introduced (those follow CONTEXT.md section 6 directly) | **Inline** — implement in main session | Faster, less coordination, easier to course-correct mid-flight |
| Otherwise | **Delegated** — dispatch 1 milestone-implementer with branch `impl-{ID}-solo` | Optional 2x for genuine disagreement; rarely justified at this repo's size |

**Default for this repo: Inline.**  The repo is small, single-developer,
and works directly on `main` per CONTEXT.md section 12.  The Delegated path
exists for future-proofing -- it's the right move when a milestone is large
enough that the main-session context window becomes a constraint, OR when
the user explicitly asks for parallel exploration.

**User override:** if the user asked for "parallel implementers" /
"explorer branches" / "two-implementer synthesis" explicitly, go Delegated
regardless of size.

## Inline path

1. Read both briefs.
2. Write a 5-bullet plan to `.claude/notes/milestones/{ID}/artifacts/implementation-plan.md` (the Rectifier reads this in Phase 4 to confirm the implementation matched intent).
3. Implement.  Commit small (<=200 LOC per commit when feasible).  Subject line format: `{type}({ID}): {what}` -- `type` in `feat|fix|refactor|test|docs|perf|chore`.
4. Run `.venv/Scripts/python.exe -m pytest tests/ -q`.  Fix anything that breaks until green (current suite is 165 tests, ~4 s).
5. **Off-screen render verification** per CONTEXT.md section 10: render the affected surfaces via `pv.OFF_SCREEN = True` to `/tmp/check-*.png` and Read the PNG to visually confirm.  Never construct `MainWindow()` under `QT_QPA_PLATFORM=offscreen` (AI-3 -- VTK GL context segfaults during construction).
6. Run `.venv/Scripts/python.exe .claude/scripts/milestone-pipeline/checkpoint.py {ID} implement-complete` (`.venv/bin/python` on POSIX).

## Delegated path

Dispatch 1 OR 2 `milestone-implementer` agents (the agent body at
`.claude/agents/milestone-implementer.md` IS the prompt — dispatch by
name; the orchestrator passes inputs via the Task tool).

| When 2 implementers | When 1 implementer |
|---|---|
| The two research briefs disagreed on approach AND both approaches are credible | Briefs agreed; OR milestone is too small to justify duplicate work |
| User explicitly asked for parallel exploration | Default for the Delegated path |

Each implementer receives:
- Its assigned brief (agent-a -> implementer-a, agent-b -> implementer-b, or solo)
- The full Implementer prompt
- The branch name to use: `impl-{ID}-solo` (single) or `impl-{ID}-a` / `impl-{ID}-b` (two-way)
- An instruction to run `.venv/Scripts/python.exe -m pytest tests/ -q` before declaring done

**Important.**  Worktree isolation is NOT used in this repo by default --
the `.venv` is gitignored, isolation breaks the venv, and this repo's flat
single-`main` workflow per CONTEXT.md section 12 makes branch synthesis
trivial.  Dispatch implementers without worktree isolation (use a regular
branch).

When implementer(s) return:
- **Single implementer:** review the branch commits, fast-forward merge to `main` if green.
- **Two implementers:** read both branches end-to-end.  Synthesize into one commit on `main`.  The synthesis itself is small (<=200 LOC of integration glue) and stays inline; the bulk of the code is one of the two branches rebased onto `main`.  Delete the explorer branches after merge.

Either way, `pytest tests/ -q` must pass on `main` before checkpoint.

## Tests are part of implementation

The Implementer writes tests for new code.  The Rectifier writes
regression-guard tests for critic findings.  They are NOT the same surface.
Don't defer test-writing to Phase 4 -- the Phase 3 critic uses test
coverage as one of its 10 axes ("Test coverage gap"), and the absence of
tests at Phase 3 fan-out generates noise findings.

This repo's test conventions (CONTEXT.md section 2, AI-2):
- All tests under `tests/`, Qt-free (pure NumPy / PyVista / scikit-image / static math).
- No `pytest-qt`, no `QT_QPA_PLATFORM=offscreen`.
- Smoke tests in `tests/test_mesh_generators.py` cover every generator.
- Static math (slider tick<->value) in `tests/test_parameters_panel.py`.
- Domain clipping in `tests/test_clip_domain.py`.

## Qt panel and generator conventions

If the milestone touches `appearance_panel.py`, `view_panel.py`,
`parameters_panel.py`, `styles.py`, `app.py`, or `surfaces.py`:
re-read AI-1, AI-6, AI-7, AI-8, AI-9, AI-10, AI-11, AI-12, AI-13, AI-14,
AI-15 in `.claude/references/app-invariants.md` before proceeding.  The
canonical descriptions live there; don't rely on summaries that drift.

CONTEXT.md section 9 explicit non-goals (no QSettings persistence, no
STL export, no first-launch auto-render, no pytest-qt UI tests) are
decisions, not oversights.  Don't lift them silently.

## Commit message convention

```
{type}({ID}): {short imperative summary, <=72 chars}

{optional body, wrapped at 80, explaining the WHY}

{optional footer with refs to research briefs}
```

Examples:
```
feat(panel-refresh-2026q2-e1): lift Enriques sawtooth via second Taubin pass
fix(panel-refresh-2026q2-e1): close H1 -- guard against bounds padding overflow
refactor(panel-refresh-2026q2-e1-rect): close C1, H2, M1 from adversary critique
```

## Checkpoint

Record the commit range and advance state:

```bash
.venv/Scripts/python.exe .claude/scripts/milestone-pipeline/checkpoint.py {ID} --set implementation_commit_range="\"<base>..<HEAD>\""
.venv/Scripts/python.exe .claude/scripts/milestone-pipeline/checkpoint.py {ID} implement-complete
```

Phase 3 critic reads from `state.implementation_commit_range`.

## Do NOT auto-push

This repo works directly on `main`, but `git push` is a manual user step
(single-developer cadence per CONTEXT.md section 12).  The pipeline never
pushes -- the user pushes when the rectification commit lands and they're
ready.
