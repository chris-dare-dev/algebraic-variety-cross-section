# /milestone-pipeline — anti-patterns

The shared table of rationalizations that surface during milestone-pipeline
runs.  The command body keeps the milestone-specific rows inline; this file
carries the long-tail generic table.

| Tempting belief | Reality |
|---|---|
| "Skip research — milestone is well-scoped." | Research agents catch prior art ~60% of the time.  15 min parallel cost prevents 4-hour rework. |
| "Fire researchers one at a time to read each brief as it lands." | Sequential research doubles wall-clock and kills diversity.  ONE turn, both agents. |
| "Critique is clean — skip Phase 4." | Even zero findings still need `pytest tests/ -q` re-run AND deferred-LOW recording. |
| "Have the implementer fix critic findings — saves a round." | Implementer is biased toward defending its design.  Rectifier must be distinct. |
| "Skip checkpointing — the pipeline is short." | Context compaction can clobber phase output mid-pipeline.  State files are 200 bytes. |
| ">40% of critic findings invalidate on re-verification." | The critic prompt is broken or was fed a stale diff.  Tune the prompt; do not skip Phase 4. |
| "Use worktree isolation for the delegated implementer." | The `.venv` is gitignored; isolation breaks it.  Use regular branches (`impl-{ID}-solo`). |
| "Just substitute `{LETTER}` later." | Sub-agents don't see follow-up instructions.  Substitute at dispatch time or the agent writes `implementer-{LETTER}-deviations.md` literally. |
| "I'll skim the diff and write findings." | Diff-skim critiques miss the bugs this skill exists to catch.  Read every non-trivial hunk end-to-end. |
| "Inflate severity to make the critique look thorough." | Inflated severity = noise.  Zero CRITICALs and zero HIGHs is a credible result. |

Milestone-specific rows (Qt-panel critic, section-9 non-goals, auto-push)
remain in `.claude/commands/milestone-pipeline.md` — they are load-bearing
in the command body's "Common rationalizations" section because they
encode AVC-specific git workflow and architectural conventions.
