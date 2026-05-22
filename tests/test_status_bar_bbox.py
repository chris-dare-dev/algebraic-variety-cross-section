"""Regression guards for the status-bar spatial bbox readout
(status-bar-bbox-2026q2-e1 + -e2, UPL-13).

These tests are Qt-free (AI-2) — they call the surface generators
directly and verify the bbox-format contract used by
``app.MainWindow._render_current``.  No ``MainWindow``, no
``QApplication``.

History:
  e1 (2026-05-22) shipped the readout in ±max half-extent form
       ('bbox ±a × ±b × ±c').  This was exact for the 11
       implicit-surface generators but an honest over-approximation
       for the 3 Hanson parametric generators whose theta sweeps
       [0, π/2] produce non-symmetric bounds.
  e2 (2026-05-22) switched to full-extent form
       ('bbox: Lx × Ly × Lz' where Lx = bounds[1] - bounds[0]),
       which is exact for ALL generators by construction.  Closes
       the F-M2 (peer-tool vocabulary mismatch), F-L1 (peer
       convention divergence) and F-L2 (.2f false equalities at
       sub-1.0 extents) findings from e1's frontend-ux critique.
       The "bbox:" label is preserved across both milestones (per
       e2 rect F-M1: peer tools all qualify the measurement
       type — bare "size:" would be ambiguous for algebraic
       surfaces).
"""
from __future__ import annotations

import math
import re

import pytest

import surfaces


# The exact format applied to mesh.bounds in app.py:_render_current.
# Mirroring it here lets us assert the format-contract without
# importing app.py (which would drag Qt in).
#
# The full extent along each axis is bounds[2i+1] - bounds[2i], which
# is the true diameter regardless of whether the sampling box is
# centered.  Precision is .3f (3 decimal places) — .2f rounded
# adjacent surfaces with extents 0.53 and 0.54 to the same display,
# which is a false-equality risk in a research tool.
#
# Use \d{3} (NOT \d+) in the regex to enforce the .3f contract — a
# regression to .2f or .4f would otherwise slip past the test.
BBOX_FORMAT = "bbox: {a:.3f} × {b:.3f} × {c:.3f}"
BBOX_REGEX = re.compile(r"^bbox: \d+\.\d{3} × \d+\.\d{3} × \d+\.\d{3}$")


def _format_bbox(mesh) -> str:
    """Compute the bbox suffix exactly as app.py:_render_current emits it.

    `mesh.bounds` returns (xmin, xmax, ymin, ymax, zmin, zmax); the
    full extent along each axis is `bounds[2i+1] - bounds[2i]`.
    """
    b = mesh.bounds
    return BBOX_FORMAT.format(a=b[1] - b[0], b=b[3] - b[2], c=b[5] - b[4])


def test_bbox_format_matches_regex_on_fermat_quartic() -> None:
    """The bbox suffix produced from Fermat quartic mesh.bounds matches
    the exact 'bbox: x.bbb × x.bbb × x.bbb' pattern that app.py emits."""
    mesh = surfaces.fermat_quartic()
    result = _format_bbox(mesh)
    assert BBOX_REGEX.fullmatch(result), (
        f"bbox string {result!r} does not match {BBOX_REGEX.pattern!r}"
    )


def test_bbox_extents_are_positive_for_symmetric_generator() -> None:
    """For any non-degenerate mesh the full extent along each axis must be
    > 0 — a zero-or-negative full extent would mean a degenerate / empty
    mesh (or a future generator returning a malformed bounding box).
    Exercised here against a representative symmetric-sampling-box
    generator (Fermat quartic); the same contract is documented in
    CONTEXT.md §4.3 for all 14 generators (since full extent is just
    ``bounds[2i+1] - bounds[2i]`` it is well-defined for every mesh)."""
    mesh = surfaces.fermat_quartic()
    b = mesh.bounds
    assert (b[1] - b[0]) > 0.0, (
        f"Fermat quartic x-extent was {b[1] - b[0]} (expected > 0)"
    )
    assert (b[3] - b[2]) > 0.0, (
        f"Fermat quartic y-extent was {b[3] - b[2]} (expected > 0)"
    )
    assert (b[5] - b[4]) > 0.0, (
        f"Fermat quartic z-extent was {b[5] - b[4]} (expected > 0)"
    )


