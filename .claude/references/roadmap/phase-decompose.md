# Phase 2 — DECOMPOSE

**Goal:** turn the refined Objective into 2-6 vertically-sliced epics that each ship a user-observable change in <=6 weeks (single-developer pace).

## Step-by-step

### 1. Pick the technique

Default is **vertical slicing + enabler stories** (Holub; Patton).  Use the long-tail techniques in [`frameworks.md`](frameworks.md) only when the problem shape demands it:

| Problem shape | Technique | Reason |
|---|---|---|
| User-journey-shaped (multi-step user-visible flow — e.g. "first-launch onboarding overlay across 5 surfaces") | **User Story Mapping** (Patton 2014) | Preserves end-to-end coherence |
| Bounded-context unclear (e.g. "where does `view_panel` end and `appearance_panel` begin?") | **Event Storming** (Brandolini 2021) | Surfaces domain seams |
| Causal link from output to outcome is fuzzy ("we think dark mode helps researchers — but does it?") | **Impact Mapping** (Adzic 2012) | Kills features that "seem useful" |
| Anything else | **Vertical Slicing** | Default; cheapest decomposition habit |

If you reach for anything other than vertical slicing, write one sentence in the Decomposition Notes explaining why.

### 2. Slice vertically

Each epic must:
- Cut through every relevant layer (`surfaces.py` generator → `parameters_panel` slider → `app.py` render pipeline → `appearance_panel` / `view_panel` UI when applicable).
- Deliver something observable on completion (a new surface visible in the dropdown; a new slider whose movement changes the render; a new view preset that actually repaints; an off-screen PNG that visually changes).
- Be sized to **<=6 weeks** at one-engineer pace.  Anything bigger gets split.

**Anti-pattern: horizontal slicing.**  "Generator first; then ParamSpec wiring; then UI panel; then tests."  Nothing demoable until the last layer ships, which destroys the feedback loop and gives the adversarial review (CONTEXT.md section 6 phase 3) nothing to grade.

### 3. Tag enabler-vs-value

Every epic carries one tag:

- **`[VALUE]`** — observable user/system change.  Default; every roadmap should be >=60% value epics.
- **`[ENABLER]`** — pure infrastructure (refactor `styles.py` into named tokens, extract a shared `_marching_cubes_to_polydata` helper, add a new dep to `requirements.txt`) that unblocks downstream value epics.  Allowed but limited.

A roadmap with >40% `[ENABLER]` epics has lost the outcome thread — push back and re-slice.

### 4. INVEST check (per epic)

Run every epic through INVEST (Wake 2003).  An epic failing two letters needs to be re-cut.

| Letter | Question | Failure signal |
|---|---|---|
| **I**ndependent | Can this epic land without epic N+1, N+2 being half-done? | "Epic 2 needs Epic 1's `Surface` subclass to compile" — split or merge. |
| **N**egotiable | Can scope shift mid-flight without breaking the implementation pipeline state? | If "all-or-nothing", the epic is too big — apply SPIDR. |
| **V**aluable | Does it deliver an observable change? | If only `[ENABLER]` chains downstream, justify the enabler. |
| **E**stimable | Can a senior engineer T-shirt-size it (S/M/L)? | "I have no idea" -> spike first (Phase 3 spike lane). |
| **S**mall | <=6 weeks at one-engineer pace? | XL epic -> split via SPIDR or User Story Mapping. |
| **T**estable | Will the adversarial review (CONTEXT.md section 6 phase 3) have something to grade? | If the epic produces no diff, it's not an epic. |

### 5. Specialist-area hints

For every epic, name 1-2 specialist areas the implementation pipeline (CONTEXT.md section 6) should consult.  **Hint-only — no callable specialist agents exist in this project.**

