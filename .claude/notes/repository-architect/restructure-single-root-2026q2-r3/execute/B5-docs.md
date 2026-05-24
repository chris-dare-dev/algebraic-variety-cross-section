# Anchor updater report — restructure-single-root-2026q2-r3 B5 docs pass

**Run at:** 2026-05-24T (local session)
**Verdict:** PASS

---

## Updates applied

- **MOVES.md**: appended r3 rosetta section (B1–B5, ~70 lines). Final SHA updated to cabf688 in a follow-up commit.
- **AGENTS.md** (= CLAUDE.md symlink target): "Where things live" section fully rewritten to reflect post-r3 single-root state. Removed: surfaces.py, parameter_grid.py, icons.py, styles.py, ui_helpers.py, render_worker.py, panels/ (all at root). Added: _qt/ tree, render/, cross_section/, varieties/ tree, pyproject.toml importlinter note, test count corrected 499→504. Build commands updated (stale `import surfaces`/`import styles` → canonical paths; added `lint-imports`). Code-style `styles.py` reference updated to `_qt/styles.py`.
- **README.md**: badge updated 499→504. Smoke-test import updated (`import app, surfaces; from panels.X` → `from varieties.registry import VARIETIES; from _qt.panels.X`). Project structure section rewritten (surfaces.py removed, full subpackage tree added). Running tests updated 499→504 and test coverage list updated. "Extending the app" step 6 legacy `from surfaces import X` path removed; backward-compat note replaced with "Post-r3 single-root state: surfaces.py has been retired."
- **CONTEXT.md**: "Last updated" bumped to 2026-05-24. §2 repo layout fully rewritten (single-root, subpackage tree, import-linter contracts sub-section added). §3 Numba side-effect note updated: `surfaces.py import` → `varieties/_kernels.py import`. §4.1 tooltip dict source updated: `surfaces.py` → `varieties/tooltips.py`. §4.5 domain clip: `panels/view.py` → `cross_section/clip.py`. §8.21 Numba threading paragraph updated. §10 verification commands updated (stale imports → canonical; test count 120→504; `lint-imports` added). §11 checklist steps 2+3 updated: `surfaces.py` → `varieties/tooltips.py`; `VARIETIES` → `varieties/registry.py`. §12 final state: test count 499→504; added single-root, import-linter, and VarietyGenerator bullets.
- **agent-memory CORRECTION blocks**: none required — stale references found were exclusively in `.claude/notes/repository-architect-design/` (historical design briefs, closed artifacts, not edited).

## MOVES.md diff (r3 section appended)

New section covers: r3 baseline SHA c1dcf89, r3 final SHA cabf688, B1 (tooling), B2 (parameter_grid.py → _qt/parameter_grid_math.py + VarietyGenerator Protocol), B3 (5 shim deletes), B4 (surfaces.py retirement, 23 import sites table), B5 (importlinter + smoke tests + docs). End-state confirmation: `ls *.py == app.py` only.

## Historical-stale references (acceptable, no edit)

- 25+ references inside `.claude/notes/repository-architect-design/scout-d-current-state.md` to `surfaces.py`, `parameter_grid.py`, etc. — this is the pre-r2 current-state audit brief (closed artifact, historical). Not edited.
- 1 reference in `.claude/notes/roadmaps/realtime-variety-render/spike-cand4-thread-safety.md` to `surfaces.py` (historical spike report). Not edited.

## .claude/notes / .claude/agent-memory grep results

```
grep -rn "parameter_grid\.py|surfaces\.py|/icons\.py|/styles\.py|/ui_helpers\.py|/render_worker\.py|panels/__init__\.py" .claude/notes/ .claude/agent-memory/ | grep -v "repository-architect/restructure-"
```

All hits are in:
- `.claude/notes/repository-architect-design/scout-d-current-state.md` — historical design brief (closed artifact)
- `.claude/notes/roadmaps/realtime-variety-render/spike-cand4-thread-safety.md` — historical spike report

No hits in `.claude/agent-memory/*/lessons.md` — no CORRECTION blocks needed.

## Final verification output

```
$ ls *.py | wc -l
1
$ ls *.py
app.py

$ .venv/bin/lint-imports
Analyzed 38 files, 103 dependencies.
varieties is pure-math (forbidden from importing app, _qt, panels, Qt) KEPT
cross_section is pure-pipeline (forbidden from Qt) KEPT
Contracts: 2 kept, 0 broken.

$ .venv/bin/python -m pytest -q 2>&1 | tail -3
504 passed in 6.85s

$ git tag -l 'refactor-r3-b*-end'
refactor-r3-b1-end
refactor-r3-b2-end
refactor-r3-b3-end
refactor-r3-b4-end
refactor-r3-b5-end
```

## Commit + tag

- Anchor docs commit: `cabf688` (`docs(restructure-single-root-2026q2-r3): anchor docs pass — single-root state (B5 docs 2/2)`)
- MOVES.md SHA finalization: `1419d03`
- Tag: `refactor-r3-b5-end` → cabf688
- Pushed: `origin/main` + `origin/refactor-r3-b5-end`

## Deviations

- CLAUDE.md is a symlink to AGENTS.md; edits applied directly to AGENTS.md (symlink resolution required).
- MOVES.md r3 final SHA required a second tiny commit (1419d03) to replace `<latest>` with the actual SHA after the main docs commit landed.
- `.claude/notes/repository-architect-design/` references not edited (historical artifacts per anchor-updater protocol).
