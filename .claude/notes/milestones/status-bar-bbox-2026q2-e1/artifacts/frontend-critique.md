# Frontend UX Critique — status-bar-bbox-2026q2-e1

**Milestone:** status-bar-bbox-2026q2-e1 (UPL-13 — status-bar spatial extent readout)
**Commit range:** `0e2e8105376ccb7fe7cdcb6ebf3ad36a8c7c155f..HEAD`
**Critic:** milestone-frontend-ux-critic (Sonnet 4.6)
**Date:** 2026-05-22
**Status:** complete

---

## Executive summary

This milestone adds a single `bbox ±a.bb × ±b.bb × ±c.bb` suffix to the
existing status-bar success message in `app.py:_render_current`.  The change
is narrow in scope, well-commented, and follows the existing `·`-separator
convention.  **Zero CRITICAL, zero HIGH findings.**

Two MEDIUM findings are raised:

1. **Status-bar overflow on the Dwork warning path** — when the conifold
   `RuntimeWarning` fires, the combined `⚠ <warning>  |  <label> · verts,
   faces · params · bbox` string is ~294 chars, well past the ~80-char
   safe display zone of a default Qt window.  The bbox suffix is the
   marginal factor that pushes an already-long message past any reasonable
   status-bar width.

2. **Hanson `±max` framing is technically honest but user-misleading** —
   the `±` prefix asserts bilateral symmetry that the Hanson parametric
   meshes do not fully exhibit (x/y-asymmetry ~0.12 units at defaults).
   The comment in `CONTEXT.md §4.3` discloses this to maintainers, but the
   user sees `±1.19` and may assume a perfectly centered mesh.  The
   disclosure is only maintainer-visible, not user-visible.

Two LOW findings address vocabulary choice and a single-digit precision
opportunity.

The implementation is otherwise clean: no new tokens, no new Qt enums, no
`processEvents`, no re-entrancy surface, no color literals, no first-launch
regression.

---

## CRITICAL findings

None.

---

## HIGH findings

None.

---

## MEDIUM findings

### MEDIUM — Status-bar Dwork warning path overflows at ~294 chars

**Where:** `app.py:447` (the `f"⚠ {_surface_warning}  |  {base_msg}"` line)
**Evidence:** Empirical measurement at default params — the Dwork conifold
`RuntimeWarning` text is 145 chars; combined with `base_msg` including the
new bbox suffix the full string is 294 chars.  A default Qt window at
~1000 px with an 11 px monospace font fits roughly 120–130 chars before
`QStatusBar` silently clips the trailing content.  The `bbox ±… × …` suffix
is therefore never seen when the warning fires.
**Why it matters:** The one generator that routinely produces a warning
(`calabi_yau_dwork` near ψ=1) is also a case where the researcher is most
likely to want the spatial extent — the conifold mesh is geometrically
unusual.  The overflow means the status bar shows only the `⚠ ψ ≈ 1 is
the (real) conifold point…` prefix and nothing else.  The bbox readout is
silently lost, not truncated visibly.
**Suggested fix:** On the warning path, emit the bbox suffix on a second
`showMessage` call with a short delay, OR prepend the bbox to the base_msg
before the warning text so the priority order is `⚠ <short-warning>  ·
bbox ±a × ±b × ±c  |  <label> verts, faces`.  Alternatively, cap the
warning text at 80 chars with an ellipsis so the full base_msg stays
visible.

---

### MEDIUM — Hanson `±max` framing silent-over-approximates x/y symmetry

**Where:** `app.py:443`  (`f"  ·  bbox ±{_b[1]:.2f} × ±{_b[3]:.2f} × ±{_b[5]:.2f}"`)
**Evidence:** At default params (`alpha=π/4, grid=41, xi_max=2.0`), the
Hanson quintic mesh has `xmin=-1.0670, xmax=1.1895` — an asymmetry of
~0.12 units (roughly 5% of the extent).  The display shows `±1.19`, which
implies the surface is centered at the origin in x/y, which it is not.
For x: the "true" half-extent of `(-1.07..+1.19)/2 ≈ 0.06` offset is
invisible to the user.  `CONTEXT.md §4.3` documents this as an "honest
over-approximation" but that disclosure is maintainer-only.  The Dwork
implicit generator is exact; the three Hanson parametric generators are
not.
**Why it matters:** Researchers positioning custom clipping planes or
comparing surfaces across varieties will notice that reported ±1.19
doesn't match the actual x-range they can verify in the VTK viewport.
For a tool aimed at mathematical rigour, the silent over-approximation is
at odds with the documented goal of giving researchers "the spatial extent
of the mathematical surface."
**Suggested fix:** For parametric generators, display the asymmetric range
as `x: -1.07..+1.19` rather than `±1.19`.  The CONTEXT.md §4.3 note
already describes this as the future-generator extension pattern.  A per-
generator flag (`ParamSpec` or a `Surface` field `symmetric_bounds: bool`)
would let `app.py` choose the format automatically without hardcoding
variety names.  V0 scope: it is acceptable to document the asymmetry in
a tooltip or a status-bar parenthetical `(approx.)` rather than the full
range format — the key fix is making the approximation user-visible.

---

## LOW findings

### LOW — `bbox` vocabulary non-standard vs peer tools

