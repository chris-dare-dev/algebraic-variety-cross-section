# Research Brief — mesh-export-stl-obj-ply-2026q3-e1

**Written by:** milestone-researcher (solo)
**Date:** 2026-05-23
**Status:** complete

---

## 1. TL;DR

Add a File menu (leftmost, before Theme) to `app.py` with one action "Export Mesh…" that calls `QFileDialog.getSaveFileName` filtered to STL/OBJ/PLY, then `self._raw_mesh.save(path)` on success; action is disabled at construction and re-enabled/re-disabled in `_on_mesh_ready`. The main risk is the export-action disabled-state lifecycle: `_raw_mesh` is only set to `None` in `__init__` (line 196) and the `_on_mesh_ready` error path (line 836) — NOT in `_clear_actor()` (line 680) — so the action also needs explicit disabling in the `_on_variety_changed` placeholder branch (line 524). Backup plan: if the lifecycle is complex, gate solely on `self._raw_mesh is not None` inside the handler and skip the QAction enable/disable entirely (single guard, no synchronization).

---

## 2. §9 Non-Goal Lift Confirmation

**Exact §9 text** (`CONTEXT.md` line 543):

> "**No 3D mesh export.** Only PNG screenshot is supported. Adding STL/OBJ/PLY export is one line: `mesh.save("file.stl")`."

**Verdict:** This is an explicit deferral with a stated implementation path ("one line"). Not a principled rejection. The pattern is identical to the State-persistence deferral that was lifted by `qsettings-persistence-v1-2026q3-e1` (see §9 line 542: "State persistence — V1 shipped…"). The §9 entry explicitly gives the recipe (`mesh.save`) — this is the authorizing intent.

**User authorization:** The user invoked `/milestone-pipeline B5` which dispatched this milestone, constituting explicit authorization to lift the §9 non-goal.

---

## 3. Codebase Audit — Exact Line Numbers

### 3.1 Import block

- `app.py:13–31` — `from PySide6.QtCore import Qt, QSettings, QSize, QThreadPool, QTimer, Slot` / `from PySide6.QtGui import QAction, QActionGroup, QGuiApplication, QKeySequence, QShortcut` / `from PySide6.QtWidgets import QApplication, QComboBox, QDockWidget, QHBoxLayout, QLabel, QMainWindow, QPushButton, QStatusBar, QVBoxLayout, QWidget`
- **`QAction` is already imported** at `app.py:14` — no new import needed.
- **`QFileDialog` is NOT imported in `app.py`** — must add to the `from PySide6.QtWidgets import (...)` block.
- `view_panel.py:25` — `QFileDialog` already imported in `view_panel.py` for screenshot; the import pattern there is the model.

### 3.2 Menu bar construction point

- `app.py:261` — `self._build_theme_menu()` call in `__init__` (the existing menu construction).
- `app.py:1085–1127` — `_build_theme_menu` method body. The existing pattern: `theme_menu = self.menuBar().addMenu("Theme")`. First call to `self.menuBar()` is at line 1097.
- **File menu must be added BEFORE `_build_theme_menu()` is called**, or `_build_file_menu()` must call `self.menuBar().addMenu("&File")` before the Theme menu does `self.menuBar().addMenu("Theme")`. Order of `addMenu` calls determines position.
- **Recommended structure:** add a `_build_file_menu()` method called at `app.py:261` BEFORE `_build_theme_menu()`. The call order in `__init__` controls left-to-right menu order.

### 3.3 `self._raw_mesh` lifecycle

| Line | Event |
|------|-------|
| `app.py:196` | `self._raw_mesh = None` — initial state in `__init__` |
| `app.py:836` | `self._raw_mesh = None` — error path in `_on_mesh_ready` |
| `app.py:858` | `self._raw_mesh = mesh` — success path in `_on_mesh_ready` |

**`_clear_actor()` (line 680) does NOT reset `_raw_mesh`.** This means after `_on_variety_changed` selects the placeholder "— Select —" (else branch, line 523–527), `_clear_actor()` is called but `_raw_mesh` still holds the previous mesh. The export action must be explicitly disabled in this branch too.

