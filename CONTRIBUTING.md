# Contributing to ecosystem-standards

This repo is the single source of truth for architectural decisions,
conventions, and rules across the MiniAppPolis ecosystem. Any human
or agent given this repo should be able to make a change — add a
rule, record a decision, update the registry — and produce the same
result as anyone else doing the same task.

The short version: find the right playbook for your change, follow
it, commit with a Conventional Commits message, let semantic-release
handle the version bump.

---

## What are you changing?

Pick the playbook that matches your change:

| Change                                                       | Playbook                              |
|--------------------------------------------------------------|---------------------------------------|
| Add, edit, or retire a rule in `standards/*.yaml`            | `playbooks/new-standard.md`           |
| Write or supersede an ADR in `docs/decisions/`               | `playbooks/new-adr.md`                |
| Edit `ecosystem.yaml`, `index.yaml` schema, types, traits,   | `playbooks/ecosystem-changes.md`      |
| canonical enums, DoD checklists, or add a standards file     |                                       |
| Bootstrap a new cog                                          | `playbooks/new-cog.md`                |

If you're unsure which applies, use this test:

- **Will the change cause a different finding to appear (or
  disappear) on a repo?** → rule change. Read `new-standard.md`.
- **Does the change record *why* we're doing something a certain
  way?** → ADR. Read `new-adr.md`.
- **Does the change add, rename, retire a service, type, trait, or
  enum value?** → ecosystem change. Read `ecosystem-changes.md`.

When a change spans two categories, follow the rule playbook last.
Types and enums must exist before rules can reference them; ADRs
should be written before the rules they justify.

---

## Principles that shape these playbooks

Four policy decisions shape everything in the contribution process.
If a playbook seems to contradict one of these, the playbook is
wrong — flag it.

1. **Scope by playbook.** Each playbook covers one class of change.
   `new-standard.md` does not cover ADRs; `new-adr.md` does not
   cover ecosystem edits. A change that spans classes chains the
   playbooks in dependency order.
2. **Delete on retirement.** Retired rules, services, types, and
   files are removed. Git history is the audit trail. Only ADRs are
   preserved after being superseded, because their reasoning is the
   artifact.
3. **Rule if enforceable; ADR if rationale.** The test for whether
   something belongs in `standards/*.yaml` is whether an evaluator
   can check it. If the claim is "here's why we chose this," that's
   an ADR.
4. **Primary concern wins; no duplication.** Cross-cutting rules go
   in the file whose prefix matches the primary concern. Before
   picking a home, check whether the rule is actually two or three
   rules welded together — often it is, and the right fix is a
   split.

---

## Self-rules

This repo's own structure is governed by `standards/meta.yaml`
(META-001 through META-007). Read those before making changes to
file headers, canonical enums, or `check_notes` format. The playbooks
operationalize the META rules — if you follow the playbook, you
satisfy META by construction.

Highlights:

- **META-001**: `package.json` version is owned by semantic-release.
  Never edit by hand.
- **META-002**: No `added:` fields, no top-level `updated:` /
  `maintainer:`, no `# Version:` header comments in YAML or
  Markdown. Git log is the record.
- **META-003**: Canonical enums in `index.yaml` are dictionaries
  with descriptions, not bare lists.
- **META-005**: Checkable rules open `check_notes` with
  `DETERMINISTIC CHECK.` or `LLM CHECK.` on the first line.
- **META-006**: A rule's ID prefix must match its file's declared
  `rule_prefix` in `index.yaml`. No orphaned prefixes.
- **META-007**: Rule IDs are append-only. Retired numbers are never
  reused — the next ID is `max(ever-seen) + 1` computed from git
  history. See `new-standard.md` Step 4 for the command.

---

## Commit messages

