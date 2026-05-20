# Phase 3 — CHALLENGE (sub-agent)

**Purpose:** dispatch a single sub-agent (the Challenger) to argue AGAINST each candidate in the synthesis catalog so Phase 4 prioritization receives honest feasibility signal.  This is the analog of CONTEXT.md §6's Phase 3 adversarial reviewer — except it critiques PROPOSED capabilities, not shipped code.

## Inputs

- `.claude/notes/capability-scouts/{ID}/artifacts/synthesis.md`
- (Optional) the 5 survey briefs for ground-checking — challenger reads these when it suspects a synthesis claim drifted from its source.

## Output

`.claude/notes/capability-scouts/{ID}/artifacts/challenge.md`

## Dispatch

Single `Agent` call with `subagent_type: general-purpose`, `model: sonnet` (no Opus override — the challenger workload fits comfortably in Sonnet's context).  Use `isolation: worktree` for repo-read isolation.

Use the canonical Challenger prompt from `references/capability-scout/agent-prompts.md` verbatim.  Substitute:
- `{ID}` → scout id
- `{SYNTHESIS_PATH}` → `.claude/notes/capability-scouts/{ID}/artifacts/synthesis.md`
- `{CHALLENGE_PATH}` → `.claude/notes/capability-scouts/{ID}/artifacts/challenge.md`

## Severity rubric (Challenger-specific)

The challenger uses a 4-tier rubric distinct from the standard CRITICAL/HIGH/MEDIUM/LOW critique format:

| Challenger tier | Maps to standard critique severity | Meaning |
|---|---|---|
| **BLOCKER** | CRITICAL | Candidate must be dropped or fundamentally redesigned (AI invariant violation with no redesign, infeasible scope, OSS license blocker, math claim that wouldn't survive AI-15 honesty discipline).  Rare — calibrate carefully. |
| **MAJOR** | HIGH | Candidate is shippable but with a significant cost the synthesis didn't surface (AI invariant collision needing redesign, performance regression, effort under-estimated by ≥2x, macOS Qt+VTK offscreen footgun unaddressed). |
| **MINOR** | MEDIUM | Candidate is shippable with light scope adjustment (tooltip-citation incomplete, color-token drift, AI-11 enum-shorthand in new code). |
| **NONE** | n/a | Candidate survives the gauntlet cleanly. |

The orchestrator maps these to the standard format when populating `state.challenge_finding_counts` for the final report.

## The 10-axis CHALLENGER checklist

Every candidate gets evaluated against:

1. **App-invariant compatibility** (AI-1 .. AI-15 in `.claude/references/app-invariants.md`).  Most common violations: AI-1 (proposing Mayavi/Plotly/matplotlib-3D), AI-4 (clip_box), AI-15 (math claim without 2-source verification).
2. **Math claim honesty (AI-15)** — does the proposal cross-reference ≥2 sources?  Does it honestly state the relationship between the named variety and what's actually being plotted (real shadow / birational / parametric cross-section)?
3. **Variety pipeline correctness (AI-6 / AI-7 / AI-14)** — for new generators: does it declare implicit vs parametric?  Use the right helper?  Hanson-style → cell_normals discipline?  Return `pv.PolyData` or raise `ValueError`?
4. **Test impact (AI-2)** — does the candidate add a test surface?  Is it Qt-free?  Adding `pytest-qt` is AI-2 BLOCKER unless macOS Qt+VTK offscreen segfault is addressed.
5. **Performance impact** — does the candidate add >100ms to render-pipeline critical path?  Marching cubes is ~0.5s already; new layers stack.  Memory budget for large grids.
6. **License compatibility (LGPL redistribution lens)** — PySide6 is LGPL; importing GPL-3.0 libraries into a redistributable binary triggers contamination.  Flag GPL-3.0 candidates MAJOR (study-only OK).  BLOCKER if redistribution is in scope.
7. **macOS Qt+VTK GL offscreen risk** — any candidate touching tests (AI-2) or off-screen rendering (AI-3) must address this footgun.
8. **Effort honesty** — t-shirt size matches the single-developer / small-team cadence of CONTEXT.md §6's 5-phase pipeline.  Compare to historical variety implementations (K3, Enriques, CY each took ~1-2 days of agent-orchestrated work; Fano is the next).
9. **Value density** — does the candidate's value justify its scope?  A 6-week candidate with marginal research-tool utility is worse than a 1-week candidate with comparable utility.
10. **Sequencing dependencies** — does this candidate depend on another candidate?  Should the catalog flag the DAG?  (E.g., "side-by-side comparison mode" depends on a viewport-management refactor; "Fano 3-fold figures" depend on settling the README-vs-CONTEXT.md doc gap.)

## After receiving the challenge

Parse the challenge to populate:

```bash
.claude/scripts/capability-scout/checkpoint.py <ID> --set challenge_path='".claude/notes/capability-scouts/<ID>/artifacts/challenge.md"'
.claude/scripts/capability-scout/checkpoint.py <ID> --set challenge_finding_counts='{"critical": N_BLOCKER, "high": N_MAJOR, "medium": N_MINOR, "low": N_CLEAN}'
.claude/scripts/capability-scout/checkpoint.py <ID> challenge-complete
```

## Anti-patterns

| Tempting belief | Reality |
|---|---|
| ">50% of candidates have MAJOR or BLOCKER objections — the synthesis was bad." | Possible.  Usually means the challenger prompt is too aggressive OR the synthesis under-considered the AI-15 math-honesty axis or the AI-2/AI-3 macOS Qt+VTK axis.  Re-read the challenge with that lens before re-running. |
| "Every candidate gets at least a MINOR objection — that's calibration." | No.  Padding objections is noise.  A clean candidate gets NONE.  If the challenger emits 0 NONEs the calibration is broken. |
| "BLOCKER findings should kill candidates outright." | Not always.  A BLOCKER + a credible redesign sketch leaves Phase 4 deciding whether the redesigned candidate is worth pursuing.  E.g., "use Mayavi for an extra view" → redesign to "evaluate PyVista alternatives; Mayavi out per AI-1" is plausible. |
| "The challenger should propose its own candidates." | No.  Phase 1's job.  The challenger evaluates the synthesis; it does not extend it. |
| "AI-15 math-honesty is overrated — researchers know the disclaimers." | No.  The Barth misattribution in CONTEXT.md §5.2 is the cautionary tale: docstring drift on math claims compounds.  Calibrate strict on AI-15. |
