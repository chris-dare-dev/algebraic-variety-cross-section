"""Centralized style constants for Algebraic Variety Viewer.

All inline font/color stylesheets in the UI modules should reference these
constants instead of hard-coding values so that the visual identity stays
coherent across panels.

Usage example::

    from styles import HEADING_STYLE, MUTED_TEXT_STYLE, VALUE_MONO_STYLE
    my_label.setStyleSheet(HEADING_STYLE)

    # Or import named tokens directly for use outside QSS:
    from styles import BG_VIEWPORT, BG_SURFACE_DEFAULT, BORDER_SWATCH

The constants are plain Qt stylesheet strings so they can be passed directly
to ``QWidget.setStyleSheet()``.

Palette structure (UPL-1, panel-refresh-2026q2-e2):
    PALETTE_LIGHT       — single source of truth for every hex color in the
                          light theme.  Downstream UPL-4 (dark mode) will
                          add a parallel PALETTE_DARK with identical keys.
    VARIETY_DEFAULT_COLOR — empty stub; UPL-5 will populate with per-variety
                          default surface colors keyed by variety family name.
    COLOR_*, BG_*, etc. — named exports computed from PALETTE_LIGHT.  Kept
                          for backward-compat (zero call-site changes) and
                          for cases where importing the named constant is
                          clearer than dict subscript at the call site.
"""

# ---------------------------------------------------------------------------
# Palette — single source of truth for all hex colors (UPL-1)
# ---------------------------------------------------------------------------
#
# All hex values are 6-digit (AI-13 requirement for any value that flows
# into PyVista; convention extended to QSS for consistency).  WCAG AA
# contrast ratios are documented per-token where the value is text or text
# adjacent.  PyVista-bound tokens (BG_VIEWPORT, BG_SURFACE_DEFAULT,
# COLOR_WIREFRAME_OVERLAY) are annotated explicitly.
#
# UPL-4 (dark mode) will add a parallel PALETTE_DARK dict with identical
# keys; the application stylesheet will then swap source dicts.  Tokens
# that are intentionally light-palette-only (e.g. TEXT_MUTED's #5a5a5a
# fails 4.5:1 on a dark panel ground; UPL-4 must provide TEXT_MUTED_DARK)
# carry a comment marker.
#
# UPL-5 (per-variety surface color) will populate VARIETY_DEFAULT_COLOR
# from this same module.

PALETTE_LIGHT: dict[str, str] = {
    # === Core viewport + panel backgrounds ===
    "BG_VIEWPORT":              "#2f2f2f",   # dark grey VTK viewport — flows into PyVista
    "BG_PANEL":                 "#f0f0f0",   # default Qt light-panel ground (anchor for WCAG ratios)
    "BG_SURFACE_DEFAULT":       "#b0c4de",   # lightsteelblue default mesh color — flows into PyVista

    # === Text / foreground ===
    "TEXT_VALUE":               "#333333",   # value readout mono text (~9.1:1 on BG_PANEL — AA pass)
    "TEXT_MUTED":               "#5a5a5a",   # muted text / labels (~5.4:1 on BG_PANEL — AA pass)
                                             # NOTE: light-palette only.  UPL-4 must add TEXT_MUTED_DARK.
    "TEXT_DISABLED":            "#aaaaaa",   # disabled widget text (intentional low contrast per WCAG exception)
    "TEXT_RESET_BTN":           "#5a3a3a",   # dark reddish on reset-btn pink bg (~6.1:1 — AA pass)

    # === Focus ===
    "FOCUS_RING":               "#5b9bd5",   # keyboard focus outline (>=3:1 vs adjacent widget bg)

    # === Dock + group-box structure ===
    "BG_DOCK_HEADER":           "#e8edf2",   # dock title bar background
    "BORDER_DOCK_HEADER":       "#c5cdd8",   # dock title bar bottom border
    "BORDER_GROUP_BOX":         "#d0d0d0",   # QGroupBox outline

    # === Color swatches in Appearance panel ===
    "BORDER_SWATCH":            "#888888",   # swatch outline — 6-digit (resolves AI-13 adjacency, UPL-21)

    # === Reset-defaults button (destructive variant) ===
    "BG_RESET_BTN":             "#f5e8e8",
    "BORDER_RESET_BTN":         "#d4b4b4",
    "BG_RESET_BTN_HOVER":       "#f0d0d0",
    "BG_RESET_BTN_DISABLED":    "#f5f5f5",
    "BORDER_RESET_BTN_DISABLED":"#d8d8d8",

    # === Reset-camera button (outlined variant) ===
    "BORDER_CAMERA_BTN":        "#b0bec5",
    "BG_CAMERA_BTN_HOVER":      "#e8f0f5",

    # === Domain-clip wireframe overlay (flows into PyVista add_mesh) ===
    "COLOR_WIREFRAME_OVERLAY":  "#888888",
}


