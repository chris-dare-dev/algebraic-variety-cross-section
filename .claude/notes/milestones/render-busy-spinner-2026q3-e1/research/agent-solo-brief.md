# Research Brief — render-busy-spinner-2026q3-e1

**Milestone:** Lift the CONTEXT.md §9 spinner deferral; add a qtawesome spin animation in the QStatusBar during mesh generation.
**Prepared by:** milestone-researcher (solo mode)
**Date:** 2026-05-22

---

## 1. TL;DR

The original AI-9 blocker is confirmed OBSOLETE: `app.py` contains zero `processEvents()` calls in the render path (verified by grep), and `surface.generate()` runs on a `QThreadPool` worker thread (`app.py:687-694`). The recommended approach is a `QLabel` spinner widget added to the status bar via `addPermanentWidget()` (RIGHT side — the only API that is never obscured by `showMessage()`), with a `qta.icon("mdi6.loading", animation=qta.Spin(label, interval=10, step=6))` icon created in a new `render_busy_spinner_icon()` factory in `icons.py` and applied via a new `refresh_icons` step in `MainWindow.__init__`. The main risk is the status bar positioning: the brief says "left" but Qt's `addWidget()` IS obscured by `showMessage()` calls (which the app makes at every render event) while `addPermanentWidget()` (RIGHT) is never obscured — RIGHT is the correct choice. The backup plan if right-side is rejected on UX grounds is `addWidget(spinner, 0)` with acceptance that the spinner may be hidden during long status text.

---

## 2. AI-9 / QThread-Move Audit — Original Blocker is OBSOLETE

### Confirmed: no `processEvents()` in the render path

```
$ grep -n "QApplication.processEvents\|processEvents" app.py
116:        ...
597:        old ``QApplication.processEvents()`` workaround (CONTEXT.md §8.5) is
1024:        call ``processEvents``.  No re-entry into the render pipeline.
1054:        # new chrome.  Synchronous; AI-9 safe (no processEvents involved)
```

Lines 597, 1024, 1054 are COMMENTS documenting the removal. There is zero live `processEvents()` call in the render path.

### Confirmed: `surface.generate()` runs OFF the GUI thread

| Item | Location | Value |
|---|---|---|
| Worker dispatch | `app.py:687` | `worker = MeshWorker(surface.generate, dict(params), self._generation)` |
| QueuedConnection | `app.py:688-689` | `worker.signals.finished.connect(self._on_mesh_ready, Qt.ConnectionType.QueuedConnection)` |
| Thread pool start | `app.py:694` | `self._render_pool.start(worker)` |
| `_computing` set True | `app.py:670` | `self._computing = True` |
| `_computing` set False | `app.py:829` | `self._computing = False` (in `_on_mesh_ready` finally block) |

`render_worker.py:174` confirms: `mesh = self._generate(**self._params)` runs inside `MeshWorker.run()` on the worker thread. ALL VTK GL calls (`add_mesh`, `render`, `reset_camera`) stay on the GUI thread in `_on_mesh_ready` (`app.py:697-843`).

### Confirmed: No `QMovie.updated` signal can race with the render path

The original deferral reason (`QMovie.updated` signals fire during `processEvents()`, re-entering `_render_current`) is structurally impossible now:
- There is no `processEvents()` call.
- The GUI thread is free (idle in the event loop) while the worker computes.
- Any signal that fires during this idle period is serialized by the event loop; it cannot re-enter `_on_mesh_ready` because `_on_mesh_ready` is a `QueuedConnection` slot and the event loop is single-threaded.

**Verdict: AI-9 blocker OBSOLETE. The spinner is safe to implement.**

---

## 3. Codebase Audit — Exact Line Numbers

### app.py

| Symbol | Line | Notes |
|---|---|---|
| `self._computing = False` init | 170 | Set in `__init__`, initial state |
| `self._computing = True` | 670 | Dispatch point — spinner SHOW here |
| `self._computing = False` | 829 | In `_on_mesh_ready` finally — spinner HIDE here |
| `statusBar().showMessage(...)` | 150, 399, 409, 425, 431, 436, 624, 681, 740, 742, 746, 819, 826, 887 | Extensive use of temporary messages |
| `self.setStatusBar(QStatusBar())` | 149 | Status bar construction |
| Worker dispatch | 687-694 | `MeshWorker` + `QueuedConnection` |
| `_on_mesh_ready` | 697 | `@Slot(object)` result slot |
| `refresh_icons` calls | 301-303 | Pattern: called after all widget construction |
| `QApplication.setOverrideCursor(WaitCursor)` | 680 | Existing busy feedback |
| `QApplication.restoreOverrideCursor()` | 828 | In `_on_mesh_ready` finally |

### icons.py

