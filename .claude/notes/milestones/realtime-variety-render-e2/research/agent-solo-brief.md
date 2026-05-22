# Research Brief — realtime-variety-render-e2
**Agent:** solo  
**Date:** 2026-05-22  
**Status:** COMPLETE — milestone already fully implemented (commit `42b6c17`)

---

## 1. TL;DR

The entire `realtime-variety-render-e2` scope (CAND-8) is already shipped: `Surface.typical_ms: int = 0` field exists at `surfaces.py:68`, the three Hanson generators carry measured values (39/11/18 ms), `should_render_on_drag()` predicate lives at `surfaces.py:82-99`, `app.py:497-530` wires `params_preview_changed` to `_on_params_preview_changed` with the `should_render_on_drag` guard, and 10 pure-Python tests in `tests/test_typical_ms.py` pass clean. The orchestrator should advance the milestone to `complete` status with no implementation work needed.

---

## 2. Codebase Audit

### Surface dataclass definition
- `surfaces.py:42-51` — `@dataclass(frozen=True) class ParamSpec`
- `surfaces.py:54-71` — `@dataclass class Surface` — NOT frozen (AI-8 confirmed)
- `surfaces.py:59-68` — `typical_ms: int = 0` field added by e2-s1, comment `# realtime-variety-render-e2-s1 (CAND-8)`
- `surfaces.py:74-79` — `FAST_RENDER_THRESHOLD_MS = 80`
- `surfaces.py:82-99` — `should_render_on_drag(surface)` predicate; pure function, no Qt

### The 3 Hanson generator entries in VARIETIES
- `surfaces.py:1193-1196` — `"Hanson quintic  [Fig. 1]"`: `typical_ms=39`
- `surfaces.py:1198-1201` — `"Hanson cubic torus  [Fig. 2]"`: `typical_ms=11`
- `surfaces.py:1203-1206` — `"Hanson asymmetric (5,3)  [Fig. 3]"`: `typical_ms=18`
- Comment at `surfaces.py:1188-1192` documents the measurement methodology (off-screen, pv.OFF_SCREEN=True, perf_counter, median of 7 runs at default params)

### Hanson generator functions
- `surfaces.py:810-824` — `calabi_yau_quintic(alpha, grid, xi_max)`; calls `_hanson_cross_section(n=5, n2=5, ...)`
- `surfaces.py:837-848` — `calabi_yau_cubic(alpha, grid, xi_max)`; calls `_hanson_cross_section(n=3, n2=3, ...)`
- `surfaces.py:861-873` — `calabi_yau_asymmetric(alpha, grid, xi_max)`; calls `_hanson_cross_section(n=5, n2=3, ...)`
- `surfaces.py:715` — `_hanson_cross_section` private helper (parametric path)
- `surfaces.py:800-807` — Hanson normals: `cell_normals=True, consistent_normals=False, auto_orient_normals=False` (AI-7 compliant, confirmed untouched by e2)

### Render dispatch path in app.py (post-e4, post-e2)
- `app.py:50` — imports `should_render_on_drag` from `surfaces`
- `app.py:262-268` — `params_panel.params_changed.connect(_on_params_changed)` + `params_panel.params_preview_changed.connect(_on_params_preview_changed)`
- `app.py:490-495` — `_on_params_changed` (release) — unconditional `_render_current(reset_camera=False)` for all surfaces
- `app.py:497-530` — `_on_params_preview_changed` (drag-tick debounced) — routes via `should_render_on_drag(self._current_surface)`; slow surfaces are no-ops
- `app.py:529-530` — guard: `if should_render_on_drag(self._current_surface): self._render_current(reset_camera=False)`
- `app.py:521-527` — AI-6 comment: "When e4 adds CAND-3's coarse-LOD path, that path's drag-tick branch MUST guard on `should_render_on_drag(surface)` / `surface.typical_ms > 0` and skip Hanson"
- `app.py:588` — `_render_current(*, reset_camera)` — submit-only, QThreadPool dispatch

### Debounce wiring (e1 plumbing + e2 wiring)
- `parameters_panel.py:47` — `params_preview_changed = Signal(dict)`
- `parameters_panel.py:55-64` — `self._debouncer = Debouncer(self._on_debounced_tick)` with 80 ms interval
- `parameters_panel.py:260-272` — `_on_debounced_tick` emits `params_preview_changed.emit(self.values())`
- `parameters_panel.py:348-359` — grid panel's drag events relayed to `params_preview_changed`

