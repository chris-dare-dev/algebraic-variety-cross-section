# Panel Refresh 2026Q2 — Roadmap

> **Slug:** `panel-refresh-2026q2` · **Created:** 2026-05-20 · **Status:** scaffold (Phase 0)

<!-- ROADMAP:section:meta -->
## 0. Meta

- **Author:** chris.dare@nalej.com
- **Brief source:** --brief flag  *(one of: `--brief` arg | conversation summary | unspecified)*
- **Execution handoff:** CONTEXT.md section 6 — the 5-phase implementation pipeline (Math research / code archeology → Implementation + off-screen render verify → Adversarial review → Remediation → UI/UX)
- **Issue tracker:** GitHub Issues *(populated only if `--gh-issues` was passed; orchestrator resolves `owner/repo` at gate time via `gh repo view --json nameWithOwner`)*
- **Repo invariants:** AI-1 .. AI-15 — `.claude/references/app-invariants.md`

<!-- ROADMAP:section:refine -->
## 1. Brief

Translate the 23-candidate frontend-uplift catalog at .claude/notes/frontend-uplifts/2026q2-panel-refresh/artifacts/final-report.md into a Now-Next-Later roadmap with epics scoped around the foundational candidates (UPL-1, UPL-2, UPL-3) and the recommended first-wave bundle (UPL-3 -> UPL-1 -> UPL-5 -> UPL-19+18 spike -> UPL-13).

## 2. How-Might-We

How might we **ship the challenger-vetted first-wave bundle (UPL-3 → UPL-1 → UPL-5 → UPL-19+UPL-18 spike → UPL-13) atop the three foundational refactors** so that **the researcher driving the GUI** can **see visually distinct, polished, artifact-free surfaces from first launch — across all four variety families — without any background flash, uniform steel-blue monotony, or Enriques sawtooth tear**?

## 3. Sharpening answers

- **Who:** The researcher driving the GUI to explore K3, Enriques, Calabi–Yau, and Fano 3-fold variety families; the single developer maintaining the app on the direct-to-`main` cadence (CONTEXT.md §12). A secondary beneficiary is the future-Claude reader of `CONTEXT.md` who must execute each epic via the 5-phase pipeline (CONTEXT.md §6).

- **Success looks like:** Off-screen renders of the canonical 5-surface set (Fermat quartic, Kummer, Enriques canonical sextic, Hanson quintic, Fano default) show: (a) no light-grey background flash on first render (UPL-3 done), (b) each variety family in a distinct default color — K3 `#8ab4d4`, Enriques `#c8a880`, CY3 `#4a90d9`, Fano `#7ec8a0` (UPL-5 done), (c) the Enriques canonical sextic shows no comb-tooth sawtooth tear (UPL-18+UPL-19 done), and (d) the status bar reads `bbox ±a × ±b × ±c` after every render (UPL-13 done). All 120 existing tests still pass.

- **Constraints:**
  - AI-1 (`.claude/references/app-invariants.md`): PySide6 + PyVista + pyvistaqt only — no Mayavi, no Plotly, no raw VTK.
  - AI-2 / AI-3: tests are Qt-free; render verification via `pv.OFF_SCREEN = True` only — never construct `MainWindow()` under `QT_QPA_PLATFORM=offscreen`.
  - AI-6: implicit surfaces (Enriques, K3, Dwork) use marching-cubes pipeline; parametric (Hanson) skip Taubin smoothing — do not mix pipelines.
  - AI-8: every surface must be a `Surface`/`ParamSpec` in the `VARIETIES` registry; no int/float-bimodal `ParamSpec`.
  - AI-9: any new `processEvents()` call requires the `self._computing` re-entrancy guard (CONTEXT.md §4.4 + §8.5).
  - AI-10: domain-clip changes do NOT regenerate the mesh — `_raw_mesh` is cached (CONTEXT.md §4.3).
  - AI-12: all visible text ≥4.5:1 contrast ratio (WCAG 2.1 AA); challenge.md §4 specifically flags `COLOR_MUTED = #5a5a5a` failing on dark viewport (ratio ~2.5:1 on `#2f2f2f`) — any new overlay text needs a viewport-specific token.
  - AI-13: 6-digit hex only in PyVista color arguments; Qt stylesheet `#888` is a separate surface but keep it 6-digit for consistency.
  - AI-14: generators return `pv.PolyData` or raise `ValueError`; `RuntimeWarning` for soft anomalies (CONTEXT.md §8.8).
  - CONTEXT.md §9 (no QSettings persistence — explicitly deferred; this roadmap does NOT lift that deferral in the first wave).
  - Single-developer cadence: direct-to-`main` commits, one commit per CONTEXT.md §6 phase (CONTEXT.md §12).
  - Test-suite runtime budget: ~4 s for 120 tests; no new Qt dependencies in the test path.

