# Playbook: writing or superseding an ADR

This is the canonical process for adding or changing an Architecture
Decision Record in `docs/decisions/`. Any human or agent supplied with
this repo should follow this playbook and produce the same result.

For rules in `standards/*.yaml`, see `playbooks/new-standard.md`. For
edits to `ecosystem.yaml`, `index.yaml` schema, repo types, traits, DoD
checklists, or canonical enums, see `playbooks/ecosystem-changes.md`.

---

## Step 1 — Is this really an ADR?

Use the same test as in `playbooks/new-standard.md` Step 1:

- **ADR** — if you are recording *why* the ecosystem chose approach X
  over approach Y, and that rationale shapes many downstream decisions,
  it belongs in `docs/decisions/` as an ADR.
- **Rule** — if the constraint can be checked against a repo by
  inspection, it belongs in `standards/*.yaml`.

A topic can have both. The ADR captures the "why"; individual rules in
`standards/*.yaml` capture the "what." If you are introducing a
significant new convention, write the ADR first, then derive rules from
it. ADR-001 → `evaluator.yaml` rules is the canonical example.

Write an ADR when at least one of these is true:

1. The decision closes off alternatives that a reasonable person would
   otherwise pick (e.g. "central vs federated config").
2. The decision has consequences that will shape future work beyond the
   immediate change (e.g. "all repos will now own an `evaluator.yaml`").
3. The decision reverses or supersedes an earlier decision — the old
   reasoning needs to be recorded before it's overwritten.

Do **not** write an ADR for:

- Adding a single rule that derives from existing decisions (that's a
  rule edit — see `new-standard.md`).
- Minor tooling changes without architectural consequence.
- Style or wording fixes.

---

## Step 2 — Pick the next ADR number

ADRs are numbered sequentially, three digits, no gaps. To find the next:

```bash
ls docs/decisions/ADR-*.md | sort | tail -1
```

Add one to the number. Never reuse an ADR number, even if the earlier
ADR was superseded — superseded ADRs stay in the directory as the
audit trail.

---

## Step 3 — Choose the file name

File name pattern (from DOC-005):

```
docs/decisions/ADR-NNN-short-slug.md
```

- `NNN` is three digits (`001`, `002`, ..., `042`).
- `short-slug` is kebab-case, 3–6 words, describing the decision not
  the component. Prefer a noun phrase over an active verb.

Good examples:

- `ADR-001-federated-evaluation-config.md`
- `ADR-002-type-trait-taxonomy-and-deferral.md`
- `ADR-003-conformance-checker-architecture.md`

Bad examples:

- `ADR-099-fix-ci.md` (too vague, reads as a ticket, not a decision)
- `ADR-099-use-postgres.md` (active-verb framing; prefer
  `ADR-099-postgres-as-primary-store.md`)

---

## Step 4 — Write the required sections

Every ADR has this structure. Use the existing three ADRs as the
formatting reference.

```markdown
# ADR-NNN: Decision title

**Date:** YYYY-MM-DD
**Status:** Proposed | Accepted | Superseded
**Repo:** ecosystem-standards
**Depends on:** ADR-NNN (optional — only if it builds on another)
**Supersedes:** ADR-NNN or <file> (optional — only if it replaces one)

---

## Context

What forces are in play? What is the current state? What problem
prompted this decision? Keep this concrete — name the repos, the
patterns, the symptoms. Abstract context is unhelpful.

---

## Decision

What did we decide? State it in one or two sentences up front, then
expand. If the decision has sub-parts, split them into subsections.
Include schema examples, code sketches, or tables where they clarify
the decision concretely.

---

## Consequences

**Positive:** what this unlocks or simplifies.
**Negative / trade-offs:** what becomes harder, what we accept.

List concrete consequences, not marketing copy. "Simpler code" is not
a consequence; "N per-repo exception entries collapse to one trait
declaration" is.

---

## Alternatives Considered

(Optional but strongly recommended.) Name each alternative in a
sub-heading, describe why it was rejected. This is what prevents the
next person from re-litigating the same decision.
```

**Required sections per DOC-005:** Context, Decision, Consequences. The
header metadata block (Date, Status, Repo) is required too. Depends on,
Supersedes, and Alternatives Considered are optional.

---

## Step 5 — Status lifecycle

ADRs move through these states:

- **Proposed** — the ADR is drafted but the decision hasn't been
  committed to yet. Rare in this repo (we tend to write ADRs after
  deciding), but valid.
- **Accepted** — the default state. The ecosystem operates on this
  decision.
