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
    VARIETY_DEFAULT_COLOR — per-variety default surface colors keyed by
                          variety family name (light theme).  Populated in
                          variety-palette-2026q2-e1 (UPL-2 from the
                          2026q2-graph-and-window uplift).
    VARIETY_DEFAULT_COLOR_DARK — dark-theme parallel; identical values
                          because all four colors clear 3:1 on the dark
                          panel.  Added by dark-mode-2026q2-e1 (UPL-1).
    get_variety_default_colors(theme) — single-line accessor returning the
                          active-theme dict; lets AppearancePanel stay
                          decoupled from theme state.
    PALETTE_DARK — key-identical companion to PALETTE_LIGHT, dark-tuned
                          values, every text token re-audited against
                          BG_PANEL_DARK = #252526.
    APP_STYLESHEET / APP_STYLESHEET_DARK — both rendered via
                          _render_stylesheet(palette) at import time.
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
# PALETTE_DARK (dark-mode-2026q2-e1, closing UPL-1) lives below this dict
# with key-identical entries.  Both palettes render through the
# `_render_stylesheet(palette)` helper to produce APP_STYLESHEET (light) and
# APP_STYLESHEET_DARK (dark).
#
# Per-variety surface colors live in VARIETY_DEFAULT_COLOR (light, populated
# by variety-palette-2026q2-e1) and VARIETY_DEFAULT_COLOR_DARK (dark, added
# by dark-mode-2026q2-e1 — reuses the light values verbatim because all four
# clear 3:1 on BG_PANEL_DARK).  See `get_variety_default_colors(theme)` for
# the theme-aware accessor.

PALETTE_LIGHT: dict[str, str] = {
    # === Core viewport + panel backgrounds ===
    "BG_VIEWPORT":              "#2f2f2f",   # dark grey VTK viewport — flows into PyVista
    "BG_PANEL":                 "#f0f0f0",   # Qt platform default light-panel ground — NOT set explicitly by the app;
                                             # update if a future Qt platform skin changes this default.  Used as
                                             # the WCAG contrast anchor in the palette annotations + test suite.
    "BG_SURFACE_DEFAULT":       "#b0c4de",   # lightsteelblue default mesh color — flows into PyVista

    # === Text / foreground ===
    # Contrast ratios verified against BG_PANEL via tests/test_styles_palette.py
    # using the WCAG 2.x relative-luminance formula (live, not approximate).
    "TEXT_VALUE":               "#333333",   # value readout mono text (11.09:1 on BG_PANEL — AA pass)
    "TEXT_MUTED":               "#5a5a5a",   # muted text / labels (6.05:1 on BG_PANEL — AA pass)
                                             # NOTE: light-palette only.  Measured 1.94:1 on BG_VIEWPORT
                                             # (dark), so UPL-4 MUST add TEXT_MUTED_DARK.
    "TEXT_DISABLED":            "#aaaaaa",   # disabled widget text (intentional low contrast per WCAG exception)
    "TEXT_RESET_BTN":           "#5a3a3a",   # dark reddish on reset-btn pink bg (8.37:1 on BG_RESET_BTN — AA pass)

    # === Focus ===
    # WCAG 2.1 §1.4.11 non-text contrast — focus indicators require >=3:1
    # against the adjacent background.  Fixed in focus-ring-contrast-2026q2-e1
    # (UPL-4): darkened from #5b9bd5 (2.60:1 on BG_PANEL — FAIL, below the
    # 3:1 floor) to #3c82c4 (3.56:1 — PASS).  Closes the deferred M4 finding
    # from panel-refresh-2026q2-e2 (variety-palette / UPL-1).  Per-theme
    # value: PALETTE_DARK keeps the prior #5b9bd5 (5.17:1 dark) — that value
    # already PASSED on dark, the failure was light-only, so no need to
    # compromise dark headroom.  Narrow light margin (0.556 absolute above
    # 3:1 floor) — do not lighten further; aligns with macOS Sequoia
    # #007aff (3.53:1) and GNOME Adwaita #3584e4 (3.31:1) which sit in the
    # same narrow-pass band.  Future regressions guarded by
    # test_light_non_text_focus_ring_meets_wcag_aa_on_bg_panel.
    "FOCUS_RING":               "#3c82c4",   # keyboard focus outline (3.56:1 on BG_PANEL — PASS, narrow margin; do not lighten further)

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

    # === Display-toggle checkable button (Wireframe / Show-edges) ===
    # display-toggles-checkable-button-2026q3-e1 (F-M2 closure): fill tint
    # for the :checked pseudo-state of QPushButton[role="display-toggle"].
    # The WCAG 1.4.11 indicator is the 2px FOCUS_RING border (3.56:1 vs
    # BG_PANEL on light, 5.17:1 on dark — already proven elsewhere).  This
    # fill is decorative reinforcement only; its contrast vs the hover
    # tint is ~1.10:1 by design (state communicated by border, not fill).
    # Text on this fill clears 4.5:1: TEXT_VALUE #333333 vs #d4e6f5 = 9.89:1.
    "BG_TOGGLE_CHECKED":        "#d4e6f5",   # light blue fill — decorative

    # === Domain-clip wireframe overlay (flows into PyVista add_mesh) ===
    "COLOR_WIREFRAME_OVERLAY":  "#888888",

    # === Parameter-grid mode (QGraphicsScene — Qt-only, not PyVista) ===
    # The grid panel draws gridlines, a draggable dot, axis labels and (for
    # the 3D isometric box) a wireframe cube inside a QGraphicsScene.  These
    # are Qt stylesheet / QPen / QBrush colors, never passed to PyVista.
    "BG_GRID_SCENE":            "#fbfbfb",   # grid drawing-surface background
    "GRID_LINE":                "#d0d0d0",   # minor gridline pen
    "GRID_AXIS_LINE":           "#9aa3ad",   # bounding axis-frame pen (stronger)
    "GRID_DOT_FILL":            "#3c6da8",   # draggable dot fill
    "GRID_DOT_BORDER":          "#1f3d5c",   # draggable dot outline
    "GRID_AXIS_LABEL":          "#4a4a4a",   # axis-name text (8.6:1 on BG_GRID_SCENE — AA pass)
    "GRID_BOX_WIRE":            "#7d8893",   # 3D isometric box wireframe pen
}


