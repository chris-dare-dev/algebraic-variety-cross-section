# Library Scout Brief — 2026q2 Panel Refresh
**Scout:** library-scout  
**Date:** 2026-05-20  
**Scope:** PySide6 / Qt6 / PyVista / VTK / math-typography modernization; strict LGPL-PySide6 redistribution lens

---

## 1. TL;DR

**Top-3 worth adopting or expanding into:** `superqt` (BSD-3-Clause, PySide6-explicit, v0.8.2) for collapsible group boxes and labeled range sliders; `qtawesome` (MIT, PySide6 via qtpy, v1.4.2) for zero-effort toolbar/panel icons; `pyqtdarktheme-fork` (MIT, PySide6-explicit, v2.3.6) for a production-ready dark-mode stylesheet that addresses the INT-94 gap without requiring `styles.py` to be rebuilt from scratch.

**Main thematic gap:** The current Qt toolkit is entirely icon-free and collapsible-panel-free — the three docks grow vertically with no way to hide sections, and all actions (reset, screenshot, view presets) are labeled text-buttons with no visual affordance. Both gaps have targeted, small-footprint solutions already confirmed to work with PySide6.

**PyVista pin note:** The current `pyvista<0.49` pin is artificially conservative; PyPI shows 0.48.4 as latest stable (no 0.49 released as of 2026-05-20), so the pin correctly excludes a release that does not yet exist. The constraint may need widening once 0.49 lands; track it.

---

## 2. Library Candidates

### A. Widget Kits

---

#### `superqt`
- **URL:** https://github.com/pyapp-kit/superqt  
- **Version:** 0.8.2 (released 2026-05-18)  
- **License:** BSD-3-Clause  
- **PySide6 compatibility:** Explicitly listed as a supported binding in PyPI `provides_extra` for PySide6; tested on PyQt5, PyQt6, and PySide6 per project README. Not just "Qt6 should work" — PySide6 is a named install extra.  
- **Maintenance signal:** 348 commits; v0.8.2 released 2026-05-18 (active); 288 GitHub stars. Small-team project in the pyapp-kit org (same org as napari, psygnal). Cadence: multiple releases per year.  
- **What the app could do with it:**  
  - `QCollapsible` — wrap each dock section (e.g. "Camera Presets", "Domain Clip", "Scene Aids" in `view_panel.py`) in a collapsible group so power users can hide infrequently-used controls, addressing the vertical-scroll pressure on smaller screens.  
  - `QLabeledSlider` / `QLabeledDoubleSlider` — replace the custom label+slider+value-readout triplet in `parameters_panel.py` with a single widget that manages its own layout and value label, removing ~30 lines of boilerplate per slider.  
  - `QLabeledRangeSlider` — future candidate for INT-97 (parameter min/max editable range), not needed today but unlocks it.  
  - `QSearchableComboBox` — could replace the variety and model dropdowns if the variety list grows large (future-proofing).  
  - `ensure_main_thread` decorator — could replace the manual `QApplication.processEvents()` / `self._computing` guard pattern in `_render_current` for any future background-thread mesh generation (pairs with AI-9).  
