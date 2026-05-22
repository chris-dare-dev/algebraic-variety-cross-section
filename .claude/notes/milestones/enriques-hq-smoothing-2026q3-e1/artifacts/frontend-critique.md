# Frontend UI/UX Critique — enriques-hq-smoothing-2026q3-e1

**Critic:** milestone-frontend-ux-critic (claude-sonnet-4-6)
**Commit range:** `105c4ba1a274c88a2b6b8acb782641f266f7e2f5..HEAD`
**Date:** 2026-05-22
**Files changed (Qt-panel surface):** `appearance_panel.py`, `app.py`
**Files NOT changed:** `view_panel.py`, `parameters_panel.py`, `styles.py`

---

## Executive Summary

The HQ-smoothing toggle is architecturally sound — the mesh-vs-actor distinction is well-handled, AI-9 / AI-11 / AI-12 / AI-13 are all clean, and the Pattern-A state storage is correctly applied. No CRITICAL findings. One HIGH finding (performance-disclosure honesty: "~140 ms" is a single-machine measurement reported as if it were a constant, which will mislead users on slower or faster hardware). Three MEDIUM findings cover: the disabled-button affordance (grayed out with no inline "why"), the absence of an HQ-on signal in the status bar so users cannot attribute the longer render to the toggle, and the icon gap for the new button. Two LOW findings cover label specificity and the state-reset-on-navigate UX choice.

No gate question is needed — all findings are addressable within the existing panel architecture.

---

## CRITICAL findings

None.

---

## HIGH findings

### HIGH — Performance tooltip claims a single-machine absolute as a universal constant

**Where:** `appearance_panel.py:243-249`
**Evidence:** Tooltip text: `"Adds ~140 ms to mesh generation time."` The spike log (`CONTEXT.md §8.16`) measured +138.2 ms on the dev machine only, at a specific grid resolution (n=240), with a single set of parameters (`enriques_figure_1(c=1.0)`). On a slower machine (the target user is a researcher, potentially on a 3–5 year old laptop) the second Taubin pass can easily run 2–3× longer — i.e., 280–420 ms, more than doubling the total generate time. On a fast workstation it might be 60–80 ms. Stating "~140 ms" as though it is a fixed cost is misleading. The spike was correctly documented in §8.16 as a dev-machine measurement; the tooltip should inherit the same caveat.
**Why it matters:** A researcher on a slow machine enables HQ, waits 700 ms instead of the ~590 ms they expected from reading "adds ~140 ms," and concludes the app is broken. Worse, if they quote the tooltip in a demo context ("this option adds 140ms"), that is a false technical claim. Performance disclosures in scientific-viz tooling need to be honest about their measurement context — ParaView's OSPRay toggle says "Rendering time depends on scene complexity and hardware"; Blender's Cycles render settings show a measured sample-time with the caveat "on this hardware."
**Suggested fix:** Change the tooltip to: `"Applies a second Taubin smoothing pass (n_iter=40, pass_band=0.05) to reduce the double-curve sawtooth-ridge artifact. Overhead is hardware-dependent (measured ~140 ms / +31% on a reference machine at default grid resolution). Disabled on non-eligible surfaces."` This preserves the +31% relative figure (which is hardware-independent by definition, since both passes run on the same machine) alongside the absolute.

---

## MEDIUM findings

### MEDIUM-1 — Greyed-out button has no inline explanation of WHY it is disabled

**Where:** `appearance_panel.py:239-253`
**Evidence:** `self._hq_smoothing_cb.setEnabled(False)` at launch with no `setStatusTip()` and no visible label adjacent to the button explaining the eligibility constraint. The tooltip (`setToolTip(...)`) IS informative — it says "Disabled (greyed out) on other surfaces — the second pass targets double-curve topology specifically..." — but Qt does NOT show tooltips on disabled widgets by default on macOS (the OS-level hover-event filter strips `QHelpEvent` for disabled widgets unless the parent widget re-routes it). A user who opens the app, looks at the Display group, and sees a greyed-out "HQ smoothing" button has no inline affordance to understand it is surface-gated.

