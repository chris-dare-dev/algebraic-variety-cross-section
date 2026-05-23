# Adversary critique — mesh-export-stl-obj-ply-2026q3-e1

**Reviewer:** milestone-adversary-critic (read-only)
**Date:** 2026-05-23
**Subject:** mesh-export-stl-obj-ply-2026q3-e1 — `b06391dcf2e8e3f67cbbab84f857837fba0cf62c..474815f`

**Diff stats:** 3 587 lines total (full range); mesh-export commit (474815f) alone: ~543 lines across 6 files.  Production delta: `app.py` +142 LOC, `tests/test_mesh_export.py` +231 LOC, `CONTEXT.md` +1 LOC.  Remaining 3 044 lines are prior-milestone artifacts (e4b coarse-preview LOD commits landed earlier in the same range) and milestone pipeline documents.

---

## Executive summary

The most actionable finding is a MEDIUM AI-15 honesty gap: `_on_export_mesh` reads `self._raw_mesh` which can hold a **coarse-preview mesh** (n=80) while the status bar shows "Preview — …"; the export action is enabled for coarse results and the success message `"Mesh exported: /path/file.stl"` carries no indication of mesh fidelity.  A second MEDIUM is a test fragility: `test_export_mesh_format_filter_includes_stl_obj_ply` asserts the exact human-readable label `"STL files (*.stl)"` — a display-string rename (`"Stereolithography (*.stl)"`) would break the test without breaking behavior.  The diff-size AUTO-HIGH fires (non-waivable per checklist): 3 587 lines > 400; the code-only delta is ~375 LOC but the commit range includes e4b commits.  One LOW covers a confusing-but-non-crashing edge case where the `except Exception` on `.save()` swallows an `AttributeError` from a racing `_raw_mesh=None` mutation, producing a misleading error message.  No CRITICALs.  All AI-1..AI-15 are clean for the mesh-export commit.  Safe to ship after the two MEDIUMs are addressed.

**Severity counts:** 0 CRITICAL, 2 HIGH (1 auto + 0 real code), 2 MEDIUM, 1 LOW.
**Verdict:** SHIP-WITH-FIXES — both MEDIUMs are one-line or two-line fixes; nothing blocks the core feature.

---

## Verdict

**SHIP-WITH-FIXES**

The core mesh-export feature is correctly implemented: the lifecycle is sound (4 `setEnabled` sites, well-documented), scope is clean (STL/OBJ/PLY only, no VTK/VTP/GEO creep, no screenshot migration), extension pre-validation is present, broad `except Exception` covers all PyVista error types, and all 8 tests pass.  The two MEDIUMs are a documentation/honesty gap (coarse-preview export warning) and a test maintenance tax (over-specific filter label assertion).  Neither is a blocking correctness defect, but both should be addressed before the milestone closes to avoid downstream confusion for researchers and future maintainers.

---

## Critical findings

None.

---

## High findings

### HIGH — Diff-size review-quality risk (auto-finding)

**Where:** `no specific file` (commit range)
**Evidence:** `git diff b06391dcf2e8e3f67cbbab84f857837fba0cf62c..474815f | wc -l` = 3 587 lines, exceeding the 400-line defect-detection threshold (Cisco/LinearB research: defect detection drops measurably above 400 LOC in a single review pass).
**Why it matters:** Per the adversary-critique checklist this finding is non-waivable regardless of cause.
**Suggested fix:** No code action required.  The excess is attributable to the e4b milestone artifacts included in the commit range (~3 044 lines of prior milestone notes, agent-memory appends, dispatch logs, and the e4b production delta).  The mesh-export production delta (app.py + tests + CONTEXT.md) is ~375 LOC — comfortably below the threshold.  Future dispatches of this milestone's critique should scope the range to `d5df236..474815f` (the mesh-export commit only) to avoid the auto-HIGH from the inflated range.

---

## Medium findings

### MEDIUM — Coarse-preview mesh exported without fidelity warning (AI-15 adjacent)

