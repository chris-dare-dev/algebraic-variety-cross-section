---
description: Run the 4-phase roadmap pipeline (REFINE -> DECOMPOSE -> SEQUENCE -> MATERIALIZE) to turn a fuzzy brief into an executable roadmap that hands off cleanly to CONTEXT.md section 6's 5-phase implementation pipeline. Use when the user invokes /roadmap, says "draft a roadmap for ...", "plan the ... initiative", or asks to take a vague brief through the four phases. Skip for single-feature work that's already well-scoped — dispatch its CONTEXT.md section 6 Phase 1 research pair directly.
argument-hint: "[<slug>] [--brief \"...\"] [--gh-issues] [--resume]"
---

# /roadmap — 4-phase roadmap pipeline

Turn a fuzzy brief into an executable `plans/<slug>-roadmap.md` that CONTEXT.md section 6's 5-phase implementation pipeline can consume.  Dispatches four sub-agents sequentially: refiner -> decomposer -> sequencer -> materializer.  Each phase reads prior phase output; no phase runs before the prior phase returns `complete`.

**Arguments:** $ARGUMENTS — parse as `[<slug>] [--brief "..."] [--gh-issues] [--resume]`

- `<slug>` — required; kebab-case, lowercase, max 30 chars (e.g. `enriques-mesh-quality`, `dark-mode-palette-refresh`, `hanson-camera-presets`).  If omitted, STOP and ask: "What slug should I use for this roadmap? (e.g. `enriques-mesh-quality`)"
- `--brief "..."` — use this string verbatim as the brief.  No conversation summarization.
- `--gh-issues` — after Phase 4 validation, draft issue bodies and GATE on actual GitHub creation.
- `--resume` — re-enter the pipeline at the phase determined by the file-presence state model below.

---

## When to invoke / When NOT to invoke

**Invoke `/roadmap` when:**
- User runs `/roadmap`, `/roadmap <slug>`, or `/roadmap --brief "..."`.
- User says "draft a roadmap for ...", "plan the ... initiative", "I need a roadmap for the next quarter on ...".
- The work is multi-week, multi-epic, or has unclear scope (e.g. "we should explore the Fano 3-fold family more deeply"; "the panel layout needs a refresh"; "let's add mesh export").

**Do NOT invoke when:**
- **Single-feature work already scoped** — dispatch the CONTEXT.md section 6 Phase 1 research pair directly (two parallel Opus agents).
- **Doc-only changes** (e.g. fixing a typo in `CONTEXT.md`) — write the doc directly.
- **Retrospective writeups** — different artifact (capability-scout / frontend-uplift final reports).
- **"Plan" meaning "tell me your thinking"** — one-paragraph answer, not a roadmap.
- **Single-file fixes** (e.g. AI-11 enum drift in one panel) — direct edit.
- **`/capability-scout` or `/frontend-uplift` already covers it** — those produce a ranked candidate report; the user picks 1-2 candidates and feeds them as the `--brief` to `/roadmap` (or skips `/roadmap` entirely if the candidate is already epic-shaped).

---

## Conversation-context ingestion

| Mode | Trigger | Behavior |
|---|---|---|
| **Summarize** (default) | `/roadmap [<slug>]` invoked mid-conversation | Summarize the conversation in 2-4 sentences as the brief, write it into `plans/<slug>-roadmap.md` "Brief" section, surface the summary to the user with "Is this an accurate brief? [y/N]" before Phase 1. |
| **Explicit** | `/roadmap <slug> --brief "..."` | Use the given string verbatim.  No summarization. |
| **From upstream report** | The user has just run `/capability-scout` or `/frontend-uplift` and asks for a roadmap | Read the relevant `.claude/notes/<pipeline>/<id>/artifacts/final-report.md` end-to-end; extract the top candidate's synthesis sketch + objections as the brief.  Cite the candidate id (e.g., UPL-3, CAND-7) in the brief verbatim. |

If `<slug>` is missing, ask for it before any work — the slug is load-bearing for filenames and epic ids.