# Per-variety default surface color — populated by variety-palette-2026q2-e1
# (the UPL-2 milestone in the 2026q2-graph-and-window uplift).
#
# Keys MUST match the VARIETIES dict in surfaces.py VERBATIM, including the
# non-ASCII characters.  The actual keys use Unicode U+2013 (en-dash) in
# "Calabi–Yau 3-fold" — NOT an ASCII hyphen — and U+03C1 (Greek small rho)
# in "Fano 3-fold (ρ=1)".  Copy-paste from surfaces.py:946,950,968,986 rather
# than retyping; a mismatched key silently misses the lookup and falls back
# to BG_SURFACE_DEFAULT.  The `test_variety_default_color_keys_match_surfaces_varieties`
# test in tests/test_styles_palette.py guards against this drift.
#
# Each value MUST be 6-digit hex (AI-13) and MUST clear >=4.5:1 luminance
# contrast against PALETTE_LIGHT["BG_VIEWPORT"] (AI-12; the surface fills
# enough of the dark canvas to function as text-level contrast for the
# variety-family identity cue, not just non-text decoration).
#
# All four values below were numerically verified against #2f2f2f:
#   K3        #8e9ed4  5.09:1  (cool periwinkle — mathematical / classical)
#   Enriques  #c4a882  5.91:1  (warm ochre — classical-geometry register)
#   CY3       #85b5d0  6.07:1  (teal-cobalt — Elegant Universe / Hanson)
#   Fano      #8fbe85  6.29:1  (sage green — distinct from the three blues)
# Hue separations are >=24° pairwise (K3-CY3 is the tightest pair at
# ~24.7°, perceptually distinct under mild color-vision deficiency due
# to saturation difference: K3 0.33 vs CY3 0.36).  All other pairs
# comfortably exceed 25°.
VARIETY_DEFAULT_COLOR: dict[str, str] = {
    "K3 surface":          "#8e9ed4",
    "Enriques surface":    "#c4a882",
    "Calabi–Yau 3-fold":   "#85b5d0",   # U+2013 en-dash in key
    "Fano 3-fold (ρ=1)":   "#8fbe85",   # U+03C1 rho in key
}