- **Positioning:** adopt-as-import  
- **Interaction primitives unlocked:** [INT-2 slider-release-render] (QLabeledSlider respects the signal discipline), [INT-40 parameters-rebuild-on-switch] (collapsible sections rebuild cleanly), aspirational [INT-90 parameter-sweep-animation] (throttled signal utilities)  
- **Risk flags:** None. BSD-3-Clause is clean for LGPL redistribution. Zero GPL exposure. Dependency is only `qtpy` (MIT) — no bloat.  
- **App-invariant check:** AI-1 (PySide6 — confirmed), AI-2 (Qt-free tests — superqt adds no test fixtures), AI-12 (contrast — QLabeledSlider inherits the app's QSS; test focus-ring visibility after adoption).

---

#### `PySide6-QtAds` (Qt Advanced Docking System)
- **URL:** https://github.com/githubuser0xFFFF/Qt-Advanced-Docking-System; PyPI: `PySide6-QtAds`  
- **Version:** 4.5.0.4 (C++ upstream 4.5.0 released 2026-01-11)  
- **License:** LGPL-2.1  
- **PySide6 compatibility:** First-class — official Python binding published by the C++ project team as `pip install PySide6-QtAds`; separate from PyQtAds and PyQt6Ads. Explicitly supports Windows, macOS, Linux.  
- **Maintenance signal:** 2.5k GitHub stars; 4.5.0 released 2026-01-11 (active); C++ project is the reference for QtAds; Python binding tracks it closely.  
- **What the app could do with it:** Replace `QDockWidget` with tabbed floating/docking panels that can be detached onto a second monitor, snapped into tab groups (e.g. Parameters + Appearance as tabs), or undocked and re-docked freely. The current three-dock layout is serviceable but feels rigid; QtAds enables a ParaView-style re-arrangeable panel UX.  
- **Positioning:** adopt-as-import (substantial integration work — replace all three `QDockWidget` instantiations in `app.py`)  
- **Interaction primitives unlocked:** [INT-6 dock-floatable] (extends beyond Qt's built-in floatable to full drag-tab-group UX), [INT-92 state-persistence-qsettings] (QtAds has its own save/restore state API that pairs cleanly with `QSettings`)  
- **Risk flags:** LGPL-2.1 is compatible with LGPL PySide6 redistribution. Wheel size ranges 476 KB–843 KB (platform-dependent). Moderate integration cost: the app must switch from `QDockWidget.addDockWidget()` to `CDockManager.addDockWidget()`. Hard `requires PySide6-Essentials==6.11.0` pin in the PyPI metadata — version-pinning rigidity is a real risk; check before adopting.  
- **App-invariant check:** AI-1 (PySide6 — confirmed), AI-2 (no test impact — dock layout is not tested). AI-12: QtAds applies its own QSS for tab strips; audit color tokens after integration to preserve WCAG AA.

---

### B. Theming + Dark Mode

---

#### `pyqtdarktheme-fork`
- **URL:** https://pypi.org/project/pyqtdarktheme-fork/ (fork of https://github.com/5yutan5/PyQtDarkTheme)  
- **Version:** 2.3.6 (released 2026-03-04). Original: 2.1.0 (released 2022-12-25, stale)  
- **License:** MIT  
- **PySide6 compatibility:** Explicitly supports PySide6, PyQt6, PyQt5, PySide2 — stated in the fork README. Fork was created specifically to fix compatibility with newer Python versions (through 3.14).  
- **Maintenance signal:** Fork is active (2.3.6 published 2026); original is stale (last release 2022). Use the fork. 746 GitHub stars on original; fork stars not surveyed but publication cadence demonstrates health.  
- **What the app could do with it:** Provide a production-ready dark-mode QSS palette (INT-94) by calling `qdarktheme.setup_theme("dark")` or `"light"` on launch. Avoids rebuilding `styles.py` from scratch — the library generates a complete QSS string that can be merged with or layered over the existing `APP_STYLESHEET`. Supports auto-detection of system dark/light preference. Includes SVG icon stubs (Material Design, Apache-2.0) that render correctly in both themes.  
- **Positioning:** adopt-as-import for the dark-mode palette; design-pattern lift for the system-preference detection pattern  
- **Interaction primitives unlocked:** [INT-94 dark-mode-stylesheet]; pairs with [INT-96 palette-template-per-variety] (dark surface colors per variety family)  
- **Risk flags:** MIT — clean. The original project is stale; always specify `pyqtdarktheme-fork` not `pyqtdarktheme` in `requirements.txt`. Small risk: fork may diverge from community tooling that targets the original package name. Consider pinning the fork at >=2.3 to stay on the active branch.  
- **App-invariant check:** AI-12 (contrast) — after applying the dark QSS, re-verify `COLOR_MUTED` equivalent on dark background clears 4.5:1; the library provides its own contrast-safe palette but the app overrides some color tokens that must be audited.

---

#### `qt-material`
- **URL:** https://github.com/UN-GCPDS/qt-material  
- **Version:** 2.17 (released 2025-04-21)  
- **License:** BSD-2-Clause  
- **PySide6 compatibility:** Explicitly listed in README: "stylesheet for PySide6, PySide2, PyQt5 and PyQt6."  
- **Maintenance signal:** 2.8k GitHub stars; 2.17 released 2025-04-21; 243 commits. Active. No abandonment signals.  
- **What the app could do with it:** Provide a Material Design stylesheet as an alternative to pyqtdarktheme-fork. Comes with 19 pre-built themes (dark and light variants) selectable by name. Useful if the team wants a more opinionated palette with color-family variants (teal-dark, blue-dark, etc.) rather than a single dark/light toggle.  
- **Positioning:** design-pattern lift (one of `pyqtdarktheme-fork` or `qt-material` should be adopted; they are alternatives, not complements)  
- **Interaction primitives unlocked:** [INT-94 dark-mode-stylesheet]  
- **Risk flags:** BSD-2-Clause — clean. Slightly heavier than pyqtdarktheme-fork because it ships 19 XML theme files. The Material Design aesthetic may feel inconsistent with the current subdued scientific-viz palette in `styles.py`. Recommend `pyqtdarktheme-fork` over `qt-material` for this app because its system-preference detection and accent-color syncing are more appropriate for a research tool than Material Design's vivid palettes.  
- **App-invariant check:** AI-12 — same audit required as any QSS replacement.

---

### C. Icons

---

#### `qtawesome`
- **URL:** https://github.com/spyder-ide/qtawesome  
- **Version:** 1.4.2 (released 2026-04-10)  
- **License:** MIT; bundled fonts: SIL Open Font License (FontAwesome), Apache-2.0 (Material Design Icons, Remix), CC-BY-4.0 (Codicons). All compatible with LGPL redistribution.  
- **PySide6 compatibility:** Uses `qtpy` as compatibility shim; qtpy explicitly supports PySide6. CI tests specifically added PySide6 6.8.3 in v1.4.1.  
- **Maintenance signal:** 930 GitHub stars; v1.4.2 released 2026-04-10 (active); maintained by Spyder IDE team — production-grade.  
- **What the app could do with it:** Add icons to currently-bare toolbar buttons and dock-panel actions. Specific affordances:  
  - `qta.icon("fa6.camera")` → Screenshot button in `view_panel.py` (currently reads "Screenshot")  
  - `qta.icon("mdi6.axis-arrow")` → World-axes triad toggle  
  - `qta.icon("mdi6.cube-outline")` → Domain clip mode  
  - `qta.icon("mdi6.rotate-3d")` → Reset Camera button  
  - `qta.icon("mdi6.palette")` → Appearance dock header  
  - `qta.icon("fa6.sliders")` → Parameters dock header  
  Without `qtawesome`, adding icons requires shipping SVG files and a custom loader — this is the cheapest viable icon path.  
- **Positioning:** adopt-as-import  
- **Interaction primitives unlocked:** [INT-5 keyboard-shortcut] icons reinforce the visual identity of shortcutted actions; [INT-98 help-menu-with-citations] (an About dialog icon)  
- **Risk flags:** `qtpy` is a transitive dependency (MIT, adds ~100 KB). Known cold-boot cost: qtawesome caches icon fonts on first use; on cold boot (no OS font cache) this can add ~150–200ms to app startup as the font files are parsed and registered with Qt's font engine. This is a one-time per-launch cost, not per-icon. Acceptable for a research desktop tool but should be noted in integration guidance. Bundle: icon font files total ~3 MB on disk.  
- **App-invariant check:** AI-1 (PySide6 via qtpy — confirmed), AI-12 (icons do not affect text contrast), AI-2 (no test impact — icons are purely visual).

---

### D. Animation

---

#### `QPropertyAnimation` + `QParallelAnimationGroup` (PySide6 built-in)
- **URL:** https://doc.qt.io/qtforpython-6/PySide6/QtCore/QPropertyAnimation.html  
- **Version:** Bundled with PySide6 ≥ 6.6 (already in deps)  
- **License:** LGPL (bundled with PySide6)  
- **PySide6 compatibility:** Native — it is PySide6.  
- **Maintenance signal:** Qt 6.x LTS; not a risk.  
- **What the app could do with it:** `QPropertyAnimation` animates Qt `Q_PROPERTY` values (opacity, geometry, color) on `QObject` subclasses. For the app, the direct use case is animating the domain-clip radius slider visually during a sweep [INT-90] — the VTK camera itself is not a `QObject` so `QPropertyAnimation` cannot drive it directly. However, a thin wrapper `QObject` with a `@Property(float)` for camera azimuth + a `QPropertyAnimation` targeting it, combined with a `QTimer` that calls `plotter.camera.azimuth = value; plotter.render()` in its setter, is the correct pattern for [INT-24 camera-transition-interp]. This is the vendor-copy-of-a-pattern approach: the pattern is well-established, no new dep is added.  
- **Positioning:** vendor-copy-of-a-pattern (already in PySide6; the pattern needs documenting, not installing)  
- **Interaction primitives unlocked:** [INT-24 camera-transition-interp], [INT-90 parameter-sweep-animation]  
- **Risk flags:** None — already in deps. The key gotcha: VTK's render window is not a Qt widget in the animation sense; any camera animation must drive VTK state via Python callbacks on a `QTimer`, not via `QPropertyAnimation` targeting VTK properties directly. Misunderstanding this leads to no-op animations.  
- **App-invariant check:** AI-9 (re-entrancy) — any `QTimer`-driven camera sweep must check `self._computing` before triggering render; AI-1 (uses PySide6 only — no new dep).

---

### E. PyVista / VTK Ecosystem

---

#### `pyvista` (upgrade candidate — already pinned)
- **URL:** https://github.com/pyvista/pyvista  
- **Version pinned:** ≥0.46, <0.49. Latest stable: 0.48.4  
- **License:** MIT  
- **PySide6 compatibility:** N/A — pyvista is a VTK Python wrapper; pyvistaqt handles the Qt bridge.  
- **Maintenance signal:** 0.48.4 is the current latest (PyPI confirmed 2026-05-20). No 0.49 exists yet. The current upper bound `<0.49` is therefore not restrictive in practice, but it will require widening when 0.49 ships.  
- **What the app could do with it:** The 0.47 release added `pv.to_trimesh()` / `pv.from_trimesh()` integration — useful for mesh export to Blender-friendly formats without `meshio`. The 0.48 release added plugin registry extensibility and `validate` CLI — not directly useful to the app but signals API stability. Neither release introduces breaking changes affecting `clip_scalar`, marching cubes pipeline, or `smooth_taubin`.  
- **Positioning:** already in deps — propose UPGRADE to `>=0.46,<0.50` (widen upper bound to not block the 0.49 release)  
- **Interaction primitives unlocked:** [INT-93 mesh-export-button] via `pv.to_trimesh()` integration  
- **Risk flags:** The `<0.49` upper bound will block the next release when it ships. Widening to `<0.50` is low-risk given no breaking changes in the 0.47–0.48 series affecting the app's usage patterns. Monitor 0.49 release notes for any `smooth_taubin`, `clip_scalar`, or `compute_normals` deprecations.

---

#### `meshio`
- **URL:** https://github.com/nschloe/meshio  
- **Version:** 5.3.5 (released 2024-01-31)  
- **License:** MIT  
- **PySide6 compatibility:** No Qt dependency at all — pure Python + NumPy mesh I/O library.  
- **Maintenance signal:** 2.3k GitHub stars; 3,577 commits; 81 releases; active CI. Well-maintained.  
- **What the app could do with it:** Enable [INT-93 mesh-export-button] with a full format suite: `meshio.write("surface.stl", mesh)`, `"surface.obj"`, `"surface.ply"`, `"surface.vtu"`. The app currently has zero export (CONTEXT.md §9). This is the correct library when the researcher wants to open the exported mesh in Blender, Meshmixer, GeoGebra, or a slicer. `pyvista`'s own `mesh.save()` covers STL/VTK natively; `meshio` adds OBJ, PLY, CGNS, Exodus, etc. for broader compatibility.  
- **Positioning:** adopt-as-import (pair with a new Export button in `view_panel.py`)  
- **Interaction primitives unlocked:** [INT-93 mesh-export-button]  
- **Risk flags:** MIT — clean. Base install requires only `numpy` and `rich` (~1 MB total). Optional `h5py`/`netcdf4` for HDF/NetCDF formats are not needed for the app's use case. No GPL exposure. The `rich` dependency adds ~500 KB but is benign.  
- **App-invariant check:** AI-2 (Qt-free tests — meshio has no Qt dependency, so mesh-export logic is testable without Qt fixtures).

---

### F. Math Typography

---

#### KaTeX via `PySide6-Addons` (`QtWebEngineWidgets`)
- **URL:** https://katex.org/ (v0.16.47, released 2026-05-16); Qt module: `PySide6.QtWebEngineWidgets` (in `PySide6-Addons`)  
- **Version:** KaTeX 0.16.47; PySide6-Addons is distributed as part of PySide6 ≥ 6.6  
- **License:** KaTeX: MIT; `QtWebEngineWidgets`: LGPL-2.1 (part of Qt WebEngine, which wraps Chromium — the Chromium bits are BSD-licensed; redistribution of the full Qt WebEngine binary is subject to Qt's LGPL terms)  
- **PySide6 compatibility:** `QtWebEngineWidgets` is explicitly in `PySide6-Addons` — confirmed from PyPI metadata. Installed automatically when `pip install PySide6` is run (Addons is a required sub-dependency of the top-level `PySide6` package).  
- **Maintenance signal:** KaTeX v0.16.47 released 2026-05-16 (bug-fix active); Qt WebEngine is Qt LTS infrastructure — not a maintenance risk.  
- **What the app could do with it:** Implement [INT-95 katex-tooltip-popover] — a floating `QDialog` containing a `QWebEngineView` that renders the variety's defining equation as typeset LaTeX (e.g., `x^4+y^4+z^4+\alpha(x^2y^2+y^2z^2+z^2x^2)=c` for the Fermat quartic). KaTeX renders synchronously with no server, sub-10ms for typical algebraic-geometry expressions. The tooltip currently shows unicode-approximated equations (`x⁴+y⁴+z⁴`); a KaTeX popover would replace that for the hover interaction on variety/subtype combo items.  
- **Positioning:** adopt-as-import for the rendering engine; design-pattern lift for the QDialog popup pattern  
- **Interaction primitives unlocked:** [INT-95 katex-tooltip-popover], [INT-7 tooltip-rich] (elevates from plain-text to rendered math)  
- **Risk flags:** **Bundle bloat — MAJOR caveat.** `QtWebEngineWidgets` is in `PySide6-Addons`. `PySide6-Addons` wheel on Windows is ~450 MB. However: `PySide6-Addons` is already installed as part of `pip install PySide6` (it is a required dependency of the top-level `PySide6` meta-package). This means the bundle bloat is **already paid** by the existing `PySide6>=6.6` pin — `QtWebEngineWidgets` is a zero-marginal-cost import for the app. The only new dependency is KaTeX itself (served as a local HTML file bundled with the app — ~300 KB for katex.min.js + katex.min.css). License: MIT + LGPL are both clean for LGPL redistribution.  
- **App-invariant check:** AI-1 (PySide6 — confirmed), AI-2 (Qt-free tests — KaTeX rendering requires a live `QWebEngineView`; the equation-preparation logic must be kept in a Qt-free layer), AI-12 (KaTeX renders its own text; verify dark-mode CSS if INT-94 is also adopted).

---

#### `matplotlib` mathtext (via Agg backend)
- **URL:** https://matplotlib.org/stable/users/explain/text/mathtext.html  
- **Version:** 3.10.9 (latest); wheel ~8–9 MB  
- **License:** BSD-3-Clause-like (PSF-compatible)  
- **PySide6 compatibility:** No direct Qt dependency — matplotlib's Agg backend renders to a numpy array/PNG buffer without a display. A `QPixmap.fromImage()` bridge converts the buffer to a Qt-displayable icon.  
- **Maintenance signal:** Actively maintained LTS scientific Python stack.  
- **What the app could do with it:** Render individual math expressions (e.g., `r"$x^4+y^4+z^4=c$"`) to a `QPixmap` via `matplotlib.mathtext.math_to_image()` and display as a `QLabel` with `setPixmap()`. Lower fidelity than KaTeX but does not require `QtWebEngineWidgets`. Best suited for static equation labels inside panels rather than floating popovers.  
- **Positioning:** adopt-as-import — lighter-weight fallback for [INT-95] if the team wants to avoid a `QWebEngineView` dependency (though the bundle cost argument above shows `QtWebEngineWidgets` is already paid)  
- **Interaction primitives unlocked:** [INT-95 katex-tooltip-popover] (partial — labels not interactive popovers)  
- **Risk flags:** Adds ~8–9 MB to the install footprint. matplotlib is not currently in `requirements.txt`; adding it solely for mathtext is disproportionate if KaTeX via the already-present `QtWebEngineWidgets` is viable. However, if the team decides to add 2D parameter-sweep plots (INT-90 companion), matplotlib is the right library for that too, making the dep proportionate.  
- **App-invariant check:** AI-1 (no Qt in the rendering path — uses Agg), AI-10 (`matplotlib.use("Agg")` must be called before importing `pyplot` to prevent it from stealing the Qt event loop — a known footgun for apps that mix Qt + matplotlib).

---

### G. Packaging

---

#### `PyInstaller`
- **URL:** https://www.pyinstaller.org/  
- **Version:** 6.20.0 (latest on PyPI)  
- **License:** GPL-2.0-or-later **with explicit redistribution exception** — the exception reads "you may use PyInstaller to build and distribute non-free programs (including commercial ones)" without GPL propagation to the bundled app. This is the standard PyInstaller exception and is widely interpreted as safe for LGPL/MIT app redistribution.  
- **PySide6 compatibility:** Explicitly supported — PyInstaller 6.x ships named hooks for PySide6 that correctly bundle all Qt shared libraries, plugin directories, and QML files. Confirmed in PyPI metadata.  
- **Maintenance signal:** 6.20.0 released 2026 (active); PyInstaller is the most-used Python bundler; hooks are community-maintained.  
- **What the app could do with it:** Bundle the entire app (PySide6 + PyVista + VTK + scikit-image + NumPy) into a single folder or one-file executable for distribution to users without a Python environment. Relevant if the project moves toward researcher-audience distribution (macOS .app, Windows .exe, Linux AppImage).  
- **Positioning:** adopt-as-import (packaging toolchain — not imported at runtime; added as a dev dependency)  
- **Interaction primitives unlocked:** N/A (packaging, not interaction)  
- **Risk flags:** The GPL-2.0 license on the tool itself does NOT propagate to the bundled app under the redistribution exception. However, bundling adds ~300–600 MB to the distribution (PySide6 alone is ~560 MB wheel). VTK adds another ~100 MB. The resulting bundle is large; the team should evaluate whether distribution to end users is a near-term priority before investing in packaging toolchain.  
- **App-invariant check:** AI-1 (PyInstaller's PySide6 hooks handle the full Qt plugin tree); the VTK GL context and pyvistaqt require careful `--collect-all pyvista` and `--collect-all pyvistaqt` hook flags.

---

## 3. Sources Reviewed

| Library | URL | License | PySide6-compat | Stars | Last Release | Recommended Tier |
|---|---|---|---|---|---|---|
| superqt | https://github.com/pyapp-kit/superqt | BSD-3-Clause | Explicit (named extra on PyPI) | 288 | 2026-05-18 | **Tier 1 — Adopt** |
| qtawesome | https://github.com/spyder-ide/qtawesome | MIT (fonts: SIL/Apache-2.0/CC-BY-4.0) | Explicit via qtpy (CI tests PySide6 6.8.3) | 930 | 2026-04-10 | **Tier 1 — Adopt** |
| pyqtdarktheme-fork | https://pypi.org/project/pyqtdarktheme-fork/ | MIT | Explicit (PySide6 listed in README) | N/A (fork) | 2026-03-04 | **Tier 1 — Adopt (prefer fork over original)** |
| qt-material | https://github.com/UN-GCPDS/qt-material | BSD-2-Clause | Explicit (README states PySide6) | 2.8k | 2025-04-21 | **Tier 2 — Alternative to pyqtdarktheme-fork** |
| PySide6-QtAds | https://github.com/githubuser0xFFFF/Qt-Advanced-Docking-System | LGPL-2.1 | Explicit (official PySide6 binding published to PyPI) | 2.5k | 2026-01-11 | **Tier 2 — High-value, moderate integration cost** |
| KaTeX (via QtWebEngineWidgets) | https://katex.org/ | MIT (KaTeX) + LGPL (Qt WebEngine, already in PySide6-Addons) | N/A — Qt module already bundled with PySide6 | N/A | 2026-05-16 | **Tier 1 — Zero marginal cost** |
| meshio | https://github.com/nschloe/meshio | MIT | No Qt dependency | 2.3k | 2024-01-31 | **Tier 1 — Adopt for INT-93** |
| numpy-stl | https://github.com/wolph/numpy-stl | BSD-3-Clause | No Qt dependency | 680 | 2024-11-25 | **Tier 3 — Only if meshio is too heavy** |
| pyvista (upgrade) | https://github.com/pyvista/pyvista | MIT | N/A — pyvistaqt handles Qt | — | 0.48.4 (2024-05-02) | **Existing dep — UPGRADE pin** |
| pyvistaqt | https://github.com/pyvista/pyvistaqt | MIT | Explicit | — | 0.11.4 (2026-04-03) | **Existing dep — monitor 0.12.0rc1** |
| matplotlib mathtext | https://matplotlib.org/ | PSF/BSD-3 | No Qt in Agg path | — | 3.10.9 | **Tier 2 — Only if KaTeX rejected** |
| sympy | https://www.sympy.org/ | BSD | No Qt dependency | — | 1.14.0 (2025-04-27) | **Tier 3 — LaTeX string generation only** |
| QPropertyAnimation (PySide6 built-in) | https://doc.qt.io/qtforpython-6/ | LGPL | Native | — | Bundled | **Pattern lift — no new dep** |
| PyInstaller | https://www.pyinstaller.org/ | GPL-2.0 + redistribution exception | Explicit (named hooks for PySide6) | — | 6.20.0 | **Tier 2 — When distribution is a goal** |
| pyqtdarktheme (original) | https://github.com/5yutan5/PyQtDarkTheme | MIT | Explicit | 746 | 2022-12-25 | **Rejected — use fork instead** |
| PyQt-Fluent-Widgets | https://github.com/zhiyiYo/PyQt-Fluent-Widgets | GPL-3.0 | Yes (PySide6 branch) | 7.9k | active | **REJECTED — GPL-3.0 MAJOR license flag** |

---

## 4. Themes

**Icon famine and collapsibility gap are the dominant near-term opportunities.** The three docks contain text-only buttons and flat vertical stacks of sliders; `qtawesome` + `superqt` address both with negligible bundle cost and zero GPL exposure — these two are the highest-confidence quick wins.

**Dark-mode is overdue but the machinery is already nearly paid.** `pyqtdarktheme-fork` provides a system-preference-aware QSS palette; the app's `styles.py` centralization makes it straightforward to add a parallel `STYLESHEET_DARK` constant. The biggest cost is auditing the PyVista `set_plot_theme('dark')` side effects on the 3D viewport.

**Math typography has a zero-marginal-cost path via KaTeX.** `QtWebEngineWidgets` is already bundled in `PySide6-Addons` which is already installed as part of `PySide6 >= 6.6`. The only new asset is a ~300 KB KaTeX bundle shipped as a local HTML file — this is the cheapest rendered-equation option and avoids adding matplotlib (~9 MB) purely for mathtext.

**The PyVista pin is correct today but will block the next minor release.** PyPI confirms 0.48.4 as the latest; no 0.49 exists. Widening the upper bound to `<0.50` in `requirements.txt` is a low-risk one-line change that future-proofs the stack.

---

## 5. The App Already Has

Libraries already in `requirements.txt` that appear in candidate considerations:

- **`PySide6>=6.6,<7`** — `QtWebEngineWidgets` is included in `PySide6-Addons`, a required sub-package. The KaTeX tooltip candidate (INT-95) is therefore a **zero-new-dep** upgrade. EXPAND: import `PySide6.QtWebEngineWidgets.QWebEngineView` for the math tooltip.
- **`pyvista>=0.46,<0.49`** — Latest stable is 0.48.4. No 0.49 released yet. UPGRADE: widen to `<0.50` to not block the next minor. The 0.47 `pv.to_trimesh()` integration pairs with INT-93 mesh export — this is an **unexploited capability** already in the dep range.
- **`pyvistaqt>=0.11.4,<0.12`** — 0.12.0rc1 released 2026-04-19. Stable 0.11.4 is appropriate for production. MONITOR: when 0.12.0 goes stable, widen upper bound; check release notes for any `QtInteractor` API changes.
- **`numpy>=1.26,<3`** — No action needed; upper bound is generous.
- **`scikit-image>=0.22,<0.27`** — No action needed; 0.22–0.26 series is stable.

---

## 6. Out of Scope / Parking Lot

| Library | Reason not surfaced |
|---|---|
| **PyQt-Fluent-Widgets** | GPL-3.0 — MAJOR license flag; import into a redistributable PySide6 binary is incompatible. Study-only. |
| **QScintilla** | GPL-3.0 (free tier) — same MAJOR flag. Only relevant if equation-entry widget is added; not on the INT roadmap. |
| **qframelesswindow** | License ambiguity (LGPL-3.0 / GPL-3.0 depending on the branch); the app's standard `QMainWindow` chrome is not a pain point worth the risk. |
| **trame** | Apache-2.0 and technically sound, but it is a web-companion framework (HTML front-end over VTK server). Not compatible with the app's Qt-native desktop-first architecture (AI-1). |
| **pymeshfix** | GPL-2.0+ — import-blocking. The app's meshes come from analytic generators + marching cubes; non-manifold repair is not a current need. |
| **PyQtGraph** | MIT, PySide6-compatible, but only relevant when a 2D companion plot (parameter sweep time-series, cross-section curve) is added. Not on the current INT roadmap; park for a future scout. |
| **MathJax v4** | Apache-2.0 — clean license, but ~7 MB JS bundle vs KaTeX's ~300 KB. KaTeX covers all the algebraic-geometry LaTeX needed; MathJax is overkill. |
| **Briefcase (BeeWare)** | BSD-3-Clause and PySide6-compatible in principle, but does not explicitly list PySide6 in its docs. PyInstaller is more mature for Qt+VTK bundles. Revisit if cross-platform .app packaging becomes a priority. |
| **SymPy** | BSD — clean, but its role here would be generating LaTeX strings that KaTeX renders. That is a thin add-on to the KaTeX pattern, not a standalone candidate. If variety equations are stored as SymPy expressions in `surfaces.py` (future refactor), SymPy becomes relevant. |
| **imageio / Pillow** | Already transitively present via PyVista; no new dep action needed. |
| **uv / ruff / pre-commit** | DX tooling — out of scope for a UI/panel-refresh scout. Relevant for a separate DX/toolchain pass. |
| **cibuildwheel** | CI infrastructure — only relevant when the project adopts GitHub Actions for multi-platform wheel builds. Not a UI concern. |
| **pyqtdarktheme (original)** | MIT but last release was 2022-12-25 — stale. Superseded by `pyqtdarktheme-fork` (v2.3.6, 2026-03-04). Never use the original package going forward. |
