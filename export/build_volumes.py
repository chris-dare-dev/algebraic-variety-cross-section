"""Printer build-volume presets + pure sizing-input resolution (Qt-free).

This module is the single home for every non-trivial decision the print-export
flow makes BEFORE it calls ``export.printable.export_to_stl``: which printer
build volume to target, whether to scale to a fixed size or fill the plate, and
how the raw user inputs (preset name / custom dimensions / target / fit / margin
/ binary) map onto ``export_to_stl`` keyword arguments.

Keeping all of that here — as pure, side-effect-free functions over plain
Python types — means both the CLI (``export.__main__``) and the GUI dialog
(``_qt.dialogs.print_options_dialog``) share one validated code path, and the
whole thing is unit-testable with **zero Qt** (AI-2).

Layering (import-linter): this module may import ``export.printable`` + stdlib
ONLY. It MUST NOT import PySide6 or anything under ``_qt``.
"""

from __future__ import annotations

from export.printable import BuildVolume

# ---------------------------------------------------------------------------
# Printer preset registry
# ---------------------------------------------------------------------------
#
# Dimensions are the manufacturer-stated usable build volumes in millimetres
# (x, y, z). The H2S is the AVC documented default (it is the printer the
# original export flow hardcoded via export.printable.BAMBU_H2S = 340x320x340).

#: The documented default printer preset name.
DEFAULT_PRINTER = "Bambu Lab H2S"

#: name -> BuildVolume. Ordered so list_presets() puts the default first.
PRINTER_PRESETS: dict[str, BuildVolume] = {
    "Bambu Lab H2S": BuildVolume(340.0, 320.0, 340.0),
    "Bambu Lab X1C": BuildVolume(256.0, 256.0, 256.0),
    "Bambu Lab P1S": BuildVolume(256.0, 256.0, 256.0),
    "Bambu Lab A1": BuildVolume(256.0, 256.0, 256.0),
    "Bambu Lab A1 mini": BuildVolume(180.0, 180.0, 180.0),
}


def list_presets() -> list[str]:
    """Return the preset printer names in registry (display) order."""
    return list(PRINTER_PRESETS)


def get_build_volume(name: str) -> BuildVolume:
    """Return the :class:`BuildVolume` for a preset *name*.

    Raises ``KeyError`` with the available names on an unknown printer.
    """
    try:
        return PRINTER_PRESETS[name]
    except KeyError:
        raise KeyError(
            f"Unknown printer {name!r}. Available presets: {list_presets()}"
        ) from None


def custom_build_volume(x_mm: float, y_mm: float, z_mm: float) -> BuildVolume:
    """Build a custom :class:`BuildVolume`, rejecting non-positive dimensions."""
    for axis, value in (("x", x_mm), ("y", y_mm), ("z", z_mm)):
        if value is None or value <= 0:
            raise ValueError(
                f"Custom build-volume {axis} dimension must be > 0, got {value!r}"
            )
    return BuildVolume(float(x_mm), float(y_mm), float(z_mm))


def resolve_build_volume(
    printer: str | None,
    dims: tuple[float, float, float] | None,
) -> BuildVolume:
    """Resolve a build volume from EITHER a preset name OR custom *dims*.

    Exactly one of ``printer`` / ``dims`` must be supplied. Supplying both, or
    neither, is an error (the caller — CLI or GUI — is expected to make them
    mutually exclusive at the input layer; this is the last-line guard).
    """
    if printer is not None and dims is not None:
        raise ValueError(
            "Specify a printer preset OR custom dimensions, not both."
        )
    if printer is None and dims is None:
        raise ValueError(
            "Specify a printer preset (name) or custom dimensions (x, y, z)."
        )
    if printer is not None:
        return get_build_volume(printer)
    # dims is not None here
    if len(dims) != 3:
        raise ValueError(
            f"Custom dimensions must be (x, y, z); got {len(dims)} value(s)."
        )
    return custom_build_volume(*dims)


def build_export_kwargs(
    *,
    printer: str | None = None,
    dims: tuple[float, float, float] | None = None,
    target_mm: float | None = None,
    fit_to_plate: bool = False,
    margin_mm: float = 5.0,
    binary: bool = True,
) -> dict:
    """Convert raw user sizing inputs into ``export_to_stl`` keyword arguments.

    Returns ``{"build", "target_mm", "margin_mm", "binary"}`` ready to splat
    into :func:`export.printable.export_to_stl`.

    Semantics
    ---------
    * ``printer`` / ``dims`` — resolved via :func:`resolve_build_volume`
      (exactly one). If BOTH are ``None`` the documented default printer
      (:data:`DEFAULT_PRINTER`) is used — this keeps the "no flags / no dialog
      change" path on the historical Bambu H2S behaviour.
    * ``fit_to_plate=True`` → ``target_mm`` becomes ``None`` (fill the plate
      minus margin). An explicit ``target_mm`` together with ``fit_to_plate``
      is rejected as contradictory.
    * ``target_mm`` must be > 0 when given (and when not fitting). An oversize
      target is *not* rejected here — ``export_to_stl`` / ``fit_to_build_volume``
      clamp it down to the build volume (``clamped=True``), which is the
      intended "never silently over-size" behaviour.
    * ``margin_mm`` must be >= 0.
    """
    if margin_mm is None or margin_mm < 0:
        raise ValueError(f"margin_mm must be >= 0, got {margin_mm!r}")

    if fit_to_plate:
        if target_mm is not None:
            raise ValueError(
                "fit_to_plate=True fills the build volume; do not also pass "
                "target_mm."
            )
        resolved_target: float | None = None
    else:
        if target_mm is None:
            raise ValueError(
                "Provide target_mm (size of the longest axis in mm) or set "
                "fit_to_plate=True."
            )
        if target_mm <= 0:
            raise ValueError(
                f"target_mm must be > 0 (or use fit_to_plate); got {target_mm!r}"
            )
        resolved_target = float(target_mm)

    # Default to the historical printer when neither input is supplied.
    if printer is None and dims is None:
        build = get_build_volume(DEFAULT_PRINTER)
    else:
        build = resolve_build_volume(printer, dims)

    return {
        "build": build,
        "target_mm": resolved_target,
        "margin_mm": float(margin_mm),
        "binary": bool(binary),
    }
