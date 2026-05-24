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

# Per restructure-feature-subpackages-2026q2-r2 Batch 8: VARIETIES registry and
# tooltips moved to varieties/registry.py and varieties/tooltips.py. Re-exported
# here for backward compatibility.
from varieties.registry import VARIETIES
from varieties.tooltips import VARIETY_TOOLTIPS, SUBTYPE_TOOLTIPS






# ---------------------------------------------------------------------------
# Numba JIT field-evaluation kernels (realtime-variety-render-e5 / CAND-2)
# ---------------------------------------------------------------------------
# Fermat quartic — generalized to the Lamé / superquadric family
# ---------------------------------------------------------------------------


