"""Shim — render_worker module moved to render.worker.

Restructure-feature-subpackages-2026q2-r2 Batch 2. Removal milestone: M+1.

External callers using `from render_worker import MeshWorker` continue to work
via the ``__getattr__`` hook below, which emits a ``DeprecationWarning``
identifying the new canonical path ``render.worker``.

Per shim-templates.md Template 2 (canonical form; uses ``getattr`` not
``__dict__`` access — verified correct for class objects like MeshWorker).
"""


def __getattr__(name: str):
    import warnings
    from render import worker as _new
    if hasattr(_new, name):
        warnings.warn(
            f"render_worker.{name} is deprecated; "
            f"import from render.worker instead.",
            DeprecationWarning, stacklevel=2)
        return getattr(_new, name)
    raise AttributeError(f"module 'render_worker' has no attribute {name!r}")