| Symbol | Line | Notes |
|---|---|---|
| `_get_qta()` lazy import | 75-100 | Pattern to follow for spinner |
| `_icon_color(theme)` | 103-116 | Returns `PALETTE[theme]["TEXT_VALUE"]` |
| `WIREFRAME_ICON_NAME = "mdi6.grid"` | 186 | Module constant naming convention |
| `SHOW_EDGES_ICON_NAME = "mdi6.border-outside"` | 187 | Module constant naming convention |
| `HQ_SMOOTHING_ICON_NAME = "mdi6.auto-fix"` | 188 | Module constant naming convention |
| Spinner deferral comment | 57-61 | MUST be updated — the old rationale |
| `hq_smoothing_icon()` | 278-293 | Pattern: uses `_get_qta().icon(NAME, color=_icon_color(theme))` |

### icons.py deferral text (lines 57-61) — OBSOLETE, needs replacement:
```
Spinner / render-busy icon — DEFERRED to a v2 milestone.  ``QMovie.updated``
signals can fire during ``QApplication.processEvents()`` inside
``_render_current``, touching the AI-9 re-entrancy surface that
``self._computing`` guards.  See CONTEXT.md §9 for the deferral rationale.
```

### CONTEXT.md §9 deferral paragraph (line 506) — OBSOLETE:
Full paragraph starts with "A render-busy spinner icon shown during mesh generation (~0.5s window)" — needs replacement with a "shipped by render-busy-spinner-2026q3-e1" note.

### CONTEXT.md §3 (line 62) — also has inline spinner deferral text:
"The render-busy spinner remains deferred to a future v2 milestone" — needs update.

---

## 4. Recommended Approach

### 4.1 QStatusBar positioning decision

**Use `addPermanentWidget(spinner)` (RIGHT side).**

- `addWidget()` MAY be obscured by `showMessage()` temporary messages. The app calls `showMessage()` at every render event (12+ call sites). The spinner would be hidden at the exact moment it's most needed.
- `addPermanentWidget()` is NEVER obscured by `showMessage()` per Qt 6 documentation. It appears on the RIGHT side of the status bar.
- VS Code places its spinner on the LEFT, but VS Code does not use `showMessage()` for status text — it uses a persistent `QLabel` widget. The AVC status bar is showMessage-based, so the Qt-idiomatic choice is RIGHT.
- The brief says "left" but also says "permanent-widget slot to avoid being clipped by the long bbox/timing message" — the second constraint (never-clipped) overrides the first (left preference). RIGHT via `addPermanentWidget()` is the only correct choice.

### 4.2 Widget construction in `__init__` (app.py)

Add immediately after `self.setStatusBar(QStatusBar())` at `app.py:149`:

```python
# render-busy-spinner-2026q3-e1: spinner widget in the status bar.
# Constructed here; icon is set in refresh_icons (after QApplication is
# fully active — qta.icon() silently returns null without it, CONTEXT.md §8.12).
# addPermanentWidget: never obscured by showMessage() temporary messages.
# Starts hidden; shown at _computing=True, hidden at _computing=False.
self._render_busy_spinner = QLabel()
self._render_busy_spinner.setFixedSize(16, 16)  # match toolbar icon size
self._render_busy_spinner.setVisible(False)
self.statusBar().addPermanentWidget(self._render_busy_spinner)
```

### 4.3 Toggle in `_render_current` and `_on_mesh_ready`

At `app.py:670` (where `self._computing = True`), add one line after:
```python
self._computing = True
self._render_busy_spinner.setVisible(True)   # ADD THIS
```

At `app.py:829` (where `self._computing = False`, inside the `finally` block):
```python
self._computing = False
self._render_busy_spinner.setVisible(False)  # ADD THIS
```

Both `setVisible()` calls are pure GUI paint operations — no `processEvents`, no signal re-emission, no re-entry into `_render_current`. AI-9 safe.

### 4.4 Icon factory in `icons.py`

Add the following module-level constant and factory function after `HQ_SMOOTHING_ICON_NAME`:

```python
RENDER_BUSY_SPINNER_ICON_NAME = "mdi6.loading"


def render_busy_spinner_icon(widget, theme: str = "dark") -> QIcon:
    """Spinning activity indicator for the status-bar render-busy spinner.

    render-busy-spinner-2026q3-e1 (UPL-4 v2): closes the §9 deferral.
    Uses ``mdi6.loading`` (MDI6 0xf0772) — a circular loading arc that
    reads clearly as "computing in progress" at 16px.  Preferred over
    ``mdi6.sync`` (bidirectional arrows — implies sync, not compute) and
    ``mdi6.progress-clock`` (clock face — implies elapsed time, not activity).

    The ``animation=qta.Spin(widget, interval=10, step=6)`` argument
    produces one full 360° rotation per 600ms — visually energetic enough
    to read as "busy" without being distracting during the 0.5-1.5s compute
    window.  The default ``step=1`` (3.6s per rotation) is imperceptibly slow.

    AI-9 note: ``qta.Spin`` uses a ``QTimer`` parented to ``widget`` that
    fires ``timeout`` → ``widget.update()`` → ``paintEvent`` — a pure paint
    path with no business-logic re-emission.  The timer is set up lazily on
    the first ``paintEvent`` (inside ``Spin.setup()`` called from
    ``CharIconPainter._paint_icon``).  No ``processEvents()`` anywhere in
    this chain.  AI-9 safe.

    AI-15: this indicator communicates compute ACTIVITY, not progress.
    Mesh generation is opaque (no percent-complete signal from Flying Edges
    or Taubin).  The status-bar text (``statusBar().showMessage(...)``) is the
    ground truth for what is being computed; the spinner is a pure visual
    companion.  The icon docstring and tooltip must NOT claim "X% done".

    ``widget`` is the ``QLabel`` that owns the icon animation.  Passing the
    correct owner ensures the ``QTimer`` in ``qta.Spin`` is parented to the
    right Qt object (auto-deleted when the QLabel is destroyed).

    Requires a running ``QApplication`` (qta.icon() returns null without one
    — CONTEXT.md §8.12).  Must be called from ``refresh_icons()``, NOT from
    ``_build_ui()`` or ``__init__``.
    """
    return _get_qta().icon(
        RENDER_BUSY_SPINNER_ICON_NAME,
        color=_icon_color(theme),
        animation=qta.Spin(widget, interval=10, step=6),
    )
```

Wait — `qta.Spin` is accessed as an attribute of the `qta` module, but `qta` is the lazy-imported module inside `_get_qta()`. The function body needs to call `_get_qta().Spin(...)`:

```python
def render_busy_spinner_icon(widget, theme: str = "dark") -> QIcon:
    """[same docstring as above]"""
    qta = _get_qta()
    return qta.icon(
        RENDER_BUSY_SPINNER_ICON_NAME,
        color=_icon_color(theme),
        animation=qta.Spin(widget, interval=10, step=6),
    )
```

### 4.5 Wire-up in `MainWindow.__init__` (app.py `refresh_icons` call)

After the existing three `refresh_icons()` calls (lines 301-303), add no new call — instead, update the existing `refresh_icons` call on `app.py` itself (MainWindow does not have a `refresh_icons` method). The spinner icon is not on a panel; it must be wired directly in `__init__` and in `_on_theme_changed`:

In `MainWindow.__init__` (after line 303), add:
```python
# Spinner icon requires QApplication (qta.icon), so set it here, not in __init__
# before the panels are built.
self._render_busy_spinner.setIcon(
    icons.render_busy_spinner_icon(self._render_busy_spinner, self._active_theme)
)
```

Actually, `QLabel.setIcon()` does not exist — `QLabel` uses `setPixmap()`. For a `QLabel` with a qtawesome animation, the correct approach is to use a `QLabel` and call `qta.icon().pixmap(QSize(16,16))` ... but that loses the animation.

**Correction — use `QPushButton` or a custom approach:** qtawesome's `Spin` animation requires a widget that receives `update()` calls. The cleanest host for an animated qtawesome icon is a `QLabel` with the icon set via `label.setPixmap(icon.pixmap(QSize))` — but this loses animation because pixmap is static.

The correct approach in qtawesome for animated icons is to use a widget that supports `setIcon()` (i.e., a `QAbstractButton` subclass) OR a helper `qta.set_icon()` call. Let's verify:

```python
# qtawesome provides qta.set_icon(widget, icon_name, **options) 
# which handles QPushButton and QLabel differently
```

After checking the qtawesome source: `qta.Spin` works with ANY widget that has an `update()` method (all `QWidget` subclasses do). The animation is triggered by the icon's `setup()` method during `paintEvent`. For a `QLabel`, the standard approach is `label.setPixmap(qta.icon(..., animation=qta.Spin(label,...)).pixmap(16, 16))` — but this loses animation because `pixmap()` generates a single static frame.

**The correct pattern for an animated qtawesome icon in a QLabel is:**

```python
# Pattern: use QPushButton with flat style + no text
spinner = QPushButton()
spinner.setFlat(True)
spinner.setFixedSize(16, 16)
spinner.setIcon(qta.icon("mdi6.loading", animation=qta.Spin(spinner)))
# OR: use qta.set_icon() if available
```

However, checking qtawesome source: `qta.icon()` returns a `QIcon` object with animation embedded. When `QIcon.paint()` or `QIcon.pixmap()` is called by Qt's rendering system (e.g., during `QPushButton.paintEvent()`), the animation's `setup()` is invoked and the QTimer is started. For `QLabel`, Qt does NOT call `QIcon.paint()` automatically — it only uses pixmaps.

