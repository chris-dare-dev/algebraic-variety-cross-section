# Implementation adversary critique — `/repository-architect`

**Reviewed:** `commands/repository-architect.md` (34KB) + 10 agents + 11 scripts + 3 hooks + 12 references + design synthesis + smoketest output at `.claude/notes/repository-architect/smoketest-restructure-r1/`.
**Critique target:** the actually-implemented pipeline on disk (not the synthesis).
**Verdict:** **PROCEED-WITH-CONDITIONS.** The skeleton is well-structured and the state machine is clean. But there are 3 CRITICAL defects that will surface within the first real run, and a handful of substantive HIGH gaps in agent/orchestrator contract alignment and missing-dep handling. The pipeline is NOT ready for a real restructure today.

**Honesty calibration:** the orchestrator did substantial, careful work. The state machine, schema, audit/evaluator scripts, shim templates, and reference structure are good. CRITICAL findings below are *real* showstoppers that would burn a real run, not severity inflation.

---

## Findings by severity

### CRITICAL — `rewrite-imports.py` silently no-ops on most import rewrites (LibCST API misuse)

**Where:** `.claude/scripts/repository-architect/rewrite-imports.py:107-127`
**Evidence:** The script imports `RemoveImportsVisitor` and `AddImportsVisitor` and calls:
```python
RemoveImportsVisitor.remove_unused_import(ctx, e["from"])
AddImportsVisitor.add_needed_import(ctx, e["to"])
...
new_tree = RemoveImportsVisitor(ctx).transform_module(tree)
new_tree = AddImportsVisitor(ctx).transform_module(new_tree)
```
This is a mis-application of the LibCST API. `RemoveImportsVisitor.remove_unused_import` only removes an import if it is **unused** in the file — but during a refactor the symbol *is still used* in the file (we want to keep using it, just imported from a new path). The result: for a typical batch where `from old_pkg import Foo` is used by `Foo()` elsewhere in the file, the remove step refuses to remove, the add step adds `from new_pkg import Foo` *in addition*, and the file ends up with double imports of the same symbol — OR, more often (because `add_needed_import` checks if `Foo` is already imported under that name), the add is also skipped and the rewrite is a silent no-op.

To actually rewrite `from old import Foo` -> `from new import Foo` you need a custom transformer (typically a `RenameCommand`-style codemod that visits `ImportFrom` / `Import` nodes and rewrites the module path), not the `Remove/AddImportsVisitor` pair. Scout-C names LibCST as the tool but doesn't write the codemod — the implementation glued the wrong two visitors together.

**Why it matters:** Phase 4's mechanical-bulk-rewrite step is the single most load-bearing piece of automation in the whole pipeline. If it silently no-ops, the implementer is forced into manual rewrites per file (defeating the "use libcst, not sed" mandate) OR worse, commits half-rewritten files that pass pytest only because the OLD module path still exists (shim catches it) — the parity-verifier won't flag this because shims are *meant* to keep the old path working. The pipeline would appear to succeed while leaving the codebase with unmoved-in-effect imports.

**Suggested fix:** replace the Remove/Add pair with a proper codemod (e.g., a `cst.CSTTransformer` that visits `ImportFrom` nodes and rewrites the `module` attribute when it matches `e["from"]`). Add a self-test fixture in `scripts/repository-architect/tests/` that round-trips a known input through the script and asserts the output. Until then, the implementer agent should treat `rewrite-imports.py` as PROOF-OF-CONCEPT and surface gate-required on first invocation.

---

### CRITICAL — Phase 4 anchor-updater dispatch in command.md is missing inputs the agent requires

**Where:** `.claude/commands/repository-architect.md:350-355` (Step 4c anchor-updater dispatch block)
**Evidence:** The orchestrator dispatch block reads:
```
Agent: repository-architect-anchor-updater
Inputs: {ID}, {BATCH_NUMBER}, {SYMBOL_MAP_PATH}, {RESTRUCTURE_BASE}
```
But the agent file (`agents/repository-architect-anchor-updater.md:21`) declares its inputs as:
```
- `{OUTPUT_PATH}` — `.claude/notes/repository-architect/{ID}/execute/anchor-updater-batch-{N}-report.md`
```
and its **Step 1** (`agents/repository-architect-anchor-updater.md:36`) reads `{PLAN_PATH}` directly. Two missing inputs:
1. `{OUTPUT_PATH}` — the agent has no idea where to write its report.
2. `{PLAN_PATH}` — the agent needs PLAN.md §6 to know whether CONTEXT.md / README.md edits are authorized.

agent-prompts.md (L97) DOES include `{OUTPUT_PATH}`, and phase-4-execute.md (L77) DOES list it correctly. The command file is the outlier and is what the orchestrator actually consults. The mismatch will cause the agent to (a) literal-substitute `{OUTPUT_PATH}` into a path on disk, (b) fall back to guessing PLAN.md authorization (likely guessing "yes" or "no" wrong).

**Why it matters:** Phase 4c is the agent that touches CONTEXT.md, README.md, and walks `.claude/notes/**`. Mis-substitution + missing-authorization = either the agent silently authorizes itself to edit CONTEXT.md (over-reach, scope violation) or refuses everything (under-reach, anchors stay stale). Either way, the user is mis-informed.

Also: command.md L379 references `anchor-updater-report.md` (no `-batch-{N}-`) in passing while design-synthesis.md L137 also lists `anchor-updater-report.md`. The agent file and the state-schema.md (L40) both use `anchor-updater-batch-{N}-report.md`. The naming convention is inconsistent across 4 files.

**Suggested fix:** align command.md Step 4c with agent-prompts.md — pass `{PLAN_PATH}` and `{OUTPUT_PATH}=.claude/notes/repository-architect/<ID>/execute/anchor-updater-batch-{N}-report.md` (with the `-batch-{N}-` infix). Update design-synthesis.md's diagram to match.

---

### CRITICAL — Three required Phase-3/Phase-4 dependencies (libcst, pydeps, coverage) are not installed and there's no install-gate

