# Research Brief — hq-disable-toast-2026q3-e1

**Researcher:** milestone-researcher (solo)
**Date:** 2026-05-23
**Status:** complete

---

## 1. TL;DR

Capture `self.appearance_panel.hq_smoothing` BEFORE calling `set_hq_smoothing_eligible(False)` in BOTH `_on_variety_changed` (app.py:523) AND `_on_subtype_changed` (app.py:626), then emit a `showMessage` toast AFTER each variety/subtype branch's own `showMessage` when the prior state was True and the new state is ineligible.  The main risk is the dual-call-site requirement — the brief's scope text focuses on `_on_variety_changed` but the Enriques Fig.1 → Fig.3 transition is handled by `_on_subtype_changed` only, so a variety-changed-only implementation silently misses that case.  Backup plan: if the implementer decides to limit scope to variety changes only (skipping the subtype-only transition), document the remaining gap as a follow-on finding in the adversary pass.

---

## 2. F-L2 deferred-finding context

### Original F-L2 — enriques-hq-smoothing-2026q3-e1/artifacts/adversary-critique.md (lines 140–144)

```
### F-LOW — F-L2: State-reset-on-navigate is silent; user may not notice their HQ preference was cleared

Where: appearance_panel.py:set_hq_smoothing_eligible
Evidence: Switching from Fig. 1 (HQ enabled) to Fig. 3 then back to Fig. 1 silently resets HQ to off.
ParaView and SageMath both preserve per-pipeline state across navigation; AVC's unconditional clear
is the minority pattern.
Suggested fix: Either accept the V0 behavior (it's defensible per CONTEXT.md §9 / QSettings non-goal)
and document the expectation, OR add a brief status-bar note ("HQ smoothing cleared on subtype switch")
when transitioning from checked-True to disabled.
```

**Deferred status (adversary-critique.md lines 183–184):**
> "F-L2 (state-reset feedback when navigating away from Fig. 1/2): defensible V0 behavior per CONTEXT.md §9 (no QSettings persistence — sticky toggles are explicit non-goals). Adding a 'HQ cleared on subtype switch' status-bar message would be net-noise for the common case (single subtype session) and only helps comparison-workflow users. Defer to a feedback-driven milestone if it surfaces in actual use."

### Re-flagging — qtawesome-icons-2026q2-e2/artifacts/adversary-critique.md

The qtawesome-icons-2026q2-e2 adversary critique does NOT re-flag the HQ-disable UX gap as a distinct finding. The F-L2 identifier in that document refers to a different finding: "minus-direction tooltips don't mention rotation strategy for screen readers" (view_panel.py minus-direction button tooltips). There is no F-L2 referencing the HQ toggle in the qtawesome-e2 critique.

**Conclusion:** The brief's claim that qtawesome-icons-2026q2-e2 "re-flagged" F-L2 is inaccurate — only one critic flagged this gap (enriques-hq-smoothing-2026q3-e1 adversary). The UX gap is real, but the brief's F-L2 citation history is partially incorrect. Both critics named the same general UX category (silent state-reset) but the qtawesome-e2 critic named a different specific finding. This does NOT change the implementation scope — the gap is genuine and the original F-L2 from enriques-hq-smoothing-2026q3-e1 is the authoritative source.

---

## 3. Codebase audit

### `_on_variety_changed` — app.py:442–579

| Line | Content |
|------|---------|
| 442 | `def _on_variety_changed(self, name: str) -> None:` |
| 523 | `self.appearance_panel.set_hq_smoothing_eligible(False)` — the unconditional clear on every variety switch |
| 528–531 | `if name == "Calabi–Yau 3-fold": statusBar().showMessage(...)` |
| 538–541 | `elif name == "Fano 3-fold (ρ=1)": statusBar().showMessage(...)` |
| 549–558 | `elif name == "Enriques surface": statusBar().showMessage("Enriques surface — back-face culling active…")` |
| 560–561 | `else: statusBar().showMessage(f"Variety: {name}. Now choose a model.")` |
| 577 | `statusBar().showMessage("Choose a variety to begin.")` — placeholder branch |