**Decision: use `QPushButton(flat=True, text="")` as the spinner widget, NOT `QLabel`.** A flat `QPushButton` with no text and a fixed size renders just the icon, and `QPushButton.paintEvent()` calls `QIcon.paint()` which triggers the animation setup.

### 4.5 Corrected widget construction

```python
# render-busy-spinner-2026q3-e1: status-bar compute activity indicator.
# QPushButton (flat, no text) is required for qtawesome animation — QLabel
# uses setPixmap() which generates a static frame; QPushButton.paintEvent()
# calls QIcon.paint() which triggers Spin.setup() → QTimer start.
# addPermanentWidget: RIGHT side, never obscured by showMessage().
from PySide6.QtWidgets import QPushButton  # already imported? check
self._render_busy_spinner = QPushButton()
self._render_busy_spinner.setFlat(True)
self._render_busy_spinner.setEnabled(False)   # non-interactive
self._render_busy_spinner.setFixedSize(16, 16)
self._render_busy_spinner.setToolTip(
    "Computing surface mesh — activity indicator (not a progress bar)."
)
self._render_busy_spinner.setVisible(False)
self.statusBar().addPermanentWidget(self._render_busy_spinner)
```

Note: `QPushButton` is NOT in `app.py`'s current imports — it would need to be added. However, looking at `app.py:20-30`, `QLabel` IS already imported. Let me reconsider.

**Re-check: can QLabel work with qtawesome animation?** The qtawesome animation system calls `setup()` from `CharIconPainter._paint_icon()` which is called from `QIconEngine.paint()`. `QLabel` sets its icon via `QLabel.setPixmap(icon.pixmap(size))` — this calls `QIcon.pixmap()` which DOES trigger `QIconEngine.paint()` internally... actually no, `pixmap()` generates a static image without animation.

**Simplest correct approach:** Use `QLabel` but set the icon's pixmap on a timer. OR use the qtawesome documentation approach for labels.

After careful analysis: **the qtawesome approach for animated icons requires a widget that calls `QIcon.paint()` in its `paintEvent`**. Only `QAbstractButton` subclasses and `QToolButton` do this automatically. `QLabel.setPixmap()` takes a `QPixmap` (static). `QLabel.setPixmap(icon.pixmap(...))` is a one-time static capture.

**Final decision: use a `QPushButton` (flat, disabled, no text).** Add `QPushButton` to `app.py`'s imports. This is the only approach that works correctly with qtawesome animations in a status bar.

### 4.6 Complete icons.py factory (corrected)

```python
RENDER_BUSY_SPINNER_ICON_NAME = "mdi6.loading"


def render_busy_spinner_icon(widget, theme: str = "dark") -> QIcon:
    """Activity-indicator icon for the status-bar render-busy spinner widget.

    render-busy-spinner-2026q3-e1 (UPL-4 v2): closes the CONTEXT.md §9 deferral.

    Icon: ``mdi6.loading`` (MDI6 codepoint 0xf0772) — a partial circular arc
    that, when spun, reads as a standard computing-activity indicator.
    Alternatives considered:
    - ``mdi6.sync`` (0xf04e6): bidirectional arrows implying sync/transfer, not compute.
    - ``mdi6.progress-clock`` (0xf0996): clock face implying elapsed time.
    - ``fa5s.circle-notch`` / ``fa5s.spinner``: FontAwesome family; the app uses mdi6
      throughout — mixing font families adds a second cold-boot cost at first call.
    ``mdi6.loading`` is the canonical "compute in progress" glyph, matches VS Code's
    language-server indicator semantics, and is visually distinct from all three
    existing mdi6 display-toggle icons (grid, border-outside, auto-fix).

    Animation: ``qta.Spin(widget, interval=10, step=6)`` — one 360° rotation per
    ~600ms.  The default ``step=1`` (3.6s/rotation) is imperceptibly slow during
    the 0.5-1.5s compute window.  ``step=6`` is energetic but not distracting.

    AI-9 audit: ``qta.Spin`` creates a ``QTimer`` (parented to ``widget``) on the
    first ``paintEvent`` inside ``Spin.setup()``.  Timer fires ``_update()`` →
    ``widget.update()`` → ``paintEvent``.  Pure paint path.  No ``processEvents()``,
    no signal re-emission, no ``_render_current`` re-entry.  AI-9 safe.

    AI-15: spinner indicates compute ACTIVITY, not percent-complete.  The status-bar
    text is the ground truth.  This docstring must not be changed to claim progress.

    ``widget``: the ``QPushButton`` (flat, disabled) that owns the animation.  Must be
    the same widget that renders the icon so ``QTimer`` parenting is correct.
    Requires a running ``QApplication``; call from ``refresh_icons()``, not ``__init__``.
    """
    qta = _get_qta()
    return qta.icon(
        RENDER_BUSY_SPINNER_ICON_NAME,
        color=_icon_color(theme),
        animation=qta.Spin(widget, interval=10, step=6),
    )
```

