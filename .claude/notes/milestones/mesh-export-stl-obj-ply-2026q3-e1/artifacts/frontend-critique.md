# Frontend UX Critique — mesh-export-stl-obj-ply-2026q3-e1

**Critic:** milestone-frontend-ux-critic
**Commit range:** `b06391dcf2e8e3f67cbbab84f857837fba0cf62c..474815f`
**Files changed:** `app.py`, `CONTEXT.md` (panel files: no changes)
**Date:** 2026-05-23

---

## Executive Summary

This milestone adds the first File menu with a single Export Mesh action. The core implementation is clean: File lands leftmost via correct `addMenu` call order, action lifecycle is correctly gated at all 4 sites, AI-9/AI-11/AI-12/AI-13 are clear (no new colors, enums, or processEvents), and first-launch UX is preserved. The `AA_EnableToolTipsOnDisabledWidgets` attribute (confirmed at `app.py:1675`) ensures the tooltip is visible on the greyed-out action on macOS, which was the lesson from `enriques-hq-smoothing-2026q3-e1`.

**0 CRITICAL, 0 HIGH, 5 MEDIUM, 4 LOW.**

The dominant finding cluster is around export discoverability and feedback quality: the success status-bar message clips on realistic deep paths; the `_selected_filter` return value is captured but not used (auto-append would prevent most extension-missing errors); the export action is enabled by coarse-preview results without any resolution disclosure; and the tooltip's `AI-15:` label is internal jargon invisible to end users.

---

## CRITICAL

None.

---

## HIGH

None.

---

## MEDIUM

### MEDIUM-1 — Success status-bar message clips on deep filesystem paths

**Where:** `app.py:1364`
**Evidence:** `self.statusBar().showMessage(f"Mesh exported: {path}")`. A realistic deep path — `"/Users/researcher/Library/CloudStorage/OneDrive-UniversityOfOxford/Research/AlgVarieties/Canonical_sextic_Fig._1.stl"` — produces a 131-character message; a Windows OneDrive path reaches 166 characters. The empirical QStatusBar visible-clip band is ~120 characters (documented in lessons.md and CONTEXT.md §4.3). At these lengths the full path is invisible but the leading `"Mesh exported:"` token stays visible, so the user knows the export succeeded but cannot confirm which file.
**Why it matters:** A researcher who exports multiple figures to the same directory cannot distinguish which export just completed without checking the filesystem directly. The success confirmation is the only user-visible acknowledgment of the save; clipping the path defeats its purpose.
**Suggested fix:** Use `os.path.basename(path)` in the success message: `f"Mesh exported: {os.path.basename(path)}"`. ParaView's Save Data uses this pattern ("Saved mesh.stl" not the full path). This keeps the message under 60 characters for any surface label.

---

### MEDIUM-2 — `_selected_filter` captured but unused; extension-missing produces error instead of auto-append

**Where:** `app.py:1336`
**Evidence:** `path, _selected_filter = QFileDialog.getSaveFileName(...)`. The `_selected_filter` variable is assigned (note the leading underscore indicating "intentionally unused") but never read. On macOS and Linux, `QFileDialog.getSaveFileName` does NOT auto-append the extension when the user types a bare filename (e.g., `"my_surface"` without `.stl`). The current handler then fires a manual error: `"Export cancelled — please include a .stl, .obj, or .ply extension."`. MeshLab and Blender both auto-append from the selected filter in this case.
**Why it matters:** A user who types `"my_surface"` and has STL selected in the filter expects `my_surface.stl` to be written. Instead they get an error and must re-open the dialog. This is the majority behaviour across desktop-sci-viz peers (MeshLab, Blender, Inkscape, GIMP all auto-append). The error message is correct and user-friendly but the workflow is unnecessarily interrupted.
**Suggested fix:** After getting `path` and `_selected_filter`, if `path` lacks a valid extension, parse `_selected_filter` with `re.search(r'\(\*(\.\w+)\)', selected_filter)` to get the expected extension and append it before proceeding. The error message branch can serve as a final fallback if the filter string is malformed. Note: on Windows, `QFileDialog` auto-appends natively — the fix eliminates a platform inconsistency.

