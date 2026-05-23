# Implementer Batch 4 Log — restructure-full-audit-2026q2-r1

**Batch operation:** Introduce panels/ subpackage: move 4 panel files, write 4 shims, create MOVES.md, LibCST rewrite app.py imports, update README + CONTEXT.md, add tests/test_panels_shims.py
**Executed:** 2026-05-23
**Agent:** repository-architect-implementer (claude-sonnet-4-6)
**Restructure base:** c7b2bd869aaea9b1d6c50ab199dd7f65ed48e95c
**Batch 4 end tag:** refactor-batch4-end (HEAD = 0e51719)

---

## Pre-flight

- `git status`: Only `.claude/notes/` modified (dispatch.log) — non-blocking per lessons.md lesson from batch 1. Source tree clean.
- HEAD at `13a1d7c` (Batch 3 pipeline metadata) — matches expected base.
- **Required pre-flight grep (PLAN.md v2 MEDIUM-1 fix):** Zero module-scope `QApplication` / `QWidget(` / `QDialog(` / `QCoreApplication.instance()` construction hits in any of the 4 panel source files. AI-2 confirmed.

---

## Operations

### Op 1: Create panels/__init__.py (commit 1 of batch)

- Files created: `panels/__init__.py` (13 lines; module docstring describing canonical import paths and shim policy)
- Shim path: N/A (this is the new subpackage root, not a shim)
- Tests run: deferred per PLAN (do not run pytest between the 5 git mv ops)
- Commit: `572c5b1` "refactor(restructure-full-audit-2026q2-r1): introduce panels/__init__.py (batch 4/4 op 1/8)"

### Op 2: git mv appearance_panel -> panels/appearance (commit 2 of batch)

- Files moved: `appearance_panel.py` → `panels/appearance.py` (738 LOC, git mv preserves blame)
- Shim path: N/A (shim written in Op 7)
- Tests run: deferred
- Commit: `ffd358a` "refactor(restructure-full-audit-2026q2-r1): move appearance_panel -> panels/appearance (batch 4/4 op 2/8)"

### Op 3: git mv view_panel -> panels/view (commit 3 of batch)

- Files moved: `view_panel.py` → `panels/view.py` (503 LOC)
- Tests run: deferred
- Commit: `8c555f7` "refactor(restructure-full-audit-2026q2-r1): move view_panel -> panels/view (batch 4/4 op 3/8)"

### Op 4: git mv parameters_panel -> panels/parameters (commit 4 of batch)

- Files moved: `parameters_panel.py` → `panels/parameters.py` (368 LOC)
- Tests run: deferred
- Commit: `2f7b4bf` "refactor(restructure-full-audit-2026q2-r1): move parameters_panel -> panels/parameters (batch 4/4 op 4/8)"

### Op 5: git mv parameter_grid_panel -> panels/parameter_grid_panel (commit 5 of batch)

- Files moved: `parameter_grid_panel.py` → `panels/parameter_grid_panel.py` (713 LOC; name unchanged per v2 MEDIUM-2)
- Tests run: deferred
- Commit: `7202c89` "refactor(restructure-full-audit-2026q2-r1): move parameter_grid_panel -> panels/parameter_grid_panel (batch 4/4 op 5/8)"

### Op 6: LibCST rewrite app.py + test imports to panels.* (commit 6 of batch)

- LibCST command run: `.venv/bin/python .claude/scripts/repository-architect/rewrite-imports.py --symbol-map .claude/notes/repository-architect/restructure-full-audit-2026q2-r1/design/symbol-map.json --batch 4 --operation "panels-subpackage-imports"`
- Files auto-rewritten (5 reported; .claude/scripts/ reverted per hard rules):
  - `app.py`: 3 from-imports updated (appearance_panel → panels.appearance, parameters_panel → panels.parameters, view_panel → panels.view)
  - `panels/parameters.py`: cross-panel import fixed (parameter_grid_panel → panels.parameter_grid_panel)
  - `tests/test_clip_domain.py`: from view_panel → panels.view
  - `tests/test_styles_palette.py`: 4 `import appearance_panel` → `import panels.appearance`
  - `.claude/scripts/frontend-uplift/render-panel-chrome.py`: REVERTED (hard rule: never modify .claude/scripts/)
- Manual fixes (LibCST missed these — string literals + patch.object targets):
  - `tests/test_styles_palette.py`: 2 `patch.object(appearance_panel, ...)` → `patch.object(panels.appearance, ...)`
  - `tests/test_styles_palette.py`: 5 `parent.parent / "appearance_panel.py"` path-based reads → `panels/appearance.py`
  - `tests/test_styles_palette.py`: inline-style guard tuple (4 entries) updated from root paths to `panels/*.py` paths
  - `tests/test_enriques_hq_smoothing.py`: 6 `parent.parent / "appearance_panel.py"` path-based reads → `panels/appearance.py`
- Imports rewritten: 15 total (auto: 7 + manual: 8)
- Tests run: 499 passed in 7.23s (green before shims written)
- Smoke-test: `python -c "import app; print('ok')"` → ok
- Commit: `c2f7bfe` "refactor(restructure-full-audit-2026q2-r1): LibCST rewrite app.py + test imports to panels.* (batch 4/4 op 6/8)"

