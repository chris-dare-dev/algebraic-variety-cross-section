# Phase 4 — PRIORITIZE (main session)

**Purpose:** the main session reads synthesis + challenge and writes the ranked final report at `artifacts/final-report.md` ready to feed a follow-on implementation pass (e.g., the 5-phase math-research → implementation → adversarial-review → remediation → UI/UX pipeline in CONTEXT.md §6).  Runs in the main session so the user can review and iterate.

## Inputs

- `.claude/notes/frontend-uplifts/{ID}/artifacts/synthesis.md`
- `.claude/notes/frontend-uplifts/{ID}/artifacts/challenge.md`

## Output

`.claude/notes/frontend-uplifts/{ID}/artifacts/final-report.md`

## Ranking method — PORTFOLIO LANES, then RICE-light WITHIN a lane

**Assign every candidate to exactly ONE lane first, then RICE-rank only WITHIN a lane.**  Cross-lane RICE ranking mathematically buries structural design under XS polish (a 0.25-day cosmetic tweak out-scores a 3-day direction-defining refactor every time), which is exactly the failure the frame-first pipeline exists to prevent.

| Lane | What lands here | Ranking rule |
|---|---|---|
| **`a11y-safety-debt`** | MANDATORY lane, listed **FIRST**, **never ranked away**.  WCAG AA / contrast regressions (AI-12), focus-ring + tab-order gaps, re-entrancy hazards (AI-9 `processEvents()` without the `_computing` guard), the "camera state change without a follow-up `render()`" bug class (`[INT-23]`), 6-digit-hex-into-PyVista (AI-13), math-honesty regressions (AI-15). | Ordered by severity, NOT RICE.  These are debt; they ship regardless of score. |
| **`signature-direction`** | Candidates that execute the chosen art-direction direction (frame-defining moves from synthesis Section 0). | RICE within lane; the recommended direction's moves lead. |
| **`foundations`** | Enabling refactors others depend on (`_qt/styles.py` token consolidation, a shared panel base class, a `LATEX_PREVIEW` helper). | RICE within lane + the foundational bonus. |
| **`workflow`** | Task-completing features (mesh export, exact-numeric entry, side-by-side compare, parameter sweep). | RICE within lane. |
| **`polish`** | Cosmetic single-surface paper-cuts. | RICE within lane; lowest priority by construction. |

Report the lanes in the order above.  A run whose only non-empty lanes are `workflow` + `polish` (nothing in `signature-direction`) is a signal the frame was not translated into candidates — say so explicitly.

## RICE-light (computed WITHIN each lane, adapted for visual / UX)

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

1. **Executive summary** (4–6 sentences) — the adopted visual thesis + chosen direction in one line; the top pick per lane; the mandatory `a11y-safety-debt` items; honest caveat about scout-run confidence ceiling.

2. **Design frame recap** — the visual thesis + 3 divergent directions + BAN-1..15 list + surface map, carried from synthesis Section 0.  Name the chosen direction.

3. **Portfolio-lane ranking table** — grouped by lane, in lane order (**`a11y-safety-debt` FIRST**, then signature-direction / foundations / workflow / polish).  RICE is computed and compared ONLY within a lane:

   | Lane | Rank | Cand id | Title | Size | R | I | C | E | Penalty | Adj-RICE | Challenger |
   |---|---|---|---|---|---|---|---|---|---|---|---|
   | a11y-safety-debt | — | UPL-3 | Restore focus ring on the parameter-grid dot | XS | 10 | 1 | 1.0 | 0.25 | (debt — ships) | — | NONE |
   | signature-direction | 1 | UPL-1 | … the chosen direction's defining move | M | 10 | 3 | 0.8 | 3 | NONE | 8.0 | MINOR |
   | foundations | 1 | UPL-7 | `_qt/styles.py` token consolidation | S | 10 | 1 | 1.0 | 1 | +30% (foundational) | 13.0 | NONE |
   | workflow | 1 | UPL-9 | Exact-numeric parameter entry | S | 3 | 1 | 0.8 | 1 | NONE | 2.4 | NONE |
   | polish | 1 | UPL-12 | Dock-header tint tweak | XS | 3 | 0.5 | 0.5 | 0.25 | NONE | 3.0 | NONE |

   (`a11y-safety-debt` rows are ordered by severity, not RICE — they ship regardless.)

4. **Lanes in detail** — for each lane in order (a11y-safety-debt first): copy the synthesis catalog entry verbatim; append the challenger findings inline; append the within-lane RICE breakdown + rank rationale + DAG dependency note.

5. **Recommended next steps** — 3–5 specific actions:
   - Which `a11y-safety-debt` items must ship first (they are debt, not features — clear them regardless of RICE)?
   - Which 1 foundational candidate unblocks the most downstream work?
   - Which 1–2 candidates (signature-direction or workflow) are ready to enter CONTEXT.md §6's implementation pipeline?
   - Which 1 candidate should be a discovery spike first (e.g., evaluating a library for hands-on PySide6 compatibility)?
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
.claude/scripts/frontend-uplift/checkpoint.py <ID> --set ranked_candidates='[{"id":"UPL-7","title":"...","lane":"foundations","rice":13.0,"rank":1}, ...]'
.claude/scripts/frontend-uplift/checkpoint.py <ID> complete
```

Print a 5-line final summary: uplift id, total candidates, the adopted thesis + chosen direction, the `a11y-safety-debt` count + top pick per lane, BLOCKER count, recommended next step.

## Anti-patterns

| Tempting belief | Reality |
|---|---|
| "Auto-invoke an implementation Agent on the top candidate." | NEVER.  Offer-and-wait. |
| "Rank all candidates in one RICE table — simplest for the user." | NO.  Assign a lane FIRST, RICE only within a lane.  A single cross-lane table lets a 0.25-day polish tweak out-rank a direction-defining refactor — the exact bury-structure-under-polish failure lanes prevent. |
| "The a11y-debt items scored low RICE, so rank them below the features." | NO.  `a11y-safety-debt` is its own lane, listed FIRST, ordered by severity, never ranked away.  It ships regardless of RICE. |
| "Skip the foundational-candidates surfacing — RICE already accounts for it." | NO.  The foundational bonus pushes them up within the `foundations` lane, but the user needs to SEE the dependency DAG to plan sequencing. |
| "RICE Confidence is 1.0 for every candidate — they all came from 4 briefs." | Triangulation is the C-dial.  4 briefs = 1.0; 3 = 0.8; etc.  Reflect the actual triangulation, not aspiration. |
| "Effort estimates should be calendar-precise." | T-shirts (XS/S/M/L) only at this stage.  Calendar precision lives in the §6 Phase 2 implementation pass. |
| "Drop the parking-lot section — it's noise." | Keep it.  Discarded candidates document why the app isn't pursuing X — invaluable when the question recurs. |
| "I'll rank a candidate even if the challenger BLOCKERed it with no redesign." | Don't.  Drop it entirely.  Half-considered BLOCKERs are noise; surface them in the parking lot with the BLOCKER rationale instead. |
