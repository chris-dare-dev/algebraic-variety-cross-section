"""Shim -- ui_helpers module moved to _qt.ui_helpers in r2 batch 3.

Restructure-feature-subpackages-2026q2-r2 Batch 3 commit 2. Removal milestone: M+1.

External callers using `from ui_helpers import …` continue to work via the
``__getattr__`` hook below, which emits a ``DeprecationWarning`` identifying
the new canonical path ``_qt.ui_helpers``.

Per shim-templates.md Template 2 (canonical form).

Designer note (per v2 MEDIUM-6): the module name `ui_helpers` was preserved
(scout-B/C had suggested renaming to `helpers` inside `_qt/`, but keeping the
name minimizes churn and matches r1 MEDIUM-2 precedent of "don't rename during
a move unless required for correctness").
"""


def __getattr__(name: str):
    import warnings
    from _qt import ui_helpers as _new
    if hasattr(_new, name):
        warnings.warn(
            f"ui_helpers.{name} is deprecated; "
            f"import from _qt.ui_helpers instead.",
            DeprecationWarning, stacklevel=2)
        return getattr(_new, name)
    raise AttributeError(f"module 'ui_helpers' has no attribute {name!r}")