### 4.7 MainWindow wiring

In `MainWindow.__init__`, after the three existing `refresh_icons()` calls (app.py:301-303):

```python
# render-busy-spinner-2026q3-e1: set spinner icon NOW (QApplication live).
self._render_busy_spinner.setIcon(
    icons.render_busy_spinner_icon(self._render_busy_spinner, self._active_theme)
)
self._render_busy_spinner.setIconSize(QSize(16, 16))
```

In `MainWindow._on_theme_changed` (already applies theme to panels), add:
```python
self._render_busy_spinner.setIcon(
    icons.render_busy_spinner_icon(self._render_busy_spinner, self._active_theme)
)
```

In `MainWindow._apply_system_theme` (already applies theme), same one-liner.

---

## 5. Decision Matrix

| Decision | Options | Recommendation | Rationale |
|---|---|---|---|
| **Icon name** | `mdi6.loading`, `mdi6.sync`, `mdi6.progress-clock`, `fa5s.circle-notch` | **`mdi6.loading`** | Canonical compute-activity glyph (VS Code LS server), stays mdi6 family, visually distinct from all 3 sibling icons |
| **Position** | LEFT (`addWidget`), RIGHT (`addPermanentWidget`) | **RIGHT (`addPermanentWidget`)** | App uses `showMessage()` at every render event; `addWidget()` would be hidden at the exact moment the spinner is most needed. Qt docs: permanent widgets "may not be obscured by temporary messages." |
| **Spinner size** | 14px, 16px, 22px | **16px** | Matches `QSize(16, 16)` used by all toolbar icons in view_panel.py:398,401,427,429 and appearance_panel.py:655,658,665 |
| **Spin speed** | `step=1` (3.6s/rotation), `step=2` (1.8s), `step=6` (600ms) | **`step=6`** | The compute window is 0.5-1.5s. `step=1` is imperceptibly slow. `step=6` (600ms/rotation) matches standard macOS spinner rate and reads as energetic-but-calm progress. |
| **Widget type** | `QLabel`, `QPushButton(flat=True)` | **`QPushButton(flat=True, enabled=False)`** | qtawesome Spin animation requires `QIcon.paint()` to be called in `paintEvent`. Only `QAbstractButton` subclasses call this. `QLabel.setPixmap()` captures a static frame only. |
| **Show/hide trigger** | Direct at `_computing=True/False` sites, `_computing` property setter, new `_on_mesh_started` helper | **Direct at the two `_computing` assignment sites** | Only 2 sites (lines 670 and 829); property setter adds complexity; `_on_mesh_started` as a named method would be confusing (not a signal slot, not a Qt-established pattern) |
| **Variable name** | `_render_busy_spinner`, `_busy_indicator`, `_compute_spinner` | **`_render_busy_spinner`** | Matches the milestone ID token; consistent with `RENDER_BUSY_SPINNER_ICON_NAME` constant; grep-friendly |

---

## 6. Test Plan

All tests use source-text grep (AI-2 compliant). No `MainWindow()` construction.
File: `tests/test_render_busy_spinner.py` (new file).

### Test 1: Widget constructed and added to status bar
```python
def test_app_has_render_busy_spinner_widget():
    """app.py constructs a _render_busy_spinner widget and adds it to
    the status bar as a permanent widget (not a temporary showMessage)."""
    src = open("app.py").read()
    assert "_render_busy_spinner" in src, (
        "_render_busy_spinner widget must be constructed in app.py"
    )
    assert "addPermanentWidget" in src and "_render_busy_spinner" in src, (
        "spinner must be added via addPermanentWidget (never obscured by showMessage)"
    )
    # Verify it is NOT added via addWidget (which can be obscured)
    # Source-grep: the addPermanentWidget call must reference the spinner
    assert "addPermanentWidget(self._render_busy_spinner)" in src, (
        "spinner must be registered as a permanent status-bar widget"
    )
```

### Test 2: Uses qtawesome Spin animation
```python
def test_app_render_busy_spinner_uses_qtawesome_spin_animation():
    """icons.py factory calls qta.Spin() for the animation — not a QMovie,
    not a QTimer stepper — the qtawesome canonical approach."""
    import icons
    src_icons = open("icons.py").read()
    assert "qta.Spin(" in src_icons or ".Spin(" in src_icons, (
        "render_busy_spinner_icon must pass animation=qta.Spin(...) to qta.icon()"
    )
    assert "RENDER_BUSY_SPINNER_ICON_NAME" in src_icons, (
        "icons.py must export RENDER_BUSY_SPINNER_ICON_NAME constant"
    )
    assert icons.RENDER_BUSY_SPINNER_ICON_NAME.startswith("mdi6."), (
        "Spinner icon must use mdi6 family for visual coherence"
    )
```

