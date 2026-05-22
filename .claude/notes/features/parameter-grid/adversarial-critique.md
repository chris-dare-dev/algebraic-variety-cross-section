# Adversarial critique — 2D/3D parameter-grid feature

**Date:** 2026-05-21
**Reviewer:** adversarial Sonnet 4.6 (read-only)
**Scope:** uncommitted working-tree implementation (`parameter_grid.py`, `parameter_grid_panel.py`, `parameters_panel.py` diff, `styles.py` diff, `tests/test_parameter_grid.py`)

---

## Executive summary

The implementation is structurally solid: the signal flow correctly honors INT-NO-1 (one render per dot-release, no mid-drag renders), the `_computing` guard is not bypassed, AI-2 (Qt-free tests) is respected, AI-11 (fully-qualified enums) is satisfied throughout, and all hex tokens are 6-digit. **One HIGH bug is real and user-facing**: the axis labels on the 3D grid become wrong the moment the user switches away from the XY drag plane — the vertical axis label reads the Y parameter name while the dot is actually driving the Z parameter. Two MEDIUM bugs round out the critical surface: a no-op `setRenderHints` call and an `AxisAssignment` type signature that promises immutability it cannot deliver. Testing covers the easy structural cases well but misses every degenerate edge (zero step, zero span, zero-length scene) and the hard-to-reach 3D-specific paths. Finding counts: 0 CRITICAL, 1 HIGH, 4 MEDIUM, 5 LOW. Top themes: (1) 3D drag-plane UX is broken by static axis labels, (2) the test suite skips degenerate inputs that the pure module handles specially.

---

## Axis 1 — Documentation

### MEDIUM — `AxisAssignment.frozen=True` with mutable `list` fields is semantically misleading

**Where:** `parameter_grid.py:170-181`

**Evidence:**
```python
@dataclass(frozen=True)
class AxisAssignment:
    axes: list[ParamSpec]
    residual: list[ParamSpec]
```
`frozen=True` prevents reassignment (`aa.axes = [...]` raises `FrozenInstanceError`), but the lists themselves are mutable — any caller can do `aa.axes.append(x)` without error. The docstring says the result is an "ordered list" but does not warn that the frozen guarantee is incomplete.

**Why it matters:** Any future caller that expects `AxisAssignment` to be fully immutable (e.g. caching, hashing) will be surprised. The type hint also claims `list[ParamSpec]` where `tuple[ParamSpec, ...]` would be honest.

**Suggested fix:** Change field types to `tuple[ParamSpec, ...]` and update every call site's list-to-tuple conversion, or remove `frozen=True` and document that the object is "logically read-only by convention."

---

### MEDIUM — `design.md` §5 misattributes the canonical value store

**Where:** `.claude/notes/features/parameter-grid/design.md:111-112`

**Evidence:** The doc says "One source of truth: a `dict[str,float]` of current values held by `ParametersPanel`." In fact, `ParametersPanel` holds no dict; in grid mode the canonical store is `ParameterGridPanel._values`, and `ParametersPanel.values()` delegates to `_grid_panel.values()`.

**Why it matters:** A maintainer reading the design doc would look for the dict in `ParametersPanel` and not find it, leading to confusion when debugging value-drift issues.

**Suggested fix:** Update §5 to say "…held by `ParameterGridPanel._values` in grid mode, or computed from the slider ticks in slider mode."

---

### LOW — `_spec_by_name` has no docstring and raises `StopIteration`, not a domain error

**Where:** `parameter_grid_panel.py:477-478`

**Evidence:**
```python
def _spec_by_name(self, name: str) -> ParamSpec:
    return next(s for s in self._specs if s.name == name)
```
No docstring. If `name` is not in `_specs` (stale `_axis_names` after a fast variety switch), `next()` raises bare `StopIteration` rather than a meaningful `ValueError("unknown axis param: ...")`.

