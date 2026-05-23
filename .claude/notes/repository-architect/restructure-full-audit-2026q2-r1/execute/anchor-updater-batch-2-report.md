# Anchor updater report — restructure-full-audit-2026q2-r1 batch 2

**Run at:** 2026-05-23T00:00:00Z (UTC)
**Verdict:** PASS

## Updates applied

- MOVES.md: not created — Batch 2 has zero file moves; MOVES.md creation is deferred to Batch 4 per PLAN.md section 2 (tree diff annotation: "Batch 4; created by anchor-updater on Batch 4's run").
- root CLAUDE.md: confirmed symlink only (target: AGENTS.md) — no `file:line` references to update; symlink valid and resolves correctly.
- CONTEXT.md: not authorized by PLAN.md for Batch 2 (Batch 4 owns CONTEXT.md §4 + §10 updates per PLAN.md section 2 tree diff).
- README.md: not authorized by PLAN.md for Batch 2 (Batch 4 owns README.md updates per PLAN.md section 2 tree diff).
- agent-memory CORRECTION blocks appended to: none — no old paths moved in Batch 2; all panel-path references in agent-memory are future-batch=4 plans and are currently-correct references (per lessons.md: "NOT stale until that batch runs").

## Batch 2 file verification

### AGENTS.md
- Present: YES (`/AGENTS.md`, 143 LOC — within Evaluator FAIL #21 limit of 200 lines)
- Content: valid AI-agent orientation doc; points to CONTEXT.md for deep context; covers module map, build/test commands, AI invariants, code style, testing, security, off-limits paths.
- `file:line` references in AGENTS.md: NONE (all references are symbol-name or section-name style, per scout-C §7 strategy A). No anchor rot surface created by AGENTS.md itself.

### CLAUDE.md
- Present: YES (symlink)
- Symlink target: `AGENTS.md` (confirmed via `readlink`)
- Symlink resolves: YES (content reads as AGENTS.md header)
- Verdict: PASS — symlink is valid per HumanLayer + agents.md spec (PLAN.md section 2 notation: `+ CLAUDE.md → AGENTS.md [Batch 2; symlink per HumanLayer + agents.md spec]`).

### pyproject.toml
- Present: YES (`/pyproject.toml`, ~25 LOC)
- `[project].dependencies` vs `requirements.txt` cross-check:
  - requirements.txt packages (9): PySide6, pyvista, pyvistaqt, numpy, numba, qtawesome, libcst, pydeps, coverage
  - pyproject.toml dependencies (9): PySide6, pyvista, pyvistaqt, numpy, numba, qtawesome, libcst, pydeps, coverage
  - Version specifiers: IDENTICAL for all 9 packages
  - ALIGNED: YES — no drift between the two dependency declarations.
- `[project.scripts]`: absent by design (preserves `python app.py` invocation per PLAN.md Batch 2 notes).
- `[build-system]`: setuptools>=68, legacy backend — correct for a flat-layout project with no src/ migration.

## Historical-stale references (acceptable, no edit)

- Panel-path references (`appearance_panel`, `parameter_grid_panel`, `parameters_panel`, `view_panel`) found in:
  - `.claude/notes/repository-architect/restructure-full-audit-2026q2-r1/design/symbol-map.json` — FUTURE batch=4 plans, not stale (moves have not occurred yet)
  - `.claude/notes/repository-architect/restructure-full-audit-2026q2-r1/design/PLAN.md` — forward-looking design artifact, not stale
  - `.claude/agent-memory/roadmap-decomposer/lessons.md` — historical lesson from prior milestone, closed artifact
  - `.claude/agent-memory/roadmap-refiner/lessons.md` — historical lesson from prior milestone, closed artifact
  - `.claude/agent-memory/milestone-researcher/lessons.md` — historical lessons from prior milestones, closed artifact
  - `.claude/agent-memory/milestone-frontend-ux-critic/lessons.md` — historical lesson, closed artifact
  - `.claude/agent-memory/milestone-adversary-critic/lessons.md` — historical lessons, closed artifact
- Classification: all references are pre-move (batch=4 has not run); CORRECTION blocks are NOT warranted at this stage per lessons.md anchor-updater guidance.

## Outstanding (flagged for follow-up)

- None. All surfaces are within scope and correctly handled.
- README.md and CONTEXT.md stale-reference updates are authorized for Batch 4 only (PLAN.md section 2 tree diff). No action needed now.

## verify-anchors.py output

```
no symbol-map entries (batch=2); nothing to verify
```
