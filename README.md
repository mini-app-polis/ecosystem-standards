# ecosystem-standards

Machine-readable standards for the MiniAppPolis ecosystem.

This repo is the single source of truth for architectural decisions, patterns, and conventions. It is the rubric used by evaluator-cog and the reference point for all development work.

---

## How It Works

Standards live as versioned YAML files — human-readable enough to edit directly, machine-readable enough for agents to fetch and evaluate against at runtime.

**For humans:** edit the YAML files directly when a real issue drives a new rule. Commit with a conventional-commit message explaining why — semantic-release owns version bumps and CHANGELOG entries.

**For agents:** fetch `index.yaml` first to discover available files, fetch `package.json` for the current release value, then fetch the relevant domain file(s).

```
GET index.yaml                        → manifest, dimensions, severities, statuses, schema
GET package.json                      → version of the standards repo
GET standards/<domain>.yaml           → rules for that domain
GET ecosystem.yaml                    → inventory of services, libraries, patterns
GET definitions-of-done.yaml          → per-artifact DoD checklists
```

Every evaluation output pins the `version` from `package.json` so findings are traceable to a specific standards state (see EVAL-002).

---

## Repo Structure

```
ecosystem-standards/
├── package.json                    ← version (owned by semantic-release)
├── index.yaml                      ← manifest — dimensions, severities, schema, file list
├── ecosystem.yaml                  ← services / libraries / patterns inventory
├── evaluator.yaml                  ← per-repo config for this repo
├── definitions-of-done.yaml        ← per-artifact DoD checklists
├── README.md
├── CONTRIBUTING.md                 ← router for all changes
├── CHANGELOG.md
├── BACKLOG.md
├── standards/
│   ├── principles.yaml             ← PRIN — immutable core philosophy
│   ├── python.yaml                 ← PY — Python tooling, structure, error handling
│   ├── config.yaml                 ← CFG — pydantic-settings & .env.example contracts
│   ├── testing.yaml                ← TEST — critical path coverage, FastAPI testing
│   ├── documentation.yaml          ← DOC — README, docstrings, OpenAPI
│   ├── api.yaml                    ← API — service structure, response envelopes
│   ├── auth.yaml                   ← AUTH — Clerk verification, client-API parity
│   ├── pipeline.yaml               ← PIPE — orchestration, idempotency, data safety
│   ├── frontend.yaml               ← FE — Astro sites, React apps
│   ├── delivery.yaml               ← CD — CI/CD, observability, Sentry, logging
│   ├── versioning.yaml             ← VER — Conventional Commits, semantic-release
│   ├── meta.yaml                   ← META — rules governing this repo itself
│   ├── evaluation.yaml             ← EVAL — how AI evaluation is performed
│   ├── monorepo.yaml               ← MONO — pnpm workspace rules
│   └── cross-stack.yaml            ← XSTACK — Python/TypeScript parity rules
├── docs/
│   └── decisions/                  ← ADRs (ADR-NNN-slug.md)
│       └── README.md               ← ADR index
└── playbooks/
    ├── new-standard.md             ← rule changes
    ├── new-adr.md                  ← ADR lifecycle
    ├── ecosystem-changes.md        ← registry, types, enums, DoD
    └── new-cog.md                  ← bootstrap a new cog
```

---

## Rule Format

Every rule has:

```yaml
- id: DOMAIN-NNN               # stable ID — used in cross-references and findings
  title: Short description
  status: requirement          # requirement | convention | gap
  dimension: ...               # maps to pipeline_evaluations.dimension
  severity: ERROR              # ERROR | WARN | INFO at the rule level
  applies_to: [pipeline-cog]   # optional — repo types scanned for this rule
  modifies: []                 # optional — rule IDs whose evaluation this rule alters
  description: >
    Full description of the rule and what it means in practice.
  checkable: true              # can an agent verify this automatically?
  check_notes: >               # if checkable: how to check it
    DETERMINISTIC CHECK.       # or LLM CHECK. — required first line (META-005)
    What to look for and what to flag.
  origin: >                    # optional — the issue that drove this rule
    Why this rule exists.
```