Note: the `set_hq_smoothing_eligible(False)` call at line 523 PRECEDES the variety-specific `showMessage` calls at lines 528–561. The toast must be emitted AFTER these, not before.

### `_on_subtype_changed` — app.py:581–641

| Line | Content |
|------|---------|
| 581 | `def _on_subtype_changed(self, name: str) -> None:` |
| 622–625 | `is_hq_eligible = (variety == "Enriques surface" and name in _HQ_SMOOTHING_ELIGIBLE_SUBTYPES)` |
| 626 | `self.appearance_panel.set_hq_smoothing_eligible(is_hq_eligible)` — may pass `False` for Figs. 3+4 |
| 641 | `self._render_current(reset_camera=True)` |

There is NO `showMessage` call in `_on_subtype_changed`'s happy path — the render pipeline's `_on_mesh_ready` writes the status bar after the render completes.

### `appearance_panel.hq_smoothing` property — appearance_panel.py:558–570

```python
def hq_smoothing(self) -> bool:
    """..."""
    return self._hq_smoothing
```

Pure attribute access on `self._hq_smoothing: bool` (initialized to `False` at line 116). No signal emission, no side effects. Safe to read at any point.

### `set_hq_smoothing_eligible` — appearance_panel.py:572–614

Critical architecture (lines 600–614):
```python
self._hq_smoothing_cb.setEnabled(eligible)
if not eligible:
    self._hq_smoothing_cb.blockSignals(True)
    try:
        self._hq_smoothing_cb.setChecked(False)
    finally:
        self._hq_smoothing_cb.blockSignals(False)
    self._hq_smoothing = False  # <-- clears _hq_smoothing to False AFTER setChecked
```

**Critical ordering constraint:** `_hq_smoothing` is set to `False` at the END of `set_hq_smoothing_eligible(False)` (after `setChecked`). Reading `self.appearance_panel.hq_smoothing` BEFORE calling `set_hq_smoothing_eligible(False)` is the only way to capture the prior state.

### Existing `showMessage` calls in `_on_variety_changed` (the toast must compose, not replace)

All four variety branches already call `showMessage` with variety-specific context messages. The toast must fire AFTER these (it is a follow-on annotation, not a replacement).

### `_HQ_SMOOTHING_ELIGIBLE_SUBTYPES` — app.py:73–76

```python
_HQ_SMOOTHING_ELIGIBLE_SUBTYPES = frozenset({
    "Canonical sextic  [Fig. 1]",
    "Diagonal λ-family  [Fig. 2]",
})
```

---

## 4. Trigger condition trace

### Case 1: Enriques Fig.1 (HQ on) → K3

1. User changes variety combo from "Enriques surface" to "K3 surface".
2. `_on_variety_changed("K3 surface")` fires.
3. Prior state: `self.appearance_panel.hq_smoothing == True`.
4. `set_hq_smoothing_eligible(False)` clears `_hq_smoothing = False`.
5. `statusBar().showMessage("Variety: K3 surface. Now choose a model.")` fires.
6. `_on_variety_changed` returns. No `_on_subtype_changed` fires from this step alone.
7. Toast trigger: prior=True, new variety ineligible. **FIRE toast in `_on_variety_changed` AFTER the branch's `showMessage`.**

### Case 2: Enriques Fig.1 (HQ on) → Enriques Fig.3

1. User changes ONLY the subtype combo (variety stays "Enriques surface").
2. `_on_variety_changed` does NOT fire (variety combo unchanged).
3. `_on_subtype_changed("Cayley symmetroid  [Fig. 3]")` fires.
4. Prior state: `self.appearance_panel.hq_smoothing == True`.
5. `is_hq_eligible = (True and "Cayley symmetroid  [Fig. 3]" in _HQ_SMOOTHING_ELIGIBLE_SUBTYPES)` = False.
6. `set_hq_smoothing_eligible(False)` clears `_hq_smoothing = False`.
7. Toast trigger: prior=True, `is_hq_eligible=False`. **FIRE toast in `_on_subtype_changed` BEFORE `_render_current`.**

### Case 3: Enriques Fig.1 (HQ on) → Enriques Fig.2