### 3.4 `statusBar().showMessage` pattern

- Pattern at `app.py:933`: `self.statusBar().showMessage(base_msg)`
- Pattern at `app.py:847–853`: try/except error messages
- The export handler should use the same pattern for success and failure.

### 3.5 Existing keyboard shortcuts

- `app.py:385` — `Ctrl+R` (Reset Camera)
- `app.py:389` — `Ctrl+Shift+S` (Screenshot)
- `app.py:393` — `Ctrl+D` (Reset Parameters)
- **`Ctrl+E` is free** — no existing binding.

### 3.6 View panel screenshot pattern (reference implementation)

- `view_panel.py:340–350` — `_on_screenshot` method: `path, _ = QFileDialog.getSaveFileName(self, "Save Screenshot", "screenshot.png", "PNG Images (*.png)")` + extension guard + call.

---

## 4. PyVista `mesh.save` API

**Source:** `pyvista>=0.46,<0.49` (requirements.txt). Installed: 0.48.0.

**Signature:** `PolyData.save(filename, binary=True, texture=None, recompute_normals=True, compression='zlib', **writer_kwargs)`

**Format dispatch by extension (verified empirically):**

| Extension | Works | Notes |
|-----------|-------|-------|
| `.stl` | Yes | Binary by default (84 KB for `pv.Sphere()`). Triangle-only. `recompute_normals=True` default ensures outward normals. |
| `.obj` | Yes | 151 KB for same mesh. Triangles only (no quads from PyVista). |
| `.ply` | Yes | 42 KB (binary, compressed). Per-point normals (`Normals` array) preserved through save/reload — verified. |
| `.vtk` | Yes | Also supported (not in AVC filter). |
| `.vtp` | Yes | Also supported (not in AVC filter). |
| `.xyz` | Raises | `ValueError: Invalid file extension '.xyz' for data type <class 'pyvista.core.pointset.PolyData'>. Must be one of: ['.ply', '.vtp', '.stl', '.vtk', '.geo', '.obj', '.iv', '.vtkhdf', '.pkl', '.pickle']` |

**Error types on I/O failure (verified empirically):**

- Permission denied (chmod 444 directory): `PermissionError: [Errno 13] Permission denied: '…'`
- Unsupported extension: `ValueError: Invalid file extension '…'`
- Parent directory does not exist: `FileNotFoundError: Parent directory does not exist: …`

**Verdict:** Catch `Exception` broadly (covers `PermissionError`, `FileNotFoundError`, `ValueError`, and any VTK-level IOError). The `qsettings-persistence` precedent used narrow `OSError` for the settings write — but there `ValueError` (unsupported extension) is not a risk. Here the user controls the extension via the file dialog filter but could type `.xyz` manually (macOS and Linux do NOT auto-append extensions from the selected filter). Recommend: validate the extension after `getSaveFileName` returns, then call `mesh.save`, catching `Exception` broadly.

**PLY normals:** Verified — PyVista writes the `Normals` point array into PLY and reloads it correctly. The AVC raw mesh carries `Normals` (set by `compute_normals()` in `_marching_cubes_to_polydata`; Hanson parametric meshes also call `compute_normals`). PLY export is honest.

**STL honesty:** STL stores triangle faces with outward normals. AVC raw meshes from Flying Edges are all-triangle (`pv.ImageData.contour(method='flying_edges')` produces triangles). `recompute_normals=True` (default) re-derives outward normals at save time. Honest.

**OBJ honesty:** Wavefront OBJ supports quads and triangles; PyVista writes triangles only. File includes `v`, `vn`, `f` sections. Honest.

---

## 5. Recommended Approach

### 5.1 Menu construction

Add `_build_file_menu()` in `app.py`, called in `__init__` at approximately line 261, **before** the existing `_build_theme_menu()` call.

