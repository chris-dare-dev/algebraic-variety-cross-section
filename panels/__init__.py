"""Hub shim — panels/ subpackage moved to _qt/panels/ in r2 batch 3.

Per refactor-pattern brief §5.4 and adversary v2 HIGH-1: tests/test_clip_domain.py
and tests/test_styles_palette.py import `from panels.view import ViewPanel` and
`import panels.appearance` at module scope. Without this hub shim, B3's
git mv would have broken those tests at collect time.

The hub shim catches attribute access for the 4 panel submodules and forwards
to _qt.panels.* with DeprecationWarning. External callers using
`from panels.view import ViewPanel` continue to work.

Removal milestone: M+1 (one /repository-architect cycle after this).
"""

_PANELS = {
    "appearance":             "_qt.panels.appearance",
    "view":                   "_qt.panels.view",
    "parameters":             "_qt.panels.parameters",
    "parameter_grid_panel":   "_qt.panels.parameter_grid_panel",
}


def __getattr__(name: str):
    """Forward panels.<name> attribute access to _qt.panels.<name>.

    Handles two cases:
      1. `import panels.view` then `panels.view.ViewPanel` — Python imports the
         submodule (which exists at _qt/panels/view.py); __getattr__ may not fire.
      2. `from panels.view import ViewPanel` — Python imports the submodule by
         walking the parent's namespace; __getattr__ fires for unknown attrs.
    """
    import importlib
    import warnings
    target = _PANELS.get(name)
    if target is None:
        raise AttributeError(f"module 'panels' has no attribute {name!r}")
    warnings.warn(
        f"panels.{name} is deprecated; use {target} instead.",
        DeprecationWarning, stacklevel=2)
    return importlib.import_module(target)