All commits follow [Conventional Commits](https://www.conventionalcommits.org/).
semantic-release reads them to pick the next version bump and write
the changelog.

| Prefix       | Version bump | Use when                                                   |
|--------------|--------------|------------------------------------------------------------|
| `feat:`      | minor        | Adding a new rule, type, trait, service, or dimension      |
| `fix:`       | patch        | Fixing a mistake — wrong threshold, typo, bad check_notes  |
| `refactor:`  | patch        | Restructuring without changing semantics                   |
| `docs:`      | patch        | README, ADRs, playbooks                                    |
| `chore:`     | none         | Release commits, dependency bumps                          |

Use `!` or a `BREAKING CHANGE:` body footer for changes that break
consumers (evaluator-cog, per-repo `evaluator.yaml` files).

Do not edit `package.json` or `CHANGELOG.md` by hand. semantic-release
owns both.

---

## Testing your change

Before committing:

1. **YAML validity.** Any `standards/*.yaml`, `index.yaml`,
   `ecosystem.yaml`, and `definitions-of-done.yaml` must parse. A
   quick check:
   ```bash
   python -c "import yaml, sys; [yaml.safe_load(open(f)) for f in sys.argv[1:]]" standards/*.yaml index.yaml ecosystem.yaml definitions-of-done.yaml
   ```
2. **Cross-references resolve.** If a rule references another rule
   ID, a repo type, or a trait, the referent must exist in
   `index.yaml`. If a `description:` mentions a service, that
   service must be in `ecosystem.yaml`.
3. **META-002 clean.** Grep for forbidden fields:
   ```bash
   grep -rnE '^\s*added:\s*[0-9]' standards/ index.yaml ecosystem.yaml
   grep -rnE '^# Version:' standards/ index.yaml ecosystem.yaml definitions-of-done.yaml
   ```
   Either command should return no matches.
4. **META-005 clean.** Every `checkable: true` rule should have a
   `check_notes` starting with `DETERMINISTIC CHECK.` or `LLM CHECK.`.

---

## Repo structure reference

```
ecosystem-standards/
├── CONTRIBUTING.md                 ← you are here
├── README.md                       ← consumer-facing overview
├── CHANGELOG.md                    ← owned by semantic-release
├── BACKLOG.md                      ← open items
├── package.json                    ← version, owned by semantic-release
├── index.yaml                      ← manifest, enums, schema
├── ecosystem.yaml                  ← service registry
├── evaluator.yaml                  ← per-repo config for this repo
├── definitions-of-done.yaml        ← DoD checklists
├── standards/
│   ├── principles.yaml             ← PRIN
│   ├── python.yaml                 ← PY, CFG
│   ├── testing.yaml                ← TEST
│   ├── documentation.yaml          ← DOC
│   ├── api.yaml                    ← API, AUTH
│   ├── pipeline.yaml               ← PIPE
│   ├── frontend.yaml               ← FE
│   ├── delivery.yaml               ← CD, VER
│   ├── meta.yaml                   ← META (rules for this repo)
│   ├── evaluation.yaml             ← EVAL
│   ├── monorepo.yaml               ← MONO
│   └── cross-stack.yaml            ← XSTACK
├── docs/
│   └── decisions/                  ← ADRs (ADR-NNN-slug.md)
│       └── README.md               ← ADR index
└── playbooks/
    ├── new-standard.md             ← rule changes
    ├── new-adr.md                  ← ADR lifecycle
    ├── ecosystem-changes.md        ← everything else
    └── new-cog.md                  ← bootstrap a new cog
```

---

## When the playbooks are wrong

Playbooks are themselves standards — they should be self-consistent
and current. If you find a contradiction between a playbook and a
META rule, the META rule wins and the playbook needs a `docs:` edit.
If you find a contradiction between two playbooks, open a PR that
resolves it. If the process itself needs rethinking, write an ADR
first (`playbooks/new-adr.md`) and update the playbooks from the
ADR.

A playbook that drifts from actual practice is a signal to fix one
or the other. Don't leave the mismatch in place.
