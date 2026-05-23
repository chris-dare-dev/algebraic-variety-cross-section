"""Tests for ViewPanel.clip_to_domain — pure PyVista geometry, no VTK render window.

clip_to_domain reads its configuration via self.domain_settings(), which returns a
plain dict.  We test the geometry logic by monkey-patching domain_settings() on a
ViewPanel instance that has been constructed without a real plotter — ViewPanel
only needs the plotter for overlay/camera calls that are not exercised here.
"""

from __future__ import annotations

import sys
import os
import types

import numpy as np
import pytest
import pyvista as pv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from panels.view import ViewPanel


# ---------------------------------------------------------------------------
# Minimal fake plotter so ViewPanel.__init__ doesn't crash
# ---------------------------------------------------------------------------

class _FakePlotter:
    """Minimal stand-in for pyvistaqt.QtInteractor in non-GUI tests."""
    def add_mesh(self, *a, **kw): pass
    def remove_actor(self, *a, **kw): pass
    def reset_camera(self): pass
    def render(self): pass
    def show_axes(self): pass
    def hide_axes(self): pass
    def add_bounding_box(self): return None
    def remove_bounding_box(self): pass
    def show_grid(self): return None
    def remove_bounds_axes(self): pass
    def screenshot(self, *a, **kw): pass
    def set_background(self, *a, **kw): pass


def _make_panel() -> ViewPanel:
    """Return a ViewPanel wired to a fake plotter, bypassing all Qt widget state
    by patching domain_settings() to return a controlled dict."""
    # ViewPanel.__init__ builds all Qt widgets but doesn't touch the plotter
    # during construction.
    from PySide6.QtWidgets import QApplication
    if QApplication.instance() is None:
        # Minimal headless QApplication — no window is shown
        QApplication(["test", "--platform", "offscreen"])
    panel = ViewPanel.__new__(ViewPanel)
    panel._plotter = _FakePlotter()
    panel._bbox_actor = None
    panel._grid_actor = None
    # Don't call _build_ui — we override domain_settings directly below.
    return panel


def _panel_with_settings(mode: str, radius: float, show_overlay: bool) -> ViewPanel:
    panel = _make_panel()
    panel.domain_settings = lambda: {
        "mode": mode,
        "radius": radius,
        "show_overlay": show_overlay,
    }
    return panel


# ---------------------------------------------------------------------------
# Build a simple symmetric test mesh (sphere of points)
# ---------------------------------------------------------------------------

def _sphere_mesh(radius: float = 2.0) -> pv.PolyData:
    return pv.Sphere(radius=radius, center=(0.0, 0.0, 0.0),
                     theta_resolution=24, phi_resolution=12)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_domain_off_returns_original():
    """Mode 'Off' should return the mesh unchanged with no overlay."""
    mesh = _sphere_mesh(radius=2.0)
    panel = _panel_with_settings(ViewPanel.DOMAIN_NONE, 2.5, True)
    clipped, overlay = panel.clip_to_domain(mesh)
    assert clipped.n_points == mesh.n_points
    assert overlay is None


def test_sphere_clip_large_radius_preserves_all_points():
    """Sphere clip with r >> max_dist should keep all vertices."""
    mesh = _sphere_mesh(radius=2.0)
    max_dist = float(np.linalg.norm(mesh.points, axis=1).max())
    large_r = max_dist * 2.0
    panel = _panel_with_settings(ViewPanel.DOMAIN_SPHERE, large_r, False)
    clipped, overlay = panel.clip_to_domain(mesh)
    assert clipped.n_points == mesh.n_points
    assert overlay is None  # show_overlay=False


def test_sphere_clip_tiny_radius_returns_empty():
    """Sphere clip with r << min_dist should exclude all vertices."""
    mesh = _sphere_mesh(radius=2.0)
    min_dist = float(np.linalg.norm(mesh.points, axis=1).min())
    tiny_r = min_dist * 0.5
    panel = _panel_with_settings(ViewPanel.DOMAIN_SPHERE, tiny_r, False)
    clipped, overlay = panel.clip_to_domain(mesh)
    assert clipped.n_points == 0


def test_sphere_clip_overlay_present_when_requested():
    """When show_overlay=True, clip_to_domain should return a non-None overlay."""
    mesh = _sphere_mesh(radius=2.0)
    panel = _panel_with_settings(ViewPanel.DOMAIN_SPHERE, 1.5, True)
    _clipped, overlay = panel.clip_to_domain(mesh)
    assert overlay is not None
    assert overlay.n_points > 0


def test_cube_clip_preserves_xyz_symmetry():
    """Cube clip on a symmetric mesh should give a result still symmetric
    about all three axes (centre of mass near origin)."""
    mesh = _sphere_mesh(radius=2.0)
    # Use a cube half-side that cuts through the sphere
    panel = _panel_with_settings(ViewPanel.DOMAIN_CUBE, 1.4, False)
    clipped, _overlay = panel.clip_to_domain(mesh)
    if clipped.n_points == 0:
        pytest.skip("No points survived the cube clip — adjust radius")
    pts = clipped.points
    # Centre of mass should be near origin for a symmetric input
    com = pts.mean(axis=0)
    assert abs(com[0]) < 0.3, f"x centroid {com[0]:.3f} off-centre after cube clip"
    assert abs(com[1]) < 0.3, f"y centroid {com[1]:.3f} off-centre after cube clip"
    assert abs(com[2]) < 0.3, f"z centroid {com[2]:.3f} off-centre after cube clip"


def test_cube_clip_large_halfside_preserves_all():
    """Cube clip with half-side >> mesh extent should return all vertices."""
    mesh = _sphere_mesh(radius=2.0)
    max_coord = float(np.max(np.abs(mesh.points)))
    large_r = max_coord * 2.0
    panel = _panel_with_settings(ViewPanel.DOMAIN_CUBE, large_r, False)
    clipped, _ = panel.clip_to_domain(mesh)
    assert clipped.n_points == mesh.n_points
