# ADR-003: Conformance Checker Architecture

**Date:** 2026-03  
**Status:** Accepted  
**Repo:** ecosystem-standards  
**Supersedes:** `docs/standards-checker-decisions.md`

---

## Context

Following the evaluator-cog PoC, the next phase was automated detection of
whether repos meet ecosystem standards. The checker is advisory only — no
automated remediation.

Two complementary layers were identified:

- `evaluator-cog / flows / pipeline_eval` — **behavioral**: did this pipeline
  run correctly?
- `evaluator-cog / flows / conformance` — **structural**: does this repo
  conform to standards?

This ADR records the architectural decisions that shape how conformance
checking is implemented, where findings land, and how LLMs are used.

---

## Decision

### Findings destination

Reuse the existing `pipeline_evaluations` table with
`source=conformance_check`. No new table — the `source` field already exists
and cleanly distinguishes conformance findings from behavioral findings
emitted by the `pipeline_eval` flow (which post as `source=flow_inline`
or `flow_hook`) in downstream views.

### Invocation

Centralized. The conformance flow lives inside `evaluator-cog` and runs on a
Prefect schedule. It clones repos from the ecosystem inventory in
`ecosystem.yaml` and evaluates each one in turn. Per-repo GitHub Actions can
be added later as a thin trigger if needed, but the core logic stays in one
place so a standards change requires only one deploy.

### LLM involvement

Hybrid:

- **Deterministic** checks for structural rules (file presence, `pyproject.toml`,
  CI YAML, AST scanning, test structure).
- **LLM** checks for soft rules (docstrings, dead code, report narrative) and
  to generate actionable suggestions per finding.

Because findings are advisory with no automated remediation, the LLM adds real
value on interpretation and recommendations without risk of acting on bad
output. Deterministic and LLM checks are tagged with the `DETERMINISTIC` /
`LLM` prefix in each rule's `check_notes` so the split is legible at the
standards level.

### First artifact

`src/evaluator_cog/flows/conformance.py` inside `evaluator-cog`, backed by
`src/evaluator_cog/engine/deterministic.py` and `engine/llm.py`.

### Drift detection lives in evaluator-cog

The `check_id` → implementation mapping between this repo and evaluator-cog
is enforced at runtime by evaluator-cog itself, not by a GitHub Actions job
in this repo. This consolidates the ownership of the check-coverage contract
into the same service that executes the checks. See `EVAL-007`.

---

## Consequences

- One deploy surface for conformance logic — changes to evaluator-cog ship
  new checks without touching each repo.
- The standards repo stays YAML-only. No conformance code here, no
  GitHub Actions job for drift, no cross-repo invocation plumbing.
- `source=conformance_check` becomes a first-class value in the
  `pipeline_evaluations.source` canonical-values contract, alongside
  `flow_inline`, `flow_hook`, `prefect_webhook`, and `standards_drift`.
- Soft rules that were previously documented-but-unenforceable become
  partially enforceable via LLM checks, with the trade-off that LLM
  findings are advisory and require human judgment.

---

## Known issues and follow-ups

### FE-003 Tailwind check — `.mjs` config and Astro integration pattern

`website-astro-software` reported a Tailwind WARN despite `tailwindcss` being
present in `dependencies`, `tailwind.config.mjs` existing, `@astrojs/tailwind`
being declared in `astro.config.mjs`, and `postcss.config.cjs` being wired.

- **Root cause (checker):** The deterministic check for FE-003 searches for
  `tailwind.config.js` or `tailwind.config.ts` — it does not match
  `tailwind.config.mjs`. The Astro integration pattern
  (`@astrojs/tailwind` in `astro.config.mjs`) is also a valid signal that
  the check does not evaluate.
- **Decision:** FE-003 `check_notes` to be updated to include `.mjs` config
  filename and the Astro integration pattern as valid signals. Until the
  checker is updated, the finding is a false positive and should be
  suppressed for repos where all three signals are present:
  1. `tailwindcss` in `dependencies`,
  2. `tailwind.config.mjs` at root,
  3. `@astrojs/tailwind` in `astro.config.*`.
- **Secondary note:** FE-003 `applies_to` is `[react-app]` — it should
  not fire for `static-site` repos like `website-astro-software` at all.
  The conformance flow is not filtering rules by `applies_to` correctly.
  Tracked as a bug in `evaluator-cog`.

---

## Addendum — `check_id` convention clarified (2026-04)

The "Drift detection lives in evaluator-cog" section above references
a `check_id` field on rules. No such field was ever added to the
catalog. The intent — a stable identifier linking each rule to its
implementation in evaluator-cog — is satisfied by the rule's own
`id` field, which evaluator-cog's check registry uses as the
registration key. ADR-005 formalized this and removed the
phantom `check_id` reference from EVAL-007. No behavior changed; the
contract clarified.

See ADR-005 for the full schema-clarity audit.
