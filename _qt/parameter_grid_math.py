"""parameter_grid — pure-Python coordinate math for the parameter-grid mode.

This module is intentionally **Qt-free and PyVista-free** (AI-2): it has no
``PySide6`` / ``pyvista`` imports at module top level, so every transform and
every assignment rule below is unit-testable without instantiating a
``QApplication`` or a VTK render window.

The Qt widget layer (``parameter_grid_panel.py``) imports from here; this
module never imports from there.

Concepts
--------
* **value**   — a parameter's real value, in ``[spec.minimum, spec.maximum]``.
* **norm**    — that value mapped to the unit interval ``[0.0, 1.0]``.
* **scene**   — a pixel coordinate along one axis of a ``QGraphicsScene``,
                in ``[0.0, length]``.

The grid dot's position is stored as scene coordinates by the widget; this
module converts in both directions and clamps so a drag past either end of an
axis maps to exactly the parameter's minimum or maximum.
"""

from __future__ import annotations

from dataclasses import dataclass

from varieties.types import ParamSpec

# Minimum number of parameters for grid mode to add anything. With 0 or 1
# parameter a grid is degenerate (no second axis), so the toggle is disabled.
MIN_GRID_PARAMS = 2

# The grid can host at most 3 axes (a 3D isometric box). Varieties with more
# parameters keep the surplus as residual sliders.
MAX_GRID_AXES = 3


# ---------------------------------------------------------------------------
# value <-> normalized <-> scene-coordinate transforms
# ---------------------------------------------------------------------------


def clamp_value(value: float, spec: ParamSpec) -> float:
    """Clamp *value* into ``[spec.minimum, spec.maximum]``."""
    if value < spec.minimum:
        return spec.minimum
    if value > spec.maximum:
        return spec.maximum
    return value


def value_to_norm(value: float, spec: ParamSpec) -> float:
    """Map a parameter *value* to the unit interval ``[0.0, 1.0]``.

    The result is clamped: a value outside ``[minimum, maximum]`` saturates at
    0.0 or 1.0 rather than extrapolating.
    """
    span = spec.maximum - spec.minimum
    if span <= 0:
        return 0.0
    norm = (value - spec.minimum) / span
    return min(1.0, max(0.0, norm))


def norm_to_value(norm: float, spec: ParamSpec) -> float:
    """Map a unit-interval coordinate *norm* back to a parameter value.

    *norm* is clamped to ``[0, 1]`` first, so the result is always within
    ``[spec.minimum, spec.maximum]``.

    The value is snapped to the nearest ``spec.step`` multiple so the grid
    produces exactly the same discrete value set the slider does — both views
    share one source of parameter truth and must agree bit-for-bit.
    """
    norm = min(1.0, max(0.0, norm))
    raw = spec.minimum + norm * (spec.maximum - spec.minimum)
    return snap_to_step(raw, spec)


def snap_to_step(value: float, spec: ParamSpec) -> float:
    """Snap *value* to the nearest ``spec.step`` grid point, then clamp.

    Mirrors the slider's behavior: ``QSlider`` stores integer ticks, so a
    slider can only ever land on ``minimum + k * step``. The grid dot is
    continuous, so without snapping the two views would disagree on values
    between tick boundaries.
    """
    if spec.step <= 0:
        return clamp_value(value, spec)
    ticks = round((value - spec.minimum) / spec.step)
    snapped = spec.minimum + ticks * spec.step
    return clamp_value(snapped, spec)


def norm_to_scene(norm: float, length: float, *, invert: bool = False) -> float:
    """Map a unit-interval coordinate to a pixel position on an axis.

    *length* is the axis length in scene units. With ``invert=True`` the
    mapping is flipped — used for the vertical axis of a ``QGraphicsScene``,
    whose Y grows downward while a parameter value grows upward.
    """
    norm = min(1.0, max(0.0, norm))
    if invert:
        norm = 1.0 - norm
    return norm * length


def scene_to_norm(scene: float, length: float, *, invert: bool = False) -> float:
    """Inverse of :func:`norm_to_scene` — pixel position back to ``[0, 1]``."""
    if length <= 0:
        return 0.0
    norm = scene / length
    norm = min(1.0, max(0.0, norm))
    if invert:
        norm = 1.0 - norm
    return norm


