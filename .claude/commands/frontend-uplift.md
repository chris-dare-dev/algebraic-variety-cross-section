# /frontend-uplift

Run the canonical 4-phase algebraic-variety-cross-section frontend-modernization pipeline:
**Discover (parallel agents — incl. off-screen surface renders + an ART-DIRECTION frame) → Synthesize → Challenge → Prioritize**

Usage:
```
/frontend-uplift                                                  # ask for uplift id
/frontend-uplift <id>
/frontend-uplift <id> --brief "verbatim user scope"
/frontend-uplift <id> --surfaces "K3 surface/Fermat quartic,..."  # override the default 5-surface render set
/frontend-uplift <id> --mode lean|standard|deep|experiential      # scout fan-out size (default standard)
/frontend-uplift <id> --surface tool|mixed|experiential|auto      # surface class (default tool — see below)
/frontend-uplift <id> --lean                                      # alias for --mode lean
/frontend-uplift <id> --workflow                                  # optional Gen-2 background orchestrator (explicit opt-in only)
/frontend-uplift <id> -- resume from current state
```

`<id>` is a free-form slug.  Convention: date-tagged scope, e.g. `2026q2-panel-refresh` or `calabi-yau-hero-experience-v1`.  If no id is given, STOP and ask: "What uplift id should I use?"

The pipeline answers: **"Where can the Algebraic Variety Viewer's GUI / panel layout / styles / interaction surface become more polished and modern — with a real ART-DIRECTION THESIS (not cookie-cutter shadcn-style polish, and not a neon sci-fi-HUD restyle), measured against 2026 SOTA scientific-viz desktop apps (ParaView, 3D Slicer, Surfer, GeoGebra) and the math-research-tool audience — without violating app invariants AI-1..AI-15 (PySide6+PyVista stack, Qt-free tests, off-screen pipeline, clip_scalar, Hanson normals, `_computing` re-entrancy guard, qualified Qt enums, WCAG AA, 6-digit hex, math-claim honesty) or breaking the macOS Qt+VTK offscreen-GL constraint?"**  It does NOT produce code; it produces a ranked candidate report ready to feed CONTEXT.md §6's implementation pipeline.

---

## Standing defaults (read before Step 0)

**Art-direction thesis — the anti-cookie-cutter mandate.**  Every run establishes a **design frame BEFORE candidates are ranked**.  The `frontend-uplift-art-direction-scout` is dispatched in **EVERY mode (lean included)**: it reads the taste canon (`.claude/references/frontend-design-language.md`) AND this repo's house-thesis overlay (`.claude/references/frontend-uplift/design-system.md` §9), scores the current UI on the §10 cookie-cutter rubric, and produces a **visual thesis + 3 divergent directions + the active BAN-1..15 list + a surface map**.  Synthesis (Phase 2) OPENS with that frame; the challenger's Axis 11 blocks frameless/template output; the prioritizer ranks in PORTFOLIO LANES (Phase 4).  Polish without direction is the failure this pipeline exists to prevent.  (For SHIPPING a designed surface in-session — not a discovery report — use the sibling `/frontend-design` skill instead; see "Sibling skill" below.)

