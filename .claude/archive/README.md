# `.claude/archive/` — opt-in-only context graveyard

## Purpose

Holds context files (prior-session notes, draft briefs, superseded plans, stale
critiques) that were once useful but are no longer load-bearing. The goal is to
**preserve them in git history without paying the AI-agent context-window tax**
each time a future agent reads the repo.

## Rule for AI agents

**Do NOT read files under `.claude/archive/` unless the user explicitly references
one by path.** Skip the directory in default greps, file scans, and "explore the
repo" sweeps. Treat it the same as `.git/` for token-cost purposes.

If you find a stale path reference and the rosetta stone in
[`MOVES.md`](../../MOVES.md) does not resolve it, only THEN may you grep
`.claude/archive/` as a fallback.

## What goes here

- One-off session-context dumps (e.g. an obsolete `NOTES.md` from a single
  conversation) — moved here instead of deleted so git blame stays meaningful.
- Roadmap drafts that were superseded before reaching the Now lane.
- Adversary critiques whose findings have been fully closed AND whose milestone
  has been finalized (the live copies live under
  `.claude/notes/milestones/<id>/artifacts/` while the milestone is open).
- Old `CONTEXT.md` snapshots from before a major restructure (keep the live
  `CONTEXT.md` at the root; drop the pre-restructure version here under a
  date-stamped name like `CONTEXT-2026q1.md`).

## What does NOT go here

- **Active rosetta stones** like [`MOVES.md`](../../MOVES.md) — these are
  load-bearing for `/repository-architect` and live at the repo root.
- **In-flight milestone notes** — these stay under
  `.claude/notes/milestones/<id>/` until the milestone is marked complete.
- **Skill reference docs** under `.claude/references/` — those are part of the
  active skill scaffold.

## How to archive a file

```bash
git mv <path/to/stale-file.md> .claude/archive/<descriptive-name>.md
# Optionally add a one-line header at the top:
#   "Archived 2026-MM-DD — original path was X; superseded by Y."
git commit -m "chore(archive): move <file> — superseded by <reason>"
```

That's it. The file stays in git history, future agents won't read it by
default, and you can always retrieve it.
