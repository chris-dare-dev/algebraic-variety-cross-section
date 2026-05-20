---
description: Run the canonical 4-phase milestone build pipeline (Research -> Implement -> Adversary critique -> Rectify) on an AVC milestone. Use when the user invokes /milestone-pipeline, says "run the milestone pipeline on <epic-id>", or asks to execute a Now-lane epic from a /roadmap doc. This is the operational counterpart to /roadmap: /roadmap produces an epic-id; /milestone-pipeline runs that epic through the 4-phase build with parallel research, optional delegated implementation, fan-out critics, and a re-verified rectification commit. Skip for trivial single-file edits (just make the change) or for full quarter-roadmap planning (use /roadmap).
argument-hint: "<id> [--brief \"...\"] [--single] [--deep] [--oss-scout] [--resume]"
---

# /milestone-pipeline — 4-phase milestone build pipeline

Run the canonical 4-phase AVC milestone build pipeline:
**Research -> Implement -> Adversary critique -> Rectify**

This pipeline is the formalization of CONTEXT.md section 6's 5-phase pattern,
collapsed to 4 phases by folding the UI/UX critic into Phase 3 fan-out (it
only fires when the diff touches Qt panel files).

**Arguments:** $ARGUMENTS — parse as `<id> [--brief "..."] [--single] [--deep] [--oss-scout] [--resume]`

- `<id>` — required; epic-shaped id matching the convention from `/roadmap` (`<slug>-eN[a-z]?`), e.g. `panel-refresh-2026q2-e2`, `enriques-mesh-quality-e1`, `fano-3folds-e4`.  If omitted, STOP and ask: "What is the milestone id?  (Expected: epic-shaped `<slug>-eN`, e.g. `panel-refresh-2026q2-e2`.)"
- `--brief "..."` — use the given string verbatim as the milestone brief.  Persisted into `state.milestone_brief`.
- `--single` — single Sonnet researcher (Phase 1 mode = `single`).
- `--deep` — single Opus researcher (Phase 1 mode = `deep`).
- `--oss-scout` — add the OSS-Scout critic to the Phase 3 fan-out.
- `--resume` — re-enter the pipeline at the phase determined by the resume routing table below.

---

## When to invoke / When NOT to invoke

**Invoke `/milestone-pipeline` when:**
- User runs `/milestone-pipeline <id>` or `/milestone-pipeline <id> --brief "..."`.
- User says "run the milestone pipeline on `<epic-id>`", "build out `<epic-id>` through the pipeline", "execute the next Now-lane epic from the roadmap".
- `/roadmap` just completed and offered the CONTEXT.md section 6 handoff for the first Now-lane epic.

**Do NOT invoke when:**
- **Trivial single-file edit** — just make the change directly.  The pipeline overhead (research + critic + rectify) isn't worth it for a typo / lint fix / docstring tweak.
- **Full-quarter roadmap planning** — use `/roadmap` first; it produces the epic ids this pipeline consumes.
- **Pure investigation / debugging** — use `/capability-scout` if you need a survey, or just ask Claude directly.  The pipeline assumes there's a milestone to build.
- **Doc-only changes** to `CONTEXT.md` / `README.md` — write directly, no pipeline.

---

## Step 0 — Initialize state

```bash
bash .claude/scripts/milestone-pipeline/init-state.sh <ID> [--brief "<verbatim user brief>"] [--single|--deep] [--oss-scout] [--resume]
```

`init-state.sh` persists every flag into `state.json`:
- `--brief "..."` → `state.milestone_brief`
- `--single` / `--deep` / (default) → `state.research_mode` (`single` | `deep` | `standard`)
- `--oss-scout` → `state.oss_scout_requested` (boolean)

Persisting flags into state is load-bearing for `--resume`: after a context
compaction the orchestrator no longer has the original argv, but state.json
does.  Phase 3 reads `oss_scout_requested` from state, NOT from argv.

- If `state.json` already exists, the script prints `state already exists at <path> (phase=X) -- resuming` and exits 0.
- If resuming: jump to the routing table at the bottom of this file ("Resume routing").

### Step 0.5 — Verify dependencies (only when the id is roadmap-shaped)

