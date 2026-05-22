# Adversary critique — Enriques back-face culling per-variety gate

**Reviewer:** milestone-adversary-critic (read-only) | **Date:** 2026-05-22 | **Subject:** enriques-backface-2026q2-e1 / 8e5c30c..4a9530a

> Diff stats: 3 files changed, 81 insertions(+), 0 deletions(−); 125 diff lines total (below the 400-LOC review-quality-at-risk threshold).

---

## Executive summary

The highest-severity finding is a factual inaccuracy in CONTEXT.md §8.13: the document claims all four Enriques subtypes "share the double-curve topology," but the Cayley symmetroid (Fig. 3) is a degree-4 surface with ordinary nodes — not double-curve singularities — and the icosahedral sextic (Fig. 4) also has point-conical A₁ nodes rather than double curves.  This is a MEDIUM math-honesty issue (AI-15 adjacent) because the gate decision itself is sound (culling is verified as a no-op for Fig. 3 and beneficial for Figs. 1, 2, 4) but the rationale mis-states the topology.  Beyond this, the diff is clean: zero CRITICALs, one MEDIUM, two LOWs.  The AI-7 Hanson exclusion is correctly enforced by a Unicode-matched string literal; the PyVista culling API is verified to accept "none" as the off-string (making the `or "none"` idiom safe); and the subtype-switch culling-persistence behavior is correct by design.  The milestone is safe to ship after the MEDIUM rectification.

---

## Critical findings

None.

---

## High findings

None.

---

## Medium findings

### MEDIUM — CONTEXT.md §8.13 topology rationale is inaccurate for Figs. 3 and 4

**Where:** `CONTEXT.md:406`
**Evidence:** §8.13 states: "All four Enriques subtypes (canonical sextic, λ-family, Cayley symmetroid, icosahedral sextic) share the double-curve topology so the variety-level gate is correct without per-subtype branching."  The Cayley quartic symmetroid (`surfaces.py:405-428`) is documented in its own docstring as "a degree-4 surface in P^3 with up to 10 ordinary nodes" — ordinary A₁ nodes, not double curves.  The icosahedral sextic (`surfaces.py:442`) is an icosahedrally symmetric surface whose singularities are point-conical A₁ nodes (related to Barth/Endrass normalizations), again not double-curve singularities.  The byte-size evidence is consistent: Fig. 3 renders at 40222→40222 bytes (culling is a no-op, as expected for a surface without the double-sheet marching-cubes artifact), while Figs. 1, 2, 4 all show size reductions from culling.
**Why it matters:** Future maintainers reading §8.13 will incorrectly conclude the variety-level gate is justified by a shared double-curve topology across all four figures.  When they add a new Enriques figure with a different topology (e.g., another Reye-cover quartic), they may assume culling is safe because "all Enriques figures have double curves."  The actual justification is narrower: the culling gate is correct because it is harmless for Figs. 3 and 4 (verified renders show no regression) and beneficial for Figs. 1 and 2.  The rationale should be honest about which figures have double curves and why culling is still applied at variety-level despite being a no-op for Fig. 3.
**Suggested fix:** Revise §8.13 to split the rationale: "Figs. 1 and 2 (sextic families) have double-curve singularities along the coordinate-tetrahedron edges; Figs. 3 and 4 have ordinary nodes.  The variety-level gate is still correct because culling is a verified no-op for Fig. 3 (40222→40222 bytes) and beneficial for Figs. 1, 2, 4.  Applying culling at the variety level avoids per-subtype branching while producing the correct result for all four."

---

## Low findings

### LOW — `set_culling` API accepts invalid strings without validation

**Where:** `appearance_panel.py:399`
**Evidence:** `set_culling` stores `value` directly with `self._culling = value`, accepting any string (e.g., `"left"`, `"backward"`, `"1"`).  The invalid value propagates silently to `apply_to_actor:337` where `actor.prop.culling = self._culling or "none"` passes it to PyVista, which raises `ValueError: Invalid culling "left". Should be either: "back", "front", or "None"` at render time — not at the set-time API boundary.  Currently only `"back"` and `None` are passed by the single call site in `app.py:254`, so this is not a live bug today.
**Why it matters:** The docstring advertises `"back"`, `"front"`, `"none"` as the valid values.  If a future maintainer adds a second call site with a typo (e.g., `set_culling("backwards")`), the failure surfaces at render time with a PyVista error in the plotter rather than at the set-call boundary where the invalid argument was introduced.
**Suggested fix:** Add a validity check at entry: `if value not in (None, "back", "front", "none"): raise ValueError(...)` — or document in the docstring that callers are responsible for passing valid values and that invalid values produce a PyVista ValueError at render time.

### LOW — Missing `set_culling` unit test analogous to `test_set_default_color_*`

