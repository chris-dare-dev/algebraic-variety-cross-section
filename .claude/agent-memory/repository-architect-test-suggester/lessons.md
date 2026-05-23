
## Lesson from restructure-full-audit-2026q2-r1 (2026-05-23)
- Suggestion category most relevant for this restructure: #10 (cyclic-import smoke) + #3 (import-time side effects via shim identity)
- AVC-specific test gap pattern: the `__getattr__` shim pattern (Template-2) is AI-2-compliant because importing a QWidget subclass class object does not construct a QApplication — suggest identity tests alongside warning tests for all future shim batches
- Suggestion the user is likely to decline: category #6 (Qt event-loop integration) — AI-2 forbids pytest-qt, and AVC has no existing Qt integration tests; never propose Qt integration tests without explicitly noting the AI-2 lift requirement
- validate-shims.py tooling gap: `kind == "module"` entries use `import X` which never triggers `__getattr__`; the script gives a false PASS for all `__getattr__`-only shims. Note this in the report but do not propose a project test for it — it is an architect-tooling bug.
- The subprocess pattern for the cyclic-import smoke (Suggestion 1) is the right AI-2-compliant approach: test process is Qt-free, subprocess handles the Qt import. This mirrors how `test_qsettings_persistence.py` uses source-text-grep to stay AI-2-compliant.