1. User changes only subtype combo. `_on_variety_changed` does NOT fire.
2. `_on_subtype_changed("Diagonal λ-family  [Fig. 2]")` fires.
3. `is_hq_eligible = True` (Fig. 2 IS in `_HQ_SMOOTHING_ELIGIBLE_SUBTYPES`).
4. `set_hq_smoothing_eligible(True)` is called — HQ stays enabled; `_hq_smoothing` is NOT cleared.
5. Toast trigger: none (HQ remains eligible). **DO NOT FIRE.**

### Case 4: K3 (HQ off) → Enriques Fig.1

1. `_on_variety_changed("Enriques surface")` fires.
2. Prior state: `self.appearance_panel.hq_smoothing == False`.
3. `set_hq_smoothing_eligible(False)` called (unconditional clear — but state was already False).
4. Toast trigger: prior=False. **DO NOT FIRE.**

### Case 5: Enriques Fig.1 (HQ on) → "— Select —" placeholder

1. `_on_variety_changed("")` fires (or name not in VARIETIES).
2. Goes to else branch (line 563). `set_hq_smoothing_eligible` is NOT called here.
3. The else branch calls `_clear_actor()` + `showMessage("Choose a variety to begin.")`.
4. **QUESTION:** Does `_hq_smoothing` need to be cleared here? Check: `set_hq_smoothing_eligible` is only called in the `if name in VARIETIES:` branch. The placeholder branch does NOT call it. This means `_hq_smoothing` could persist as `True` in the placeholder state. However, `_current_surface = None` and `_raw_mesh = None` prevent any render from using it. Edge-case: acceptable as-is because the next variety selection will always call `set_hq_smoothing_eligible(False)` first. No toast needed in this branch.

### Summary: dual-call-site requirement confirmed

| Transition | Method that catches it | Should toast fire? |
|---|---|---|
| Enriques Fig.1 → K3 | `_on_variety_changed` | YES (prior=T, new ineligible) |
| Enriques Fig.1 → CY3 | `_on_variety_changed` | YES |
| Enriques Fig.1 → Fano | `_on_variety_changed` | YES |
| Enriques Fig.1 → Fig.3 | `_on_subtype_changed` ONLY | YES |
| Enriques Fig.1 → Fig.4 | `_on_subtype_changed` ONLY | YES |
| Enriques Fig.1 → Fig.2 | `_on_subtype_changed` ONLY | NO (remains eligible) |
| K3 → anything | `_on_variety_changed` | NO (prior=False) |
| Enriques Fig.2 → Fig.3 | `_on_subtype_changed` ONLY | YES (prior=T, new ineligible) |

**Implementer must add the toast to BOTH `_on_variety_changed` and `_on_subtype_changed`.**

---

## 5. Recommended approach

### Code shape for `_on_variety_changed`

Insert the prior-state capture BEFORE line 523, and the conditional toast AFTER each variety branch's `showMessage`:

```python
# hq-disable-toast-2026q3-e1: capture prior HQ state before clearing it.
# set_hq_smoothing_eligible(False) below clears _hq_smoothing to False;
# we must read the value before that call.
_prior_hq = self.appearance_panel.hq_smoothing  # pure bool read, no side effects

self.appearance_panel.set_hq_smoothing_eligible(False)   # existing line 523

if name == "Calabi–Yau 3-fold":
    self.statusBar().showMessage(
        "Calabi–Yau 3-fold — each figure is a 2D real shadow of a "
        "6-dimensional manifold.  Now choose a model."
    )
    # ... (existing context hint code)
elif name == "Fano 3-fold (ρ=1)":
    self.statusBar().showMessage(
        "Fano 3-fold (ρ=1) — each figure is a 2D real slice of a "
        "6-dimensional variety.  Now choose a model."
    )
    # ... (existing context hint code)
elif name == "Enriques surface":
    self.statusBar().showMessage(
        "Enriques surface — back-face culling active to suppress "
        "the double-curve zipper seam.  Now choose a model."
    )
    self.parameters_panel.set_context_hint("")
else:
    self.statusBar().showMessage(f"Variety: {name}. Now choose a model.")
    self.parameters_panel.set_context_hint("")

# hq-disable-toast-2026q3-e1: after the variety message, append a one-shot
# note when Double-pass smooth was active and is now ineligible.  This
# overwrites the variety message above (Qt replaces, not appends), so the
# combined message must include the full variety context.
if _prior_hq:
    # Compose with the existing variety message — append the HQ note.
    _existing = self.statusBar().currentMessage()
    self.statusBar().showMessage(
        f"{_existing}  [Double-pass smooth disabled — only available on "
        f"Enriques figs 1+2.]"
    )
```

