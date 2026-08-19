# ADR-007: External provider failure — reporting and recovery contract

**Date:** 2026-08-19
**Status:** Accepted
**Repo:** ecosystem-standards
**Depends on:** ADR-006 (startup registration resilience)

---

## Context

Every service in the ecosystem depends on external providers it does not
control: Prefect Cloud, Google Drive/Sheets, Clerk, Sentry, Anthropic,
OpenAI, Spotify, AcoustID, MusicBrainz, Todoist, GitHub, Railway.
Provider failure is not an edge case — it is a routine operating
condition, and the July 2026 fleet-down incident (ADR-006) was one
instance of it.

The catalog already says something about *retrying* these calls:

- **PIPE-007** — Prefect `@task`s that call external APIs use
  `retries=2, retry_delay_seconds=30`.
- **XSTACK-005** — don't hand-roll retry around Google/Anthropic; use
  the shared-library facades.
- **CD-016** — `serve()` startup registration is wrapped in
  `serve_with_retry`.
- `common-python-utils` carries concrete per-provider retry:
  `google/_retry.py` (`RetryConfig(max_retries=8)`), the LLM clients,
  and now `serve_resilience`.

Nothing says what happens **after** those retries are exhausted. That is
the gap this ADR addresses, and it has two halves.

**Half one: an outage is indistinguishable from a defect.** When Spotify
is down mid-run, deejay-cog emits a finding along the lines of
`sets_failed=3`. Nothing in that row says the cause was a vendor being
unavailable rather than a bug in our Spotify code. Pipeline Health cannot
answer "was last month's failure spike ours or theirs?" — every provider
outage in the ecosystem currently launders itself into looking like our
own defect. That is the same shape of problem as July, one layer up: the
failure is recorded, but the record does not say what caused it.

**Half two: recovery after full stop is unbounded-then-nothing.** ADR-006
established two layers for a process that cannot start: in-process retry
(30 min) and Railway `ON_FAILURE` restarts (10). Multiplied, that is
roughly five hours of unattended coverage. After that the service stays
down until a human redeploys it. Nothing in the ecosystem notices.

## Decision

We standardize **how provider failure is reported** and **what recovery
posture is expected**. We deliberately do **not** standardize how an
application degrades.

### What is explicitly out of scope: degradation behavior

Whether a given provider being down should skip a step, fail an item,
fail the run, or stop the process is a property of *that application's
purpose*, and the catalog cannot know it. Spotify being unavailable is
survivable for `process-new-files` (the CSV still normalizes, the Sheets
still write) and fatal for a hypothetical playlist-only cog. Google Drive
being unavailable is fatal for `process-new-files` because there is no
input, and irrelevant to a cog that never touches Drive.

A rule that prescribed degradation would either be too vague to check or
wrong for some cog. Each application decides how it degrades. PRIN-002
(continue on item failure) remains the only ecosystem-wide statement on
the subject, and it is a principle, not a per-provider prescription.

This scope line is the load-bearing part of this ADR. Future rules
derived from it must constrain *reporting and recovery*, never
degradation.

### 1. Two error classes, acknowledged at every interface

Every external-service interface must let its caller distinguish:

- **COMMUNICATION FAILURE** — no usable response. Connection refused,
  DNS, TLS, timeouts, reset, truncated body. *We do not know whether the
  request took effect.*
- **RESPONSE ERROR** — the provider answered and said no, or the payload
  is unusable. Any 4xx/5xx, schema mismatch, unparseable complete body.
  *We know the outcome.*

The line is epistemic rather than severity-based, and that is the whole
point: a `500` is a RESPONSE ERROR even though it means the provider is
unhealthy, because our request was received and rejected. What changes
between the classes is what we *know*, and therefore whether a retry is
safe, whether an idempotency guard is needed (PIPE-013), and what an
operator should investigate.

