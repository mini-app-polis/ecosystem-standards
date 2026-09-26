# ADR-011: Trigger Cogs Run on a Schedule, Not as a Resident Process

**Date:** 2026-09-26
**Status:** Accepted
**Repo:** ecosystem-standards
**Depends on:** ADR-009 (pipeline cogs on Lambda), ADR-010 (infrastructure
in one repository)
**Amends:** ADR-009 — its definition of `trigger-cog` as "an always-on
asyncio loop", and its rescoping of CD-017 and OPS-007 to that type

---

## Context

ADR-009 moved pipeline cogs to Lambda and left `trigger-cog` defined as an
always-on asyncio loop on Railway, because watcher-cog — the only trigger
cog — still was one. It remembered which Drive files it had seen and fired
on the difference, and that memory was why it had to be resident.

watcher-cog no longer remembers anything (its ADR-005). An EventBridge
schedule invokes a Lambda function once a minute; each tick asks
api-kaianolevine-com for every file present, and the API's dispatch claims
turn the repeats into one job per file. The function is declared in
mini-app-polis/infra, in `modules/scheduled-worker`. The Railway service is
gone, and with it `railway.json`.

The rules that followed the old definition now describe a process that does
not exist. CD-017 requires a Railway restart policy and CD-024 reads memory
and CPU ceilings from `railway.json`; both fail on a repository that has
correctly deleted it. CD-027, CD-028 and SEC-008 look for Terraform in a
repository that, under ADR-010, holds none.

ADR-002 names the signal: when a correct repository needs exemptions from
rules written for its type, the type is what changed.

## Decision

**`trigger-cog` means an AWS Lambda function on an EventBridge schedule,
declared in mini-app-polis/infra. No resident process.**

Rescoped, by removing `trigger-cog` from `applies_to`:

| Rule | Why it no longer applies to a trigger cog | Where the fact is checked now |
|---|---|---|
| CD-017 | No process to restart; a failed tick is retried by the next tick | — |
| CD-024 | Its ceiling is the function's `memory_size` and `timeout` | mini-app-polis/infra, as `infrastructure` |
| CD-027, CD-028, SEC-008 | It declares no Terraform (ADR-010) | mini-app-polis/infra, as `infrastructure` |

Unchanged, because each still describes the trigger cog as it is:

- **CD-007** (Healthchecks.io). A scheduled function that stops being
  invoked raises no error anywhere, so a ping that fires on absence is
  still the one signal that catches it.
- **PIPE-019** (work started through the API).
- **CD-010.** Layer 1 is still the Healthchecks ping.

**OPS-007** (drain in-flight work on SIGTERM) is left scoped to
`trigger-cog` for now. It is `status: gap` and produces no findings, and it
now has no resident subject among the cogs. Where it belongs, most likely
`api-service`, is its own decision.

## Consequences

- watcher-cog carries no deferral or exemption for the loss of
  `railway.json`.
- A future trigger cog that genuinely needed to be resident would be a new
  type rather than a return to the old definition: the rules above
  depended on residency, not on detecting events.
- This amends ADR-009's type definition; ADR-009 is not superseded, and its
  pipeline-cog decisions stand.
