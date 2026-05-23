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
    AND PLY (the three formats the milestone contracts).

    rect MEDIUM (adversary critic): relaxed from the over-specific
    ``"STL files (*.stl)"`` triplet to the glob-only triplet ``"*.stl"``
    / ``"*.obj"`` / ``"*.ply"``.  The behavioral contract is the format
    set, not the human-readable display label.  A valid relabel like
    ``"STL files (*.stl)"`` → ``"Stereolithography (*.stl)"`` would
    have broken the prior tests without breaking any behavior.
    """
    # The three globs each must appear (in the filter or the
    # extension-validation branch — both anchor the contract).
    assert "*.stl" in _APP_SRC, (
        "app.py must reference the *.stl glob (in the QFileDialog "
        "filter, the extension-validation branch, or both)."
    )
    assert "*.obj" in _APP_SRC, (
        "app.py must reference the *.obj glob."
    )
    assert "*.ply" in _APP_SRC, (
        "app.py must reference the *.ply glob."
    )
    # The filter-string separator triple anchors the structural
    # ordering: STL is offered first as the default, then OBJ, then
    # PLY.  This catches accidental filter reordering or drop.
    assert "(*.stl);;" in _APP_SRC and ";;" in _APP_SRC, (
        "QFileDialog filter MUST list the three formats separated by "
        "Qt's `;;` separator — the order and triple are the "
        "structurally meaningful contract."
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


# ---------------------------------------------------------------------------
# rect Phase 4 regression guards
# ---------------------------------------------------------------------------


def test_export_mesh_tracks_coarse_fidelity_for_ai15_disclosure() -> None:
    """rect MEDIUM (cross-critic AI-15) regression guard: ``app.py``
    MUST track ``self._raw_mesh_is_coarse`` parallel to ``self._raw_mesh``
    so the export handler can disclose draft-resolution exports in
    BOTH the suggested filename (``_preview`` suffix) and the success
    status-bar message.  Without this flag the export silently writes
    a coarse n=80 approximation when triggered mid-drag — an AI-15
    honesty gap both Phase 3 critics independently flagged.
    """
    # Attribute MUST be initialized in __init__.
    assert "self._raw_mesh_is_coarse: bool = False" in _APP_SRC or (
        "self._raw_mesh_is_coarse = False" in _APP_SRC
    ), (
        "app.py must initialize self._raw_mesh_is_coarse in __init__ "
        "(the LOD-fidelity flag parallel to self._raw_mesh)."
    )
    # Set in _on_mesh_ready success path alongside the _raw_mesh
    # assignment (both branches — coarse AND full — update the flag).
    assert "self._raw_mesh_is_coarse = bool(result.is_coarse)" in _APP_SRC, (
        "_on_mesh_ready success path must set self._raw_mesh_is_coarse "
        "to bool(result.is_coarse) immediately after self._raw_mesh = "
        "mesh — keeps the LOD flag in sync with the mesh it describes."
    )
    # Used in _on_export_mesh to annotate either the filename or the
    # success message (or both).
    handler_start = _APP_SRC.find("def _on_export_mesh(")
    handler_end = _APP_SRC.find("\n    def ", handler_start + 1)
    body = _APP_SRC[handler_start:handler_end]
    assert "self._raw_mesh_is_coarse" in body, (
        "_on_export_mesh must read self._raw_mesh_is_coarse to "
        "disclose draft-resolution exports (in the suggested "
        "filename, success message, or both)."
    )


def test_export_mesh_success_message_uses_basename_not_full_path() -> None:
    """rect MEDIUM-1 (frontend critic) regression guard: the success
    status-bar message MUST use ``os.path.basename(path)``, NOT the
    full path.  The full path is the canonical case where the ~120-
    char QStatusBar visible-clip band silently truncates the most-
    informative trailing component (the filename itself) on macOS /
    Windows cloud-storage paths.
    """
    handler_start = _APP_SRC.find("def _on_export_mesh(")
    handler_end = _APP_SRC.find("\n    def ", handler_start + 1)
    body = _APP_SRC[handler_start:handler_end]
    assert "os.path.basename(path)" in body or "basename(path)" in body, (
        "_on_export_mesh's success message MUST use os.path.basename "
        "(or pathlib equivalent), NOT the full path — QStatusBar's "
        "~120-char visible-clip band would silently truncate the "
        "filename on deep cloud-storage paths."
    )


def test_export_mesh_auto_appends_extension_from_selected_filter() -> None:
    """rect MEDIUM-2 (frontend critic) regression guard: when the
    user types a bare filename (no .stl/.obj/.ply suffix — Qt does
    NOT auto-append on macOS/Linux), the handler MUST parse the
    selected filter and auto-append.  This matches MeshLab / Blender /
    GIMP / Inkscape's behavior and removes a workflow interruption.
    """
    handler_start = _APP_SRC.find("def _on_export_mesh(")
    handler_end = _APP_SRC.find("\n    def ", handler_start + 1)
    body = _APP_SRC[handler_start:handler_end]
    # The selected_filter return value must be CAPTURED (not _selected_filter
    # underscored) and USED via re.search for the extension glob.
    assert "selected_filter" in body and "_selected_filter" not in body, (
        "The dialog's return value must be captured as selected_filter "
        "(not _selected_filter — the leading underscore signals "
        "intentionally-unused and is incorrect now that the handler "
        "auto-appends from the filter)."
    )
    # The extension-glob regex MUST be present.
    assert "re.search" in body and "selected_filter" in body, (
        "Handler MUST regex-extract the extension glob from "
        "selected_filter to auto-append when the user types a bare "
        "filename — see rect MEDIUM-2 (frontend critic)."
    )


def test_export_mesh_re_guards_raw_mesh_after_dialog() -> None:
    """rect LOW (adversary critic) regression guard: ``_on_export_mesh``
    MUST re-guard ``self._raw_mesh`` AFTER the dialog returns.  The
    modal dialog runs its own event loop; a queued catch-up render
    could fail mid-dialog and flip ``_raw_mesh`` to ``None``.  Without
    the re-guard, the subsequent ``self._raw_mesh.save(path)`` raises
    ``AttributeError`` (caught by the broad except but surfaced as
    confusing implementation jargon to the user).
    """
    handler_start = _APP_SRC.find("def _on_export_mesh(")
    handler_end = _APP_SRC.find("\n    def ", handler_start + 1)
    body = _APP_SRC[handler_start:handler_end]
    # There must be at least TWO `if self._raw_mesh is None` guards
    # in the handler — one at the top (the action-disabled belt-and-
    # braces guard) and one after the dialog returns (the catch-up-
    # failure-during-dialog guard).
    count_guards = body.count("if self._raw_mesh is None")
    assert count_guards >= 2, (
        f"Found {count_guards} `if self._raw_mesh is None` guard(s) in "
        "_on_export_mesh; rect LOW requires at least 2 (one at top, "
        "one after the dialog returns) — the dialog's event loop can "
        "let a queued render fail and flip _raw_mesh to None."
    )


def test_export_mesh_uses_ctrl_shift_e_shortcut() -> None:
    """rect LOW-3 (frontend critic) regression guard: the shortcut
    is ``Ctrl+Shift+E`` (NOT ``Ctrl+E``).  ``Ctrl+Shift+E`` matches
    MeshLab / GIMP / Inkscape's "Export As" convention; ``Ctrl+E`` was
    free in AVC but is atypical in desktop sci-viz peers and a
    researcher with MeshLab muscle memory would find nothing.
    """
    assert 'QKeySequence("Ctrl+Shift+E")' in _APP_SRC, (
        "Export Mesh action MUST use QKeySequence(\"Ctrl+Shift+E\") "
        "for peer alignment (MeshLab / GIMP / Inkscape)."
    )
    # Negative guard: the prior Ctrl+E binding must not remain.
    assert 'QKeySequence("Ctrl+E")' not in _APP_SRC, (
        "QKeySequence(\"Ctrl+E\") must NOT appear — rect LOW-3 "
        "replaced it with Ctrl+Shift+E."
    )


def test_export_mesh_default_filename_is_ascii_safe() -> None:
    """rect LOW-2 (frontend critic) regression guard: the default
    filename derivation MUST NFKD-normalize and ASCII-strip the
    surface label so non-ASCII glyphs in surface labels (the U+2013
    EN DASH in "Calabi–Yau" is the conspicuous case) become ASCII
    before they hit Windows's legacy VTK C ``FILE*`` writer which
    can mangle non-ANSI codepoints in paths.
    """
    handler_start = _APP_SRC.find("def _on_export_mesh(")
    handler_end = _APP_SRC.find("\n    def ", handler_start + 1)
    body = _APP_SRC[handler_start:handler_end]
    # NFKD + ASCII encode/decode is the canonical Python pattern.
    has_normalize = (
        'unicodedata.normalize("NFKD"' in body
        or "unicodedata.normalize('NFKD'" in body
    )
    assert has_normalize, (
        "Default filename derivation MUST call unicodedata.normalize"
        "(\"NFKD\", surface.label) to strip non-ASCII glyphs — "
        "without it the U+2013 EN DASH in \"Calabi–Yau\" can fail "
        "or silently mangle on Windows's legacy VTK C FILE* writer."
    )
    # ASCII encode/decode pair must follow.  Substring check (NOT a
    # single-literal match) so the assertion survives a multi-line
    # split of the .encode() call's keyword arguments.
    encode_pos = body.find(".encode(")
    decode_pos = body.find('.decode("ascii")')
    if decode_pos == -1:
        decode_pos = body.find(".decode('ascii')")
    assert encode_pos != -1 and decode_pos != -1, (
        "NFKD normalization must be followed by an ASCII encode/decode "
        "pair (.encode(\"ascii\", \"ignore\").decode(\"ascii\")) to "
        "drop the now-decomposed combining marks."
    )
    # encode must precede decode in the handler body.
    assert encode_pos < decode_pos, (
        "Expected .encode(...) BEFORE .decode(...) — they form a pair "
        "around the NFKD-normalized surface label."
    )
    # The encode must include the "ascii" target and "ignore" error mode.
    encode_window = body[encode_pos:decode_pos]
    assert '"ascii"' in encode_window or "'ascii'" in encode_window, (
        ".encode(...) target must be \"ascii\"."
    )
    assert '"ignore"' in encode_window or "'ignore'" in encode_window, (
        ".encode(...) error mode must be \"ignore\" (drop unmappable "
        "combining marks)."
    )


def test_export_mesh_tooltip_drops_ai15_internal_jargon() -> None:
    """rect MEDIUM-4 (frontend critic) regression guard: the tooltip
    MUST NOT expose the internal ``AI-15:`` invariant tag as user-
    facing text.  Users don't read app-invariants.md; ``AI-15:`` reads
    as legalese / a version number to a mathematician hovering the
    action.  Replaced with plain-language ``Note:`` prefix.
    """
    # Find the tooltip block (the multi-line setToolTip call after
    # the QAction construction).
    action_pos = _APP_SRC.find("self._export_mesh_action.setToolTip(")
    assert action_pos != -1, (
        "Export Mesh action must call setToolTip."
    )
    # Capture the next ~400 chars (the tooltip body).
    tooltip_block = _APP_SRC[action_pos:action_pos + 600]
    assert "AI-15:" not in tooltip_block, (
        "Tooltip MUST NOT contain 'AI-15:' (internal invariant tag); "
        "rect MEDIUM-4 replaced it with 'Note:' for user-facing clarity."
    )
    # The tooltip should still cover the mathematical-caveats note
    # (just without the AI-15: jargon prefix).
    assert "Note:" in tooltip_block or "caveats" in tooltip_block, (
        "Tooltip should still cover the mathematical-caveats note "
        "(rect MEDIUM-4 replaced the AI-15: prefix with Note:)."
    )
