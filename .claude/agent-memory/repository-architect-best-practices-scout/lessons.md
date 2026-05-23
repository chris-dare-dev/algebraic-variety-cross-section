
## Lesson from restructure-full-audit-2026q2-r1 (2026-05-23)

### Source changes since seed brief

- **CLAUDE.md line count recommendation updated:** Anthropic's live Claude Code best practices
  page now says <200 lines (not <300 as the HumanLayer article states). Use 200 as the target
  when advising on CLAUDE.md size.
  Source: https://code.claude.com/docs/en/best-practices (confirmed live 2026-05-23)

- **napari, PyVista, Spyder still have NO AGENTS.md or CLAUDE.md** (all three return 404 via
  gh API, confirmed 2026-05-23). AVC can be ahead of its reference peers by adding one.

- **Real Python (2025) now recommends src layout for desktop apps** in addition to libraries
  (previously the consensus was "src for libraries only"). Reference:
  https://realpython.com/ref/best-practices/project-layout/

- **context7.json is NOT a broadly-adopted Python standard** — confirmed to be a PyVista-specific
  integration with the Context7 MCP service (upstash). Do not present it as an ecosystem pattern.

### New 2026 patterns observed

- **Datadog frontend guide (2026)** explicitly covers AGENTS.md in monorepos with per-directory
  precedence — good reference for the "nearest wins" claim.
  Source: https://dev.to/datadog-frontend-dev/steering-ai-agents-in-monorepos-with-agentsmd-13g0

- **agents.md GitHub Issue #53** confirms per-folder precedence behavior for AGENTS.md
  (nearest file wins). Useful to cite directly.

### AVC-specific lessons (do not generalize)

- **Import graph direction is already correct** in AVC: `surfaces.py` has no Qt imports,
  `render_worker.py` has no Qt imports, Qt code is confined to panel files + app.py. The
  subpackage split would make this structural rather than informal.

- **Numba JIT kernel import side effect** (`numba.config.THREADING_LAYER = "workqueue"` at module
  import time in surfaces.py) is a hard constraint on any surfaces.py split. Any refactor of
  surfaces.py must preserve this as a single process-global write that fires before any kernel
  is dispatched.

- **The dual parameter panel files are NOT duplicates.** `parameters_panel.py` is the container;
  `parameter_grid_panel.py` is the implementation it wraps. The relationship is an import, not
  duplication. Fix is naming clarity, not deletion.

- **Evaluator script output path:** the script writes to
  `.claude/notes/repository-architect/<ID>/audit/evaluator-report.md`. Run with:
  `python3 .claude/scripts/repository-architect/evaluate-checklist.py <ID>`

### Recommendation strength updates

- **AGENTS.md: HIGH → confirmed HIGH.** 60k+ repos, 20+ tools, Linux Foundation stewardship
  confirmed on agents.md home page (2026-05-23).
- **src/avcs/ migration: MEDIUM — unchanged.** Still contested for apps. Flat-package first
  remains the right recommendation for AVC's conservative-bias brief.
- **pyproject.toml: HIGH → confirmed HIGH.** PyPA canonical, required for peer review, no
  counter-argument.
