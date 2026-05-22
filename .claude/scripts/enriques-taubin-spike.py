#!/usr/bin/env python3
"""Spike: measure second Taubin-pass cost on Enriques canonical sextic.

Spike milestone: ``enriques-taubin-spike-2026q2-e1``.
This script does NOT modify production code — it measures the proposed
double-Taubin path in isolation and writes the timing log.  The
production code change (Path A or Path B) is decided by the implementer
based on these numbers.

Outputs:
  - /tmp/enriques-taubin-spike.txt
  - .claude/notes/milestones/enriques-taubin-spike-2026q2-e1/artifacts/timing-log.txt

Budget per CONTEXT.md §4.4 / §9 / roadmap §4 [MUST]: ~500ms generate-only.

Conditional outcome:
  - Path A: median double-pass <= 500ms → ship 2nd Taubin pass on
    figs 1+2 + bounds*1.05 padding universal.
  - Path B: median double-pass >  500ms → ship bounds*1.05 only;
    defer 2nd Taubin to a future "HQ smoothing" toggle milestone.
"""
from __future__ import annotations

import os
import statistics
import sys
import time

# Make the repo root importable so `import surfaces` and
# `from skimage import measure` work the same as in production.
_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
sys.path.insert(0, _REPO_ROOT)

import numpy as np  # noqa: E402
import pyvista as pv  # noqa: E402
from skimage import measure  # noqa: E402

import surfaces  # noqa: E402


def _enriques_double_pass(c: float = 1.0, n: int = 240, bounds: float = 1.8) -> pv.PolyData:
    """Inlined Enriques fig-1 generator with a SECOND Taubin pass and
    bounds * 1.05 padding.

    This mirrors the proposed Path A production code without modifying
    `surfaces.py`.  Field sampling + marching cubes are identical to
    `enriques_figure_1`; the only differences are (a) `bounds` is
    multiplied by 1.05 (wing-tip truncation fix), (b) a second
    `smooth_taubin(n_iter=40, pass_band=0.05)` call is added after
    the existing `smooth_taubin(n_iter=20, pass_band=0.1)` pass.
    """
    padded = bounds * 1.05  # 1.8 * 1.05 = 1.89
    g = np.linspace(-padded, padded, n)
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    X2, Y2, Z2 = X * X, Y * Y, Z * Z

    F = (
        X2 * Y2 + X2 * Z2 + Y2 * Z2 + X2 * Y2 * Z2
        + c * (X * Y * Z) * (1.0 + X2 + Y2 + Z2)
    )
    F = np.clip(F, -10.0, 10.0)

    # Inline mirror of _marching_cubes_to_polydata, then add the 2nd pass.
    spacing = (2 * padded / (n - 1),) * 3
    if F.min() > 0 or F.max() < 0:
        raise ValueError("Spike: no real zero set at default params")
    verts, faces, normals, _ = measure.marching_cubes(F, level=0.0, spacing=spacing)
    verts -= padded
    n_faces = faces.shape[0]
    pv_faces = np.empty((n_faces, 4), dtype=np.int64)
    pv_faces[:, 0] = 3
    pv_faces[:, 1:] = faces
    mesh = pv.PolyData(verts, pv_faces.ravel())
    mesh.point_data["Normals"] = normals.astype(np.float32)
    mesh = mesh.clean()

    # First pass — identical to production.
    if mesh.n_points > 0:
        mesh = mesh.smooth_taubin(n_iter=20, pass_band=0.1)
    # Second pass — the spike.  Lower-frequency, more aggressive
    # smoothing to attenuate residual double-curve sawtooth.
    if mesh.n_points > 0:
        mesh = mesh.smooth_taubin(n_iter=40, pass_band=0.05)

    if mesh.n_points > 0:
        mesh = mesh.compute_normals(
            cell_normals=False, point_normals=True,
            consistent_normals=True, auto_orient_normals=False,
            split_vertices=False,
        )
    return mesh


