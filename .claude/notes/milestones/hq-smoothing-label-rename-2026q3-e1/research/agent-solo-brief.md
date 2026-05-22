# Research Brief — hq-smoothing-label-rename-2026q3-e1

**Researcher:** milestone-researcher (solo)
**Date:** 2026-05-22
**Milestone:** Close F-L1 from enriques-hq-smoothing-2026q3-e1 — rename "HQ smoothing" button label to "Double-pass smooth"

---

## 1. TL;DR

Replace exactly three user-visible strings (button label, status-bar suffix `[HQ]`, and any test assertions referencing the old label) while leaving all internal symbols untouched; this is a pure rename with zero logic change and ~35 LOC of functional diff. The main risk is missing a test that does a source-grep for `'QPushButton("HQ smoothing")'` — that test must be updated to assert the new label AND assert the old label does NOT appear (regression guard). The backup plan if the button label clips: shorten to "Double-pass" (11 chars; see §3 for the width reasoning).

---

## 2. Codebase audit — bucketed match table

### Legend
- **USER-VISIBLE** = must rename
- **TEST ASSERTION** = must rename (references user-visible string)
- **SYMBOL / COMMENT** = stays per brief decision
- **DOC PROSE** = rename in prose; preserve in code-quote blocks that document old name historically
- **HISTORICAL** = stays (agent-memory, milestone notes)

---

### appearance_panel.py

| Line | Text excerpt | Bucket | Action |
|------|-------------|--------|--------|
| 265 | `QPushButton("HQ smoothing")` | **USER-VISIBLE** | Rename to `QPushButton("Double-pass smooth")` |
| 269–279 | tooltip text (`"Apply a second Taubin smoothing pass ... "`) | **USER-VISIBLE** | Update first phrase (see §3) |
| 67–75 | `hq_smoothing_changed = Signal(bool)` comment block mentioning "HQ-smoothing toggle" | SYMBOL / COMMENT | STAYS |
| 107–116 | `self._hq_smoothing: bool = False` + comment | SYMBOL / COMMENT | STAYS |
| 202 | Comment: `"HQ smoothing trio"` | COMMENT | STAYS (describes internal naming) |
| 249–264 | Block comment: "HQ-smoothing toggle changes the MESH..." | COMMENT | STAYS |
| 384–399 | `def _on_hq_smoothing_toggled(...)` + docstring "Slot for the HQ-smoothing toggle." | SYMBOL / COMMENT | STAYS |
| 534–545 | `def hq_smoothing(self) -> bool:` + docstring | SYMBOL / COMMENT | STAYS |
| 547–589 | `def set_hq_smoothing_eligible(...)` + docstring | SYMBOL / COMMENT | STAYS |
| 635–641 | `refresh_icons` call to `hq_smoothing_icon(theme)` + comment | SYMBOL / COMMENT | STAYS |

### app.py

| Line | Text excerpt | Bucket | Action |
|------|-------------|--------|--------|
| 56–65 | `_HQ_SMOOTHING_ELIGIBLE_SUBTYPES`, `_HQ_SMOOTHING_ELIGIBLE_GENERATORS` | SYMBOL | STAYS |
| 241–246 | `hq_smoothing_changed.connect(...)` wiring + comment | SYMBOL / COMMENT | STAYS |
| 386–393 | Comment: `"enable the HQ-smoothing toggle"` + `set_hq_smoothing_eligible(False)` | COMMENT | STAYS |
| 473–485 | Comment: `"enable the 'HQ smoothing' toggle"` + `set_hq_smoothing_eligible(...)` | COMMENT | STAYS — note: the string `"HQ smoothing"` here is used in a comment, not as a user-facing string |
| 545–569 | `def _on_hq_smoothing_changed(...)` + docstring | SYMBOL / COMMENT | STAYS |
| 647–660 | `_is_hq_active` computation; `_hq_label = " [HQ]" if _is_hq_active else ""` | **USER-VISIBLE** | Rename: `_hq_label = " [Double-pass]" if _is_hq_active else ""` (see §4 decision) |
| 660 | Literal `" [HQ]"` in `_hq_label` assignment | **USER-VISIBLE** | Rename to `" [Double-pass]"` |
| 672–674 | Comment: "Hold the HQ label..." + `self._inflight_hq_label = _hq_label` | COMMENT + SYMBOL | STAYS (var name `_hq_label` stays; comment stays) |
| 678 | `f"Computing {surface.label}{_hq_label}…"` — uses `_hq_label` variable | SYMBOL (via var) | No change needed; gets renamed value automatically |
| 795–800 | Comment: `hq_label appended right after the surface label... "Enriques surface [HQ]"` | COMMENT | Update comment to reflect new label `[Double-pass]` |
| 1138–1141 | Comment: "greyed-out HQ-smoothing button" | COMMENT | STAYS |