**Where:** `app.py:974` (setEnabled(True) called for both coarse and full results), `app.py:1364` (success message `"Mesh exported: {path}"`)
**Evidence:** `_on_mesh_ready` calls `self._export_mesh_action.setEnabled(True)` at line 974 for **every** successful result, including `result.is_coarse=True` (n=80) coarse-preview renders.  When a researcher triggers Export Mesh while the status bar reads `"Preview — Fermat quartic — 42 ms"`, `self._raw_mesh` holds the coarse n=80 PolyData.  The export action is enabled, the dialog opens, and on success the status bar writes `"Mesh exported: Fermat_quartic.stl"` — no indication that the file is a coarse approximation with ~10× fewer vertices than the production n=240 mesh.  There is no `self._raw_mesh_is_coarse` attribute tracking fidelity state; `_on_export_mesh` has no mechanism to query whether the current mesh is coarse.  The AI-15 Preview badge is the correct mechanism for on-screen fidelity disclosure, but it is not surfaced inside the export dialog or in the success message.
**Why it matters:** A researcher could unknowingly export an n=80 coarse approximation and use it for downstream analysis (topology, curvature computation, mesh statistics) without knowing the mesh has ~1/8 the vertex count of the canonical surface.  This is an honesty gap under AI-15, which requires that the user can always distinguish full-fidelity from preview output.
**Suggested fix:** Two options (either is sufficient): (a) In `_on_mesh_ready`, call `setEnabled(True)` only when `not result.is_coarse` — the action stays disabled during coarse previews and re-enables when the full-resolution catch-up completes; OR (b) track fidelity state via `self._raw_mesh_is_coarse: bool = False` (set in `_on_mesh_ready` based on `result.is_coarse`; reset to `False` on error/clear) and in `_on_export_mesh` annotate the success message: `f"Mesh exported (preview-resolution — drag for full): {path}"` when `self._raw_mesh_is_coarse`.  Option (b) is less disruptive to UX (action stays enabled); option (a) is cleaner for AI-15 but adds a flicker during rapid drag.
**Regression-guard test:** Add `test_export_mesh_action_stays_disabled_on_coarse_result` that searches `_on_mesh_ready` source for the presence of `result.is_coarse` near `setEnabled(True)` (or alternatively that `setEnabled(True)` is NOT in the coarse-branch before the `if result.is_coarse: ... return` block).

### MEDIUM — Filter-string test asserts display label, not glob (over-specific source-grep)

**Where:** `tests/test_mesh_export.py:160,163,166`
**Evidence:** The three format-filter assertions are `assert "STL files (*.stl)" in _APP_SRC`, `assert "OBJ files (*.obj)" in _APP_SRC`, `assert "PLY files (*.ply)" in _APP_SRC`.  These pin the human-readable display label (`"STL files"`) in addition to the glob.  A future maintainer renaming `"STL files (*.stl)"` to `"Stereolithography (*.stl)"` — a valid display-label refactor that preserves the `*.stl` filter behavior and the extension-validation logic — would break all three test assertions without breaking any user-visible behavior.
**Why it matters:** Source-grep tests that enforce DISPLAY STRINGS rather than BEHAVIORAL assertions compound maintenance tax over time.  When the test breaks on a benign rename, the maintainer must either revert a legitimate refactor or update the test, losing confidence in what the test is actually guarding.  The behavioral contract here is `*.stl / *.obj / *.ply` glob presence, not the human label.
**Suggested fix:** Relax the assertions to pin only the glob portion: `assert "*.stl" in _APP_SRC and "*.obj" in _APP_SRC and "*.ply" in _APP_SRC`.  Alternatively, assert the full filter string `"*.stl);;OBJ files (*.obj);;PLY files (*.ply)"` (which pins the triple AND separator, the structurally meaningful part) while accepting any label prefix.

---

## Low findings

### LOW — Post-dialog `_raw_mesh=None` mutation yields confusing `AttributeError` message