- **Prior art:**
  - Centralized stylesheet `styles.py` (~140 LOC) exists but hex literals are scattered — refactor was explicitly deferred until now. CONTEXT.md §3 line 34; final-report.md §3 (UPL-1 foundational sketch).
  - Background flash root cause: `AppearancePanel.apply_to_actor(None)` is a no-op at startup. Documented in synthesis.md §3 (F3 = UPL-3), challenge.md clean-candidate list.
  - Taubin smoothing is `n_iter=20, pass_band=0.1` globally (CONTEXT.md §3 line 57; AI-6); the Enriques v0 fix is a second pass at `n_iter=40, pass_band=0.05` + bounds `* 1.05` (final-report.md §4, rank 4; challenge.md §3 MAJOR UPL-18 v0 scope-cut).
  - No per-variety default surface color exists — `appearance_panel.py:74` hardcodes `#b0c4de` for all 14 surfaces. final-report.md §4 rank 1 (UPL-5).
  - Status bar shows N_verts and N_faces but no spatial extent — 3-line addition to `app.py:326`. final-report.md §4 rank 3 (UPL-13).
  - `#888` short-hex bug in `appearance_panel.py:48` is an AI-13-adjacent violation already cataloged in synthesis.md (UPL-21) and challenge.md §4 (MINOR). First wave does not fix this standalone; it may ride on UPL-1.
  - No state persistence: CONTEXT.md §9 line 361 — explicitly deferred. The challenge (MAJOR UPL-15) reinforces this is second-wave only.
  - No `pytest-qt` UI tests: AI-2 / CONTEXT.md §9 — acknowledged; this roadmap does not change the test strategy.

- **Why now:** The `/frontend-uplift 2026q2-panel-refresh` pipeline completed 2026-05-20 and produced a fully challenger-vetted 23-candidate catalog with RICE scores, DAG ordering, and explicit first-wave recommendation (final-report.md §5.4). The Fano 3-fold was added in the two most recent commits (11d40dc, 8d5d7c0), making 4 variety families live — exactly the four families UPL-5 targets with distinct default colors. The Enriques sawtooth CRITICAL (UPL-18) was render-evidenced in the uplift, has a v0 scope-cut (~2 lines), and is the only CRITICAL render-quality finding in the catalog. All first-wave candidates have NONE or MINOR challenger findings (except UPL-18 MAJOR, whose v0 scope-cut resolves the MAJOR concern). No new dependencies are required for this wave.

## 4. Assumptions

- `[MUST]` The UPL-18 v0 Taubin lift (second pass `n_iter=40, pass_band=0.05` + bounds `* 1.05`) eliminates the Enriques sawtooth without pushing render time above the ~500ms single-render budget — *spike in Phase 3: measure render time before/after the second Taubin pass on the Enriques canonical sextic via off-screen render; if render time exceeds 500ms, fall back to bounds-padding only and defer the Taubin pass*

- `[MUST]` `Surface` dataclass (frozen=True, AI-8) accepts a new `recommends_backface_culling: bool = False` field without breaking the existing registry or any test — *spike in Phase 3: confirm `@dataclass(frozen=True)` allows default-valued field addition in Python 3.12; verify `VARIETIES` registry still instantiates cleanly*

- `[SHOULD]` The `APP_STYLESHEET` f-string refactor (UPL-1 palette token extraction) can be done without changing any rendered surface colors, dock sizes, or font sizes — the existing behavior is purely preserved while the constants are renamed — *fallback: if any panel visual regression is detected during off-screen smoke renders, revert to literal-by-literal substitution one token at a time rather than a bulk f-string rewrite*

- `[SHOULD]` Moving `plotter.set_background(...)` to `MainWindow.__init__()` (UPL-3) does not interact with the VTK GL context setup timing — the plotter is fully constructed before the call — *fallback: if the background call at init time produces a blank/grey viewport, defer the call to after the first `plotter.render()` using a `QTimer.singleShot(0, ...)`*

- `[SHOULD]` The four proposed per-variety default hex tokens (K3 `#8ab4d4`, Enriques `#c8a880`, CY3 `#4a90d9`, Fano `#7ec8a0`) are visually adequate against the light viewport background `#f0f0f0` as well as the dark `#2f2f2f` — *fallback: substitute any token that fails visual legibility with a slightly more saturated alternative (same hue, +10% L in HSL)*

- `[MIGHT]` The `backface_culling=True` flag (UPL-19 Option a) reduces the Enriques sawtooth visibility independently of UPL-18 — *defer: ship both, but if UPL-19 alone closes the visual complaint sufficiently, the UPL-18 spike may not need a v0 ship*

- `[MIGHT]` Appending `bbox ±a × ±b × ±c` to the status bar (UPL-13) using `mesh.bounds` indices `[1]`, `[3]`, `[5]` (max extents) gives a compact, correct representation for all symmetric surfaces in the registry — *defer: if any asymmetric surface produces a confusing ± readout, extend to `xmin..xmax × ymin..ymax × zmin..zmax` format in a follow-on*

## 5. Objective and Key Results

**Objective:** By 2026-06-13 (end of ~2-week first-wave sprint), the app delivers a visually polished, artifact-free first-launch experience across all four variety families, with no background flash, distinct per-variety surface colors, an Enriques sawtooth-free canonical render, a status-bar spatial readout, and a clean `styles.py` palette-token foundation for second-wave candidates — all while all 120 existing tests continue to pass.