# Dark-mode variety colors — added by dark-mode-2026q2-e1 (UPL-1).
#
# The four light-mode values clear BOTH thresholds against the dark panel
# background (BG_PANEL_DARK = #252526):
#   K3        #8e9ed4   5.83:1 vs BG_PANEL_DARK (swatch chip 3:1 PASS)
#   Enriques  #c4a882   6.76:1
#   CY3       #85b5d0   6.94:1
#   Fano      #8fbe85   7.20:1
# All four already clear 5+:1 against BG_VIEWPORT (the shared canvas).  Reuse
# the light values verbatim — this closes the deferred MF1 finding from
# variety-palette-2026q2-e1 (swatch-chip contrast was 1.87-2.31:1 on the
# light panel; in dark mode the same colors hit 5.83-7.20:1 on the dark
# panel, comfortably above the WCAG 1.4.11 non-text 3:1 threshold).
VARIETY_DEFAULT_COLOR_DARK: dict[str, str] = dict(VARIETY_DEFAULT_COLOR)


def get_variety_default_colors(theme: str = "dark") -> dict[str, str]:
    """Return the active-theme per-variety surface-color dict.

    Single source of truth for theme-aware variety color resolution.  Callers
    (currently ``MainWindow._on_variety_changed`` and ``_on_subtype_changed``)
    pass the active theme name; this accessor returns the matching dict.
    AppearancePanel stays decoupled from theme state — it receives the
    resolved hex string from ``set_default_color(hex_str)`` and never knows
    which theme produced it.

    Unknown theme names fall through to the dark dict (the launch default).
    """
    return VARIETY_DEFAULT_COLOR if theme == "light" else VARIETY_DEFAULT_COLOR_DARK


