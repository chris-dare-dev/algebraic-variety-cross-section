"""Algebraic variety generators + dataclass contracts + dispatch helpers.

Per restructure-feature-subpackages-2026q2-r2 Batch 5+: extracted from the
1811-LOC surfaces.py monolith into per-concern submodules.

Submodules (landed incrementally across batches 5-8):
    varieties.types     — ParamSpec + Surface dataclasses (Batch 5; AI-8)
    varieties.dispatch  — should_render_on_drag, dispatch_mode,
                          FAST_RENDER_THRESHOLD_MS (Batch 5)
    varieties._kernels  — 11 Numba @njit field kernels (Batch 6) [planned]
    varieties._marching — _marching_cubes_to_polydata + parametric helpers (Batch 6) [planned]
    varieties.k3        — fermat_quartic, kummer_surface (Batch 7) [planned]
    varieties.enriques  — 4 Enriques figures (Batch 7) [planned]
    varieties.calabi_yau — 4 CY3 generators (Batch 7) [planned]
    varieties.fano      — 4 Fano 3-folds (Batch 7) [planned]
    varieties.registry  — VARIETIES dict (Batch 8) [planned; AI-8 stable surface]
    varieties.tooltips  — VARIETY_TOOLTIPS, SUBTYPE_TOOLTIPS (Batch 8) [planned]

Convenience re-exports below (canonical = `from varieties.types import …`):
"""
from varieties.types import ParamSpec, Surface
from varieties.dispatch import (
    should_render_on_drag,
    dispatch_mode,
    FAST_RENDER_THRESHOLD_MS,
)

__all__ = [
    "ParamSpec",
    "Surface",
    "should_render_on_drag",
    "dispatch_mode",
    "FAST_RENDER_THRESHOLD_MS",
]