**Why it matters:** `StopIteration` escaping a method is a well-known Python gotcha that silently converts to `RuntimeError` in some generator contexts. A domain `ValueError` with the bad name attached is far easier to debug.

**Suggested fix:** Add `default=None` and raise `ValueError(f"no ParamSpec named {name!r}")` explicitly, plus a one-line docstring.

---

### LOW — `_draw_iso_box` docstring makes a claim that is not fully implemented

**Where:** `parameter_grid_panel.py:337-341`

**Evidence:** The docstring says "The front face is the active 2D drag plane." That is true only when `_drag_plane == 'XY'`. For `XZ` or `YZ`, the dot moves on the visual front face but drives different parameter pairs — the front face is no longer "the XZ plane" or "the YZ plane". The docstring does not acknowledge this mismatch.

**Why it matters:** A maintainer reading the docstring would expect the scene to update when the drag plane changes. The mismatch between the docstring's promise and the actual behavior (see Axis 2 HIGH finding) obscures the bug.

**Suggested fix:** Rewrite: "The grid is drawn on a fixed front face. The drag-plane selector controls which parameter pair the dot drives, not which face is rendered."

---

### LOW — Mouse event overrides lack return-type annotations

**Where:** `parameter_grid_panel.py:88-102`

**Evidence:**
```python
def mousePressEvent(self, event):  # noqa: N802 (Qt override)
def mouseMoveEvent(self, event):   # noqa: N802 (Qt override)
def mouseReleaseEvent(self, event):# noqa: N802 (Qt override)
```
No `event` type annotation (`QGraphicsSceneMouseEvent`) and no `-> None`. The existing codebase styles Qt overrides with minimal annotation in practice, but consistency with the rest of the file (which has full hints on every public method) would be better.

**Suggested fix:** Add `event: QGraphicsSceneMouseEvent` parameter type and `-> None` return. Import `QGraphicsSceneMouseEvent` from `PySide6.QtWidgets`.

---

## Axis 2 — Downstream bugs / errors

### HIGH — Axis labels are wrong for non-XY drag planes in 3D mode

**Where:** `parameter_grid_panel.py:373-394`, `parameter_grid_panel.py:614-616`

**Evidence:**
`_draw_axis_labels` places the label for `_axis_names[0]` on the horizontal axis and `_axis_names[1]` on the vertical axis unconditionally. `_on_drag_plane_changed` only updates `_drag_plane` and repositions the dot — it does not redraw the scene or refresh labels:

```python
def _on_drag_plane_changed(self, plane: str) -> None:
    self._drag_plane = plane
    self._sync_dot_to_values()  # repositions dot, but no label update
```

When `_drag_plane = 'XZ'`, `_plane_axes()` returns `(0, 2)`, so dot.y drives `_axis_names[2]` (the Z parameter). But the label on the vertical axis continues to show `_axis_names[1]` (the Y parameter). For `YZ`, dot.x drives the Y parameter but the horizontal label shows the X parameter name.

A user in XZ drag-plane mode will read "Alpha" on the vertical axis while the dot is actually controlling "Beta" (the Z parameter). The computed values are numerically correct, but the displayed axis names are actively wrong.

**Why it matters:** The user cannot tell which parameter each axis drives. This defeats the primary purpose of the labeled grid.

**Suggested fix:** In `_on_drag_plane_changed`, call `_draw_axis_labels()` after clearing the existing label items and updating `_drag_plane`. A lighter fix: redraw only the two axis labels using the result of `_plane_axes()` to select the correct `_axis_names` indices.

---

### MEDIUM — `setRenderHints(self._view.renderHints())` is a no-op

**Where:** `parameter_grid_panel.py:195`

**Evidence:**
```python
self._view.setRenderHints(self._view.renderHints())
```
This reads the view's current render hints and immediately writes them back, changing nothing. The intent was almost certainly to enable antialiasing on the `QGraphicsView` so gridlines and the dot edge render smoothly.

