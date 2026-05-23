# Research Brief — appearance-panel-render-mode-split-2026q3-e3

**Status:** complete  
**Date:** 2026-05-22  
**Agent:** solo (milestone is XS; single agent per --single mode precedent for sub-200 LOC label renames)

---

## 1. TL;DR

Rename `QGroupBox("Render Mode")` at `appearance_panel.py:208` to `QGroupBox("Display && Quality")` (double-ampersand for literal `&` in Qt mnemonic context), update the inline comment block at lines 199–207 to record the rename rationale and milestone id, update 2 CONTEXT.md prose occurrences (lines 147 and 488) from "Render Mode group" to "Display & Quality group" (prose; code-quote blocks that document historical context stay), and update `test_appearance_panel_render_mode_group_header` in `tests/test_styles_palette.py` (lines 842–869) to assert the new header and gate against both the old "Render Mode" and the even-older "Display" header.  The main risk is the Qt mnemonic interpretation of `&` — a bare `"Display & Quality"` would underline "Q" as an Alt-Q shortcut, so the literal-ampersand escape `"Display && Quality"` is required.  Backup plan: use `"Display and Quality"` (avoids the escape entirely) — still semantically accurate, no Qt mnemonic handling needed, but loses the visual conciseness of `&`.

---

## 2. Codebase Audit — Bucketed Match Table

### USER-VISIBLE STRING — MUST RENAME

| File | Line | Snippet | Action |
|------|------|---------|--------|
| `appearance_panel.py` | 208 | `box = QGroupBox("Render Mode")` | **Rename** → `QGroupBox("Display && Quality")` |

### TEST ASSERTION referencing user-visible string — MUST UPDATE

| File | Line | Snippet | Action |
|------|------|---------|--------|
| `tests/test_styles_palette.py` | 842 | `def test_appearance_panel_render_mode_group_header()` | **Rename function** → `test_appearance_panel_display_and_quality_group_header` |
| `tests/test_styles_palette.py` | 843–844 | Docstring: `"display-toggles group's QGroupBox header is "Render Mode""` | **Update docstring** to reference new header |
| `tests/test_styles_palette.py` | 857 | `assert 'QGroupBox("Render Mode")' in src` | **Replace** → `assert 'QGroupBox("Display && Quality")' in src` |
| `tests/test_styles_palette.py` | 858–859 | Error message string: `"missing QGroupBox('Render Mode')"` | **Update** error text |
| `tests/test_styles_palette.py` | 862–863 | Comment: `# case where someone adds a Render Mode group elsewhere` | **Update comment** |
| `tests/test_styles_palette.py` | 864 | `assert 'QGroupBox("Display")' not in src` | **KEEP** (already correct — still a valid regression guard) |
| `tests/test_styles_palette.py` | 865–869 | Error message referencing "F-L2 milestone renamed it to 'Render Mode'" | **Update** — add "then F-M2 renamed it to 'Display & Quality'" trail |
| `tests/test_styles_palette.py` | 864–869 | Add new negative assertion: `assert 'QGroupBox("Render Mode")' not in src` | **NEW** — regression guard against reverting to old name |

### TEST DOCSTRING — update prose only (not assertion strings)

| File | Line | Snippet | Action |
|------|------|---------|--------|
| `tests/test_enriques_hq_smoothing.py` | 355 | `"""The Render Mode group's third button must read 'Double-pass smooth'` | **Update docstring prose** only: "Render Mode group" → "Display & Quality group"; assertion logic unchanged |

### CODE COMMENT / DOCSTRING — inline comments that record rationale — UPDATE per precedent

| File | Lines | Snippet | Action |
|------|-------|---------|--------|
| `appearance_panel.py` | 199–207 | Comment block citing MeshLab/Blender/ParaView rationale for "Render Mode" | **Update**: change "Render Mode" to "Display & Quality" in the new-rationale sentence; preserve the historical "MeshLab/Render Mode" peer-tool audit text as attributed context (`appearance-panel-layout-pass-2026q3-e2` chose it; this milestone supersedes per `appearance-panel-render-mode-split-2026q3-e3`) |
| `appearance_panel.py` | 155–161 | Comment: `"vs the 4px Render Mode group below"` (×2 occurrences) | **Update both** occurrences: "Render Mode group" → "Display & Quality group" |
| `appearance_panel.py` | 173 | Comment: `"display-toggle buttons in the Render Mode group below"` | **Update**: "Render Mode group" → "Display & Quality group" |
| `styles.py` | 483 | Comment: `"fracture against the Render Mode group below"` | **Update**: "Render Mode group" → "Display & Quality group" |

