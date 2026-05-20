# Phase 4 — PRIORITIZE (main session)

**Purpose:** the main session reads synthesis + challenge and writes the ranked final report at `artifacts/final-report.md` ready to feed a follow-on implementation pass (e.g., the 5-phase math-research → implementation → adversarial-review → remediation → UI/UX pipeline in CONTEXT.md §6).  Runs in the main session so the user can review and iterate.

## Inputs

- `.claude/notes/frontend-uplifts/{ID}/artifacts/synthesis.md`
- `.claude/notes/frontend-uplifts/{ID}/artifacts/challenge.md`

## Output

`.claude/notes/frontend-uplifts/{ID}/artifacts/final-report.md`

## Ranking method — RICE-light (adapted for visual / UX)

Each candidate scored on:

| Variable | Scale | Source |
|---|---|---|
| **Reach** (R) | 1 / 3 / 10 | 1 = one panel / one surface; 3 = handful of surfaces or panels; 10 = app-wide (every launch / every surface benefits). |
| **Visual-Impact** (I) | 0.5 / 1 / 3 | 0.5 = polish; 1 = noticeably nicer; 3 = transformative (user first-launch reaction changes). |
| **Confidence** (C) | 0.3 / 0.5 / 0.8 / 1.0 | Triangulation: 1 brief source → 0.3; 2 → 0.5; 3 → 0.8; 4 → 1.0. |
| **Effort** (E) | 0.25 / 1 / 3 / 8 | T-shirt → person-days: XS=0.25, S=1, M=3, L=8. |

**RICE = R × I × C / E**

Challenger penalty:
- BLOCKER with no redesign → drop the candidate entirely (don't rank).
- BLOCKER with a credible redesign sketch → halve the RICE.
- MAJOR → -25% RICE.
- MINOR or NONE → no adjustment.

**Foundational-candidate bonus:** if synthesis Section 3 flagged a candidate as foundational (other candidates depend on it), add +30% to its RICE.  Reasoning: foundational candidates unlock downstream value; their effort is amortized across all dependents.

## Final report sections

1. **Executive summary** (4–6 sentences) — top-3 candidates by adjusted RICE; main thematic recommendation; honest caveat about scout-run confidence ceiling.

2. **Quick-glance ranking table:**

   | Rank | Cand id | Title | Category | Size | R | I | C | E | Penalty | Adj-RICE | Challenger |
   |---|---|---|---|---|---|---|---|---|---|---|---|
   | 1 | UPL-1 | Adopt qtawesome icons across toolbar buttons | Layout | S | 10 | 1 | 0.8 | 1 | +30% (foundational) | 10.4 | NONE |
   | 2 | UPL-7 | Per-variety surface color tokens in `styles.py` | Color/theme | S | 10 | 1 | 1.0 | 1 | NONE | 10.0 | NONE |
   …

3. **Foundational candidates** (FIRST in detailed section) — these unblock the rest; surface them prominently so the user sees the sequencing implications.

4. **Top-10 in detail** — copy the synthesis catalog entry verbatim; append the challenger findings inline; append the RICE breakdown + adjusted score + rank rationale + DAG dependency note.

5. **Recommended next steps** — 3–5 specific actions:
   - Which 1 foundational candidate should ship first?
   - Which 1–2 candidates are ready to enter CONTEXT.md §6's 5-phase implementation pipeline?
   - Which 1 candidate should be a discovery spike first (e.g., evaluating `qtawesome` vs `qtfluentwidgets` for icons — needs hands-on PySide6 compatibility check)?
   - Which candidates to park for the next uplift run?

6. **Visual evidence index** — table of render paths × candidate ids that use them.  Lets the user click through to see what's being proposed.

7. **Honest limitations** — bullet list:
   - Scouts had a 15-minute budget; some surfaces may be under-explored.
   - Triangulation across 4 briefs is strong but not infallible.
   - Effort estimates are rough; ±50% accuracy is the realistic ceiling.
   - The challenger evaluated against current app invariants (AI-1..AI-15); if invariants evolve, BLOCKERs may flip.
   - macOS Qt+VTK offscreen segfault is platform-specific; Linux/Windows may have other footguns the scouts didn't probe.

8. **Cross-reference index** — table of `UPL-id` → which discover briefs cited it + which renders support it.

## Optional handoff offers

The final report includes these footer offers when the top candidates clear sensible thresholds:

```text
## Handoff offers

### Single-candidate handoff (RICE ≥ 5 candidates)

To ship UPL-1 via the 5-phase implementation pipeline (CONTEXT.md §6):

1. Math research is N/A for UI candidates — skip Phase 1.
2. Implementation Sonnet (Phase 2): hand it the UPL-1 detail section + the AI invariants table; ask for a single commit at the end.
3. Adversarial Sonnet (Phase 3): scope to the new UI changes only.
4. Remediation Sonnet (Phase 4): work through the punch list.
5. UI/UX Sonnet (Phase 5): if the candidate touched cross-cutting affordances.

### Multi-candidate program

For ≥ 3 candidates above RICE 3.0, run them sequentially through Phase 2 → 5 of the §6 pipeline, with adversarial reviews scoped to each newly-shipped change.

(Note: frontend-uplift NEVER auto-invokes any implementation.  Always offer-and-wait.)
```

## After writing

```bash
.claude/scripts/frontend-uplift/checkpoint.py <ID> --set final_report_path='".claude/notes/frontend-uplifts/<ID>/artifacts/final-report.md"'
.claude/scripts/frontend-uplift/checkpoint.py <ID> --set ranked_candidates='[{"id":"UPL-1","title":"Adopt qtawesome icons","rice":10.4,"rank":1}, ...]'
.claude/scripts/frontend-uplift/checkpoint.py <ID> complete
```

Print a 5-line final summary: uplift id, total candidates, top-3 by RICE, BLOCKER count, recommended next step.

## Anti-patterns

| Tempting belief | Reality |
|---|---|
| "Auto-invoke an implementation Agent on the top candidate." | NEVER.  Offer-and-wait. |
| "Skip the foundational-candidates section — RICE already accounts for it." | NO.  The foundational bonus pushes them to the top, but the user needs to SEE the dependency DAG to plan sequencing. |
| "RICE Confidence is 1.0 for every candidate — they all came from 4 briefs." | Triangulation is the C-dial.  4 briefs = 1.0; 3 = 0.8; etc.  Reflect the actual triangulation, not aspiration. |
| "Effort estimates should be calendar-precise." | T-shirts (XS/S/M/L) only at this stage.  Calendar precision lives in the §6 Phase 2 implementation pass. |
| "Drop the parking-lot section — it's noise." | Keep it.  Discarded candidates document why the app isn't pursuing X — invaluable when the question recurs. |
| "I'll rank a candidate even if the challenger BLOCKERed it with no redesign." | Don't.  Drop it entirely.  Half-considered BLOCKERs are noise; surface them in the parking lot with the BLOCKER rationale instead. |
