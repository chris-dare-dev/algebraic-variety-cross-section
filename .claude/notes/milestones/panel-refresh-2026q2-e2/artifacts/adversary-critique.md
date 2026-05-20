# Adversary critique — palette tokenization (UPL-1)

**Reviewer:** milestone-adversary-critic (read-only) | **Date:** 2026-05-20 | **Subject:** panel-refresh-2026q2-e2 · dc328d7..be2b2b9

> **Format reference**: see `.claude/references/critique-format.md` for the
> canonical section structure, severity rubric (CRITICAL/HIGH/MEDIUM/LOW
> with examples), and the per-finding template format.

---

## Executive summary

One HIGH: the diff is 429 lines, exceeding the 400-LOC review-quality-at-risk threshold (non-waivable per checklist §2). One MEDIUM: `app.py:364` retains the raw `"#888888"` literal in the empty-clipped early-return branch while the structurally identical branch at `app.py:386` was correctly migrated — incomplete extraction, and no test catches it. A second MEDIUM flags that the regression-guard test (`test_app_stylesheet_substitutes_no_raw_hex_outside_palette`) only scans `APP_STYLESHEET`, leaving the `app.py` runtime call sites unguarded. Two LOWs cover a missing UPL-4 forward-compatibility comment and an unexported `BG_PANEL` token. No CRITICALs. Safe to merge after the MEDIUM at `app.py:364` is fixed; the HIGH is informational and does not block ship on its own.

---

## Critical findings (must-fix before this can ship)

None.

---

## High findings (should-fix this iteration)

### HIGH — Diff exceeds 400-LOC review-quality-at-risk threshold

**Where:** no specific file (cross-cutting)
**Evidence:** `git diff dc328d7..be2b2b9 | wc -l` returns 429 lines. The 400-LOC threshold is the Cisco / LinearB defect-detection inflection point cited in the adversary-critique checklist §2.
**Why it matters:** Diffs at this size have a documented higher miss rate for reviewers (human and automated). The orphaned literal at `app.py:364` is exactly the class of subtle same-file inconsistency that dense diffs obscure — the reviewer's eye moves from the correctly-migrated `app.py:386` without scanning the earlier branch.
**Suggested fix:** No code change required for this finding; it is informational. The implementer should note that future UPL milestones with similar all-files-touched scope should split into two commits (e.g., `styles.py` dict extraction + downstream call-site migration as a follow-up) to keep each diff reviewable.
**Regression-guard test:** Enforce a per-commit LOC cap in CI (e.g., `git diff HEAD~1 | wc -l` check in a pre-commit hook at 400 lines) if the team wants this to be machine-enforced rather than advisory.

---

## Medium findings (nice-to-fix)

### MEDIUM — Orphaned raw hex literal at app.py:364 — incomplete extraction

**Where:** `app.py:364`
**Evidence:** `color="#888888"` remains at line 364 (the empty-clipped early-return overlay branch). The structurally identical call at `app.py:386` was correctly migrated to `color=COLOR_WIREFRAME_OVERLAY`. The diff shows only the line-386 site was updated; the line-364 site was skipped.
**Why it matters:** The refactor's goal is that `grep -rE '#[0-9a-fA-F]{3,6}' app.py` returns zero matches outside comments. This literal defeats that acceptance criterion and means the domain-clip overlay rendered when the clipped mesh is empty uses a hard-coded color instead of the palette token — the two branches are now inconsistent. If a future palette swap (UPL-4 dark mode) updates `PALETTE_LIGHT["COLOR_WIREFRAME_OVERLAY"]`, the early-return branch will silently stay at `#888888`.
**Suggested fix:** Replace `color="#888888"` at `app.py:364` with `color=COLOR_WIREFRAME_OVERLAY` — identical to the line-386 fix already made. One-line change; `COLOR_WIREFRAME_OVERLAY` is already imported at `app.py:30`.
**Regression-guard test:** Add a test in `tests/test_styles_palette.py` (or a new `tests/test_no_raw_hex_in_callsites.py`) that opens `app.py` as text and asserts `re.search(r'color="#[0-9a-fA-F]{3,6}"', content) is None`. This complements the existing `test_app_stylesheet_substitutes_no_raw_hex_outside_palette` which only scans the rendered `APP_STYLESHEET` string, not runtime call sites in `app.py`.

