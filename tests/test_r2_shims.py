"""Regression guards for r2's shim files.

Per restructure-feature-subpackages-2026q2-r2 Batch 9 + design-adversary v2 MED-5:
these tests prove that every shim emits DeprecationWarning with the new canonical
path in the message. They replace the deleted r1 tests/test_panels_shims.py with
broader coverage matching r2's expanded shim surface (render_worker, icons, styles,
ui_helpers, panels hub, surfaces hub).

AI-2 compliant: every test is import-only; no Qt construction.

Per scout-C 5.7: shim tests are PARITY VERIFICATION, not features. The shims
themselves are the safety net (the M+1 deprecation cycle); these tests ensure
the safety net is actually wired correctly.
"""

from __future__ import annotations

import warnings


def test_render_worker_shim_emits_deprecation():
    """render_worker.MeshWorker -> render.worker.MeshWorker (r2 batch 2)."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        from render_worker import MeshWorker  # noqa: F401
    assert any(
        "render.worker" in str(w.message) and issubclass(w.category, DeprecationWarning)
        for w in caught
    ), f"render_worker shim missing or silent; captured warnings: {[str(w.message) for w in caught]}"


def test_icons_shim_emits_deprecation():
    """icons.<name> -> _qt.icons.<name> (r2 batch 3 commit 2)."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        import icons
        # Trigger __getattr__ via attribute access (bare `import icons` doesn't fire it).
        _ = icons._icon_color
    assert any(
        "_qt.icons" in str(w.message) and issubclass(w.category, DeprecationWarning)
        for w in caught
    ), f"icons shim missing or silent; captured warnings: {[str(w.message) for w in caught]}"


def test_styles_shim_emits_deprecation():
    """styles.<name> -> _qt.styles.<name> (r2 batch 3 commit 2)."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        from styles import APP_STYLESHEET  # noqa: F401
    assert any(
        "_qt.styles" in str(w.message) and issubclass(w.category, DeprecationWarning)
        for w in caught
    ), f"styles shim missing or silent; captured warnings: {[str(w.message) for w in caught]}"


def test_ui_helpers_shim_emits_deprecation():
    """ui_helpers.<name> -> _qt.ui_helpers.<name> (r2 batch 3 commit 2)."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        from ui_helpers import Debouncer  # noqa: F401
    assert any(
        "_qt.ui_helpers" in str(w.message) and issubclass(w.category, DeprecationWarning)
        for w in caught
    ), f"ui_helpers shim missing or silent; captured warnings: {[str(w.message) for w in caught]}"


def test_panels_hub_shim_emits_deprecation():
    """panels.<submod> -> _qt.panels.<submod> (r2 batch 3 commit 1 panels/__init__.py hub).

    The hub shim's __getattr__ catches the attribute-access pattern:
        import panels
        panels.view  # triggers __getattr__("view") which returns _qt.panels.view

    The `from panels.view import Y` pattern was handled by LibCST in B3 (which
    rewrote test_clip_domain.py:21 to `from _qt.panels.view import ViewPanel`).
    The hub shim is preserved for any out-of-tree callers (notebooks, scratch
    scripts) that may still use the bare `panels` namespace.
    """
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        import panels
        _ = panels.view  # triggers hub shim __getattr__
    assert any(
        "_qt.panels.view" in str(w.message) and issubclass(w.category, DeprecationWarning)
        for w in caught
    ), f"panels hub shim missing or silent; captured warnings: {[str(w.message) for w in caught]}"


def test_surfaces_private_kernel_reexport_works():
    """surfaces._fermat_field_kernel (private, _-prefixed) -> varieties._kernels (r2 batches 5-8).

    surfaces.py re-exports all 11 private kernel symbols at module top.
    This test verifies the back-compat path used by tests/test_numba_field_kernels.py.
    """
    from surfaces import _fermat_field_kernel  # noqa: F401
    assert _fermat_field_kernel is not None
    import varieties._kernels
    assert _fermat_field_kernel is varieties._kernels._fermat_field_kernel, (
        "surfaces re-export of _fermat_field_kernel is not identity-preserving"
    )


def test_surfaces_public_symbol_reexport_works():
    """surfaces.VARIETIES -> varieties.registry.VARIETIES (r2 batch 8 re-export)."""
    from surfaces import VARIETIES  # noqa: F401
    assert isinstance(VARIETIES, dict)
    from varieties.registry import VARIETIES as canonical
    assert VARIETIES is canonical, "surfaces.VARIETIES is not the canonical VARIETIES"
