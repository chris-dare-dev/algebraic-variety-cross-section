
## Lesson from restructure-full-audit-2026q2-r1 (2026-05-23)
- Suggestion category most relevant for this restructure: #10 (cyclic-import smoke) + #3 (import-time side effects via shim identity)
- AVC-specific test gap pattern: the `__getattr__` shim pattern (Template-2) is AI-2-compliant because importing a QWidget subclass class object does not construct a QApplication — suggest identity tests alongside warning tests for all future shim batches
- Suggestion the user is likely to decline: category #6 (Qt event-loop integration) — AI-2 forbids pytest-qt, and AVC has no existing Qt integration tests; never propose Qt integration tests without explicitly noting the AI-2 lift requirement
- validate-shims.py tooling gap: `kind == "module"` entries use `import X` which never triggers `__getattr__`; the script gives a false PASS for all `__getattr__`-only shims. Note this in the report but do not propose a project test for it — it is an architect-tooling bug.
- The subprocess pattern for the cyclic-import smoke (Suggestion 1) is the right AI-2-compliant approach: test process is Qt-free, subprocess handles the Qt import. This mirrors how `test_qsettings_persistence.py` uses source-text-grep to stay AI-2-compliant.

## Lesson from restructure-single-root-2026q2-r3 (2026-05-24)
- Suggestion category most relevant for this restructure: #3 (Numba threading-layer side-effect assertion) + #5 (registry seam — more exposed after shim tests deleted in B3)
- AVC-specific test gap pattern: when a shim test file is deleted as part of M+1 cycle closure (r3 B3 deleted `test_r2_shims.py`), any seam coverage the shim test was providing becomes naked. Always check what the deleted test was implicitly covering before closing the shim cycle.
- Suggestion the user is likely to decline: Suggestion 5 (VarietyGenerator Protocol conformance as a standalone test) — it is fully subsumed by Suggestion 2 and the user will correctly note the overlap. Present it as "covered by Suggestion 2" rather than a separate deliverable.
- New r3-specific pattern: import-linter contracts in pyproject.toml are NOT run by pytest; the gap between "contract exists" and "contract is enforced in CI" is real. A thin subprocess wrapper (`test_import_linter_contracts.py`) closes this gap and is low-effort (S). This pattern will recur in any future restructure that adds import-linter contracts.
- The single-root invariant test (Suggestion 4, `test_single_root.py`) is the lowest-effort, highest-signal-to-noise test after a single-root restructure. Always propose it when the restructure's primary goal was a root .py count reduction.
