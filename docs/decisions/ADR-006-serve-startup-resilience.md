# ADR-006: Startup registration resilience for serve()-based cogs

**Date:** 2026-08-19
**Status:** Accepted
**Repo:** ecosystem-standards
**Depends on:** ADR-003 (conformance checker architecture)

---

## Context

On 2026-07-22 a transient Prefect Cloud `503 Service Unavailable` on the
deployment-registration endpoint crashed all four `serve()`-based cogs
simultaneously — deejay-cog, transcription-cog, evaluator-cog, and
watcher-cog. None auto-restarted. No finding was posted. The fleet-down
event was completely silent, and was discovered by a human noticing that
nothing had run.

The root cause is structural, not incidental. CD-015 makes
`prefect.serve()` in `main()` the canonical registration pattern for
every cog. Before its runner loop begins, `serve()` makes a blocking,
fail-fast HTTP call to Prefect Cloud (`read_deployment_by_name`). In
every cog's `main.py` that call was unguarded — the only `except` was
`KeyboardInterrupt` — so a `503` propagated out of `main()` and the
process exited non-zero.

Because the scaffolding is standardized, so is the failure mode. This
was one single point of failure hit four times, not four coincidences.
The ecosystem's consistency, normally its strength, correlated the
blast radius perfectly.

Three defects converged, and they are independent of one another:

1. **No retry on startup registration.** A seconds-long upstream blip
   killed services that would otherwise have run for weeks.
2. **No restart policy.** Railway restart policy was `NEVER` (or an
   exhausted low cap) on every affected service. The setting existed
   only in the Railway dashboard — nothing in any repo recorded it,
   reviewed it, or would reproduce it if a service were recreated.
3. **No signal.** The flows' `on_crashed` / `on_failure` hooks are
   correctly wired via `mini_app_polis.pipeline_status.make_failure_hook`,
   but those hooks attach to *flow runs*. This crash happened during
   `serve()` registration, before any flow run existed, so no hook could
   fire. Not a crashed flow: a crashed process with no flow at all —
   a window no existing mechanism covered, because every reporting path
   in the ecosystem hangs off a flow run.

Defect 3 is the one that made the other two expensive. A fleet that
falls over and says so is an incident; a fleet that falls over silently
is a discovery.

---

## Decision

Startup registration is made resilient in two independent layers, both
required, both enforced by new rules in `standards/delivery.yaml`. A
third change records the crash in Pipeline Health.

### Layer 1 — in-process retry (CD-016)

Cogs call `mini_app_polis.serve_resilience.serve_with_retry(...)` rather
than `prefect.serve(...)`. The helper:

- Retries transient failures only: any HTTP `5xx`, plus `408` and `429`,
  plus network-level `httpx` transport errors (the whole
  `TimeoutException` and `NetworkError` branches, `ProxyError`, and
  `RemoteProtocolError`).
- Fails fast on the rest of `4xx` — `401`/`403`/`404`. A bad
  `PREFECT_API_KEY` or a deleted deployment is a configuration error.
  Retrying it burns the ceiling and delays the real signal.

  The 5xx classification is a range, not an allowlist. Prefect Cloud is
  Cloudflare-fronted and its edge emits `520`–`529` (`522`, `524`) when
  an origin is degraded — the most common client-side presentation of a
  Prefect Cloud incident. An allowlist of `{500, 502, 503, 504}` would
  fail fast on exactly that, then post a CRITICAL finding claiming the
  failure was a configuration error: the July failure mode plus a
  misleading alert. Whole `httpx` exception branches are taken for the
  same reason — `ConnectTimeout` is not a subclass of `ConnectError`, so
  naming leaf classes silently misses operationally identical siblings.
- Backs off exponentially (`multiplier=2, min=2, max=30`) to a
  wall-clock ceiling of 30 minutes, overridable per-process via
  `SERVE_RETRY_MAX_SECONDS`.
- On give-up, POSTs one finding (see below) and re-raises so the process
  still exits non-zero.

