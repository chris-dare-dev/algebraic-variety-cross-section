# Phase 2 — Design (synthesis + pre-execution adversary)

**Goal:** convert audit findings into a concrete PLAN.md + symbol-map.json, then have the design-adversary critique it BEFORE execution (cheap insurance).

## Step 1 — Main session synthesizes PLAN.md

Read all three audit briefs end-to-end. Write `design/PLAN.md` with these MANDATORY sections (do not skip or merge sections — the design-adversary checks for them by name):

1. **Restructure goal** — one paragraph, traceable to a scout-D monolith finding or scout-B checklist failure.
2. **Tree diff** — old tree -> new tree, line-by-line.
3. **Symbol map** — per moved/split symbol: source `path:line` -> target `path:line`. Mirror to `symbol-map.json` for the rewrite-imports.py codemod.
4. **Delta size table** — per new/changed file: predicted LOC; per split: source LOC -> target1 + target2 + shim LOC.
5. **Shim plan** — per moved symbol: shim path, deprecation message, removal milestone.
6. **AI-invariant impact** — per AI-1..AI-15 the restructure touches: does the new layout still satisfy it?
7. **Cross-suite test gaps** — per scout-C §8: which categories this restructure introduces (seam tests, GUI integration, VTK pipeline, cyclic-import-under-entrypoint).
8. **Rollback plan** — Tier 1 (single revert) cmd, plus Tier 3 (partial) per-module template.

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

The adversary walks an 11-axis checklist:
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
