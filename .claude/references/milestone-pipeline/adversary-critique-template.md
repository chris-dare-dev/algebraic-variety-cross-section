# Adversary critique — {SUBJECT}

**Reviewer:** milestone-adversary-critic (read-only) | **Date:** {ISO_DATE} | **Subject:** {SUBJECT_DETAIL}

> **Format reference**: see `.claude/references/critique-format.md` for the
> canonical section structure, severity rubric (CRITICAL/HIGH/MEDIUM/LOW
> with examples), and the per-finding template format.  This file is the
> per-invocation entry point — fill in the placeholders below, drop any
> empty severity sections (write `None.` in their place), and use the exact
> per-finding shape shown below.

Placeholders: `{SUBJECT}` is a short noun phrase ("Enriques sawtooth lift",
"Fano 3-fold default-color tokens"); `{SUBJECT_DETAIL}` is the commit range
/ branch name / milestone id; `{ISO_DATE}` is `YYYY-MM-DD`.

---

## Executive summary

{3-5 sentences.  Open by naming the most-severe finding (short title +
location).  State total severity counts ("Two HIGHs, no CRITICALs, three
MEDIUMs").  Close with overall risk ("Safe to merge after the HIGHs
rectify" / "Block merge until C1-C3 close" / "Foundation sound; the gaps
are forward-looking, not blocking").}

---

## Critical findings (must-fix before this can ship)

> Reserve CRITICAL for: panel segfault, AI-1 stack violation
> (Mayavi/Plotly/k3d/raw-VTK import), AI-3 offscreen-MainWindow construction,
> AI-4 clip_box-on-PolyData regression, a math claim that's actually false
> (AI-15), or a generator that raises something other than ValueError on
> empty field (AI-14 contract violation).  If none, write `None.` — do
> NOT reach down to elevate a HIGH.

### CRITICAL — {short title}

**Where:** `{path}:{line}` (or "no specific file" for cross-cutting findings)
**Evidence:** {verbatim quote, off-screen-render path, or 1-2 sentence observation citing the actual code or behavior}
**Why it matters:** {1-2 sentences on user impact / risk / which app invariant is breached}
**Suggested fix:** {1-2 sentences — surface the direction, NOT a full implementation plan}

### CRITICAL — {short title}

**Where:** `{path}:{line}`
**Evidence:** {...}
**Why it matters:** {...}
**Suggested fix:** {...}

{If none, replace this whole section with a single line: `None.`}

---

## High findings (should-fix this iteration)

> HIGH = real bug class.  Examples for this repo: clip_scalar without
> `scalars=` keyword (AI-5); Hanson normals regressed to
> `consistent_normals=True` (AI-7); processEvents without `_computing`
> guard (AI-9); new generator without smoke test in
> tests/test_mesh_generators.py; tooltip missing AI-15 disclaimer on a
> non-compact-variety figure; short-hex flowing into PyVista (AI-13).

### HIGH — {short title}

**Where:** `{path}:{line}`
**Evidence:** {...}
**Why it matters:** {...}
**Suggested fix:** {...}

### HIGH — {short title}

**Where:** `{path}:{line}`
**Evidence:** {...}
**Why it matters:** {...}
**Suggested fix:** {...}

{Continue as needed.  If none, replace section body with `None.`}

---

## Medium findings (nice-to-fix)

> MEDIUM = correctness edge or maintainability hit.  Examples for this
> repo: shorthand Qt enum in new code (AI-11); missing
> `tests/test_parameters_panel.py:ALL_PARAM_SPECS` entry for a new
> ParamSpec; new color literal not in styles.py; tooltip slightly clipped
> in the dropdown; missing non-compactness warning on a parameter range
> that's borderline.

### MEDIUM — {short title}

**Where:** `{path}:{line}`
**Evidence:** {...}
**Why it matters:** {...}
**Suggested fix:** {...}

### MEDIUM — {short title}

**Where:** `{path}:{line}`
**Evidence:** {...}
**Why it matters:** {...}
**Suggested fix:** {...}

{Continue.  If none, `None.`}

---

## Low findings (cosmetic / future iteration)

> LOW = belt-and-suspenders.  Wrong variable name; magic number without a
> comment; missing CONTEXT.md section 8 entry on a load-bearing bug fix;
> docstring typo.  Never block merge on a LOW.

### LOW — {short title}

**Where:** `{path}:{line}`
**Evidence:** {...}
**Why it matters:** {...}
**Suggested fix:** {...}

### LOW — {short title}

**Where:** `{path}:{line}`
**Evidence:** {...}
**Why it matters:** {...}
**Suggested fix:** {...}

{Continue.  If none, `None.`}

---

## What was done well

> REQUIRED.  Specific, real praise — empty/generic makes the critique
> read as adversarial-for-its-own-sake.  Aim for 5-10 bullets, each
> citing a concrete decision ("Reused `_marching_cubes_to_polydata`
> rather than reimplementing the zero-crossing pre-check"; "Tooltip
> honestly disclaims that the rendered surface is the Endrass-normalized
> variant, NOT Barth's classical 65-nodal sextic"; "ParamSpec range
> capped at alpha = -1.0 to keep the surface compact per CONTEXT.md
> section 5.1").

- **{Specific positive 1.}** {1-2 sentence elaboration on why it was done correctly.}
- **{Specific positive 2.}** {...}
- **{Specific positive 3.}** {...}
- **{Specific positive 4.}** {...}
- **{Specific positive 5.}** {...}

---

## Recommended rectification order

> Order by severity, then by fix efficiency.  Group findings that share a
> root cause (two AI-13 short-hex violations in different files are one
> rectification — batch them).  Actionable order: a rectifier walks
> top-to-bottom and ships fixes in sequence.

1. **Fix the CRITICALs first.** {One sentence on why and what the unified fix looks like.}
2. **Fix the HIGHs.** {If two HIGHs share a root cause, say so explicitly: "Same two-line change in both call sites; write one regression test that covers both."}
3. **Batch the MEDIUMs by file or area when possible.**
4. **LOWs are optional follow-ups** at the maintainer's discretion.

---

*End of critique.  Mandatory rectification: all CRITICALs and HIGHs.
Everything else is optional but recommended before milestone close.*
