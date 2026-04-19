# ADR-002: Type/Trait Taxonomy, Rule Applicability Scoping, and Deferred Keyword

**Date:** 2026-04-06  
**Status:** Proposed  
**Repo:** ecosystem-standards  
**Depends on:** ADR-001 (Federated Evaluation Configuration)

---

## Context

With ADR-001 establishing that each repo will own its own `evaluator.yaml`, the next question is: what should repos actually have to declare as exemptions, and what should be automatically resolved by the type and trait taxonomy?

The current state of `ecosystem.yaml` contains **62 exception entries** across 13 active repos. The goal of this ADR is to reduce that to as close to zero as possible by promoting shared patterns into first-class types and traits, and to introduce a `deferred` keyword for known failures that are not yet prioritized.

The principle: **if two or more repos share the same exception for the same structural reason, that reason should be a type or trait, not a repeated exemption.**

---

## Current Exception Audit

Running a frequency count across all active repos in `ecosystem.yaml`:

| Rule | Count | Reason Pattern |
|------|-------|---------------|
| TEST-001 | 9 | Not a pipeline-cog with normalization logic |
| TEST-002 | 9 | Not a pipeline-cog with deduplication logic |
| TEST-004 | 9 | Not a pipeline-cog with output shape to verify |
| CD-009 | 5 | Logger primitive or no runtime logging surface |
| CD-002 | 5 | No server entry point (library/static-site) |
| XSTACK-001 | 4 | Is the library itself, or static site with no server logic |
| TEST-003 | 3 | No pipeline failure path (sites, React app) |
| XSTACK-003 | 2 | Pre-dates rule, npm permitted for frontend sites |
| VER-003 | 2 | Cloudflare Pages Git integration — no ci.yml needed |
| VER-005 | 2 | Cloudflare Pages Git integration |
| VER-006 | 2 | Cloudflare Pages Git integration |
| CD-010 | 2 | Library or site — observability stack not applicable |
| PY-011 | 2 | Intentional naming divergence (different reasons) |
| PIPE-008 | 2 | Is the trigger mechanism, or contains retired strings as literals |
| PY-009 | 1 | Pre-dates hatchling standardisation |
| PY-006 | 1 | Is common-python-utils — cannot depend on itself |
| PIPE-011 | 1 | Trigger cog — no evaluation step expected |
| CD-015 | 1 | Multi-flow structure confuses source scanner |

**Total: 62 exception entries.** Target after this ADR: **≤ 5.**

---

## Decision

### Part 1: Revised Type Taxonomy

Types are mutually exclusive. Every repo is exactly one type. The type drives the base set of applicable rules automatically — no exceptions needed for structural facts about the repo category.

**Current types in use:** `worker`, `api`, `library`, `site`, `standards`

**Proposed revised types:**

```yaml
# Mutually exclusive — every repo is exactly one
type:
  pipeline-cog      # Always-on Railway worker running Prefect @flow(s). Processes data.
  trigger-cog       # Always-on Railway worker running asyncio loop. Fires Prefect runs.
  api-service       # HTTP API service (FastAPI or Hono). Has routes, auth, DB.
  shared-library    # Published package consumed by other repos. No entry point.
  static-site       # Astro/HTML site deployed to Cloudflare Pages. No server runtime.
  react-app         # Vite/React SPA. Client-side only. May be in a monorepo.
  standards-repo    # YAML-only definition and tooling repo. Not a deployed service.
```

**Rule applicability by type** — what each type automatically satisfies or excepts:

| Rule | pipeline-cog | trigger-cog | api-service | shared-library | static-site | react-app | standards-repo |
|------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| TEST-001 | ✓ | — | ✓ | — | — | — | — |
| TEST-002 | ✓ | — | ✓ | — | — | — | — |
| TEST-003 | ✓ | — | ✓ | — | — | — | — |
| TEST-004 | ✓ | — | ✓ | — | — | — | — |
| CD-002 | ✓ | ✓ | ✓ | — | — | ✓† | — |
| CD-009 | ✓ | ✓ | ✓ | — | — | — | — |
| CD-010 | ✓ | ✓ | ✓ | — | — | — | — |
| XSTACK-001 | ✓ | ✓ | ✓ | — | — | ✓ | — |
| PIPE-001 | ✓ | — | — | — | — | — | — |
| PIPE-002–009 | ✓ | — | — | — | — | — | — |
| PIPE-011 | ✓† | — | — | — | — | — | — |
| PIPE-008 | ✓ | — | — | — | — | — | — |
| CD-015 | ✓ | — | — | — | — | — | — |
| CD-007 | — | ✓ | — | — | — | — | — |
| VER-003/005/006 | ✓ | ✓ | ✓ | ✓ | — | ✓† | — |
| PY-006 | ✓ | ✓ | ✓ | — | — | — | — |
| PY-012–014 | ✓ | — | — | — | — | — | — |

