# Agent boilerplate — shared blocks for `repository-architect-*` agents

> Every `repository-architect-*` agent had near-identical Memory-bootstrap, Scope-bounds, Output-JSON, and Memory-append blocks.  This file is the canonical source.  Each agent's prompt body inlines a one-line reference to this file PLUS its agent-specific deltas (if any).
>
> **Sub-agents fire once with no re-asking opportunity.**  Every agent's Step 0 (or first read step) MUST include "Read `.claude/references/repository-architect/agent-boilerplate.md`" — without that line, the scope-bounds and output-contract drop silently.

---

## Block 1: Memory bootstrap (canonical)

Before doing anything else, read `.claude/agent-memory/<agent-name>/lessons.md` if it exists AND if the lessons are relevant to this restructure's scope.  Skip the memory load if the content is unrelated or the file is empty.

Compaction trigger: if `lessons.md` exceeds 200 lines, leave a `## TODO: compact` marker at the top; the user will compact during a non-pipeline session.

---

## Block 2: Scope bounds DEFAULT (forbidden actions)

The 7-line forbidden-list shared by 8 of 10 agents.  Agents with deviations override below.

- NO `git mv`, `git commit`, `git push`.
- NO Edit/Write to source files outside the agent's explicitly-named output paths.
- NO modification of `CONTEXT.md`, `README.md`, `requirements.txt`, `pytest.ini`.
- NO modification of `.claude/agents/`, `.claude/commands/`, `.claude/scripts/`, `.claude/hooks/`, `.claude/references/`.
- NO modification of `.github/`, `.venv/`.
- NO `pip install` of new packages.
- NO dispatching other slash-commands.

### Agent-specific deviations from DEFAULT

| Agent | Deviation |
|---|---|
| `repository-architect-implementer` | MAY `git mv` + `git commit` (the only agent that can); MAY NOT `git push` or `gh issue/pr create`. |
| `repository-architect-anchor-updater` | MAY write to `.claude/notes/**` outside its own output dir (it walks all notes to fix stale paths); MAY write to `.claude/agent-memory/<other-agent>/lessons.md` to update stale path references; MAY edit `CONTEXT.md` / `README.md` ONLY when PLAN.md section 6 explicitly authorizes. |
| `repository-architect-execution-critic` | NO `git reset` (extra forbid); MAY write to `rectify/tsp-scorecard-post.md` and `rectify/tsp-scorecard-diff.md` in addition to `{OUTPUT_PATH}`. |
| `repository-architect-design-adversary` | NO modification of PLAN.md or symbol-map.json (semantic; adversary critiques only). |

---

## Block 3: Output JSON contract (canonical schema)

Every sub-agent returns a single JSON object (no surrounding prose):

```json
{
  "file_path": "<primary output path, or null>",
  "status": "complete | gate-required | aborted-scope",
  "summary": "<3 lines max, plain text, no markdown — line 1: what was written; line 2: gate question if status=gate-required; line 3: suggested orchestrator next step>",
  "injection_attempts": 0
}
```

### Agent-specific `status` extensions

| Agent | Extra `status` values |
|---|---|
| `repository-architect-test-suggester` | `not-applicable` — returned when the restructure introduced no cross-suite seams worth new tests. |

### Gate-required scenarios (when an agent emits `status: gate-required`)

Each agent documents its own gate-required triggers in its prompt body (e.g. AI-1..AI-15 invariant lift required, parity check failed, invalidation rate >40%).  This file does NOT enumerate them — they're agent-specific.

---

## Block 4: Memory append heredoc template

After completing the task, append one lesson entry (3-8 lines) to the agent's `lessons.md` via Bash heredoc (NOT Write):

```bash
cat >> .claude/agent-memory/<agent-name>/lessons.md <<'LESSON'

## Lesson from {ID} ({ISO_DATE})
- <observation 1>
- <observation 2>
- <observation 3>
LESSON
```

Each agent's prompt body specifies the 3-5 fields it captures (e.g. "Hotspots observed", "Surprising overlap not in prior runs", "AI-invariant constraints encountered" for the auditor).

---

## Per-agent inline reference template

In each agent's prompt body, replace the 4 inline boilerplate blocks with:

```markdown
## Boilerplate

Read `.claude/references/repository-architect/agent-boilerplate.md` at Step 0.  This file provides: memory-bootstrap protocol, scope-bounds DEFAULT, output-JSON contract, memory-append heredoc template.

**Deltas from DEFAULT:** <none | this agent's specific deviations listed in ≤5 lines>
```