Rule-level severity is `ERROR | WARN | INFO`. `CRITICAL` and `SUCCESS` are emission-only outcome severities used by evaluators and pipeline cogs — they do not appear on rule definitions. See `index.yaml` for the full severity and status tables.

---

## Making changes

All changes to this repo follow a playbook. The top-level router is
[`CONTRIBUTING.md`](CONTRIBUTING.md) — start there. It points at:

- `playbooks/new-standard.md` — add, edit, or retire a rule in `standards/*.yaml`.
- `playbooks/new-adr.md` — write or supersede an ADR in `docs/decisions/`.
- `playbooks/ecosystem-changes.md` — edit `ecosystem.yaml`, `index.yaml` schema, types, traits, canonical enums, or DoD checklists.

The git history is the audit trail. The `origin` field on each rule is the permanent record of why it exists. Status progression for rules is `gap → (check_notes added, implementation shipped) → requirement → enforced by evaluator`. Rules observed in practice but not yet ready to enforce sit at `convention` until they become checkable requirements.

---

## Dimensions

Evaluation dimensions map directly to the `pipeline_evaluations` table. Every rule declares exactly one dimension — findings are aggregated on this field in the Pipeline Health views.

| Dimension | What it covers |
|---|---|
| `structural_conformance` | Repo/workflow follows documented patterns — src layout, naming, error handling, tooling choices. |
| `pipeline_consistency` | Run behaved the same as previous runs — timing, error types, output shape. |
| `pipeline_reliability` | Pipeline runs correctly under concurrent or repeated invocation — idempotency, retries, integrity guards. |
| `testing_coverage` | Critical paths covered by appropriate test layer — unit, integration, contract. |
| `documentation_coverage` | Repo understandable without reading every file — README, docstrings, ADRs, `.env.example`. |
| `cd_readiness` | Safe to deploy continuously — Sentry, structured logging, semantic-release, feature flags. |
| `cross_repo_coherence` | Similar concepts look similar across repos — naming, response shapes, shared library usage. |
| `standards_currency` | Evaluated against current standards version — version resolution, staleness, evaluator/standards drift. |
| `monorepo_coherence` | pnpm monorepo workspaces satisfy per-app and root-level rules — workspace_deps, scoping, dedup. |

Canonical definitions live in `index.yaml` `dimensions:` — edit there, not here.

---

## Repo Types and Traits

Each evaluatable repo declares a type (and optional traits) in its own `evaluator.yaml` at its repo root (see EVAL-008). The taxonomy is defined in `index.yaml` `schema.repo_types` and `schema.traits`. Rules gate themselves by type via `applies_to:`; traits carry additional context. Each trait may declare structured `exempts:` (rule IDs the trait unconditionally exempts) or `downgrades:` (rule IDs whose severity is lowered when the trait applies). Example: `logger-primitive` exempts the shared logger repo from CD-009. The full dispatch precedence across types, traits, exemptions, deferrals, and downgrades is documented in `index.yaml` `schema.dispatch`.

---

## Related Docs

- `CONTRIBUTING.md` — top-level router for any change to this repo.
- `docs/decisions/` — Architecture Decision Records. See `docs/decisions/README.md` for the index. Start with ADR-001 (federated evaluation), ADR-002 (type/trait taxonomy), ADR-003 (conformance checker architecture), ADR-004 (`applies_to` single meaning), ADR-005 (schema clarity audit).
- `playbooks/` — narrative guides for common changes: `new-standard.md` (rules), `new-adr.md` (decisions), `ecosystem-changes.md` (registry, types, enums, DoD), `new-cog.md` (bootstrap a new cog).
- `BACKLOG.md` — open items and roadmap for the standards themselves.
- `CHANGELOG.md` — managed by semantic-release; never edit manually.
