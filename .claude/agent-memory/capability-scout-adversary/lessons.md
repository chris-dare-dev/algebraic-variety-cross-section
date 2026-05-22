# Adversary Scout Lessons

## Lesson 1 — Run a timing probe before writing any gap

The informal "~0.5 s" estimate in CONTEXT.md is wrong for heavy surfaces (Enriques Fig 4, Dwork pencil measure at 1.2–1.45 s). A 10-line off-screen probe with `time.perf_counter()` around individual steps (`field eval`, `marching_cubes`, `clean`, `taubin`, `compute_normals`, `add_mesh`, `render`) replaces informed guesswork with calibrated data. This data anchors every severity rating and every speedup estimate in the brief, and catches surprises (e.g., `add_mesh` + `render` are negligible — 9 ms + <1 ms — while `mesh.clean()` scales badly with vert count at 103 ms for a 400K-vert mesh).

**Pattern:** Always open an adversary brief by running `pv.OFF_SCREEN = True` + `time.perf_counter()` around each sub-step of `_marching_cubes_to_polydata`. This is AI-3 safe (no `MainWindow`, no Qt). The numbers go directly into Section 8 of the brief and calibrate every other gap.

## Lesson 2 — Differentiate pipelines before proposing architecture changes

The Hanson parametric pipeline (27–38 ms) and the implicit marching-cubes pipeline (650–1450 ms) are wired identically by `ParametersPanel` and `_render_current`. The fastest win for real-time update is NOT architectural (no worker thread, no JIT) — it is wiring the fast pipeline's `valueChanged` signal differently from the slow pipeline's `sliderReleased` signal. Always check whether the codebase already has a faster pipeline hiding behind uniform wiring before proposing heavier solutions.

## Lesson 3 — The "drop vs queue" re-entrancy pattern is a separate gap from the "synchronous" gap

A `_computing` guard that drops intermediate updates (C-2) compounds the synchronous-main-thread gap (C-1) into a "stale final frame" bug: the user can finish a drag at a new position and see no update until they drag again. These are two independent bugs with independent fixes. Flag them separately in the brief and make clear that C-2 (add `_pending_render` flag) is a 2-line fix that can ship before C-1 (worker thread).

## Lesson 4 — Calibrate the "What peers/SOTA expect" section to actual peer behavior, not aspirational

Surfer (Imaginary.org) genuinely does render a low-res preview during slider drag. Mathematica `Manipulate` genuinely debounces and executes the latest update. These are factual peer behaviors that justify the HIGH/CRITICAL ratings. Unverified claims ("peers all do X") erode the brief's credibility. Stick to peers listed in source-registry.md with concrete behaviors.

## Lesson 5 — The coarse-preview LOD API is already partially present

`_marching_cubes_to_polydata` already accepts `smooth_iter: int = 20` as an optional parameter (`surfaces.py:53`). Passing `smooth_iter=0` is already handled (`surfaces.py:94`). The API surface for LOD is half-done; only the `n` override and the call-site wiring are missing. When writing gap H-1 (coarse LOD), cite this existing affordance so the implementer knows the delta is small.