**Where:** `.venv/bin/python -c "import libcst"` → `ModuleNotFoundError`; same for `pydeps`, `coverage`.
**Evidence:** Verified in the smoketest environment. `requirements.txt` does not list any of the three. The Phase 3 reference (L29) says "If `pydeps` / `coverage` are missing, the snapshot writes a warning file and continues. PLAN.md should have proposed adding them — surface as a Phase 3 sub-gate" — but the command file does NOT actually implement that sub-gate anywhere I can find. snapshot-baseline.py degrades gracefully (rc 127 written to log), but:
- `rewrite-imports.py` hard-exits 2 ("LibCST not installed").
- `dry-run-validator` agent file L42 says "If LibCST is not installed, surface gate-required" — but this depends on the agent actually running and checking, which is at Phase 3 step 2, AFTER snapshot-baseline.py has already silently fallen back.
- `parity-verifier` agent file L101 says "If a check tool is missing (pydeps not installed), surface gate-required" — but again, this only fires at Phase 4, after the user has already approved Gate 3.

There's no preflight script that says "before you start, here are the deps you need; install them or this run will fail at Phase 3-step-2/Phase-4." The user will hit a failure deep in the pipeline.

**Why it matters:** A user invokes `/repository-architect restructure-foo-r1 --brief "..."` and burns through Phase 1 (3 parallel agents, ~25 min), Phase 2 (PLAN synthesis + adversary, ~15 min), Phase 3 step 1 (snapshot with cryptic warnings), and only at Phase 3 step 2 does the dry-run-validator surface "LibCST required for dry-run" — at which point the user has to abort, install, restart, and possibly re-run Phase 1 because state.json is mid-flight. The pipeline is supposed to be "highly disruptive, runs rarely" — burning an hour of LLM time before discovering missing deps is bad UX for the user paying the bill.

**Suggested fix:** Add a `preflight-deps.sh` script that runs at `init-state.sh` time (or as the very first line of Step 0 in command.md) — checks for libcst/pydeps/coverage and either (a) ABORTs with "install these first: `pip install libcst pydeps coverage`" or (b) emits a sub-gate "deps missing; install or proceed without dry-run? [y/n]". Either way, fail-loud at second 1, not at minute 40.

---

### HIGH — `evaluate-checklist.py` c11 false-positive: `tests/` counts as the source package

**Where:** `.claude/scripts/repository-architect/evaluate-checklist.py:211-220` (c11 check)
**Evidence:** Smoketest output (`/Users/chris.dare/Personal/SourceCode/algebraic-variety-cross-section/.claude/notes/repository-architect/smoketest-restructure-r1/audit/evaluator-report.md`):
```
| 11 | Importable code under a named package | PASS | package(s): ['tests'] |
```
The check iterates `REPO_ROOT.iterdir()` looking for directories with `__init__.py` — `tests/` qualifies. But the intent of c11 (per evaluator-checklist.md item 11: "Importable code under a named package (src/<pkg>/ or <pkg>/)") is to flag AVC's flat-layout `app.py` / `surfaces.py` setup as FAIL until a real source package is created.

**Why it matters:** The whole point of the audit is to feed PLAN.md accurate raw material. If c11 PASSes on AVC today, the designer agent will read "package layout is fine" and miss the foundational scout-D finding that AVC's flat 7-file layout is a candidate for restructure. The evaluator is silently misleading.

**Suggested fix:** exclude `tests` and `docs` from the package-detection set, OR require the discovered package to actually import something from at least one root-level `.py` file (or `app.py` to be inside it).

---

### HIGH — `audit-tree.py` and `evaluate-checklist.py` do NOT exclude `.claude/` itself when walking `.py` files

**Where:** `.claude/scripts/repository-architect/audit-tree.py:36,65-69` and `.claude/scripts/repository-architect/evaluate-checklist.py:59,75,242-243`
**Evidence:** `EXCLUDE_DIRS = {".venv", ".git", "__pycache__", ".pytest_cache"}` excludes 4 dirs and `.claude/worktrees/` via the path-fragment list, but does NOT exclude the entire `.claude/` tree. Smoketest c14 output:
```
| 14 | Module names lowercase with underscores | FAIL | OFFENDERS: ['.claude/scripts/enriques-taubin-spike.py', '.claude/notes/roadmaps/realtime-variety-render/spike-numba-test.py', '.claude/notes/roadmaps/realtime-variety-render/spike-thread-test.py', '.claude/worktrees/agent-a6c58b3c31815c67b/.claude/scripts/roadmap/score-rice.py', ...]
```
Two of those `.claude/worktrees/` paths ARE excluded by the path-fragment filter — good. But `.claude/scripts/enriques-taubin-spike.py` and the spike scripts in `.claude/notes/roadmaps/` slip through and pollute the OFFENDERS list. The user receives a c14 FAIL pointing at files that the pipeline itself just said are OUT OF SCOPE (`.claude/` is OUT OF SCOPE per the user brief per command.md L36-39).