---

### MEDIUM-3 — Export action enabled by coarse (draft-resolution) mesh without disclosure

**Where:** `app.py:974`
**Evidence:** In `_on_mesh_ready`, `self._export_mesh_action.setEnabled(True)` is called unconditionally in the success path at line 974, BEFORE the `if result.is_coarse: ... return` branch at line 1002. This means after a drag-tick coarse result lands: `_raw_mesh` is set to the `n=80` coarse mesh, the export action is enabled, and the status bar shows `"Preview — Fermat quartic — 45 ms"`. A user who opens File > Export Mesh at this point exports a ~80-grid mesh, not the ~240-grid production mesh.
**Why it matters:** The coarse mesh represents the same mathematical surface but at significantly lower vertex count (approximately 1/27th the voxel count). A researcher doing downstream mesh analysis or publication rendering expects the full-resolution surface. There is no indicator in the exported filename, the status-bar success message, or the exported file itself that the mesh is a draft. This is a subtle AI-15 honesty gap: the export inherits the variety's tooltips but not the resolution caveat introduced by the LOD path.
**Suggested fix:** Gate `setEnabled(True)` on `not result.is_coarse`: `self._export_mesh_action.setEnabled(not result.is_coarse)`. This keeps the action greyed out during drag-preview and enables it only on full-resolution results. Alternatively, allow coarse exports but append `_preview` to `default_name` when `_raw_mesh` is a coarse result (requires tracking `_raw_mesh_is_coarse: bool` alongside `_raw_mesh`).

---

### MEDIUM-4 — Tooltip exposes internal `AI-15` invariant tag as user-facing text

**Where:** `app.py:1283`
**Evidence:**
```
"AI-15: the mathematical caveats of the active variety "
"(real shadow, birational model, parametric cross-section) "
"carry through to the exported file — see the variety "
"tooltip for the specifics."
```
`AI-15` is an internal code-review invariant label from `app-invariants.md`. It has no meaning to an end-user researcher. The research brief (§9) proposed the cleaner phrasing `"Note: the mathematical caveats of the variety (real shadow, birational model, parametric cross-section) also apply to the exported file — see the variety tooltip for details."`.
**Why it matters:** A mathematician or student hovering the Export Mesh action and seeing `"AI-15:"` will interpret it as a version number, a legal clause, or random metadata. It undercuts the tooltip's clarity and signals that the code's internal review language leaked into the UI. VS Code, ParaView, and MeshLab never expose internal ticket or invariant IDs in user-facing tooltip strings.
**Suggested fix:** Replace `"AI-15: the mathematical caveats..."` with `"Note: the mathematical caveats..."`. Four characters, full semantic preservation, no jargon leak.

---

### MEDIUM-5 — Tooltip too long: 4 declared lines with 2 that word-wrap to ~7 visual lines

**Where:** `app.py:1278–1287`
**Evidence:** The tooltip has 4 explicit `\n`-delimited lines. Line 3 is 117 characters; Line 4 (the AI-15 line) is 191 characters. Qt word-wraps each to ~60–70 characters at typical tooltip width, producing approximately 7 visual lines total. UX research across VS Code, Blender, and ParaView tooltips consistently suggests ≤3 visual lines as the maximum for action tooltips (longer text is better served by a Help menu entry or hover-over status-bar description).
**Why it matters:** A tooltip that spans 7 visual lines obscures surrounding UI chrome while open, reads as a documentation dump rather than a quick affordance hint, and will overflow the screen on smaller displays. The research brief's §9 proposed a tighter 4-visual-line version that excluded the PyVista routing note.
**Suggested fix:** Trim to 3 lines:
```
"Save the current surface mesh to a file.\n"
"Formats: STL · OBJ · PLY. Exports the full unclipped surface.\n"
"Note: mathematical caveats of the variety apply — see variety tooltip."
```
The "PyVista routes by extension" implementation detail belongs in the docstring, not the user tooltip.

