"""Domain-clip math + helpers, pure-functional and Qt-free.

Per restructure-feature-subpackages-2026q2-r2 Batch 4: extracted the math
core of ``ViewPanel.clip_to_domain`` (formerly at panels/view.py, now at
_qt/panels/view.py) into a pure function that takes plain-data args.

ViewPanel keeps the widget reads (via ``domain_settings()``) and the public
``clip_to_domain(mesh)`` method; the method now delegates the math/PyVista
pipeline to ``cross_section.clip.clip_to_domain(mesh, mode, radius, show_overlay)``.

This is AI-2-compliant (the cross_section.clip module has no Qt dependencies).

AI-4 + AI-5 preserved: the function still uses ``clip_scalar(scalars=..., invert=True)``.
"""

from cross_section.clip import (
    DOMAIN_NONE,
    DOMAIN_SPHERE,
    DOMAIN_CUBE,
    clip_to_domain,
)

__all__ = ["DOMAIN_NONE", "DOMAIN_SPHERE", "DOMAIN_CUBE", "clip_to_domain"]