### MEDIUM — Regression-guard test covers APP_STYLESHEET but not app.py call sites

**Where:** `tests/test_styles_palette.py:80`
**Evidence:** `test_app_stylesheet_substitutes_no_raw_hex_outside_palette` scans `styles.APP_STYLESHEET` for raw hex literals. It does not scan `app.py`, `appearance_panel.py`, or any other file for inline `color="..."` literals passed to PyVista. The orphaned `app.py:364` literal passes all 173 tests because no test looks at `app.py`'s source text.
**Why it matters:** The regression guard is the only automated backstop preventing future raw-hex drift in PyVista call sites (the highest-risk surface per AI-13). Its current scope covers only the QSS stylesheet — exactly the surface that is NOT the AI-13 risk — while leaving the PyVista color arguments unguarded.
**Suggested fix:** Extend `test_styles_palette.py` with a test that reads the source text of `app.py` and `appearance_panel.py` and asserts no `color="#..."` pattern matches a 3- or 6-digit hex literal. A targeted regex like `r'color\s*=\s*"#[0-9a-fA-F]{3,6}"'` is sufficient. Keep it in `test_styles_palette.py` (already the palette-discipline test file) to avoid a new module.

---

## Low findings (cosmetic / future iteration)

### LOW — Missing UPL-4 forward-compat comment above APP_STYLESHEET

**Where:** `styles.py:163`
**Evidence:** Agent B's research brief (§4.4) explicitly recommended adding a one-line comment above `APP_STYLESHEET`: `# UPL-4 will refactor this into _build_stylesheet(palette) — keep all hex references tokenized.` The comment is absent. The UPL-4 placeholder comment does appear at `styles.py:97–101` in the body of the file, but not immediately above the f-string where UPL-4's implementer will work.
**Why it matters:** The UPL-4 implementer will look directly at `APP_STYLESHEET` and may not notice the placeholder further up in the file. A proximate hint prevents a second migration pass where the implementer extracts the logic without knowing the intended refactor shape.
**Suggested fix:** Add a single comment line immediately above `APP_STYLESHEET = f"""` pointing to the UPL-4 planned refactor. No functional change.

### LOW — BG_PANEL in PALETTE_LIGHT but not exported as a named constant

**Where:** `styles.py:52` (dict), `styles.py:104–126` (named exports block)
**Evidence:** `BG_PANEL = "#f0f0f0"` is the WCAG anchor for all contrast-ratio calculations and is referenced by the research briefs as a required Tier-1 token. The named-exports block exports `BG_VIEWPORT`, `BG_SURFACE_DEFAULT`, `BORDER_SWATCH`, and `COLOR_WIREFRAME_OVERLAY` — but not `BG_PANEL`. The WCAG test in `test_critical_text_tokens_meet_wcag_aa_on_bg_panel` correctly reads it via `styles.PALETTE_LIGHT["BG_PANEL"]`, so there is no functional gap today.
**Why it matters:** When UPL-4 adds `PALETTE_DARK` and UPL-11 verifies contrast on the dark panel, authors will expect to import `BG_PANEL` the same way they import `BG_VIEWPORT`. Inconsistency in what is exported as a named constant is a minor discoverable-API smell.
**Suggested fix:** Add `BG_PANEL = PALETTE_LIGHT["BG_PANEL"]` to the named-exports block in `styles.py` alongside the other `BG_*` exports. One-line addition.

---

## What was done well

- **All 20 hex literals fully inventoried and migrated — except one.** The hex census in the research briefs (20 literals across 5 files) was executed faithfully. Fourteen of fifteen `styles.py` literals, all three `appearance_panel.py` literals, and one of two `app.py` literals were migrated. The single miss (app.py:364) is a scope-level oversight, not a design failure.

