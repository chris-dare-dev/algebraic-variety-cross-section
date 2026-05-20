# Frameworks — long-tail (lazy-loaded)

**Default rules** (OKR, Now/Next/Later, MoSCoW, RICE, vertical slicing, Given/When/Then, Spike lane) are baked into the four phase reference files.  **Read this file ONLY when a non-default situation arises** — e.g., the problem shape doesn't fit vertical slicing, the work is deadline-sensitive in a way RICE flattens, or the user explicitly asks for Shape Up appetite framing.

## Decomposition long-tail

### User Story Mapping (Patton 2014)

**Use when:** the work is user-journey-shaped (multi-step user-visible flow).  Example for AVC: "First-launch onboarding overlay walking the researcher through dropdown -> parameter sliders -> domain clip -> screenshot" or "End-to-end variety-exploration flow: pick variety -> tune params -> compare two figures side by side -> export STL".

**How:** lay the user's narrative left-to-right (the "backbone": Discover -> Select -> Configure -> Confirm -> ...).  Decompose each step into vertical alternatives ranked top-to-bottom by priority.  The top row is your MVP slice; deeper rows are subsequent releases.

**Output for the roadmap:** the backbone steps become epics; the alternatives become stories.  INVEST still applies per epic.

**Skip when:** the work isn't journey-shaped (a single panel refactor, a new variety generator, a bug-fix epic).

### Event Storming (Brandolini 2021)

**Use when:** bounded contexts are unclear and the proposed decomposition makes you uncomfortable but you can't say why.  Example for AVC: "Where does `view_panel` end and `appearance_panel` begin?", "Which dock owns the color preset menu — `appearance_panel`, `view_panel`, or a new dock?".

**How:** in past tense, sticky-note every domain event ("Surface generated", "Mesh cached as raw", "Domain clipped", "Color applied to actor", "Screenshot saved").  Cluster events into bounded contexts.  Each cluster is a candidate epic; cluster boundaries are candidate API surfaces.

**Output for the roadmap:** clusters -> epics; boundary events -> integration tests.

**Skip when:** boundaries are obvious.  This is heavyweight; reserve for new bounded-context design (e.g., adding a fifth panel).

### Impact Mapping (Adzic 2012)

**Use when:** the causal link from output to outcome is fuzzy.  "We think dark mode will help researchers — but will it?" or "We think adding KaTeX tooltips will help — but for which audience?"

**How:** Goal -> Actor -> Impact -> Deliverable, drawn as a four-level mind map.  The Goal is the outcome; Actors are the users/agents/systems whose behavior you want to change; Impacts are the *behavioral changes* in those actors; Deliverables are the features that might cause those changes.

**Output for the roadmap:** Deliverables -> epics.  The Impact column is your "Acceptance signals" for each epic.

