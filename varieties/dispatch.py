"""Render-dispatch predicates for AVC: speed-routing decisions for variety generators.

Per restructure-feature-subpackages-2026q2-r2 Batch 5: extracted from
surfaces.py (originally L96-L165) into a stable canonical path.

This module is Qt-free (AI-2) — the routing decisions are pure-functional
predicates over Surface dataclass state.
"""

from __future__ import annotations

from varieties.types import Surface


# realtime-variety-render-e2-s2 (CAND-8): the continuous-drag fast-path
# threshold, in ms.  A surface whose measured `typical_ms` falls in
# (0, FAST_RENDER_THRESHOLD_MS] is "fast enough" to regenerate at every
# debounced drag tick (~80 ms cadence) without the GUI feeling sluggish;
# anything slower stays release-only until the e4 coarse-LOD path lands.
FAST_RENDER_THRESHOLD_MS = 80


def should_render_on_drag(surface: "Surface | None") -> bool:
    """Pure speed-routing predicate for the continuous-drag fast-path.

    Returns ``True`` when *surface* is fast enough to regenerate on every
    debounced drag tick — i.e. it carries a measured ``typical_ms`` in the
    half-open range ``(0, FAST_RENDER_THRESHOLD_MS]``.  Returns ``False`` for
    ``None`` and for any surface with ``typical_ms == 0`` (unmeasured /
    implicit marching-cubes generators), which therefore stay release-only
    exactly as before this epic.

    Extracted as a free function (no Qt, no ``QApplication``) so the routing
    decision is unit-testable under the Qt-free AI-2 suite.  ``MainWindow``
    calls this from its drag-tick handler; the panels do not — they have no
    visibility into the current surface's ``typical_ms``.
    """
    return (
        surface is not None
        and 0 < surface.typical_ms <= FAST_RENDER_THRESHOLD_MS
    )


def dispatch_mode(surface: "Surface | None", in_drag: bool) -> str:
    """Return the e4b speed-routing decision for a render request.

    Three outcomes (the names are stable — `app.py` keys on them):

    - ``"full"`` — render at full resolution.  Fired (a) on slider RELEASE
      for every surface; (b) on slider DRAG for Hanson parametric surfaces
      (already fast enough — the e2 continuous-drag fast-path).
    - ``"coarse"`` — render at the surface's per-surface ``coarse_n`` floor
      (realtime-variety-render-e4b / CAND-3).  Fired only on slider DRAG
      for implicit (marching-cubes) generators with ``coarse_n > 0``; the
      release path then re-renders at full resolution.
    - ``"skip"`` — do nothing.  Fired on slider DRAG for opt-out implicit
      generators (``coarse_n == 0``, e.g. ``fano_two_quadrics`` whose
      ε-tube is too fragile for any practical coarse floor) and for
      ``None`` (no surface selected).

    AI-6 (three-layer Hanson skip):
      1. This function returns ``"full"`` (NOT ``"coarse"``) for Hanson
         because ``typical_ms > 0`` is checked before ``coarse_n``.
      2. Hanson surfaces' ``coarse_n == 0`` default — even if a future bug
         called for coarse mode on Hanson, the dispatch ``params["n"]``
         injection in ``app.py`` skips when ``coarse_n == 0``.
      3. The worker (``render_worker.MeshWorker``) is mode-agnostic — it
         passes ``params`` through to ``surface.generate`` unmodified, so
         a Hanson generator never sees an unwanted ``n`` override.

    Extracted as a free function (no Qt, no ``QApplication``) so the
    routing decision is unit-testable under the Qt-free AI-2 suite — same
    pattern as ``should_render_on_drag`` (this module) and
    ``clipped_cache_is_valid`` (``app.py``).
    """
    if surface is None:
        return "skip"
    if not in_drag:
        # Release path is always full-resolution.
        return "full"
    if surface.typical_ms > 0:
        # Hanson parametric surfaces are already fast enough; render full at
        # every drag tick.  (AI-6 layer 1: positive Hanson signal.)
        return "full"
    if surface.coarse_n > 0:
        # Implicit surface with a validated coarse-LOD floor.
        return "coarse"
    # Implicit, opt-out (coarse_n == 0): no drag render.
    return "skip"