**Wait — Option C (read currentMessage + append) is fragile.** Qt truncates long status-bar messages and the concatenation could exceed the ~120-char display limit. The correct implementation is Option A: build the combined message string per-branch. See Section 6 decisions.

### Code shape for `_on_subtype_changed`

Insert BEFORE line 626 and add toast AFTER line 626:

```python
# hq-disable-toast-2026q3-e1: capture prior state before the eligible call
# may clear it.  Must come before set_hq_smoothing_eligible().
_prior_hq = self.appearance_panel.hq_smoothing   # pure bool, no side effects

is_hq_eligible = (
    variety == "Enriques surface"
    and name in _HQ_SMOOTHING_ELIGIBLE_SUBTYPES
)
self.appearance_panel.set_hq_smoothing_eligible(is_hq_eligible)

# hq-disable-toast-2026q3-e1: when the user switches to an ineligible
# subtype with Double-pass smooth enabled, acknowledge the auto-disable.
# The toast fires BEFORE _render_current so it's visible during compute.
if _prior_hq and not is_hq_eligible:
    self.statusBar().showMessage(
        f"Subtype: {name}.  Double-pass smooth disabled — only available "
        f"on Enriques figs 1+2 (double-curve topology)."
    )
```

### Toast wording

**In `_on_variety_changed`:** Per the brief's proposal, the variety message already occupies the status bar. The combined string per-branch is the only robust approach. Example for K3:

> "Variety: K3 surface. Now choose a model.  Double-pass smooth disabled — only available on Enriques figs 1+2."

**In `_on_subtype_changed`:** No prior variety-branch message exists (the status bar shows whatever the last render wrote). A simple `showMessage` before `_render_current` is fine:

> "Subtype: {name}.  Double-pass smooth disabled — only available on Enriques figs 1+2 (double-curve topology)."

**Note:** This message will be replaced by `_render_current`'s success/error message when the render completes (~449 ms later). For the variety-change case the render hasn't started yet (subtype not yet selected), so the message persists until the user picks a subtype. For the subtype-change case the message persists for ~449 ms then is replaced by the render result.

### Placement decision (Option A — append per-branch)

Modify each of the 4 variety branches in `_on_variety_changed` (lines 528–561) to check `_prior_hq` and include the HQ note in the message string when True. Example:

```python
_hq_note = (
    "  Double-pass smooth disabled — only available on Enriques figs 1+2."
    if _prior_hq else ""
)
if name == "Calabi–Yau 3-fold":
    self.statusBar().showMessage(
        f"Calabi–Yau 3-fold — each figure is a 2D real shadow of a "
        f"6-dimensional manifold.  Now choose a model.{_hq_note}"
    )
elif name == "Enriques surface":
    self.statusBar().showMessage(
        f"Enriques surface — back-face culling active to suppress "
        f"the double-curve zipper seam.  Now choose a model.{_hq_note}"
    )
# ... etc.
```

This approach: no `currentMessage()` read, no string concatenation after the fact, no character-limit risk. The `_hq_note` variable is empty string by default so the else branch also gets it automatically.

### AI-9 audit

- `self.appearance_panel.hq_smoothing` is a `@property` returning `self._hq_smoothing: bool` — pure Python attribute access. No signal emission, no Qt call. Safe anywhere.
- `self.statusBar().showMessage(text)` is a synchronous Qt call that updates the status bar text and triggers a paint. No `processEvents`. AI-9 clean.
- The ordering is: read `_prior_hq` → call `set_hq_smoothing_eligible(False)` → call variety-branch `showMessage` → conditionally include HQ note in the message string. No re-entrancy risk.