If `<ID>` matches `<slug>-eN[a-z]?`, parse `plans/<slug>-roadmap.md` for the
milestone's epic and its dependency list (the DAG section).  For each
dependency epic-id, verify the dep's `.claude/notes/milestones/<dep-id>/state.json`
shows `state.phase == "complete"`.  If any dep is not complete, surface a
gate-required to the user:

```
Cannot start <ID> -- depends on <dep-id-1>, <dep-id-2> which are not complete.
Run /milestone-pipeline <dep-id-1> first, or override with /milestone-pipeline <ID> --force-deps?
```

Wait for explicit `[y]` before proceeding.  If no `plans/<slug>-roadmap.md`
exists (the milestone id is ad-hoc, not roadmap-shaped), skip this step.

```bash
bash .claude/scripts/milestone-pipeline/status.sh <ID>
```

Read `.claude/references/milestone-pipeline/state-schema.md` only if you
need to inspect or write a field that isn't covered by the scripts.

---

## Phase 1 — Research (PARALLEL dispatch)

Read `.claude/references/milestone-pipeline/phase-research.md` at phase entry.

**Advance state BEFORE dispatch** so status.sh wall-clock per phase is
accurate:

```bash
.venv/Scripts/python.exe .claude/scripts/milestone-pipeline/checkpoint.py <ID> research-running
```

Dispatch the researchers per the matrix.  The `milestone-researcher` agent
body is its own prompt — dispatch by name; no separate substitution file.

### Dispatch mode

| Flag / signal | Mode | What to dispatch |
|---|---|---|
| Default (no flag) | Standard | 2x `milestone-researcher` sub-agents **in the same turn** |
| `--single` | Single | 1x `milestone-researcher` |
| `--deep` | Deep | 1x `milestone-researcher` with `model: opus` in the agent call |
| Milestone touches >2 subsystems OR novel math (new variety family, post-2010 construction) | Deep | same as above |

**Fire all research agents in ONE assistant turn** — sequential dispatch
defeats the parallelism point entirely.

Each `milestone-researcher` agent receives:
- The milestone id `{ID}`
- The user's milestone brief verbatim from `state.milestone_brief` (do NOT paraphrase)
- Output path: `.claude/notes/milestones/{ID}/research/agent-{a|b}-brief.md` (use `solo` for Single/Deep mode)

Agents have `memory: project` set — do not block or override their memory
writes at task completion.

**Observability:** at each dispatch, append a line to
`.claude/notes/milestones/<ID>/dispatch.log`:
```
2026-05-20T14:32:00Z | milestone-researcher | agent-a | dispatched
```
On return, append:
```
2026-05-20T14:47:12Z | milestone-researcher | agent-a | returned | 15m12s
```
The user can `tail -f` this log to see pipeline progress.

**Transient failure handling:** if a researcher returns with no output
file (network blip, WebFetch timeout), re-dispatch ONCE before failing the
phase.  Two consecutive empty returns is a real failure — surface
gate-required to the user.

**Phase wall-clock budget:** Soft cap 15 min, hard cap 30 min (per
`phase-research.md`).  After dispatching, the orchestrator polls `status.sh`
every 5 minutes.  If the phase exceeds 30 min, surface a "phase budget
exceeded — continue / abort?" gate to the user.

When all researcher agents have returned:

```bash
# Record each returned brief into state for downstream reference.
.venv/Scripts/python.exe .claude/scripts/milestone-pipeline/checkpoint.py <ID> --append research_briefs='".claude/notes/milestones/<ID>/research/agent-a-brief.md"'
.venv/Scripts/python.exe .claude/scripts/milestone-pipeline/checkpoint.py <ID> --append research_briefs='".claude/notes/milestones/<ID>/research/agent-b-brief.md"'
# Advance state.
.venv/Scripts/python.exe .claude/scripts/milestone-pipeline/checkpoint.py <ID> research-complete
```

(On POSIX the path is `.venv/bin/python` — both forms are documented in
CONTEXT.md section 10.)

---

## Phase 2 — Implement

Read `.claude/references/milestone-pipeline/phase-implement.md` at phase entry.

**Capture the pre-milestone HEAD as `implementation_base` BEFORE any
commits land** — Phase 3's frontend-detect uses it as the diff base.
Skipping this step makes the Qt-panel critic silently never fire:

```bash
.venv/Scripts/python.exe .claude/scripts/milestone-pipeline/checkpoint.py <ID> --set implementation_base="\"$(git rev-parse HEAD)\""
.venv/Scripts/python.exe .claude/scripts/milestone-pipeline/checkpoint.py <ID> implement-running
```

Read BOTH research briefs end-to-end.  Write a synthesis paragraph to
`state.research_synthesis` (soft cap 500 chars):

```bash
.venv/Scripts/python.exe .claude/scripts/milestone-pipeline/checkpoint.py <ID> --set research_synthesis="\"<one paragraph>\""
```

### Inline vs Delegated

| Predicate | Path |
|---|---|
| Merged plan <=500 LOC across <=5 files **AND** no novel-pipeline scaffolding (e.g. introducing a new mesh helper class) **AND** no new variety family being introduced | **Inline** — implement in the main session |
| Otherwise, OR user asked for "parallel implementers" / "explorer branches" | **Delegated** — dispatch milestone-implementer sub-agent(s) |

**Default for this repo: Inline.**  The repo is small, single-developer,
and works directly on `main` per CONTEXT.md section 12.  The Delegated path
is documented but rarely needed — use it when the main-session context
window becomes a constraint, OR when the user explicitly asks for parallel
exploration.

Record the chosen path:

```bash
# Inline:
.venv/Scripts/python.exe .claude/scripts/milestone-pipeline/checkpoint.py <ID> --set implementation_path='"inline"'
# Delegated:
.venv/Scripts/python.exe .claude/scripts/milestone-pipeline/checkpoint.py <ID> --set implementation_path='"delegated"'
```

**Inline path:**
1. Write a 5-bullet plan to `.claude/notes/milestones/{ID}/artifacts/implementation-plan.md`, then record its path:
   ```bash
   .venv/Scripts/python.exe .claude/scripts/milestone-pipeline/checkpoint.py <ID> --set implementation_plan='".claude/notes/milestones/<ID>/artifacts/implementation-plan.md"'
   ```
2. Implement.  Commit small (<=200 LOC per commit).  Subject: `{type}({ID}): {imperative}`.
3. Run `.venv/Scripts/python.exe -m pytest tests/ -q`.  Fix until green (currently 165 tests, ~4 s).
4. **Off-screen render verification** per CONTEXT.md section 10 if you touched a generator or render path: render via `pv.OFF_SCREEN = True` to `/tmp/check-*.png` and Read the PNG to visually confirm.  Never construct `MainWindow()` under `QT_QPA_PLATFORM=offscreen` (AI-3).

**Delegated path (optional / rarely used in this repo):**
- Dispatch 1 or 2 `milestone-implementer` agents (their body is the prompt).  Substitute `{ID}`, `{BRIEF_PATH}`, `{BRANCH_NAME}`, `{LETTER}` via the Task tool's inputs.
- `{LETTER}` convention:
  - Single-implementer dispatch (default): pass `{LETTER}=solo`.  Output files become `implementer-solo-deviations.md`, `implementer-solo-ai-conflict.md`, etc.
  - Two-implementer dispatch: pass `{LETTER}=a` to the first implementer (reads `agent-a-brief.md`) and `{LETTER}=b` to the second (reads `agent-b-brief.md`).  Output files become `implementer-a-deviations.md` and `implementer-b-deviations.md`.
  - Failing to substitute `{LETTER}` results in literal `implementer-{LETTER}-deviations.md` filenames in the artifacts directory — a clear regression signal.
- Branch naming: `impl-{ID}-solo` (single) or `impl-{ID}-a` / `impl-{ID}-b` (two-way).
- **Do NOT use worktree isolation in this repo** — the `.venv` is gitignored, isolation breaks the venv, and this repo's flat single-`main` workflow per CONTEXT.md section 12 makes branch synthesis trivial.  Dispatch implementers on regular branches.
- Use 2 implementers only when the two research briefs genuinely disagree on approach AND both approaches are credible.
- When implementer(s) return: review commits, fast-forward merge to `main` (single implementer) or synthesize (two implementers).  Delete the explorer branches after merge.
- `pytest tests/ -q` must pass on `main` before checkpoint.