- **AI-13 compliance on all PALETTE_LIGHT values.** Every value in `PALETTE_LIGHT` is 6-digit hex; the `test_every_palette_value_is_six_digit_hex` test enforces this mechanically, so future contributors cannot accidentally add a 3-digit hex without a CI failure.

- **AI-13 adjacency fix (UPL-21) delivered correctly.** `appearance_panel.py:48` `#888` was expanded to `#888888` and routed through the `BORDER_SWATCH` token. This is the correct fix shape — the token is QSS-only and does not flow into PyVista, so no AI-13 runtime risk, but the 6-digit convention is enforced for consistency.

- **Backward-compat alias pattern is clean and verified.** The seven legacy named constants (`COLOR_MUTED`, `COLOR_VALUE`, etc.) are module-level variables that read from `PALETTE_LIGHT` at import time, with a regression test (`test_backward_compat_named_constants_match_palette`) that will catch any future dict-key rename that forgets to update the alias.

- **Tests are Qt-free (AI-2 compliant).** `test_styles_palette.py` imports only `re` and `styles` — no PySide6, no pyvistaqt. Confirmed: `styles.py` has no intra-app imports and no Qt imports at module level. The test runs in any pure-Python environment.

- **WCAG AA ratios documented inline and machine-verified.** The per-token WCAG comments (`~9.1:1`, `~5.4:1`, `~6.1:1`) are accompanied by a live contrast-ratio test (`test_critical_text_tokens_meet_wcag_aa_on_bg_panel`) that computes relative luminance per WCAG 2.x. This means the contract can never silently regress if a future token value is changed.

- **PyVista-bound token set is explicitly declared and tested.** `test_pyvista_bound_tokens_are_present` names the three tokens that flow into PyVista calls and fails if any is removed from the dict. This is the right guard shape for AI-13 — the test fails at import time, not at widget initialization.

- **UPL-4 and UPL-5 forward-compatibility stubs are present.** The `VARIETY_DEFAULT_COLOR: dict[str, str] = {}` stub and the `PALETTE_DARK` placeholder comment correctly scope out future work without polluting the current palette.

- **Zero call-site changes in view_panel.py and parameters_panel.py.** The alias pattern delivered the refactor's zero-disruption promise. Both files were confirmed to have no hex literals before the milestone (per research brief §2e, §2f), so no changes were needed and none were made.

- **APP_STYLESHEET comment updated to match the new invariant.** The comment above the f-string was updated from "Modern dock widget title bar styling..." to include "All hex values are substituted from PALETTE_LIGHT — no raw literals here." This is the right form of in-code documentation: the invariant is stated where the maintainer will read it.

---


## Cross-critic agreement

The following findings cluster within 5 lines of each other in the same file. Multiple critics flagged the same area -- these are the strongest signals to fix first.

- **M1, H1** at `app.py:364-364` (MEDIUM): Orphaned raw hex literal at app.py:364 — incomplete extraction; Residual raw `"#888888"` in empty-clip branch bypasses `COLOR_WIREFRAME_OVERLAY` token
- **L2, L3** at `styles.py:52-52` (LOW): BG_PANEL in PALETTE_LIGHT but not exported as a named constant; `BG_PANEL` token is present in `PALETTE_LIGHT` but has no named export and no QSS usage

## Recommended rectification order

1. **Fix the orphaned `app.py:364` literal (MEDIUM M1).** Replace `color="#888888"` with `color=COLOR_WIREFRAME_OVERLAY`. One-line change; `COLOR_WIREFRAME_OVERLAY` is already imported. Verify with `grep -n '888' app.py` returning zero matches outside comments.

2. **Extend the regression-guard test to cover app.py call sites (MEDIUM M2).** Add a test in `tests/test_styles_palette.py` that reads `app.py` source text and asserts `re.search(r'color\s*=\s*"#[0-9a-fA-F]{3,6}"', content) is None`. This closes the guard gap that allowed M1 to slip through.

3. **Add `BG_PANEL` named export (LOW L2).** Single-line addition to the named-exports block. Do alongside M1/M2 since the file is already open.

