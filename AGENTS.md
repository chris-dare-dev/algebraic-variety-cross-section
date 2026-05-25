# AGENTS.md — AI-agent orientation for algebraic-variety-cross-section (AVC)

> Short orientation for AI coding agents. For the authoritative deep context,
> read **CONTEXT.md** (sections linked below).

---

## 1. Project overview

AVC is a desktop visualiser for algebraic varieties (implicit-surface and
parametric-surface families). It renders cross-sections using marching cubes
or structured grids (depending on surface type) and displays them in an
interactive 3-D viewport.

**Stack:** Python 3.12 · PySide6 (Qt 6) · PyVista / pyvistaqt · Numba · NumPy

Deep-dive: CONTEXT.md §1 (Purpose), §2 (Architecture), §3 (Data flow)

---

## 2. Where things live

```
app.py                         Entry point and main window (~1900 LOC — God Object, do not Extract Class here)
_qt/                           Qt-layer subpackage (icons, styles, ui_helpers, panels)
  _qt/icons.py                 qtawesome icon helpers
  _qt/styles.py                QSS stylesheets (light + dark modes, WCAG AA palette)
  _qt/ui_helpers.py            Misc Qt helpers
  _qt/parameter_grid_math.py   Pure-math coordinate math for grid mode (moved from root in restructure-single-root-2026q2-r3 batch 2)
  _qt/panels/                  UI panel subpackage
    _qt/panels/appearance.py         Appearance controls panel (AppearancePanel)
    _qt/panels/parameter_grid_panel.py  Parameter-grid interactive panel (ParameterGridPanel)
    _qt/panels/parameters.py         Surface-parameter sliders panel (ParametersPanel)
    _qt/panels/view.py               3-D viewport + clip controls (ViewPanel)
render/worker.py               QThread worker for off-thread mesh computation
cross_section/clip.py          Domain-clip pure function (clip_to_domain)
varieties/                     Surface registry + mesh generators
  varieties/types.py           Surface + ParamSpec dataclasses; VarietyGenerator(Protocol)
  varieties/registry.py        VARIETIES registry dict
  varieties/dispatch.py        dispatch_mode, should_render_on_drag, FAST_RENDER_THRESHOLD_MS
  varieties/tooltips.py        VARIETY_TOOLTIPS, SUBTYPE_TOOLTIPS
  varieties/k3.py              K3 generators (fermat_quartic, kummer_surface)
  varieties/enriques.py        Enriques generators (4 figures)
  varieties/calabi_yau.py      Calabi-Yau generators (4 figures)
  varieties/fano.py            Fano 3-fold generators (4 figures)
  varieties/_kernels.py        Numba @njit field kernels for all 11 implicit generators
  varieties/_marching.py       Marching-cubes + grid pipeline helpers
tests/                         Flat test layout — 504 tests, all Qt-free
  tests/test_import_smoke.py   Subprocess smoke tests (5 entries: varieties, render, _qt, cross_section, app)
requirements.txt               Runtime + restructure-tooling pins (includes import-linter>=2.0,<3)
pyproject.toml                 [tool.importlinter] section: 2 forbidden contracts enforcing layer direction
```

Post-r3 state: `app.py` is the ONLY `.py` file at the repo root (single-root invariant). All other
modules live in subpackages: `_qt/`, `render/`, `cross_section/`, `varieties/`. Layer direction is
enforced by import-linter contracts in `pyproject.toml`.

Note: All root-level shims from r1 + r2 have now been removed:
- r2 batch 1 closed M+1 cycle for r1 panel shims (appearance_panel.py, view_panel.py, parameters_panel.py, parameter_grid_panel.py)
- r3 batch 3 closed M+1 cycle for r2 Qt shims (icons.py, styles.py, ui_helpers.py, render_worker.py, panels/__init__.py)
- r3 batch 4 retired surfaces.py (123-LOC re-export hub, down from 1811 LOC pre-r2)
The canonical paths for all moved symbols are in MOVES.md (the full r1->r2->r3 rosetta stone).

Deep-dive: CONTEXT.md §4 (Module map), §5 (Panel inventory)

---