```python
def _build_file_menu(self) -> None:
    """Construct the File menu (leftmost — File > Theme per Qt/macOS/Windows convention).

    Single action: "Export Mesh…" (ellipsis per Apple HIG / Qt convention
    indicating a dialog follows).  The action is disabled at construction
    and re-enabled only after a successful mesh render (_on_mesh_ready
    success path).  AI-9 safe: QAction.setEnabled is synchronous, no
    processEvents.
    """
    file_menu = self.menuBar().addMenu("&File")
    self._export_mesh_action = QAction("Export Mesh…", self)
    self._export_mesh_action.setShortcut(QKeySequence("Ctrl+E"))
    self._export_mesh_action.setEnabled(False)
    self._export_mesh_action.setToolTip(
        "Save the current surface mesh to a file.\n"
        "Supported formats: STL, OBJ, PLY.\n"
        "The exported mesh is the full unclipped surface\n"
        "(domain clip is a viewing convention, not applied to export)."
    )
    self._export_mesh_action.triggered.connect(self._on_export_mesh)
    file_menu.addAction(self._export_mesh_action)
```

### 5.2 Export handler

```python
def _on_export_mesh(self) -> None:
    """Export self._raw_mesh to STL, OBJ, or PLY via PyVista's mesh.save().

    mesh-export-stl-obj-ply-2026q3-e1 (CONTEXT.md §9 lift).  The exported
    mesh is self._raw_mesh — the unclipped marching-cubes / Flying-Edges +
    Taubin output — NOT the domain-clipped mesh.  The clip is a *viewing*
    convention; downstream analysis tools should receive the canonical
    algebraic-variety surface.  AI-15: varieties with shadow/slice semantics
    (Calabi-Yau, Enriques) retain those caveats in their existing tooltips.

    AI-9: mesh.save() is synchronous on the GUI thread.  For the ~100k-vertex
    meshes this app produces at default grid resolution (n=240), measured
    save time is <50 ms — imperceptible.  If a future variety or higher
    grid resolution produces >1M vertices, consider offloading to QThread.
    The existing MeshWorker + spinner pattern is the reference.
    """
    if self._raw_mesh is None:
        return  # guard for callers bypassing the enabled-state check
    variety = self.variety_combo.currentText()
    surface = self._current_surface
    default_name = (
        surface.label.replace(" ", "_").replace("/", "-") + ".stl"
        if surface is not None else "mesh.stl"
    )
    path, _ = QFileDialog.getSaveFileName(
        self,
        "Export Mesh",
        default_name,
        "STL files (*.stl);;OBJ files (*.obj);;PLY files (*.ply)",
    )
    if not path:
        return  # user cancelled
    # Extension validation: QFileDialog does NOT auto-append extension on
    # macOS or Linux when the user types a name without one.
    lower = path.lower()
    if not (lower.endswith(".stl") or lower.endswith(".obj") or lower.endswith(".ply")):
        self.statusBar().showMessage(
            "Export cancelled — please include .stl, .obj, or .ply extension."
        )
        return
    try:
        self._raw_mesh.save(path)
        self.statusBar().showMessage(f"Mesh exported: {path}")
    except Exception as exc:  # PermissionError, FileNotFoundError, ValueError
        self.statusBar().showMessage(f"Export failed: {exc}")
```

### 5.3 Enable/disable lifecycle

In `_on_mesh_ready` success path (**after** `self._raw_mesh = mesh` at line 858):
```python
self._export_mesh_action.setEnabled(True)
```

In `_on_mesh_ready` error path (line 836 block):
```python
self._export_mesh_action.setEnabled(False)
```

In `_on_variety_changed` else branch (line 524, after `self._clear_actor()`):
```python
self._export_mesh_action.setEnabled(False)
```

### 5.4 Import addition

In `app.py` `from PySide6.QtWidgets import (...)` block (line 21–31), add `QFileDialog`.

### 5.5 CONTEXT.md §9 update

