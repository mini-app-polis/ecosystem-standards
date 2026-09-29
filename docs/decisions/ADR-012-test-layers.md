# ADR-012: Four Test Layers, Each Proving Something the Others Cannot

**Date:** 2026-09-29
**Status:** Accepted
**Repo:** ecosystem-standards
**Amends:** TEST-000 — its scheduling of end-to-end tests as nightly

---

## Context

The catalog says a good deal about *which* tests a pipeline cog needs
(TEST-001 to TEST-004) and how Python tests are run (TEST-005 to
TEST-008), but nothing about which *kinds* of test any repo must have.
TEST-000 describes a pyramid and is `checkable: false`. A repo with a
hundred unit tests and nothing else reads as fully conformant.

deejaytools shows what that misses. In September 2026 it had unit tests
in both repos and a live contract suite in the web app, and still:

- **Unique conflicts returned 500 instead of 409** in three routes.
  Drizzle wraps the Postgres error and puts `code: "23505"` on
  `err.cause`; the handlers read `err.code`. Unit tests mock the
  database, so the wrapping never happened in them. Integration tests
  against a real Postgres found it the first time they ran.
- **Faults that exist only once something is deployed.** The dev site
  was built with the wrong kind of Clerk key; the dev API's
  `CORS_ORIGINS` did not admit the Pages preview origin; Cloudflare's
  bot protection turned GitHub's runners away with a 403; the song
  upload's Google Drive path had never run outside a mock. None of
  these is visible from a repository. Each was found by a check run
  against the deployed dev environment.
- **Nothing tied the web app to the API it calls** except that
  contract suite, which existed because one repo happened to build it.

TEST-000 also schedules end-to-end tests nightly. deejaytools runs them
after every dev deploy instead, and declined a nightly run: a nightly
failure arrives hours after the change that caused it, attached to no
commit, and is the kind of red that gets read as noise.

TEST-010 ("contract test for every API endpoint") is a different thing
from the contract layer below, despite the name: it asks the API itself
to assert its response envelope, per endpoint. It stays as it is.

---

## Decision

**A repo has the test layers that apply to its type: unit, integration,
contract and end-to-end. Each layer is defined by what it proves and
what it runs against, and each is a separate rule.**

| Layer | Proves | Runs against | When | Applies to | Rule |
|---|---|---|---|---|---|
| Unit | Logic is right in isolation | Nothing — no I/O | CI, every push | pipeline-cog, trigger-cog, api-service, shared-library, react-app | TEST-014 |
| Integration | The repo's own parts work together, with its real stateful dependencies | The production database engine, in CI; external services stubbed at the boundary | CI, every push | api-service, pipeline-cog | TEST-015 |
| Contract | What a consumer expects of a fleet API is what the deployed API does | The deployed dev API | After a dev deploy of either side | Any repo that calls a fleet API | TEST-016 |
| End-to-end | A user's real path through the product works | The deployed dev frontend and API, in a real browser | After a dev deploy | react-app | TEST-017 |

The rules require the layer to **exist and run**, not a quantity of it.
How much is enough is a per-repo judgement; the catalog's job is to
make a missing layer visible.

### What each layer means

**Unit** tests run without a network, database or filesystem beyond
temporary files. They are the fast, numerous base of TEST-000's pyramid.

**Integration** tests exercise the repo through its real entry point.
For an api-service that means requests through the app, against a
database of the production engine — Postgres, not SQLite or a mock —
because driver behaviour (error wrapping, constraint names, type
coercion) is part of what is being tested. For a pipeline-cog it means
the handler invoked end to end with external services stubbed at the
HTTP boundary (TEST-007), which is TEST-000's existing definition.

**Contract** tests are consumer-driven. The suite lives with the
consumer, because the consumer's expectations *are* the contract: the
web app's endpoint catalog, not the API's route list, says what must
not change. It runs against the provider's deployed dev instance, and
it runs when either side changes — a push to the consumer, and a
dispatch from the provider once its dev deploy succeeds, so it meets
the API that is actually live. A consumer that calls through a shared
client library may keep the suite in that library instead.

**End-to-end** tests drive a real browser through the deployed dev
site, signed in through the identity provider's development instance.
One or a few, on the paths people actually use.

### Where tests may write

