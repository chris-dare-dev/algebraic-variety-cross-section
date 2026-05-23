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
app.py                   Entry point and main window (~1900 LOC — God Object, do not Extract Class here)
surfaces.py              Surface registry + mesh generators (~1811 LOC)
appearance_panel.py      Appearance controls panel
parameter_grid_panel.py  Parameter-grid interactive panel
parameters_panel.py      Surface-parameter sliders panel
view_panel.py            3-D viewport + clip controls
render_worker.py         QThread worker for off-thread mesh computation
parameter_grid.py        Draggable-dot grid widget
styles.py                QSS stylesheets (light + dark modes, WCAG AA palette)
icons.py                 qtawesome icon helpers
ui_helpers.py            Misc Qt helpers
tests/                   Flat test layout — 499 tests, all Qt-free
requirements.txt         Runtime + restructure-tooling pins
```

Deep-dive: CONTEXT.md §4 (Module map), §5 (Panel inventory)

---

## 3. Build and test commands

```bash
# Run the app
python app.py

# Run the full test suite (expected: 499 tests, ~7 s on Apple Silicon)
python -m pytest -q

# Run a single test file
python -m pytest tests/test_surfaces.py -q

# Smoke-test imports (no Qt required)
python -c "import surfaces; print('OK')"
python -c "import styles; print('OK')"
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
  hardcode hex values directly in `setStyleSheet` calls. See `styles.py` for
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
