# Implementation plan — status-bar-bbox-2026q2-e2

**Inline path. ~50 LOC across 3 files.** Switch status-bar bbox readout from half-extent `±max` to full-extent `size: Lx × Ly × Lz`, closing F-M2 + F-L1 + F-L2 from status-bar-bbox-2026q2-e1. The full-extent format is exact for all 14 generators (no more "honest over-approximation" caveat for the 3 Hanson parametric ones) and aligns with peer scientific-viz tools (ParaView/MeshLab/Blender all use full extents). Precision bumps from `.2f` to `.3f` to avoid false equalities at sub-1.0 extents.

1. **app.py:_render_current** — Three edits to the bbox block:
   - Rename `bbox_suffix` → `size_suffix` (assignment + 2 consumption sites: `base_msg` success path + warning path).
   - Replace f-string `f"bbox ±{_b[1]:.2f} × ±{_b[3]:.2f} × ±{_b[5]:.2f}"` with `f"size: {_b[1]-_b[0]:.3f} × {_b[3]-_b[2]:.3f} × {_b[5]-_b[4]:.3f}"`.
   - Rewrite the inline comment block (the "11 implicit-surface generators with symmetric sampling" / "Hanson over-approximation" framing) to explain full-extent semantics: `Lx = bounds[1] - bounds[0]` etc. is the true diameter, exact for all generators by construction. Update the cross-reference to `CONTEXT.md §4.3`. ~12 LOC delta.

2. **tests/test_status_bar_bbox.py** — Five edits:
   - `BBOX_FORMAT`: `"bbox ±{a:.2f} × ±{b:.2f} × ±{c:.2f}"` → `"size: {a:.3f} × {b:.3f} × {c:.3f}"`.
   - `BBOX_REGEX`: `r"^bbox ±\d+\.\d+ × ±\d+\.\d+ × ±\d+\.\d+$"` → `r"^size: \d+\.\d{3} × \d+\.\d{3} × \d+\.\d{3}$"` (note `\d{3}` not `\d+` to actually enforce the `.3f` contract — researcher caught this).
   - `_format_bbox` helper: read full extent `b[1]-b[0]` / `b[3]-b[2]` / `b[5]-b[4]` instead of `b[1]/b[3]/b[5]`. Rename to `_format_size` for internal consistency.
   - `test_bbox_max_extents_are_positive_for_symmetric_generator`: rewrite assertions to check `(b[1]-b[0]) > 0` etc.; docstring updated to drop the "± framing" language. Also rename to `test_size_extents_are_positive_for_symmetric_generator` for accuracy.
   - `test_bbox_format_matches_regex_on_hanson_quintic`: extend `math.isfinite` from 3 indices (1,3,5) to all 6 indices (0..5) since the subtractions now require b[0]/b[2]/b[4] too — researcher's catch. Docstring rewritten to drop the "honest over-approximation" framing.
   - `test_valueerror_path_cannot_produce_bbox`: docstring update only (the error-string example `bbox ±0.00 × ±0.00 × ±0.00` → `size: 0.000 × 0.000 × 0.000`); test logic unchanged.
   ~30 LOC delta.

3. **CONTEXT.md §4.3 "Status-bar bbox readout"** — Rewrite the entire paragraph (one paragraph at ~line 137 — already documents the v1 ±max format + warning-path priority): keep the warning-path priority note (still relevant, still applies); remove the "honest over-approximation" framing for Hanson (no longer applies — full-extent is exact for all generators); add the peer-tool industry-comparison sentence (ParaView/MeshLab/Blender); document the `.3f` precision rationale. Section header `Status-bar size readout (status-bar-bbox-2026q2-e1 + -e2, UPL-13)` updated for traceability. ~10 LOC delta.

4. **Verify** —
   - `pytest tests/ -q` stays at 336 + 0 net new tests (the 5 existing tests are updated in-place; one was renamed but the count stays at 5).
   - The new BBOX_REGEX `\d{3}` would FAIL on `.2f` output, proving the regex is a real precision guard.
   - The Hanson isfinite extension would catch a future NaN-producing generator change in any of the 6 bounds — broader coverage than the v1 guard.
   - No off-screen render required (status-bar string change only).

5. **Commit** — `feat(status-bar-bbox-2026q2-e2): switch bbox readout from ±max to size: Lx × Ly × Lz (full-extent, peer-aligned) — close F-M2/F-L1/F-L2 from e1`.
