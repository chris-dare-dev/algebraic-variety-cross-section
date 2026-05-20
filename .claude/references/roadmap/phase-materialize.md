# Phase 4 — MATERIALIZE

**Goal:** finalize `plans/<slug>-roadmap.md`, optionally draft GitHub issue bodies (gated; orchestrator does the actual `gh` calls), and offer (never auto-invoke) the CONTEXT.md section 6 5-phase implementation pipeline handoff.

## Step-by-step

### 1. Lint the roadmap doc

```bash
.venv/Scripts/python.exe .claude/scripts/roadmap/validate-roadmap.py <slug>
```

The validator checks:
- All 8 canonical sections present (`<!-- ROADMAP:section:* -->` markers — `meta`, `refine`, `decompose`, `sequence`, `lanes`, `spikes`, `tracking`, `handoff`).
- No template placeholders left (`{{TOKEN}}`).
- Every `[MUST]` assumption has either a spike OR an evidence citation.
- Every Now-lane story has Given/When/Then.
- Every epic has a `<slug>-eN` id.
- MoSCoW cap is satisfied.
- Dependency graph is a DAG.

Exit codes:
- `0` = clean — proceed.
- `1` = lint failure — orchestrator surfaces the violations and **STOPS**.  Do not advance until clean.
- `2` = usage error.

### 2. GitHub issue drafts (only if `--gh-issues` flag was passed at invocation)

The flag triggers epic + child stories integration depth: one parent issue per Initiative (epic), child issues per Now-lane story, label-based parent reference (`epic:<slug>-eN`).

**The materializer DRAFTS to local files; the orchestrator runs `gh issue create`.**

1. Read the roadmap doc to extract:
   - All Now-lane epics from section 6.3 (parents)
   - All Now-lane stories from section 8 with their Given/When/Then AC

2. Create the draft directory:
   ```bash
   mkdir -p .claude/notes/roadmaps/<slug>/issue-drafts
   ```

3. For each Now-lane epic, write a draft parent-issue body to `.claude/notes/roadmaps/<slug>/issue-drafts/epic-N.md` using the template from `.claude/references/roadmap/templates/epic-issue.md`.  Substitute all `{PLACEHOLDER}` tokens.

4. For each Now-lane story, write a draft child-issue body to `.claude/notes/roadmaps/<slug>/issue-drafts/story-N-M.md` using `.claude/references/roadmap/templates/story-issue.md`.

5. Set `status: gate-required` with summary line 2 = "Drafted N issues at .claude/notes/roadmaps/<slug>/issue-drafts/ — orchestrator will resolve repo via `gh repo view` and ask the user before creating."

The orchestrator (the main `/roadmap` session) then:

1. Resolves the active repo: `gh repo view --json nameWithOwner -q .nameWithOwner` (silently falling back to `git remote get-url origin` parsed for `owner/repo` if `gh` is unavailable).  Never hardcoded.
2. Surfaces the issue creation plan to the user:

   ```
   I'm about to create the following issues in <resolved owner/repo>:

   Parent epics (2):
   - enriques-mesh-quality-e1: Resolve canonical sextic sawtooth tear (label: epic:enriques-mesh-quality-e1)
   - enriques-mesh-quality-e2: Back-face culling toggle (label: epic:enriques-mesh-quality-e2)

   Child stories under enriques-mesh-quality-e1 (3):
   - enriques-mesh-quality-e1-s1: Add second Taubin pass guard
   - enriques-mesh-quality-e1-s2: Bounds-pad parameter sweep test
   - enriques-mesh-quality-e1-s3: Off-screen render diff in CI

   Total: 5 issues. Proceed? [y/N]
   ```

3. Waits for explicit `[y]`.  Anything else is **NOT authorization**.

4. On `[y]`, uses `gh issue create` for each one (ONE at a time, from the draft files, against the resolved repo).

5. Appends the created issue numbers back into the roadmap doc under section 10 (`<!-- ROADMAP:section:tracking -->`).

6. Do NOT push.  Do NOT create branches.  Do NOT comment on issues.  Just create.

### 3. Mark state complete

State advancement happens via `init-roadmap.sh --advance`.  `validate-roadmap.py` does NOT support `--advance`.  Call init-roadmap.sh directly with NO fallback chain — a failure here is real (state.json corruption, missing repo root) and MUST surface, not be swallowed.

```bash
bash .claude/scripts/roadmap/init-roadmap.sh <slug> --advance complete
```

