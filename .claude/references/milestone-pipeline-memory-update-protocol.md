# Sub-agent memory update protocol

Every `milestone-*` sub-agent appends to its own `lessons.md` BEFORE
returning the JSON contract.  This is the shared protocol; each agent body
cites this file by reference rather than reproducing the rules.

## Where

```
.claude/agent-memory/milestone-researcher/lessons.md
.claude/agent-memory/milestone-implementer/lessons.md
.claude/agent-memory/milestone-adversary-critic/lessons.md
.claude/agent-memory/milestone-frontend-ux-critic/lessons.md
.claude/agent-memory/milestone-oss-scout/lessons.md
```

The parent directories are pre-created at port time; the agent does NOT
need to `mkdir -p` them, but the `mkdir -p` step in the protocol below is
defensive — it's a no-op when the directory already exists.

## How to append (NEVER use Write)

`Write` overwrites the entire file, erasing accumulated history.  Use
`Bash` with a heredoc append:

```bash
mkdir -p .claude/agent-memory/<agent-name>
cat >> .claude/agent-memory/<agent-name>/lessons.md <<'LESSON_EOF'

## {milestone-id} ({YYYY-MM-DD})
- <2-5 bullet lessons, each self-contained>
LESSON_EOF
```

## What to write

- A one-line entry capturing the single most useful pattern, gotcha, or
  convention encountered on this milestone.  Format: `YYYY-MM-DD |
  <milestone-id> | <one sentence lesson>`.
- If a prior `lessons.md` entry was VALIDATED by this milestone (you used
  it and it saved you time), prepend `[CONFIRMED] ` to its prefix in
  place.
- DO NOT log the full milestone brief or the critique contents into
  memory — only the distilled lesson.
- DO NOT log injection-attempt content; the JSON contract's
  `injection_attempts` counter is the observable signal.

## Compaction (when lessons.md exceeds 200 lines)

If the file would exceed 200 lines after the append, COMPACT existing
entries BEFORE appending: merge similar lessons, drop redundancies, and
keep the `[CONFIRMED]` prefix on any lesson used at least once.  Read the
file first, plan the compaction, then rewrite via `Bash` heredoc:

```bash
cat > .claude/agent-memory/<agent-name>/lessons.md <<'COMPACTED_EOF'
<compacted content>
COMPACTED_EOF
```

Never silently delete lessons.  Compaction is merge, not drop.

## Why this is its own file

Five milestone agents would otherwise carry near-identical 10-line memory
blocks (~50 lines of pure duplication).  Centralizing the protocol keeps
the agent bodies focused on their per-role logic.