**Why it matters:** The dot and grid lines are rendered without antialiasing, appearing jagged at typical screen densities. The fix is one line; its absence is invisible until you look at the output at 96+ DPI.

**Suggested fix:** Replace with:
```python
from PySide6.QtGui import QPainter
self._view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
```

---

### MEDIUM — Residual slider construction divides by `spec.step` without a zero guard

**Where:** `parameter_grid_panel.py:445`, `parameter_grid_panel.py:564`

**Evidence:**
```python
# line 445
ticks = max(1, int(round((spec.maximum - spec.minimum) / spec.step)))
# line 564
slider.setValue(int(round((cur - spec.minimum) / spec.step)))
```
`parameter_grid.py:snap_to_step` defensively handles `spec.step <= 0` (line 88), but the residual slider construction and sync paths divide by `spec.step` without the same guard. `ParamSpec.step` defaults to `0.01` and no existing spec sets it to `0`, so this does not crash today. However, `ParamSpec` is a public dataclass and the step field has a default — a future caller could construct `ParamSpec("x", "X", 0.0, 1.0, 0.5, step=0)` and trigger `ZeroDivisionError` in `_build_residual_row` and `_sync_residual_sliders`, crashing the panel during a variety switch.

**Why it matters:** The pure module protects itself but the Qt layer does not, creating an inconsistency and a latent crash path for any future spec with `step=0`.

**Suggested fix:** Add `if spec.step <= 0: spec.step = 1e-9  # degenerate guard` (or skip the slider and show a fixed-value label) at the top of `_build_residual_row`. Mirror `snap_to_step`'s guard pattern.

---

### LOW — Dot is unconstrained within the scene; visually escapes the grid boundary

**Where:** `parameter_grid_panel.py:83`

**Evidence:**
```python
self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsMovable, True)
```
No `itemChange` override constrains the dot's position to `[0, _GRID_SIZE] × [0, _GRID_SIZE]`. Dragging briskly to the corner allows the dot to enter the margin area or exit the scene rect entirely. The computed parameter value clamps correctly (via `scene_to_norm`), but the dot visually sits outside the grid, which looks broken.

**Why it matters:** The clamping gap is purely visual — users will think the dot is "stuck" outside the grid or that the control is broken.

**Suggested fix:** Override `itemChange` with `GraphicsItemChange.ItemPositionChange` and return `QPointF(clamp(pos.x(), 0, _GRID_SIZE), clamp(pos.y(), 0, _GRID_SIZE))`.

---

### LOW — `_on_axis_param_changed` triggers a full `_rebuild_scene()` even when the selected param is unchanged

**Where:** `parameter_grid_panel.py:593-612`

**Evidence:** When the user opens and closes an axis combo without changing selection, `currentIndexChanged` fires with the same index, `chosen == self._axis_names[axis]`, no swap happens, but `_rebuild_scene()` and `_rebuild_residual_sliders()` are called unconditionally. This tears down and reconstructs the entire `QGraphicsScene`.

**Why it matters:** Scene reconstruction is not free — it deletes and recreates all `QGraphicsItem`s, resets the dot position, and repaints. The visual flicker is noticeable.

**Suggested fix:** Add an early-return guard: `if chosen == self._axis_names[axis]: return`.

---

## Axis 3 — Testing

### MEDIUM — Degenerate-input branches in `parameter_grid.py` are entirely untested

**Where:** `parameter_grid.py:59`, `parameter_grid.py:88`, `parameter_grid.py:110`; `tests/test_parameter_grid.py` (missing tests)

**Evidence:** Three defensive guards have zero test coverage:

1. `value_to_norm` line 59: `if span <= 0: return 0.0` — triggered when `spec.maximum == spec.minimum`. No test constructs such a `ParamSpec`.
2. `snap_to_step` line 88: `if spec.step <= 0: return clamp_value(value, spec)` — no test uses `step=0` or `step<0`.
3. `scene_to_norm` line 110: `if length <= 0: return 0.0` — no test passes `length=0`.

