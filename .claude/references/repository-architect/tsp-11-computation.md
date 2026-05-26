# TSP-11 entry-point pseudocode — AST computation methodology

> **Correctness contract:** the pre-state TSP scorecard (produced by `repository-architect-current-state-auditor` in Phase 1) and the post-state TSP scorecard (produced by `repository-architect-execution-critic` in Phase 5) MUST use the IDENTICAL methodology below.  A diff between two scorecards that used different methodology is meaningless.  Both agents read this file at dispatch time.

## What TSP-11 grades

For EACH root-level `.py` entry point (currently AVC has one: `app.py`), produce this row:

| Entry point | LOC | Statements | Call-statements | Density % | Business-logic patterns found | Verdict |
|---|---|---|---|---|---|---|
| `<path>` | <L> | <S> | <C> | <C/S × 100> | <comma-separated list, or "none"> | PASS / FAIL |

**PASS criteria** (all three must hold):
- Density % ≥ **70**
- Business-logic patterns list is empty
- LOC ≤ **500** (alarm threshold; ≤200 is the advisory target)

Any FAIL → TSP-11 FAIL for that entry point.

## AST methodology — Statements (denominator)

Use Python's `ast` module via the Bash tool.  Parse the file; count the number of `ast.stmt` nodes that are:

**INCLUDED** (counted in the denominator):
- All statements in the module body (top-level)
- All statements recursively inside top-level function bodies

**EXCLUDED** (NOT counted):
- `ast.Import` and `ast.ImportFrom` (imports)
- Top-level string `ast.Expr` at module or function start (docstrings)
- `ast.Pass`

## AST methodology — Call-statements (numerator)

Count the number of statements whose value contains a top-level `ast.Call` expression:

- `factory(...)` (bare call as `ast.Expr` wrapping `ast.Call`)
- `result = factory(...)` (assignment whose value is `ast.Call`)
- `return factory(...)` (return whose value is `ast.Call`)
- `raise SomeError(...)` (raise whose exc is `ast.Call`)
- `yield factory(...)` (yield whose value is `ast.Call`)

Loops, conditionals, and assignments to literals are NOT call-statements.  Method chains (`a.b().c()`) count as one call-statement.

## Business-logic patterns (any hit = FAIL)

AST-inspect for the following patterns.  Hit ANY → record in the "Business-logic patterns found" column:

| Pattern | AST signal |
|---|---|
| Formula evaluation / math kernels | Arithmetic ops (`ast.BinOp`, `ast.UnaryOp`) on numeric literals beyond CLI-default sentinels (e.g. `argparse` `default=0`); imports of `numpy`/`numba`/`math` used in expressions |
| Panel/widget construction | `setStyleSheet(...)` calls; `QSS` string construction; `QWidget`/`QLabel`/`QPushButton`/`QVBoxLayout`/`QHBoxLayout` instantiation |
| Qt signal/slot wiring | `.connect(...)` / `.disconnect(...)` calls on signal attributes; non-trivial `Qt.Signal` declarations |
| Qt enum handling | Non-trivial expressions involving `Qt.AlignmentFlag`, `Qt.Key`, etc. (more than a single attribute access in a call argument) |
| Parsing | `re.compile`, `json.loads`, `yaml.safe_load`, `ast.literal_eval`, `urllib.parse.*` |
| File I/O | `open(...)`, `Path(...).read_text/write_text/read_bytes/write_bytes`, `os.path.*` walks |
| Validation loops | For-loops or while-loops containing `raise` on a condition |

**Allowed at root** (these do NOT count as business-logic patterns):
- `argparse.ArgumentParser` construction + `parse_args()` — that's CLI dispatch, not business logic
- `QApplication.instance()` / `QApplication([])` / `app.exec()` / `sys.exit(...)` — that's Qt app lifecycle
- A single class-construction call (e.g. `MainWindow()`) — the class itself lives in a subpackage
- `if __name__ == "__main__":` guard

## LOC computation

Total `.py` lines including blank/comment/docstring (i.e. `wc -l <path>`).  No filtering — the LOC budget is about whole-file scannability.

- ≤ 200: target
- ≤ 500: alarm (PASS with concern)
- \> 500: FAIL (LOC criterion)

## AVC-specific expected baseline

At first audit (`app.py` pre-decomposition):
- LOC ≈ 1900 → FAIL on LOC criterion alone
- Density expected ≈ 30-40% → FAIL on density criterion
- Business-logic patterns expected: formula-eval, panel-construction, signal/slot-wiring, Qt-enum-handling at minimum → FAIL on patterns criterion

Record the actual numbers exactly — they are the baseline against which post-state grades are diffed.

## Reference Python skeleton

```python
import ast
from pathlib import Path

def grade_entry_point(path: Path) -> dict:
    tree = ast.parse(path.read_text())
    statements, call_statements = _count(tree)
    patterns = _find_business_logic_patterns(tree)
    loc = sum(1 for _ in path.read_text().splitlines())
    density = (call_statements / statements * 100) if statements else 0.0
    return {
        "path": str(path),
        "loc": loc,
        "statements": statements,
        "call_statements": call_statements,
        "density_pct": round(density, 1),
        "business_logic_patterns": patterns,
        "verdict": "PASS" if (density >= 70 and not patterns and loc <= 500) else "FAIL",
    }

def _count(tree):
    # Walk module body + recurse into top-level function bodies
    # Skip Import/ImportFrom, docstring Expr nodes, and Pass
    # Count Call-bearing statements
    ...

def _find_business_logic_patterns(tree):
    # Pattern matchers per the table above
    ...
```

Each consumer (auditor / execution-critic) implements `_count` and `_find_business_logic_patterns` against this exact spec.  Drift between consumer implementations breaks the pre/post diff.
