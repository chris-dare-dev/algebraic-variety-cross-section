# Phase 5 — Critique + Rectify

**Goal:** post-execution adversary on the actual diff; main-session rectification of CRITICAL/HIGH; defer MEDIUM/LOW.

## Step 1 — Fan-out critics (ONE assistant turn)

```
Agent: repository-architect-execution-critic
Inputs:
  {ID}
  {EXECUTE_COMMIT_RANGE}  (from state.execute_commit_range)
  {BASELINE_DIR}
  {PLAN_PATH}
  {PARITY_DIFF_PATH}      .claude/notes/repository-architect/{ID}/execute/parity-diff.md
  {OUTPUT_PATH}           .claude/notes/repository-architect/{ID}/rectify/execution-critic-critique.md

Agent: repository-architect-test-suggester
Inputs:
  {ID}
  {EXECUTE_COMMIT_RANGE}
  {PLAN_PATH}
  {OUTPUT_PATH}           .claude/notes/repository-architect/{ID}/rectify/test-suggester-suggestions.md
```

The execution critic walks scout-C's 20-item rubric + a 10-axis institutional checklist against the actual diff and parity-diff.md.

The test-suggester proposes new cross-suite tests per scout-C §8 — does NOT write tests.

Append dispatch.log entries on dispatch + return.

## Step 2 — Record + advance

```bash
CRIT="$(.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py {ID} --get execution_critic_path 2>/dev/null || echo '')"
if [[ -z "$CRIT" ]]; then
  CRIT=".claude/notes/repository-architect/{ID}/rectify/execution-critic-critique.md"
  .venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py {ID} --set execution_critic_path="\"$CRIT\""
fi

# Parse severity counts
C=$(grep -c '^### CRITICAL' "$CRIT" || echo 0)
H=$(grep -c '^### HIGH'     "$CRIT" || echo 0)
M=$(grep -c '^### MEDIUM'   "$CRIT" || echo 0)
L=$(grep -c '^### LOW'      "$CRIT" || echo 0)
.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py {ID} \
    --set critique_finding_counts="{\"critical\": $C, \"high\": $H, \"medium\": $M, \"low\": $L}"

.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py {ID} \
    --set test_suggester_path='".claude/notes/repository-architect/{ID}/rectify/test-suggester-suggestions.md"'
.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py {ID} rectify-running
```

## Step 3 — GATE 5: surface critique to user

```
Phase 5 critique for {ID}:
  Execution critic: C<n> H<n> M<n> L<n>
  Test suggester:   <K> suggestions across <J> categories

Rectify? [y/n]
```

## Step 4 — Main-session rectification (NOT delegated)

The rectifier IS the main session. Do NOT delegate Phase 5 step 4 to a sub-agent — it needs the user's review surface and the ability to commit.

### Re-verification (required BEFORE any fix)

For every CRITICAL and HIGH finding: read the cited `file:line` (±30 surrounding lines) to confirm the issue is still present. If no longer present, mark INVALIDATED — do NOT silently drop.

```bash
.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py {ID} \
    --append invalidated_findings='"H3"'
```

If invalidation rate exceeds 40% (more than 4/10), surface gate-required: the critic prompt is likely broken or was fed a stale diff.

### Fix loop

Priority: CRITICAL (block ship) -> HIGH (block ship) -> MEDIUM (fix if <=30 LOC) -> LOW (defer).

For each CRITICAL/HIGH:
1. If the fix needs a regression test that's Qt-free (AI-2): write it.
2. Make the fix.
3. Run affected tests. 3 inner-loop iterations max.

After all mandatory fixes: full `pytest -q`. 3 outer-loop iterations max.

### Rectification commit (single commit, NOT amended)

```
rect-restructure({ID}): close C1, H1, H2; defer M1, L1
```

Body lists fixed / deferred / invalidated severity-ids.

```bash
.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py {ID} \
    --set rectification_commit="\"$(git rev-parse HEAD)\""
for fid in C1 H1 H2; do
  .venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py {ID} \
      --append fixed_findings="\"$fid\""
done
for fid in M1 L1; do
  .venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py {ID} \
      --append deferred_findings="\"$fid\""
done

.venv/Scripts/python.exe .claude/scripts/repository-architect/checkpoint.py {ID} complete
bash .claude/hooks/repository-architect/summarize-phase.sh {ID} complete
```

## Step 5 — Final summary (7 lines)

```
Restructure: {ID}
Batches:     <N> executed
Commits:     <N> (range <base>..<HEAD>)
Findings:    C<critical> H<high> M<medium> L<low>
Resolved:    fixed=<n> deferred=<n> invalidated=<n>
Parity:      collection delta=<n>, coverage delta=<%>, cycles delta=<n>
MOVES.md:    updated with <N> entries
```

**Do NOT auto-push.** This pipeline never pushes — the user pushes when ready.

## Anti-patterns to refuse

- Running Phase 5 step 4 as a sub-agent (needs user review surface).
- Letting the implementer write the critique (scope separation).
- Elevating severity to "earn" the pipeline. Zero CRITICAL is legitimate.
- Skipping the re-verification step ("the critic said so, must be true").
- Bundling test-suggester suggestions INTO this restructure's rectify commit (write tests in a follow-up milestone per scout-C §10.1).