### Re-entrancy guard (AI-9)
- `app.py:166-185` — `self._computing` + `self._pending_render` — in-flight guard
- `app.py:612-616` — `_render_current`: if `_computing`, set `_pending_render = True` and return
- `app.py:824-836` — finally block: clear `_computing`; if `_pending_render`, schedule `QTimer.singleShot(0, ...)` catch-up

### e4 coarse-LOD guard
- The e4 coarse-LOD path (CAND-3) has NOT been shipped as of the code surveyed. The comment at `app.py:524-527` pre-documents the required guard for when it does land.

### Tests
- `tests/test_typical_ms.py` — 10 tests, all passing (verified: `pytest tests/test_typical_ms.py` → 10 passed 0.54s)
- Full suite: 380 tests, all passing (verified: `pytest tests/` → 380 passed 9.03s)

---

## 3. External Sources Reviewed

| Source | URL | Key finding | Relevance |
|---|---|---|---|
| Final capability-scout report | `.claude/notes/capability-scouts/realtime-variety-render/artifacts/final-report.md` | CAND-8 spec: `typical_ms: int`, threshold 80 ms, no CAND-4 dependency (CC-3 correction) | Primary spec source |
| App invariants | `.claude/references/app-invariants.md` | AI-6 (parametric skip), AI-7 (Hanson normals), AI-8 (Surface not frozen), AI-9 (re-entrancy) | Confirmed all respected |
| CONTEXT.md | `./CONTEXT.md §4.3, §4.4, §5.3` | Hanson math, async dispatch architecture, normals fix history | Architecture ground truth |

---

## 4. Recommended Approach

**The milestone is complete.** The recommended action for the orchestrator is:

1. Verify the 10 tests in `tests/test_typical_ms.py` pass (they do — confirmed above).
2. Verify the 3 acceptance signals are met:
   - `Surface.typical_ms: int = 0` field exists — YES (`surfaces.py:68`)
   - All 3 Hanson generators have non-zero values (39, 11, 18 ms) — YES (`surfaces.py:1196, 1201, 1206`)
   - All implicit generators default to 0 — YES (confirmed by `test_implicit_surfaces_keep_typical_ms_zero`)
   - Dispatch guard `should_render_on_drag` wired to `_on_params_preview_changed` — YES (`app.py:529`)
   - AI-7 normals pattern untouched — YES (`surfaces.py:802-805`)
3. Advance milestone `state.json` from `research-running` to `complete`.

If the orchestrator wants to also verify the off-screen render acceptance signal, the recipe is:
```python
import pyvista as pv
pv.OFF_SCREEN = True
from surfaces import calabi_yau_quintic, calabi_yau_cubic, calabi_yau_asymmetric
for fn, kwargs in [
    (calabi_yau_quintic, {"alpha": 0.3, "grid": 41, "xi_max": 1.2}),
    (calabi_yau_cubic, {"alpha": 1.0, "grid": 33, "xi_max": 0.8}),
    (calabi_yau_asymmetric, {"alpha": 0.5, "grid": 35, "xi_max": 1.5}),
]:
    mesh = fn(**kwargs)
    assert mesh.n_points > 0
    p = pv.Plotter(off_screen=True, window_size=(440, 380))
    p.add_mesh(mesh)
    p.show(screenshot=f"/tmp/{fn.__name__}_nondefault.png")
```

---

## 5. Alternatives Considered

- **`fast: bool` field instead of `typical_ms: int`** — rejected (final-report CAND-8 Challenger MINOR): a bare bool discards quantitative data needed for future routing tuning; `int` carries the measurement and allows future threshold adjustment without code changes.
- **Implement in-line in `_on_params_preview_changed` without a free predicate** — rejected: pulling `should_render_on_drag` out as a pure free function is required for AI-2 (Qt-free tests) compliance; the dispatch decision must be unit-testable without constructing QApplication.
- **Wait for e4 (CAND-4 background worker) before wiring** — rejected: the final-report CC-3 correction explicitly removed the CAND-4 dependency; CAND-8 ships independently because Hanson already generates in 11-39 ms (well under 80 ms budget).

---

## 6. Decisions (for implementation reference — already resolved)

| Decision | Choice made | Justification |
|---|---|---|
| Threshold value | `FAST_RENDER_THRESHOLD_MS = 80` | 80 ms is the round-trip budget from the acceptance signal; Hanson values (11-39 ms) have 2-7x headroom |
| Field type | `typical_ms: int = 0` | Quantitative; future routing tuning doesn't require code changes |
| e4 coarse-LOD guard | Comment at `app.py:524-527` pre-documents the guard; guard is NOT needed in e2 because e4 is unshipped | e4 guard will be `if should_render_on_drag(surface): skip_coarse_path` |

---

## 7. Test Plan (all 4 tests are already implemented and passing)

