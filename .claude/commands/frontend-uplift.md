# /frontend-uplift

Run the canonical 4-phase algebraic-variety-cross-section frontend-modernization pipeline:
**Discover (4 parallel agents — incl. off-screen surface renders) → Synthesize → Challenge → Prioritize**

Usage:
```
/frontend-uplift                                                  # ask for uplift id
/frontend-uplift <id>
/frontend-uplift <id> --brief "verbatim user scope"
/frontend-uplift <id> --surfaces "K3 surface/Fermat quartic,..."  # override the default 5-surface set
/frontend-uplift <id> --lean                                      # 2 agents only (visual-scout + current-state-critic)
/frontend-uplift <id> -- resume from current state
```

`<id>` is a free-form slug.  Convention: date-tagged scope, e.g. `2026q2-panel-refresh` or `calabi-yau-hero-experience-v1`.  If no id is given, STOP and ask: "What uplift id should I use?"

The pipeline answers: **"Where can the Algebraic Variety Viewer's GUI / panel layout / styles / interaction surface become more polished and modern — measured against 2026 SOTA scientific-viz desktop apps (ParaView, 3D Slicer, Surfer, GeoGebra) and the math-research-tool audience — without violating app invariants AI-1..AI-15 (PySide6+PyVista stack, Qt-free tests, off-screen pipeline, clip_scalar, Hanson normals, re-entrancy guard, qualified Qt enums, WCAG AA, 6-digit hex, math claim honesty) or breaking the macOS Qt+VTK offscreen-GL constraint?"**  It does NOT produce code; it produces a ranked candidate report ready to feed CONTEXT.md §6's 5-phase implementation pipeline.

---

## Step 0 — Initialize state

```bash
.claude/scripts/frontend-uplift/init-uplift.sh <ID> [--brief "<verbatim user brief>"] [--surfaces "<csv>"]
mkdir -p .claude/agent-memory/frontend-uplift-visual-scout \
         .claude/agent-memory/frontend-uplift-library-scout \
         .claude/agent-memory/frontend-uplift-inspiration-scout \
         .claude/agent-memory/frontend-uplift-current-state-critic \
         .claude/agent-memory/frontend-uplift-challenger
```

- If the state file already exists, the script prints `state already exists (phase=X) — resuming`.
- If resuming: run `status.sh` first, then skip to the appropriate phase below.
- The `mkdir -p` ensures per-agent memory dirs exist; safe to re-run.

```bash
.claude/scripts/frontend-uplift/status.sh <ID>
```

Read `.claude/references/frontend-uplift/state-schema.md` only if you need to inspect or write a field that isn't covered by the scripts.

---

## Step 1 — Discover (parallel, 4 agents in ONE turn)

Read `.claude/references/frontend-uplift/phase-discover.md` once at phase start.

### 1a — Preflight: ensure the off-screen render pipelines are operational