**Key Results:**
1. Off-screen render of `Enriques surface / Canonical sextic  [Fig. 1]` at default parameters produces no visible comb-tooth sawtooth tear in `/tmp/check-enriques.png` (UPL-18 + UPL-19 done).
2. Off-screen renders of the canonical 5-surface set each display a distinct default surface color matching the `VARIETY_DEFAULT_COLOR` map — no two variety families share the same hue — confirmed visually from `/tmp/check-*.png` (UPL-5 done).
3. Status bar after any successful render reads `N vertices, N faces · bbox ±a × ±b × ±c` (UPL-13 done), confirmed by grepping the app's `_render_current` method for the bbox format string.
4. `styles.py` contains a named `PALETTE_LIGHT` dict (or equivalent token structure) with at least 6 named tokens covering viewport background, panel background, value text, muted text, focus ring, and variety-family colors — no raw hex literals remaining for these properties in `styles.py` or `appearance_panel.py` (UPL-1 done).

**Won't:**
- No `QSettings` cross-launch state persistence in this wave (CONTEXT.md §9 deferred; UPL-15 is explicitly second-wave per final-report.md §5.5 and carries a MAJOR challenger penalty).
- No `superqt` / `qtawesome` dependency landing in this wave — first wave explicitly excludes UPL-2 and all candidates that depend on it (UPL-7, UPL-8, UPL-10 icons, UPL-14, UPL-16) to keep the dep surface zero-change.
- No dark-mode toggle (UPL-4) in this wave — dark mode depends on UPL-1 landing AND carries M effort; it is explicitly second-wave per final-report.md §5.5. The first wave lays the palette-token foundation only.

<!-- ROADMAP:section:decompose -->
## 6. Epics

### 6.1 Decomposition technique

Vertical slicing + enabler stories.

### 6.2 Dependency graph

| Epic | Depends on |
|---|---|
| `panel-refresh-2026q2-e1` | — |
| `panel-refresh-2026q2-e2` | e1 |
| `panel-refresh-2026q2-e3` | e2 |
| `panel-refresh-2026q2-e4` | e1 |
| `panel-refresh-2026q2-e5` | — |

### 6.3 Epics

#### `panel-refresh-2026q2-e1` — Launch background flash fix (UPL-3) `[VALUE]`

**Goal:** Eliminate the light-grey-to-dark-grey viewport background flash visible during the first ~500ms of every launch by moving `plotter.set_background(...)` from `AppearancePanel.apply_to_actor()` into `MainWindow.__init__()`, so the intended background is set before any surface render fires.

**Slice:** `app.py` (MainWindow.__init__ — add `set_background` call right after plotter widget construction), `appearance_panel.py` (remove / guard the no-op `set_background` call in `apply_to_actor(None)` path), `tests/` (off-screen smoke render verifying background colour from an out-of-box startup state via `pv.OFF_SCREEN = True`).

**INVEST:** 6/6 — Independent (no code dependency on any other epic; DAG note in final-report §3 confirms standalone), Negotiable (exact call-site can shift to a `QTimer.singleShot(0, ...)` deferral if VTK GL context timing is wrong — section 4 `[SHOULD]` assumption), Valuable (removes the most immediately visible launch defect), Estimable (2-line fix, XS effort), Small (hours, well under 1 week), Testable (off-screen PNG before/after shows colour difference; adversarial review can grep for the moved call).

**Specialist hints:**
- `app.py:_render_current` + `appearance_panel.py:apply_to_actor`: AI-9 — any new `processEvents()` call added here needs the `self._computing` re-entrancy guard; this fix itself does not add one, but the reviewer should confirm none is silently introduced. AI-10 — confirm `_raw_mesh` caching logic is not disrupted by background init order.
- Off-screen render verification: AI-3 — use `pv.OFF_SCREEN = True; pv.Plotter(off_screen=True)` ONLY. Never construct `MainWindow()` under `QT_QPA_PLATFORM=offscreen`. AI-13 — if the background hex is inlined, use 6-digit form (e.g. `#2f2f2f`, not `#2f2f` or similar). Cite UPL-3 (final-report.md §3).

**T-shirt:** S (2-line fix, but full vertical slice with off-screen render verification; realistically 0.5–1 day total including Phase 3–5 pipeline).

**Predecessors:** —

**Acceptance signals:**
- Off-screen render of `K3 surface / Fermat quartic [Fig. 1]` at default parameters shows the dark viewport background (`#2f2f2f` or palette token equivalent) immediately, with no grey flash frame present in `/tmp/check-k3-bg.png`.
- `AppearancePanel.apply_to_actor(None)` at startup no longer silently becomes a no-op that leaves the background unset; confirmed by reading `appearance_panel.py` and verifying the call is either removed or guarded.
- All 120 existing tests still pass.

---

#### `panel-refresh-2026q2-e2` — Named palette token foundation (UPL-1) `[ENABLER]`

**Goal:** Extract every scattered hex literal in `styles.py` and `appearance_panel.py` into a `PALETTE_LIGHT` dict (or equivalent named-constant block) covering at minimum: `BG_VIEWPORT`, `BG_PANEL`, `TEXT_VALUE`, `TEXT_MUTED`, `FOCUS_RING`, and placeholders for per-variety colors — so UPL-5 (per-variety colors) and future dark-mode work (UPL-4) can populate tokens without touching structural code.

**Slice:** `styles.py` (introduce `PALETTE_LIGHT` dict; replace raw hex literals in `APP_STYLESHEET` f-string; include WCAG-precomputed contrast ratio comments for the `TEXT_MUTED` slot and dark-mode placeholder tokens), `appearance_panel.py` (consume palette tokens instead of inline hex; fix the known `#888` short-hex AI-13 violation cataloged as UPL-21 — small enough to absorb here), `tests/` (no new tests needed for a pure token rename; but if `appearance_panel.py` behaviour changes, add a regression smoke).