# ---------------------------------------------------------------------------
# PALETTE_DARK — dark-mode-2026q2-e1 (UPL-1)
# ---------------------------------------------------------------------------
#
# Key-identical companion to PALETTE_LIGHT.  Every token has a dark-tuned
# value verified against BG_PANEL_DARK = #252526 (VS Code sidebar register
# — dark but not pitch-black, leaving headroom for the dock header to
# differentiate at #313132).
#
# Tokens shared between themes (intentionally identical):
#   BG_VIEWPORT         #2f2f2f   canvas is always dark
#   BG_SURFACE_DEFAULT  #b0c4de   flows to PyVista; reads on either background
#   BORDER_SWATCH       #888888   neutral grey reads on either panel
#   COLOR_WIREFRAME_OVERLAY #888888  same — 4.32:1 vs #252526 PASS
#
# Every text token re-audited vs BG_PANEL_DARK at the 4.5:1 floor; every
# non-text UI border re-audited at 3:1.  The dock header's structural
# contrast (1.18:1 vs panel) mirrors the light-mode pattern (1.03:1 vs
# panel) — the BORDER_DOCK_HEADER separator line at 3.05:1 provides the
# WCAG 1.4.11-compliant boundary.  TEXT_DISABLED at 2.87:1 is intentionally
# below 4.5:1 per WCAG §1.4.3 disabled-state exception.
PALETTE_DARK: dict[str, str] = {
    # === Core viewport + panel backgrounds ===
    "BG_VIEWPORT":              "#2f2f2f",   # SHARED — VTK canvas always dark
    "BG_PANEL":                 "#252526",   # dark panel anchor (VS Code sidebar register)
    "BG_SURFACE_DEFAULT":       "#b0c4de",   # SHARED — flows into PyVista

    # === Text / foreground (4.5:1 floor vs BG_PANEL = #252526) ===
    "TEXT_VALUE":               "#e0e0e0",   # 11.60:1 — was #333333 (light); inverted to near-white
    "TEXT_MUTED":                "#a0a0a0",   # 5.86:1  — was #5a5a5a (light, 1.94:1 on dark — known fail)
    "TEXT_DISABLED":             "#6b6b6b",   # 2.87:1  — intentional low contrast (WCAG §1.4.3 exception)
    "TEXT_RESET_BTN":            "#ffc0c0",   # 9.32:1 vs BG_RESET_BTN dark — light pink on dark wine

    # === Focus ring (3:1 floor vs BG_PANEL for non-text UI) ===
    # FOCUS_RING #5b9bd5 measures 5.17:1 vs #252526 (PASS).  Per-theme by
    # design: PALETTE_LIGHT uses a darker #3c82c4 (3.56:1 on #f0f0f0) to
    # clear the same 3:1 floor on the light panel, but the original
    # #5b9bd5 already PASSED on dark — keeping it here preserves the
    # 5.17:1 dark headroom (72% above floor) rather than collapsing to
    # 3.78:1 (26% above floor) for shared-value uniformity.  The
    # "key-identical palettes" pattern (dark-mode-2026q2-e1) means same
    # KEYS across PALETTE_LIGHT/PALETTE_DARK, values may differ where
    # contrast demands it — same rationale as TEXT_VALUE, TEXT_MUTED,
    # BORDER_GROUP_BOX, etc. (all theme-divergent for contrast).
    "FOCUS_RING":                "#5b9bd5",   # 5.17:1 vs BG_PANEL_DARK — PASS for non-text 3:1 (dark headroom preserved)

    # === Dock + group-box structure ===
    # BG_DOCK_HEADER is structural (1.18:1 vs panel); the BORDER_DOCK_HEADER
    # at 3.05:1 carries the WCAG 1.4.11 boundary contrast.  Same pattern as
    # light mode (#e8edf2 on #f0f0f0 is 1.03:1).
    "BG_DOCK_HEADER":            "#313132",   # structural; close-to-panel
    "BORDER_DOCK_HEADER":        "#6f6f6f",   # 3.05:1 vs BG_PANEL — separator line
    "BORDER_GROUP_BOX":          "#777777",   # 3.42:1 vs BG_PANEL — non-text 3:1 PASS

    # === Color swatches in Appearance panel ===
    "BORDER_SWATCH":             "#888888",   # SHARED — 6-digit, reads on either ground

    # === Reset-defaults button (destructive variant) — dark-wine on dark ===
    "BG_RESET_BTN":              "#4a1a1a",   # structural dark wine
    "BORDER_RESET_BTN":          "#c05050",   # 3.28:1 vs BG_PANEL — component boundary
    "BG_RESET_BTN_HOVER":        "#5a2020",   # structural hover state
    "BG_RESET_BTN_DISABLED":     "#333333",   # disabled state (WCAG exception)
    "BORDER_RESET_BTN_DISABLED": "#444444",   # disabled state (WCAG exception)

    # === Reset-camera button (outlined variant) ===
    "BORDER_CAMERA_BTN":         "#6a8090",   # 3.72:1 vs BG_PANEL — non-text 3:1 PASS
    "BG_CAMERA_BTN_HOVER":       "#2a3a45",   # structural hover

    # === Display-toggle checkable button (Wireframe / Show-edges) ===
    # display-toggles-checkable-button-2026q3-e1 (F-M2 closure): per-theme
    # value to match the dark panel.  WCAG indicator is the 2px FOCUS_RING
    # border (5.17:1 vs BG_PANEL_DARK — already proven).  Fill is decorative.
    # Text on this fill clears 4.5:1: TEXT_VALUE #e0e0e0 vs #1a3048 = 10.20:1.
    "BG_TOGGLE_CHECKED":         "#1a3048",   # deep navy fill — decorative

    # === Domain-clip wireframe overlay (flows into PyVista add_mesh) ===
    "COLOR_WIREFRAME_OVERLAY":   "#888888",   # SHARED — 4.32:1 vs #252526

    # === Parameter-grid mode (QGraphicsScene — Qt-only, not PyVista) ===
    # Dark-tuned companions to the PALETTE_LIGHT GRID_* tokens, kept so the
    # two palettes stay key-identical (enforced by
    # test_palette_dark_has_minimum_tokens).  NOTE: parameter_grid_panel.py
    # currently freezes these into QColor objects at module-import time, so
    # the grid scene does not yet live-swap on a theme toggle — a dark-grid
    # runtime refresh is a tracked follow-up (see
    # .claude/notes/features/parameter-grid/design.md).
    "BG_GRID_SCENE":             "#2a2a2b",   # dark grid drawing surface
    "GRID_LINE":                 "#4a4a4c",   # minor gridline on dark
    "GRID_AXIS_LINE":            "#6f7780",   # bounding axis-frame pen (stronger)
    "GRID_DOT_FILL":             "#5b9bd5",   # draggable dot fill — bright blue on dark
    "GRID_DOT_BORDER":           "#cfe4f5",   # draggable dot outline — pale rim
    "GRID_AXIS_LABEL":           "#c8c8c8",   # axis-name text on dark grid scene
    "GRID_BOX_WIRE":             "#8a929c",   # 3D isometric box wireframe pen
}


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
BG_PANEL                   = PALETTE_LIGHT["BG_PANEL"]
BG_SURFACE_DEFAULT         = PALETTE_LIGHT["BG_SURFACE_DEFAULT"]
BORDER_SWATCH              = PALETTE_LIGHT["BORDER_SWATCH"]
COLOR_WIREFRAME_OVERLAY    = PALETTE_LIGHT["COLOR_WIREFRAME_OVERLAY"]