Industry comparison:
- **Blender N-panel** greys out many mode-specific toggles (e.g. "Shade Auto Smooth" is greyed when the active object has no Custom Normals modifier) but shows them with a small `(i)` info icon and the property description is always accessible via hover-over the label — not the control itself. The Blender tooltip is shown even on disabled controls because Blender re-routes hover events at the panel level.
- **ParaView Properties** (5.13) greys incompatible properties but places them under a collapsible "Advanced" header with a text annotation "Available for X representation only." The grouping provides in-place context without needing tooltip hover.

Here, the tooltip is on the button itself (disabled, no hover) and there is no adjacent label or status tip. On macOS the user must select a non-Enriques variety, observe the button become enabled, then navigate to an Enriques Fig. 1/2 subtype to understand the gate — this is pure trial-and-error.
**Why it matters:** This is a discoverability failure for a research tool. A first-time user who opens a K3 surface sees "Wireframe", "Show edges", and a greyed "HQ smoothing" with no explanation. They will interpret the grey as "this feature is unavailable" and never learn it is surface-gated.
**Suggested fix:** Add `self._hq_smoothing_cb.setStatusTip("HQ smoothing is enabled only for Enriques figs 1 and 2")` so the status bar provides the "why" when the button receives focus or the user right-clicks. Additionally, consider using `QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableToolTipsOnDisabledWidgets, True)` in `main()` — this re-enables Qt's tooltip dispatch for disabled widgets globally, which is the standard fix for this exact pattern. One-line change to `app.py:main()`.

### MEDIUM-2 — Status bar does not indicate HQ mode during render; user cannot attribute the longer wait to the toggle

**Where:** `app.py:583, app.py:689-693`
**Evidence:** The status bar "Computing…" message at line 583 is `f"Computing {surface.label}…"` regardless of whether HQ smoothing is active. The final success message (line 689-692) is `f"{surface.label}  ·  {self._raw_mesh.n_points:,} verts, {self._raw_mesh.n_cells:,} faces{param_str}  ·  {bbox_suffix}  ·  {_gen_ms:.0f} ms"` — also without any HQ indicator. When the user has HQ enabled and adjusts a parameter slider, the render takes ~587 ms instead of ~449 ms; the status bar shows the measured wall time (e.g., "587 ms") but gives no signal that HQ is the cause. The user will attribute the ~140 ms overhead to parameter complexity or machine load, not to their toggle choice.

Industry comparison:
- **SageMath Jupyter widgets** show the active render-option set in the output cell header (e.g., "rendering with adaptive=True"). This is the closest analog: a user-toggled quality mode that changes generation time.
- **ParaView OSPRay** toggle: when OSPRay is on, the status bar shows "OSPRay rendering..." and the frame-rate counter clearly reflects the OSPRay overhead, giving the user direct causal attribution.
- **Mathematica `Manipulate[]`** with `ProgressIndicator` — each render pass shows a labeled task in the progress bar (not just "rendering").

The fix is minimal — `f"Computing {surface.label} [HQ]…"` during the busy phase and a `[HQ]` suffix in the final message.
**Why it matters:** Without this, users will report "the app got slower after I enabled that button" rather than "HQ smoothing added the expected overhead." Causal attribution is fundamental to informed UX, especially in a research context where timing matters.
**Suggested fix:** In `_render_current`, derive `_hq_label = " [HQ]" if extra_kwargs.get("hq_smoothing") else ""`. Use `f"Computing {surface.label}{_hq_label}…"` at the computing message line and append `_hq_label` to the `base_msg` before the `{_gen_ms:.0f} ms` token. Total change: 3 lines.

### MEDIUM-3 — New "HQ smoothing" button has no icon; breaks visual register of the Display group

**Where:** `appearance_panel.py:239-253`; compare `appearance_panel.py:549-592` (`refresh_icons`)
**Evidence:** Wireframe has icon `mdi6.grid`; Show edges has icon `mdi6.border-outside`. Both are wired up in `refresh_icons()`. The new `_hq_smoothing_cb` button receives no icon — `refresh_icons()` at lines 549-592 does not include a `setIcon` call for it. The result is a Display group where two buttons have left-side icons at 16px and one (HQ smoothing) has plain text only, creating a vertical-rhythm alignment fracture.