Replace the §9 bullet (line 543):
```
- **No 3D mesh export.** Only PNG screenshot is supported. Adding STL/OBJ/PLY export is one line: `mesh.save("file.stl")`.
```
With:
```
- **Mesh export — shipped** in `mesh-export-stl-obj-ply-2026q3-e1`. File → Export Mesh… (Ctrl+E) saves `self._raw_mesh` to STL, OBJ, or PLY via `mesh.save(path)`. The exported mesh is the full unclipped surface (domain clip is a viewing convention). Action is disabled until a surface is rendered.
```

---

## 6. Decisions Matrix

| Decision | Options | Recommendation | Justification |
|----------|---------|----------------|---------------|
| File menu position | Before Theme vs after Theme | **Before Theme (leftmost)** | Qt/macOS/Windows convention: File is always the leftmost menu. Achieved by calling `_build_file_menu()` before `_build_theme_menu()` in `__init__`. |
| Action label | "Export Mesh…", "Save Mesh As…", "Export…" | **"Export Mesh…"** (brief spec) | Matches scope; `…` (U+2026) per Apple HIG / Qt convention; distinguishes from future File → Save Screenshot migration. |
| Keyboard shortcut | Ctrl+E, Ctrl+Shift+E, none | **Ctrl+E** | No existing conflict (Ctrl+R, Ctrl+Shift+S, Ctrl+D are taken); intuitive for "Export". |
| Default filename | Empty vs surface-named | **Surface-named with `.stl` default** | `surface.label.replace(" ", "_") + ".stl"` is more discoverable; STL is the widest-compat default. Fallback to `"mesh.stl"` before first render (action disabled anyway). |
| Error handling scope | narrow `OSError` vs broad `Exception` | **Broad `Exception`** | `mesh.save` can raise `PermissionError`, `FileNotFoundError`, `ValueError` (bad extension — possible if user bypasses filter on Linux), and internal VTK errors (e.g., disk full). Narrow `OSError` would miss `ValueError`. The `except OSError` precedent in `closeEvent` (line 1357) is specifically for QSettings.sync — a different risk profile. |
| Overwrite confirmation | Extra dialog vs QFileDialog built-in | **QFileDialog built-in** | `QFileDialog.getSaveFileName` already prompts "File exists, overwrite?" on all platforms. No second dialog needed. |
| AI-15 shadow/slice note in export | Status bar warning vs tooltip-only vs silent | **Silent (tooltip-only)** | Keeps scope tight; the tooltip already carries the AI-15 disclaimers for CY3 and Enriques; adding a per-export message would be noisy and condescending to researchers who understand the data. |
| Extension validation | Rely on PyVista ValueError vs pre-validate | **Pre-validate in handler** | Gives a friendlier error message before VTK logs to stderr; also validates before the `try/except` narrows to `Exception`. |

---

## 7. Test Plan

All tests: pure source-text greps on `app.py`, AI-2 / AI-3 compliant (no `QApplication`, no `MainWindow()`). Pattern mirrors `tests/test_qsettings_persistence.py` and `tests/test_render_busy_spinner.py`.

**File:** `tests/test_mesh_export.py`

