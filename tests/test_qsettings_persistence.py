"""Regression guards for V1 session persistence.

qsettings-persistence-v1-2026q3-e1 (UPL-25 partial): lifts the
CONTEXT.md §9 "No state persistence" non-goal for V1 scope only —
window geometry, dock layout, and last-used variety + subtype.  V2/V3
(per-subtype slider values, theme preference, surface/bg colors,
camera pose, clip state) remain explicitly out-of-scope.

All tests here are pure source-text greps on ``app.py`` (AI-2 / AI-3
compliant — no ``QApplication`` construction, no ``MainWindow()``
construction, no live ``QSettings()`` write to the test runner's
registry/plist/INI store).
"""
from __future__ import annotations

import pathlib


_APP_SRC = (
    pathlib.Path(__file__).resolve().parent.parent / "app.py"
).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 1. QSettings imported
# ---------------------------------------------------------------------------


def test_app_imports_qsettings() -> None:
    """``app.py`` must import ``QSettings`` from ``PySide6.QtCore``.
    Guards against a future refactor silently dropping the import.
    """
    # Match the literal "QSettings" inside an import statement.  The
    # canonical form is "from PySide6.QtCore import ..., QSettings, ...".
    assert "QSettings" in _APP_SRC, (
        "app.py must import QSettings — qsettings-persistence-v1-2026q3-e1 "
        "depends on it for both save and restore."
    )
    # And the import must be inside a from-PySide6.QtCore line (not just
    # mentioned in a comment / docstring).
    import_lines = [
        line for line in _APP_SRC.splitlines()
        if "from PySide6.QtCore import" in line
    ]
    assert any("QSettings" in line for line in import_lines), (
        "QSettings must be imported from PySide6.QtCore — verify the "
        "import line still includes it."
    )


# ---------------------------------------------------------------------------
# 2. Org + app name set in main() so QSettings() no-arg form works
# ---------------------------------------------------------------------------


def test_app_sets_org_and_app_name_in_main() -> None:
    """The org + application name MUST be set in ``main()`` BEFORE the
    QApplication construction so every subsequent ``QSettings()`` no-arg
    constructor inherits them as scope identifiers.  Locking the exact
    string literals prevents a silent rename from creating a second
    parallel settings store and orphaning the user's V1 state.
    """
    assert 'QApplication.setOrganizationName("AVC")' in _APP_SRC, (
        "main() must call QApplication.setOrganizationName(\"AVC\") "
        "BEFORE app = QApplication(sys.argv)."
    )
    assert (
        'QApplication.setApplicationName("AlgebraicVarietyCrossSection")'
        in _APP_SRC
    ), (
        "main() must call QApplication.setApplicationName(\"AlgebraicVariety"
        "CrossSection\") BEFORE app = QApplication(sys.argv)."
    )


# ---------------------------------------------------------------------------
# 3. Window geometry save + restore present
# ---------------------------------------------------------------------------


def test_app_persists_window_geometry() -> None:
    """``saveGeometry()`` (in ``_save_settings``) and ``restoreGeometry(``
    (in ``_restore_settings``) must both appear in ``app.py``.
    """
    assert "saveGeometry()" in _APP_SRC, (
        "app.py must call self.saveGeometry() to persist window geometry."
    )
    assert "restoreGeometry(" in _APP_SRC, (
        "app.py must call self.restoreGeometry(...) to restore window "
        "geometry on launch."
    )


# ---------------------------------------------------------------------------
# 4. Window state (dock layout) save + restore present
# ---------------------------------------------------------------------------


def test_app_persists_window_state() -> None:
    """``saveState()`` and ``restoreState(`` must both appear — these
    persist the dock layout (which docks are visible, their docked /
    floating state, their sizes).  Without them the geometry is restored
    but every dock returns to its default position on every launch.
    """
    assert "saveState()" in _APP_SRC, (
        "app.py must call self.saveState() to persist dock layout."
    )
    assert "restoreState(" in _APP_SRC, (
        "app.py must call self.restoreState(...) to restore dock layout "
        "on launch.  Must be called AFTER all addDockWidget calls in "
        "__init__ (Qt restoreState contract — see CONTEXT.md §4.5)."
    )


# ---------------------------------------------------------------------------
# 5. LastSession/variety + LastSession/subtype keys present
# ---------------------------------------------------------------------------


def test_app_persists_last_session_variety_and_subtype() -> None:
    """The exact key-name strings ``"LastSession/variety"`` and
    ``"LastSession/subtype"`` must appear.  Locking the literals
    prevents a silent key rename from orphaning saved state across
    versions — a user with a saved V1 state would silently lose their
    last variety/subtype if a future refactor renamed the keys.
    """
    assert '"LastSession/variety"' in _APP_SRC, (
        "app.py must use the exact key \"LastSession/variety\" — see "
        "CONTEXT.md §4.5 for the canonical key schema."
    )
    assert '"LastSession/subtype"' in _APP_SRC, (
        "app.py must use the exact key \"LastSession/subtype\" — see "
        "CONTEXT.md §4.5 for the canonical key schema."
    )


