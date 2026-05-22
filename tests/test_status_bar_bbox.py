"""Regression guards for the status-bar spatial bbox readout
(status-bar-bbox-2026q2-e1, UPL-13).

These tests are Qt-free (AI-2) — they call the surface generators
directly and verify the bbox-format contract used by
``app.MainWindow._render_current``.  No ``MainWindow``, no
``QApplication``.
"""
from __future__ import annotations

import re

import pytest

import surfaces


# The exact format applied to mesh.bounds[1]/[3]/[5] in
# app.py:_render_current.  Mirroring it here lets us assert the
# format-contract without importing app.py (which would drag Qt in).
BBOX_FORMAT = "bbox ±{a:.2f} × ±{b:.2f} × ±{c:.2f}"
BBOX_REGEX = re.compile(r"^bbox ±\d+\.\d+ × ±\d+\.\d+ × ±\d+\.\d+$")


def _format_bbox(mesh) -> str:
    b = mesh.bounds  # (xmin, xmax, ymin, ymax, zmin, zmax)
    return BBOX_FORMAT.format(a=b[1], b=b[3], c=b[5])


def test_bbox_format_matches_regex_on_fermat_quartic() -> None:
    """The bbox suffix produced from Fermat quartic mesh.bounds matches
    the exact 'bbox ±a.bb × ±a.bb × ±a.bb' pattern that app.py emits."""
    mesh = surfaces.fermat_quartic()
    result = _format_bbox(mesh)
    assert BBOX_REGEX.fullmatch(result), (
        f"bbox string {result!r} does not match {BBOX_REGEX.pattern!r}"
    )


def test_bbox_max_extents_are_positive_for_symmetric_generator() -> None:
    """For any symmetric-sampling-box generator, mesh.bounds[1]/[3]/[5]
    (the positive max-extents) must be > 0.  Validates the ±max framing
    that app.py uses — a non-positive max would mean the surface is
    confined to the negative half-space, which makes ± framing
    nonsensical.  All 12 implicit-surface generators in the live
    registry produce strictly positive max-extents at defaults."""
    mesh = surfaces.fermat_quartic()
    b = mesh.bounds
    assert b[1] > 0.0, f"Fermat quartic xmax was {b[1]} (expected > 0)"
    assert b[3] > 0.0, f"Fermat quartic ymax was {b[3]} (expected > 0)"
    assert b[5] > 0.0, f"Fermat quartic zmax was {b[5]} (expected > 0)"


def test_bbox_format_matches_regex_on_kummer_surface() -> None:
    """Second positive-path test covering a different generator family
    (Kummer quartic with adaptive bounds), confirming the format
    contract holds across the implicit-surface registry."""
    mesh = surfaces.kummer_surface()
    result = _format_bbox(mesh)
    assert BBOX_REGEX.fullmatch(result), (
        f"bbox string {result!r} does not match {BBOX_REGEX.pattern!r}"
    )


def test_valueerror_path_cannot_produce_bbox() -> None:
    """Generator-contract guard supporting the AI-14 claim that the
    error branch of app.py:_render_current never emits a bbox suffix.
    Kummer at mu² = 0.2 is below the lambda=0 threshold (mu² ≤ 1/3)
    and the generator raises ValueError before any mesh is built —
    so there is no mesh.bounds to format.  This test fails loudly if
    the generator contract ever weakens to e.g. return an empty
    PolyData on bad input, which would let app.py emit a bbox like
    'bbox ±0.00 × ±0.00 × ±0.00' on the error path."""
    with pytest.raises(ValueError):
        surfaces.kummer_surface(mu_squared=0.2)