### DOC PROSE — CONTEXT.md — UPDATE in prose; preserve code-quote blocks documenting history

| File | Line | Snippet | Action |
|------|------|---------|--------|
| `CONTEXT.md` | 147 | Prose: `"This is the only Render Mode-group toggle that regenerates"` | **Update** "Render Mode-group" → "Display & Quality group"; add parenthetical `(renamed from "Render Mode" by appearance-panel-render-mode-split-2026q3-e3)` once, in the first occurrence |
| `CONTEXT.md` | 488 | Prose: `"the Appearance dock's Render Mode group (renamed from 'Display')"` | **Update** "Render Mode group" → "Display & Quality group"; update the parenthetical to `(renamed from "Display" by appearance-panel-layout-pass-2026q3-e2, then to "Display & Quality" by appearance-panel-render-mode-split-2026q3-e3)` |

### SYMBOL NAMES / INTERNAL NAMES — STAYS per brief

| File | Symbol | Stays |
|------|--------|-------|
| `appearance_panel.py:198` | `_build_toggles_group` method name | STAYS |
| `appearance_panel.py:235,241,246` | `setProperty("role", "display-toggle")` on all 3 buttons | STAYS |
| `appearance_panel.py:231` | `self._wireframe_cb` | STAYS |
| `appearance_panel.py:239` | `self._edges_cb` | STAYS |
| `appearance_panel.py` | `self._hq_smoothing_cb` | STAYS |

### HISTORICAL — milestone notes from completed milestones — STAYS

All occurrences in:
- `.claude/notes/milestones/hq-smoothing-label-rename-2026q3-e1/` (all files)
- `.claude/notes/milestones/appearance-panel-layout-pass-2026q3-e2/` (all files)
- `.claude/notes/milestones/display-toggles-checkable-button-2026q3-e1/` (all files)
- `.claude/agent-memory/milestone-researcher/lessons.md`
- `.claude/agent-memory/milestone-adversary-critic/lessons.md`
- `.claude/agent-memory/milestone-frontend-ux-critic/lessons.md`

These are completed-milestone artifacts / historical records — unchanged.

---

## 3. Recommended Approach

**Exact string to use:** `"Display && Quality"`

Qt's `QGroupBox` inherits the mnemonic/accelerator interpretation of `&` from `QLabel` — when the title contains a single `&`, Qt underlines the next character and makes it an `Alt+<key>` shortcut. `"Display & Quality"` (single `&`) would make `Q` an `Alt+Q` accelerator (unintended). The escape form `"Display && Quality"` produces a literal displayed `&` with no accelerator. This is standard Qt behavior documented in `QLabel::text` property notes (Qt 5/6 docs).

No other QGroupBox title in the codebase currently uses `&` — all existing headers are single-word or two-word noun titles (`"Colors"`, `"Opacity"`, `"Shading"`). "Display & Quality" would be the first compound header. The `&&` escape is the correct and idiomatic Qt way to display a literal ampersand; it does not require any additional handling.

