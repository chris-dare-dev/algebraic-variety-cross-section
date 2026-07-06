# AVC-specific integration

Project-specific conventions for the **Algebraic Variety Viewer** (this repo, `algebraic-variety-cross-section`).  Read this once per roadmap to wire the `/roadmap` output into the project correctly.  This file is a repo-local overlay; it is not in the registry manifest.

## Repo identity

| Item | Value |
|---|---|
| Default branch | `main` |
| Branch policy | **Always work directly on `main`** — no feature branches, no PRs, single commit per phase per CONTEXT.md section 12.  Roadmaps are no exception; the materializer stages `plans/<slug>/roadmap.yaml` and the user commits it. |
| Ticket system | **GitHub Issues** (no GitLab, Jira, Linear).  The orchestrator resolves `owner/repo` at gate time via `gh repo view --json nameWithOwner` — never hardcoded so forks see the correct prompt. |
| Canonical root doc | **`CONTEXT.md`** (not `CLAUDE.md`).  Read its section 6 (5-phase pipeline), section 3 (stack rationale), section 4 (architecture conventions), section 8 (bugs caught), section 9 (things explicitly NOT done), section 12 (final state at handoff). |
| App invariants | `.claude/references/app-invariants.md` — AI-1 .. AI-15.  Every epic must respect these. |

## Roadmap location

The roadmap pipeline writes ONLY to `plans/<slug>/roadmap.yaml` (roadmap/1 format — one flat `items:` list with write-once IDs; scaffolded by `.claude/scripts/roadmap-init.py`, validated by `.claude/scripts/roadmap-validate.py`).  Execution progress goes to append-only journals under `plans/<slug>/progress/`.  Legacy prose roadmaps at `plans/<slug>-roadmap.md` remain readable via `.claude/scripts/milestone-pipeline-resolve-brief.py`'s fallback.

There is no equivalent of `docs/roadmaps/` in this repo — per-epic execution artifacts produced by CONTEXT.md section 6's 5-phase pipeline live under `.claude/notes/<pipeline>/<id>/artifacts/`, NOT under `docs/`.  The relevant existing artifact roots are:

- `.claude/notes/capability-scouts/<id>/artifacts/` — `/capability-scout` outputs (`synthesis.md`, `challenge.md`, `final-report.md`)
- `.claude/notes/frontend-uplifts/<id>/artifacts/` — `/frontend-uplift` outputs (same triple)
- `plans/<slug>/github/` — the roadmap pipeline's issue-body drafts (when `--github` is passed)

The roadmap pipeline never writes outside `plans/<slug>/` (the plan + journals + drafts).

## Milestone-ID format

roadmap/1 IDs are write-once semantic slugs enforced by `roadmap-validate.py`: epics `<slug>-eN`, milestones `<slug>-mN`, spikes `<slug>-spike-N`, tasks `<slug>-t-<sem>`.

- `<slug>` is kebab-case, lowercase, no spaces, max 30 chars.  Same slug as the roadmap directory.
- Dropped items are tombstoned in `retired:`, never deleted; regeneration must carry every existing id forward.

Examples drawn from realistic AVC roadmap scopes:

- `enriques-mesh-quality-e1`, `enriques-mesh-quality-e2`
- `dark-mode-palette-refresh-e1`
- `hanson-camera-presets-e1`, `hanson-camera-presets-e2`
- `fano-3fold-prep-e1`
- `mesh-export-stl-obj-e1`

There is **no `<id>-eN`-keyed state directory in this repo** — CONTEXT.md section 6's 5-phase pipeline runs against each epic by reading the roadmap doc + the epic's specialist hints, and writes its own per-phase artifacts under `.claude/notes/` as it goes (see the existing patterns in `.claude/notes/capability-scouts/` and `.claude/notes/frontend-uplifts/`).

## GitHub Issues integration

Triggered by the `--github` flag at `/roadmap` invocation.

### Depth: epic + child stories

- One **parent issue** per Initiative (epic).  Labels: `epic:<slug>-e<N>`, `roadmap:<slug>`.
- One **child issue** per Now-lane story.  Labels: `story`, `epic:<slug>-e<N>`.
- Parent reference: child body contains a literal `## Parent: #<number>` line (auto-substituted after parent is created).  GitHub renders this as a clickable cross-link.

GitHub does NOT have native epic/story types in Issues (only in Projects).  The label-based approach is the standard workaround.

### Tooling

Uses `gh issue create` from the GitHub CLI.  The **materializer never shells out to `gh`** — it emits per-issue body files under `plans/<slug>/github/` and reports the count.  The **orchestrator** (the main `/roadmap` session) is the only thing that may run `gh issue create`, and only after explicit per-event `[y]` from the user.  One issue at a time so a partial failure is recoverable.

The orchestrator must resolve the repo identity at gate time:

```bash
gh repo view --json nameWithOwner -q .nameWithOwner   # primary
# fallback if gh is unavailable:
git remote get-url origin                              # parse for owner/repo
```

Never hardcode `cedar/algebraic-variety-cross-section` or any other identity — operators forking this repo would otherwise see a misleading prompt.

### Hard rules

- **Always gate.**  External writes (issue creation) require explicit per-event authorization.  Prior `[y]` does not authorize a future creation.
- **No `gh pr *`.**  The single-developer cadence is "no PRs"; this skill never creates PRs.
- **No `gh issue comment`, `gh issue close`, `gh issue edit`.**  Creation only.
- **No labels not on the existing label set.**  Run `gh label list` first; if `epic:*` labels do not exist, create them in a single batch (gated separately).

