"""Mesh generators for K3, Enriques, and Calabi–Yau (3-fold) surfaces.

Each surface is a `Surface` carrying a generator function and a list of
`ParamSpec` describing its tunable parameters. Implicit surfaces are
extracted via marching cubes on a sampled scalar field. Parametric
surfaces (used for the Hanson-style Calabi–Yau cross-sections) are
built directly from a 2D parameter grid via `_grid_to_polydata`.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from typing import Callable

import numpy as np
import pyvista as pv

# realtime-variety-render-e5 (CAND-2): Numba JIT field-evaluation kernels.
# numba is a pure compute dependency (BSD-2-Clause) — no renderer, AI-1 clean.
# THREADING_LAYER MUST be set before the first parallel kernel is *called*;
# module-import time is the safe, spike-proven placement (kernels are only
# called at generate() time, long after import).  `workqueue` is Numba's
# always-available, dependency-free layer — it keeps Numba's thread pool
# separate from VTK's SMP pool so a kernel and a Flying Edges contour running
# back-to-back in the e4 worker do not contend (e5 Numba arm64 spike §6).
#
# NOTE — intentional process-global side-effect: assigning
# `numba.config.THREADING_LAYER` mutates Numba's *process-wide* config.
# Importing `surfaces` therefore pins the threading layer for the whole
# process.  This is benign and desired here — `surfaces` is imported only by
# the AVC app and its test suite, both of which want `workqueue` — but a
# future in-process embedding that also uses Numba with a different layer
# expectation would have its choice silently decided by import order.  See
# CONTEXT.md §3.
import numba

# B6: numba threading-layer + @njit import removed -- now lives in varieties/_kernels.py
# which is imported below; the threading-layer side effect fires before any @njit
# decorated function in this module is referenced.


# Per restructure-feature-subpackages-2026q2-r2 Batch 5: ParamSpec and Surface
# moved to varieties/types.py; should_render_on_drag, dispatch_mode, and
# FAST_RENDER_THRESHOLD_MS moved to varieties/dispatch.py. Re-exported here for
# backward-compatibility (existing `from surfaces import ParamSpec` keeps working).
from varieties.types import ParamSpec, Surface
from varieties.dispatch import (
    should_render_on_drag,
    dispatch_mode,
    FAST_RENDER_THRESHOLD_MS,
)

# Per restructure-feature-subpackages-2026q2-r2 Batch 6: marching pipeline helpers
# and 11 Numba kernels moved to varieties/_marching.py and varieties/_kernels.py.
# Re-exported here for backward compatibility.  CRITICAL: importing _kernels eagerly
# ensures `numba.config.THREADING_LAYER = "workqueue"` fires before any generator
# below uses @njit-decorated functions.
from varieties._marching import (
    _marching_cubes_to_polydata,
    _grid_to_polydata,
    _concat_polydata,
    _hanson_cross_section,
)
from varieties._kernels import (
    _fermat_field_kernel,
    _kummer_field_kernel,
    _enriques_fig1_field_kernel,
    _enriques_fig2_field_kernel,
    _enriques_fig3_field_kernel,
    _enriques_fig4_field_kernel,
    _dwork_field_kernel,
    _klein_cubic_field_kernel,
    _segre_cubic_field_kernel,
    _two_quadrics_field_kernel,
    _sextic_double_solid_field_kernel,
)

# Per restructure-feature-subpackages-2026q2-r2 Batch 7: 14 generator functions
# + 14 _PARAMS constants moved to varieties/{k3,enriques,calabi_yau,fano}.py.
# Re-exported here for backward compatibility (tests + app.py still import via
# `from surfaces import ...`).
from varieties.k3 import (
    fermat_quartic, FERMAT_PARAMS,
    kummer_surface, KUMMER_PARAMS,
)
from varieties.enriques import (
    enriques_figure_1, ENRIQUES_FIGURE_1_PARAMS,
    enriques_figure_2, ENRIQUES_FIGURE_2_PARAMS,
    enriques_figure_3, ENRIQUES_FIGURE_3_PARAMS,
    enriques_figure_4, ENRIQUES_FIGURE_4_PARAMS,
)
from varieties.calabi_yau import (
    calabi_yau_quintic, CALABI_YAU_QUINTIC_PARAMS,
    calabi_yau_cubic, CALABI_YAU_CUBIC_PARAMS,
    calabi_yau_asymmetric, CALABI_YAU_ASYMMETRIC_PARAMS,
    calabi_yau_dwork, CALABI_YAU_DWORK_PARAMS,
)
from varieties.fano import (
    fano_klein_cubic, FANO_KLEIN_CUBIC_PARAMS,
    fano_segre_cubic, FANO_SEGRE_CUBIC_PARAMS,
    fano_two_quadrics, FANO_TWO_QUADRICS_PARAMS,
    fano_sextic_double_solid, FANO_SEXTIC_DOUBLE_SOLID_PARAMS,
)






# ---------------------------------------------------------------------------
# Numba JIT field-evaluation kernels (realtime-variety-render-e5 / CAND-2)
# ---------------------------------------------------------------------------
# Fermat quartic — generalized to the Lamé / superquadric family
# ---------------------------------------------------------------------------


VARIETIES: dict[str, dict[str, Surface]] = {
    # realtime-variety-render-e4b (CAND-3): per-surface `coarse_n` floors set
    # below opt 9 of 11 implicit generators into the drag-time coarse-preview
    # LOD path.  Values measured by agent-a's empirical n-sweep on the dev
    # machine (see .claude/notes/milestones/realtime-variety-render-e4b/
    # research/agent-a-brief.md §4.1); each floor is validated by
    # tests/test_coarse_n.py.  Two implicit surfaces stay opt-out:
    # `fano_two_quadrics` (ε-tube width ≈ voxel spacing at coarse n — see the
    # brief's §4.1 opt-out justification).  Hanson generators leave coarse_n=0
    # (AI-6 layer 2 — the worker dispatch's coarse-injection is a no-op).
    "K3 surface": {
        "Fermat quartic": Surface(
            "Fermat quartic", fermat_quartic, FERMAT_PARAMS, coarse_n=80,
        ),
        "Kummer surface": Surface(
            "Kummer surface", kummer_surface, KUMMER_PARAMS, coarse_n=100,
        ),
    },
    "Enriques surface": {
        "Canonical sextic  [Fig. 1]": Surface(
            "Enriques sextic (canonical, S₄ symmetry)",
            enriques_figure_1, ENRIQUES_FIGURE_1_PARAMS, coarse_n=80,
        ),
        "Diagonal λ-family  [Fig. 2]": Surface(
            "Enriques sextic (diagonal λ-family)",
            enriques_figure_2, ENRIQUES_FIGURE_2_PARAMS, coarse_n=80,
        ),
        "Cayley symmetroid  [Fig. 3]": Surface(
            "Cayley quartic symmetroid (Reye cover)",
            enriques_figure_3, ENRIQUES_FIGURE_3_PARAMS, coarse_n=80,
        ),
        "Icosahedral sextic  [Fig. 4]": Surface(
            "Barth-style icosahedral sextic (A₅ symmetry)",
            enriques_figure_4, ENRIQUES_FIGURE_4_PARAMS, coarse_n=80,
        ),
    },
    "Calabi–Yau 3-fold": {
        # realtime-variety-render-e2-s1 (CAND-8): typical_ms values measured
        # off-screen on the dev machine (pv.OFF_SCREEN=True, time.perf_counter,
        # median of 7 runs at the ParamSpec default parameters): quintic ~39 ms,
        # cubic torus ~11 ms, asymmetric ~18 ms.  All well under the 80 ms
        # fast-path threshold, so all three render continuously during drag.
        # AI-6 (e4b): Hanson generators MUST keep `coarse_n=0` (the default) —
        # they are parametric and never go through marching cubes; a coarse
        # `n` would be meaningless.
        "Hanson quintic  [Fig. 1]": Surface(
            "Hanson quintic CY cross-section (n=5)",
            calabi_yau_quintic, CALABI_YAU_QUINTIC_PARAMS,
            typical_ms=39,
        ),
        "Hanson cubic torus  [Fig. 2]": Surface(
            "Hanson cross-section (n=3, torus)",
            calabi_yau_cubic, CALABI_YAU_CUBIC_PARAMS,
            typical_ms=11,
        ),
        "Hanson asymmetric (5,3)  [Fig. 3]": Surface(
            "Hanson cross-section (n₁=5, n₂=3)",
            calabi_yau_asymmetric, CALABI_YAU_ASYMMETRIC_PARAMS,
            typical_ms=18,
        ),
        "Dwork pencil  [Fig. 4]": Surface(
            "Dwork pencil real slice (ψ-family)",
            calabi_yau_dwork, CALABI_YAU_DWORK_PARAMS, coarse_n=100,
        ),
    },
    "Fano 3-fold (ρ=1)": {
        "Klein cubic  [Fig. 1]": Surface(
            "Klein cubic threefold V₃ (PSL₂(11) symmetry)",
            fano_klein_cubic, FANO_KLEIN_CUBIC_PARAMS, coarse_n=80,
        ),
        "Segre cubic  [Fig. 2]": Surface(
            "Segre cubic (S₆ symmetry, max-nodal)",
            fano_segre_cubic, FANO_SEGRE_CUBIC_PARAMS, coarse_n=80,
        ),
        "Two-quadrics CI tube  [Fig. 3]": Surface(
            # OPT-OUT (coarse_n=0): the ε-tube width (default ε=0.18) is
            # close to the voxel spacing at any practical coarse floor — at
            # n=100 the spacing is ~0.04, which produces swiss-cheese
            # artifacts the existing ε<0.08 RuntimeWarning already calls out
            # at production `n`.  Coarse-LOD would render a topologically
            # misleading drag preview here, so this surface stays release-
            # only (e4b agent-a brief §4.1).
            "Two-quadrics CI tube V₄ (ε-tube around Q₁∩Q₂, not the actual CI)",
            fano_two_quadrics, FANO_TWO_QUADRICS_PARAMS,
        ),
        "Sextic double solid  [Fig. 4]": Surface(
            "Sextic double solid V₁ (sign-flipped Fermat branch)",
            fano_sextic_double_solid, FANO_SEXTIC_DOUBLE_SOLID_PARAMS,
            coarse_n=80,
        ),
    },
}

# ---------------------------------------------------------------------------
# Tooltips for the variety / subtype dropdowns (used by the GUI)
# ---------------------------------------------------------------------------

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
