"""tests/test_panels_shims.py — regression-guard for panels/ subpackage shim integrity.

Verifies that each deprecated root-level panel module shim:
  1. Still allows importing the panel class via the old path.
  2. Emits a DeprecationWarning pointing at the new panels.* path.

AI-2 compliant: import-only tests, no class construction, no QApplication needed.

Restructure: restructure-full-audit-2026q2-r1 batch 4
Shim added: 2026-05-23 (move SHA: ffd358a / 8c555f7 / 2f7b4bf / 7202c89)
Removal milestone: M+1 (next /repository-architect run).
"""

import importlib
import sys
import warnings


def _reload_shim(module_name: str) -> None:
    """Remove cached module so catch_warnings gets a fresh import."""
    sys.modules.pop(module_name, None)


def test_appearance_panel_shim_emits_deprecation() -> None:
    """Importing AppearancePanel via old appearance_panel path emits DeprecationWarning
    that mentions the new canonical path panels.appearance.
    """
    _reload_shim("appearance_panel")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        from appearance_panel import AppearancePanel  # noqa: F401
    assert any(
        issubclass(w.category, DeprecationWarning)
        and "panels.appearance" in str(w.message)
        for w in caught
    ), (
        "Expected DeprecationWarning mentioning 'panels.appearance' when importing "
        "AppearancePanel from old path appearance_panel; got: "
        + str([str(w.message) for w in caught])
    )


def test_view_panel_shim_emits_deprecation() -> None:
    """Importing ViewPanel via old view_panel path emits DeprecationWarning
    that mentions the new canonical path panels.view.
    """
    _reload_shim("view_panel")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        from view_panel import ViewPanel  # noqa: F401
    assert any(
        issubclass(w.category, DeprecationWarning)
        and "panels.view" in str(w.message)
        for w in caught
    ), (
        "Expected DeprecationWarning mentioning 'panels.view' when importing "
        "ViewPanel from old path view_panel; got: "
        + str([str(w.message) for w in caught])
    )


def test_parameters_panel_shim_emits_deprecation() -> None:
    """Importing ParametersPanel via old parameters_panel path emits DeprecationWarning
    that mentions the new canonical path panels.parameters.
    """
    _reload_shim("parameters_panel")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        from parameters_panel import ParametersPanel  # noqa: F401
    assert any(
        issubclass(w.category, DeprecationWarning)
        and "panels.parameters" in str(w.message)
        for w in caught
    ), (
        "Expected DeprecationWarning mentioning 'panels.parameters' when importing "
        "ParametersPanel from old path parameters_panel; got: "
        + str([str(w.message) for w in caught])
    )


def test_parameter_grid_panel_shim_emits_deprecation() -> None:
    """Importing ParameterGridPanel via old parameter_grid_panel path emits
    DeprecationWarning that mentions the new canonical path panels.parameter_grid_panel.
    """
    _reload_shim("parameter_grid_panel")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        from parameter_grid_panel import ParameterGridPanel  # noqa: F401
    assert any(
        issubclass(w.category, DeprecationWarning)
        and "panels.parameter_grid_panel" in str(w.message)
        for w in caught
    ), (
        "Expected DeprecationWarning mentioning 'panels.parameter_grid_panel' when "
        "importing ParameterGridPanel from old path parameter_grid_panel; got: "
        + str([str(w.message) for w in caught])
    )
