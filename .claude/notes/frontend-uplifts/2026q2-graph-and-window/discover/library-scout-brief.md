# Library Scout Brief — 2026q2-graph-and-window

**Agent:** library-scout
**Uplift scope:** Tier-1 panel-chrome shakedown — surface gaps in BOTH the 3D plot rendering AND the Qt panel chrome / window frame / dock layout / styles. First exercise of the render-panel-chrome.py pipeline.
**Date:** 2026-05-21
**Orientation reads:** requirements.txt, CONTEXT.md, source-registry.md §2, design-system.md, interaction-vocabulary.md

---

## 1. TL;DR

The three strongest candidates for immediate adoption are **superqt** (collapsible panels + throttled sliders address the most acute panel-chrome gaps), **qtawesome** (zero-cost toolbar icons — no icons exist today), and **pyqtdarktheme-fork** (the only production-grade, actively maintained dark+light stylesheet with verified PySide6 6.6+ support). The app's main thematic toolkit gap is that it manually works around the absence of collapsible group boxes, throttled slider signals, and any icon set — all three are stock features of superqt and qtawesome that would replace custom boilerplate in `parameters_panel.py` and `appearance_panel.py` today. A secondary viewport-rendering gap is that `Plotter.fly_to` is the only camera-animation primitive in the current dep set, and it is too coarse for the smooth 300ms preset transitions INT-24 requires — QPropertyAnimation (already in PySide6) is the correct pairing.

---

## 2. Library Candidates

### Category A — Widget Kits

---

#### A1. superqt

