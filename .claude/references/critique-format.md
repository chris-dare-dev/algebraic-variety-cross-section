# Canonical critique format (algebraic-variety-cross-section)

Shared severity language for the adversary scout (Phase 1 of `/capability-scout`) and every Challenger sub-agent.  Mirrors CONTEXT.md §6's 5-phase adversarial reviewer convention.

## Severity rubric

| Severity | Meaning | Calibration anchor |
|---|---|---|
| **CRITICAL** | Erodes core value proposition or violates a load-bearing app invariant (AI-1 .. AI-15) with no easy redesign path. | Rare. Reserve for genuine showstoppers (e.g., a candidate that would segfault under offscreen tests, mis-attribute a math claim, or break the marching-cubes pipeline contract). |
| **HIGH** | Capability gap that peer scientific-viz / desktop math tools all have and this app lacks, OR a clear regression in user-visible quality. | Typical count: 1-3 per critique. |
| **MEDIUM** | Quality-of-life gap that compounds over time, OR a stylistic / a11y / perf paper-cut that's visible most launches. | Typical count: 3-6 per critique. |
| **LOW** | Cosmetic / docs / micro-UX paper-cut. | Typical count: 0-many; this is the catch-all. |

**Honesty calibration:** a critique with 0 CRITICALs and 2 HIGHs is a credible result.  Padding severity erodes signal.  Inflating to make findings look impressive is the opposite of useful.

## Challenger 4-tier mapping (for /capability-scout Phase 3 and /frontend-uplift Phase 3)

| Challenger tier | Maps to | Meaning |
|---|---|---|
| **BLOCKER** | CRITICAL | Candidate must be dropped or fundamentally redesigned (AI violation with no redesign, infeasible scope, OSS license blocker). |
| **MAJOR** | HIGH | Candidate is shippable but with significant cost the synthesis didn't surface. |
| **MINOR** | MEDIUM | Candidate is shippable with light scope adjustment. |
| **NONE** | (none) | Candidate survives the gauntlet cleanly. |

The orchestrator maps these to `state.challenge_finding_counts` as `{critical, high, medium, low}` for downstream prioritization.

## Finding entry shape

Every entry — regardless of severity — uses this shape:

```markdown
### <severity> — <short title>

**Where:** `<file>:<line>` (or "no specific file" for cross-cutting findings)
**Evidence:** verbatim quote, off-screen-render path, or 1-2 sentence observation
**Why it matters:** 1-2 sentences on user impact / risk
**Suggested fix:** 1-2 sentences (NOT a full implementation plan — surface the direction, let the rectify phase or follow-on milestone do the design)
```

For the Challenger's per-candidate findings, the entry shape is:

```markdown
### <BLOCKER|MAJOR|MINOR|NONE> — CAND-N / <verbatim title from synthesis>

**Objections:** (one bullet per AI / axis the candidate violated)
- AI-N: <specific violation>
- Effort honesty: <if applicable>
- Value density: <if applicable>

**Suggested scope adjustment:** (MAJOR/MINOR only — concrete v0/v1 cut-line)
**If BLOCKER:** recommended kill OR redesign sketch.
```

## What NOT to do

- **Don't manufacture findings to round out severity counts.**  A clean candidate getting `NONE` is the calibration anchor.
- **Don't soften BLOCKER findings.**  If a candidate violates AI-1 (proposes Mayavi) or AI-3 (segfault-prone offscreen test), name it.
- **Don't propose detailed implementations in findings.**  That's the follow-on remediation pass's job (see CONTEXT.md §6 phases 4-5).  The critique surfaces direction, not implementation.
- **Don't be hyperbolic.**  "The app is unusable" is wrong unless it genuinely is. "Reset Camera button doesn't repaint the viewport without a follow-up `render()` call" is precise (and is in fact the §8.1 bug that was fixed in commit 1).
