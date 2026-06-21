"""CLI: turn an AVC variety cross-section into a print-ready STL.

Examples
--------
    # The headline: compact Fermat quartic  x^4 + y^4 + z^4 = 1, ~120 mm
    python -m export --out fermat.stl

    # Same surface bounded by a sphere ("printed in a spherical pattern")
    python -m export --out fermat_ball.stl --clip sphere --radius 0.85

    # A Kummer surface, cube-clipped, scaled to 150 mm on its longest axis
    python -m export --variety "K3 surface" --subtype "Kummer surface" \\
        --param mu_squared=1.6 --clip cube --radius 1.4 --size 150 --out kummer.stl

    # List everything the registry can export
    python -m export --list

    # Print to a Bambu Lab A1 mini (preset build volume), fill the plate
    python -m export --out fermat.stl --printer "Bambu Lab A1 mini" --size 0

    # Custom build volume (mm) instead of a preset
    python -m export --out fermat.stl --printer-dims 200 200 200

    # List the available printer presets
    python -m export --list-printers
"""

from __future__ import annotations

import argparse
import sys

from export.build_volumes import (
    DEFAULT_PRINTER,
    PRINTER_PRESETS,
    build_export_kwargs,
    list_presets,
)
from export.printable import (
    FIELD_PROVIDERS,
    ClipMode,
    export_to_stl,
)
from varieties.registry import VARIETIES


def _parse_params(pairs: list[str]) -> dict[str, float]:
    out: dict[str, float] = {}
    for pair in pairs:
        if "=" not in pair:
            raise SystemExit(f"--param expects name=value, got {pair!r}")
        name, _, value = pair.partition("=")
        try:
            out[name.strip()] = float(value)
        except ValueError:
            raise SystemExit(f"--param {name!r} value {value!r} is not a number")
    return out


def _print_catalog() -> None:
    print("Exportable surfaces (variety / subtype):\n")
    for variety, subtypes in VARIETIES.items():
        print(f"  {variety}")
        for subtype, surface in subtypes.items():
            clip_ok = (variety, subtype) in FIELD_PROVIDERS
            tag = "clip:sphere/cube" if clip_ok else "clip:unclipped-only"
            sliders = ", ".join(p.name for p in surface.params) or "(none)"
            print(f"    - {subtype:<32} [{tag}]  params: {sliders}")
    print(
        "\nSurfaces tagged 'unclipped-only' export their full mesh; CSG sphere/"
        "cube\nclipping is wired for the [clip:sphere/cube] surfaces "
        "(extend export.printable.FIELD_PROVIDERS for more)."
    )


def _print_printers() -> None:
    print("Printer presets (build volume, mm):\n")
    for name in list_presets():
        bv = PRINTER_PRESETS[name]
        default_tag = "  (default)" if name == DEFAULT_PRINTER else ""
        x, y, z = int(bv.x_mm), int(bv.y_mm), int(bv.z_mm)
        print(f"  {name:<22} {x} x {y} x {z}{default_tag}")
    print(
        f"\nDefault printer: {DEFAULT_PRINTER}. Use --printer NAME for a preset "
        "or\n--printer-dims X Y Z for a custom build volume (mutually exclusive)."
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="python -m export",
        description="Convert an algebraic-variety cross-section to a printable STL.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--list", action="store_true", help="list exportable surfaces and exit")
    p.add_argument(
        "--list-printers", action="store_true",
        help="list the available printer presets and exit",
    )
    p.add_argument("--variety", default="K3 surface", help="variety family (default: %(default)r)")
    p.add_argument("--subtype", default="Fermat quartic", help="subtype within the family")
    p.add_argument(
        "--param", action="append", default=[], metavar="NAME=VALUE",
        help="set a generator parameter (repeatable), e.g. --param c=1.0",
    )
    p.add_argument(
        "--clip", choices=[m.value for m in ClipMode], default=ClipMode.NONE.value,
        help="clip the printed solid to a shape (default: %(default)s)",
    )
    p.add_argument("--radius", type=float, default=1.0, help="clip radius / cube half-side (math units)")
    p.add_argument("--n", type=int, default=200, help="CSG sampling resolution per axis (clip only)")
    p.add_argument(
        "--size", type=float, default=120.0, dest="target_mm",
        help="target size of the longest axis in mm (default: %(default)s); "
             "use 0 to fill the build volume",
    )
    p.add_argument("--margin", type=float, default=5.0, help="build-volume margin per side, mm")
    p.add_argument("--ascii", action="store_true", help="write ASCII STL (default is binary)")
    p.add_argument(
        "--printer", metavar="NAME", default=None,
        help=f"printer preset build volume (default: {DEFAULT_PRINTER!r}); "
             "see --list-printers",
    )
    p.add_argument(
        "--printer-dims", type=float, nargs=3, metavar=("X", "Y", "Z"), default=None,
        help="custom build volume in mm (mutually exclusive with --printer)",
    )
    p.add_argument("--out", help="output .stl path")

    args = p.parse_args(argv)

    if args.list:
        _print_catalog()
        return 0
    if args.list_printers:
        _print_printers()
        return 0
    if not args.out:
        p.error("--out is required (or use --list / --list-printers)")

    if args.printer is not None and args.printer_dims is not None:
        p.error("--printer and --printer-dims are mutually exclusive")

    # --size 0 means "fill the build volume" (fit to plate).
    fit_to_plate = args.target_mm == 0
    dims = tuple(args.printer_dims) if args.printer_dims is not None else None
    try:
        export_kwargs = build_export_kwargs(
            printer=args.printer,
            dims=dims,
            target_mm=(None if fit_to_plate else args.target_mm),
            fit_to_plate=fit_to_plate,
            margin_mm=args.margin,
            binary=not args.ascii,
        )
    except (KeyError, ValueError) as exc:
        p.error(str(exc))

    result = export_to_stl(
        args.out,
        variety=args.variety,
        subtype=args.subtype,
        params=_parse_params(args.param),
        clip=args.clip,
        radius=args.radius,
        n=args.n,
        **export_kwargs,
    )

    print(f"Wrote {result.path}")
    print(f"  surface     : {args.variety} / {args.subtype}")
    print(f"  clip        : {result.clip}" + (f" (radius {args.radius})" if result.clip != "none" else ""))
    print(f"  mesh        : {result.n_points:,} vertices  {result.n_faces:,} triangles")
    print(f"  watertight  : {'yes' if result.watertight else 'NO  (slicer repair needed)'}")
    print(f"  size (mm)   : {result.extent_mm[0]} x {result.extent_mm[1]} x {result.extent_mm[2]}")
    print(f"  note        : {result.note}")
    if not result.watertight:
        print(
            "  ! Open mesh (parametric shell). In Bambu Studio use a shell/"
            "solidify\n    modifier, or print as a thin surface.",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
