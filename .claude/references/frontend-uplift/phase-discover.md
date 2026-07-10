# Phase 1 — DISCOVER (two waves, parallel within each)

**Purpose:** dispatch the discover scouts in **two waves** so they run concurrently within a wave but the direction scout gets to read the evidence first.  **Wave 1 (evidence):** the visual scout (off-screen renders + panel chrome) + the current-state critic (inward gap audit).  **Wave 2 (direction + outward, fed wave-1 evidence):** the **art-direction scout** (the design frame — dispatched in EVERY mode) + the library and inspiration scouts.  The art-direction scout is what keeps the pipeline from producing cookie-cutter polish; it reads the taste canon (`frontend-design-language.md`) + this repo's `design-system.md` §9 house thesis and produces a visual thesis + 3 divergent directions + the BAN-1..15 list + a surface map.

## Preflight — verify off-screen render pipeline is operational

BEFORE dispatching the visual scout, the slash command body MUST run:

```bash
.claude/scripts/frontend-uplift/ensure-render-up.sh
```

If exit status != 0, halt and surface the recovery hint (install requirements, fix surfaces.py import error, install system OpenGL libs on Linux).  Re-invoke `/frontend-uplift <ID>` after fixing — `init-uplift.sh` is idempotent, so it picks up where it left off.

The non-visual scouts (current-state-critic, library, inspiration) do NOT strictly depend on the render pipeline.  The art-direction scout (wave 2) reads the renders as evidence, so it too is degraded without them.  In practice, the orchestrator should halt the whole phase on preflight failure — partial discovery without visual evidence is low-signal.

## Dispatch matrix (two waves; art-direction scout in EVERY mode)

| Mode | Wave 1 (evidence) | Wave 2 (direction + outward) | When to choose |
|---|---|---|---|
| **lean** | visual-scout + current-state-critic | art-direction-scout | Quick scan; library/inspiration deferred |
| **standard** (default) | visual-scout + current-state-critic | art-direction-scout + library-scout + inspiration-scout | The canonical configuration |
| **deep** | visual-scout + current-state-critic | art-direction-scout + library-scout + inspiration-scout | standard, but bump current-state-critic to opus / effort:high |
| **experiential** | — | — | **INERT for this repo.**  This is a 100% S-2 native Qt tool with no marketing/hero/onboarding surface; the experiential-scout reverse-engineers award *websites* (near-zero transfer).  Fall back to `standard` and say why — do NOT silently drop it. |

Set the mode + surface via `checkpoint.py <ID> --set discover_mode='"standard"'` and `--set surface_class='"tool"'` BEFORE dispatch so resume can see the original choice.

## Dispatch protocol (CRITICAL — two waves, parallel within each)

Fire **all scouts in a wave in one assistant message** containing N `Agent` tool blocks.  Parallel WITHIN a wave; never one-at-a-time (sequential dispatch destroys diversity and doubles wall-clock).  Open wave 2 only after wave 1 returns — the art-direction scout's Step 2 contract requires it to read the visual renders + the current-state brief BEFORE forming the frame.  Do NOT collapse the two waves back into one blind wave, and do NOT serialize further than two waves.

The FOUR existing scouts (visual, library, inspiration, current-state-critic) receive the FULL canonical prompt from `references/frontend-uplift/agent-prompts.md` verbatim, with these substitutions:

- `{ID}` → uplift slug
- `{UPLIFT_BRIEF}` → `state.uplift_brief` verbatim
- `{BRIEF_PATH}` → `.claude/notes/frontend-uplifts/{ID}/discover/<agent-short-name>-brief.md`
- `{RENDER_DIR}` → `state.render_dir` (only used by the visual scout)
- `{SURFACES}` → comma-joined `state.surfaces_to_render` (empty = default 5-surface set)

The **art-direction scout** is NOT prompted from `agent-prompts.md` — it is a self-contained agent (`.claude/agents/frontend-uplift-art-direction-scout.md`).  Dispatch it by name (`subagent_type: frontend-uplift-art-direction-scout`); if registration lag blocks that, fall back to `general-purpose` and have it Read + follow that agent file.  Its substitutions:

- `{ID}` → uplift slug · `{BRIEF}` → `state.uplift_brief` · `{SURFACE}` → `state.surface_class` (default `tool`)
- `{BRIEF_PATH}` → `.claude/notes/frontend-uplifts/{ID}/discover/art-direction-scout-brief.md`
- `{VISUAL_MANIFEST}` → `.claude/notes/frontend-uplifts/{ID}/renders/` (the PNG render dir; the scout Reads the images directly — there is no JSON manifest, so it treats the directory as the index and degrades gracefully)
- `{CURRENT_STATE_BRIEF}` → `.claude/notes/frontend-uplifts/{ID}/discover/current-state-critic-brief.md` (available because it runs in wave 2)
- `{TARGETS}` → empty (no web exemplars for a native Qt app) · `{LIVE_RECON_PATH}` → empty (no browser)

Use `isolation: worktree` on every agent — each gets a worktree-isolated repo state.  Visual-scout uses the local Python interpreter to do off-screen renders; that's process-internal (worktree gets its own .venv if needed, but typically the parent .venv is symlinked).