Industry comparison:
- **Blender 4.x N-panel** left-aligns ALL icon+text controls uniformly within a panel. A plain-text button between two icon+text buttons in the same group is not a pattern Blender uses; the visual weight mismatch signals a different tier of control, which is misleading here since all three are equal-rank display toggles.
- **3D Slicer modules panel**: all checkable toggles in a group carry the same icon-size footprint; an icon is either present on ALL or on NONE within a group.

Additionally, `refresh_icons()` is called by `MainWindow.__init__`, `_on_theme_changed`, and `_apply_system_theme`. The HQ button is not in `refresh_icons()`, so if a future milestone adds a theme-aware icon for it, the call site is already wired — but the current gap means the button breaks the visual cadence the previous milestone established.
**Why it matters:** The alignment fracture is visually noticeable. A user scanning the Display group will perceive the HQ button as a different kind of control. This is a quality-of-life regression relative to the icon discipline established in qtawesome-icons-2026q2-e2.
**Suggested fix:** Either (a) add an appropriate icon (`mdi6.shimmer`, `mdi6.auto-fix`, or `mdi6.star-four-points` are semantically plausible — "something extra applied to the surface") in `refresh_icons()` with the same `QSize(16, 16)` treatment, or (b) explicitly document that the HQ button is intentionally icon-free (e.g., to signal "this one is different — it changes the mesh, not the view"). Option (a) is the consistency-preferred choice.

---

## LOW findings

### LOW-1 — Label "HQ smoothing" is generic; does not communicate the scope to a first-time user

**Where:** `appearance_panel.py:239`
**Evidence:** `QPushButton("HQ smoothing")`. "HQ" is informal shorthand that means different things in different contexts (High Quality, High-Q factor, headquarters). In isolation, a new user on Enriques Fig. 1 who sees the button become enabled has no affordance beyond "something called HQ smoothing became available." Peer tools use more explicit labels:
- **Blender:** "Smooth Shading" (not "HQ Shading") — describes the geometric operation
- **ParaView 5.13:** "Use Tessellated Mesh Surface" — describes what changes
- **Mathematica `ContourPlot3D` → `MaxRecursion`:** explicitly labeled in options dialog as "Maximum Subdivisions"

The tooltip does explain the operation in detail ("second Taubin smoothing pass, n_iter=40, pass_band=0.05, reduces double-curve sawtooth-ridge artifact") but, as noted in MEDIUM-1, the tooltip may not render on disabled state. A slightly more descriptive label — "Double-pass smooth" or "High-Q smooth (Enriques)" — would communicate scope without relying on tooltip hover.
**Why it matters:** LOW cosmetic impact but compounds the MEDIUM-1 discoverability gap.
**Suggested fix:** Consider `"Double-pass smooth"` as the button label, with the full technical explanation remaining in the tooltip. This describes the geometry operation (two smoothing passes) rather than a quality tier, which is more honest and more specific.

### LOW-2 — State-reset-on-navigate silently discards user's HQ preference; no visual cue that reset happened

**Where:** `appearance_panel.py:539-547`; `app.py:356`
**Evidence:** `set_hq_smoothing_eligible(False)` calls `setChecked(False)` unconditionally on any variety/subtype switch that makes HQ ineligible (variety change, or navigate from Fig. 1 to Fig. 3). If the user enables HQ on Fig. 1, switches to Fig. 3 ("test the non-HQ result"), then switches back to Fig. 1, HQ is now OFF — the user must re-enable it. The implementation note in the docstring acknowledges this design: "switching away from a double-curve subtype with HQ enabled does NOT persist the setting across the move." This is a valid defensible choice (CONTEXT.md §9 notes no QSettings persistence is a deliberate V0 scope), but the silent reset with no status-bar feedback means the user may not notice the preference was cleared.

Industry comparison:
- **ParaView:** per-pipeline-object properties (e.g., OSPRay toggle) persist across time steps; navigation does not reset them. The "reset on navigate" pattern is unusual in ParaView.
- **SageMath Jupyter widgets:** all parameters are sticky — navigating between cells does not reset widget state.
- Both examples support "preserve per-surface toggle state across navigation" as the peer-expected default. The AVC implementation clears unconditionally, which is the minority pattern.

