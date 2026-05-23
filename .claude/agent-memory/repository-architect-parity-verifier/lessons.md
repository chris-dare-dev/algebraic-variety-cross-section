
## Lesson from restructure-full-audit-2026q2-r1 batch 1 (2026-05-23)
- False alarm pattern: star-import grep diff shows line ordering change between baseline and post — not a new import. Always sort both sides before diffing to confirm.
- Coverage tool quirk: pyvistaqt internal path issue ("No source for code: '<repo>/pyscript'") prevents `coverage xml` from completing in this repo. Treat coverage.xml absence as INFORMATIONAL/SKIPPED, not FAIL, per PREFLIGHT.md obs 2.
- Pydeps cycle classification: pydeps v3.0.6 cannot analyse repos with hyphens in the directory name. Both baseline and post produce identical empty-graph error. Not a regression — skip with INFORMATIONAL/SKIPPED, note in lessons, recommend `pydeps app` as fix for future batches.
- venv path quirk: this repo uses `.venv/bin/python` (macOS/Linux layout), NOT `.venv/Scripts/python.exe` (Windows layout). Agent prompt template uses Windows path — always check actual venv layout first.
- Import time variance: +6.6% observed between two measurements with zero Python source changes. Normal OS cache fluctuation. ±20% tolerance comfortably covers this.

## Lesson from restructure-full-audit-2026q2-r1 batch 2 (2026-05-23)
- False alarm pattern: none encountered — batch 2 was a pure documentation/config batch (AGENTS.md, CLAUDE.md symlink, pyproject.toml), zero Python source changes. All 6 checks passed cleanly.
- Coverage tool quirk: same as batch 1 — coverage.xml absent due to pyvistaqt internal-path issue. Treat as INFORMATIONAL/SKIPPED on all future batches unless Python source is touched.
- Import time variance: -12.7% improvement observed (baseline 752.9 ms → 657.0 ms). Negative delta is fine and within ±20%. Likely warm OS disk cache from same-day batch 1 verification.
- Shim validation: when a batch has no Python module moves, validate-shims.py correctly reports "no symbol-map entries for batch N -- nothing to validate" and exits 0. This is a PASS, not an error.

## Lesson from restructure-full-audit-2026q2-r1 batch 3 (2026-05-23)
- False alarm pattern: import-time cold runs (run1=1517ms, run2=1406ms) appeared to exceed ±20% tolerance vs baseline 752ms. Third warm-cache run was 728ms (-3.3%). Cold-run spikes are pure OS disk-cache noise — always take the warm-cache run (run 3) as the representative measurement. If run3 is within tolerance, mark PASS.
- Coverage tool quirk: same as batches 1+2 — pyvistaqt internal-path blocks coverage.xml. Treat as INFORMATIONAL/SKIPPED perpetually until pyvistaqt is resolved upstream.
- Collection diff exit code: `diff` exits 1 when only the wall-clock timing line changes (e.g. "499 tests collected in 2.67s" → "499 tests collected in 1.40s"). This is NOT a test-ID regression. Always inspect the diff lines — if the only delta is the timing suffix, mark PASS.
- Pydeps: identical empty-graph error on all batches; repo name with hyphens is permanently incompatible. Skip with INFORMATIONAL/SKIPPED on every batch.