Either path ends with:

```bash
# Record the commit range AND the full commit list (load-bearing for status.sh).
.venv/Scripts/python.exe .claude/scripts/milestone-pipeline/checkpoint.py <ID> --set implementation_commit_range="\"<base>..<HEAD>\""
# Append each commit sha individually so status.sh can report progress.
for SHA in $(git log --format=%H <base>..HEAD); do
  .venv/Scripts/python.exe .claude/scripts/milestone-pipeline/checkpoint.py <ID> --append implementation_commits="\"$SHA\""
done
.venv/Scripts/python.exe .claude/scripts/milestone-pipeline/checkpoint.py <ID> implement-complete
```

---

## Phase 3 — Adversary critique (PARALLEL when Qt panels touched)

Read `.claude/references/milestone-pipeline/phase-critique.md` at phase entry.

Advance state BEFORE dispatch (wall-clock accuracy):
```bash
.venv/Scripts/python.exe .claude/scripts/milestone-pipeline/checkpoint.py <ID> critique-running
```

### Detect Qt-panel changes

The AVC "frontend" is the Qt panels, not a web frontend.  This grep
assumes panel files live at repo root (the current AI-1-locked
convention).  If AI-1 is ever lifted to allow a `ui/` subdir, widen the
regex.

```bash
# checkpoint.py --get exits 2 when the field is unset (None) and 0 when set.
# This split lets us distinguish "Phase 2 never ran" from "Phase 2 ran but
# set an empty string" (which shouldn't happen, but if it does, the
# diagnostic is clearer).
if ! BASE=$(.venv/Scripts/python.exe .claude/scripts/milestone-pipeline/checkpoint.py <ID> --get implementation_base); then
  echo "ERROR: implementation_base is unset -- Phase 2 did not persist it.  Cannot detect Qt-panel changes." >&2
  echo "       Fix: re-run Phase 2's '--set implementation_base=...' line, then retry Phase 3." >&2
  exit 1
fi
# Match panel files at repo root OR in a future subdir (forward-compat).
git diff --name-only ${BASE}..HEAD | grep -E '(^|/)(appearance_panel|view_panel|parameters_panel|styles|app)\.py$' && echo "frontend_changed=true" || echo "frontend_changed=false"
```

### Dispatch critics

In ONE assistant turn (write a dispatch.log line per agent — see
"Observability" under Phase 1):

1. **Always:** dispatch `milestone-adversary-critic` sub-agent on the implementation diff.
   - The agent reads `.claude/references/milestone-pipeline/adversary-critique-skill.md` and `adversary-critique-checklist.md` itself at startup.
   - Substitute `{ID}`, `{COMMIT_RANGE}`, `{CRITIQUE_PATH}` in the agent inputs.  `{COMMIT_RANGE}` comes from `state.implementation_commit_range` (set at the end of Phase 2).  `{CRITIQUE_PATH}` is `.claude/notes/milestones/{ID}/artifacts/adversary-critique.md`.  Failing to substitute these results in the agent running `git diff {COMMIT_RANGE}` literally, which git rejects.

2. **If `frontend_changed=true`:** ALSO dispatch `milestone-frontend-ux-critic` sub-agent in the same turn.
   - Substitute `{ID}`, `{COMMIT_RANGE}`, `{FRONTEND_CRITIQUE_PATH}`.
   - Output path: `.claude/notes/milestones/{ID}/artifacts/frontend-critique.md`.

3. **If `state.oss_scout_requested == true`** OR milestone is in an active-research area (new variety family, novel parametric construction, modern mesh-smoothing algorithm): dispatch `milestone-oss-scout` in the same turn.
   - Substitute `{ID}`, `{COMMIT_RANGE}`, `{DOMAIN_AREA}`, `{OSS_SCOUT_PATH}`.
   - Output path: `.claude/notes/milestones/{ID}/artifacts/oss-scout.md`.

**Transient failure handling:** if a critic returns with no output file
(network blip), re-dispatch ONCE before failing the phase.  Two consecutive
empty returns is a real failure — surface gate-required.

**Phase wall-clock budget:** Soft cap 30 min for the full fan-out, hard
cap 60 min.  Poll `status.sh` every 5 minutes; surface gate-required if
exceeded.

