# ADR-005: Schema clarity audit — document all rule fields, formalize traits, specify dispatch

**Date:** 2026-04-21
**Status:** Accepted
**Repo:** ecosystem-standards
**Extends:** ADR-002 (type/trait taxonomy)

---

## Context

A fresh implementer building an evaluator from only the standards
catalog should be able to do so without guessing or reading
evaluator-cog source. The catalog fell short of that bar in several
concrete ways:

- `schema.rule_fields` documented only 1 of 11 fields actually used
  on rules.
- `EVAL-007` referenced a `check_id` field that did not exist; the
  rule `id` was the de facto check identifier.
- Trait exemptions were embedded in prose descriptions, not
  machine-readable.
- `applies_to: [all]` had no specified expansion.
- Four skip/modify mechanisms (`applies_to` non-match, trait
  exemption, per-repo exemption, per-repo deferral) coexisted with
  undocumented precedence.
- Monorepo rules (MONO-001, MONO-002) modified the evaluation of
  sibling rules, expressed only in prose.
- The five `status` values did not specify evaluator behavior;
  `idea` had zero usages and `advisory` had one.
- The `DETERMINISTIC CHECK.` / `LLM CHECK.` prefix convention (a
  load-bearing second schema contract) was not referenced from
  `schema.rule_fields`.
- The `pre-rule` trait was defined but never used.

## Decision

One coordinated revision:

1. **Full `schema.rule_fields` specification.** Every field a rule
   may carry is documented with `required`, `type`, and semantic
   description. The `check_notes` field's schema specifies the
   `DETERMINISTIC CHECK.` / `LLM CHECK.` prefix as canonical.
2. **`id` is the check identifier.** No `check_id` field. EVAL-007's
   description is corrected.
3. **Traits carry structured `exempts:` and `downgrades:`.**
   Prose-only exemption mechanics are replaced by data fields.
   `pre-rule` is removed.
4. **`[all]` is defined** to expand to every member of `repo_types`,
   including future additions.
5. **`statuses:` specifies per-status evaluator behavior.**
   `advisory` and `idea` are removed from the enum; CD-001 is
   converted to `convention`.
6. **Rules gain an optional `modifies:` field** for meta-rules that
   alter sibling rule evaluation (currently MONO-001 and MONO-002).
7. **A new `dispatch:` section** documents the precedence order
   across scope, trait exemption, repo exemption, repo deferral,
   trait downgrade, rule modifier, and default.

## Rationale

The catalog is the core of the system. A field that isn't
documented can't be relied on by a second implementer; a mechanism
expressed only in prose can't be parsed by the evaluator's
dispatcher. The changes here are all either (a) documenting
contracts that were already being honored informally, or (b)
removing machinery that was never used (`pre-rule`, `advisory`,
`idea`).

Nothing in this change alters the set of repos being scanned or the
findings being emitted today. It formalizes the contracts so future
work has a specification to build against.

## Consequences

- **Breaking change.** Consumers of `index.yaml` (notably
  evaluator-cog) must be updated to read the new schema fields.
- **Semantic-release will bump to a major version.** The `feat!:`
  commit footer drives the bump.
- **Per-repo `evaluator.yaml` files do not change.** No repo
  currently declares `pre-rule` or uses removed status values at
  the repo level.
- **The single `advisory` rule (CD-001) becomes a `convention`.**
  Its severity, applies_to, and check behavior are unchanged.
- **Future rule additions** follow the expanded `schema.rule_fields`
  spec and select from three statuses (`requirement`, `convention`,
  `gap`) rather than five.