The same exclusion gap affects c16 (star-imports), c17 (>800-LOC files — counts the test_styles_palette.py at 1261 LOC; that's intentional in tests but might be intended to focus on source-tree files), and `audit-tree.py`'s `write_loc`, `write_imports`.

**Why it matters:** The audit brief that goes into PLAN.md is contaminated with out-of-scope `.claude/` files. The designer either has to manually filter them out (cognitive overhead) OR proposes restructure operations on files the pipeline explicitly forbids touching.

**Suggested fix:** add `.claude` and `.github` to `EXCLUDE_DIRS` in `audit-tree.py:36` (probably also `EXCLUDE_PATH_FRAGMENTS += (".claude/",)` since `.claude` is at the root). In `evaluate-checklist.py`, c14/c16/c17 should skip paths starting with `.claude/` and `.github/` (currently only c13's `max_depth_under` does this correctly at L100-103).

---

### HIGH — `summarize-phase.sh` reports total git history count, not "commits since baseline"

**Where:** `.claude/hooks/repository-architect/summarize-phase.sh:60`
**Evidence:**
```bash
execute-complete)
  COMMITS=$(git -C "$REPO_ROOT" log --oneline HEAD 2>/dev/null | wc -l | tr -d ' ' || echo "?")
  SUMMARY="execute complete: $COMMITS commit(s) since baseline; parity-diff.md written"
  ;;
```
`git log --oneline HEAD` lists ALL commits ever in the repo (today: hundreds). The phrase "since baseline" is wrong — the hook doesn't know the baseline SHA at this point. It should be `git log --oneline ${BASELINE}..HEAD`, but the hook signature is `summarize-phase.sh <ID> <new-phase>` — no SHA passed.

**Why it matters:** The summary appended to `dispatch.log` will say something like "execute complete: 287 commit(s) since baseline" when the actual restructure introduced, say, 6 commits. The user `tail -f`-ing dispatch.log will believe the restructure was massive. Compounds: the orchestrator's final 7-line summary at command.md L432-441 reads from state, not from this hook, so the orchestrator's summary is correct — but the dispatch.log will be permanently wrong in the historical record.

**Suggested fix:** read `restructure_base` from state.json inside the hook (or extend the hook signature to accept it), then `git log --oneline "${BASE}..HEAD" | wc -l`. Fall back to "?" if state read fails.

---

### HIGH — Phase 1 step 4 has no orchestrator code path for `audit_briefs` being recorded BEFORE the agent returns

**Where:** `.claude/commands/repository-architect.md:124-131` (Phase 1 "After all 3 agents return")
**Evidence:** The orchestrator runs 3 `--append audit_briefs='".../current-state-brief.md"'` calls AFTER agent return. Each append is atomic (checkpoint.py `_save_atomic`). But the 3 agents run in PARALLEL in one assistant turn (L94 dispatch matrix). If any agent emits a `--append` to its OWN state directly (which the agent prompt allows since they have Bash tool), there's a race window between the file being written and the orchestrator's post-return append.

Worse: the 3 agents share access to `state.json` since they all run under the same repo root. While agent prompts forbid writing to state.json directly (no agent calls checkpoint.py per the agent file scope-bounds — verified), there's nothing in the orchestrator code enforcing it. The smoketest only ran init-state.sh, not actual agent dispatch, so this is untested.

Phase 5 step 1 has the same shape — 2 critics in parallel — but Phase 5's append (parsing critique severity counts) is done by the orchestrator after both return, so no race.

**Why it matters:** Phase 1 race is low-likelihood (agents are scope-bounded), but the parity-verifier batch loop's `--append parity_verifier_reports=...` (phase-4-execute.md L91) inside the per-batch loop happens SEQUENTIALLY (per design), so no race there. Phase 4 batch loop is safe. The Phase 1 race is theoretical given the scope bounds, but the orchestrator should still serialize the appends in its own turn, and the scope-bounds document that "no agent calls checkpoint.py" should be lifted to a higher-visibility position.

**Suggested fix:** Add to "External-write boundary" section: "No sub-agent may invoke `checkpoint.py`. State writes are orchestrator-only." Currently this is implicit in the per-agent scope-bounds but not stated as a pipeline-wide rule.

---

### HIGH — No regression coverage for the pipeline itself (init-state.sh, checkpoint.py, validate-state.py)

**Where:** No `tests/test_repository_architect*.py` exists. Verified via `ls tests/`.
**Evidence:** The smoketest at `.claude/notes/repository-architect/smoketest-restructure-r1/` is a one-shot manual check, not a regression suite. A future change to `PHASE_ORDER` in `checkpoint.py` could silently break the resume-routing dict in `validate-state.py` and the `NEXT_HINTS` dict in `status.sh` — there are THREE phase-list authorities that must stay in sync, with zero automated check.

**Why it matters:** This pipeline is intentionally rare-fire (quarter-cadence). Memory of how it works will fade between runs. The next time someone touches `checkpoint.py:42` PHASE_ORDER, they'll mis-edit one of the other two and discover the desync mid-restructure. Test coverage is the canonical way to lock cross-file consistency.

**Suggested fix:** Add `tests/test_repository_architect_state_machine.py` (Qt-free per AI-2) that:
1. Asserts `checkpoint.PHASE_ORDER == validate_state.PHASE_ORDER`.
2. Asserts `validate_state.NEXT_PHASE_ENTRYPOINT.keys() == set(checkpoint.PHASE_ORDER)`.
3. Asserts `status.sh`'s NEXT_HINTS dict (parsed from the bash file) is the same set.
4. Round-trips init-state.sh → checkpoint advances → validate-state.
5. Asserts forward-only, single-step refusal works.

---

### HIGH — `rewrite-imports.py` cannot rewrite import sites for symbol-map entries that don't import the moved module at all

**Where:** `.claude/scripts/repository-architect/rewrite-imports.py:108-117`
**Evidence:** The script walks every `.py` file and unconditionally applies the remove+add pair. If file `foo.py` does not import the moved symbol at all, the AddImportsVisitor will still try to add it (since `add_needed_import` is presence-checked, this is a no-op in practice). But the bigger concern: for an entry like `{"kind": "module", "from": "appearance_panel", "to": "panels.appearance"}`, calling `RemoveImportsVisitor.remove_unused_import(ctx, "appearance_panel")` is asking LibCST to remove the import IF it is unused in this file. Then `AddImportsVisitor.add_needed_import(ctx, "panels.appearance")` adds it.

What's missing: when the file *does* use `appearance_panel.AppearancePanel`, those references at the *call sites* (e.g. `appearance_panel.AppearancePanel(parent)` in the code body) are NOT rewritten — LibCST's AddImports doesn't touch attribute-access expressions. So the file ends up with `from panels.appearance import AppearancePanel` AND the old `appearance_panel.AppearancePanel(...)` call site, producing a `NameError` at runtime (unless the shim is also imported, which by design it should be — but only because the shim works, not because the rewrite is correct).

**Why it matters:** Same root cause as CRITICAL #1 — the script does not actually accomplish what its docstring claims. Either the shim catches everything (in which case the rewrite is unnecessary) or the rewrite is incomplete (in which case the diff has dangling references). Either way, the pipeline's "use libcst for bulk rewrites" mandate is unfulfilled in practice.

**Suggested fix:** see CRITICAL #1. Same fix family — use a proper `cst.CSTTransformer` that rewrites both imports AND attribute-access references.

---

### HIGH — No `git tag` is ever created for `refactor-baseline-{ID}` despite ROLLBACK.md referencing it

**Where:** `.claude/references/repository-architect/phase-3-preflight.md:72`
**Evidence:** The ROLLBACK.md template includes:
```
**Baseline tag:** refactor-baseline-{ID}
**Baseline SHA:** {restructure_base}
```
But no script in `scripts/repository-architect/` ever calls `git tag`. Neither `init-state.sh`, `precache-baseline.sh`, nor `snapshot-baseline.py` creates the tag. The tag is a phantom reference.

**Why it matters:** Tier 1 rollback (per phase-3-preflight.md L75-77) is `git revert --no-commit {restructure_base}..HEAD`. This is SHA-based, not tag-based, so the rollback still works without the tag. But a user looking at ROLLBACK.md and trying `git checkout refactor-baseline-{ID}` (a natural reflex during a panic) will get "did not match any file(s) known to git". The ROLLBACK.md document is misleading the user about what exists.

**Suggested fix:** Either (a) `snapshot-baseline.py` creates the tag at baseline capture (one extra `git tag refactor-baseline-{ID}`), or (b) remove the `**Baseline tag:**` line from the ROLLBACK.md template. Option (a) is the safer choice because tagged baselines are easier to find months later when the restructure is forgotten.

---

### HIGH — Phase 2's PLAN.md synthesis has no agent — the orchestrator does it in main-session, with no critic on the synthesis itself

**Where:** `.claude/commands/repository-architect.md:159-178` (Phase 2 step 1 "main session synthesizes PLAN.md")
**Evidence:** Phase 1 has 3 parallel research agents. Phase 2 *should* (by symmetry with milestone-pipeline's pattern) have a dedicated synthesizer agent. Instead, the command file says "Read all three audit briefs end-to-end. Write `design/PLAN.md` with these mandatory sections..." This is a main-session task. The design-adversary then critiques that main-session output.

The problem: the design-adversary checks an 11-axis checklist, but only AFTER the orchestrator has spent a large slice of context window reading 3 briefs and writing a multi-thousand-line PLAN.md inline. Context-rot during PLAN synthesis is the most likely vector for hallucinated patterns (the very thing design-adversary is meant to catch).

**Why it matters:** This is structurally weaker than milestone-pipeline, which has dedicated researcher AND implementer agents and uses the main session for orchestration + rectification. Here, the main session is doing both orchestration AND heavy synthesis. A future maintainer comparing the two pipelines will ask "why is the PLAN.md not delegated?" and may not find a documented reason.

**Suggested fix:** Add `repository-architect-plan-synthesizer` agent (Phase 2 step 1, before design-adversary). The main session calls it with `{ID}, {AUDIT_BRIEFS}` and gets back `{PLAN_PATH, SYMBOL_MAP_PATH}`. The design-adversary then critiques. Main session remains orchestrator-only.

---

### MEDIUM — `init-state.sh` ID regex allows ids that don't conform to the documented convention

**Where:** `.claude/scripts/repository-architect/init-state.sh:66`
**Evidence:** Pattern `^[a-zA-Z][a-zA-Z0-9]*(-[a-zA-Z0-9]+)*$` allows `BAD-CAPS-ID`, `restructure-x-r1`, `Bad-Caps-OK` — but the documented convention (command.md L20) is `restructure-<scope>-<YYYYqN>-r<N>`, lowercase-only with the `restructure-` prefix. Smoketest used `smoketest-restructure-r1` which violates the prefix convention but the script accepted it. Acceptable for smoke-testing, but a real user will inevitably commit `Restructure-Panels-r1` or similar and the state directory will be created with caps.

**Why it matters:** State directory naming is load-bearing for `status.sh`, `verify-anchors.py`'s "other restructure run" detection (L51-57), and grep-ability of `dispatch.log` across runs. Mixed-case ids and prefix variation will eventually cause `verify-anchors.py` to mis-classify a current restructure as historical.

**Suggested fix:** tighten the regex to `^restructure-[a-z][a-z0-9]*(-[a-z0-9]+)*$` (forced `restructure-` prefix, lowercase-only), OR keep the loose regex but emit a WARN line if the id doesn't match the strict convention.

---

### MEDIUM — `diff-baselines.py` import-time parser is fragile across Python versions

**Where:** `.claude/scripts/repository-architect/diff-baselines.py:94-110`
**Evidence:** Parses `python -X importtime` output by splitting each line on `|` and looking for `"import time:"` in parts[0]. The format has changed across Python 3.7→3.12, and 3.12's first line is a header (`import time: self [us] | cumulative | imported package`) that should be skipped explicitly. Current code's heuristic "if `import time:` is in parts[0]" will match the HEADER ROW, where `parts[0].split(":")[-1].strip()` is `" self [us] "` — `int()` raises ValueError, caught and skipped. So the header is silently skipped. Function falls through to a real numerical line for the rest. OK.

But there's a deeper issue: `importtime_total` sums `self_us` across ALL lines. This double-counts because each line's `cumulative` already includes children. The current code uses `self`, not `cumulative` — that's correct in principle. But the format also varies: 3.10+ adds nesting indicators that can be in parts[0]. Best-effort, but the orchestrator's final summary "import-time delta: X%" might be 2x off on some systems.

**Why it matters:** The summary number is informational, not a gate. Acceptable as best-effort, but if the importtime delta becomes a decision input (e.g., a critic decides "the import time exploded"), the user might act on a wrong number.

**Suggested fix:** mark the importtime delta as `[informational]` in the parity-diff.md output, or pivot to a more robust parser (`importtime`'s output is well-defined; could iterate from `cumulative` of the top-level `import app` line if present).

---

### MEDIUM — `validate-shims.py` over-trusts process exit codes: a shim that emits a different DeprecationWarning still passes

**Where:** `.claude/scripts/repository-architect/validate-shims.py:91-96`
**Evidence:** Logic:
```python
if result.returncode == 0:
    failures.append((stmt, "no DeprecationWarning emitted"))
elif "DeprecationWarning" not in (result.stderr + result.stdout):
    failures.append(...)
else:
    print(f"  PASS  {stmt}")
```
A PASS only requires (a) non-zero exit AND (b) the literal substring `"DeprecationWarning"` appears somewhere in output. It does NOT check that the warning message contains the *new path* (per scout-C requirement: "Shim warnings include the new path" — rubric item 12). A buggy shim that emits `DeprecationWarning("placeholder")` without the new path will pass validation.

**Why it matters:** verification-rubric.md item 12 ("Shim warnings include the new path") is supposedly checked at Phase 4 by `validate-shims.py`, but the script doesn't actually check it. A migration where the shim says "deprecated" but forgets to say `"use foo.bar instead"` will pass parity and confuse users 6 months later.

**Suggested fix:** extend `validate-shims.py` to parse the symbol-map entry's `to` path and assert the warning message contains a substring of `to`. Add it to the FAIL set if not.

---

### MEDIUM — `verify-anchors.py` won't detect renamed-symbol references; only path-string references

**Where:** `.claude/scripts/repository-architect/verify-anchors.py:108`
**Evidence:** Builds needles from `e["from"]` (module/path strings) but ignores `e["symbol"]` for symbol-kind entries. If a `lessons.md` has a reference like "the AppearancePanel constructor at appearance_panel.py:340", the script will catch `appearance_panel.py` but not `AppearancePanel` if the symbol itself was renamed (e.g. `appearance_panel.AppearancePanel` -> `panels.appearance.AppearancePanelV2`).

**Why it matters:** scout-C §7 ("AI agent context-anchor problem") specifically calls out symbol-name references in agent memory as a known stale-anchor surface. The verifier only catches path-string references.

**Suggested fix:** include `e["symbol"]` in the needle set when present (symbol-kind entries).

---

### MEDIUM — No dedupe-findings.py equivalent for the design-adversary OR execution-critic outputs

**Where:** No `.claude/scripts/repository-architect/dedupe-findings.py` exists, despite milestone-pipeline having one at `.claude/scripts/milestone-pipeline/dedupe-findings.py`.
**Evidence:** Milestone-pipeline command file L291 calls dedupe-findings.py to deduplicate findings before parsing severity counts. /repository-architect parses severity counts directly from the critic output (phase-2-design.md L56-59, phase-5-rectify.md L41-44).

**Why it matters:** The design-adversary walks 11 axes and may emit overlapping findings (e.g., axis 1 "AI-1..AI-15 conflicts" and axis 2 "AI-15 honesty" can both flag the same PLAN.md section). The execution-critic walks 20 rubric items + 10 axes = 30 total checkpoints, with even higher overlap potential. Without deduping, the user-facing severity counts ("C2 H4 M7 L11") will be inflated.

**Suggested fix:** clone `dedupe-findings.py` from milestone-pipeline (or refactor it to a shared `.claude/scripts/_shared/dedupe-findings.py`) and call it after both adversary and execution-critic returns. Severity-count parsing should happen on the deduped output, not the raw.

---

### MEDIUM — Phase 4d batches-landed increment in phase-4-execute.md uses bash that may fail if `--get` returns non-numeric

**Where:** `.claude/references/repository-architect/phase-4-execute.md:96-99`
**Evidence:**
```bash
LANDED=$(.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py {ID} --get execute_batches_landed)
.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py {ID} \
    --set execute_batches_landed=$((LANDED + 1))
```
If `checkpoint.py --get` errors (state corruption, missing field), `LANDED` becomes empty string, `$((LANDED + 1))` becomes `1` (bash treats empty as 0). The increment silently resets the counter. The command file itself (L373-376) has the SAME shell-arithmetic pattern that the phase-4 reference uses, including `$(.venv/Scripts/python.exe ...checkpoint.py <ID> --get restructure_base)..$(git rev-parse HEAD)` — and `--get restructure_base` will print the SHA followed by a newline; the surrounding double-quote wrap (`"$BASE..$HEAD"`) handles the newline, but a state-corruption scenario could yield `null\n` (the literal Python None print).

**Why it matters:** silent resets to a counter could cause the orchestrator to lose track of how many batches have landed when resuming after a context compaction. The user re-resumes and gets restarted at batch 1 even though batch 3 was already in flight.

**Suggested fix:** wrap the `--get` in a check: `LANDED=$(checkpoint.py --get execute_batches_landed) || exit 1; [[ "$LANDED" =~ ^[0-9]+$ ]] || exit 1`. Or use `checkpoint.py --increment execute_batches_landed` (new command) instead of read-modify-write.

---

### MEDIUM — Phase 2 design-adversary loops back to Step 1 without bumping a re-dispatch counter

**Where:** `.claude/commands/repository-architect.md:214`; `.claude/references/repository-architect/phase-2-design.md:81-82`
**Evidence:** "If any CRITICAL/HIGH findings are unaddressed in PLAN.md, the orchestrator MUST loop back to Step 1 (revise PLAN.md) before surfacing the gate as approvable." There's no state field for "design-revision-count" or "design-adversary-runs"; if the loop bounces 3+ times the orchestrator has no signal to bail.

**Why it matters:** A bad PLAN that keeps regressing on the same 11 axes could send the pipeline into a synthesis-critique loop that burns tokens with no progress. The user has no visibility into "we're on round 5 of revising PLAN.md."

**Suggested fix:** add `design_revision_count: int` to state.json schema; bump on each Phase 2 step 1 re-entry; surface gate-required to user if count > 3 with summary of what's not converging.

---

### MEDIUM — `precache-audit-snapshot.sh` and `precache-baseline.sh` freshness check is by mtime, not by repo SHA

**Where:** `.claude/hooks/repository-architect/precache-audit-snapshot.sh:54-64`; `precache-baseline.sh:49-58`
**Evidence:** Freshness = "all files exist AND each is <1h old by mtime." If the user has just committed a large change (`git commit -am "refactor X"`) and re-runs the pipeline 30 minutes later, the cache will be considered fresh even though the underlying repo has shifted. This is acceptable for the audit cache (it's an audit — slight staleness is OK) but more concerning for the baseline cache (Phase 3 baseline should reflect the CURRENT HEAD, not a 30-min-old snapshot).

**Why it matters:** The baseline snapshot is the load-bearing reference for parity checks across all of Phase 4. A stale baseline taken before a final commit would make every batch report inflated coverage/import-time deltas.

**Suggested fix:** in `precache-baseline.sh`, ALSO compare `git rev-parse HEAD` against `baseline.git_sha.txt`. If different, force re-snapshot regardless of mtime.

---

### MEDIUM — `snapshot-baseline.py` hard-codes `"import app"` for the importtime measurement

**Where:** `.claude/scripts/repository-architect/snapshot-baseline.py:158`
**Evidence:** `[py, "-X", "importtime", "-c", "import app"]`. AVC's main module is `app.py` at root — this currently works because of the flat layout. But the WHOLE POINT of `/repository-architect` is to introduce a package (per scout-D restructure brief). After a restructure that introduces `avc/` as a package, `import app` may stop working or import the wrong thing.

**Why it matters:** Post-restructure `snapshot-baseline.py --post` runs with the new layout. If `app` is now `avc.app`, the importtime call fails with `ModuleNotFoundError`, the warning goes to the .log file, and importtime parity check silently degrades.

**Suggested fix:** read the root-import-target from state.json (new field `entrypoint_module`, default `"app"`) so the post-restructure run can use the new path. Or fall back to `python -c "import sys; print(sys.executable)"` if `import app` fails (smoke probe).

---

### MEDIUM — `precache-audit-snapshot.sh` writes to `dispatch.log` is missing — no dispatch line on hook fire

**Where:** `.claude/hooks/repository-architect/precache-audit-snapshot.sh` (entire file)
**Evidence:** The hook prints to stdout ("Pre-caching audit snapshot...") but does NOT append to `dispatch.log`. Per command.md L107-108, dispatch.log is meant to be the `tail -f`-able log of pipeline progress. Hook executions are silent in that log.

**Why it matters:** A user watching `dispatch.log` for "what's the pipeline doing now?" will see a 30-second gap when the precache hook is running (it walks the whole tree), with no indication of what's happening.

**Suggested fix:** add `echo "$(date -u +%FT%TZ) | hook | precache-audit-snapshot | start" >> "$DISPATCH_LOG"` at hook entry and `... end` at hook exit.

---

### LOW — `evaluate-checklist.py` c25 will fail on the AVC repo today (missing `.pytest_cache` in `.gitignore`) but this is informational not actionable

**Where:** `.claude/scripts/repository-architect/evaluate-checklist.py:333-339`
**Evidence:** Smoketest: `| 25 | .gitignore covers __pycache__, .pytest_cache, *.pyc, build, IDE | FAIL | MISSING: ['.pytest_cache'] |`. The check requires literal `.pytest_cache` substring; AVC's `.gitignore` only has `__pycache__/` and `*.pyc`.

**Why it matters:** This is a real audit finding, just not necessarily one the user wants flagged at restructure time. Adding `.pytest_cache/` to `.gitignore` is a 1-line fix; it doesn't need a restructure.

**Suggested fix:** keep the check (it's correct), but evaluator-checklist.md should note this is a c25 FAIL that's a 1-line fix outside the restructure scope.

---

### LOW — `status.sh` brief-truncation is character-count not unicode-aware

**Where:** `.claude/scripts/repository-architect/status.sh:70`
**Evidence:** `state['restructure_brief'][:60]` slices by character count. A brief with multi-byte unicode characters could cut mid-character (Python 3 string slicing is by codepoint, so this is actually safe — false alarm). Real issue: if brief is empty (default), it prints `Brief:       ` (no warning); user might be confused why their brief is missing.

**Why it matters:** Minor UX paper-cut.

**Suggested fix:** if brief is empty, print `Brief:       (not set — pass --brief)`.

---

### LOW — `agent-prompts.md` shows `<from state.X>` literal in some places but `{X}` in others — minor consistency

**Where:** `.claude/references/repository-architect/agent-prompts.md` throughout
**Evidence:** L46-47: `{PLAN_PATH} = <from state.plan_path>`; L93: `{SYMBOL_MAP_PATH} = <from state.symbol_map_path>`. The substitution convention switches between angle-bracket and curly-brace in places. Trivial.

**Why it matters:** A new agent author copying the template might be confused about which form to expect at substitution time. Cosmetic.

**Suggested fix:** standardize on `<from state.field_name>` in templates.

---

### LOW — `audit-tree.py` `write_ai_invariants` loops `range(1, 30)` — assumes invariants are AI-1..AI-29

**Where:** `.claude/scripts/repository-architect/audit-tree.py:125`
**Evidence:** `for i in range(1, 30)` to look for AI-N markers. App-invariants.md currently has AI-1..AI-15. If AI-16 is added later, it's covered (range goes to 30). If AI-30 is ever added, it won't be picked up.

**Why it matters:** Minor future-proofing. The auditor would notice the missing one quickly. The "30" is somewhat arbitrary — could be `range(1, 50)` or `range(1, 100)` at zero extra cost.

**Suggested fix:** bump to `range(1, 100)` (still cheap) or scan the file for `^AI-(\d+)` first to get the actual count.

---

## Axes with NONE findings (clean axes)

- **Severity calibration** — no inflation observed; CRITICAL count is realistically 3.
- **Sub-agent JSON contract shape** — all 10 agents declare the same `{file_path, status, summary, injection_attempts}` schema; test-suggester correctly adds `not-applicable` as its unique status (command.md L500 documents this).
- **Resume routing key-set integrity** — `validate-state.py:NEXT_PHASE_ENTRYPOINT` has exactly 11 keys matching `checkpoint.py:PHASE_ORDER`. `status.sh`'s `NEXT_HINTS` also matches. No drift detected.
- **External-write boundary documentation** — every agent declares scope-bounds with a forbidden list AND an allowed list (or implicit single-output-path). Anchor-updater's special permission is clearly delimited.
- **AI-1..AI-15 invariant coverage in design-adversary** — axis 1 in design-adversary explicitly lists AI-1, AI-2, AI-3, AI-4/5, AI-6, AI-7, AI-8, AI-9, AI-10, AI-12, AI-14, AI-15. AI-11 and AI-13 are not enumerated but the axis is "AI-1..AI-15 conflicts" so they're implicitly covered.
- **5-gate enforcement language** — Gates 1, 2, 3, 4, 5 are each documented with the explicit "[y/n]" surface and are referenced from multiple files (command.md, phase-N-*.md). No "auto-advance" path detected.
- **Shim template correctness** — shim-templates.md Template 1 and 2 are both correct Python 3 `__getattr__` patterns; Template 3 (the WRONG pattern) is correctly marked DO-NOT-USE.
- **Memory bootstrap pattern** — every agent reads its `lessons.md` first; the protocol is uniform.

---

## Comparison to `/milestone-pipeline` — what was missed

The milestone-pipeline siblings have the following capabilities not present here:

1. **`dedupe-findings.py`** — milestone-pipeline dedupes critic findings before counting. /repository-architect doesn't. See MEDIUM finding above.
2. **`--force-deps` override flag** — milestone-pipeline has a dep-check at init time that gates on prior milestones. /repository-architect doesn't have a parallel concept (multiple restructures in flight), but the cleanliness gate `git status --porcelain` (phase-3-preflight.md Step 0) has no override flag. If a user has a small uncommitted change they want to keep for unrelated reasons, they MUST stash. No `--force-clean` escape hatch.
3. **`status.sh` polling cadence** — milestone-pipeline says "poll every 5 min". /repository-architect says the same in phase-1-audit.md L71 but the orchestrator doesn't have a built-in poller. (Both pipelines push this on the user.)
4. **`oss-scout` add-on** — milestone-pipeline has `--oss-scout` to add a peer-comparison critic. /repository-architect could benefit from a "how do napari/ParaView lay out their tree?" peer-comparison critic at Phase 1 (the best-practices-scout sort of does this but as web research, not as a code-level comparison).
5. **`--single` / `--deep` flags for Phase 1** — milestone-pipeline lets the user toggle single vs deep researcher; /repository-architect hardcodes the 3-agent fan-out. A user wanting a quick "just give me the audit" should be able to dispatch only the current-state-auditor.

---

## Plus: proposed additional agents / capabilities

### 1. `repository-architect-plan-synthesizer` (Phase 2, NEW)

**Phase:** 2, BEFORE design-adversary.
**What:** Read the 3 audit briefs, draft PLAN.md + symbol-map.json with all 8 mandatory sections. Hand back to orchestrator.
**Why:** Removes the main-session synthesis bottleneck (see HIGH finding above). Lets the main session stay clean for orchestration.
**Complexity:** M. ~10K agent file, mirrors milestone-implementer's shape.

### 2. `repository-architect-diff-explainer` (Phase 5, NEW)

**Phase:** 5, alongside execution-critic.
**What:** Read `parity-diff.md` + the execution-critic's CRITICAL/HIGH findings, write a 1-page human-readable "what changed, what's at risk" summary in plain English (target reader: future maintainer reviewing the restructure 6 months later).
**Why:** The 7-line orchestrator summary at Phase 5 step 5 is too terse. A reviewer 6 months out needs to understand WHY each batch was structured the way it was, not just what changed.
**Complexity:** S. ~4K agent file. Read-only, single output.

### 3. `repository-architect-peer-comparison-scout` (Phase 1, NEW — gated on `--peer-scout` flag)

**Phase:** 1, parallel to the existing 3.
**What:** Survey 3-5 peer Qt+VTK desktop apps (napari, ParaView, PyMOL-open-source, Spyder) and write a structured comparison of their `panels/`, `surfaces/`, `varieties/`, `render/`, `_qt/` layouts. Outputs `audit/peer-comparison-brief.md`.
**Why:** Best-practices-scout does WEB research; this would do CODE-LEVEL comparison ("how do they actually organize 50+ panel widgets?"). Gated on flag to keep default invocations cheap.
**Complexity:** M. ~6K agent file, depends on Bash + WebFetch.

### 4. `repository-architect-test-mover` (Phase 4, NEW — gated on PLAN containing test moves)

**Phase:** 4, AFTER implementer per batch, BEFORE parity-verifier.
**What:** Handles the `tests/` mirror-tree restructure specifically. Tests are tricky because of conftest.py scope drift (scout-C §3). This agent reads PLAN.md's test-move section, executes `git mv` for affected tests, updates conftest.py imports IF authorized, and runs `pytest --collect-only` to confirm fixtures still resolve.
**Why:** The implementer agent's prompt currently lumps test moves with source moves. Test moves have a different risk profile (conftest, fixtures, parametrize, plugin discovery) that deserves separate handling.
**Complexity:** M. ~7K agent file.

### 5. `repository-architect-dependency-proposer` (Phase 2 sub-step, NEW)

**Phase:** 2, AFTER PLAN synthesis, BEFORE design-adversary.
**What:** Read the PLAN, detect any new tools the implementer will need (libcst, pydeps, coverage, mutmut, ruff), emit a proposed `requirements.txt` diff and a "user-must-install" gate. Acts as a sub-gate to Gate 2/3 to head off the CRITICAL #3 issue (missing deps surfaced mid-pipeline).
**Why:** Closes the missing-dep failure mode at the design-review phase, not at execution.
**Complexity:** S. ~3K agent file, single-purpose.

### 6. `repository-architect-rollback-rehearser` (Phase 3 sub-step, NEW)

**Phase:** 3, AFTER ROLLBACK.md is written, BEFORE Gate 3.
**What:** In a `git worktree add` scratch directory, ACTUALLY runs the Tier 1 rollback command from ROLLBACK.md against the planned commit set (simulated via `git commit --allow-empty` markers). Confirms the rollback would return cleanly to the baseline SHA.
**Why:** verification-rubric.md item 20 ("Rollback command tested in a scratch worktree") is listed as a Phase 3 check but no script actually runs it. This agent operationalizes the check.
**Complexity:** L. Requires worktree management, multiple git operations, error handling. ~8K agent file.

### 7. `repository-architect-pre-flight-deps-checker` (script, NEW — not an agent)

**Phase:** Step 0, run by `init-state.sh`.
**What:** `scripts/repository-architect/check-deps.sh` that runs `python -c "import libcst, pydeps, coverage"` and emits ABORT with install instructions if any fail.
**Why:** Closes CRITICAL #3 at second 1 of the pipeline.
**Complexity:** XS. ~30-line bash script.

### 8. `repository-architect-state-machine-test` (test file, NEW — not an agent)

**Phase:** N/A — pre-commit safety net.
**What:** `tests/test_repository_architect_state_machine.py` (Qt-free per AI-2) that locks PHASE_ORDER consistency across `checkpoint.py`, `validate-state.py`, `status.sh`. Round-trips init-state.sh + checkpoint.py advances. Asserts forward-only and single-step rejection.
**Why:** Closes HIGH finding above. Lock against bit-rot during multi-month no-restructure stretches.
**Complexity:** S. ~150-line pytest file.

---

## Recommended pre-Phase-3-real-use edits

Block before any real `/repository-architect <real-id>` invocation:
1. Fix CRITICAL #1 (rewrite-imports.py LibCST API misuse).
2. Fix CRITICAL #2 (Phase 4c anchor-updater missing OUTPUT_PATH + PLAN_PATH).
3. Fix CRITICAL #3 (deps gate at init time).
4. Fix HIGH #1 (c11 false-positive) — the audit narrative is misleading without it.
5. Fix HIGH #2 (`.claude/` exclusion gap) — same reason.

After those 5, the remaining HIGH/MEDIUM/LOW are deferrable to a "post-first-real-run hardening" milestone.

---

## Rectification status (appended 2026-05-23)

The orchestrator rectified the 5 BLOCKER-grade findings (CRITICAL 1-3 + HIGH 1-2) plus 3 cheap-fix HIGH items. The remaining HIGH items are deferred to a follow-up "post-first-real-run hardening" milestone because they require either significant new agent work (plan-synthesizer) or a separate test-pipeline scaffold (state-machine regression tests).

### Fixed in this rectify pass

| Severity-id | Title | Fix |
|---|---|---|
| C1 | rewrite-imports.py LibCST API misuse | Replaced Remove/Add visitor pair with a proper `cst.CSTTransformer` that rewrites BOTH `ImportFrom`/`Import` module paths AND attribute-access call sites (`old.X(args)` -> `new.X(args)`). Closes HIGH #6 as the same root cause. |
| C2 | Phase 4c anchor-updater missing `OUTPUT_PATH` + `PLAN_PATH` | command.md Step 4c dispatch block updated to include both inputs. design-synthesis.md filename naming aligned to `anchor-updater-batch-{N}-report.md`. |
| C3 | No preflight deps gate | New `scripts/repository-architect/check-deps.sh` verifies libcst/pydeps/coverage at second 1 of every run; wired into `init-state.sh` to ABORT before any agent dispatch. Smoke-tested: correctly exits 1 when deps are missing. |
| H1 | c11 false-positive (`tests/` counted as source package) | `evaluate-checklist.py:c11` now excludes `tests/`, `docs/`, `examples/`, `scripts/`, `tools/`, `benchmarks/` from package detection. Smoke-test confirmed: AVC now correctly FAILs c11 with "NO SOURCE PACKAGE -- 11 loose .py files at root". |
| H2 | `.claude/` not excluded from auditor + evaluator | `audit-tree.py:EXCLUDE_DIRS` adds `.claude` + `.github`; `evaluate-checklist.py` introduces shared `_is_out_of_scope()` helper applied to c14/c16/c17. Smoke-test confirmed: c14 now PASSes (was OFFENDERS containing 5 `.claude/` files). |
| H3 | `summarize-phase.sh` reports total git log, not "since baseline" | Hook now reads `restructure_base` from `state.json` and uses `git log "${BASE}..HEAD"`. Falls back to "?" if state read fails. |
| H4 | Phase 1 race / no orchestrator-only state-write rule | command.md external-write boundary now declares: "No sub-agent may invoke `checkpoint.py` to write state.json. State writes are orchestrator-only." |
| H7 | Phantom `git tag refactor-baseline-{ID}` in ROLLBACK.md | phase-3-preflight.md Step 4 now creates the tag (`git tag "refactor-baseline-{ID}" $restructure_base`) and ROLLBACK.md offers an alternate tag-based Tier-1 cmd. |

### Deferred (to follow-up hardening milestone)

| Severity-id | Title | Deferral reason |
|---|---|---|
| H5 | No regression coverage for state machine | Significant new test file (~150 LOC) requires a separate milestone; not a runtime risk for the first /repository-architect invocation. |
| H8 | No PLAN.md synthesizer agent (main-session does it) | Significant new agent (~10K file) + Phase 2 restructure; ergonomic-not-blocking improvement. |
| M1-M9 | All MEDIUM | Polish + edge-case handling; defer to hardening milestone. |
| L1-L4 | All LOW | Cosmetic; defer. |

### Recommended follow-up milestone

Name: `repository-architect-post-first-run-hardening-2026q4-e1`
Scope: H5, H8, M1-M9, L1-L4 + adversary's 8 proposed agents/capabilities.
Estimated effort: M-L (multiple new agents + test scaffold + script enhancements).

