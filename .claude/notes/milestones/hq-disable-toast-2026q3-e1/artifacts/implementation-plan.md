# Implementation plan — hq-disable-toast-2026q3-e1

**Inline path. ~80 LOC across 3 files.** Close F-L2 from `enriques-hq-smoothing-2026q3-e1` (deferred). Surfaces a one-shot status-bar acknowledgment when `set_hq_smoothing_eligible(False)` silently auto-disables an active Double-pass smooth toggle on variety/subtype switch.

**One load-bearing catch** from the researcher: the toast must fire at BOTH `_on_variety_changed` AND `_on_subtype_changed`. Variety-only would silently miss the Enriques Fig.1 → Fig.3 transition (a subtype-only change). The researcher also corrected the brief's mistaken claim that `qtawesome-icons-2026q2-e2` re-flagged the same gap (it didn't — that F-L2 was a different finding about rotated axis-glyph tooltips).

1. **app.py — `_on_variety_changed`** —
   - Capture `_prior_hq = self.appearance_panel.hq_smoothing` BEFORE `set_hq_smoothing_eligible(False)` (the eligible call clears `_hq_smoothing` to False).
   - Compose `_hq_note = "  Double-pass smooth disabled — only available on Enriques figs 1+2." if _prior_hq else ""`.
   - Append `{_hq_note}` to each of the 4 variety-branch `showMessage` strings (Calabi–Yau / Fano / Enriques / else).
   - The Enriques branch's note normally stays empty because `_on_subtype_changed` re-enables HQ for figs 1+2 — but for figs 3+4 the subtype handler fires its own more specific toast.
   ~14 LOC delta.

2. **app.py — `_on_subtype_changed`** —
   - Capture `_prior_hq = self.appearance_panel.hq_smoothing` BEFORE `set_hq_smoothing_eligible(is_hq_eligible)`.
   - Add conditional toast after the eligible call: `if _prior_hq and not is_hq_eligible: self.statusBar().showMessage(f"Subtype: {name}.  Double-pass smooth disabled — only available on Enriques figs 1+2 (double-curve topology).")`.
   - Toast persists until `_render_current`'s success/error message overwrites it (~449 ms).
   ~12 LOC delta.

3. **CONTEXT.md §4.3a** — append one-sentence note documenting the dual-call-site requirement + the `hq-disable-toast-2026q3-e1 / F-L2 closure` cross-reference.
   ~1 line delta (extends existing paragraph).

4. **tests/test_hq_disable_toast.py (new)** — 4 source-grep tests (AI-2 compliant):
   - `test_hq_disable_toast_captures_prior_state_before_eligible_call`
   - `test_hq_disable_toast_conditional_guard_present`
   - `test_hq_disable_toast_message_explains_eligibility_scope`
   - `test_hq_disable_toast_fires_in_both_variety_and_subtype_handlers` (count `_prior_hq` ≥ 2 + verify `double-curve topology` present)
   ~55 LOC delta.

5. **Verify** —
   - `.venv/bin/pytest tests/ -q` reaches 449 + 4 = 453.
   - **No off-screen render verification needed** — pure status-bar text change, no VTK.
   - Static `import app` smoke check.

6. **Commit** — `feat(hq-disable-toast-2026q3-e1): status-bar acknowledgment when Double-pass smooth auto-disables on variety/subtype switch (F-L2 closure)`.