## Pairing with CONTEXT.md section 6's 5-phase implementation pipeline

The roadmap pipeline OFFERS the implementation-pipeline handoff at the end of Phase 4 — never auto-invokes.  Because this repo does not yet have a single named slash command that drives all five phases (the user dispatches phase agents directly per CONTEXT.md section 6's "wakeup pattern"), the offer reads:

```
Roadmap complete: plans/<slug>/roadmap.yaml

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

On `[y]`, the orchestrator emits a single instruction the user reads and types into their next prompt — the orchestrator does NOT dispatch the research agents directly.  Slash-command-to-research-agent direct invocation is anti-pattern in this project; the user is the orchestration layer.  (See CONTEXT.md section 6 "Wakeup pattern" for the same principle applied to multi-agent dispatch.)

## Resumability after compaction

The roadmap.yaml file IS the state.  Re-invoking `/roadmap enriques-mesh-quality` after compaction reads the existing `plans/enriques-mesh-quality/roadmap.yaml`, validates it with `.venv/Scripts/python.exe .claude/scripts/roadmap-validate.py <path>`, and resumes at the first incomplete phase per the orchestrator contract in `.claude/commands/roadmap.md`.  IDs are write-once — regeneration carries every existing id forward; drops go to `retired:`.

## Existing slash commands the roadmap should pair with

These commands exist in this repo; the roadmap should name them in the relevant epic's "Specialist hints" section when the work overlaps.  They are NOT auto-invoked by the roadmap — they live at the same orchestration level as `/roadmap` itself and the user dispatches each in turn.

| Slash command | When the roadmap epic should hint at it |
|---|---|
| `/capability-scout` | The epic is exploratory / "what should we build next in the variety-survey space?"  Final report at `.claude/notes/capability-scouts/<id>/artifacts/final-report.md` is the canonical input.  Run BEFORE `/roadmap` when the brief is itself a question. |
| `/frontend-uplift` | The epic touches the GUI / panel layout / styles / interaction surface.  Final report at `.claude/notes/frontend-uplifts/<id>/artifacts/final-report.md` (e.g., `2026q2-panel-refresh`) is a strong brief source.  The roadmap epic's specialist hints should cite the relevant UPL-N candidate ids. |

A typical workflow: `/capability-scout` or `/frontend-uplift` produces a ranked candidate report -> the user picks the top 1-2 candidates -> invokes `/roadmap` with `--brief` set to the candidate's synthesis sketch -> the roadmap pipeline produces `plans/<slug>/roadmap.yaml` -> the user dispatches CONTEXT.md section 6's 5-phase pipeline per Now-lane epic.

## Canonical 5-surface set + renderable surfaces

For epics that need off-screen render verification (any epic touching `surfaces.py`, `app.py`'s render pipeline, or `appearance_panel.py`'s color handling), the canonical 5-surface set documented in `.claude/references/frontend-uplift/phase-discover.md` is the right "show me it works across the variety registry" smoke set.  The renderable surfaces today are: K3 (2 subtypes — Fermat quartic, Kummer), Enriques (4 figures), Calabi-Yau (4 figures — 3 parametric Hanson + 1 implicit Dwork), Fano 3-fold (Picard rank 1 family).

## Qt + VTK + PyVista stack constraints

CONTEXT.md section 3 documents the stack rationale; AI-1 through AI-15 in `.claude/references/app-invariants.md` document the architectural locks.  The most load-bearing for roadmap epics:

- **AI-1**: PySide6 + PyVista + pyvistaqt only.  No Mayavi (broken on Apple Silicon 2025), no Plotly / k3d / matplotlib-3D, no raw VTK.
- **AI-2 / AI-3**: tests are Qt-free; render verification is `pv.OFF_SCREEN = True`.  NEVER construct `MainWindow()` under `QT_QPA_PLATFORM=offscreen` — segfaults during VTK GL context creation.
- **AI-9**: any new `processEvents()` call requires the `self._computing` re-entrancy guard.
- **AI-10**: domain-clip changes do NOT regenerate the mesh — only the clip is recomputed.  Raw mesh cached as `self._raw_mesh`.

Primary platform: macOS on Apple Silicon (the user's daily-driver desktop).  Linux/Windows are claimed but less-tested; if an epic might regress them, name it in the specialist hints.

## What the roadmap pipeline should NOT touch

- `app.py`, `surfaces.py`, `parameters_panel.py`, `appearance_panel.py`, `view_panel.py`, `styles.py` (these are the implementation pipeline's surface)
- `tests/` (same)
- `requirements.txt` (no new deps without a deliberate pinned-range bump)
- `CONTEXT.md`, `README.md` (these are the user-curated root docs; roadmaps must not auto-edit them)
- `docs/` if it ever exists (off-limits as a forward-looking rule)
- `.claude/notes/capability-scouts/` / `.claude/notes/frontend-uplifts/` (other pipelines' state)
- `.claude/agent-memory/<other-pipelines>/` (other pipelines' memory)
- The frontend or backend code at large — the roadmap pipeline is plan-only; code-writing is the implementation pipeline's job

The pipeline writes ONLY under `plans/<slug>/` and `.claude/agent-memory/roadmap-*/`.
