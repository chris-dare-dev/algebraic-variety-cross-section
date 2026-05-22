# Frontend UI/UX Critique — status-bar-bbox-2026q2-e2

**Milestone:** status-bar-bbox-2026q2-e2
**Commit range:** `269f38ffbea5ed3578fe07d17b2a04ab75bdbdcb..HEAD`
**Critic:** milestone-frontend-ux-critic (claude-sonnet-4-6)
**Date:** 2026-05-22
**Files changed (Qt-panel surface):** `app.py` only

---

## Executive summary

The diff replaces the status-bar bbox token from the e1 half-extent format
(`bbox ±a × ±b × ±c`) to the e2 full-extent format (`size: Lx × Ly × Lz`)
in `app.py:_render_current`. The change is text-only — no widget construction,
no QSS, no Qt enum, no color, no `processEvents`. Axes 1–4, 6–12 are all
N/A for this milestone.

**0 CRITICAL, 0 HIGH.** The implementation is correct and the data it reports
is accurate for all 14 generators. Two findings: one MEDIUM (label precision
regression) and one LOW (cosmetic precision noise). The transition from `bbox`
to `size:` removes the measurement-type qualifier that e1 had and that every
peer tool examined qualifies explicitly — at zero character cost.

---

## CRITICAL

None.

---

## HIGH

None.

---

## MEDIUM

### MEDIUM — `"size:"` drops the AABB qualifier that `"bbox"` carried; peer tools all qualify explicitly

**Where:** `app.py:587`
**Evidence:** e1 format was `bbox ±a × ±b × ±c` — the word `bbox` explicitly names the measurement
type (axis-aligned bounding box). e2 replaces this with `size: Lx × Ly × Lz`, which removes the
qualifier. Peer tools examined:
- MeshLab (PyMeshLab API): `dim_x()` / `dim_y()` / `dim_z()` are documented as "the X size of the
  Bounding Box" — the qualifier "Bounding Box" is always present.
- ParaView Information panel: uses `Bounds` and `X Range: min to max` — the word "Bounds" names
  the measurement type.
- Blender Properties panel / status bar: `Dimensions:` — which implies bounding-box extent by
  convention in all desktop 3D tools.
None of the three peer tools uses bare `size:` without a type qualifier.

The character cost of using `bbox:` in place of `size:` is zero — both yield a
27-character suffix for a Kummer-wide mesh (`size: 6.400 × 6.400 × 6.400` =
`bbox: 6.400 × 6.400 × 6.400` = 27 chars). The compactness rationale does not hold.

A researcher encountering `size: 6.400 × 6.400 × 6.400` for an algebraic surface could
interpret "size" as surface area (an integral over the manifold), as volume (for closed
surfaces), or as the true geometric diameter (maximum pairwise Euclidean distance on the
surface, which exceeds the AABB extent for non-convex shapes). All three are distinct
quantities from what is actually reported (AABB extent in user-coordinate space). The
e1 label `bbox ±...` was less ambiguous despite its ±-notation limitation.

**Why it matters:** Research tools accumulate credibility through precision. A label that
could be read as "surface area" or "volume" by a less familiar user erodes trust in the
readout. The e2 change is a data-accuracy improvement (full-extent vs half-extent for
Hanson) but a label-precision regression (removing the "bbox" qualifier). Both goals
could be achieved simultaneously with `bbox: Lx × Ly × Lz`.

**Suggested fix:** Change `"size:"` to `"bbox:"` at `app.py:587` and `app.py:607`. The
full-extent arithmetic (`_b[1]-_b[0]` etc.) is correct and should be preserved. This
restores the measurement-type signal that e1 carried, aligns with MeshLab's explicit
"Bounding Box" qualifier, and is character-neutral.

---

## LOW

### LOW — `.3f` trailing zeros on symmetric generators may read as false precision to some users

**Where:** `app.py:587`
**Evidence:** For any symmetric-sampling-box generator (Fermat quartic, Kummer surface,
all Enriques figures), `bounds[1] - bounds[0]` returns exactly `2 * grid_half_extent` in
floating point. For Kummer with `bounds=3.2`, the full extent is exactly `6.4`, rendered
as `6.400`. For Fermat quartic with `bounds=1.5`, the extent is `3.0`, rendered as `3.000`.
The trailing zeros are numerically exact (not false precision), but a user accustomed to
short-form readouts may read `6.400` as "measured to 0.001 accuracy" rather than "the
sampling domain is exactly 6.4 wide."