On non-zero exit: do NOT continue.  Return `status: aborted-scope` with summary line 2 = `"state advance failed: <stderr from init-roadmap.sh>"`.  State.json drift between disk and the orchestrator's view causes silent re-dispatch of already-completed phases on the next `--resume` — refuse to leave it that way.

### 4. CONTEXT.md section 6 implementation-pipeline handoff

OFFER, never auto-invoke.  This repo does NOT have a single named slash command for the 5-phase implementation pipeline (math research / code archeology -> implementation + off-screen render verify -> adversarial review -> remediation -> UI/UX pass) — the user dispatches each phase per CONTEXT.md section 6's "wakeup pattern".

Single message at the end of Phase 4:

```
Roadmap complete: plans/<slug>-roadmap.md

Now-lane epics:
1. <slug>-e1 — {epic title} ({N} stories)
2. <slug>-e2 — {epic title} ({N} stories) [optional, depending on capacity]

The first Now-lane epic <slug>-e1 is ready to feed CONTEXT.md section 6's 5-phase pipeline:
  Phase 1: dispatch two parallel Opus research agents (math + visual/code-archeology)
  Phase 2: synthesize 4 figures, implement, off-screen render verify, single commit
  Phase 3: adversarial Sonnet reviewer (read-only, ~10 findings)
  Phase 4: remediation Sonnet (MUST/SHOULD/SKIP, new tests, single commit)
  Phase 5: UI/UX Sonnet (critique then implement 4-7 findings)

Proceed by dispatching the Phase 1 research pair for <slug>-e1? [y/N]
```

Wait for explicit `[y]`.  On `[y]`, the orchestrator emits a single instruction: "Dispatch the CONTEXT.md section 6 Phase 1 research pair for `<slug>-e1` now."  The orchestrator does NOT directly dispatch the research agents — the user reads the message and types the next prompt.  Slash-command-to-research-agent auto-dispatch is anti-pattern; the user is the orchestration layer.

## Output additions to roadmap.md

```markdown
<!-- ROADMAP:section:tracking -->
## 10. Tracking (populated by --gh-issues only)

| Epic / Story | GH Issue | Status |
|---|---|---|
| `<slug>-e1` | #234 | open |
| `<slug>-e1-s1` | #235 | open |
| ... | ... | ... |

<!-- ROADMAP:section:handoff -->
## 11. Execution handoff

First Now-lane epic: `<slug>-e1`.

Handoff target: **CONTEXT.md section 6 — the 5-phase implementation pipeline**.

[remainder of section 11 already in the template — repeats the 5-phase summary and the .claude/notes/ artifact convention]
```

## Auto-advance vs gate (decision table)

| Condition | Action |
|---|---|
| `validate-roadmap.py` exit 0 | **Auto-advance** to step 2 |
| `validate-roadmap.py` exit 1 | **STOP.**  Surface violations.  Do NOT proceed. |
| `--gh-issues` flag passed | **GATE before any issue creation.**  No exceptions.  Materializer drafts; orchestrator gates and creates. |
| `--gh-issues` flag passed AND user typed `[y]` | Orchestrator creates issues one at a time; populates section 10 Tracking |
| End of Phase 4 | **GATE on implementation-pipeline handoff.**  OFFER, never auto-invoke. |
| User responds anything other than `[y]` to handoff | Exit cleanly.  Roadmap doc is the artifact; user dispatches Phase 1 of CONTEXT.md section 6 when ready. |

## Hard rules

- **Validator must pass.**  No partial roadmaps shipped.
- **Issue creation gates per-event.**  Prior `[y]` does not authorize a future creation.
- **No `gh issue comment`, `gh pr *`, or `git push` from this skill.**  Issue creation only, and only from the orchestrator.
- **No auto-dispatch of CONTEXT.md section 6 phases.**  OFFER is a string the user reads and types into their next prompt.  The skill does not chain to other agents directly.
- **`.claude/notes/capability-scouts/` / `.claude/notes/frontend-uplifts/` are OFF-LIMITS** for this skill's writes.  Those are other pipelines' state.  The roadmap skill writes ONLY to `plans/<slug>-roadmap.md` and `.claude/notes/roadmaps/<slug>/`.
- **Materializer never runs `gh`.**  Even though the materializer agent has `Write` in its tool list (for drafting), it must NEVER execute `gh issue create`, `gh pr create`, `gh release create`, `gh api` (any write verb), `glab *`, or any `mcp__GitLab__*` write tool.  If the materializer finds itself about to run one of those, return `status: aborted-scope`.