An audit of every outbound-call surface in `common-python-utils` found
this handled inconsistently. `google/_retry.py` separates them cleanly
(`except HttpError` reading `resp.status`, versus
`is_retryable_non_http_error` over `TimeoutError`/`socket.timeout`/
`httplib2.HttpLib2Error`/`OSError` errnos), as do `spotify/spotify.py`
and `serve_resilience.py`. But `api/client.py` collapses both into
`KaianoApiError`, discriminated only by an undocumented `status_code=0`
sentinel that *also* means "machine secret not set" — so a caller
writing the obvious `if e.status_code >= 500` treats a total network
failure as a client error. And `llm/anthropic_client.py` wraps
everything in `except Exception as e: raise LLMError(f"...{e}")`,
leaving the distinction alive only inside a string.

This is enforced by **PY-016**, which constrains the shape of the
interface and nothing else. Acceptable implementations are distinct
exception types, or one type with an explicit documented discriminator
field — not a sentinel, not the message text.

Note this rule is a precondition for the rest of this ADR: a cog cannot
report *which* class of failure a provider had if the client it calls
does not tell it.

### 2. The reporting contract

When an external provider's unavailability is the reason work did not
happen — a step skipped, items failed, a run aborted, or a process
exited — the responsible service emits a finding through
`mini_app_polis.pipeline_status` with:

- `source="external_dependency"` — a free-form `source` value, alongside
  the existing `flow_inline`, `flow_hook`, and `startup`. This is what
  makes provider outages queryable as a class.
- `provider=<id>` — passed as an extra, so it lands in the finding text
  as `provider=spotify`. The id comes from the provider registry
  (below), not free text, so the values aggregate.
- Severity chosen by what actually happened to the work, which the
  application decides: the run finished with less done than intended
  (`WARN`), the run could not do its job (`ERROR`), or no work can
  happen at all and the process is exiting (`CRITICAL`, per ADR-006 —
  still reserved for the pre-flow process lifecycle).

Alongside the finding, the failure is logged via the shared logger and
captured explicitly with `sentry_sdk.capture_exception()`. The Sentry
leg needs saying out loud: CD-002 and CD-010 scope Sentry to *unhandled*
exceptions, and a provider failure an application catches in order to
degrade is by definition handled — so it reaches Sentry only if captured
deliberately. **CD-018** carries all three legs.

No new API field and no library change is required. `post_run_finding`
already accepts free-form `source` and arbitrary `**extras`, which is
the same mechanism `source="startup"` used.

### 3. The telemetry exemption

Providers whose only job is to receive our observability data —
currently Sentry, and the Pipeline Health POST path itself
(api-kaianolevine-com plus Clerk M2M, which authenticates it) — are
exempt from the reporting contract and must fail silently.

This is not a convenience. A finding that says "we could not post
findings" cannot be posted, and a system that retries or escalates its
own reporting failure spends the outage generating noise about the
outage. `post_run_finding` is already best-effort by construction
(ADR-004), and `serve_resilience` wraps its own reporting call for the
same reason. Telemetry failure is a log line, never a finding.

### 4. The recovery contract

A service that stops entirely because a provider is unavailable must:

- exit **non-zero**, so the platform can act (a zero exit is a
  deliberate shutdown and will not be restarted — CD-017), and
- be restartable without human action, via the version-controlled
  `ON_FAILURE` policy (CD-017).

**On "should it restart again after some time?" — deferred, deliberately.**
The current posture is bounded: in-process ceiling × restart budget,
then the service stays down. We are keeping that, because an unbounded
restart loop against a multi-hour outage is indistinguishable from a
crash-loop caused by a bad deploy, and the bounded budget is what makes
a genuinely broken build stop rather than churn forever. deejay-cog's
2026-08-19 `ModuleNotFoundError` crash-loop is the case that argues for
keeping a ceiling.

What is missing is not more restarts but *noticing*: nothing currently
observes that a service exhausted its restart budget and stayed down.
That is a monitoring gap, not a restart-policy gap, and it is recorded
in `BACKLOG.md` rather than solved here — solving it needs a component
that watches from outside the failing service, which does not exist yet.

### 5. Per-provider requirements live in a registry, not in prose