def value_to_scene(
    value: float, spec: ParamSpec, length: float, *, invert: bool = False
) -> float:
    """Composite transform: parameter value -> scene pixel coordinate."""
    return norm_to_scene(value_to_norm(value, spec), length, invert=invert)


def scene_to_value(
    scene: float, spec: ParamSpec, length: float, *, invert: bool = False
) -> float:
    """Composite transform: scene pixel coordinate -> parameter value.

    The result is clamped to ``[spec.minimum, spec.maximum]`` and snapped to
    the parameter step, so dragging the dot past the edge of the grid yields
    exactly the minimum / maximum value.
    """
    return norm_to_value(scene_to_norm(scene, length, invert=invert), spec)


# ---------------------------------------------------------------------------
# enable / disable predicate
# ---------------------------------------------------------------------------


def grid_enabled(specs: list[ParamSpec]) -> bool:
    """Return whether grid mode should be available for this parameter set.

    A grid needs at least two axes; with 0 or 1 parameter it adds nothing, so
    the Qt layer disables the toggle (with an explanatory tooltip).
    """
    return len(specs) >= MIN_GRID_PARAMS


def default_axis_count(specs: list[ParamSpec]) -> int:
    """How many axes the grid should default to for this parameter set.

    * 0 / 1 param  -> 0  (grid disabled; caller should check ``grid_enabled``)
    * exactly 2    -> 2  (2D grid)
    * 3 or more    -> 3  (3D grid; surplus params become residual sliders)
    """
    n = len(specs)
    if n < MIN_GRID_PARAMS:
        return 0
    return min(MAX_GRID_AXES, n)


# ---------------------------------------------------------------------------
# axis-assignment logic
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AxisAssignment:
    """The result of mapping parameters onto grid axes.

    ``axes`` is the ordered tuple of ``ParamSpec`` placed on the grid (length
    2 or 3). ``residual`` is every other ``ParamSpec`` — the params that stay
    as ordinary sliders alongside the grid; it preserves the original
    ``specs`` order.

    Both fields are ``tuple``, not ``list``: the dataclass is ``frozen=True``,
    and tuples make that immutability genuine.  A ``list`` field would still
    be mutable in place (``aa.axes.append(...)`` would silently succeed), so
    ``frozen`` would be only a half-promise.
    """

    axes: tuple[ParamSpec, ...]
    residual: tuple[ParamSpec, ...]


def assign_axes(specs: list[ParamSpec], axis_names: list[str]) -> AxisAssignment:
    """Map a chosen ordered list of parameter *names* onto the grid axes.

    Parameters
    ----------
    specs:
        Every ``ParamSpec`` for the current surface.
    axis_names:
        The parameter ``name`` chosen for each axis, in axis order
        (X, Y, [Z]). Length must be 2 or 3.

    Returns
    -------
    AxisAssignment
        ``axes`` follows ``axis_names`` order; ``residual`` preserves the
        original ``specs`` order for the params not placed on an axis.

    Raises
    ------
    ValueError
        * if ``axis_names`` is not length 2 or 3,
        * if the same parameter name appears on two axes,
        * if an axis name is not a known parameter,
        * if there are not enough parameters to fill the requested axes.
    """
    if len(axis_names) not in (2, MAX_GRID_AXES):
        raise ValueError(
            f"a grid hosts 2 or {MAX_GRID_AXES} axes; got {len(axis_names)}"
        )
    if len(axis_names) != len(set(axis_names)):
        raise ValueError(
            f"the same parameter cannot be assigned to two axes: {axis_names}"
        )
    if len(specs) < len(axis_names):
        raise ValueError(
            f"need at least {len(axis_names)} parameters for a "
            f"{len(axis_names)}-axis grid; surface has {len(specs)}"
        )

    by_name = {spec.name: spec for spec in specs}
    axes: list[ParamSpec] = []
    for name in axis_names:
        if name not in by_name:
            raise ValueError(f"unknown parameter for grid axis: {name!r}")
        axes.append(by_name[name])

    assigned = set(axis_names)
    residual = [spec for spec in specs if spec.name not in assigned]
    return AxisAssignment(axes=tuple(axes), residual=tuple(residual))