## Subagent_type and model

| Agent | Wave | Sub-agent type | Model | Tools beyond default |
|---|---|---|---|---|
| visual-scout | 1 | `general-purpose` | sonnet | Add `Bash` (for off-screen render commands), `Read` for PNG inspection |
| current-state-critic | 1 | `general-purpose` | sonnet (deep mode: opus / effort:high) | Standard (no Web tools needed; codebase-only) |
| art-direction-scout | 2 | `frontend-uplift-art-direction-scout` (fallback `general-purpose`) | opus | `Read + Grep + Glob + Bash + WebSearch + WebFetch + Write` |
| library-scout | 2 | `general-purpose` | sonnet | Standard `Bash + Read + Grep + Glob + WebSearch + WebFetch + Write` |
| inspiration-scout | 2 | `general-purpose` | sonnet | Same as library-scout |

## Canonical 5-surface set (visual-scout default)

When `surfaces_to_render` is empty, the visual scout walks these in order via `pv.OFF_SCREEN = True`:

1. `app-startup` — synthetic startup mockup (no Qt instantiation; describes the placeholder state from `app.py:_PLACEHOLDER`)
2. K3 surface / Fermat quartic — implicit, at default params
3. K3 surface / Kummer surface — implicit, at default params
4. Enriques surface / Canonical sextic [Fig. 1] — implicit, at default params
5. Calabi–Yau 3-fold / Hanson quintic [Fig. 1] — parametric, at default params (iconic image)

User override via `init-uplift.sh --surfaces "K3 surface/Fermat quartic,..."` replaces this list verbatim (stored in `state.surfaces_to_render`).

## Per-surface capture spec (visual-scout)

For each surface in the list:

```python
import pyvista as pv
pv.OFF_SCREEN = True
from surfaces import VARIETIES
surf = VARIETIES[variety_key][model_key]
mesh = surf.generate()  # at default params
for w, h, suffix in [(1200, 800, "default"), (2400, 1600, "2x")]:
    p = pv.Plotter(off_screen=True, window_size=(w, h))
    p.add_mesh(mesh, color="#9aa6c8", smooth_shading=True)
    p.show(screenshot=f"{RENDER_DIR}/{slug}-{suffix}.png")
```

`<slug>` derivation: `<variety-lower-with-hyphens>-<model-lower-with-hyphens-no-bracketed-tag>`.  E.g. `K3 surface / Fermat quartic` → `k3-surface-fermat-quartic`.

After capturing, the visual scout uses `Read` to inspect each PNG and capture observations:
- Mesh shape (smooth? crinkled? expected morphology?)
- Color discipline (`#9aa6c8` slate today — is that the right cue?)
- Background (Plotter default — is the contrast right?)
- Lighting / shading (Phong default — does it suit the variety?)

## Returning briefs into state

When an agent returns, the main session:

```bash
.claude/scripts/frontend-uplift/checkpoint.py <ID> --append agents_returned='"<agent-name>"'
.claude/scripts/frontend-uplift/checkpoint.py <ID> --append discover_briefs='"<brief-path>"'
```

When `len(agents_returned) == len(agents_dispatched)`:

```bash
.claude/scripts/frontend-uplift/checkpoint.py <ID> discover-complete
```

## Severity rubric (visual-scout + current-state-critic)

| Severity | Meaning |
|---|---|
| **CRITICAL** | Visual gap that erodes credibility on first launch (e.g., a generator that segfaults, a panel that renders blank, a missing default parameter that produces an empty mesh).  Rare. |
| **HIGH** | Visual gap peer scientific-viz tools all address and this app lacks (e.g., no dark-mode toggle when ParaView / 3D Slicer / Blender all have one; no rendered-math tooltip when Mathematica's `Manipulate` ships it). |
| **MEDIUM** | Quality-of-life gap that compounds across many surfaces (e.g., the default `#9aa6c8` slate doesn't differentiate K3 from Enriques visually). |
| **LOW** | Cosmetic / single-surface paper-cut. |

Calibrate HONESTLY.  A clean surface with no gaps is a credible result.

## Failure modes

- **`ensure-render-up.sh` returns red** → preflight failed; halt before dispatch.  Surface the recovery hint and stop.  Re-invoke after fix.
- **Visual scout's off-screen render fails for a specific surface** (e.g., a generator raises `ValueError` at defaults) → document the failure as a CRITICAL finding (the generator-default is broken; ship-blocker).
- **A library / inspiration scout returns a thin brief** (< 5 candidates) → re-dispatch ONCE with a stricter prompt suffix.  Accept the second attempt's result; weight accordingly in synthesis.
- **A scout hangs for >30 min** → kill the task; re-dispatch with the same prompt.
- **All scouts in a wave fail** → halt; surface to the user.  (A degraded but non-empty wave proceeds; note it.)
- **The art-direction scout returns `frame_degraded`** → the synthesizer builds a provisional frame from `frontend-design-language.md` §8/§9; the challenger's Axis 11 treats a frameless catalog as a run-level BLOCKER.  Say so plainly.