- **Superseded** — a later ADR replaces this one. The file stays in
  place but the status is flipped, and a `**Superseded by:** ADR-NNN`
  line is added near the top.

You do not delete superseded ADRs. The history of how thinking evolved
is the value — a current reader needs to be able to trace why ADR-007
exists by reading the ADR-003 it replaced.

This is different from rule retirement (see `new-standard.md` Step 8),
where deletion is correct because `standards/*.yaml` reflects the
current required state. ADRs are the audit trail, not the state.

---

## Step 6 — Superseding an existing ADR

When writing a new ADR that replaces an older one:

1. **In the new ADR**, add `**Supersedes:** ADR-NNN` to the header
   block. Reference the old decision in the Context section and
   explain what changed.
2. **In the old ADR**, add `**Superseded by:** ADR-NNN` below the
   existing header lines, and change `**Status:** Accepted` to
   `**Status:** Superseded`. Do not rewrite the old ADR's body — its
   original reasoning is the point.
3. If rules in `standards/*.yaml` were derived from the old ADR and
   need to change, make those edits in the same commit. Reference
   both the old and new ADR in the commit message.

---

## Step 7 — Partial supersession

Occasionally a later ADR replaces part of an earlier one but leaves
other parts intact. In that case:

- Do not flip the old ADR to `Superseded` — its still-active parts
  need to read as Accepted.
- In the new ADR, name which sub-sections of the old ADR it replaces.
- In the old ADR, add a note near the affected section pointing at
  the new ADR: `> Superseded in part by ADR-NNN — see that ADR's
  Decision section for the updated rule.`

This is rare. If an ADR is being partially superseded more than once,
consider rewriting it as a single replacement ADR for clarity.

---

## Step 8 — The relationship to rules

ADRs and rules are paired:

- ADR = why. Prose. Lives in `docs/decisions/`.
- Rule = what. YAML. Lives in `standards/*.yaml`.

When an ADR introduces a new convention, derive the enforceable rules
from it in the same PR (or the next PR if the rule implementation
needs design). Cross-reference the ADR from the rule's `description`
or `origin` field. ADR-002 → the `applies_to` type/trait taxonomy in
`index.yaml` and `evaluator.yaml` schema is the canonical example of
this pairing.

When a rule turns out to rest on an unwritten ADR — you find yourself
explaining the "why" repeatedly in Slack or PR reviews — write the
ADR retroactively. Backfilling is fine. An unwritten ADR is a
hot-potato problem; writing it down ends the re-litigation.

---

## Step 9 — Commit the change

Commit messages follow Conventional Commits. For ADRs, use `docs:`:

```
docs: add ADR-099 postgres as primary store
docs: supersede ADR-099 with ADR-100 (conformance checker v2)
```

semantic-release treats `docs:` as a patch-level bump. If the ADR is
being introduced alongside a new rule or a breaking standards change,
let the rule's commit drive the version bump (use `feat:` for the
rule and `docs:` for the ADR).

Do not edit `package.json` or `CHANGELOG.md` by hand (see META-001).

---

## Minimum working skeleton

```markdown
# ADR-004: Short decision title

**Date:** 2026-05-01
**Status:** Accepted
**Repo:** ecosystem-standards

---

## Context

What problem or force prompted this decision? Name the specific repos
or behaviors involved.

---

## Decision

What we decided, in one or two sentences, then detail.

---

## Consequences

**Positive:**
- Concrete outcome 1.
- Concrete outcome 2.

**Negative / trade-offs:**
- Concrete cost or constraint 1.

---

## Alternatives Considered

**Alternative A.** What it was, why rejected.
**Alternative B.** What it was, why rejected.
```

---

## See also

- `docs/decisions/ADR-001-federated-evaluation-config.md` — canonical
  reference for ADR format and "decision opens a path" style.
- `docs/decisions/ADR-002-type-trait-taxonomy-and-deferral.md` —
  canonical reference for a large ADR with sub-decisions, tables,
  implementation plan, and worked schema examples.
- `docs/decisions/ADR-003-conformance-checker-architecture.md` —
  canonical reference for a `Supersedes:` entry pointing at a
  non-ADR predecessor doc.
- `docs/decisions/README.md` — ADR index with status and one-line
  summaries.
- `standards/documentation.yaml` — DOC-005 defines the structural
  requirements this playbook operationalizes.
- `playbooks/new-standard.md` — for enforceable rule changes.
- `playbooks/ecosystem-changes.md` — for schema, registry, or enum
  changes.
