# `export/` — variety cross-sections → 3-D-printable STL

Turns AVC surfaces into watertight STL solids sized for a printer build volume
(default preset: **Bambu Lab H2S**, 340 × 320 × 340 mm). Qt-free; depends only
on the public `varieties` registry.

## Quick start

```bash
# The headline: compact Fermat quartic  x^4 + y^4 + z^4 = 1, ~120 mm
python -m export --out fermat.stl

# Bound it by a sphere — "printed in a spherical pattern"
python -m export --out fermat_ball.stl --clip sphere --radius 0.85

# Kummer surface, cube-clipped, 150 mm on the longest axis
python -m export --variety "K3 surface" --subtype "Kummer surface" \
    --param mu_squared=1.6 --clip cube --radius 1.4 --size 150 --out kummer.stl

# What can I export, and which surfaces support clipping?
python -m export --list
```

Programmatic:

```python
from export import export_to_stl

info = export_to_stl(
    "fermat_ball.stl",
    variety="K3 surface", subtype="Fermat quartic",
    params={"c": 1.0},
    clip="sphere", radius=0.85, target_mm=150.0,
)
print(info.watertight, info.extent_mm)
```

## How it maps to the app's graph parameters

| App control            | CLI flag / API arg          |
|------------------------|-----------------------------|
| Variety / subtype      | `--variety` / `--subtype`   |
| Parameter sliders      | `--param name=value` (repeat) / `params={...}` |
| Clip Region = Sphere   | `--clip sphere --radius R`  |
| Clip Region = Cube     | `--clip cube --radius R`    |
| Clip Region = Off      | `--clip none` (default)     |

`--size` sets the longest-axis length in mm (`--size 0` fills the build volume
minus margin); oversize requests are clamped to fit, never silently overflowed.

## Why clipping is done in the field, not on the mesh

The app's on-screen clip cuts the surface and leaves **open** boundary loops —
fine to look at, not printable. Here the clip is a CSG intersection of the
variety solid `{f ≤ 0}` with the sphere/cube solid `{g ≤ 0}`, whose boundary is
the zero set of `max(f, g)`. A single Flying-Edges pass on `max(f, g)` (the same
iso-surfacer the generators use) yields a **watertight** solid with genuine
spherical / cubic caps. This needs the analytic field `f`, wired in
`FIELD_PROVIDERS`.

CSG sphere/cube clipping now covers **all 11 implicit surfaces** — every
marching-cubes variety in the registry:

| Family            | Subtypes with CSG clip                                            |
|-------------------|------------------------------------------------------------------|
| K3 surface        | Fermat quartic · Kummer surface                                  |
| Enriques surface  | Canonical sextic · Diagonal λ-family · Cayley symmetroid · Icosahedral sextic |
| Calabi–Yau 3-fold | Dwork pencil (the only implicit CY subtype)                     |
| Fano 3-fold (ρ=1) | Klein cubic · Segre cubic · Two-quadrics CI tube · Sextic double solid |

Each provider is a faithful numpy transcription of the generator's defining
field (cross-checked against the Numba kernel in `varieties/_kernels.py` by
`tests/test_csg_clip_families.py` at `rtol=atol=1e-9`, including all scalar
pre-computes: Endrass's φ²/1+2φ, the two-quadrics λ-pencil tuple, R⁶, ψ, …).
Use `supports_csg_clip(variety, subtype)` to probe whether a (variety, subtype)
pair can be CSG-clipped. To extend coverage, add an entry to `FIELD_PROVIDERS`.

The **3 parametric Hanson Calabi–Yau** subtypes (`Hanson quintic`,
`Hanson cubic torus`, `Hanson asymmetric (5,3)`) have **no** field provider:
they are open 2-surfaces in R³ with no enclosed solid, so `clip_for_print`
raises `NotImplementedError` for them by design. `supports_csg_clip` returns
`False` for these three.

Unclipped export works for **every** registry surface: implicit surfaces are
already watertight; parametric (Hanson Calabi–Yau) cross-sections are open
shells — they export, but Bambu Studio needs a shell/solidify modifier (or
print them as a thin surface).

## Print notes

- **Solid vs. shell:** a closed surface (e.g. Fermat) bounds a *solid* region;
  the slicer fills it. Use Bambu Studio's infill setting to hollow it out.
- **Small features:** node/cusp detail (Kummer's 16 nodes, Calabi–Yau handles)
  needs adequate print size + a fine nozzle; scale up via `--size` if they
  vanish.
- **Units:** the mesh is scaled so 1 unit = 1 mm; Bambu Studio imports STL in mm.