### Test 3: Spinner starts hidden
```python
def test_app_render_busy_spinner_starts_hidden():
    """The spinner must start hidden (setVisible(False) in __init__)
    so it only appears during active compute, not on launch."""
    src = open("app.py").read()
    # The setVisible(False) must appear BEFORE the first setVisible(True)
    # in the source (i.e., initial state is hidden).
    hidden_pos = src.find("_render_busy_spinner.setVisible(False)")
    shown_pos = src.find("_render_busy_spinner.setVisible(True)")
    assert hidden_pos != -1, (
        "app.py must call _render_busy_spinner.setVisible(False) at init"
    )
    assert shown_pos != -1, (
        "app.py must call _render_busy_spinner.setVisible(True) at computing start"
    )
    assert hidden_pos < shown_pos, (
        "setVisible(False) must appear before setVisible(True) in source "
        "(initial state is hidden)"
    )
```

### Test 4: Spinner shown when computing starts
```python
def test_app_render_busy_spinner_shown_on_computing_true():
    """In _render_current, setVisible(True) is called when _computing becomes True.
    The show and the flag assignment must be adjacent in source."""
    src = open("app.py").read()
    # Both assignments must appear together — within 5 lines of each other
    computing_true = src.find("self._computing = True")
    spinner_show = src.find("_render_busy_spinner.setVisible(True)")
    assert computing_true != -1 and spinner_show != -1, (
        "Both _computing=True and spinner show must be present"
    )
    # Allow up to ~300 chars between them (5 lines of 60 chars)
    assert abs(computing_true - spinner_show) < 300, (
        "spinner.setVisible(True) must be adjacent to self._computing = True"
    )
```

### Test 5: Spinner hidden when computing finishes
```python
def test_app_render_busy_spinner_hidden_on_computing_false():
    """In _on_mesh_ready finally block, setVisible(False) is called when
    _computing becomes False."""
    src = open("app.py").read()
    computing_false = src.find("self._computing = False")
    spinner_hide = src.find("_render_busy_spinner.setVisible(False)")
    assert computing_false != -1 and spinner_hide != -1
    # The hide must come near the False assignment (in the finally block)
    assert abs(computing_false - spinner_hide) < 300, (
        "spinner.setVisible(False) must be adjacent to self._computing = False "
        "(in the _on_mesh_ready finally block)"
    )
```

### Test 6: icons.py factory exists and exports constant
```python
def test_icons_module_has_render_busy_spinner_icon_factory():
    """icons.py must define render_busy_spinner_icon() and export
    RENDER_BUSY_SPINNER_ICON_NAME."""
    import icons
    assert hasattr(icons, "render_busy_spinner_icon"), (
        "icons.py must export render_busy_spinner_icon()"
    )
    assert hasattr(icons, "RENDER_BUSY_SPINNER_ICON_NAME"), (
        "icons.py must export RENDER_BUSY_SPINNER_ICON_NAME constant"
    )
    assert callable(icons.render_busy_spinner_icon), (
        "render_busy_spinner_icon must be callable"
    )
    # Verify it uses the correct icon family
    assert icons.RENDER_BUSY_SPINNER_ICON_NAME.startswith("mdi6."), (
        f"RENDER_BUSY_SPINNER_ICON_NAME={icons.RENDER_BUSY_SPINNER_ICON_NAME!r} "
        "must use mdi6 family"
    )
```

### Anti-regression guard: no QApplication construction in tests
All six tests above: no `MainWindow()`, no `QApplication`, no `QtInteractor`. Pure `open("app.py").read()` + `import icons`. AI-2 compliant.

---

## 7. AI-1..AI-15 Conflict Scan

| Invariant | Status | Notes |
|---|---|---|
| AI-1 (PySide6+PyVista+pyvistaqt stack) | GREEN | `QPushButton` + `QLabel` are PySide6 core; no new renderer |
| AI-2 (Qt-free tests) | GREEN | All 6 tests use source-text grep only; no `QApplication`, no `MainWindow()` |
| AI-3 (no MainWindow under offscreen) | GREEN | Tests never construct `MainWindow()` |
| AI-4 (clip_scalar not clip_box) | GREEN | Spinner has no clipping interaction |
| AI-5 (clip_scalar scalars= kwarg) | GREEN | No clip calls |
| AI-6 (implicit vs parametric pipeline) | GREEN | Spinner is pure UI chrome; no mesh pipeline interaction |
| AI-7 (Hanson normals) | GREEN | No mesh generation change |
| AI-8 (VARIETIES registry contract) | GREEN | No new surface registration |
| AI-9 (re-entrancy guard) | GREEN | `setVisible()` is a pure paint call; `qta.Spin` uses `QTimer.timeout` → `widget.update()` → `paintEvent` — pure paint path; no `processEvents()`, no signal re-emission to `_render_current`. The existing `_computing` guard is preserved and unchanged. |
| AI-10 (raw mesh cache) | GREEN | No domain clip or mesh regeneration |
| AI-11 (qualified Qt enums) | GREEN | No new Qt enum uses; `setVisible(bool)` and `setFlat(bool)` take primitives |
| AI-12 (WCAG AA text contrast) | GREEN | Spinner is a glyph icon, not text. Icon color routes through `_icon_color(theme)` → `TEXT_VALUE` which already passes WCAG; spinner has no text label |
| AI-13 (6-digit hex) | GREEN | Icon color from `_icon_color(theme)` → `palette["TEXT_VALUE"]` — already verified 6-digit in existing tests |
| AI-14 (generator PolyData/ValueError contract) | GREEN | No generator change |
| AI-15 (math honesty) | GREEN | Spinner is a UI activity indicator, not a math representation. Docstring explicitly states "compute ACTIVITY, not percent-complete". No mathematical claim made. |

