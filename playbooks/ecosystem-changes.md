# Playbook: changes outside `standards/*.yaml`

This is the canonical process for editing anything in this repo that
is not a rule in `standards/*.yaml` and not an ADR in `docs/decisions/`.

That includes:

- `ecosystem.yaml` — the service and library registry.
- `index.yaml` — the manifest: dimensions, severities, statuses,
  `schema.repo_types`, `schema.traits`, `schema.evaluator_yaml`, the
  `files:` list.
- `definitions-of-done.yaml` — per-artifact DoD checklists.
- New or renamed files under `standards/` (the container, not a
  specific rule).

For rule changes, see `playbooks/new-standard.md`. For decision records,
see `playbooks/new-adr.md`.

---

## Decision tree

Before editing, identify the shape of the change. That determines
which section of this playbook applies.

```
  is the change a new rule or rule edit?             → new-standard.md
  is the change an ADR (decision rationale)?         → new-adr.md
  is the change about a service, library, or repo?   → §1 ecosystem.yaml
  is the change a new repo type or trait?            → §2 taxonomy
  is the change a new dimension, severity, status?   → §3 canonical enums
  is the change a new standards file or prefix?      → §4 standards file
  is the change a DoD checklist item?                → §5 definitions-of-done
  is the change to index.yaml schema itself?         → §6 schema surface
```

If a change spans more than one section, do them in the order listed —
taxonomy before enums, enums before the rule that uses them, rule
before the DoD item that references it. A commit that adds a new repo
type and a rule that uses it in one step is fine; a rule that
references a repo type not yet in `index.yaml` is not.

---

## §1 — `ecosystem.yaml` (service and library registry)

`ecosystem.yaml` is the inventory of everything that gets evaluated.
Update it whenever a service is added, renamed, archived, or changes
role.

### Adding a new service or library

1. Add an entry under `services:` with the required fields:
   ```yaml
   - id: <repo-name>              # canonical kebab-case repo name
     type: <type>                 # one of the types in index.yaml
     status: active               # active | transitioning | retired
     dod_type: <dod_key>          # key in definitions-of-done.yaml, or null
     language: python             # python | typescript | astro | yaml | ...
     host: railway                # or cloudflare-pages, etc.
     description: >
       One-paragraph description — what the service does, what it
       consumes, what it produces.
   ```
2. If the service belongs in a monorepo, add `monorepo:` and
   `monorepo_path:` (see `index.yaml` `schema.monorepo_fields`).
3. If the service has no matching DoD checklist yet, see §5.
4. If the service introduces a new type, see §2 first.

### Renaming a service

Service names are referenced by rule `description` and `origin` fields
across the repo. A rename is not just editing one line.

1. Update the `id:` in `ecosystem.yaml`.
2. Grep for the old name across the repo and update each reference:
   ```bash
   grep -rn "old-name" standards/ docs/ playbooks/ README.md
   ```
3. In rule `origin:` fields, update the name. Descriptions should
   prefer role words ("the shared logger repo") over specific names
   where possible, but a specific name is fine if the rule is genuinely
   about that repo.

### Retiring a service

The policy is **delete, don't tombstone**. Git history is the record.

1. Remove the entry from `services:`.
2. Grep for remaining references and either:
   - Remove them, if the rule is no longer relevant; or
   - Rewrite them to reference a current service or use role words,
     if the underlying concern still applies.
3. If a rule existed only to constrain the retired service, retire the
   rule too (see `new-standard.md` Step 8).
4. The commit message should say what was retired and why. That's the
   durable record.

### Transitioning status

`status: transitioning` signals a repo that is being migrated — new
work should target the successor, but the old one still runs. Use
sparingly. A transition longer than one or two release cycles should
either complete (set successor to `active` and retire predecessor) or
roll back.

---

## §2 — Adding a repo type or trait

Types and traits live in `index.yaml` under `schema.repo_types` and
`schema.traits`. They are canonical — rules gate themselves by type
via `applies_to:`, and traits carry additional context.

### Adding a type

A new type is justified when:

1. At least one existing or near-future repo doesn't fit any current
   type.
2. Rule applicability across multiple domains (testing, delivery,
   pipeline) would differ if the repo had its own type.