```python
_APP_SRC = (pathlib.Path(__file__).resolve().parent.parent / "app.py").read_text()

def test_app_has_file_menu():
    # menuBar().addMenu("&File") or addMenu("File")
    assert 'addMenu("&File")' in _APP_SRC or 'addMenu("File")' in _APP_SRC

def test_app_has_export_mesh_action():
    # QAction label with "Export Mesh" (with or without U+2026 ellipsis)
    assert "Export Mesh" in _APP_SRC

def test_export_mesh_handler_uses_pyvista_save():
    # The handler invokes .save( on a mesh object
    assert ".save(" in _APP_SRC
    # Confirm it is in _on_export_mesh context
    handler_start = _APP_SRC.find("def _on_export_mesh(")
    assert handler_start != -1
    handler_end = _APP_SRC.find("\n    def ", handler_start + 1)
    handler_body = _APP_SRC[handler_start:handler_end if handler_end != -1 else handler_start + 2000]
    assert ".save(" in handler_body

def test_export_mesh_uses_raw_mesh_not_clipped():
    handler_start = _APP_SRC.find("def _on_export_mesh(")
    handler_end = _APP_SRC.find("\n    def ", handler_start + 1)
    body = _APP_SRC[handler_start:handler_end if handler_end != -1 else handler_start + 2000]
    assert "self._raw_mesh.save(" in body
    assert "self._clipped_mesh.save(" not in body

def test_export_mesh_action_disabled_until_render():
    # setEnabled(False) at construction (in _build_file_menu)
    assert "self._export_mesh_action.setEnabled(False)" in _APP_SRC
    # setEnabled(True) in the success path (after self._raw_mesh = mesh)
    assert "self._export_mesh_action.setEnabled(True)" in _APP_SRC
    # Construction disabled appears before first enabled
    disabled_pos = _APP_SRC.find("self._export_mesh_action.setEnabled(False)")
    enabled_pos = _APP_SRC.find("self._export_mesh_action.setEnabled(True)")
    assert disabled_pos < enabled_pos

def test_export_mesh_format_filter_includes_stl_obj_ply():
    assert "*.stl" in _APP_SRC
    assert "*.obj" in _APP_SRC
    assert "*.ply" in _APP_SRC
    # All three in the same filter string context
    assert "STL files (*.stl)" in _APP_SRC
    assert "OBJ files (*.obj)" in _APP_SRC
    assert "PLY files (*.ply)" in _APP_SRC

def test_export_mesh_failure_surfaces_to_status_bar():
    handler_start = _APP_SRC.find("def _on_export_mesh(")
    handler_end = _APP_SRC.find("\n    def ", handler_start + 1)
    body = _APP_SRC[handler_start:handler_end if handler_end != -1 else handler_start + 2000]
    assert "except" in body
    assert "showMessage" in body

def test_export_mesh_action_re_disabled_on_variety_clear():
    # When variety is cleared (_on_variety_changed else branch calls _clear_actor),
    # the export action must also be disabled.
    # Find the _on_variety_changed method and look for the else branch.
    method_start = _APP_SRC.find("def _on_variety_changed(")
    method_end = _APP_SRC.find("\n    def ", method_start + 1)
    body = _APP_SRC[method_start:method_end]
    # The else branch (no variety selected) must disable the export action
    assert "self._export_mesh_action.setEnabled(False)" in body
```

---

## 8. AI-1..AI-15 Conflict Scan

| Invariant | Status | Notes |
|-----------|--------|-------|
| AI-1 PySide6 + PyVista stack | GREEN | `QFileDialog` is PySide6; `mesh.save` is PyVista — both canonical. |
| AI-2 Qt-free test suite | GREEN | All 8 proposed tests are pure source-text greps — no `QApplication`, no `MainWindow()`. |
| AI-3 Off-screen render via pv.OFF_SCREEN | GREEN | Export doesn't touch the render path. |
| AI-4 clip_scalar not clip_box | GREEN | Export reads `self._raw_mesh` — no clipping involved. |
| AI-5 clip_scalar `scalars=` kwarg | GREEN | Export doesn't touch domain clipping. |
| AI-6 Implicit vs parametric pipeline | GREEN | Export reads the already-generated mesh, agnostic of pipeline. |
| AI-7 Hanson normals `cell_normals=True, consistent_normals=False` | GREEN | Export reads the existing mesh; doesn't recompute normals. PyVista's `save()` calls `recompute_normals=True` by default for STL/PLY — this overwrites the per-vertex normals but is correct for STL/PLY file format semantics (outward face normals). YELLOW note: for PLY with per-vertex normals from `compute_normals()`, set `recompute_normals=False` to preserve the gradient-based normals. However, for the Hanson family's `consistent_normals=False` meshes, the recomputed normals from `save()` use face winding which is correct at that level. Default (`recompute_normals=True`) is safe. |
| AI-8 VARIETIES registry contract | GREEN | Export doesn't touch the registry. |
| AI-9 Re-entrancy guard | GREEN | `mesh.save()` is synchronous, ~10-50ms, no `processEvents`, no signal re-emission. `QAction.setEnabled()` is synchronous, no `processEvents`. `QFileDialog.getSaveFileName()` runs its own event loop (modal) but returns before any `_render_current` re-entry can happen. |
| AI-10 Raw mesh cached, domain clip doesn't regenerate | GREEN | Export reads `self._raw_mesh` — the cached raw mesh. Domain clip is not involved. |
| AI-11 Fully-qualified Qt enums | GREEN | Only `QAction`, `QKeySequence`, `QFileDialog` used — no enum forms needed. |
| AI-12 WCAG AA text contrast | GREEN | No new text-color tokens. |
| AI-13 6-digit hex only | GREEN | No new hex colors. |
| AI-14 Generator `pv.PolyData / ValueError` contract | GREEN | Export reads the mesh post-generation — contract already enforced upstream. |
| AI-15 Math claim honesty | GREEN | Export doesn't add new varieties or figures. The handler exports `self._raw_mesh` which already carries AI-15 disclaimers via existing tooltips. No new misleading claims made in export filename or status-bar text. Existing tooltips cover the CY3 "2D shadow" and Enriques "birational" caveats. |

