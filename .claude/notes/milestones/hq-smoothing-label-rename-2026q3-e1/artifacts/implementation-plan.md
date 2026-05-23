# Implementation plan — hq-smoothing-label-rename-2026q3-e1

**Inline path. ~25 LOC across 4 files.** Close F-L1 from `enriques-hq-smoothing-2026q3-e1` (deferred). Researcher recommended (a) `"Double-pass smooth"` button label, (b) `" [Double-pass]"` status-bar suffix, (c) keep all internal symbol names.

1. **appearance_panel.py:265** — `QPushButton("HQ smoothing")` → `QPushButton("Double-pass smooth")`.
   - Update tooltip first phrase (`appearance_panel.py:269–279`) to add "— two passes total —" bridge per brief §4.
   - Internal comments referencing "HQ smoothing" / "HQ-smoothing" STAY (they describe symbol names, not user-visible text).
   ~3 LOC delta.

2. **app.py** —
   - `app.py:660` `_hq_label = " [HQ]" if _is_hq_active else ""` → `" [Double-pass]"`.
   - `app.py:795–797` comment example "Enriques surface [HQ] · …" → "Enriques surface [Double-pass] · …".
   - Update comment at app.py:653–657 if it references "[HQ]".
   - Variable name `_hq_label` STAYS (internal).
   ~3 LOC delta.

3. **tests/test_enriques_hq_smoothing.py** —
   - Update existing assertions at lines 172, 179, 326–327 from "HQ smoothing" string to "Double-pass smooth".
   - Add 4 new tests per brief §5:
     - `test_appearance_panel_uses_double_pass_smooth_label` (positive, button)
     - `test_appearance_panel_does_not_use_old_hq_smoothing_label` (negative regression, button)
     - `test_app_status_bar_uses_double_pass_suffix` (positive, status bar)
     - `test_app_status_bar_does_not_use_old_hq_suffix` (negative regression, status bar)
   ~30 LOC delta.

4. **CONTEXT.md** —
   - §4.3a — replace `"HQ smoothing"` prose label references with `"Double-pass smooth"`; preserve internal symbol names (`hq_smoothing_changed = Signal(bool)` etc.) verbatim.
   - §8.16 — append rename note: "Relabeled to 'Double-pass smooth' by hq-smoothing-label-rename-2026q3-e1 (F-L1 closure)."
   ~4 LOC delta.

5. **Verify** —
   - `.venv/bin/pytest tests/ -q` reaches 380 + 4 = 384.
   - **No off-screen render verification needed** — pure label rename, no render path touched.

6. **Commit** — `feat(hq-smoothing-label-rename-2026q3-e1): rename "HQ smoothing" → "Double-pass smooth" (F-L1 closure)`.