def measure_runs(fn, label: str, n_runs: int) -> tuple[float, list[float], pv.PolyData]:
    """Time `fn()` n_runs times and return (median_ms, all_times_ms, last_mesh)."""
    times: list[float] = []
    last_mesh = None
    for i in range(n_runs):
        t0 = time.perf_counter()
        last_mesh = fn()
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        times.append(elapsed_ms)
        print(
            f"  {label} run {i+1}/{n_runs}: {elapsed_ms:7.1f} ms  "
            f"({last_mesh.n_points:>6d} pts, {last_mesh.n_faces:>6d} faces)"
        )
    med = statistics.median(times)
    print(f"  → MEDIAN {label}: {med:7.1f} ms\n")
    return med, times, last_mesh


def main() -> int:
    n_runs = 7
    budget_ms = 500.0

    print("=" * 60)
    print("Enriques Taubin Spike — enriques-taubin-spike-2026q2-e1")
    print("=" * 60)
    print(f"N runs per case: {n_runs}; taking median to filter outliers")
    print(f"Budget: {budget_ms:.0f} ms (generate-only, per CONTEXT.md §4.4)")
    print()

    # Warm up import + JIT caches by discarding a first call from each path.
    print("Warming up caches...")
    _ = surfaces.enriques_figure_1(c=1.0)
    _ = _enriques_double_pass(c=1.0)
    print("Done.\n")

    # Baseline: production single-pass at original bounds=1.8.
    print("--- Baseline (PRODUCTION: single Taubin pass, bounds=1.8) ---")
    med_single, single_times, _ = measure_runs(
        lambda: surfaces.enriques_figure_1(c=1.0),
        "SINGLE",
        n_runs,
    )

    # Spike: proposed double-pass at bounds*1.05=1.89.
    print("--- Spike (PROPOSED: double Taubin pass, bounds=1.89) ---")
    med_double, double_times, _ = measure_runs(
        _enriques_double_pass,
        "DOUBLE",
        n_runs,
    )

    overhead_ms = med_double - med_single
    overhead_pct = (overhead_ms / med_single) * 100.0 if med_single > 0 else 0.0
    under_budget = med_double <= budget_ms
    headroom_ms = budget_ms - med_double

    print("=" * 60)
    print("Result")
    print("=" * 60)

    result_lines = [
        "=== Enriques Taubin Spike Results ===",
        "",
        "Milestone: enriques-taubin-spike-2026q2-e1",
        "Date:      2026-05-22",
        f"Runs/case: {n_runs} (median used for decision)",
        "Surface:   surfaces.enriques_figure_1(c=1.0), n=240",
        "Budget:    500.0 ms (generate-only)",
        "",
        "Single-pass (production, bounds=1.8):",
        f"  raw times (ms): {[round(x, 1) for x in single_times]}",
        f"  median:         {med_single:.1f} ms",
        "",
        "Double-pass (proposed, bounds=1.89):",
        f"  raw times (ms): {[round(x, 1) for x in double_times]}",
        f"  median:         {med_double:.1f} ms",
        "",
        f"Second-pass median overhead: {overhead_ms:+.1f} ms "
        f"({overhead_pct:+.1f}%)",
        f"Budget headroom (500 - double): {headroom_ms:+.1f} ms",
        "",
        f"Outcome: {'PATH A (UNDER BUDGET)' if under_budget else 'PATH B (OVER BUDGET)'}",
        f"Decision: {'Ship 2nd Taubin pass on figs 1+2 + bounds*1.05 universal' if under_budget else 'Ship bounds*1.05 only; defer 2nd pass to HQ-toggle milestone'}",
    ]
    log_text = "\n".join(result_lines)
    print()
    print(log_text)
    print()

    tmp_path = "/tmp/enriques-taubin-spike.txt"
    artifacts_path = os.path.abspath(
        os.path.join(
            _HERE,
            "..",
            "notes",
            "milestones",
            "enriques-taubin-spike-2026q2-e1",
            "artifacts",
            "timing-log.txt",
        )
    )
    os.makedirs(os.path.dirname(artifacts_path), exist_ok=True)
    for path in (tmp_path, artifacts_path):
        with open(path, "w") as f:
            f.write(log_text + "\n")
        print(f"Written: {path}")

    return 0 if under_budget else 1  # exit-code mirrors Path A/B for CI use


if __name__ == "__main__":
    sys.exit(main())