These are the exact edge cases identified in the design brief ("`ParamSpec` where `maximum == minimum`", division-by-zero) as high-risk. The pure module handles them, but without tests, a future refactor could silently drop the guard.

**Why it matters:** The guards exist because these inputs are plausible (future user-constructed `ParamSpec`, or a scene resized to zero). Without tests, they are unreachable by the CI gate and can regress silently.

**Suggested fix:** Add three parametrized tests in `test_parameter_grid.py`:
- `test_degenerate_span`: `ParamSpec("x","X",0.5,0.5,0.5)` → `value_to_norm` returns `0.0`.
- `test_zero_step`: `ParamSpec("x","X",0.0,1.0,0.5,step=0)` → `snap_to_step` returns clamped value.
- `test_zero_scene_length`: `scene_to_norm(5.0, 0.0)` returns `0.0`.

---

### MEDIUM — `FANO_TWO_QUADRICS_PARAMS` absent from the round-trip parametrize set

**Where:** `tests/test_parameter_grid.py:35-37`

**Evidence:**
```python
_ROUND_TRIP_SPECS = (
    FERMAT_PARAMS + KUMMER_PARAMS + CALABI_YAU_QUINTIC_PARAMS + ENRIQUES_FIGURE_2_PARAMS
)
```
`FANO_TWO_QUADRICS_PARAMS` (4 params) is used in `test_grid_enabled` and `test_default_axis_count` but not in the `test_value_scene_round_trip` or `test_scene_past_edge_clamps_to_bounds` parametrize sets. This is the surface family most likely to exercise the 4-param residual-split path in practice, and its `ParamSpec` geometry (step sizes, ranges) may differ from Fermat.

**Why it matters:** If a Fano Two-Quadrics `ParamSpec` has unusual step or range that triggers float rounding differently, the round-trip test would miss it.

**Suggested fix:** Add `FANO_TWO_QUADRICS_PARAMS` to `_ROUND_TRIP_SPECS`.

---

### LOW — 3D-mode Z-axis value mapping is untested

**Where:** `tests/test_parameter_grid.py` (missing); `parameter_grid_panel.py:480-488`

**Evidence:** No test exercises the `_plane_axes()` logic or validates that a 3-axis assignment correctly maps scene coordinates to the third parameter. The 3D path uses the same `value_to_scene` / `scene_to_value` primitives (already tested), so a round-trip bug is unlikely — but the axis-index mapping `{"XY":(0,1), "XZ":(0,2), "YZ":(1,2)}` is untested, and the label-sync bug (see Axis 2 HIGH) went undetected partly because there is no test that checks which parameter the vertical axis drives in each plane.

**Why it matters:** The 3D drag-plane path is the riskiest new code path (most novel, most user-visible) and has zero direct test coverage in the pure module.

**Suggested fix:** Extract `_plane_axes()` logic into `parameter_grid.py` as `plane_axes(plane: str, axis_count: int) -> tuple[int, int]` and add tests for all three planes. This also resolves the AI-2 testability leak.

---

### LOW — `test_assign_axes_rejects_too_few_params` tests a degenerate duplicate, not a true too-few case

**Where:** `tests/test_parameter_grid.py:187-190`

**Evidence:**
```python
def test_assign_axes_rejects_too_few_params() -> None:
    one = [ParamSpec("a", "A", 0.0, 1.0, 0.5)]
    with pytest.raises(ValueError):
        pg.assign_axes(one, ["a", "a"])  # duplicate check fires first
```
The duplicate guard (`len(axis_names) != len(set(axis_names))`) fires before the too-few-params guard, so this test is actually verifying duplicate rejection, not too-few-params rejection. A 2-param surface requesting 3 axes (a legitimate too-few case) is untested.

