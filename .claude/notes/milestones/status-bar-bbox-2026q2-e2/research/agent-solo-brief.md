# Research brief — status-bar-bbox-2026q2-e2

**Agent:** milestone-researcher (Sonnet, solo mode)
**Date:** 2026-05-22
**Milestone:** status-bar-bbox-2026q2-e2 — switch status-bar bbox from ±max to size: full-extent format

---

## 1. TL;DR

Replace the single f-string `f"bbox ±{_b[1]:.2f} × ±{_b[3]:.2f} × ±{_b[5]:.2f}"` at `app.py:578` with `f"size: {_b[1]-_b[0]:.3f} × {_b[3]-_b[2]:.3f} × {_b[5]-_b[4]:.3f}"`, rename the variable from `bbox_suffix` to `size_suffix` for semantic clarity (the variable name appears in only 2 places, not a call-site risk), and update `CONTEXT.md:137` plus `tests/test_status_bar_bbox.py` (5 tests, format contract + 3 docstrings). The main risk is a subtle `.2f` → `.3f` digit-count change in the BBOX_REGEX: the regex `\d+\.\d+` matches any digit-dot-digit pattern and will pass with either precision — but the new BBOX_REGEX must require exactly 3 decimal places (`\d+\.\d{3}`) to guard the contract. No backup plan is needed — this is a mechanical 3-LOC code change with 3-LOC test change; both paths (success and warning) consume the same variable.

---

## 2. Prior art in this repo

- `app.py:571–601` — the full bbox block in `_render_current`: local variable `_b = self._raw_mesh.bounds`, `bbox_suffix` f-string at `app.py:578`, consumed by `base_msg` at `app.py:584` and the warning path at `app.py:597`. Both consuming sites reference `bbox_suffix` by name — a rename to `size_suffix` touches exactly these 2 usage lines plus the assignment line (3 edits total in the f-string block).
- `app.py:576` — inline comment block (lines 569–577) that explains the `±max` framing and its over-approximation for Hanson. This comment must be rewritten for the full-extent framing; the `±max` / "over-approximation" language is no longer accurate.
- `CONTEXT.md:137` — the entire §4.3 status-bar bbox paragraph. Contains: (a) the `±a × ±b × ±c` format description, (b) the "11 symmetric generators exact / 3 Hanson honest over-approximation" split, (c) the future-extension note ("if a future generator uses a non-centered domain extend to `xmin..xmax`"), (d) the warning-path priority note. Items (a)/(b)/(c) must change; item (d) stays.
- `tests/test_status_bar_bbox.py:22` — `BBOX_FORMAT = "bbox ±{a:.2f} × ±{b:.2f} × ±{c:.2f}"` — must become `BBOX_FORMAT = "size: {a:.3f} × {b:.3f} × {c:.3f}"`.
- `tests/test_status_bar_bbox.py:23` — `BBOX_REGEX` — must become `r"^size: \d+\.\d{3} × \d+\.\d{3} × \d+\.\d{3}$"`.
- `tests/test_status_bar_bbox.py:26–28` — `_format_bbox` helper — reads `b[1]`/`b[3]`/`b[5]` (positive max-extents). Must change to compute full extents: `b[1]-b[0]`, `b[3]-b[2]`, `b[5]-b[4]`.
- `tests/test_status_bar_bbox.py:41–54` — `test_bbox_max_extents_are_positive_for_symmetric_generator` — tests that `b[1]/b[3]/b[5] > 0`, which was valid for the ±max framing. With full extents, the right assertion is `b[1]-b[0] > 0` etc. (full extent is always > 0 for any non-degenerate mesh). The test intent survives but the assertion lines and docstring need rewriting.
- `tests/test_status_bar_bbox.py:68–85` — `test_bbox_format_matches_regex_on_hanson_quintic` — the `math.isfinite` assertions check `b[1]`/`b[3]`/`b[5]`. With full extents, must check all 6 bounds indices (`b[0]`..`b[5]`) since `bounds[0]` (xmin) also matters for the subtraction. The isfinite guard purpose (catch NaN-producing generator changes) is equally valid for full extents; keep all checks but extend to cover all 6.
- `tests/test_status_bar_bbox.py:88–98` — `test_valueerror_path_cannot_produce_bbox` — references `'bbox ±0.00 × ±0.00 × ±0.00'` in its docstring. Update docstring to `'size: 0.000 × 0.000 × 0.000'`. Test logic (raises ValueError) is unaffected.
- `view_panel.py:60,253–257,303–307,356–362,492–494` — `_bbox_actor`, `_bbox_cb`, `_on_bbox_toggled`, `_remove_bbox` — these use "bbox" as a name for the *wireframe bounding box VTK actor*, which is a completely different feature from the status-bar text readout. No changes required; the naming collision is cosmetic.

