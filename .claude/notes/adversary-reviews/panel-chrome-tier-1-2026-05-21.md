# Adversary review — panel-chrome Tier 1 (+ Tier 2 design)

**Reviewer:** general-purpose adversary
**Date:** 2026-05-21
**Review surface:** Tier 1 implementation (5 files modified + 1 new) + Tier 2 chat-only proposal
**Files audited:**
- `.claude/scripts/frontend-uplift/render-panel-chrome.py` (284 LOC — executed)
- `.claude/scripts/frontend-uplift/ensure-render-up.sh` (139 LOC — read)
- `.claude/commands/frontend-uplift.md` (Phase 1a and 1a' sections — read)
- `.claude/agents/frontend-uplift-visual-scout.md` (panel-chrome instruction paragraph — read)
- `.claude/references/frontend-uplift/source-registry.md` (§4b — read)
- `.claude/references/app-invariants.md` (AI-3 clarifying paragraph — read)
- `appearance_panel.py` (full — read, attribute names verified)
- `view_panel.py` (full — read, attribute names verified)
- `parameters_panel.py` (full — read, API verified)
- `styles.py` (palette and APP_STYLESHEET sections — read)
- `surfaces.py` (VARIETIES registry and FERMAT_PARAMS — spot-checked)

**Script executed:** YES — `render-panel-chrome.py` was executed against the live .venv
(Python 3.x, PySide6 in the repo's venv). Output: 12 PNGs produced, exit 0.
Attribute name bugs confirmed by: (a) hasattr probe run, (b) byte-size comparison of
"empty" vs "populated" ViewPanel captures (identical: 24 838 bytes each).

---

## TL;DR

Three private attribute names in `render-panel-chrome.py` are wrong
(`_wireframe_check`, `_domain_combo`, `_bbox_check`), causing the "populated"
states for `AppearancePanel` (wireframe branch) and `ViewPanel` (domain + bbox
branches) to silently fail at `hasattr()` and produce captures *identical to the
empty state*. The visual scout will believe it has evidence of active checkbox and
combo-box styling when it does not. This is the single most damaging finding
because it corrupts the evidence base for the downstream uplift work. A secondary
concern is that `ensure-render-up.sh` does not add `REPO_ROOT` to `sys.path`
in either heredoc probe, so both probes fail with a cryptic `ModuleNotFoundError`
when the script is invoked from a working directory other than the repo root — a
common scenario for agents dispatched into a worktree. The Tier 2 design has two
independently race-prone pieces (the `osascript` window-finder and the fixed-sleep
screencapture timing) and is missing all platform-guard detail.

---

## Findings by severity

### CRITICAL

**[C-1] Three attribute names wrong in `render-panel-chrome.py` — populated state silently identical to empty for ViewPanel and partially for AppearancePanel**

- **Location:** `render-panel-chrome.py:189` (`_wireframe_check`), `:221` (`_domain_combo`), `:224` (`_bbox_check`)
- **What:** The script uses `hasattr` guards before poking private attributes on the constructed panels. The three attribute names do not match the actual names in the panel classes: the actual names are `_wireframe_cb` (in `appearance_panel.py:158`), `_domain_mode` (in `view_panel.py:160`), and `_bbox_cb` (in `view_panel.py:232`). Because the `hasattr` check silently returns `False` for all three, the "populated" captures for ViewPanel are byte-for-byte identical to the empty captures (confirmed: both 24 838 bytes at default resolution). For AppearancePanel, only the opacity branch succeeds (correct name `_opacity_slider`); the wireframe branch silently skips.
- **Why it matters:** The entire value proposition of the Tier 1 capability is that the visual scout receives pixel-truth on *active* control states (slider at 72%, wireframe checkbox ticked, domain mode set to Sphere, bbox overlay on). With this bug, the scout has no visual evidence of any checkbox or combo-box in an active state. Any uplift findings about "checkbox styling" or "domain combo styling" will be fabricated from code introspection rather than pixel evidence — precisely the gap this work was meant to close.
- **Fix:** In `render-panel-chrome.py:189`, change `_wireframe_check` → `_wireframe_cb`. At `:221`, change `_domain_combo` → `_domain_mode` (and replace `setCurrentText` on the combo with `setCurrentText` on `_domain_mode` — the method call itself is fine). At `:224`, change `_bbox_check` → `_bbox_cb`. Add a CI-style assertion (or at minimum a post-capture byte-size comparison printed to stderr) to catch future drift.
- **Effort:** XS (< 15 min)

---

**[C-2] `ensure-render-up.sh` heredoc probes do not add `REPO_ROOT` to `sys.path` — both probes fail with `ModuleNotFoundError: No module named 'surfaces'` / `'appearance_panel'` when invoked outside the repo root**

- **Location:** `ensure-render-up.sh:47–61` (first probe) and `:97–112` (second probe)
- **What:** Both Python inline scripts (`<<'PYEOF'`) import `surfaces` and `appearance_panel` without any `sys.path` manipulation. The `REPO_ROOT` variable is set at line 14 but never added to `sys.path` in either heredoc. Running the script from any CWD other than the repo root — including from within a Claude worktree dispatched under `.claude/worktrees/agent-*/` — causes `ModuleNotFoundError`. The `2>/dev/null` redirect suppresses the error, so the script reports a generic `[fail] off-screen surface-render pipeline NOT operational` instead of the true cause.
- **Why it matters:** Agents are dispatched into git worktrees (e.g., `.claude/worktrees/agent-a52d8eb85fb5d5d95/`) whose CWD is the worktree root, not the repo root. Both worktrees mount their own `.claude` tree (including the `scripts/` subtree) so the script would run from the worktree. The test confirmed: invoking the venv Python with `from surfaces import VARIETIES` from `/tmp` fails immediately. The preflight intended to be "load-bearing" (per the slash command's anti-pattern table) will silently produce false-negative failures on every agent-dispatched run.
- **Fix:** Prepend `sys.path.insert(0, "<REPO_ROOT>")` at the top of both heredoc Python bodies. The cleanest way: add one line at the top of each heredoc body: `sys.path.insert(0, os.environ.get("AVC_REPO_ROOT", os.getcwd()))` and export `AVC_REPO_ROOT="$REPO_ROOT"` before each if-block. Or simpler: add `cd "$REPO_ROOT"` right after `REPO_ROOT` is set (line 14), since the rest of the script assumes CWD = repo root anyway.
- **Effort:** XS (< 15 min)

---

### HIGH

**[H-1] Docstring says dark-theme gated on `styles.PALETTE_DARK` but code checks `styles.APP_STYLESHEET_DARK` — the gate will silently remain closed when UPL-4 ships**

- **Location:** `render-panel-chrome.py:32–33` (docstring), `:106` (code)
- **What:** The module docstring says "Dark-theme variants are gated on `styles.PALETTE_DARK` existing". The actual code at line 106 does `getattr(styles, "APP_STYLESHEET_DARK", None)`. `PALETTE_DARK` is the data dict; `APP_STYLESHEET_DARK` is the rendered QSS string. The CONTEXT.md §10 / styles.py confirms that UPL-4 will add `PALETTE_DARK` as a parallel dict. If UPL-4 ships `PALETTE_DARK` but generates the QSS string at runtime under a *different* attribute name (e.g. inline, or exports it as `APP_STYLESHEET`'s dark variant), the auto-emit never fires and the docstring's promise ("emitted automatically") is silently broken.
- **Why it matters:** The feature was explicitly sold as "no slash-command edit required when UPL-4 lands." That claim is only true if `APP_STYLESHEET_DARK` is the exact attribute UPL-4 exports. The docstring names `PALETTE_DARK` — the wrong thing — which will confuse whoever lands UPL-4 into thinking they can stop at the data dict without adding `APP_STYLESHEET_DARK`. The false promise could persist through two milestones.
- **Fix:** Either (a) align the docstring with the code: change line 32–33 to say "gated on `styles.APP_STYLESHEET_DARK` existing"; or (b) align the code with the intent and check for `PALETTE_DARK` then derive the QSS in the script rather than waiting for a separate export. Option (a) is the minimal fix; it also should be paired with a note in `styles.py` (near the PALETTE_DARK placeholder) instructing UPL-4 to also export `APP_STYLESHEET_DARK`.
- **Effort:** XS (< 10 min for docstring fix; S if coordinating with UPL-4 plan)

---

**[H-2] `render-panel-chrome.py` does not suppress Qt platform/font warnings — they pollute stdout, corrupting the `[ok]` output the slash command reads**

- **Location:** `render-panel-chrome.py:52` (no warning suppression before QApplication import), confirmed in live run output
- **What:** On macOS with PySide6 under `QT_QPA_PLATFORM=offscreen`, Qt emits at least two categories of noise to stdout/stderr before any user code runs: (a) `qt.qpa.fonts: Populating font family aliases took 116 ms. Replace uses of missing font family "Sans Serif"…`, and (b) `This plugin does not support propagateSizeHints()` (four instances, one per panel shown and hidden). The `[ok] captured 12…` message is buried in this noise. Any orchestration that checks for `[ok]` on stdout by substring would still work, but structured machine-parsing of the output line count or path list is unreliable.
- **Why it matters:** The slash command step 1a' captures the output for display to the user. Qt noise before the success line is confusing in the session output and makes it harder to quickly confirm the capture count. The font warning also signals a real gap: `Sans Serif` isn't resolved, meaning slider labels and group-box headers are being rendered in a fallback font, not the intended QSS font — so the captures may not reflect real-font rendering.
- **Fix:** Add `os.environ.setdefault("QT_LOGGING_RULES", "*.debug=false;qt.qpa.*=false")` before the QApplication import. To suppress `propagateSizeHints`, redirect Qt platform messages using `QLoggingCategory.setFilterRules("qt.qpa.*=false")` after QApplication is created. The font warning requires installing a font that provides `Sans Serif` (e.g. `qt6-base` on Linux, already present on macOS as `Helvetica Neue`; the alias chain may need `fontconfig` on Linux CI).
- **Effort:** S (< 1 hour)

---

**[H-3] `_grab()` calls `app.processEvents()` once — single drain may be insufficient for QScrollArea layout completion in `AppearancePanel`**

- **Location:** `render-panel-chrome.py:143`, `appearance_panel.py:107–110` (QScrollArea wraps the inner layout)
- **What:** `AppearancePanel._build_ui` wraps all controls in a `QScrollArea`. After `widget.show()` and a single `app.processEvents()`, the scroll area's contained widget may not have completed its deferred layout pass. Qt can schedule layout resizes asynchronously, especially when a scroll area computes its content size. In practice the captures look complete in the current run, but under load or on CI this is a timing risk — the grabbed pixmap may show a partially laid-out panel.
- **Why it matters:** A single partial layout in a captured PNG would undermine the scout's ability to comment accurately on spacing between control rows. This is low-probability in interactive use but non-zero in any CI-like headless run.
- **Fix:** Replace the single `app.processEvents()` with a small loop: call `app.processEvents()` twice (or use `QApplication.processEvents(QEventLoop.ProcessEventsFlag.AllEvents, 50)` with a 50ms budget). Alternatively, call `widget.adjustSize()` before grab. The `ensure-render-up.sh` panel probe already calls `processEvents()` once — same gap there.
- **Effort:** XS

---

### MEDIUM

**[M-1] Comment at `render-panel-chrome.py:252` says "K3/Kummer ParamSpec list" but `populated_specs` is loaded from Fermat quartic (line 116) — misleading cross-reference**

- **Location:** `render-panel-chrome.py:252`
- **What:** The comment on the `params_populated` block reads `# Populated state: load the K3/Kummer ParamSpec list`. The actual `populated_specs` variable is populated from `VARIETIES["K3 surface"]["Fermat quartic"]` at lines 116–120. The Kummer surface has 2 params (`mu_squared`, `n`); Fermat quartic has 4 (`c`, `alpha`, `beta`, `gamma`). Using Fermat is the right choice (more params = better populated-state coverage), but the comment is wrong.
- **Why it matters:** A developer debugging the panel captures would look at the comment, expect Kummer's 2-param layout, and be confused by the 4-slider output. Documentation drift in capture harnesses is load-bearing because the harness is itself documentation.
- **Fix:** Change line 252 comment to `# Populated state: load the K3/Fermat quartic ParamSpec list — 4 params (c, α, β, γ)`.
- **Effort:** XS

---

**[M-2] `render-panel-chrome.py:78` — `out_dir.mkdir(parents=True, exist_ok=True)` is not inside a try block; `FileExistsError` (when `out_dir` is an existing file) produces an unhandled traceback rather than a clean diagnostic**

- **Location:** `render-panel-chrome.py:78`
- **What:** If the caller passes a path that already exists as a regular file (e.g., `render-panel-chrome.py ./some-file`), `Path.mkdir(parents=True, exist_ok=True)` raises `FileExistsError`. This propagates out of `main()` as an unhandled exception and Python prints a traceback to stderr, then exits with status 1. The exit code is correct but the diagnostic (`FileExistsError: [Errno 17] File exists: ...`) bypasses the `[render-panel-chrome]` error prefix convention.
- **Why it matters:** Minor, but the script's error-handling convention promises "human-readable diagnostic to stderr so the slash command can surface it" (docstring line 40). A raw traceback violates this.
- **Fix:** Wrap lines 77–78 in a try/except: catch `(FileExistsError, NotADirectoryError)` and call `_err(f"out-dir '{argv[1]}' exists as a file, not a directory"); return 1`.
- **Effort:** XS

---

**[M-3] `2x` captures resize the *widget* rather than capturing a HiDPI pixmap — captures do not reflect actual text anti-aliasing or border-pixel fidelity on a Retina display**

- **Location:** `render-panel-chrome.py:135–154` (DEFAULT_SIZE/HIRES_SIZE + `_grab` comment)
- **What:** The `HIRES_SIZE = QSize(640, 1440)` captures work by resizing the Qt widget to twice the nominal size before calling `QWidget.grab()`. This means all text, borders, and sub-pixel rendering are still at device-pixel-ratio 1 — just physically larger. On a real Retina macOS display, the OS would render at DPR 2 with sub-pixel font hinting and 2× border resolution. The current `2x` captures are simply "larger at the same DPR" — they test layout at a larger nominal size but do NOT test true HiDPI rendering.
- **Why it matters:** A visual scout using these captures to comment on "font crispness at 2x" or "border pixel precision on Retina" is drawing incorrect conclusions. The captures are useful for examining layout breathing room at a wider dock, but they are not HiDPI captures. The docstring comment at line 147 correctly says "For HiDPI *scrutiny* we explicitly resize the widget itself" — the word "scrutiny" softens the claim but the implication of "2x" in the filename is misleading.
- **Fix:** Rename HIRES_SIZE captures from `-2x.png` to `-wide.png` or `-large.png` to signal "larger widget" rather than "HiDPI." Alternatively, document clearly in §4b of source-registry that these are *not* DPR-2 captures. True Retina captures would require `QScreen.devicePixelRatio()` and `QWidget.grab()` with a device-pixel-aware pixmap — only possible on a headed macOS session.
- **Effort:** XS (rename/doc) or M (true HiDPI capture, requires headed session)

---

**[M-4] AI-3 clarifying paragraph's "one-line rule" is stated as cross-platform absolute but the underlying constraint is macOS-specific; Linux with mesa/EGL may support `QtInteractor` under offscreen**

- **Location:** `app-invariants.md:47` ("offscreen is safe whenever the QApplication tree contains *zero* `QtInteractor` instances. The moment one is added, switch to a real window server.")
- **What:** The one-line rule at the bottom of AI-3 is framed without platform qualification. The rationale in AI-2 and CONTEXT.md §10 consistently says the segfault is a *macOS* issue ("Qt + VTK GL context creation is unstable under `QT_QPA_PLATFORM=offscreen` on macOS"). On Linux with mesa software rendering and EGL or osmesa, `pyvistaqt.QtInteractor` can work under offscreen — this is in fact how many CI Docker containers run VTK tests. The absolute rule as written would mislead a Linux contributor into believing even their Docker CI environment cannot use `QtInteractor` under offscreen.
- **Why it matters:** It doesn't affect the current macOS dev flow, but it creates a false invariant that would block a well-intentioned contributor from adding Linux CI VTK rendering. It also means the "one-line rule" is harder to reason about when someone wants to extend the Tier 2 design to Linux.
- **Fix:** Add a platform qualifier: "On macOS, offscreen is safe whenever the QApplication tree contains zero `QtInteractor` instances; the moment one is added, switch to a real window server. On Linux with mesa/EGL, `QtInteractor` may work under offscreen, but this is outside the current repo's tested surface."
- **Effort:** XS

---

**[M-5] Visual-scout prompt's panel-critique instruction lists what to look at but does not alert the scout that "focus rings" will never appear in the static captures**

- **Location:** `.claude/agents/frontend-uplift-visual-scout.md:56`
- **What:** The prompt instructs the scout to "Critique slider rails, value-readout typography, range-label positioning, group-box header weight, button styling (especially the styled `resetDefaultsBtn`), focus rings, spacing between control rows…". Focus rings (Qt's `QFocusFrame` / `:focus` QSS pseudo-class) only appear when a widget has keyboard focus — which requires either tab-navigation or programmatic `setFocus()` + a second `processEvents()` cycle. None of the captures include a focused widget.
- **Why it matters:** If the scout writes "focus rings appear adequate" based on a capture that shows no focus ring (because none was captured), the finding is fabricated. If the scout is honest enough to note "no focus ring was visible," it may flag it as a gap even though a focus ring does exist in the QSS — the scout just wasn't given a capture showing it.
- **Fix:** Add one sentence to the prompt instruction: "Note: no widget is in focus state in these captures; focus rings cannot be assessed from pixel evidence — assess focus rings from the `:focus` rules in `styles.py:APP_STYLESHEET` instead."
- **Effort:** XS

---

**[M-6] `§4b` in `source-registry.md` documents ViewPanel populated state as "domain Sphere, bbox overlay on" but the actual captured PNG is identical to the empty state due to the C-1 attribute name bugs**

- **Location:** `.claude/references/frontend-uplift/source-registry.md:157`
- **What:** The §4b documentation table says the ViewPanel populated state exercises "active combo + checkbox styling." With the C-1 bugs in place, both the domain combo and bbox checkbox use the wrong attribute names, so the populated captures are pixel-identical to empty. The documentation is aspirational, not actual.
- **Why it matters:** Any scout reading §4b will believe the populated PNG shows an active Sphere combo selection. It does not. The documentation misleads the scout into over-counting evidence.
- **Fix:** Fix C-1 first (the attribute names), then verify that the populated captures actually differ from empty by comparing file sizes. Add a verification note to §4b or link to the C-1 fix.
- **Effort:** XS (after C-1 fix)

---

### LOW

**[L-1] `render-panel-chrome.py` does not check `out_dir` writability before entering the capture loop — if the directory is created but not writable, each `pix.save()` returns `False` and raises `RuntimeError` per-capture rather than failing fast**

- **Location:** `render-panel-chrome.py:78`, `_grab` function `:152`
- **What:** The `out_dir.mkdir(parents=True, exist_ok=True)` call succeeds even on NFS mounts where the directory is created but writes are denied. The `pix.save(str(dest))` then returns `False` and the script raises `RuntimeError(f"failed to save PNG: {dest}")` per capture. With 12 captures it produces 12 identical errors.
- **Fix:** After `mkdir`, write a probe file (`(out_dir / ".write_test").touch(); (out_dir / ".write_test").unlink()`) and emit a clear "out_dir not writable" diagnostic early.
- **Effort:** XS

---

**[L-2] Exit code `2` for usage errors is documented only in `_usage()` — the `if __name__` block converts all `RuntimeError` to exit 1, but usage errors are not `RuntimeError` so they exit `main()` with `return 2` — which the `raise SystemExit(main(sys.argv))` correctly propagates. Fine, but the `2` is undocumented in the script's output documentation section of the docstring.**

- **Location:** `render-panel-chrome.py:41` (docstring says "Exits 0 on success, 1 on any panel construction / grab failure" — omits exit code 2)
- **Fix:** Add "2 on usage error (wrong argument count)" to the exit-code docs in the docstring.
- **Effort:** XS

---

**[L-3] No test or CI check verifies `render-panel-chrome.py`'s output PNGs are non-identical across empty/populated states — the C-1 regression survived because there is zero post-capture verification**

- **Location:** No file — absent test
- **What:** AI-2 forbids pytest-qt-style Qt tests. But `render-panel-chrome.py` is a standalone script, not a Qt test fixture. A post-capture smoke check (shell or Python) that asserts `sha256(populated_png) != sha256(empty_png)` for each panel would have caught C-1 immediately. This could live in `ensure-render-up.sh` as a third stage, or as a companion `verify-panel-captures.sh`.
- **Fix:** Add a fourth check to `ensure-render-up.sh` (or a new script) that runs `render-panel-chrome.py` into a temp dir and asserts populated != empty for each panel pair.
- **Effort:** S

---

**[L-4] `render-panel-chrome.py`'s path-listing output has a subtle edge case when `out_dir` has no parent (i.e., `out_dir` is the filesystem root `/`) — `out_dir.parent in path.parents` is always True for root, producing unexpected relative paths**

- **Location:** `render-panel-chrome.py:275`
- **What:** The condition `out_dir.parent in path.parents` — if `out_dir` were `/tmp` (depth 1 from root), `out_dir.parent = /` and `/` is in every path's `.parents`. The output would show paths relative to `/` rather than relative to the parent directory. In practice `out_dir` is never `/` or `/tmp` directly in the slash command usage, but it's a latent correctness issue.
- **Fix:** Replace the conditional with `path.relative_to(out_dir)` (relative to the capture dir itself, not its parent) or just `path.name` for a flat listing.
- **Effort:** XS

---

## Per-axis result (12 axes from the checklist)

### Axis 1 — Correctness bugs in `render-panel-chrome.py`

**CRITICAL [C-1]**: Three private attribute names wrong (`_wireframe_check` should be `_wireframe_cb`; `_domain_combo` should be `_domain_mode`; `_bbox_check` should be `_bbox_cb`). Confirmed live: the `hasattr` guards silently swallow the mismatch, producing captures identical to the empty state for ViewPanel. Confirmed by hasattr probe and byte-size comparison of output PNGs.

Path resolution (`parents[3]` = repo root for the main checkout path) is correct. Return code paths are correct (0/1/2). Error messages follow the `[render-panel-chrome]` prefix convention. `out_dir.mkdir` lack of try-wrap is a LOW issue (M-2 is MEDIUM for the diagnostic quality violation; technically low-criticality). No cross-platform issues introduced (Windows path handled via `Scripts/python.exe` in the venv detection, though `render-panel-chrome.py` itself is not Windows-tested).

### Axis 2 — Correctness bugs in `ensure-render-up.sh`

**CRITICAL [C-2]**: Both heredoc probes lack `sys.path.insert(0, REPO_ROOT)`, causing `ModuleNotFoundError` when the script is run outside the repo root (e.g., from a git worktree CWD).

Trap correctness: the second `trap` on line 95 correctly supersedes the first and cleans both temp files regardless of which exit path is taken. No collision risk: `$$` PID-based naming ensures unique temp files even under parallel agent runs. Heredoc quoting: both Python probes use `<<'PYEOF'` (single-quoted, no shell substitution in the Python body); diagnostic messages use unquoted `<<EOF` with intentional `$PY` interpolation — correct. `set -euo pipefail` interacts correctly with the `if/then/else` structure (exit codes from the Python probes are absorbed by the conditional, not triggering the `pipefail` abort). `git -C "$(dirname "$0")" rev-parse --show-toplevel` pattern works correctly from a worktree: tested — returns the worktree root, which is the correct "repo root" for that checkout.

### Axis 3 — Code structure / readability

**LOW [L-4]**, **MEDIUM [M-1]**: The `_grab` function is clean and single-purpose. The `DEFAULT_SIZE = QSize(320, 720)` / `HIRES_SIZE = QSize(640, 1440)` magic numbers are partially documented (the comment on line 131–133 references "app.py's dock construction (~320 px nominal width)") but the 720 height is not explained. The DRY observation is correct: 12 blocks (3 × 2 × 2) are laid out explicitly rather than data-driven. For the current 3-panel scope this is readable; adding a fourth panel requires manually adding a new block. A data-driven approach (list of `(panel_class, constructor_kwargs, populated_setup, slug)` tuples) would scale better. Not a bug today but HIGH future-proofing risk.

The comment error at line 252 (K3/Kummer vs K3/Fermat) is a MEDIUM documentation issue (M-1).

### Axis 4 — Documentation completeness

**HIGH [H-1]**: Docstring says dark gated on `PALETTE_DARK`, code checks `APP_STYLESHEET_DARK` — breaking the forward-compat promise.

**MEDIUM [M-5]**: Visual-scout prompt doesn't warn that focus rings cannot appear in static captures.

**MEDIUM [M-6]**: §4b documents ViewPanel populated state as "active combo + checkbox styling" but actual captures are identical to empty (consequence of C-1).

**LOW [L-2]**: Exit code 2 undocumented in docstring.

CLI args are documented. §4b describes the capture set adequately as a registry (though it documents aspirational rather than actual behavior until C-1 is fixed). The "dark theme auto-emits" promise is verifiable only if H-1 is fixed first. Exit codes are partially documented.

### Axis 5 — Future-proofing

**HIGH**: The `_opacity_slider`, `_wireframe_cb`, etc. attribute accesses will silently degrade if any panel is refactored (even just a rename). The `hasattr` guard prevents crashes but masks the regression entirely — the captures will just become stale identical-to-empty images with no error signal. There is no canonical mechanism to detect this drift (see L-3).

When UPL-4 (dark theme) lands: the auto-emit will work only if `APP_STYLESHEET_DARK` is exported with that exact name — see H-1. No script edit needed IF the naming convention is honored.

When a new panel is added (e.g., a Layers panel): there is no discoverable extension point. The script hard-codes three panel blocks. Adding a fourth requires editing the script, which is correct coupling but undocumented.

When `ParametersPanel.set_specs` signature changes: the script would fail at the import/call stage, caught by the `except Exception` block with a readable message. Relatively safe.

When a panel gains an external dependency (e.g., KaTeX overlay via `QtWebEngineWidgets`): the `MagicMock()` plotter may not satisfy the new dependency's type-checking at construction time, causing a hard failure. This is acceptable (fail loudly).

### Axis 6 — Test coverage

**LOW [L-3]**: No test exists for `render-panel-chrome.py`'s output integrity. AI-2 forbids pytest-qt, but `render-panel-chrome.py` is a standalone script whose output can be checked with a pure shell assertion (compare hashes of populated vs. empty PNGs). The entire C-1 class of regression is undetectable without such a check.

### Axis 7 — Error handling / user experience

**CRITICAL [C-2] (via ensure-render-up.sh)**: `ModuleNotFoundError` is suppressed to generic failure message.

**MEDIUM [H-2]**: Qt platform/font warnings pollute stdout, obscuring the `[ok]` output.

`out_dir` as a file: raises unformatted `FileExistsError` — LOW/MEDIUM (M-2). Disk-full: `pix.save()` returns `False` → `RuntimeError` per capture — acceptable (12 identical errors is noisy but not silent). `surfaces.py` import failure: caught by broad `except Exception` with readable diagnostic. PySide6 missing: caught by the inner `try/except ImportError`. pyvistaqt not installed: not needed by this script (panels don't import it) — NONE.

### Axis 8 — Honesty of the AI-3 clarifying paragraph

**MEDIUM [M-4]**: The "one-line rule" at the bottom of the clarifying paragraph ("The moment one [QtInteractor] is added, switch to a real window server") is stated as cross-platform absolute but the underlying constraint is macOS-specific. Linux with mesa/EGL can support `QtInteractor` under offscreen. The rule should add a platform qualifier to avoid misleading Linux contributors. The rest of the AI-3 clarifying paragraph is accurate: the distinction between `MainWindow` (forbidden) and pure-Qt panel widgets (allowed) is correctly drawn and consistent with the code.

Does the paragraph match CONTEXT.md §10 and AI-2? Yes: CONTEXT.md §10 correctly says "Qt + VTK GUI segfaults under offscreen on macOS" and the AI-3 update is coherent with that. The one-line rule is a simplification that loses the platform qualifier present in the supporting text.

### Axis 9 — Tier 2 design honesty

**CRITICAL (design only)**: The `osascript` window-finder strategy `tell app "System Events" to id of window 1 of (first process whose frontmost is true)` finds the *frontmost process's first window*, not the AVC window by title. If the user switches focus during the 1.8 s sleep, or if the AVC window is never brought to front during launch, the captured window ID may belong to the terminal, VS Code, or another app entirely. The correct approach is to find the process by PID (`first process whose unix id is <PID>`) rather than frontmost status.

**HIGH (design only)**: The 1.8 s sleep before `screencapture` is a hard race condition. VTK render initialization (VTK OpenGL context + shader compilation on first `show()`) on a loaded system can take 3–5 s. The surface would not have loaded yet, and the capture would show the empty "Choose a variety to begin" state. This timing must be driven by app readiness signaling (e.g., a watchfile written by `AVC_AUTO_QUIT_AFTER` on first render complete, or polling for the window title change).

**HIGH (design only)**: The design proposes `AVC_AUTO_PRESET` + `AVC_AUTO_QUIT_AFTER` env-var hooks in `app.py`. The AI-9 guard (`self._computing`) wraps `_render_current`. If `AVC_AUTO_PRESET` triggers a surface render in `__init__` before the guard is initialized, or if the env-var hook triggers a second render before the first completes, the re-entrancy guard would need to be set before any auto-render call. The design document does not address this; it's a medium-probability re-entrancy bug.

**HIGH (design only)**: macOS Screen Recording permission is required to use `screencapture -l <window-id>`. The first time this runs, macOS will show a permission prompt — but only if the invoking application (Terminal, Claude Code) is the one requesting screen recording. In a headless or SSH session, the prompt would be silently suppressed and `screencapture` would fail. The design says "refuse to run in CI / SSH" but doesn't address the Screen Recording permission grant flow for first-time interactive use.

**MEDIUM (design only)**: The `--live-chrome` flag needs to propagate from the slash command invocation through the orchestrator all the way into the subprocess call. The design mentions it as an "opt-in flag" but gives no detail on how it travels from the user's `/frontend-uplift <id> --live-chrome` through `frontend-uplift.md`'s step 1a' block to the render script. This is implementation detail, not a correctness flaw, but worth calling out as a gap.

**MEDIUM (design only)**: `screencapture -l <window-id>` on macOS Retina captures at device pixel ratio 2, producing a 2x-pixel image. This is actually the correct behavior for HiDPI capture (unlike Tier 1's fake-2x approach). However, the design should document this explicitly and set a consistent expected capture size.

**LOW (design only)**: The design is explicitly macOS-only. CONTEXT.md §3 / §9 confirm the app is macOS-primary, so this is acceptable. The cross-platform interaction is: on Linux, `--live-chrome` should either be silently ignored (returning "live chrome not available on Linux") or it should fall through to the Tier 1 panel captures. The design does not specify which.

### Axis 10 — The "view the full app frontend" production gap

See expanded section below.

### Axis 11 — License / dependency surface

**NONE**: `render-panel-chrome.py` imports only `os`, `sys`, `pathlib.Path`, `unittest.mock.MagicMock` (all stdlib) plus `PySide6` and the repo's own panel modules. No new dependencies introduced. The proposed Tier 2 uses `screencapture` and `osascript` (macOS system tools, no license concern). LGPL/PySide6 redistribution implications are pre-existing and unchanged by this work.

### Axis 12 — Maintenance / sequencing

**NONE** for the main composition story: the script composes cleanly with `init-uplift.sh` (idempotent) and `checkpoint.py` (pure-state, doesn't care about PNG output). It runs after the preflight `ensure-render-up.sh` (Phase 1a) and before agent dispatch (Phase 1b) — the timing is correct. The visual-scout's prompt already references `{RENDER_DIR}/panels/` so the scout will look in the right place.

Running the script ad-hoc (outside `/frontend-uplift`) produces useful output: the 12 PNGs are self-contained and labeled by panel/theme/state/resolution. No dependence on state.json. This is good.

The Phase 1a/1a' wording in `frontend-uplift.md` is clear that both run before agent dispatch. The only ordering concern: if the Phase 1a preflight fails, Phase 1a' is never run — but this is intentional (don't capture panels if the Python environment is broken).

---

## The production gap (axis 10, expanded)

### What an LLM still CANNOT see after Tier 1 + Tier 2

**Tier 1 alone (panel-only static captures):**

1. **The 3D viewport at all.** Tier 1 captures the *panel chrome* only — the `QtInteractor` viewport, VTK toolbar overlays, orientation marker, and axis widget are entirely absent. The scout has no pixel evidence of the app's headline feature.
2. **Panels in their actual dock context.** The captures are standalone QWidget grabs, not the panels embedded in `QDockWidget` with a dock title bar, resize handle, and the font/color of the dock title set by `APP_STYLESHEET`'s `QDockWidget::title` rule. The dock chrome is invisible to Tier 1.
3. **Splitter handles + dock floats/tabs.** No capture shows what happens when the user detaches a dock or floats a panel.
4. **Interactive state transitions.** Slider drag (hover + drag cursor), button hover, focus-on-tab, radio button press animation — all invisible. Static captures are frozen frames of a "just shown, never touched" widget.
5. **Focus rings.** The `styles.py` QSS has `:focus` rules for `QSlider` and `QComboBox`. These never appear in any capture because no widget is programmatically focused (see M-5).
6. **Disabled state.** The reset button (`resetDefaultsBtn`) appears disabled in `parameters-light-empty-*.png` — this IS captured. But the slider in disabled state (domain clip slider when mode=Off) is NOT captured because the ViewPanel populated attempt silently fails (C-1).
7. **Tooltips.** Qt tooltips require a `QHelpEvent` on `QEvent.Type.ToolTip`, which can't be synthesized in an offscreen session without a windowing system event queue. None of the capture methods give tooltip pixel evidence.
8. **Color-picker modals.** `AppearancePanel` has "Surface…" and "Background…" buttons that open `QColorDialog`. The dialog chrome is entirely uncaptured.
9. **Screenshot dialog.** `ViewPanel`'s "Screenshot…" button opens a `QFileDialog`. Uncaptured.
10. **Status bar.** The main window's status bar (surface name, point count, timing) is a `MainWindow`-level widget, not part of any panel. Tier 1 never sees it.
11. **Multi-monitor / window-resize behavior.** The dock layout at different main-window sizes is invisible to both tiers. Whether the panels reflow correctly at narrow widths is not captured.
12. **Keyboard focus order.** An LLM cannot tab through the app and observe which widget receives focus in which order.
13. **Theme transitions / animations.** No animation is in the current app, but any future animation work (INT-24 camera transitions, INT-90 parameter-sweep) would be invisible to static captures.
14. **Real surface + panel TOGETHER.** Tier 1 uses `MagicMock()` plotters. The actual visual integration — panel controls reflecting a loaded surface's state (color swatch showing the applied surface color, domain slider range matching the surface's natural extent) — is never captured.

**Tier 2 adds (when operational):**

15. **The integrated MainWindow chrome** (viewport + all panels + status bar + title bar) — but only as a single composite screenshot, not decomposed.
16. **A surface actually loaded in the viewport** — but only the first preset loaded by `AVC_AUTO_PRESET`, at first-render state (no user interaction).

**What Tier 2 still cannot provide:**

17. The viewport after domain clip is applied (clip boundary wire overlay + clipped mesh together).
18. The viewport with scene aids toggled on (bounding box, grid, axes orientation widget).
19. Any hover state (buttons, swatches, sliders).
20. Any focused-widget state in the integrated window.
21. The wireframe rendering mode (Tier 2 loads the surface once at default Phong mode).
22. Error states: the status bar message after a parameter combination that yields `ValueError("No real zero set...")`.
23. The warning-state status bar (the ⚠ prefix for Dwork conifold warning).

### Tier 3 design sketch

A production-grade "LLM sees the full app frontend" capability would require:

**Tier 3A — Programmatic interaction replay (high value, medium effort)**

Extend `render-panel-chrome.py` with a `--with-interaction` flag that, after showing each panel, programmatically:
- Sets keyboard focus on each interactive control (`slider.setFocus()`)
- Simulates a mouse-press-release on the opacity slider (at 72%) using `QTest.mousePress` / `QTest.mouseRelease` (from `PySide6.QtTest`, which is LGPL and doesn't require a window server for QWidget-level events)
- Calls `widget.grab()` between each state change

This would capture: hover styles (requires `QTest.mouseMove`), focus rings (requires `setFocus()`), active slider track fill. No real window server needed for widget-level QTest events. Scope: ~1 day.

**Tier 3B — Headed composite capture with programmatic surface loading (medium value, medium effort)**

The Tier 2 headed launch with `AVC_AUTO_PRESET`, but improved:
- Drive app readiness via a watchfile (app writes `.avc_ready` on first successful render), not a fixed sleep
- Use `osascript` to find the window by PID (not by frontmost), avoiding the race condition
- Capture a sequence: (a) surface loaded, camera reset; (b) domain clip applied (Sphere, radius 2.5); (c) wireframe mode; (d) scene aids toggled on
- Write each capture in sequence to a timestamped directory
- Compose the interaction replay using `QTest` events piped into the subprocess or via subprocess stdin if the app grows a `--replay-events` mode

Scope: ~2–3 days.

**Tier 3C — Accessibility tree traversal (low effort, high signal for tab-order and tooltip coverage)**

Use `AT-SPI2` (Linux) or macOS `Accessibility Inspector` APIs to enumerate the accessible widget tree from outside the process. This gives tab order, role/state of each control, and tooltip text without screen recording. Python bindings exist (`pyatspi` on Linux; `AppKit.NSAccessibility` on macOS). The LLM reads the accessibility tree as structured data, not PNGs — complementary to visual evidence.

Scope: ~1 day per platform.

**Minimum viable Tier 3 (recommended next step):**

Fix C-1 (attribute names, XS), then add programmatic `setFocus()` + `QTest.mousePress` before each `_grab` call for the single most informative state (opacity slider at 72% + focused). This gives: correct populated states for all three panels + one focused-slider capture. Total scope: XS for fix + S for the QTest extension.

---

## Recommended remediation order

1. **Fix C-1** — wrong attribute names in `render-panel-chrome.py:189,221,224` (addresses: C-1, M-6, visual-scout evidence quality). **XS effort. Current PR.**

2. **Fix C-2** — add `sys.path.insert(0, "$REPO_ROOT")` to both heredoc probes in `ensure-render-up.sh` (or `cd "$REPO_ROOT"` on line 15) (addresses: C-2). **XS effort. Current PR.**

3. **Fix H-1** — align docstring to say `APP_STYLESHEET_DARK`, and add a note to `styles.py`'s PALETTE_DARK placeholder instructing UPL-4 to also export `APP_STYLESHEET_DARK` (addresses: H-1). **XS effort. Current PR.**

4. **Fix M-4** — add platform qualifier to AI-3's one-line rule (addresses: M-4). **XS effort. Current PR.**

5. **Fix M-5** — add focus-ring caveat to visual-scout prompt (addresses: M-5). **XS effort. Current PR.**

6. **Fix M-2** — wrap `out_dir.mkdir` in try/except (addresses: M-2). **XS effort. Current PR.**

7. **Fix M-1** — correct comment on line 252 (K3/Kummer → K3/Fermat quartic) (addresses: M-1). **XS effort. Current PR.**

8. **Fix H-2** — suppress Qt platform/font warnings in `render-panel-chrome.py` using `QT_LOGGING_RULES` env var (addresses: H-2). **S effort. Current PR or immediate follow-up.**

9. **Fix H-3** — add second `processEvents()` call or `widget.adjustSize()` before each `grab()` (addresses: H-3). **XS effort. Follow-up.**

10. **Add populated-state verification** — shell assertion in `ensure-render-up.sh` or a separate script that confirms `sha256(populated) != sha256(empty)` per panel (addresses: L-3). **S effort. Follow-up.**

11. **Fix M-3** — rename `*-2x.png` to `*-wide.png` or document the non-HiDPI nature of these captures (addresses: M-3). **XS effort. Rename is breaking for any existing downstream consumers; do in a coordinated commit with §4b update.**

12. **Tier 2 design** — before any implementation, replace the `osascript frontmost` window-finder with PID-based window lookup, and replace the fixed 1.8 s sleep with a watchfile-based readiness gate (addresses: axis-9 CRITICAL and HIGH design flaws). **L effort overall. Future milestone.**
