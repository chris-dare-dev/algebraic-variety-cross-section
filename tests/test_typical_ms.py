"""Tests for the CAND-8 speed-routing surface (realtime-variety-render-e2).

Two pure-Python (Qt-free, AI-2) surfaces are covered here:

  * e2-s1 — the `Surface.typical_ms` dataclass field: it exists, defaults to
    0, the 3 Hanson parametric generators carry a measured positive value,
    and every implicit (marching-cubes) generator keeps the 0 default.
  * e2-s2 — the `should_render_on_drag` speed-routing predicate: a fast
    (Hanson) surface routes to the continuous-drag fast-path; an implicit
    surface and `None` do not.

No Qt, no `QApplication`, no `MainWindow` — these exercise only the
`surfaces.py` dataclass + free function.
"""

from __future__ import annotations

import dataclasses
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from varieties.dispatch import (
    FAST_RENDER_THRESHOLD_MS,
    should_render_on_drag)

from varieties.registry import (
    VARIETIES)

from varieties.types import (
    Surface)

from varieties.calabi_yau import (
    calabi_yau_asymmetric,
    calabi_yau_cubic,
    calabi_yau_quintic)

from varieties.k3 import (
    fermat_quartic)

# The 3 Hanson parametric generators that get a measured typical_ms (e2-s1).
_HANSON_GENERATORS = {
    calabi_yau_quintic,
    calabi_yau_cubic,
    calabi_yau_asymmetric,
}


def _all_surfaces() -> list[Surface]:
    """Every Surface in the registry, flattened across variety families."""
    return [s for family in VARIETIES.values() for s in family.values()]


# ---------------------------------------------------------------------------
# e2-s1 — the typical_ms dataclass field
# ---------------------------------------------------------------------------


def test_typical_ms_field_exists_with_default_zero():
    """`Surface` has a `typical_ms` field defaulting to 0."""
    field_names = {f.name for f in dataclasses.fields(Surface)}
    assert "typical_ms" in field_names

    # A Surface built without typical_ms must default to 0.
    s = Surface("probe", calabi_yau_quintic, [])
    assert s.typical_ms == 0


def test_hanson_surfaces_have_positive_typical_ms():
    """All 3 Hanson parametric surfaces carry a measured typical_ms > 0."""
    hanson = [s for s in _all_surfaces() if s.generate in _HANSON_GENERATORS]
    # Sanity: exactly the 3 Hanson figures are registered.
    assert len(hanson) == 3
    for surface in hanson:
        assert surface.typical_ms > 0, (
            f"{surface.label} should have a measured typical_ms"
        )


def test_implicit_surfaces_keep_typical_ms_zero():
    """Every implicit (non-Hanson) generator keeps the default typical_ms == 0."""
    implicit = [s for s in _all_surfaces() if s.generate not in _HANSON_GENERATORS]
    # Sanity: 8 marching-cubes generators (Fermat, Kummer, Enriques x4,
    # Dwork, plus 4 Fano) — anything not on the Hanson parametric path.
    assert len(implicit) >= 8
    for surface in implicit:
        assert surface.typical_ms == 0, (
            f"{surface.label} is implicit and must keep typical_ms == 0"
        )


def test_hanson_typical_ms_under_fast_threshold():
    """The measured Hanson values all fall under the fast-path threshold."""
    hanson = [s for s in _all_surfaces() if s.generate in _HANSON_GENERATORS]
    for surface in hanson:
        assert 0 < surface.typical_ms <= FAST_RENDER_THRESHOLD_MS


# ---------------------------------------------------------------------------
# e2-s2 — the should_render_on_drag speed-routing predicate
# ---------------------------------------------------------------------------


def test_predicate_true_for_hanson_surface():
    """A Hanson surface routes to the continuous-drag fast-path."""
    quintic = VARIETIES["Calabi–Yau 3-fold"]["Hanson quintic  [Fig. 1]"]
    assert should_render_on_drag(quintic) is True


def test_predicate_false_for_implicit_surface():
    """An implicit (Fermat) surface stays release-only — predicate False."""
    fermat = VARIETIES["K3 surface"]["Fermat quartic"]
    assert fermat.typical_ms == 0
    assert should_render_on_drag(fermat) is False


def test_predicate_false_for_none():
    """No surface selected — predicate is False (no drag render)."""
    assert should_render_on_drag(None) is False


def test_predicate_false_for_too_slow_surface():
    """A surface measured slower than the threshold is NOT fast-pathed."""
    slow = Surface("slow probe", fermat_quartic, [],
                   typical_ms=FAST_RENDER_THRESHOLD_MS + 1)
    assert should_render_on_drag(slow) is False


def test_predicate_true_at_threshold_boundary():
    """typical_ms exactly at the threshold is inclusive (fast-pathed)."""
    boundary = Surface("boundary probe", calabi_yau_quintic, [],
                        typical_ms=FAST_RENDER_THRESHOLD_MS)
    assert should_render_on_drag(boundary) is True


def test_every_hanson_registry_surface_is_fast_pathed():
    """All 3 registered Hanson surfaces route through the fast-path."""
    hanson = [s for s in _all_surfaces() if s.generate in _HANSON_GENERATORS]
    assert len(hanson) == 3
    for surface in hanson:
        assert should_render_on_drag(surface) is True