**The helper is shared library code.** It lives in
`common-python-utils`, alongside the existing `post_run_finding` /
`make_failure_hook` shims, not copy-pasted per cog. All four cogs pin
`common-python-utils` at `rev = "main"` and inherit it on next deploy
with no version bump. A hand-rolled per-cog retry violates CD-016: the
entire point is that one fix covers the fleet, and four copies drift.

### Layer 2 — version-controlled restart policy (CD-017)

Each service declares `railway.json` at its repo root with
`restartPolicyType: "ON_FAILURE"` and `restartPolicyMaxRetries: 10`.

Version-controlled rather than dashboard-configured. A dashboard-only
value is invisible to code review and silently lost when a service is
recreated — which is how four services ended up on `NEVER` with nobody
having decided that.

`ON_FAILURE` rather than `ALWAYS`: a clean exit is a deliberate
shutdown and should not be fought.

### The layers are multiplicative, not redundant

Total unattended outage coverage is roughly *layer-1 wall-clock ceiling
× layer-2 max retries*. This is the reasoning behind both the 30-minute
ceiling and the max-retries floor of 10, and it is why CD-016 and CD-017
are separate rules rather than one: they are independently checkable,
independently violated, and remediated by different means (a code change
vs. a config file).

They also cover different failures. Retry rides out an upstream blip
in-process. Restart recovers from failures a retry cannot fix — a wedged
event loop, leaked in-process state, an outage longer than the ceiling.
Implementing only one leaves a real gap in both directions.

### `source="startup"` and the CRITICAL severity

`serve_with_retry` emits one finding on give-up with `source="startup"`
and severity `CRITICAL`.

`startup` joins the existing `flow_inline` (end-of-run self-report) and
`flow_hook` (Prefect on_failure/on_crashed) source values. A `startup`
row means: no flow run exists, the cog process itself failed. Its
`run_id` resolves to `"local-run"` because there is no flow run to
attribute it to — which is exactly the condition being reported.

`CRITICAL` required expanding
`mini_app_polis.pipeline_status.Severity`, which had deliberately
excluded it. The original reasoning — CRITICAL is for cross-cog signals
no single flow run can authoritatively raise, and "a cog that is
critically broken can't reach this code path at all" — was correct for
its scope, and still governs use. This decision does not overturn it; it
records the exception the original note anticipated. "All four cogs are
down and no flow will ever run" is the cross-cog, fleet-wide signal
CRITICAL was reserved for, and `serve_with_retry` is what makes that
code path reachable: the process is alive enough to report on its way
out.

The scope stays narrow. `index.yaml` already documents CRITICAL as
emission-only and never valid on a rule definition; that is unchanged.
Flow-run outcomes still cap at `ERROR`, whatever the blast radius.
CRITICAL is not "ERROR but I really mean it" — using it that way
dilutes the one signal that means "nothing is running at all".

### CD-015's check had to change too

A cog that adopts `serve_with_retry` has no bare `serve(` token left in
its source. CD-015's existing `check_notes` say to flag when "neither
serve() nor deploy() is found — the registration pattern is missing
entirely", so compliance with CD-016 would have produced a CD-015 ERROR
on every cog in the fleet. CD-015's `check_notes` now name
`serve_with_retry(` as a third valid registration form.

This is a `check_notes` clarification, not a semantic change, so CD-015
is edited in place rather than retired and replaced (`new-standard.md`
Step 9). The rule still requires exactly what it required: in-process
registration, no work pool.

---

## Consequences

**Positive:**

- A transient Prefect Cloud blip no longer takes a cog down. Combined
  layer-1 × layer-2 coverage goes from effectively zero to roughly five
  hours unattended.
- Registration crashes are visible in Pipeline Health for the first
  time, as `source="startup"` CRITICAL rows. The July incident produced
  none.
- One shared helper covers four cogs. The next `serve()`-based cog
  inherits the behavior by depending on `common-python-utils`.
- Railway restart behaviour becomes reviewable in a PR and reproducible
  on service recreation.
- Closes the pre-flow half of infrastructure-level crash capture —
  process-level crashes at registration. The remaining gap is a crashed
  flow run whose own hook fails to post; that is still uncovered and is
  noted against the `pipeline-eval-deprecation` item in `BACKLOG.md`.

**Negative / trade-offs:**