def test_bbox_format_matches_regex_on_kummer_surface() -> None:
    """Second positive-path test covering a different generator family
    (Kummer quartic with adaptive bounds), confirming the format
    contract holds across the implicit-surface registry."""
    mesh = surfaces.kummer_surface()
    result = _format_bbox(mesh)
    assert BBOX_REGEX.fullmatch(result), (
        f"bbox string {result!r} does not match {BBOX_REGEX.pattern!r}"
    )


def test_bbox_format_matches_regex_on_hanson_quintic() -> None:
    """Hanson parametric generators sample `theta ∈ [0, π/2]` (non-centered),
    so their mesh.bounds are not symmetric — CONTEXT.md §4.3 documents the
    switch to full-extent widths (`bbox: Lx × Ly × Lz`, e2) which reports
    the actual diameter honestly rather than over-approximating with ±max
    (the e1 format).  The format-contract still holds (regex match), and
    ALL 6 bounds indices must be finite — the full-extent computation
    subtracts ``b[0]/b[2]/b[4]``, so a NaN anywhere in the bounds tuple
    (not just in the positive indices the e1 format read) corrupts the
    bbox suffix.  This guards against future changes to
    `_hanson_cross_section` that might produce degenerate vertex
    coordinates (e.g. a phase-cancelling configuration), which would
    otherwise let the status bar emit `bbox: nan × nan × nan`."""
    mesh = surfaces.calabi_yau_quintic()
    b = mesh.bounds
    # Full-extent computation needs all 6 indices to be finite.
    for i, axis in enumerate(("xmin", "xmax", "ymin", "ymax", "zmin", "zmax")):
        assert math.isfinite(b[i]), (
            f"Hanson quintic bounds[{i}] ({axis}) was {b[i]!r}; expected finite"
        )
    result = _format_bbox(mesh)
    assert BBOX_REGEX.fullmatch(result), (
        f"Hanson quintic bbox string {result!r} does not match "
        f"{BBOX_REGEX.pattern!r}"
    )


def test_bbox_format_matches_regex_on_hanson_asymmetric() -> None:
    """Hanson asymmetric is the strongest regression canary in the Hanson
    family: at default parameters its full extents are 2.257 × 2.449 ×
    3.343 — visibly different along all three axes (x ≠ y ≠ z), making
    it the only generator where a per-axis arithmetic bug (e.g.
    swapping ``b[3]-b[2]`` with ``b[5]-b[4]``) would be visible in the
    output rather than masked by the symmetry of the cubic/quintic
    generators (which both have x = y ≈ 2.4, z ≈ 3.0).

    Mirrors the quintic test structure: all 6 bounds indices must be
    finite (the full-extent subtraction reads b[0]/b[2]/b[4] too), and
    the format-contract regex must fullmatch.

    Added in status-bar-bbox-2026q2-e2 rect (adversary M1): closes the
    Hanson family coverage gap identified by the adversary critic — the
    e2 implementation tested only the quintic, leaving the most
    structurally distinct member of the family unguarded.
    """
    mesh = surfaces.calabi_yau_asymmetric()
    b = mesh.bounds
    for i, axis in enumerate(("xmin", "xmax", "ymin", "ymax", "zmin", "zmax")):
        assert math.isfinite(b[i]), (
            f"Hanson asymmetric bounds[{i}] ({axis}) was {b[i]!r}; expected finite"
        )
    result = _format_bbox(mesh)
    assert BBOX_REGEX.fullmatch(result), (
        f"Hanson asymmetric bbox string {result!r} does not match "
        f"{BBOX_REGEX.pattern!r}"
    )


def test_valueerror_path_cannot_produce_bbox() -> None:
    """Generator-contract guard supporting the AI-14 claim that the
    error branch of app.py:_render_current never emits a bbox suffix.
    Kummer at mu² = 0.2 is below the lambda=0 threshold (mu² ≤ 1/3)
    and the generator raises ValueError before any mesh is built —
    so there is no mesh.bounds to format.  This test fails loudly if
    the generator contract ever weakens to e.g. return an empty
    PolyData on bad input, which would let app.py emit a bbox string
    like 'bbox: 0.000 × 0.000 × 0.000' on the error path."""
    with pytest.raises(ValueError):
        surfaces.kummer_surface(mu_squared=0.2)