**Where:** `app.py:443`
**Evidence:** ParaView 5.12's Information panel displays spatial extent as
`X Range: -1.000 to 1.000` / `Y Range: -1.000 to 1.000` / `Z Range: …`
on separate rows.  MeshLab's "Quoted Box" display labels axes individually
(`X: 2.000  Y: 2.000  Z: 2.000`) using full-extent widths, not half-
extents.  Blender's status bar shows `Dimensions: X: 2.00 m  Y: 2.00 m
Z: 2.00 m` using full-extent widths.  All three peers use **full extent**
(diameter, not radius) and avoid the `±` half-extent convention.  AVC's
`bbox ±1.19 × ±1.19 × ±1.52` format is unique: it uses half-extents and
the `bbox` keyword that none of the three peers use as a label prefix.
**Why it matters:** Researchers familiar with ParaView or MeshLab will read
`±1.19` and mentally double it to recover the full extent they're used to
seeing.  The mental translation is minor but adds friction.  `extent` or
`size` is a more standard label.  Full-extent format `2.38 × 2.38 × 3.04`
or `L: 2.38 × 2.38 × 3.04` aligns with peer vocabulary.
**Suggested fix:** Consider `size: 2.38 × 2.38 × 3.04` (full extents,
computed as `bounds[1]-bounds[0]` etc.) as a vocabulary-aligned alternative.
For the symmetric implicit generators this is identical to `2 × ±max`.
For Hanson it is also more accurate (see MEDIUM-2).  The change is one
line and eliminates the MEDIUM-2 asymmetry issue simultaneously.

---

### LOW — `.2f` precision redundant for sub-1.0 extents

**Where:** `app.py:443`
**Evidence:** Several generators (Two-quadrics CI tube at defaults:
`±0.53 × ±0.76 × ±0.99`) produce sub-1.0 extents where `.2f` gives only
2 significant figures of precision (`0.53` = 2 sig figs).  The Fermat
quartic at default params (`±1.00 × ±1.00 × ±1.00`) gives 3 sig figs.
The Kummer surface can have adaptive bounds yielding values like `±2.70`
(3 sig figs).  A format of `.3f` would give consistent 3-significant-
figure precision across all generators (`±0.530 × ±0.760 × ±0.990` vs
`±0.53 × ±0.76 × ±0.99`) — relevant when comparing surfaces with similar
but not identical extents.  Current `.2f` also makes the Fermat default
`±1.00 × ±1.00 × ±1.00` look artificially clean (rounded to exactly 1.00)
rather than reflecting actual mesh extent.
**Why it matters:** Low precision in a research tool can create false
equalities — two surfaces with extents `0.53` and `0.54` both display as
`0.53` with `.2f` at sub-0.1-step sliders.  This is cosmetic at the current
slider granularities but could matter when a future generator has extents
close to a threshold the researcher cares about.
**Suggested fix:** Change `:.2f` → `:.3f` at `app.py:443`.  The bbox
suffix grows by 3 chars per axis (9 chars total) — negligible against
current worst-case message length.

---

## What was done well

1. **Separator consistency.** The `  ·  bbox …` pattern precisely mirrors
   the `  ·  {verts}, {faces}` and `  ·  {params}` separators established
   in the pre-existing line.  A first-time reader can scan the status bar
   and parse its structure immediately.

2. **Raw mesh vs clipped mesh semantics are correct.** Reading from
   `self._raw_mesh.bounds` (not from the domain-clipped copy) is the
   mathematically correct choice — domain clipping shows a viewport slice,
   not the surface's actual extent.  `_apply_domain_and_render` is called
   after `_raw_mesh` is populated, so there is no race where `_raw_mesh`
   could be stale at the readout line.

3. **AI-14 safety.** The bbox readout is inside the success branch of
   `_render_current` — both the `except ValueError` and `except Exception`
   paths clear `_raw_mesh = None` and `return` before reaching the
   `_b = self._raw_mesh.bounds` line.  No `NoneType.bounds` AttributeError
   is possible.

4. **No new Qt enum, color, or `processEvents` surface.** The change
   introduces zero new tokens that could violate AI-9, AI-11, AI-12, or
   AI-13.  Token discipline is clean.

5. **Test coverage is appropriate.** `tests/test_status_bar_bbox.py`
   covers the format regex, positive-max-extent invariant, and the
   ValueError path — all without a `QApplication` dependency, consistent
   with AI-2.

6. **Inline comment precision.** The comment at `app.py:431–438` correctly
   names the asymmetry limitation and points to `CONTEXT.md §4.3` — this
   is a genuinely useful contributor note, not boilerplate.

---

## Recommended rectification order

1. **(MEDIUM-1, quick win)** Cap or restructure the warning-path
   `showMessage` so the bbox suffix is visible when a `RuntimeWarning`
   fires.  The highest-impact one-liner: shorten the warning prefix to
   `⚠ ψ near conifold` and move the full warning text to a tooltip or
   secondary `showMessage` on a timer.

2. **(LOW-1 + MEDIUM-2 combined fix)** Switch the format from `±max` to
   full-extent widths (`size: Lx × Ly × Lz` using `bounds[1]-bounds[0]`
   etc.).  This simultaneously aligns with peer vocabulary (LOW-1),
   eliminates the over-approximation caveat for Hanson (MEDIUM-2), and
   removes the `±` symbol that implies bilateral symmetry the parametric
   generators don't guarantee.

3. **(LOW-2, one character)** Change `:.2f` to `:.3f` if full-extent
   format is not adopted first.  If LOW-1+MEDIUM-2 are addressed by
   switching to full extents, revisit precision on the new numbers.