| Test | File:line | Status |
|---|---|---|
| `typical_ms` field exists with default 0 | `tests/test_typical_ms.py:53-60` | PASS |
| All 3 Hanson generators have non-zero `typical_ms` | `tests/test_typical_ms.py:63-71` | PASS |
| All non-Hanson generators have `typical_ms == 0` | `tests/test_typical_ms.py:74-83` | PASS |
| `should_render_on_drag` predicate correct across boundary conditions | `tests/test_typical_ms.py:98-135` | PASS (7 cases) |

---

## 8. AI-1..AI-15 Conflict Scan

| Invariant | Status | Notes |
|---|---|---|
| AI-1 (PySide6 + PyVista stack) | GREEN | No renderer changes; field addition is pure Python |
| AI-2 (Qt-free tests) | GREEN | `tests/test_typical_ms.py` imports only `surfaces.py`; no QApplication |
| AI-3 (off-screen via `pv.OFF_SCREEN`) | GREEN | Not touched by e2; off-screen recipe in §4 above is AI-3 compliant |
| AI-4 (clip_scalar not clip_box) | GREEN | Not touched |
| AI-5 (clip_scalar `scalars=` kwarg) | GREEN | Not touched |
| AI-6 (parametric vs implicit pipeline) | GREEN | Hanson surfaces stay on `_grid_to_polydata` path; `_on_params_preview_changed` only changes WHEN `generate()` is called, not HOW; pre-documents e4 guard at `app.py:524-527` |
| AI-7 (Hanson normals: cell_normals=True, consistent_normals=False) | GREEN | `surfaces.py:802-805` confirmed untouched; e2 adds no mesh-generation code |
| AI-8 (Surface dataclass non-frozen) | GREEN | `@dataclass` (no `frozen=True`) confirmed at `surfaces.py:54`; trailing defaulted field is safe |
| AI-9 (re-entrancy guard `_computing`) | GREEN | `_on_params_preview_changed` calls `_render_current` which respects `_computing` guard; at most one worker in flight + one catch-up queued |
| AI-10 (raw mesh cached) | GREEN | Not touched; `_on_params_preview_changed` triggers a fresh generate only for fast surfaces, which is correct behavior |
| AI-11 (fully-qualified Qt enums) | GREEN | No new Qt code added |
| AI-12 (WCAG AA contrast) | GREEN | No UI text added |
| AI-13 (6-digit hex) | GREEN | No color strings added |
| AI-14 (generator returns PolyData or ValueError) | GREEN | Generator contract unchanged; e2 adds no generator code |
| AI-15 (math honesty) | GREEN | No new variety or figure added; existing Hanson tooltips unchanged |

---

## 9. Estimated Diff Size

The shipped diff (commit `42b6c17`) touches:
- `surfaces.py`: ~25 LOC (dataclass field + FAST_RENDER_THRESHOLD_MS constant + `should_render_on_drag` function + 4 `typical_ms=N` registry entries)
- `app.py`: ~15 LOC (import + `_on_params_preview_changed` signal connection + handler body)
- `tests/test_typical_ms.py`: ~135 LOC (new test file, 10 tests)
- **Total: ~175 LOC across 3 files**

---

## 10. AI-15 Disclaimers

No new variety or figure was proposed or implemented in this milestone. The Hanson cross-sections already carry the correct `"Hanson parametric cross-section"` framing (2D real shadow of CY3). No new tooltip text needed.

---

## 11. Open Questions

None. The milestone is implemented and all acceptance signals are satisfied.

---

## References

- `surfaces.py:54-71` — Surface dataclass + typical_ms field
- `surfaces.py:74-99` — FAST_RENDER_THRESHOLD_MS + should_render_on_drag predicate
- `surfaces.py:715-807` — _hanson_cross_section implementation + normals (AI-7)
- `surfaces.py:810-883` — 3 Hanson generator functions
- `surfaces.py:1188-1206` — VARIETIES registry Calabi-Yau entries with typical_ms values
- `app.py:50` — should_render_on_drag import
- `app.py:263-268` — signal wiring
- `app.py:490-530` — _on_params_changed + _on_params_preview_changed handlers
- `app.py:588-837` — _render_current + _on_mesh_ready (re-entrancy)
- `parameters_panel.py:47,55-64,260-272,348-359` — params_preview_changed signal + debounce
- `tests/test_typical_ms.py` — 10 tests, all passing
- `.claude/notes/capability-scouts/realtime-variety-render/artifacts/final-report.md §3 rank-4` — CAND-8 original spec
- Git commit `42b6c17` — `feat(realtime-variety-render-e2): Hanson parametric continuous-drag fast-path`