---

## LOW

### LOW-1 — Default filename preserves `Fig._1` period, producing awkward underscore-dot sequence

**Where:** `app.py:1327–1333`
**Evidence:** The sanitisation replaces `[` and `]` with empty strings but does not strip the period from `"Fig. 1"`. Result: `"Canonical sextic [Fig. 1]"` → `"Canonical_sextic_Fig._1.stl"`. The `_Fig._1` token contains a literal period embedded between underscores, which looks like a secondary file extension or a typo to filesystem tools and users alike. `"Canonical_sextic_Fig_1.stl"` is unambiguous.
**Why it matters:** Minor readability paper-cut. No functional harm (the period is legal on all filesystems), but it looks like a sanitisation bug to users who notice it. The `Dwork_pencil_(Calabi–Yau)_Fig._4.stl` result is the most conspicuous case.
**Suggested fix:** Add `.replace(".", "")` scoped to the bracket-removed portion, or use `re.sub(r'\[Fig\. (\d+)\]', r'Fig_\1', surface.label)` before the other replacements.

---

### LOW-2 — EN DASH (`U+2013`) in default filename for Dwork pencil may fail on Windows via VTK legacy path

**Where:** `app.py:1327–1333`
**Evidence:** `"Dwork pencil (Calabi–Yau) [Fig. 4]"` → `"Dwork_pencil_(Calabi–Yau)_Fig._4.stl"`. The `–` (U+2013 EN DASH) is passed through sanitisation unchanged. On macOS/Linux (HFS+/ext4) this is valid; on Windows, VTK's legacy C `FILE*` writer in some versions uses the ANSI codepage for file path creation, which may fail or silently mangle non-ASCII characters in paths.
**Why it matters:** A Windows user exporting a Dwork pencil mesh may encounter a VTK `IOError` or a file created with a garbled name. The `except Exception` catch surfaces the error to the status bar, so no crash occurs, but the experience is confusing and opaque. This is the only surface label in the current registry with a non-ASCII character in the visible label portion (the `–` in `Calabi–Yau`).
**Suggested fix:** Add `.replace('–', '-').replace('—', '-')` to the sanitisation chain, or use `unicodedata.normalize('NFKD', label).encode('ascii', 'ignore').decode('ascii')` for a blanket ASCII-safe pass.

---

### LOW-3 — Ctrl+E is atypical for Export in the desktop sci-viz ecosystem

**Where:** `app.py:1276`
**Evidence:** `self._export_mesh_action.setShortcut(QKeySequence("Ctrl+E"))`. Across desktop sci-viz and creative tools: MeshLab uses `Ctrl+Shift+E` (File > Export Mesh As); GIMP uses `Ctrl+Shift+E` (File > Export As); Inkscape uses `Ctrl+Shift+E` (File > Export). ParaView uses `Ctrl+S` (File > Save Data, the nearest equivalent). `Ctrl+E` is not conflicting within AVC and is mnemonic (`E` for Export), but the ecosystem convention for "Export As" is `Ctrl+Shift+E`.
**Why it matters:** A researcher familiar with MeshLab or GIMP will reach for `Ctrl+Shift+E` and nothing will happen. `Ctrl+E` will be discovered eventually via the File menu, so discoverability is not blocked, but the convention mismatch adds marginal friction.
**Suggested fix:** Consider `Ctrl+Shift+E` for alignment with MeshLab / GIMP / Inkscape. If `Ctrl+E` is kept, document the deliberate divergence in CONTEXT.md §9 (the shortcut section already notes `Ctrl+R`, `Ctrl+Shift+S`, `Ctrl+D`).

---

### LOW-4 — Format filter uses "STL files (*.stl)" while Qt docs convention is "STL (*.stl)"

