# Phase 2 — SYNTHESIZE (main session)

**Purpose:** the main session reads every survey brief end-to-end and writes a unified opportunity catalog at `artifacts/synthesis.md`.  Sub-agents do NOT synthesize — the main session does, because synthesis requires holding all 5 briefs in working memory simultaneously and judging cross-brief signal.

## Inputs

- `.claude/notes/capability-scouts/{ID}/survey/competitive-brief.md`
- `.claude/notes/capability-scouts/{ID}/survey/math-research-brief.md`
- `.claude/notes/capability-scouts/{ID}/survey/oss-trends-brief.md`
- `.claude/notes/capability-scouts/{ID}/survey/desktop-platform-brief.md`
- `.claude/notes/capability-scouts/{ID}/survey/adversary-brief.md`

(Subset for `survey_mode=lean`.)

## Output

`.claude/notes/capability-scouts/{ID}/artifacts/synthesis.md`

## Synthesis protocol (read this BEFORE writing)

1. **Read every brief end-to-end first.**  Do NOT start writing synthesis after reading one brief — the value is in cross-referencing.

2. **Build a candidate inventory.**  Every distinct capability proposed across the 5 briefs becomes a candidate row.  Each candidate gets a stable id (`CAND-1`, `CAND-2`, …) ordered by appearance.

3. **Deduplicate.**  When two scouts surface the same capability (e.g. competitive scout flags "Fano 3-fold support" and math-research scout flags "Klein cubic V₃ implementation"), merge them into ONE candidate with BOTH evidence sources cited.

4. **Cross-link evidence.**  Each candidate cites EVERY brief that contributed evidence — that triangulation is the strongest signal for prioritization.

5. **Categorize.**  Use this taxonomy (do not invent new categories):
   - **Variety / mathematical scope** — new variety family (Fano 3-fold, abelian surface, Severi variety…), new figure within an existing variety, new mathematical convention
   - **Rendering / mesh pipeline** — alternative renderer evaluation, mesh-quality improvements, marching-cubes alternatives, parametric pipeline polish
   - **Interaction / UI** — sliders, dropdowns, dock layout, color picker, keyboard shortcuts (NOTE: heavy UI focus belongs in `/frontend-uplift`; reserve `/capability-scout` for capability-level UI like "side-by-side comparison mode")
   - **Math typography / documentation** — KaTeX-rendered tooltips, citation surfacing, help menu, mathematical disclaimers
   - **Export / interoperability** — STL/OBJ/PLY mesh export, screenshot polish, Mathematica-format export, animation video export
   - **Performance / numerics** — marching-cubes acceleration (Numba/JIT), GPU rendering, large-grid handling
   - **Distribution / packaging** — PyInstaller, Briefcase, single-binary `.app`/`.exe`/`.dmg`
   - **State / persistence** — `QSettings`-backed state, parameter presets, "tour" mode through saved configurations

6. **Rough-size every candidate.**  T-shirt: XS (<1wk), S (1-2wk), M (3-6wk), L (>6wk).  Don't go finer than t-shirts at this stage; the challenger and Phase 4 prioritization refine.

7. **Don't propose solutions in detail.**  Each candidate gets a 1-paragraph "what it would look like" sketch.  Detailed design happens in CONTEXT.md §6's 5-phase pipeline if/when the user pulls it forward.

## Candidate entry shape (use verbatim)

```markdown
### CAND-N — Short imperative title

**Category:** Variety/scope | Rendering/mesh | Interaction/UI | Typography/docs | Export/interop | Performance/numerics | Distribution/packaging | State/persistence
**Size:** XS | S | M | L
**Evidence triangulation:** N briefs (e.g. "competitive ✓, math-research ✓, adversary ✓" — count of briefs that surfaced this)

**What it is:** 2-3 sentence plain-English description.

**Why it matters:** 1-2 sentence value-pitch from the user's / researcher's perspective.

**Sources:**
- Competitive scout: <bullet pointing to the capability row in competitive-brief.md>
- Math-research scout: <bullet pointing to the paper / construction in math-research-brief.md>
- (or any subset of the 5 briefs)

**Closest app analog (today):** `surfaces.py:NNN` or `view_panel.py:NNN` — what's there now, why it's insufficient.  Or "no analog" when net-new.

**Sketch:** 1-paragraph design hint.  Cite specific file:line attach points where credible.  This is enough for the challenger to evaluate feasibility; it is NOT a full implementation plan.

**Open questions:** bullet list, or "none" when the candidate is well-specified.
```

## Synthesis sections (use this order)

1. **Executive summary** — 4-6 sentences: how many candidates, what categories dominate, top theme, top tension across briefs.
2. **Triangulation strength** — count candidates by evidence-source count: "N candidates have 3+ brief sources (strong signal); N have 2; N have 1 (weak — flag for challenger scrutiny)".
3. **Candidate catalog** — every candidate, ordered as: high-triangulation first within each category, then by t-shirt size ascending.
4. **Cross-cutting tensions** — places where briefs disagreed (e.g. "competitive scout favored Fano 3-fold; math-research scout flagged the README claim as aspirational vs CONTEXT.md ground-truth that only 3 varieties are live — explicitly close that doc-vs-code gap").  Surface these explicitly.
5. **What's already in flight** — bullet list of candidates that overlap CONTEXT.md §9 "things explicitly NOT done" entries (cite the §9 entry).  These are NOT killed — they're flagged so the challenger doesn't re-litigate.
6. **Parking lot** — proposals from the briefs that don't survive synthesis (1-2 sentence rejection reason each, often citing AI-N violations).

## After writing

```bash
.claude/scripts/capability-scout/checkpoint.py <ID> --set synthesis_path='".claude/notes/capability-scouts/<ID>/artifacts/synthesis.md"'
.claude/scripts/capability-scout/checkpoint.py <ID> --set candidate_count=<N>
.claude/scripts/capability-scout/checkpoint.py <ID> synthesize-complete
```

## Anti-patterns

| Tempting belief | Reality |
|---|---|
| "I can synthesize without reading every brief — the executive summaries are enough." | The triangulation signal lives in matching specific claims across briefs.  Executive summaries don't carry that signal. |
| "Let me invent new categories." | The taxonomy is fixed for a reason — it makes Phase 4 ranking comparable across scout runs. |
| "Candidates should be ranked here, not in Phase 4." | Synthesis is inventory; ranking is Phase 4.  Don't conflate them — the challenger needs to see all candidates equally weighted. |
| "I'll skip the cross-cutting tensions section." | This is the HIGHEST-VALUE section.  Disagreements between briefs are where novel insights live — and the README-claims-Fano-but-CONTEXT-says-no kind of tension is uniquely powerful for this app. |
| "I'll write detailed implementation plans for each candidate." | Phase 4's job, not Phase 2's.  Sketches only.  Detailed plans land in CONTEXT.md §6's 5-phase pipeline after the user picks winners. |
| "Propose Mayavi as an alternative renderer." | **AI-1**: broken on Apple Silicon as of 2025.  Don't surface — drop to parking lot with the AI-1 citation. |
