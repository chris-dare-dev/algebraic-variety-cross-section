"""Variety + subtype tooltips for the GUI dropdowns.

Per restructure-feature-subpackages-2026q2-r2 Batch 8: extracted from surfaces.py.

AI-15 (load-bearing): every tooltip carries an honest "real shadow" disclaimer
for non-R^3 varieties and a Preview-badge LOD note for implicit coarse-LOD generators.
The discipline lives in this module — any new variety MUST add a SUBTYPE_TOOLTIPS
entry with the appropriate _LOD_NOTE_* suffix.

Stable canonical import paths:
    from varieties.tooltips import VARIETY_TOOLTIPS, SUBTYPE_TOOLTIPS

Backward-compat: `from surfaces import VARIETY_TOOLTIPS, SUBTYPE_TOOLTIPS` still works.
"""

from __future__ import annotations



# cleanup-deferred-findings-2026q3-e1 item 3 (M7 closure): per-subtype
# tooltip render-mode disclosures.  Three classes per the realtime-
# variety-render-e4b LOD architecture:
#   _LOD_NOTE_COARSE        — implicit surfaces with coarse_n > 0 (the
#                              default).  Drag fires a coarse-preview
#                              render at the lower grid (n=80 or n=100);
#                              release fires the full-resolution render.
#                              AI-15 Preview badge surfaces the fidelity
#                              state in the status bar.
#   _LOD_NOTE_HANSON        — Hanson parametric family.  The e2 typical_ms
#                              fast-path renders at full resolution on
#                              every debounced tick (no coarse preview —
#                              parametric meshes are too cheap to need
#                              an LOD downgrade).
#   _LOD_NOTE_RELEASE_ONLY  — Two-quadrics CI tube only (coarse_n=0
#                              opt-out per CONTEXT.md §4.4a — the f =
#                              Q₁²+Q₂²−ε² tube degenerates fast under
#                              coarse marching cubes).
_LOD_NOTE_COARSE = " · Drag = coarse preview; release = full render."
_LOD_NOTE_HANSON = (
    " · Renders full at every debounced drag tick (~80 ms; parametric)."
)
_LOD_NOTE_RELEASE_ONLY = (
    " · Release-only render (topology precision-sensitive; coarse drag "
    "preview would degrade the mesh)."
)


VARIETY_TOOLTIPS: dict[str, str] = {
    # realtime-variety-render-e4b (CAND-3): each family's tooltip closes with
    # a single sentence about the drag-time coarse-preview LOD behavior — the
    # AI-15 disclosure for users who hover the variety combo before/instead of
    # watching the status-bar Preview badge (CONTEXT.md §8.19).  Hanson CY3
    # surfaces use the e2 fast-path (full at every tick); the K3, Enriques,
    # Dwork, and Fano implicit subtypes use the e4b coarse-preview LOD.
    "K3 surface": (
        "A K3 surface is a compact complex surface with trivial canonical bundle "
        "and first Betti number 0. K3 surfaces are the 2-dimensional analogue of "
        "elliptic curves and play a central role in mirror symmetry. "
        "Drag-time renders use a coarse preview (n≈80–100); slider release "
        "re-renders at full resolution."
    ),
    "Enriques surface": (
        "An Enriques surface is the quotient of a K3 surface by a fixed-point-free "
        "involution. It has Euler number 12 and 2K=0. Four representative real "
        "affine models are provided here. "
        "Drag-time renders use a coarse preview (n=80); slider release re-renders "
        "at full resolution."
    ),
    "Calabi–Yau 3-fold": (
        "A Calabi–Yau 3-fold is a 6-real-dimensional space — it cannot be embedded "
        "in ℝ³. Each entry below is a 2D shadow, slice, or projection (in the "
        "Hanson-1994 tradition that produced the iconic 'Elegant Universe' image), "
        "not the 3-fold itself. "
        "Hanson parametric figures render at full resolution every drag tick; "
        "the Dwork pencil uses a coarse preview (n=100) during drag."
    ),
    "Fano 3-fold (ρ=1)": (
        "A smooth Fano 3-fold of Picard rank 1 (Iskovskikh's 'prime Fano "
        "threefold') is 6-real-dimensional. Each entry below is a 2D real "
        "slice obtained by fixing one or two ambient projective coordinates. "
        "The visualization tradition is essentially nonexistent — these are "
        "novel renderings. "
        "Most figures use a coarse preview (n=80) during drag and re-render "
        "at full resolution on release; the two-quadrics ε-tube is release-"
        "only (its topology is too fragile for any practical coarse floor)."
    ),
}

