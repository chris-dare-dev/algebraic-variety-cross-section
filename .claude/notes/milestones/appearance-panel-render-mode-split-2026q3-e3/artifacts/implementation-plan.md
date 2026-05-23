# Implementation plan — appearance-panel-render-mode-split-2026q3-e3

**Inline path. ~35 LOC across 5 files.** Close deferred F-M2 from `appearance-panel-layout-pass-2026q3-e2`. Path (a) per the original finding — single QGroupBox stays, header text only changes. Researcher caught the load-bearing Qt mnemonic detail: source literal MUST be `"Display && Quality"` (double `&`) to render as `Display & Quality` without activating Alt+Q.

1. **appearance_panel.py** —
   - Line 208: `QGroupBox("Render Mode")` → `QGroupBox("Display && Quality")`.
   - Lines 199–207: extend comment block — keep historical "Render Mode chosen by ..." rationale, append new "Display & Quality is more accurate because..." rationale with milestone-id citation.
   - Lines 155, 159, 173: update 4 inline comments referencing "Render Mode group" → "Display & Quality group".
   ~10 LOC delta.

2. **styles.py:483** — update 1 inline comment "Render Mode group" → "Display & Quality group".
   ~1 LOC delta.

3. **CONTEXT.md** —
   - §4.3a line 147: "Render Mode-group toggle" → "Display & Quality group toggle" + parenthetical `(renamed from "Render Mode" by appearance-panel-render-mode-split-2026q3-e3)`.
   - §8.16 line 488: extend the existing parenthetical to include this milestone's rename.
   ~4 LOC delta.

4. **tests/test_styles_palette.py:842–869** —
   - Rename function `test_appearance_panel_render_mode_group_header` → `test_appearance_panel_display_and_quality_group_header`.
   - Update docstring to reference new label + cite this milestone.
   - Replace positive assertion: `'QGroupBox("Render Mode")' in src` → `'QGroupBox("Display && Quality")' in src`.
   - **KEEP** existing negative: `'QGroupBox("Display")' not in src` (still guards against the older name).
   - **ADD** new negative: `'QGroupBox("Render Mode")' not in src` (guards against reverting to the immediately-prior name).
   - Update error message strings.
   ~25 LOC delta.

5. **tests/test_enriques_hq_smoothing.py:355** — update docstring prose only: "The Render Mode group's third button" → "The Display & Quality group's third button". No assertion change.
   ~1 LOC delta.

6. **Verify** —
   - `.venv/bin/pytest tests/ -q` reaches 385 + 0 = 385 (no new tests, one renamed test).
   - **No off-screen render verification needed** — pure header rename, no render path touched.

7. **Commit** — `feat(appearance-panel-render-mode-split-2026q3-e3): rename "Render Mode" group → "Display & Quality" (F-M2 closure)`.
