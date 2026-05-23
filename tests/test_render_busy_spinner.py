"""Regression guards for the status-bar render-busy spinner.

render-busy-spinner-2026q3-e1 (UPL-4 v2): closes the CONTEXT.md §9
spinner deferral.  All tests here are pure source-text greps + a single
module-level import of ``icons`` — no ``QApplication`` construction, no
``MainWindow()`` construction, no Qt imports needed for the test
machinery (AI-2 / AI-3 compliant).

The seven tests below capture, in order:

1. The spinner widget is constructed in ``app.py`` and added to the
   status bar via the permanent-widget slot (not the temporary-widget
   slot — ``showMessage()`` would obscure it).
2. The icon factory in ``icons.py`` uses qtawesome's ``qta.Spin``
   animation (not a ``QMovie``, not a hand-rolled ``QTimer`` stepper).
3. The spinner starts hidden so it appears only during active compute.
4. The spinner becomes visible the moment ``self._computing = True``.
5. The spinner becomes hidden the moment ``self._computing = False``.
6. The ``icons.render_busy_spinner_icon`` factory + module constant exist
   and the constant pins the ``mdi6`` font family for visual coherence
   with the rest of the icon set.
7. The factory docstring carries an explicit AI-9 audit note + the
   word "paint" — anchors the future-maintainer understanding that
   ``qta.Spin``'s ``QTimer`` is a pure paint-path construct that cannot
   re-enter ``_render_current``.
"""
from __future__ import annotations

import pathlib


_APP_SRC = (
    pathlib.Path(__file__).resolve().parent.parent / "app.py"
).read_text(encoding="utf-8")
_ICONS_SRC = (
    pathlib.Path(__file__).resolve().parent.parent / "icons.py"
).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 1. Widget constructed + registered as PERMANENT (not temporary) status-bar widget
# ---------------------------------------------------------------------------


def test_app_has_render_busy_spinner_widget() -> None:
    """``app.py`` must construct a ``_render_busy_spinner`` widget and add
    it via ``addPermanentWidget`` — NOT via ``addWidget``.  ``addWidget``
    slots are obscured by ``showMessage()`` calls, which this app fires
    at every render event; the spinner would be hidden at the exact
    moment it is most needed.  The permanent-widget slot renders on the
    right side of the status bar and is never obscured.
    """
    assert "self._render_busy_spinner" in _APP_SRC, (
        "app.py must construct a self._render_busy_spinner widget — "
        "render-busy-spinner-2026q3-e1 introduces this name."
    )
    assert "addPermanentWidget(self._render_busy_spinner)" in _APP_SRC, (
        "app.py must register the spinner via "
        "self.statusBar().addPermanentWidget(self._render_busy_spinner) — "
        "addWidget() is obscured by showMessage(), which the app calls at "
        "every render event."
    )


# ---------------------------------------------------------------------------
# 2. Icon factory uses qtawesome qta.Spin animation
# ---------------------------------------------------------------------------


def test_app_render_busy_spinner_uses_qtawesome_spin_animation() -> None:
    """The icon factory in ``icons.py`` must use qtawesome's ``qta.Spin``
    animation — not a ``QMovie`` (the original §9 deferral was rooted in
    ``QMovie.updated`` racing the GUI thread; that approach is rejected
    even now that the AI-9 blocker is obsolete) and not a hand-rolled
    ``QTimer`` stepper (qtawesome already provides the canonical pattern).
    """
    assert "qta.Spin(" in _ICONS_SRC, (
        "icons.py render_busy_spinner_icon must call qta.Spin(...) "
        "(qtawesome's canonical animation primitive)."
    )
    # Guard against actual QMovie USAGE — historical-context mentions of
    # "QMovie" in comments/docstrings explaining why the original
    # spinner deferral chose to wait for the QThread move are FINE
    # (educational anchor for future maintainers).  What's banned is
    # a concrete reintroduction of QMovie as an animation primitive.
    assert "from PySide6.QtGui import QMovie" not in _ICONS_SRC, (
        "icons.py must NOT import QMovie — the AI-9-blocker rationale "
        "that deferred the spinner originally was QMovie.updated racing "
        "the GUI thread; qta.Spin's QTimer is the safer paint-path-only "
        "alternative now in use."
    )
    assert "QMovie(" not in _ICONS_SRC, (
        "icons.py must NOT instantiate QMovie() — see import guard above "
        "for the AI-9 rationale.  qta.Spin is the canonical alternative."
    )


# ---------------------------------------------------------------------------
# 3. Spinner starts hidden
# ---------------------------------------------------------------------------


def test_app_render_busy_spinner_starts_hidden() -> None:
    """The spinner must start hidden — call ``setVisible(False)`` at
    construction so it only appears during active compute, not on launch.
    The first occurrence of ``_render_busy_spinner.setVisible(`` in the
    source must be ``setVisible(False)`` (initial state) — followed
    later by a ``setVisible(True)`` for the compute-start trigger.
    """
    hidden_pos = _APP_SRC.find("self._render_busy_spinner.setVisible(False)")
    shown_pos = _APP_SRC.find("self._render_busy_spinner.setVisible(True)")
    assert hidden_pos != -1, (
        "app.py must call self._render_busy_spinner.setVisible(False) "
        "during __init__ so the spinner is hidden at launch."
    )
    assert shown_pos != -1, (
        "app.py must call self._render_busy_spinner.setVisible(True) "
        "when mesh generation begins."
    )
    assert hidden_pos < shown_pos, (
        "The initial setVisible(False) (at construction) must appear "
        "before the first setVisible(True) (at _computing = True) in "
        "the source — guards against constructing the spinner visible "
        "and then flipping it off at the first compute."
    )


