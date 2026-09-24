# ADR-010: Infrastructure Lives in One Repository, With Its State Remote

**Date:** 2026-09-24
**Status:** Accepted
**Repo:** ecosystem-standards
**Depends on:** ADR-009 (pipeline cogs run on Lambda behind their own queue)
**Amends:** ADR-009 — its clause that each pipeline cog's queue and function
are "declared in the repo's `infra/`"

---

## Context

ADR-009 put each pipeline cog's runtime in the cog's own `infra/`. Three
cogs later that meant three copies of one template (about 800 lines each,
already drifting), three local Terraform states on one workstation, and
secrets passed to Terraform as variables — so every Lambda secret sat in
plaintext in a state file and in every plan. The account's shared
resources (the budget, the GitHub OIDC provider, the API's producer user)
lived in evaluator-cog's state behind `create_*` flags every other cog set
to false.

The principle that forced the change: nothing important lives on a
workstation. Local state failed it outright, and moving state to a bucket
exposed the rest — secrets in state, singletons in a cog, and one template
copied per cog.

---

## Decision

**Infrastructure lives in mini-app-polis/infra: one Terraform root, one
remote state, one module for every pipeline cog. Cog repositories own
their code.**

- **State** is in S3, versioned, with S3-native locking. The bucket is
  managed by the root that uses it.
- **Secrets never pass through Terraform.** Doppler's `prd` config syncs to
  SSM Parameter Store under `/mini-app-polis/prd/`; each worker loads the
  parameters its module block names, at cold start, through
  `mini_app_polis.ssm_secrets`. Its role may read those and no others.
  Terraform holds names, never values (CD-011).
- **One module per cog.** `modules/cog-worker` declares a cog's queue,
  dead-letter queue and alarm, function, event source mapping, and the
  role its CI deploys code through. `cogs.tf` calls it once per cog.
- **The account's shared resources** are in `account.tf`, once.
- **Changes** plan on pull requests from `dev` and apply on merge to
  `main` through a GitHub OIDC role scoped to one environment. The merge
  is the approval. A plan that destroys or replaces anything is refused
  unless the pull request is labelled `allow-destroy`.
- **Cogs deploy code only**, through `UpdateFunctionCode`, as before.
- **A new repository type, `infrastructure`**, for a Terraform root at a
  repository's root.

**Each evaluation reads only its own repository**, so every rule that
touched a cog's `infra/` is checked where its facts now live:

| Rule | Cog (`pipeline-cog`) | mini-app-polis/infra (`infrastructure`) |
|---|---|---|
| PIPE-016 | No Prefect dependency | — |
| PIPE-017 | The handler returns `batchItemFailures` | `ReportBatchItemFailures`, redrive to a DLQ, visibility outlasts the timeout — once, on the module |
| PIPE-018 | — | Every module call states exactly one concurrency ceiling |
| CD-010 | Layers 2 and 3 | Layer 1: the DLQ alarm has an action |
| CD-024 | — | Functions and module calls set memory and timeout |
| CD-027, CD-028, SEC-008 | — | At the repository root, including modules |

Two facts neither side can see alone are not rule checks:

- **That a cog is declared at all.** A cog with no module block has no
  function to deploy to, so its deploy job fails. That failure is the
  check.
- **That the cog's deploy job matches its module block** (handler,
  architecture, runtime). The fix is one copy, not a comparison: the
  shared deploy workflow can read them from the function itself. Until it
  does, the match is a comment in each `ci.yml`.

**Terraform, not CloudFormation.** Weighed explicitly, because the first
decision (evaluator-cog `docs/aws-foundation.md`) compared Terraform only
with click-ops. CloudFormation would hold state for free and roll a failed
update back atomically. Terraform was kept because the infrastructure
reaches past AWS (GitHub, Doppler and Cloudflare all have providers);
"CI owns the code, Terraform owns the configuration" is one
`ignore_changes` here, where CloudFormation expects code to ship through
the stack — widening CI's permissions or living with permanent drift; and
switching would rewrite working infrastructure to avoid one bucket.

---

## Consequences

**Positive**

- Nothing the fleet depends on lives on a workstation. The admin keys are
  break-glass only.
- No secret is in Terraform state, in a plan, or in a Lambda's configured
  environment. Lambda's 4 KB environment limit stops mattering.
- One module: a fix to how every cog is wired is made once. A new cog is a
  module block plus its secrets' names.
- The rules that describe the runtime are checked once, on the module,
  rather than three times on copies of it.

**Negative**

- A cog repository no longer shows its own infrastructure; it is one
  repository away.
- Handler and architecture are stated twice — the cog's deploy job and its
  module block — until the deploy workflow reads them from the function.
- Repositories created after GitHub's change present an id-based OIDC
  subject (`repo:owner@id/name@id`). The cog module's deploy-role trust
  matches the older `repo:owner/name` form, which fits the three existing
  cogs; a new cog needs the id-based form.

---

## Alternatives Considered

**A shared module, with each cog keeping its own root and state.** The
first plan. It kept infrastructure beside code, but needed a versioned
module repository, four states, moving the account's singletons between
states, and a second copy of every rule reader. The split existed only
because each cog's secrets had to reach Terraform; with secrets out of
Terraform the reason was gone.

**Letting a cog's evaluation read mini-app-polis/infra.** It would have
kept "this cog is declared" and "the deploy job matches" as rule checks.
Rejected to keep every evaluation independent of every other repository;
the deploy job's failure covers the first, and removing the duplication
covers the second.

**Each Lambda reading Doppler directly at cold start.** No sync and no
five-config limit on Doppler's free plan, but every cold start would
depend on Doppler being up and each cog would need a hand-placed token.
The sync is used; the loader hides which source is behind it, so the
alternative remains available.
