# Adversary critique -- AVC milestone diff

Produce a fair-but-harsh critique of a milestone's implementation diff in
the canonical AVC adversary format (CRITICAL/HIGH/MEDIUM/LOW + `file:line`).
Mirrors the pattern documented in CONTEXT.md section 6 phase 3 and used
across the three variety passes (K3, Enriques, Calabi-Yau) plus the
panel-refresh epic.

## When to invoke

Invoke from `/milestone-pipeline` Phase 3 -- always.  The
milestone-adversary-critic sub-agent fires on every milestone regardless
of size; the critique is the institutional-memory artifact that lets the
next milestone start with the prior pass's lessons.

Specific trigger phrases handled by `/milestone-pipeline`:

- `/milestone-pipeline <id>` -> Phase 3 invokes this critique automatically
- `/milestone-pipeline <id> -- resume from current state` -> if state is
  `implement-complete`, the resume re-enters Phase 3

Do NOT invoke standalone for: trivial typo / lint / docstring tweaks; pure
formatting commits (`ruff format`); doc-only changes whose scope is prose
editing only; reverts.

## What this skill produces

A single markdown file in the canonical AVC adversary format, written to:
`.claude/notes/milestones/{ID}/artifacts/adversary-critique.md`.

Full structure: `adversary-critique-template.md` (this directory).  Fixed
checklist of axes the model walks before writing findings:
`adversary-critique-checklist.md` (this directory).

The output always opens with an executive summary (3-5 sentences naming the
highest-severity issues by short title) and closes with a recommended
rectification order.  Every finding cites `file:line`, gives a concrete
suggested fix, and -- when relevant -- names a regression-guard test the
rectifier should add.

## The fixed checklist of axes

Every critique walks these axes BEFORE looking at feature-specific issues.
Each has a dedicated section in `adversary-critique-checklist.md` with
concrete checks.  The axes encode this repo's institutional risk memory --
the categories where prior bug fixes (CONTEXT.md section 8) landed.

| Axis | Severity it usually maps to | Anchor bug |
|---|---|---|
| App invariants AI-1..AI-15 | HIGH or CRITICAL | AI-1 (LGPL stack), AI-4 (clip_box ban), AI-9 (re-entrancy), AI-15 (math honesty) |
| Pipeline discipline (AI-6, AI-7) | HIGH | Mixing Taubin onto parametric / wrong normal mode on Hanson |
| VTK / PolyData ownership (AI-4, AI-5, AI-10, AI-14) | HIGH or MEDIUM | clip_box invert reversed; clip_scalar without `scalars=`; cached `_raw_mesh` regressions |
| Qt re-entrancy (AI-9) | HIGH | `_render_current` re-entry corrupting `_raw_mesh` |
| Color / contrast / token discipline (AI-11, AI-12, AI-13) | MEDIUM or HIGH | `#888` short-hex into PyVista; `Qt.AlignLeft` deprecation; muted-color WCAG fail |
| Math claim honesty (AI-15) | HIGH | Barth icosahedral mis-attribution; Hanson `n²` vs `n_2` |
| Test coverage gap | MEDIUM | New generator without `tests/test_mesh_generators.py` smoke entry |
| Off-screen render verification (AI-3) | HIGH | `MainWindow()` under `QT_QPA_PLATFORM=offscreen` segfault |
| Documentation drift | LOW | New variety without CONTEXT.md section 5 entry; new non-goal not in section 9 |
| Scope discipline | LOW or MEDIUM | Defensive `try/except` for impossible cases; narrative comments; backwards-compat shims |

The first ten checks always run.  Feature-specific issues come AFTER.  The
reason: the same axes have caught real bugs documented in CONTEXT.md
section 8, and an adversary that skips them is doing nothing more than a
fresh code review.  The whole point of this skill is institutional memory.

## Severity rubric

> **Canonical format and severity table**: see
> `.claude/references/critique-format.md`.  That file is the single source
> of truth for: (a) CRITICAL/HIGH/MEDIUM/LOW bar definitions with anchor
> calibration, (b) the required section order (Executive summary ->
> CRITICAL -> HIGH -> MEDIUM -> LOW -> What was done well -> Rectification
> order), and (c) the per-finding template format.

Summary of calibration principle: Inflated severity = noise; deflated
severity ships bugs.  A critique with zero CRITICALs and zero HIGHs is a
credible result.  Five CRITICALs and ten HIGHs is usually a calibration
failure -- re-audit each finding against the rubric before writing the
output.

## How to invoke

This skill fires automatically as Phase 3 of `/milestone-pipeline`.  No
direct user invocation.  The orchestrator dispatches the
`milestone-adversary-critic` sub-agent with:

1. **The target.**  A commit range `{base}..HEAD` from `state.implementation_commit_range`.
2. **The milestone id** (so the output filename is correct).
3. **The output path** `.claude/notes/milestones/{ID}/artifacts/adversary-critique.md` substituted as `{CRITIQUE_PATH}` in the prompt.

The critic reads `git diff <range>` end-to-end and walks the 10 axes
before writing findings.  If the target is empty (zero diff lines), the
critic exits with a single-line note rather than manufacturing findings.

## Output destination

- `.claude/notes/milestones/{ID}/artifacts/adversary-critique.md`.
- Executive summary at the top; rectification order at the bottom.
- Findings grouped by severity, not by file.
- Append-only after creation -- Phase 4 appends a rectification-status footer; nothing else mutates it.

## Don'ts

- **Don't manufacture issues to pad the count.**  Zero findings is a
  credible result.  Fabricating two more HIGHs erodes signal.
- **Don't gold-plate.**  "Add property-based tests for every function" is
  not a finding; "Add a regression test for the `mu_sq <= 1/3` Kummer
  boundary that the existing test suite covers at 0.4 but not at exactly
  1/3" is.
- **Don't relax AI-1..AI-15.**  These are non-negotiable.  The critique
  surfaces violations; it does not argue for lifting locks.  The scope is
  the diff, not the architectural lock list.
- **Don't lift CONTEXT.md section 9 non-goals** through a finding.  "The
  app should have QSettings persistence" is a non-goal -- noting it as a
  finding without escalating to a separate milestone scope discussion is
  out-of-scope.
- **Don't skip "What was done well".**  This section calibrates the rest
  of the critique.  Real, specific praise required ("Reused
  `_marching_cubes_to_polydata` helper rather than reimplementing the
  zero-crossing check" -- panel-refresh anchor).  An empty section makes
  the critique read as adversarial-for-its-own-sake.
- **Don't write anything before reading the target end-to-end.**  The
  Hanson `consistent_normals` regression (CONTEXT.md section 8.7) is
  invisible without reading the actual `_concat_polydata` call site and
  tracing what `compute_normals(...)` does on a 25-component mesh.
  Diff-skim critiques miss exactly the bugs this skill exists to catch.

## References

- **Format & structure**: `adversary-critique-template.md` (this directory) -- per-invocation template.  For the canonical section structure and severity rubric, see `.claude/references/critique-format.md`.
- **Per-axis prompts**: `adversary-critique-checklist.md` (this directory).  Walk BEFORE writing findings.
- **App invariants AI-1..AI-15**: `.claude/references/app-invariants.md` (full list with implications and Challenger usage).
- **CONTEXT.md sections 4, 5, 8, 9, 12**: architecture, math conventions, bugs caught, explicit non-goals, git workflow.
- **Critique format reference**: `.claude/references/critique-format.md` -- canonical severity language used by `/capability-scout`, `/frontend-uplift`, and this skill.