# ---------------------------------------------------------------------------
# 4. Spinner shown when computing starts (adjacent to self._computing = True)
# ---------------------------------------------------------------------------


def test_app_render_busy_spinner_shown_on_computing_true() -> None:
    """The spinner's ``setVisible(True)`` call must be adjacent (within
    the same code block) to the ``self._computing = True`` assignment
    in ``_render_current`` — anchors the show-on-dispatch invariant.
    """
    computing_true_pos = _APP_SRC.find("self._computing = True")
    spinner_show_pos = _APP_SRC.find(
        "self._render_busy_spinner.setVisible(True)"
    )
    assert computing_true_pos != -1, (
        "app.py must contain the self._computing = True dispatch sentinel."
    )
    assert spinner_show_pos != -1, (
        "app.py must contain self._render_busy_spinner.setVisible(True)."
    )
    # Within 500 chars (~8 lines of 60-char source) of each other —
    # tight enough to catch reordering into different blocks, loose
    # enough to allow a multi-line explanatory inline comment between
    # the two calls.
    assert abs(computing_true_pos - spinner_show_pos) < 500, (
        "self._render_busy_spinner.setVisible(True) must be adjacent to "
        "self._computing = True in _render_current — same atomic step as "
        "handing work to the worker thread."
    )


# ---------------------------------------------------------------------------
# 5. Spinner hidden when computing finishes (adjacent to self._computing = False)
# ---------------------------------------------------------------------------


def test_app_render_busy_spinner_hidden_on_computing_false() -> None:
    """The spinner's ``setVisible(False)`` call inside ``_on_mesh_ready``
    (the result slot) must be adjacent to the ``self._computing = False``
    assignment.  The two share the same finally block so the spinner is
    hidden whether the worker succeeded, raised, or was superseded.
    """
    # _on_mesh_ready contains a self._computing = False assignment in
    # its finally block.  The construction-site assignment at __init__
    # (line ~200) is a different occurrence; find the second one to
    # match the finally-block site.
    first_false = _APP_SRC.find("self._computing = False")
    finally_false = _APP_SRC.find("self._computing = False", first_false + 1)
    spinner_hide_in_finally = _APP_SRC.find(
        "self._render_busy_spinner.setVisible(False)",
        first_false + 1,  # skip the __init__-time hide
    )
    assert finally_false != -1, (
        "app.py must contain the self._computing = False finally-block "
        "reset in _on_mesh_ready."
    )
    assert spinner_hide_in_finally != -1, (
        "app.py must call self._render_busy_spinner.setVisible(False) "
        "in _on_mesh_ready's finally block."
    )
    # 500 char threshold; same reasoning as the True-site test above.
    assert abs(finally_false - spinner_hide_in_finally) < 500, (
        "self._render_busy_spinner.setVisible(False) must be adjacent to "
        "self._computing = False in _on_mesh_ready's finally — same "
        "atomic step that returns the GUI thread to the idle state."
    )


# ---------------------------------------------------------------------------
# 6. icons.py factory + constant exist; constant pins mdi6 family
# ---------------------------------------------------------------------------


def test_icons_module_has_render_busy_spinner_icon_factory() -> None:
    """``icons.py`` must export ``render_busy_spinner_icon`` (callable)
    and the module-level constant ``RENDER_BUSY_SPINNER_ICON_NAME``
    pinned to the ``mdi6.`` font family for visual coherence with the
    rest of the AVC icon set.
    """
    import icons  # safe — module-level import is not Qt-construction.

    assert hasattr(icons, "render_busy_spinner_icon"), (
        "icons.py must export render_busy_spinner_icon() factory."
    )
    assert callable(icons.render_busy_spinner_icon), (
        "icons.render_busy_spinner_icon must be callable."
    )
    assert hasattr(icons, "RENDER_BUSY_SPINNER_ICON_NAME"), (
        "icons.py must export RENDER_BUSY_SPINNER_ICON_NAME module constant."
    )
    assert icons.RENDER_BUSY_SPINNER_ICON_NAME.startswith("mdi6."), (
        f"RENDER_BUSY_SPINNER_ICON_NAME={icons.RENDER_BUSY_SPINNER_ICON_NAME!r} "
        "must pin the mdi6.* font family — mixing in fa5s.* or fa6s.* would "
        "add a second cold-boot font-load cost on first icon construction."
    )


# ---------------------------------------------------------------------------
# 7. Factory docstring carries AI-9 audit anchor
# ---------------------------------------------------------------------------


def test_render_busy_spinner_icon_docstring_carries_ai9_audit_anchor() -> None:
    """The ``render_busy_spinner_icon`` docstring must contain an
    explicit ``AI-9`` reference AND the word ``paint`` — anchors the
    future-maintainer understanding that ``qta.Spin``'s ``QTimer`` is a
    pure paint-path construct (``timer.timeout`` → ``widget.update()`` →
    ``paintEvent``) that cannot re-enter ``_render_current``.  Without
    this anchor a future re-introduction of the original §9 blocker
    rationale is more likely.
    """
    import icons

    doc = icons.render_busy_spinner_icon.__doc__ or ""
    assert "AI-9" in doc, (
        "render_busy_spinner_icon docstring must explicitly cite AI-9 — "
        "documents why the original §9 spinner deferral is now obsolete."
    )
    assert "paint" in doc.lower(), (
        "render_busy_spinner_icon docstring must mention the paint path — "
        "qta.Spin's QTimer fires widget.update() → paintEvent, a pure "
        "paint-only construct that cannot re-enter business logic."
    )