# Parameter-grid mode tokens — consumed by parameter_grid_panel.py.
BG_GRID_SCENE              = PALETTE_LIGHT["BG_GRID_SCENE"]
GRID_LINE                  = PALETTE_LIGHT["GRID_LINE"]
GRID_AXIS_LINE             = PALETTE_LIGHT["GRID_AXIS_LINE"]
GRID_DOT_FILL              = PALETTE_LIGHT["GRID_DOT_FILL"]
GRID_DOT_BORDER            = PALETTE_LIGHT["GRID_DOT_BORDER"]
GRID_AXIS_LABEL            = PALETTE_LIGHT["GRID_AXIS_LABEL"]
GRID_BOX_WIRE              = PALETTE_LIGHT["GRID_BOX_WIRE"]


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
# DEPRECATED (dark-mode-2026q2-e1 rect H1): these inline-style constants
# hardcode PALETTE_LIGHT colors and bypass the dark QSS cascade when applied
# via widget.setStyleSheet(). New call sites MUST use the QSS role-property
# pattern instead:
#     label.setProperty("role", "muted")        # was: setStyleSheet(MUTED_TEXT_STYLE)
#     label.setProperty("role", "value-mono")   # was: setStyleSheet(VALUE_MONO_STYLE)
#     label.setProperty("role", "range-label")  # was: setStyleSheet(RANGE_LABEL_STYLE)
# The QSS role selectors in _render_stylesheet handle color + font for both
# themes automatically.  These constants remain as backward-compat exports
# only — every in-repo call site was migrated to setProperty in the same
# milestone.  Test guard: test_no_inline_color_styles_in_panel_files.
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
# dark-mode-2026q2-e1 (UPL-1) refactored this into _render_stylesheet(palette)
# so the same template renders against either PALETTE_LIGHT or PALETTE_DARK.
# Every hex reference is tokenized through palette[...] subscripts — there is
# no light-only literal in the template.  The two module-level constants
# below (APP_STYLESHEET, APP_STYLESHEET_DARK) capture both renderings at
# import time.  Theme switching at runtime is a single
# QApplication.setStyleSheet() call between the two — no template re-render
# needed.