**Where:** `tests/test_styles_palette.py` (no specific line — missing test)
**Evidence:** The variety-palette-2026q2-e1 milestone introduced `test_set_default_color_updates_surface_color` and `test_set_default_color_ignores_invalid_hex` using the unbound-method shim pattern (no QApplication needed, AI-2 compliant).  This milestone adds `set_culling`, a structurally identical public method on `AppearancePanel`.  No equivalent shim test was added to verify `_culling` is correctly updated and that calling `set_culling(None)` sets `self._culling = None`.  The variety-palette-2026q2-e1 adversary critique explicitly flagged this pattern gap; the same lesson applies here.
**Why it matters:** The per-variety gate at `app.py:254-255` is the critical routing logic (`"back" if name == "Enriques surface" else None`).  A test for `set_culling` that uses the unbound-method shim would catch a future rename of `self._culling` to `self._cull_mode` that breaks the gate without touching the test suite.  As with `set_default_color`, the shim requires only Python — no Qt, no PyVista, no special fixture.
**Suggested fix:** Add two shim tests to `tests/test_styles_palette.py`: (1) `test_set_culling_stores_back_value` — calls the unbound `set_culling("back")` on a shim and asserts `shim._culling == "back"`; (2) `test_set_culling_clears_to_none` — calls `set_culling(None)` and asserts `shim._culling is None`.  Optionally also assert that the `or "none"` expression in `apply_to_actor` evaluates to `"none"` when `_culling` is `None`.

---

## What was done well

- **Unicode key audit passed.** The gate condition `name == "Enriques surface"` at `app.py:255` uses the identical byte sequence (all ASCII printable) as the VARIETIES dict key at `surfaces.py:950`.  The variety-palette-2026q2-e1 incident (en-dash homoglyph in "Calabi–Yau 3-fold") is not repeated here — this key is pure ASCII and the bytes were verified to match.
- **AI-7 Hanson exclusion is correctly enforced.** The `else None` branch in `set_culling("back" if name == "Enriques surface" else None)` guarantees `self._culling = None` (and therefore `actor.prop.culling = "none"`) for every non-Enriques variety.  The "Calabi–Yau 3-fold" and "Fano 3-fold (ρ=1)" keys are distinct enough from "Enriques surface" that no accidental match is possible.
- **PyVista `or "none"` idiom is correct.** `self._culling or "none"` evaluates to `"none"` when `self._culling is None`, and to the stored string otherwise.  PyVista's `Property.culling` setter accepts `"back"`, `"front"`, or `"none"` as valid strings; the `or "none"` fallback maps the Python-None default to the correct PyVista off-state.  This was verified against the PyVista property source.
- **Pattern-A architecture is correctly applied.** `set_culling` follows the exact shape established by `set_default_color` and `refresh_icons`: panel stores state, MainWindow sets it on variety change, `apply_to_actor` pushes it to the actor on every render.  This keeps `AppearancePanel` free of variety-name string comparisons, correctly decoupling state-storage from gate-logic.
- **Subtype-switch culling persistence is correct by design.** `set_culling` is called only from `_on_variety_changed` (not `_on_subtype_changed`), so switching between Enriques Fig.1→Fig.2→Fig.3→Fig.4 correctly preserves `self._culling = "back"` — the variety-level state carries through.  Switching to K3 clears it via the `else None` branch.  This is the intended semantic and requires no additional wiring in `_on_subtype_changed`.
- **AI-9 re-entrancy is clean.** `set_culling` is a synchronous setter with no `processEvents` call.  It is invoked from `_on_variety_changed` before `_render_current` is called, so the guard `self._computing = True` is not yet set.  No re-entrancy hazard.
- **CONTEXT.md §8.13 strong-form warning is high quality.** The bolded forward-maintenance rule ("If you add a new K3 / CY3 / Fano figure, do NOT add a variety-level culling branch") is exactly the right institutional-memory entry for this footgun.  Future agents and developers get a clear "stop" signal rather than having to re-derive the AI-7 hazard.
- **Commit message correctly documents the c=0 brief error.** The commit message explicitly notes: "the original visual-scout brief referenced 'default c=0' for the Enriques canonical sextic. Actual default is c=1.0 (the slider minimum is 0.1; c=0 raises ValueError)."  This error was not propagated into CONTEXT.md §8.13 or into surfaces.py — the ParamSpec at `surfaces.py:348` correctly shows minimum=0.1, default=1.0.

---

## Recommended rectification order

1. **Rectify the MEDIUM (M1) — CONTEXT.md §8.13 topology rationale.** Revise the claim that all four Enriques subtypes share the double-curve topology.  Separate the sextic-family rationale (Figs. 1 and 2 have double curves; culling removes the zipper artifact) from the non-sextic rationale (Fig. 3 is a degree-4 surface with ordinary nodes; culling is a verified no-op; Fig. 4 has point-conical nodes; culling is beneficial but not because of double curves).  One concise paragraph update; no code change.

2. **Optionally add the LOW shim tests (L2).** Two tests following the `test_set_default_color_*` shim pattern, added to `tests/test_styles_palette.py`.  Fast, zero-dependency, and closes the regression-guard gap for the variety-routing logic.  Recommended before milestone close but not blocking.

3. **L1 (API validation) is optional.** The single call site is correct today.  Adding input validation to `set_culling` is a defensive measure; defer unless a second call site materializes.

---

*End of critique.  Mandatory rectification: M1 (CONTEXT.md §8.13 topology claim).  L1 and L2 are optional but L2 is recommended before milestone close.*
