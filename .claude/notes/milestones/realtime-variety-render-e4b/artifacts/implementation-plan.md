# Implementation plan — realtime-variety-render-e4b (CAND-3 coarse-preview LOD)

Inline path. Two-pass coarse-LOD on top of the e4 worker.

1. **`surfaces.py` — Surface field + dispatch predicate + per-surface floors.**
   Add `coarse_n: int = 0` to the `Surface` dataclass as a trailing defaulted
   field (mirror of `typical_ms`). Add a Qt-free `dispatch_mode(surface,
   in_drag) -> "coarse" | "full" | "skip"` free function (mirror of
   `should_render_on_drag`). In the `VARIETIES` registry set `coarse_n` per
   agent-a's measured n-sweep table: **Fermat=80, Kummer=100, Enriques×4=80,
   Dwork=100, Fano Klein/Segre/SexticDoubleSolid=80, Fano two-quadrics=0
   (opt-out — ε-tube fragility), Hanson trio=0 (AI-6 skip)**.

2. **`render_worker.py` — plumb the mode tag.** Add `is_coarse: bool = False`
   to `MeshResult` (trailing defaulted). Add `is_coarse: bool = False` to
   `MeshWorker.__init__` (stashed as `self._is_coarse`); `_compute()` passes
   it into the `MeshResult` on both success and failure paths. The worker
   stays mode-agnostic — it does nothing differently; the flag is just a tag
   for the slot.

3. **`app.py` — drag-routing + dispatch coarse flag + slot badge state machine.**
   - `_render_current(*, reset_camera, coarse: bool = False)`: when
     `coarse=True` AND `surface.coarse_n > 0`, inject `params["n"] =
     surface.coarse_n` before constructing the worker. Capture
     `self._inflight_is_coarse = coarse` (mirror of `_inflight_hq_label`).
     Worker constructed with `is_coarse=coarse`.
   - `_pending_is_coarse: bool = True` (identity element for AND-promote). The
     `_computing` branch does `self._pending_is_coarse = self._pending_is_coarse
     and coarse` so a queued *full* request demotes a queued *coarse* (full
     wins); two queued coarses stay coarse.
   - `_on_params_preview_changed` routes via `dispatch_mode(surface,
     in_drag=True)`: `"coarse"` → `_render_current(coarse=True)`; `"full"`
     (Hanson) → `_render_current(coarse=False)`; `"skip"` → noop.
   - `_on_params_changed` (release): unchanged — defaults to `coarse=False`.
   - `_on_mesh_ready` branches on `result.is_coarse`: coarse → status text
     `f"Preview — {label} — {gen_ms:.0f} ms"` (warning prefix if any), skip
     verts/faces/bbox; full → existing `base_msg` path (the replacement IS
     the "clear" of the badge per Qt `showMessage` semantics). The catch-up
     reads `_pending_is_coarse` and passes it to the next `_render_current`.

4. **Tests.** `tests/test_coarse_n_topology.py` (new, Qt-free): per-surface
   n-sweep at `coarse_n` asserting non-empty + per-generator topology-honesty
   signature (Kummer 16-node octant symmetry; Enriques double-curve vertex
   fraction; Fermat bbox extent; Dwork bbox; Fano bbox); declarative
   `test_coarse_n_values_match_table` asserting every implicit Surface has
   the expected floor and Hanson/fano_two_quadrics are 0. Extend
   `tests/test_render_worker.py` with `MeshResult.is_coarse` round-trip +
   `dispatch_mode` 4-way table for None / Hanson / coarse-eligible /
   opt-out. **Off-screen render verify** Fermat + Kummer + Enriques Fig 1
   at `coarse_n` (AI-3 — `pv.OFF_SCREEN`, never `MainWindow`).

5. **Docs.** CONTEXT.md §3 (numba bullet adjacent — add a coarse-LOD bullet);
   §4.4 (re-entrancy: note the new `coarse` mode parameter doesn't change the
   `_computing` single-flight guard; AND-promote on `_pending_is_coarse`);
   §8 new entry §8.19 documenting the AI-15 Preview-badge contract (coarse
   writes the badge; only full clears it via replacement); §9 (extend the
   AI-2 worker-lifecycle gap to note the coarse↔full state machine).
   `.claude/references/app-invariants.md` AI-15 — record the Preview-badge
   rule. macOS pre-ship residual carries forward from e3/e5 spikes.

Constraints: AI-1, AI-2 (extracted `dispatch_mode` for Qt-free coverage), AI-3,
AI-6 (Hanson three-layer skip: predicate returns "full" / `coarse_n=0` default
/ worker mode-agnostic), AI-9 (re-entrancy unchanged structurally; AND-promote
mirrors OR-promote on `_pending_reset_camera`), AI-14 (kernel just lowers n;
ValueError contract unchanged), AI-15 (Preview badge is the math-honesty
disclaimer for the coarse mesh — persists until full-res confirms).
Predecessors e4 + e5 complete.
