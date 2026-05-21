# Implementation plan — graph-and-window-2026q2-e1

**Inline path.** ~30 LOC across 3 files. Sequence per researcher recommendation:

1. **UPL-9** — `app.py:_apply_domain_and_render` — Add `ambient=0.15, diffuse=0.85` to the primary `plotter.add_mesh(...)` call. Do NOT touch the `lighting=False` overlay `add_mesh` call.

2. **UPL-28** — Two-file change:
   - `.claude/references/frontend-uplift/agent-prompts.md` visual-scout template: insert `p.set_background('#2f2f2f')` between `pv.Plotter(...)` and `p.add_mesh(...)`.
   - `.claude/scripts/frontend-uplift/render-panel-chrome.py` `_grab()`: insert `widget.clearFocus()` after `widget.show()` and before the first `app.processEvents()`. Use `clearFocus()` (not `setFocusPolicy`) because focus policy on a container doesn't prevent children from tab-cycle receiving focus.

3. **UPL-27** — `.claude/scripts/frontend-uplift/render-panel-chrome.py`:
   - Add `QDockWidget` to the `PySide6.QtWidgets` import line.
   - For each of the 6 panel-construction blocks (appearance/view/parameters × empty/populated), wrap the panel in a bare `QDockWidget` with the matching production dock title ("Appearance" / "View" / "Parameters") before calling `_grab()`.
   - Filename convention unchanged (`f"{panel}-{theme_name}-empty-default.png"`) — wrapping is transparent to filenames.
   - Integrity check loop needs no changes.

4. **Verify** — Run `.venv/bin/python -m pytest tests/ -q` (must stay green, currently 165 tests). Then run `.venv/bin/python .claude/scripts/frontend-uplift/render-panel-chrome.py /tmp/verify-milestone`; confirm 12 PNGs written, no `WARNING: populated capture IDENTICAL` on stderr, dock title bar visible in a Read of one PNG. Also run an off-screen render snippet to visually confirm UPL-9 lighting improvement on the Kummer surface.

5. **Commit** — Single commit, conventional subject: `feat(graph-and-window-2026q2-e1): bundle UPL-9 + UPL-27 + UPL-28 (Sprint 0)`. Body lists each candidate + render evidence.