def _render_stylesheet(palette: dict[str, str]) -> str:
    """Render the application QSS against the given palette.

    Single source of truth for the QSS template.  Both ``APP_STYLESHEET``
    (light) and ``APP_STYLESHEET_DARK`` (dark) are produced by calling this
    once per palette at module import time.  Future template edits land in
    one place; both themes automatically pick them up.
    """
    return f"""
/* --- Base widget defaults --------------------------------------------- */
/* dark-mode-2026q2-e1 rect: explicit text color on QLabel/QWidget so the
   OS QPalette doesn't leak through when QApplication.setStyleSheet swaps
   to the dark theme.  Without this, light-OS users running our Dark theme
   see Qt's QPalette.WindowText (near-black) on dark backgrounds. */
QWidget {{
    color: {palette["TEXT_VALUE"]};
}}
QLabel {{
    color: {palette["TEXT_VALUE"]};
}}

/* --- Role-based label styling (theme-aware via QSS cascade) ----------- */
/* dark-mode-2026q2-e1 rect H1: panels set `label.setProperty("role", X)`
   instead of `label.setStyleSheet(INLINE_STYLE)` so theme switching is
   automatic when QApplication.setStyleSheet swaps light↔dark.  Each role
   captures the size + family that the legacy MUTED_TEXT_STYLE /
   VALUE_MONO_STYLE / RANGE_LABEL_STYLE constants used to inline. */
QLabel[role="muted"] {{
    color: {palette["TEXT_MUTED"]};
    font-size: 10px;
}}
QLabel[role="value-mono"] {{
    font-family: monospace;
    font-size: 11px;
    color: {palette["TEXT_VALUE"]};
}}
QLabel[role="range-label"] {{
    font-family: monospace;
    font-size: 9px;
    color: {palette["TEXT_MUTED"]};
}}

/* --- Dock widget title bars ------------------------------------------ */
QDockWidget {{
    font-size: 12px;
}}
QDockWidget::title {{
    background: {palette["BG_DOCK_HEADER"]};
    color: {palette["TEXT_VALUE"]};
    border-bottom: 1px solid {palette["BORDER_DOCK_HEADER"]};
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
    border: 1px solid {palette["BORDER_GROUP_BOX"]};
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
    background-color: {palette["BG_RESET_BTN"]};
    border: 1px solid {palette["BORDER_RESET_BTN"]};
    color: {palette["TEXT_RESET_BTN"]};
}}
QPushButton#resetDefaultsBtn:hover {{
    background-color: {palette["BG_RESET_BTN_HOVER"]};
}}
QPushButton#resetDefaultsBtn:disabled {{
    background-color: {palette["BG_RESET_BTN_DISABLED"]};
    border: 1px solid {palette["BORDER_RESET_BTN_DISABLED"]};
    color: {palette["TEXT_DISABLED"]};
}}

/* --- Reset Camera button -- outlined, different from view-preset grid -- */
QPushButton#resetCameraBtn {{
    border: 1px solid {palette["BORDER_CAMERA_BTN"]};
    background: transparent;
}}
QPushButton#resetCameraBtn:hover {{
    background: {palette["BG_CAMERA_BTN_HOVER"]};
}}

/* --- Display-toggle checkable buttons (Appearance dock) ------------------ */
/* display-toggles-checkable-button-2026q3-e1 (F-M2 closure):
   QPushButton(checkable=True) replaces QCheckBox for Wireframe + Show-edges.
   The icon is the primary affordance; the 2px FOCUS_RING border signals
   the :checked state (WCAG 1.4.11 non-text contrast carried by the border —
   3.56:1 light / 5.17:1 dark, already proven by focus-ring-contrast-2026q2-e1).
   BG_TOGGLE_CHECKED is decorative fill reinforcement; its contrast vs hover
   is ~1.10:1 by design (state is the BORDER, not the fill).  Industry-aligned
   with Blender N-panel viewport-shading and 3D Slicer modules panel.
   See CONTEXT.md §8.15 for the migration pattern. */
QPushButton[role="display-toggle"] {{
    padding: 3px 8px;
    border-radius: 3px;
    border: 1px solid transparent;
    background: transparent;
    text-align: left;
}}
QPushButton[role="display-toggle"]:hover {{
    background: {palette["BG_CAMERA_BTN_HOVER"]};
    border: 1px solid {palette["BORDER_CAMERA_BTN"]};
}}
QPushButton[role="display-toggle"]:checked {{
    background: {palette["BG_TOGGLE_CHECKED"]};
    border: 2px solid {palette["FOCUS_RING"]};
}}
QPushButton[role="display-toggle"]:checked:hover {{
    background: {palette["BG_CAMERA_BTN_HOVER"]};
    border: 2px solid {palette["FOCUS_RING"]};
}}

/* --- Keyboard focus ring -- visible on all interactive widgets --------- */
QAbstractButton:focus, QComboBox:focus, QSlider:focus {{
    outline: 2px solid {palette["FOCUS_RING"]};
    outline-offset: 1px;
}}

/* --- Status bar -------------------------------------------------------- */
/* dark-mode-2026q2-e1 rect H2: explicit background so the OS QPalette
   doesn't leak through (light-OS user on Dark theme would otherwise see
   the muted text on platform-light QPalette.Window — well below the
   WCAG AA 4.5:1 floor).  See the milestone critique for the exact
   contrast measurement. */
QStatusBar {{
    font-size: 11px;
    color: {palette["TEXT_MUTED"]};
    background: {palette["BG_PANEL"]};
}}
"""


# Rendered once per palette at module import.  `render-panel-chrome.py`
# detects dark-mode capability via `getattr(styles, "APP_STYLESHEET_DARK", None)`
# (see `.claude/references/frontend-uplift/source-registry.md` §4b.1).  Honor
# this naming convention — do NOT rename either constant.
APP_STYLESHEET = _render_stylesheet(PALETTE_LIGHT)
APP_STYLESHEET_DARK = _render_stylesheet(PALETTE_DARK)