Contract and end-to-end tests create and delete data, so they run
**only against dev**, only with development credentials, and one at a
time. deejaytools enforces this three ways: the suite refuses a key
that is not a development key (`sk_test_`), refuses production
hostnames, and a production API would reject the development token
anyway. Production gets read-only smoke checks after each deploy —
health, an unauthenticated request refused in the error envelope, and
for a frontend, the identity key and API URL built into the bundle
(CD-032, CD-033).

### Keeping the layers honest

Having a layer is the floor. deejaytools also keeps its layers from
eroding, and those practices are rules too:

- **Every route is exercised** (TEST-018). The integration suite records
  each request; at teardown it fails on any registered route no test
  called, unless that route is listed with a written reason, and fails on
  a listed route that is now called or no longer exists.
- **Coverage only moves up** (TEST-019). Thresholds are set to current
  coverage and rise automatically when it rises; a change that lowers
  coverage fails. There is no target number.
- **Tests do not depend on the time of day** (TEST-020). Dates are
  computed in the domain's timezone and span midnight. UTC dates broke
  three suites on one evening, once UTC had reached tomorrow in Chicago.
- **A unique-constraint violation is a 409** (API-012), detected through
  the driver's error wrapping — the defect only the integration layer
  found.

### How the checks are wired

- **Changes reach main only through the promotion pull request**
  (CD-034). `dev` is where every layer runs against a deployed
  environment; `main` is what passed there, merged by a person.
- **Each commit's checks run once** (CD-035). Deploy-time suites run on
  the push or the deploy, not again on the promotion pull request, whose
  head is the same commit.

### Derived rules

| Rule | Title |
|---|---|
| TEST-014 | Has unit tests |
| TEST-015 | Has integration tests |
| TEST-016 | Has contract tests against the APIs it calls, when it calls one |
| TEST-017 | Has end-to-end tests |
| TEST-018 | Every API route is exercised by an integration test, and the suite enforces it |
| TEST-019 | Coverage has a floor that only rises |
| TEST-020 | Tests do not depend on the time of day |
| API-012 | A unique-constraint violation is a 409, never a 500 |
| CD-032 | Every deploy is smoke-checked where it landed |
| CD-033 | Test suites that write run only against dev, with development credentials, one at a time |
| CD-034 | Changes reach main only through the promotion pull request |
| CD-035 | Each commit's checks run once |

All are `LLM CHECK.` with their deterministic steps tagged, so they are
evaluated from the start; each can move to the deterministic engine as
evaluator-cog implements it.

---

## Consequences

**Positive:**
- A repo missing a layer produces a finding. Today it produces nothing.
- Each layer's rule names what it runs against, so "we have
  integration tests" cannot be satisfied by unit tests with a mocked
  database.
- End-to-end failures land on the change that caused them, in the run
  that deploy started.
- A provider change that breaks a consumer is caught on dev, before the
  promotion pull request to main.

**Negative / trade-offs:**
- Contract and end-to-end tests need a deployed dev environment with
  its own database, identity-provider development instance and test
  user. A repo without one cannot satisfy TEST-016 or TEST-017 until it
  has one.
- They are slower and flakier than CI tests: deejaytools' contract run
  takes about two minutes, most of it waiting on background work.
- Pipeline cogs call api-kaianolevine-com, so TEST-016 applies to them.
  The practical home for that contract is common-python-utils' client,
  once, rather than every cog.
- End-to-end testing of pipeline cogs is not decided here. It needs a
  dev queue and function per cog, which infra does not declare today.
- static-site is out of scope for all four. Its content is checked by
  its build and, once deployed, by a smoke check.

---

## Alternatives Considered

**One rule for "has tests".** Satisfied by any single layer, which is
the gap this ADR exists to close.

**A coverage percentage.** Rejected: a number invites tests written to
reach it. Coverage that only moves up keeps the level without choosing
one.

**End-to-end tests nightly** (TEST-000 as written). Rejected for the
reasons in Context. Running them per dev deploy costs minutes, not
hours, and only when something changed.

**Provider-side contract tests** — the API checks its responses against
the consumer's schemas in its own CI. Catches a break before deploy,
but the API does not know which schema belongs to which endpoint; that
mapping lives in the consumer. It would be a second copy of the
contract. Worth revisiting if a provider gains many consumers.

**Contract tests in CI against a locally started API.** Needs real
identity and Drive credentials in CI, and misses exactly the faults the
deployed check finds: configuration, CORS, bot protection, real
providers.

**Contract and end-to-end tests against production.** Rejected: both
write data.