The visual scout drives TWO off-screen pipelines: (i) `pv.OFF_SCREEN = True` renders of representative surfaces, and (ii) `QT_QPA_PLATFORM=offscreen` + `QWidget.grab()` captures of panel chrome (`AppearancePanel`, `ViewPanel`, `ParametersPanel` — these are pure-Qt and host no `QtInteractor`, so they're safe under offscreen; the AI-3 ban is specifically on `MainWindow` under offscreen).  Before dispatching, run:

```bash
.claude/scripts/frontend-uplift/ensure-render-up.sh
```

The probe exercises both pipelines (cheapest K3 surface + an `AppearancePanel.grab()`).  If exit status != 0, surface the recovery hint and HALT before dispatching any agent.  Re-invoke `/frontend-uplift <ID>` after fixing — `init-uplift.sh` is idempotent and `status.sh` will show `phase: init` ready to advance.

### 1a' — Capture panel chrome (always)

The visual scout needs pixel-truth on the Qt panel chrome (slider rails, group-box headers, button states, QSS-rendered colors), not just the 3D surface.  Run the panel-chrome capture into the same render directory as the surface renders so the scout reads them together:

```bash
RENDER_DIR=".claude/notes/frontend-uplifts/<ID>/renders"
mkdir -p "$RENDER_DIR/panels"
.venv/bin/python .claude/scripts/frontend-uplift/render-panel-chrome.py "$RENDER_DIR/panels"
```

This emits 12 PNGs today (3 panels × empty/populated × 1×/2×, LIGHT theme only).  When `styles.PALETTE_DARK` lands (UPL-4), the script auto-emits dark variants too — no slash-command edit required.  Cost: ~3 seconds wall-clock.  Safe under offscreen by AI-3's clarifying paragraph (pure-Qt panels host no VTK GL context).

### 1b — Set mode + dispatch

Set the discover mode (default standard):
```bash
.claude/scripts/frontend-uplift/checkpoint.py <ID> --set discover_mode='"standard"'
```

Then dispatch all 4 agents in **one assistant turn** containing 4 `Agent` tool blocks.  Each uses `subagent_type: general-purpose`, sonnet, `isolation: worktree`.  The canonical prompts live in `.claude/references/frontend-uplift/agent-prompts.md` — copy verbatim and substitute `{ID}`, `{UPLIFT_BRIEF}`, `{BRIEF_PATH}`, `{RENDER_DIR}`, `{SURFACES}`.

| Agent name (state field) | Brief path |
|---|---|
| `visual-scout` | `.claude/notes/frontend-uplifts/<ID>/discover/visual-scout-brief.md` |
| `library-scout` | `.claude/notes/frontend-uplifts/<ID>/discover/library-scout-brief.md` |
| `inspiration-scout` | `.claude/notes/frontend-uplifts/<ID>/discover/inspiration-scout-brief.md` |
| `current-state-critic` | `.claude/notes/frontend-uplifts/<ID>/discover/current-state-critic-brief.md` |

Record each dispatch and advance state:
```bash
for agent in visual-scout library-scout inspiration-scout current-state-critic; do
  .claude/scripts/frontend-uplift/checkpoint.py <ID> --append agents_dispatched="\"$agent\""
done
.claude/scripts/frontend-uplift/checkpoint.py <ID> discover-running
```

In **lean** mode, dispatch only `visual-scout` + `current-state-critic`.

### 1c — Return briefs

As each agent returns:
```bash
.claude/scripts/frontend-uplift/checkpoint.py <ID> --append agents_returned='"<agent-name>"'
.claude/scripts/frontend-uplift/checkpoint.py <ID> --append discover_briefs='"<brief-path>"'
```

When all dispatched agents have returned:
```bash
.claude/scripts/frontend-uplift/checkpoint.py <ID> discover-complete
```

---

## Step 2 — Synthesize (main session)

Read `.claude/references/frontend-uplift/phase-synthesize.md` once at phase start.

```bash
.claude/scripts/frontend-uplift/checkpoint.py <ID> synthesize-running
```

Read EVERY brief end-to-end AND look at the off-screen renders under `.claude/notes/frontend-uplifts/<ID>/renders/`.  Build the unified modernization-candidate catalog at:
```
.claude/notes/frontend-uplifts/<ID>/artifacts/synthesis.md
```

Use the fixed candidate-entry shape and 11-category taxonomy from `phase-synthesize.md`.  Deduplicate across briefs.  Surface FOUNDATIONAL candidates first (the ones other candidates depend on).  Cross-link interaction primitives `[INT-N]`.

```bash
.claude/scripts/frontend-uplift/checkpoint.py <ID> --set synthesis_path='".claude/notes/frontend-uplifts/<ID>/artifacts/synthesis.md"'
.claude/scripts/frontend-uplift/checkpoint.py <ID> --set candidate_count=<N>
.claude/scripts/frontend-uplift/checkpoint.py <ID> synthesize-complete
```

---

## Step 3 — Challenge (single sub-agent)

Read `.claude/references/frontend-uplift/phase-challenge.md` once at phase start.

```bash
.claude/scripts/frontend-uplift/checkpoint.py <ID> challenge-running
```

Single `Agent` call with `subagent_type: general-purpose`, sonnet, `isolation: worktree`.  Use the canonical Challenger prompt from `agent-prompts.md` verbatim.  Substitute `{ID}`, `{SYNTHESIS_PATH}`, `{CHALLENGE_PATH}`.

The challenger writes to:
```
.claude/notes/frontend-uplifts/<ID>/artifacts/challenge.md
```

Record:
```bash
.claude/scripts/frontend-uplift/checkpoint.py <ID> --set challenge_path='".claude/notes/frontend-uplifts/<ID>/artifacts/challenge.md"'
.claude/scripts/frontend-uplift/checkpoint.py <ID> --set challenge_finding_counts='{"critical":N_BLOCKER,"high":N_MAJOR,"medium":N_MINOR,"low":N_CLEAN}'
.claude/scripts/frontend-uplift/checkpoint.py <ID> challenge-complete
```

(BLOCKER → critical, MAJOR → high, MINOR → medium, NONE → low.)

---

## Step 4 — Prioritize (main session)

Read `.claude/references/frontend-uplift/phase-prioritize.md` once at phase start.

```bash
.claude/scripts/frontend-uplift/checkpoint.py <ID> prioritize-running
```

Run in the **main session** (NOT a sub-agent) — the user reviews this report directly.

Read synthesis + challenge end-to-end.  Score every candidate via **RICE-light** (R 1/3/10 × Visual-Impact 0.5/1/3 × Triangulation-Confidence 0.3-1.0 / Effort-by-tshirt 0.25-8).  Apply challenger penalties (drop on un-redesigned BLOCKER; halve on redesigned BLOCKER; -25% on MAJOR; no adjustment on MINOR / NONE) AND a **foundational-candidate bonus** (+30% on candidates synthesis flagged as foundational).  Write:
```
.claude/notes/frontend-uplifts/<ID>/artifacts/final-report.md
```

with these sections in order:

1. Executive summary (top-3 by adjusted RICE, theme, caveat)
2. Quick-glance ranking table
3. Foundational candidates (FIRST in detail; they unblock the rest)
4. Top-10 in detail (synthesis entry + challenger objections + RICE breakdown + DAG note)
5. Recommended next steps (foundational first; then 1–2 ready for CONTEXT.md §6's 5-phase implementation pipeline; spike candidates; parking lot)
6. Visual evidence index (renders × candidates)
7. Honest limitations
8. Cross-reference index

**Always OFFER but NEVER auto-invoke any implementation pipeline.**  Include the offer footer when candidates clear the documented thresholds; the user picks the next step.

Record:
```bash
.claude/scripts/frontend-uplift/checkpoint.py <ID> --set final_report_path='".claude/notes/frontend-uplifts/<ID>/artifacts/final-report.md"'
.claude/scripts/frontend-uplift/checkpoint.py <ID> --set ranked_candidates='[{"id":"UPL-1","title":"Adopt qtawesome icons","rice":13.0,"rank":1},...]'
.claude/scripts/frontend-uplift/checkpoint.py <ID> complete
```

Print a 5-line final summary: uplift id, total candidates, top-3 by adjusted RICE, BLOCKER count, recommended next step.

---

## State machine

```
init → discover-running → discover-complete
     → synthesize-running → synthesize-complete
     → challenge-running → challenge-complete
     → prioritize-running → complete
```

`status.sh` prints elapsed time per phase, which agents are pending, and the count of renders captured.

---

## Common rationalizations (anti-pattern guard)

| Tempting belief | Reality |
|---|---|
| "Skip the render preflight check — the agents can figure it out." | NO.  The visual scout can't run without an operational `pv.OFF_SCREEN` pipeline.  Preflight is load-bearing. |
| "Skip the visual scout — the other 3 agents cover the gaps." | NO.  Without rendered evidence, every claim about visual state is unverifiable.  The visual scout is the EVIDENCE-PRODUCING agent; the rest are interpreters. |
| "Fire agents one at a time to read each brief as it lands." | Sequential dispatch doubles wall-clock and kills diversity.  ONE turn, 4 tool blocks. |
| "Synthesize from TL;DRs only." | Triangulation lives in matching specific claims across briefs.  Read every brief end-to-end + look at renders. |
| "Skip the challenger — the synthesis is good enough." | Synthesis biases toward "more polish".  Without an adversary, Phase 4 ranks aspirational candidates blind to AI-2/AI-3 macOS-segfault, LGPL-redistribution, and accessibility cost. |
| "Auto-invoke an implementation Agent on the top candidate." | NEVER.  Offer-and-wait. |
| "Inflate severity to surface more findings." | The challenger's NONE is a credible result.  Aim 30–60% NONE; padding objections erodes signal. |
| "Propose Mayavi for an alternative renderer." | AI-1 violation.  Mayavi is broken on Apple Silicon as of 2025.  Mayavi/matplotlib-3D/Plotly/k3d/raw-VTK are anti-pattern. |
| "Propose `clip_box` for the cube domain clip — it should work now." | AI-4 violation.  `clip_box(invert=...)` semantics on PolyData are reversed/unreliable (CONTEXT.md §8.2).  Stick with `clip_scalar`. |
| "Use `Qt.AlignLeft` shorthand for new code." | AI-11 drift.  Use `Qt.AlignmentFlag.AlignLeft` consistently. |

---

## Don'ts

- **Don't run Phase 4 as a sub-agent.**  It needs the user's review surface.
- **Don't let the synthesizer write the challenge.**  Distinct roles.
- **Don't auto-invoke any implementation pipeline.**  Offer-and-wait.
- **Don't skip the preflight `ensure-render-up.sh` check.**  The whole Phase 1 hinges on a reachable off-screen render pipeline.
- **Don't manufacture candidates.**  Every catalog entry traces to ≥1 discover brief.
- **Don't bypass `scripts/init-uplift.sh`.**  State directory naming is load-bearing.
- **Don't commit uplift artifacts unless asked.**  Uplift notes live under `.claude/notes/frontend-uplifts/` and are local.

---

## Sub-agent memory

All `frontend-uplift-*` agents have `memory: project` in their frontmatter.  Their memory accumulates under `.claude/agent-memory/<agent-name>/` across uplift runs.  Do NOT clear or overwrite these directories — they carry institutional memory across runs (which inspiration apps have richer docs, which render edge cases need workarounds, recurring synthesis blind spots, etc.).

---

## References

Phase references (`phase-discover.md`, `phase-synthesize.md`, `phase-challenge.md`, `phase-prioritize.md`), the agent-prompts source (`agent-prompts.md`), and the curated knowledge files (`source-registry.md`, `interaction-vocabulary.md`, `design-system.md`) are all surfaced INLINE at their phase entries — no need to list them here.  Cross-cutting references the phase bodies don't already link:

- `.claude/references/frontend-uplift/state-schema.md` — `state.json` field reference
- `.claude/references/app-invariants.md` — AI-1 .. AI-15 architectural locks (Challenger checklist axis #1)
- `.claude/references/critique-format.md` — canonical severity rubric
- `CONTEXT.md` §6 — the 5-phase implementation pipeline that consumes the final report
- `CONTEXT.md` §3 + §8 — stack rationale + bugs caught (load-bearing repo quirks the challenger must respect)
