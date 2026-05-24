"""Pure domain-clip math for AVC variety cross-sections.

Per restructure-feature-subpackages-2026q2-r2 Batch 4 (Move Method per Fowler):
extracted the math core of ``ViewPanel.clip_to_domain`` (which lives in
``_qt/panels/view.py``) into this pure-functional module.

This module is Qt-free (AI-2). The widget reads stay in ViewPanel; this module
just takes the plain-data args (mode, radius, show_overlay) and produces the
clipped mesh + overlay.

AI-4 + AI-5 preserved: uses ``clip_scalar(scalars=..., invert=True)``.
"""

from __future__ import annotations

import numpy as np
import pyvista as pv

# Domain mode constants — string-valued for round-trippability with the
# QComboBox in ViewPanel. ViewPanel.DOMAIN_NONE etc. are aliases of these.
DOMAIN_NONE = "Off"
DOMAIN_SPHERE = "Sphere"
DOMAIN_CUBE = "Cube"


def clip_to_domain(
    mesh: pv.PolyData,
    mode: str,
    radius: float,
    show_overlay: bool,
) -> tuple[pv.PolyData, pv.PolyData | None]:
    """Apply the user-chosen domain clip to *mesh*.

    Args:
        mesh: The unclipped surface mesh.
        mode: One of ``DOMAIN_NONE`` / ``DOMAIN_SPHERE`` / ``DOMAIN_CUBE``.
        radius: Radius of the sphere / half-side of the cube (in mesh units).
        show_overlay: If True, return a wireframe overlay (sphere or box).

    Returns:
        ``(clipped_mesh, overlay_mesh_or_None)``. The overlay is the wireframe
        sphere/cube to draw alongside the clipped surface, or ``None`` if the
        caller asked to suppress it (``show_overlay=False``) or the mode is
        ``DOMAIN_NONE``.

    Notes:
        Per AI-4 + AI-5: uses ``clip_scalar(scalars=..., invert=True)`` not
        ``clip_box`` (which has broken invert semantics on PolyData surfaces).
    """
    if mode == DOMAIN_NONE or mesh.n_points == 0:
        return mesh, None

    # Both clips use the same scalar-clipping approach for reliable behavior
    # on PolyData surfaces: tag every vertex with a "domain function" (radial
    # distance for the sphere, Chebyshev / max-coord distance for the cube),
    # then keep only verts where that function is <= the threshold.
    work = mesh.copy()
    if mode == DOMAIN_SPHERE:
        work.point_data["_domain_dist"] = np.linalg.norm(work.points, axis=1)
        overlay = (
            pv.Sphere(radius=radius, center=(0.0, 0.0, 0.0),
                      theta_resolution=48, phi_resolution=24)
            if show_overlay else None
        )
    else:  # DOMAIN_CUBE
        work.point_data["_domain_dist"] = np.max(np.abs(work.points), axis=1)
        overlay = pv.Box(bounds=(-radius, radius, -radius, radius, -radius, radius)) if show_overlay else None

    clipped = work.clip_scalar(scalars="_domain_dist", value=radius, invert=True)
    return clipped, overlay