### tests/test_enriques_hq_smoothing.py

| Line | Text excerpt | Bucket | Action |
|------|-------------|--------|--------|
| 172 | `assert 'QCheckBox("HQ smoothing")' not in src` | **TEST ASSERTION** | Update to: `assert 'QCheckBox("Double-pass smooth")' not in src` |
| 179 | `assert 'QPushButton("HQ smoothing")' in src` | **TEST ASSERTION** | Update to: `assert 'QPushButton("Double-pass smooth")' in src` |
| 326 | `hq_block_idx = src.find('QPushButton("HQ smoothing")')` | **TEST ASSERTION** | Update to: `src.find('QPushButton("Double-pass smooth")')` |
| 327 | `assert hq_block_idx > 0, "HQ smoothing button not found in source"` | **TEST ASSERTION** | Update error message to mention "Double-pass smooth" |
| Various (1–2, 35–42, etc.) | Docstrings/comments referencing "HQ smoothing" as a name for the feature | COMMENT | STAYS |
| 137–138 | `f"... HQ-off ({mesh_off.n_points}) and HQ-on..."` (in assertion messages) | COMMENT (test internal) | STAYS — these describe internal state, not the button label |

### tests/test_styles_palette.py

Grep result: **no matches** for "HQ smoothing" — this file has no assertions on the HQ button label. No changes needed.

### tests/test_status_bar_bbox.py

Grep result: **no matches** for "HQ smoothing" or "[HQ]". No changes needed.

### icons.py

| Line | Text excerpt | Bucket | Action |
|------|-------------|--------|--------|
| 188 | `HQ_SMOOTHING_ICON_NAME = "mdi6.auto-fix"` | SYMBOL | STAYS |
| 278 | `def hq_smoothing_icon(...)` | SYMBOL | STAYS |
| 279, 288–293 | Docstring: "HQ smoothing display-toggle" | COMMENT | STAYS |

### surfaces.py

| Line | Text excerpt | Bucket | Action |
|------|-------------|--------|--------|
| 205, 209 | Comments: "hq_smoothing param" | COMMENT | STAYS |
| 528 | `hq_smoothing: bool = False,` (kwarg) | SYMBOL | STAYS |
| 553–558 | Comments + `second_smooth_iter=40 if hq_smoothing else 0` | SYMBOL / COMMENT | STAYS |
| 574, 603–605 | Same pattern in `enriques_figure_2` | SYMBOL / COMMENT | STAYS |

### styles.py, view_panel.py, parameters_panel.py

Grep result: **no matches** for HQ or hq_smoothing. No changes needed.

### CONTEXT.md

| Lines | Text | Bucket | Action |
|-------|------|--------|--------|
| 147 | Prose: `"HQ smoothing"` button label + `hq_smoothing_changed = Signal(bool)` description | **DOC PROSE** | Update prose mentions of `"HQ smoothing"` as the button label to `"Double-pass smooth"`; preserve internal symbol names verbatim |
| 488 | Prose: `"HQ smoothing" QPushButton(checkable=True)` in the deferral-closed paragraph | **DOC PROSE** | Update to `"Double-pass smooth"` with a note that it was renamed from `"HQ smoothing"` by this milestone |

### README.md

Grep result: no file or no HQ matches — no changes needed.

### .claude/notes/milestones/enriques-hq-smoothing-2026q3-e1/ (milestone artifacts)

