# Lessons — capability-scout-math-research

## Lesson 1 (2026-05-21, realtime-variety-render run)

**When surveying interactive-rendering techniques for implicit algebraic surfaces, always characterize the cost split between field evaluation and mesh extraction before recommending any acceleration.**

For degree-4–6 polynomial fields on ~240³ grids, NumPy broadcasting field evaluation dominates (~200–350 ms) over `skimage` marching cubes extraction (~50–100 ms). Techniques that only accelerate the MC step (Flying Edges: 3–5× speedup on MC alone) yield < 2× overall improvement, while techniques that accelerate field evaluation (Numba JIT: 10–30× on eval) or reduce the grid size (LOD: up to 64×) address the true bottleneck. **Always profile the split, not just the total, before ranking candidates.**

## Lesson 2 (2026-05-21, realtime-variety-render run)

**Parameter-space mesh interpolation is always an AI-15 violation without a prominent disclaimer, regardless of visual quality.**

Interpolating between precomputed meshes at different parameter values produces geometry that corresponds to no algebraic equation. For surfaces with parameter-dependent topology (Kummer nodes, Dwork conifold, Enriques double curves), the interpolated mesh will have provably incorrect topology at intermediate parameter values. This must be treated as a high-risk AI-15 issue in any math-education visualization context. The capability-scout-math-research role should flag this pattern immediately and prominently whenever it appears as a candidate technique.

## Lesson 3 (2026-05-21, realtime-variety-render run)

**Coarse-grid preview is AI-15 compliant only if the disclaimer is UI-visible and the UI clearly differentiates "preview" from "true variety."**

The mathematical question is not just "is this fast?" but "what is the user shown and what do they believe they are looking at?" For a coarse preview at n=60 (grid spacing ~5× coarser than production), topology may be misrepresented for surfaces with thin necks, nodes near the grid scale, or singularities. The Stander-Hart / Plantinga-Vegter topological guarantee literature provides the mathematical framework for bounding safe coarse resolutions, but requires per-surface analysis. In the absence of that analysis, the status bar must explicitly label the preview as approximate.
