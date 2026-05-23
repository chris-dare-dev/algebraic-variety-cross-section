# parameter_grid_panel.py — shim, slated for removal in milestone M+1
# (next /repository-architect run; move SHA: 7202c89)
# Canonical import: from panels.parameter_grid_panel import ParameterGridPanel


def __getattr__(name: str):
    import warnings
    from panels.parameter_grid_panel import __dict__ as _ns
    if name in _ns:
        warnings.warn(
            f"parameter_grid_panel.{name} is deprecated; "
            f"import from panels.parameter_grid_panel instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return _ns[name]
    raise AttributeError(
        f"module 'parameter_grid_panel' has no attribute {name!r}")
