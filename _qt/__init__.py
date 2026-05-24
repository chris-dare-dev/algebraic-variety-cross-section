"""Qt-framework adapter subpackage.

Per scout-B's napari-pattern recommendation: a `_qt/` subpackage groups all
Qt-coupled modules so domain-level code (varieties/, render/, cross_section/)
need not know about the GUI framework. The leading underscore signals
"framework adapter — implementation detail; external callers should not
depend on internal layout."

Per restructure-feature-subpackages-2026q2-r2 Batch 3: extracted from root.

Submodules:
    _qt.panels         — PySide6 panel widgets (4 files: appearance, view,
                         parameters, parameter_grid_panel)
    _qt.icons          — qtawesome icon factories (lazy-loaded)
    _qt.styles         — QSS palette + stylesheet renderer
    _qt.ui_helpers     — Debouncer + slider-row builder + shared widgets

Old import paths (panels, icons, styles, ui_helpers) still work via shims;
the shims emit DeprecationWarning pointing here.
"""