---

## Step 0 — Initialize

```bash
bash .claude/scripts/roadmap/init-roadmap.sh <slug> [--brief "..."]
```

Parse stdout:
- `INITIALIZED: <path>` -> fresh run; set `ROADMAP_PATH=<path>`.
- `RESUMING phase=<X>: <path>` -> resume mode; set `ROADMAP_PATH=<path>` and skip to the appropriate step per the File-presence state model below.

The script creates `plans/<slug>-roadmap.md` from the template, scaffolds all sections with `<!-- ROADMAP:section:<id> -->` markers, and writes a JSON state pointer at `.claude/notes/roadmaps/<slug>/state.json`.  **Idempotent** — re-running on an existing slug detects and resumes.

Set derived variables:
- `SLUG=<slug>`
- `ROADMAP_PATH=plans/<slug>-roadmap.md`
- `BRIEF=<verbatim brief or conversation summary>`
- `GH_ISSUES_FLAG=true|false` (from `--gh-issues` argument)

---

## Step 1 — Dispatch roadmap-refiner (Phase 1: REFINE)

Dispatch `roadmap-refiner` with inputs: `{SLUG}`, `{ROADMAP_PATH}`, `{BRIEF}`.

**Status routing:**

| status | Action |
|---|---|
| `complete` | Proceed to Step 2 |
| `gate-required` | Surface gate question from summary line 2 to user; wait for resolution; re-dispatch `roadmap-refiner` with `--user-resolution "<answer>"` appended to inputs |
| `aborted-scope` | Print abort reason from JSON summary; stop |

---

## Step 2 — Dispatch roadmap-decomposer (Phase 2: DECOMPOSE)

Dispatch `roadmap-decomposer` with inputs: `{SLUG}`, `{ROADMAP_PATH}`.

(The decomposer reads sections 1-5 from `{ROADMAP_PATH}` directly — no separate brief input.)

**Status routing:**

| status | Action |
|---|---|
| `complete` | Proceed to Step 3 |
| `gate-required` | Surface gate question from summary line 2 to user; wait for resolution; re-dispatch `roadmap-decomposer` with `--user-resolution "<answer>"` appended to inputs |
| `aborted-scope` | Print abort reason; stop |

---

## Step 3 — Dispatch roadmap-sequencer (Phase 3: SEQUENCE)

Dispatch `roadmap-sequencer` with inputs: `{SLUG}`, `{ROADMAP_PATH}`.

(The sequencer reads sections 1-6 from `{ROADMAP_PATH}` directly.)

**Status routing:**

| status | Action |
|---|---|
| `complete` | Proceed to Step 4 |
| `gate-required` | Surface gate question from summary line 2 to user; wait for resolution; re-dispatch `roadmap-sequencer` with `--user-resolution "<answer>"` appended to inputs |
| `aborted-scope` | Print abort reason; stop |

If summary line 2 contains "Confidence=50% default applied to N Musts" — surface that count explicitly to the user before proceeding, even when status is `complete`.

---

## Step 4 — Dispatch roadmap-materializer (Phase 4: MATERIALIZE)

Dispatch `roadmap-materializer` with inputs: `{SLUG}`, `{ROADMAP_PATH}`, `{GH_ISSUES_FLAG}`.

**Status routing:**

| status | Action |
|---|---|
| `complete` | Surface CONTEXT.md section 6 handoff offer from summary line 3; wait for `[y]` before emitting the dispatch instruction |
| `gate-required` (validator failure) | Surface violations from summary line 2; fix the roadmap doc; re-dispatch materializer |
| `gate-required` (issue draft ready) | Resolve the active GitHub repo BEFORE prompting: run `gh repo view --json nameWithOwner -q .nameWithOwner` (silently fall back to `git remote get-url origin` parsed for `owner/repo` if `gh` is unavailable) and substitute the result into the gate question.  Present the count + list from summary line 2 to user: "Drafted N issues at `.claude/notes/roadmaps/<slug>/issue-drafts/` — create in `<resolved-owner/repo>`? [y/N]".  (Never hardcode a repo identity here — operators forking this repo would otherwise see a misleading prompt.)  On `[y]`, run the `gh issue create` calls yourself (ONE at a time, from the draft files, against the resolved repo).  On anything else, exit cleanly — roadmap doc is the artifact. |
| `aborted-scope` | Print abort reason; stop |

