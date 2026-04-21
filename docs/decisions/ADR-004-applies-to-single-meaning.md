# ADR-004: `applies_to` has a single meaning; evaluator pseudo-type removed

**Date:** 2026-04-21
**Status:** Accepted
**Repo:** ecosystem-standards
**Supersedes, in part:** ADR-002 (specifically, the evaluator pseudo-type
pseudo-type in the type taxonomy)

---

## Context

Three rules carried `applies_to` values that did not match the
meaning `applies_to` held everywhere else in the catalog:

- **EVAL-003** and **MONO-003** declared `applies_to` using a dedicated
  evaluator-only pseudo-type.
- **EVAL-007** declared `applies_to: [standards-repo]` with an inline
  paragraph explaining "`applies_to` points at where the coverage
  contract lives, not where the check runs."

For every other rule, `applies_to` listed repo types the conformance
scanner clones and runs the rule against. For these three, it named
something else — the conceptual target of the rule, or a pseudo-type
used only to satisfy the field's presence.

An evaluator-only pseudo-type had been added to `schema.repo_types` in
`index.yaml` to give the first two rules a type to point at. It did
not satisfy ADR-002's requirement that types are mutually exclusive
and that every repo has exactly one. No repo ever declared
that pseudo-type in its `evaluator.yaml` — evaluator-cog is
correctly a `pipeline-cog`. The pseudo-type existed only to back-fill
a field that shouldn't have needed a back-fill.

## Decision

`applies_to` has one meaning: **the list of repo types the conformance
scanner clones and scans for this rule.** The field is optional.

Rules that are not repo-source checks — rules whose check reads the
pipeline_evaluations table, the evaluator's own check registry, or any
other non-per-repo source — omit `applies_to`. Their `check_notes`
field is authoritative for what they read and when they run.

The three existing rules that fit this shape have had `applies_to`
removed:

- **EVAL-003**: reads pipeline_evaluations for finding quality.
- **MONO-003**: reads pipeline_evaluations grouped by monorepo for
  dedup behavior.
- **EVAL-007**: reads the standards catalog and evaluator-cog's check
  registry for drift.

The evaluator pseudo-type entry has been removed from
`schema.repo_types` in `index.yaml`. It was never a repo type; it
was a workaround.

Workaround prose that existed in EVAL-007's `description` and in all
three rules' `check_notes` to explain the mismatch has been removed.
The rules now read cleanly without needing to justify their
`applies_to` values.

## Rationale

- **One field, one meaning.** `applies_to` is read by humans authoring
  and reviewing rules, by evaluator-cog dispatching checks, and by
  anyone debugging why a check did or didn't run. Overloading it
  multiplies cost at every layer.
- **No new machinery.** An earlier draft of this decision proposed
  adding a `check_mode` field with values `source_scan`,
  `output_scan`, `drift_check`. The three-rule population doesn't
  justify a new field; omitting `applies_to` carries the same
  information with less surface area.
- **The `pipeline_evaluations.source` enumeration already names the
  distinction.** EVAL-003's output is tagged
  `source=conformance_check`, EVAL-007's is `source=standards_drift`.
  The data model already distinguishes these from repo-scan findings.
  The catalog doesn't need a parallel distinction at the rule level.
- **ADR-002 is preserved where it matters and corrected where it
  drifted.** Types remain mutually exclusive. The drift was the
  addition of the evaluator pseudo-type to the type list; removing it
  restores the invariant.

## Consequences

- Readers of the catalog see a consistent `applies_to` semantic.
  Absence of the field is itself informative: this rule is not a
  repo-source scan.
- `schema.repo_types` is a smaller, cleaner list. Every entry is
  actually a repo type.
- Evaluator-cog's dispatch logic must not rely on
  `applies_to` as a universal routing key. Rules without
  `applies_to` are dispatched based on their `check_notes` content.
  Implementation in evaluator-cog is a follow-up commit in that repo
  and is out of scope for this ADR.
- No repo's `evaluator.yaml` changes. The evaluator pseudo-type was never
  declared as a `type:` in any repo.
- The backlog item proposing to flip evaluator-cog's `type:` from
  `pipeline-cog` to the evaluator pseudo-type is removed. It was predicated
  on the pseudo-type existing.

## Breaking change

This is a breaking schema change. Semantic-release will bump to the
next major version. Evaluator-cog's implementation must be updated
in a corresponding commit before the new major version can be
considered fully honored.
