# Adversary critique -- per-axis checklist

Walk this file BEFORE writing findings.  Each axis has concrete checks plus
an anchor example from this repo's documented bugs (CONTEXT.md section 8)
or from the app-invariants list (AI-1..AI-15).  App-invariants and pipeline
discipline go first -- they catch CRITICALs and HIGHs.

> **App invariants AI-1..AI-15**: see `.claude/references/app-invariants.md`
> (full list with rationale, concrete grep patterns, and Challenger
> mapping).  Non-negotiable.  Cite verbatim ("AI-4 -- clip_box ban"), not
> in prose.

---

## 1. App invariant violations (AI-1..AI-15)

**Typical severity: HIGH or CRITICAL.**

**Concrete checks:**

- New import of `mayavi`, `matplotlib.mpl_toolkits.mplot3d`, `plotly`, `k3d`, or `vtk` directly (bypassing PyVista)?  AI-1, CRITICAL.
- New test under `tests/` that imports `pytest_qt` or `pytestqt`?  AI-2, HIGH (the macOS Qt+VTK offscreen segfault is documented in CONTEXT.md section 10).
- Construction of `MainWindow()` under `QT_QPA_PLATFORM=offscreen` (in a test, in a script, in a render-verify pattern)?  AI-3, CRITICAL.
- New call to `mesh.clip_box(invert=...)` on a PolyData?  AI-4, HIGH (commit `b68456f` documents the broken invert semantics).
- New call to `mesh.clip_scalar(...)` without `scalars=` kwarg?  AI-5, HIGH (silent warning today, hard error in pyvista 0.49+).
- Hanson generator changed to `consistent_normals=True` or `auto_orient_normals=True`?  AI-7, HIGH (regresses commit `f58ee05`).
- New `processEvents()` call lacking the `self._computing` guard?  AI-9, HIGH.
- Domain-clip change that regenerates the mesh (calls `surface.generate()`) instead of reusing `self._raw_mesh`?  AI-10, MEDIUM/HIGH.
- New code using shorthand Qt enums (`Qt.AlignLeft`, `QSizePolicy.Expanding`)?  AI-11, MEDIUM (deprecation warning today, hard error in future PySide6).
- New text color without a cited WCAG AA contrast ratio?  AI-12, MEDIUM (HIGH if it's actually below 4.5:1 on body text).
- 3-digit hex (`#888`) anywhere flowing into PyVista?  AI-13, HIGH (cryptic error at runtime).
- Generator that returns something other than `pv.PolyData` or raises something other than `ValueError`/`RuntimeWarning`?  AI-14, HIGH.
- New variety / figure without >=2 sources cited and without an honest "real shadow"/"birational"/"parametric cross-section" tooltip?  AI-15, HIGH.

**Anchor (Barth icosahedral mis-attribution, CONTEXT.md section 5.2):** The
original Figure 4 docstring claimed `tau=1` reproduces Barth's classical
65-nodal sextic.  Adversarial review caught the error -- Barth uses
`(x^2+y^2+z^2)^2`, this code uses `(r^2-1)^2`.  The Endrass-normalized form
is what we plot.  Use `grep -n "Barth" surfaces.py` and verify every match
either says "Endrass-normalized" or "NOT Barth's classical".

---

## 2. Pipeline discipline (AI-6, AI-7)

**Typical severity: HIGH.**

Implicit and parametric pipelines are different and must not mix.

**Concrete checks:**

- New implicit-surface generator that skips `_marching_cubes_to_polydata` and calls `skimage.measure.marching_cubes` directly?  AI-6, MEDIUM (loses the zero-crossing pre-check, the Taubin smoothing, and the gradient normals).
- New parametric generator that goes through `_marching_cubes_to_polydata`?  AI-6, HIGH (no scalar field to march on).
- Parametric generator that calls `smooth_taubin(...)` after `_concat_polydata`?  AI-6, HIGH (smears patch boundaries; Hanson grid is already C^2).
- Generator that uses `_grid_to_polydata` without `_concat_polydata` for multi-patch surfaces?  MEDIUM (each patch becomes a disconnected component anyway -- this is fine -- but the normal mode must match per AI-7).
- Hanson normal mode regressed to `consistent_normals=True, auto_orient_normals=True`?  AI-7, HIGH (per-patch lighting flips).

**Anchor (CONTEXT.md section 4.2):** `_marching_cubes_to_polydata` runs a
fixed sequence: zero-crossing pre-check -> `marching_cubes` with
`gradient_direction` -> `mesh.clean()` -> `smooth_taubin(n_iter=20,
pass_band=0.1)` -> `compute_normals()`.  Skipping any of these breaks
parity with the existing K3/Enriques/Dwork generators.  Use
`grep -n "_marching_cubes_to_polydata\|skimage.measure.marching_cubes"
surfaces.py` -- the bare skimage call should only appear inside the helper.

---

## 3. VTK / PolyData ownership (AI-4, AI-5, AI-10, AI-14)

**Typical severity: HIGH or MEDIUM.**

PolyData ownership semantics in VTK are subtle; PyVista wraps them.  Bugs
here look like "mesh has zero vertices" or "domain slider does nothing".

**Concrete checks:**

- `clip_box` on PolyData? AI-4, HIGH (use scalar clip with Chebyshev distance for cube mode).
- `clip_scalar` without `scalars=` keyword? AI-5, HIGH.
- New domain-clip path that calls `surface.generate(**kwargs)` instead of operating on `self._raw_mesh`?  AI-10, MEDIUM (breaks the snappy radius-slider feel; regenerates ~500 ms of mesh on every drag).
- Generator that raises something other than `ValueError("No real zero set in the sampling box for these parameters. ...")` for an empty field?  AI-14, HIGH (`MainWindow._render_current` catches `ValueError` specifically and surfaces the message in the status bar; other exceptions propagate and crash).
- Generator that prints to stdout or calls `sys.exit`?  AI-14, HIGH.
- `RuntimeWarning` emitted without going through `warnings.warn(..., RuntimeWarning)`?  AI-14, MEDIUM (`MainWindow._render_current`'s `catch_warnings` only catches the proper warning protocol).

**Anchor (CONTEXT.md section 8.2):** `mesh.clip_box(bounds, invert=False)`
returned 0 vertices; `invert=True` returned the full mesh.  Both wrong.
Fix in commit `b68456f`: use scalar clip with Chebyshev `max(|x|,|y|,|z|)`
distance.  Verify by greping `grep -n "clip_box" view_panel.py surfaces.py`
-- should return empty after the fix.

---

## 4. Qt re-entrancy and event loop (AI-9)

**Typical severity: HIGH.**

`QApplication.processEvents()` drains the Qt event queue; this can re-enter
the calling function via slider-release -> `_on_params_changed` ->
`_render_current`.  Without a guard, `self._raw_mesh` corrupts and actors
dangle.

**Concrete checks:**

- New `processEvents()` call?  Is the surrounding scope guarded by `if self._computing: return` at the top and `self._computing = True` set before `processEvents`, cleared in a `finally`?
- New synchronous I/O (file write, network call) inside a slot that also calls `processEvents`?  Slow I/O extends the re-entrancy window.
- New blocking `QDialog.exec()` while `self._computing` is True?  The modal blocks the event loop AND the guard is still set -- combined, the app can deadlock.

**Anchor (CONTEXT.md section 8.5):** Re-entrancy from
`QApplication.processEvents` in `_render_current` corrupted `_raw_mesh` and
dangled actors.  Fix: `self._computing = True` at the top, cleared in
`finally`.  Verify with `grep -n "processEvents\|_computing" app.py` --
every `processEvents` call site should be inside a `_computing = True`
block.

---

## 5. Color / contrast / token discipline (AI-11, AI-12, AI-13)

**Typical severity: MEDIUM (HIGH if WCAG AA fail on body text).**

`styles.py` is the centralized stylesheet.  Token discipline matters
because the same constants ship to Qt stylesheets AND to PyVista
`add_mesh(color=...)` calls.

**Concrete checks:**

- Inline `Qt.AlignLeft`, `Qt.AlignRight`, `Qt.AlignCenter`, `QSizePolicy.Expanding`, `QSizePolicy.Fixed`, `QSizePolicy.Minimum` etc. in new code?  AI-11, MEDIUM.
- New `COLOR_*` constant or new f-string in `styles.py` without a cited WCAG AA ratio in a comment?  AI-12, MEDIUM (HIGH if the actual ratio is below 4.5:1 against the documented background).
- 3-digit hex (`#888`, `#abc`) ANYWHERE in code that flows into PyVista?  AI-13, HIGH.
- 3-digit hex in Qt stylesheet text?  AI-13, MEDIUM (Qt accepts it but mixing short/long across stylesheets is a smell).
- New color literal not in `styles.py`?  MEDIUM (the centralized stylesheet is the source of truth).

**Anchor (CONTEXT.md section 8.3):** PyVista's color parser rejected
`#888` with a cryptic error; everything must be 6-digit hex.  Use
`grep -nE '#[0-9a-fA-F]{3}([^0-9a-fA-F]|$)' styles.py app.py surfaces.py
appearance_panel.py view_panel.py parameters_panel.py` -- every match
should be inside a Qt stylesheet string only, never flowing into
`pv.Plotter.add_mesh(color=...)` or `pv.set_plot_theme`.

---

## 6. Math claim honesty (AI-15)

**Typical severity: HIGH.**

This repo's epistemic stance is that we plot real shadows / birational
models / parametric cross-sections, NOT the abstract varieties they're
named after.  Tooltips must be honest about this.

**Concrete checks:**

- New variety / figure whose tooltip says "this is the X variety" without a "real shadow" / "birational to" / "parametric cross-section" disclaimer?  AI-15, HIGH.
- New variety / figure docstring citing fewer than 2 sources?  AI-15, HIGH (Wikipedia + MathWorld + arXiv + classical text is the bar).
- New variety / figure citing a source that's actually wrong (e.g., attributing the Endrass-normalized icosahedral sextic to Barth without qualification)?  AI-15, HIGH.
- Non-compactness warning missing on a parameter range that lets the surface go non-compact (e.g., Fermat alpha < -1)?  AI-15, MEDIUM (the surface still renders but no longer is what it claims to be).
- Hanson docstring uses superscript `n^2` (U+00B2) where subscript `n_2` (U+2082) is meant?  AI-15, MEDIUM (the adversarial reviewer of the CY3 pass caught a `(n, n^2) = (5, 5)` line that implied 5^2 = 5).

**Anchor (CONTEXT.md section 5.2 Figure 4):** The Endrass-normalized
icosahedral sextic was originally attributed to "Barth's classical
65-nodal sextic" -- adversarial review caught the misattribution because
Barth uses `(x^2+y^2+z^2)^2` while this code uses `(r^2-1)^2`.  Docstring
was rewritten to honestly describe this as "Endrass-normalized variant,
NOT Barth's classical surface".  Don't repeat that misattribution.

---

## 7. Test coverage gap

**Typical severity: MEDIUM (HIGH for missing tests on a new generator).**

This repo's tests are Qt-free (AI-2).  The bar is:
- New generator -> smoke test in `tests/test_mesh_generators.py`
- New `ParamSpec` -> tick<->value test in `tests/test_parameters_panel.py:ALL_PARAM_SPECS`
- New clip / domain path -> test in `tests/test_clip_domain.py`
- New `_grid_to_polydata` / `_concat_polydata` use -> coverage in `tests/test_grid_helpers.py`
- New marching-cubes-empty edge case -> coverage in `tests/test_marching_cubes_empty.py`

**Concrete checks:**

- New generator function in `surfaces.py` without an entry in `tests/test_mesh_generators.py`?  HIGH.
- New `ParamSpec` instance without an entry in `tests/test_parameters_panel.py:ALL_PARAM_SPECS`?  MEDIUM.
- New variety added to `VARIETIES` dict without a tooltip in `SUBTYPE_TOOLTIPS`?  MEDIUM.
- New ValueError raise path in a generator without a test that hits the error message?  MEDIUM.
- New RuntimeWarning emit path without a test that confirms the warning fires under the right conditions?  MEDIUM.

**Anchor:** the current suite is 165 tests and ~4 s.  Every variety pass
documented in CONTEXT.md section 6 added tests for its new figures.  A
milestone that adds a figure without tests is reverting from a multi-pass
established pattern.

---

## 8. Off-screen render verification (AI-3)

**Typical severity: HIGH (CRITICAL if the new code segfaults under offscreen Qt).**

Render verification is offscreen via `pv.OFF_SCREEN = True` and
`pv.Plotter(off_screen=True).show(screenshot=...)`.  Constructing
`MainWindow()` under `QT_QPA_PLATFORM=offscreen` segfaults during VTK GL
context creation.

**Concrete checks:**

- New offscreen render path constructs `MainWindow()` or any Qt widget under `QT_QPA_PLATFORM=offscreen`?  AI-3, CRITICAL.
- New script in the repo that renders surfaces but doesn't set `pv.OFF_SCREEN = True` before constructing the plotter?  AI-3, HIGH (will pop up a GUI window in CI).
- New generator without a documented off-screen render check in the milestone artifacts?  MEDIUM (the milestone artifact should include a `/tmp/check-*.png` reference + the Read attestation).

**Anchor (CONTEXT.md section 10):** the documented render-verification
pattern is `pv.OFF_SCREEN = True; pv.Plotter(off_screen=True).show(screenshot="/tmp/check.png")`
followed by Reading the PNG to visually verify.  Anything that bypasses
this (Qt offscreen, direct VTK render window, X11 forwarding) is an AI-3
risk.

---

## 9. Documentation drift

**Typical severity: LOW.**

CONTEXT.md / README.md / `.claude/references/app-invariants.md` are the
canonical sources.  Stale docs are the slowest poison in the codebase.

**Concrete checks:**

- New variety / figure in `VARIETIES` -> row in CONTEXT.md section 1's variety table?  Tooltip entries in `SUBTYPE_TOOLTIPS`?  README "Mathematical scope" section updated?
- New bug fix that's load-bearing for future maintainers -> entry in CONTEXT.md section 8?
- New explicit non-goal -> entry in CONTEXT.md section 9?
- New app invariant discovered or refined -> entry in `.claude/references/app-invariants.md` AI-N?
- New panel pattern (dock layout, slider style, status-bar feedback) -> entry in CONTEXT.md section 4?

**Anchor (CONTEXT.md section 5.2 Figure 4):** the Barth->Endrass
correction was documented in CONTEXT.md section 5.2 with a "Pitfall fixed
mid-build" callout.  Every load-bearing math correction needs that
treatment so the next agent can't repeat it.

---

## 10. Scope discipline (single-developer cadence)

**Typical severity: LOW or MEDIUM.**

CONTEXT.md section 12 documents single-developer, direct-to-`main`
workflow.  The implementer's brief explicitly forbids:
- Defensive error handling for scenarios that can't happen (trust internal code)
- Narrative comments (the WHAT) -- only WHY when non-obvious
- Backwards-compat shims (just change the code)
- Lifting CONTEXT.md section 9 non-goals silently

**Concrete checks:**

- New `try/except` around code that can't actually raise the caught exception?  MEDIUM.
- New `if X is None: raise ValueError("X is None")` immediately after an assignment that can never produce None?  LOW.
- New code path retained behind a feature flag for "backwards compatibility"?  MEDIUM.
- New comment that describes WHAT the code does (e.g., `# Loop over surfaces`)?  LOW.
- New code that introduces QSettings, STL export, first-launch auto-render, or pytest-qt -- all explicit CONTEXT.md section 9 non-goals?  MEDIUM (the fix is to escalate to a separate milestone, not to slip the non-goal lift in).

**Anchor (CONTEXT.md section 9):** the explicit non-goals list exists
because each non-goal was *considered* and *rejected* by prior UI/UX or
adversarial passes.  Lifting one of them is a milestone-scope decision,
not a Phase 2 implementation choice.

---

## After walking the checklist

Sanity-check before drafting:

1. CRITICAL findings meet the bar (panel segfault, AI-1 stack violation, AI-3 offscreen MainWindow, math claim that's actually false)?  If not, demote to HIGH.
2. Five+ HIGHs in a small diff?  Re-audit.  Diffs under 200 LOC rarely produce more than 2-3 genuine HIGHs.
3. "What was done well" has specific bullets?  Empty/generic = critique is incomplete.
4. Every finding cites `file:line`?  Always `surfaces.py:354`, never "the surfaces module is broken".
5. At least one CRITICAL or HIGH has a regression-guard test proposed?  The point of the critique is preventing the bug from coming back.