def default_axis_names(specs: list[ParamSpec], axis_count: int) -> list[str]:
    """Pick a sensible default parameter -> axis mapping.

    Takes the first *axis_count* parameters from *specs* in registry order.
    This makes the 2-param case (and the 3-param case) auto-assigned with no
    user action required, while leaving the combos free to be re-picked.
    """
    if axis_count not in (2, MAX_GRID_AXES):
        raise ValueError(f"axis_count must be 2 or {MAX_GRID_AXES}; got {axis_count}")
    if len(specs) < axis_count:
        raise ValueError(
            f"need at least {axis_count} parameters; surface has {len(specs)}"
        )
    return [spec.name for spec in specs[:axis_count]]


# ---------------------------------------------------------------------------
# slider-tick conversion + value formatting (shared by both panels)
# ---------------------------------------------------------------------------
#
# A ``QSlider`` stores an integer tick; tick ``k`` corresponds to the value
# ``minimum + k * step``.  These helpers are the single source of the
# value<->tick mapping so the slider stack (``ParametersPanel``) and the
# residual sliders (``ParameterGridPanel``) cannot drift apart.  All three
# guard a degenerate ``step <= 0`` (a public ``ParamSpec`` could be built
# with ``step=0``); the slider then collapses to a single tick.


def tick_count(spec: ParamSpec) -> int:
    """Number of slider ticks spanning ``[minimum, maximum]`` — always >= 1.

    A degenerate ``step <= 0`` collapses the slider to a single tick rather
    than raising ``ZeroDivisionError``.
    """
    if spec.step <= 0:
        return 1
    return max(1, int(round((spec.maximum - spec.minimum) / spec.step)))


def value_to_tick(value: float, spec: ParamSpec) -> int:
    """Map a parameter *value* to the integer tick index a ``QSlider`` stores.

    A degenerate ``step <= 0`` yields tick 0 (the single-point slider).
    """
    if spec.step <= 0:
        return 0
    return int(round((value - spec.minimum) / spec.step))


def tick_to_value(tick: int, spec: ParamSpec) -> float:
    """Inverse of :func:`value_to_tick` — tick index back to a parameter value."""
    return spec.minimum + tick * spec.step


def format_value(value: float, spec: ParamSpec) -> str:
    """Format a parameter *value* for display, precision keyed to ``spec.step``.

    Coarse steps (>= 1) show no decimals, medium steps (>= 0.1) show two,
    finer steps show three.  The spec's ``suffix`` (e.g. a unit) is appended.
    This is the single source of the readout format shared by the slider
    stack and the grid panel.
    """
    if spec.step >= 1:
        text = f"{value:.0f}"
    elif spec.step >= 0.1:
        text = f"{value:.2f}"
    else:
        text = f"{value:.3f}"
    return f"{text}{spec.suffix}"


# ---------------------------------------------------------------------------
# 3D drag-plane axis mapping
# ---------------------------------------------------------------------------

# Which two of the three axis indices the dot's 2D motion drives, per plane.
_PLANE_AXIS_MAP: dict[str, tuple[int, int]] = {
    "XY": (0, 1),
    "XZ": (0, 2),
    "YZ": (1, 2),
}

# The drag-plane names, in the order the selector lists them.
DRAG_PLANES: tuple[str, ...] = ("XY", "XZ", "YZ")


def plane_axes(plane: str, axis_count: int) -> tuple[int, int]:
    """Return the (horizontal, vertical) axis indices the dot's motion drives.

    For a 2-axis grid the dot always drives axes ``(0, 1)`` regardless of
    *plane*.  For a 3-axis grid the drag plane selects which two of the three
    axes move; the third is held fixed (see :func:`held_axis`).

    Raises
    ------
    ValueError
        if *plane* is not one of ``"XY"``, ``"XZ"``, ``"YZ"`` for a 3-axis
        grid.
    """
    if axis_count == 2:
        return 0, 1
    if plane not in _PLANE_AXIS_MAP:
        raise ValueError(
            f"unknown drag plane: {plane!r} (expected one of {DRAG_PLANES})"
        )
    return _PLANE_AXIS_MAP[plane]


def held_axis(plane: str, axis_count: int) -> int | None:
    """The axis index held fixed in a 3-axis grid; ``None`` for a 2-axis grid.

    Raises
    ------
    ValueError
        via :func:`plane_axes` if *plane* is unknown for a 3-axis grid.
    """
    if axis_count < MAX_GRID_AXES:
        return None
    moving = set(plane_axes(plane, axis_count))
    for i in range(MAX_GRID_AXES):
        if i not in moving:
            return i
    return None