4. **Add the UPL-4 forward-compat comment above APP_STYLESHEET (LOW L1).** One comment line. Optional but prevents the next implementer from missing the planned refactor shape.

5. **HIGH H1 (diff size) is advisory only** — no code change required. Record in the milestone retrospective.

---

*End of critique. Mandatory rectification: M1 (orphaned literal) and M2 (test gap). H1 is non-waivable in the critique record but requires no source change. L1 and L2 are optional follow-ups.*

---

## Frontend UI/UX findings (from milestone-frontend-ux-critic)

## HIGH findings

### HIGH — Residual raw `"#888888"` in empty-clip branch bypasses `COLOR_WIREFRAME_OVERLAY` token

**Where:** `app.py:364`
**Evidence:** The diff correctly replaces the wireframe color in the normal-render path (line 386: `color=COLOR_WIREFRAME_OVERLAY`). The empty-clip branch at line 361-369 handles the case where `clipped.n_points == 0` and still shows the domain outline. This branch was not updated: it retains `color="#888888"` as a raw string literal flowing directly into `plotter.add_mesh(color=...)`. The imported `COLOR_WIREFRAME_OVERLAY` token is not used here. Both paths render the same wireframe overlay actor but only one uses the token, creating a two-source-of-truth situation for the same visual element. If UPL-4 swaps `PALETTE_LIGHT["COLOR_WIREFRAME_OVERLAY"]` to a lighter value for dark mode, the empty-clip path will show the wrong color.
**Why it matters:** The entire purpose of UPL-1 is to make `PALETTE_LIGHT` the exhaustive single source of truth so that UPL-4 dark mode swap works by editing only `styles.py`. A surviving inline literal in a PyVista-bound call site breaks that contract. It is also an AI-13 adjacency issue: `#888888` is a 6-digit hex (technically compliant), but its presence as a raw string outside the palette undermines the token discipline.
**Suggested fix:** Replace `color="#888888"` at `app.py:364` with `color=COLOR_WIREFRAME_OVERLAY` — identical to the fix already applied at `app.py:386`.

---

## MEDIUM findings

### MEDIUM — Two palette comment contrast ratios are inaccurate

**Where:** `styles.py:57, 60`
**Evidence:** The palette comments annotate:
- `TEXT_MUTED` (`#5a5a5a`): "~5.4:1 on BG_PANEL" — measured value is **6.05:1**
- `TEXT_RESET_BTN` (`#5a3a3a` on `#f5e8e8`): "~6.1:1" — measured value is **8.37:1**

These are not rounding errors; they are off by 12% and 37% respectively. The comments were inherited from a prior pass and not re-verified against the new 6-digit palette entries. For `TEXT_RESET_BTN` the discrepancy is large enough that a UPL-4 author choosing a dark-mode equivalent guided by "~6.1:1" would select a color with significant headroom to spare.
**Why it matters:** The palette doc comments are the primary guidance for UPL-4 (dark mode). Incorrect contrast ratios cause future authors to calibrate dark-surface text colors against wrong baseline numbers, potentially producing tokens that "look similar to the 6.1 ratio" but actually fail WCAG AA.
**Suggested fix:** Re-run the WCAG luminance formula (already in `test_styles_palette.py`) for every annotated text token and update comment figures. Accept ~1% tolerance for the "~" prefix.

### MEDIUM — `FOCUS_RING` palette comment claims ">= 3:1 vs adjacent widget bg" but actual ratio is 2.60:1

**Where:** `styles.py:63`
**Evidence:** `PALETTE_LIGHT["FOCUS_RING"]` = `#5b9bd5`. Against `BG_PANEL` (`#f0f0f0`), measured contrast ratio is **2.60:1**, below the WCAG AA 3:1 threshold for non-text UI components (focus indicators). The comment reads: "keyboard focus outline (>=3:1 vs adjacent widget bg)" — this is aspirational, not empirical.
**Why it matters:** This token is now in the documented palette with an incorrect specification. WCAG 2.1 Success Criterion 1.4.11 (Non-text Contrast) requires 3:1 for focus indicators. Any accessibility audit will flag this. Now that UPL-1 has made the palette the single source of truth, the annotation is the spec; it needs to be accurate. Note: this token pre-existed the diff, so this is not a regression introduced by UPL-1, but its inclusion in `PALETTE_LIGHT` with a false claim is a UPL-1 artifact.
**Suggested fix:** Either (a) darken `FOCUS_RING` to achieve 3:1 (e.g., `#3c82c4` gives ~3.1:1 on `#f0f0f0`) and update the comment, or (b) update the comment to reflect the measured ratio and file a separate UPL issue for the WCAG fix. Option (a) is a one-line palette change; option (b) keeps UPL-1 surface-minimal and flags it for UPL-4's accessibility pass.

