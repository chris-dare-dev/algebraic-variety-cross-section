# Epic: {{EPIC_TITLE}}

> **Epic ID:** `{{EPIC_ID}}` · **Roadmap:** [{{SLUG}}]({{ROADMAP_PATH}})

## Goal

{{EPIC_GOAL}}

## Slice

{{EPIC_SLICE}}

## Tag

{{VALUE_OR_ENABLER}}

## INVEST check

{{INVEST_RESULT}}

## T-shirt size

{{TSHIRT}}

## Predecessors

{{PREDECESSORS}}

## Acceptance signals

{{ACCEPTANCE_SIGNALS}}

## Specialist hints

{{SPECIALIST_HINTS}}

## Relevant app invariants

This epic must respect AI-1 .. AI-15 (`.claude/references/app-invariants.md`).  The specialist hints above name the invariants most relevant to this slice; the full list is the floor.

## Stories

*Stories are tracked as separate child issues with label `epic:{{EPIC_ID}}`.  Run `gh issue list --label 'epic:{{EPIC_ID}}'` to list them.*

{{STORY_LIST}}

## Execution

This epic is consumed by **CONTEXT.md section 6's 5-phase implementation pipeline** (math research / code archeology → implementation + off-screen render verify → adversarial review → remediation → UI/UX pass).  Per-epic artifacts (research briefs, adversarial critique, remediation notes, UI/UX critique) land under `.claude/notes/` and are committed directly to `main` per the single-developer cadence in CONTEXT.md section 12.

---

*Created by `/roadmap`.  Source: [{{ROADMAP_PATH}}]({{ROADMAP_PATH}}).*