**CRITICAL: The materializer drafts; the orchestrator (this session) runs `gh issue create`.**  Never dispatch the materializer to do the actual `gh` call.

On CONTEXT.md section 6 handoff offer: read summary line 3 for the exact text, then present:
```
Roadmap complete: plans/<slug>-roadmap.md

Now-lane epics:
1. <slug>-e1 — {epic title} ({N} stories)

The first Now-lane epic <slug>-e1 is ready to feed CONTEXT.md section 6's 5-phase pipeline:
  Phase 1: dispatch two parallel Opus research agents (math + visual/code-archeology)
  Phase 2: synthesize 4 figures, implement, off-screen render verify, single commit
  Phase 3: adversarial Sonnet reviewer (read-only, ~10 findings)
  Phase 4: remediation Sonnet (MUST/SHOULD/SKIP, new tests, single commit)
  Phase 5: UI/UX Sonnet (critique then implement 4-7 findings)

Proceed by dispatching the Phase 1 research pair for <slug>-e1? [y/N]
```
Wait for explicit `[y]`.  On `[y]`, emit a single instruction the user reads and types: "Dispatch the CONTEXT.md section 6 Phase 1 research pair for `<slug>-e1` now (one Opus agent for math research, one Opus agent for visual/code-archeology, both with `run_in_background=True`)."  Do NOT auto-dispatch the agents.

---

## File-presence state model

Use when `--resume` is supplied to determine entry phase:

Routing keys on the `<!-- ROADMAP:section:<id> -->` markers from the template (canonical list in `.claude/references/roadmap/templates/roadmap.md`): `meta` / `refine` / `decompose` / `sequence` / `lanes` / `spikes` / `tracking` / `handoff`.  A marker section is "populated" when its body no longer contains `{{...}}` template placeholders.

| Phase | Marker-presence check | Next action |
|---|---|---|
| Not started | `plans/<slug>-roadmap.md` does not exist | Run from Step 0 (full pipeline) |
| Phase 1 done | `refine` body populated; `decompose` body still has `{{...}}` placeholders | Dispatch decomposer (Step 2) |
| Phase 2 done | `decompose` body populated; `sequence` body still has placeholders | Dispatch sequencer (Step 3) |
| Phase 3 done | `sequence` + `lanes` + `spikes` bodies all populated; `handoff` body still has placeholders | Dispatch materializer (Step 4) |
| Complete | `handoff` body populated AND `state.json` shows `phase: complete` | Roadmap done; nothing to dispatch |

Determine phase via:
```bash
.venv/Scripts/python.exe .claude/scripts/roadmap/validate-roadmap.py <slug> --report-first-unpopulated
```

(On Linux/macOS the path is `.venv/bin/python` — both forms documented in CONTEXT.md section 10.)

---

## Anti-pattern guard