**INVEST:** 6/6 — Independent (no code dependency on e1 at the code level; DAG notes "can land in parallel with UPL-3" — but brief sequences after e1 for clean layering), Negotiable (scope can stop at `styles.py` only if `appearance_panel.py` changes prove risky — the `[SHOULD]` assumption in section 4 covers this), Valuable (unblocks UPL-5 which is rank-1 RICE; an enabler with a named, immediate downstream value epic satisfies the INVEST-V rule), Estimable (S effort, 1 day), Small (1 week or less), Testable (grep confirms no raw hex literals survive outside the palette dict; off-screen smoke renders of the canonical 5 show no visual regression).

**Specialist hints:**
- `styles.py` + `appearance_panel.py` color flowing into PyVista: AI-13 — all hex literals flowing into `pv.Plotter.add_mesh(color=...)` or `pv.set_plot_theme(...)` MUST be 6-digit. AI-12 — new `TEXT_MUTED` token and any dark-mode placeholder must include a WCAG 2.1 AA computed contrast ratio comment (≥4.5:1 body, ≥3:1 large). The existing `COLOR_MUTED = #5a5a5a` passes on light but fails on dark (`#2f2f2f` background, ~2.5:1) — document this in the placeholder. Cite UPL-1 (final-report.md §3) and UPL-21 (AI-13 cleanup, final-report.md §2 rank 17).
- New UI code (Qt enums): AI-11 — any new `QLabel`, `QSizePolicy`, or alignment call must use fully-qualified form (`Qt.AlignmentFlag.AlignLeft`, `QSizePolicy.Policy.Expanding`). `/frontend-uplift` report file: `.claude/notes/frontend-uplifts/2026q2-panel-refresh/artifacts/final-report.md`.

**T-shirt:** S (1 day for the token extraction; final-report prices E=1).

**Predecessors:** e1

**Acceptance signals:**
- `styles.py` exports a `PALETTE_LIGHT` dict (or named-constant block) containing at least 6 named tokens; no raw hex literals remain in `styles.py` or `appearance_panel.py` for the covered properties.
- The short-hex `#888` in `appearance_panel.py:48` is replaced with `#888888` (6-digit), resolving the AI-13 UPL-21 violation.
- Off-screen renders of the canonical 5-surface set (Fermat quartic, Kummer, Enriques canonical sextic, Hanson quintic, Fano default) show no visual regression from the token rename (colours visually identical to pre-refactor).
- All 120 existing tests still pass.

---

#### `panel-refresh-2026q2-e3` — Per-variety default surface color (UPL-5) `[VALUE]`

**Goal:** Make the first-launch surface color visually distinct per variety family (K3 `#8ab4d4`, Enriques `#c8a880`, CY3 `#4a90d9`, Fano `#7ec8a0`) by adding a `VARIETY_DEFAULT_COLOR: dict[str, str]` map in `styles.py` and wiring `AppearancePanel.set_default_color(...)` to fire whenever the user selects a new variety — so no two variety families share the same default hue at first render.

**Slice:** `styles.py` (add `VARIETY_DEFAULT_COLOR` dict keyed by top-level variety family string — e.g. `"K3 surface"`, `"Enriques surface"`, `"Calabi–Yau 3-fold"`, `"Fano 3-fold"`), `appearance_panel.py` (add `set_default_color(hex: str)` method that updates `_surface_color`, repaints the swatch, and re-applies to the live actor), `app.py` (wire the variety-changed signal → `AppearancePanel.set_default_color(VARIETY_DEFAULT_COLOR[family])`), `tests/` (off-screen render for each of the 4 variety families confirming distinct mesh color; pure PyVista / NumPy, no pytest-qt — AI-2).

