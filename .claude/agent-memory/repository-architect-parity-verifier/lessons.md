
## Lesson from restructure-full-audit-2026q2-r1 batch 1 (2026-05-23)
- False alarm pattern: star-import grep diff shows line ordering change between baseline and post — not a new import. Always sort both sides before diffing to confirm.
- Coverage tool quirk: pyvistaqt internal path issue ("No source for code: '<repo>/pyscript'") prevents `coverage xml` from completing in this repo. Treat coverage.xml absence as INFORMATIONAL/SKIPPED, not FAIL, per PREFLIGHT.md obs 2.
- Pydeps cycle classification: pydeps v3.0.6 cannot analyse repos with hyphens in the directory name. Both baseline and post produce identical empty-graph error. Not a regression — skip with INFORMATIONAL/SKIPPED, note in lessons, recommend `pydeps app` as fix for future batches.
- venv path quirk: this repo uses `.venv/bin/python` (macOS/Linux layout), NOT `.venv/Scripts/python.exe` (Windows layout). Agent prompt template uses Windows path — always check actual venv layout first.
- Import time variance: +6.6% observed between two measurements with zero Python source changes. Normal OS cache fluctuation. ±20% tolerance comfortably covers this.