**Suggested fix:** Add a companion test: `assign_axes(two_params, ["a", "b", "a"])` → duplicate; `assign_axes(two_params, ["a", "b", "x"])` → unknown param; and specifically: `assign_axes(two_params, ["a", "b", "b_extra"])` where `b_extra` is not in the spec list.

---

## Axis 4 — Code structure / nesting

### MEDIUM — `_build_residual_row` duplicates `ParametersPanel._build_row`

**Where:** `parameter_grid_panel.py:426-471`; `parameters_panel.py:185-241`

**Evidence:** Both methods build a `QVBoxLayout` containing a header `QHBoxLayout` (param label left, value label right), a `QSlider`, and a range-label row. The only structural difference is that `_build_residual_row` omits the `spec.description` label and wires to `_on_residual_value_changed` / `_on_residual_released` instead of `_on_value_changed` / `_on_slider_released`. The tick-to-value formulas and formatting are identical.

**Why it matters:** When `ParametersPanel._build_row` is updated (tooltip format, layout spacing, accessibility label, etc.), `_build_residual_row` must be updated separately and in sync. This is a maintenance coupling that will diverge.

**Suggested fix:** Extract a `_build_slider_row(spec, on_change, on_release)` factory function into a shared helper (either a standalone function in a new `ui_helpers.py`, or a static method on `ParametersPanel` that `ParameterGridPanel` imports). The two-phase signal discipline is compatible — the factory just takes callback arguments.

---

### LOW — `_format_value` is duplicated verbatim across two classes

**Where:** `parameter_grid_panel.py:629-637`; `parameters_panel.py:329-337`

**Evidence:** Both classes define an identical `@staticmethod _format_value(value, spec)` with exactly the same three-branch `if spec.step >= 1 / elif spec.step >= 0.1 / else` logic and the same `f"{text}{spec.suffix}"` return. This is a textbook DRY violation.

**Why it matters:** If the formatting precision needs to change (e.g., a 4-decimal step size is introduced), both copies must be updated.

**Suggested fix:** Move `_format_value` to `parameter_grid.py` (which is already the pure utility module) or to `styles.py` / a shared `formatting.py`. It has no Qt dependency and is already Qt-free.

---

### LOW — `_plane_axes()` is Qt-layer logic that belongs in the pure module

**Where:** `parameter_grid_panel.py:480-488`

**Evidence:**
```python
def _plane_axes(self) -> tuple[int, int]:
    if self._axis_count == 2:
        return 0, 1
    return {"XY": (0, 1), "XZ": (0, 2), "YZ": (1, 2)}[self._drag_plane]
```
This is a pure mapping from a string and an integer to a tuple of integers — no Qt involved. Placing it in `ParameterGridPanel` (the Qt layer) means it cannot be tested without a `QApplication` (AI-2). Extracting it to `parameter_grid.py` as `plane_axes(plane: str, axis_count: int) -> tuple[int, int]` would add testable coverage of the 3D axis-index mapping at zero cost.

**Suggested fix:** Move to `parameter_grid.py`, add a `ValueError` for unknown plane strings, and add tests.

---

### LOW — `_axis_count_combo` internal state is inconsistent for 1-param surfaces

**Where:** `parameter_grid_panel.py:232-235`

**Evidence:**
```python
idx = self._axis_count_combo.findData(self._axis_count)
self._axis_count_combo.setCurrentIndex(idx if idx >= 0 else 0)
```
When `_axis_count = 0` (a 1-param surface triggering `set_specs`), `findData(0)` returns `-1` (the combo only contains `2` and `3`), so `setCurrentIndex(0)` is called, leaving the combo showing "2D (2 axes)" while `self._axis_count = 0`. The panel is hidden, so there is no visual impact, but querying `self._axis_count_combo.currentData()` would return `2`, not `0`. This is a hidden state inconsistency that could mislead debugging.