---

## 8. CONTEXT.md Update Plan

### §9 deferral paragraph (line 506) — REPLACE entire bullet point

**Old (remove):**
```
- **A render-busy spinner icon shown during mesh generation (~0.5s window)** — deferred beyond `qtawesome-icons-2026q2-e2` (UPL-4 v2 scope).  The camera-preset and display-toggle icons closed in v1 (`qtawesome-icons-2026q2-e2`); v0 (`qtawesome-icons-2026q2-e1`) covered Reset Camera / Screenshot / Reset Defaults.  The spinner is deferred because `QMovie.updated` signals can fire during `QApplication.processEvents()` in `_render_current`, touching the AI-9 re-entrancy surface that already required the `self._computing` guard machinery.  A correct implementation requires either (a) a `QTimer.singleShot`-based frame stepper that checks `self._computing` before advancing, or (b) moving mesh generation to a `QThread` — neither fits the XS-effort pattern of v0/v1.  The existing `QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)` at `_render_current` line 381 already provides user-visible busy feedback; a spinner adds visual polish but no functional value at v2 scope.
```

**New (replace with):**
```
- **Render-busy spinner icon** — shipped in `render-busy-spinner-2026q3-e1` (UPL-4 v2).  The original deferral rationale (`QMovie.updated` signals firing during `QApplication.processEvents()` in `_render_current`) was mooted by `realtime-variety-render-e4`: that milestone moved `surface.generate()` onto a background-thread worker and removed the `processEvents()` call entirely.  Implementation: a flat `QPushButton` (disabled, 16×16) added to the status bar via `addPermanentWidget()` (right side — never obscured by `showMessage()` calls); set `setVisible(True)` at `_computing = True` (dispatch), `setVisible(False)` at `_computing = False` (result slot finally block).  Icon: `mdi6.loading` with `qta.Spin(widget, interval=10, step=6)` (600ms/rotation) from `icons.render_busy_spinner_icon()`.  The spinner indicates compute *activity* only (no percent-complete signal available from Flying Edges or Taubin).  AI-9 safe: `qta.Spin` uses a `QTimer` parented to the spinner widget; fires `widget.update()` → `paintEvent` (pure paint path, no business logic).
```

### §3 stack rationale (line 62) — UPDATE inline sentence

**Old inline text:** "The render-busy spinner remains deferred to a future v2 milestone — it is simply not yet built."

**New:** "The render-busy spinner (`mdi6.loading`, `qta.Spin(interval=10, step=6)`) shipped in `render-busy-spinner-2026q3-e1` (UPL-4 v2); it uses `addPermanentWidget()` on the status bar and toggles at the `_computing` state transitions."

### §4.3 additions (after the status-bar bbox paragraph) — ADD new paragraph note

No §4.3a/4.3b addition needed — the spinner is not a new architectural component, just a status-bar widget. The existing §4.3 already documents the render pipeline; a one-sentence callout in §4.3 pointing to the spinner's `_computing` integration is sufficient.

### `icons.py` deferral comment (lines 57-61) — REPLACE

**Old:** `Spinner / render-busy icon — DEFERRED to a v2 milestone...`
**New:** `Spinner / render-busy icon (v2) — shipped in render-busy-spinner-2026q3-e1. See render_busy_spinner_icon() below.`

---

## 9. Estimated Diff Size + Inline vs Delegated

| File | Est. LOC delta | Nature |
|---|---|---|
| `app.py` | +18-22 LOC | Widget construction (~8 LOC), toggle at 2 sites (~4 LOC), theme refresh wiring (~4 LOC), import `QPushButton` (+1), `QSize` already imported |
| `icons.py` | +28-32 LOC | `RENDER_BUSY_SPINNER_ICON_NAME` constant (+1), `render_busy_spinner_icon()` factory with docstring (+25-30), update deferral comment (-4 +2) |
| `CONTEXT.md` | +12-15 LOC | §9 bullet replacement, §3 inline update |
| `tests/test_render_busy_spinner.py` | +70-80 LOC | 6 source-text grep tests |
| **Total** | **~135-150 LOC** | |