---

## 6. Decisions matrix

| Decision | Option A | Option B | Option C | Recommendation |
|---|---|---|---|---|
| **Placement** | Append to variety-branch string (per-branch, 4 sites) | Separate `showMessage(toast, 5000)` after branch | `currentMessage()` + append after branch | **Option A** — deterministic, no character-limit risk, no Qt API subtlety |
| **Wording style** | Explanatory: "...only available on Enriques figs 1+2 (double-curve topology)." | Short: "Double-pass smooth turned off — Enriques figs 1+2 only." | None | **Explanatory** — the brief's proposed text is adequate; add "(double-curve topology)" in the subtype variant only |
| **Acknowledgment scope** | `_on_variety_changed` only | `_on_variety_changed` AND `_on_subtype_changed` | None | **Both methods** — variety-only misses Fig.1 → Fig.3 transition |
| **Timing** | Before existing variety `showMessage` | After (replacing) variety `showMessage` | Combined with variety `showMessage` | **Combined (Option A above)** — appended to the variety message as `_hq_note` |
| **Test count** | 2 tests (source-grep only) | 3 tests | 4 tests | **3 tests minimum** — see Section 7 |

### Option B (timeout `showMessage`) analysis

Qt's `QStatusBar.showMessage(text, timeout_ms)` replaces the current message immediately (not after timeout) and then auto-clears (restores to permanent widget text, not prior message) after `timeout_ms` milliseconds. Using `showMessage("variety text")` followed by `showMessage("HQ note", 5000)` would show ONLY the HQ note for 5 seconds, then clear — the variety context message would be lost. This is NOT what we want. **Option B is rejected.**

### Option C (currentMessage) analysis

`QStatusBar.currentMessage()` returns the current temporary message text. After calling `showMessage("Variety: K3…")`, `currentMessage()` would return that string. Then `showMessage(f"{currentMessage()}  HQ note")` would produce the combined string. This works but is fragile: if any other code path calls `showMessage` between the variety branch call and the currentMessage read (unlikely but possible in a signal chain), the read picks up stale text. Option A is cleaner. **Option C is rejected.**

---

## 7. Test plan

All tests are source-text greps (AI-2 compliant). Suggested file: `tests/test_hq_disable_toast.py`.

### Test 1: `test_hq_disable_toast_captures_prior_state_before_eligible_call_in_variety_changed`

Assert that in `_on_variety_changed`, the source reads `appearance_panel.hq_smoothing` at a line BEFORE the line containing `set_hq_smoothing_eligible(False)`.

```python
_APP_SRC = pathlib.Path("app.py").read_text()

def test_hq_disable_toast_captures_prior_state_before_eligible_call_in_variety_changed():
    idx_read = _APP_SRC.find("_prior_hq = self.appearance_panel.hq_smoothing")
    idx_clear = _APP_SRC.find("self.appearance_panel.set_hq_smoothing_eligible(False)")
    assert idx_read != -1, "_prior_hq capture missing in app.py"
    assert idx_clear != -1, "set_hq_smoothing_eligible(False) call missing"
    assert idx_read < idx_clear, (
        "_prior_hq must be captured BEFORE set_hq_smoothing_eligible(False) — "
        "the eligible call clears _hq_smoothing to False, so reading after it "
        "always returns False regardless of prior user state."
    )
```

### Test 2: `test_hq_disable_toast_conditional_guard_present_in_variety_changed`

Assert that the `if _prior_hq` (or equivalent) conditional guard appears in `_on_variety_changed` body after the `set_hq_smoothing_eligible(False)` call.

```python
def test_hq_disable_toast_conditional_guard_present_in_variety_changed():
    assert "if _prior_hq" in _APP_SRC, (
        "'if _prior_hq' conditional guard missing from app.py — the toast must "
        "only fire when the user had Double-pass smooth enabled before the switch."
    )
```

### Test 3: `test_hq_disable_toast_message_references_enriques_eligibility_scope`

Assert that the acknowledgment text contains a reference to "Enriques figs 1+2" (or equivalent) and "Double-pass smooth disabled" so the message accurately explains WHY the auto-disable happened.

