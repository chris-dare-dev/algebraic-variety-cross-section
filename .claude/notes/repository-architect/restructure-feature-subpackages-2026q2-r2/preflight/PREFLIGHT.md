# PREFLIGHT.md — restructure-feature-subpackages-2026q2-r2

**Phase 3 wall-clock:** ~13 min (baseline snapshot 2 min + dry-run-validator 10 min + rollback rehearsal + 1 fix-cycle)
**Verdict:** GREEN (originally YELLOW; the single broken-imports finding was a real bug in PLAN.md symbol-map and was fixed inline)

## Baseline (pre-restructure)

| Signal | Value |
|---|---|
| Git SHA | `2bfc6c8038d57b931f6d4128fb03cd2bb9130645` (tag: `refactor-baseline-restructure-feature-subpackages-2026q2-r2`) |
| Tests collected | 503 (Phase 4 will: B1 -4 + B9 +5 = +1 net; final 504 expected) |
| Tests passing | 503 in 1.36s |
| Symbols indexed | 523 top-level def/class |
| Star-imports | 3 (pre-existing; none in AVC source) |
| coverage.xml | ⚠️ NOT generated (pyvistaqt internal `pyscript` path — same issue as r1 Phase 3) |
| importtime | captured |

## Dry-run validator results (after fix)

Verdict: **GREEN** (originally YELLOW; 1 finding fixed inline before advancing).

| # | Category | Result |
|---|---|---|
| 1 | New cycles | **0** (hub shim one-hop; no `_qt.panels.*` reimports from `panels.*`; no `varieties` ↔ `surfaces` mutual import) |
| 2 | Orphans | **0** (every new module has a clear incoming import path) |
| 3 | Broken imports | **0** after fano_segre fix (was 3 before) |
| 4 | conftest scope drift | **0** (AVC has no conftest.py) |
| 5 | Predicted collection delta | **+1** (B1 -4 panel-shim tests, B9 +5 r2-shim tests) |
| 6 | Star-import shadow | **0** (PLAN refuses Template 3; `_PRIVATE_NAMES` used for underscore symbols) |
| 7 | Fan-in spikes | **0** (highest predicted fan-in ~16, same as pre-restructure surfaces) |

### Bug caught + fixed inline

Dry-run validator caught **3 broken imports** that would have caused AttributeError at runtime in tests test_coarse_n.py, test_mesh_generators.py, test_parameters_panel.py:

- symbol-map had `"fano_segre"` and `"FANO_SEGRE_PARAMS"`
- Actual surfaces.py defines `fano_segre_cubic` (L1371) and `FANO_SEGRE_CUBIC_PARAMS` (L1411)
- Fixed: 2 symbol-map.json entries corrected; PLAN.md §3 table corrected

**This is the THIRD save** the design phase has produced for r2 (HIGH-1 panels imports, HIGH-2 FAST_RENDER_THRESHOLD_MS in adversary v2; this fano_segre in dry-run v3). The 12-axis adversary + dry-run validator combination is doing the work it's meant to do.

## Non-blocking observations baked into Phase 4

- **Threading-layer side effect timing:** `varieties/__init__.py` does `import varieties._kernels` eagerly (v2 LOW-2 fix). The shim path to `VARIETIES` does NOT eagerly trigger _kernels — but B9 test_r2_shims.py covers the shim path explicitly. The pre-state import-time is captured for Phase 4 parity check.
- **rewrite-imports.py last-wins quirk:** the dry-run validator noted a latent bug in our rewrite-imports.py (when multiple symbol-map entries share the same `from` module, last-wins). r2's 52 symbol-kind entries from `surfaces` all share `from=surfaces` — but they have DIFFERENT `symbol` fields so the bug doesn't trigger. Worth fixing in a future tooling milestone.
- **Coverage XML still missing** (pre-existing pyvistaqt issue) — per-file coverage parity check degrades to informational.

## Rollback rehearsal

**TESTED:** `git worktree add /tmp/avc-r2-rollback-test refactor-baseline-restructure-feature-subpackages-2026q2-r2` succeeded with HEAD at `2bfc6c8...` (matches baseline SHA). Worktree removed cleanly. The Tier 1 baseline tag is valid.

## Pipeline state at Phase 3 end

- `restructure_base = 2bfc6c8038d57b931f6d4128fb03cd2bb9130645`
- `baseline_dir = .claude/notes/repository-architect/restructure-feature-subpackages-2026q2-r2/preflight/`
- Tag created + verified: `refactor-baseline-restructure-feature-subpackages-2026q2-r2`
- `dry_run_verdict = GREEN` (post fano_segre fix)
- Ready to advance to `preflight-complete` and surface GATE 3.
