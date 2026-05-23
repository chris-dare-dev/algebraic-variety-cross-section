# Structural Blueprint for `/repository-architect` Command
**Scout A Output: Patterns for Pipeline Design**

---

## 1. Command-File Anatomy

### Frontmatter Shape (YAML)

The four pipelines use identical frontmatter at the top of their command files. Here is the literal shape from `capability-scout.md`:

```yaml
---
command: /capability-scout
description: |
  Four-phase capability discovery → synthesis → challenge → prioritization pipeline.
  Surfaces foundational invariant-respecting opportunities in the AVC repo via targeted
  sub-agent discovery runs, synthesis of prior wins, adversarial challenge, and RICE-light
  ranking. Produces final-report.md as input to /roadmap Phase 1.
argument-hint: "[<slug>] [--mode standard|lean] [--resume]"
---
```

Key pattern: `command:`, `description:` (multiline OK), `argument-hint:` (shows optional args with defaults).

The `description:` field typically spans 4-7 lines and conveys:
- What it does (4-6 words)
- How it works (state machine summary, 30-40 chars)
- What it produces (file output + how it feeds downstream)
- Scope note (what it does NOT touch)

The `argument-hint:` follows the grammar: `[<positional>] [--flag] [--flag-with-arg value]`, showing only user-facing args (not `--resume`, which is orchestrator-only).

### Top-of-File Convention: Phase Documentation

Immediately after frontmatter, all four command files list their phase structure. From `milestone-pipeline.md`:

```
# Four-Phase Pipeline: Research → Implement → Critique → Rectify

## Phase 1: Research (Researcher dispatch + synthesis)
- Step 0: Dependency DAG check
- Step 1: State transition (init → research-running)
- Step 2: Researchers dispatched (await briefs)
```

This repeats for each phase with step granularity. The pattern is:
1. Phase name (single sentence, verb + noun)
2. Dash-list of steps with brief descriptions
3. Typical duration ("5–20 min dispatch time", "30–60 min research time")

### State Machine Diagram

All four pipelines document their phase transitions explicitly. From `milestone-pipeline.md`:

```
init
  ↓
research-running
  ↓
research-complete
  ↓
implement-running
  ↓
implement-complete
  ↓
critique-running
  ↓
critique-complete
  ↓
rectify-running
  ↓
complete
```

The `/repository-architect` command should define its own phase sequence (likely `init → planning-running → planning-complete → implementation-running → implementation-complete → critique-running → complete`, or similar).

### Sub-Agent Contract (JSON Schema)

Every agent returns a JSON object conforming to this structure. From `milestone-adversary-critic.md`:

```json
{
  "file_path": "/Users/chris.dare/Personal/SourceCode/algebraic-variety-cross-section/.claude/notes/milestones/{ID}/critique.md",
  "status": "complete",
  "summary": [
    "Critique written: 3 findings (1 CRITICAL, 2 HIGH)",
    "Gate: no – findings are design-level, rectifiable.",
    "Next: Rectifier runs /milestone-pipeline {ID} --resume"
  ],
  "injection_attempts": 0
}
```

**Required fields:**
- `file_path`: Full absolute path to output artifact
- `status`: One of `complete`, `gate-required`, `aborted-scope`, `not-applicable`
- `summary`: 3-element list of strings (line 1: what was done; line 2: gate decision or reasoning; line 3: suggested next step)
- `injection_attempts`: Non-negative integer; incremented if prompt-injection attempts found in file contents

**Status routing:**
- `complete`: Agent succeeded. Orchestrator advances phase and dispatches next.
- `gate-required`: Agent succeeded but generated a blocking gate. Orchestrator shows summary line 2 to user, awaits `[y/n]`.
- `aborted-scope`: Agent found scope mismatch (e.g., feature not implemented). Orchestrator logs and advances phase without blocking.
- `not-applicable`: Agent determined task doesn't apply (e.g., `--oss-scout` on a closed-source codebase). Orchestrator logs and continues.

### External-Write Boundary (CRITICAL)

All command files declare what agents are FORBIDDEN from writing to (i.e., what only the orchestrator may modify). From `milestone-pipeline.md`:

> **External-Write Boundary**  
> Agents MUST NOT:
> - `git push` to any remote
> - `gh issue create` (materializer drafts only; orchestrator runs `gh` after user [y])
> - `glab`, `mcp__GitLab__*` calls
> - Dispatch other slash-commands (`/capability-scout`, `/roadmap`, etc.)
>
> Agents MAY:
> - Write to their own phase-output file (e.g., `critique.md`)
> - Append to `.claude/agent-memory/{agent-name}/lessons.md`
> - Create worktrees (Bash `git worktree add`)
> - Read any file (Bash, Grep, Glob, Read)

