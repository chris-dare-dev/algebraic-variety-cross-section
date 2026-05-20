# Phase 1 -- Research

**Goal:** maximize prior-art coverage in 15 wall-clock minutes so the
Implement phase doesn't reinvent or contradict known-better approaches.

This phase mirrors CONTEXT.md section 6's "Phase 1: Two parallel Opus
research agents" pattern -- the same convention that produced the three
existing variety passes (K3, Enriques, Calabi-Yau).  The milestone-pipeline
formalizes that pattern with explicit state, checkpoints, and an agent
memory file per role.

## Dispatch matrix

| User signal | Mode | Concurrency | Model |
|---|---|---|---|
| Default (no override) | Standard | 2 agents in PARALLEL | Sonnet |
| `--deep`, milestone touches >2 subsystems, novel math (new variety family, post-2010 parametric construction) | Deep | 1 agent | Opus (`model: "opus"` on the Agent call) |
| `--single`, "quick", "small", milestone <=200 LOC | Single | 1 agent | Sonnet |

Research output is a brief, not code -- there is no merge surface, so
sub-agents run without worktree isolation.  This is the simplest call.

## What every researcher receives

1. **Milestone id** (epic-shaped, e.g. `panel-refresh-2026q2-e5`) -- must appear in the brief filename.
2. **Full user-supplied brief** -- copy the user's original ask verbatim.  Do NOT paraphrase; paraphrasing biases the search.
3. **Dispatch by name** — the `milestone-researcher` agent body at `.claude/agents/milestone-researcher.md` IS the prompt; the orchestrator passes inputs (`{ID}`, `{MILESTONE_BRIEF}`, `{BRIEF_PATH}`) via the Task tool, NOT via prompt substitution.
4. **Output path:** `.claude/notes/milestones/{ID}/research/agent-{a|b}-brief.md`.  Use `a` for the first dispatched, `b` for the second; `solo` for Single / Deep mode.

## Sources to cover (the researcher prompt enforces these)

| Source | Tool | Why |
|---|---|---|
| Existing AVC code | `Grep`, `Read` | Prevents reinventing; finds the generator or panel that already solves a sibling problem |
| `CONTEXT.md` sections 4, 5, 8, 9 | `Read` | The architectural locks (re-entrancy guard, raw-mesh cache, clip_box ban), variety-specific math conventions, bugs already fixed, and explicit non-goals |
| `.claude/references/app-invariants.md` (AI-1..AI-15) | `Read` | The non-negotiable locks the implementer cannot violate |
| Prior milestone artifacts | `Grep` over `.claude/notes/milestones/` | Captures institutional memory not visible in code |
| arXiv math.AG | `WebFetch` | New variety constructions, parameter conventions, real-locus rendering tricks (last 18 months) |
| GitHub OSS | `WebFetch`, `WebSearch` | SageMath / Macaulay2 examples, Imaginary.org, PyVista demos -- license, recency, what to borrow |
| Library docs | `WebFetch` | PySide6, PyVista, pyvistaqt, scikit-image -- version-pinned per `requirements.txt` |

## Brief format (researcher emits this)

Each brief is a single markdown file <=500 lines with these sections in order:

1. **TL;DR** -- 3 sentences.  The recommended approach, the main risk, the backup plan.
2. **Prior art in this repo** -- bulleted list of existing modules / generators / panels the milestone overlaps with.  Include `file:line` for each.
3. **External sources reviewed** -- table of (source, URL, key finding, relevance to this milestone).
4. **Recommended approach** -- <=500 words.  Specific enough that the Implementer can start without further research.
5. **Alternatives considered** -- bulleted list of approaches NOT recommended, with one-sentence reason for rejection.  (Without this section the Implementer cannot defend the choice when challenged.)
6. **Risks and unknowns** -- anything the Implementer needs to design AROUND.  Most often: AI-1..AI-15 conflicts, render-time budget (~500ms single render), Qt re-entrancy (AI-9), VTK PolyData ownership (AI-7, AI-10, AI-14).
7. **AI-15 disclaimers** -- if the milestone proposes a new variety or figure, draft the honest "this is actually..." tooltip text.  Real shadow?  Birational?  Parametric cross-section?
8. **Open questions for the user** -- empty by default.  Populate ONLY if the milestone is genuinely under-specified.

The orchestrator merges briefs by reading both, identifying agreement
(high-confidence path) and disagreement (decision points the main session
resolves).  If a single Opus brief is used (Deep mode), the orchestrator
still reads it end-to-end and writes a 1-paragraph synthesis to
`state.research_synthesis`.

## Hard rules for researchers

- **Read code, don't speculate.**  Every "the existing X generator does Y" claim must have a `file:line` citation.
- **Don't write code.**  Research output is a brief.  If the researcher proposes code, the Implementer ignores it (research-stage code is not under critique).
- **Don't recommend deprecated patterns.**  `requirements.txt`, `CONTEXT.md`, and `.claude/references/app-invariants.md` define current conventions; the researcher must read them before recommending tooling.
- **Cite license on every OSS finding.**  A "great library!" without license info is a dead recommendation.
- **AI-15 honesty.**  Any new variety / figure must declare what mathematical object is actually being plotted (real shadow, birational model, parametric cross-section), not the abstract variety it's named after.  See `.claude/references/app-invariants.md` AI-15.
- **AI-6 / AI-7 pipeline discipline.**  Implicit surfaces go through `_marching_cubes_to_polydata` + Taubin; parametric (Hanson) skip Taubin.  Don't mix.

## Wall-clock budget

Soft cap 15 min, hard cap 30 min (Sonnet 2x parallel).  If a researcher hits
30 min with no brief, kill it and proceed with whatever the other returned.
Pipeline progress > research completeness.

## Checkpoint

When all dispatched researchers have written their brief files:

```bash
.venv/Scripts/python.exe .claude/scripts/milestone-pipeline/checkpoint.py {ID} research-complete
```

This writes `state.phase = "research-complete"` and timestamps the
transition.  Phase 2 reads from this state.
