# ADR-001: Federated Evaluation Configuration

**Date:** 2026-04-06  
**Status:** Accepted  
**Repo:** ecosystem-standards  

---

## Context

The MiniAppPolis ecosystem uses `evaluator-cog` to run conformance checks against every repo after each pipeline run. Rules are defined in `ecosystem-standards`, and `ecosystem.yaml` has served as the central registry — tracking which repos exist, their types, and any carve-outs or exceptions to standard rules.

As the number of repos grew, a pattern emerged: `ecosystem.yaml` and the standards repo were being edited frequently — not to update standards, but to accommodate legitimate per-repo exceptions. Examples from the current findings snapshot include:

- `watcher-cog` is a trigger cog, not a pipeline cog — several rules don't apply
- `common-python-utils` and `common-typescript-utils` are shared libraries — observability rules are excepted
- Static sites deployed via Cloudflare Pages don't need `ci.yml`, `prefect.serve()`, or Sentry
- `common-typescript-utils` cannot depend on itself

Each of these exceptions required knowledge that only makes sense in the context of the repo being evaluated. Encoding it centrally meant the standards repo was absorbing change that belonged elsewhere, and the evaluator was generating false positives because it had to infer context from file inventories rather than being told explicitly.

A centralized exception model does not scale. At a small number of repos it is manageable. At any meaningful scale, `ecosystem.yaml` becomes a growing list of special cases and the standards repo becomes a configuration file rather than a stable authority.

---

## Decision

Adopt a **federated evaluation configuration** model:

- `ecosystem.yaml` becomes a **registry only** — a list of repos to evaluate, nothing more
- Each repo owns an **`evaluator.yaml`** file at its root that declares its type, any exemptions, and any metadata the evaluator needs to assess it correctly
- `ecosystem-standards` defines **rules and their default applicability by repo type** — it does not track per-repo exceptions
- `evaluator-cog` clones each repo, reads its `evaluator.yaml`, applies the applicable rules for that type, and stores findings — including exemption justifications — in `pipeline_evaluations`

### `evaluator.yaml` structure (per repo)

```yaml
type: trigger-cog  # pipeline-cog | trigger-cog | shared-library | static-site | standards-repo | api-service

exemptions:
  - rule: CD-015
    reason: "watcher-cog uses direct Prefect API calls rather than prefect.serve() — it is the trigger mechanism, not a flow host"
  - rule: XSTACK-001
    reason: "this repo IS common-python-utils — cannot depend on itself"
```

### `ecosystem.yaml` structure (registry only)

```yaml
repos:
  - name: watcher-cog
    url: https://github.com/kaianolevine/watcher-cog
  - name: evaluator-cog
    url: https://github.com/kaianolevine/evaluator-cog
  - name: common-python-utils
    url: https://github.com/kaianolevine/common-python-utils
```

### Guardrails

- **Exemptions require a reason string.** An exemption without a justification is invalid and treated as a finding.
- **The LLM evaluation layer should flag exemptions that appear unjustified or suspiciously broad.** Repos own their config, but the evaluator retains the right to question it.
- **Exemption justifications are stored in `pipeline_evaluations`** alongside findings, so there is a full audit trail of why rules were skipped — not just that they were.
- **Repo type drives automatic rule applicability.** Most carve-outs should be derivable from type without explicit exemptions — e.g., `static-site` type automatically excepts Prefect, Sentry, and `ci.yml` rules. Explicit exemptions are for edge cases the type alone can't resolve.

---

## Consequences

**Positive:**

- `ecosystem-standards` becomes slow-moving and deliberate — the signal of a healthy standards repo
- Adding a new repo does not require touching any central file beyond the registry
- False positives from context inference are eliminated — the evaluator is told what a repo is rather than guessing from file inventory
- Per-repo exceptions are co-located with the code they describe, making them self-documenting and reviewable in the repo's own PRs
- The system scales to any number of repos without central file bloat

**Negative / trade-offs:**

- Repos can now influence their own evaluation. This is intentional but requires the LLM guardrail to remain active and skeptical of broad exemptions
- Migration work required: existing carve-outs in `ecosystem.yaml` and evaluator logic must be extracted into per-repo `evaluator.yaml` files
- `evaluator-cog` must be updated to read and validate `evaluator.yaml` as part of its clone-and-check flow

---

## Alternatives Considered

**Keep the centralized model, add structured metadata to `ecosystem.yaml`.**  
Adding a `type` field to `ecosystem.yaml` per repo would reduce false positives without full federation. Rejected because it still routes all exception knowledge through a central file — the scalability problem persists even if it is temporarily less noisy.

**No change.**  
The current model works at the current repo count. Rejected because the pattern of frequent standards-repo edits is already established and will only worsen.