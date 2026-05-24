"""Shim -- styles module moved to _qt.styles in r2 batch 3.

Restructure-feature-subpackages-2026q2-r2 Batch 3 commit 2. Removal milestone: M+1.

External callers using `from styles import …` continue to work via the
``__getattr__`` hook below, which emits a ``DeprecationWarning`` identifying
the new canonical path ``_qt.styles``.

Per shim-templates.md Template 2 (canonical form).
"""


def __getattr__(name: str):
    import warnings
    from _qt import styles as _new
    if hasattr(_new, name):
        warnings.warn(
            f"styles.{name} is deprecated; "
            f"import from _qt.styles instead.",
            DeprecationWarning, stacklevel=2)
        return getattr(_new, name)
    raise AttributeError(f"module 'styles' has no attribute {name!r}")