**Suggested fix:** When `axis_count < 2`, skip the combo update entirely (it is hidden and irrelevant): `if self._axis_count >= 2: ...`.

---

## What was done well

- **Signal discipline is correct end-to-end.** `_on_drag_move` updates readouts only; `_on_drag_release` emits exactly once; `ParametersPanel._on_grid_params_changed` relays through the existing `params_changed` signal without adding a second render path. The `_computing` guard in `app.py` is fully respected — no new `processEvents()` is introduced.
- **AI-2 compliance is genuine.** `parameter_grid.py` has zero PySide6/pyvista imports. The test file imports only the pure module. The `_plane_axes` leak is minor and isolated.
- **AI-11 compliance is complete.** Every Qt enum in the new code is fully qualified (`Qt.CursorShape.OpenHandCursor`, `Qt.Orientation.Horizontal`, `QGraphicsEllipseItem.GraphicsItemFlag.ItemIsMovable`, etc.).
- **AI-13 compliance is complete.** All seven new `PALETTE_LIGHT` tokens are 6-digit hex. `QColor` wrappers are built at module level from the palette tokens; no raw hex string appears in a QPen/QBrush/setStyleSheet call.
- **Variety-switch teardown is clean.** The 4-param → 0-param switch path is correctly handled: the toggle is disabled with `blockSignals`, the grid panel is explicitly hidden, and the early return prevents `_apply_view_mode` from being called with stale state. The 4-param → 1-param path similarly lands in a correct state.
- **State coherence across toggle is correct.** Toggle to grid: slider values are pushed to the grid dot. Toggle back: grid values are pulled into sliders. Reset in grid mode: both views are updated and `params_changed` is emitted once. No desync path was found.

---

## Recommended remediation order

1. **(HIGH / S)** Fix axis labels for non-XY drag planes: in `_on_drag_plane_changed`, redraw axis labels using `_plane_axes()` to select the correct `_axis_names` indices for horizontal and vertical. (`parameter_grid_panel.py:614`)

2. **(MEDIUM / XS)** Fix the `setRenderHints` no-op: replace with `self._view.setRenderHint(QPainter.RenderHint.Antialiasing, True)`. (`parameter_grid_panel.py:195`)

3. **(MEDIUM / S)** Add degenerate-input tests: `step=0`, `span=0`, `length=0` branches in `parameter_grid.py` that currently execute with zero test coverage. (`tests/test_parameter_grid.py`)

4. **(MEDIUM / S)** Add zero-step guard to residual slider construction: mirror `snap_to_step`'s `if spec.step <= 0` check in `_build_residual_row` and `_sync_residual_sliders`. (`parameter_grid_panel.py:445`, `564`)

5. **(MEDIUM / M)** Eliminate `_build_residual_row` / `_build_row` duplication: extract a shared `_build_slider_row(spec, on_change, on_release)` factory. (`parameter_grid_panel.py:426`, `parameters_panel.py:185`)

6. **(MEDIUM / S)** Fix `AxisAssignment.frozen=True` + mutable `list` mismatch: use `tuple[ParamSpec, ...]` or remove `frozen=True`. (`parameter_grid.py:170`)

7. **(LOW / XS)** Move `_format_value` to `parameter_grid.py` and delete the duplicate in `parameter_grid_panel.py`. (`parameter_grid_panel.py:629`, `parameters_panel.py:329`)

8. **(LOW / S)** Move `_plane_axes()` logic to `parameter_grid.py` as `plane_axes(plane, axis_count)` and add tests. (`parameter_grid_panel.py:480`)

9. **(LOW / XS)** Add `FANO_TWO_QUADRICS_PARAMS` to `_ROUND_TRIP_SPECS`. (`tests/test_parameter_grid.py:35`)

10. **(LOW / XS)** Add dot-position constraint via `itemChange` override to prevent the dot from escaping the grid boundary visually. (`parameter_grid_panel.py:83`)

