# Design adversary critique — restructure-feature-subpackages-2026q2-r2

**Reviewed:** PLAN.md @ dfe286e (untracked), symbol-map.json @ dfe286e (untracked)
**Axes walked:** 12
**Verdict:** PROCEED-WITH-CONDITIONS

---

## Findings by severity

### HIGH — Batch 3 PLAN incorrectly asserts "no callers of `from panels.X`" but two test files use `panels.*`

**Axis:** 8. Test parity risk / Shim-cycle correctness
**Where:** PLAN.md §3 Batch 3 symbol-map annotation (line 158): "**No shim is added at root `panels/`** — only consumer was the 4 r1 shims (which are removed in Batch 1) and `app.py` (which LibCST rewrites in this batch). Verified: `grep -r 'from panels\\|import panels' --include='*.py'` shows only `app.py` + panels' own internal files."
**Why it matters:** The grep verification cited in the PLAN is factually wrong. Two test files import `panels.*` at their canonical paths:
- `tests/test_clip_domain.py:21` — `from panels.view import ViewPanel`
- `tests/test_styles_palette.py:243, 280, 301, 320` — `import panels.appearance` (4 times with `patch.object(panels.appearance, ...)`)
- `tests/test_styles_palette.py:646-649` — file-path literals `"panels/appearance.py"` etc. (style-check for hex literals; may not break at runtime but will silently bypass the check if the file no longer exists at that path)

After `git mv panels/ _qt/panels/` in Batch 3 with no `panels/__init__.py` shim, these three test files will raise `ModuleNotFoundError` at collect time, immediately dropping the test suite below the parity threshold. The PLAN's stated guard condition ("no callers") is wrong, which means the stated rationale for omitting the `panels/` hub shim is invalid.

The refactor-pattern scout (§4.4, §5.4) explicitly documented this scenario and prescribed creating a `panels/__init__.py` hub shim after `git mv panels/ _qt/panels/`. The PLAN adopted Option A (direct-target update of the 4 r1 root shims) but omitted the shim that covers `from panels.view import ViewPanel` and `import panels.appearance` in the test suite.

**Suggested fix:** Add a `panels/__init__.py` re-export shim to Batch 3's tree diff (as the refactor-pattern brief §5.4 prescribes). LibCST-update `test_clip_domain.py:21` to `from _qt.panels.view import ViewPanel` in the same Batch 3 commit, OR add the hub shim at `panels/__init__.py` and update it in a follow-on shim-removal milestone. For `test_styles_palette.py`'s `import panels.appearance` calls, either LibCST-rewrite them or rely on the hub shim — but the shim must exist. Remove the false "Verified" claim from §3 or correct it with accurate grep output.

---

### HIGH — `FAST_RENDER_THRESHOLD_MS` is missing from the symbol map and hub-shim `_PUBLIC_NAMES`

