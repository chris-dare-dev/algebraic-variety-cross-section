# State schema

`scripts/milestone-pipeline/init-state.sh`, `checkpoint.py`, and `status.sh`
all read/write `.claude/notes/milestones/{ID}/state.json`.  This file
defines the schema.

## Path

```
.claude/notes/milestones/{ID}/
+-- state.json                   # this schema
+-- research/
|   +-- agent-a-brief.md
|   +-- agent-b-brief.md
|   +-- (or agent-solo-brief.md for Single / Deep mode)
+-- artifacts/
    +-- implementation-plan.md   (inline path only -- main session writes)
    +-- implementer-a-deviations.md  (delegated path -- implementer writes if deviated)
    +-- implementer-b-deviations.md
    +-- adversary-critique.md    (Phase 3 critic output)
    +-- frontend-critique.md     (only if Qt panels touched)
    +-- oss-scout.md             (only when OSS scout fired)
```

The canonical critique location is
`.claude/notes/milestones/{ID}/artifacts/adversary-critique.md` -- this
repo follows the `.claude/notes/` convention used by every other
`/capability-scout`, `/frontend-uplift`, and `/roadmap` artifact.

## Schema

```json
{
  "id": "panel-refresh-2026q2-e1",
  "created_at": "2026-05-20T14:32:00Z",
  "updated_at": "2026-05-20T15:47:00Z",
  "phase": "research-complete",
  "phase_history": [
    { "phase": "init",                 "at": "2026-05-20T14:32:00Z" },
    { "phase": "research-running",     "at": "2026-05-20T14:32:01Z" },
    { "phase": "research-complete",    "at": "2026-05-20T14:47:00Z" }
  ],
  "milestone_brief": "Lift the Enriques canonical sextic sawtooth tear...",
  "research_mode": "standard",
  "oss_scout_requested": false,
  "research_briefs": [
    ".claude/notes/milestones/panel-refresh-2026q2-e1/research/agent-a-brief.md",
    ".claude/notes/milestones/panel-refresh-2026q2-e1/research/agent-b-brief.md"
  ],
  "research_synthesis": "Both briefs converge on a second Taubin pass with n_iter=40, pass_band=0.05 plus a 1.05x bounds pad. Agent A notes parametric pipeline must NOT be touched (AI-6/AI-7). Decision: implement Enriques-only second-pass smoothing as a kwarg on _marching_cubes_to_polydata.",
  "implementation_path": "inline",
  "implementation_plan": ".claude/notes/milestones/panel-refresh-2026q2-e1/artifacts/implementation-plan.md",
  "implementation_base": "dc328d7",
  "implementation_commit_range": "dc328d7..ef901ab",
  "implementation_commits": ["abc1234", "def5678", "ef901ab"],
  "implementation_branch": "main",
  "critique_path": ".claude/notes/milestones/panel-refresh-2026q2-e1/artifacts/adversary-critique.md",
  "critics_run": ["adversary", "frontend-ux"],
  "critique_finding_counts": { "critical": 0, "high": 2, "medium": 4, "low": 5 },
  "rectification_commit": "ab12cd3",
  "fixed_findings": ["H1", "H2", "M1", "M2"],
  "deferred_findings": ["M3", "M4", "L1", "L2", "L3", "L4", "L5"],
  "invalidated_findings": [],
  "regression_tests_added": [
    "tests/test_mesh_generators.py:120",
    "tests/test_clip_domain.py:185"
  ]
}
```

## Field reference