- **URL:** https://github.com/pyapp-kit/superqt
- **Version:** 0.8.2 (released 2026-05-18)
- **License:** BSD-3-Clause
- **PySide6 compatibility:** Explicitly tested against PySide6 ≥ 6.4 on macOS, Windows, Linux (from pyproject.toml extras: `pyside6>=6.4.0`). v0.8.0 dropped PySide2 and Python 3.9, committing fully to PyQt5/PyQt6/PySide6 as the supported triad.
- **Maintenance signal:** 35 releases; v0.8.2 shipped 2026-05-18 (3 days before this survey). GitHub stars: 288. Active micro-release cadence.
- **What the app could do with it:** (1) Replace the flat parameter list in `parameters_panel.py` with `QCollapsible` group boxes — one collapsible section per logical parameter group (K3 shape, K3 scale, etc.) without adding any `QGroupBox` subclass boilerplate. (2) Replace manual "only render on sliderReleased" workaround with `superqt.signals.throttled` — a decorator that throttles the signal to fire at most once per N ms, replacing the current ad-hoc connection gymnastics. (3) `QLabeledSlider` and `QLabeledRangeSlider` give per-slider min/max tick labels natively, replacing the custom `RANGE_LABEL_STYLE` span layout that `parameters_panel.py` constructs by hand.
- **Positioning:** adopt-as-import (pip install superqt — no vendoring needed)
- **Interaction primitives unlocked:** [INT-2 slider-release-render] (throttled slot replaces manual sliderReleased connection), [INT-40 parameters-rebuild-on-switch] (QCollapsible teardown is self-contained), [INT-97 parameter-spin-box-alternative] (superqt's `QQuantitySpinBox` is a drop-in)
- **Risk flags:** qtpy is a transitive dep (superqt uses qtpy as its Qt shim). qtpy 2.4.3 is MIT and stable, but adds one indirection layer over direct PySide6 imports — ensure the app's direct `from PySide6.QtWidgets import ...` imports are not replaced by qtpy-style imports to avoid mixing idioms. No GPL exposure. No bundle bloat (pure Python, ~200 KB wheel).
- **App-invariant check:** AI-2 safe (no Qt in tests). AI-1 safe (adds widgets on top of PySide6, does not replace it). AI-12: `QCollapsible` uses the system palette by default — verify contrast when collapsed label is rendered on `#e8edf2` dock header.

---

#### A2. PySide6-QtAds (Qt Advanced Docking System)

- **URL:** https://github.com/mborgerson/pyside6_qtads | https://github.com/githubuser0xFFFF/Qt-Advanced-Docking-System
- **Version:** 4.5.0.4 (PySide6 Python binding; upstream ADS latest)
- **License:** LGPL-2.1 (same as PySide6 — compatible redistribution posture)
- **PySide6 compatibility:** This is a PySide6-native binding (not a PyQt5 port). Install: `pip install PySide6-QtAds`. The binding requires **`PySide6-Essentials==6.11.0` exactly** — a hard version pin that conflicts with the app's current `PySide6>=6.6,<7` range unless that minor also happens to be 6.11.
- **Maintenance signal:** 252 commits, 40 GitHub stars on the Python binding wrapper. The upstream C++ ADS library is far more active (4.4k stars). The Python binding is a thin wrapper — upstream activity is the meaningful signal.
- **What the app could do with it:** Replace the three `QDockWidget` instances with ADS docks to gain: (a) true tabbed docking (View + Parameters + Appearance as tabs on demand), (b) floating docks that remember their position across launches when paired with `QSettings` [INT-92], (c) dock-area separators that resize without popping out of the main window, and (d) a horizontal dock-header strip that is denser than Qt's default vertical title. ADS panels look visually heavier than the current light chrome — only adopt after the panel-chrome critique lands.
- **Positioning:** adopt-as-import — but BLOCKED by `PySide6-Essentials==6.11.0` hard pin until PySide6-QtAds ships a version compatible with the app's installed PySide6 minor. Do not adopt in this sprint without first pinning `PySide6==6.11.*` and verifying the rest of the dep tree.
- **Interaction primitives unlocked:** [INT-6 dock-floatable] (enhanced beyond Qt default), [INT-92 state-persistence-qsettings] (ADS serializes dock state natively)
- **Risk flags:** MAJOR — hard `PySide6-Essentials==6.11.0` pin means adopting QtAds forces a PySide6 minor upgrade across the whole project. This can break `pyvistaqt` which also pins pyvista and VTK transitively. Audit the full dep tree before attempting. Do not adopt speculatively.
- **App-invariant check:** AI-1 safe (layered on PySide6). AI-2 safe. AI-12: ADS title bars use the host QSS, so `COLOR_DOCK_HEADER_BG` still applies.

---

### Category B — Theming + Dark-Mode

---

#### B1. pyqtdarktheme-fork

- **URL:** https://github.com/5yutan5/PyQtDarkTheme (fork; PyPI: `pyqtdarktheme-fork`)
- **Version:** 2.3.6 (released 2026-03-04)
- **License:** MIT
- **PySide6 compatibility:** Explicitly demonstrated with `from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton` in its own docs. Tested against Python 3.8–3.14. The original `pyqtdarktheme` package is frozen at v2.1.0 (2022-12-25) and should NOT be used — the fork is the live project.
- **Maintenance signal:** PyPI fork last released 2026-03-04. Original repo: 746 stars. Fork adds Python 3.14 support and ongoing bugfixes. One runtime dep: `darkdetect>=0.7` (MIT, 30 KB) for OS-level dark/light detection.
- **What the app could do with it:** (1) Implement [INT-94 dark-mode-stylesheet] via `qdarktheme.setup_theme("dark")` or `setup_theme("light")` — a single call that replaces `APP_STYLESHEET` application-wide with a polished, WCAG-tested dark or light QSS. (2) Wire `setup_theme("auto")` to follow macOS system appearance. (3) A toggle button in the View panel or menu bar flips themes at runtime without restart. The app's current `styles.py` palette (`COLOR_MUTED`, `COLOR_DOCK_HEADER_BG`, etc.) would need to be conditionally applied as overrides on top of the pyqtdarktheme base — or ported into a `STYLESHEET_DARK` parallel following the existing pattern.
- **Positioning:** adopt-as-import; the existing `styles.py` custom QSS is complementary (override-on-top), not replaced wholesale
- **Interaction primitives unlocked:** [INT-94 dark-mode-stylesheet] (this is the direct vehicle), [INT-82 focus-ring-on-controls] (pyqtdarktheme includes its own focus-ring tokens — verify they match the app's `#5b9bd5` blue)
- **Risk flags:** `darkdetect` dep is tiny and MIT — no concern. The fork's GitHub is the original repo (the fork lives as a separate PyPI slug, not a separate repo). Verify `COLOR_MUTED = #5a5a5a` retains WCAG AA (≥4.5:1) against pyqtdarktheme's dark background (~`#1e1e2e` or similar) before shipping — light-mode contrast ratios do not transfer to dark backgrounds.
- **App-invariant check:** AI-12 — requires explicit contrast audit on dark palette. AI-13: PyVista `add_mesh(color=...)` is unaffected by QSS. Colors flowing to `plotter.set_plot_theme(...)` should be set in parallel with `setup_theme()`.

---

#### B2. qt-material

- **URL:** https://github.com/dunderlab/qt-material
- **Version:** 2.17 (released 2025-04-21 — ~13 months before this survey)
- **License:** BSD-2-Clause
- **PySide6 compatibility:** Explicitly documented with `--pyside6` flag in CLI examples. Confirmed working with PySide6 in its own docs.
- **Maintenance signal:** 72 GitHub stars. Last release over 13 months ago. One dep: Jinja2 (BSD-3-Clause, ~200 KB). The low star count relative to pyqtdarktheme-fork (~746) suggests lower community adoption.
- **What the app could do with it:** Apply a Material Design color palette to the Qt chrome — 18 built-in themes (dark amber, light teal, etc.). Would give the app a different visual register than pyqtdarktheme — Material Design palette suits general productivity apps; pyqtdarktheme's flat palette suits scientific tools more closely.
- **Positioning:** design-pattern lift only — do NOT adopt alongside pyqtdarktheme-fork; pick one. qt-material is secondary here because of lower maintenance velocity and lower community adoption.
- **Interaction primitives unlocked:** [INT-94 dark-mode-stylesheet]
- **Risk flags:** Last release >13 months ago suggests maintenance risk. Jinja2 dep adds ~200 KB. Material Design palette may clash with the app's restrained scientific-viz color language. The 72-star signal is weak for a theming library being adopted as a core dep.
- **App-invariant check:** AI-12 — same dark-palette contrast audit required as B1.

---

### Category C — Icons

---

#### C1. qtawesome

- **URL:** https://github.com/spyder-ide/qtawesome
- **Version:** 1.4.2 (released 2026-04-10)
- **License:** MIT
- **PySide6 compatibility:** v1.4.1 (Jan 2026) specifically fixed segfaults on PySide6 6.8.x and added comprehensive Qt6 test coverage. The library operates via `qtpy` as its shim — `qtpy` 2.4.3 supports PySide6. Confirmed working with PySide6 across CI matrix.
- **Maintenance signal:** 930 GitHub stars. v1.4.2 released 2026-04-10. Active; two releases in 2026.
- **What the app could do with it:** Add icons to the five camera-preset buttons (Reset, Front, Top, Side, Isometric), the screenshot button, the Reset Defaults button, and the screenshot/export action — none of which carry icons today (`view_panel.py`, `parameters_panel.py`). Icons from FontAwesome 6 (`fa6s.arrows-rotate` for Reset Camera, `fa6s.camera` for Screenshot, `fa6s.rotate-left` for Reset Defaults) would give the toolbar visual anchors that reduce cognitive load. MaterialDesign icons (`mdi6.*`) offer 6,997 icons and match the scientific-app icon vocabulary better than FontAwesome brands.
- **Positioning:** adopt-as-import; lazy-import recommended (see lesson in agent-memory) to avoid ~150–200ms cold-boot hit
- **Interaction primitives unlocked:** [INT-5 keyboard-shortcut] (icons on shortcut-bound buttons make shortcuts more discoverable), [INT-3 busy-cursor] (a spinner icon `fa6s.spinner` can animate inside the button while computing)
- **Risk flags:** cold-boot icon-font caching adds ~150–200ms on first use (documented in agent-memory/frontend-uplift-library-scout/lessons.md). Mitigate with lazy import. `qtpy` transitive dep — same concern as superqt. No GPL exposure.
- **App-invariant check:** AI-2 safe (icons are runtime Qt — no test import). AI-12: icon color should be set explicitly to match `COLOR_MUTED = #5a5a5a` or `COLOR_VALUE = #333333` rather than defaulting to theme foreground, so contrast is controlled.

---

### Category D — Animation

---

#### D1. Qt QPropertyAnimation + QParallelAnimationGroup (built-in PySide6)

- **URL:** https://doc.qt.io/qtforpython-6/PySide6/QtCore/QPropertyAnimation.html
- **Version:** Ships with PySide6 ≥ 6.6 (already in requirements.txt)
- **License:** LGPL-2.1 (Qt license — already accepted by the project)
- **PySide6 compatibility:** Native — QPropertyAnimation is part of PySide6.QtCore.
- **Maintenance signal:** Qt LTS — not a third-party dependency; effectively maintenance-free from the app's perspective.
- **What the app could do with it:** (1) [INT-24 camera-transition-interp]: animate camera position/focal-point between view presets over ~300ms using a `QPropertyAnimation` on a custom `QObject` subclass that wraps VTK camera position — when the user clicks Front, Top, Side, or Isometric, the camera smoothly interpolates rather than snapping. (2) [INT-90 parameter-sweep-animation]: a "sweep" button animates a `QPropertyAnimation` on the slider's `value` property from `minimum()` to `maximum()` over user-configurable N seconds, driving `sliderReleased` at each step — the iconic Dwork ψ → 1 sweep demo. (3) Panel open/close transitions for collapsible group boxes (if superqt's QCollapsible is adopted — it uses QPropertyAnimation internally already).
- **Positioning:** already-in-deps — propose adoption pattern (zero new imports; PySide6.QtCore is already used throughout)
- **Interaction primitives unlocked:** [INT-24 camera-transition-interp], [INT-90 parameter-sweep-animation]
- **Risk flags:** VTK camera is not a QObject — animating it requires a thin mediator `QObject` that writes to `plotter.camera.position` each animation tick and calls `plotter.render()`. Each tick fires `render()` — budget ~16ms per frame for 60fps, or 33ms for 30fps; marching-cubes generators must NOT be triggered in the tick loop (only the camera write + render call). The AI-9 `_computing` guard must stay in place. Easing curve: `QEasingCurve.OutCubic` is the standard desktop-app feel (not `Linear`).
- **App-invariant check:** AI-9 — the `_computing` guard must be respected; camera-animation ticks bypass `_render_current` entirely and call `plotter.render()` directly to avoid re-entrancy. AI-2 safe (no Qt in tests).

---

#### D2. PyVista Plotter.fly_to (already in deps via pyvista)

- **URL:** https://docs.pyvista.org/version/stable/api/plotting/_autosummary/pyvista.Plotter.fly_to.html
- **Version:** pyvista ≥ 0.46 (already pinned)
- **License:** MIT (already in requirements.txt)
- **PySide6 compatibility:** N/A — PyVista is not a Qt library; `fly_to` is a VTK-level camera animation that runs in the VTK render loop regardless of Qt binding.
- **Maintenance signal:** Already a dep; pyvista 0.48.4 is current.
- **What the app could do with it:** `fly_to(point, duration=0.3)` animates the camera to look at a given point in 3D space. Useful for "focus on origin" or "focus on surface centroid" actions. More limited than QPropertyAnimation: it only controls the focal point, not full camera pose (position + up vector + focal point).
- **Positioning:** already-in-deps — propose adoption pattern (currently unused; the app uses `reset_camera()` which is instantaneous)
- **Interaction primitives unlocked:** [INT-24 camera-transition-interp] (limited — focal-point only, not full pose)
- **Risk flags:** `fly_to` runs synchronously in the VTK event loop — it blocks Qt's event processing during the animation duration. For durations ≤ 300ms this is acceptable but must be validated on Apple Silicon (some VTK builds run the animation loop at lower cadence). The AI-9 `_computing` guard should be set during `fly_to` to prevent slider re-entrancy if duration > 100ms. Less expressive than QPropertyAnimation D1 for full pose transitions.
- **App-invariant check:** AI-9 — set `_computing = True` during any `fly_to` call that exceeds ~100ms. AI-2 safe.

---

### Category E — PyVista / VTK Ecosystem

---

#### E1. MeshIO

- **URL:** https://github.com/nschloe/meshio
- **Version:** 5.3.5 (released 2024-01-31)
- **License:** MIT
- **PySide6 compatibility:** Not a Qt library — pure Python + NumPy I/O. No compatibility concern.
- **Maintenance signal:** 2.3k GitHub stars. 81 releases, 3,577 commits. Last release Jan 2024 (~16 months before this survey) — slower cadence recently. The maintained subset (STL/OBJ/PLY/VTK) is stable; the exotic format codecs may drift.
- **What the app could do with it:** Implement [INT-93 mesh-export-button] in `view_panel.py`: a "Export mesh…" button opens a `QFileDialog`, lets the user pick format (STL / OBJ / PLY / VTU), and calls `meshio.write(path, meshio.Mesh(...))` after converting the current PyVista PolyData to MeshIO's format. Supports all the formats that researchers use in Blender / Meshmixer / Gmsh. PyVista's own `mesh.save("file.stl")` covers the STL case natively (no new dep), but OBJ and PLY via MeshIO is cleaner than the PyVista path for those formats.
- **Positioning:** adopt-as-import for multi-format export; OR defer to `pyvista.PolyData.save(path)` for STL-only (no new dep at all)
- **Interaction primitives unlocked:** [INT-93 mesh-export-button]
- **Risk flags:** `rich` is a transitive dep of meshio (MIT, ~500 KB) — acceptable. For STL-only export, the zero-dep path (`mesh.save("file.stl")`) is preferable. Only adopt meshio if the brief calls for multi-format export. Last release 16 months ago: file format codecs may lag new format versions, but the core STL/OBJ/PLY paths are stable and unlikely to break.
- **App-invariant check:** AI-2 safe. AI-1 safe. AI-13 irrelevant (meshio is I/O, not colors).

---

#### E2. numpy-stl

- **URL:** https://github.com/WoLpH/numpy-stl/
- **Version:** 3.2.0 (released 2024-11-25)
- **License:** BSD (BSD-3-Clause implied by the project's LGPL-exempt history)
- **PySide6 compatibility:** Not a Qt library — pure Python.
- **Maintenance signal:** 3.2.0 released 2024-11-25. Low star count (not retrievable from PyPI metadata alone) but actively versioned as of late 2024.
- **What the app could do with it:** Lightweight alternative to meshio for STL-only export. Deps: numpy + python-utils. Total overhead ~80 KB. If the only export format needed is STL, this is lighter than meshio. However, PyVista's own `mesh.save("file.stl")` is already present in the dep tree with zero additional pip install — numpy-stl adds a dep that PyVista renders redundant for this specific use case.
- **Positioning:** out-of-scope unless meshio is too heavy — PyVista already covers STL export natively
- **Interaction primitives unlocked:** [INT-93 mesh-export-button] (STL only)
- **Risk flags:** redundant with `pyvista.PolyData.save("*.stl")` which is already in requirements. Do not add a new dep for a capability the existing dep provides.
- **App-invariant check:** AI-2 safe. AI-1 safe.

---

### Category F — Math Typography

---

#### F1. KaTeX via QtWebEngineWidgets

- **URL:** https://katex.org/ | https://cdn.jsdelivr.net/npm/katex@latest/
- **Version:** 0.16.x (CDN latest; exact version pinned at bundle time)
- **License:** MIT
- **PySide6 compatibility:** `QtWebEngineWidgets` is part of `PySide6-Addons`, which ships as a required sub-dependency of the top-level `PySide6` meta-package (see agent-memory lesson). Any app already pinning `PySide6>=6.6` has QtWebEngineWidgets installed — no additional pip install needed.
- **Maintenance signal:** KaTeX is maintained by Khan Academy; active. The CDN approach (inline HTML + `<script src="cdn">`) works in `QWebEngineView` with network access, but for offline reliability the KaTeX assets should be bundled locally (one-time `npm install katex` → copy dist/ assets). KaTeX is faster-startup than MathJax and renders identically across environments.
- **What the app could do with it:** Implement [INT-95 katex-tooltip-popover]: when the user hovers over a variety or subtype name in the combo box (or presses a dedicated "?" button), a small `QWebEngineView` popup window renders the equation in LaTeX-quality typography. This is dramatically better than the current unicode-subscript tooltips (`n₁`, `n₂`, `φ`, `ψ`) for readers who want publication-quality equation display. The popup is a floating `QDialog` or `QToolTip`-replacement — not embedded in a dock.
- **Positioning:** adopt-as-import (zero new pip installs; KaTeX JS bundled from CDN or local copy); the `QtWebEngineWidgets` import is already available in the installed `PySide6-Addons`
- **Interaction primitives unlocked:** [INT-95 katex-tooltip-popover], [INT-7 tooltip-rich] (replaces plain-text tooltip with rendered math)
- **Risk flags:** `QWebEngineView` startup cost is ~100–300ms on first instantiation (Chromium engine cold-start). Mitigate by pre-constructing the view at app launch and hiding it until needed. CDN dependency requires network — bundle KaTeX locally for offline research use. The Chromium subprocess adds ~50–80 MB to the process memory footprint when the view is active; this is acceptable for a desktop research tool but should be lazy-initialized. macOS notarization and hardened-runtime flags require entitlement for the Chromium subprocess — relevant only if packaging for distribution (Category G).
- **App-invariant check:** AI-2 safe (no Qt in tests). AI-12: KaTeX renders its own contrast — verify the HTML template uses `color: #333333` (matching `COLOR_VALUE`) against a white or `#f0f0f0` background for WCAG AA.

---

#### F2. matplotlib mathtext (already in dep tree transitively)

- **URL:** https://matplotlib.org/stable/api/mathtext_api.html
- **Version:** transitively present (matplotlib ships with scikit-image as optional dep; confirm with `pip show matplotlib` in .venv)
- **License:** PSF-style (BSD-compatible — the "matplotlib license")
- **PySide6 compatibility:** matplotlib ≥ 3.8 ships a Qt6-compatible backend. `matplotlib.mathtext.MathTextParser` can render a LaTeX string to a PNG in memory (no figure window needed) via `parser.to_rgba(expr)`, which returns a NumPy RGBA array convertible to `QImage`/`QPixmap` without spawning a display.
- **Maintenance signal:** matplotlib is the gold-standard scientific Python plotting library. Active, ~20k stars.
- **What the app could do with it:** Render equation strings to `QPixmap` for use in `QLabel` tooltip overlays or a small label widget inside the Parameters panel, showing the active surface's equation inline. Lighter than KaTeX/WebEngine for this use case — no Chromium overhead. Covers a narrower TeX subset (AMS LaTeX math mode only, not full KaTeX coverage) but sufficient for the algebraic-variety equations in use.
- **Positioning:** vendor-copy-of-a-pattern (use `matplotlib.mathtext` as a rendering utility, not as a plotting backend — do NOT import `matplotlib.pyplot` which triggers the plotting stack anti-pattern AI-1 warns about). Confirm matplotlib is transitively present before proposing as a zero-new-dep approach.
- **Interaction primitives unlocked:** [INT-95 katex-tooltip-popover] (lighter-weight alternative), [INT-7 tooltip-rich]
- **Risk flags:** matplotlib is NOT in requirements.txt — if it is only a transitive dep of scikit-image, future scikit-image versions may drop it. Pinning matplotlib explicitly as a dep solely for mathtext rendering is justified only if KaTeX/WebEngine is too heavy. Confirm transitive status before committing to this path. The `mathtext` rendering API is considered semi-internal by matplotlib maintainers — the `parser.to_rgba()` method works but is not the public surface. Prefer KaTeX for a production-quality tooltip; use matplotlib mathtext only if QtWebEngineWidgets has a system-level blocker.
- **App-invariant check:** AI-1: do NOT import `matplotlib.pyplot`, `matplotlib.axes`, or any `mpl_toolkits` — use only `matplotlib.mathtext.MathTextParser`. AI-2 safe if confined to mathtext only.

---

### Category G — Packaging

---

#### G1. Briefcase (BeeWare)

- **URL:** https://briefcase.readthedocs.io/
- **Version:** 0.4.2 (released 2026-05-06)
- **License:** BSD-3-Clause
- **PySide6 compatibility:** Briefcase supports PySide6 as a GUI backend via the `beeware` template; PySide6 apps are explicitly in its documentation. Python 3.10–3.14 supported.
- **Maintenance signal:** 0.4.2 released 2026-05-06 (very recent). BeeWare project is active. BSD-3-Clause — clean.
- **What the app could do with it:** Package the app as a native `.app` (macOS), `.msi` (Windows), or `.deb` (Linux) without requiring users to install Python. Briefcase handles PySide6 wheel inclusion and native packaging conventions (macOS `Info.plist`, notarization hooks, etc.) more cleanly than PyInstaller for Qt apps.
- **Positioning:** adopt-as-import only if distribution becomes a goal; out of scope for the current panel-chrome uplift sprint
- **Interaction primitives unlocked:** None in the UI vocabulary — this is a distribution concern only
- **Risk flags:** VTK/PyVista C-extension wheels must be available for the target platform via PyPI; the AArch64 + x86_64 macOS universal wheel situation for VTK is not always clean. The macOS notarization requirement for the Chromium subprocess (if KaTeX/QtWebEngineWidgets is adopted) adds entitlement complexity. Briefcase 0.4.x does not yet support iOS/Android for desktop Qt apps — irrelevant here but worth knowing.
- **App-invariant check:** AI-2 safe (packaging is build-time, not runtime). Briefcase does not affect the test suite.

---

#### G2. PyInstaller

- **URL:** https://www.pyinstaller.org/
- **Version:** 6.20.0 (released 2024-04-22)
- **License:** GPL-2.0-or-later with a special exception that allows bundling non-free programs — effectively redistribution-safe for this app
- **PySide6 compatibility:** PyInstaller 6.x has PySide6 hooks. The license exception specifically permits bundling PySide6 (LGPL) and commercial code.
- **Maintenance signal:** Active, 6.20.0 is current. Widely used for Qt6/PySide6 bundling.
- **What the app could do with it:** Single-executable or single-folder bundle of the app. Older and better-tested for PySide6 + VTK bundles than Briefcase in 2026.
- **Positioning:** design-pattern lift only for now — relevant only if CONTEXT.md §9 "no distribution" policy changes
- **Interaction primitives unlocked:** None in UI vocabulary
- **Risk flags:** GPL-2.0-or-later (with exception) — the exception is widely cited as redistribution-safe but is not OSI-certified. If the app is ever to be distributed commercially, get legal review on the exception wording. PyInstaller bundles tend to be 150–250 MB for Qt6 + VTK apps on macOS.
- **App-invariant check:** AI-2 safe.

---

## 3. Sources Reviewed

| Library | URL | License | PySide6-compat | Stars | Last release | Recommended tier |
|---|---|---|---|---|---|---|
| superqt | https://github.com/pyapp-kit/superqt | BSD-3-Clause | Explicit: `pyside6>=6.4.0` in extras | 288 | 2026-05-18 | ADOPT |
| qtawesome | https://github.com/spyder-ide/qtawesome | MIT | Fixed PySide6 6.8.x segfaults in v1.4.1 (2026-01); tested Qt6 in CI | 930 | 2026-04-10 | ADOPT |
| pyqtdarktheme-fork | PyPI: pyqtdarktheme-fork | MIT | PySide6 demo code in docs; Python 3.8–3.14 tested | ~746 (orig) | 2026-03-04 | ADOPT |
| PySide6-QtAds | https://github.com/mborgerson/pyside6_qtads | LGPL-2.1 | PySide6-native; requires PySide6-Essentials==6.11.0 exact | 40 | 4.5.0.4 | WATCH (version-lock risk) |
| qt-material | https://github.com/dunderlab/qt-material | BSD-2-Clause | PySide6 demo code in docs | 72 | 2025-04-21 | SKIP (low stars; stale) |
| QPropertyAnimation | https://doc.qt.io/qtforpython-6/PySide6/QtCore/QPropertyAnimation.html | LGPL-2.1 | Native PySide6 | — | N/A (Qt 6.6) | ADOPT (already-in-deps) |
| Plotter.fly_to | https://docs.pyvista.org | MIT | N/A (PyVista, not Qt) | — | 0.48.4 | ADOPT (already-in-deps) |
| MeshIO | https://github.com/nschloe/meshio | MIT | N/A (not Qt) | 2,300 | 2024-01-31 | ADOPT IF multi-format export |
| numpy-stl | https://github.com/WoLpH/numpy-stl/ | BSD-3-Clause (BSD) | N/A (not Qt) | — | 2024-11-25 | SKIP (redundant with PyVista) |
| KaTeX via QtWebEngineWidgets | https://katex.org/ | MIT | Via PySide6-Addons (zero new install) | — | 0.16.x | ADOPT (no new dep) |
| matplotlib mathtext | https://matplotlib.org/ | PSF/BSD-compatible | Transitive only; confirm presence | ~20k | — | WATCH (confirm transitive) |
| pymeshfix | https://github.com/pyvista/pymeshfix | AGPL-3.0 | N/A (not Qt) | — | 0.18.1 | BLOCK (AGPL-3.0) |
| Briefcase | https://briefcase.readthedocs.io/ | BSD-3-Clause | PySide6 explicitly supported | — | 2026-05-06 | PARKING LOT (future dist) |
| PyInstaller | https://www.pyinstaller.org/ | GPL-2.0+exception | PySide6 hooks in v6.x | — | 2024-04-22 | PARKING LOT (future dist) |

---

## 4. Themes

**superqt is quietly closing the gap the app's custom panel code opens.** The app manually constructs per-slider label layouts (`RANGE_LABEL_STYLE` spans), wires `sliderReleased` individually, and has no collapsible section for the parameter list — all three are addressed by `QCollapsible`, `QLabeledSlider`, and `superqt.signals.throttled` as stock features. This is the clearest single-library "stop writing boilerplate, start adopting it" opportunity in the current codebase.

**The icon gap is acute on both viewport and chrome findings.** The Tier-1 panel captures will show that every button in ViewPanel and ParametersPanel is text-only — no icons. qtawesome's MIT license, PySide6 6.8.x segfault fix (Jan 2026), and 930-star signal make it the obvious zero-friction solution, with the cold-boot cost the only operational concern (mitigatable by lazy import).

**The theming gap is a latent, not yet visible problem.** The app is light-only today and intentionally so — but the math-research audience (3Blue1Brown / Quanta-register) skews toward dark tools. pyqtdarktheme-fork is the only candidate with a live maintenance signal, verified PySide6 6.6+ support, and a runtime-switching API. The original `pyqtdarktheme` package is abandoned; any proposal citing it should be re-routed to the fork.

**The math-typography opportunity is uniquely cheap.** KaTeX via `QtWebEngineWidgets` costs zero new pip installs (the Chromium engine ships with PySide6-Addons, which is already installed). The main cost is implementation effort and the Chromium cold-start on first popup — not a dependency budget concern.

---

## 5. The App Already Has

Libraries in `requirements.txt` that appear in the candidate field:

- **PySide6 ≥ 6.6, < 7** — already adopted; `QPropertyAnimation` + `QParallelAnimationGroup` (Category D1) are bundled and available at zero new cost. EXPAND: wire camera-transition interpolation [INT-24] and parameter-sweep animation [INT-90] using already-available classes in `PySide6.QtCore`.
- **pyvista ≥ 0.46, < 0.49** — already adopted; `Plotter.fly_to` (Category D2) is unused today. EXPAND: add a "fly to surface centroid" action in `view_panel.py`. Current pin (`<0.49`) is sound — 0.48.4 is the latest stable, 0.49 does not yet exist. WATCH: widen to `<0.50` when 0.49 ships.
- **pyvistaqt ≥ 0.11.4, < 0.12** — already adopted; `QtInteractor` carries a native `screenshot()` method. No upgrade needed; 0.11.4 is the current PyPI release (2026-04-03).
- **scikit-image ≥ 0.22, < 0.27** — already adopted; `measure.marching_cubes` API is stable. No upgrade signal.
- **numpy ≥ 1.26, < 3** — already adopted; no candidate depends on a newer NumPy.

No library in `requirements.txt` should be proposed as a "new" candidate. The above are already-in-deps EXPAND/UPGRADE opportunities only.

---

## 6. Out of Scope / Parking Lot

| Library | Reason not surfaced |
|---|---|
| **pymeshfix** | AGPL-3.0 license — import into redistributable binary is a MAJOR flag; blocks adoption under any open-distribution model |
| **PyQtGraph** | MIT, PyQt/PySide compatible, but scoped to 2D companion plot use only (source-registry §2 note). No 2D plot is in-scope for this panel-chrome uplift |
| **trame** | Apache-2.0 and relevant for web-companion, but the app is desktop-only; trame would require a full architecture pivot away from `QMainWindow`. Out of scope. |
| **MathJax v4** | Apache-2.0 but heavier than KaTeX (~500 KB bundle vs KaTeX ~280 KB), slower render, identical coverage for this app's equations. KaTeX is the right call. |
| **qframelesswindow** | Dual-licensed LGPL-3.0 / GPL-3.0 depending on variant; the frameless-window aesthetic conflicts with the app's research-tool identity and with macOS native window management. |
| **PyQtFluent-Widgets / qfluentwidgets** | GPL-3.0 (community edition) — MAJOR license flag for redistribution. Study-only at best; vendor-copy of small primitives requires verifying each snippet's license independently. |
| **QScintilla** | GPL-3.0 (or commercial) — equation entry isn't in scope for this sprint. |
| **cibuildwheel** | Build infra, not a runtime lib; out of scope until distribution is a goal. |
| **uv / Poetry** | Dependency management tooling, not a runtime dep; out of scope. |
| **pre-commit / ruff** | Dev tooling; out of scope for a UI uplift brief. |
| **imageio / Pillow** | Transitively present via scikit-image; no new capability for the panel-chrome surface. |
| **SymPy** | BSD-3-Clause, but its only role here would be LaTeX-string generation for KaTeX — the equations are already known strings, not derived symbolically. Over-engineered for this sprint. |
