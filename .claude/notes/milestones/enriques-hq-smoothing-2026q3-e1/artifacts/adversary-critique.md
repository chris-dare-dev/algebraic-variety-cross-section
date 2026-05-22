# Adversary critique — Enriques HQ Smoothing opt-in toggle

**Reviewer:** milestone-adversary-critic (read-only) | **Date:** 2026-05-22 | **Subject:** `105c4ba..HEAD` (commit `ad17cbe`) — `enriques-hq-smoothing-2026q3-e1`

---

## Executive summary

The most-severe finding is the process auto-HIGH (1159-LOC total diff with 514 lines of research artifacts, crossing the 400-line threshold). There are zero CRITICALs: all AI invariants (AI-2, AI-6, AI-8, AI-9, AI-10, AI-14) cited in the implementation are verified clean. Two MEDIUMs: (1) a double-render on the specific path where the user switches variety while HQ is enabled — the `set_hq_smoothing_eligible(False)` call fires `_on_hq_smoothing_changed` against the stale old mesh before the new variety's subtype has been selected, wasting ~449 ms; (2) no test validates that the two frozensets (`_HQ_SMOOTHING_ELIGIBLE_SUBTYPES` and `_HQ_SMOOTHING_ELIGIBLE_GENERATORS`) stay in sync with each other or that the subtype strings exist in the VARIETIES registry. Two LOWs: a docstring inaccuracy in `set_hq_smoothing_eligible` and an unused Signal payload. **Safe to merge after the MEDIUMs rectify.**

---

## Critical findings

None.

---

## High findings

### HIGH — diff size exceeds 400-LOC review-quality threshold (auto-finding)

**Where:** no specific file — full diff `105c4ba..HEAD`
**Evidence:** `git diff 105c4ba..HEAD | wc -l` = 1159. Breakdown: surfaces.py 88 LOC, appearance_panel.py 162 LOC, app.py 150 LOC, tests/test_enriques_hq_smoothing.py 224 LOC, CONTEXT.md 21 LOC (645 LOC functional); remainder is research artifacts (agent-memory lesson 10 LOC, implementation-plan 31 LOC, dispatch.log 2 LOC, research brief 388 LOC, state.json 50 LOC = 481 LOC artifact inflation, bringing the raw diff to 1159).
**Why it matters:** Cisco / LinearB defect-detection research shows that review quality degrades sharply above 400 LOC. Non-waivable auto-finding per checklist.
**Suggested fix:** No code action required. ~56% of the diff is milestone-pipeline artifacts (research brief, state.json, dispatch.log). The functional code delta is 645 LOC. This is a process note, not a correctness issue.

**Regression-guard test:** N/A for a process finding.

---

## Medium findings

### MEDIUM — double-render on variety-switch when HQ is enabled

**Where:** `app.py:363` (`set_hq_smoothing_eligible(False)` inside `_on_variety_changed`), `appearance_panel.py:546` (`setChecked(False)` inside `set_hq_smoothing_eligible`)
**Evidence:** When the user is on Enriques fig. 1 with HQ enabled and switches variety (e.g., to K3): `_on_variety_changed` calls `set_hq_smoothing_eligible(False)` at line 363 while `self._raw_mesh` is still the old Enriques mesh and `self._current_surface` is still the old Enriques surface. `setChecked(False)` emits `toggled(False)` (because the button was checked) → `_on_hq_smoothing_toggled` → `hq_smoothing_changed.emit(False)` → `_on_hq_smoothing_changed`: the guard at app.py:541 (`if self._raw_mesh is None or self._current_surface is None: return`) does NOT fire because neither is None yet. `_invalidate_clipped_mesh()` + `_render_current(reset_camera=False)` execute, rendering the old Enriques surface without HQ (~449 ms), before `_on_variety_changed` continues to unblock `subtype_combo.blockSignals(False)` at line 408.
**Why it matters:** The user experiences an unexpected ~449 ms freeze during what should be a snappy variety switch, plus a brief flash of the previous surface. The docstring of `set_hq_smoothing_eligible` (appearance_panel.py:533–537) claims this render is "a no-op on the resulting render since the same subtype change already triggered `_render_current` upstream" — that is accurate only for the _subtype_-switch call site (line 455), not for the _variety_-switch call site (line 363) where no `_render_current` has yet been triggered.
**Suggested fix:** Guard `_on_hq_smoothing_changed` against the case where the HQ state is being cleared as part of a variety switch, for example by checking `if not self.appearance_panel.hq_smoothing_changed_by_user_action: return` (a flag set only in response to direct user interaction), or by resetting `_hq_smoothing = False` and setting `_hq_smoothing_cb.setChecked(False)` without emitting `hq_smoothing_changed` from within `set_hq_smoothing_eligible` (i.e., `blockSignals(True)` around `setChecked(False)` in that method, then emit manually only when the caller intends a re-render). Update the docstring to remove the inaccurate "already triggered" claim.

