# Architecture Decision Records

This directory holds the permanent record of architectural decisions
that shape the MiniAppPolis ecosystem. ADRs capture the *why* — what
forces led to a decision, what alternatives were considered, what
trade-offs were accepted. Enforceable rules derived from these
decisions live in `standards/*.yaml`.

For the process of writing or superseding an ADR, see
[`playbooks/new-adr.md`](../../playbooks/new-adr.md).

---

## Index

| ID      | Status    | Title                                                          |
|---------|-----------|----------------------------------------------------------------|
| ADR-001 | Accepted  | [Federated Evaluation Configuration](ADR-001-federated-evaluation-config.md) |
| ADR-002 | Accepted  | [Type/Trait Taxonomy, Rule Applicability Scoping, and Deferred Keyword](ADR-002-type-trait-taxonomy-and-deferral.md) |
| ADR-003 | Accepted  | [Conformance Checker Architecture](ADR-003-conformance-checker-architecture.md) |
| ADR-004 | Accepted  | [`applies_to` Has a Single Meaning; `evaluator-service` Removed](ADR-004-applies-to-single-meaning.md) |
| ADR-005 | Accepted  | [Schema Clarity Audit — Document All Rule Fields, Formalize Traits, Specify Dispatch](ADR-005-schema-clarity-audit.md) |

---

## Summaries

**ADR-001 — Federated Evaluation Configuration.**
Per-repo `evaluator.yaml` files own type, traits, exemptions, and
deferrals. `ecosystem.yaml` becomes a registry only. Standards files
no longer carry per-repo exceptions. Unblocks scaling to arbitrary
repo count without central-file bloat.

**ADR-002 — Type/Trait Taxonomy.**
Builds on ADR-001. Defines seven canonical repo types
(`pipeline-cog`, `trigger-cog`, `api-service`, `shared-library`,
`static-site`, `react-app`, `standards-repo`) and composable traits
(e.g. `logger-primitive`, `cloudflare-pages`). Introduces the
`deferred` keyword for known-failing rules not yet remediated.
Reduces per-repo exception count from 62 to ~3.

**ADR-003 — Conformance Checker Architecture.**
`evaluator-cog` runs two flows: `pipeline_eval` (behavioral) and
`conformance` (structural). Findings land in `pipeline_evaluations`
with a `source` field distinguishing them. Deterministic checks for
structural rules, LLM checks for soft rules, with the split tagged
in each rule's `check_notes` via the `DETERMINISTIC CHECK.` /
`LLM CHECK.` prefix (see META-005).

**ADR-004 — `applies_to` Has a Single Meaning.**
`applies_to` is optional and means exactly "repo types the
conformance scanner scans for this rule." Rules that aren't repo-
source scans (EVAL-003, MONO-003, EVAL-007) omit the field;
`check_notes` is authoritative for what they read. The
`evaluator-service` pseudo-type is removed from `schema.repo_types`
— it existed only to give the field a target on rules that weren't
actually scanning a repo type.

**ADR-005 — Schema Clarity Audit.**
Extends ADR-002. Documents all 13 rule fields in
`schema.rule_fields` (previously only `applies_to` was documented).
Replaces prose trait-exemption language with structured `exempts:`
and `downgrades:` fields. Removes the unused `pre-rule` trait.
Reduces statuses to three (`requirement`, `convention`, `gap`);
`advisory` and `idea` removed. Adds optional `modifies:` to rules
for meta-rule interactions (MONO-001 / MONO-002). Adds a
`dispatch:` section documenting precedence across scope, trait
exemption, repo exemption, repo deferral, trait downgrade, rule
modifier, and default.

---

## Status legend

- **Proposed** — drafted but not yet committed to.
- **Accepted** — the ecosystem operates on this decision.
- **Superseded** — replaced by a later ADR. The file stays in place
  with a `**Superseded by:** ADR-NNN` line in its header; the
  superseding ADR references it in its Context section. Superseded
  ADRs are preserved — their reasoning is the audit trail for why
  the current approach exists.

Retiring rules, services, or types is different: those are deleted
outright and the git history is the record. ADRs are preserved
because the *reasoning* is the artifact, not the configuration.

See `playbooks/new-adr.md` for the supersession process.