**Where:** `app.py:1360` (`self._raw_mesh.save(path)` — no re-guard after dialog returns)
**Evidence:** `_on_export_mesh` guards `self._raw_mesh is None` at line 1313 BEFORE opening `QFileDialog.getSaveFileName`.  The dialog runs its own nested event loop.  In the narrow window where (a) the action was enabled from a previous coarse success, (b) a catch-up full render was queued via `QTimer.singleShot(0, ...)`, and (c) that catch-up render FAILS inside the dialog's event loop (e.g., parameter combination produces an empty field), `_on_mesh_ready`'s error path fires: `_raw_mesh = None`, `setEnabled(False)`.  The user then clicks OK in the dialog; `_on_export_mesh` resumes with `path` non-empty but `self._raw_mesh` is now `None`.  `self._raw_mesh.save(path)` raises `AttributeError: 'NoneType' object has no attribute 'save'` — caught by `except Exception as exc` and surfaced as `"Export failed: 'NoneType' object has no attribute 'save'"`.  No crash; the broad `except Exception` saves it.  But the message is confusing.
**Why it matters:** The error message is implementation-internal jargon, not actionable for a researcher.  The scenario requires: coarse render in-flight, user presses Ctrl+E before catch-up fires, catch-up fails.  Very rare in practice; the except Exception is the safety net.
**Suggested fix:** Add a second `if self._raw_mesh is None: return` guard immediately after `if not path: return` (i.e., after the dialog returns and before the extension validation), with status bar message: `"Export cancelled — surface is no longer available (render failed during dialog)."`.  This is a 3-line addition.

---

## What was done well

- **Scope discipline is exemplary.** The milestone delivers exactly STL/OBJ/PLY via `mesh.save()` — no `.vtk`, `.vtp`, `.geo`, `.iv`, `.pkl`, `.pickle`, `.vtkhdf` scope creep despite all being supported by PyVista.  The filter string and extension validation lock the three formats; the screenshot migration from `view_panel` was correctly NOT attempted.  This is the tightest possible §9 lift.

- **Export-action lifecycle at all 4 sites.** The researcher identified that `_clear_actor()` does NOT reset `_raw_mesh` and added the explicit `setEnabled(False)` in `_on_variety_changed`'s placeholder branch (`app.py:560`).  Without this the user could silently export the prior surface from an empty viewport.  The commit message documents this as the "most subtle UX bug in the milestone" — accurate, and the corresponding test (`test_export_mesh_action_re_disabled_on_variety_clear`) covers it.

- **Broad `except Exception` is correct here (not an AI-10 scope violation).** Unlike `closeEvent`'s narrow `OSError` for `QSettings.sync`, the `mesh.save()` call can raise `PermissionError`, `FileNotFoundError`, `ValueError` (unsupported extension if user bypasses filter), and internal VTK IO errors.  The comment `# noqa: BLE001 — PermissionError, FileNotFoundError, ValueError, VTK IOError` explicitly documents the intentional broadening.  This is the right call, grounded in the researcher's empirical verification of the error types.

- **Extension pre-validation before `mesh.save()`.** The `lower.endswith` pre-check catches the macOS/Linux `QFileDialog` non-auto-append case and gives a friendlier message than VTK's stderr error.  The researcher verified empirically that PyVista raises `ValueError: Invalid file extension '.xyz'...` rather than a VTK stderr message, and the pre-validation turns this into a clear user-facing status bar message.

- **File menu position via call order.** Calling `_build_file_menu()` before `_build_theme_menu()` in `__init__` (app.py:285-286) is the correct Qt idiom for controlling left-to-right menu order without any `insertMenu()` or `QMenuBar.actions()` manipulation.  Clean and future-proof.

- **AI-15 tooltip is specific.** The export action tooltip explicitly names the mathematical caveats: `"AI-15: the mathematical caveats of the active variety (real shadow, birational model, parametric cross-section) carry through to the exported file"`.  This is the correct institutional-memory cross-reference for researchers who notice the phrasing and look up the caveats in `SUBTYPE_TOOLTIPS`.

- **Ctrl+E shortcut conflict-free and documented.** The researcher confirmed Ctrl+E is not used by any of the three existing shortcuts (Ctrl+R, Ctrl+Shift+S, Ctrl+D), and the 4 months of subsequent milestones (qsettings-persistence, render-busy-spinner) did not claim it.  No conflict.