---

## 3. External sources reviewed

No external web searches performed. This milestone is purely mechanical format-string surgery on 3 source locations with no novel math, no new variety, no new library. All signal is in repo-local files. Per prior memory lessons (status-bar-bbox-2026q2-e1, qtawesome-icons-2026q2-e1): for XS UI-feedback milestones with a fully-spec'd format change, skip external searches entirely.

| Source | URL | Key finding | Relevance |
|---|---|---|---|
| Prior adversary critique | `.claude/notes/milestones/status-bar-bbox-2026q2-e1/artifacts/adversary-critique.md` | F-M2+F-L1 defer decision and rectification status confirmed | Supplies exact format proposal and industry vocab citations (ParaView/MeshLab/Blender) already embedded in brief |
| CONTEXT.md §4.3 (live) | local file, line 137 | Current paragraph text to be replaced; warning-path note to be preserved | Direct edit target |
| app.py:569–601 | local file | Full bbox block: variable name, f-string, 2 consuming sites | Direct edit target |
| tests/test_status_bar_bbox.py | local file | BBOX_FORMAT, BBOX_REGEX, _format_bbox, 5 test functions | Direct edit targets |

---

## 4. Recommended approach

### 4.1 Variable-name decision: rename `bbox_suffix` to `size_suffix`

Recommendation: **rename**. The variable currently named `bbox_suffix` carries the value `"bbox ±…"` — but after this milestone the value will be `"size: …"`. Keeping the old name creates a semantic mismatch visible in git blame for the life of the repo. The rename touches exactly 3 lines in app.py (assignment at line 578, consumption at line 584, consumption at line 597) — trivial cost. The `bbox` prefix in `view_panel.py` (`_bbox_actor`, `_bbox_cb`) is a separate widget feature and is NOT being renamed; there is no naming collision risk.

### 4.2 Label vocabulary decision: "size:"