All content here is **HISTORICAL** — stays unchanged. The adversary-critique.md entry for F-L1 at line 134–138 is a historical record of the deferred finding; it accurately describes what was deferred and is NOT renamed (it's a diagnosis, not live UI text).

### .claude/agent-memory/ (agent memory files)

All content: **HISTORICAL** — stays unchanged.

---

## 3. Recommended approach

### Step 1 — appearance_panel.py (1 change)

**Button label** (`appearance_panel.py:265`):
```
OLD: QPushButton("HQ smoothing")
NEW: QPushButton("Double-pass smooth")
```

**Width fit reasoning:** The dock has `setMinimumWidth(200)` (`appearance_panel.py:127`). The button uses no fixed width; it stretches to the full group box width via `QVBoxLayout`. The peer buttons are "Wireframe" (9 chars) and "Show edges" (10 chars). "Double-pass smooth" (18 chars) is 8 chars longer than the next-longest button but will fit at 200px minimum dock width with the standard QPushButton font (~7–8px per char at 13pt → ~126–144px for 18 chars, well within 200px minus icon padding). No clipping risk at minimum dock width.

**Tooltip** (`appearance_panel.py:269–279`):
The current tooltip already starts with "Apply a second Taubin smoothing pass...". The new label "Double-pass smooth" is self-explanatory enough that the tooltip does NOT need to lead with a repetitive "Double-pass smooth:" prefix. Recommended minimal change: update the opening phrase to acknowledge the label relationship:
```
OLD: "Apply a second Taubin smoothing pass (n_iter=40, pass_band=0.05) to reduce the double-curve sawtooth-ridge artifact..."
NEW: "Applies a second Taubin smoothing pass (n_iter=40, pass_band=0.05) — two passes total — to reduce the double-curve sawtooth-ridge artifact..."
```
The phrase "two passes total" is the honest bridge from the label "Double-pass smooth" to the implementation. Everything else in the tooltip (the cost disclosure, hardware dependency warning, scope restriction) stays unchanged.

### Step 2 — app.py (1 change)

**Status-bar suffix** (`app.py:660`):
```
OLD: _hq_label = " [HQ]" if _is_hq_active else ""
NEW: _hq_label = " [Double-pass]" if _is_hq_active else ""
```
The variable name `_hq_label` stays. The comment at lines 653–657 that mentions `[HQ]` should be updated to reflect `[Double-pass]`.

Also update the comment at `app.py:795–797`:
```
OLD: # "Enriques surface [HQ] · … · 587 ms" when the toggle is on
NEW: # "Enriques surface [Double-pass] · … · 587 ms" when the toggle is on
```

### Step 3 — tests/test_enriques_hq_smoothing.py (3 line changes + new tests)

Update the three source-grep assertions that look for the old button label string:
- `line 172`: change `'QCheckBox("HQ smoothing")'` to `'QCheckBox("Double-pass smooth")'`
- `line 179`: change `'QPushButton("HQ smoothing")'` to `'QPushButton("Double-pass smooth")'`
- `line 326`: change `src.find('QPushButton("HQ smoothing")')` to `src.find('QPushButton("Double-pass smooth")')`
- `line 327`: update error message string

Add 4 new regression-guard tests (see §5).

### Step 4 — CONTEXT.md prose updates (optional, judgment call — see §4)

---

## 4. Decisions

| Decision | Options | Picked | Justification |
|----------|---------|--------|---------------|
| **Tooltip first phrase** | (A) Keep "Apply a second Taubin smoothing pass..." unchanged | (B) Add "— two passes total —" to bridge label and implementation | **B** — the label says "Double-pass" so the tooltip should confirm what "double" means (n=2 passes, not n=2 iterations). Minimal change. |
| **Status-bar suffix** | `[HQ]` vs `[Double-pass]` vs `[2-pass]` vs `[Double-pass smooth]` | **`[Double-pass]`** | Matches the label's most distinctive word. `[2-pass]` is too cryptic without context. `[Double-pass smooth]` is too long for the status bar; the status bar already says "Enriques surface" so "smooth" is implied. `[HQ]` is exactly what we're replacing. |
| **Comment at `appearance_panel.py:202`** "HQ smoothing trio" | Leave as-is vs update | **Leave as-is** | Internal comment describing the naming of the group (`_hq_smoothing_cb`), not user-visible text. Renaming it adds zero value and could confuse future readers who need to reconcile with the symbol name `_hq_smoothing_cb`. |
| **Comment at `app.py:473`** "enable the 'HQ smoothing' toggle" | Leave as-is vs update | **Leave as-is** | This is a description of the internal signal/slot pattern, not the user-visible label. The symbol name it refers to (`_hq_smoothing_cb`) is not changing. |
| **CONTEXT.md §4.3a prose** | Full prose rename throughout | **Update button-label references only** | The section refers to both the user-facing label (must update: `"HQ smoothing" QPushButton`) and the internal symbol (`hq_smoothing_changed = Signal(bool)` — must NOT rename). Be surgical: replace the quoted label strings `"HQ smoothing"` in prose with `"Double-pass smooth"` and add a parenthetical `(formerly "HQ smoothing" — renamed by hq-smoothing-label-rename-2026q3-e1)`. |
| **CONTEXT.md §8.16 prose** | Full rename vs add a note | **Add rename note** | The §8.16 "deferral closed" paragraph is historical documentation of how the feature shipped. Update the single phrase `"HQ smoothing" QPushButton(checkable=True)` to `"Double-pass smooth" QPushButton(checkable=True)` and append a one-sentence note: "Relabeled to 'Double-pass smooth' by hq-smoothing-label-rename-2026q3-e1 (F-L1 closure)." |
| **Variable `_hq_label` in app.py** | Rename to `_double_pass_label` vs keep | **Keep `_hq_label`** | Pure internal variable name. Renaming gains nothing (no API surface, no test asserts the var name) and risks introducing a typo in the refactor. The brief explicitly permits this. |
| **`_hq_smoothing` field name** | Rename to `_double_pass_smooth` vs keep | **Keep** | Per brief: internal symbol names stay as-is to avoid blast-radius churn. |

---

## 5. Test plan

All tests are pure source-text greps (AI-2 compliant — no QApplication).

### Test 1 — `test_appearance_panel_uses_double_pass_smooth_label`
```python
def test_appearance_panel_uses_double_pass_smooth_label() -> None:
    src = (pathlib.Path(__file__).resolve().parent.parent / "appearance_panel.py").read_text(encoding="utf-8")
    assert 'QPushButton("Double-pass smooth")' in src, (
        "appearance_panel.py is missing QPushButton('Double-pass smooth') — "
        "the relabeled opt-in toggle from hq-smoothing-label-rename-2026q3-e1."
    )
```

### Test 2 — `test_appearance_panel_does_not_use_old_hq_smoothing_label`
```python
def test_appearance_panel_does_not_use_old_hq_smoothing_label() -> None:
    src = (pathlib.Path(__file__).resolve().parent.parent / "appearance_panel.py").read_text(encoding="utf-8")
    assert 'QPushButton("HQ smoothing")' not in src, (
        "appearance_panel.py still contains QPushButton('HQ smoothing') — "
        "regression: the label rename to 'Double-pass smooth' did not apply."
    )
```

### Test 3 — `test_app_status_bar_uses_double_pass_suffix`
```python
def test_app_status_bar_uses_double_pass_suffix() -> None:
    src = (pathlib.Path(__file__).resolve().parent.parent / "app.py").read_text(encoding="utf-8")
    assert '"[Double-pass]"' in src or '" [Double-pass]"' in src, (
        "app.py is missing the '[Double-pass]' status-bar suffix — "
        "hq-smoothing-label-rename-2026q3-e1 must update the _hq_label string."
    )
```

### Test 4 — `test_app_status_bar_does_not_use_old_hq_suffix`
```python
def test_app_status_bar_does_not_use_old_hq_suffix() -> None:
    src = (pathlib.Path(__file__).resolve().parent.parent / "app.py").read_text(encoding="utf-8")
    # Allow the variable name _hq_label and comments; disallow the old literal.
    assert '" [HQ]"' not in src, (
        "app.py still contains the ' [HQ]' status-bar string — "
        "regression: the status-bar suffix rename to '[Double-pass]' did not apply."
    )
```

### Update to existing Test 5 (modify, not replace)

The existing `test_hq_smoothing_toggle_is_checkable_qpushbutton_in_appearance_panel` and `test_hq_smoothing_disabled_by_default_in_appearance_panel` contain the three source-grep assertions on the old label (lines 172, 179, 326). These must be updated in-place to use "Double-pass smooth". The assertion at line 172 (QCheckBox negative guard) is updated to check the new label string.

**Note:** Tests 1 and 2 above are new tests that complement the existing test rather than replacing it. The existing test should be updated to use the new label AND the two new tests should be added. The four-test set (2 positive + 2 negative for both button and status-bar) provides full regression coverage per the brief.

---

## 6. AI-1..AI-15 conflict scan

| Invariant | Status | Notes |
|-----------|--------|-------|
| AI-1 (PySide6/PyVista/pyvistaqt stack) | GREEN | Pure label rename; no renderer change. |
| AI-2 (Qt-free tests) | GREEN | All new/updated tests are pure source-text greps — no QApplication needed. |
| AI-3 (off-screen render via pv.OFF_SCREEN) | GREEN | No render code touched. |
| AI-4 (clip_scalar not clip_box) | GREEN | Domain clip not touched. |
| AI-5 (scalars= kwarg on clip_scalar) | GREEN | Not touched. |
| AI-6 (implicit vs parametric pipeline discipline) | GREEN | No mesh generation code touched. |
| AI-7 (Hanson normals cell_normals=True) | GREEN | Not touched. |
| AI-8 (Surface/ParamSpec registry contract) | GREEN | No dataclass or registry changes. |
| AI-9 (re-entrancy guard) | GREEN | No event-loop or processEvents change. |
| AI-10 (raw mesh cached; domain clip doesn't regenerate) | GREEN | Not touched. |
| AI-11 (fully-qualified Qt enums) | GREEN | No new Qt widget code beyond label string. |
| AI-12 (WCAG AA text contrast) | GREEN | No color change. |
| AI-13 (6-digit hex only for PyVista) | GREEN | No color change. |
| AI-14 (generator pv.PolyData / ValueError contract) | GREEN | No generator change. |
| AI-15 (math claim honesty) | GREEN | "Double-pass smooth" is technically accurate: exactly 2 Taubin passes (n_iter=20 then n_iter=40). "Double-pass" = TRUE. "smooth" = TRUE (both passes are Taubin smoothing). No dishonest marketing. See §7 for full AI-15 attestation. |

---

## 7. AI-15 disclaimers

**Label accuracy attestation for "Double-pass smooth":**

- "Double-pass" — TRUE: `_marching_cubes_to_polydata` runs `smooth_taubin(n_iter=20, pass_band=0.1)` as the standard first pass (for all implicit surfaces, AI-6 requirement), then conditionally runs `smooth_taubin(n_iter=40, pass_band=0.05)` as the second pass when `second_smooth_iter > 0` (`surfaces.py:558, 605`). Exactly 2 Taubin passes fire when the toggle is ON.
- "smooth" — TRUE: both passes are Taubin smoothing (volume-preserving). Not Loop subdivision, not Catmull-Clark, not Laplacian shrinking. The word "smooth" in the label directly names the operation class.
- The tooltip already contains the honest cost disclosure: "+31% generate time, hardware-dependent". This must be preserved unchanged.
- The tooltip phrase "two passes total" (proposed addition) correctly reinforces the "Double" in the label.

**No new variety or figure is proposed — AI-15 is trivially satisfied; no "real shadow" or "birational" disclaimers needed.**

---

## 8. Estimated diff size + files-touched

| File | Est. LOC changed | Type |
|------|-----------------|------|
| `appearance_panel.py` | ~3 | Label string + tooltip phrase |
| `app.py` | ~3 | Status-bar suffix string + 2 comment updates |
| `tests/test_enriques_hq_smoothing.py` | ~15 | 3 existing assertion updates + 4 new tests |
| `CONTEXT.md` | ~4 | Prose label references + rename note |
| **Total** | **~25 LOC** | |

**Inline vs delegated:** This is a pure S-effort (XS if CONTEXT.md is excluded). Recommend inline implementation — the implementer can handle all changes in a single focused pass without a separate sub-agent.

**Recommended commit message:** `feat(hq-smoothing-label-rename-2026q3-e1): rename "HQ smoothing" → "Double-pass smooth" (F-L1)`

---

## 9. References

| File | Lines | Claim verified |
|------|-------|---------------|
| `appearance_panel.py` | 127 | `setMinimumWidth(200)` — confirms button has 200px minimum width; "Double-pass smooth" fits |
| `appearance_panel.py` | 265–282 | Exact button label `QPushButton("HQ smoothing")` and tooltip text |
| `appearance_panel.py` | 198–208 | Render Mode group box; peer buttons "Wireframe", "Show edges" |
| `app.py` | 660 | `_hq_label = " [HQ]" if _is_hq_active else ""` — the status-bar suffix |
| `app.py` | 678 | `f"Computing {surface.label}{_hq_label}…"` — the computing message |
| `app.py` | 800 | `f"{surface.label}{hq_label}  ·  ..."` — the success message |
| `tests/test_enriques_hq_smoothing.py` | 172, 179, 326 | Three test assertions that reference the old label string |
| `.claude/notes/milestones/enriques-hq-smoothing-2026q3-e1/artifacts/adversary-critique.md` | 134–138 | F-L1 finding: original critique recommending "Double-pass smooth" |
| `surfaces.py` | 558, 605 | `second_smooth_iter=40 if hq_smoothing else 0` — confirms exactly 2 Taubin passes |
| `CONTEXT.md` | 147, 488 | Prose references to "HQ smoothing" button label that need updating |

---

*End of research brief.*
