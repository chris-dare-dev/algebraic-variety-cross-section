"""AVC STL-export subpackage — turn variety cross-sections into printable solids.

This package is a thin *consumer* layer above ``varieties`` (it reads the
``VARIETIES`` registry and calls the public generators). It is Qt-free (AI-2)
and has no dependency on ``_qt`` / ``render`` — so it imports cleanly in the
test suite and from a plain ``python -m export`` invocation.

Public API (see ``export.printable``):

    BuildVolume, BAMBU_H2S          — printer build-volume model + preset
    export_to_stl(...)              — one-call: registry surface -> .stl on disk
    generate_surface_mesh(...)      — registry lookup + generator call
    clip_for_print(...)             — watertight sphere/cube CSG clip
    fit_to_build_volume(...)        — scale + center math into millimetres
    save_stl(...)                   — write a PolyData as binary/ASCII STL
    FIELD_PROVIDERS                 — surfaces wired for CSG clipping
"""

from __future__ import annotations

from export.printable import (
    BAMBU_H2S,
    BuildVolume,
    FIELD_PROVIDERS,
    ClipMode,
    clip_for_print,
    export_to_stl,
    fit_to_build_volume,
    generate_surface_mesh,
    save_stl,
    supports_csg_clip,
)
from export.build_volumes import (
    DEFAULT_PRINTER,
    PRINTER_PRESETS,
    build_export_kwargs,
    custom_build_volume,
    get_build_volume,
    list_presets,
    resolve_build_volume,
)

__all__ = [
    # core pipeline (export.printable)
    "BAMBU_H2S",
    "BuildVolume",
    "ClipMode",
    "FIELD_PROVIDERS",
    "clip_for_print",
    "export_to_stl",
    "fit_to_build_volume",
    "generate_surface_mesh",
    "save_stl",
    "supports_csg_clip",
    # build-volume presets + sizing (export.build_volumes)
    "DEFAULT_PRINTER",
    "PRINTER_PRESETS",
    "build_export_kwargs",
    "custom_build_volume",
    "get_build_volume",
    "list_presets",
    "resolve_build_volume",
]
