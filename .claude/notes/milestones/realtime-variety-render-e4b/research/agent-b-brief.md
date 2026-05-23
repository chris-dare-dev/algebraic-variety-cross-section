# agent-b research brief — realtime-variety-render-e4b

**Milestone:** `realtime-variety-render-e4b` — CAND-3 coarse-preview LOD (the split-off other half of `realtime-variety-render-e4`).
**Lens:** Qt / dispatch / integration (the worker, the slot, and the AI-9 / AI-15 state machines).
**Date:** 2026-05-22

---

## 1. TL;DR

Pass coarse mode as an **`is_coarse: bool` constructor arg on `MeshWorker`** (which both threads the boolean into the existing `params: dict` as `params["n"] = coarse_n[surface]` and sets `MeshResult.is_coarse=True` for the slot), invert `_on_params_preview_changed` to fire `_render_current(reset_camera=False, coarse=True)` for **implicit** surfaces, and make `_on_params_changed` always full-res — so the existing `_computing` / `_pending_render` queue-latest guard coalesces drag-tick bursts and the release-time full dispatch lands on top. The main risk is the **AI-15 Preview-badge state machine** under the four edge cases the brief flags (error path, close-event mid-flight, coarse-without-follow-up because the user keeps dragging, supersede by a full-on-top-of-coarse) — get any of them wrong and the badge sticks or vanishes. Backup plan: if a single `is_coarse` field proves too coupled to dispatch state, lift it to a tiny `RenderMode` enum (`COARSE` / `FULL`) that worker, result, and slot all key off — same plumbing, three-state-safe.

---

## 2. Prior art in this repo