This is LOW (not MEDIUM) because: (1) the choice is documented and defensible (avoids the dangling-enabled bug described in `app.py:356-361`); (2) the sticky-across-navigate alternative would require per-surface-key storage, which is in the QSettings deferral territory of CONTEXT.md §9.1. The feedback gap (no status-bar message when HQ is cleared) is the addressable part.
**Why it matters:** Users who rely on HQ-on for comparison work (Fig. 1 HQ vs non-HQ) will be confused when their preference silently resets after navigating away.
**Suggested fix:** When `set_hq_smoothing_eligible(False)` transitions from checked=True to checked=False (i.e., `if not eligible and self._hq_smoothing_cb.isChecked()`), emit a brief status tip or use `QApplication.instance().beep()` — or, least-intrusive, just ensure the caller can log "HQ smoothing cleared" to the status bar for one event-loop cycle. Alternatively, accept the behavior and document the "re-enable after returning to Fig. 1/2" expectation in the tooltip's final sentence.

---

## What was done well

1. **Mesh-vs-actor architecture is correctly identified and wired.** The `hq_smoothing_changed = Signal(bool)` pattern — emitting a signal instead of calling `render()` directly — is exactly the right split. The docstring at `_on_hq_smoothing_toggled` is unusually clear in explaining why `render()` would silently no-op here. This prevents the subtle "stale mesh re-rendered" bug that is the most common mistake in this pattern.

2. **AI-9 re-entrancy is correctly handled.** The `_on_hq_smoothing_changed` handler (app.py:512-547) correctly does nothing when `self._raw_mesh is None or self._current_surface is None`, avoiding a render attempt on an invalid state. The no-op early-return with a comment is the right pattern, better than silently falling through a None dereference.

3. **Generator-membership check rather than subtype-string check at injection point.** `surface.generate in _HQ_SMOOTHING_ELIGIBLE_GENERATORS` (app.py:604) is a more robust guard than string-matching the subtype dropdown key. If a future refactor renames the dropdown key, the injection guard still works. The string-based check in `_on_subtype_changed` (which gates the UI toggle) is the right place for the string comparison; the generator-set check in `_render_current` is the right place for the injection guard. The two-layer defense is well-designed.

4. **`set_hq_smoothing_eligible(False)` is called on VARIETY switch as well as subtype switch.** The variety-level clear (app.py:356) prevents the dangling-enabled bug described in the inline comment. This is correctly ordered before `_on_subtype_changed` runs, so the clear happens before the new subtype's eligibility is evaluated.

5. **Token discipline is clean.** No short-hex literals anywhere in the diff. No shorthand Qt enum forms (`Qt.AlignLeft`, `QSizePolicy.Expanding`). `Signal(bool)` is from `PySide6.QtCore` — correctly imported. No `processEvents()` outside the existing `_render_current` guard. AI-9, AI-11, AI-12, AI-13 all clear.

6. **First-launch / section-9.3 is preserved.** `set_hq_smoothing_eligible` does not touch `variety_combo` or `subtype_combo` and does not call `_render_current`. `_on_hq_smoothing_changed` returns immediately when `_raw_mesh is None`. No auto-render risk from the new code path.

---

## Recommended rectification order

1. **HIGH (performance tooltip):** Change tooltip to cite "+31% / hardware-dependent" rather than "~140 ms" as a fixed cost. One string change in `appearance_panel.py`. Do immediately — the current wording will generate user confusion and mis-quotes.

2. **MEDIUM-1 (disabled affordance):** Add `QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableToolTipsOnDisabledWidgets, True)` in `app.py:main()`. One line. Closes the "tooltip invisible on disabled widget" gap on macOS without any panel changes.

3. **MEDIUM-2 (status-bar HQ attribution):** Add `_hq_label = " [HQ]" if extra_kwargs.get("hq_smoothing") else ""` and thread it through the computing message and success message in `_render_current`. Three-line change.

4. **MEDIUM-3 (icon gap):** Add a thematically appropriate qtawesome icon for `_hq_smoothing_cb` in `refresh_icons()`. Follow the `QSize(16, 16)` convention already in use.

5. **LOW-1 / LOW-2:** Address in the same commit as MEDIUM-3 if desired; both are cosmetic and low-risk.
