"""Regression guards for File → Export Mesh… (STL/OBJ/PLY).

mesh-export-stl-obj-ply-2026q3-e1 (CONTEXT.md §9 lift): adds the File
menu's only action — Export Mesh… (Ctrl+E) — which saves
``self._raw_mesh`` via ``pyvista.PolyData.save(path)`` (format routed by
extension).

All tests are pure source-text greps on ``app.py`` (AI-2 / AI-3
compliant — no ``QApplication``, no ``MainWindow()``, no live
``QFileDialog`` show, no actual ``mesh.save`` write to the test
runner's filesystem).
"""
from __future__ import annotations

import pathlib


_APP_SRC = (
    pathlib.Path(__file__).resolve().parent.parent / "app.py"
).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 1. File menu added (and ampersand-escaped per Qt mnemonic convention)
# ---------------------------------------------------------------------------


def test_app_has_file_menu() -> None:
    """``app.py`` MUST add a "File" menu to the menu bar.  Either the
    bare-string ``addMenu("File")`` or the Qt mnemonic-escaped
    ``addMenu("&File")`` form is acceptable — Qt interprets the leading
    ``&`` as an Alt+F accelerator on Windows / Linux (and ignores it on
    macOS).
    """
    assert (
        'addMenu("&File")' in _APP_SRC
        or 'addMenu("File")' in _APP_SRC
    ), (
        "app.py must add a File menu via menuBar().addMenu(\"&File\") "
        "(or unescaped \"File\") — mesh-export-stl-obj-ply-2026q3-e1 "
        "places it leftmost (before Theme) per Qt / macOS / Windows "
        "convention."
    )


# ---------------------------------------------------------------------------
# 2. Export Mesh action present
# ---------------------------------------------------------------------------


def test_app_has_export_mesh_action() -> None:
    """The Export Mesh… action label must appear as a ``QAction`` arg.
    The ``…`` U+2026 ellipsis is the Apple HIG / Qt convention for
    "this action opens a dialog".
    """
    assert 'QAction("Export Mesh' in _APP_SRC, (
        "app.py must construct QAction(\"Export Mesh…\", self) — the "
        "ellipsis (U+2026) signals that the action opens a file dialog."
    )


# ---------------------------------------------------------------------------
# 3. Handler invokes PyVista save
# ---------------------------------------------------------------------------


def test_export_mesh_handler_uses_pyvista_save() -> None:
    """The ``_on_export_mesh`` handler MUST call ``.save(`` on a mesh
    object — that's the entire point of the milestone (PyVista routes
    format by extension; ``mesh.save("/tmp/x.stl")`` writes STL).
    """
    handler_start = _APP_SRC.find("def _on_export_mesh(")
    assert handler_start != -1, (
        "app.py must define a _on_export_mesh handler."
    )
    handler_end = _APP_SRC.find("\n    def ", handler_start + 1)
    body = _APP_SRC[handler_start:handler_end]
    assert ".save(" in body, (
        "_on_export_mesh must call mesh.save(path) — the entire purpose "
        "of the handler."
    )


# ---------------------------------------------------------------------------
# 4. Export target is raw mesh, NOT clipped mesh
# ---------------------------------------------------------------------------


def test_export_mesh_uses_raw_mesh_not_clipped() -> None:
    """**Load-bearing AI-15 contract:** the exported mesh MUST be
    ``self._raw_mesh`` (the unclipped marching-cubes / Flying-Edges +
    Taubin output) — NOT ``self._clipped_mesh``.  The domain clip is a
    *viewing* convention; downstream analysis tools should receive the
    canonical algebraic-variety surface.  A future refactor that
    silently swapped to clipped would create an honesty gap (the export
    no longer matches the variety the user asked for).
    """
    handler_start = _APP_SRC.find("def _on_export_mesh(")
    handler_end = _APP_SRC.find("\n    def ", handler_start + 1)
    body = _APP_SRC[handler_start:handler_end]
    assert "self._raw_mesh.save(" in body, (
        "_on_export_mesh must call self._raw_mesh.save(path) — the raw "
        "(unclipped) mesh is the canonical variety surface and what the "
        "milestone brief contracts for downstream analysis."
    )
    assert "self._clipped_mesh.save(" not in body, (
        "_on_export_mesh must NOT call self._clipped_mesh.save(...) — "
        "the domain clip is a viewing convention only, NOT a mesh-"
        "fidelity choice.  See CONTEXT.md §9 mesh-export bullet."
    )


# ---------------------------------------------------------------------------
# 5. setEnabled lifecycle: disabled at construction, enabled after first render
# ---------------------------------------------------------------------------