The `.3f` rationale is sound: `.2f` aliases surfaces with extents `0.530` and `0.540` to
the same display (`0.53`), which is a false-equality risk in a research tool. The choice
is correctly motivated by the sub-1.0 edge case, not by a desire for extra precision in
the common case.

**Why it matters:** Cosmetic only. The data is correct. Users who notice `6.400` may
initially wonder why three decimal places are shown, but the value is self-consistent.
This is a paper-cut, not a functional issue.

**Suggested fix:** The existing code comment (`Precision .3f avoids false equalities at
sub-1.0 extents`) is accurate. No code change needed. If the trailing-zeros appearance
is a concern, a `g`-format with a 4-significant-figure floor (`:.4g` → `6.4` for
exactly-round values, `0.5300` for sub-1.0 with adequate precision) would suppress the
trailing zeros while preserving the disambiguation benefit. This is a cosmetic
refinement and can wait for a future UPL iteration.

---

## What was done well

1. **Hanson asymmetry fix is technically correct and peer-validated.** The switch from
   `±max` half-extents to `bounds[1]-bounds[0]` full extents is the right call. The e1
   half-extent format was an over-approximation for Hanson's `[0, π/2]` theta sweeps;
   e2 is exact by construction for all 14 generators. This is the same convention used
   by MeshLab (`dim_x()` = `max_x - min_x`) and Blender `Dimensions`.

2. **Warning-path hoisting preserved correctly.** The e1 architecture — hoist the spatial
   suffix immediately after `⚠ {warning}` to protect it from clip-width overflow, push
   the verbose verts/faces label to the trailing position — is carried through to e2
   unchanged. The +1-character delta vs e1 is negligible given the warning prefix already
   overflows the ~120-char clip window by ~25 chars.

3. **`×` separator (U+00D7) retained.** Already shipped in e1; no regression introduced.
   On macOS and Windows with system fonts, U+00D7 is in Latin-1 Supplement and renders
   reliably. Changing to ASCII `x` would create letter/symbol ambiguity. The character
   choice is correct.

4. **Test suite extended appropriately (AI-2 compliant).** The test file covers all four
   key scenarios: format-regex match on Fermat quartic, positivity check on Fermat
   quartic, format-regex match on Kummer, and all-6-bounds `math.isfinite` + format-regex
   on Hanson quintic (the asymmetric case that motivated the e2 change). The `ValueError`
   path guard (`test_valueerror_path_cannot_produce_size_suffix`) ensures the error
   branch never emits a size token. All four tests are Qt-free (no `MainWindow`,
   no `QApplication`), satisfying AI-2.

5. **Code comment quality.** The inline comment at `app.py:569–584` is precise: it
   names both e1 and e2 milestones, explains the full-extent formula, cites the Hanson
   asymmetry root cause, and cross-references peer tools. This level of inline
   documentation is above the repo baseline and will accelerate future reviewers.

---

## Recommended rectification order

1. **(MEDIUM-1)** Change `"size:"` → `"bbox:"` in both locations (`app.py:587` suffix
   construction and `app.py:607` warning-path hoist). Zero character impact, restores
   measurement-type qualifier, aligns with MeshLab and ParaView naming conventions.
   Update the code comment to reflect the label change (one line).

2. **(LOW-1)** Optional / defer: if trailing zeros on round values are considered a UX
   concern in a future pass, evaluate `:.4g` vs `.3f`. Not recommended for immediate
   action — the current rationale is sound and the display is numerically correct.

---

## Industry comparison axis (axis 12)

Two peer scientific-viz tools examined for the status-bar spatial readout:

**MeshLab** (closest analog — algebraic mesh viewer): uses "Bounding Box" explicitly
in its UI and `dim_x()` / `dim_y()` / `dim_z()` in its API, both of which compute
`max - min` per axis — identical to the e2 formula. MeshLab does NOT use bare "size:"
without the "Bounding Box" qualifier. This is the concrete basis for MEDIUM-1.

**ParaView 6.x** Information panel: displays `Bounds` with `X Range: [min, max]` and
`Y Range: [min, max]`, `Z Range: [min, max]`. Does not compute AABB width as a single
number; shows the min/max pair. The AVC full-extent `Lx × Ly × Lz` is a more compact
encoding of the same information. ParaView's use of `Bounds` (not `size`) further
supports the MEDIUM-1 direction.

Blender `Dimensions:` is the closest semantic match to what is displayed, and Blender
uses the word "Dimensions" (implying bounding-box width), not "size". This is consistent
with the MEDIUM-1 finding.

---

*Status: complete. 0 CRITICAL, 0 HIGH, 1 MEDIUM, 1 LOW.*
