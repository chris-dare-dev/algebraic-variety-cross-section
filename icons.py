"""Shim -- icons module moved to _qt.icons in r2 batch 3.

Restructure-feature-subpackages-2026q2-r2 Batch 3 commit 2. Removal milestone: M+1.

External callers using `from icons import …` continue to work via the
``__getattr__`` hook below, which emits a ``DeprecationWarning`` identifying
the new canonical path ``_qt.icons``.

Per shim-templates.md Template 2 (canonical form; uses ``getattr`` not
``__dict__`` access -- verified correct for class objects).
"""


def __getattr__(name: str):
    import warnings
    from _qt import icons as _new
    if hasattr(_new, name):
        warnings.warn(
            f"icons.{name} is deprecated; "
            f"import from _qt.icons instead.",
            DeprecationWarning, stacklevel=2)
        return getattr(_new, name)
    raise AttributeError(f"module 'icons' has no attribute {name!r}")
