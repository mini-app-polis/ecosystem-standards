# ADR-008: Named Machine Keys as the Machine Identity

**Date:** 2026-09-02
**Status:** Accepted
**Repo:** ecosystem-standards

---

## Context

Until this change the ecosystem had one credential family: Clerk. Humans
presented Clerk session JWTs. Cogs presented Clerk M2M opaque tokens,
obtained by `common_python_utils.auth.get_m2m_token` from a
`CLERK_SECRET_KEY` that every cog read out of the same shared Doppler
config. CD-012 encoded that arrangement as a requirement, and
`api-kaianolevine-com` was its only enforcement point.

Three concrete problems drove this decision.

**The shared secret erased the caller.** Because every cog read the same
`CLERK_SECRET_KEY`, every M2M token resolved to the same machine subject.
A catalog row written by `deejay-cog` and a pipeline row written by
`transcription-cog` carried an identical `owner_id`. There was no answer
to "which cog wrote this" anywhere in the system — not in the data, not
in a log, not in an audit table, because there was no audit table.

**Authority was carried by token shape, not by grant.** The API's
guards were `require_wcs_service` ("this credential is a machine,
therefore it may write") and `require_wcs_admin` ("this row has
`is_admin=true`"). Both encode authority in something other than a
grant. Widening one cog's access meant widening every cog's access,
because there was only one machine.

**Verification left the process.** The opaque path was a synchronous
`POST https://api.clerk.com/v1/m2m_tokens/verify` on every machine
request. Clerk sat on the hot path of every internal write in the
ecosystem, so a Clerk outage was an ecosystem outage, and every
cross-service call paid a vendor round trip.

Separately, `auth.py` in `api-kaianolevine-com` had named its own
extraction condition in a docstring: *"If a second service ever needs to
verify Clerk tokens, upstream this logic ... and convert this module into
a thin consumer rather than copying it."* A second enforcement point
became real, so the condition fired.

---

## Decision

Machines authenticate with a **named API key each**, verified locally
against configuration. Humans keep Clerk. The rules both populations
share live in a new shared library, `identity`, which every enforcement
point consumes.

### 1. `identity` is the specification, not a service

`identity` defines one binding contract — **verify → resolve → authorize
→ emit_audit**, run exactly once per request — plus the principal store
schema, the scope vocabulary, the decision function, and cross-language
conformance fixtures.

One specification, N conformant enforcement points. Explicitly **not** a
central auth service on the request path: each service makes its own
decision from the shared specification and its own store instance.

### 2. Humans: Clerk session JWTs, verified locally

RS256, verified against the issuer's JWKS document, cached in process.
Multi-issuer by design — two Clerk tenants stay separate rather than
being flattened into one namespace. Configured via `CLERK_ISSUERS` (a
JSON array of `{issuer, jwks_url}`) or the singular `CLERK_ISSUER` /
`CLERK_JWKS_URL` shorthand.

### 3. Machines: one named key each, and the key *is* the name

Each machine gets its own key, stored only in Doppler as
`<MACHINE_NAME>_API_KEY` (`deejay-cog` → `DEEJAY_COG_API_KEY`). The API
holds the same set in its own environment and compares the presented
credential against each in constant time. A match names the caller.

Possession of the key **is** the identity claim. There is no separate
name for the caller to assert, and therefore nothing to spoof by
asserting it.

### 4. No key material touches the database

Not plaintext, not hashed. The principal store holds
`(issuer='apikey', subject='deejay-cog')` and that principal's role
grants. The secret stays in configuration and nowhere else.

### 5. The machine roster is declared in code

`identity_registry.MACHINES` in `api-kaianolevine-com` declares each
machine and the roles it holds. The declaration is reconciled into the
principal store at boot: missing principals are created, declared role
grants are synced, and grants the registry did not make are left alone.
Adding a cog is a reviewed code change, not a row inserted by hand.

### 6. Authority is roles and scopes

A scope is exactly three dot-separated segments —
`<domain>.<resource>.<action>`. Roles are named bundles of scopes.
Explicit per-resource grants cover the narrow cases roles cannot.
Every non-public route names the single scope it requires, and the
decision has a fixed precedence: no principal → deny; suspended → deny
(checked before roles, deliberately); scope in a role → allow; explicit
resource grant → allow; otherwise deny.

### 7. No fallback

The Clerk M2M path was removed, not kept behind a flag.
`CLERK_SECRET_KEY`, the BAPI verify call, and
`common_python_utils.auth.get_m2m_token` are gone from the ecosystem. A
credential with two dots routes to the Clerk verifier; anything else
routes to the machine-key verifier; nothing falls through between them.

---

## Consequences

**Positive:**

- Five distinct machine principals (`deejay-cog`, `transcription-cog`,
  `evaluator-cog`, `wiki-curator-cog`, `watcher-cog`) where there was
  one. The audit trail names the caller.
- Machine verification is in-process. Clerk is no longer on the path of
  any internal write, and a Clerk outage no longer stops cog traffic.
- Widening one cog's access is one role edit against one principal.
  Previously it widened every machine's access at once.
- Enforcement went from 1 guarded endpoint to 51 scope-guarded routes and
  3 authenticated-only (`POST /v1/wcs/me`, `GET /v1/wcs/me`,
  `GET /v1/identity/whoami` — each one a case where requiring a scope
  would be circular). The remaining 22 are public: 19 application reads
  plus `/health`, `/version` and `/`.
- Key rotation is a Doppler value change plus a redeploy. No migration,
  no re-hashing, nothing to purge from the database.
- The one-enforcement-point assumption is gone. A second service can
  become conformant by consuming `identity` and running the same
  fixtures, rather than by copying `auth.py`.

**Negative / trade-offs:**

- The API's environment now holds every machine's key, so its blast
  radius is the whole machine population. The mitigating property is
  that keys are not shared *between* machines: a single compromised cog
  cannot authenticate as any other.
- Rotation is manual and two-sided — Doppler plus a redeploy of both the
  caller and the API. There is no rolling window in which the old and
  new key are both valid.
- Machine keys are opaque bearer strings with no expiry. A leaked key is
  valid until rotated. Short-lived tokens traded that away for a
  per-request vendor round trip and a shared subject; the trade was made
  knowingly.
- `owner_id` on machine-written rows changed value. Rows `deejay-cog`
  wrote before the switch carry the old shared M2M subject; rows after
  carry `deejay-cog`. Re-ingesting a source file from before the switch
  creates a duplicate set rather than updating the existing one. This
  was accepted rather than re-keyed.
- `common-python-utils` v4.0.0 is a breaking release (`machine_secret`
  and the token cache removed). Every consumer had to move in the same
  pass; there is no version of the library that speaks both schemes.

---

## Alternatives Considered

**Keep Clerk M2M, add a Clerk machine per cog.** This would have fixed
attribution while keeping short-lived tokens. Rejected because it keeps a
synchronous vendor call on the path of every internal write, and because
it makes onboarding a cog an operation in a vendor console rather than a
reviewed code change. The attribution problem was solvable without
paying the availability cost.

**Shared machine credential plus a self-asserted name.** Briefly
designed: one machine credential proves "a machine", an `X-Machine-Name`
header says which one, and permissions are granted against the asserted
name. Rejected — a self-asserted name is not an identity claim. Any cog
holding the shared credential could claim to be any other, which is the
same attribution failure with more moving parts.

**Hash the keys into the principal store.** The familiar API-key-table
shape. Rejected: it puts credential material in the database for no gain
at this scale. The roster is small, declared in code, and fully known at
boot, so the comparison set is already in memory. A hash column would add
a table worth compromising and a migration to rotate, without removing
the need for the value in Doppler.

**A central auth service.** Rejected on the request path. It makes every
service's availability depend on one more hop for a decision that
service can already make from a shared specification plus its own store.
`identity` distributes the specification instead of centralising the
decision.