| Region keywords (epic touches...) | Specialist hint to embed in epic body |
|---|---|
| `surfaces.py`, `_marching_cubes_to_polydata`, new variety / figure | Cross-verify equations against >=2 sources (AI-15).  If implicit: marching cubes pipeline + Taubin smoothing.  If parametric: `_grid_to_polydata` + `_concat_polydata`, skip Taubin, Hanson normal convention `cell_normals=True, consistent_normals=False` (AI-6, AI-7). |
| `view_panel.py:clip_to_domain`, sphere/cube clip | Use scalar-clipping with `clip_scalar(scalars="_dist", ...)` — NOT `clip_box`.  AI-4 + AI-5. |
| `app.py:_render_current`, render pipeline | Re-entrancy guard `self._computing` around any `processEvents()` (AI-9).  Cached raw mesh, domain-clip recompute only (AI-10). |
| `appearance_panel.py`, `styles.py`, color flowing into PyVista | 6-digit hex only into `pv.Plotter.add_mesh(color=...)` / `pv.set_plot_theme(...)` — AI-13.  WCAG AA >=4.5:1 body text, >=3:1 large text — AI-12. |
| New UI code (Qt enums) | Use `Qt.AlignmentFlag.AlignLeft` / `QSizePolicy.Policy.Expanding` qualified forms — AI-11. |
| New `Surface` registration in `VARIETIES` | `Surface` + `ParamSpec` dataclasses; tooltips in `VARIETY_TOOLTIPS` + `SUBTYPE_TOOLTIPS`; `[Fig. N]` tag in dropdown key; honest "real shadow" disclaimer if the genuine variety can't live in R^3 — AI-8, AI-15. |
| New generator function | Return `pv.PolyData` or raise `ValueError("No real zero set in the sampling box for these parameters. ...")`; soft signals via `warnings.warn(..., RuntimeWarning)` surfaced in status bar — AI-14. |
| Off-screen render verification (any visual epic) | `pv.OFF_SCREEN = True; pv.Plotter(off_screen=True).show(screenshot=...)`.  NEVER `MainWindow()` under `QT_QPA_PLATFORM=offscreen` — AI-3. |
| Tests (any new behavior) | Pure NumPy / PyVista / scikit-image only; no `pytest-qt` — AI-2.  ~4s budget for 120 tests; aim to stay under 5s. |
| Capability-scout / frontend-uplift artifacts cited as brief | Read `.claude/notes/capability-scouts/<id>/artifacts/final-report.md` or `.claude/notes/frontend-uplifts/<id>/artifacts/final-report.md` end-to-end before opening the epic — the candidate id (e.g., UPL-3, CAND-7) belongs in the epic body. |

### 6. Dependency graph

Every epic lists its predecessors.  The graph must be a DAG (no cycles).  If a cycle is forming, two epics are too coupled — merge or split.

## Output template (appended to roadmap.md)

```markdown
<!-- ROADMAP:section:decompose -->
## 6. Epics

### 6.1 Decomposition technique

{Vertical slicing | User Story Mapping | Event Storming | Impact Mapping}

{One-sentence rationale ONLY if not vertical slicing.}

### 6.2 Dependency graph

| Epic | Depends on |
|---|---|
| `<slug>-e1` | — |
| `<slug>-e2` | e1 |
| ... | ... |

### 6.3 Epics

#### `<slug>-e1` — {Short title} `[VALUE]` (or `[ENABLER]`)

**Goal:** {one sentence — observable change on completion}

**Slice:** {which files touched? `surfaces.py`? `view_panel.py`? `styles.py`? `tests/`?}

**INVEST:** {6/6, or list any failing letters with one-sentence justification}

**Specialist hints:**
- {hint from the table — e.g., "AI-6 + AI-7: parametric pipeline + Hanson normal convention"}
- {hint #2}

**T-shirt:** S (<=1 week) / M (<=3 weeks) / L (<=6 weeks)

**Predecessors:** —  *(or epic ids)*

**Acceptance signals:** {2-3 bullets — what makes this epic done?  Off-screen PNG diff?  Test count delta?  WCAG contrast ratio achieved?}

#### `<slug>-e2` — {next epic}
... (repeat for 2-6 epics)
```

## Auto-advance vs gate (decision table)

| Condition | Action |
|---|---|
| Every epic INVEST-clean, dependency graph is DAG, >=60% `[VALUE]`, all sized <=L | **Auto-advance** to Phase 3 |
| Cut between epics has >=2 credible alternatives (e.g., split-by-variety vs split-by-feature; vertical vs hybrid slicing) | **GATE.**  Surface both with one-paragraph tradeoffs.  Wait for `[a]` or `[b]`. |
| `[ENABLER]` epics > 40% of total | **NOT a gate** — push back; re-slice to expose value sooner. |
| One epic is XL (>6 weeks) | **NOT a gate** — apply SPIDR (in [`frameworks.md`](frameworks.md)) and re-cut. |

## Hard rules

- **No story-level decomposition in Phase 2.**  That's Phase 3 (Now lane only).  Epics here, stories there.
- **Every epic has a `<slug>-eN` id.**  Sub-epic letters (`e2a`, `e2b`) only when an epic is split mid-flight, NOT pre-emptively.
- **No epic has dependencies on its own descendants.**  Cycle = merge two epics or split a third.
- **`[ENABLER]` epics need an explicit downstream value epic.**  A pure-enabler chain is a reorganization disguised as a roadmap.
- **Specialist hint section is text, not invocation.**  No "run `/capability-scout`" inside an epic body — that's the user's job to dispatch.