Different providers warrant different obligations, and encoding them in
rule prose would scatter them. `ecosystem.yaml` is already the
authoritative inventory of services, patterns, and terminology; it gains
a top-level `external_providers:` section — one entry per provider, with
the canonical `id` used in `provider=`, whether it is telemetry-exempt,
and which shared-library facade (if any) is the required access path.

Making this data rather than prose means a derived rule can check
conformance deterministically, and adding a provider is an
`ecosystem.yaml` edit under the existing `ecosystem-changes` playbook
rather than a new rule each time.

## Consequences

**Positive:**

- Provider outages become queryable as a class. "Show me every
  `source="external_dependency"` finding grouped by `provider`" answers
  whether a failure spike was ours or a vendor's — a question that
  cannot be asked today at all.
- Vendor reliability becomes evidence rather than recollection, which is
  what a decision to drop or replace a provider should rest on.
- Zero implementation cost for the reporting half: no API migration, no
  library release, no version bump. Cogs adopt by passing two extra
  keyword arguments at call sites they already have.
- The degradation scope line means derived rules stay checkable. Every
  obligation here is "did you emit the right shape" or "does this file
  say ON_FAILURE", not "did you handle this sensibly".

**Negative / trade-offs:**

- `provider=` is only as good as the discipline applying it. A cog that
  swallows a provider error and reports a generic failure still produces
  an unattributable row, and no deterministic check can prove a *missing*
  attribution — the checker cannot know an unlabelled failure was
  Spotify's fault. Derived rules can verify the shape where the
  convention is used, and can require that known provider call sites are
  wrapped, but coverage will be partial.
- `ecosystem.yaml` grows a section that must be maintained as providers
  come and go. A stale registry is worse than none, because `provider=`
  values would drift from it.
- The telemetry exemption means the ecosystem is structurally blind to
  its own reporting path failing. If api-kaianolevine-com or Clerk is
  down, findings are silently lost and only the Railway logs record it.
  This is accepted — the alternative is infinite regress — but it means
  "no findings" is ambiguous between "healthy" and "reporting broken".
- The recovery contract's bounded budget means a provider outage longer
  than roughly five hours still ends with a service down and nobody
  told. Deferring the monitoring gap is a real accepted risk, not a
  technicality.

## Alternatives Considered

### Standardize degradation behavior too

Rejected, and this is the main thing this ADR declines to do. A rule
prescribing "skip the step and continue" would be wrong for a cog whose
entire purpose is that step; "fail the run" would be wrong for a cog
where the provider is incidental. Any wording general enough to be
correct everywhere ("degrade appropriately") is not checkable and would
land as an LLM judgment call producing findings nobody can act on.

### A new `provider` column on `pipeline_evaluations`

Rejected for now. Structurally cleaner than a `k=v` suffix in the
finding text, but it requires an api-kaianolevine-com schema migration,
a `PipelineEvaluationCreate` change, a `pipeline_status` change, a
library release, and a redeploy of every cog — to gain query ergonomics
over a convention that works today with none of that. Worth revisiting
if `source="external_dependency"` sees real use and the text-suffix
querying becomes the bottleneck.

### A new `external_dependency` dimension

Rejected. Dimensions aggregate Pipeline Health views and every rule
declares exactly one; adding one for this would mean provider findings
stop appearing under `pipeline_consistency`, where operators already
look for "did this run do its job". The cause belongs in `source` and
`provider`, not in the dimension.

### Unbounded restarts on provider outage

Rejected. It removes the distinction between "the world is broken" and
"we shipped a broken build", and the second case is the one that needs
to stop. See the recovery contract above.

### Rules first, ADR later

Rejected. The scope line — that degradation is deliberately not
standardized — is the part most likely to be lost, and it is reasoning,
not a rule. Writing rules first would have produced a degradation rule
that had to be retired.

## See also

- ADR-006 — startup registration resilience; the special case this
  generalizes
- ADR-004 (deejay-cog) — best-effort pipeline evaluation posting
- PRIN-002 — pipeline resilience, continue on item failure
- PIPE-007, XSTACK-005, CD-016, CD-017 — the retry-side rules this
  ADR sits downstream of
- `playbooks/ecosystem-changes.md` — the process for adding the
  `external_providers:` section and its entries
