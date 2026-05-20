# Phase 1 — REFINE

**Goal:** turn a fuzzy brief into a sharp, evidence-backed problem statement that the rest of the pipeline can decompose without guessing.

## Step-by-step

### 1. How-Might-We reframe

Take the brief (verbatim user text or 2-4-sentence conversation summary) and restate it as **one** crisp HMW problem statement:

> "How might we **{do something concrete}** so that **{specific user/system/team}** can **{achieve specific outcome}**?"

Rules:
- The middle clause must name a real beneficiary (user persona, agent, downstream system) — not a vague "the platform".  For this repo, common beneficiaries are: a researcher driving the GUI to explore a variety family; a future Claude session re-entering the codebase via `CONTEXT.md`; the off-screen render pipeline (`pv.OFF_SCREEN`); the test suite.
- The outcome clause must be observable — something a metric, a test, or a user can confirm.
- If the brief permits two or more credible HMW reframings, **STOP and surface both with one-paragraph tradeoffs.**  This is the Phase 1 gate condition.

### 2. Sharpening questions (3-5)

Answer all of these from in-context evidence (the conversation, the codebase, `.claude/notes/capability-scouts/<id>/artifacts/`, `.claude/notes/frontend-uplifts/<id>/artifacts/`, `CONTEXT.md`).  If the in-context answer is "I don't know", flag it as a `[MUST]` assumption to validate (see step 3) — do NOT ask the user yet.

1. **Who is this for, specifically?** A researcher persona, the future-Claude reader of CONTEXT.md, the off-screen render pipeline, a CI smoke harness.  Name them.
2. **What does success look like?** The single observable thing that changes when this lands.  For AVC: a new tooltip that passes WCAG AA contrast; a new variety family rendering without a sawtooth; the dark-mode background flash on launch eliminated.
3. **What are the real constraints?** AI-1 .. AI-15 invariants; the Qt+VTK offscreen segfault constraint; macOS Apple Silicon as primary; the single-developer "commit to main" cadence; the test-suite-runtime budget (~4s for 120 tests).  Cite specific AI-N numbers and CONTEXT.md sections.
4. **What's been tried before?** Grep `.claude/notes/capability-scouts/`, `.claude/notes/frontend-uplifts/`, and CONTEXT.md section 8 (bugs caught) / section 9 (things explicitly NOT done) for prior attempts at the same shape of problem.  List with file:line citations.
5. **Why now?** What changed that makes this the right moment? (A capability-scout report just landed; a new SOTA in scientific-viz desktop apps; a recent bug-fix unblocked an epic; an adversarial review surfaced a CRITICAL.)

### 3. Assumption tiering

Every claim about the world that is not yet evidence-backed gets one of three tags:

| Tag | Meaning | Action |
|---|---|---|
| `[MUST]` | Validating-this-is-wrong invalidates the whole roadmap. | Spike in Phase 3 BEFORE any value epic depends on it.  <=3-day spike. |
| `[SHOULD]` | Validating-this-is-wrong forces a redesign of one epic but not the whole. | Design a fallback at decomposition time.  Don't spike unless cheap. |
| `[MIGHT]` | Validating-this-is-wrong is a minor tweak. | Defer.  Note in the "open questions" section. |

Tag every assumption explicitly.  An untagged assumption is the same as a `[MUST]` you forgot to validate — i.e. the most dangerous kind.

### 4. Objective + Key Results + Won't list

**Objective** (one sentence, outcome-shaped, single-developer-appropriate):

> "By {date}, {observable outcome that didn't exist before}."

Skip OKR ritual scoring — anti-pattern for single-developer / few-developer projects.  The objective is *one outcome statement* for this roadmap.

**Key Results** (2-4, leading-indicator shaped):
- Each one is a metric, a test outcome, or a user-observable change.
- No KR is "ship X" — that's an output, not a result.
- If you can't write a KR without phrasing it as "ship feature Y", the outcome isn't real yet — go back to step 1.

For AVC, good KR shapes include:
- "Off-screen render of `<variety>/<subtype>` produces no visible sawtooth in `/tmp/check.png`" (binary, render-checkable).
- "Text contrast ratio on `<element>` >= 4.5:1 against its background" (WCAG-checkable).
- "120 tests still pass; N new tests added under `tests/test_<area>.py`" (test-suite-checkable).
- "Dropdown subtype `<key>` exists in `VARIETIES` and its `Surface.label` appears in the status bar after selection" (UI-observable).

**Won't list** (>=3 items, explicit non-goals):
- The 3 most tempting things this roadmap is NOT doing, named verbatim.
- This is the load-bearing scope-discipline artifact.  Empty Won't list = scope creep waiting to happen.
- For AVC, common Won't items: "no Qt unit tests via pytest-qt" (AI-2); "no Mayavi as alternative renderer" (AI-1); "no auto-rendering on first launch" (CONTEXT.md section 9); "no QSettings cross-launch state persistence" (CONTEXT.md section 9 documents this was explicitly deferred).

## Output template (appended to roadmap.md)

```markdown
<!-- ROADMAP:section:refine -->
## 1. Brief

{verbatim brief or 2-4-sentence conversation summary}

## 2. How-Might-We

How might we **{action}** so that **{beneficiary}** can **{observable outcome}**?

## 3. Sharpening answers

- **Who:** {persona / future-Claude reader / off-screen pipeline / etc.}
- **Success looks like:** {single observable change}
- **Constraints:** {bulleted list with AI-N + CONTEXT.md section citations}
- **Prior art:** {bulleted list with file:line citations to .claude/notes/ or CONTEXT.md sections}
- **Why now:** {triggering change}

## 4. Assumptions

- `[MUST]` {assumption} — *spike in Phase 3*
- `[SHOULD]` {assumption} — *fallback: {brief description}*
- `[MIGHT]` {assumption} — *defer*
- ...

## 5. Objective and Key Results

**Objective:** By {date}, {outcome}.

**Key Results:**
1. {leading-indicator metric or test outcome}
2. {leading-indicator metric or test outcome}
3. {leading-indicator metric or test outcome}

**Won't:**
- {explicit non-goal #1}
- {explicit non-goal #2}
- {explicit non-goal #3}
```

## Auto-advance vs gate (decision table)

| Condition | Action |
|---|---|
| One credible HMW + every sharpening Q has evidence + every assumption is tier-tagged + Won't list >=3 | **Auto-advance** to Phase 2 |
| >=2 credible HMW reframings — different beneficiaries OR different outcomes | **GATE.**  Surface both with tradeoffs.  Wait for `[a]` or `[b]`. |
| Sharpening Q has no in-context answer AND impacts decomposition | **GATE.**  Ask the user the single most-load-bearing question. |
| Won't list <3 items | **NOT a gate** — push the model to add more.  Empty Won't = lazy scoping. |

## Hard rules

- **No code in Phase 1.**  Output is a problem statement, not a design.  Code-shaped answers in this phase pre-commit decomposition before Phase 2 has run.
- **No paraphrasing of the user's brief.**  Quote it verbatim in section 1 — paraphrasing biases every downstream decision.
- **Every constraint citation has a specific reference.**  "AI-9" alone is hand-wavy; "AI-9 (re-entrancy guard on processEvents) — `.claude/references/app-invariants.md`" is auditable.  "CONTEXT.md section 8.5" is auditable; "the bugs section" is not.
- **Every prior-art citation has a file path.**  Grep first, ask never.
- **Tagged assumptions only.**  Untagged assumption = forgotten `[MUST]`.
