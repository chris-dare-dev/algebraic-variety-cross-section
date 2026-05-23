
## Lesson from restructure-full-audit-2026q2-r1 (2026-05-23)

### New axis worth adding
- **Intermediate-commit greenness is the most important bisect check for multi-op batches.** When a batch has N `git mv` commits followed by a LibCST import-rewrite commit, the intermediate mv commits will break any test that imports the moved module through an unrewritten importer (e.g., `app.py` still has old imports; a test that imports `from app import X` will fail with `ModuleNotFoundError`). Always check whether the test suite can survive each `git mv` commit independently BEFORE the LibCST rewrite lands. The safe pattern is either: (a) `git mv` + LibCST rewrite in the same commit, or (b) pre-write shims before any `git mv`.

### False-positive patterns to avoid
- **`validate-shims.py` FAIL on Template-2 `__getattr__` shims is always a false negative.** The script runs `import <module>` which does NOT trigger `__getattr__`; only attribute access does. Don't escalate this to CRITICAL or HIGH. The correct check is: do all 4 pytest shim tests pass? Do the manual smoke-tests (`from <old_mod> import <Symbol>`) emit DeprecationWarning? If yes to both, the shims are correct and the script is the problem.
- **`verify-anchors.py` reporting 400+ "stale" anchors after a move that includes `parameter_grid_panel` in a path is a known false positive.** The `parameter_grid_panel` needle matches `panels/parameter_grid_panel.py` (the correct new path). This is a substring match bug in the script. Don't elevate the 400+ count to a CRITICAL unless genuine stale paths remain in CLAUDE.md, AGENTS.md, CONTEXT.md, or README.md.

### AVC-specific post-execution gotchas
- **`pydeps` cycle check is structurally impossible for this repo** (directory name `algebraic-variety-cross-section` is not a valid Python identifier; pydeps rejects it). Rubric item 6 must be verified via `python -c "import app"` smoke-test instead.
- **`coverage xml` fails due to pyvistaqt internal path error** in this repo. Rubric items 4 and 5 cannot be mechanically checked until this is fixed. This is pre-existing, not introduced by any restructure.
- **PLAN "~9 total commits" is consistently an undercount for 4-batch restructures.** Actual commit counts are closer to 18–24 (source) + 4 (pipeline metadata). Calibrate user expectations accordingly.
- **stacklevel=2 in shims correctly points at the caller.** Verified by running the shim with `-W always` and checking the file:line in the warning output — it shows `<string>:N` (the calling code's line), not the shim's internal line.