- **Test file quality: 8 tests, each covering a distinct behavioral contract.** `test_export_mesh_uses_raw_mesh_not_clipped` pinning `self._raw_mesh.save(` and asserting `self._clipped_mesh.save(` is absent is an AI-15 contract guard that survives refactors as long as the behavioral contract holds.  `test_export_mesh_action_re_disabled_on_variety_clear` covers the load-bearing lifecycle invariant that's easy to miss in future maintenance.  The handler-body scoping via `_APP_SRC.find("def _on_export_mesh(")` + `_APP_SRC.find("\n    def ", handler_start + 1)` is correct and consistent with prior source-grep patterns in this repo.

- **Correct `except Exception` scope (no BaseException swallowing).** Python's `Exception` hierarchy does NOT include `KeyboardInterrupt`, `SystemExit`, or `GeneratorExit` — those are `BaseException` subclasses.  The concern from the milestone brief is correctly resolved: the broad `except Exception` does not prevent clean process termination.

---


## Cross-critic agreement

The following findings cluster within 5 lines of each other in the same file. Multiple critics flagged the same area -- these are the strongest signals to fix first.

- **M1, M4** at `app.py:974-974` (MEDIUM): Coarse-preview mesh exported without fidelity warning (AI-15 adjacent); 3 — Export action enabled by coarse (draft-resolution) mesh without disclosure
- **M3, L3** at `app.py:1336-1340` (LOW): 2 — `_selected_filter` captured but unused; extension-missing produces error instead of auto-append; 4 — Format filter uses "STL files (*.stl)" while Qt docs convention is "STL (*.stl)"
- **L1, M2** at `app.py:1360-1364` (LOW): Post-dialog `_raw_mesh=None` mutation yields confusing `AttributeError` message; 1 — Success status-bar message clips on deep filesystem paths

## Recommended rectification order

1. **Fix MEDIUM M1 (coarse export fidelity gap):** In `_on_mesh_ready`, add `self._raw_mesh_is_coarse = result.is_coarse` after `self._raw_mesh = mesh` (line 969), initialize `self._raw_mesh_is_coarse = False` in `__init__`, reset to `False` on error/clear paths, and annotate the success message in `_on_export_mesh`.  Alternatively, gate `setEnabled(True)` on `not result.is_coarse`.  Add the regression-guard test.

2. **Fix MEDIUM M2 (filter-string over-specific assertion):** In `tests/test_mesh_export.py:160,163,166`, relax the three `"STL files (*.stl)"` / `"OBJ files (*.obj)"` / `"PLY files (*.ply)"` assertions to pin only the glob `*.stl` / `*.obj` / `*.ply` presence (or the filter separator triple).

3. **LOW L1 (post-dialog _raw_mesh re-guard):** After `if not path: return` in `_on_export_mesh` (~line 1342), add a second `if self._raw_mesh is None: self.statusBar().showMessage("Export cancelled — surface is no longer available."); return`.  2-line fix, prevents the confusing AttributeError message.

---

*End of critique.  Mandatory rectification: M1 and M2 (both MEDIUMs).  L1 is optional but recommended before milestone close.*
## Frontend UI/UX findings

_Merged from milestone-frontend-ux-critic._

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

---

## Rectification status — 2026-05-23