| Field | Type | Set by | Notes |
|---|---|---|---|
| `id` | string | init-state.sh | The milestone id.  Convention: epic-shaped (`<slug>-eN`), matching `/roadmap` output. |
| `created_at` | ISO8601 | init-state.sh | UTC. |
| `updated_at` | ISO8601 | every checkpoint | UTC. |
| `phase` | enum | every checkpoint | `init`, `research-running`, `research-complete`, `implement-running`, `implement-complete`, `critique-running`, `critique-complete`, `rectify-running`, `complete` |
| `phase_history` | array | every checkpoint | Append-only.  Each entry is `{phase, at}`. |
| `milestone_brief` | string | init-state.sh (from `--brief` arg) | Verbatim user ask.  Don't paraphrase. |
| `research_mode` | enum | init-state.sh (from `--single` / `--deep` / default) | `standard` (2x Sonnet), `deep` (1x Opus), `single` (1x Sonnet). |
| `oss_scout_requested` | bool | init-state.sh (from `--oss-scout`) | When true, Phase 3 dispatches the OSS-Scout critic.  Persisted into state so `--resume` after context compaction still routes correctly. |
| `research_briefs` | array | Phase 1 (per-brief `--append`) | Paths to written briefs. |
| `research_synthesis` | string | Phase 1 | One paragraph (soft cap 500 chars).  Required for Deep mode (no merge), recommended for Standard. |
| `implementation_path` | enum | Phase 2 (`--set`) | `inline` or `delegated`. |
| `implementation_plan` | string | Phase 2 inline path (`--set`) | Path to the 5-bullet plan written before implementation.  The Rectifier reads this in Phase 4 to confirm intent. |
| `implementation_base` | sha | Phase 2 start | The pre-milestone HEAD sha (used by Phase 3 to compute the diff). |
| `implementation_commit_range` | string | Phase 2 end | `{base}..{HEAD}`. |
| `implementation_commits` | array | Phase 2 end | All commit shas in the range. |
| `implementation_branch` | string | Phase 2 end | `main` for inline; `impl-{ID}-{a|b|solo}` for delegated. |
| `critique_path` | string | Phase 3 | `.claude/notes/milestones/{ID}/artifacts/adversary-critique.md`. |
| `critics_run` | array | Phase 3 | At minimum `["adversary"]`.  Frontend / OSS scout added when fan-out fired. |
| `critique_finding_counts` | object | Phase 3 | Aggregate counts for status reporting. |
| `rectification_commit` | sha | Phase 4 | The single rect commit sha. |
| `fixed_findings` | array | Phase 4 | Severity-id strings (`C1`, `H2`, `M1`, etc.). |
| `deferred_findings` | array | Phase 4 | Becomes input to next milestone research. |
| `invalidated_findings` | array | Phase 4 | Findings re-verification proved no longer present. |
| `regression_tests_added` | array | Phase 4 | `file:line` strings. |

## Reading state

From bash:
```bash
phase=$(.venv/Scripts/python.exe -c "import json; print(json.load(open('.claude/notes/milestones/panel-refresh-2026q2-e1/state.json'))['phase'])")
```

From the orchestrator (preferred -- always uses the venv interpreter):
```bash
.venv/Scripts/python.exe .claude/scripts/milestone-pipeline/checkpoint.py panel-refresh-2026q2-e1 --get phase
.venv/Scripts/python.exe .claude/scripts/milestone-pipeline/checkpoint.py panel-refresh-2026q2-e1 --get implementation_base
```

On POSIX, the path is `.venv/bin/python` -- both forms are documented in
CONTEXT.md section 10.

## Writing state (advancing phase)

```bash
.venv/Scripts/python.exe .claude/scripts/milestone-pipeline/checkpoint.py <ID> research-complete
```

The script:
1. Loads the existing state.json (errors if absent -- `init-state.sh` should have created it).
2. Validates the new phase is reachable from the current phase (no skips, no backwards).
3. Sets `phase`, appends to `phase_history`, updates `updated_at`.
4. Writes atomically (temp file + rename).

## Resumability

The orchestrator's first action on every invocation is `status.sh {ID}` which
prints current phase and elapsed time per phase.  The orchestrator then jumps
to the appropriate Phase section in the command body.

```
$ .claude/scripts/milestone-pipeline/status.sh panel-refresh-2026q2-e1
Milestone: panel-refresh-2026q2-e1
Phase:     critique-complete (since 2026-05-20T16:12:00Z, 3 min ago)
History:
  init               2026-05-20T14:32:00Z + 1s -> research-running
  research-running   2026-05-20T14:32:01Z +15m -> research-complete
  research-complete  2026-05-20T14:47:00Z + 0s -> implement-running
  implement-running  2026-05-20T14:47:01Z +45m -> implement-complete
  implement-complete 2026-05-20T15:32:00Z + 0s -> critique-running
  critique-running   2026-05-20T15:32:01Z +40m -> critique-complete
  critique-complete  2026-05-20T16:12:00Z (now)
Critics run: adversary, frontend-ux
Findings:    C0 H2 M4 L5
Next phase:  rectify-running (run Phase 4 of milestone-pipeline)
```

## Why not SQLite

A single-flat-JSON file is enough -- no concurrent writers (the orchestrator
is single-threaded), <1KB per milestone, human-readable for ad-hoc
inspection, atomic writes via temp-file-rename.  SQLite would add a dep with
no payoff.