**Where:** `app.py:1340`
**Evidence:** `"STL files (*.stl);;OBJ files (*.obj);;PLY files (*.ply)"`. Qt's own documentation examples consistently use `"Images (*.png *.xpm *.jpg)"` and `"Text files (*.txt)"` — the noun-first compact form. The existing screenshot filter in `view_panel.py` uses `"PNG Images (*.png)"` (mixed). Apple HIG recommends `"Stereolithography (STL)"` (format name first, abbreviation in parens without glob). Shortest equivalent: `"STL (*.stl);;OBJ (*.obj);;PLY (*.ply)"`.
**Why it matters:** Cosmetic consistency only. No functional impact. A user reading the file dialog sees the slightly redundant `"STL files (*.stl)"` instead of just `"STL (*.stl)"`.
**Suggested fix:** Align to Qt convention: `"STL (*.stl);;OBJ (*.obj);;PLY (*.ply)"`.

---

## What Was Done Well

1. **Menu position is correct.** `_build_file_menu()` is called before `_build_theme_menu()` in `__init__` (lines 286–287), placing File leftmost via `addMenu` call order. This works identically on macOS (system menu bar) and Windows/Linux (window menu bar). The comment in the code explicitly documents the ordering rationale.

2. **Disabled-state tooltip is reachable on macOS.** `Qt.ApplicationAttribute.AA_EnableToolTipsOnDisabledWidgets` is confirmed at `app.py:1675`. The greyed-out Export Mesh action will show its tooltip on hover on macOS without any additional work — the lesson from `enriques-hq-smoothing-2026q3-e1` was applied correctly.

3. **Action lifecycle is complete at all 4 sites.** Construction-disabled, `_on_mesh_ready` success-enabled, `_on_mesh_ready` error-disabled, `_on_variety_changed` placeholder-disabled. The explicit disable in `_on_variety_changed` is the load-bearing site that the research brief identified as the most likely oversight. It was not missed.

4. **Extension pre-validation prevents raw VTK error leakage.** The handler validates the extension before calling `mesh.save()`, so the user sees `"Export cancelled — please include a .stl, .obj, or .ply extension."` rather than `"Export failed: Invalid file extension '.xyz' for data type <class 'pyvista.core.pointset.PolyData'>. Must be one of: ['.ply', ...]"`. This is exactly the right layering.

5. **Broad `except Exception` is the correct scope here.** The `qsettings-persistence` milestone's `except OSError` was correctly NOT reused. The export path can raise `PermissionError`, `FileNotFoundError`, `ValueError` (invalid extension if user bypasses filter), and internal VTK IOErrors — all correctly caught and surfaced via status bar. The `# noqa: BLE001` annotation documents the deliberate breadth.

6. **AI-9 re-entrancy is clean.** No new `processEvents()` calls. `QAction.setEnabled()` is synchronous. `QFileDialog.getSaveFileName()` is modal and blocks the render trigger path while open. `mesh.save()` is synchronous at <50 ms. The re-entrancy analysis in the docstring is accurate.

7. **Raw mesh (unclipped) is exported, not the domain clip.** `self._raw_mesh.save(path)` rather than any clipped variant. The design comment is explicit and correct: the domain clip is a viewing convention, not an analytical one.

---

## Recommended Rectification Order

1. **MEDIUM-3** (export on coarse mesh) — gate `setEnabled(True)` on `not result.is_coarse`. One-line change, prevents the AI-15 resolution-disclosure gap at the most impactful site. Do first because it requires understanding the coarse/full branching.

2. **MEDIUM-4 + MEDIUM-5** (tooltip jargon + tooltip length) — these are adjacent edits in `_build_file_menu`. Replace `"AI-15:"` with `"Note:"` and trim the tooltip to 3 lines in the same commit.

3. **MEDIUM-1** (success message clips) — add `os.path.basename()` to the `showMessage` call. Trivial.

4. **MEDIUM-2** (auto-append from selected filter) — requires parsing `_selected_filter` with a regex. Low risk but slightly more code than the others. Can ride with MEDIUM-1 or stand alone.

5. **LOW-1 + LOW-2** (filename sanitisation) — strip period from `Fig.` token and en-dash from the sanitised label in one sanitisation-chain edit.

6. **LOW-3 + LOW-4** (shortcut + filter wording) — cosmetic; defer to a subsequent style pass.
