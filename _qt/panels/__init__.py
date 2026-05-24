"""panels — AVC UI panel subpackage.

Canonical import paths (post restructure-full-audit-2026q2-r1 batch 4):
  from panels.appearance import AppearancePanel
  from panels.parameter_grid_panel import ParameterGridPanel
  from panels.parameters import ParametersPanel
  from panels.view import ViewPanel

Old root-level paths (appearance_panel, view_panel, parameters_panel,
parameter_grid_panel) are still importable via backward-compat shims at
the original paths; each shim emits a DeprecationWarning and is slated
for removal in the next /repository-architect milestone (M+1).
"""