## 3. Build and test commands

```bash
# Run the app
python app.py

# Run the full test suite (expected: 504 tests, ~7 s on Apple Silicon)
python -m pytest -q

# Run a single test file
python -m pytest tests/test_mesh_generators.py -q

# Smoke-test imports (no Qt required)
python -c "from varieties.registry import VARIETIES; print('OK')"
python -c "from _qt.styles import APP_STYLESHEET; print('OK')"

# Verify import-linter layer contracts (expects 2 contracts KEPT)
lint-imports
```

No build step required — pure-Python project; no `pip install -e .` needed to
run tests (flat-path imports work from the repo root).

Deep-dive: CONTEXT.md §10 (Running the project)

---

## 4. AI-invariants (AI-1 .. AI-15)

There are 15 hard invariants that MUST NOT be violated. Violating any one
can silently corrupt renders or break Qt event handling.

Critical invariants for day-to-day edits:

| # | Rule |
|---|------|
| AI-2 | Tests are Qt-free — never construct `QApplication` or any `QWidget` subclass inside `tests/` |
| AI-6 | Implicit surfaces → marching cubes; parametric surfaces → structured grid. NEVER mix. |
| AI-9 | Re-entrancy guard `self._computing` in `app.py` — never remove or bypass it |
| AI-11 | Always use fully-qualified Qt enums: `Qt.AlignmentFlag.AlignLeft`, NOT `Qt.AlignLeft` |
| AI-12 | WCAG AA contrast on all visible text — no hardcoded palette colours in stylesheets |
| AI-15 | Math-honest tooltips — surface tooltips must cite a source or note the formula is approximate |

Full table: CONTEXT.md §11 (AI invariants)

---

## 5. Code style

- **Python 3.12** — use `match/case` where natural; f-strings preferred.
- **Qt enums fully-qualified** (AI-11 above). Grep for bare `Qt.Align` / `Qt.Key` etc. and fix.
- **No star-imports** anywhere in production code.
- **Stylesheet colours** via QSS palette roles (e.g. `palette(window)`) — never
  hardcode hex values directly in `setStyleSheet` calls. See `_qt/styles.py` for
  the palette + WCAG notes.
- **Type hints** on new public functions; not required on private helpers.
- **Line length:** 100 chars (no hard linter; be reasonable).

---

## 6. Testing

- All tests live in `tests/` (flat layout).
- Tests are **Qt-free** (AI-2). Importing a panel class is fine; instantiating
  it (`AppearancePanel()`) requires a `QApplication` — do not do this in tests.
- Run `python -m pytest -q` after every change. Aim for zero new failures.
- Coverage is tracked with `coverage` (see requirements.txt). Do not worry
  about coverage deltas in routine edits; the restructure pipeline handles
  coverage parity separately.

---

## 7. Security considerations

- AVC is a local desktop app with no network access and no user-provided
  data paths. There are no auth secrets, API keys, or credentials.
- The `tests/` directory should never import or execute `app.py` at module
  scope (it constructs a `QApplication`).
- Do not add `subprocess` calls, file-system watchers, or network I/O without
  a design discussion.

---

## 8. What NOT to touch

| Path | Why off-limits |
|---|---|
| `.claude/` | AI agent scaffold — self-modification trap |
| `.claude/archive/` | **Opt-in-only context graveyard — do NOT auto-read.** Stale notes, superseded plans, retired critiques. Only grep here when the user explicitly references a path or when `MOVES.md` lookup fails. See `.claude/archive/README.md`. |
| `.github/` | CI/CD pipeline — out of scope for source edits |
| `plans/` | Historical design artefacts — read-only |
| `pytest.ini` | Anchor-updater owns this |
| `CONTEXT.md` | Anchor-updater owns restructure-cycle edits |
| `README.md` | Anchor-updater owns restructure-cycle edits |

---

## 9. Asking for context

Before making non-trivial changes, read:
1. **CONTEXT.md §4** — module map (who imports whom)
2. **CONTEXT.md §11** — AI invariants (full table)
3. **CONTEXT.md §13** — known issues / deferred items

If a change looks like it might violate an AI invariant, stop and ask.