When all critics return:

- If the Qt-panel critic ran: merge its findings into the adversary critique under a `## Frontend UI/UX findings` section, severity-graded.  Then dedup:

```bash
.venv/Scripts/python.exe .claude/scripts/milestone-pipeline/dedupe-findings.py .claude/notes/milestones/<ID>/artifacts/adversary-critique.md
```

Record critics run AND derive finding counts from the merged critique:
```bash
.venv/Scripts/python.exe .claude/scripts/milestone-pipeline/checkpoint.py <ID> --set critics_run='["adversary","frontend-ux"]'

# Parse severity headers from the deduped critique to populate finding counts.
CRIT_PATH=".claude/notes/milestones/<ID>/artifacts/adversary-critique.md"
C=$(grep -c '^### CRITICAL' "$CRIT_PATH" || echo 0)
H=$(grep -c '^### HIGH'     "$CRIT_PATH" || echo 0)
M=$(grep -c '^### MEDIUM'   "$CRIT_PATH" || echo 0)
L=$(grep -c '^### LOW'      "$CRIT_PATH" || echo 0)
.venv/Scripts/python.exe .claude/scripts/milestone-pipeline/checkpoint.py <ID> --set critique_finding_counts="{\"critical\": $C, \"high\": $H, \"medium\": $M, \"low\": $L}"
.venv/Scripts/python.exe .claude/scripts/milestone-pipeline/checkpoint.py <ID> --set critique_path="\"$CRIT_PATH\""
echo "Phase 3 found: C=$C H=$H M=$M L=$L"  # surface counts to user before Phase 4
```

(Adjust the JSON array to match which critics actually fired.)

Advance state:
```bash
.venv/Scripts/python.exe .claude/scripts/milestone-pipeline/checkpoint.py <ID> critique-complete
```

---

## Phase 4 — Rectify (MAIN SESSION — not a sub-agent)

Read `.claude/references/milestone-pipeline/phase-resolve.md` at phase entry.

Advance state:
```bash
.venv/Scripts/python.exe .claude/scripts/milestone-pipeline/checkpoint.py <ID> rectify-running
```

This phase runs in the **main session**.  Do NOT delegate to a sub-agent
unless the user explicitly requests it — and only then to a fresh agent
that did NOT write the implementation.  If the user DOES request
delegation, dispatch a fresh sub-agent with explicit inputs `{ID}` and
`{CRITIQUE_PATH}`; the sub-agent must abort if it discovers it also wrote
the implementation (the agent body encodes this invariant).

### Re-verification (required before any fix)

For every CRITICAL and HIGH finding: read the cited `file:line` (+/- 30
surrounding lines) to confirm the issue is still present.  If no longer
present, mark it invalidated — do NOT silently drop.

```bash
.venv/Scripts/python.exe .claude/scripts/milestone-pipeline/checkpoint.py <ID> --append invalidated_findings='"H3"'
```

If the invalidation rate exceeds 40% (more than 4 in 10 findings
invalidate), surface gate-required to the user: the critic prompt is
likely broken or was fed a stale diff.

### Fix loop

Fix priority: CRITICAL (block ship) -> HIGH (block ship) -> MEDIUM (fix if
<=30 LOC) -> LOW (defer).

For each CRITICAL/HIGH:
1. Write regression-guard test (fail on pre-fix code, pass after).  This repo's tests are Qt-free (AI-2) — if a fix would need Qt to test, document the manual verification step in the commit body instead.
2. Make the fix.
3. Run affected tests.  Cap inner loop at 3 iterations; escalate to user if still red.

After all mandatory fixes:
```bash
.venv/Scripts/python.exe -m pytest tests/ -q
```
Cap outer loop at 3 iterations.

**Off-screen render verification** per CONTEXT.md section 10 if any fix
touched a generator or render path: re-render the affected surface(s) to
`/tmp/check-*.png` and Read each PNG to visually confirm.

### Rectification commit

Single commit, NOT amended onto Phase 2:
```
rect({ID}): close C1, H1, H2, M1
```

Body should list fixed / deferred / invalidated severity-ids.