SUBTYPE_TOOLTIPS: dict[str, str] = {
    # K3
    "Fermat quartic": (
        "Fig. — | x⁴+y⁴+z⁴+… = c | "
        "3-parameter deformation of the classical Fermat quartic. "
        "Full octahedral O_h symmetry at α=β=γ=0."
        + _LOD_NOTE_COARSE
    ),
    "Kummer surface": (
        "Fig. — | (x²+y²+z²−μ²)² = λ·pqrs | "
        "Classic 16-nodal quartic (Hudson form). "
        "Smooth in the range 1 < μ² < 3."
        + _LOD_NOTE_COARSE
    ),
    # Enriques
    "Canonical sextic  [Fig. 1]": (
        "Figure 1 · S₄ tetrahedral symmetry | "
        "The Enriques 1896 canonical sextic: "
        "x²y²+x²z²+y²z²+x²y²z² + c·xyz·(1+x²+y²+z²) = 0."
        + _LOD_NOTE_COARSE
    ),
    "Diagonal λ-family  [Fig. 2]": (
        "Figure 2 · S₄→S₃ symmetry breaking | "
        "Dolgachev's λ-family: independent weights on the four "
        "'missing-one-variable' degree-6 monomials."
        + _LOD_NOTE_COARSE
    ),
    "Cayley symmetroid  [Fig. 3]": (
        "Figure 3 · Reye congruence model | "
        "Cayley quartic symmetroid: (x+y+z+xy+xz+yz)² = k·xyz. "
        "Historically the first Enriques surface (Reye 1882)."
        + _LOD_NOTE_COARSE
    ),
    "Icosahedral sextic  [Fig. 4]": (
        "Figure 4 · A₅ icosahedral symmetry | "
        "Endrass-normalized variant of Barth's 65-nodal sextic; "
        "τ≈0.18 gives Enriques-compatible node count."
        + _LOD_NOTE_COARSE
    ),
    # Calabi–Yau 3-fold
    "Hanson quintic  [Fig. 1]": (
        "Figure 1 · Hanson 1994, Z₅×Z₅ symmetry | "
        "The iconic CY₃ cross-section: z₁⁵ + z₂⁵ = 1 in C², projected to ℝ³. "
        "This is the image on the cover of 'The Elegant Universe.'"
        + _LOD_NOTE_HANSON
    ),
    "Hanson cubic torus  [Fig. 2]": (
        "Figure 2 · Hanson n=3 (torus) | "
        "z₁³ + z₂³ = 1, same construction with lower exponent. "
        "Genus 1 — visually a 9-patch torus."
        + _LOD_NOTE_HANSON
    ),
    "Hanson asymmetric (5,3)  [Fig. 3]": (
        "Figure 3 · Hanson asymmetric construction | "
        "z₁⁵ + z₂³ = 1 — Hanson's own (n₁ ≠ n₂) extension. "
        "Breaks the visual symmetry of the quintic."
        + _LOD_NOTE_HANSON
    ),
    "Dwork pencil  [Fig. 4]": (
        "Figure 4 · Implicit Dwork-pencil real slice | "
        "x⁵+y⁵+z⁵+2 = 5ψ·xyz. The ψ slider sweeps the canonical "
        "one-parameter CY₃ family; ψ=1 is the (real) conifold point; "
        "the five conifold points in ℂ are the fifth roots of unity."
        + _LOD_NOTE_COARSE
    ),
    # Fano 3-folds (Picard rank 1)
    "Klein cubic  [Fig. 1]": (
        "Figure 1 · PSL₂(11) symmetry, index 2 | "
        "Klein cubic V₃: V²W+W²X+X²Y+Y²Z+Z²V=0. Slice by Z=z₀. "
        "The unique smooth cubic 3-fold with order-660 symmetry."
        + _LOD_NOTE_COARSE
    ),
    "Segre cubic  [Fig. 2]": (
        "Figure 2 · S₆ symmetry of the parent (broken in the slice) | "
        "Σxᵢ=0 ∧ Σxᵢ³=0 in P⁵, eliminating x₅ and slicing by (x₃,x₄)=(a,b). "
        "Maximally nodal cubic 3-fold (10 nodes in the parent variety; "
        "visible singular points in the slice depend on (a,b))."
        + _LOD_NOTE_COARSE
    ),
    "Two-quadrics CI tube  [Fig. 3]": (
        "Figure 3 · Sum-of-squares tube of V₄, index 2 | "
        "f = Q₁²+Q₂²−ε² approximates the codim-2 intersection. "
        "Diagonal pencil with 5 distinct λ values."
        + _LOD_NOTE_RELEASE_ONLY
    ),
    "Sextic double solid  [Fig. 4]": (
        "Figure 4 · Index 1, genus 2 (Iskovskikh family 1-1) | "
        "z² + x⁶+y⁶+α·x²y²(x²+y²) = R⁶. Sign-flipped Fermat branch "
        "gives a closed compact double cover; α deforms the sextic equator."
        + _LOD_NOTE_COARSE
    ),
}
