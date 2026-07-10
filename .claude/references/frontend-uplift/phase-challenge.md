# Phase 3 — CHALLENGE (sub-agent)

**Purpose:** dispatch a single sub-agent (the Challenger) to argue AGAINST each modernization candidate so Phase 4 prioritization receives honest signal about feasibility, accessibility risk, dep cost, and Algebraic-Variety-Viewer architectural fit.  Mirrors `/capability-scout` Phase 3 but specialized for the GUI / interaction surface.

## Inputs

- `.claude/notes/frontend-uplifts/{ID}/artifacts/synthesis.md`
- (Optional) the 4 discover briefs under `.claude/notes/frontend-uplifts/{ID}/discover/` for ground-checking the synthesis against its sources.

## Output

`.claude/notes/frontend-uplifts/{ID}/artifacts/challenge.md`

## Dispatch

Single `Agent` call with `subagent_type: general-purpose`, sonnet, `isolation: worktree`.  Use the canonical Challenger prompt from `references/frontend-uplift/agent-prompts.md` verbatim.

Substitute:
- `{ID}` → uplift slug
- `{SYNTHESIS_PATH}` → `.claude/notes/frontend-uplifts/{ID}/artifacts/synthesis.md`
- `{CHALLENGE_PATH}` → `.claude/notes/frontend-uplifts/{ID}/artifacts/challenge.md`

## Severity rubric (Challenger-specific)

The challenger uses the 4-tier rubric mapped to the standard format for state-field consistency:

| Challenger tier | Maps to standard severity | Meaning |
|---|---|---|
| **BLOCKER** | CRITICAL | Must be dropped or fundamentally redesigned.  Examples: app-invariant violation (AI-1 proposing Mayavi / Plotly / matplotlib-3D, AI-2 pytest-qt-style UI tests, AI-3 MainWindow under offscreen, AI-4 clip_box on PolyData, AI-7 Hanson `consistent_normals=True`), GPL-3.0 library that can't be vendored cleanly with PySide6 LGPL stack, segfault-prone proposal, **Axis-11 distinctiveness failure (a frameless synthesis, or a projected surface scoring 6+ on the §10 rubric — e.g. a neon sci-fi-HUD restyle, BAN-1/8)**. |
| **MAJOR** | HIGH | Shippable but with significant cost the synthesis didn't surface.  Examples: 50MB+ wheel for a small affordance; macOS Qt+VTK offscreen surface not addressed for a new render path; AI-12 contrast regression with no remediation plan; AI-9 re-entrancy guard missed on a new `processEvents()` call; UX regression on first-launch (`— Select —` placeholder removed without alt UX); **an Axis-11 projected §10 score of 3–5 (template-leaning)**. |
| **MINOR** | MEDIUM | Light scope adjustment.  Examples: dock-header color drift, missing `aria`-equivalent label on a button, slider-step coercion edge case, AI-11 Qt-enum-shorthand drift in new code. |
| **NONE** | LOW (clean) | Candidate survives.  Aim for 30–60% of candidates rating NONE — that's calibrated. |

## The 11-axis FRONTEND-CHALLENGER checklist

Every candidate gets evaluated against:

1. **App-invariant compatibility** — AI-1 (PySide6+PyVista stack), AI-2 (Qt-free tests), AI-3 (pv.OFF_SCREEN for headless render), AI-4 (clip_scalar, not clip_box), AI-5 (`scalars=` kwarg on clip_scalar), AI-6 (implicit vs parametric pipelines), AI-7 (Hanson normals: cell_normals=True, consistent_normals=False), AI-8 (`Surface`/`ParamSpec` contract), AI-9 (`_computing` re-entrancy guard), AI-10 (cached raw mesh on domain change), AI-11 (qualified Qt enums), AI-12 (WCAG AA contrast), AI-13 (6-digit hex for PyVista), AI-14 (`pv.PolyData` or `ValueError`), AI-15 (math claim honesty).  Any violation defaults to MAJOR; AI-1 (alternative renderer) / AI-3 (offscreen MainWindow) / AI-4 (clip_box) violation is a BLOCKER.
2. **License compatibility** — PySide6 is LGPL; vendoring/importing GPL-3.0 libraries (e.g. `qfluentwidgets` core) into the binary distribution is problematic.  MIT / Apache-2.0 / BSD / LGPL all fine.  GPL/AGPL is a flag.
3. **macOS Qt+VTK GL offscreen segfault risk** — any candidate that proposes touching the test surface (AI-2) or off-screen render path (AI-3) must explicitly address this footgun.
4. **Test impact** — does the candidate require new tests?  Are they Qt-free (pure NumPy/PyVista/static math)?  Adding `pytest-qt` is an AI-2 BLOCKER unless the macOS issue is addressed.
5. **Performance impact** — does the candidate introduce >100ms latency on the render-pipeline critical path?  Marching cubes is already ~0.5s; new layers stack.  Memory-heavy operations (alternate fields, smoothing) need a budget.
6. **Re-entrancy / threading discipline** — does the candidate introduce a new `processEvents()` call?  A long-running task that should be off the main thread (QThread)?  CONTEXT.md §4.4 documents the only safe pattern.
7. **Cross-platform (macOS / Linux / Windows)** — the user develops on macOS Apple Silicon; the README claims Linux + Windows work but aren't routinely verified.  Heavy GL-dep candidates need a Linux/Windows fallback note.
8. **Effort honesty** — t-shirt size matches the single-developer / small-team cadence in CONTEXT.md §6's 5-phase pipeline (S=1-3d, M=4-10d, L=>10d).
9. **Anti-pattern check** — explicitly check candidate against `interaction-vocabulary.md` §8 (INT-NO-1 … INT-NO-13).
10. **Sequencing dependencies** — DAG between candidates (e.g., per-variety palette tokens depend on the `_qt/styles.py` refactor that introduces palette templates first).
11. **Distinctiveness / anti-template** — the anti-cookie-cutter axis (`frontend-design-language.md` §5 BAN-1..15 + §10 rubric).  Score the candidate's PROJECTED end-state against the 13 §10 tells, translated to this native Qt app (neon "sci-fi HUD" dark restyle = BAN-1/8; accent-icon-chip-on-every-button = BAN-3; equal-weight "ParaView property-wall" with no focal element = BAN-5/14; rainbow-colormap-as-decoration / diluted ⚠ semantic color = BAN-6/11; "Welcome" splash + quick-action tiles over the honest `— Select —` = BAN-10/13; parallax/scroll-zoom/WebGL spectacle on this S-2 surface = BAN-12; cloning the canon's own WEB house look or another repo's dashboard shell = BAN-15).  Apply the §11 four questions; a candidate that cannot answer Q4 ("recognizably NOT a template assembly?") is polish, not design (exempt only for pure a11y/token/mechanical fixes).  A **frameless synthesis** (Phase 2 did not open with an adopted frame) or a projected §10 score of **6+** is a **run-level BLOCKER**; **3–5** is **MAJOR**.  The challenger Reads `.claude/references/frontend-design-language.md` directly for this axis.

## After receiving the challenge

Parse the challenge to populate:

```bash
.claude/scripts/frontend-uplift/checkpoint.py <ID> --set challenge_path='".claude/notes/frontend-uplifts/<ID>/artifacts/challenge.md"'
.claude/scripts/frontend-uplift/checkpoint.py <ID> --set challenge_finding_counts='{"critical":N_BLOCKER,"high":N_MAJOR,"medium":N_MINOR,"low":N_CLEAN}'
.claude/scripts/frontend-uplift/checkpoint.py <ID> challenge-complete
```

## Anti-patterns

| Tempting belief | Reality |
|---|---|
| ">50% of candidates have MAJOR or BLOCKER objections — the synthesis was bad." | Possible.  More often, the challenger prompt is too aggressive or the synthesis under-considered the AI-2/AI-3 macOS Qt+VTK axis or the WCAG AA axis.  Re-read with that lens before re-running. |
| "Every candidate must have AT LEAST a MINOR objection." | NO.  A clean NONE is a credible verdict.  Calibrated runs see 30–60% NONE. |
| "BLOCKER findings should kill candidates outright." | Not always.  A BLOCKER + a credible redesign sketch leaves Phase 4 deciding whether the redesigned candidate is worth pursuing.  E.g., a candidate proposing Mayavi → redesign to "alternative VTK-only renderer evaluation if PyVista upstream breaks" is plausible. |
| "The challenger should propose its own candidates." | NO.  Phase 1's job.  Challenger evaluates the synthesis; it does not extend it. |
| "GPL-3.0 libraries are always BLOCKER." | License analysis is more nuanced — GPL-3.0 imports into the redistributable binary trigger AGPL/GPL contamination.  Study-only / pattern-mine use of GPL-3.0 is fine.  Flag MAJOR with the redistribution lens. |
