# Phase 3 -- Adversary critique

**Goal:** stress-test the implementation from every angle that has
historically caught real bugs in this repo, and emit a canonical-format
critique the Rectifier can walk top-to-bottom.

This phase formalizes CONTEXT.md section 6 Phase 3 ("Adversarial Sonnet,
read-only, ~10 findings") with explicit state, a 10-axis institutional
checklist, and optional fan-out for UI / OSS critics.

## Primary path: dispatch `milestone-adversary-critic`

The repo has `.claude/agents/milestone-adversary-critic.md`.  Phase 3 of
this pipeline dispatches it on the implementation diff:

1. Determine the diff range from `state.implementation_commit_range` (set by Phase 2 checkpoint).
2. Dispatch the `milestone-adversary-critic` sub-agent by name; the agent body at `.claude/agents/milestone-adversary-critic.md` IS the prompt.  The orchestrator passes `{ID}`, `{COMMIT_RANGE}`, `{CRITIQUE_PATH}` as Task tool inputs.
3. The critic walks the 10-axis checklist from `adversary-critique-checklist.md` (in this directory) and writes its critique in the canonical format from `.claude/references/critique-format.md`.

The 10 institutional-memory axes for the algebraic-variety-cross-section
repo (full details in `adversary-critique-checklist.md`):

1. **App invariants (AI-1..AI-15)** -- the non-negotiable architectural locks
2. **Pipeline discipline (AI-6, AI-7)** -- implicit vs parametric path, Taubin only on implicit, Hanson normals
3. **VTK / PolyData ownership (AI-4, AI-5, AI-7, AI-10, AI-14)** -- clip_box ban, clip_scalar kwarg form, raw-mesh cache, generator contract
4. **Qt re-entrancy (AI-9)** -- `_computing` guard around `processEvents()`
5. **Color / contrast / token discipline (AI-11, AI-12, AI-13)** -- fully-qualified enums, WCAG AA, 6-digit hex
6. **Math claim honesty (AI-15)** -- >=2 sources, real-shadow / birational / parametric disclaimers
7. **Test coverage** -- new generator -> smoke test; new param spec -> tick<->value test; new clip path -> clip_domain test
8. **Off-screen render verification (AI-3)** -- `pv.OFF_SCREEN = True`, never `MainWindow()` under `QT_QPA_PLATFORM=offscreen`
9. **Documentation drift** -- new variety -> `CONTEXT.md` section 5 entry; new bug fix -> section 8; new explicit non-goal -> section 9; new generator -> README "Extending the app"
10. **Scope discipline** -- no defensive error handling for impossible cases, no narrative comments, no backwards-compat shims (single-person repo)

## Conditional fan-out: frontend (Qt panel) UI/UX critic

If the implementation diff touches the Qt panel files, dispatch a SECOND
parallel critic in the same assistant turn as the adversary-critique
dispatch.

```bash
# Detect Qt-panel changes (the AVC frontend is the Qt panels, not a web frontend).
BASE=$(.venv/Scripts/python.exe .claude/scripts/milestone-pipeline/checkpoint.py {ID} --get implementation_base)
git diff --name-only ${BASE}..HEAD | grep -E '^(appearance_panel|view_panel|parameters_panel|styles|app)\.py$' && echo frontend_changed=true || echo frontend_changed=false
```

If `frontend_changed=true`: dispatch the `milestone-frontend-ux-critic`
sub-agent.  It walks UX axes specific to a desktop scientific-viz Qt app:

- Visual hierarchy in dock layout (View / Parameters / Appearance)
- First-launch experience -- placeholder text, empty plotter, no auto-render
- Status-bar feedback during ~0.5 s mesh generation (busy cursor, warning surfacing per AI-14)
- Slider affordances (label, suffix, range, step granularity)
- Tooltip honesty (AI-15 disclaimers on new varieties / figures)
- Color contrast and accessibility (AI-12, AI-13)
- Keyboard shortcuts (`Ctrl+R`, `Ctrl+Shift+S`, `Ctrl+D`) and tab order
- Reset Camera / view-preset wiring (always followed by `render()` per CONTEXT.md section 8.1)

Frontend critic emits findings in the same canonical format.  The
orchestrator merges them into the adversary critique under a new
`## Frontend UI/UX findings` section, severity-graded.

## Optional fan-out: industry/OSS scout

If the user supplied `--oss-scout` OR the milestone implements a known
active-research area (math.AG construction recently published, novel
parametric rendering technique, mesh-quality algorithm), dispatch the
`milestone-oss-scout` critic.  Output goes into a `## Industry comparison`
appendix on the critique.  Findings are typically MEDIUM ("a newer SageMath
construction X exists that obsoletes our approach Y") -- never CRITICAL.

Default sources for this repo's domain area (math.AG / variety viz):
- arXiv math.AG (last 18 months)
- Imaginary.org gallery + tools (SURFER, Singular, Macaulay2 demos)
- SageMath / Macaulay2 examples in PyVista / VTK
- Classical references (Cossec-Dolgachev, Iskovskikh-Prokhorov, Hanson 1994)

## Dedup mechanics

When 2 or 3 critics fan out in parallel, the same `file:line` is sometimes
flagged by multiple critics with different framing.  The orchestrator runs:

```bash
.venv/Scripts/python.exe .claude/scripts/milestone-pipeline/dedupe-findings.py .claude/notes/milestones/{ID}/artifacts/adversary-critique.md
```

This:
- Parses findings (severity tag + `file:line` + short title).
- Groups findings within a 5-line window of the same file.
- Emits a "Cross-critic agreement" callout for any cluster of >=2 findings (these are the strongest signals).
- Rewrites the critique file in place with the cross-critic section
  inserted before "## Recommended rectification order".

## Hard rules for the critic phase

- **Don't paraphrase the diff** -- read every non-trivial hunk end-to-end.  Diff-skim critiques miss the bugs this skill exists to catch.
- **Don't manufacture findings to pad count.**  Zero CRITICALs and zero HIGHs is a credible result.  See `.claude/references/critique-format.md` for the honesty rubric.
- **Don't relax AI-1..AI-15.**  These are non-negotiable.  The critique surfaces violations; it does NOT argue for lifting locks.
- **Don't propose architectural rewrites.**  Critique scope is the diff.  "Rewrite the renderer in raw VTK" is not a finding (and would violate AI-1).
- **Always include "What was done well".**  5-10 bullets.  Calibrates the rest of the critique.  Empty section makes the critique read as adversarial-for-its-own-sake.
- **Cite >=2 sources** for any "this math is wrong" finding (AI-15 honesty mirror).

## Critique read budget

The critique is verbose by design (institutional memory matters).  For a
typical milestone the critique is 200-500 lines.  The Rectifier reads it
end-to-end in Phase 4.

## Checkpoint

```bash
.venv/Scripts/python.exe .claude/scripts/milestone-pipeline/checkpoint.py {ID} --set critics_run='["adversary","frontend-ux"]'
.venv/Scripts/python.exe .claude/scripts/milestone-pipeline/checkpoint.py {ID} critique-complete
```

State now records `critique_path` and the dispatched critic count.  Phase 4
reads from this.