# Per-variety default surface color — populated by UPL-5 (panel-refresh-2026q2-e3).
# Keys are variety family names matching VARIETIES dict in surfaces.py
# (e.g. "K3 surface", "Enriques surface", "Calabi-Yau 3-fold", "Fano 3-fold (rho=1)").
# Each value MUST be 6-digit hex (AI-13) and SHOULD clear >=3:1 luminance contrast
# against PALETTE_LIGHT["BG_VIEWPORT"] for surface legibility.
VARIETY_DEFAULT_COLOR: dict[str, str] = {}


# UPL-4 placeholder marker: PALETTE_DARK will live here as a parallel dict
# with identical keys.  The application stylesheet will then swap source
# dicts (or merge PALETTE_LIGHT with PALETTE_DARK_OVERRIDES).  Do NOT add
# the dark dict in UPL-1 — it ships in its own milestone with its own
# WCAG verification pass.


# ---------------------------------------------------------------------------
# Backward-compat named exports — read from PALETTE_LIGHT at import time
# ---------------------------------------------------------------------------
#
# Existing call sites in view_panel.py, parameters_panel.py, appearance_panel.py
# import these constants by name.  Keeping the names stable means the UPL-1
# refactor touches only styles.py (plus the small set of call sites that
# previously inlined hex literals — see appearance_panel.py and app.py).

COLOR_MUTED                = PALETTE_LIGHT["TEXT_MUTED"]
COLOR_VALUE                = PALETTE_LIGHT["TEXT_VALUE"]
COLOR_DOCK_HEADER_BG       = PALETTE_LIGHT["BG_DOCK_HEADER"]
COLOR_DOCK_HEADER_BORDER   = PALETTE_LIGHT["BORDER_DOCK_HEADER"]
COLOR_RESET_BTN_BG         = PALETTE_LIGHT["BG_RESET_BTN"]
COLOR_RESET_BTN_BORDER     = PALETTE_LIGHT["BORDER_RESET_BTN"]
COLOR_RESET_BTN_HOVER_BG   = PALETTE_LIGHT["BG_RESET_BTN_HOVER"]

# New named exports — for use by appearance_panel.py and app.py to replace
# previously-inlined literals.
BG_VIEWPORT                = PALETTE_LIGHT["BG_VIEWPORT"]
BG_SURFACE_DEFAULT         = PALETTE_LIGHT["BG_SURFACE_DEFAULT"]
BORDER_SWATCH              = PALETTE_LIGHT["BORDER_SWATCH"]
COLOR_WIREFRAME_OVERLAY    = PALETTE_LIGHT["COLOR_WIREFRAME_OVERLAY"]


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
#   * Modern dock widget title bar styling
#   * Group box title font boost
#   * Keyboard-focus highlight that's visible but not garish
#   * Reset button variant (#resetDefaultsBtn object name)
#
# All hex values are substituted from PALETTE_LIGHT — no raw literals here.
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
    border: 1px solid {PALETTE_LIGHT["BORDER_GROUP_BOX"]};
    border-radius: 4px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 4px;
    left: 8px;
}}

/* --- Push buttons -- default style ------------------------------------ */
QPushButton {{
    padding: 3px 8px;
    border-radius: 3px;
}}

/* --- Reset-to-defaults button -- visually distinct from primary actions */
QPushButton#resetDefaultsBtn {{
    background-color: {COLOR_RESET_BTN_BG};
    border: 1px solid {COLOR_RESET_BTN_BORDER};
    color: {PALETTE_LIGHT["TEXT_RESET_BTN"]};
}}
QPushButton#resetDefaultsBtn:hover {{
    background-color: {COLOR_RESET_BTN_HOVER_BG};
}}
QPushButton#resetDefaultsBtn:disabled {{
    background-color: {PALETTE_LIGHT["BG_RESET_BTN_DISABLED"]};
    border: 1px solid {PALETTE_LIGHT["BORDER_RESET_BTN_DISABLED"]};
    color: {PALETTE_LIGHT["TEXT_DISABLED"]};
}}

/* --- Reset Camera button -- outlined, different from view-preset grid -- */
QPushButton#resetCameraBtn {{
    border: 1px solid {PALETTE_LIGHT["BORDER_CAMERA_BTN"]};
    background: transparent;
}}
QPushButton#resetCameraBtn:hover {{
    background: {PALETTE_LIGHT["BG_CAMERA_BTN_HOVER"]};
}}

/* --- Keyboard focus ring -- visible on all interactive widgets --------- */
QAbstractButton:focus, QComboBox:focus, QSlider:focus {{
    outline: 2px solid {PALETTE_LIGHT["FOCUS_RING"]};
    outline-offset: 1px;
}}

/* --- Status bar -------------------------------------------------------- */
QStatusBar {{
    font-size: 11px;
    color: {COLOR_MUTED};
}}
"""
