# Phase 2 — SYNTHESIZE (main session)

**Purpose:** the main session reads every discover brief end-to-end + reviews the captured off-screen renders + writes a unified modernization-candidate catalog at `artifacts/synthesis.md`.

## Inputs

- `.claude/notes/frontend-uplifts/{ID}/discover/visual-scout-brief.md`
- `.claude/notes/frontend-uplifts/{ID}/discover/library-scout-brief.md`
- `.claude/notes/frontend-uplifts/{ID}/discover/inspiration-scout-brief.md`
- `.claude/notes/frontend-uplifts/{ID}/discover/current-state-critic-brief.md`
- `.claude/notes/frontend-uplifts/{ID}/renders/*.png` (visual evidence — off-screen renders)

## Output

`.claude/notes/frontend-uplifts/{ID}/artifacts/synthesis.md`

## Synthesis protocol

1. **Read every brief end-to-end first.**  Hold all 4 in working memory.
2. **Look at the renders.**  The visual scout's PNGs are evidence; the synthesizer references them in candidate entries by path.  `Read` each PNG to confirm what the brief described matches what the image shows.
3. **Build a candidate inventory.**  Every distinct modernization opportunity proposed across the 4 briefs becomes a candidate row (`UPL-1`, `UPL-2`, …).
4. **Deduplicate.**  Triangulation is the strongest signal.  When two briefs surface the same upgrade (e.g., library-scout cites `qtawesome` adoption + visual-scout cites "no icon affordances on toolbar buttons"), merge into ONE candidate with both evidence sources.
5. **Cross-link interaction vocabulary.**  Every candidate that involves interaction / animation / panel-layout cites a `[INT-N]` primitive from `references/frontend-uplift/interaction-vocabulary.md`.  This is what makes the catalog comparable.
6. **Categorize** with this fixed taxonomy:
   - **Interaction** — slider behavior, button semantics, dock affordances, keyboard shortcuts, drag-and-drop
   - **Camera / viewport** — VTK trackball, view presets, camera transitions, domain-clip UX
   - **Typography** — font, scale, weight, monospace usage, math typography (KaTeX-tooltip / equation rendering)
   - **Layout** — dock arrangement, panel density, group-box hierarchy, status-bar zoning
   - **Color / theme** — palette tokens, dark mode, per-variety color cues
   - **Tooltips / disclosure** — hover hints, contextual help, citation surfacing
   - **Status / feedback** — busy cursor, status-bar messages, warnings, progress, error overlays
   - **Export / persistence** — screenshot, mesh export, `QSettings` state persistence
   - **Accessibility** — focus rings, contrast, screen-reader / keyboard navigation
   - **Library / dependency** — adopting a new lib (qtawesome, superqt, pyqtdarktheme, etc.)
   - **Cross-cutting refactor** — `styles.py` rationalization, panel base class, etc.
7. **T-shirt every candidate.**  XS (<1d), S (1–3d), M (4–10d), L (>10d).
8. **Don't propose solutions in detail.**  1-paragraph sketches; detailed design happens in the follow-on implementation pass.

## Candidate entry shape (use verbatim)

```markdown
### UPL-N — Short imperative title

**Category:** Interaction | Camera/viewport | Typography | Layout | Color/theme | Tooltips/disclosure | Status/feedback | Export/persistence | Accessibility | Library/dependency | Cross-cutting refactor
**Size:** XS | S | M | L
**Evidence triangulation:** N briefs (e.g. "visual ✓, library ✓, inspiration ✓" — count of briefs that surfaced this)
**Interaction primitives:** [INT-N name], [INT-N name] (if applicable)

**What it is:** 2-3 sentence plain-English description of the upgrade.

**Why it matters:** 1-2 sentence value-pitch from the user's perspective.

**Sources:**
- Visual scout: <bullet pointing to the gap row + render path>
- Library scout: <bullet pointing to the library row>
- Inspiration scout: <bullet pointing to the pattern row + peer-app URL/screenshot>
- Current-state critic: <bullet pointing to the gap row + file:line>

**Closest existing app analog today:** `view_panel.py:NNN` — what's there now, why it's insufficient.  Or "no analog" when net-new.

**Render evidence:** `renders/<slug>-default.png` (visual-scout-captured)

**Sketch:** 1-paragraph design hint.  Cite specific file:line attach points where credible.  Cite `styles.py` constants to be applied or extended.  Cite [INT-N] primitives composing the upgrade.  Note any AI invariants (AI-1 … AI-15) the proposal interacts with.

**Open questions:** bullet list, or "none" when well-specified.
```

## Synthesis sections

1. **Executive summary** — 4–6 sentences: how many candidates, dominant categories, top theme, top tension across briefs.
2. **Triangulation strength** — count candidates by evidence-source count: "N candidates have 3+ brief sources (strong); N have 2; N have 1 (weak — flag for challenger scrutiny)".
3. **Foundational candidates** — surface FIRST: candidates other candidates depend on.  Canonical example for this app: "centralize all string-rendering of equations into a `LATEX_PREVIEW` helper" — once landed, both the rendered-math tooltip and the Help-menu citation card become unlocked.  Synthesis MUST flag foundational candidates explicitly so Phase 4 sequences them correctly.
4. **Candidate catalog** — every candidate, ordered by:  foundational first; then high-triangulation within each category; then by t-shirt size ascending.
5. **Cross-cutting tensions** — places where briefs disagreed (e.g., "inspiration-scout proposed a dark-mode default; current-state-critic flagged 100% of the existing palette as light-theme-coupled — resolution: dark mode is a parallel `styles.py` palette, not a redefinition of the current one").
6. **Already considered + rejected** — bullet list of candidates from the briefs that don't survive synthesis (1-2 sentence rejection reason each, often citing AI-X violations or CONTEXT.md §9 "explicitly NOT done").
7. **Interaction-vocabulary index** — table mapping each `[INT-N]` primitive cited across candidates to the candidate ids using it.

## After writing

```bash
.claude/scripts/frontend-uplift/checkpoint.py <ID> --set synthesis_path='".claude/notes/frontend-uplifts/<ID>/artifacts/synthesis.md"'
.claude/scripts/frontend-uplift/checkpoint.py <ID> --set candidate_count=<N>
.claude/scripts/frontend-uplift/checkpoint.py <ID> synthesize-complete
```

## Anti-patterns

| Tempting belief | Reality |
|---|---|
| "I can synthesize without looking at the renders." | Visual evidence anchors visual claims.  Renders are 30% of the brief's value. |
| "Let me invent new categories." | Fixed taxonomy keeps Phase 4 ranking comparable across runs. |
| "Candidates with 1 brief source are still strong if they sound good." | Single-source candidates ARE weaker signal.  Flag for challenger scrutiny — don't filter them out, but rank them with eyes open. |
| "I'll write detailed implementation plans for each candidate." | Phase 4's job, not Phase 2's.  Sketches only. |
| "Skip the foundational-candidates surface — Phase 4 will figure out dependencies." | NO.  Foundational candidates change the sequencing math; surface them prominently in Section 3 so Phase 4 can RICE-rank with the right DAG context. |
| "Propose `Mayavi` as an alternative renderer in case PyVista has issues." | **AI-1**: Mayavi is broken on Apple Silicon; don't surface as a candidate.  Don't even surface light-touch consideration. |
| "Propose `clip_box` for cube domain clip — it should work in v0.49." | **AI-4**: PyVista's `clip_box` invert semantics on PolyData are broken; commit `b68456f` worked around this with scalar clipping.  Don't relitigate. |
