# Test-suggester suggestions — restructure-feature-subpackages-2026q2-r2

**Authored:** 2026-05-24 main session (inline)
**Status:** 3 suggestions across 3 scout-C §8 categories

Per the PLAN's §7 cross-suite test gaps analysis, r2 introduced gaps in categories 3 (import-time side effects), 5 (seam tests), and 10 (cyclic-import smoke). The 7 r2 shim tests added in B9 (`tests/test_r2_shims.py`) cover category 5 partially. Three additional suggestions worth considering for a follow-up `repository-architect-post-r2-test-hardening` milestone.

---

## Suggestion 1: Numba threading-layer side-effect smoke test (Category 3)

**Why:** B6's `varieties/_kernels.py` MUST set `numba.config.THREADING_LAYER = "workqueue"` at the TOP before `from numba import njit`. The shim re-export chain ensures this fires via `import surfaces`, but a future restructure could silently break this if someone moves the threading-layer line elsewhere in `_kernels.py`.

**Suggested test (Qt-free):**
```python
# tests/test_numba_threading_layer.py
def test_threading_layer_fires_before_njit_compile():
    """varieties._kernels must set THREADING_LAYER='workqueue' before any @njit compile."""
    import subprocess, sys
    # Subprocess for clean import-graph (no other test has polluted sys.modules).
    out = subprocess.run(
        [sys.executable, "-c",
         "import varieties._kernels; import numba; print(numba.config.THREADING_LAYER)"],
        capture_output=True, text=True, check=True,
    )
    assert out.stdout.strip() == "workqueue", out.stdout
```

**Effort:** S (~20 LOC, 1 test). AI-2 compliant (subprocess keeps the test process Qt-free).

---

## Suggestion 2: import-app cyclic-import smoke test (Category 10)

**Why:** r2 introduced 4 new subpackages and reshuffled the import graph. `import app` succeeds at HEAD, but a future restructure could introduce a cycle that pytest's `sys.modules` cache papers over. A subprocess-based smoke test would catch this.

**Suggested test:**
```python
# tests/test_import_app_smoke.py
def test_import_app_succeeds_in_fresh_subprocess():
    """python -c 'import app' must succeed (catches subtle cyclic imports)."""
    import subprocess, sys
    out = subprocess.run(
        [sys.executable, "-c", "import app; print('OK')"],
        capture_output=True, text=True, check=True,
    )
    assert out.stdout.strip() == "OK", out.stderr
```

**Effort:** S (~15 LOC, 1 test).

---

## Suggestion 3: varieties.registry consistency test (Category 5 — seam)

**Why:** B8 split VARIETIES out of surfaces.py into varieties/registry.py, which imports all 14 generators from 4 family modules + 14 PARAMS. A future refactor that renames a generator without updating registry.py would produce a runtime AttributeError but be silently green to the existing test suite.

**Suggested test:**
```python
# tests/test_varieties_registry_consistency.py
def test_every_variety_generator_is_callable():
    """Each Surface.generate in VARIETIES must be a real callable producing PolyData."""
    from varieties.registry import VARIETIES
    for variety, subtypes in VARIETIES.items():
        for subtype, surface in subtypes.items():
            assert callable(surface.generate), (
                f"VARIETIES[{variety!r}][{subtype!r}].generate is not callable"
            )
            mesh = surface.generate(**surface.defaults())
            assert mesh.n_points > 0, (
                f"VARIETIES[{variety!r}][{subtype!r}] produced empty mesh at defaults"
            )
```

**Effort:** M (~30 LOC, 1 test; would run all 14 generators — might be slow at ~5s).

---

## Not suggested (deliberately deferred per scout-C §10.1)

- Per-folder CLAUDE.md test (the per-folder CLAUDE.md was deferred in PLAN per ETH Zurich cost finding)
- Mutation tests on the new subpackages (overkill for first-run shim verification)
- pytest-qt integration tests (AI-2 blocks)

---

## Disposition

All 3 suggestions are DEFERRED to a follow-up `repository-architect-post-r2-test-hardening-2026q3-r3` milestone. They are not blocking for r2's "complete" state — the existing 506 tests + 7 r2-shim tests provide solid coverage of the shim mechanism. The seam test (Suggestion 3) is the highest-priority follow-up because it covers the AI-8-load-bearing VARIETIES registry consistency.