† See traits section below for remaining edge cases.

This single change — type-scoped rule applicability — eliminates approximately **45 of the 62 current exception entries**.

---

### Part 2: Trait System

Traits are composable boolean flags that handle legitimate edge cases that type alone cannot resolve. A repo can have zero or more traits.

**Proposed traits:**

```yaml
traits:
  - logger-primitive       # This repo IS the shared logger — CD-009 self-reference exempt
  - cloudflare-pages       # Deployed via Cloudflare Pages Git integration — VER-003/005/006 exempt
  - multi-flow             # Runs multiple Prefect flows — CD-015 source-scan false positive known
  - pre-rule               # Predates the rule it would fail — use with rule_id for scoped exemption
  - monorepo-app           # Evaluated as part of a monorepo — CI/config checks at root
  - pipeline-cog-evaluator # Is evaluator-cog itself — PIPE-011 self-reference exempt
```

**How traits eliminate remaining exceptions:**

`logger-primitive` → replaces CD-009 exceptions on `common-python-utils`, `common-typescript-utils`, and logger wrapper modules in `watcher-cog` and `evaluator-cog`. (4 exception entries → 1 trait declaration)

`cloudflare-pages` → replaces VER-003, VER-005, VER-006 exceptions on `website-astro-software` and `website-astro-wcs`. Already partially handled by `static-site` type for Astro sites, but `react-app` on Cloudflare Pages would also need this. (6 exception entries → 1 trait declaration per site)

`multi-flow` → replaces CD-015 exception on `evaluator-cog` where the source scanner cannot resolve `prefect.serve()` due to the dual-flow structure. (1 exception entry → 1 trait declaration)

`pipeline-cog-evaluator` → replaces PIPE-011 self-reference exception on `evaluator-cog`. (1 exception entry → 1 trait declaration)

---

### Part 3: Remaining Genuine Per-Repo Exceptions

After applying the type taxonomy and traits, these are the exceptions that genuinely cannot be generalized — they are specific to one repo for a unique reason:

**`api-kaianolevine-com` — PY-009:**
Pre-dates hatchling standardisation, uses setuptools. Low-priority migration. This is a legitimate `deferred` rather than an exemption — the rule applies, the repo is failing it, fix is planned but not imminent. → Use `deferred` keyword (see Part 4).

**`api-kaianolevine-com` — PY-011:**
Intentional project name `kaianolevine_api` diverges from repo name convention. Renaming would be a breaking change. This is a genuine exemption with a documented reason. → Stays as a per-repo exemption in `evaluator.yaml`.

**`common-python-utils` — PY-011:**
Intentional split package identity: distributed as `common-python-utils`, imported as `mini_app_polis`. Predates PY-011, deliberate branding decision, rename is an indefinitely deferred breaking change. → Stays as a per-repo exemption in `evaluator.yaml`. (Different reason from the api-kaianolevine-com PY-011 exception — both are legitimate.)

**`common-python-utils` — PY-006:**
Cannot depend on itself. Fully covered by `shared-library` type if PY-006 is scoped to `[pipeline-cog, trigger-cog, api-service]` only. → Eliminated by type scoping.

**`evaluator-cog` — PIPE-008:**
The checker source contains retired trigger pattern strings as string literals being checked against, not as active trigger usage. This is genuinely unique to the evaluator — it's the only repo that will ever contain these strings as literals. → Stays as a per-repo exemption in `evaluator.yaml`.

**`website-astro-software` and `website-astro-wcs` — XSTACK-003 (npm, pre-dates pnpm rule):**
Both Astro sites use npm and were scaffolded before XSTACK-003. Migration is low-priority but these are `static-site` type which already excepts XSTACK-003 (pnpm only applies to `new_hono_service` and `new_react_app`). → Eliminated by type scoping. XSTACK-003 should not apply to `static-site` at all.

**After cleanup, remaining genuine per-repo exceptions: 3**
- `api-kaianolevine-com`: PY-011 (intentional project name)
- `common-python-utils`: PY-011 (intentional split package identity)
- `evaluator-cog`: PIPE-008 (contains retired strings as literals, not active usage)

Everything else is either type-scoped, trait-covered, or deferred.

---

### Part 4: The `deferred` Keyword

A `deferred` entry signals: **"this rule applies to us, we know we are failing it, we intend to fix it, but it is not prioritized right now."**

This is semantically distinct from an exemption:
- An **exemption** says the rule does not apply. The evaluator skips the check.
- A **deferral** says the rule applies and we are failing it. The evaluator still runs the check but suppresses the finding from the noise queue, storing it silently in `pipeline_evaluations` with `status: deferred`.