**Regression-guard test:** Add a test that calls `appearance_panel.set_hq_smoothing_eligible(True)`, then flips `_hq_smoothing_cb` to checked (simulating user enabling HQ), then calls `set_hq_smoothing_eligible(False)`, and asserts that `hq_smoothing_changed` was NOT emitted (signal call count == 0), verifying the variety-switch path is silent.

---

### MEDIUM — no test validates the two frozensets stay in sync

**Where:** `app.py:62–69` (`_HQ_SMOOTHING_ELIGIBLE_SUBTYPES`, `_HQ_SMOOTHING_ELIGIBLE_GENERATORS`), `tests/test_enriques_hq_smoothing.py` (absence)
**Evidence:** The two frozensets are co-located and documented, but no test asserts (a) that every string in `_HQ_SMOOTHING_ELIGIBLE_SUBTYPES` exists as a key in `VARIETIES["Enriques surface"]`, or (b) that the generators in `_HQ_SMOOTHING_ELIGIBLE_GENERATORS` are exactly the generators referenced by those VARIETIES entries (i.e., the two sets are in 1-to-1 correspondence). The subtype-scope tests in `test_enriques_hq_smoothing.py` guard against wrong generators gaining the `hq_smoothing` kwarg, but they don't guard against a future developer adding a fig. 5 to `_HQ_SMOOTHING_ELIGIBLE_SUBTYPES` and forgetting `_HQ_SMOOTHING_ELIGIBLE_GENERATORS` (or vice versa). A typo in a frozenset string silently disables the button for a subtype the developer intended to enable — no runtime error, just a broken button.
**Why it matters:** The double-gate is intentional defense-in-depth (subtype set → UI feedback, generator set → runtime TypeError safety), but without a sync-guard test it becomes a hidden maintenance trap. When Enriques fig. 5 is added, a developer who updates only one set gets no feedback from the test suite.
**Suggested fix:** Add a test in `tests/test_enriques_hq_smoothing.py` that imports `VARIETIES` from surfaces and asserts: (a) every string in `_HQ_SMOOTHING_ELIGIBLE_SUBTYPES` is a key in `VARIETIES["Enriques surface"]`; (b) for each such key, `VARIETIES["Enriques surface"][key].generate` is a member of `_HQ_SMOOTHING_ELIGIBLE_GENERATORS`. This test is Qt-free (AI-2 compliant).

---

## Low findings

### LOW — `set_hq_smoothing_eligible` docstring inaccurately describes the variety-switch case