Append rectification status footer to
`.claude/notes/milestones/{ID}/artifacts/adversary-critique.md`
(append-only).

Use `--append` (NOT `--set`) when recording fixed / deferred / invalidated
ids one at a time:
```bash
.venv/Scripts/python.exe .claude/scripts/milestone-pipeline/checkpoint.py <ID> --append fixed_findings='"C1"'
.venv/Scripts/python.exe .claude/scripts/milestone-pipeline/checkpoint.py <ID> --append fixed_findings='"H1"'
.venv/Scripts/python.exe .claude/scripts/milestone-pipeline/checkpoint.py <ID> --append deferred_findings='"L1"'
```

### After commit

```bash
.venv/Scripts/python.exe .claude/scripts/milestone-pipeline/checkpoint.py <ID> --set rectification_commit="\"$(git rev-parse HEAD)\""
.venv/Scripts/python.exe .claude/scripts/milestone-pipeline/checkpoint.py <ID> complete
```

**Do NOT auto-push.**  This repo works directly on `main` per CONTEXT.md
section 12, but `git push` is a manual user step (single-developer
cadence).  The pipeline never pushes — the user pushes when ready.

Print a 5-line final summary (one line per element):
```
Milestone: <ID>
Findings:  C<critical> H<high> M<medium> L<low> (total <N>)
Resolved:  fixed=<n> deferred=<n> invalidated=<n>
Critique:  .claude/notes/milestones/<ID>/artifacts/adversary-critique.md
Rect:      <rect-commit-sha>
```

---

## State machine

```
init -> research-running -> research-complete
     -> implement-running -> implement-complete
     -> critique-running -> critique-complete
     -> rectify-running -> complete
```

The scripts enforce forward-only, single-step transitions.  `status.sh`
prints elapsed time per phase.

---

## File-presence and resume routing

If `--resume` is supplied, determine the entry phase via
`state.phase`.  Use:

```bash
.venv/Scripts/python.exe .claude/scripts/milestone-pipeline/validate-state.py <ID> --report-next-phase
```

The script prints the canonical Phase-N-step-Y entrypoint the orchestrator
should jump to.  Mapping:

| state.phase | Next action |
|---|---|
| `init` | Phase 1 step 0 (advance to research-running, dispatch researchers) |
| `research-running` | Phase 1 step 2 (researchers in flight; await brief files, then advance to research-complete) |
| `research-complete` | Phase 2 step 0 (capture implementation_base, advance to implement-running, then implement) |
| `implement-running` | Phase 2 step 4 (implementation in flight; await commits, then advance to implement-complete) |
| `implement-complete` | Phase 3 step 0 (advance to critique-running, detect Qt panels, dispatch critics) |
| `critique-running` | Phase 3 step 3 (critics in flight; await critique files, then dedupe and advance to critique-complete) |
| `critique-complete` | Phase 4 step 0 (advance to rectify-running, then run re-verification) |
| `rectify-running` | Phase 4 step 5 (rectification in progress; finish fixes, commit, advance to complete) |
| `complete` | terminal — pipeline done; nothing to dispatch |

`init-state.sh` is idempotent — it prints `state already exists at <path>
(phase=X) -- resuming` and exits 0 when state already exists.

---

## Sub-agent contract

Every milestone sub-agent returns a single JSON object (no surrounding prose):

```json
{
  "file_path": "<primary output path, or null>",
  "status": "complete | gate-required | aborted-scope",
  "summary": "<3 lines max, plain text, no markdown — line 1: what was written; line 2: gate question if status=gate-required; line 3: suggested orchestrator next step>",
  "injection_attempts": 0
}
```