The distinction matters for audit integrity. Deferred findings are still recorded — they just don't surface as active noise. When a deferral expires or is resolved, the finding reappears if the rule is still failing.

**Schema:**

```yaml
# in repo's evaluator.yaml
deferrals:
  - rule: PY-009
    reason: "Pre-dates hatchling standardisation — using setuptools. Migration planned but not scheduled."
    until: null          # null = open-ended. Set a date if there's a real deadline.
    owner: kaiano        # who owns the fix (always the same person in a solo ecosystem, but good habit)

  - rule: XSTACK-003
    reason: "Scaffolded before XSTACK-003 formalised. npm → pnpm migration is low priority."
    until: null
```

**Behavior in the evaluator:**
- Deferred rules are still evaluated — the check runs.
- If failing: finding is written to `pipeline_evaluations` with `status: deferred`, `severity` downgraded to INFO regardless of original severity.
- Deferred findings are excluded from the error/warn counts in the pipeline health summary.
- A separate "Deferred" section in the pipeline health view lists them, so they remain visible but not noisy.
- If a deferred rule is somehow passing, the deferral is noted as resolved in findings and a WARN is raised suggesting the deferral be removed.
- If `until` is set and the date has passed, the deferral expires — the finding re-surfaces at its original severity.

**What should NOT be deferred:**
- Security or data integrity issues (e.g. missing upsert guards, unguarded exception propagation)
- Anything that would cause silent data loss or production failures

**What is appropriate to defer:**
- Tooling standardization (build backend, package manager migrations)
- Documentation coverage (docstrings, README sections)
- Low-urgency structural conventions

---

## Implementation Plan

**Step 1: Update `index.yaml` in `ecosystem-standards`**
Add `type` values using the new taxonomy. Add `traits` as a list field. Document which rules apply to which types. Version bumps are managed by semantic-release via conventional commits.

**Step 2: Update each standards YAML file**
Add or update `applies_to` on each rule to use the new type names. Remove exceptions that are now covered by type scoping. Add `trait_exceptions` where traits grant automatic exemption.

**Step 3: Update `evaluator-cog`**
Teach the evaluator to read `type` and `traits` from each repo's `evaluator.yaml`, apply rule scoping automatically, and handle `deferred` entries.

**Step 4: Create `evaluator.yaml` per repo**
Migrate existing exceptions from `ecosystem.yaml` into per-repo files. After migration, strip `check_exceptions` from `ecosystem.yaml`.

**Step 5: Slim down `ecosystem.yaml`**
Remove `check_exceptions` from all entries. It becomes a registry only (ADR-001).

---

## Resulting `evaluator.yaml` Examples

**`watcher-cog/evaluator.yaml`** — after migration, no exceptions needed:
```yaml
type: trigger-cog
traits:
  - logger-primitive
  - cloudflare-pages    # not applicable — but shown for illustration
```

**`common-python-utils/evaluator.yaml`:**
```yaml
type: shared-library
traits:
  - logger-primitive
exemptions:
  - rule: PY-011
    reason: "Intentional split package identity: distributed as common-python-utils, imported as mini_app_polis. Predates PY-011. Rename is a breaking change deferred indefinitely."
```

**`api-kaianolevine-com/evaluator.yaml`:**
```yaml
type: api-service
exemptions:
  - rule: PY-011
    reason: "Intentional project name kaianolevine_api. Repo named api-kaianolevine-com by infrastructure convention. Renaming would break installed package."
deferrals:
  - rule: PY-009
    reason: "Pre-dates hatchling standardisation — using setuptools. Migration is low-priority backlog."
    until: null
```

**`evaluator-cog/evaluator.yaml`:**
```yaml
type: pipeline-cog
traits:
  - multi-flow
  - pipeline-cog-evaluator
exemptions:
  - rule: PIPE-008
    reason: "Deterministic checker source contains retired trigger pattern strings as string literals being checked against, not as active trigger usage."
```

**`website-astro-software/evaluator.yaml`:**
```yaml
type: static-site
traits:
  - cloudflare-pages
```

---

## Consequences

**Positive:**
- Exception count drops from 62 to 3 genuine per-repo exemptions + a small number of deferrals
- `ecosystem.yaml` becomes a clean registry with no exception management
- New repos get correct rule scoping automatically from type declaration — near-zero `evaluator.yaml` configuration for standard repo types
- Deferred findings remain visible and auditable without generating noise
- The taxonomy is self-documenting — reading a repo's `evaluator.yaml` immediately tells you what it is and why anything is excepted

**Negative / trade-offs:**
- Rule applicability logic in `evaluator-cog` becomes more sophisticated — it must resolve type + trait combinations rather than a flat exception list
- Requires a one-time migration pass across all repos
- Standards YAML files need `applies_to` updated to use the new type names (breaking change in the standards schema — requires a major version bump)