def test_export_mesh_action_disabled_until_render() -> None:
    """The export action MUST start disabled and only become enabled
    after a successful ``_on_mesh_ready`` (so the user cannot export
    before any surface has been generated; would crash on
    ``None.save(path)``).  Source-position guarantees the construction-
    site disable precedes the success-path enable in the source.
    """
    disabled_pos = _APP_SRC.find(
        "self._export_mesh_action.setEnabled(False)"
    )
    enabled_pos = _APP_SRC.find(
        "self._export_mesh_action.setEnabled(True)"
    )
    assert disabled_pos != -1, (
        "app.py must call self._export_mesh_action.setEnabled(False) "
        "at construction in _build_file_menu — the action must start "
        "disabled."
    )
    assert enabled_pos != -1, (
        "app.py must call self._export_mesh_action.setEnabled(True) "
        "in _on_mesh_ready's success path — the action becomes "
        "available the moment a valid raw mesh exists."
    )
    assert disabled_pos < enabled_pos, (
        "The construction-time setEnabled(False) (in _build_file_menu) "
        "must appear in the source BEFORE the first setEnabled(True) "
        "(in _on_mesh_ready success path) — protects against a future "
        "refactor that reverses the initial state."
    )


# ---------------------------------------------------------------------------
# 6. Format filter includes all three formats with the canonical strings
# ---------------------------------------------------------------------------


def test_export_mesh_format_filter_includes_stl_obj_ply() -> None:
    """The ``QFileDialog.getSaveFileName`` filter MUST offer STL, OBJ,
    AND PLY (the three formats the milestone contracts).  Locking the
    exact display strings prevents a silent rename like "STL files" →
    "STL meshes" which would break user-visible expectations.
    """
    assert "STL files (*.stl)" in _APP_SRC, (
        "app.py must include 'STL files (*.stl)' in the QFileDialog filter."
    )
    assert "OBJ files (*.obj)" in _APP_SRC, (
        "app.py must include 'OBJ files (*.obj)' in the QFileDialog filter."
    )
    assert "PLY files (*.ply)" in _APP_SRC, (
        "app.py must include 'PLY files (*.ply)' in the QFileDialog filter."
    )


# ---------------------------------------------------------------------------
# 7. Failure surfaces to status bar via try/except + showMessage
# ---------------------------------------------------------------------------


def test_export_mesh_failure_surfaces_to_status_bar() -> None:
    """The handler MUST wrap ``mesh.save()`` in a ``try/except`` so
    ``PermissionError`` / ``FileNotFoundError`` / ``ValueError`` (bad
    extension) / VTK IOError don't crash the app, and MUST surface the
    failure via ``statusBar().showMessage`` so the user knows the save
    didn't happen (silent failure would be the worst UX outcome).
    """
    handler_start = _APP_SRC.find("def _on_export_mesh(")
    handler_end = _APP_SRC.find("\n    def ", handler_start + 1)
    body = _APP_SRC[handler_start:handler_end]
    assert "try:" in body, (
        "_on_export_mesh must wrap mesh.save() in try/except — "
        "PermissionError / FileNotFoundError / ValueError otherwise "
        "crash the app."
    )
    assert "except" in body, (
        "_on_export_mesh must have an except clause paired with the try."
    )
    assert "showMessage" in body, (
        "_on_export_mesh must surface success AND failure via "
        "statusBar().showMessage — silent failure would be the worst "
        "UX outcome (user thinks save succeeded but file isn't there)."
    )


# ---------------------------------------------------------------------------
# 8. Variety-clear path re-disables the action
# ---------------------------------------------------------------------------


def test_export_mesh_action_re_disabled_on_variety_clear() -> None:
    """**Load-bearing lifecycle invariant:** when the user selects the
    "— Select —" placeholder (``_on_variety_changed`` else branch), the
    export action MUST be re-disabled.  ``_clear_actor`` does NOT reset
    ``self._raw_mesh`` (see CONTEXT.md §9 mesh-export bullet), so
    without the explicit disable here the user could click File →
    Export Mesh… after going back to the placeholder and silently save
    the prior surface — a confusing "I exported the empty viewport but
    got an Enriques mesh" behavior.
    """
    method_start = _APP_SRC.find("def _on_variety_changed(")
    assert method_start != -1, (
        "app.py must define _on_variety_changed."
    )
    method_end = _APP_SRC.find("\n    def ", method_start + 1)
    body = _APP_SRC[method_start:method_end]
    assert (
        "self._export_mesh_action.setEnabled(False)" in body
    ), (
        "_on_variety_changed's else branch (placeholder selected) "
        "must call self._export_mesh_action.setEnabled(False) — "
        "_clear_actor does NOT reset self._raw_mesh, so without this "
        "explicit disable the user could silently export the prior "
        "surface from the empty viewport."
    )