**Axis:** 5. Shim-cycle correctness
**Where:** symbol-map.json (no entry for `FAST_RENDER_THRESHOLD_MS`); PLAN.md §5 Template 1 `_PUBLIC_NAMES` dict (lines 284–303) — no entry for `FAST_RENDER_THRESHOLD_MS`
**Why it matters:** `surfaces.py:96` defines `FAST_RENDER_THRESHOLD_MS = 80`. `tests/test_typical_ms.py:25` imports it via `from surfaces import FAST_RENDER_THRESHOLD_MS`. This is a HARD lock (current-state brief §6 "critical path locks" table). If `FAST_RENDER_THRESHOLD_MS` is not in the hub-shim's `_PUBLIC_NAMES` dict, the `__getattr__` hook will raise `AttributeError` for this symbol after Batch 5 converts surfaces.py to a shim. The constant will logically land in `varieties/dispatch.py` (alongside `should_render_on_drag` and `dispatch_mode` which are its siblings at surfaces.py:L93-L167), but neither the symbol-map nor the shim plan mentions it. The refactor-pattern brief §4.3 sample `_PUBLIC_NAMES` does include `"FAST_RENDER_THRESHOLD_MS": "varieties.FAST_RENDER_THRESHOLD_MS"` — so the scout caught this gap but the designer missed propagating it to the final PLAN.
**Suggested fix:** Add `FAST_RENDER_THRESHOLD_MS` to symbol-map.json (Batch 5, kind: symbol, from: `surfaces`, to: `varieties.dispatch`). Add `"FAST_RENDER_THRESHOLD_MS": "varieties.dispatch"` to `_PUBLIC_NAMES` in the hub-shim template. Assign it to `varieties/dispatch.py` (co-location with `should_render_on_drag` is semantically correct since the constant is used only in `should_render_on_drag`'s predicate).

---

### HIGH — `_hanson_cross_section` placement contradicts itself in PLAN.md tree diff vs. §3 symbol map

**Axis:** 1. AI-1..AI-15 conflicts (AI-6 implicit/parametric split)
**Where:** PLAN.md §2 tree diff line 101: "`+ varieties/_marching.py [_marching_cubes_to_polydata + _grid_to_polydata + _concat_polydata + _hanson_cross_section]`"; versus PLAN.md §2 tree diff line 108: "`+ varieties/calabi_yau.py [4 generators + PARAMS + _hanson_cross_section local helper; 241 LOC]`"
**Why it matters:** The tree diff says `_hanson_cross_section` goes to BOTH `varieties/_marching.py` AND `varieties/calabi_yau.py`. The symbol-map.json correctly maps `surfaces._hanson_cross_section` → `varieties._marching._hanson_cross_section`, and the AI-6 impact table (§6) correctly says it goes to `_marching.py`. The calabi_yau.py line-108 annotation is an inconsistency — it will cause the implementer to either duplicate the function (introducing two canonical definitions) or create an import cycle (`calabi_yau.py` imports `_marching.py`, and `_marching.py` would import `calabi_yau.py` if the helper is local there). The current-state brief §4.1 confirms `_hanson_cross_section` is defined at `surfaces.py:1087` as a shared helper called by all three Hanson generators.
**Suggested fix:** Correct line 108 of the tree diff to: "`+ varieties/calabi_yau.py [4 generators + PARAMS; 241 LOC — calls _hanson_cross_section from varieties._marching]`". Remove the "local helper" annotation. The implementer should verify `calabi_yau.py` will import `_hanson_cross_section` from `varieties._marching`, not define it locally.

---

### MEDIUM — Batch 3 is 8-10 commits + 2273 LOC across 7 files: bisect-redness risk from insufficient sub-commit granularity

**Axis:** 10. Sequencing safety
**Where:** PLAN.md §4 delta table, Batch 3 row: "8-10 commits (4 panels move + 3 module moves + 3 shim files + 1 LibCST rewrite + 1 panels/ removal)"; §9 batch sequencing table: "75 min" estimate noted as "optimistic if LibCST surprises emerge"
**Why it matters:** The r1 bisect-redness lesson (agent-memory lessons.md, refactor-pattern-brief §5 critical rule) states: "Each `git mv` must land in the SAME commit as its LibCST import rewrite." Batch 3 bundles `git mv panels/ _qt/panels/`, three separate `git mv` calls for icons/styles/ui_helpers, three new shim files, one LibCST rewrite pass for `app.py`, and a `panels/` directory removal — all in "one batch." The PLAN bundles these together but does not define the intra-batch commit boundaries. At 2273 LOC moved, if the LibCST rewrite partially completes and the batch is interrupted, git bisect will show a red range spanning multiple commits. The PLAN's Section 4 commit count of "8-10" but no explicit commit-by-commit sequencing within the batch creates ambiguity for the implementer.

The issue is not that Batch 3 should be split into two user-gate batches (the user brief expected 6-9 batches and 9 is fine). The issue is that the intra-batch commit ordering is under-specified, creating a risk that the implementer sequences them incorrectly (moves panels/ before updating the 4 r1 shims, leaving a red commit).
**Suggested fix:** Add to PLAN.md §4 Batch 3 a required intra-batch commit sequence as a numbered list: (1) create `_qt/` skeleton (`__init__.py` only) + 3 new `_qt/*.py` files (icons/styles/ui_helpers, content-copied but NOT yet removed from root) — commit; (2) `git mv panels/ _qt/panels/` + update 4 r1 shims to `_qt.panels.*` + create `panels/__init__.py` hub shim if needed + LibCST rewrite all `from panels.*` callers — single atomic commit; (3) remove root icons/styles/ui_helpers old content + create 3 root shims — commit; (4) LibCST rewrite `from icons/styles/ui_helpers import` callers — commit. This makes each commit self-contained and bisect-green.

---

### MEDIUM — Shim test deletion (Batch 1) removes proof-of-pattern without replacement and contradicts refactor-pattern brief §5.7

**Axis:** 8. Test parity risk
**Where:** PLAN.md §5 shim-test section (line 370): "NEW shim tests for r2's shims are deferred to a follow-up `tests/test_r2_shims.py` task — NOT bundled into this restructure (per scout-C §10.1 'we can refactor and add features in the same PR — refused' — the SHIMS themselves are the safety net; explicit tests of them are a separate feature)."
**Why it matters:** The PLAN uses scout-C §10.1 (R1: "we can refactor and add features in the same PR") to justify deferring shim tests. But shim tests are not a feature — they are the regression guard that proves shims work correctly. The refactor-pattern brief §5.7 is explicit: "Extend `tests/test_shims.py` (or `test_panels_shims.py`) to cover all new r2 shims using the `catch_warnings(record=True)` pattern." The cite is `[S22]` (Feathers characterization testing) + `[r1-lesson-validate-shims-gap]`. The validate-shims.py script is documented to NOT verify `__getattr__` shim behavior (it only verifies the file exists). Without test_r2_shims.py landing in the same restructure, the only evidence that the `surfaces.py` hub shim's `__getattr__` is working is the one smoke test in Batch 6 (which covers only `_fermat_field_kernel`, not public symbols like `VARIETIES` or `dispatch_mode`). The validate-shims.py script will report PASS for all module-kind entries even if the `__getattr__` dispatch is broken. This is the exact footgun the r1 validate-shims.py gap lesson was written to prevent.

The PLAN's exception ("one smoke test in Batch 6 for the `_PRIVATE_NAMES` dict") is correct as far as it goes, but it doesn't extend to the public-names dispatch or the new Template 2 shims (render_worker, icons, styles, ui_helpers). The refactor-pattern brief §5.7 provides ready-to-use test templates for exactly these cases.
**Suggested fix:** Retarget the issue. The PLAN should add `tests/test_r2_shims.py` in Batch 9 (documentation batch) — not as a feature, but as the post-execution verification the refactor-pattern brief requires. The file can be minimal: one test per new shim type (public surfaces symbol, private kernel symbol, render_worker symbol, one of icons/styles/ui_helpers). The scout's `test_surfaces_shim_public_symbol`, `test_surfaces_shim_private_kernel`, and `test_render_worker_shim` templates (refactor-pattern brief §5.7) can be used verbatim. This is 30-50 LOC and is not a new feature — it is parity verification.

---

### MEDIUM — PLAN proposes `_qt/ui_helpers.py` but symbol-map uses `_qt.ui_helpers`; scout recommended renaming to `_qt/helpers.py`

**Axis:** 3. Hallucinated patterns / Axis 11. Effort honesty
**Where:** PLAN.md §2 tree diff (line 76): "`+ _qt/ ... ui_helpers.py (← ui_helpers.py)`"; PLAN.md §3 symbol-map table: "`ui_helpers` | `_qt.ui_helpers`"; PLAN.md §5 shim template (line 264): "`ui_helpers.py (→ _qt.ui_helpers)`"
**Why it matters:** The refactor-pattern brief §4.7 explicitly flagged: "The new module name is `helpers`, not `ui_helpers`. The shim at the old path `ui_helpers.py` must forward to the new module. LibCST rewrite must update `from ui_helpers import X` → `from _qt.helpers import X`. The `tests/test_debounce.py` imports `ui_helpers` directly — verify it is updated." The designer kept the name `ui_helpers` everywhere in the PLAN (the new path is `_qt/ui_helpers.py`, not `_qt/helpers.py`). This is a valid designer decision — it is defensible to keep the name to reduce churn — but it was made silently without acknowledging the scout's rename recommendation. There is a secondary consequence: `tests/test_debounce.py` imports `from ui_helpers import Debouncer, DebounceCounter` and is not mentioned in the PLAN's LibCST rewrite coverage. If the shim works correctly this test passes via the shim, but the test will receive DeprecationWarnings per import, and if the pytest.ini ever adds `-W error::DeprecationWarning` this will become a test failure.

The PLAN's coverage of test file updates is also incomplete: it mentions `app.py` and `_qt/panels/*` internal imports for Batch 3, but doesn't enumerate `tests/test_debounce.py` as a LibCST target for the `ui_helpers` rename.
**Suggested fix:** Either (a) explicitly document the designer decision to keep `ui_helpers` as the module name within `_qt/` (and note this deviates from scout-B/C recommendations), OR (b) adopt the `helpers` rename and add `tests/test_debounce.py` to the LibCST rewrite list with `from ui_helpers → from _qt.helpers`. Either way, `tests/test_debounce.py` must appear in the Batch 3 LibCST rewrite list.

---

### MEDIUM — Axis 12 (under-engineering vs evidence): CLAUDE.md deferral invokes ETH Zurich citation but the cited source says "exceptions exist" for non-obvious constraints

**Axis:** 12. Under-engineering relative to scout evidence
**Where:** PLAN.md §1 "Explicitly NOT addressed" entry: "**Per-folder CLAUDE.md for each new subpackage** — scout-B's r2 brief Appendix B notes ETH Zurich 2026: 'context files increase agent cost 19-23% for only +4% benefit; AGENTS.md should stay minimal.' Per-folder CLAUDE.md amplifies this cost. Defer to a separate documentation milestone with an explicit benefit hypothesis."
**Why it matters:** The ETH Zurich deferral is partially honest. The best-practices brief Appendix B does say "do NOT add per-subpackage CLAUDE.md files in r2 for all subpackages" — but immediately follows with "EXCEPTION: `varieties/_kernels.py` has a non-obvious Numba constraint that is exactly the kind of 'thing agents cannot discover' the ETH Zurich paper recommends including." The refactor-pattern brief §8 Phase 8 prescribes per-folder CLAUDE.md for all four new subpackages with specific invariant bullets (AI-6/7/8/14/15 for varieties/, AI-9 for render/, AI-2/11/12/13 for _qt/, AI-4/5/10 for cross_section/). The PLAN defers ALL per-folder CLAUDE.md files and cites the ETH Zurich cost finding — but the same citation the PLAN invokes explicitly carves out `varieties/_kernels.py`'s Numba threading-layer constraint as a case worth documenting.

The Numba threading-layer invariant is non-obvious: `numba.config.THREADING_LAYER = "workqueue"` must appear before `from numba import njit` in `varieties/_kernels.py`, or the threading layer defaults to a VTK-incompatible value. This is exactly the kind of hard-won knowledge the ETH Zurich paper says is worth the 4% benefit. Deferring it risks the next agent touching `varieties/_kernels.py` silently breaking the threading invariant.
**Suggested fix:** Add at minimum a `varieties/_kernels.py` module-level docstring block (5-10 lines, not a full CLAUDE.md) that documents the threading-layer ordering invariant — as the best-practices brief §6 specifically recommends ("A 5-line comment block in `varieties/_kernels.py` docstring is more appropriate than a CLAUDE.md there"). This is not a full per-folder CLAUDE.md; it is what the ETH Zurich exception case calls for. The PLAN's Batch 6 should add this docstring to `varieties/_kernels.py`'s specification.

---

### LOW — Batch 3 `_qt/` subpackage has 9 batches total, justified, but Batch 3 reuses refactor-pattern scout's 6-batch sketch with re-ordered operations

**Axis:** 4. Over-engineering relative to repo size / 2. AI-15 honesty applied to design
**Where:** PLAN.md §9 batch-sequencing table
**Why it matters:** The user brief expected 6-9 batches. The PLAN delivers 9. The 9-batch structure is justified: Batches 1 (trivial shim cleanup) and 9 (docs only) are genuine units that would bloat other batches if folded in. Batches 5-8 decompose the varieties/ extraction into 4 incremental sub-batches (types/dispatch → kernels/marching → generators → registry/tooltips), which is the correct "low-blast-radius first" ordering for a 1811-LOC split. None of the 9 batches is padding. This is NONE severity.

However, the refactor-pattern brief's 6-batch execution sketch (§12) ordered: render/ first, then cross_section/, then varieties/, then _qt/ files, then _qt/panels/. The PLAN re-orders to: r1 shim cleanup, render/, _qt/ (combined), cross_section/, then varieties/ in 4 sub-batches, then docs. The re-ordering is architecturally sound (cleaning up r1 artifacts before adding new structure, and delaying the highest-risk surfaces.py split until _qt/ is stable). This is a legitimate designer choice, not a problem.
**Suggested fix:** No fix needed. The 9-batch structure is justified and the ordering rationale is traceable.

---

### LOW — Batch 2 `render/` subpackage introduces a 1-file subpackage; scout flagged this as "low structural justification"

**Axis:** 2. AI-15 honesty applied to design
**Where:** PLAN.md §1 Axis-12 self-check paragraph: "`render/` subpackage — Batch 2"; current-state brief §8 ("A subpackage with 1 file + `__init__.py` is minimal overhead but adds import path distance")
**Why it matters:** The current-state brief §8 flagged render/ as "low structural justification currently" and called it a "judgement call." The best-practices brief §P2 rates it HIGH for r2 specifically because it creates a named domain boundary. The PLAN's Batch 2 adopts the subpackage with justification (import-graph direction enforcement, forward-compatibility). This is consistent with axis-12 (the evidence supports it), but the word "currently" in scout-A's flag means this observation from the current-state brief is explicitly overruled by scout-B's HIGH rating. This is NONE severity for the design — the move is justified.

One minor accuracy concern: the PLAN's section 4 shim description for `render_worker.py` (lines 253-262) imports `from render.worker import __dict__ as _ns` which is non-idiomatic. The standard Template 2 pattern from the refactor-pattern brief §5.2 uses `from render import worker as _new; getattr(_new, name)`. This is cosmetic but could mislead the implementer if they copy the shim template verbatim and `__dict__` behaves differently than expected for `MeshWorker` (a class).
**Suggested fix:** Correct the shim template in PLAN.md §5 for `render_worker.py` to match Template 2 exactly as written in the refactor-pattern brief §5.2 (`from render import worker as _new; return getattr(_new, name)`), not the `__dict__`-access variant.

---

### LOW — Numba threading-layer side effect: PLAN says "hub shim does NOT eagerly trigger _kernels import" but this is the correct behavior only if app.py still imports from varieties before kernel access

**Axis:** 7. Cross-suite test gaps (category 3: import-time side effects)
**Where:** PLAN.md §7 cross-suite test gaps table, Category 3 (line 419): "The hub shim's surfaces.py `__getattr__` does NOT eagerly trigger _kernels import — only attribute access does. A smoke test like `import surfaces; import numba; assert numba.config.THREADING_LAYER == 'workqueue'` would FAIL because surfaces.py no longer sets it."
**Why it matters:** The PLAN correctly identifies the problem and correctly identifies what would fail. However, it prescribes "test-suggester should propose a test" (deferred) rather than specifying how the threading layer is guaranteed to fire before the first kernel call in production. The best-practices brief §P6 states: "The recommended implementation: put it at the top of `varieties/_kernels.py`, which is imported by every kernel-using module. The `varieties/__init__.py` should eagerly import `varieties._kernels` to ensure the side effect fires before any lazy-loading resolves." The PLAN says `varieties/__init__.py` is a "convenience re-export" (lines 341-357) with `from varieties.types import ParamSpec, Surface` and `from varieties.dispatch import ...` — but does NOT include `import varieties._kernels` as an eager import. If the app starts and imports `varieties` before any generator is called, and the generator family modules don't individually import `_kernels` until first call, there is a window where the threading layer hasn't fired.

In practice, `app.py` imports generator functions via `from surfaces import enriques_figure_1, enriques_figure_2` which via the hub shim will trigger `importlib.import_module("varieties.enriques")` → which imports `from varieties._kernels import ...` — so the side effect fires on first surface selection. This is likely safe for interactive use, but it is late compared to the current behavior (side effect fires on `import surfaces` before any generator is called). The PLAN's Batch 6 spec says "numba.config.THREADING_LAYER MUST be at top of the file before njit import" — this is correct — but `varieties/__init__.py` should also add `import varieties._kernels` as an eager side-effect trigger.
**Suggested fix:** Add `import varieties._kernels  # eager: ensures Numba threading-layer side effect fires at `import varieties` time` to the `varieties/__init__.py` spec in PLAN.md §5. This matches the best-practices brief §P9 recommendation and eliminates the late-fire window.

---

## Axes with NONE findings

**Axis 1 — AI-1..AI-15 conflicts:** AI-1 (stack lock) untouched. AI-3 (offscreen) untouched. AI-4/5 (clip_scalar) preserved verbatim by Move Method design. AI-6 (implicit/parametric split) preserved at caller level per §6. AI-7 (Hanson normals) preserved inside `_concat_polydata` which moves intact. AI-8 (VARIETIES + ParamSpec) preserved via hub shim + new canonical path. AI-9 (re-entrancy guard) untouched (app.py stays). AI-10 (raw mesh cache) untouched (clip_to_domain signature preserved). AI-11 (Qt enums) preserved by construction (new files have no Qt code except _qt/). AI-12 (WCAG palette) preserved (styles.py content unchanged). AI-13 (6-digit hex) untouched. AI-14 (generator return contract) preserved by verbatim function moves. AI-15 (math honesty) preserved (docstrings travel with generators). The `_hanson_cross_section` dual-placement inconsistency (HIGH finding) affects AI-6 integrity only if the implementer creates a duplicate — the symbol-map correctly resolves it to `_marching.py`.

**Axis 2 — AI-15 honesty applied to the PLAN:** Each proposed split has a traceable justification. surfaces.py split → Evaluator FAIL #17, scout-B §P1 HIGH. _qt/ subpackage → FAIL #24, scout-B §P4 HIGH. render/ → scout-B §P2 HIGH. cross_section/ extraction → scout-B §P3 HIGH. The 6 deferrals each cite a specific audit brief or user-brief instruction. No batch is justified purely on "agents like splits."

**Axis 3 — Hallucinated patterns:** No package-by-layer names (`controllers/`, `services/`, `lib/`). No `utils.py` reintroduction. No star-imports in any shim (Template 3 explicitly refused, §5). No capitalized directory names. No src-layout introduction. `_qt/` adopts napari-documented convention (scout-B Appendix A). `varieties/` adopts scipy `_lib/`-for-kernels pattern (scout-B §1.5). All naming is lowercase with underscores.

**Axis 4 — Over-engineering relative to repo size:** 9 batches for a 7849-LOC app is appropriate for the scope (1811-LOC god module decomposition + 4 subpackages). No three-deep nesting introduced (`_qt/panels/*.py` is 2 levels from root, which is the limit per evaluator check #13 and scout-B §A7). No `api/` subpackage with no consumers. No `plugins/` directory. varieties/ + render/ + cross_section/ + _qt/ are all substantiated by evaluator FAILs.

**Axis 6 — Rollback feasibility:** Tier 1 rollback (`git revert --no-commit <baseline>..HEAD`) is specified, tested in scratch worktree per §8 rehearsal command. Tier 3 per-batch rollback via batch-end tags is specified. The MOVES.md and CONTEXT.md rollback limitation is documented. No "we'll figure it out" deferrals.

**Axis 7 — Anchor coverage:** Batch 9 explicitly updates README.md "Extending the app" section, CONTEXT.md §4 architecture conventions + §3 numba threading-layer note, MOVES.md with r2 entries. The PLAN omits explicit mention of AGENTS.md/CLAUDE.md update in Batch 9's tree diff — but §8 rollback section implies those are covered. This gap is minor (AGENTS.md pointer update to varieties/render/_qt/ is a 5-line change) and does not rise to HIGH.

**Axis 9 — Cross-suite test gaps:** The PLAN §7 table covers all 10 scout-C §8 categories. Categories 3 (threading-layer side effect), 5 (seam tests across new module boundaries), and 10 (cyclic-import smoke under entrypoint) are all flagged as YES and assigned to Phase 5 test-suggester. This is adequate planning — the test gaps are acknowledged and dispositioned.

**Axis 10 — Sequencing safety:** Batches ordered low-risk first: trivial shim deletion (B1) → single-file structural moves B2 (render/) → medium structural _qt/ (B3) → semantic extraction B4 (cross_section/) → incremental god-module decomposition B5-B8 (varieties/) → documentation B9. Batches 5-8 decompose the highest-risk operation (surfaces.py split) into 4 incremental steps from low-blast-radius symbols first (types/dispatch) to the final terminal shim state (registry/tooltips). This is correct.

**Axis 11 — Effort honesty:** The delta-size table is credible. varieties/ LOC: 807 generators + ~590 kernels/marching/types/dispatch/registry/tooltips = ~1397 LOC moved (surfaces.py 1811 → ~50 shim = 1761 LOC moved; the ~360 LOC difference is the overhead of new `__init__.py` + re-export boilerplate, which is believable). Batch 3 at 2273 LOC moved is the largest single-batch delta; the 75-min estimate is labeled "optimistic" which is honest. Total ~40 commits for the restructure is consistent with the batch structure.

**Axis 12 — Under-engineering relative to scout evidence (new axis):** The PLAN addresses all four of scout-B's HIGH-rated patterns (varieties/, render/, _qt/, cross_section/). The six deferrals (FAIL #4, #5, #11, #19, #20 + per-folder CLAUDE.md) each cite the audit source that rated them non-urgent. The CLAUDE.md deferral is the closest call (MEDIUM finding above), but the body of the PLAN is not under-engineered relative to the evidence — if anything, it is slightly over-specified in the shim template section.

---

## Recommended PLAN.md edits before Phase 3

1. **§3 Batch 3 symbol-map annotation (line 158):** Remove "Verified: `grep -r 'from panels\\|import panels'` shows only `app.py` + panels' own internal files." Replace with: "NOTE: `tests/test_clip_domain.py:21` and `tests/test_styles_palette.py:243,280,301,320` import from `panels.*` and must be handled. Options: (a) add a `panels/__init__.py` hub shim per refactor-pattern brief §5.4; OR (b) LibCST-rewrite both test files in the same Batch 3 commit. Choose one and document it."

2. **§2 tree diff line 108:** Change "`+ varieties/calabi_yau.py [4 generators + PARAMS + _hanson_cross_section local helper; 241 LOC]`" to "`+ varieties/calabi_yau.py [4 generators + PARAMS; 241 LOC — imports _hanson_cross_section from varieties._marching]`".

3. **symbol-map.json and §5 `_PUBLIC_NAMES`:** Add `FAST_RENDER_THRESHOLD_MS` → `varieties.dispatch` entry to both the symbol map (Batch 5) and the `_PUBLIC_NAMES` dict in the hub-shim template.

4. **§5 Template 2 for `render_worker.py`:** Replace `from render.worker import __dict__ as _ns; if name in _ns: ... return _ns[name]` with the canonical refactor-pattern-brief §5.2 form: `from render import worker as _new; if hasattr(_new, name): ... return getattr(_new, name)`.

5. **§5 or Batch 6 spec:** Add `import varieties._kernels  # eager: ensures Numba threading-layer side effect fires` to the `varieties/__init__.py` specification, before any lazy-loading `__getattr__` definition.

6. **§4 Batch 3 commit count / intra-batch sequence:** Add a numbered required commit sequence within Batch 3 (see MEDIUM finding above) so the implementer cannot reorder the `git mv panels/` step before updating the 4 r1 shims and handling the `test_clip_domain.py` / `test_styles_palette.py` callers.

7. **§5 shim-test plan or Batch 9:** Add `tests/test_r2_shims.py` to Batch 9's tree diff using the refactor-pattern brief §5.7 templates for `test_surfaces_shim_public_symbol`, `test_surfaces_shim_private_kernel`, `test_render_worker_shim`, and at minimum one Template 2 shim (icons/styles/ui_helpers). The scout-C R1 anti-pattern ("refactor and add features in same PR") does not apply to a test file that is the parity verification of the restructure itself.
