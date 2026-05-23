# Implementation plan — mesh-export-stl-obj-ply-2026q3-e1

**Inline path. ~141 LOC across 3 files.** Lifts CONTEXT.md §9 "No 3D mesh export" non-goal. Adds File → Export Mesh… (Ctrl+E) action that saves `self._raw_mesh` to STL/OBJ/PLY via `pyvista.PolyData.save(path)`.

**Two load-bearing detail catches** from the researcher's audit:
1. `QAction` is already imported in `app.py`; `QFileDialog` is NOT — must add to the `PySide6.QtWidgets` import block.
2. `_clear_actor()` does NOT reset `self._raw_mesh`. So the export action must be explicitly disabled in `_on_variety_changed`'s placeholder-branch in addition to the obvious enable-on-success / disable-on-error sites in `_on_mesh_ready`. Otherwise the user could select "— Select —", get an empty viewport, click File → Export Mesh…, and silently save the prior surface (confusing UX).

1. **app.py — import block** —
   - Add `QFileDialog` to `from PySide6.QtWidgets import (...)`.
   ~1 LOC delta.

2. **app.py — `_build_file_menu()` method (new)** —
   - Adds the File menu via `menuBar().addMenu("&File")`.
   - Constructs `QAction("Export Mesh…", self)` with `Ctrl+E` shortcut and a tooltip covering: supported formats; raw-vs-clipped semantics; AI-15 caveats inheritance.
   - Starts disabled (`setEnabled(False)`).
   - Wires `triggered.connect(self._on_export_mesh)`.
   ~18 LOC delta.

3. **app.py — `_build_file_menu()` call in `__init__`** —
   - Insert before the existing `self._build_theme_menu()` call (~line 281) so File lands LEFT of Theme in the menu bar per Qt/macOS/Windows convention.
   ~3 LOC delta.

4. **app.py — `_on_export_mesh()` handler (new)** —
   - Defensive `if self._raw_mesh is None: return` guard.
   - Surface-named default filename (`f"{sanitised_label}.stl"`) sanitising spaces / slashes / brackets.
   - `QFileDialog.getSaveFileName` with filter `"STL files (*.stl);;OBJ files (*.obj);;PLY files (*.ply)"`.
   - Cancel branch: silent return on empty path.
   - Pre-validate extension (Qt does NOT auto-append on macOS/Linux) with statusBar feedback for missing extension.
   - `try: self._raw_mesh.save(path)` wrapped in broad `except Exception` (covers `PermissionError`, `FileNotFoundError`, `ValueError`, VTK IOError).
   - Success / failure both surface via `statusBar().showMessage`.
   ~30 LOC delta.

5. **app.py — setEnabled lifecycle wiring** —
   - `_on_mesh_ready` success path (after `self._raw_mesh = mesh`): `self._export_mesh_action.setEnabled(True)`.
   - `_on_mesh_ready` error path (after `self._raw_mesh = None`): `self._export_mesh_action.setEnabled(False)`.
   - `_on_variety_changed` placeholder branch (after `_clear_actor()`): `self._export_mesh_action.setEnabled(False)` — load-bearing (see §load-bearing details above).
   ~9 LOC delta.

6. **CONTEXT.md** —
   - §9 "No 3D mesh export" bullet replaced with "Mesh export — shipped" note covering key schema (the 3 formats + Ctrl+E + raw-vs-clipped + the lifecycle invariant).
   ~2 LOC delta.

7. **tests/test_mesh_export.py (new)** — 8 pure source-grep tests:
   - `test_app_has_file_menu`
   - `test_app_has_export_mesh_action`
   - `test_export_mesh_handler_uses_pyvista_save`
   - `test_export_mesh_uses_raw_mesh_not_clipped` (AI-15 contract guard)
   - `test_export_mesh_action_disabled_until_render` (positive + negative + position order)
   - `test_export_mesh_format_filter_includes_stl_obj_ply` (locks the 3 filter strings)
   - `test_export_mesh_failure_surfaces_to_status_bar` (try/except + showMessage)
   - `test_export_mesh_action_re_disabled_on_variety_clear` (load-bearing lifecycle invariant)
   ~80 LOC delta.

8. **Verify** —
   - `.venv/bin/pytest tests/ -q` → 8 new tests pass.
   - `.venv/bin/python -c "import app"` smoke check.
   - NO off-screen render verification needed (Qt menu chrome, not VTK).

9. **Commit** — `feat(mesh-export-stl-obj-ply-2026q3-e1): File → Export Mesh… (Ctrl+E) — STL/OBJ/PLY via mesh.save (CONTEXT.md §9 lift)`.
