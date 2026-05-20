# Phase 1 — SURVEY (parallel)

**Purpose:** dispatch 5 scouts in a single assistant turn so they run concurrently in their own context windows.  Wall-clock budget: ~15 minutes per scout; total elapsed time on the main session ≈ slowest scout's wall-clock (NOT 5× sequential).

## Dispatch matrix

| Mode | Scouts fired | When to choose |
|---|---|---|
| **standard** (default) | competitive + math-research + oss-trends + desktop-platform + adversary (5) | Default for any open-ended scout run; the canonical configuration. |
| **lean** | competitive + adversary + math-research (3) | When the user explicitly requests a fast turnaround OR the scope is narrow (e.g. "what would peer algebraic-geometry apps ship that we don't"). |
| **deep** | All 5; adversary uses Opus | When the scope is full-app AND the user requests `--deep`. |

The orchestrator sets `survey_mode` via `checkpoint.py <ID> --set survey_mode='"standard"'` BEFORE dispatch so resume can see what was originally chosen.

## Dispatch protocol (CRITICAL — single turn)

Fire **all selected scouts in one assistant message** containing N `Agent` tool blocks (one per scout).  Sequential dispatch destroys the diversity benefit and doubles wall-clock.

Each scout receives the FULL canonical prompt from `references/capability-scout/agent-prompts.md` verbatim, with these substitutions:

- `{ID}` → the scout id (slug)
- `{SCOUT_BRIEF}` → state.scout_brief verbatim
- `{BRIEF_PATH}` → `.claude/notes/capability-scouts/{ID}/survey/<scout-name>-brief.md`

Use `isolation: worktree` on every scout — each gets its own copy of the repo state so they can't interfere.  Scouts do not write code, but worktree isolation ensures they can grep / read the repo without contention.

## Subagent_type and model

| Scout | Sub-agent type | Model override |
|---|---|---|
| competitive | `general-purpose` | sonnet (default) |
| math-research | `general-purpose` | sonnet (default) |
| oss-trends | `general-purpose` | sonnet (default) |
| desktop-platform | `general-purpose` | sonnet (default) |
| adversary | `general-purpose` | sonnet (default) — OR Opus when `survey_mode=deep` |

The custom agent definitions in `.claude/agents/capability-scout-*.md` exist to carry the agent's persistent memory (`memory: project`) — when invoked via the slash command, the runtime should route based on agent definition matching.  When dispatched via `Agent` tool, use `subagent_type: general-purpose` and paste the canonical prompt; the memory accumulation happens via the agent-definition file even when called this way.

## Returning briefs into state

When a scout returns, the main session:

```bash
.claude/scripts/capability-scout/checkpoint.py <ID> --append scouts_returned='"<scout-name>"'
.claude/scripts/capability-scout/checkpoint.py <ID> --append survey_briefs='".claude/notes/capability-scouts/<ID>/survey/<scout-name>-brief.md"'
```

When all dispatched scouts have returned:

```bash
.claude/scripts/capability-scout/checkpoint.py <ID> survey-complete
```

The orchestrator should NOT advance to `survey-complete` until `len(scouts_returned) == len(scouts_dispatched)`.  `status.sh` will surface the pending set if you forget.

## Reading the briefs

Each brief is ~500–1500 words.  Read EVERY brief end-to-end before starting Phase 2 synthesis.  The synthesis step's value comes from cross-referencing patterns across briefs (e.g., "Surfer ships per-surface color templates; QtAds has palette-template support; the adversary flags 'all 9 surfaces share `#9aa6c8`' as HIGH — high-signal triangulation").

## Failure modes

- **A scout returns with a thin brief** (< 200 words, < 3 candidates) → re-dispatch ONCE with a stricter prompt suffix.  If the second attempt also fails, accept the thin brief and document the failure in `artifacts/synthesis.md` (the synthesis section can simply note "competitive scout returned a thin brief; weighting accordingly").
- **A scout hangs** (background task without notification past 30 min) → kill the task; re-dispatch with the same prompt.
- **All scouts fail** → halt the pipeline; surface to the user before advancing state.