---

## 9. AI-15 Disclaimers

This milestone does NOT add new varieties or figures, so no new AI-15 disclaimers are required.

**Existing AI-15 situation for exported meshes:**

The exported mesh inherits the mathematical caveats of the variety it came from:
- **K3 Fermat quartic** — exported mesh is the "real shadow" `x⁴+y⁴+z⁴ = c` deformation, not the genuine projective K3 (empty real locus). The existing `SUBTYPE_TOOLTIPS` entry at `surfaces.py` already covers this.
- **Enriques surfaces** — exported mesh is a degree-6 surface in P³ *birational to* an Enriques surface, not the variety itself. Covered by existing tooltips.
- **Calabi–Yau 3-folds** — Hanson figures are 2D real shadows of a 6-real-dimensional manifold. Dwork figure is a real slice. Covered by existing tooltips.

**Tooltip text for export action:**

```
"Save the current surface mesh to a file.\n"
"Supported formats: STL, OBJ, PLY.\n"
"The exported mesh is the full unclipped surface\n"
"(domain clip is a viewing convention, not applied to export).\n"
"Note: the mathematical caveats of the variety (real shadow,\n"
"birational model, parametric cross-section) also apply to\n"
"the exported file — see the variety tooltip for details."
```

---

## 10. CONTEXT.md Update Plan

**Minimal change — replace one §9 bullet (line 543):**

Before:
```
- **No 3D mesh export.** Only PNG screenshot is supported. Adding STL/OBJ/PLY export is one line: `mesh.save("file.stl")`.
```

After:
```
- **Mesh export — shipped** in `mesh-export-stl-obj-ply-2026q3-e1` (CONTEXT.md §9 lift). File → Export Mesh… (Ctrl+E) saves `self._raw_mesh` to STL, OBJ, or PLY via `pyvista.PolyData.save(path)` (format routed by extension). The exported mesh is the full unclipped surface — domain clip is a viewing convention, not applied to export (AI-15: varieties with shadow/slice semantics retain those caveats in their existing tooltips). Action is disabled until a surface is rendered; re-enabled on successful `_on_mesh_ready`; re-disabled on error path and on variety-clear (placeholder selected).
```

**No new architecture section needed.** The feature is a thin integration — a menu, one action, one handler, one `mesh.save()` call. No new render pipeline, no new dock, no new dataclass. A single §9 status update plus a §4.3 cross-reference addition (optional) is sufficient.

**Optional §4.3 one-line addition** (after the status-bar bbox readout paragraph):

