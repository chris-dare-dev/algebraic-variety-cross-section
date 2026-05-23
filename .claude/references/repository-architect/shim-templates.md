# Shim templates

Canonical Python 3 `__getattr__` shim patterns for `/repository-architect` Phase 4. Used by the implementer when moving / renaming modules and symbols. Per scout-C §5, `__getattr__` is preferred over `from new import *` because:
- Lazy: target module imported only when accessed (no startup cost).
- Pinpoint warnings: `stacklevel=2` places the warning at the caller's site.
- Cleanly errors on bogus names rather than silently re-exporting.

## Template 1 — Per-symbol shim within a moved package

Use when a SUBPACKAGE renames or re-homes a symbol but the package itself still exists at the old location.

```python
# panels/__init__.py — backward-compat shim, remove in milestone M+1

_RENAMES = {
    # old name in panels.*        ->  new home (dotted import path + attribute)
    "ParameterGridPanel":         "panels.parameter_grid.ParameterGridPanel",
    "AppearancePanel":            "panels.appearance.AppearancePanel",
    "ViewPanel":                  "panels.view.ViewPanel",
}


def __getattr__(name: str):
    import importlib
    import warnings
    target = _RENAMES.get(name)
    if target is None:
        raise AttributeError(f"module 'panels' has no attribute {name!r}")
    module_path, _, attr = target.rpartition(".")
    warnings.warn(
        f"panels.{name} is deprecated; use {target} instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return getattr(importlib.import_module(module_path), attr)
```

## Template 2 — Whole-module shim (path itself moved)

Use when the entire module moved to a new path (e.g. `appearance_panel.py` -> `panels/appearance.py`).

```python
# appearance_panel.py — shim, slated for removal in milestone M+1


def __getattr__(name: str):
    import warnings
    from panels.appearance import __dict__ as _ns
    if name in _ns:
        warnings.warn(
            f"appearance_panel.{name} is deprecated; "
            f"import from panels.appearance instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return _ns[name]
    raise AttributeError(f"module 'appearance_panel' has no attribute {name!r}")
```

## Template 3 — Star-import-style shim (REFUSED)

**DO NOT USE THIS PATTERN.** Listed only as a reference for what NOT to do.

```python
# appearance_panel.py — WRONG SHIM PATTERN, do not use
import warnings
warnings.warn(
    "appearance_panel is deprecated; import from panels.appearance instead.",
    DeprecationWarning, stacklevel=2)
from panels.appearance import *  # noqa: F401, F403  ← BAD
```

Why this is wrong:
- The warning fires at IMPORT time, but `stacklevel=2` points at the SHIM file, not the caller.
- Static analyzers can't see what's re-exported.
- AI agent can't tell whether a symbol came from the old shim or the new module.
- Bogus name access silently returns nothing instead of raising AttributeError.

## Test recipe (paired with each shim)

```python
# tests/test_shims.py — regression-guard for shim integrity
import warnings


def test_appearance_panel_import_still_works():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        from appearance_panel import AppearancePanel  # noqa: F401
    assert any(
        issubclass(w.category, DeprecationWarning)
        and "panels.appearance" in str(w.message)
        for w in caught
    )
```

`warnings.catch_warnings(record=True)` is the canonical test recipe per the Python docs `warnings` module.

## Deprecation timeline for AVC

AVC is internal-only with no public API. Collapse the NumPy / pandas deprecation policies to:

- **Shim lives for one milestone after the move milestone.**
- **`DeprecationWarning` only** (`FutureWarning` is for user-facing behavior changes, not for renames).
- **Removal commit is SEPARATE from the move commit**, lands in milestone M+1, and references the move's commit hash in the message:
  ```
  refactor: remove appearance_panel shim (deprecated since {move-sha})
  ```

## Warning-category cheat sheet

| Category | When to use | Visibility |
|---|---|---|
| `DeprecationWarning` | Default for "you should change your code" (move/rename). | Ignored by default except in `__main__`; devs running tests see it. |
| `FutureWarning` | Behavior is changing (not a rename). | Visible by default. AVC almost never needs this. |
| `PendingDeprecationWarning` | Rarely useful — go straight to DeprecationWarning. | Ignored by default. |
| `UserWarning` | Avoid for refactor shims — use deprecation classes for searchability. | Default category. |

## Shim validation in CI

After every batch, `scripts/repository-architect/validate-shims.py` runs:
```bash
python -W error::DeprecationWarning -c "import <old-module>"
```
- Exit 1 with `DeprecationWarning` in stderr = PASS (shim is correct).
- Exit 0 = FAIL (no warning emitted; shim missing or silent).
- Exit 1 with non-`DeprecationWarning` exception = FAIL (shim broken).
