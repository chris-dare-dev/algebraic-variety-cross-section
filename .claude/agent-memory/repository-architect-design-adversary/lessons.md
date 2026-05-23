
## Lesson from restructure-full-audit-2026q2-r1 (2026-05-23)

- Anti-pattern caught that escaped audit: A partial monolith extraction (Batch 5 kernels: 401 LOC of 1811 → leaves 1410 LOC, closes zero evaluator FAILs) was dressed up as "addressing FAIL #17" when the current-state auditor's own §13 said "don't fix" for this batch. The audit briefs can contain self-contradictory signals (§4.2 says "cleanest seam" while §13 says "already well-organized, no urgent extraction"). The design-adversary should explicitly cross-check §4 recommendations against §13 "already good" entries before endorsing an extraction.

- Anti-pattern caught that escaped audit: Naming a re-export "NOT a deprecation shim" to avoid the shim lifecycle. For private _underscore symbols the DeprecationWarning cycle is legitimately skippable (R10 exception), but the symbol still needs a MOVES.md entry so future maintainers know the authoritative location. The distinction "permanent re-export vs shim" only matters for the warning; the MOVES.md tracking obligation survives it.

- Anti-pattern caught that escaped audit: Tier-3 rollback using `git log --grep` on an uncommitted commit message pattern. This is fragile — the grep pattern must match exactly, and commit message formats drift. Prefer tag-based Tier-3 rollback: tag after each batch, revert from tag.

- New axis worth adding to the 11: "Partial extraction audit" — for any Extract Module operation, check: (a) does the extraction close at least one evaluator FAIL or fix an invariant violation, or (b) does it reduce the source file below a stated LOC threshold? If neither, the extraction is premature optimization within the conservative-bias brief.

- AI-invariant subtlety: AI-6 (Numba threading layer) has an import-order dependency that becomes a hidden footgun when kernels are extracted to a private module. The config write (`numba.config.THREADING_LAYER = "workqueue"`) must precede `from numba import njit` in the module that houses the kernels — not just in the module that imports the kernel module. This is self-healing if you mirror the surfaces.py pattern but is easy to miss if the implementer just moves the kernel functions and adds a re-export without also moving the config preamble.

- MOVES.md creation: always listed in Phase 8, easy to omit from tree-diff in Phase 2. The design-adversary should check that `+ MOVES.md` appears in the tree diff for the first batch that contains file moves.