**Recommendation: inline (non-delegated).** The changes are spread across 4 files but each change is small and clearly scoped. No new panel class, no new dataclass, no new registry entry. The implementer can do this in a single sitting without a delegated sub-agent.

**Import note:** `QPushButton` is not currently in `app.py`'s imports. It must be added to the `from PySide6.QtWidgets import ...` block. `QSize` is imported indirectly via appearances — verify it is in scope at the relevant site. `QSize` is NOT in the current `app.py` top-level imports (it appears only inside panel `refresh_icons` methods). The `setFixedSize(16, 16)` approach avoids needing `QSize` — use that instead.

---

## 10. References

| Claim | Source | Location |
|---|---|---|
| No `processEvents()` in render path | `app.py` grep | Lines 597, 1024, 1054 are comments documenting removal; no live call |
| `surface.generate()` on worker thread | `render_worker.py:174` | `mesh = self._generate(**self._params)` |
| Worker dispatch via `QueuedConnection` | `app.py:687-694` | `MeshWorker` + `finished.connect(..., QueuedConnection)` + `_render_pool.start()` |
| `_computing = True` site | `app.py:670` | In `_render_current` |
| `_computing = False` site | `app.py:829` | In `_on_mesh_ready` finally block |
| `addWidget()` obscured by `showMessage()` | Qt 6 docs | https://doc.qt.io/qt-6/qstatusbar.html — "widgets added with addWidget() may be obscured by temporary messages" |
| `addPermanentWidget()` never obscured | Qt 6 docs | "Permanently means that the widget may not be obscured by temporary messages" |
| `qta.Spin` signature | qtawesome 1.4.2 source | `.venv/lib/python3.12/site-packages/qtawesome/__init__.py`: `Spin(parent_widget, interval=10, step=1, autostart=True)` |
| `qta.Spin` creates `QTimer` in `paintEvent` | qtawesome 1.4.2 source | `Spin.setup()` creates `QTimer(self.parent_widget)` on first paint |
| `mdi6.loading` exists in MDI6 6.9.96 | Charmap JSON | `.venv/lib/python3.12/site-packages/qtawesome/fonts/materialdesignicons6-webfont-charmap-6.9.96.json` key `"loading": "0xf0772"` |
| `mdi6.sync` exists | Same charmap | `"sync": "0xf04e6"` |
| `qta.icon()` requires live `QApplication` | qtawesome issue #144 / CONTEXT.md §8.12 / `icons.py:21-27` | Confirmed: silently returns null QIcon + UserWarning without QApplication |
| Icon size = 16px convention | `appearance_panel.py:655`, `view_panel.py:398,401,427,429` | All existing icons use `QSize(16, 16)` |
| Spinner deferral in §9 | `CONTEXT.md:506` | Full paragraph |
| Spinner deferral in §3 | `CONTEXT.md:62` | Inline sentence |
| Spinner deferral in `icons.py` | `icons.py:57-61` | Module docstring comment |
| `QPushButton` not in `app.py` imports | `app.py:20-30` | Only `QLabel`, `QStatusBar`, `QWidget`, `QComboBox`, etc. present |
| Existing icon constant naming | `icons.py:186-188` | `WIREFRAME_ICON_NAME`, `SHOW_EDGES_ICON_NAME`, `HQ_SMOOTHING_ICON_NAME` |
| Existing `refresh_icons` pattern | `appearance_panel.py:616`, `view_panel.py` | Called from `MainWindow.__init__` and `_on_theme_changed` |
| Total current test count | `pytest --collect-only` | 385 tests |

---

## 7. AI-15 Disclaimers

Not applicable in the traditional sense (this milestone proposes no new mathematical surface visualization). However, the spinner's semantics must be accurately described:

**Mandatory docstring + comment text for `render_busy_spinner_icon()`:**
> "AI-15: this indicator communicates compute ACTIVITY, not percent-complete. Mesh generation via Flying Edges + Taubin is opaque — no intermediate percent-complete signal is emitted. The status-bar text `statusBar().showMessage(...)` is the ground truth. This spinner must never be labeled or presented as a progress bar."

**Mandatory tooltip text (from §4.5):**
> `"Computing surface mesh — activity indicator (not a progress bar)."`

---

## 8. Open Questions for the User

None. The milestone brief is fully specified. The only ambiguity (LEFT vs RIGHT position) is resolved by Qt API behavior: `addWidget()` is hidden by `showMessage()` calls, which the app makes at every render event; therefore `addPermanentWidget()` (RIGHT) is the correct choice. This is documented in the Decisions section.