**Fixed (in-scope, this rect commit):**
- `cross-critic MEDIUM` (coarse-preview AI-15 gap): added `self._raw_mesh_is_coarse: bool = False` parallel-track to `self._raw_mesh`; set in `_on_mesh_ready` success path via `bool(result.is_coarse)`; reset to False on error path AND on `_on_variety_changed` placeholder branch; consumed in `_on_export_mesh` to (a) tag suggested filename with `_preview` suffix when coarse, and (b) annotate the success status-bar message `"Mesh exported (preview-resolution — release to render full): {basename}"`. Both critics independently flagged this; chose Option (b) from the brief (keep action enabled, annotate disclosure) over Option (a) (gate setEnabled on not coarse) because Option (a) introduces visible flicker during rapid drag while Option (b) preserves discoverability + honesty.
- `adversary MEDIUM` (filter-string test over-specific): relaxed `tests/test_mesh_export.py::test_export_mesh_format_filter_includes_stl_obj_ply` from pinning display labels `"STL files (*.stl)"` triplet to pinning only globs `*.stl` / `*.obj` / `*.ply` + the `;;` separator triple. Catches the structural contract without breaking on a future label rename.
- `MEDIUM-1 frontend` (path clip on success): use `os.path.basename(path)` in success message instead of full path. Added `import os.path` to app.py imports. Matches ParaView's "Save Data" pattern.
- `MEDIUM-2 frontend` (`_selected_filter` unused / no auto-append): captured as `selected_filter` (no leading underscore); parse with `re.search(r"\(\*(\.\w+)\)", selected_filter)` to extract glob; auto-append extension when user types bare filename. Falls through to the prior error branch if filter is malformed. Added `import re` to app.py imports. Matches MeshLab / Blender / GIMP / Inkscape behavior.
- `MEDIUM-4 frontend` (`AI-15:` tooltip jargon leak): replaced `"AI-15: the mathematical caveats..."` with `"Note: mathematical caveats..."`. Users don't read app-invariants.md; the internal invariant tag reads as version-number / legalese to a hovering mathematician.
- `MEDIUM-5 frontend` (tooltip too long): trimmed from 4 source lines (~7 visual lines after Qt word-wrap) to 3 lines per the critic's suggested tighter wording. Removed the PyVista routing implementation note (moved to docstring only).
- `LOW adversary` (post-dialog `_raw_mesh` re-guard): added second `if self._raw_mesh is None` check after `if not path: return` with the friendlier message "Export cancelled — surface no longer available (render failed during dialog)." Prevents the confusing `AttributeError: 'NoneType' object has no attribute 'save'` surface when a queued render fails inside the dialog's modal event loop.
- `LOW-2 frontend` (EN DASH on Windows VTK legacy path): added `unicodedata.normalize("NFKD", surface.label).encode("ascii", "ignore").decode("ascii")` to the filename sanitisation chain. Drops the U+2013 EN DASH in "Calabi–Yau" (the only non-ASCII glyph in the current registry) before it hits Windows's legacy VTK C FILE* writer. Added `import unicodedata` to app.py imports.
- `LOW-3 frontend` (Ctrl+E → Ctrl+Shift+E): changed shortcut to align with MeshLab / GIMP / Inkscape "Export As" convention. Ctrl+E was free in AVC but atypical in desktop sci-viz peers.

Added 7 new regression-guard tests in `tests/test_mesh_export.py`:
- `test_export_mesh_tracks_coarse_fidelity_for_ai15_disclosure`
- `test_export_mesh_success_message_uses_basename_not_full_path`
- `test_export_mesh_auto_appends_extension_from_selected_filter`
- `test_export_mesh_re_guards_raw_mesh_after_dialog`
- `test_export_mesh_uses_ctrl_shift_e_shortcut`
- `test_export_mesh_default_filename_is_ascii_safe`
- `test_export_mesh_tooltip_drops_ai15_internal_jargon`

**Deferred (out-of-scope or cosmetic):**
- `HIGH adversary` (process / diff-size auto-finding): 3587-line range includes 3044 lines of unrelated merged e4b artifacts; mesh-export production+test delta is ~375 LOC. No code action.
- `LOW-1 frontend` (`_Fig._1` underscore-dot in filename): cosmetic readability paper-cut; the `Fig._N` pattern is unambiguous to most users and the period is filesystem-legal everywhere. Defer to a future filename-polish pass.
- `LOW-4 frontend` (filter string "STL files (*.stl)" vs Qt convention "STL (*.stl)"): cosmetic only; no functional impact. Defer.

**Invalidated:** none.

**Test count:** 449 pass (was 442, +7 rect regression guards). 4 of the regression guards anchor multiple finding closures so future refactors can't silently reintroduce any one of them.