---

## Remediation status (post-critique)

**Date:** 2026-05-21 · **Tests:** 288 passed (was 236; +52 net — see below).

All 10 findings addressed:

| ID | Severity | Status | Resolution |
|----|----------|--------|------------|
| Axis-2 HIGH | HIGH | FIXED | `_on_drag_plane_changed` now rebuilds the scene; `_draw_axis_labels` rewritten to use `pg.plane_axes` / `pg.held_axis` so horizontal/vertical/held labels track the active drag plane. Held axis is marked "(held)". Headless smoke confirms correct labels for XY/XZ/YZ. |
| Axis-2 MEDIUM (setRenderHints) | MEDIUM | FIXED | Replaced the no-op with `setRenderHint(QPainter.RenderHint.Antialiasing, True)`. |
| Axis-2 MEDIUM (zero-step) | MEDIUM | FIXED | Residual rows now build via the shared factory which uses `pg.tick_count`/`pg.value_to_tick` — both guard `step <= 0`. `_sync_residual_sliders`/`_collect_values` routed through the same guarded helpers. |
| Axis-3 MEDIUM (degenerate tests) | MEDIUM | FIXED | Added `test_value_to_norm_degenerate_span_returns_zero`, `test_snap_to_step_zero_step_clamps_without_raising`, `test_scene_to_norm_zero_length_returns_zero`, `test_tick_helpers_guard_zero_step`. |
| Axis-3 MEDIUM (FANO round-trip) | MEDIUM | FIXED | `FANO_TWO_QUADRICS_PARAMS` added to `_ROUND_TRIP_SPECS`. |
| Axis-4 MEDIUM (`_build_residual_row` dup) | MEDIUM | FIXED | Extracted `ui_helpers.build_slider_row` factory; both `ParametersPanel._build_row` and `ParameterGridPanel._build_residual_row` now delegate to it (single source). |
| Axis-1 MEDIUM (`AxisAssignment` frozen+list) | MEDIUM | FIXED | Fields changed to `tuple[ParamSpec, ...]`; `assign_axes` returns tuples; `test_assign_axes_fields_are_tuples` added. |
| Axis-4 LOW (`_format_value` dup) | LOW | FIXED | Moved to `parameter_grid.format_value`; both panels delegate. |
| Axis-4 LOW (`_plane_axes` Qt-layer logic) | LOW | FIXED | Moved to `parameter_grid.plane_axes` (+ `held_axis`); panel method is a thin wrapper; `test_plane_axes_*` / `test_held_axis` added. |
| Axis-2 LOW (dot escapes grid) | LOW | FIXED | `_DraggableDot.itemChange` clamps `ItemPositionChange` to `[0, _GRID_SIZE]^2`; `ItemSendsGeometryChanges` flag set. Headless smoke confirms. |

Embedded LOW doc findings also resolved: `_spec_by_name` docstring + `ValueError` (no bare `StopIteration`); `_draw_iso_box` docstring corrected; mouse-event overrides given `QGraphicsSceneMouseEvent` / `-> None` annotations; `_on_axis_param_changed` early-return guard; `_axis_count_combo` 1-param guard; `design.md` §5 value-store attribution corrected; `_no_raw_hex` test extended.

**Cross-finding remediation regression test (M2-style):** `test_no_raw_hex_in_pyvista_color_kwargs_*` (already in `test_styles_palette.py` from the e2 milestone) continues to guard PyVista call sites.

**Known follow-up (out of scope for these 10 findings):** the grid feature predates the dark-mode milestone. `parameter_grid_panel.py` freezes `GRID_*` colors into `QColor` objects at module import, so the grid scene does not yet live-swap on a theme toggle. Dark-tuned `GRID_*` tokens were added to `PALETTE_DARK` for key-parity; a runtime dark-grid refresh is a tracked follow-up.