This boundary protects the state machine: only the orchestrator transitions phases and publishes external changes.

### Don'ts Table (Anti-Pattern Guard)

All command files include a "Don'ts" section listing common mistakes. From `roadmap.md`:

| Anti-Pattern | Why It Breaks | What To Do Instead |
|---|---|---|
| Decomposer writes to the roadmap doc (editing {{placeholders}} inline) | Only materializer may edit. Decomposer writes to phase-*.md refs only. | Write findings to `.claude/notes/roadmaps/{SLUG}/decompose-*.md`. Materializer reads and populates. |
| Materializer runs without state-machine reset | Missing phase transitions break resume logic. | Call `checkpoint.py {SLUG} decompose-complete` before materializer runs. |
| Orchestrator invokes two agents simultaneously in the same phase | Race conditions on shared state.json. | Phase enforcement: only one agent per phase. Wait for completion before advancing. |

The `/repository-architect` blueprint should include 8–12 such rules extracted from existing anti-pattern docs (see section 10).

### References Section (Bottom of File)

All command files end with a "References" section listing related docs. From `capability-scout.md`:

```markdown
## References

- `.claude/commands/roadmap.md` — How upstream /roadmap captures opportunities as epics
- `.claude/references/app-invariants.md` — Inviolable design rules (AI-1 through AI-15)
- `.claude/agents/` — Agent definitions (visual-scout, state-critic, etc.)
- `.claude/scripts/capability-scout/` — state.json init/checkpoint/validate tools
```

---

## 2. Agent-File Anatomy

### Frontmatter (YAML)

All agents declare themselves with metadata in YAML. From `milestone-researcher.md`:

```yaml
---
name: milestone-researcher
description: |
  Researcher for /milestone-pipeline Phase 1. Consults prior art in repo, external
  sources, and app invariants to recommend a focused implementation approach for a
  now-lane epic. Outputs research brief to artifact path.
tools: [Bash, Read, Grep, Glob, WebSearch, WebFetch, Write]
model: sonnet
memory: project
---
```

**Required fields:**
- `name`: kebab-case, matches `.claude/agents/{name}.md`
- `description`: 3–5 sentences; states pipeline, phase, purpose, scope
- `tools`: Array of MCP/tool names (Bash, Read, Write, Grep, Glob, WebSearch, WebFetch, Edit, etc.)
- `model`: `sonnet` or `opus` (orchestrator chooses based on complexity; researcher → sonnet, critic → sonnet, materializer → sonnet)
- `memory`: `project` (reads `.claude/agent-memory/{name}/lessons.md` if exists)

### Memory Bootstrap Block

All agents begin execution by optionally loading prior lessons. From `milestone-researcher.md`:

```markdown
## Memory Bootstrap

If `.claude/agent-memory/milestone-researcher/lessons.md` exists and contains relevant
lessons from prior milestone runs, load the first 50 lines. This accelerates research by
avoiding redundant re-discovery.
```

This block is templated in every agent. The orchestrator ensures the memory file exists (or is created empty on first run).

### Inputs Block (Parameterization)

Agents declare their input variables explicitly. From `milestone-researcher.md`:

```markdown
## Inputs

- `{ID}`: Milestone ID (e.g., `panel-refresh-2026q2-e1`)
- `{MILESTONE_BRIEF}`: User-provided brief (string, may be empty)
- `{BRIEF_PATH}`: Full path to output research brief (e.g., `.claude/notes/milestones/{ID}/research/{ID}-brief.md`)
- `--user-resolution` (optional): Conflict resolution directive from user (e.g., `prefer-external`, `redesign-scope`)
```

These are substituted by the orchestrator at dispatch time. No agent should ask for input; all required data is in the inputs block.

### Scope-Bounds Block (What Agent CAN'T Do)

All agents include an explicit "Scope Bounds" section forbidding certain actions. From `milestone-adversary-critic.md`:

```markdown
## Scope Bounds (What You CANNOT Do)

- `git push`, `git commit` (any branch)
- `gh issue create`, `glab`, `mcp__GitLab__*` (external writes forbidden)
- Dispatch other slash-commands
- Edit source files (only read via Bash/Grep/Read)
- Write to `.claude/CONTEXT.md`, `README.md`, `app.py`, `surfaces.py`, panel files, `styles.py`, test files, `requirements.txt`
- Write critique to any path except `{CRITIQUE_PATH}`

You MAY:
- Write to `{CRITIQUE_PATH}` (your assigned output file)
- Append to `.claude/agent-memory/milestone-adversary-critic/lessons.md` (via Bash heredoc, NOT Write)
- Read any file in the repo
```