**Skip when:** the outcome is direct ("eliminate the launch background flash" — you don't need an Impact map).  Cheapest tool for *killing* features that "seem useful".

### SPIDR (Cohn 2017)

**Use when:** an epic is XL (>6 weeks) or a story is L (>3 days) and you can't see the seam.

**The five seams to try in order:**
1. **Spike** — split into a learning task + the subsequent execution task.
2. **Path** — split by code path (happy path first; error/edge paths second).
3. **Interface** — split by API surface (one panel this iteration, another next).
4. **Data** — split by data slice (one variety first, the others later; K3 only first, Enriques and CY3 after).
5. **Rules** — split by business rule (one parameter range active first; the wider range activates after).

**Output for the roadmap:** SPIDR turns one epic into 2-3 epics or one story into 2-3 stories.  Re-run INVEST on the splits.

## Prioritization long-tail

### WSJF (Reinertsen 2009 / SAFe)

**Use when:** items have very different durations AND you can estimate Cost of Delay components (urgency + value + risk reduction).

**Formula:** `(User+Business Value + Time Criticality + Risk Reduction) / Job Size`.  SAFe scores each component on a 1/2/3/5/8/13 Fibonacci-ish scale.

**Beats RICE when:** a 2-week item blocking a downstream Fano 3-fold variety pass clearly beats a 1-week polish item, but RICE flattens duration into Effort linearly.  WSJF respects that delay × value-per-time is a real dimension.

**Skip when:** all items are similar in duration (RICE is fine), or you can't estimate Cost-of-Delay components without inventing numbers.

### Kano (Noriaki Kano 1984)

**Use when:** deciding whether a feature is *table-stakes* vs *differentiator* — i.e., a positioning question, not a sequencing question.

**How:** for each feature, ask both a functional and dysfunctional question ("How would you feel if X is present? / absent?").  Classify as Basic / Performance / Excitement / Indifferent / Reverse.

**Output for the roadmap:** Kano informs which Should/Could to invest extra polish in (Excitement features) vs which to ship at minimum bar (Basic features).  Doesn't replace MoSCoW + RICE; it complements them.

**Skip when:** the question is "do this before that", not "invest deeply or shallowly".

### ICE (Sean Ellis ~2014)

**Use when:** triage of 20+ ideas in <30 min, no reach data available.

**Formula:** Impact × Confidence × Ease (each 1-10).

**Beats RICE when:** the backlog is too large for RICE's 4-axis scoring AND items are similar in duration.  Use ICE to pick the top 5-8, then RICE those.

**Skip when:** items have very different durations (Ease is too crude a stand-in for Effort).

For AVC: a `/capability-scout` or `/frontend-uplift` final-report already uses RICE-light scoring; the roadmap's RICE pass refines those numbers with Effort-in-weeks rather than Effort-by-tshirt.  ICE rarely beats reusing the upstream RICE-light numbers.

### Cost of Delay (Reinertsen 2009) — standalone

**Use when:** a single decision is high-stakes — "ship now half-done vs ship in 4 weeks complete?"

**How:** estimate the marginal economic value lost per unit time of delay.  Reinertsen's empirical claim: the *act of estimating* CoD surfaces hidden assumptions even when the number is rough.

**Output for the roadmap:** a one-paragraph appendix justifying the lane assignment for an unusual epic.  Not a routine tool.

**Skip when:** delay cost isn't meaningfully bounded ("delaying this by a month doesn't matter" -> use it freely as a Should/Could).

## Roadmap-format long-tail

### GIST (Itamar Gilad 2021)

**Use when:** you have >30 candidate ideas competing for attention and need an evidence-gathering pipeline rather than a sequence.

**The four levels:** Goals / Ideas / Step-projects / Tasks.  Every Idea must accumulate evidence (a capability-scout brief, a frontend-uplift challenger objection, an off-screen render diff) before becoming a Step-project.

**Output for the roadmap:** replaces "Now / Next / Later" with "Validated / Validating / Backlog".  Heavyweight; reserve for product orgs or large initiative ranges.

**Skip when:** you have <30 candidates (Now/Next/Later is sufficient).  Most single-roadmap scopes for this repo have <10 candidates.

### Outcome-based (Bruce McCarthy 2017)

**Use when:** the roadmap audience is mistaking outputs for outcomes (commitment-as-feature-list).

**How:** roadmap rows are *outcomes* ("reduce launch background flash duration from 500ms to 0ms"), not features.  Features hang underneath as *bets to test the outcome*.

**Output for the roadmap:** if the user keeps phrasing roadmap items as "ship X", switch to outcome rows and put X underneath as a bet.  The Phase 1 KRs are already outcome-shaped — extend that into the lane assignment.

**Skip when:** the user is fine with feature-shaped lanes and outputs are obviously the right unit (e.g., "add Fano 3-fold variety family" is a feature that is itself the outcome).

### Theme-based

**Use when:** stakeholder communication needs a one-page summary above the epic level.

**How:** group epics under 2-4 Themes (multi-quarter strategic areas — for AVC: "Variety coverage", "GUI polish", "Test/CI hardening").  The roadmap doc has Themes as level-1 headings; Now/Next/Later sits inside each Theme.

**Output for the roadmap:** an additional section organizing the lanes by Theme.  Doesn't replace the Now/Next/Later spine — it overlays it.

**Skip when:** there's only one Theme (most multi-week roadmaps for solo work) or the audience doesn't need the abstraction.

## Process long-tail

### Shape Up (Singer / Basecamp 2019)

**Use when:** an epic is genuinely uncertain and you need to *fix the time and vary the scope*.  Example for AVC: "Fano 3-fold variety pass — 6 weeks fixed; we'll ship whatever fits."

**The two artifacts:**
- **Pitch:** a shaped problem with explicit appetite (1 / 2 / 6 weeks), no-gos, and rabbit holes named.
- **Bet:** a yes/no decision per cycle on which Pitches to commit to.

**Output for the roadmap:** convert the Now lane to one or two Bets, each with appetite + no-gos.  The story decomposition becomes the *interior* of the bet, not the lane structure.

**Skip when:** the work is well-understood and a fixed-scope/variable-time framing is fine.

### Scrumban

**Use when:** migrating an existing Scrum-shaped backlog to Kanban-style flow.  Not relevant to a single-developer project starting fresh.

## Anti-pattern: when long-tail framework selection itself becomes theatre

If you find yourself reading this file at every roadmap, the defaults are wrong.  Re-tune the defaults in the four phase reference files instead.

If the user is asking for a specific framework by name (e.g., "use Shape Up for the Fano 3-fold epic"), use that one and skip the long-tail browse.
