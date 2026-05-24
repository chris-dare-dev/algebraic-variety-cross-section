
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

---

## Lesson from restructure-feature-subpackages-2026q2-r2 (2026-05-23)

### New 2026 patterns observed

- **ETH Zurich study (arxiv 2602.11988v1) confirms context files add cost without proportional
  benefit.** LLM-generated files: -2-3% success, +23% cost. Human-curated: +4% success, +19%
  cost. Implication: AGENTS.md should be minimal (only what agents cannot discover from code).
  Per-subpackage CLAUDE.md should be under 20 lines or skipped entirely.
  Source: https://arxiv.org/html/2602.11988v1 (confirmed live 2026-05-23)

- **napari's `_qt/` isolation principle is now explicitly documented** in napari's architecture
  guide (not just implied by directory name). Direct quote: "we try to confine code that
  directly imports Qt to the folders `_qt/` and `_vispy/`." This is the strongest available
  citation for the `_qt/` subpackage pattern in Qt+VTK Python apps.
  Source: https://napari.org/dev/developers/architecture/dir_organization.html (live 2026-05-23)

- **Augment Code (2026) guidance says split AGENTS.md at 150-200 lines** (per-directory
  files). AVC's AGENTS.md at 148 lines is right at the split boundary.
  Source: https://www.augmentcode.com/guides/how-to-build-agents-md (live 2026-05-23)

- **"Flat package + feature subpackages" is the practiced pattern for scipy, pandas, django,
  pyvista** — all flat-at-root, domain-split inside. Not named in the literature as a distinct
  pattern (no canonical name found), but consistently practiced. No 2026 dissent found.

### Source changes since r1

- **napari architecture docs now explicitly state `_qt/` policy** (2026). Previously only
  implied. Use this as the primary citation for `_qt/` isolation in Qt+VTK apps.

- **ETH Zurich AGENTS.md study** is a new primary source that changes the per-subpackage
  CLAUDE.md recommendation from LOW to "only if genuinely non-obvious constraints exist."

### AVC-specific lessons (do not generalize)

- **r1 closed items 2, 3, 6, 7, 8, 21, 22, 25, 28** — evaluator score went from 14/28 to
  21/28 PASS. r2 targets items 17 (surfaces.py LOC) and 24 (framework adapter isolation).

- **The r2 evaluator report is at:**
  `.claude/notes/repository-architect/restructure-feature-subpackages-2026q2-r2/audit/evaluator-report.md`
  Result: 21/28 PASS.

- **panels/ is now at root as a working subpackage.** The 4 root-level shim files
  (appearance_panel.py, view_panel.py, parameters_panel.py, parameter_grid_panel.py) are 18
  LOC each and function via `__getattr__`. This counts as item #11 PASS but item #24 is still
  FAIL (icons.py, ui_helpers.py, styles.py remain at root with Qt coupling).

### Recommendation strength updates (r2)

- **napari `_qt/` pattern: confirmed HIGH** — now has explicit documentation, not just
  directory convention. Use the architecture docs URL as the citation.
- **Per-subpackage CLAUDE.md: downgraded from LOW to "avoid unless < 20 lines"** — ETH Zurich
  finding changes the calculus for single-developer projects.
- **varieties/ subpackage: confirmed HIGH** — surfaces.py at 1811 LOC is the primary r2 target;
  no dissent found on this decomposition approach.
- **AGENTS.md size cap: updated to 200 lines** (from 300) — Anthropic docs confirmed; ETH Zurich
  supports minimalism; AVC is currently at 148 lines (well-positioned).

---

## Lesson from restructure-single-root-2026q2-r3 (2026-05-24)

### New 2026 patterns observed

- **Protocol + frozen dataclass is now CONSENSUS for registry polymorphism.**
  Multiple 2025-2026 sources agree: use Protocol at the interface boundary,
  keep dataclasses for concrete entries, do NOT inherit from Protocol.
  The `VarietyGenerator` Protocol alongside `Surface` dataclass is the textbook
  application of this pattern.
  Sources: https://tiendu.github.io/2026/02/27/modern-python-oop-eng.html,
           https://mypy.readthedocs.io/en/stable/protocols.html

- **import-linter `forbidden` + `layers` dual-contract is the correct setup
  for a ~10-package Qt desktop app.** `layers` for direction; `forbidden` for
  external-package isolation. `include_external_packages = true` required for
  forbidden to catch PySide6.
  Source: https://import-linter.readthedocs.io/en/v2.7/contract_types.html

- **PyPA src-vs-flat page is silent on "app.py at root + subpackages" pattern.**
  This shape is practiced (Spyder uses bootstrap.py at root + flat spyder/)
  but is not named or explicitly endorsed. Not condemned either.
  Source: https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/

- **napari uses src/napari/ (proper src layout), NOT "app.py at root".**
  Spyder uses flat layout with bootstrap.py at root. AVC is closer to Spyder.
  Fetched via gh API 2026-05-24.

### AVC-specific lessons (do not generalize)

- **parameter_grid.py is ALREADY pure math** — confirmed by reading the file.
  It has no PySide6 or pyvista imports. Docstring explicitly says "Qt-free."
  The logical split (math vs widget) already exists: math in parameter_grid.py,
  widget in _qt/panels/parameter_grid_panel.py (or _qt/parameter_grid_panel.py).
  r3 rename to parameter_grid_math.py is cosmetic; the split is done.

- **r3 evaluator score is 23/28 PASS** (same as post-r2, since r3 changes are
  not yet applied). Open failures: #4 (CODE_OF_CONDUCT), #5 (CONTRIBUTING),
  #17 (app.py 1900 LOC), #19 (docs/), #20 (examples/) — none are r3 targets.

- **M+1 shim deletion is justified by NEP 29 minimum** ("at least one minor
  release") + Django's 1-cycle internal policy. PEP 387 does not govern
  internal intra-repo restructuring. Confirm no live internal callers before
  deleting shims.

- **import-linter `layers` contract should NOT include app.py.** app.py is a
  script, not a package; list only varieties, render, _qt, panels, cross_section
  in root_packages.

- **pyvista is a DOMAIN dependency for varieties/, not a framework adapter.**
  Do NOT put pyvista in the forbidden list for varieties/. Only Qt/PySide6 belongs
  in the forbidden list for varieties/ and render/.

### Recommendation strength updates (r3)

- **VarietyGenerator Protocol: NEW, HIGH** — consensus pattern, zero migration
  cost (existing generators satisfy it structurally), improves AI-navigability.
- **import-linter dual-contract (layers + forbidden): NEW, HIGH** — adds
  machine-readable architecture enforcement; < 20 lines of pyproject.toml config.
- **parameter_grid.py rename to _math: LOW** — cosmetic; split already exists;
  moving it INSIDE _qt/ would be misleading (file has no Qt).
- **M+1 shim deletion: confirmed HIGH** — NEP 29 + Django analog support it.