- **`app.py:497-532` `_on_params_preview_changed`** — the debounced drag-tick slot. Today it does `if should_render_on_drag(self._current_surface): self._render_current(reset_camera=False)`. AI-6 guard already enforces "Hanson only" via `should_render_on_drag` (the predicate at `surfaces.py:82`). e4b INVERTS this routing for implicits: a `typical_ms == 0` surface dispatches `coarse=True`, a `typical_ms > 0` surface dispatches `coarse=False` (existing Hanson fast-path). The docstring explicitly anticipates this work at `app.py:521-527`: "When e4 adds CAND-3's coarse-LOD path, that path's drag-tick branch MUST guard on `should_render_on_drag(surface)` / `surface.typical_ms > 0` and skip Hanson".
- **`app.py:490-495` `_on_params_changed`** — the slider-release slot. Today always full-res (`_render_current(reset_camera=False)`). e4b leaves this alone — release is always full.
- **`app.py:588-691` `_render_current`** — the dispatch function. Today it takes `*, reset_camera: bool` only. e4b adds `coarse: bool = False`. The `_computing` short-circuit at `app.py:612-627` and the dispatch body at `app.py:629-691` both need the coarse flag plumbed through (it must end up on the constructed `MeshWorker` AND on the in-flight context for the slot to recover at result time).
- **`app.py:629-674` the dispatch body** — captures `_inflight_surface`, `_inflight_params`, `_inflight_reset_camera`, `_inflight_hq_label`. e4b adds a parallel `_inflight_is_coarse: bool` slot AND a `_inflight_coarse_label_set: bool` (so the badge's "was the Preview badge already shown?" state can be recovered when the full-res result lands — see §4).
- **`app.py:684` `MeshWorker(surface.generate, dict(params), self._generation)`** — the worker constructor. The `params: dict` already carries the user's slider values. The brief's question (coarse `n` via params dict vs new arg) is settled by `surfaces.py`: every implicit generator accepts `n` as a kwarg with a per-generator default (`kummer_surface(mu_squared=1.3, n=240)` at `surfaces.py:467`; `enriques_figure_1` at `surfaces.py:526` `n: int = 240`; `enriques_figure_3` `n: int = 240` at `surfaces.py:621`; `enriques_figure_4` `n: int = 220` at `surfaces.py:658`; `calabi_yau_dwork` `n: int = 260` at `surfaces.py:888`; `fano_klein_cubic` `n: int = 240` at `surfaces.py:947`; `fano_segre_cubic` `n: int = 240` at `surfaces.py:989`). `fermat_quartic(..., n: int | None = None)` at `surfaces.py:380` — passes through to an adaptive cap if None — but an explicit small `n` overrides the cap (the body just does `if n is None: n = int(np.clip(...))` at `surfaces.py:435-436`). Conclusion: **inject `params["n"] = coarse_n` at dispatch time**. No worker-API change to thread the value through; the worker change is purely the `is_coarse` flag for the result.
- **`render_worker.py:65-104` `MeshResult` dataclass** — adds one field: `is_coarse: bool = False`. Defaulted so callers in `test_render_worker.py:79` (mesh smoke-test) keep compiling.
- **`render_worker.py:118-151` `MeshWorker`** — constructor gains `is_coarse: bool` (4th arg, defaulted False); `run()` passes it through to the `MeshResult` constructor. The worker stays mode-agnostic — it doesn't *do* anything differently for coarse, the only signal it carries is the tag.
- **`render_worker.py:42-62` `is_stale_result`** — unchanged semantics (the supersede predicate ignores mode). But CONTEXT.md §8.18 anticipates this exact future: "the coarse-LOD / per-tick-dispatch direction `render_worker.is_stale_result`'s docstring explicitly anticipates" — when every drag tick dispatches a worker, the supersede check load-bears.
- **`app.py:693-839` `_on_mesh_ready`** — the result slot. Today its `try` body unconditionally calls `_apply_domain_and_render(reset_camera=self._inflight_reset_camera)` (`app.py:753`), the status-bar branch (`app.py:799-821`), and the `finally` (`app.py:822-838`) that restores cursor + clears `_computing` + fires catch-up. e4b adds: read `result.is_coarse`; if coarse, set the badge text "Preview — {label} — NNN ms" and SKIP the full bbox/verts/faces formatting; if full-res, render the full base_msg AND clear the badge (the badge text contract IS the prefix of the status-bar message, see §4).
- **`app.py:610-627` the `_computing` / `_pending_render` guard** — re-entered for analysis (§4). Today bullet-proof for single-flight; the per-tick dispatch of e4b doesn't change the guard, only what's queued.
- **`app.py:570-574` `_on_hq_smoothing_changed`** — a non-render-trigger that re-renders via the same `_render_current` path. e4b does NOT touch HQ-smoothing — but the `_HQ_SMOOTHING_ELIGIBLE_GENERATORS` set + the `params["hq_smoothing"] = True` injection at `app.py:647-652` lives at the same code site where coarse `params["n"] = coarse_n` belongs. The pattern is established; the implementer should mirror it.
- **`surfaces.py:54-71` `Surface` dataclass** — has `typical_ms: int = 0` as a trailing defaulted field (AI-8 safe). e4b adds a SECOND trailing defaulted field `coarse_n: int = 0` (the per-surface coarse floor) — the brief's "exposed via a function or a per-Surface field on the Surface dataclass" alternative. Per-Surface field is cleaner: no second registry to keep in sync, no `if surface.generate in {...}` lookup, the `Surface` *is* the spec. `coarse_n=0` (the default) is the "no coarse-LOD" signal — the dispatch guard `if surface.coarse_n > 0 and surface.typical_ms == 0` makes the AI-6 Hanson skip explicit at the call site.
- **`surfaces.py:82-100` `should_render_on_drag`** — the established free-function precedent for an AI-2-testable speed-routing predicate. e4b adds a sibling free function `dispatch_mode(surface, in_drag) -> Literal["coarse", "full", "skip"]` (or equivalent — implementer's call on naming). The pattern is identical to `should_render_on_drag` / `clipped_cache_is_valid` / `is_stale_result` — extracted explicitly so the routing decision is unit-testable Qt-free (AI-2 satisfied for what *can* be tested).
- **`parameters_panel.py:39-47` `params_changed` / `params_preview_changed` Signals** — the drag/release distinction is already at the panel level. e4b consumes both unchanged; no panel work.
- **`parameter_grid_panel.py:133-139` `grid_params_changed` / `grid_params_preview_changed`** — same distinction in the grid mode. Relayed through `ParametersPanel._on_grid_params_preview_changed` (`parameters_panel.py:348-359`) into the same `params_preview_changed` signal. Grid mode coarse-LOD comes for free.
- **`ui_helpers.Debouncer`** — 80 ms debounce window. The brief's "every drag tick dispatches a coarse worker" is rate-limited at this layer; the `_computing` guard catches anything faster than worker-completion time.
- **`tests/test_render_worker.py`** — the established Qt-free worker-payload + supersede-predicate test pattern. e4b extends with `is_coarse` round-trip + the `dispatch_mode` free function + the per-surface `coarse_n` floor n-sweep tests.
- **e4 adversary critique** (`.claude/notes/milestones/realtime-variety-render-e4/artifacts/adversary-critique.md` HIGH 1, p.16 lines 38-44) — the stale-result early-return bug. CONTEXT.md §8.18 codified the fix: "the `is_stale_result` discard now lives *inside* the `try`". e4b inherits this discipline — any new early `return` in `_on_mesh_ready` (e.g. an "ignore stale-coarse-when-full-is-current" sub-rule) MUST live inside the `try`.
- **CONTEXT.md §4.4** — the e4 re-entrancy contract. e4b's per-tick dispatch changes the *cardinality* (was ≤1 in flight + ≤1 queued; now still ≤1 in flight + ≤1 queued, but the in-flight one may be coarse and the queued one may be a full release). The single-flight guard is preserved; the catch-up logic is unchanged. State this explicitly so the implementer doesn't believe they need a new guard.
- **CONTEXT.md §8.18** — the stale-result-in-try discipline (anticipated coarse-LOD direction by name).
- **CONTEXT.md §9** — the AI-2 worker-lifecycle test gap. e4b adds a second known gap: the live coarse→full state machine cannot be driven Qt-free. The substitute is the new `dispatch_mode` free function plus the existing manual `.venv/Scripts/python.exe app.py` gate.

---

## 3. External sources reviewed

| Source | URL | Key finding | Relevance |
|---|---|---|---|
| Qt 6 docs — QStatusBar::showMessage | doc.qt.io/qt-6/qstatusbar.html#showMessage | `showMessage(text, timeout=0)` replaces the current temporary message; setting `timeout=0` makes it persist until cleared or replaced. A second `showMessage` call simply replaces the text — no queue. | Confirms the AI-15 badge's "persists until the FULL result clears it" is implemented by NOT calling `showMessage` on the coarse-result branch except to update the Preview-badge text, and by calling `showMessage(full_base_msg)` (which replaces) on the full branch. |
| ParaView "Render View" docs — interactive vs still render | docs.paraview.org/en/latest/UsersGuide/displayingData.html#interactive-vs-still-render | Industry pattern: interactive render uses a degraded representation (LOD) and a still render uses full quality on release. Status-bar "Interactive" indicator. | Direct prior art for the AI-15 Preview badge UX (peer scientific viz uses the same coarse-on-drag / full-on-release pattern and surfaces it textually). |
| Mayavi `traits_view` LOD | docs.enthought.com/mayavi/mayavi/mlab.html | Same pattern; degraded LOD during interaction, full quality on release. | Confirms the architectural choice is conventional, not novel. |
| superqt PR review of QRunnable supersede | (rejected as dep in e4) | Same supersede pattern at the framework level; we already have it via `_generation`. | No dep — confirms our hand-rolled supersede + `is_coarse` flag is the right complexity. |
| AVC repo — `app.py` + `surfaces.py` + `render_worker.py` (read in full) | n/a — repo | (See §2 for the file:line attribution per claim.) | Primary; this is mostly a repo-archeology brief. |
| AVC roadmap §6.3 `realtime-variety-render-e4` epic body | `plans/realtime-variety-render-roadmap.md:168-189` | The e4b split is sanctioned: "if the spike report reveals XL risk, split CAND-4 into its own L epic and CAND-3 becomes e4b after CAND-4 stablises". Acceptance signals 1+3 are the e4b-specific ones (coarse-mode off-screen render + AI-15 Preview badge persistence). | Confirms scope of e4b matches the roadmap text. |

---

## 4. Recommended approach

**The split: `_on_params_preview_changed` becomes the coarse-LOD entry; `_on_params_changed` stays the full-res entry.**

(1) **`Surface` dataclass gets a trailing `coarse_n: int = 0` field.** `0` is the "no coarse-LOD" signal; only implicit generators populate it. Per the brief: `fermat_quartic=80, kummer=100, enriques_*=80, dwork=100`; Fano figures default to 80 (a reasonable analogue — Klein cubic n=240→80, Segre n=240→80, etc.). The Hanson trio (`typical_ms ∈ {39,11,18}`) keeps `coarse_n=0` because the AI-6 guard requires it; the n-sweep test validates each floor renders a topology-honest mesh.

(2) **A new free function in `surfaces.py` (mirroring `should_render_on_drag`):**
```
def dispatch_mode(surface: Surface | None, in_drag: bool) -> str:
    """Return 'coarse', 'full', or 'skip' per the e4b speed-routing rules."""
    if surface is None:
        return "skip"
    if not in_drag:
        return "full"  # release path is always full-res
    if surface.typical_ms > 0:
        return "full"  # Hanson fast-path (continuous full at every tick)
    if surface.coarse_n > 0:
        return "coarse"  # implicit with a valid coarse floor
    return "skip"
```
Pure, Qt-free, AI-2-testable. `app.py` calls it from `_on_params_preview_changed(in_drag=True)` and (for symmetry) `_on_params_changed(in_drag=False)` — though the release path can also just call `_render_current(reset_camera=False, coarse=False)` directly. Either way the routing logic is in one place.

(3) **`_render_current(*, reset_camera, coarse=False)`**: when `coarse=True`, inject `params["n"] = surface.coarse_n` (defensive: skip the injection if `coarse_n == 0`, which is the AI-6 Hanson belt-and-suspenders). Construct `MeshWorker(surface.generate, dict(params), self._generation, is_coarse=coarse)`. Capture `self._inflight_is_coarse = coarse` so the slot can recover it. The `_computing` short-circuit at `app.py:612-627` records `_pending_render` as today — a coarse-in-flight + late drag tick coalesces to one catch-up; a coarse-in-flight + slider release also coalesces, but the catch-up must be full (release wins). Two options: (a) record `_pending_is_coarse` and OR it logically (`_pending_is_coarse = _pending_is_coarse AND coarse` — i.e., any full request promotes the catch-up); (b) the simpler "the catch-up re-reads `dispatch_mode` from the live drag state" rule — but the GUI thread doesn't know whether the slider is still being dragged at catch-up time. Option (a) is cleaner; the OR-promote rule mirrors `_pending_reset_camera`'s OR-promote at `app.py:620`.

(4) **`MeshResult.is_coarse: bool = False`**. `MeshWorker.run()` sets it from `self._is_coarse` on both the success and failure paths.

(5) **`_on_mesh_ready`'s AI-15 badge state machine:**
- **states:** `IDLE` (no badge), `PREVIEW` (badge showing "Preview — {label} — NNN ms").
- **transitions:**
  - `IDLE → PREVIEW`: a successful coarse result lands. Badge text replaces status bar.
  - `PREVIEW → PREVIEW`: another coarse result lands (later drag tick won the race). Update the badge text with the new NNN ms.
  - `PREVIEW → IDLE`: a successful FULL result lands. Replace status bar with full base_msg (this clears the badge by replacement).
  - `IDLE → IDLE` (i.e., no badge transition): a successful FULL result with no prior coarse — the existing e4 path.
  - **error path (coarse or full failure):** clear `_raw_mesh = None`, show the error message (which replaces the Preview badge). Treat as IDLE.
  - **close-event mid-flight:** `closeEvent` drains the pool — the result slot runs on workers that complete before drain; any post-drain result is ignored by Qt's event loop teardown. No badge work needed; the QStatusBar dies with the window.
  - **coarse-without-full-follow-up edge case:** user drags continuously and never releases. Each tick dispatches a coarse worker; the supersede guard discards stale ones; the badge keeps updating. This is the *intended steady state* — the badge stays until release. AI-15 is satisfied because the user is still actively dragging; the disclaimer is true.
- **the `_inflight_is_coarse` plumbing:** read it via `result.is_coarse` (the worker tagged it) and branch on that. The slot does NOT recompute from `surface.coarse_n` — the worker was told at dispatch what mode it was.

(6) **AI-6 Hanson skip mechanics:** the `dispatch_mode` free function returns `"full"` (not `"coarse"`) for Hanson because `surface.typical_ms > 0`. Belt-and-suspenders: in `_render_current` the `params["n"] = surface.coarse_n` injection only fires when `coarse=True AND surface.coarse_n > 0`. Belt-AND-suspenders-AND-paranoia: Hanson's `coarse_n` defaults to `0` (the Surface dataclass default), so even if a future bug calls `_render_current(coarse=True)` on a Hanson surface, the injection is a no-op and the surface generates at its parametric `grid` resolution as today.

(7) **AI-9 re-entrancy re-derivation:** today (`app.py:182-187`) `_generation` is incremented once per dispatch; `_computing` blocks concurrent dispatch; the QueuedConnection slot serializes with GUI events. e4b changes the cardinality of dispatches (every 80 ms during drag vs one at release) but not the locking. The `_computing` guard still ensures ≤1 worker in flight at any moment; `_pending_render` still ensures ≤1 catch-up queued; the supersede `_generation` discard handles any race a future implementation introduces. The **new** load-bearing thing is that a stale **coarse** result must not overwrite an in-flight **full**'s in-progress state — but it can't, because `_computing=False` is set in the `finally` of `_on_mesh_ready`, and the slot runs serially (QueuedConnection). So a coarse-then-full sequence is: dispatch coarse → coarse result arrives → set `_computing=False`, run catch-up if `_pending_render`. The catch-up is either another coarse (still dragging) or full (released). The slot fires once per worker, never overlapped.

(8) **AI-2 Qt-free coverage:** `dispatch_mode(surface, in_drag) -> str` is unit-testable: 4 cases per surface family (None, Hanson, implicit-with-coarse_n, implicit-without). `is_stale_result` already covers supersede. `MeshResult.is_coarse` round-trip via a `MeshWorker._compute` direct call is testable (no `QThreadPool`, no signal — direct method invocation). The **n-sweep topology-honesty tests** are pure PyVista off-screen renders: generate Kummer at `n=100` and assert ≥16 connected components (`mesh.connectivity().n_points > 0` per node region); Dwork at ψ=1.0 and `n=100`; Enriques figs 1/2/4 at `n=80` and check non-empty + bounds-finite. The live coarse-vs-full state machine remains untestable Qt-free (live `_on_mesh_ready` invocation requires QApplication) — document in CONTEXT.md §9 alongside the e4 entry.

---

## 5. Alternatives considered

- **New `coarse_n` arg on `MeshWorker.__init__` (separate from `params: dict`):** rejected. The worker's `_compute` already does `self._generate(**self._params)`. Injecting `params["n"] = coarse_n` at dispatch is one line in `_render_current`; adding a worker arg requires worker constructor surgery + a fork in `_compute` to merge `n` into `params`. The `params` dict IS the kwarg vehicle.
- **Reading `coarse_n` from a free-standing module-level dict in `surfaces.py`** (e.g., `COARSE_N: dict[Callable, int] = {fermat_quartic: 80, ...}`): rejected. Requires duplicate registry sync; the per-Surface field mirrors the established `typical_ms` precedent.
- **Adding `RenderMode` enum** (`COARSE`/`FULL`/`SCREENSHOT`): considered as backup. A bool is simpler today; if a future "screenshot/export mode at n=300" ships, lifting to an enum is a 3-line refactor and the slot's `if result.is_coarse:` becomes `if result.mode is RenderMode.COARSE:`. Don't pre-build; leave the door open.
- **Promoting `_pending_render` to a queue of `(coarse, reset_camera)` tuples** (so a coarse + a full in flight both get processed): rejected. Violates the "≤1 catch-up" invariant from e1, and a coarse result superseded by a full request can simply be discarded — the full result is what the user wants. Single-slot OR-promote (`_pending_is_coarse = _pending_is_coarse AND new_coarse`) preserves the invariant and produces the right behavior.
- **AI-15 badge as a separate QLabel widget overlaying the status bar:** rejected. AI-9 risk (extra widget, layout interaction with `showMessage`) is non-trivial; reusing the status bar text is one line. The roadmap acceptance signal says "the status bar reads 'Preview — NNN ms'" — text only.
- **Recompute `is_coarse` from `_inflight_is_coarse` in the slot rather than reading `result.is_coarse`:** functionally equivalent today. But carrying the tag on the result is more honest: the result describes itself; the slot is a pure consumer. Costs ~16 bytes per result. Take it.
- **Skipping the `dispatch_mode` extraction (inline in `_on_params_preview_changed`):** rejected. AI-2 test coverage for the routing logic disappears. Mirror the `should_render_on_drag` discipline.

---

## 6. Risks and unknowns

- **AI-9 re-entrancy under per-tick dispatch.** The `_computing` guard prevents concurrent dispatch; the QueuedConnection slot serializes with GUI events. The only *new* hazard is mode confusion: a coarse result arriving after a full request was dispatched (impossible because the full request waits in `_pending_render` until the coarse finishes; the coarse's slot then fires the full catch-up). State this re-derivation explicitly in the CONTEXT.md §4.4 update so the critic doesn't need to re-do it.
- **AI-15 Preview-badge state machine edge cases:**
  - *Coarse fails, user still dragging:* badge replaced by error message; next coarse success re-shows it. Self-healing.
  - *Coarse succeeds, user releases, full fails:* the badge was up; the full error message replaces it. Status now shows error, which is correct (the user wants to know).
  - *Coarse succeeds, no release for a long time:* badge keeps updating with each tick's NNN ms — this is the intended steady state.
  - *Close mid-coarse:* `closeEvent` calls `self._render_pool.waitForDone(30000)` (`app.py:1131`) — the in-flight worker finishes; its slot fires; the slot's `_apply_domain_and_render` touches the live VTK context, then `super().closeEvent(event)` runs. Watch: if the QStatusBar is already torn down when the slot runs, `showMessage` is a no-op (Qt parents-handle gracefully) — but verify with a manual close-during-drag gate on the macOS pre-ship checklist (CONTEXT.md §9).
- **The worker-lifecycle test gap from e4 widens to a state-machine test gap.** Document in CONTEXT.md §9 + name the substitute: a manual `.venv/Scripts/python.exe app.py` session where the implementer drags a Fermat slider continuously, releases, drags again — the screen recording is the regression artifact.
- **AI-6 Hanson skip — the THREE-LAYER guard.** `dispatch_mode` returns "full" for Hanson; the `coarse_n=0` default on the Hanson surfaces makes the dispatch-time `n` injection a no-op; the worker doesn't know coarse-vs-full intrinsically. The brief calls this out: "the coarse-path guard MUST check surface.typical_ms > 0 and SKIP Hanson". Three layers because routing the parametric pipeline through marching cubes silently produces a wrong mesh (Hanson's `_concat_polydata` path doesn't use marching cubes at all; `n` isn't its grid param anyway — `grid` is). State this clearly so the implementer doesn't relax even one layer.
- **macOS arm64 residual.** Same as e4 — the AI-2 manual gate cannot run on this Windows machine. Mention the on-device checklist (e3 spike report §7 + e4 CONTEXT.md §9 entry).
- **Per-surface `coarse_n` floor topology honesty.** The brief pre-commits floors: `fermat_quartic=80, kummer=100, enriques_*=80, dwork=100`. The n-sweep test MUST run BEFORE final commit — Kummer at `n=100` rendering only 12 of 16 nodes is a real risk if the spacing exceeds the node-resolution threshold (Kummer mu²=2.5 at n=100 has spacing ~0.05; the node neighborhoods are ~0.03-0.1 across, so n=100 is just at the edge of honesty). The brief's "must be validated by an off-screen n-sweep" is non-negotiable. Recommend the implementer render `n=60, 80, 100, 120` for each, compare PNG-on-PNG, AND assert connected-component count programmatically.
- **`fermat_quartic`'s adaptive `n`** (`surfaces.py:435-436`). At default params it caps at 220; with `coarse_n=80`, the dispatch `params["n"] = 80` overrides this. Verify the adaptive bounds (`bounds = max(2.5, 1.15·sqrt(...) + 0.3)`) doesn't combine with `n=80` to produce sub-spec voxel spacing — at `c=30` (extreme slider), bounds grows to ~3, spacing at n=80 is ~0.075. Above the practical floor (~0.03 per CONTEXT.md §8.16) but worth a smoke test.
- **`_inflight_is_coarse` cleared in `finally`:** mirror the existing `_inflight_surface = None` pattern (e4 critique MEDIUM-2 noted aliasing risk on `_inflight_params`). Use `_inflight_is_coarse: bool = False` reset.
- **The "supersede coarse with full" race in `_pending_render`:** if a coarse is in flight and the user releases, the catch-up must be full. The OR-promote rule (`_pending_is_coarse = _pending_is_coarse AND new_coarse`) handles it: `True AND False = False` — a `_render_current(coarse=False)` arriving while `_pending_is_coarse=True` promotes the queued catch-up to full. Document this with a worked example.

---

## 7. AI-15 disclaimers

**Confirming the Preview-badge timing rule from the brief:** "the status bar shows Preview — {label} — NNN ms from the FIRST coarse render and persists until _apply_domain_and_render confirms it has just received the FULL-RES mesh (the coarse-result slot does NOT clear the badge; only the full-res result clears it)". Mechanism in this brief: the badge IS the status-bar text; coarse results write `"Preview — {label} — NNN ms"`; full results write the standard base_msg (which *replaces* the badge text — the "clear" is by replacement, not by an explicit clear call). `_apply_domain_and_render` itself doesn't clear the badge — it can't see the mode — but the slot calling it (which knows `result.is_coarse=False`) is the one that issues the post-clear `showMessage(base_msg)`. The roadmap §6.3 acceptance signal explicitly says "the badge is only cleared when the full-res mesh is confirmed received by `_apply_domain_and_render` (not on coarse render completing)" — this matches.

**Exact badge text:** `"Preview — {surface.label} — {result.gen_ms:.0f} ms"`. The em-dash matches the existing status-bar conventions (`base_msg` uses `"  ·  "` middle-dot separators; the Preview badge uses em-dash so it is visually distinct as a *modal* indicator). The roadmap §6.3 uses `"Preview — NNN ms"` literally; matching it character-for-character preserves the documented acceptance signal. If `result.warning_text` is set on a coarse render (e.g., a coarse Dwork at ψ=1), prefix with `"⚠ "` ahead of `"Preview — ..."` so the warning is preserved (Dwork's conifold warning is the only known case today).

**What is being plotted under coarse:** the same algebraic surface, sampled on a coarser marching-cubes grid. The math is identical; only the visual fidelity is reduced. No new "real shadow" disclaimer is needed (the existing surface tooltips cover the underlying object). The badge is purely a fidelity/freshness indicator — "what you see right now is a low-resolution preview."

---

## 8. Open questions for the user

None. Every implementer-level decision is resolved:
- coarse `n` plumbing: `params["n"] = surface.coarse_n` injection at dispatch (no worker-API change).
- `is_coarse` propagation: new `MeshWorker` constructor arg + `MeshResult` field, default False.
- `Surface.coarse_n` per-surface field on the dataclass (trailing defaulted, mirrors `typical_ms`).
- `dispatch_mode` extracted as the Qt-free routing free function.
- AI-15 badge state machine: 5 transitions enumerated.
- AI-6 Hanson skip: three-layer guard (predicate + `coarse_n=0` default + worker mode-agnostic).
- `_pending_is_coarse` OR-promote (`AND` actually — any full arriving promotes the catch-up to full).
- Coarse floors per the brief; n-sweep test gates them.

If the implementer hits an unforeseen interaction (e.g., the bbox readout at `app.py:789-792` looking weird on a coarse mesh's bbox), the brief's pre-committed answer is: the bbox is read from `_raw_mesh`, which is the LATEST mesh — coarse during drag, full after release. The bbox readout for a coarse mesh is slightly less precise (Kummer n=100 vs n=240 may differ in the 4th decimal); accept this as a feature, not a bug — researchers want to see *what's on screen*. The Preview badge already discloses the fidelity reduction.
