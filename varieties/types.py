"""ParamSpec + Surface dataclass contracts for the AVC variety registry.

Per restructure-feature-subpackages-2026q2-r2 Batch 5: extracted from
surfaces.py (originally L42-L97) into a stable canonical path.

AI-8 (load-bearing): the Surface + ParamSpec dataclasses are the GUI
extension point. Any new variety goes through this contract. The shape is
deliberately stable across restructures; if you change anything here, also
update README "Extending the app" + CONTEXT.md §4 + every existing Surface
in varieties/registry.py.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

import pyvista as pv


@dataclass(frozen=True)
class ParamSpec:
    name: str        # kwarg name passed to the generator
    label: str       # human-readable label for the slider
    minimum: float
    maximum: float
    default: float
    step: float = 0.01
    suffix: str = ""
    description: str = ""


@dataclass
class Surface:
    label: str
    generate: Callable[..., pv.PolyData]
    params: list[ParamSpec] = field(default_factory=list)
    # realtime-variety-render-e2-s1 (CAND-8): measured typical generation
    # time in ms at the surface's default parameters.  0 means "unmeasured /
    # not fast" — every implicit (marching-cubes) generator keeps this default.
    # The three Hanson parametric generators carry their measured values so
    # `app.py`'s continuous-drag fast-path (see `should_render_on_drag`) can
    # speed-route them: a surface with 0 < typical_ms <= 80 renders at every
    # debounced drag tick; everything else stays release-only.  Defaulted
    # field placed after `params` so the dataclass contract stays clean
    # (AI-8 — the dataclass is not frozen; a trailing defaulted field is safe).
    typical_ms: int = 0
    # realtime-variety-render-e4b (CAND-3): coarse-preview-LOD floor for the
    # marching-cubes grid `n`.  0 means "no coarse-LOD" — the safe default for
    # any surface not explicitly opted in:
    #   * Hanson parametric generators (typical_ms > 0): always render full;
    #     they never go through marching cubes, so a coarse `n` is meaningless
    #     (AI-6 — three-layer guard, this default is the second layer).
    #   * Implicit generators whose topology is fragile at any practical
    #     coarse floor (e.g. fano_two_quadrics's ε-tube): stay opt-out so
    #     drag-time renders preserve mathematical honesty.
    # Implicit generators that DO opt in carry a per-surface `coarse_n` value
    # validated by tests/test_coarse_n.py's n-sweep — the floor is
    # the smallest `n` at which the surface's defining topological features
    # (Kummer's 16 nodes, Enriques double curves, etc.) survive the sweep.
    # Mutually exclusive in use with `typical_ms`: a Surface with
    # `typical_ms > 0` is parametric; a Surface with `coarse_n > 0` is
    # implicit-LOD-eligible.
    coarse_n: int = 0

    def defaults(self) -> dict[str, float]:
        return {p.name: p.default for p in self.params}


@runtime_checkable
class VarietyGenerator(Protocol):
    """Structural protocol for any callable that produces a PolyData mesh.

    Surface.generate is currently typed `Callable[..., pv.PolyData]` for backward
    compat with the frozen dataclass contract (AI-8). VarietyGenerator is an
    ADDITIVE structural alternative — type-checkers can verify any registered
    generator function satisfies this signature without changing the dataclass.

    Per refactor-pattern-scout Topic 4 + best-practices-scout focus area 2:
    Protocol is the correct instrument for generator/registry polymorphism
    (PEP-544). Dataclass and Protocol coexist cleanly; the existing 14
    generator functions in varieties/{k3,enriques,calabi_yau,fano}.py satisfy
    this Protocol structurally with zero changes.

    Per axis-12 honesty: this Protocol is ADDITIVE — it does NOT re-type
    Surface.generate, which would be a backward-incompatible change to the
    AI-8 frozen contract.
    """

    def __call__(self, **kwargs: float) -> pv.PolyData: ...
