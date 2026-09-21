# ADR-009: Pipeline Cogs Run on Lambda Behind Their Own Queue

**Date:** 2026-09-21
**Status:** Accepted
**Repo:** ecosystem-standards
**Depends on:** ADR-002 (type/trait taxonomy)
**Supersedes:** ADR-006 (startup registration resilience for serve()-based cogs)

---

## Context

ADR-002 defined `pipeline-cog` as an "always-on Railway worker running one
or more Prefect @flow(s)" and `trigger-cog` as a worker that "fires Prefect
flow runs via API". Eight rules encoded that runtime: PIPE-001, PIPE-004,
PIPE-006, PIPE-009, PIPE-012, CD-005, CD-015 and CD-016, with CD-017,
CD-024, CD-007, CD-010 and OPS-007 assuming it in part.

In 2026-09 the fleet started moving off it, one cog at a time
(evaluator-cog `docs/serverless-migration.md`). evaluator-cog and
deejay-cog now run as Lambda functions behind SQS queues of their own,
hold no resident process, and do not depend on Prefect. watcher-cog
starts deejay-cog's work by asking api-kaianolevine-com, which enqueues.

The first release of each moved cog was graded against the old runtime:
"Prefect is not declared" (PIPE-001), "no railway.json restart policy"
(CD-017), "no railway.json memory or CPU ceiling" (CD-024). Both cogs
were correct, and the standard was describing the wrong target. Two more
cogs were due to carry the same exemptions, which ADR-002 names as the
signal to change the taxonomy rather than write the exemption again.

---

## Decision

**`pipeline-cog` means a queue-driven Lambda worker, now, for every cog of
that type — including the two that have not moved yet.**

- `pipeline-cog`: an AWS Lambda function behind an SQS queue of its own,
  both declared in the repo's `infra/`. No resident process.
- `trigger-cog`: an always-on asyncio loop that asks api-kaianolevine-com
  to run the owning cog; the API enqueues.

Retired (deleted; git history is the record): PIPE-001, PIPE-004,
PIPE-006, PIPE-009, PIPE-012, CD-005, CD-015, CD-016, and the
`multi-flow` trait, which existed only to downgrade CD-015.

Added:

| Rule | Replaces | Requires |
|---|---|---|
| PIPE-016 | PIPE-001, CD-005, CD-015, CD-016 | `infra/` declares queue, function and event source mapping; no Prefect dependency |
| PIPE-017 | CD-017 (for pipeline cogs) | Per-record failure reporting, a dead-letter queue, a visibility timeout longer than the function timeout |
| PIPE-018 | PIPE-004, PIPE-009 | A concurrency ceiling declared in `infra/` |
| PIPE-019 | PIPE-001 (trigger half) | Work started through the API; no Prefect client, no queue writes |

Rescoped: CD-017, CD-007 and OPS-007 apply to `trigger-cog` (and CD-017 to
`api-service`) only. CD-024 reads a pipeline cog's `infra/` Terraform —
`memory_size` and `timeout` — as its platform descriptor. CD-010's liveness
layer for a pipeline cog is a dead-letter-queue alarm with an action.
PIPE-008, PIPE-015, CD-006 and PRIN-005 describe the new trigger path.

PIPE-012's concern — retry waits that slow the test suite — is TEST-013's
(delays sourced from config), which already applies.

---

## Consequences

**Positive**

- evaluator-cog and deejay-cog are graded against what they are. Their
  Prefect/Railway findings disappear without an exemption, and the
  exemptions deejay-cog and evaluator-cog carried for CD-015, PIPE-004 and
  PIPE-006 can be deleted.
- The rules now check the things that failed during the migration: a
  handler that swallows failures, a queue with no dead-letter target, a
  visibility timeout shorter than the job, an unbounded burst.
- One taxonomy. There is no `lambda-cog` to retire later.

**Negative / trade-offs**

- transcription-cog and wiki-curator-cog, still on Prefect and Railway,
  now fail PIPE-016 and PIPE-017 and lose the checks that guarded their
  current runtime — notably CD-016, which caught an unwrapped `serve()`
  that crashes the process at boot. Their code is not changing until they
  move, so the lost check guards against a regression nobody is making;
  their new findings are an accurate list of what the move involves. Their
  dashboards read red until then, deliberately.
- watcher-cog fails PIPE-019 until transcription-cog moves, because its
  transcription triggers still create Prefect flow runs.

---

## Alternatives Considered

### A separate `lambda-cog` type during the transition

Moved cogs would declare `lambda-cog`; `pipeline-cog` would keep the
Prefect rules for the two remaining cogs and be deleted with them. Cleaner
signal for a few weeks, at the cost of two parallel rule sets and a type
created to be deleted. Rejected: the standard describes the target, and a
cog that has not reached it should say so.

### Exempting the moved cogs

Rejected on ADR-002's own test. Four cogs carrying the same exemptions for
the same structural reason is a taxonomy that has fallen behind.