The `milestone-oss-scout` agent gets ONE additional documented status:
`not-applicable` (returned when the diff has no production code changes;
the agent's Step 0 exit-fast self-check produces this).  No other agent
emits `not-applicable`.

### Status routing table (all agents)

| Agent + status | Routing |
|---|---|
| `researcher.complete` | Append brief path to `state.research_briefs`; when ALL researchers complete, advance to `research-complete` |
| `researcher.gate-required` | Surface gate question (e.g. "2+ credible 'Recommended approach' branches with no priority signal"); re-dispatch researcher with `--user-resolution "<answer>"` appended |
| `researcher.aborted-scope` | Print abort reason from JSON summary; stop |
| `implementer.complete` | Review commits; fast-forward / synthesize to `main`; advance to `implement-complete` |
| `implementer.gate-required` | Surface gate question (e.g. "merge conflict between explorer branches"); re-dispatch with user resolution |
| `implementer.aborted-scope` | Read `scope-exceeded.md` artifact; commit partial work; surface to user with continue-or-abort prompt |
| `adversary-critic.complete` | Proceed to dedupe; if `frontend_changed=true` wait for frontend-ux-critic to also complete |
| `adversary-critic.gate-required` | Surface gate question (e.g. "AI-1..AI-15 violation requires user lift"); re-dispatch with user resolution |
| `adversary-critic.aborted-scope` | Print abort reason; stop |
| `frontend-ux-critic.complete` | Merge findings into adversary critique under `## Frontend UI/UX findings`; proceed to dedupe |
| `frontend-ux-critic.gate-required` | Surface gate question; re-dispatch with user resolution |
| `frontend-ux-critic.aborted-scope` | Print abort reason; stop |
| `oss-scout.complete` | Append `## Industry comparison` appendix to critique; proceed to dedupe |
| `oss-scout.not-applicable` | No-op (diff had no production code changes); proceed to dedupe without appending |
| `oss-scout.gate-required` | Surface gate question (rare); re-dispatch with user resolution |
| `oss-scout.aborted-scope` | Print abort reason; stop |
| `<any-agent>.gate-required` (AI-1..AI-15 violation) | This is the lift-decision gate; user resolves whether to fix in this milestone or open a follow-up |

### When agents gate

| Agent | Gate-required scenarios |
|---|---|
| researcher | 2+ credible "Recommended approach" branches with no priority signal; brief reveals AI-1..AI-15 lift requirement |
| implementer | merge conflict between two explorer branches; AI-1..AI-15 violation that requires user lift |
| adversary-critic | AI-1..AI-15 violation that requires user lift (not surfaceable as a finding because the lift is the question) |
| frontend-ux-critic | AI-1..AI-15 violation that requires user lift; first-launch UX regression that requires section-9 non-goal lift |
| rectifier (orchestrator, not a sub-agent) | invalidation rate >40%; CRITICAL finding cannot close inside 3 inner-loop iterations |

---

## External-write boundary

The `/milestone-pipeline` pipeline enforces strict external-write boundaries:

- **No `git push`** from any phase.  This repo's git workflow is manual;
  the user pushes when ready.
- **No `gh issue create` / `gh pr create` / `gh release create` /
  `gh api` (write verb)** from sub-agents.  Phase 4 may surface a "should
  we open follow-up issues for the deferred findings?" gate, but the
  orchestrator (not a sub-agent) runs `gh` after explicit `[y]`.
- **No `glab *`** (GitLab CLI — defense in depth; this is a GitHub project).
- **No `mcp__GitLab__*`** write tool calls.
- **No dispatching of other slash commands** from milestone sub-agents
  (no `/capability-scout`, no `/frontend-uplift`, no `/roadmap`).
- **No mutation of `~/.claude/`** outside a sentinel-hook-gated
  optimizer run.
- **No POSTing to non-loopback hosts** beyond the WebFetch / WebSearch
  surfaces explicitly allowed for the researcher / oss-scout.
- **No writes to `CONTEXT.md`, `README.md`, `requirements.txt`** from any
  sub-agent.  The orchestrator may update these in Phase 4 if a finding
  requires (e.g. new section 8 entry); sub-agents never do.
- **Sub-agent writes are confined** to their assigned artifact path
  (`{BRIEF_PATH}` / `{CRITIQUE_PATH}` / `{FRONTEND_CRITIQUE_PATH}` /
  `{OSS_SCOUT_PATH}`) plus their per-agent memory directory under
  `.claude/agent-memory/<agent-name>/`.

This repo does not currently install hook-level enforcement (unlike some
reference repos).  The boundary above is doc-enforced and load-bearing for
sub-agent prompts (each sub-agent's `<scope-bounds>` block re-states the
relevant subset).

---

## Common rationalizations (anti-pattern guard)

See `.claude/references/milestone-pipeline/anti-patterns.md` for the full
table.  The milestone-specific rows worth keeping inline (they are NOT in
the shared roadmap anti-patterns list):

| Tempting belief | Reality |
|---|---|
| "Qt-panel critic is overkill on a generator-only milestone." | Correct — and the orchestrator skips it automatically when no panel files changed. |
| "Lift CONTEXT.md section 9 non-goal X (e.g. QSettings) as a sneak-in fix during rectification." | Non-goals are decisions, not oversights.  Open a separate milestone if lifting one is justified. |
| "Auto-push after Phase 4 like the reference repo does." | This repo's git workflow is manual.  The pipeline writes commits but never pushes. |

---

## Don'ts

- **Don't run Phase 4 as a sub-agent** by default.  It needs full repo
  access, the user's review surface, and the ability to commit.
  Sub-agents return one bundle and can't pause for user input.
- **Don't let the implementer write the critique.**  Critic and
  implementer are deliberately different agents.
- **Don't elevate severity to "earn" the pipeline.**  Zero CRITICALs and
  zero HIGHs is legitimate.
- **Don't skip the 10-axis checklist.**  It encodes prior incidents
  documented in CONTEXT.md section 8 (clip_box invert, Hanson normals,
  Barth misattribution, processEvents re-entrancy, marching-cubes empty
  field, conifold singularity).
- **Don't bypass `scripts/init-state.sh`.**  State directory naming is
  load-bearing for status and checkpoint.
- **Don't auto-dispatch the next milestone's pipeline.**  At `complete`,
  surface the summary and stop.  The user chooses what's next.

---

## Sub-agent memory

All `milestone-*` agents have `memory: project` in their frontmatter.
Their memory accumulates under `.claude/agent-memory/<agent-name>/`
across runs.  Do NOT clear or overwrite these directories — they carry
institutional memory from prior milestone runs.

Each agent appends to `lessons.md` per the protocol documented in
`.claude/references/milestone-pipeline/memory-update-protocol.md`.

---

## References

Phase references (`phase-research.md`, `phase-implement.md`,
`phase-critique.md`, `phase-resolve.md`) are surfaced INLINE at their
phase entries above.  Cross-cutting references:

- `.claude/references/milestone-pipeline/state-schema.md` — `state.json` field reference; read only when inspecting/writing a field beyond what scripts cover
- `.claude/references/milestone-pipeline/adversary-critique-skill.md` — how the critic is dispatched
- `.claude/references/milestone-pipeline/adversary-critique-checklist.md` — 10-axis institutional checklist
- `.claude/references/milestone-pipeline/adversary-critique-template.md` — per-invocation critique template
- `.claude/references/milestone-pipeline/anti-patterns.md` — shared anti-pattern table (the inline table above carries only the milestone-specific rows)
- `.claude/references/milestone-pipeline/memory-update-protocol.md` — sub-agent memory append protocol
- `.claude/references/critique-format.md` — canonical severity language (shared with `/capability-scout` and `/frontend-uplift`)
- `.claude/references/app-invariants.md` — AI-1..AI-15 architectural locks
- `CONTEXT.md` — root doc; section 6 documents the original 5-phase pattern this pipeline formalizes

Files this command writes to (and the only places sub-agents may write):

```
.claude/notes/milestones/<ID>/
+-- state.json                      # phase pointer, finding counts, etc.
+-- dispatch.log                    # one line per agent dispatch / return
+-- research/
|   +-- agent-{a|b|solo}-brief.md   # researcher outputs
+-- artifacts/
    +-- implementation-plan.md      # inline path only
    +-- implementer-{a|b|solo}-deviations.md  # delegated path
    +-- implementer-{a|b|solo}-ai-conflict.md # delegated path
    +-- scope-exceeded.md           # implementer abort signal
    +-- adversary-critique.md       # Phase 3 main output
    +-- frontend-critique.md        # Phase 3 conditional output
    +-- oss-scout.md                # Phase 3 conditional output

.claude/agent-memory/
+-- milestone-researcher/lessons.md
+-- milestone-implementer/lessons.md
+-- milestone-adversary-critic/lessons.md
+-- milestone-frontend-ux-critic/lessons.md
+-- milestone-oss-scout/lessons.md
```