**Motion-jobs test (no quota).**  Every interaction / animation candidate must name the **job** it serves — *orientation / causality / feedback / continuity* (`interaction-vocabulary.md` is this repo's motion-vocabulary analogue; cite `[INT-N]`).  No job, no motion; there is no motion quota to fill.  **Native Qt facility first** — the existing `[INT-*]` primitives (busy-cursor, status-bar feedback, slider-release render, camera-fire-and-render).  A new animation engine (`QPropertyAnimation` / `QGraphicsOpacityEffect`) is proposed only when a named job needs one, and any reduced-motion honour is a **QSettings toggle**, not a `prefers-reduced-motion` media query.

**Surface awareness.**  `--surface` gates whether experiential (cinematic) motion is even considered.  **This app is a NATIVE Qt tool surface (S-2) end to end** — see the translation note.  Default is `--surface tool`.

### Translation note — this is a PySide6/Qt desktop app, not a web frontend

The taste canon and motion vocabularies are product-neutral but written in **web** mechanics.  They are folded in here by **translation**, not by copy.  The doctrine's *substance* (thesis-before-pixels, the BAN-1..15 anti-template list, the §10 cookie-cutter score, the motion-jobs test, the mandatory a11y lane) applies **fully**; its *web mechanics* do not.  Translate each axis:

| Canon axis (web form) | This repo (Qt form) |
|---|---|
| Design tokens / CSS custom properties | `_qt/styles.py` `PALETTE_LIGHT` / `PALETTE_DARK` dicts + `.qss` (`_render_stylesheet`) + `QPalette` roles |
| Motion (GSAP/Lenis/WebGL, `[MOT-N]`/`[EXP-N]`) | `QPropertyAnimation` / `QGraphicsOpacityEffect` / VTK camera interpolation; cite `[INT-N]` |
| `prefers-reduced-motion` media query | a **QSettings** reduced-motion toggle (honoured in code, not by the OS media query) |
| Perf budget = KB shipped / bundle size | **startup-render time + frame time on camera interaction** (marching cubes ≈0.5s; new layers stack) |
| a11y = ARIA / WCAG-via-DOM | keyboard focus + tab order, `setAccessibleName`, `.qss` contrast (WCAG AA in BOTH themes) — AI-11/AI-12 |
| Dark/light via `@media (prefers-color-scheme)` | `APP_STYLESHEET` / `APP_STYLESHEET_DARK` swapped by the Theme menu (dark is the launch default — the VTK viewport is always `#2f2f2f`) |
| React 19 / RSC compat | **INERT** — no React, no DOM, no bundler.  N/A. |

**Experiential motion is INERT here and BLOCKED by surface class.**  The whole app is S-2 (tool): there is NO marketing / landing / hero / login / onboarding surface anywhere.  Reverse-engineering award-winning *websites* (parallax, smooth-scroll, scroll-driven scrub, WebGL galleries) has **near-zero transfer** to a Qt desktop tool, so `frontend-uplift-experiential-scout` is **NOT dispatched by default in any mode** — this is stated explicitly, not silently dropped.  It stays available only if the user explicitly names a real web surface to model (there is none today); even then, warn about the transfer gap.  The award sites' *discipline* (type hierarchy, one focal idea, authored chrome, honest copy) still translates to S-2 and is exactly what the art-direction-scout adapts.

---

## Step 0 — Initialize state + canon freshness

```bash
.claude/scripts/frontend-uplift/init-uplift.sh <ID> [--brief "<verbatim user brief>"] [--surfaces "<csv>"]
mkdir -p .claude/agent-memory/frontend-uplift-art-direction-scout \
         .claude/agent-memory/frontend-uplift-visual-scout \
         .claude/agent-memory/frontend-uplift-library-scout \
         .claude/agent-memory/frontend-uplift-inspiration-scout \
         .claude/agent-memory/frontend-uplift-current-state-critic \
         .claude/agent-memory/frontend-uplift-challenger
```

- If the state file already exists, the script prints `state already exists (phase=X) — resuming`.
- If resuming: run `status.sh` first, then skip to the appropriate phase below.
- The `mkdir -p` ensures per-agent memory dirs exist; safe to re-run.

Set the surface class and discover mode (default `tool` / `standard`) so resume can see the original choice:

```bash
.claude/scripts/frontend-uplift/checkpoint.py <ID> --set surface_class='"tool"'      # parsed --surface, default tool
.claude/scripts/frontend-uplift/checkpoint.py <ID> --set discover_mode='"standard"'  # parsed --mode, default standard
```

**Canon freshness (advisory — surface loudly, NEVER blocks):**

```bash
python3 .claude/scripts/frontend-uplift-canon-lint.py check --root .
```

Print the result prominently.  If it reports drift or warnings, say so — the canon may be stale — but proceed regardless; this check never halts a run.

```bash
.claude/scripts/frontend-uplift/status.sh <ID>
```

Read `.claude/references/frontend-uplift/state-schema.md` only if you need to inspect or write a field the scripts don't cover.

---

## Step 1 — Discover (two waves, parallel WITHIN each wave)

Read `.claude/references/frontend-uplift/phase-discover.md` once at phase start.

### 1a — Preflight: ensure the off-screen render pipelines are operational

The visual scout drives TWO off-screen pipelines: (i) `pv.OFF_SCREEN = True` renders of representative surfaces, and (ii) `QT_QPA_PLATFORM=offscreen` + `QWidget.grab()` captures of panel chrome (`AppearancePanel`, `ViewPanel`, `ParametersPanel`, `ParameterGridPanel` — pure-Qt panels that host no `QtInteractor`, so they're safe under offscreen; the AI-3 ban is specifically on `MainWindow` under offscreen).  Before dispatching, run:

```bash
.claude/scripts/frontend-uplift/ensure-render-up.sh
```

If exit status != 0, surface the recovery hint and HALT before dispatching any agent.  Re-invoke `/frontend-uplift <ID>` after fixing — `init-uplift.sh` is idempotent and `status.sh` will show the phase ready to advance.

### 1a' — Capture panel chrome (always)

The visual scout and the art-direction scout both need pixel-truth on the Qt panel chrome (slider rails, group-box headers, button states, QSS-rendered colors in BOTH themes), not just the 3D surface.  Capture into the render directory so the scouts read them together:

```bash
RENDER_DIR=".claude/notes/frontend-uplifts/<ID>/renders"
mkdir -p "$RENDER_DIR/panels"
.venv/bin/python .claude/scripts/frontend-uplift/render-panel-chrome.py "$RENDER_DIR/panels"
```

`render-panel-chrome.py` auto-detects dark-mode capability via `getattr(styles, "APP_STYLESHEET_DARK", None)` and emits light + dark variants (both themes now ship).  Cost: ~3 seconds wall-clock.  Safe under offscreen by AI-3's clarifying paragraph (pure-Qt panels host no VTK GL context).

### 1b — Dispatch matrix (by mode)

The art-direction scout runs in **EVERY** mode.  Dispatch in **two waves** — evidence first, then the direction/outward scouts fed that evidence:

| Mode | Wave 1 (evidence) | Wave 2 (direction + outward, fed wave-1 evidence) | When to choose |
|---|---|---|---|
| **lean** | visual-scout + current-state-critic | art-direction-scout | Quick scan; library/inspiration deferred |
| **standard** (default) | visual-scout + current-state-critic | art-direction-scout + library-scout + inspiration-scout | The canonical configuration |
| **deep** | visual-scout + current-state-critic | art-direction-scout + library-scout + inspiration-scout | standard, but bump current-state-critic reasoning one tier (dispatch it opus / effort:high) |
| **experiential** | — | — | **INERT for this repo** (see translation note).  Do NOT add the experiential-scout for a native S-2 app; fall back to `standard` and say why. |

Fire **all scouts in a wave in ONE assistant turn** (N `Agent` tool blocks).  Parallel within each wave; never one-at-a-time.  Wave 2 opens only after wave 1 returns, so the art-direction scout can read the visual evidence + the current-state critique before forming its frame (its Step 2 contract).

The existing scouts (`visual-scout`, `library-scout`, `inspiration-scout`, `current-state-critic`, `challenger`) use the canonical prompts in `.claude/references/frontend-uplift/agent-prompts.md` — copy verbatim, `subagent_type: general-purpose`, sonnet, `isolation: worktree`, substituting `{ID}`, `{UPLIFT_BRIEF}`, `{BRIEF_PATH}`, `{RENDER_DIR}`, `{SURFACES}`.

The `art-direction-scout` is a self-contained agent (`.claude/agents/frontend-uplift-art-direction-scout.md`) — dispatch by name (`subagent_type: frontend-uplift-art-direction-scout`, opus, `isolation: worktree`).  If `subagent_type` dispatch fails because the agent was synced this session (registration lag), fall back to `general-purpose` and instruct it to Read + follow `.claude/agents/frontend-uplift-art-direction-scout.md` verbatim.  Substitute its input variables:

- `{ID}` → uplift slug · `{BRIEF}` → `state.uplift_brief` · `{SURFACE}` → `state.surface_class` (default `tool`)
- `{BRIEF_PATH}` → `.claude/notes/frontend-uplifts/<ID>/discover/art-direction-scout-brief.md`
- `{VISUAL_MANIFEST}` → the render directory `.claude/notes/frontend-uplifts/<ID>/renders/` (PNG index; the scout Reads the PNGs directly)
- `{CURRENT_STATE_BRIEF}` → `.claude/notes/frontend-uplifts/<ID>/discover/current-state-critic-brief.md`
- `{TARGETS}` → empty (no web exemplars for a native app) · `{LIVE_RECON_PATH}` → empty (no browser)

Record each dispatch and advance state:
```bash
for agent in visual-scout current-state-critic art-direction-scout library-scout inspiration-scout; do
  .claude/scripts/frontend-uplift/checkpoint.py <ID> --append agents_dispatched="\"$agent\""
done
.claude/scripts/frontend-uplift/checkpoint.py <ID> discover-running
```

(In lean mode the dispatched set is `visual-scout`, `current-state-critic`, `art-direction-scout` only.)

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

If the art-direction scout returns `frame_degraded` (it could not build a frame), say so plainly — the synthesizer will build a provisional frame from `frontend-design-language.md` §8/§9 and the challenger's Axis 11 treats a frameless catalog as a run-level BLOCKER.

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

**OPEN with the design frame.**  Section 1 of the synthesis ADOPTS the art-direction scout's frame verbatim as its opening: the visual thesis, the 3 divergent directions, the active BAN-1..15 list, and the surface map.  Then place every candidate relative to that frame — `[DIRECTION-DEFINING]` (executes the chosen direction), compatible, or `[polish]`.  A frameless catalog (candidates with no adopted frame) is not acceptable — if the art-direction scout failed, build a provisional frame from `frontend-design-language.md` §8/§9 and say so.

Use the fixed candidate-entry shape and taxonomy from `phase-synthesize.md`.  Deduplicate across briefs.  Surface FOUNDATIONAL candidates (the ones others depend on).  Cross-link interaction primitives `[INT-N]` and note the motion **job** each motion candidate serves.

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

Single `Agent` call — dispatch `frontend-uplift-challenger` (`subagent_type: general-purpose`, opus, `isolation: worktree`) with the canonical Challenger prompt from `agent-prompts.md` verbatim.  Substitute `{ID}`, `{SYNTHESIS_PATH}`, `{CHALLENGE_PATH}`.  The challenger walks an **11-axis** checklist; its **Axis 11 is distinctiveness / anti-template** — it Reads `.claude/references/frontend-design-language.md` directly, scores each candidate's projected end-state against BAN-1..15 + the §10 cookie-cutter rubric, and treats a frameless synthesis or a template/neon-HUD projected surface as a run-level BLOCKER.

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

## Step 4 — Prioritize (main session, PORTFOLIO LANES)

Read `.claude/references/frontend-uplift/phase-prioritize.md` once at phase start.

```bash
.claude/scripts/frontend-uplift/checkpoint.py <ID> prioritize-running
```

Run in the **main session** (NOT a sub-agent) — the user reviews this report directly.

Read synthesis + challenge end-to-end.  **Assign every candidate to exactly ONE portfolio lane, then RICE-rank ONLY WITHIN a lane** (cross-lane ranking mathematically buries structural design under XS polish):

1. **`a11y-safety-debt`** — MANDATORY lane, listed **FIRST**, **never ranked away**.  WCAG AA / contrast regressions (AI-12), focus-ring + tab-order gaps, re-entrancy hazards (AI-9 `processEvents()` without the `_computing` guard), the "camera state change without a follow-up `render()`" class of bug (`[INT-23]`), 6-digit-hex-into-PyVista (AI-13), and math-honesty regressions (AI-15).  These are debt; they ship regardless of RICE.
2. **`signature-direction`** — candidates that execute the chosen art-direction direction (frame-defining moves).
3. **`foundations`** — enabling refactors others depend on (e.g. `_qt/styles.py` token consolidation, a shared panel base class, a `LATEX_PREVIEW` helper).
4. **`workflow`** — task-completing features (mesh export, exact-numeric entry, side-by-side compare, parameter sweep).
5. **`polish`** — cosmetic single-surface paper-cuts.

Within each lane, score **RICE-light** (R 1/3/10 × Visual-Impact 0.5/1/3 × Confidence 0.3–1.0 / Effort-by-tshirt 0.25/1/3/8).  Apply challenger penalties (drop on un-redesigned BLOCKER; halve on redesigned BLOCKER; −25% on MAJOR; none on MINOR/NONE).  Write:
```
.claude/notes/frontend-uplifts/<ID>/artifacts/final-report.md
```

with these sections in order:

1. Executive summary (the adopted thesis + chosen direction in one line; top pick per lane; caveat)
2. Design frame recap (thesis + 3 directions + BAN list + surface map, from synthesis §1)
3. Portfolio lanes — **`a11y-safety-debt` FIRST**, then signature-direction / foundations / workflow / polish; RICE-ranked within each
4. Top candidates in detail (synthesis entry + challenger objections + within-lane RICE breakdown + DAG note)
5. Recommended next steps (a11y-debt first; then 1–2 ready for CONTEXT.md §6's implementation pipeline; spike candidates; parking lot)
6. Visual evidence index (renders × candidates)
7. Honest limitations
8. Cross-reference index

**Always OFFER but NEVER auto-invoke any implementation pipeline.**  Include the offer footer when candidates clear the documented thresholds; the user picks the next step.

Record:
```bash
.claude/scripts/frontend-uplift/checkpoint.py <ID> --set final_report_path='".claude/notes/frontend-uplifts/<ID>/artifacts/final-report.md"'
.claude/scripts/frontend-uplift/checkpoint.py <ID> --set ranked_candidates='[{"id":"UPL-1","title":"...","lane":"a11y-safety-debt","rice":13.0,"rank":1},...]'
.claude/scripts/frontend-uplift/checkpoint.py <ID> complete
```

Print a 5-line final summary: uplift id, total candidates, the adopted thesis + chosen direction, a11y-debt lane count, top pick per lane, BLOCKER count, recommended next step.

---

## Optional Gen-2 path — `--workflow` (explicit opt-in ONLY)

`--workflow` runs Discover → Synthesize → Challenge → Prioritize as a deterministic **background Workflow** (`.claude/scripts/frontend-uplift-workflow.mjs`) instead of the in-session Gen-1 path above.  **The Workflow tool requires the user's explicit opt-in per run** — `--workflow` must NEVER be taken automatically; the default is the Gen-1 in-session path documented above.

When `--workflow` is passed:

1. Step 0 (init + `--set surface_class`/`discover_mode` + the canon-lint) and Step 0.5 (the **REQUIRED** `ensure-render-up.sh` preflight + the panel-chrome capture) still run in the **MAIN session** — the Workflow JS cannot exec scripts or drive off-screen renders.
2. Then invoke the Workflow tool:
   ```
   Workflow({ scriptPath: ".claude/scripts/frontend-uplift-workflow.mjs",
              args: { id: "<ID>", brief: "<BRIEF>", mode: "<lean|standard|deep>",
                      surface: "<tool|mixed>", surfaces: "<SURFACES>" } })
   ```
   The Workflow offloads SYNTHESIZE / PRIORITIZE to the tool-capped `pipeline-synthesizer` / `pipeline-prioritizer` agents.  Record the returned `runId` for `--resume`; on `--resume` relaunch with `resumeFromRunId`.

> **No Workflow tool in this session?** Some harness builds don't provide it.  Do NOT re-inline the transforms — just use the default Gen-1 in-session path (Steps 0–4).

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

## Sibling skill — `/frontend-design` vs `/frontend-uplift`

- **`/frontend-design`** (`.claude/skills/frontend-design/SKILL.md`) BUILDS or RESTYLES a surface **in-session**: thesis → implement → self-score.  It ships code.
- **`/frontend-uplift`** (this command) produces a **ranked discovery report** and **ships NOTHING**.  Use it when you can't yet name which 3 modernizations to ship next.  Hand the report to `/frontend-design` or CONTEXT.md §6 to actually build.

---

## Common rationalizations (anti-pattern guard)

| Tempting belief | Reality |
|---|---|
| "Skip the render preflight check — the agents can figure it out." | NO.  The visual scout can't run without an operational `pv.OFF_SCREEN` pipeline.  Preflight is load-bearing. |
| "Skip the art-direction scout in lean mode — it's just taste." | Taste IS the deliverable gap.  The art-direction scout is in EVERY mode; dropping it re-creates the cookie-cutter output this pipeline was rebuilt to prevent. |
| "Better cards, nicer shadows, some motion — that's the uplift." | Polish on an undirected layout is still generic.  The frame comes first: thesis + direction + BAN list (art-direction scout), THEN candidates.  A run whose top picks are all `[polish]` must say so explicitly (Phase 4). |
| "Skip the visual scout — the other agents cover the gaps." | NO.  Without rendered evidence, every claim about visual state is unverifiable.  The visual scout is the EVIDENCE-PRODUCING agent; the rest are interpreters. |
| "Fire the scouts one at a time so I can read each brief as it lands." | The pipeline already does this the RIGHT way: wave 1 (visual + current-state) then wave 2 fed that evidence — parallel WITHIN each wave.  Do not serialize further, and never collapse to one blind wave. |
| "Dispatch the experiential scout — award sites are impressive." | This app is 100% S-2 native Qt; there is NO web/hero/landing surface.  Reverse-engineering award WEBSITES has near-zero transfer.  The experiential scout is INERT here — say so, don't dispatch it. |
| "Propose parallax / scroll-zoom / a WebGL gallery for the viewport." | Marketing spectacle on an S-2 tool surface is BAN-12 → challenger Axis 11 BLOCKS it.  Motion must name an orientation/causality/feedback/continuity job (`[INT-N]`), or it doesn't ship. |
| "The dark theme could pop with neon-cyan wireframes and glass docks." | That's the Qt analogue of the generic AI dashboard (BAN-1/3/8) — a sci-fi HUD.  Dark here is a darkroom for the specimen, not a HUD.  Axis 11 BLOCKS it. |
| "Skip the challenger — the synthesis is good enough." | Synthesis biases toward "more polish".  Without an adversary, Phase 4 ranks aspirational candidates blind to AI-2/AI-3 macOS-segfault, LGPL-redistribution, accessibility cost, AND distinctiveness (Axis 11). |
| "Rank a11y-debt against features by RICE." | NO.  a11y-safety-debt is its own lane, listed FIRST, never ranked away.  RICE is computed only WITHIN a lane; cross-lane RICE buries structural work under XS polish. |
| "Auto-invoke an implementation pipeline on the top candidate." | NEVER.  Offer-and-wait. |
| "Inflate severity to surface more findings." | The challenger's NONE is a credible result.  Aim 30–60% NONE; padding objections erodes signal. |
| "Propose Mayavi for an alternative renderer." | AI-1 violation.  Mayavi is broken on Apple Silicon as of 2025.  Mayavi/matplotlib-3D/Plotly/k3d/raw-VTK are anti-pattern. |
| "Propose `clip_box` for the cube domain clip — it should work now." | AI-4 violation.  `clip_box(invert=...)` semantics on PolyData are reversed/unreliable (CONTEXT.md §8.2).  Stick with `clip_scalar`. |
| "Use `Qt.AlignLeft` shorthand for new code." | AI-11 drift.  Use `Qt.AlignmentFlag.AlignLeft` consistently. |
| "Hardcode a hex in a new `setStyleSheet` call." | Drift from the role-property + `PALETTE_*` pattern (`_qt/styles.py`); breaks theme switching.  Route colors through `palette[...]` tokens / QSS role selectors (AI-12/AI-13). |

---

## Don'ts

- **Don't run Phase 4 as a sub-agent.**  It needs the user's review surface.
- **Don't drop the art-direction scout.**  It fires in EVERY mode, lean included.
- **Don't accept a frameless synthesis.**  Phase 2 opens with the adopted frame; Axis 11 treats a frameless catalog as a run-level BLOCKER.
- **Don't dispatch the experiential scout for this native app.**  It's INERT (no web surface); note it, don't silently drop it.
- **Don't let experiential/marketing motion leak onto the S-2 tool surface** (BAN-12).  Every motion candidate names its job or it doesn't ship.
- **Don't rank across lanes.**  a11y-safety-debt first and always; RICE only within a lane.
- **Don't auto-invoke any implementation pipeline, and don't ship code.**  Offer-and-wait; the final report is the deliverable.
- **Don't skip the preflight `ensure-render-up.sh` check.**  The whole Phase 1 hinges on a reachable off-screen render pipeline.
- **Don't take `--workflow` automatically.**  The Workflow tool needs the user's explicit opt-in per run.
- **Don't manufacture candidates.**  Every catalog entry traces to ≥1 discover brief.
- **Don't bypass `scripts/init-uplift.sh`.**  State directory naming is load-bearing.
- **Don't commit uplift artifacts unless asked.**  Uplift notes live under `.claude/notes/frontend-uplifts/` and are local.

---

## Sub-agent memory

All `frontend-uplift-*` agents have `memory: project` in their frontmatter.  Their memory accumulates under `.claude/agent-memory/<agent-name>/` across uplift runs (including `frontend-uplift-art-direction-scout`, whose lessons track which directions survived challenge and which reference traits translated to S-2).  Do NOT clear or overwrite these directories — they carry institutional memory across runs.

---

## References

Phase references (`phase-discover.md`, `phase-synthesize.md`, `phase-challenge.md`, `phase-prioritize.md`), the agent-prompts source (`agent-prompts.md`), and the repo-local knowledge files (`interaction-vocabulary.md`, `design-system.md`) are surfaced INLINE at their phase entries.  The cross-cutting references:

**Taste canon (SYNCED — flat `.claude/references/`, product-neutral, read-only; translate the web mechanics per the note above):**
- `frontend-design-language.md` — THE taste canon: §1 anti-reference, §4 REF-1..9 library, §5 BAN-1..15, §6 premium-instrument S-2 spec, §8 direction seeds, §9 house-thesis contract (this repo fills it in `frontend-uplift/design-system.md`), §10 cookie-cutter rubric, §11 four questions, §14 evidence tiers + DQS
- `frontend-uplift-motion-vocabulary.md` — §0 surface-class model (S-1 / S-1m / S-2) + `[MOT-N]` tokens (web motion; the Qt analogue is `interaction-vocabulary.md`)
- `frontend-uplift-experiential-motion.md` — `[EXP-N]` experiential recipes (INERT here — no S-1/S-1m surface)
- `frontend-uplift-source-registry.md` — award-site exemplars + toolkit (web; the Qt scientific-viz peers live in this repo's `frontend-uplift/source-registry.md`)

**Repo-local (this repo's stack-specific pipeline):**
- `.claude/references/frontend-uplift/interaction-vocabulary.md` — the Qt `[INT-N]` interaction + visual-effect vocabulary (this repo's motion-vocabulary analogue; cite by id)
- `.claude/references/frontend-uplift/design-system.md` — the design-system inventory + **§9 house thesis** (visual thesis, named anti-references, surface map)
- `.claude/references/frontend-uplift/state-schema.md` — `state.json` field reference
- `.claude/references/app-invariants.md` — AI-1 .. AI-15 architectural locks (Challenger Axis 1)
- `.claude/references/critique-format.md` — canonical severity rubric
- `CONTEXT.md` §6 — the implementation pipeline that consumes the final report
- `CONTEXT.md` §3 + §8 — stack rationale + bugs caught (load-bearing repo quirks the challenger must respect)
