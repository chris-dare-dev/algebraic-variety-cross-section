# parameters_panel.py — shim, slated for removal in milestone M+1
# (next /repository-architect run; move SHA: 2f7b4bf)
# Canonical import: from panels.parameters import ParametersPanel


def __getattr__(name: str):
    import warnings
    from panels.parameters import __dict__ as _ns
    if name in _ns:
        warnings.warn(
            f"parameters_panel.{name} is deprecated; "
            f"import from panels.parameters instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return _ns[name]
    raise AttributeError(
        f"module 'parameters_panel' has no attribute {name!r}")
