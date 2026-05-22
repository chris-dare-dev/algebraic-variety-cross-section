"""Qt-free tests for the CAND-11 clipped-mesh cache (e1-s5).

AI-2: no ``QApplication``, no VTK.  The cache-validity logic is extracted as
the pure function :func:`app.clipped_cache_is_valid` precisely so it can be
tested here without a Qt event loop.  A second test models the
``_apply_domain_and_render`` call path with a call-counted fake ``clip`` to
assert the headline property: ``clip_to_domain`` is NOT re-run for an
appearance-only re-render.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import clipped_cache_is_valid


# ---------------------------------------------------------------------------
# Pure cache-validity predicate
# ---------------------------------------------------------------------------

def test_no_cache_is_invalid():
    """With nothing cached the predicate always reports a miss."""
    assert clipped_cache_is_valid(None, raw_mesh_changed=False,
                                  domain_changed=False) is False


def test_cached_and_unchanged_is_valid():
    """A populated cache with no raw-mesh / domain change is reusable."""
    assert clipped_cache_is_valid(object(), raw_mesh_changed=False,
                                  domain_changed=False) is True


def test_raw_mesh_change_invalidates():
    assert clipped_cache_is_valid(object(), raw_mesh_changed=True,
                                  domain_changed=False) is False


def test_domain_change_invalidates():
    """AI-10: a domain-radius change is a cache miss (re-clip) but never
    implies a raw-mesh regeneration — the predicate is mesh-agnostic."""
    assert clipped_cache_is_valid(object(), raw_mesh_changed=False,
                                  domain_changed=True) is False


def test_both_changed_invalidates():
    assert clipped_cache_is_valid(object(), raw_mesh_changed=True,
                                  domain_changed=True) is False


# ---------------------------------------------------------------------------
# Call-counted model of _apply_domain_and_render — appearance-only re-render
# must NOT re-run clip_to_domain.
# ---------------------------------------------------------------------------

class _ClipCacheSim:
    """Pure model of ``MainWindow``'s clip-cache control flow.

    Reproduces ``app.py``: ``_clipped_mesh`` is the cache slot;
    ``_apply_domain_and_render`` populates it on a miss and reuses it on a
    hit; ``_invalidate_clipped_mesh`` clears it; a raw-mesh change (generate)
    and a domain change both invalidate.  ``clip_calls`` counts how many
    times the (faked) ``clip_to_domain`` actually ran.
    """

    def __init__(self) -> None:
        self._raw_mesh = "raw-v0"
        self._clipped_mesh = None
        self.clip_calls = 0

    def _invalidate(self) -> None:
        self._clipped_mesh = None

    def _clip_to_domain(self) -> str:
        # Stand-in for view_panel.clip_to_domain — the expensive
        # mesh.copy() + scalar-tag + clip_scalar.
        self.clip_calls += 1
        return f"clipped({self._raw_mesh})"

    def apply_domain_and_render(self) -> None:
        if self._clipped_mesh is None:
            self._clipped_mesh = self._clip_to_domain()
        # else: cache hit — reuse, no clip.

    def generate(self) -> None:
        """A new surface.generate() — raw mesh changes, cache invalidated."""
        self._raw_mesh = "raw-" + str(self.clip_calls + 1)
        self._invalidate()

    def domain_changed(self) -> None:
        """Domain settings changed — cache invalidated, raw mesh untouched."""
        self._invalidate()


def test_appearance_only_rerender_does_not_reclip():
    """Two sequential renders with NO raw-mesh / domain change between them
    run clip_to_domain exactly once (CAND-11 headline property)."""
    sim = _ClipCacheSim()
    sim.generate()                 # first surface
    sim.apply_domain_and_render()  # cache miss -> clip #1
    assert sim.clip_calls == 1
    # An appearance-only re-render (e.g. surface colour change) — no
    # invalidation happened, so the cached clip is reused.
    sim.apply_domain_and_render()
    sim.apply_domain_and_render()
    assert sim.clip_calls == 1     # still 1 — clip was NOT re-run


def test_domain_change_triggers_one_reclip():
    sim = _ClipCacheSim()
    sim.generate()
    sim.apply_domain_and_render()  # clip #1
    sim.domain_changed()           # invalidate
    sim.apply_domain_and_render()  # clip #2
    sim.apply_domain_and_render()  # cache hit — no clip
    assert sim.clip_calls == 2


def test_new_surface_triggers_one_reclip():
    sim = _ClipCacheSim()
    sim.generate()
    sim.apply_domain_and_render()  # clip #1
    sim.generate()                 # new raw mesh -> invalidate
    sim.apply_domain_and_render()  # clip #2
    assert sim.clip_calls == 2


def test_raw_mesh_untouched_by_domain_change():
    """AI-10: a domain change must not regenerate the raw mesh."""
    sim = _ClipCacheSim()
    sim.generate()
    raw_before = sim._raw_mesh
    sim.domain_changed()
    assert sim._raw_mesh == raw_before  # raw mesh preserved