```python
def test_hq_disable_toast_message_references_enriques_eligibility_scope():
    assert "Double-pass smooth disabled" in _APP_SRC, (
        "Status-bar toast must include 'Double-pass smooth disabled' — AI-15: "
        "the message must name what was auto-disabled and why."
    )
    assert "Enriques figs 1+2" in _APP_SRC or "Enriques fig" in _APP_SRC, (
        "Status-bar toast must reference Enriques fig scope — the auto-disable "
        "reason is per-subtype topology (double-curve only, per CONTEXT.md §8.13)."
    )
```

### Test 4 (optional but recommended): `test_hq_disable_toast_also_present_in_subtype_changed`

Assert that the prior-state capture + conditional guard ALSO appears in `_on_subtype_changed`.

```python
def test_hq_disable_toast_also_present_in_subtype_changed():
    # Both occurrences must be present — one in each method.
    count = _APP_SRC.count("_prior_hq = self.appearance_panel.hq_smoothing")
    assert count >= 2, (
        f"Expected >= 2 '_prior_hq' captures (one in _on_variety_changed, one in "
        f"_on_subtype_changed) but found {count}. Enriques Fig.1 → Fig.3 transitions "
        f"are only caught by _on_subtype_changed."
    )
```

**4 tests total.** All source-grep, AI-2 compliant, Qt-free.

---

## 8. AI-1..AI-15 conflict scan

| Invariant | Status | Notes |
|---|---|---|
| AI-1 (PySide6 + PyVista stack) | GREEN | Pure status-bar call + bool read; no renderer change |
| AI-2 (Qt-free tests) | GREEN | All proposed tests are source-grep; no Qt construction |
| AI-3 (offscreen render verification) | GREEN | No render verification needed for a status-bar change |
| AI-4 (clip_scalar domain clip) | GREEN | Not touched |
| AI-5 (clip_scalar scalars= kwarg) | GREEN | Not touched |
| AI-6 (implicit vs parametric pipelines) | GREEN | Not touched |
| AI-7 (Hanson normals) | GREEN | Not touched |
| AI-8 (Surface/ParamSpec dataclass contract) | GREEN | Not touched |
| AI-9 (re-entrancy guard) | GREEN | `showMessage` is synchronous, no processEvents; `hq_smoothing` read is pure Python bool; no signal chain risk |
| AI-10 (raw mesh cached) | GREEN | Not touched |
| AI-11 (fully-qualified Qt enums) | GREEN | No new Qt enum usage |
| AI-12 (WCAG AA text contrast) | GREEN | No new colors introduced |
| AI-13 (6-digit hex only) | GREEN | No colors introduced |
| AI-14 (generator PolyData/ValueError contract) | GREEN | Not touched |
| AI-15 (math claim honesty) | GREEN | Toast message explains WHY: "only available on Enriques figs 1+2" matches the actual eligibility gate; references the correct per-subtype scope from CONTEXT.md §8.13 |

**AI-9 detailed:** The prior-state read (`self.appearance_panel.hq_smoothing`) is a pure `@property` returning a Python `bool`. No Qt signal, no `processEvents`. The `showMessage` call is a synchronous paint-queue update with no business-logic side effects. The entire sequence (read → clear → branch → toast) is in the GUI thread with no worker dispatch, no processEvents, no re-entrancy surface. Clean.

---

## 9. CONTEXT.md update plan

A CONTEXT.md §4.3a addition is warranted but MINIMAL. The existing §4.3a paragraph on `set_hq_smoothing_eligible` already documents the blockSignals architecture and the M1 rectification. Recommend adding ONE sentence to the end of the §4.3a HQ smoothing sub-paragraph:

> "When `set_hq_smoothing_eligible(False)` auto-disables an active toggle during a variety or subtype switch, `_on_variety_changed` and `_on_subtype_changed` emit a one-shot `statusBar().showMessage` acknowledgment so the user understands why the toggle was cleared (hq-disable-toast-2026q3-e1 / F-L2 closure)."

This is a ~2-line CONTEXT.md addition — sufficient to anchor the architecture decision without duplicating the inline code comments that will explain the mechanism.

