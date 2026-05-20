# Visual Scout — Lessons

## Lesson 1 (2026-05-20 / 2026q2-panel-refresh)

Enriques canonical sextic shows severe sawtooth mesh-tear artifacts along its internal singularity node lines at default render zoom — these are geometry artifacts from marching-cubes on a near-zero-crossing band, not rendering glitches. The existing `smooth_taubin(n_iter=20, pass_band=0.1)` is insufficient. Future uplifts should: (a) flag implicit surfaces whose equations have known singular loci as candidates for more aggressive post-processing or grid-boundary padding, and (b) consider adding a RuntimeWarning (like the Dwork conifold warning) for near-singular parameter regions — the warning would make the artifact *expected* rather than mysterious. The node-closeup render pattern (camera at known singular locus) is worth adding to the standard scout render checklist for any implicit surface with degree > 4.

## Lesson 2 (2026-05-20 / 2026q2-panel-refresh)

`AppearancePanel.apply_to_actor(None)` at `app.py:145` is a no-op, so the plotter background is not initialized to `#2f2f2f` until the first surface render fires. Dark-background scout renders (manually setting `p.set_background('#2f2f2f')`) reveal the actual intended first-launch appearance much better than default PyVista white-background renders. Always add a dark-bg variant render matching the app's default `AppearancePanel._bg_color` — it surfaces contrast and depth problems that white-background renders mask.

## Lesson 3 (2026-05-20 / 2026q2-panel-refresh)

The 2x (2400×1600) render is a useful mesh-quality regression tool: smooth marching-cubes surfaces (Fermat quartic, Kummer) scale cleanly; surfaces with structural discontinuities (Enriques singularity lines, Hanson patch boundaries) reveal more at 2x. Always compare 1x and 2x before assigning severity — what is barely visible at 1x may be HIGH at Retina-scale display.
