# appearance_panel.py — shim, slated for removal in milestone M+1
# (next /repository-architect run; move SHA: ffd358a)
# Canonical import: from panels.appearance import AppearancePanel


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
    raise AttributeError(
        f"module 'appearance_panel' has no attribute {name!r}")