**INVEST:** 6/6 — Independent (depends on e2's palette tokens for clean integration, but can be implemented standalone if needed), Negotiable (fallback: if any of the 4 proposed hex tokens fails visual legibility on light background, substitute a slightly more saturated alternative — section 4 `[SHOULD]` assumption), Valuable (rank-1 RICE 30.0 in final-report; biggest first-impression delta in the catalog), Estimable (S effort; final-report prices E=1), Small (1 day), Testable (off-screen render PNGs show distinct colors; grep confirms `VARIETY_DEFAULT_COLOR` is defined with 4 keys).

**Specialist hints:**
- `styles.py` + `appearance_panel.py` + `app.py` render pipeline: AI-13 — the four proposed hex tokens are 6-digit (`#8ab4d4`, `#c8a880`, `#4a90d9`, `#7ec8a0`) — do not shorten. AI-12 — Challenger §4 notes surface color is not text; WCAG AA contrast framing does not apply here. Verify all four tokens are visually legible against the light viewport background `#f0f0f0` in off-screen renders. AI-9 — if `set_default_color` triggers a re-render, it must not bypass the `self._computing` guard in `_render_current`.
- `app.py:_render_current` variety-changed wiring: AI-10 — `set_default_color` must NOT regenerate the raw mesh; it should reapply color to the existing actor (or trigger a re-render using `_raw_mesh`). Off-screen render verification (AI-3) across all 4 families. Cite UPL-5 (final-report.md §4 rank 1). Read `.claude/notes/frontend-uplifts/2026q2-panel-refresh/artifacts/final-report.md` §4 for the full color palette rationale and challenger objections.

**T-shirt:** S (1 day; final-report prices E=1 for S effort).

**Predecessors:** e2

**Acceptance signals:**
- Off-screen renders of the canonical 5-surface set each show a distinct surface color: K3 family surfaces use `#8ab4d4`, Enriques family uses `#c8a880`, CY3 family uses `#4a90d9`, Fano family uses `#7ec8a0`; confirmed visually from `/tmp/check-variety-colors-*.png`.
- No two variety families share the same default hue at first render; confirmed by reading `VARIETY_DEFAULT_COLOR` in `styles.py`.
- All 120 existing tests still pass; new off-screen render tests for the 4 family colors added (pure NumPy/PyVista — AI-2).

---

#### `panel-refresh-2026q2-e4` — Enriques sawtooth visual fix (UPL-19 + UPL-18 spike) `[VALUE]`

**Goal:** Eliminate the comb-tooth sawtooth tear on the Enriques canonical sextic by (a) enabling back-face culling for Enriques surfaces (UPL-19, no spike needed) and (b) applying a second Taubin smoothing pass (`smooth_taubin(n_iter=40, pass_band=0.05)`) plus bounds padding (`bounds * 1.05`) to the Enriques generator (UPL-18 v0 scope-cut) — with a mandatory render-time spike before shipping the Taubin pass to confirm it stays under the ~500ms single-render budget.

**Slice:** `surfaces.py` (Enriques generator: add bounds padding `* 1.05` and second Taubin pass; add optional `recommends_backface_culling: bool = False` field to `Surface` dataclass — section 4 `[MUST]` assumption to spike; set `True` for Enriques subtypes), `app.py` (wire `recommends_backface_culling` from the active `Surface` into `plotter.add_mesh(backface_culling=...)` or equivalent render call), `tests/` (off-screen render of `Enriques surface / Canonical sextic [Fig. 1]` at default parameters; assert mesh has no obvious near-zero-face-area degenerate triangles; spike script measures render time before/after second Taubin pass and writes a timing log to `/tmp/enriques-taubin-spike.txt`).

**INVEST:** 6/6 — Independent (depends on e1 for a stable render pipeline with correct background, so the Enriques PNG comparison is uncontaminated by the flash artifact; code-level no strict dep), Negotiable (UPL-19 back-face culling ships regardless of spike outcome; UPL-18 Taubin pass is gated on the spike — if render time exceeds 500ms, ship bounds-padding only per section 4 `[MIGHT]` assumption), Valuable (the only CRITICAL render-quality finding in the catalog; RICE 11.25 for UPL-18, most dispositive visual evidence in the entire uplift), Estimable (S in challenger's v0 scope), Small (spike + implementation within 2 days), Testable (off-screen PNG diff of Enriques before/after is dispositive; adversarial reviewer can confirm no new degenerate triangles).

**Specialist hints:**
- `surfaces.py` implicit Enriques generator + `Surface` dataclass: AI-6 — Enriques is an implicit surface (marching cubes pipeline + Taubin smoothing); do NOT skip Taubin or switch to the parametric pipeline. The second Taubin pass (`n_iter=40, pass_band=0.05`) stacks on top of the existing pass (`n_iter=20, pass_band=0.1`); apply AFTER the first pass. AI-8 — adding `recommends_backface_culling: bool = False` to the `@dataclass(frozen=True) Surface` must not break the frozen contract or any existing `Surface(...)` instantiation site in the `VARIETIES` registry; spike this first (section 4 `[MUST]` assumption). AI-14 — confirm the generator still returns `pv.PolyData` or raises `ValueError` after bounds padding; bounds `* 1.05` should not push the sampling grid below the `marching_cubes` resolution floor.
- `app.py:_render_current` render pipeline + off-screen verification: AI-9 — if `backface_culling` wiring touches `processEvents()`, apply the `self._computing` guard. AI-3 — off-screen render spike uses `pv.OFF_SCREEN = True`. Cite UPL-18 (final-report.md §4 rank 4) and UPL-19 (final-report.md §2 rank 12). The spike MUST run before the second Taubin pass is committed; output timing to `/tmp/enriques-taubin-spike.txt`. Read `.claude/notes/frontend-uplifts/2026q2-panel-refresh/artifacts/final-report.md` §4 for the full challenger v0 scope-cut rationale.

**T-shirt:** S (UPL-19 is XS; UPL-18 v0 is S; combined with the spike day, total is 1–2 days).

**Predecessors:** e1

**Acceptance signals:**
- Off-screen render of `Enriques surface / Canonical sextic [Fig. 1]` at default parameters (written to "/tmp/check-enriques-post.png") shows no visible comb-tooth sawtooth tear (compare against the pre-fix render evidenced at `renders/enriques-surface-canonical-sextic-node-closeup.png`).
- Spike timing log `/tmp/enriques-taubin-spike.txt` confirms second Taubin pass keeps render time under 500ms; if over budget, commit shows bounds-padding only with a comment deferring the second pass.
- `surfaces.py` Enriques `Surface` entry has `recommends_backface_culling=True`; `app.py` wires this into `add_mesh(backface_culling=...)`.
- All 120 existing tests still pass.

---

#### `panel-refresh-2026q2-e5` — Status-bar spatial bbox readout (UPL-13) `[VALUE]`

**Goal:** After every successful render, append `bbox ±a × ±b × ±c` to the existing status bar text (`{N_verts} vertices, {N_faces} faces · bbox ±a × ±b × ±c`) so researchers can read the spatial extent of the current surface without measuring it from the viewport.

**Slice:** `app.py` (`_render_current`: extract `mesh.bounds` max-extents `[1]`, `[3]`, `[5]` and format into the status bar string immediately after the vertex/face count), `tests/` (assert the status bar string contains the `bbox ±` prefix after a render call — pure PyVista, no pytest-qt; can be verified by calling the generator directly and checking bounds format).

**INVEST:** 6/6 — Independent (no code dependency on any other epic; final-report §4 rank 3 DAG note: "no dependencies"), Negotiable (format can be extended to `xmin..xmax × ymin..ymax × zmin..zmax` if any asymmetric surface produces a confusing ± readout — section 4 `[MIGHT]` assumption), Valuable (direct researcher quality-of-life win; RICE 16.0, rank 3 in final-report), Estimable (XS, ~3 lines), Small (hours), Testable (grepping `app.py` for the bbox format string; off-screen render confirms status bar text).

**Specialist hints:**
- `app.py:_render_current`: AI-9 — this is a read of `mesh.bounds` only, no `processEvents()` addition expected; but confirm the bounds read is positioned after `self._raw_mesh` is assigned (AI-10) so it always reflects the freshly generated mesh, not a stale cached value. AI-14 — if `self._raw_mesh is None` (ValueError path), skip the bbox readout and surface only the error message in the status bar (already handled by existing try/except; confirm bounds read is inside the success branch).
- Test strategy: AI-2 — pure NumPy / PyVista test; call a generator directly, get `mesh.bounds`, assert the expected ± format. No pytest-qt. ~4s test budget. Cite UPL-13 (final-report.md §4 rank 3). Read `.claude/notes/frontend-uplifts/2026q2-panel-refresh/artifacts/final-report.md` §4 for the `mesh.bounds` index rationale and the hover-readout v2 deferral note.

**T-shirt:** S (XS effort — ~3 lines — but include vertical slice through tests and status-bar wiring; total ~half a day).

**Predecessors:** —

**Acceptance signals:**
- After any successful render, the status bar text matches the pattern `N vertices, N faces · bbox ±a × ±b × ±c` (confirmed by grepping `app.py:_render_current` for the bbox format string).
- If `_raw_mesh is None` (ValueError path), the status bar shows the error message only; no `bbox` line is appended.
- All 120 existing tests still pass; at least one new pure-PyVista test asserts the bbox format string for a known surface (e.g. Fermat quartic at default parameters).

<!-- ROADMAP:section:sequence -->
## 7. Prioritization

### 7.1 MoSCoW

| Epic | Tag | Rationale |
|---|---|---|
| `panel-refresh-2026q2-e1` | Must | Foundational; eliminates the most visible launch defect; unblocks e3 color fidelity (no flash contaminates off-screen verification); KR depends on clean viewport background from first render. |
| `panel-refresh-2026q2-e2` | Must | Enabler; KR4 explicitly requires named palette tokens; unblocks e3 (UPL-5 depends on UPL-1 for clean integration); without this, per-variety color ships as ad-hoc inlined hex — defeating the Objective's "palette-token foundation for second-wave candidates". |
| `panel-refresh-2026q2-e3` | Should | Rank-1 RICE (30.0) and KR2 target; depends on e2 landing first; high-impact but can slip to cycle+1 if e2 is delayed without breaking core Objective. |
| `panel-refresh-2026q2-e4` | Must | Only CRITICAL render-quality finding in catalog; KR1 directly targets sawtooth-free Enriques canonical sextic; independent of e2/e3 so no sequencing blocker for Now lane. |
| `panel-refresh-2026q2-e5` | Should | KR3 target; XS effort, no dependencies, but not load-bearing for the Objective's foundational deliverables; can be pulled into Now if capacity allows without disrupting lane balance. |

**Must cap:** 3/5 = 60% (cap: 60%) — *script-validated*

### 7.2 RICE rank (Musts only)

| Rank | Epic | R | I | C | E | RICE |
|---|---|---|---|---|---|---|
| 1 | `panel-refresh-2026q2-e1` | 10 | 1 | 50 | 0.25 | 20.00 |
| 2 | `panel-refresh-2026q2-e4` | 10 | 3 | 50 | 1 | 15.00 |
| 3 | `panel-refresh-2026q2-e2` | 10 | 1 | 80 | 1 | 8.00 |

*Confidence defaults to 50% where no evidence exists. Defaults: e1 (C=50%, 2-source: visual scout GAP-H1 + current-state critic per final-report §3), e4 (C=50%, 1-source render-evidenced per final-report §4 rank 4 — UPL-18 RICE breakdown explicitly states C=0.5). e2 has C=80% anchored to 3-source triangulation per final-report §3 UPL-1 RICE breakdown.*

<!-- ROADMAP:section:lanes -->
## 8. Now / Next / Later

### Now (fully spec'd)

*Sprint window: 2026-05-20 → 2026-06-06 (approx. week 1–2). These two epics have no inter-dependencies and can be developed in parallel or sequentially.*

#### `panel-refresh-2026q2-e1` — Launch background flash fix (UPL-3)

**Stories:**

**`panel-refresh-2026q2-e1-s1` — Move `set_background` call to `MainWindow.__init__`** (XS)

Given the app codebase has `plotter.set_background(...)` called only inside `AppearancePanel.apply_to_actor()`, which is a no-op when called with `None` at startup,
When the developer moves the `plotter.set_background(PALETTE_LIGHT["BG_VIEWPORT"])` (or the raw `#2f2f2f` literal if UPL-1 hasn't landed yet) call to `MainWindow.__init__()` immediately after the plotter widget is constructed,
Then an off-screen render via `pv.OFF_SCREEN = True` of `K3 surface / Fermat quartic [Fig. 1]` at default parameters shows the dark viewport background (`#2f2f2f`) in `/tmp/check-k3-bg.png` without any grey flash frame, and grepping `app.py` confirms `set_background` is called in `__init__` before any `_render_current` invocation.

Specialist: `app.py` MainWindow constructor call-order — AI-9 (confirm no `processEvents()` is silently introduced here); AI-13 (background hex must be 6-digit: `#2f2f2f`). Cite UPL-3, final-report.md §3.

**`panel-refresh-2026q2-e1-s2` — Guard `apply_to_actor(None)` no-op and add off-screen smoke regression** (S)

Given the `set_background` call has been moved to `MainWindow.__init__` (s1 done) and `AppearancePanel.apply_to_actor(None)` at startup previously silently left background unset,
When the developer either removes the `set_background` call from `apply_to_actor` entirely or adds an `if actor is None: return` early-exit guard before it, and adds an off-screen smoke render test (`pv.OFF_SCREEN = True; pv.Plotter(off_screen=True)`) that confirms `plotter.background_color == (47/255, 47/255, 47/255)` after init,
Then `AppearancePanel.apply_to_actor(None)` no longer silently bypasses background setup, the smoke test passes in the existing `~4 s` test budget, and all 120 existing tests still pass.

Specialist: `appearance_panel.py:apply_to_actor` — AI-2/AI-3 (off-screen render only, never `MainWindow()` under `QT_QPA_PLATFORM=offscreen`); AI-10 (confirm `_raw_mesh` caching is not disrupted by the guard change). Cite UPL-3, final-report.md §3.

---

#### `panel-refresh-2026q2-e5` — Status-bar spatial bbox readout (UPL-13)

**Stories:**

**`panel-refresh-2026q2-e5-s1` — Append bbox extent string to status bar after render** (XS)

Given `app.py:_render_current` currently sets the status bar to `{N_verts} vertices, {N_faces} faces` after a successful render, and `self._raw_mesh` is a valid `pv.PolyData` at that point,
When the developer appends ` · bbox ±{a:.2f} × ±{b:.2f} × ±{c:.2f}` to the status bar text using `self._raw_mesh.bounds[1]`, `self._raw_mesh.bounds[3]`, `self._raw_mesh.bounds[5]` (the max-extent half-widths for symmetric surfaces) inside the success branch of the existing try/except,
Then grepping `app.py:_render_current` confirms the `bbox ±` format string is present, the status bar text after any successful render matches the pattern `N vertices, N faces · bbox ±a × ±b × ±c`, and the `ValueError` / error path in the same try/except does NOT include any bbox append.

Specialist: `app.py:_render_current` bounds read — AI-10 (bounds read positioned after `self._raw_mesh` is assigned, not before); AI-14 (if `self._raw_mesh is None`, skip bbox — confirm the read is inside the success branch). Cite UPL-13, final-report.md §4 rank 3.

**`panel-refresh-2026q2-e5-s2` — Add pure-PyVista bbox format regression test** (XS)

Given the Fermat quartic generator (`surfaces.py`) produces a symmetric `pv.PolyData` mesh with known approximate bounds when called at default parameters,
When a pure-PyVista test (no Qt, no `MainWindow`) calls the Fermat quartic generator directly, reads `mesh.bounds`, and formats the `bbox ±` string using the same index formula as s1,
Then the test asserts the formatted string matches `re.fullmatch(r"bbox ±\d+\.\d+ × ±\d+\.\d+ × ±\d+\.\d+", result)` and the test runs within the ~4 s budget with no new Qt dependencies.

Specialist: `tests/` strategy — AI-2 (pure NumPy/PyVista, no pytest-qt); test budget ~4 s for 120 tests; call generator directly, no `MainWindow`. Cite UPL-13, final-report.md §4.

---

### Next (shaped)

*Sprint window: 2026-06-06 → 2026-06-13 (approx. week 2–3). These epics begin after e1 lands on main. No story decomposition — rolling-wave decay.*

#### `panel-refresh-2026q2-e4` — Enriques sawtooth visual fix (UPL-19 + UPL-18 spike)

**Prerequisite:** e1 lands first (stable render pipeline ensures the Enriques PNG comparison is uncontaminated by the background flash artifact). Spike results (section 9) resolve before the UPL-18 Taubin pass is committed.

See section 6.3 for full epic body, INVEST check, specialist hints, and acceptance signals. Summary: enable back-face culling for Enriques surfaces (UPL-19, no spike needed) and apply a second Taubin smoothing pass + bounds padding (UPL-18 v0, gated on spike). T-shirt: S (1–2 days). Acceptance: off-screen render `/tmp/check-enriques-post.png` shows no comb-tooth sawtooth tear; spike timing log confirms render time under 500ms budget.

#### `panel-refresh-2026q2-e2` — Named palette token foundation (UPL-1)

**Prerequisite:** e1 lands first (palette token for `BG_VIEWPORT` should reference the same literal already moved to `__init__` in e1, so the token extraction in e2 is a clean rename).

See section 6.3 for full epic body, INVEST check, specialist hints, and acceptance signals. Summary: extract hex literals from `styles.py` and `appearance_panel.py` into `PALETTE_LIGHT` dict; fix `#888` short-hex AI-13 violation. T-shirt: S (1 day). Acceptance: no raw hex literals remain in covered properties; off-screen renders of canonical 5-surface set show no visual regression.

---

### Later (outcomes only)

*Beyond the 2-week sprint window, or if e2 slips. No story decomposition — outcomes only.*

- `panel-refresh-2026q2-e3` — Make every variety family visually distinct at first launch by wiring `VARIETY_DEFAULT_COLOR` (K3 `#8ab4d4`, Enriques `#c8a880`, CY3 `#4a90d9`, Fano `#7ec8a0`) from `styles.py` through `AppearancePanel.set_default_color(...)` on variety-selection; depends on e2 (palette tokens) for clean integration.

<!-- ROADMAP:section:spikes -->
## 9. Spike lane

Both spikes block `panel-refresh-2026q2-e4` (Enriques sawtooth fix). Run them before or in parallel with Now-lane work so e4 can proceed in the Next window without surprises.

- **Spike: Enriques Taubin-pass render timing** (<=1 day) — validates `[MUST]` from section 4: "The UPL-18 v0 Taubin lift (second pass `n_iter=40, pass_band=0.05` + bounds `* 1.05`) eliminates the Enriques sawtooth without pushing render time above the ~500ms single-render budget." Blocks: `panel-refresh-2026q2-e4`. Method: in a scratch script using `pv.OFF_SCREEN = True`, call the Enriques canonical sextic generator at default parameters with and without the second Taubin pass; record wall-clock time for each via `time.perf_counter`; write timing log to `/tmp/enriques-taubin-spike.txt`. If render time exceeds 500ms, fall back to bounds-padding only. Output: `.claude/notes/roadmaps/panel-refresh-2026q2/spike-enriques-taubin-timing.md`.

- **Spike: `Surface` dataclass frozen-field extension** (<=1 day) — validates `[MUST]` from section 4: "`Surface` dataclass (frozen=True, AI-8) accepts a new `recommends_backface_culling: bool = False` field without breaking the existing registry or any test." Blocks: `panel-refresh-2026q2-e4`. Method: in a scratch script, add `recommends_backface_culling: bool = False` to the `Surface` dataclass definition and attempt to instantiate every existing `Surface(...)` entry in `VARIETIES`; run `python -c "from surfaces import VARIETIES"` to confirm no `TypeError` is raised; run all 120 existing tests (`pytest -q`) to confirm no regression. Output: `.claude/notes/roadmaps/panel-refresh-2026q2/spike-surface-dataclass-field.md`. If the frozen dataclass rejects the addition, evaluate `dataclasses.replace(...)` as a workaround or adding to the parent class.

*Note: The two `[SHOULD]` assumptions (f-string refactor visual regression, `set_background` GL context timing) and both `[MIGHT]` assumptions have documented fallbacks in section 4 and do not require spikes — the fallback paths are low-risk and resolvable during implementation without a dedicated time-box.*

<!-- ROADMAP:section:tracking -->
## 10. Tracking

*Populated by `--gh-issues` flag in Phase 4.*

| Epic / Story | GH Issue | Status |
|---|---|---|

<!-- ROADMAP:section:handoff -->
## 11. Execution handoff

First Now-lane epic: `panel-refresh-2026q2-e1`.

Handoff target: **CONTEXT.md section 6 — the 5-phase implementation pipeline**:

1. **Math research / code archeology** — two parallel Opus agents (research-A: equations / sources / cross-verified references; research-B: visual / code-archeology / library options). Output: a concrete report keyed to this epic's specialist hints.
2. **Implementation + off-screen render verify** — synthesize 4 figures (or equivalent unit of work for non-variety epics), implement, render with `pv.OFF_SCREEN = True` to `/tmp/*.png`, Read the images. Single commit on `main`.
3. **Adversarial review** — Sonnet, six categories (libraries, engineering, gaps, docs, bugs, testing). Read-only; aim for ~10 findings.
4. **Remediation** — Sonnet, grouped MUST FIX / SHOULD FIX / SKIP. Single commit; new tests for new behavior.
5. **UI/UX pass** — Sonnet, two-phase brief (critique 5-10 findings THEN implement 4-7 of them). All existing tests still pass before committing.

Per-epic artifacts produced by the pipeline land under `.claude/notes/` (not in this roadmap doc); commits are direct to `main` per the single-developer cadence documented in CONTEXT.md section 12. This roadmap is the source of truth for *what to build*; the implementation pipeline is the source of truth for *how it landed*.

---

*This roadmap was produced by `/roadmap`. Update directly with edits; for major restructures, re-invoke `/roadmap panel-refresh-2026q2` and the orchestrator will resume at the first unpopulated section.*
