# Phase 3 — Pre-flight (baseline snapshot + dry-run + user gate)

**Goal:** capture an authoritative pre-restructure baseline AND predict the post-restructure import-graph delta WITHOUT moving any files. This is the cheapest place to catch "all tests pass but 20 tests now silently no-op."

## Step 0 — Hard cleanliness gate

Before anything else:
```bash
git status --porcelain | grep -q . && { echo "ERROR: working tree not clean; commit or stash, then re-run"; exit 1; }
```

This is non-negotiable per scout-C §1.

## Step 1 — Precache baseline hook

```bash
bash .claude/hooks/repository-architect/precache-baseline.sh {ID}
```

Wraps `snapshot-baseline.py`. Captures pre-restructure:
- `baseline.collect.txt` — `pytest --collect-only -q`.
- `baseline.coverage.xml` — coverage XML from `coverage run -m pytest`.
- `baseline.imports.json` — pydeps JSON dump.
- `baseline.importtime.log` — `python -X importtime -c "import app"`.
- `baseline.starimports.txt` — grep for `import *`.
- `baseline.git_sha.txt` — `git rev-parse HEAD`.
- `baseline.symbols.json` — per-symbol location index.

If `pydeps` / `coverage` are missing, the snapshot writes a warning file and continues. PLAN.md should have proposed adding them — surface as a Phase 3 sub-gate.

## Step 2 — Persist restructure_base

```bash
.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py {ID} \
    --set restructure_base="\"$(git rev-parse HEAD)\""
.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py {ID} \
    --set baseline_dir='".claude/notes/repository-architect/{ID}/preflight/"'
```

This SHA anchors Phase 4 (diff range) and Phase 5 (critic input).

## Step 3 — Dispatch dry-run-validator

```
Agent: repository-architect-dry-run-validator
Inputs:
  {ID}
  {PLAN_PATH}
  {SYMBOL_MAP_PATH}
  {BASELINE_DIR}
  {DRY_RUN_PATH}  .claude/notes/repository-architect/{ID}/preflight/dry-run-validator-report.md
```

Uses LibCST + pydeps to predict the post-restructure import graph IN MEMORY (no files moved). Reports:
- New cycles introduced.
- Orphaned modules.
- Broken imports (no shim).
- conftest.py scope drift per scout-C §3.
- Predicted `pytest --collect-only` count delta.
- Star-import shadow risk (LibCST can't safely rewrite `import *`).
- Fan-in spikes (god-module risk).

Verdict: GREEN / YELLOW / RED.

## Step 4 — Write PREFLIGHT.md + ROLLBACK.md

Main session compiles `preflight/PREFLIGHT.md` (baseline + dry-run summary) and `preflight/ROLLBACK.md` (the rollback plan from PLAN.md §8 as a runnable artifact). The orchestrator also creates a `git tag` for the baseline so the user can navigate via tag name (not just SHA) during a panic-rollback. Run this once at Step 4 entry:

```bash
git tag "refactor-baseline-{ID}" $(checkpoint.py {ID} --get restructure_base)
```

ROLLBACK.md template:

```markdown
# Rollback plan — {ID}

**Baseline tag:** refactor-baseline-{ID}  (created by Phase 3 Step 4)
**Baseline SHA:** {restructure_base}

## Tier 1 — whole-restructure revert
git revert --no-commit {restructure_base}..HEAD
git commit -m "revert: roll back {ID}"

## Tier 3 — partial (per-module)
git checkout {restructure_base} -- <path>
git commit -m "revert: partial rollback of <module> from {ID}"

## Alternate Tier 1 (via tag) — easier to remember weeks later
git revert --no-commit refactor-baseline-{ID}..HEAD
git commit -m "revert: roll back {ID}"

## What rollback does NOT restore
- MOVES.md entries
- CLAUDE.md / CONTEXT.md edits
- Agent-memory CORRECTION blocks
```

Persist:
```bash
.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py {ID} \
    --set dry_run_report_path='".claude/notes/repository-architect/{ID}/preflight/dry-run-validator-report.md"'
.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py {ID} \
    --set dry_run_verdict='"GREEN"'  # or YELLOW or RED
.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py {ID} preflight-complete
bash .claude/hooks/repository-architect/summarize-phase.sh {ID} preflight-complete
```

## Step 5 — GATE 3

Surface to user:
```
Pre-flight complete for {ID}.
Baseline:
  - tests:  <N> collected
  - coverage: <X>%
  - import graph: <M> modules, <K> cycles
  - git SHA: <restructure_base>
Dry-run verdict: <GREEN | YELLOW | RED>
  - new cycles: <delta>
  - orphans:    <delta>
  - conftest scope drift: <list>
  - predicted collection delta: <delta>
Rollback: ROLLBACK.md ready (Tier 1 cmd: git revert --no-commit <base>..HEAD)

Continue to Execute? [y/n]
```

If verdict is RED and user says `[y]`, log the override in dispatch.log so Phase 5 critic has visibility.

## Anti-patterns to refuse

- Proceeding past Step 0 with uncommitted changes.
- Treating snapshot-baseline.py warnings (missing pydeps/coverage) as fatal — they're best-effort; the orchestrator surfaces a sub-gate.
- Skipping dry-run because "the design looked obvious."
- Advancing past GATE 3 when verdict is RED without explicit user `[y]` override.