**Where:** `appearance_panel.py:533–537`
**Evidence:** The docstring states: "Setting checked to False emits `toggled(False)` which fires `_on_hq_smoothing_toggled` and re-emits `hq_smoothing_changed` — but MainWindow's handler is a no-op on the resulting render since **the same subtype change already triggered `_render_current` upstream**." This is accurate for `_on_subtype_changed` (app.py:455 calls `set_hq_smoothing_eligible` then `_render_current` at line 458), but false for `_on_variety_changed` (app.py:363 calls `set_hq_smoothing_eligible` without any prior `_render_current` — the variety switch hasn't rendered yet).
**Why it matters:** Documentation that misstates the "harmless" condition is itself the future maintenance trap that leads a developer to believe the double-render has been reasoned away. This is also the docstring justifying why no signal-blocking is done in `set_hq_smoothing_eligible`.
**Suggested fix:** Qualify the "already triggered" claim: "When called from `_on_subtype_changed`, a render is already in flight — the signal is a no-op. When called from `_on_variety_changed`, no render has been triggered yet; see M1 in the `enriques-hq-smoothing-2026q3-e1` adversary critique."

---

### LOW — `Signal(bool)` payload is unused; `Signal()` would be more precise

**Where:** `appearance_panel.py:75` (`hq_smoothing_changed = Signal(bool)`), `app.py:515` (`_on_hq_smoothing_changed(self, _enabled: bool)`)
**Evidence:** The handler names its argument `_enabled` (leading underscore — intentionally unused) because `_render_current` reads `appearance_panel.hq_smoothing` fresh rather than consuming the emitted value. PySide6's `toggled` signal is `Signal(bool)`, which is why the pattern looks natural, but the handler explicitly documents that it ignores the payload.
**Why it matters:** `Signal(bool)` vs `Signal()` is not a correctness issue. The `_enabled` parameter naming correctly communicates intent. However, `Signal()` would make the contract explicit: this is an edge-triggered notification, not a value-carrying signal.
**Suggested fix:** Change `hq_smoothing_changed = Signal(bool)` to `hq_smoothing_changed = Signal()` and `emit(checked)` to `emit()` and `_on_hq_smoothing_changed(self, _enabled: bool)` to `_on_hq_smoothing_changed(self)`. Update the signal test assertion in `test_enriques_hq_smoothing.py` accordingly. Alternatively, leave as-is with a comment explaining the payload is a symmetry courtesy with PySide6's `toggled` pattern, not functionally required.

---

## What was done well

- **AI-6 compliance is precise and documented.** The second `smooth_taubin` call at `surfaces.py:152` is positioned after the first pass (line 145) and is conditional on `second_smooth_iter > 0 and mesh.n_points > 0`, making the stack-vs-replace distinction unambiguous. The docstring in `_marching_cubes_to_polydata` explicitly calls out "STACKS on top of the first pass per AI-6 — do NOT replace."
- **Correct mesh-vs-actor architecture discipline.** The decision to emit `hq_smoothing_changed = Signal(bool)` from the toggle slot instead of calling `plotter.render()` directly is the right architectural call. The commit message, the docstring on `_on_hq_smoothing_toggled`, and CONTEXT.md §4.3a all explain WHY (the second pass moves every vertex — the raw mesh changes, not just actor properties), so future maintainers won't regress to the silent-no-op render path.
- **AI-10 correctness: `_invalidate_clipped_mesh()` before `_render_current()`.** The `_on_hq_smoothing_changed` handler at app.py:543–544 calls these in the correct order, mirroring `_on_domain_changed` discipline. Without the invalidation, the clip would be applied to the stale HQ-off mesh and silently produce a wrong result.
- **Double gate provides genuine defense-in-depth at different layers.** `_HQ_SMOOTHING_ELIGIBLE_SUBTYPES` gates the Qt button (UI feedback); `_HQ_SMOOTHING_ELIGIBLE_GENERATORS` gates the kwarg injection at the call site (runtime TypeError safety). These guard different failure modes: the subtype set catches "user tried to enable HQ on fig 3"; the generator set catches a hypothetical future code path that bypasses the button gate and calls `_render_current` on a non-eligible generator. Neither alone is sufficient for the full threat model.
- **Quantitative quality guard is well-designed and flake-resistant.** `test_enriques_fig1_hq_on_moves_vertices_vs_hq_off` measures per-vertex displacement (mean > 1e-5) rather than normal variance, with explicit reasoning: normal variance is dominated by global surface anisotropy on tetrahedrally-symmetric surfaces and would produce flaky tests. The 150x margin between the threshold (1e-5) and measured value (~0.0015) makes this robust to minor PyVista `smooth_taubin` behavior changes.
- **AI-8 preserved cleanly.** No `Surface` dataclass fields were added. `hq_smoothing` lives as a generator kwarg (opt-in per-call) and as Pattern-A state on `AppearancePanel` (like `_culling`). This avoids bloating the frozen registry dataclass with UI-ephemeral state.
- **`setEnabled(False)` at launch prevents TypeError.** Without the initial disabled state, a user who toggled the HQ button before selecting any surface would trigger `hq_smoothing_changed` → `_on_hq_smoothing_changed` → `_render_current` → `surface.generate(..., hq_smoothing=True)` on a non-eligible generator, raising TypeError. The enabled-at-launch guard is correctly identified and tested.
- **Scope enforcement for figs 3+4 is tested.** `test_enriques_fig3_has_no_hq_kwarg` and `test_enriques_fig4_has_no_hq_kwarg` use `inspect.signature` to verify the A₁-node figures don't accidentally receive the kwarg, ensuring the +138 ms cost isn't silently imposed on surfaces that gain nothing.
- **Default-False tests guard the 449 ms baseline.** `test_enriques_fig1_hq_default_is_false` / `fig2` use `inspect.signature` to verify the default is exactly `False` — protecting all existing callers from silent opt-in to the second pass.
- **CONTEXT.md §8.16 "Deferral closed" paragraph is complete and accurate.** It covers the opt-in architecture, the per-subtype gating rationale, the generator API changes, and the regression guard inventory. Future agents will see a clear audit trail from spike → deferral → opt-in closure.

---

## Recommended rectification order

1. **Fix M1 (double-render on variety-switch with HQ enabled).** The cleanest fix is to `blockSignals(True)` around `setChecked(False)` in `set_hq_smoothing_eligible`, then explicitly clear `_hq_smoothing = False` without emitting the signal. The signal should only fire on direct user interaction with the toggle, not on programmatic resets. Update the docstring to remove the inaccurate "already triggered" claim.

2. **Fix M2 (frozenset sync test).** Add a Qt-free test in `tests/test_enriques_hq_smoothing.py` that validates both frozensets against the VARIETIES registry. One test, ~8 lines, guards against future fig-5 maintenance drift.

3. **Fix L1 (docstring inaccuracy in `set_hq_smoothing_eligible`).** After M1 is fixed (which changes the behavior so the signal IS blocked), the docstring becomes straightforwardly correct. If M1 is addressed differently, update the docstring to accurately reflect the corrected contract.

4. **L2 (Signal payload) is optional.** Leave `Signal(bool)` if the symmetry with PySide6's `toggled` is considered a readability win. Change to `Signal()` if the unused-payload concern outweighs the symmetry benefit.

---

*End of critique. Mandatory rectification: M1 (double-render) and M2 (frozenset sync test). L1 and L2 are optional follow-ups.*

---

## Frontend UI/UX findings

*Merged from `frontend-critique.md`. Frontend critic emitted 0 CRITICAL, 1 HIGH, 3 MEDIUM, 2 LOW. Severity-ids prefixed with `F-`.*

### F-HIGH — Performance tooltip claims a single-machine absolute as a universal constant

**Where:** `appearance_panel.py` HQ button tooltip
**Evidence:** Tooltip says "Adds ~140 ms to mesh generation time." The spike measured +138.2 ms on the dev machine at n=240, c=1.0 — but the absolute number is hardware-dependent (slower laptop: 280-420 ms; fast workstation: 60-80 ms). The +31% RELATIVE figure is hardware-independent.
**Why it matters:** A researcher on a slow machine waits 700 ms instead of the ~590 ms they expected, concludes the app is broken. Quoting the tooltip in a demo is a false technical claim.
**Suggested fix:** Change to: "Applies a second Taubin smoothing pass (n_iter=40, pass_band=0.05) to reduce the double-curve sawtooth-ridge artifact. Adds roughly +31% generate time — about +140 ms on a reference dev machine at default grid resolution; absolute cost is hardware-dependent."

### F-MEDIUM — F-M1: Greyed-out button tooltip not shown on macOS (disabled-widget hover suppression)

**Where:** `appearance_panel.py` HQ button + `app.py` main()
**Evidence:** Qt does not show tooltips on disabled widgets by default on macOS (the OS-level hover filter strips QHelpEvent). Users see the greyed button with no inline explanation of WHY it's disabled.
**Suggested fix:** Add `QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableToolTipsOnDisabledWidgets, True)` in `main()`. One-line, app-wide fix that re-enables tooltip dispatch for disabled widgets (also benefits future disabled-state UX across the app).

### F-MEDIUM — F-M2: Status bar gives no HQ-on attribution; user can't connect longer render to the toggle

**Where:** `app.py:_render_current` status-bar messages
**Evidence:** "Computing {label}…" and the success message are identical whether HQ is on or off. User adjusts slider with HQ on, render takes ~587 ms vs ~449 ms; status bar shows the wall time but no signal that HQ is the cause.
**Suggested fix:** Thread `_hq_label = " [HQ]" if extra_kwargs.get("hq_smoothing") else ""` into the computing message and the final success message. ~3 lines.

### F-MEDIUM — F-M3: New HQ button has no icon; breaks Display group's visual rhythm

**Where:** `appearance_panel.py:refresh_icons` doesn't set an icon on `_hq_smoothing_cb`
**Evidence:** Wireframe has `mdi6.grid` icon; Show edges has `mdi6.border-outside`. HQ smoothing has plain text only — creates an alignment fracture in the Display group where two buttons have 16px left-side icons and one doesn't.
**Suggested fix:** Add a thematically appropriate qtawesome icon (e.g., `mdi6.auto-fix`, `mdi6.shimmer`, or `mdi6.blur`) in `refresh_icons()` following the established `QSize(16, 16)` pattern.

### F-LOW — F-L1: Label "HQ smoothing" is generic; peers use more explicit verbiage

**Where:** `appearance_panel.py:QPushButton("HQ smoothing")`
**Evidence:** "HQ" is informal shorthand (could mean "high quality", "high-Q factor", etc.). Blender uses "Smooth Shading"; ParaView uses "Use Tessellated Mesh Surface". A more descriptive label like "Double-pass smooth" would communicate what's happening without relying on tooltip hover.
**Suggested fix:** Consider relabeling. Defer if tooltip discoverability (F-M1 fix) is sufficient.

### F-LOW — F-L2: State-reset-on-navigate is silent; user may not notice their HQ preference was cleared

**Where:** `appearance_panel.py:set_hq_smoothing_eligible`
**Evidence:** Switching from Fig. 1 (HQ enabled) to Fig. 3 then back to Fig. 1 silently resets HQ to off. ParaView and SageMath both preserve per-pipeline state across navigation; AVC's unconditional clear is the minority pattern.
**Suggested fix:** Either accept the V0 behavior (it's defensible per CONTEXT.md §9 / QSettings non-goal) and document the expectation, OR add a brief status-bar note ("HQ smoothing cleared on subtype switch") when transitioning from checked-True to disabled.

---

## Combined rectification order

1. **M1 (double-render on variety switch with HQ enabled)** — the most concrete correctness bug. Add `blockSignals(True)` around `setChecked(False)` in `set_hq_smoothing_eligible` so programmatic resets don't trigger the signal chain. Update the docstring to remove the inaccurate "already triggered" claim.
2. **F-HIGH (tooltip honesty)** — rewrite the tooltip to cite "+31% / hardware-dependent" alongside the absolute. Strong honest-disclosure win for a research tool.
3. **F-M1 (AA_EnableToolTipsOnDisabledWidgets in main)** — one-line fix that ALSO benefits the existing greyed-out widgets across the app, not just this milestone.
4. **F-M2 (status-bar [HQ] attribution)** — 3 lines, threading `_hq_label` through the computing + success messages.
5. **M2 (frozenset sync-guard test)** — 8 lines; protects against the fig-5 maintenance drift trap.
6. **F-M3 (HQ button icon)** — add a qtawesome icon in `refresh_icons()` to restore Display-group visual rhythm.
7. **L1 / L2** — docstring polish; bundle with M1 fix.
8. **F-L1 / F-L2** — defer (labeling + state-reset feedback can wait for a follow-up UX-polish milestone).
9. **H1 (1159-LOC diff)** — process-only; ~514 LOC artifact inflation. No code action.

---

## Rectification status (orchestrator, 2026-05-22)

**Fixed in rect commit:**

- **M1 (double-render on variety-switch with HQ enabled)**: `set_hq_smoothing_eligible` now wraps the `setChecked(False)` call in `blockSignals(True)` / `blockSignals(False)` so programmatic state resets are silent.  The `hq_smoothing_changed` signal fires ONLY on direct user toggle interaction.  Docstring rewritten to remove the inaccurate "already triggered upstream" claim and replaced with the explicit blockSignals rationale.  New `test_set_hq_smoothing_eligible_blocks_signals_around_setchecked` regression-guard test (source-grep, AI-2 compliant — testing the signal-blocking under a real QApplication would require Qt, which AI-2 bans).

- **M2 (frozenset sync-guard test)**: new `test_hq_smoothing_frozensets_stay_in_sync_with_varieties_registry` test asserts (a) every string in `_HQ_SMOOTHING_ELIGIBLE_SUBTYPES` exists in the VARIETIES registry under "Enriques surface", (b) for each such subtype the registered generator function is exactly in `_HQ_SMOOTHING_ELIGIBLE_GENERATORS`, AND (c) the reverse direction — every eligible generator has at least one corresponding subtype string.  Catches the fig-5 maintenance trap where a future developer adds a new Enriques subtype but forgets one of the two frozensets.

- **F-HIGH (tooltip honesty)**: tooltip rewritten from "Adds ~140 ms to mesh generation time" to "Adds roughly +31% generate time — about +140 ms on a reference dev machine at default grid resolution; absolute cost is hardware-dependent."  The relative figure (+31%) IS hardware-independent (same ratio on any machine); the absolute is correctly framed as a dev-machine reference, not a constant.  Closes the "users on slow machines will think the app is broken" UX failure.

- **F-M1 (AA_EnableToolTipsOnDisabledWidgets)**: added `QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableToolTipsOnDisabledWidgets, True)` to `main()` BEFORE QApplication construction.  App-wide fix that re-enables tooltip dispatch for disabled widgets (Qt's default on macOS suppresses QHelpEvent for disabled widgets).  Benefits not just the HQ toggle but any future disabled-state control across the app — a strict win.

- **F-M2 (status-bar [HQ] attribution)**: `_render_current` now computes `_is_hq_active` up-front and threads `_hq_label = " [HQ]"` through (a) the "Computing…" message and (b) the final success/warning messages.  Users see "Computing Enriques surface [HQ]…" when the toggle is on, then "Enriques surface [HQ]  ·  401,592 verts, 803,088 faces  ·  …  ·  587 ms" — the longer render time is now causally attributable to the toggle.  Refactored to share `_is_hq_active` with the kwarg-injection guard at the surface.generate call site so there's a single source of truth (no duplicated boolean computation).

- **F-M3 (HQ button icon)**: added `mdi6.auto-fix` (magic-wand-with-sparkles) as the HQ toggle icon via a new `icons.hq_smoothing_icon(theme)` factory + module-level `HQ_SMOOTHING_ICON_NAME` constant.  Wired up in `appearance_panel.refresh_icons` next to the existing Wireframe / Show-edges icon calls.  Three-way distinctness assertion added to `test_icons.py:test_wireframe_and_edges_icons_are_distinct_names` so the three Display group icons are guaranteed orthogonal at 16px.  The mdi6.auto-fix icon was also added to the QApplication smoke-test target list and the mock-based name/color guard.

- **L1 + L2 (docstring polish + Signal payload)**: rolled into the M1 docstring rewrite.  Signal(bool) payload kept (rather than narrowing to Signal()) for symmetry with PySide6's `toggled(bool)` pattern — the implementation cost of Signal() was greater than the readability concession, and the unused payload is now explained in the rewritten docstring.

**Deferred (out of milestone scope):**

- **F-L1 (label "HQ smoothing" → "Double-pass smooth")**: real UX critique but a label-rename mid-rectify isn't worth the churn — the tooltip-on-disabled fix from F-M1 carries most of the discoverability gap.  Open a future labeling-polish milestone if/when the term "HQ" proves confusing in user feedback.

- **F-L2 (state-reset feedback when navigating away from Fig. 1/2)**: defensible V0 behavior per CONTEXT.md §9 (no QSettings persistence — sticky toggles are explicit non-goals).  Adding a "HQ cleared on subtype switch" status-bar message would be net-noise for the common case (single subtype session) and only helps comparison-workflow users.  Defer to a feedback-driven milestone if it surfaces in actual use.

**Process-only:**

- **H1 (1159-LOC diff overage)**: ~514 LOC milestone artifact inflation; code delta was 645 LOC.  No code action.

**Test suite:** 348 → 350 passed (+2 new rect tests: signal-block guard + frozenset-sync guard).  No regressions.

**Architecture lessons recorded:**

1. *"blockSignals around programmatic state resets"* — when a public method's job is to align widget state with external context (a variety/subtype change), it should never look like a user action to downstream slots.  blockSignals + try/finally pair is the canonical Qt pattern.  Now documented inline in `set_hq_smoothing_eligible` and reinforced by the source-grep test.

2. *"Frozenset double-gates need explicit sync-guard tests"* — when defense-in-depth is implemented as two parallel collections (subtype names + generator functions), a test that asserts their bidirectional correspondence is essential.  The maintenance-trap risk is exactly the kind of failure mode that only surfaces months later when someone adds Fig. 5.

3. *"Hardware-dependent perf disclosures should cite the relative figure"* — +138 ms varies 2-3× across hardware; +31% does not.  When citing a measured cost in user-facing tooltip text, lead with the relative figure (hardware-independent) and follow with the absolute (clearly labeled as a reference-machine measurement).
