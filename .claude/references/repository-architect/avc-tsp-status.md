# AVC-specific application of TSP-1..TSP-11

> Canonical AVC status against the Tree-Structure Principle framework defined in `.claude/commands/repository-architect.md`.  Read at Phase 1 (auditor), Phase 2 (design synthesis + design-adversary), and Phase 5 (execution-critic).  Cited by the orchestrator's `When to invoke` section.

## Current state snapshot (post-r3, 2026-05)

- Root: 1 `.py` file — `app.py` (~1900 LOC).
- Source subpackages: `_qt/`, `render/`, `cross_section/`, `varieties/`.
- Layer direction: enforced mechanically by import-linter (2 forbidden contracts in `pyproject.toml`).

## Status against the TSP framework

| Principle | Status | Notes |
|---|---|---|
| TSP-1 root thinness (count) | PASS | Only `app.py` at root |
| TSP-2 dependency order | PASS | import-linter contracts KEPT |
| TSP-3 cycles | PASS | `pydeps --show-cycles` empty |
| TSP-4 single-responsibility | FAIL | `app.py` exceeds the 500/800 LOC thresholds |
| TSP-5 responsibility names | PASS | No banlist hits |
| TSP-7 retention justifications | FAIL | `app.py` retained AS-IS across r1, r2, r3 with no named follow-up restructure-id |
| TSP-9 test mirroring | PASS | Flat-tests carve-out per AI-2 (see below) |
| TSP-11 entry-point pseudocode | FAIL | `app.py` is a monolith, not a pseudocode entry point |

## Carve-outs and load-bearing AVC rules

### AI-9 is NOT a retention reason

The `self._computing` re-entrancy guard is a constraint on WHERE the guard lives (with its semantic owner, `MainWindow`), not on what file path `MainWindow` is in.  The clean decomposition target is:

- `MainWindow` (and `_computing`) moves to `_qt/main_window.py`
- AI-9's invariant text in `.claude/references/app-invariants.md` is updated to reference the new location
- The guard's behavior is unchanged

Any PLAN.md for an `app.py` restructure MUST address AI-9 in section 6 (invariant impact) with this migration shape — citing AI-9 as a retention reason is anti-pattern R23.

### CLAUDE.md §2 "God Object" note is HISTORICAL

The note in repo-root `CLAUDE.md` §2 ("~1900 LOC — God Object, do not Extract Class here") reflects a pre-TSP framing that this pipeline now rejects.  The next restructure run targeting `app.py` MUST propose an anchor-updater edit to remove or invert that note.  Until then, treat the note as out-of-date; the TSP framework wins.

### AI-2 → TSP-9 flat-tests carve-out

AVC keeps `tests/` flat (504 Qt-free tests) per AI-2 — flat layout makes the "is this Qt-free?" check obvious at a glance and avoids `tests/_qt/...` confusion.  The TSP-9 carve-out applies to LAYOUT only: a new module added in a restructure batch MUST gain its corresponding `tests/test_<module>.py` IN THE SAME BATCH (the file lives in flat `tests/`, but it must exist).  Any moved test (when a module is renamed) moves WITH its source.

## `app.py` deferral chronology

`app.py` has been retained AS-IS across:
- r1 (panels extraction)
- r2 (Qt-layer shims retirement)
- r3 (surfaces.py retirement)

That deferral has expired.  Any future PLAN.md that retains `app.py` AS-IS must either (a) name a specific follow-up restructure-id that will decompose it, OR (b) absorb at least one decomposition batch in the current restructure (e.g. "batch 1: extract `MainWindow` + `_computing` guard into `_qt/main_window.py`").  Open-ended retention is anti-pattern R20.

## TSP-11-compliant `app.py` target shape

```python
# app.py — TSP-11-compliant target (~10-200 LOC, pseudocode-style)
from PySide6.QtWidgets import QApplication
from _qt.main_window import MainWindow   # MainWindow + AI-9 _computing guard live here

def main() -> int:
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())
```

Everything else — `MainWindow` class, panel construction, computation orchestration, AI-9 re-entrancy guard, formula evaluation, signal/slot wiring — lives in subpackages.

## See also

- `.claude/commands/repository-architect.md` — TSP-1..TSP-11 verbatim
- `.claude/references/repository-architect/anti-patterns.md` R20, R22, R23 — refusal patterns
- `.claude/references/app-invariants.md` AI-9 — the re-entrancy guard invariant text
- Repo-root `CLAUDE.md` §2 — the historical "God Object" note (slated for anchor-updater edit)