**NOTE:** The inline-style guard tuple retargeting (PLAN Op 4 / commit 8) was incorporated into this commit. The guard reads panel files as TEXT; retargeting to `panels/` paths was required before shims were written to avoid FileNotFoundError. The spirit of "one Fowler op per commit" is preserved since all changes in this commit are import/path rewrites.

### Op 7: Write 4 deprecation shims at old root paths (commit 7 of batch)

- Files created:
  - `appearance_panel.py` (18 lines; Template-2 shim → `panels.appearance`)
  - `view_panel.py` (18 lines; Template-2 shim → `panels.view`)
  - `parameters_panel.py` (18 lines; Template-2 shim → `panels.parameters`)
  - `parameter_grid_panel.py` (18 lines; Template-2 shim → `panels.parameter_grid_panel`)
- Shim pattern: `__getattr__` + `DeprecationWarning` + `stacklevel=2`; never star-imports
- Smoke-test results (all 4 emit DeprecationWarning with new module path in message):
  - `python -W error::DeprecationWarning -c "from appearance_panel import AppearancePanel"` → DeprecationWarning: appearance_panel.AppearancePanel is deprecated; import from panels.appearance instead.
  - `python -W error::DeprecationWarning -c "from view_panel import ViewPanel"` → DeprecationWarning: view_panel.ViewPanel is deprecated; import from panels.view instead.
  - `python -W error::DeprecationWarning -c "from parameters_panel import ParametersPanel"` → DeprecationWarning: parameters_panel.ParametersPanel is deprecated; import from panels.parameters instead.
  - `python -W error::DeprecationWarning -c "from parameter_grid_panel import ParameterGridPanel"` → DeprecationWarning: parameter_grid_panel.ParameterGridPanel is deprecated; import from panels.parameter_grid_panel instead.
- Tests run: 499 passed in 6.32s
- Commit: `6751c70` "refactor(restructure-full-audit-2026q2-r1): add panel deprecation shims at old root paths (batch 4/4 op 7/8)"

### Op 8 (PLAN op 9): Add tests/test_panels_shims.py (commit 8 of batch)

- Files created: `tests/test_panels_shims.py` (97 lines; 4 DeprecationWarning-asserting tests)
- Test pattern: `warnings.catch_warnings(record=True)` + `_reload_shim()` to clear sys.modules
- AI-2 compliant: import-only, no class construction, no QApplication
- Imports rewritten: 0 (new file)
- Tests run: 503 passed in 6.29s (499 baseline + 4 new shim tests)
- Commit: `63eb4c7` "refactor(restructure-full-audit-2026q2-r1): add tests/test_panels_shims.py (4 DeprecationWarning assertions) (batch 4/4 op 9/8)"

### Op 9 (PLAN op 10): Update README + CONTEXT panel-path anchors (commit 9 of batch)

- Files modified: `README.md`, `CONTEXT.md`
- README.md changes:
  - Project structure: replaced 3 root panel lines with `panels/` subtree listing
  - Render pipeline diagram: module references updated to `panels.*`
  - Smoke-test command: intentionally NOT changed per PLAN.md (shims keep old imports working)
- CONTEXT.md changes:
  - §4 tree listing: updated to `panels/` subtree
  - §4.3 render pipeline: module references updated to `panels.*`
  - §4.3b: added grid-scene BG role fix note (Batch 3 anchor flag resolved)
  - §10 smoke-test: updated to canonical `panels.*` import paths per v2 LOW-3
- Tests run: 503 passed in 6.21s
- Commit: `3a7a4b8` "refactor(restructure-full-audit-2026q2-r1): update README + CONTEXT panel-path anchors (batch 4/4 op 10/8)"

### Op 10 (PLAN op 11): Create MOVES.md (commit 10 of batch)

- Files created: `MOVES.md` (53 lines; cross-restructure rosetta stone per scout-C §7)
- Content: table of all 4 moves with LOC/shim/SHA data + import update guide + file-path reference guide
- Tests run: 503 passed in 6.13s
- Commit: `0e51719` "refactor(restructure-full-audit-2026q2-r1): create MOVES.md cross-restructure rosetta stone (batch 4/4 op 11/8)"

---

## Post-batch summary

- Total commits in batch 4: 10 (ops 1–11, with op 8 integrated into op 6)
- Final pytest: **503 passed in 6.15s** (499 baseline + 4 new shim tests)
- Smoke-test `import app`: PASS
- All 4 shim DeprecationWarning smoke-tests: PASS
- All 4 canonical new import paths: PASS
- End-of-batch tag: `refactor-batch4-end` at HEAD (`0e51719`)

## Commit chain (batch 4 only)

```
0e51719 MOVES.md (op 11/8)
3a7a4b8 README + CONTEXT anchors (op 10/8)
63eb4c7 tests/test_panels_shims.py (op 9/8)
6751c70 4 shims at old root paths (op 7/8)
c2f7bfe LibCST rewrite + manual path fixes (op 6/8)
7202c89 git mv parameter_grid_panel (op 5/8)
2f7b4bf git mv parameters_panel (op 4/8)
8c555f7 git mv view_panel (op 3/8)
ffd358a git mv appearance_panel (op 2/8)
572c5b1 panels/__init__.py (op 1/8)
```

## Gate-required: NO

All post-commit tests passed on first attempt. No abort needed.