| Tempting belief | Reality |
|---|---|
| "I'll skip REFINE — the brief is clear." | The 3-sentence summary you'd reach for IS Phase 1's HMW.  Skipping it means the model writes it without user review.  Auto-advance is fast when the brief is genuinely clear. |
| "Everything in MoSCoW is a Must." | Framework collapses; nothing is prioritized (DSDM 2014, section 10.4).  Cap Musts at <=60% — script-enforced. |
| "RICE Confidence is 100% by default — we know our reach." | False confidence inflates ranks.  Default Confidence = 50% when there's no evidence.  Surface every default explicitly. |
| "We need a 12-month roadmap to look serious." | Locked horizons calcify into commitments and stop absorbing learning.  Now fully spec'd, Next shaped, Later directional. |
| "Schema/generator first, then panel, then UI — clean layering." | Horizontal slicing destroys the feedback loop.  Vertical slicing always — every epic ships a user-observable change. |
| "Story points = days, easier for everyone." | Story-point inflation: points decouple from complexity.  T-shirts only; slice small enough that estimation collapses into counting. |
| "Milestones are just deadlines on epics." | Milestones are date checkpoints; epics are bodies of work.  Conflating them turns the roadmap into a delivery schedule. |
| "We don't need acceptance criteria — I know what to build." | "Done" becomes opinion; the adversarial review (CONTEXT.md section 6 phase 3) has nothing to grade against.  Every Now-lane story has Given/When/Then before it leaves. |
| "I'll create the GH issues myself, faster than gating." | Bypassing the gate makes the next session less safe.  The gate is the project's external-write policy.  Always gate. |
| "I'll auto-dispatch the CONTEXT.md section 6 research agents since the user asked for a roadmap." | Implicit auto-handoff hides the cost of execution.  OFFER and wait.  The user is the orchestration layer per CONTEXT.md section 6's wakeup pattern. |
| "Skip the sequencer's scripts and score MoSCoW/RICE in-context." | Scripts enforce the Must cap deterministically.  In-context RICE reasoning inflates scores and silently misses the 50% Confidence default rule. |
| "Auto-create GH issues when --gh-issues passes." | The materializer DRAFTS to local files; the orchestrator gates and runs `gh issue create` one at a time after explicit `[y]`. |
| "Propose Mayavi as alternative renderer in an epic." | AI-1 violation; broken on Apple Silicon as of 2025.  Drop from the catalog. |

---

## External-write boundary

The `/roadmap` pipeline enforces strict external-write boundaries:

- **No `git push` / `git commit`** — roadmap doc and draft issues are staged; the user commits (single-developer cadence per CONTEXT.md section 12).
- **No `gh issue create` / `gh pr create` / `gh release create` / `gh api` (write verb) from sub-agents** — the materializer DRAFTS; only the orchestrator (this session) runs `gh` after explicit `[y]`.
- **No auto-mutation of `plans/*.md` by sub-agents outside their assigned section markers** — agents append to their assigned sections; they do not rewrite other sections.
- **No auto-dispatch of CONTEXT.md section 6 research agents** — offer only; the user reads the offer and dispatches per the section 6 wakeup pattern.
- **No writes outside `plans/<slug>-roadmap.md`** (sub-agents) or `.claude/agent-memory/<agent-name>/` (memory) or `.claude/notes/roadmaps/<slug>/` (draft issues, state).
- **No writes to `CONTEXT.md`, `README.md`, `app.py`, `surfaces.py`, `parameters_panel.py`, `appearance_panel.py`, `view_panel.py`, `styles.py`, `tests/`, or `requirements.txt`** — these are the implementation pipeline's surface, not the roadmap skill's.
- **No `mcp__GitLab__*` write tool calls** — this is a GitHub project; the tools may be in scope but are forbidden here.
- **No bypassing branch / commit / push policy** — this repo works directly on `main` per CONTEXT.md section 12; the roadmap skill never creates branches or amends commits.