3. The alternative is a growing list of per-repo exemptions that all
   share the same reason.

Process:

1. Add the entry to `index.yaml` `schema.repo_types:` with a one-line
   description (see META-003 — these must be dict-with-description).
2. Grep every `standards/*.yaml` file for `applies_to:` and decide
   whether each rule includes the new type. Err on the side of
   narrowing: a new type should opt in to rules explicitly, not
   inherit broadly.
3. If an ADR is shaping the decision, write it first
   (`new-adr.md`) — a new type almost always has an ADR behind it.
   ADR-002 is the canonical example.
4. Update `README.md` and any playbook that references the type list.

### Adding a trait

Traits compose with types. They exist to handle edge cases that type
alone can't resolve — e.g. `logger-primitive` exempts the shared
logger repo from the rule that says "import the shared logger."

A new trait is justified when:

1. Two or more repos share the same structural exemption for the same
   reason.
2. Encoding the exemption as a rule-level `applies_to` change would
   mis-fit repos that happen to share the type but not the trait.

Process:

1. Add to `index.yaml` `schema.traits:` with a one-line description.
2. Name the trait for the structural property, not the outcome.
   `logger-primitive` ≠ `exempt-from-cd-009`.
3. Document which rules the trait interacts with in the rule's
   `check_notes` (evaluator-cog reads this).
4. Never invent a trait for a one-off. If only one repo has the
   condition, use an `exemption` in that repo's `evaluator.yaml`
   instead.

### Retiring a type or trait

Same policy as services: delete, don't tombstone.

1. Remove from `index.yaml`.
2. Grep every rule file and every `evaluator.yaml` across the
   ecosystem for references. Update or remove.
3. If any repo's `evaluator.yaml` used the trait, that file needs a
   commit in the repo it lives in. Coordinate the removal.

---

## §3 — Canonical enums (dimensions, severities, statuses)

`index.yaml` defines three canonical enum sets used by every rule:

- `dimensions:` — categories of concern (one per rule).
- `severities:` — ERROR / WARN / INFO at the rule level, plus
  CRITICAL / SUCCESS as emission-only outcomes.
- `statuses:` — requirement / convention / advisory / idea / gap.

These are **dictionaries mapping each value to a description** per
META-003. A new value is a material change to what the ecosystem
measures.

### Adding a dimension

A new dimension is justified when findings about a meaningfully
distinct concern would otherwise be miscategorized against an
existing dimension.

Process:

1. Write or update an ADR explaining the addition — a new dimension
   is architectural (see `new-adr.md`).
2. Add the entry to `index.yaml` `dimensions:` with a one-sentence
   description of what it covers.
3. Update `README.md`'s dimension table.
4. Update `new-standard.md` Step 6 decision guide with the new
   dimension.
5. Assign the dimension to any existing rule it applies to — usually
   none at introduction; the dimension is introduced alongside a
   rule that uses it.

### Adding a severity or status

Extremely rare. The three rule-level severities (ERROR, WARN, INFO)
and five statuses (requirement, convention, advisory, idea, gap)
have been stable. Adding a value here is an ADR-worthy decision —
write the ADR first.

### Retiring a value

Delete the value. Grep every rule file for it and either reassign
or delete the affected rules. A retired dimension may leave findings
in `pipeline_evaluations` that reference it — that is historical
data, not a reason to keep the value.

---

## §4 — Adding a standards file or prefix

Each `standards/*.yaml` file is scoped to a rule prefix (PY, TEST,
etc.). Adding a file is a material expansion of the catalog.

### When to add a new file

1. A new domain exists that doesn't fit any current file
   (`standards/security.yaml` would be a candidate if security rules
   grew past what fits naturally in `api.yaml`, `python.yaml`, or
   `delivery.yaml`).
2. An existing file grew past the point where readers have to scroll
   to find rules they know exist.

Adding a prefix without a new file (e.g. a new SEC prefix inside
`api.yaml`) is usually a sign to split the file instead.

### Process

1. Pick the prefix. Uppercase letters, short (3–6 characters). Must
   not collide with any existing prefix.
