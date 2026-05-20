# Phase 1 — DISCOVER (parallel)

**Purpose:** dispatch 4 agents in a single assistant turn so they run concurrently in their own context windows.  The visual scout drives off-screen renders; the other 3 do code/web research in parallel.

## Preflight — verify off-screen render pipeline is operational

BEFORE dispatching the visual scout, the slash command body MUST run:

```bash
.claude/scripts/frontend-uplift/ensure-render-up.sh
```

If exit status != 0, halt and surface the recovery hint (install requirements, fix surfaces.py import error, install system OpenGL libs on Linux).  Re-invoke `/frontend-uplift <ID>` after fixing — `init-uplift.sh` is idempotent, so it picks up where it left off.

The other 3 scouts (library, inspiration, current-state-critic) do NOT depend on the render pipeline.  In principle they could fire even if it's down.  In practice, the orchestrator should still halt the whole phase on preflight failure — partial discovery without visual evidence is low-signal.

## Dispatch matrix

| Mode | Agents fired | When to choose |
|---|---|---|
| **standard** (default) | visual-scout + library-scout + inspiration-scout + current-state-critic (4) | Default — the canonical configuration |
| **lean** | visual-scout + current-state-critic (2) | When the user wants a quick scan and library/inspiration discovery is intentionally deferred |

Set via `checkpoint.py <ID> --set discover_mode='"standard"'` BEFORE dispatch so resume can see the original choice.

## Dispatch protocol (CRITICAL — single turn)

Fire **all selected agents in one assistant message** containing N `Agent` tool blocks.  Sequential dispatch destroys diversity and doubles wall-clock.

Each agent receives the FULL canonical prompt from `references/frontend-uplift/agent-prompts.md` verbatim, with these substitutions:

- `{ID}` → uplift slug
- `{UPLIFT_BRIEF}` → `state.uplift_brief` verbatim
- `{BRIEF_PATH}` → `.claude/notes/frontend-uplifts/{ID}/discover/<agent-short-name>-brief.md`
- `{RENDER_DIR}` → `state.render_dir` (only used by the visual scout)
- `{SURFACES}` → comma-joined `state.surfaces_to_render` (empty = default 5-surface set)

Use `isolation: worktree` on every agent — each gets a worktree-isolated repo state.  Visual-scout uses the local Python interpreter to do off-screen renders; that's process-internal (worktree gets its own .venv if needed, but typically the parent .venv is symlinked).

## Subagent_type and model

| Agent | Sub-agent type | Model | Tools beyond default |
|---|---|---|---|
| visual-scout | `general-purpose` | sonnet | Add `Bash` (for off-screen render commands), `Read` for PNG inspection |
| library-scout | `general-purpose` | sonnet | Standard `Bash + Read + Grep + Glob + WebSearch + WebFetch + Write` |
| inspiration-scout | `general-purpose` | sonnet | Same as library-scout |
| current-state-critic | `general-purpose` | sonnet | Standard (no Web tools needed; codebase-only) |

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
- **All 4 scouts fail** → halt; surface to the user.