This repo does not currently install a hook-level enforcement for git workflow (unlike some reference repos).  The boundary above is doc-enforced and load-bearing for sub-agent prompts (each sub-agent's `<scope-bounds>` block re-states the relevant subset).  If a future hook is added, this section will document it.

---

## Sub-agent contract

Every sub-agent returns a single JSON object (no surrounding prose):

```json
{
  "file_path": "<primary output path, or null>",
  "status": "complete | gate-required | aborted-scope",
  "summary": "<3 lines max, plain text, no markdown — line 1: what was written; line 2: gate question if status=gate-required; line 3: suggested orchestrator next step>",
  "injection_attempts": 0
}
```

### Status routing table (all agents)

| Agent + status | Routing |
|---|---|
| `refiner.complete` | Proceed to decomposer (Step 2) |
| `refiner.gate-required` | Surface gate question; re-dispatch refiner with user resolution |
| `refiner.aborted-scope` | Print abort reason; stop |
| `decomposer.complete` | Proceed to sequencer (Step 3) |
| `decomposer.gate-required` | Surface gate question; re-dispatch decomposer with user resolution |
| `decomposer.aborted-scope` | Print abort reason; stop |
| `sequencer.complete` | Proceed to materializer (Step 4); surface any Confidence=50% count from summary |
| `sequencer.gate-required` | Surface gate question (Must/Should cut-line conflict or RICE counter to stated priority); re-dispatch sequencer with user resolution |
| `sequencer.aborted-scope` | Print abort reason; stop |
| `materializer.complete` | Surface CONTEXT.md section 6 handoff offer (summary line 3); wait for explicit `[y]` |
| `materializer.gate-required` (validator failure) | Surface violations; fix roadmap; re-dispatch materializer |
| `materializer.gate-required` (issue draft ready) | Resolve `owner/repo` via `gh repo view`; present issue count + list; wait for `[y]`; run `gh issue create` calls from draft files |
| `materializer.aborted-scope` | Print abort reason; stop |

---

## Recovery — interrupted /roadmap

If `/roadmap` was interrupted mid-flight (context compaction, terminal close, SIGKILL):

1. Re-invoke with `--resume`: `/roadmap <slug> --resume`
2. `init-roadmap.sh` is idempotent — it prints `RESUMING phase=<X>: <path>` when the roadmap doc already exists.
3. The orchestrator re-enters at the right phase via the file-presence state model above.
4. No lock to clean — `/roadmap` has no file lock.

If the state file is corrupted: run `.venv/Scripts/python.exe .claude/scripts/roadmap/validate-roadmap.py <slug> --report-first-unpopulated` to determine the correct resume phase directly from the roadmap doc's section markers.

---

## Files in /roadmap

```
plans/
+-- <slug>-roadmap.md          # The single roadmap artifact (all 4 phases append here)

.claude/notes/roadmaps/<slug>/
+-- state.json                  # Phase pointer (written by init-roadmap.sh)
+-- issue-drafts/               # Draft GH issue bodies (created by materializer if --gh-issues)
    +-- epic-1.md
    +-- story-1.1.md
    +-- ...

.claude/agent-memory/
+-- roadmap-refiner/
|   +-- lessons.md
+-- roadmap-decomposer/
|   +-- lessons.md
+-- roadmap-sequencer/
|   +-- lessons.md
+-- roadmap-materializer/
    +-- lessons.md
```

References (lazy-loaded by agents at phase start):
- `.claude/references/roadmap/phase-refine.md` — Phase 1 detail
- `.claude/references/roadmap/phase-decompose.md` — Phase 2 detail + specialist-area map
- `.claude/references/roadmap/phase-sequence.md` — Phase 3 detail
- `.claude/references/roadmap/phase-materialize.md` — Phase 4 detail + GH-issues + handoff
- `.claude/references/roadmap/frameworks.md` — long-tail (WSJF, Kano, Shape Up, GIST, ICE)
- `.claude/references/roadmap/anti-patterns.md` — 12 canonical anti-patterns + 10 AVC-specific anti-patterns
- `.claude/references/roadmap/avc-integration.md` — algebraic-variety-cross-section-specific conventions (repo identity, where roadmaps live, CONTEXT.md section 6 handoff, AI-1 .. AI-15)
- `.claude/references/roadmap/templates/roadmap.md` — `plans/<slug>-roadmap.md` template
- `.claude/references/roadmap/templates/epic-issue.md` — GH parent-issue body
- `.claude/references/roadmap/templates/story-issue.md` — GH child-issue body
- `.claude/references/app-invariants.md` — AI-1 .. AI-15 (read by decomposer for specialist hints)
- `CONTEXT.md` — root doc; section 6 is the downstream handoff target