### MEDIUM — `PALETTE_LIGHT` lacks a token for `QSS` status-bar text color; `APP_STYLESHEET` references `COLOR_MUTED` (an alias), not the palette key directly

**Where:** `styles.py:232-234` (status bar QSS rule)
**Evidence:** The `APP_STYLESHEET` status-bar rule uses `{COLOR_MUTED}` (the backward-compat alias). Every other QSS rule in the updated stylesheet was migrated to use `PALETTE_LIGHT[...]` subscripts directly. The status bar rule was not. This is inconsistent with the "no raw literals in APP_STYLESHEET" invariant the test `test_app_stylesheet_substitutes_no_raw_hex_outside_palette` guards. The test passes because `COLOR_MUTED == PALETTE_LIGHT["TEXT_MUTED"]` — the value is the same — but the authoring pattern is inconsistent.
**Why it matters:** In UPL-4, if dark mode requires `TEXT_MUTED_DARK` for the status bar specifically, the author must remember to patch this rule separately because it references the alias rather than a key lookup. The other rules read `PALETTE_LIGHT["KEY"]` and will be trivially found by a sed/grep sweep. This one requires reading the backward-compat section too.
**Suggested fix:** Replace `{COLOR_MUTED}` with `{PALETTE_LIGHT["TEXT_MUTED"]}` in the status bar QSS rule to make all QSS palette references stylistically uniform.

---

## LOW findings

### LOW — `VARIETY_DEFAULT_COLOR` stub docstring lists a non-matching key for Calabi-Yau 3-fold

**Where:** `styles.py:90-94`
**Evidence:** The `VARIETY_DEFAULT_COLOR` docstring example comment lists `"Calabi-Yau 3-fold"` (ASCII hyphen) as a sample key, but `surfaces.py`'s `VARIETIES` dict uses `"Calabi–3-fold"` (Unicode en-dash, U+2013). If UPL-5 follows the stub comment verbatim, the dict lookup will silently miss and the per-variety default will not apply.
**Why it matters:** Low impact now (the dict is empty), but the wrong key in the comment seeds a copy-paste bug in UPL-5.
**Suggested fix:** Update the comment to use the en-dash form `"Calabi–3-fold"` or note that keys must match `VARIETIES` dict verbatim.

### LOW — `BG_PANEL` token is present in `PALETTE_LIGHT` but has no named export and no QSS usage

**Where:** `styles.py:52`
**Evidence:** `PALETTE_LIGHT["BG_PANEL"]` (`#f0f0f0`) is the WCAG contrast anchor documented in all text-token comments, and is referenced by the test suite. However it is not exported as a named constant and does not appear in `APP_STYLESHEET`. It is the implicit panel ground color Qt inherits from the OS theme — but it is not set explicitly anywhere in the app. If Qt's default changes on a future platform, the token will diverge from reality without any test catching it.
**Why it matters:** Cosmetically low risk on today's Qt default, but when UPL-4 adds an explicit dark-panel background, the symmetric light-panel token should also be wired (or documented as "OS-provided, not set explicitly").
**Suggested fix:** Add a brief comment to the `BG_PANEL` entry: "Qt platform default — not set explicitly by the app; update if a future Qt platform skin changes this." No code change required.

---

## What was done well