**Alternative: `"Display and Quality"`** — avoids the `&&` escape entirely; the displayed string is identical in semantics. Recommendation per brief: use `&&` (canonical compound-label form; matches ParaView's tab naming convention, consistent with how Qt compound widgets are labeled in GUI-builder-based tools). The `&&` form is the correct choice per the brief's explicit mention of "Display & Quality" as the target.

**Implementation steps in order:**

1. `appearance_panel.py:208` — rename `QGroupBox("Render Mode")` → `QGroupBox("Display && Quality")`
2. `appearance_panel.py:199–207` — update comment block: keep the historical peer-tool rationale sentence (it describes why "Render Mode" was chosen by `appearance-panel-layout-pass-2026q3-e2`), add a new sentence explaining why this milestone supersedes it: *"'Display & Quality' is more accurate: Wireframe / Show edges are display-pipeline toggles (change `actor.prop.*`); Double-pass smooth is a quality toggle (changes mesh fidelity). ParaView's Display tab follows the same single-group-multiple-axes pattern."* End with `# appearance-panel-render-mode-split-2026q3-e3 (F-M2 closure)`.
3. `appearance_panel.py:155–161` — update 2 occurrences of "Render Mode group" → "Display & Quality group"
4. `appearance_panel.py:173` — update 1 occurrence of "Render Mode group below" → "Display & Quality group below"
5. `styles.py:483` — update 1 occurrence: "Render Mode group below" → "Display & Quality group below"
6. `CONTEXT.md:147` — update "Render Mode-group" → "Display & Quality group" in prose; add parenthetical note
7. `CONTEXT.md:488` — update the parenthetical to include this milestone's rename
8. `tests/test_styles_palette.py:842–869` — rename function + update docstring + update 3 assertion strings + add new `'QGroupBox("Render Mode")' not in src` guard
9. `tests/test_enriques_hq_smoothing.py:355` — update docstring prose only ("Render Mode group" → "Display & Quality group")

---

## 4. Decisions Matrix

| Decision | Options | Pick | Justification |
|----------|---------|------|---------------|
| **Ampersand handling in QGroupBox title** | (a) `"Display & Quality"` — single `&`, activates Qt mnemonic on `Q` (Alt+Q shortcut, unintended)<br>(b) `"Display && Quality"` — double `&`, displays literal `&`, no shortcut<br>(c) `"Display and Quality"` — avoids the issue entirely | **(b) `"Display && Quality"`** | Qt `QGroupBox`/`QLabel` mnemonic handling: single `&` before a letter creates an `Alt+letter` keyboard shortcut. There is no existing precedent in this codebase for intentional group-box accelerators. Double `&&` is the canonical Qt escape for a displayed literal `&`. `"Display and Quality"` is acceptable as backup but the brief specifies the `&` form, and `&&` is idiomatic Qt. |
| **Comment at `appearance_panel.py:199–207`** | (a) Replace entire comment with new rationale<br>(b) Keep historical rationale + append new superseding rationale | **(b) Keep historical + append** | Precedent from `hq-smoothing-label-rename-2026q3-e1`: "preserve in code-quote blocks / attributed context." The MeshLab peer-tool audit is accurate historical context (it explains *why* "Render Mode" was chosen in `appearance-panel-layout-pass-2026q3-e2`). A future reader benefits from understanding both the prior choice and why it was superseded. |
| **`_build_toggles_group` method name** | Rename to `_build_display_quality_group` or stay | **STAYS as `_build_toggles_group`** | Brief explicitly: internal symbol names stay. `_build_toggles_group` describes the technical pattern (toggle buttons), not the user-facing semantic axis. |
| **CONTEXT.md §4.3a / §8.16 prose** | (a) Full prose rename<br>(b) Rename prose + add parenthetical "renamed from 'Render Mode'" note | **(b) Rename prose + parenthetical** | Exact precedent from `hq-smoothing-label-rename-2026q3-e1` research brief (line 175–176 of that brief): "Be surgical: replace the quoted label strings in prose and add a parenthetical (formerly X — renamed by milestone-id)." The parenthetical anchors the rename for future git-blame readers. |
| **Test function rename** | (a) Keep `test_appearance_panel_render_mode_group_header`<br>(b) Rename to `test_appearance_panel_display_and_quality_group_header` | **(b) Rename** | The function name is the only discoverable documentation of what it guards. After the rename, a function asserting "Display & Quality" named `render_mode_group_header` is semantically misleading. The rename is cosmetic (no behavior change) but worth it for clarity. Precedent: `hq-smoothing-label-rename-2026q3-e1` renamed `_format_bbox` → `_format_size` for the same reason. |
| **`"display-toggle"` role property on all 3 buttons** | Rename role or stay | **STAYS as `"display-toggle"`** | Brief explicitly. Role property describes the technical widget pattern; not a user-visible string. Internal to the QSS selector. |
| **Variable name `vl` in `_build_toggles_group`** | Stay | **STAYS** | No semantic change warranted; single-scope layout variable. |

---

## 5. Test Plan

### Primary test — `test_appearance_panel_display_and_quality_group_header` (renamed from `test_appearance_panel_render_mode_group_header`)

**Exact assertions for the updated test:**

```python
def test_appearance_panel_display_and_quality_group_header() -> None:
    """appearance-panel-render-mode-split-2026q3-e3 (F-M2 closure): the
    display-toggles group's QGroupBox header is "Display && Quality"
    (displayed as "Display & Quality" — the && is the Qt literal-ampersand
    escape).  "Render Mode" was chosen by appearance-panel-layout-pass-2026q3-e2
    (F-L2) but misclassified Double-pass smooth: Wireframe/Show-edges are
    display-pipeline toggles; Double-pass smooth is a quality toggle that
    changes mesh fidelity.  Path (a) from the adversary critique: single group
    stays, label acknowledges both axes.

    Source-text grep (AI-2 compliant — verifying the QGroupBox label
    under a real QApplication would require Qt, which AI-2 bans).
    """
    import pathlib
    src = (
        pathlib.Path(__file__).resolve().parent.parent / "appearance_panel.py"
    ).read_text(encoding="utf-8")

    assert 'QGroupBox("Display && Quality")' in src, (
        "appearance_panel.py is missing QGroupBox('Display && Quality') — the "
        "display-toggles-group header rename from the F-M2 milestone "
        "(appearance-panel-render-mode-split-2026q3-e3)."
    )
    # The old "Render Mode" header must NOT remain.
    assert 'QGroupBox("Render Mode")' not in src, (
        "appearance_panel.py still contains QGroupBox('Render Mode') — "
        "regression: the F-M2 milestone renamed it to 'Display && Quality'.  "
        "Internal symbol names (_build_toggles_group, 'display-toggle' role) "
        "are NOT tested here — only the user-visible group-box header."
    )
    # The even-older generic "Display" header must NOT appear either.
    assert 'QGroupBox("Display")' not in src, (
        "appearance_panel.py contains QGroupBox('Display') — the "
        "appearance-panel-layout-pass-2026q3-e2 renamed it away from 'Display'.  "
        "If a future group genuinely needs to be called 'Display', pick a "
        "more specific name."
    )
```

### Secondary docstring update (no assertion change)

`tests/test_enriques_hq_smoothing.py:355`:
- Change `"""The Render Mode group's third button` → `"""The Display & Quality group's third button`
- No assertion code changes (that test only checks `QPushButton("Double-pass smooth")` content, unaffected)

### Verification that no other test imports construct an AppearancePanel or inspect group headers

Grep confirms no other test files reference `QGroupBox`, `Render Mode`, or `_build_toggles_group`. The only affected tests are in `test_styles_palette.py` and `test_enriques_hq_smoothing.py`. All tests are AI-2-compliant source-text greps.

---

## 6. AI-1..AI-15 Conflict Scan

| Invariant | Status | Notes |
|-----------|--------|-------|
| AI-1 PySide6/PyVista/pyvistaqt stack | GREEN | No stack change; QGroupBox title rename only |
| AI-2 Qt-free test suite | GREEN | All tests are source-text greps, no QApplication needed |
| AI-3 Off-screen render via pv.OFF_SCREEN | GREEN | No render-path changes |
| AI-4 clip_scalar not clip_box | GREEN | No clipping changes |
| AI-5 clip_scalar scalars= kwarg | GREEN | No clipping changes |
| AI-6 Implicit/parametric pipeline separation | GREEN | No mesh generation changes |
| AI-7 Hanson normals | GREEN | No normals changes |
| AI-8 VARIETIES registry / ParamSpec | GREEN | No surface registry changes |
| AI-9 Re-entrancy guard `_computing` | GREEN | No event loop / processEvents changes |
| AI-10 Raw mesh cache | GREEN | No render path changes |
| AI-11 Fully-qualified Qt enums | GREEN | No enum usage introduced; `QGroupBox("Display && Quality")` is a string, not an enum |
| AI-12 WCAG AA text contrast | GREEN | No color changes |
| AI-13 6-digit hex only | GREEN | No hex literals introduced |
| AI-14 Generator pv.PolyData / ValueError contract | GREEN | No generator changes |
| AI-15 Math claim honesty | GREEN | "Display & Quality" is factually accurate (see section 7 below) |

**Qt mnemonic note (not an AI-N conflict but an implementation correctness point):** `"Display && Quality"` (double ampersand) is the required string literal in the Python source. It renders to the user as "Display & Quality" with no keyboard shortcut. A single `&` would activate Alt+Q as a group-box shortcut — unintended and not idiomatic for this panel style. This is a correctness concern, not an AI-N violation.

---

## 7. AI-15 Disclaimers

This milestone does not introduce a new variety or figure — no new mathematical object is being plotted. The AI-15 audit is limited to verifying that "Display & Quality" accurately describes the group's contents:

- **"Display"** — TRUE for:
  - Wireframe button (`appearance_panel.py:231`): calls `actor.prop.style = pv.plotting.opts.InterpolationType.WIREFRAME` (display-pipeline toggle; no mesh regeneration)
  - Show edges button (`appearance_panel.py:239`): calls `actor.prop.show_edges = True/False` (display-pipeline toggle; no mesh regeneration)
  - CONTEXT.md §4.3a confirms: "those toggles change actor *display properties* (`actor.prop.style`, `actor.prop.show_edges`) and call `_get_plotter().render()` directly"

- **"Quality"** — TRUE for:
  - Double-pass smooth button (`appearance_panel.py:271`): emits `hq_smoothing_changed = Signal(bool)` → `MainWindow._on_hq_smoothing_changed` → `_invalidate_clipped_mesh()` + `_render_current()` — full mesh regeneration. CONTEXT.md §4.3a: "Double-pass smooth changes the **mesh** (the second Taubin pass moves every vertex by ~0.0015 units mean displacement)" — this is a mesh-fidelity / quality change, not an actor-display toggle.

- **"&"** — TRUE; the group contains BOTH axes. The compound header honestly describes the heterogeneous contents.

- **Peer cite:** ParaView's "Display" tab contains both representation toggles (Wireframe/Surface) and sampling-quality settings (max value for geometric error) in a single group — the same single-group-multiple-axes pattern. Source: ParaView User's Guide, "Display tab" section (ParaView.org docs; open source, BSD license).

**Tooltip text for the group box header (for implementer reference):**
No tooltip is needed on a `QGroupBox` header — group box headers are structural labels, not interactive elements that warrant tooltips. The existing per-button tooltips on the three buttons suffice.

---

## 8. Estimated Diff Size + Inline-vs-Delegated

### Files touched and estimated LOC changes

| File | Changed lines (est.) | Nature |
|------|---------------------|--------|
| `appearance_panel.py` | ~8–10 | Lines 155, 159, 173, 200–208 (comment rework + header rename) |
| `styles.py` | ~1 | Line 483: comment |
| `CONTEXT.md` | ~4 | Lines 147, 488: prose + parenthetical notes |
| `tests/test_styles_palette.py` | ~20–25 | Lines 842–869: function rename + docstring + 3 assertion strings + 1 new assertion |
| `tests/test_enriques_hq_smoothing.py` | ~1 | Line 355: docstring prose only |

**Total estimated diff: ~35–40 LOC changed**

### Inline-vs-delegated recommendation

**Inline.** This is a pure XS-effort rename (35–40 LOC, no logic change, no API surface change, no new tokens). The brief is fully specified (exact strings, exact file:line, exact test text). No sub-agent needed. Implementer can complete in a single focused pass.

---

## 9. References

| Source | Location | Key finding |
|--------|----------|-------------|
| `appearance_panel.py` | Line 208 | `QGroupBox("Render Mode")` — the single USER-VISIBLE string requiring rename |
| `appearance_panel.py` | Lines 155, 159, 173 | Inline comments referencing "Render Mode group" — update required |
| `appearance_panel.py` | Lines 199–207 | Comment block explaining prior peer-tool rationale for "Render Mode" — update to add new rationale |
| `appearance_panel.py` | Lines 152, 297, 321 | Other QGroupBox headers: `"Colors"`, `"Opacity"`, `"Shading"` — all single-word; "Display & Quality" is first compound header |
| `styles.py` | Line 483 | Comment: "Render Mode group below" — update to "Display & Quality group below" |
| `CONTEXT.md` | Line 147 | Prose: "Render Mode-group toggle" — update |
| `CONTEXT.md` | Line 488 | Prose: "Render Mode group (renamed from 'Display')" — update parenthetical |
| `tests/test_styles_palette.py` | Lines 842–869 | `test_appearance_panel_render_mode_group_header` — rename + update assertions |
| `tests/test_styles_palette.py` | Lines 864–869 | Negative guard `QGroupBox("Display") not in src` — KEEP; also ADD `QGroupBox("Render Mode") not in src` guard |
| `tests/test_enriques_hq_smoothing.py` | Line 355 | Docstring prose: "Render Mode group" — update to "Display & Quality group" |
| `.claude/notes/milestones/appearance-panel-layout-pass-2026q3-e2/artifacts/adversary-critique.md` | Lines 132–136 | F-M2 original finding: "Display & Quality" Path (a) named as V0-adequate single-group solution |
| `.claude/notes/milestones/hq-smoothing-label-rename-2026q3-e1/research/agent-solo-brief.md` | Lines 97–110, 163–176 | Precedent for DOC PROSE handling: update prose occurrences, preserve historical code-quote blocks, add parenthetical "renamed from X by milestone-id" |
| Qt QGroupBox docs | Qt 6 docs (QGroupBox.title) | `&` in title string creates keyboard accelerator; `&&` is the literal-ampersand escape — confirmed by Qt doc and standard Qt behavior |
| CONTEXT.md §4.3a | Line 147 | Confirms Wireframe/Show-edges are actor-display toggles; Double-pass smooth is a mesh-regeneration (quality) toggle — the semantic basis for "Display & Quality" |
