# Phase 2 — Design (synthesis + pre-execution adversary)

**Goal:** convert audit findings into a concrete PLAN.md + symbol-map.json, then have the design-adversary critique it BEFORE execution (cheap insurance).

## Step 1 — Main session synthesizes PLAN.md

Read all three audit briefs end-to-end. Write `design/PLAN.md` with these MANDATORY sections (do not skip or merge sections — the design-adversary checks for them by name):

1. **Restructure goal** — one paragraph, traceable to a scout-D monolith finding or scout-B checklist failure.  **The goal MUST be expressed in TSP terms** (see the TSP section in `.claude/commands/repository-architect.md` for the verbatim TSP-1..TSP-11 text).  The design-adversary REJECTS goals phrased as "split surfaces.py"; the acceptable form is "decompose surfaces.py into a 4-module subpackage rooted at `surfaces/` (under `varieties/`) to achieve TSP-4 single-responsibility per module and TSP-8 call-graph alignment".
2. **Tree diff** — old tree -> new tree, line-by-line.
2b. **Tree-structure compliance (TSP-1..TSP-11)** — a per-principle table covering EVERY one of TSP-1..TSP-11 (verbatim text lives in the slash command; cite by number here):
   - **TSP-1 root thinness (count + content)** — pre/post root `.py` count; for each retained root script, both its LOC and its TSP-11 grade (the count check is necessary; the TSP-11 content check is sufficient).  If a root file passes count but fails TSP-11, log it under TSP-11 (not TSP-1) for clarity.
   - **TSP-2 dependency order** — import-DAG depth pre/post; confirmation that `lint-imports` still reports 2 KEPT contracts post-restructure (or, if the restructure adds/changes a contract, the explicit pyproject.toml diff is shown here AND the user-gate noted).  List any retained sibling-cross-imports with justification (default: empty).
   - **TSP-3 cycles** — pre/post `pydeps --show-cycles` output (target: empty both sides).
   - **TSP-4 single-responsibility** — per file >500 LOC: list of responsibilities the file currently mixes and the proposed decomposition (or, if retained, the TSP-7 annotation with named follow-up restructure-id).
   - **TSP-5 responsibility-named modules** — list of new module names, each with a one-sentence responsibility claim.  Names from the banlist (`utils`, `helpers`, `common`, `misc`, `lib`, `core`, `manager`, `services`, `controllers`) MUST be replaced (auto-FAIL otherwise).
   - **TSP-6 script-to-subpackage migrations** — for each root script or split target: pre-state (path, LOC), post-state (subpackage tree), shim path.  Follow the AVC-precedent shape from r2/r3 retirements (see MOVES.md).  For `app.py`-shaped decompositions, the post-state ENTRY POINT must satisfy TSP-11 (pseudocode).
   - **TSP-7 retention justifications (time-bounded)** — by default empty.  Any retained root script or any retained >500-LOC module needs (a) a one-paragraph justification for why decomposing it within THIS restructure's scope is unsafe AND (b) a NAMED follow-up restructure-id (`restructure-<scope>-<YYYYqN>-r<N>`) that will address it.  Open-ended retentions (no named follow-up) are CRITICAL findings — the design-adversary rejects the plan.  For `app.py` specifically: deferral across r1, r2, r3 has expired; any new retention MUST either name a follow-up OR absorb at least one decomposition batch in this restructure (e.g. "batch 1: extract MainWindow + `_computing` guard into `_qt/main_window.py`; defer remaining business-logic extraction to <named follow-up>").
   - **TSP-8 call-stack alignment** — link to the `call-graph.json` produced by the Phase 1 auditor; show the alignment between current call edges and proposed import edges (one direction only — calls up, imports up).  Misalignments (decomposing along section comments rather than call clusters) MUST be flagged here, not buried.
   - **TSP-9 test mirroring (AVC carve-out)** — confirm new modules gain `tests/test_<module>.py` IN THE SAME BATCH (flat `tests/` layout retained per AI-2).  Any moved tests move WITH the source.
   - **TSP-10 tree-shape metrics** — `tree -L 3` output before vs after; depth; fan-out per subpackage; total subpackage count.  LOC delta is INFORMATIONAL ONLY — not the success metric.
   - **TSP-11 entry-point pseudocode** — for EACH root entry-point file (currently `app.py`): pre-state LOC, post-state LOC, function-call density % (≥70% required), business-logic inventory (formula evaluation, parsing, panel construction, etc. — must be empty post-restructure for a TSP-11 PASS), and the post-state body shown verbatim (it should fit in PLAN.md, that's the point).  If this restructure does not touch the entry point: state pre-state TSP-11 grade and reference the standing follow-up restructure-id for the entry-point decomposition.
3. **Symbol map** — per moved/split symbol: source `path:line` -> target `path:line`. Mirror to `symbol-map.json` for the rewrite-imports.py codemod.
4. **Delta size table** — per new/changed file: predicted LOC; per split: source LOC -> target1 + target2 + shim LOC.
5. **Shim plan** — per moved symbol: shim path, deprecation message, removal milestone.
6. **AI-invariant impact** — per AI-1..AI-15 the restructure touches: does the new layout still satisfy it?
7. **Cross-suite test gaps** — per scout-C §8: which categories this restructure introduces (seam tests, GUI integration, VTK pipeline, cyclic-import-under-entrypoint).
8. **Rollback plan** — Tier 1 (single revert) cmd, plus Tier 3 (partial) per-module template.

### Worked examples

For concrete TSP-6 decomposition shapes — including symbol-map.json structure, shim-plan format, AI-invariant impact analysis, and rollback templating — read a prior PLAN.md from `.claude/notes/repository-architect/`:

- `restructure-feature-subpackages-2026q2-r2/design/PLAN.md` — real r2 panel-subpackage extraction (panels.py + appearance_panel.py + view_panel.py + parameters_panel.py + parameter_grid_panel.py → `_qt/panels/` subpackage).
- `restructure-single-root-2026q2-r3/design/PLAN.md` — real r3 single-root invariant cleanup (Qt-layer shim retirement + surfaces.py retirement).

These are the canonical templates.  Synthesize PLAN.md by analogy from the closest-shape prior; do not invent a hypothetical from scratch.

Persist:
```bash
.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py {ID} \
    --set plan_path='".claude/notes/repository-architect/{ID}/design/PLAN.md"'
.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py {ID} \
    --set symbol_map_path='".claude/notes/repository-architect/{ID}/design/symbol-map.json"'
```

## Step 2 — Dispatch design-adversary

```
Agent: repository-architect-design-adversary
Inputs:
  {ID}
  {PLAN_PATH}         (from state.plan_path)
  {SYMBOL_MAP_PATH}   (from state.symbol_map_path)
  {ADVERSARY_PATH}    .claude/notes/repository-architect/{ID}/design/design-adversary-critique.md
```

The adversary walks a 13-axis checklist:
1. AI-1..AI-15 conflicts
2. AI-15 honesty applied to the design
3. Hallucinated patterns
4. Over-engineering relative to repo size
5. Shim-cycle correctness
6. Rollback feasibility
7. Anchor coverage
8. Test parity risk
9. Cross-suite test gaps
10. Sequencing safety
11. Effort honesty
12. Under-engineering relative to scout evidence (deferral scrutiny)
13. TSP-1..TSP-11 conformance — every principle has a row in PLAN.md section 2b; the adversary checks each row for evidence, citations to call-graph.json (TSP-8), AVC-specific carve-out restatements (TSP-9 flat-tests), named follow-up restructure-ids for any TSP-7 retentions (NO open-ended retentions accepted), and the TSP-11 pseudocode check on every root entry point (function-call density ≥70%, no business logic, post-state body shown verbatim in PLAN.md).  Missing or evidence-free TSP rows are CRITICAL.

Emits CRITICAL/HIGH/MEDIUM/LOW findings using `.claude/references/critique-format.md`.

## Step 3 — Record + advance

Parse severity counts from the critique file:
```bash
C=$(grep -c '^### CRITICAL' "<ADVERSARY_PATH>" || echo 0)
H=$(grep -c '^### HIGH'     "<ADVERSARY_PATH>" || echo 0)
M=$(grep -c '^### MEDIUM'   "<ADVERSARY_PATH>" || echo 0)
L=$(grep -c '^### LOW'      "<ADVERSARY_PATH>" || echo 0)
.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py {ID} \
    --set design_adversary_finding_counts="{\"critical\": $C, \"high\": $H, \"medium\": $M, \"low\": $L}"
.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py {ID} \
    --set design_adversary_path='".claude/notes/repository-architect/{ID}/design/design-adversary-critique.md"'
.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py {ID} design-complete
bash .claude/hooks/repository-architect/summarize-phase.sh {ID} design-complete
```

## Step 4 — GATE 2

Surface to user:
```
Design complete for {ID}.
PLAN.md: <path>
Design adversary: C<n> H<n> M<n> L<n> findings.
  -> All CRITICAL/HIGH findings MUST be addressed in PLAN.md before advancing.
  -> MEDIUM/LOW may be deferred.

Continue to Pre-flight? [y/n]
```

**If any CRITICAL/HIGH is unaddressed**, the orchestrator MUST loop back to Step 1 (revise PLAN.md, then re-dispatch the adversary) before surfacing the gate as approvable. Record loop iterations in dispatch.log.

If `state.stop_after_phase == "design"`, stop here.

## Anti-patterns to refuse

- Skipping the design-adversary "because the plan is obviously right." Plans look right until they're executed.
- Dispatching the design-adversary on a PLAN.md missing any of the 8 mandatory sections (adversary will gate-required).
- Advancing past GATE 2 with unaddressed CRITICAL/HIGH findings.
- Letting the design-adversary write the PLAN (separation of duties — adversary critiques only).