2. Create `standards/<domain>.yaml` with the file-header comment
   pattern the other files use (see `standards/testing.yaml` for the
   template).
3. Add an entry to `index.yaml` `files:`:
   ```yaml
   - file: standards/<domain>.yaml
     domain: <domain>
     description: One-sentence scope.
     rule_prefix: <PREFIX>     # or [PREFIX_A, PREFIX_B] for multi-prefix
   ```
4. Update the prefix table in `playbooks/new-standard.md` Step 3.
5. Update the tree in `README.md` under "Repo Structure".

### Retiring a file or prefix

Delete the file. Delete or merge its rules into another file. Update
`index.yaml`, `new-standard.md`, `README.md`.

---

## §5 — DoD checklists (`definitions-of-done.yaml`)

DoD checklists are consumed by evaluator-cog for post-PR assessment.
Each key is a `dod_type` referenced from `ecosystem.yaml`.

### Adding a checklist

1. Add a new key at the top level of `definitions_of_done:`. The key
   should match the `dod_type` used in `ecosystem.yaml`.
2. Give it a `label:` (human-readable) and a `checklist:` (list of
   one-line criteria strings).
3. Each checklist item should be independently checkable — if two
   criteria always fail together, collapse them into one.
4. Reference specific rule IDs where applicable (e.g. "see PY-012"
   or "per DOC-013"). This keeps the checklist honest and links it to
   the enforceable rules.

### Editing a checklist

Edit in place for most changes — adding items, clarifying wording,
removing obsolete items. The `dod_type` key itself is stable; do not
rename it unless you're also updating every `ecosystem.yaml` entry
that references it.

### Removing a checklist

If no service references the `dod_type`, delete the key. Grep
`ecosystem.yaml` to be sure.

---

## §6 — `index.yaml` schema surface

The `schema:` section of `index.yaml` documents the shape of rule
files, the `evaluator.yaml` file per repo, service fields in
`ecosystem.yaml`, and monorepo fields. Changes here are changes to
the data contract between this repo and every consumer.

### Adding a schema field

1. Write the ADR first if the field changes how repos configure
   themselves (`evaluator.yaml`) or how rules are evaluated.
2. Add the field under the relevant schema section with a
   description of format, purpose, and whether it is required.
3. If the field is optional, document the default and when to use it.
   If required, note how existing files should be migrated.
4. Update at least one consumer reference implementation in the same
   or an immediately-following commit (evaluator-cog, most commonly).

### Removing a schema field

1. Audit consumers. A schema removal can break runtime behavior in
   evaluator-cog or any repo's `evaluator.yaml`.
2. If the field was optional, remove from `index.yaml` and grep the
   repo for references in rule `check_notes` or playbook text.
3. If the field was required, stage the removal: first mark it
   optional, let consumers migrate, then remove.

---

## Commit messages

Conventional Commits. semantic-release reads them to pick the next
version bump.

| Change                                               | Prefix         |
|------------------------------------------------------|----------------|
| Adding a service, type, trait, dimension, or file    | `feat:`        |
| Editing a description or checklist item              | `fix:` or `refactor:` |
| Renaming a service (with ripple updates)             | `refactor:`    |
| Retiring a service, type, file, or DoD checklist     | `feat!:` or `refactor!:` with `BREAKING CHANGE:` body if it affects consumers |
| Playbook or README edits                             | `docs:`        |

Examples:

- `feat(ecosystem): add spotify-cog to services registry`
- `refactor(taxonomy): split api-service into api-service and
  api-service-billing`
- `feat!(schema): remove deprecated check_exceptions from
  ecosystem.yaml` (with BREAKING CHANGE body referring to ADR-001)

Do not edit `package.json` or `CHANGELOG.md` by hand (see META-001).

---

## See also

- `index.yaml` — the file most of this playbook edits.
- `ecosystem.yaml` — the service registry.
- `definitions-of-done.yaml` — DoD checklists.
- `standards/meta.yaml` — META-001 through META-005, the self-rules
  that govern this repo's structure.
- `playbooks/new-standard.md` — for rule changes in `standards/*.yaml`.
- `playbooks/new-adr.md` — for ADRs in `docs/decisions/`.
