# Adversarial critique - /milestone-pipeline port to algebraic-variety-cross-section

**Date:** 2026-05-20
**Critic:** adversarial Opus
**Files reviewed:** 24 port files + 4 reference comparison points (`/roadmap` command + 4 roadmap sub-agents + `critique-format.md` + reference repo originals)

---

## Executive summary

The port is functional - scripts run, paths resolve, the state machine validates - but it carries systematic drift from the freshest local convention (`/roadmap`, ported earlier in this session): zero of the five milestone sub-agents carry the `Memory bootstrap` heading + `<scope-bounds>` + `<untrusted-content-policy>` + JSON-contract trio that all four `/roadmap` sub-agents carry, and the command body lacks the matching "Sub-agent contract" / "Recovery" / "File-presence state model" scaffolding. The adversary-critique-template defines a per-finding format that **directly contradicts** `critique-format.md`'s canonical shape, which the dedupe-findings.py script then parses against - a triangle of incompatible truths. Token bloat is concentrated in agent-prompts.md (375 lines) which is a second copy of the five sub-agent bodies that the orchestrator never actually substitutes from. Finally, a long list of adopt-from-`/roadmap` agentic capabilities are missing: no `validate-state.py`, no first-unpopulated-phase resume detector, no `--resume` actually wired into the orchestrator body, no gate-required JSON contract, no Phase 0 phase advance to `research-running` before dispatch, no `implementation_path` ever written, no dependency-graph awareness when the milestone id comes from a `/roadmap` epic, and no `oss-scout` `not-applicable` status in the state schema even though the agent prompt instructs the agent to return it.

Total findings by severity: **3 CRITICAL, 12 HIGH, 18 MEDIUM, 11 LOW = 44 findings**.

Top 2 themes: (1) systematic absence of the `/roadmap` sub-agent contract pattern (memory bootstrap section, scope-bounds block, untrusted-content-policy block, JSON return contract) across all five milestone agents; (2) format inconsistency between `adversary-critique-template.md`, `critique-format.md`, and the regex in `dedupe-findings.py:39` - three sources, three different shapes.

---

## Axis 1 - Formatting that doesn't fit the repository

### CRITICAL findings

- **F1-C1 - Adversary critique template format collides with `critique-format.md`** at `.claude/references/milestone-pipeline/adversary-critique-template.md:37-46`
  - Observation: Template defines findings as `**C1 -- {Short title}** (CRITICAL)\nFile: \`{path}:{line}\`\nIssue: ...\nSuggested fix: ...\nRegression-guard test: ...`. The canonical `.claude/references/critique-format.md:32-38` (which `adversary-critique-skill.md:72-73` explicitly cites as the single source of truth) defines findings as `### <severity> — <short title>\n\n**Where:** \`<file>:<line>\`\n**Evidence:** ...\n**Why it matters:** ...\n**Suggested fix:** ...`. The two shapes are mutually exclusive. The adversary-critic agent's body (`.claude/agents/milestone-adversary-critic.md:105-111`) prescribes a THIRD shape that matches neither - `**{SEVERITY-ID} -- {Short title}** ({SEVERITY})` + four named fields with no `**` bolding on field names.
  - Reference convention: `.claude/references/critique-format.md` is shared with `/capability-scout` Phase 1 adversary scout and every Challenger sub-agent. Every other critique in this repo uses its `### CRITICAL — title` + `**Where:**`/`**Evidence:**`/`**Why it matters:**`/`**Suggested fix:**` shape (see `.claude/notes/frontend-uplifts/upl-2026q2/artifacts/final-report.md` for an existing instance).
  - Suggested remediation: Pick ONE shape and make all three files match. The pragmatic call is to keep the canonical `critique-format.md` shape and rewrite both `adversary-critique-template.md` and the per-finding skeleton in `milestone-adversary-critic.md:105-111`. The dedupe-findings.py regex must then be rewritten to match (see Axis 2 F2-C2).

### HIGH findings