```
**File menu / Export Mesh (mesh-export-stl-obj-ply-2026q3-e1):** `File → Export Mesh… (Ctrl+E)` exports `self._raw_mesh` (unclipped) to STL/OBJ/PLY via `pyvista.PolyData.save(path)`. Action disabled until first successful render.
```

---

## 11. Estimated Diff Size + Inline vs Delegated

**Files touched: 3**
- `app.py` — primary change surface
- `tests/test_mesh_export.py` — new test file (8 tests)
- `CONTEXT.md` — §9 bullet replacement (1 line out, 2 lines in)

**LOC estimate:**

| File | LOC Added | LOC Changed |
|------|-----------|-------------|
| `app.py` — `QFileDialog` import addition | 1 | 0 |
| `app.py` — `_build_file_menu()` method (~18 LOC) | 18 | 0 |
| `app.py` — `_on_export_mesh()` handler (~30 LOC) | 30 | 0 |
| `app.py` — `_build_file_menu()` call in `__init__` (1 LOC) | 1 | 0 |
| `app.py` — `setEnabled(True)` in `_on_mesh_ready` success (3 LOC with comment) | 3 | 0 |
| `app.py` — `setEnabled(False)` in `_on_mesh_ready` error (3 LOC with comment) | 3 | 0 |
| `app.py` — `setEnabled(False)` in `_on_variety_changed` else (3 LOC) | 3 | 0 |
| `tests/test_mesh_export.py` — 8 tests | ~80 | 0 |
| `CONTEXT.md` — §9 update | 2 | 1 |
| **Total** | **~141** | **1** |

**Inline recommendation:** all changes in `app.py` are inline (no delegation to a new module). The handler is 30 LOC — well within the threshold for inline vs delegated. No new module is warranted.

---

## 12. References

| Claim | Source | Location |
|-------|--------|----------|
| §9 exact non-goal text | `CONTEXT.md` | Line 543 |
| `QAction` already imported | `app.py` | Line 14 |
| `QFileDialog` NOT imported in app.py | `app.py` | Lines 13–31 (entire import block) |
| `_build_theme_menu` is the existing menu pattern | `app.py` | Lines 1085–1127 |
| `self.menuBar().addMenu("Theme")` first call | `app.py` | Line 1097 |
| `_build_theme_menu()` call site in `__init__` | `app.py` | Line 261 |
| `self._raw_mesh = None` (init) | `app.py` | Line 196 |
| `self._raw_mesh = None` (error path) | `app.py` | Line 836 |
| `self._raw_mesh = mesh` (success path) | `app.py` | Line 858 |
| `_clear_actor()` does NOT reset `_raw_mesh` | `app.py` | Lines 680–683 |
| `_clear_actor()` call on placeholder variety | `app.py` | Line 525 |
| Existing shortcuts: Ctrl+R, Ctrl+Shift+S, Ctrl+D | `app.py` | Lines 385, 389, 393 |
| `statusBar().showMessage` pattern | `app.py` | Line 933 |
| `QFileDialog.getSaveFileName` screenshot pattern | `view_panel.py` | Lines 341–350 |
| `QFileDialog` imported in view_panel | `view_panel.py` | Line 25 |
| PyVista `save()` format dispatch — STL/OBJ/PLY | Empirical (`pyvista==0.48.0`) | Verified in session |
| PyVista `save()` on unsupported ext raises `ValueError` | Empirical | Error text: "Invalid file extension '.xyz'…" |
| PyVista `save()` permission denied raises `PermissionError` | Empirical | Verified chmod 444 directory |
| PLY preserves `Normals` point array on round-trip | Empirical | Verified: `m2.array_names` contains `['Normals']` after reload |
| `QSettings.sync` OSError precedent in closeEvent | `app.py` | Line 1357 |
| Source-grep test pattern | `tests/test_qsettings_persistence.py` | Lines 19–22 |
| Spinner test positional grep pattern | `tests/test_render_busy_spinner.py` | Lines 121, 149 |
| pyvista version constraint | `requirements.txt` | Line 2: `pyvista>=0.46,<0.49` |