---

## 10. Estimated diff size + inline-vs-delegated

| File | Change | Est. LOC |
|---|---|---|
| `app.py` | `_on_variety_changed`: add `_prior_hq` capture + `_hq_note` string + use in 4 `showMessage` branches | ~12 LOC |
| `app.py` | `_on_subtype_changed`: add `_prior_hq` capture + `if _prior_hq and not is_hq_eligible` toast | ~8 LOC |
| `tests/test_hq_disable_toast.py` | New test file: 4 source-grep tests | ~55 LOC |
| `CONTEXT.md` | §4.3a one-sentence addition | ~3 LOC |
| **Total** | | **~78 LOC** |

**Inline (no new module).** The change is entirely in `app.py` (2 method modifications) + a new test file. No new helpers, no new signals, no new panel API surface.

---

## 11. AI-15 disclaimers

The acknowledgment text "Double-pass smooth disabled — only available on Enriques figs 1+2" is AI-15 honest:

- "Double-pass smooth" = exactly 2 Taubin passes (surfaces.py:558/605, confirmed by hq-smoothing-label-rename-2026q3-e1 research). The label names the implementation accurately.
- "only available on Enriques figs 1+2" matches the actual eligibility gate in `_HQ_SMOOTHING_ELIGIBLE_SUBTYPES` (frozenset at app.py:73–76) — these are "Canonical sextic  [Fig. 1]" and "Diagonal λ-family  [Fig. 2]".
- CONTEXT.md §8.13 canonically explains WHY: Figs. 1+2 have double-curve singularities where the second Taubin pass attenuates the sawtooth-ridge artifact. Adding "(double-curve topology)" in the subtype-change variant is a minor enhancement, not required.
- No marketing language. The message explains the mechanism (auto-disabled), the scope (figs 1+2), without implying the feature is globally broken.

**Draft tooltip text for CONTEXT.md §8.13 cross-reference (no change needed):** The existing §8.13 text already canonically defines the double-curve scope. The toast text is derived from it correctly.

---

## 12. References

| File | Line | Item |
|---|---|---|
| `app.py` | 442 | `def _on_variety_changed` |
| `app.py` | 523 | `self.appearance_panel.set_hq_smoothing_eligible(False)` |
| `app.py` | 528–561 | Variety-specific `showMessage` branches |
| `app.py` | 581 | `def _on_subtype_changed` |
| `app.py` | 622–626 | `is_hq_eligible` computation + `set_hq_smoothing_eligible` call |
| `app.py` | 73–80 | `_HQ_SMOOTHING_ELIGIBLE_SUBTYPES` + `_HQ_SMOOTHING_ELIGIBLE_GENERATORS` frozensets |
| `appearance_panel.py` | 116 | `self._hq_smoothing: bool = False` initialization |
| `appearance_panel.py` | 558–570 | `hq_smoothing` property |
| `appearance_panel.py` | 572–614 | `set_hq_smoothing_eligible` (including blockSignals pattern at lines 609–613) |
| `.claude/notes/milestones/enriques-hq-smoothing-2026q3-e1/artifacts/adversary-critique.md` | 140–144 | Original F-L2 finding (enriques critic) |
| `.claude/notes/milestones/enriques-hq-smoothing-2026q3-e1/artifacts/adversary-critique.md` | 183–184 | F-L2 deferral justification |
| `.claude/notes/milestones/qtawesome-icons-2026q2-e2/artifacts/adversary-critique.md` | 215–219 | F-L2 in qtawesome-e2 (DIFFERENT finding: tooltip accessibility, NOT HQ) |
| `CONTEXT.md` | §4.3a | `hq_smoothing` property + `set_hq_smoothing_eligible` architecture + blockSignals rationale |
| `CONTEXT.md` | §8.13 | Double-curve vs A₁-node per-subtype scope rationale |
| `CONTEXT.md` | §8.16 | Spike timing log + per-subtype scope decision |
| `PySide6/QtWidgets.pyi` | 6308 | `QStatusBar.showMessage(text, timeout=None)` signature |

---

*End of research brief.*
