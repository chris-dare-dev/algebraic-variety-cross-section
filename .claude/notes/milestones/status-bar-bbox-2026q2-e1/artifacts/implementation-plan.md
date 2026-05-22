# Implementation plan — status-bar-bbox-2026q2-e1

**Inline path. ~9 LOC across 3 files.** Append spatial bbox readout to the status bar after every successful render, per roadmap epic `panel-refresh-2026q2-e5` (UPL-13). Researcher confirmed exact insertion point at `app.py:433` and that the symmetric-sampling-box assumption holds for 12/13 generators (Hanson parametric is the lone near-symmetric exception, documented in CONTEXT.md §4).

1. **app.py** — In `_render_current`, just before the existing `base_msg` f-string at line 433, add `_b = self._raw_mesh.bounds`. Extend the `base_msg` with one extra f-string fragment `f"  ·  bbox ±{_b[1]:.2f} × ±{_b[3]:.2f} × ±{_b[5]:.2f}"`. The insertion is inside the success branch only — the `except ValueError` / `except Exception` paths at lines 400–415 do not reach this code (already AI-14 compliant: they call `showMessage` with the error message and return). ~3 LOC.

2. **tests/test_status_bar_bbox.py** — New pure-PyVista regression test file. Test 1: call `fermat_quartic()` at defaults, format the bbox string with the same `±{b[1]:.2f} × ±{b[3]:.2f} × ±{b[5]:.2f}` formula, assert via `re.fullmatch(r"bbox ±\d+\.\d+ × ±\d+\.\d+ × ±\d+\.\d+", result)`, and that all three max-extents are positive. Test 2: call a generator at a known-invalid parameter (Kummer with `mu_squared=0.2`) and assert it raises `ValueError` cleanly — supports the AI-14 claim that the error path cannot produce a bbox string. No `MainWindow`, no `QApplication` — AI-2 compliant. ~25 LOC.

3. **CONTEXT.md** — Add a §4 forward-maintenance note explaining: (a) status-bar format `bbox ±a × ±b × ±c` after every successful render; (b) `±max` is an exact half-width for the 12 generators using `np.linspace(-bounds, bounds, n)` symmetric sampling; (c) Hanson parametric is an honest over-approximation (`theta ∈ [0, π/2]`, α=π/4 averaging produces near-symmetric Z-bounds at defaults); (d) if a future generator uses a non-centered sampling domain, extend to `xmin..xmax × ymin..ymax × zmin..zmax`. ~6 LOC.

4. **Verify** —
   - `pytest tests/ -q` stays at 290.
   - Off-screen render verification per CONTEXT.md §10 is NOT required (no generator or render-pipeline change; only a status-bar string extension).
   - Optional sanity: launch app in foreground mode briefly to eyeball the new readout (out-of-scope for the pipeline; manual user test).

5. **Commit** — `feat(status-bar-bbox-2026q2-e1): append bbox ±a × ±b × ±c to status bar after every successful render`.
