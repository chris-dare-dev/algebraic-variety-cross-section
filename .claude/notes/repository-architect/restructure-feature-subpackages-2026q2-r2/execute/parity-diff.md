# Parity diff report — restructure-feature-subpackages-2026q2-r2

## Test collection diff
  - baseline tests: 503
  - post     tests: 506
  - delta:          3
  - removed (in pre, not post): 4
  - added   (in post, not pre): 7

## Coverage diff (totals)
  - baseline coverage XML missing or unparseable

## Import-time diff
  - baseline: 667.1 ms
  - post:     639.5 ms
  - delta:    -4.1%

## Star-imports diff
  - new star-imports introduced: 0
  - star-imports removed:        0

## Symbol relocation audit (top-level def/class only)
  - symbols whose location changed: 128
    ~ DebounceCounter: ['ui_helpers.py:37'] -> ['_qt/ui_helpers.py:37']
    ~ Debouncer: ['ui_helpers.py:96'] -> ['_qt/ui_helpers.py:96']
    ~ build_slider_row: ['ui_helpers.py:168'] -> ['_qt/ui_helpers.py:168']
    ~ is_stale_result: ['render_worker.py:42'] -> ['render/worker.py:42']
    ~ MeshResult: ['render_worker.py:66'] -> ['render/worker.py:66']
    ~ WorkerSignals: ['render_worker.py:124', '.claude/notes/roadmaps/realtime-variety-render/spike-thread-test.py:81'] -> ['render/worker.py:124', '.claude/notes/roadmaps/realtime-variety-render/spike-thread-test.py:81']
    ~ MeshWorker: ['render_worker.py:135', '.claude/notes/roadmaps/realtime-variety-render/spike-thread-test.py:94'] -> ['render/worker.py:135', '.claude/notes/roadmaps/realtime-variety-render/spike-thread-test.py:94']
    ~ ParamSpec: ['surfaces.py:43'] -> ['varieties/types.py:22']
    ~ Surface: ['surfaces.py:55'] -> ['varieties/types.py:34']
    ~ should_render_on_drag: ['surfaces.py:99'] -> ['varieties/dispatch.py:23']
    ~ dispatch_mode: ['surfaces.py:120'] -> ['varieties/dispatch.py:44']
    ~ _marching_cubes_to_polydata: ['surfaces.py:173'] -> ['varieties/_marching.py:23']
    ~ _fermat_field_kernel: ['surfaces.py:315'] -> ['varieties/_kernels.py:56']
    ~ _enriques_fig1_field_kernel: ['surfaces.py:348'] -> ['varieties/_kernels.py:89']
    ~ _kummer_field_kernel: ['surfaces.py:393'] -> ['varieties/_kernels.py:134']
    ~ _enriques_fig2_field_kernel: ['surfaces.py:427'] -> ['varieties/_kernels.py:168']
    ~ _enriques_fig3_field_kernel: ['surfaces.py:460'] -> ['varieties/_kernels.py:201']
    ~ _enriques_fig4_field_kernel: ['surfaces.py:487'] -> ['varieties/_kernels.py:228']
    ~ _dwork_field_kernel: ['surfaces.py:520'] -> ['varieties/_kernels.py:261']
    ~ _klein_cubic_field_kernel: ['surfaces.py:556'] -> ['varieties/_kernels.py:297']
    ~ _segre_cubic_field_kernel: ['surfaces.py:582'] -> ['varieties/_kernels.py:323']
    ~ _two_quadrics_field_kernel: ['surfaces.py:614'] -> ['varieties/_kernels.py:355']
    ~ _sextic_double_solid_field_kernel: ['surfaces.py:651'] -> ['varieties/_kernels.py:392']
    ~ _grid_to_polydata: ['surfaces.py:686'] -> ['varieties/_marching.py:135']
    ~ _concat_polydata: ['surfaces.py:717'] -> ['varieties/_marching.py:166']
    ~ fermat_quartic: ['surfaces.py:749'] -> ['varieties/k3.py:40']
    ~ kummer_surface: ['surfaces.py:841'] -> ['varieties/k3.py:132']
    ~ enriques_figure_1: ['surfaces.py:899'] -> ['varieties/enriques.py:40']
    ~ enriques_figure_2: ['surfaces.py:943'] -> ['varieties/enriques.py:84']
    ~ enriques_figure_3: ['surfaces.py:990'] -> ['varieties/enriques.py:131']
    ~ enriques_figure_4: ['surfaces.py:1028'] -> ['varieties/enriques.py:169']
    ~ _hanson_cross_section: ['surfaces.py:1087'] -> ['varieties/_marching.py:195']
    ~ calabi_yau_quintic: ['surfaces.py:1182'] -> ['varieties/calabi_yau.py:40']
    ~ calabi_yau_cubic: ['surfaces.py:1209'] -> ['varieties/calabi_yau.py:66']
    ~ calabi_yau_asymmetric: ['surfaces.py:1233'] -> ['varieties/calabi_yau.py:90']
    ~ calabi_yau_dwork: ['surfaces.py:1258'] -> ['varieties/calabi_yau.py:115']
    ~ fano_klein_cubic: ['surfaces.py:1328'] -> ['varieties/fano.py:40']
    ~ fano_segre_cubic: ['surfaces.py:1371'] -> ['varieties/fano.py:83']
    ~ fano_two_quadrics: ['surfaces.py:1419'] -> ['varieties/fano.py:131']
    ~ fano_sextic_double_solid: ['surfaces.py:1491'] -> ['varieties/fano.py:203']
    ~ _get_qta: ['icons.py:78'] -> ['_qt/icons.py:78']
    ~ _icon_color: ['icons.py:106'] -> ['_qt/icons.py:106']
    ~ _reset_defaults_icon_color: ['icons.py:122'] -> ['_qt/icons.py:122']
    ~ reset_camera_icon: ['icons.py:140'] -> ['_qt/icons.py:140']
    ~ screenshot_icon: ['icons.py:154'] -> ['_qt/icons.py:154']
    ~ reset_defaults_icon: ['icons.py:164'] -> ['_qt/icons.py:164']
    ~ preset_plus_x_icon: ['icons.py:197'] -> ['_qt/icons.py:197']
    ~ preset_minus_x_icon: ['icons.py:207'] -> ['_qt/icons.py:207']
    ~ preset_plus_y_icon: ['icons.py:231'] -> ['_qt/icons.py:231']
    ~ preset_minus_y_icon: ['icons.py:236'] -> ['_qt/icons.py:236']
    ... and 78 more
  - symbols lost entirely (present in pre, absent in post): 5
    - _reload_shim
    - test_appearance_panel_shim_emits_deprecation
    - test_view_panel_shim_emits_deprecation
    - test_parameters_panel_shim_emits_deprecation
    - test_parameter_grid_panel_shim_emits_deprecation
