# view_panel.py — shim, slated for removal in milestone M+1
# (next /repository-architect run; move SHA: 8c555f7)
# Canonical import: from panels.view import ViewPanel


def __getattr__(name: str):
    import warnings
    from panels.view import __dict__ as _ns
    if name in _ns:
        warnings.warn(
            f"view_panel.{name} is deprecated; "
            f"import from panels.view instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return _ns[name]
    raise AttributeError(
        f"module 'view_panel' has no attribute {name!r}")