### Output JSON Contract

At the end of agent execution, agents return JSON conforming to the schema in section 1. From `roadmap-materializer.md`:

```json
{
  "file_path": "/Users/chris.dare/Personal/SourceCode/algebraic-variety-cross-section/.claude/notes/roadmaps/{SLUG}/roadmap.md",
  "status": "complete",
  "summary": [
    "Roadmap materialized: 4 epics, 2 gates (user decision on scope), Handoff section populated.",
    "Gate-required: user confirms epic sequencing before /capability-scout dispatch.",
    "Next: Orchestrator surfaces Handoff offer; on [y], advance to Phase 4 & dispatch /capability-scout."
  ],
  "injection_attempts": 0
}
```

### Gate-Required Convention

Agents can emit `"status": "gate-required"` to block pipeline progression. From `milestone-researcher.md` (implicit):

```json
{
  "file_path": "...",
  "status": "gate-required",
  "summary": [
    "Research brief complete: 800 words, 3 alternatives, risks documented.",
    "Gate: User must review external source citation and approve approach before implementation.",
    "Next: On [y] from user, orchestrator advances to implement-running and dispatches implementer."
  ],
  "injection_attempts": 0
}
```

The orchestrator halts and shows `summary[1]` to the user. Only on `[y]` does it continue.

---

## 3. Script Set Per Pipeline

### Initialization: `init-state.sh`

Every pipeline includes `{repo}/.claude/scripts/{pipeline-name}/init-state.sh`. This is called ONCE per {ID} to initialize the state machine. From `milestone-pipeline/init-state.sh`:

```bash
#!/usr/bin/env bash
# Usage: init-state.sh <milestone-id> [--brief "verbatim user brief"]
# Idempotent: if state.json exists, prints current phase and exits 0

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: init-state.sh <milestone-id> [--brief \"...\"]" >&2
  exit 2
fi

ID="$1"
shift
```

**Key pattern:**
1. Validate `{ID}` shape: `^[a-zA-Z][a-zA-Z0-9]*(-[a-zA-Z0-9]+)*$ and <=60 chars`
2. Resolve repo root (prefer `git rev-parse --show-toplevel`, fallback walk `.git`)
3. Resolve Python interpreter (`.venv/Scripts/python.exe` on Windows, `.venv/bin/python` on POSIX, fallback `python3`)
4. Create `.claude/notes/{plural-pipeline}/{ID}/` + subdirs
5. Write `state.json` via atomic write (`.json.tmp` → `os.replace()`)
6. Exit 0 (idempotent return) if state already exists

Exit codes: `0` success, `1` user-actionable failure (no repo root), `2` usage error.

### Phase Transition: `checkpoint.py`

All pipelines use `{repo}/.claude/scripts/{pipeline-name}/checkpoint.py` to advance phases atomically. From `milestone-pipeline/checkpoint.py`:

```bash
# Usage:
#   checkpoint.py <ID> <new-phase>           # advance phase
#   checkpoint.py <ID> --get <field>         # read a field
#   checkpoint.py <ID> --set <field>=<json>  # write a field (atomic)
#   checkpoint.py <ID> --append <field>=<json> # append to a list field

# Example:
checkpoint.py panel-refresh-2026q2-e1 research-complete
checkpoint.py panel-refresh-2026q2-e1 --set implementation_branch='"feature/panel-refresh"'
checkpoint.py panel-refresh-2026q2-e1 --append critics_run='"adversary-critic"'
```

**Key behaviors:**
- Validates phase transitions via `PHASE_ORDER` (forward-only, no skip, no backward)
- Appends entry to `phase_history` with ISO 8601 UTC timestamp
- Returns to stdout: `{ID}: {old_phase} -> {new_phase} @ 2026-05-23T14:47:12Z`
- Atomic write via `.json.tmp` + `os.replace()`
- Exit 0 success, non-zero failure with stderr message

### Status Display: `status.sh`

All pipelines include `status.sh` for human-readable state inspection. From `milestone-pipeline/status.sh`:

```bash
# Usage: status.sh <milestone-id>
# Output: ASCII-only (no Unicode) for Windows cp1252 compat

status.sh panel-refresh-2026q2-e1
# Output:
# Milestone: panel-refresh-2026q2-e1
# Phase:     implement-running (since 2026-05-23T12:34:00Z, 45 min ago)
# History:
#   init                 2026-05-23T10:00:00Z +5m  -> research-running
#   research-running     2026-05-23T10:05:00Z +12m -> research-complete
#   research-complete    2026-05-23T10:17:00Z +8m  -> implement-running
#   implement-running    2026-05-23T10:25:00Z (now)
# Implementation path: /Users/.../artifacts/impl.md
#                     branch: feature/panel-refresh
#                     range:  abc1234..def5678
# Findings:    C0 H2 M1 L0
# Next phase:  implement-complete (implementer in flight; await commit)
```

Output includes elapsed time in each phase (minutes or seconds), branch/range if set, finding counts (C#/H#/M#/L# format), next phase hint.

### Validation & Resume Routing: `validate-state.py`

All pipelines use `validate-state.py` to validate and route resume entrypoints. From `milestone-pipeline/validate-state.py`:

```bash
# Usage:
#   validate-state.py <ID>                 # print summary
#   validate-state.py <ID> --report-next-phase  # canonical Phase-N-step-Y entrypoint
#   validate-state.py <ID> --check         # exit 0 if valid, 2 if corrupted

validate-state.py panel-refresh-2026q2-e1 --report-next-phase
# Output: Phase 2 step 4 (implementation in flight; await commits, then advance to implement-complete)
```

**Key pattern:**
- Reads `state.json`
- Validates schema (all REQUIRED_FIELDS present, phase in PHASE_ORDER)
- Maps current phase → canonical resume entrypoint string
- Exit 0 success, 1 missing, 2 schema error
- PHASE_ORDER and NEXT_PHASE_ENTRYPOINT dicts are single source of truth for phase naming

### Python Interpreter Resolution (Venv Quirk)

All scripts and Python entry points use this pattern:

```bash
PY="$REPO_ROOT/.venv/Scripts/python.exe"
if [[ ! -x "$PY" ]]; then
  PY="$REPO_ROOT/.venv/bin/python"
fi
if [[ ! -x "$PY" ]]; then
  PY="python3"
fi
```

This ensures Windows and POSIX both work correctly, and avoids stale system `python3`.

---

## 4. References Layout (Shared & Pipeline-Local)

### Shared References (Used by ALL Four Pipelines)

These live in `.claude/references/` and are imported by command files:

- **`app-invariants.md`** (100–150 lines): AI-1 through AI-15 inviolable design rules
  - Example: AI-1 (PySide6+PyVista stack), AI-2 (Qt-free tests), AI-3 (pv.OFF_SCREEN), AI-4 (clip_scalar not clip_box)
  - Every agent references this; violations are CRITICAL findings

- **`critique-format.md`** (60–80 lines): Canonical severity rubric and finding entry template
  - Severity: CRITICAL, HIGH, MEDIUM, LOW
  - Finding shape: `### <SEVERITY> — <title>`, **Where:** file:line, **Evidence:** quote, **Why it matters:** impact, **Suggested fix:** direction
  - Critic agents follow this exactly for dedupe

- **`anti-patterns.md`** (150–200 lines): Canonical "Don't" guard rules (shared + pipeline-specific)
  - Example: "Critic elevates severity to make pipeline look productive" (CRITICAL)
  - Example: "Implementer writes critique sections" (BLOCKER)

### Pipeline-Local References

Each pipeline has a `.claude/references/{pipeline-name}/` directory:

- **`state-schema.md`** (milestone-pipeline only): Path layout, JSON schema, field reference table
  - Documents: `.claude/notes/milestones/{ID}/` + `research/`, `artifacts/`, `state.json`

- **`phase-*.md`** (all pipelines): Detailed phase descriptions and step procedures
  - Example: `phase-1-research.md`, `phase-2-implement.md`, etc.
  - Used by agents to understand expected outputs

- **`agent-prompts.md`** (all pipelines): Templates for agent dispatch
  - Pre-filled Inputs blocks, scope boilerplate, etc.

- **`source-registry.md`** (capability-scout, frontend-uplift): Known external sources and their relevance
  - Links to arXiv, GitHub issues, design docs, academic papers

- **`adversary-critique-checklist.md`** (milestone-pipeline, frontend-uplift): 10-axis checklist for critics
  - Axes: app-invariant compatibility, math honesty, test impact, performance, license, GL offscreen risk, effort, value, sequencing, etc.

- **`adversary-critique-template.md`** (milestone-pipeline): Pre-filled finding template with all required sections

---

## 5. Notes/Output Directory Layout

### Generic Pattern

Each pipeline stores its outputs in `.claude/notes/{PLURAL-PIPELINE-NAME}/{ID}/`:

| Pipeline | Directory | Subdirs | Key Files |
|---|---|---|---|
| `/capability-scout` | `.claude/notes/capability-scouts/{SLUG}/` | `discovery/`, `synthesis/`, `artifacts/` | `final-report.md`, `phase-*.md` |
| `/milestone-pipeline` | `.claude/notes/milestones/{ID}/` | `research/`, `artifacts/` | `state.json`, `research/{ID}-brief.md`, `implement-plan.md`, `critique.md`, `dispatch.log` |
| `/roadmap` | `.claude/notes/roadmaps/{SLUG}/` | (none) | `state.json`, `roadmap.md`, `issue-drafts/`, `phase-*.md` |
| `/frontend-uplift` | `.claude/notes/frontend-uplift/{SLUG}/` | `discovery/`, `synthesis/`, `artifacts/` | `panel-chrome/` (PNGs), `final-report.md`, `state.json` |

### Milestone-Pipeline Detail

The most elaborate layout is `.claude/notes/milestones/{ID}/`:

```
.claude/notes/milestones/panel-refresh-2026q2-e1/
├── state.json
├── research/
│   ├── panel-refresh-2026q2-e1-brief.md     (researcher output)
│   └── [other-researcher]-brief.md           (if multiple researchers)
├── artifacts/
│   ├── implement-plan.md                    (implementer output)
│   ├── critique.md                          (critic output)
│   └── impl-branch-commits.txt              (tracking commits)
└── dispatch.log                             (orchestrator log)
```

### Dispatch Log Format

The `dispatch.log` is human-readable, with ISO 8601 UTC timestamps and elapsed time. Format (from `milestone-pipeline.md` Phase 1 Step 2):

```
2026-05-20T14:32:00Z | milestone-researcher | agent-a | dispatched
2026-05-20T14:47:12Z | milestone-researcher | agent-a | returned | 15m12s | status=complete
2026-05-20T14:48:00Z | milestone-researcher | agent-b | dispatched
2026-05-20T15:03:45Z | milestone-researcher | agent-b | returned | 15m45s | status=gate-required | gate_reason=external_dependency
```

Fields: timestamp | agent-role | agent-name | event | [duration] | [status=...] | [extra info]

This log is used for debugging, resume logic, and user visibility.

---

## 6. Agent-Memory Layout

### Directory Structure

Each agent that uses memory gets a dedicated directory:

```
.claude/agent-memory/
├── milestone-researcher/
│   └── lessons.md          (append-only)
├── milestone-adversary-critic/
│   └── lessons.md
├── roadmap-materializer/
│   └── lessons.md
└── [other-agent-names]/
    └── lessons.md
```

### Lessons.md Protocol

All lessons files are **append-only**. From agent memory bootstrap:

```markdown
## Memory Bootstrap

If `.claude/agent-memory/{agent-name}/lessons.md` exists and is < 200 lines,
load all content. If >= 200 lines, load first 50 lines only and note that file
may be compacted (see memory-update-protocol.md).

Lessons are lessons from prior runs. Use them to accelerate discovery.
```

**Who appends:**
- Only the agent itself appends (via Bash heredoc `>>`, NOT Write tool)
- Example (from `roadmap-materializer.md` Step 7):

```bash
# Append lesson to memory
cat >> "$REPO_ROOT/.claude/agent-memory/roadmap-materializer/lessons.md" <<'LESSON'

## Lesson from {SLUG} materialization ({ISO_DATE})

[Agent documents what it learned for future runs]
- Scope expansion risk: user often wants to pull in related epics
- Materialization time: ~5 min to draft 4 epics with dependencies
LESSON
```

### Compaction Protocol

File `.claude/references/memory-update-protocol.md` (shared) documents when/how to compact:

- **Trigger:** lessons.md ≥ 200 lines
- **Action:** Compress to first 30 lines (summary) + most recent 5 lessons
- **Owner:** User or Scout (not during pipeline runs)
- **No loss:** Old lessons archived to `.claude/agent-memory/{agent-name}/archive/lessons-{DATE}.md`

---

## 7. Re-Usable Shared Infrastructure (DO NOT DUPLICATE)

### What Exists Globally (in `.claude/references/`)

These artifacts are used by multiple pipelines and agents. The `/repository-architect` command should **import and reference**, not redefine:

1. **`app-invariants.md`** — AI-1 through AI-15 (currently AI-1 through AI-15 documented)
   - Used by: milestone-researcher, adversary-critic, capability-scout-challenger, all agents
   - Severity: Violating an invariant = CRITICAL finding
   - **DO NOT duplicate per-pipeline; reference globally**

2. **`critique-format.md`** — Severity rubric, finding template, dedupe logic
   - Used by: adversary-critic, capability-scout-challenger, any critic agent
   - **DO NOT redefine severity; use canonical CRITICAL/HIGH/MEDIUM/LOW**
   - **DO NOT redefine finding shape; use canonical ### <SEVERITY> — <title> template**

3. **`adversary-critique-checklist.md`** — 10-axis checklist (app-invariants, math, tests, performance, license, GL offscreen, effort, value, sequencing, cross-cutting)
   - Used by: milestone-adversary-critic, adversary-critic, frontend-uplift-critic
   - **DO NOT duplicate; reference in agent description**

4. **`anti-patterns.md`** — Canonical "Don't" guard rules
   - Canonical 12 entries: critic-elevating, implementer-writing-critique, skipping init-state, concurrent agent dispatch, etc.
   - Pipeline-specific entries added as appendix (e.g., milestone-specific: "don't run rectify as sub-agent")
   - **DO NOT spread across files; centralize in one anti-patterns.md with pipeline callouts**

### What Must Be Pipeline-Local

Some infrastructure is specific to the pipeline's phase structure and cannot be shared:

- **`state-schema.md`** — Defines the shape of `state.json` for that pipeline
  - `.claude/references/milestone-pipeline/state-schema.md` documents milestone state fields
  - `.claude/references/repository-architect/state-schema.md` (NEW) will document repo-architect state fields
  - **Cannot be shared; each pipeline has unique phase history, artifact tracking**

- **Phase-*.md documents** — Detailed phase procedures
  - `.claude/references/milestone-pipeline/phase-1-research.md`, `phase-2-implement.md`, etc.
  - `.claude/references/repository-architect/phase-*.md` (NEW) for new pipeline phases
  - **Cannot be shared; each pipeline has its own step sequences**

- **Agent-prompts.md** — Boilerplate for agent dispatch
  - `.claude/references/milestone-pipeline/agent-prompts.md` templates researcher, implementer, critic, rectifier
  - `.claude/references/repository-architect/agent-prompts.md` (NEW) for repo-architect agents
  - **Cannot be shared; each pipeline has different agent roles**

---

## 8. Hooks (Present or Absent?)

### Search for Hook References

Existing pipelines do NOT reference hooks in their command files or agent descriptions. A search for `.claude/hooks/` in the repo yields no matches in the four existing pipeline command files.

```bash
grep -r "\.claude/hooks" .claude/commands/*.md
grep -r "\.claude/hooks" .claude/agents/*.md
# (no output)
```

### Current State

The `.claude/hooks/` directory **does not exist** in the AVC repo currently. However, the four-pipeline infrastructure is built to support hooks for future use:

- **Potential hook points:** Pre-init validation, post-phase-advance notifications, pre-dispatch checks, post-dispatch artifact validation
- **Pattern (if added):** `.claude/hooks/{event-name}.sh` (executable bash script)
  - Example: `.claude/hooks/pre-phase-advance.sh {pipeline} {ID} {new_phase}` → validates schema before transition

### User Intent

Based on the system design, it appears the user **intends for `/repository-architect` to ADD hook support** if it makes sense for structural refactoring (e.g., validate file moves before commit, verify directory tree consistency post-refactor). The blueprint should:

1. **Document where hooks COULD live** if future phases need them
2. **NOT require hooks for Phase 1** (they're optional infrastructure)
3. **Show the expected hook signature** if a pipeline author wants to add one

Example placeholder in `/repository-architect` phase-*.md:

```markdown
## Optional: Pre-Phase Hook

If `.claude/hooks/pre-plan-validation.sh` exists, the orchestrator runs:
  bash .claude/hooks/pre-plan-validation.sh {ID}

This allows custom validation (e.g., check that source tree is consistent) before
the planning phase begins. Exit 0 = proceed, exit non-zero = block with error.
```

---

## 9. Conventions to Mirror Verbatim

### Venv-Path Pattern (Python Interpreter Resolution)

**ALWAYS include this in every bash script that calls Python:**

```bash
# Prefer the .venv interpreter so we never accidentally hit a stale system python3.
PY="$REPO_ROOT/.venv/Scripts/python.exe"
if [[ ! -x "$PY" ]]; then
  PY="$REPO_ROOT/.venv/bin/python"
fi
if [[ ! -x "$PY" ]]; then
  PY="python3"
fi
```

This ensures:
1. Windows `.venv/Scripts/python.exe` is tried first
2. POSIX `.venv/bin/python` is tried second
3. Bare `python3` is the fallback only if venv is missing

### Milestone ID Shape Validation

**Copy this exact regex for any pipeline using user-provided IDs:**

```bash
# From init-state.sh
if ! [[ "$ID" =~ ^[a-zA-Z][a-zA-Z0-9]*(-[a-zA-Z0-9]+)*$ ]] || (( ${#ID} > 60 )); then
  echo "error: invalid milestone id '$ID' -- must be 1-60 chars, alphanumeric segments separated by single dashes, starting with a letter" >&2
  exit 2
fi
```

Pattern: `^[a-zA-Z][a-zA-Z0-9]*(-[a-zA-Z0-9]+)*$`
- Starts with letter
- Allows alphanumerics
- Dashes separate segments (no double-dash, no leading/trailing dash)
- Max 60 chars

### Dispatch.log Format (ISO 8601 UTC, elapsed time)

**Timestamps MUST be ISO 8601 UTC format:**

```
2026-05-20T14:32:00Z | role | agent-name | dispatched
2026-05-20T14:47:12Z | role | agent-name | returned | 15m12s | status=<status>
```

Rules:
- Always UTC (Z suffix, never timezone offsets)
- Elapsed time in `15m12s` format (minutes then seconds)
- Status field is always present on `returned` line
- Each field separated by ` | ` (space-pipe-space)

### Critique Severity Headers (Canonical Shape)

**Every finding in a critique MUST start with:**

```markdown
### <SEVERITY> — <title>

**Where:** `file.py:line-number`

**Evidence:** (quote or observation from code)

**Why it matters:** (1-2 sentences on impact)

**Suggested fix:** (direction, NOT full implementation plan)

**Regression-guard test:** (optional; testing strategy)
```

Where `<SEVERITY>` is exactly one of: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` (all caps).

### Rectification Commit Subject (Milestone-Specific)

**When a rectifier commits fixes, subject line MUST follow:**

```
rect({ID}): close C1, H1, H2, M1
```

Format: `rect({milestone-id}): close {finding-ids-comma-separated}`

Finding IDs are auto-assigned by dedupe script: `C#` (CRITICAL), `H#` (HIGH), `M#` (MEDIUM), `L#` (LOW).

### No-Auto-Push Rule (CRITICAL)

**This is enforced by External-Write Boundary but stated explicitly:**

> Agents MUST NOT `git push` to any remote under any circumstances.
> Only the user can authorize publication. Orchestrator does NOT push either.
> All changes stay local until user runs `git push` manually.

This is non-negotiable for safety (prevents accidental publication of incomplete work).

### Don't Run Rectify as Sub-Agent Rule

**Rectification is the ONLY phase that must NOT be automated:**

From `milestone-pipeline.md` anti-pattern guard:

> **Anti-Pattern: Dispatching rectifier as a sub-agent**
> Rectification requires user decision on deferred/invalidated findings. Never auto-dispatch;
> require explicit user [y] after critique review. Include gate text in Phase 4 Step 0.

Rectifier is run by the user as part of Phase 4 Step 1, not as a dispatched sub-agent.

---

## 10. Anti-Patterns to Flag (Existing Pipeline Guards)

The existing pipelines guard against specific mistakes. The `/repository-architect` command should adopt similar guards for its domain. Here are the canonical anti-patterns from the four pipelines:

### Canonical (Cross-Pipeline) Anti-Patterns

| Pattern | Why It Breaks | Guard |
|---|---|---|
| **Critic elevates severity to look productive** | Artificial inflation masks real risk. | Severity calibration rule: CRITICAL requires AI violation or design dead-end, not "wish it were better." |
| **Implementer writes critique sections** | Phases must not overlap; critic independence is required. | Scope-bounds forbid implementer from reading/writing critique.md. |
| **Concurrent agent dispatch in same phase** | Race conditions on state.json. Exactly one agent per phase. | Orchestrator enforces one dispatch per phase; validate-state.py returns unique next entrypoint. |
| **Skipping init-state.sh** | state.json doesn't exist; validators crash. | init-state.sh MUST be called once per {ID} before any other script. |
| **Agent writes beyond their scope** | Corrupts shared state or downstream artifacts. | Every agent lists scope-bounds; orchestrator validates against file-write logs. |
| **Phase transition without checkpoint.py** | State machine desync; resume logic breaks. | Only checkpoint.py may transition phases; all other scripts are read-only. |
| **Agent ignores lessons.md** | Redundant re-discovery; slower pipelines. | Agent description explicitly says "bootstrap memory" on startup. |
| **Critic doesn't use canonical finding template** | Dedupe script can't parse; findings get duplicated. | critique-format.md is non-optional; agent validates output shape. |

### Milestone-Pipeline-Specific Anti-Patterns

| Pattern | Why It Breaks | Guard |
|---|---|---|
| **Researcher writes to implementation_path before approval** | Implementer doesn't have clean baseline. | Researcher outputs brief only; impl_path set by implementer after user approval. |
| **Implementer ignores implementation_base commit** | Changes can't be traced to original; blame breaks. | Phase 2 Step 1 requires base commit capture via checkpoint.py before implementation. |
| **Critic runs on uncommitted changes** | Critique is out of sync with actual commits. | Critic reads git log and diff of {COMMIT_RANGE} only; enforces range was committed. |
| **Finding IDs not sequential (C1, H5, M2)** | Dedupe logic assumes contiguous numbering. | Dedupe script auto-assigns C#, H#, M#, L# based on position; rectifier reads these. |
| **Rectifier defers all findings** | Pipeline stalls; no progress. | User must decide: defer is OK only if explicitly justified per finding. |
| **Multiple critics run sequentially without deduplication** | Redundant findings in critique_finding_counts. | Phase 3 Step 3 includes dedupe-findings.py to merge/collapse duplicates. |

### Roadmap-Specific Anti-Patterns

| Pattern | Why It Breaks | Guard |
|---|---|---|
| **Decomposer edits roadmap.md directly** | Materializer can't populate {{placeholders}}; overwrites happen. | Decomposer writes to phase-*.md refs only; materializer owns roadmap.md edit. |
| **Materializer runs without state transition** | Resume logic skips phases. | checkpoint.py must be called to advance to decompose-complete before materializer. |
| **Issue draft created without user approval** | Issues published without review. | Materializer drafts only; orchestrator surfaces drafts and waits for [y] before gh issue create. |

### Capability-Scout-Specific Anti-Patterns

| Pattern | Why It Breaks | Guard |
|---|---|---|
| **Synthesizer elevates loose ideas to candidates** | Bloat; unclear scope. | Candidate must reference prior win or explicit code pattern from repo; no free-form ideas. |
| **Challenger reviews candidate without app-invariant cross-check** | Invariant violations slip through. | 10-axis checklist MUST include app-invariants.md column; BLOCKER if AI violated. |
| **Final report ranked without RICE calibration** | User doesn't know effort/value. | RICE-light applied per scoring rubric; +30% bonus for foundational candidates. |

### Frontend-Uplift-Specific Anti-Patterns

| Pattern | Why It Breaks | Guard |
|---|---|---|
| **Visual scout renders Qt app under QT_QPA_PLATFORM=offscreen** | Segfault (Qt crashes without display). | Render verification uses pv.OFF_SCREEN = True; never construct MainWindow() in test. |
| **Panel chrome capture misses a panel** | Incomplete review; critic can't assess all surfaces. | render-panel-chrome.py emits 12 PNGs; critic asserts all panels present before challenge. |
| **Critic uses Mayavi for volume render** | Violates AI-1 (forbidden stack). | Anti-pattern guard: "Mayavi AI-1 violation" listed; critic rejects any Mayavi suggestion. |

---

## Summary: Blueprint for `/repository-architect`

This document outlines the **exact structural patterns** used across the four existing pipelines. The `/repository-architect` command should:

1. **Use identical command-file frontmatter** (YAML: command, description, argument-hint)
2. **Define a phase state machine** with forward-only transitions via `checkpoint.py`
3. **Dispatch sub-agents** returning JSON (file_path, status, summary, injection_attempts)
4. **Enforce external-write boundary** (no git push, no orchestrator functions, no other slash commands)
5. **Create pipeline-local references** (state-schema.md, phase-*.md, agent-prompts.md)
6. **Store outputs in `.claude/notes/repository-architect/{ID}/`** with dispatch.log
7. **Use agent-memory** for lessons.md (append-only, shared across runs)
8. **Reference shared infrastructure** (app-invariants.md, critique-format.md, anti-patterns.md) without duplication
9. **Guard against canonical anti-patterns** listed in section 10
10. **Mirror conventions exactly** (venv-path pattern, ISO 8601 timestamps, severity headers, commit message shape)

The blueprint provides the raw material for the orchestrator to clone these patterns when designing the `/repository-architect` command.

