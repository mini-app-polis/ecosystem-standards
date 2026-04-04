# ecosystem-standards

Machine-readable standards for the MiniAppPolis ecosystem.

This repo is the single source of truth for all architectural decisions, patterns, and conventions. It is the rubric used by evaluator agents and the reference point for all development work.

---

## How It Works

Standards live as versioned YAML files — human-readable enough to edit directly, machine-readable enough for agents to fetch and evaluate against at runtime.

**For humans:** edit the YAML files directly when a real issue drives a new rule. Commit with a clear message explaining why.

**For agents:** fetch `index.yaml` first to discover available files and the current version, then fetch the relevant domain file(s).

```
GET index.yaml                        → manifest, version, file list
GET standards/<domain>.yaml           → rules for that domain
```

Every evaluation output should pin the `version` from `index.yaml` so findings are traceable to a specific standards state.

---

## Repo Structure

```
ecosystem-standards/
├── index.yaml                  ← start here — manifest and version
├── README.md
├── CHANGELOG.md
├── standards/
│   ├── principles.yaml         ← PRIN — immutable core philosophy
│   ├── python.yaml             ← PY, CFG — Python tooling, structure, config
│   ├── testing.yaml            ← TEST — critical path coverage, FastAPI testing
│   ├── documentation.yaml      ← DOC — README, docstrings, OpenAPI
│   ├── api.yaml                ← API, AUTH — service structure, auth rules
│   ├── pipeline.yaml           ← PIPE — orchestration, idempotency, data safety
│   ├── frontend.yaml           ← FE — Astro sites, React apps
│   ├── delivery.yaml           ← CD, VER — CI/CD, observability, versioning
│   ├── evaluation.yaml         ← EVAL — how AI evaluation is performed
│   └── cross-stack.yaml        ← XSTACK — Python/TypeScript parity rules
└── evaluators/                 ← agent scripts (future)
```

---

## Rule Format

Every rule has:

```yaml
- id: DOMAIN-NNN               # stable ID — used in cross-references and evaluation findings
  title: Short description
  status: requirement          # requirement | convention | advisory | idea | gap
  dimension: ...               # maps to pipeline_evaluations.dimension
  severity: ERROR              # ERROR | WARN | INFO — maps to pipeline_evaluations.severity
  description: >
    Full description of the rule and what it means in practice.
  checkable: true              # can an agent verify this automatically?
  check_notes: >               # if checkable: how to check it
    What to look for and what to flag.
  origin: >                    # optional — the issue that drove this rule
    Why this rule exists.
  added: 2026-03               # when the rule was added
```

---

## How Standards Evolve

**When you hit an issue:**
1. Open this repo
2. Add or update a rule in the relevant YAML file
3. Commit with a message explaining the issue that drove it
4. Bump the version in `index.yaml` and add a changelog entry

The git history is your audit trail. The `origin` field on each rule is the permanent record of why it exists.

**Status progression:**
```
idea → (validated by real issue) → requirement → (check_notes added) → enforced by agent
```

**Standard types:**
- `requirement` — must-comply, agents flag violations
- `convention` — should-comply, deviation requires a comment
- `advisory` — guidance only, agents report informational
- `idea` — under consideration, not yet enforced
- `gap` — known deficiency, tracked for remediation

---

## Dimensions

Evaluation dimensions map directly to the `pipeline_evaluations` table:

| Dimension | What it covers |
|---|---|
| `structural_conformance` | repo/workflow follows documented patterns |
| `pipeline_consistency` | run behaves the same as previous runs |
| `testing_coverage` | critical path and contract tests present |
| `documentation_coverage` | README, .env.example, OpenAPI complete |
| `cd_readiness` | Sentry, logging, feature flags, CI configured |
| `cross_repo_coherence` | naming, data shapes consistent across repos |
| `standards_currency` | evaluated against current standards version |