- **Exhaustive 6-digit hex discipline (AI-13):** Every value in `PALETTE_LIGHT` is 6-digit hex. The test `test_every_palette_value_is_six_digit_hex` is a strong regression guard. The `BORDER_SWATCH` fix (`#888` → `#888888` in `_apply_swatch_color`) is applied correctly at `appearance_panel.py:53`.
- **Backward-compat exports are live aliases, not copies:** The pattern `COLOR_MUTED = PALETTE_LIGHT["TEXT_MUTED"]` (and all analogous exports) ensures that changing the palette dict automatically propagates to all existing call sites. The test suite verifies this at import time.
- **UPL-4 readiness of key vocabulary:** The token names (`BG_VIEWPORT`, `BG_PANEL`, `BG_SURFACE_DEFAULT`, `TEXT_MUTED`, `TEXT_VALUE`, `TEXT_DISABLED`, `FOCUS_RING`) are semantically role-based rather than value-based, which is exactly the vocabulary a dark-mode swap needs. Adding `PALETTE_DARK` with identical keys will be a clean parallel addition.
- **PyVista-bound token annotation:** `BG_VIEWPORT`, `BG_SURFACE_DEFAULT`, and `COLOR_WIREFRAME_OVERLAY` are explicitly flagged "flows into PyVista" in the palette comments. This is the correct way to document the AI-13 risk surface for future contributors.
- **Zero regression in rendered colors or dock sizes:** The pre- and post-refactor color values for every token match the prior inline literals (`#b0c4de`, `#2f2f2f`, `#888888`, `#5a5a5a`, `#333333`, `#e8edf2`, `#c5cdd8`, `#f5e8e8`, `#d4b4b4`, `#f0d0d0`). The off-screen render at `/tmp/check-e2-palette.png` confirms `BG_VIEWPORT` and `BG_SURFACE_DEFAULT` are preserved.
- **First-launch behavior preserved (CONTEXT.md §9.3):** The refactor touches no render-trigger paths. `MainWindow.__init__` still opens to the `-- Select --` placeholder. No auto-render was introduced.
- **No AI-9, AI-10, AI-11 regressions:** No new `processEvents()` calls. No mesh regeneration on domain changes. No shorthand Qt enum forms (`Qt.AlignLeft` etc.) appear in the changed files.
- **Keyboard shortcuts (`Ctrl+R`, `Ctrl+Shift+S`, `Ctrl+D`) untouched:** The refactor is stylesheet-only; no action wiring was changed.

---

## Recommended rectification order

1. **(HIGH — must fix before UPL-4)** `app.py:364`: replace `color="#888888"` with `color=COLOR_WIREFRAME_OVERLAY`. One-line fix; eliminates the only remaining PyVista-bound inline literal.
2. **(MEDIUM)** `styles.py:57,60`: update palette comment contrast ratios to measured values (`6.05:1` for `TEXT_MUTED`, `8.37:1` for `TEXT_RESET_BTN`).
3. **(MEDIUM)** `styles.py:63`: either darken `FOCUS_RING` to achieve 3:1 or correct the comment. Flag as a UPL-4 candidate if color change is deferred.
4. **(MEDIUM)** `styles.py:232-234`: replace `{COLOR_MUTED}` alias reference in status-bar QSS with `{PALETTE_LIGHT["TEXT_MUTED"]}` for authoring consistency.
5. **(LOW)** `styles.py:92`: correct `"Calabi-Yau 3-fold"` to `"Calabi–3-fold"` in the `VARIETY_DEFAULT_COLOR` docstring comment.
6. **(LOW)** `styles.py:52`: add "OS-provided, not set explicitly" note to `BG_PANEL` comment.

---

## Rectification status (Phase 4 footer)

**Rectification commit:** `cf8d2ef`
**Outer-loop iterations:** 1 (well within cap of 3)
**Tests:** 175/175 pass post-fix
**Date:** 2026-05-20

**Fixed:** M1, M2, M3, M5, L1, L2, L3, L4 (8 findings)
**Deferred:** M4 (FOCUS_RING contrast — flagged to UPL-4 accessibility pass; out of UPL-1 scope per "preserve every existing rendered color" acceptance signal)
**Invalidated:** H1 (diff-size advisory — informational only per critic's own annotation; no source change required)
