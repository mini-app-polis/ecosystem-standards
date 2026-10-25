# ADR-0013: Railway-Hosted Cogs Are Recorded Exceptions to ADR-0009

**Date:** 2026-10-16
**Status:** Accepted
**Repo:** ecosystem-standards
**Depends on:** ADR-0002 (type/trait taxonomy), ADR-0009 (pipeline cogs run on
Lambda behind their own queue)
**Amends:** ADR-0009 — its decision that `pipeline-cog` means a queue-driven
Lambda worker "for every cog of that type", and its consequence that cogs
not yet moved read as backlog rather than being exempted
**Amends:** ADR-0007 — its §4 recovery contract, which no longer covers the
Railway-hosted one-shot cogs (see ADR-0007's current-state note)

---

## Context

ADR-0009 defined `pipeline-cog` as an AWS Lambda function behind an SQS queue
of its own and applied that to every cog of the type, including the two that
had not moved. A cog still on the old runtime was to fail PIPE-016 and
PIPE-017 on purpose, so that its findings read as the list of what the move
involved.

Two pipeline cogs now run on Railway, and neither is a cog that has not
finished moving in the sense ADR-0009 meant:

- **wiki-curator-cog** left Prefect on 2026-09-23 for a one-shot Railway
  process: one wake is one run, a full idempotent re-render of the wiki that
  takes no arguments, with no queue and no resident container
  (wiki-curator-cog ADR-0004). It did not go to Lambda then because GitPython
  needs a git executable the managed Python runtime does not ship, and
  because every queue message would have been identical. On 2026-10-14 it
  was decided that it will move to Lambda once that design is finished.
- **db-ops** is three Railway cron services — db-poller, db-backup and
  db-drill — that reach both production databases over Railway private
  networking, which is why they are not Lambda functions (db-ops ADR-0001).
  It is not moving.

Both carry the queue- and Lambda-shaped rules (PIPE-015 to PIPE-018,
PIPE-020, CD-010, CD-024) as exemptions in their `evaluator.yaml`, not as
deferrals: the rules are not unmet, they describe a runtime the repository
does not have. ADR-0009 said this would not happen, so the record and the
fleet disagree.

---

## Decision

**A pipeline cog may run on Railway when the Lambda shape does not fit it.
It stays `pipeline-cog`, and exempts the queue- and Lambda-shaped rules in
its own `evaluator.yaml`, each with its reason.**

- **No new repo type.** Once wiki-curator-cog moves, db-ops is the only
  Railway-hosted cog, and ADR-0002's test for a new type is several
  repositories carrying the same exemptions for the same structural
  reason — not one. If a second repository of db-ops's shape appears, the
  type is what changes, and the exemptions come out of both.
- **wiki-curator-cog is a transitional exception.** Its exemptions end in
  the change that moves it to Lambda and retires its Railway service; until
  then it is graded against the rules that still describe it.
- **Liveness is declared per repository.** CD-010's Layer 1 for a pipeline
  cog is a dead-letter-queue alarm, which a Railway cog has no queue for.
  Each exempting repository names its own liveness signal in the CD-010
  exemption's reason. This ADR does not prescribe one.
- **Sentry is the shared cogs project.** Railway-hosted cogs read
  `SENTRY_DSN_COGS` and set a `service` tag (CD-002), like the Lambda cogs.
  There is no per-cog DSN.
- **Status follows the fleet's rule.** A Railway-hosted cog is `active` in
  `ecosystem.yaml` once it runs in production, so the fleet sweep grades it
  when the catalog moves, not only when it releases.

---

## Consequences

**Positive**

- ADR-0009 and the fleet agree again. A reader of ADR-0009 finds this
  amendment instead of a decision the registry contradicts.
- The exemptions in wiki-curator-cog's and db-ops's `evaluator.yaml` are
  sanctioned rather than tolerated, and the conditions that end them are
  written down.
- db-ops is `active`, so it is regraded on every standards and evaluator
  release.

**Negative / trade-offs**

- The queue- and Lambda-shaped rules do not check the Railway cogs at all,
  and nothing replaces them: a Railway cog's run budget, restart policy and
  liveness signal are visible only in its exemption reasons, not in a rule.
- PIPE-020's concern — a run that stops before its ceiling and says so —
  applies on Railway too, but its check reads Lambda's clock. Both Railway
  cogs implement a deadline of their own, and nothing verifies it.

---

## Alternatives Considered

**A `railway-cog` (or `scheduled-cog`) repo type.** Would let the rules
scope by type instead of by exemption. Rejected for now: with wiki-curator
moving, it would be a type with one member, which ADR-0002 rejects.

**Deferring the Lambda rules instead of exempting them.** A deferral says
"applies, unmet, known". For db-ops the rules will never apply; for
wiki-curator-cog they apply only after a move that replaces the code they
would grade. Either way the finding would be noise until the exemption's
condition changes.

**Leaving ADR-0009 as written.** Rejected: its "for every cog of that type"
is the clause a reader would reasonably act on, and it is no longer true.