- **F1-H1 - All five milestone sub-agents lack the `## Memory bootstrap` H2 section that all four `/roadmap` agents carry** at `.claude/agents/milestone-{researcher,implementer,adversary-critic,frontend-ux-critic,oss-scout}.md:7-10` (each file's intro paragraph)
  - Observation: Each milestone agent has its memory load instruction as a one-line paragraph immediately after the YAML frontmatter (e.g. `milestone-researcher.md:9`: "Before doing anything else, read `.claude/agent-memory/milestone-researcher/lessons.md` if it exists..."). `roadmap-refiner.md:9-11` carries a dedicated `## Memory bootstrap` H2 with explicit relevance gating ("Skip memory load if the content is unrelated to the current domain"). All four roadmap agents do this. None of the five milestone agents do.
  - Reference convention: `roadmap-refiner.md:9-11`, `roadmap-decomposer.md:9-11`, and `roadmap-sequencer.md` / `roadmap-materializer.md` all carry this section with identical phrasing and the explicit relevance check.
  - Suggested remediation: Promote each milestone agent's memory-load paragraph into a `## Memory bootstrap` H2 with the explicit "skip if unrelated" relevance gate. Place it at the top, before the inputs / role description, matching the roadmap-refiner shape exactly.

- **F1-H2 - All five milestone sub-agents lack the canonical JSON return contract used by every `/roadmap` agent** at end of each milestone agent file
  - Observation: `milestone-researcher.md:76`, `milestone-implementer.md:70`, `milestone-adversary-critic.md:142`, `milestone-frontend-ux-critic.md:82`, `milestone-oss-scout.md:108` all end with prose like "Return a single message with the path to the critique, a 3-line summary..." with no JSON shape spelled out. `roadmap-refiner.md:192-201` (and every other roadmap agent) ends with `Return a single message containing ONLY this JSON object` followed by the literal `{"file_path": ..., "status": "complete | gate-required | aborted-scope", "summary": ..., "injection_attempts": 0}` shape.
  - Reference convention: The roadmap orchestrator's "Status routing table" (`commands/roadmap.md:227-241`) only works because each agent returns JSON. The milestone orchestrator has no equivalent because the milestone agents return prose.
  - Suggested remediation: Add the canonical four-key JSON contract to each milestone agent. Use the existing prose-return summary as the value of `summary`. Define a parallel status routing table in the command body (see Axis 4 F4-H1).

- **F1-H3 - Indentation of `[MUST]`/`[SHOULD]`/`[MIGHT]` style scope-bounds blocks does not match `/roadmap` convention** at `.claude/agents/milestone-researcher.md:67-74`, `milestone-implementer.md:61-68`, `milestone-adversary-critic.md:134-140`, `milestone-frontend-ux-critic.md:74-80`, `milestone-oss-scout.md:100-106`
  - Observation: The milestone agents do carry `<scope-bounds>` blocks but they are SHORTER and CONTENT-LIGHTER than the roadmap versions. Compare `milestone-researcher.md:67-74` (8 lines, 3 bullets) to `roadmap-refiner.md:160-178` (19 lines, ~10 bullets including the explicit ban list of `glab *`, `mcp__GitLab__*`, dispatching other slash commands, mutating `~/.claude/`, POSTing to non-loopback hosts).
  - Reference convention: `roadmap-refiner.md:160-178` ban list is the calibration. Each agent's block lists every external-write surface AND every cross-pipeline dispatch surface AND the specific files the agent is forbidden from writing.
  - Suggested remediation: Expand each milestone-agent scope-bounds block to mirror the roadmap-refiner block: name `glab *` and `mcp__GitLab__*` explicitly, ban dispatching other slash commands, ban mutating `~/.claude/`, ban POSTing to non-loopback hosts, and (this is the most useful AVC-specific addition) name the specific source files (`surfaces.py`, `app.py`, the four panel files, `styles.py`, `tests/`, `requirements.txt`) that the milestone agents are forbidden from writing.

- **F1-H4 - Command file mixes argument-hint frontmatter with a verbose Usage block that no other command has** at `.claude/commands/milestone-pipeline.md:3` (frontmatter) vs `.claude/commands/milestone-pipeline.md:15-23` (Usage block)
  - Observation: The frontmatter `argument-hint: "<id> [--brief \"...\"] [--single] [--deep] [--oss-scout] [--resume]"` is correct and matches `/roadmap`'s pattern (`commands/roadmap.md:3`). But then lines 15-23 reproduce essentially the same argument syntax with comments inside a fenced block. `/roadmap` does not duplicate this - it states the args once in the frontmatter and once via inline backtick references where each flag is first introduced (`commands/roadmap.md:12-15`).
  - Reference convention: `commands/roadmap.md:12-15` introduces each argument inline as a definition list, not in a `Usage:` fenced block.
  - Suggested remediation: Replace the `Usage:` fenced block (lines 15-23) with a definition-list-style introduction of each flag mirroring `roadmap.md:12-15`. Keeps frontmatter as the one source of truth.

- **F1-H5 - Phase reference files use ad-hoc `+--` ASCII tree art where `/roadmap` references use indentation only** at `.claude/references/milestone-pipeline/phase-implement.md:27-35`, `commands/milestone-pipeline.md:127-134`
  - Observation: The Inline-vs-Delegated decision uses `+-- YES -> Inline.` / `+-- NO  -> Delegated.`. This is the OSE reference's ASCII tree art (which used `├──`/`└──` Unicode in the reference repo and was hand-ASCIIfied here). Neither `/roadmap`'s phase references nor `/capability-scout`'s use this pattern - they use either a Markdown table or an `if/else` prose pattern.
  - Reference convention: `commands/roadmap.md:124-127` uses a `| status | Action |` table to encode the same kind of two-branch decision.
  - Suggested remediation: Replace each `+-- YES / +-- NO` block with a 2-row Markdown table or with a short `if/else` prose decision. Easier to scan and consistent with the rest of `.claude/references/`.

### MEDIUM findings

- **F1-M1 - `/milestone-pipeline` slash command title uses double-dash separator; `/roadmap` uses em-dash-with-space** at `commands/milestone-pipeline.md:6` (`# /milestone-pipeline -- 4-phase milestone build pipeline`)
  - Observation: Milestone uses `-- 4-phase...`; roadmap uses `— 4-phase...` (em-dash). Capability-scout and frontend-uplift use `/<id>` then a newline-separated tagline.
  - Reference convention: `commands/roadmap.md:6` = `# /roadmap — 4-phase roadmap pipeline`.
  - Suggested remediation: Unify on the em-dash. The decision matters because the title is shown verbatim in slash-command pickers.

- **F1-M2 - Inconsistent dash convention across milestone-pipeline files** (sample: `commands/milestone-pipeline.md:43,45,109,153` use `--` while `phase-research.md` and the agent prompts use mixed)
  - Observation: Some files use `--` (ASCII double dash, e.g. command line 43 `Trivial single-file edit -- just make the change directly`); others use UTF-8 em-dash. The port appears to have ASCIIfied selectively from the OSE reference, leaving mixed conventions.
  - Reference convention: `/roadmap` consistently uses em-dash `—` in prose.
  - Suggested remediation: Pick one. The previous slash-command ports kept em-dash. Run a `grep -n "--"` sweep across milestone-pipeline files and unify.

- **F1-M3 - Memory file naming "lessons.md" vs no anti-patterns.md** at `.claude/agent-memory/milestone-*/`
  - Observation: Every milestone agent body instructs the agent to "ALSO update `anti-patterns.md` if you discovered a recurring anti-pattern" but no anti-patterns.md file is pre-created. Each lessons.md is a 1-line empty stub. Compare roadmap agents which also have empty lessons stubs but no anti-patterns instruction.
  - Reference convention: `roadmap-refiner.md:153-156` lists ONE focus: lessons.md only. No anti-patterns.md surface.
  - Suggested remediation: Either pre-create `anti-patterns.md` stubs alongside `lessons.md` so the agent doesn't need to also `mkdir -p` parent (already exists), OR remove the anti-patterns mention from the agent body and consolidate everything into `lessons.md`. The latter is simpler.

- **F1-M4 - Phase ref `phase-research.md` heading depth differs from `/roadmap` phase refs** at `phase-research.md:1` (`# Phase 1 -- Research`)
  - Observation: Milestone phase refs use `# Phase N -- Title` (top-level). Roadmap phase refs use `# Phase N: <title>` (colon, not double-dash). Visible at `.claude/references/roadmap/phase-refine.md:1` (canonical comparison point).
  - Reference convention: Roadmap uses `# Phase 1: REFINE` shape.
  - Suggested remediation: Unify on the colon-form. Mechanical sed across the four `phase-*.md` files.

- **F1-M5 - Command body's "Step 0" section uses different heading shape than `/roadmap`** at `commands/milestone-pipeline.md:48` (`## Step 0 -- Initialize state`)
  - Observation: Milestone uses `## Step 0 -- Initialize state`. Roadmap uses `## Step 0 — Initialize` (em-dash, single noun). Minor visual drift.
  - Reference convention: `commands/roadmap.md:48`.
  - Suggested remediation: Use em-dash + the shorter "Initialize" noun phrase.

- **F1-M6 - `/milestone-pipeline` carries no `argument-hint` validation for the `--brief` whitespace-only case** at `init-state.sh:31-43`
  - Observation: `init-state.sh` accepts `--brief ""` and `--brief "   "` and writes whitespace as the brief. Compare `roadmap`'s `init-roadmap.sh` which has explicit slug validation but does NOT validate brief content. Marking MEDIUM because empty-brief is a real bug class (status.sh reports `(empty -- pass --brief to populate)` only when literal empty, not when whitespace).
  - Reference convention: N/A - same gap exists in `/roadmap`.
  - Suggested remediation: Strip whitespace from `--brief` before assignment in `init-state.sh:34-36`. Cheap fix.

- **F1-M7 - Final-summary line count inconsistent with command body** at `commands/milestone-pipeline.md:285` ("Print a 5-line final summary") vs `phase-resolve.md:119` ("Print a final 5-line summary")
  - Observation: Both say 5 lines but the example structure in `phase-resolve.md:119` lists 4 elements (id, total, fixed/deferred, critique link, rect commit = 5 elements but the example shape suggests 4 lines). Not technically wrong, but the 5-line target is fuzzy.
  - Reference convention: None (this is new territory).
  - Suggested remediation: Either spell out the 5 lines explicitly (one per element) or relax the constraint to "5-line max final summary".

### LOW findings

- **F1-L1 - State schema example uses today's date** at `state-schema.md:34-43`
  - Observation: Example state shows `created_at: 2026-05-20T14:32:00Z`. Coincidence with today but reads like a stale paste.
  - Suggested remediation: Use the same anchor date used elsewhere in `.claude/references/` (most other examples use 2026-03 / 2026-04 ranges).

- **F1-L2 - `dedupe-findings.py:39` regex comment claims to accept em-dash but the per-finding template only uses double-dash** at `dedupe-findings.py:39-42`
  - Observation: `FINDING_RE` accepts `[—\-]` to match both em-dash and ASCII dash. But `adversary-critique-template.md:37,43` only writes the double-dash form. The regex is defensive against a format the template never emits.
  - Suggested remediation: Either trim the regex to just `\-` OR update the template to use em-dash and let the regex stand.

- **F1-L3 - Step 0's `mkdir -p` block duplicates what init-state.sh already does** at `commands/milestone-pipeline.md:52-57`
  - Observation: Step 0 instructs the orchestrator to `mkdir -p .claude/agent-memory/milestone-{five names}/`. But these directories already exist (the lessons.md files were created at port time). The mkdir is harmless but unnecessary.
  - Suggested remediation: Either delete the mkdir block, or move it INTO init-state.sh so the command body stays minimal.

---

## Axis 2 - Errors or bugs

### CRITICAL findings

- **F2-C1 - `checkpoint.py:108` collapses `None` and empty-string to the same output - breaks the Phase 3 bash guard** at `checkpoint.py:107-110`
  - Observation: `get_field` prints empty string when `val is None`. The orchestrator's Phase 3 detect runs `BASE=$(... checkpoint.py <ID> --get implementation_base)` and then `if [[ -z "$BASE" ]]`. When the field is literally unset (NULL), `$BASE` is empty - guard catches it correctly. But when the field IS set to empty string (e.g. a user accidentally passes `--set implementation_base=""`), `$BASE` is ALSO empty - same guard catches it and the orchestrator silently aborts Phase 3. Distinguishing these two cases would matter for diagnosis ("not yet set" vs "explicitly empty - bug upstream").
  - Reference convention: N/A - this is a genuine bug introduced in the port (the OSE reference has the same shape but the OSE Phase 3 frontend-detect was a simpler `grep -q '^frontend/'` - the AVC port made the guard tighter, exposing this collision).
  - Suggested remediation: When `val is None`, print to stderr instead of stdout, OR exit non-zero with a clear "field never set" message. The Phase 3 guard then catches "never set" via exit code, and only treats actual empty-string as the data condition.

- **F2-C2 - `dedupe-findings.py:39` FINDING_RE will never match findings written in either the canonical `critique-format.md` shape OR the prose-style outputs of the actual milestone-frontend-ux-critic / milestone-oss-scout** at `dedupe-findings.py:39-42`
  - Observation: `FINDING_RE` matches `**{ID} -- {title}** ({SEV})` where `{ID}` is `[CHML]\d+`. But: (1) `critique-format.md:32` specifies `### CRITICAL — short title` with no `{ID}` prefix at all - those findings will never match. (2) The frontend-ux-critic body (`milestone-frontend-ux-critic.md:59`) only says "complete critique in the canonical AVC format" - if it follows critique-format.md, its findings will never match. (3) `dedupe-findings.py` is wired to run unconditionally at `commands/milestone-pipeline.md:213` after every multi-critic Phase 3 - the script will report 0 findings and exit 0, falsely succeeding on input that has 20+ findings.
  - Reference convention: The OSE reference (`adversary-critique` skill) used a different finding ID scheme. The port did not reconcile.
  - Suggested remediation: This is the same root cause as F1-C1. Fix the template format and the agent body format, AND rewrite FINDING_RE to match the chosen canonical shape. Best path: align everything to `critique-format.md` and rewrite the regex to match `^### (CRITICAL|HIGH|MEDIUM|LOW) — (.+)$` with the file:line extracted from `**Where:** \`...\`` on a subsequent line.

- **F2-C3 - Phase 1 dispatch starts implicit state = "init" but the script's first allowed transition is `init -> research-running`, which the command body advances AFTER the agents return (line 99) - all research time is logged as `init`** at `commands/milestone-pipeline.md:96-101`
  - Observation: Line 96: "When all researcher agents have returned, advance state". Lines 99-100: `checkpoint.py <ID> research-running` then `checkpoint.py <ID> research-complete`. This means while researchers are running, state.phase remains `init`. status.sh shows "Phase: init" through the entire 15-minute research wallclock. The `phase_history` then records `init -> research-running -> research-complete` all within seconds of each other after research is done. The wallclock-per-phase reporting in status.sh is therefore broken - "research-running" is recorded as taking 0 seconds.
  - Reference convention: The OSE reference repo's command body had the same shape (this is inherited, not introduced) but in the OSE repo the timing reporting was less load-bearing because OSE used worktree isolation that produced its own logs. In AVC, status.sh wallclock is the only timing signal.
  - Suggested remediation: Advance to `research-running` IMMEDIATELY before dispatch. The current "advance both back-to-back after return" pattern is logically the same as no checkpointing at all. Add `checkpoint.py <ID> research-running` at the top of Phase 1, before the dispatch instructions.

### HIGH findings

- **F2-H1 - `state.implementation_path` is declared in the schema and printed by status.sh but is NEVER set by any orchestrator instruction** at `commands/milestone-pipeline.md` (entire Phase 2 body) vs `init-state.sh:102` (declares None) vs `status.sh:93-94` (reads and prints)
  - Observation: `init-state.sh:102` initialises `implementation_path: None`. status.sh:93 reads it. The state-schema.md:50 example sets it to `"inline"`. But searching the command body and the phase refs for `--set implementation_path=` returns ZERO hits. The orchestrator never writes it. status.sh will always print nothing for this field.
  - Reference convention: N/A - this is a schema field with no writer.
  - Suggested remediation: Add `checkpoint.py <ID> --set implementation_path='"inline"'` (or `delegated`) inside the Inline vs Delegated decision in command body line 137 OR in `phase-implement.md`. Without this, the `implementation_path` field is dead.

- **F2-H2 - `state.implementation_commits` and `state.research_briefs` schema fields are also never written by the orchestrator body** at `init-state.sh:105` and `init-state.sh:101`
  - Observation: Same shape as F2-H1. `implementation_commits` is supposed to be the full list of commit shas in Phase 2's range; `research_briefs` is supposed to be the paths to written brief files. Neither has a `--set` or `--append` call in the command body or phase refs. Both stay `[]`.
  - Reference convention: N/A - schema gap.
  - Suggested remediation: After Phase 1 returns: `checkpoint.py <ID> --append research_briefs='".claude/notes/milestones/<ID>/research/agent-a-brief.md"'` per brief. After Phase 2: `git log --format=%H {BASE}..HEAD | xargs -I{} checkpoint.py <ID> --append implementation_commits='"{}"'` (or write a small helper). OR delete these fields from the schema as dead weight.

- **F2-H3 - `state.critique_finding_counts` declared in schema; never updated** at `init-state.sh:109`, `state-schema.md:57`, `status.sh:102-105`
  - Observation: Same shape as F2-H1/H2. status.sh tries to print finding counts if any value > 0 - because nothing ever sets them, the line never appears.
  - Reference convention: N/A.
  - Suggested remediation: After the critic returns and after dedupe-findings.py, the orchestrator must scan the critique markdown for severity counts and `--set critique_finding_counts='{"critical": N, "high": N, ...}'`. Or extract from the critic's return summary if it's structured (which would require F1-H2 fix - the JSON contract).

- **F2-H4 - `oss-scout` agent return contract says `status: not-applicable` (`milestone-oss-scout.md:30`) but `not-applicable` is not in the canonical status enum** at `milestone-oss-scout.md:30`
  - Observation: The agent prompt instructs returning `status: not-applicable`. No other milestone agent's body documents the status enum, and there is no "Sub-agent contract" section in the command body that defines the allowed statuses. The roadmap canonical enum is `complete | gate-required | aborted-scope`. `not-applicable` is a NEW status with no orchestrator handler.
  - Reference convention: `commands/roadmap.md:213-221` defines the canonical 3-status enum.
  - Suggested remediation: Either add `not-applicable` to the canonical enum AND document a handler in the command body (similar to how the gate-required handler is documented), OR change the oss-scout agent to return `status: complete` with a one-line summary noting the no-scope outcome.

- **F2-H5 - Bash heredoc in `init-state.sh:89-120` injects Python that depends on shell argv quoting; on cmd.exe / Git-Bash for Windows the heredoc body opens fine but `r'$STATE'` only works because $STATE doesn't contain a single quote** at `init-state.sh:80`
  - Observation: Line 80: `PHASE=$("$PY" -c "import json; print(json.load(open(r'$STATE'))['phase'])")`. The Python raw string `r'...'` cannot escape an internal single quote. If `$STATE` ever contains a single quote (it won't, given the ID validation regex), the Python raises SyntaxError. The validation regex at line 47 blocks IDs containing single quotes, so this is technically safe today.
  - Reference convention: N/A - defensive concern.
  - Suggested remediation: Pass `$STATE` as argv to a here-doc Python block instead of interpolating into source: `"$PY" - "$STATE" <<'PY'` followed by `import json, sys; print(json.load(open(sys.argv[1]))['phase'])`. Matches the pattern at lines 89-120. Belt-and-suspenders for any future regex loosening.

- **F2-H6 - Frontend-detect grep at `commands/milestone-pipeline.md:189` does NOT match files in subdirectories - only at repo root, which is correct for this repo but not documented as a constraint** at `commands/milestone-pipeline.md:189`
  - Observation: `git diff --name-only ${BASE}..HEAD | grep -E '^(appearance_panel|view_panel|parameters_panel|styles|app)\.py$'`. Anchored to start `^` and ends `$`. If the panel files ever move into a subdir (`ui/appearance_panel.py`), this grep silently returns false. The constraint is undocumented.
  - Reference convention: N/A - the OSE reference used `grep -q '^frontend/'` (a directory match).
  - Suggested remediation: Either widen to `(^|/)(appearance_panel|view_panel|...)\.py$` for forward-compat with directory moves, OR add a code comment in `phase-critique.md` noting "this assumes panel files are at repo root - update if AI-1 ever lifts that".

- **F2-H7 - Phase 3 fan-out check for `--oss-scout` uses inconsistent variable name vs the argument flag** at `commands/milestone-pipeline.md:204` and `phase-critique.md:64-69`
  - Observation: The command body argument is `--oss-scout` (kebab). The phase ref says "If the user supplied `--oss-scout`" which matches. But there's no shell variable set during arg-parsing that the command body documents. The arg-parsing for `--single`, `--deep`, `--oss-scout`, `--resume` is left entirely implicit; the orchestrator is presumed to "remember" what flags were passed.
  - Reference convention: `commands/roadmap.md:62-64` explicitly defines `GH_ISSUES_FLAG=true|false` as a derived variable.
  - Suggested remediation: Add a "Step 0.5 - Parse args and persist into state" instruction that writes `state.research_mode` (single/standard/deep) and a new `state.oss_scout_requested` (boolean) from the arg parse. Then Phase 3 reads from state instead of remembering the original argv. This is also load-bearing for `--resume` (see Axis 4 F4-C1).

- **F2-H8 - `phase-implement.md:54` instructs `Run scripts/checkpoint.py {ID} implement-complete` without the `.venv/Scripts/python.exe` prefix used everywhere else** at `phase-implement.md:54`
  - Observation: Inconsistent with the rest of the document (line 81 has the full `.venv/Scripts/python.exe` prefix). Will fail on Windows where `scripts/checkpoint.py` is not directly executable.
  - Reference convention: `phase-implement.md:81` is the right form.
  - Suggested remediation: Fix line 54 to match line 81.

### MEDIUM findings

- **F2-M1 - `init-state.sh:123` byte counting via `wc -c | tr -d ' '` includes the trailing newline from echo** at `init-state.sh:123`
  - Observation: `BRIEF_NOTE="set ($(echo "$BRIEF" | wc -c | tr -d ' ') chars)"`. `echo` adds a trailing newline before `wc -c` counts it, so a brief of "abc" reports `4 chars`. Off-by-one but harmless.
  - Suggested remediation: Use `echo -n` or `printf '%s' "$BRIEF" | wc -c`.

- **F2-M2 - `dedupe-findings.py:104` and `:122` write file with UTF-8 but the script regex at line 39 includes em-dash which only matches if input is read as UTF-8 - the read at line 104 IS UTF-8 so this is OK; but a hand-edit on Windows could clobber the encoding and break the regex silently** at `dedupe-findings.py:39,104`
  - Observation: Defensive note. The regex includes literal `—`. If the file ever gets saved as cp1252, the em-dash becomes the cp1252 byte sequence and the regex no longer matches.
  - Suggested remediation: Use the Unicode escape `—` instead of literal `—` in the regex. Decouples regex correctness from file encoding.

- **F2-M3 - `checkpoint.py:71` writes `.json.tmp` and renames; `init-state.sh:116` writes `.tmp` and renames. Different temp suffix conventions** at `checkpoint.py:71` and `init-state.sh:116`
  - Observation: Doesn't matter functionally but is a stylistic gap. Could cause issues if a `.json.tmp` left over by a crash mid-checkpoint coexists with a new `.tmp` from init-state.sh.
  - Suggested remediation: Pick one suffix (`.json.tmp` is clearer) and use everywhere.

- **F2-M4 - `phase-resolve.md:39` example sets invalidated_findings to `'["H3"]'` but this only works if no prior invalidations exist - calling `--set` REPLACES the field; an `--append` pattern would be safer** at `phase-resolve.md:39`
  - Observation: The orchestrator is supposed to set invalidations one at a time during re-verification. Using `--set` overwrites prior invalidations. The correct call is `--append invalidated_findings='"H3"'`. Same shape issue affects `fixed_findings` and `deferred_findings`.
  - Suggested remediation: Switch the examples in phase-resolve.md and the command body (line 246) to `--append`. The `--append` operator already exists at `checkpoint.py:132-150`.

- **F2-M5 - `milestone-implementer.md:42` quotes the wrong branch name pattern for "single-implementer dispatch (default)"** at `milestone-implementer.md:42`
  - Observation: Implementer body says "the slash command gave you a branch name (`impl-{ID}-solo` / `impl-{ID}-a` / `impl-{ID}-b`)". This is correct for single OR two-implementer cases. But the related convention at `phase-implement.md:69` says exactly the same - so it's just repeated. Not strictly wrong, but the implementer body should not need to recapitulate the dispatch matrix.
  - Suggested remediation: Trim implementer body to "commit to whichever branch the orchestrator told you to use" without trying to enumerate possible branch names.

- **F2-M6 - `checkpoint.py:114-128` (`set_field`) catches `json.JSONDecodeError` and falls back to treating `raw` as a plain string. But this means `--set field=true` sets the boolean, and `--set field=True` (Python-cased) sets the string. Easy footgun.** at `checkpoint.py:118-121`
  - Observation: `json.loads("true")` => `True`; `json.loads("True")` raises and falls back to literal string `"True"`. Surface for confusion.
  - Suggested remediation: Document the JSON expectation explicitly in the script doc, OR be stricter (require quoted strings always).

- **F2-M7 - `status.sh:88` formats elapsed time as `+%2dm` for >=1 minute and `+%2ds` for <1 minute - boundary at 60s shows "60s" rather than "1m"** at `status.sh:82-85`
  - Observation: Logic: if `mins > 0` show minutes; else show seconds. So 59s shows "+59s", 60s shows "+ 1m", 119s shows "+ 1m". Slightly jarring transition. Not a bug.
  - Suggested remediation: Either show hours:minutes:seconds always, or accept the boundary.

- **F2-M8 - `phase-implement.md:31` references "new mesh helper class" as a non-trivial scaffolding signal but doesn't define what counts** at `phase-implement.md:31`
  - Observation: Inline-vs-Delegated decision uses "no novel-pipeline scaffolding (e.g. introducing a new mesh helper class)" as one of the three AND conditions. Vague.
  - Suggested remediation: Replace with a measurable signal like "no new file in `surfaces.py` outer scope (helper or generator), OR no new function added to `app.py` `MainWindow` class".

- **F2-M9 - `init-state.sh:45-51` allows IDs that include `--` (e.g. `panel-refresh--bad-e1`) which is not an epic-id shape** at `init-state.sh:47`
  - Observation: Regex `^[a-zA-Z][a-zA-Z0-9-]{0,59}$` permits double-dashes. The validate-roadmap.py epic id regex is `^[a-z][a-z0-9-]*-e\d+[a-z]?$` (single source of truth). The milestone-pipeline's id regex is intentionally LOOSER (epics from `/roadmap` are subset). But the looser regex allows obviously-bad ids like `a--b` or `e--1`.
  - Suggested remediation: Tighten to `^[a-zA-Z][a-zA-Z0-9](?:-[a-zA-Z0-9]+)*$` (no double-dashes, no trailing dash) for safety.

### LOW findings

- **F2-L1 - `commands/milestone-pipeline.md:189` POSIX `grep -E` works fine on Git-Bash for Windows but the surrounding code uses `[[ -z "$BASE" ]]` bash-isms; in a pure-cmd.exe shell neither works** at `commands/milestone-pipeline.md:189`
  - Observation: Defensive concern. The orchestrator runs commands via Bash tool which uses Git-Bash, so this is fine in practice.
  - Suggested remediation: None - already correct for this repo's environment.

- **F2-L2 - `checkpoint.py:60` uses `parents[3]` but the OSE reference used `parents[4]` - the port shift is correct (one fewer level since the script lives at `.claude/scripts/milestone-pipeline/` instead of `.claude/skills/milestone-pipeline/scripts/`) but uncommented** at `checkpoint.py:60`
  - Observation: Verified: file path is `.claude/scripts/milestone-pipeline/checkpoint.py`, so parents are `[milestone-pipeline, scripts, .claude, <repo-root>]` => index 3. Correct.
  - Suggested remediation: Add a comment explaining the 3 vs 4 - it will save the next reader 30 seconds.

- **F2-L3 - `phase-implement.md:142` example shows commit subject `feat(panel-refresh-2026q2-e1): lift Enriques sawtooth via second Taubin pass` but the slash command description says ids look like `panel-refresh-2026q2-e2`** at `phase-implement.md:131-134`
  - Observation: Just example drift. `e1` vs `e2` from the command body description.
  - Suggested remediation: Unify on one example id everywhere or vary intentionally.

---

## Axis 3 - Token bloat

### HIGH findings

- **F3-H1 - `agent-prompts.md` (375 lines) duplicates 80%+ of the content of each milestone agent body, but the command body never instructs "substitute from agent-prompts.md" for adversary-critic** at `agent-prompts.md` (entire file) vs `milestone-adversary-critic.md:13-122`
  - Observation: The command body says "Read agent-prompts.md and extract the Researcher prompt block verbatim" (line 75) ONLY for Phase 1 researcher. For frontend-ux-critic (line 201) it says "Read the Frontend-UX-Critic prompt from agent-prompts.md". For oss-scout (line 205) same. But for adversary-critic (line 197-198) it just says "dispatch milestone-adversary-critic sub-agent" - no agent-prompts.md instruction. So the adversary-critic prompt in agent-prompts.md is INERT - it's never substituted. Yet it occupies ~50 lines of the 375.
  - Reference convention: `roadmap` has no `agent-prompts.md` - each sub-agent's body IS the prompt; the orchestrator just dispatches by name. That's the simpler model.
  - Suggested remediation: Two paths. (A) Delete `agent-prompts.md` entirely and rely on the sub-agent bodies as the source of truth. The orchestrator dispatches by name; `{ID}` / `{MILESTONE_BRIEF}` / `{COMMIT_RANGE}` substitution happens because the agent body has those placeholders and the orchestrator's dispatch instruction sets them via tool params. (B) Keep `agent-prompts.md` but make ALL agent dispatches go through it (including adversary-critic). Drop the duplication in the agent bodies. Path A matches the `/roadmap` model and is preferred.

- **F3-H2 - `milestone-adversary-critic.md:42-78` reproduces the 10-axis checklist that `.claude/references/milestone-pipeline/adversary-critique-checklist.md` is supposed to be the single source of truth for** at `milestone-adversary-critic.md:42-78` vs `adversary-critique-checklist.md` (entire file)
  - Observation: The agent body lists axes 1-10 as inline section headers with specific checks per axis. The checklist file has the same axes with FULLER checks. The agent body explicitly references the checklist ("Walk the full checklist from adversary-critique-checklist.md before writing findings") AND then reproduces 36 lines of it.
  - Reference convention: `roadmap-decomposer.md:31-33` reads the phase-decompose.md reference and does NOT inline its content. Cleaner.
  - Suggested remediation: Delete lines 42-78 of `milestone-adversary-critic.md`. Replace with one paragraph: "Walk the 10-axis checklist from `.claude/references/milestone-pipeline/adversary-critique-checklist.md`. The axes are summarised at the top of that file in a table you can scan in 30 seconds, with full per-axis checks below."

### MEDIUM findings

- **F3-M1 - `phase-implement.md:99-118` reproduces the AI-N table that `app-invariants.md` is the canonical source for** at `phase-implement.md:99-118`
  - Observation: Phase 2 phase ref lists AI-1, AI-9, AI-10, AI-11, AI-12, AI-13 with one-line summaries. `app-invariants.md` has the canonical full descriptions. The summaries drift over time.
  - Reference convention: Other phase refs in this repo (e.g. `phase-research.md` line 51) say "AI-1..AI-15 conflicts" without inlining.
  - Suggested remediation: Replace with "Touching `appearance_panel.py`, `view_panel.py`, `parameters_panel.py`, `styles.py`, or `app.py`? Re-read AI-1, AI-9, AI-10, AI-11, AI-12, AI-13 in `.claude/references/app-invariants.md` before proceeding."

- **F3-M2 - `adversary-critique-checklist.md` has Anchor sections for each axis citing CONTEXT.md section 8 incidents** at `adversary-critique-checklist.md:35-40,58-64,84-88,107-112,132-137,156-162,184-188,206-211,228-233,256-259`
  - Observation: Each axis carries 5-10 lines of "Anchor (CONTEXT.md section 8.X)" example. These are useful for an outside reader but the agent that loaded `app-invariants.md` and `CONTEXT.md` already has this context. Could be trimmed to a single line citation per axis.
  - Reference convention: N/A.
  - Suggested remediation: Trim each Anchor to one citation line (`Anchor: CONTEXT.md section 8.5 -- _render_current re-entrancy bug`). Removes ~50 lines.

- **F3-M3 - `phase-research.md:33-40` reproduces the Source/Tool/Why table that `milestone-researcher.md:25-39` enumerates as text** at `phase-research.md:33-40` vs `milestone-researcher.md:25-39`
  - Observation: Two presentations of the same source list. Phase ref has a table; agent body has a numbered list. Either could be deleted.
  - Suggested remediation: Keep the table in the phase ref; delete lines 25-39 of the researcher body and replace with "See `phase-research.md`'s source table for the full list".

- **F3-M4 - Command body's "Common rationalizations (anti-pattern guard)" table at lines 302-316 reproduces 11 of 12 of the `/roadmap` anti-pattern table, with 1-2 milestone-specific additions** at `commands/milestone-pipeline.md:302-316`
  - Observation: Most of the table content is generic ("Skip research", "Fire researchers one at a time", "Skip checkpointing") and could live in a shared anti-patterns reference. Only "Qt-panel critic is overkill", "Lift CONTEXT.md section 9 non-goal X", and "Auto-push after Phase 4" are milestone-specific.
  - Reference convention: `/roadmap` has its anti-patterns in `.claude/references/roadmap/anti-patterns.md` and only cites a subset inline.
  - Suggested remediation: Create `.claude/references/milestone-pipeline/anti-patterns.md` and trim the inline table to the 3 milestone-specific rows + one pointer.

- **F3-M5 - `agent-prompts.md:1-10` carries a preamble that the orchestrator never reads (it reads each prompt block individually)** at `agent-prompts.md:1-10`
  - Observation: 10 lines of "Update here, NOT in the command body" meta-instruction. Useful for human maintainers, dead weight for the LLM orchestrator that loads this file at Phase 1.
  - Suggested remediation: Move preamble to a CONTRIBUTING note. Or trim to one sentence.

- **F3-M6 - Each milestone agent body ends with a near-identical 8-line "Memory update (mandatory)" block** at `milestone-researcher.md:80-89`, `milestone-implementer.md:74-83`, `milestone-adversary-critic.md:146-156`, `milestone-frontend-ux-critic.md:86-95`, `milestone-oss-scout.md:112-121`
  - Observation: Five copies of the same instruction with the agent-name swapped. Bullet 4 ("DO NOT log the full milestone brief or the critique contents") is repeated five times. ~50 lines of pure duplication.
  - Reference convention: The roadmap agents have the memory-append instructions in their Step 8 / final-step body, but the actual heredoc pattern is reproduced verbatim because each agent has a different lessons-content focus. Still less duplication than the milestone five-way clone.
  - Suggested remediation: Factor into `.claude/references/milestone-pipeline/memory-update-protocol.md` and cite by reference in each agent body with "Append to `.claude/agent-memory/<this-agent>/lessons.md` per `memory-update-protocol.md`."

- **F3-M7 - `state-schema.md:130-145` shows a sample status.sh output that duplicates the inline example in `commands/milestone-pipeline.md`** at `state-schema.md:130-145`
  - Observation: 15 lines of sample status output. Useful in isolation but the orchestrator never reads this file unless it's debugging.
  - Suggested remediation: Trim or move to a CONTRIBUTING note.

- **F3-M8 - `adversary-critique-template.md:5-9` carries a NOTE comment that is also implicitly explained by every other section header** at `adversary-critique-template.md:5-9`
  - Observation: HTML comment explaining what `{SUBJECT}`, `{SUBJECT_DETAIL}`, `{ISO_DATE}` mean. The placeholders are self-documenting in context.
  - Suggested remediation: Delete the comment block. Saves 5 lines + a foot-gun (the comment says "Remove these comments in the final output" but the agent might forget).

- **F3-M9 - `phase-resolve.md:64-72` reproduces the Bug-location-to-Test-location table that should live in CONTEXT.md or a tests reference** at `phase-resolve.md:64-72`
  - Observation: 7-row table mapping bug location to test file. Useful but reproduced here only; if a new test file is added, this drifts.
  - Suggested remediation: Move to `.claude/references/app-invariants.md` AI-2 (tests) section, or to a new `.claude/references/test-conventions.md`.

### LOW findings

- **F3-L1 - `commands/milestone-pipeline.md:319-327` "Don'ts" section duplicates the Don'ts in `phase-resolve.md:144-152`** at `commands/milestone-pipeline.md:319-327` vs `phase-resolve.md:144-152`
  - Observation: Some overlap, especially around "Don't push", "Don't bypass init-state.sh", "Don't run Phase 4 as a sub-agent".
  - Suggested remediation: Pick one. Command body should be load-bearing; phase ref should be deep-dive.

- **F3-L2 - `agent-prompts.md` lines 145-220 (Frontend-UX-Critic prompt) ENTIRELY duplicates `milestone-frontend-ux-critic.md:13-83`** at `agent-prompts.md:145-220` vs `milestone-frontend-ux-critic.md:13-83`
  - Observation: This is the most extreme case of F3-H1.
  - Suggested remediation: Covered by F3-H1.

- **F3-L3 - Each agent body opens with "Before doing anything else, read `.claude/agent-memory/<agent>/lessons.md`" - 5 copies of identical phrasing** at all 5 milestone-*.md files
  - Observation: Covered by F1-H1 (the memory bootstrap pattern). If F1-H1 is fixed by promoting to a `## Memory bootstrap` section, this duplication remains - but at least it's structurally signalled.

---

## Axis 4 - Missing agentic capabilities

### CRITICAL findings

- **F4-C1 - `--resume` flag is documented in the command body and frontmatter but has no implementation path - the orchestrator never reads which phase to enter** at `commands/milestone-pipeline.md:3,22,59-60`
  - Observation: Frontmatter declares `[--resume]`. Line 22: "`/milestone-pipeline <id> --resume   # resume from current state`". Line 59: "If `state.json` already exists, the script prints `state already exists (phase=X) -- resuming`." Line 60: "If resuming: run status first, then skip to the appropriate phase below." But NO instruction tells the orchestrator HOW to map `phase=X` to a phase entrypoint. Compare `/roadmap`'s File-presence state model (`commands/roadmap.md:152-170`) which has both a marker-presence table AND a validator script (`validate-roadmap.py --report-first-unpopulated`). The milestone-pipeline has neither.
  - Reference convention: `commands/roadmap.md:152-170` is the calibration.
  - Suggested remediation: Add a "File-presence state model" / "State machine resume table" section to the command body that maps each `state.phase` value to "skip to Phase N step Y". Add a validator script (see F4-H1).

- **F4-C2 - No `validate-state.py` analogue to `validate-roadmap.py` - cannot programmatically determine the correct resume entry without reading state.json by hand** at `.claude/scripts/milestone-pipeline/` (entire directory)
  - Observation: `/roadmap` ships `.claude/scripts/roadmap/validate-roadmap.py` (with `--report-first-unpopulated` flag). `/milestone-pipeline` ships only init-state.sh, checkpoint.py, status.sh, dedupe-findings.py. No validator. status.sh comes close (it prints "Next phase: research-running") but it's bash + prose - not machine-readable for orchestrator routing.
  - Reference convention: `commands/roadmap.md:167` uses `validate-roadmap.py <slug> --report-first-unpopulated` for resume routing.
  - Suggested remediation: Add `.claude/scripts/milestone-pipeline/validate-state.py` that takes `<ID>` and a `--report-next-phase` flag and prints the canonical Phase N step Y entrypoint string the orchestrator should jump to.

### HIGH findings

- **F4-H1 - No "Sub-agent contract" section in the command body parallel to `commands/roadmap.md:211-241`** at `commands/milestone-pipeline.md` (missing)
  - Observation: `/roadmap` has a 30-line "Sub-agent contract" section that defines: (1) the JSON return shape, (2) the status routing table for each agent+status combination, (3) what the orchestrator does on each path. `/milestone-pipeline` has none of this. The orchestrator's behaviour after each sub-agent returns is implied by prose in each Phase section, not formalised.
  - Reference convention: `commands/roadmap.md:211-241`.
  - Suggested remediation: Add a "Sub-agent contract" section with the 4-key JSON return shape (file_path, status, summary, injection_attempts) and a status routing table for every {agent, status} pair (researcher.complete, researcher.aborted-scope, implementer.complete, implementer.scope-exceeded, adversary-critic.complete, frontend-ux-critic.complete, frontend-ux-critic.no-changes, oss-scout.complete, oss-scout.not-applicable).

- **F4-H2 - No `gate-required` mechanism for milestone agents - they cannot pause the pipeline for user input** at all 5 agent bodies + command body
  - Observation: `/roadmap` agents return `status: gate-required` when there are 2+ credible HMW reframings (refiner), Must/Should cut-line conflicts (sequencer), validator failures (materializer). The command body has handlers that surface the gate question and re-dispatch. `/milestone-pipeline` has no gate-required path - researchers either complete or fail; implementers either finish or "abort" via the scope-exceeded file (a side channel, not a status). Critic and rectifier have no pause path at all.
  - Reference convention: `commands/roadmap.md:227-241`.
  - Suggested remediation: Define gate cases per agent: (a) researcher: 2+ credible "Recommended approach" branches with no priority signal; (b) implementer (delegated): merge conflict between explorer branches; (c) rectifier: >40% invalidation rate (the meta-issue flagged in phase-resolve.md:43); (d) any agent: AI-1..AI-15 violation that requires user lift. Wire to JSON status return.

- **F4-H3 - No `--report-first-unset-field` or `--get-phase` machine-readable interface on checkpoint.py for resume routing** at `checkpoint.py` (missing flag)
  - Observation: `checkpoint.py --get phase` works but returns just the phase name. The orchestrator then has to embed the phase-to-step mapping in its own logic. A `checkpoint.py --next-step` that returns "phase-1-step-2" or similar would be load-bearing for resume.
  - Suggested remediation: Add `--next-step` flag (or roll into the F4-C2 validate-state.py).

- **F4-H4 - No retry policy for transient sub-agent failures** at `commands/milestone-pipeline.md` (entire body)
  - Observation: WebSearch / WebFetch are flaky. arXiv occasionally returns 503. If milestone-researcher fails mid-flight, the command body has no retry instruction. The orchestrator either re-dispatches manually or fails the whole pipeline. `/roadmap`'s gate-required mechanism handles this implicitly (the orchestrator can re-dispatch with `--user-resolution`); `/milestone-pipeline` has nothing equivalent.
  - Suggested remediation: Add a "Transient failure handling" sub-section to the Phase 1 and Phase 3 fan-out: "If a researcher or critic returns with no output file, re-dispatch ONCE before failing the phase."

- **F4-H5 - No phase wall-clock budget enforcement - status.sh reports elapsed time but no orchestrator instruction acts on it** at `phase-research.md:72` ("Soft cap 15 min, hard cap 30 min") vs command body (no enforcement)
  - Observation: Phase ref defines budgets ("Soft cap 15 min, hard cap 30 min"). Command body never reads status.sh or checks elapsed time. A hung sub-agent runs forever.
  - Suggested remediation: Add "After dispatching agents, the orchestrator polls status.sh every 5 minutes. If a phase exceeds its hard cap, the orchestrator surfaces a 'phase budget exceeded - continue / abort?' gate to the user."

- **F4-H6 - No dependency-graph awareness when milestone id comes from a `/roadmap` epic** at `commands/milestone-pipeline.md:25-29`
  - Observation: The command body acknowledges epic-shaped ids from `/roadmap` (`<slug>-eN`) but never reads the upstream `plans/<slug>-roadmap.md` to find dependencies. If `panel-refresh-2026q2-e3` depends on `e1` and `e2` (per the roadmap's DAG section), the milestone-pipeline doesn't check whether the dependencies are `complete`. The user could accidentally run e3 before e1.
  - Reference convention: `/roadmap`'s validate-roadmap.py S007 enforces DAG correctness at roadmap-write time. The milestone-pipeline is the consumer; it should enforce DAG ordering at execute time.
  - Suggested remediation: Add a "Step 0.7 - Verify dependencies" instruction: parse the roadmap doc for the milestone's epic-id, list its dependencies, and assert each dependency milestone has `state.phase == "complete"` in `.claude/notes/milestones/<dep-id>/state.json`. If any dep is not complete, surface a gate-required to the user.

- **F4-H7 - No observability - dispatched sub-agents have no run-id, no logs directory, no way for the user to see what's in flight** at all agents + command body
  - Observation: `/capability-scout` and `/frontend-uplift` ALSO lack this, so it's a repo-wide gap. But for milestone-pipeline (which has 4+ phases, 2+ parallel dispatches, can run 30+ minutes), observability is more load-bearing.
  - Suggested remediation: At each dispatch, write a one-line entry to `.claude/notes/milestones/<ID>/dispatch.log`: `2026-05-20T15:32:00Z | milestone-researcher | agent-a | dispatched`. On return, write `... | returned | <duration>`. The user can `tail -f` it.

### MEDIUM findings

- **F4-M1 - No find-count surfacing to the user mid-pipeline** at command body (missing)
  - Observation: status.sh's Findings line is great for ad-hoc inspection, but the orchestrator never says "Phase 3 found 2 HIGH and 4 MEDIUM - proceeding to Phase 4". The user only learns counts when they manually run status.sh.
  - Suggested remediation: After Phase 3 dedup, the orchestrator should grep the critique markdown for severity counts and surface them inline in the message before advancing to Phase 4.

- **F4-M2 - No "dispatch rationale" logging for the Inline vs Delegated decision** at `phase-implement.md:27-35`
  - Observation: The orchestrator picks Inline or Delegated based on a 3-condition AND. Whichever it picks, no record of the reasoning is written. If the rectifier or a future agent wants to know why Inline was chosen, they have to re-derive.
  - Suggested remediation: After deciding, write a one-line rationale to `state.implementation_path` AND `state.implementation_path_rationale` (new field). E.g. `inline | merged plan 320 LOC across 4 files, no novel scaffolding`.

- **F4-M3 - No structured-output contract for the rectification commit** at `commands/milestone-pipeline.md:268-281`
  - Observation: Rectification commit subject and body shape are described in prose. The next-milestone research phase has no programmatic way to read "what was fixed in C1" without parsing the prose commit body.
  - Suggested remediation: Either standardise the commit body shape and add a `extract-rect-commit.py` helper, OR write a JSON file at `.claude/notes/milestones/<ID>/artifacts/rectification.json` with `{fixed, deferred, invalidated, regression_tests_added}`.

- **F4-M4 - No memory-bootstrap "relevance gate" in milestone agents** at all 5 agent bodies
  - Observation: The roadmap-refiner body explicitly says "Skip memory load if the content is unrelated to the current domain - do not load memory for its own sake" (`roadmap-refiner.md:11`). The milestone agents just say "read it if it exists". For a critic that has accumulated 200+ lessons over time, blind-loading wastes tokens.
  - Suggested remediation: Add the relevance gate to each milestone agent's memory-bootstrap section. Covered by F1-H1.

- **F4-M5 - No `injection_attempts` counter exposed in any milestone agent's return** at all 5 agent bodies
  - Observation: The roadmap agents return `"injection_attempts": 0` as part of their JSON contract (`roadmap-refiner.md:198`). The milestone agents have an `<untrusted-content-policy>` block but no observable counter. If an agent encounters an injection attempt, the orchestrator never knows.
  - Suggested remediation: Tied to F1-H2 (JSON contract). When that fix lands, include `injection_attempts`.

- **F4-M6 - No checkpoint for "implementation-plan-written"** - the inline-path implementation-plan.md is mentioned but never recorded in state at `phase-implement.md:50`
  - Observation: Inline path step 2: "Write a 5-bullet plan to `.claude/notes/milestones/{ID}/artifacts/implementation-plan.md`". This file becomes the rectifier's reference for "what was the original intent". But state.json never records its path or its existence.
  - Suggested remediation: Add a `state.implementation_plan` field set during Phase 2.

- **F4-M7 - No "abort-and-cleanup" path** at command body (missing)
  - Observation: If a user starts `/milestone-pipeline foo-e1` and decides to abandon it mid-Phase-2, there's no documented way to remove state. The next invocation will detect existing state and resume. Manual `rm -rf .claude/notes/milestones/foo-e1` is the only path.
  - Suggested remediation: Add a `/milestone-pipeline <id> --abort` flag OR document the manual cleanup procedure.

- **F4-M8 - No "compaction" support for memory files** at all 5 agent bodies
  - Observation: `roadmap-refiner.md:151` instructs "If the file would exceed 200 lines, COMPACT existing entries (merge similar lessons, drop redundancies) BEFORE appending." The milestone agents have no compaction instruction. After 50 milestones, lessons.md will be a 500-line wall of one-line entries.
  - Suggested remediation: Copy the compaction instruction from roadmap-refiner.md:151 into each milestone agent's memory-update section.

- **F4-M9 - No reference to a `.claude/references/milestone-pipeline/avc-integration.md` (analogue to `.claude/references/roadmap/avc-integration.md`)** at `commands/milestone-pipeline.md` (missing)
  - Observation: `/roadmap` has `.claude/references/roadmap/avc-integration.md` which encodes repo identity, where roadmaps live, AI-1..AI-15 summary, and CONTEXT.md handoff. `/milestone-pipeline` has no equivalent. Every milestone agent re-derives this context from `CONTEXT.md` + `app-invariants.md` at runtime. Slow + drift-prone.
  - Suggested remediation: Create `.claude/references/milestone-pipeline/avc-integration.md` mirroring the roadmap version, and have each milestone agent read it first.

- **F4-M10 - No hook integration** at `.claude/settings.local.json` and at `.claude/hooks/` (missing)
  - Observation: The reference repo (OSE) has `.claude/hooks/` for git-policy enforcement (no-push-from-sub-agent, etc.). AVC has no hooks directory and no `settings.local.json` hook configs for milestone-pipeline. The external-write boundary is enforced by doc only.
  - Reference convention: `commands/roadmap.md:194-207` documents the external-write boundary as doc-enforced for the same reason.
  - Suggested remediation: Document the gap (already done at commands/roadmap.md:207); plan a hook-level enforcement layer in a follow-up milestone. NOT a blocker for the port - but worth flagging.

### LOW findings

- **F4-L1 - status.sh prints "Next phase: research-running (run Phase 1 of milestone-pipeline)" - actionable, but doesn't give a copy-paste command** at `status.sh:119-130`
  - Observation: Prose vs command. The user has to mentally translate "run Phase 1" into actual orchestrator action.
  - Suggested remediation: Print the actual `.venv/Scripts/python.exe checkpoint.py <ID> research-running` next-step (or a /milestone-pipeline re-invocation hint).

- **F4-L2 - No `state.research_synthesis` length cap** at `commands/milestone-pipeline.md:122`
  - Observation: Phase 2 writes the synthesis as `--set research_synthesis="\"<one paragraph>\""`. No length cap. A paragraph could be 3000 chars.
  - Suggested remediation: Cap at 500 chars in checkpoint.py, OR document a soft cap in the command body.

---

## Cross-cutting concerns

**Pattern 1 - Systematic drift from the `/roadmap` sub-agent contract.** Five sub-agents, five missed conventions. Each milestone agent: (a) lacks the `## Memory bootstrap` H2 section (relevance-gated), (b) lacks the canonical 4-key JSON return contract, (c) carries a `<scope-bounds>` block that's shorter than the roadmap calibration (missing `glab *`, `mcp__GitLab__*`, slash-command-dispatch ban, named source-file ban), (d) ends with a 5-way-cloned "Memory update" block that should be factored. This is not an oversight on one file; it's a systematic miss across all five files. The port agent likely read the OSE reference and faithfully reproduced its conventions without realising that `/roadmap` (ported earlier in the same session) had ALREADY established the new local convention. Remediation: re-port each milestone agent against the `roadmap-refiner.md` shape, copying the structural elements (memory-bootstrap section, JSON contract, expanded scope-bounds, untrusted-content-policy, status routing).

**Pattern 2 - Format triangle: template, agent body, and parser regex disagree.** `adversary-critique-template.md` (per-invocation finding template), `milestone-adversary-critic.md` (agent body's per-finding skeleton), `critique-format.md` (canonical shared format), and `dedupe-findings.py:39` (parser regex) are FOUR sources of truth for the per-finding shape. They disagree pairwise. The dedupe script will silently report zero clusters even on a critique with cross-critic duplicates - the F2-C2 critical. This is the single highest-leverage fix: pick `critique-format.md` as canon (it's the established shared format), rewrite the template, rewrite the agent body, rewrite the regex. Costs maybe 30 minutes; unblocks the dedupe pipeline and removes a class of bugs.

**Pattern 3 - Schema fields that nobody writes.** `implementation_path`, `implementation_commits`, `research_briefs`, `critique_finding_counts` are all declared in `init-state.sh:102-114` and read by `status.sh:93-105` but never set by the orchestrator body. This is dead weight - the schema looks complete on inspection, but invoking the pipeline produces a partial state. The pattern hints at a port that copied the schema from the OSE reference without auditing the writer side. Remediation: either wire writers for each field (preferred for `implementation_commits` and `critique_finding_counts` since they're load-bearing for status), or delete the dead fields from the schema.

**Pattern 4 - Resume is documented but unimplemented.** Frontmatter declares `[--resume]`, command body declares "If resuming: skip to the appropriate phase", but no instruction maps `state.phase` to a phase-step entrypoint and no validator script exists to compute it. By contrast, `/roadmap` ships both a marker-presence table AND a validator with `--report-first-unpopulated` flag. The milestone-pipeline's resume path is currently a no-op promise. If a user runs `/milestone-pipeline foo-e1 --resume` after a context compaction during Phase 3, the orchestrator has no documented route. Remediation: ship a `validate-state.py --report-next-phase`, add a phase-to-step routing table to the command body.

---

## Recommended remediation order

The fix order biases toward unblocking common-path runs (CRITICAL/HIGH first), then closing systematic drift, then bloat trim.

1. **F2-C2 + F1-C1** - Reconcile the four format sources. Pick `critique-format.md` canon, rewrite `adversary-critique-template.md`, rewrite the per-finding skeleton in `milestone-adversary-critic.md:105-111`, rewrite `dedupe-findings.py:39` FINDING_RE. **Effort: M.** Without this fix, dedupe-findings.py silently no-ops on every Phase 3 run.

2. **F2-C3** - Move the `research-running` checkpoint BEFORE dispatch (`commands/milestone-pipeline.md:96-101`). One-line move. Restores status.sh wallclock-per-phase accuracy. **Effort: XS.**

3. **F2-C1** - Distinguish `None` from empty-string in `checkpoint.py:107-110` (--get output). Belt-and-suspenders for the Phase 3 frontend-detect guard. **Effort: XS.**

4. **F4-C1 + F4-C2** - Implement `--resume`. Add `validate-state.py --report-next-phase` mirroring `validate-roadmap.py`. Add a phase-to-step routing table to the command body. **Effort: M.** Without this, every context compaction is a re-start.

5. **F1-H1 + F1-H2 + F1-H3 + F4-H2 + F4-M4 + F4-M5 + F4-M8** - Re-port each of the five milestone sub-agents against the roadmap-refiner.md shape: add `## Memory bootstrap` section with relevance gate, add the canonical 4-key JSON return contract, expand `<scope-bounds>` blocks, wire gate-required paths, add compaction instruction. **Effort: M.** This is the systematic-drift fix.

6. **F4-H1** - Add a "Sub-agent contract" section to the command body with the status routing table parallel to `commands/roadmap.md:211-241`. **Effort: S.**

7. **F2-H1 + F2-H2 + F2-H3** - Wire writers for `implementation_path`, `implementation_commits`, `research_briefs`, `critique_finding_counts`. OR delete from schema. Prefer wiring (status.sh becomes useful). **Effort: S.**

8. **F2-H8** - Fix the missing `.venv/Scripts/python.exe` prefix at `phase-implement.md:54`. **Effort: XS.**

9. **F2-H4** - Either add `not-applicable` to the canonical status enum (with handler) or change oss-scout to return `complete`. **Effort: XS.**

10. **F2-H7** - Persist `--single` / `--deep` / `--oss-scout` / `--resume` flag state into state.json at Step 0.5. Load-bearing for resume (item 4) and OSS scout gating. **Effort: XS.**

11. **F3-H1 + F3-H2 + F3-M1..M9** - Token bloat trim. Delete `agent-prompts.md` (or restructure so the orchestrator uses it for all dispatches). Trim the 10-axis checklist reproduction from `milestone-adversary-critic.md`. Trim the AI-N table from `phase-implement.md`. Factor the memory-update protocol into a single reference. **Effort: M.**

12. **F4-H6** - Dependency-graph awareness when consuming a `/roadmap` epic id. Read `plans/<slug>-roadmap.md` for the milestone's deps; assert each dep's state.phase is `complete`. **Effort: M.**

13. **F4-H4 + F4-H5 + F4-H7 + F4-M1..M3, M6, M7, M9** - Operational gaps: retry policy, wall-clock budget enforcement, dispatch.log observability, find-count surfacing, dispatch rationale, abort-and-cleanup, avc-integration.md reference. **Effort: M total** (each individually XS or S).

14. **Axis 1 + Axis 2 MEDIUM and LOW polish** - Em-dash unification, heading depth unification, single-vs-double dash unification, comment trims, encoding hardening. **Effort: S total.**

15. **F4-M10** - Document the hook-integration gap (already implicitly documented in `commands/roadmap.md:207`); plan a follow-up milestone for hook enforcement. **Effort: XS** (doc-only).

Estimated total effort: ~6-10 hours focused remediation, with items 1-4 unblocking common-path runs in the first 2 hours.
