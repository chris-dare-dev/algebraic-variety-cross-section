"""Centralized style constants for Algebraic Variety Viewer.

All inline font/color stylesheets in the UI modules should reference these
constants instead of hard-coding values so that the visual identity stays
coherent across panels.

Usage example::

    from styles import HEADING_STYLE, MUTED_TEXT_STYLE, VALUE_MONO_STYLE
    my_label.setStyleSheet(HEADING_STYLE)

The constants are plain Qt stylesheet strings so they can be passed directly
to ``QWidget.setStyleSheet()``.
"""

# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------

# High-contrast muted text — replaces the former #888 / #888888 (WCAG AA fail)
# #5a5a5a on #f0f0f0 ≈ 5.4:1 contrast ratio (WCAG AA pass for small text)
COLOR_MUTED = "#5a5a5a"

# Stronger muted color for value readouts — clearly readable, not competing
# with primary labels
COLOR_VALUE = "#333333"

# Dock/panel header background — subtle tint so headers are visually distinct
COLOR_DOCK_HEADER_BG = "#e8edf2"
COLOR_DOCK_HEADER_BORDER = "#c5cdd8"

# Accent for secondary / destructive buttons so they read differently from
# primary action buttons
COLOR_RESET_BTN_BG = "#f5e8e8"
COLOR_RESET_BTN_BORDER = "#d4b4b4"
COLOR_RESET_BTN_HOVER_BG = "#f0d0d0"

# ---------------------------------------------------------------------------
# Typography — stylesheet fragments
# ---------------------------------------------------------------------------

# Panel section heading (group box alternative or explicit heading label)
HEADING_STYLE = "font-weight: bold; font-size: 13px; padding: 2px 0;"

# Normal label — used for slider names, checkbox labels, etc.
LABEL_STYLE = "font-size: 12px;"

# Small descriptive / help text under sliders and beside inputs
SMALL_LABEL_STYLE = "font-size: 11px;"

# Muted small text — descriptions, hints — WCAG AA-compliant contrast
MUTED_TEXT_STYLE = f"color: {COLOR_MUTED}; font-size: 10px;"

# Monospace value readout — slider current value, parameter value
VALUE_MONO_STYLE = f"font-family: monospace; font-size: 11px; color: {COLOR_VALUE};"

# Monospace min/max range labels flanking a slider
RANGE_LABEL_STYLE = f"font-family: monospace; font-size: 9px; color: {COLOR_MUTED};"

# ---------------------------------------------------------------------------
# Application-level QSS stylesheet
# ---------------------------------------------------------------------------

# Applied via QApplication.setStyleSheet() in main() so it cascades to all
# widgets automatically.  Provides:
#   • Modern dock widget title bar styling
#   • Group box title font boost
#   • Keyboard-focus highlight that's visible but not garish
#   • Reset button variant (.reset-btn object name)
APP_STYLESHEET = f"""
/* --- Dock widget title bars ------------------------------------------ */
QDockWidget {{
    font-size: 12px;
}}
QDockWidget::title {{
    background: {COLOR_DOCK_HEADER_BG};
    border-bottom: 1px solid {COLOR_DOCK_HEADER_BORDER};
    padding: 4px 8px;
    font-weight: bold;
    font-size: 12px;
    text-align: left;
}}

/* --- Group boxes ------------------------------------------------------- */
QGroupBox {{
    font-size: 11px;
    font-weight: bold;
    margin-top: 8px;
    padding-top: 4px;
    border: 1px solid #d0d0d0;
    border-radius: 4px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 4px;
    left: 8px;
}}

/* --- Push buttons —— default style ------------------------------------ */
QPushButton {{
    padding: 3px 8px;
    border-radius: 3px;
}}

/* --- Reset-to-defaults button — visually distinct from primary actions  */
QPushButton#resetDefaultsBtn {{
    background-color: {COLOR_RESET_BTN_BG};
    border: 1px solid {COLOR_RESET_BTN_BORDER};
    color: #5a3a3a;
}}
QPushButton#resetDefaultsBtn:hover {{
    background-color: {COLOR_RESET_BTN_HOVER_BG};
}}
QPushButton#resetDefaultsBtn:disabled {{
    background-color: #f5f5f5;
    border: 1px solid #d8d8d8;
    color: #aaaaaa;
}}

/* --- Reset Camera button — outlined, different from view-preset grid -- */
QPushButton#resetCameraBtn {{
    border: 1px solid #b0bec5;
    background: transparent;
}}
QPushButton#resetCameraBtn:hover {{
    background: #e8f0f5;
}}

/* --- Keyboard focus ring — visible on all interactive widgets ---------- */
QAbstractButton:focus, QComboBox:focus, QSlider:focus {{
    outline: 2px solid #5b9bd5;
    outline-offset: 1px;
}}

/* --- Status bar -------------------------------------------------------- */
QStatusBar {{
    font-size: 11px;
    color: {COLOR_MUTED};
}}
"""