Recommendation: **`size:`** (lowercase `s`, colon-space separator). Rationale:
- MeshLab uses "X: / Y: / Z:" with per-axis labels; Blender uses "Dimensions:" then per-axis. AVC's single-line compact format has no space for per-axis labels.
- Among single-field compact notations, `size:` is the peer vocabulary that best matches the mathematical notion of "spatial extent along each axis." The word "size" is unambiguous, short, and aligns with MeshLab's semantics (it reports full-extent widths as "size").
- `"dim:"` is an acceptable abbreviation but is less immediately legible. `"extent:"` is longer and less common in GUIs. `"Size:"` (capital S) is unnecessary capitalization mid-sentence in a status bar token.
- The previous `"bbox"` prefix is an abbreviation for bounding box; `"size"` is more informative (it names what's being shown, not the data structure it came from).

### 4.3 Precision decision: .3f

Confirmed as correct. The v1 critique noted `.3f` costs 9 chars in worst-case message length (3 extra chars per axis × 3 axes). The warning path is already the tight case. After the v1 rect, the warning path reads:
```
f"⚠ {_surface_warning}  ·  {bbox_suffix}  |  {surface.label}  ·  {n_points} verts, {n_cells} faces{param_str}  ·  {gen_ms:.0f} ms"
```
The `size_suffix` change adds 9 chars to `size_suffix` itself (from `"bbox ±1.19 × ±1.19 × ±0.90"` (27 chars) to `"size: 2.261 × 2.261 × 1.800"` (29 chars) — actually only 2 chars longer, since "bbox ±" is 6 chars and "size: " is 6 chars, but `.3f` vs `.2f` adds 3 chars per axis = 9 chars total, making the full token `"size: 2.261 × 2.261 × 1.800"` = 29 chars vs `"bbox ±1.19 × ±1.19 × ±0.90"` = 27 chars). The warning path already works within the clip budget per the v1 rect; 2 extra chars is not a regression risk.

### 4.4 Exact code change in app.py

Three edits to the bbox block (lines 569–601):

**Line 569–577 (comment block):** Replace the comment explaining `±max` framing with a comment explaining full-extent semantics. The new comment should: (a) state that `size: Lx × Ly × Lz` where `Li = bounds[2i+1] - bounds[2i]` is the full extent, (b) confirm this is exact for all generators including Hanson (no over-approximation framing needed), (c) retain the CONTEXT.md reference.

**Line 578 (assignment):**
- Old: `bbox_suffix = f"bbox ±{_b[1]:.2f} × ±{_b[3]:.2f} × ±{_b[5]:.2f}"`
- New: `size_suffix = f"size: {_b[1]-_b[0]:.3f} × {_b[3]-_b[2]:.3f} × {_b[5]-_b[4]:.3f}"`

**Line 584 (base_msg consumption):** rename `bbox_suffix` → `size_suffix`.

**Line 597 (warning path consumption):** rename `bbox_suffix` → `size_suffix`.

### 4.5 Test changes in tests/test_status_bar_bbox.py

Five changes:

**BBOX_FORMAT (line 22):**
- Old: `"bbox ±{a:.2f} × ±{b:.2f} × ±{c:.2f}"`
- New: `"size: {a:.3f} × {b:.3f} × {c:.3f}"`

**BBOX_REGEX (line 23):**
- Old: `re.compile(r"^bbox ±\d+\.\d+ × ±\d+\.\d+ × ±\d+\.\d+$")`
- New: `re.compile(r"^size: \d+\.\d{3} × \d+\.\d{3} × \d+\.\d{3}$")`
- Note: `\d{3}` (exactly 3 decimal places) is preferred over `\d+` to explicitly guard the `.3f` contract. The old regex with `\d+` would pass `.2f` or `.4f` — the new regex fails unless exactly 3 decimal places are present.

**`_format_bbox` helper (line 27–28):**
- Old: `return BBOX_FORMAT.format(a=b[1], b=b[3], c=b[5])`
- New: `return BBOX_FORMAT.format(a=b[1]-b[0], b=b[3]-b[2], c=b[5]-b[4])`

**`test_bbox_max_extents_are_positive_for_symmetric_generator` (lines 41–54):**
- Assertion lines: change `b[1] > 0` / `b[3] > 0` / `b[5] > 0` to `(b[1]-b[0]) > 0` / `(b[3]-b[2]) > 0` / `(b[5]-b[4]) > 0`.
- Docstring: remove the "Validates the ±max framing" and "makes ± framing nonsensical" language. Replace with: "For any non-degenerate mesh, the full extent along each axis must be > 0. Exercised against a representative symmetric-sampling-box generator (Fermat quartic); the same contract holds for all generators."

**`test_bbox_format_matches_regex_on_hanson_quintic` (lines 68–85):**
- `math.isfinite` assertions: extend from `b[1]`/`b[3]`/`b[5]` to all 6 indices `b[0]`..`b[5]` (since the full-extent computation subtracts `b[0]`/`b[2]`/`b[4]` — they must also be finite). Keep the existing `b[1]/b[3]/b[5]` checks and add the three new `b[0]/b[2]/b[4]` checks.
- Docstring: remove "honest over-approximation" language. Replace with: "Hanson parametric generators sample `theta ∈ [0, π/2]` (non-centered), so their mesh.bounds are not symmetric — CONTEXT.md §4.3 documents the switch to full-extent widths (`size: Lx × Ly × Lz`) which reports the actual diameter honestly rather than over-approximating with ±max. All 6 bounds must be finite."

**`test_valueerror_path_cannot_produce_bbox` (lines 88–98):**
- Docstring only: change `'bbox ±0.00 × ±0.00 × ±0.00'` to `'size: 0.000 × 0.000 × 0.000'`. Test logic (pytest.raises ValueError) is unaffected.

### 4.6 CONTEXT.md §4.3 rewrite

Target: line 137. Replace the entire sentence from "After every successful render..." to "...and the ValueError path)" (the full current paragraph) with the following:

---
**Status-bar size readout (status-bar-bbox-2026q2-e1 + -e2, UPL-13).** After every successful render the status bar appends `size: Lx × Ly × Lz` to the `{N_verts} verts, {N_faces} faces` line, where `Lx = bounds[1]-bounds[0]`, `Ly = bounds[3]-bounds[2]`, `Lz = bounds[5]-bounds[4]` — the true full extents along each axis. Read from `_raw_mesh` (not the domain-clipped copy) so researchers see the spatial extent of the mathematical surface, not the current viewport slice. The full-extent format is **exact for all generators** in the live registry — including the 3 Hanson parametric generators (calabi_yau_quintic, calabi_yau_cubic, calabi_yau_asymmetric) whose theta sweeps `[0, π/2]` produce asymmetric bounds; full extent `bounds[1]-bounds[0]` reports the actual diameter regardless of centering. This format aligns with peer scientific-viz tools: ParaView shows per-axis ranges, MeshLab shows full extents (`X: 2.000 Y: 2.000 Z: 2.000`), Blender shows `Dimensions: X: 2.00 m`. Precision is `.3f` (3 decimal places) — avoids false equalities at sub-1.0 extents where `.2f` rounds adjacent values to the same display. **Warning path:** on the conifold-warning render path (Dwork ψ ≈ 1), the size suffix is hoisted to immediately follow the `⚠ {warning}` prefix and the verbose `{label} verts, faces` content moves to the trailing position, because the combined warning + base_msg can exceed `QStatusBar`'s ~120-char clip width; this preserves the size readout visibility on the one render path where spatial extent is most informative. AI-10 safe — the read is inside the success branch of `_render_current` only; the `except ValueError` / `except Exception` paths set `_raw_mesh = None` and return before reaching the format line (AI-14). Format-contract guard: `tests/test_status_bar_bbox.py` (covers Fermat quartic, Kummer surface, Hanson quintic with `math.isfinite` guard on all 6 bounds indices, and the ValueError path).
---

### 4.7 `±` symbol elsewhere

Grep confirms all `±` occurrences in Python source files (`surfaces.py:844`, `surfaces.py:942`, `surfaces.py:953`, `surfaces.py:979`) are in docstring/comment mathematical notation (e.g. `±1000 covers all reachable corners`, `z = ±√f_6`, `x=±y`). None reference the status-bar `±a × ±b × ±c` literal. No changes needed outside the 3 target lines in app.py and the 5 test targets.

---

## 5. Alternatives considered

- **Keep `bbox_suffix` variable name.** Rejected: semantic mismatch post-format-change. The variable name would say "bbox" but hold "size: …" text. Cost is 3 trivial line edits to rename; benefit is permanent clarity in git blame.
- **Use `"dim:"` label.** Rejected in favor of `"size:"`: "dim" is less immediately legible in a status-bar scan, and does not map to the MeshLab/Blender vocabulary as naturally as "size" does. Not wrong, just slightly weaker.
- **Use `"Size:"` (capital S).** Rejected: status-bar tokens in this app use lowercase labels (`bbox`, `verts`, `faces`) — capital S would be a style inconsistency.
- **Per-axis labels like `"x: 2.261  y: 2.261  z: 1.800"`** (MeshLab row style). Rejected: the compact `×`-separator format is already established by v1; adding per-axis labels adds 6 chars with no information gain for 3-axis output where order is unambiguous.
- **Keep `.2f` precision.** Rejected per F-L2: `.2f` allows false equality at sub-1.0 extents. The 9-char overhead from `.3f` is within the warning-path budget confirmed by the v1 rect.
- **`BBOX_REGEX` using `\d+` (any decimal digits).** Rejected: `\d+` passes `.2f` format, defeating the test as a precision guard. `\d{3}` explicitly verifies the `.3f` contract.
- **Option (c) from F-M2 critique: `symmetric_bounds: bool` flag on Surface dataclass.** Rejected (correctly deferred): adds Surface dataclass complexity, requires a registry-wide audit of all 14 surfaces, and the full-extent format makes the flag unnecessary — full-extent is honest for ALL generators by construction.
- **Option (b) from F-M2 critique: add `(approx.)` suffix on Hanson rows only.** Rejected: the full-extent format eliminates the need for per-generator disclosure, and selective annotation would require conditional logic in the f-string block.

---

## 6. Risks and unknowns

**AI-9 (re-entrancy guard):** The change is format-string only. No new `processEvents()` calls, no new signal connections. The `_b = self._raw_mesh.bounds` read is O(1). NONE.

**AI-10 (raw mesh cache):** The read is inside the success branch after `_apply_domain_and_render` returns. `self._raw_mesh` is the un-clipped mesh set at the successful `new_mesh = surface.generate(**params)` call. NONE.

**AI-14 (generator contract):** `except ValueError` and `except Exception` branches both set `self._raw_mesh = None` and `return` before reaching the format block. NONE — structural guarantee unchanged by the format switch.

**AI-2 (Qt-free tests):** The test file imports only `re`, `math`, `pytest`, `surfaces`. No Qt. The format change does not introduce any Qt dependency. NONE.

**Message length on warning path:** The full size_suffix at typical values is 29 chars (`"size: 2.261 × 2.261 × 1.800"`) vs 27 chars for the old format (`"bbox ±1.19 × ±1.19 × ±0.90"`). The 2-char increase on the already-clipping warning path is negligible; the warning path already clips at the verbose trailing content, not at the size token which is hoisted to the front per the v1 rect. NONE.

**CONTEXT.md forward-maintenance note:** The current paragraph includes a "future extension" note: "If a future generator uses a non-centered sampling domain, extend the format to `xmin..xmax × ymin..ymax × zmin..zmax`". With full-extent format, this note is obsolete — `bounds[1]-bounds[0]` is already correct for non-centered domains. The CONTEXT.md rewrite removes this note. Future generator authors who want per-axis signed ranges can adopt `"range: xmin..xmax × ymin..ymax × zmin..zmax"` in a future milestone; that is out of scope here.

**`_format_bbox` helper function name in test file:** The function is named `_format_bbox` but now formats `size: …`. Renaming to `_format_size_suffix` is cosmetic — not wrong to leave as `_format_bbox` as an internal test helper, but renaming avoids confusion. Recommend renaming to `_format_size` in the test file for internal consistency (the function is a private helper referenced only within the 5 test functions).

**Worktrees:** grep found `±` and `bbox` references in `.claude/worktrees/agent-*/` directories. These are detached milestone worktrees not part of the live app. No action required.

---

## 7. AI-15 disclaimers

Not applicable. This milestone proposes no new variety, no new figure, and no change to the mathematical content of any surface. The status-bar text is metadata about the bounding box of the rendered mesh — it does not describe or claim anything about the mathematical nature of the variety. AI-15 emits NONE.

---

## 8. Open questions for the user

None. The brief, format, precision, variable name, label vocabulary, test changes, CONTEXT.md rewrite, and AI invariant matrix are all fully specified by the prior milestone critique (F-M2 + F-L1 + F-L2) and the user's verbatim brief. No decisions remain.