- A cog whose Prefect Cloud connectivity is genuinely broken now takes
  up to 30 minutes to surface a *transient*-classified failure.
  Configuration errors (401/403/404) still fail fast, so the common
  "deployed with a bad key" case is unaffected.
- During a long outage the give-up finding fires once per process life
  — roughly two per hour per cog, times four cogs. That is the intended
  alerting cadence, not silence, but it is not free either.
- CD-016 gives `common-python-utils` a second hard runtime dependency
  (`tenacity`; `httpx` was already declared). Every consumer of the
  library pays that install cost, including consumers with no Prefect
  entry point.
- CD-015's exemption in each adopting cog's `evaluator.yaml` must stay
  until evaluator-cog's `check_prefect_serve_pattern` implements the
  amended `check_notes`. Until then the fleet carries an exemption whose
  reason is "the detector cannot see through the shared wrapper" —
  tracked by EVAL-007 (standards/evaluator drift).
- CD-017 applies to `api-service` as well as the cog types, so
  api-kaianolevine-com and deejaytools-com-api will report violations
  until they add `railway.json`. This is intended — the dashboard-only
  restart policy problem is not specific to cogs — but it means the rule
  lands red on repos that were not part of the incident.

---

## Alternatives Considered

### Per-cog retry, copy-pasted into each `main.py`

Rejected. It recreates the exact property that caused the incident: four
identical implementations of one concern, which drift and must each be
fixed separately. The shared-shim pattern already established by
`post_run_finding` / `make_failure_hook` is the ecosystem's answer to
this and applies unchanged here.

### Restart policy only, no in-process retry

Rejected. A restart is a blunt instrument for a two-second blip: the
process dies, Railway rebuilds and reschedules it, and the cog is
unavailable for the full restart cycle for a failure that a four-second
sleep would have absorbed. It also burns the finite restart budget on
failures that are not the kind restarts are for.

### In-process retry only, no restart policy

Rejected. Retry cannot fix an outage longer than its ceiling, and cannot
fix a process that is wedged rather than erroring. Leaving restart
policy at `NEVER` means any failure outside the retry classifier is
still permanently fatal — which is precisely defect 2 from the incident,
left in place.

### A short retry ceiling (~2–3 min) handing off quickly to Railway

Rejected after analysis. The argument for it — "hand off rather than
retry forever in isolation" — assumes the handoff buys something for
this failure. It does not: a restart re-runs the same code path against
the same outage. With ~2.5 minutes × 10 restarts, combined coverage is
about 25 minutes, and Prefect Cloud incidents routinely run longer. The
handoff is valuable only for failures a fresh process fixes but a retry
does not, which is why give-up still exists rather than retrying
unbounded — but that argues for keeping a ceiling, not for making it
short.

### Attempt-count ceiling (`stop_after_attempt`) instead of wall-clock

Rejected. The ceiling operators reason about is "how long do we ride
this out", and an attempt count silently changes meaning whenever the
backoff curve is tuned. `stop_after_delay` states the intent directly.
An attempt-count guard is retained, but only as a runaway backstop.

### Emitting the give-up finding at ERROR instead of CRITICAL

Rejected. It avoids touching the `Severity` Literal, but a fleet-down
registration crash would then read identically to one failed flow run in
Pipeline Health — the exact invisibility this ADR exists to remove.

### Folding the retry requirement into CD-015 rather than adding CD-016

Rejected per `new-standard.md` Step 2. The two are independently
checkable (registration mechanism vs. resilience wrapper),
independently violated, and CD-015's dimension is
`structural_conformance` while the resilience concern is `cd_readiness`.
Welding them would also mean a severity/dimension change to CD-015,
which Step 9 requires be handled as retire-and-replace — a more
disruptive change to a rule many repos already reference.

---

## See also

- `standards/delivery.yaml` — CD-015 (amended), CD-016, CD-017
- `index.yaml` `severities:` — CRITICAL as an emission-only severity
- deejay-cog `docs/decisions/ADR-005-serve-startup-resilience.md` — the
  canary adoption, and the amendment to deejay-cog ADR-001
- `BACKLOG.md` — infrastructure-level crash/failure capture
