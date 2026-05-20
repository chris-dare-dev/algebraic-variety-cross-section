# lessons — roadmap-sequencer

Accumulates 2-5-bullet lessons per roadmap run.  Appended via heredoc, never overwritten.  Compact only when exceeding 200 lines.

## panel-refresh-2026q2 (2026-05-20)
- **MoSCoW cut heuristic — enabler at boundary:** UPL-1 (palette tokens, ENABLER epic e2) was correctly tagged Must because the Objective explicitly names the token foundation as a deliverable AND it directly unblocks the rank-1 RICE epic (e3/UPL-5). Enabler epics with an immediate, named, high-RICE downstream value epic satisfy INVEST-V and belong at Must, not Should.
- **MoSCoW cut heuristic — 60% cap management:** With 5 epics, 3 Musts = exactly 60% — the script uses `<=` so this passes. When the catalog has exactly N=5 epics, be deliberate: every Must you add removes a Should. The XS-effort Should (e5/UPL-13) stayed Should because it's not load-bearing for the Objective even though it's a KR.
- **RICE Confidence pattern — AVC foundational epics:** UPL-3 (background flash) had C=50% despite being ranked #2 overall because the evidence was 2-source (visual scout + critic) and the final-report itself priced it at C=0.5. Don't conflate high Adj-RICE (with foundational bonus) with high Confidence. The 50% default applied to 2 of 3 Musts (e1 and e4) — surface this always.
- **Lane assignment — Now vs Next for Musts:** When all 5 epics fit in a single 2-week sprint, use the DAG to split Now/Next within the sprint rather than splitting by RICE rank alone. e4 (2nd-RICE Must) went to Next — not Now — because its spike must resolve first, making it naturally a second-week item even though its RICE > e2.
- **Story decomposition — background flash epics:** The 2-line fix (s1) and the guard+test (s2) decompose cleanly: s1 is the structural move, s2 is the defensive guard + regression insurance. This pattern (structural-change story + guard+test story) works well for all "move X to Y to fix initialization order" epics in AVC.