# ---------------------------------------------------------------------------
# 6. Window/schema_version key present (forward-compat for V2)
# ---------------------------------------------------------------------------


def test_app_settings_schema_version_key_present() -> None:
    """The ``"Window/schema_version"`` key MUST be persisted (currently
    ``= 1``) so a future V2 / V3 milestone can detect older-version
    saved state and migrate / ignore it.  Without this anchor, V2 must
    either blindly clear the store on first launch or risk applying a
    V1 state blob to V2-shape keys.  Cheap (1 extra setValue per save).
    """
    assert '"Window/schema_version"' in _APP_SRC, (
        "app.py must persist the \"Window/schema_version\" key — "
        "forward-compat anchor for V2 migration."
    )


# ---------------------------------------------------------------------------
# 7. closeEvent calls _save_settings BEFORE thread-pool drain
# ---------------------------------------------------------------------------


def test_app_save_called_in_close_event() -> None:
    """``_save_settings()`` MUST be called inside ``closeEvent`` AND
    must appear BEFORE the ``_render_pool.waitForDone(...)`` call — the
    drain can block up to 30 s and the save must complete while the GUI
    is still live (``saveGeometry`` reads the current window state).
    """
    close_event_pos = _APP_SRC.find("def closeEvent(")
    assert close_event_pos != -1, "app.py must define closeEvent."

    # The next def after closeEvent bounds its body.
    next_def_pos = _APP_SRC.find("\n    def ", close_event_pos + 1)
    if next_def_pos == -1:
        # closeEvent is the last method on the class; use the next
        # top-level def (which is `def main`).
        next_def_pos = _APP_SRC.find("\ndef ", close_event_pos + 1)
    body = _APP_SRC[close_event_pos:next_def_pos]

    assert "self._save_settings()" in body, (
        "closeEvent must call self._save_settings() — the V1 persist "
        "trigger for window geometry + dock layout."
    )
    # Save must come BEFORE the thread-pool drain (which can block).
    save_pos = body.find("self._save_settings()")
    drain_pos = body.find("self._render_pool.waitForDone")
    assert save_pos != -1 and drain_pos != -1, (
        "closeEvent must contain both _save_settings() and "
        "_render_pool.waitForDone() calls."
    )
    assert save_pos < drain_pos, (
        "self._save_settings() must come BEFORE self._render_pool."
        "waitForDone(...) in closeEvent — saveGeometry/saveState read "
        "the live window state and waitForDone can block up to 30 s."
    )


# ---------------------------------------------------------------------------
# 8. First-launch restore is guarded
# ---------------------------------------------------------------------------


def test_app_restore_is_guarded_against_first_launch() -> None:
    """First-launch behavior (no saved state) MUST be a graceful no-op:
    ``_restore_settings`` must check the schema_version and bail out
    when it's below the current version (default 0 on a fresh launch
    with no settings file).  Without this guard, ``restoreGeometry(None)``
    is called on the QByteArray-typed default which returns silently
    false but the variety/subtype restore would crash with TypeError.
    """
    # Find _restore_settings method body.
    restore_def_pos = _APP_SRC.find("def _restore_settings(")
    assert restore_def_pos != -1, (
        "app.py must define a _restore_settings() method."
    )
    next_def_pos = _APP_SRC.find("\n    def ", restore_def_pos + 1)
    body = _APP_SRC[restore_def_pos:next_def_pos]

    # Schema-version guard MUST be the first non-comment / non-docstring
    # logical line.  Any of these forms is acceptable:
    #   if schema < self._SETTINGS_SCHEMA_VERSION:
    #   if schema < 1:
    #   if schema_version < ...
    has_schema_guard = (
        "schema < self._SETTINGS_SCHEMA_VERSION" in body
        or "schema < 1" in body
        or "_SETTINGS_SCHEMA_VERSION" in body
    )
    assert has_schema_guard, (
        "_restore_settings must guard against first-launch (no saved "
        "state) by checking schema_version < current_version and "
        "returning a no-op.  Without this, restoreGeometry(None) and "
        "variety setCurrentText(\"\") fire on a fresh install."
    )

    # The variety/subtype restore must be guarded by the in-VARIETIES check.
    assert "in VARIETIES" in body, (
        "_restore_settings must guard variety restore with "
        "`if saved_variety in VARIETIES:` — protects against a saved "
        "variety that was later removed from the registry."
    )
