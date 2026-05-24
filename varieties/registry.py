"""VARIETIES registry — AI-8 GUI extension point.

Per restructure-feature-subpackages-2026q2-r2 Batch 8: extracted from surfaces.py
(originally L1550 in pre-r2; now the only substantial content remaining besides
the hub-shim re-exports).

AI-8 (load-bearing): VARIETIES is the dict-of-dicts that the parameter panel
reads to populate its dropdown.  The shape is {variety_name: {subtype_name: Surface}}.
Any new variety must be added here AND get a corresponding entry in
varieties.tooltips.VARIETY_TOOLTIPS + SUBTYPE_TOOLTIPS.

Stable canonical import path: `from varieties.registry import VARIETIES`.

(Per restructure-single-root-2026q2-r3 Batch 4: the `surfaces.py` hub-shim was
retired on 2026-05-24; the historical `from surfaces import VARIETIES` path
no longer exists. All callers now use the canonical path above.)
"""

from __future__ import annotations

from varieties.types import Surface
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

