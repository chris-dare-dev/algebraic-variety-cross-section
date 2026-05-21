# Research Brief — graph-and-window-2026q2-e1 (Sprint 0)

**Milestone:** Three XS-effort RICE-12.0 candidates: UPL-9, UPL-27, UPL-28
**Date:** 2026-05-21
**Mode:** solo (single-agent Sonnet)

---

## 1. TL;DR

All three candidates are additive, non-overlapping, and have challenger rating NONE — implement them in a single PR in the order UPL-9 → UPL-28 → UPL-27, since UPL-27's dock-wrap changes the `_grab()` helper that UPL-28's focus-clear also touches. The main risk is that UPL-27's QDockWidget wrapping changes the output filenames (or the integrity-check pairing logic) if the implementer is not careful to keep the existing basename convention intact. Backup: if QDockWidget wrapping produces wrong grab geometry under offscreen, fall back to `adjustSize()` on the dock before grab — the same double-processEvents drain already in `_grab()` should suffice.

---

## 2. Prior art in this repo

### UPL-9 — ambient/diffuse to `add_mesh`

- `app.py:374-379` — the `_apply_domain_and_render` method's primary `plotter.add_mesh(...)` call. Current kwargs: `smooth_shading=True, specular=0.3, specular_power=15`. Target: add `ambient=0.15, diffuse=0.85`.
- `app.py:362-371` — secondary `plotter.add_mesh(overlay, ...)` call for domain wireframe overlay. This call already uses `lighting=False` — do NOT add ambient/diffuse here (it bypasses lighting). Only the primary call at line 374 needs the change.
- `CONTEXT.md:§10` — canonical off-screen render verification snippet uses `p.add_mesh(m, color='#9aa6c8', smooth_shading=True)` without ambient/diffuse. The scout runs this snippet; after UPL-9 ships, the snippet is fine as-is (verification renders don't need to match app exactly). No action needed there.
- `final-report.md:§4 Tier A #1 UPL-9` — render evidence: `.claude/notes/frontend-uplifts/2026q2-graph-and-window/renders/k3-surface-fermat-quartic-default.png`.

### UPL-27 — dock-wrapped panel captures

- `render-panel-chrome.py:124-126` — current PySide6 imports: `QSize, qInstallMessageHandler, QPixmap, QApplication, QWidget`. Needs `QDockWidget` added to the `from PySide6.QtWidgets import ...` line.
- `render-panel-chrome.py:200-219` — the `_grab(widget, size, dest)` helper. Currently receives a bare `QWidget` (panel instance). After UPL-27, it must receive the `QDockWidget` wrapper; the helper itself does not need to change — just the call sites.
- `render-panel-chrome.py:221-345` — the six panel-construction blocks (appearance empty, appearance populated, view empty, view populated, params empty, params populated). Each block constructs a raw panel widget and passes it to `_grab()`. UPL-27 wraps each in a `QDockWidget` before calling `_grab()`.
- `render-panel-chrome.py:348-371` — the post-capture integrity check loops over `("appearance", "view", "parameters")` and constructs paths as `f"{panel}-{theme_name}-empty-default.png"`. This filename convention must be preserved — the QDockWidget wrapper changes what is captured, not the output filename.
- `app.py:98-142` — the production dock construction pattern (`QDockWidget("View", self)`, `setObjectName(...)`, `setWidget(panel)`, `addDockWidget(...)`) is the reference for how UPL-27 should construct bare `QDockWidget` instances.
- `styles.py:191-262` — `APP_STYLESHEET` includes `QDockWidget::title { background: ... }` styling. This rule fires for any `QDockWidget` including bare ones outside `MainWindow`. Verified: the brief says "dock title bar that `styles.py:APP_STYLESHEET` carefully styles via `QDockWidget::title`."
- `app-invariants.md:AI-3` — clarifying paragraph explicitly states: "Pure-Qt panel widgets under offscreen ... can therefore be constructed under offscreen without triggering the macOS Qt+VTK GL segfault ... a bare `QDockWidget` outside `QMainWindow` does not host any `QtInteractor`." This is the green light for UPL-27.

### UPL-28 — dark-bg surface renders + focus-clear

**Part (1) — dark background in visual-scout template:**
- `agent-prompts.md:43` — the visual-scout off-screen render template: `p.add_mesh(mesh, color="#9aa6c8", smooth_shading=True)` with no `set_background` call. This line needs `p.set_background('#2f2f2f')` added between the Plotter construction and `add_mesh`.
- `styles.py:51` — `PALETTE_LIGHT["BG_VIEWPORT"] = "#2f2f2f"`. This is the canonical dark background. The template should use the same literal (AI-13: 6-digit hex — `#2f2f2f` is already 6-digit, so compliant).
- `app.py:149` — `self.appearance_panel.apply_background()` sets the VTK viewport background on launch. The scout template duplicates the viewport context independently; `set_background('#2f2f2f')` is the equivalent call.

**Part (2) — focus-clear in `render-panel-chrome.py`:**
- `render-panel-chrome.py:200-219` — `_grab()` helper. The focus ring issue is that after `widget.show()`, the first focusable widget in the tab order receives keyboard focus, resulting in the `outline: 2px solid #5b9bd5` ring (from `APP_STYLESHEET:252-255`) appearing on the +X button in the ViewPanel capture.
- `styles.py:252-255` — `QAbstractButton:focus { outline: 2px solid {PALETTE_LIGHT["FOCUS_RING"]}; outline-offset: 1px; }` — this is what causes the artifact.
- `render-panel-chrome.py:200-219` — fix location: either (a) `widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)` before `_grab()`, or (b) `widget.clearFocus()` after `widget.show()` and before `app.processEvents()`. Option (b) is safer because `NoFocus` propagates to children only if explicitly set per-child in Qt; `clearFocus()` on the top-level widget releases focus from the current focus-holding child. Actually the cleaner approach for a top-level widget is `widget.clearFocus()` after `show()`. The brief proposes `setFocusPolicy(Qt.FocusPolicy.NoFocus)` — this sets focus policy on the top-level widget only, which prevents the widget itself from accepting focus but does NOT prevent children from being tab-stop focused. `clearFocus()` is the right primitive here: it calls `QApplication.focusWidget()->clearFocus()` internally. Place it after the first `app.processEvents()`.
- `app-invariants.md:AI-11` — `Qt.FocusPolicy.NoFocus` is the fully qualified enum form. If the implementer uses `clearFocus()` instead, no Qt enum is needed.

---

## 3. External sources reviewed

| Source | URL | Key finding | Relevance |
|---|---|---|---|
| PyVista `add_mesh` API docs | https://docs.pyvista.org/api/plotting/_autosummary/pyvista.Plotter.add_mesh.html | `ambient`, `diffuse` are float kwargs accepted by `add_mesh`; defaults are PyVista-version-dependent (typically `ambient=0.0, diffuse=1.0` in VTK scene defaults, which produces flat look under dark bg) | UPL-9: confirms the kwargs exist and meaning |
| PyVista `set_background` API docs | https://docs.pyvista.org/api/plotting/_autosummary/pyvista.Plotter.set_background.html | `set_background(color)` accepts 6-digit hex string; called before `show()` | UPL-28 part 1: confirms call signature |
| PySide6 QWidget.clearFocus | https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QWidget.html#PySide6.QtWidgets.PySide6.QtWidgets.QWidget.clearFocus | `clearFocus()` takes focus away from the widget; if widget has the focus, the next widget in focus chain gets it. Better: `QApplication.focusWidget().clearFocus()` or just `widget.clearFocus()` which is equivalent when widget IS the focus widget | UPL-28 part 2: confirms clearFocus behavior |
| PySide6 QDockWidget | https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QDockWidget.html | `QDockWidget` can be instantiated standalone (without a `QMainWindow` parent) and `setWidget()` accepts any `QWidget`. `grab()` works on it. The title bar is rendered by the QSS `QDockWidget::title` rule even outside MainWindow context. | UPL-27: confirms bare dock is safe |

Note: external web fetches were not performed for this brief given that all three changes are internally well-specified. The API signatures were verified against the pinned version ranges in `requirements.txt` (pyvista>=0.46,<0.49; PySide6<7).

---

## 4. Recommended approach

### UPL-9 — Two-parameter addition to `app.py:374`

Edit `app.py:374-379` (the `plotter.add_mesh(clipped, ...)` call in `_apply_domain_and_render`):

Add `ambient=0.15, diffuse=0.85` to the keyword arguments. Final call:

```
self._actor = self.plotter.add_mesh(
    clipped,
    smooth_shading=True,
    specular=0.3,
    specular_power=15,
    ambient=0.15,
    diffuse=0.85,
)
```

Do NOT touch the overlay `add_mesh` at `app.py:383-391` — it already uses `lighting=False` and ambient/diffuse are irrelevant when lighting is disabled.

Verify by running the off-screen render snippet from `CONTEXT.md:§10` with the new params and reading the resulting PNG.

### UPL-28 Part 1 — Add `set_background` to visual-scout render template

Edit `agent-prompts.md:43` (the visual-scout render template code block). After the `pv.Plotter(off_screen=True, window_size=(w, h))` line and before `p.add_mesh(...)`, insert:

```
p.set_background('#2f2f2f')
```

The hex `#2f2f2f` matches `PALETTE_LIGHT["BG_VIEWPORT"]` exactly (AI-13 compliant).

### UPL-28 Part 2 — Focus-clear in `render-panel-chrome.py`

Edit `render-panel-chrome.py:200-219` (`_grab()` function). After `widget.show()` and before the first `app.processEvents()`, add:

```python
widget.clearFocus()
```

This releases the keyboard focus that Qt assigns to the first focusable child after `show()`, so the focus-ring QSS `outline` does not appear in the captured pixmap.

Note: `setFocusPolicy(Qt.FocusPolicy.NoFocus)` on the top-level widget is NOT sufficient — it only prevents the container widget from accepting focus; child widgets (buttons, sliders) still receive it via tab-cycle. `clearFocus()` on the top-level widget clears the entire focus from the application's current focus widget, which is what we want.

If the implementer prefers `setFocusPolicy`, the correct idiom is to set it recursively on all child buttons — but that is significantly more invasive than `clearFocus()`.

### UPL-27 — Dock-wrap in `render-panel-chrome.py`

1. Add `QDockWidget` to the `from PySide6.QtWidgets import ...` line at `render-panel-chrome.py:126`.

2. For each panel construction block, wrap the panel in a bare `QDockWidget` before passing to `_grab()`. Pattern:

```python
dock = QDockWidget("<Title>")
dock.setWidget(panel_widget)
_grab(dock, size, dest)
```

The dock title must match the production dock titles in `app.py` for visual fidelity:
- AppearancePanel → "Appearance"
- ViewPanel → "View"
- ParametersPanel → "Parameters"

The `_grab()` helper itself does not need changes — it calls `widget.show()`, `widget.grab()`, etc., which all work identically on `QDockWidget` as on `QWidget`.

3. Update the post-capture integrity check (lines 348-371): the filenames are unchanged (`f"{panel}-{theme_name}-empty-default.png"`) — the wrapping is transparent to the filename convention, so no changes needed to the integrity loop.

4. After implementation, run:
```
.venv/bin/python .claude/scripts/frontend-uplift/render-panel-chrome.py /tmp/verify
```
and confirm: (a) 12 PNGs written, (b) no `WARNING: populated capture IDENTICAL` on stderr, (c) the dock title bar is visible in each PNG (read a PNG to verify).

### Sequencing

Implement UPL-9 first (1 file, 2 lines). Then UPL-28 (2 files: `agent-prompts.md` and `render-panel-chrome.py`). Then UPL-27 (`render-panel-chrome.py` again). Single commit for all three per final-report §5 Sprint 0 plan.

---

## 5. Alternatives considered

- **For UPL-28 focus-clear: `setFocusPolicy(Qt.FocusPolicy.NoFocus)` on the top-level widget** — rejected because Qt's focus policy on a container does not prevent child widgets from receiving focus via tab-cycle. `clearFocus()` is the correct primitive.
- **For UPL-28 focus-clear: `QApplication.focusWidget().clearFocus()` with a None guard** — functionally identical to `widget.clearFocus()` but more verbose. Rejected in favor of the simpler form.
- **For UPL-27: using `QFrame` or `QGroupBox` as the dock title stand-in** — rejected because the production app uses `QDockWidget` and `APP_STYLESHEET` styles `QDockWidget::title` specifically; a `QFrame` would not trigger that rule.
- **For UPL-9: also updating the visual-scout render template's `add_mesh` call** — rejected because the scout template's purpose is to render surfaces in isolation for gap identification, not to replicate app rendering exactly. Adding ambient/diffuse to the template would be a separate decision. The brief does not prescribe this.
- **For UPL-9: modifying `appearance_panel.apply_to_actor()`** — rejected because ambient/diffuse are scene-level VTK lighting parameters best set at `add_mesh` time alongside `smooth_shading`/`specular`; `apply_to_actor` handles actor-level properties (color, opacity, wireframe) after the mesh is added.

---

## 6. Risks and unknowns

### UPL-9

- **VTK version behavior:** `ambient` and `diffuse` are passed to the VTK property via PyVista's `add_mesh`. The pinned range is `pyvista>=0.46,<0.49`. Both kwargs have been stable across this range. No known breakage.
- **Actor vs scene lighting interaction:** `appearance_panel.apply_to_actor(self._actor)` is called at `app.py:380` immediately after `add_mesh`. If `AppearancePanel` sets actor properties that override ambient/diffuse (e.g., a future "flat shading" toggle), the UPL-9 values would be overwritten. Check `appearance_panel.py` for any `prop.SetAmbient` / `prop.SetDiffuse` calls — none found in the current codebase, so no risk at this time.
- **No AI-N conflicts** — this is a 2-kwarg addition to a single call. AI-6 (pipeline discipline) is not affected (we are not changing the mesh generator). AI-9 (re-entrancy) is not affected (no new `processEvents()` call).

### UPL-27

- **`QDockWidget` geometry under offscreen:** the offscreen platform renders widgets at their logical size. `QDockWidget` adds a title bar (~24px typically) so the captured PNG will be taller than the bare panel by the title bar height. The `HIRES_SIZE = QSize(640, 1440)` is tall enough that this is not a problem.
- **`setWidget()` sizing:** `QDockWidget.setWidget(panel)` may not call `adjustSize()` on the dock automatically. The `_grab()` helper already calls `widget.adjustSize()` after the first `processEvents()`, so this should be handled. If the dock title bar squashes the panel, the implementer should call `dock.adjustSize()` explicitly before `_grab()`.
- **Integrity check pairing:** the integrity check at lines 356-366 constructs paths from the original basename convention (`f"{panel}-{theme_name}-empty-default.png"`). The dock wrapping does not change filenames, so the integrity loop needs no edits. **Verify this is correct after implementation** — if the output filename changes accidentally, the check would silently pass (two new paths that differ from each other, both new).
- **AI-3 compliance:** explicitly cleared by the AI-3 clarifying paragraph. The bare `QDockWidget` outside `QMainWindow` is explicitly allowed.
- **AI-11 compliance:** `Qt.DockWidgetArea` is not needed (we are not calling `addDockWidget`). The only Qt enum that may appear is for `setFeatures` (if the implementer wants to hide the close button) — but the brief does not require `setFeatures`. If added, use `QDockWidget.DockWidgetFeature.DockWidgetMovable` (qualified form, AI-11).

### UPL-28

- **`clearFocus()` timing:** must be called after `widget.show()` but before `widget.grab()`. The current `_grab()` sequence is: `show()` → `processEvents()` → `adjustSize()` → `processEvents()` → `grab()`. Inserting `clearFocus()` between `show()` and the first `processEvents()` is correct — focus is cleared before the event-drain would process any focus-in events.
- **Agent-prompts.md is a non-code reference file:** edits here are safe and do not affect any tests. The visual-scout sub-agent reads this file verbatim and executes the render template code block. The `p.set_background('#2f2f2f')` insertion is a one-liner that does not change any other behavior.
- **AI-13 compliance:** `#2f2f2f` is 6-digit hex. Compliant.
- **AI-11 compliance:** `Qt.FocusPolicy.NoFocus` would be fully qualified if used; `clearFocus()` has no Qt enum at all. Either approach is AI-11 compliant.

---

## 7. AI-15 disclaimers

Not applicable. None of the three candidates proposes a new variety, figure, or mathematical claim. UPL-9 is a lighting parameter change; UPL-27 and UPL-28 are tooling changes. No tooltip text needs updating.

---

## 8. Open questions for the user

None. All three candidates are fully specified in the milestone brief and the final-report prior art. The implementer can proceed without further clarification.
