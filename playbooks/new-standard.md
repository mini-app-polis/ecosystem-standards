# Playbook: adding, editing, or retiring a standard

This is the canonical process for changing a rule in `standards/*.yaml`.
Any human or agent supplied with this repo should follow this playbook
and produce the same result.

For ADRs, see `playbooks/new-adr.md`. For edits to `ecosystem.yaml`,
`index.yaml` schema, repo types, traits, DoD checklists, or canonical
enums, see `playbooks/ecosystem-changes.md`.

---

## Step 1 — Is this a rule or an ADR?

Use the following test:

- **Rule** — if the constraint can be checked against a repo by
  inspection (file exists, field present, pattern matches, count above
  threshold), it belongs in `standards/*.yaml`.
- **ADR** — if you are recording *why* the ecosystem chose approach X
  over approach Y, and that rationale shapes many downstream decisions,
  it belongs in `docs/decisions/` as an ADR.

A topic can have both. ADRs capture the "why"; rules capture the "what."
If you are introducing a significant new convention, write the ADR first,
then derive rules from it.

If it is an ADR, stop here and switch to `playbooks/new-adr.md`.

---

## Step 2 — Is this one rule or multiple?

Before choosing a file, ask: does this change encode a single atomic
requirement, or is it a bundle of related requirements?

Split into multiple rules if any of the following apply:

1. The parts could be checked independently (different checks, different
   remediation).
2. The parts have different severities in practice (one is blocking,
   another is advisory).
3. The parts apply to different repo types.
4. The parts might be remediated by different people or at different
   times.

Keep as one rule if all parts must be satisfied together to mean
anything, and splitting would force every reader to cross-reference
sibling rules just to understand intent.

Worked example: "CI must run tests and measure coverage and deploy to
Railway" should be three rules (TEST-006, CD-008, CD-010), not one —
each is independently checkable and independently violated.

---

## Step 3 — Which file does the rule go in?

The rule prefix determines the file, and the prefix-to-file mapping
is authoritative in `index.yaml` `files:`. Putting a rule in the
wrong file is a META-006 violation — its prefix must match the file's
declared `rule_prefix`.

| Prefix        | File                            | Scope                                             |
|---------------|---------------------------------|---------------------------------------------------|
| `PRIN`        | `standards/principles.yaml`     | Immutable core philosophy                         |
| `PY`, `CFG`   | `standards/python.yaml`         | Python tooling, structure, configuration          |
| `TEST`        | `standards/testing.yaml`        | Test structure, critical path, FastAPI testing    |
| `DOC`         | `standards/documentation.yaml`  | README, docstrings, OpenAPI, ADR presence         |
| `API`, `AUTH` | `standards/api.yaml`            | Service structure, routing, authentication        |
| `PIPE`        | `standards/pipeline.yaml`       | Prefect patterns, idempotency, data safety        |
| `FE`          | `standards/frontend.yaml`       | Astro sites, React apps                           |
| `CD`, `VER`   | `standards/delivery.yaml`       | CI/CD, observability, versioning                  |
| `META`        | `standards/meta.yaml`           | Rules governing the standards repo itself         |
| `EVAL`        | `standards/evaluation.yaml`     | How AI evaluation is performed                    |
| `MONO`        | `standards/monorepo.yaml`       | pnpm workspace rules                              |
| `XSTACK`      | `standards/cross-stack.yaml`    | Python/TypeScript parity rules                    |

### Cross-cutting rules

When a rule touches more than one domain (e.g. auth spans API,
delivery, and security), first reconfirm Step 2 — make sure you are not
looking at two rules welded together. If it really is one atomic
requirement, pick the file whose prefix matches the **primary concern**.
Do not duplicate the rule across files. Use prose cross-references in
the `description:` to point readers at related rules.

The primary-concern test: "If this rule fails, whose dashboard does the
finding land on first?" That is the primary concern.

---

## Step 4 — Pick the next rule ID

Rule IDs are **append-only**: three digits, sequential within their
prefix, and retired numbers are never reused (META-007). The next
ID is `max(ever-seen ID for this prefix) + 1` — computed from git
history, not from the file's current contents. A rule deleted in a
past commit still occupies its number forever.

To find the next ID correctly:

```bash
# include retired IDs by walking git history, not just the current file
git log --all -p -- standards/<domain>.yaml \
  | grep -hE "^\+\s*- id:\s+<PREFIX>-[0-9]{3}" \
  | sed -E 's/.*id:\s*(<PREFIX>-[0-9]{3}).*/\1/' \
  | sort -u \
  | tail -1
```

Add one to the three-digit suffix. If the command returns nothing,
the prefix has never been used — start at `001`.

Do **not** use the simpler `grep ... standards/<file>.yaml | sort |
tail -1` form. It only sees currently-present rules and will happily
hand you a retired number to reuse, which silently changes what old
cross-references mean.

For gap-status rules, append `-GAP-NNN` as a secondary series (e.g.
`TEST-GAP-001`) so gap rules don't occupy the primary number space.
The same append-only policy applies independently to the `-GAP-`
series.

---

## Step 5 — Fill in the required fields

Every rule has this shape. Fields marked **required** must be present;
**optional** may be omitted; **forbidden** must not appear (see META-002).

```yaml
- id: DOMAIN-NNN                 # required
  title: Short description       # required — one line, imperative voice
  status: requirement            # required — see Step 6
  dimension: ...                 # required — see Step 6
  severity: ERROR                # required — ERROR | WARN | INFO
  applies_to: [pipeline-cog]     # required — list; see Step 6
  description: >                 # required — full prose explanation
    ...
  checkable: true                # required — true or false
  check_notes: >                 # required if checkable: true; absent otherwise
    DETERMINISTIC CHECK.         # required first line — see Step 7
    ...
  origin: >                      # optional — short note on the issue that drove this rule
    ...
  supersedes: "..."              # optional — only on a rule that replaces a retired one
```

**Forbidden fields** (see META-002):

- `added:` — version/date metadata on rules is banned; git log is the record.
- Top-level `updated:` / `maintainer:` on any file in this repo.
- `# Version:` header comments.

---

## Step 6 — Choose `status`, `dimension`, `severity`, `applies_to`

### status

Values are defined in `index.yaml` `statuses:`. Pick by intent:

- `requirement` — must-comply. Evaluator flags violations as blocking.
- `convention` — should-comply. Deviation requires an inline comment in
  the offending repo.
- `advisory` — guidance only. Evaluator reports as informational.
- `idea` — under consideration. Not yet enforced. Used while you're
  validating the rule against at least one real incident.
- `gap` — known deficiency tracked for remediation. The rule *would*
  pass if the codebase were in the desired state; it currently doesn't.

An `idea` rule should graduate to `requirement` (or `convention`) once a
real issue validates it. A rule sitting at `idea` for more than a
release cycle is a signal to either delete it or promote it.

### dimension

Pick exactly one. Canonical values are in `index.yaml` `dimensions:`.
Decision guide:

- Does the rule check repo layout, framework choice, naming, error
  handling? → `structural_conformance`
- Does it check that a pipeline run looked the same as previous runs?
  → `pipeline_consistency`
- Does it check idempotency, concurrency, retry behavior? →
  `pipeline_reliability`
- Does it check test presence or shape? → `testing_coverage`
- Does it check README, docstrings, ADRs, `.env.example`? →
  `documentation_coverage`
- Does it check Sentry, logging, semantic-release, CI steps? →
  `cd_readiness`
- Does it check naming parity or response-shape parity across repos? →
  `cross_repo_coherence`
- Does it check evaluation version currency or standards drift? →
  `standards_currency`
- Does it check pnpm workspace behavior (dedup, root CI)? →
  `monorepo_coherence`

### severity

Rule-level severity is `ERROR`, `WARN`, or `INFO`. `CRITICAL` and
`SUCCESS` are emission-only outcome severities and must not appear on
rule definitions (see `index.yaml` `severities:`).

- `ERROR` — violation blocks deploy or indicates a principle violated.
  Must be remediated.
- `WARN` — current-state pattern in new code, or a target state not
  being progressed toward. Remediation recommended.
- `INFO` — observation worth recording. No action required.

### applies_to

Pick from `index.yaml` `schema.repo_types:`. Use `[all]` only when the
rule genuinely applies to every repo type.

Prefer the narrowest correct list. `[pipeline-cog, api-service]` is
better than `[all]` if those two types are the actual scope.

`evaluator-service` is for rules that describe evaluator-cog's own
output quality (e.g. EVAL-003, MONO-003). Do not use it for rules that
describe repo behavior generally.

`standards-repo` is for rules that apply to this repo itself. These go
in `meta.yaml` by convention.

---

## Step 7 — Write `check_notes`

Only required when `checkable: true`. The first non-blank line of
`check_notes` **must** start with `DETERMINISTIC CHECK.` or `LLM CHECK.`
(see META-005).

Use `DETERMINISTIC CHECK.` when the check can be expressed as:

- File presence or absence.
- A regex match against source text.
- AST scan (function signatures, class bodies, imports).
- YAML / TOML / JSON parse and field inspection.
- A count comparison, version comparison, or set difference.

Use `LLM CHECK.` when the check requires:

- Judgment about prose quality ("is this description specific enough?").
- Understanding intent across multiple files or repos.
- Assessing whether a section "covers" a topic.
- Reading code comments for semantic meaning.

If a check has both kinds of parts, prefix with `LLM CHECK.` and tag
each numbered step `[deterministic]` or `[LLM]` in the body. See
META-004 for an example.

The check_notes should be specific enough that a new evaluator
implementation could be written against them without asking questions.
Vague notes like "look for anti-patterns" are disallowed — they make
findings unactionable (see EVAL-003).

---

## Step 8 — Retiring a rule

When a rule no longer applies, **delete it**. Git history is the record.

- Do not leave the rule behind as `status: retired` or similar. The
  catalog should reflect the current required state, not its history.
- **The retired ID number is never reused** (META-007). A later rule
  that seems to address the same topic gets a new number via Step 4.
  Cross-references in findings, ADRs, and external repos stay
  unambiguous across time only if IDs are append-only.
- If a new rule replaces the retired one, add a `supersedes:` field on
  the **new** rule describing what it replaced. This is forward-pointing
  metadata on the active rule, not a retained retired rule.
- If the rule is obsolete with no replacement, delete it and explain why
  in the commit message.

`status: gap` is **not** retirement. A gap rule tracks a known unmet
requirement that is still in force — the codebase doesn't meet it yet,
and we know it. Keep gap rules until the gap is closed, then retire
(delete) them.

---

## Step 9 — Editing an existing rule

Small edits in place are fine:

- Tightening or clarifying `description` prose.
- Adding or refining `check_notes` steps.
- Adding `origin:` after the fact if the rule predates the convention.
- Narrowing `applies_to` when we realize a repo type doesn't belong.

Larger edits call for retire-and-replace:

- Changing `severity` from WARN to ERROR (or vice versa).
- Changing `dimension`.
- Changing the fundamental requirement (the rule says something
  materially different).

Retire-and-replace means: delete the old rule, add a new rule with a
new ID, and put a `supersedes:` field on the new one. This preserves
the audit trail for downstream consumers whose findings reference the
old ID.

---

## Step 10 — The `origin` field

`origin:` is optional but strongly recommended for `requirement` and
`convention` rules. It records the real issue that drove the rule —
a single sentence or short paragraph.

Good origin examples:

```yaml
origin: "common-python-utils/__init__.py had broken install URL and no
         explanation of the name split. New consumers had to discover
         the import namespace by inspecting src/."
```

```yaml
origin: "api-kaianolevine-com has no mypy CI step. common-python-utils
         does. Standard aligns them."
```

Origins should name the repo and the concrete symptom. They should not
be abstract ("we want better docs"). If you can't write a concrete
origin, the rule may be premature — use `status: idea` until a real
issue validates it.

---

## Step 11 — Commit the change

Commit messages follow Conventional Commits — semantic-release reads
them to pick the next version bump and write the changelog.

| Prefix       | Version bump | Use when                                           |
|--------------|--------------|----------------------------------------------------|
| `feat:`      | minor        | Adding a new rule or a new canonical concept       |
| `fix:`       | patch        | Fixing a mistake in a rule (typo, wrong threshold) |
| `refactor:`  | patch        | Restructuring without changing rule semantics      |
| `docs:`      | patch        | README, ADRs, playbooks                            |
| `chore:`     | none         | Release commits, dependency bumps                  |

Do not edit `package.json` or `CHANGELOG.md` by hand — semantic-release
owns both (see META-001).

---

## Minimum working examples

### A new requirement

```yaml
- id: PY-NNN
  title: All services run under uvloop in production
  status: requirement
  dimension: structural_conformance
  severity: WARN
  applies_to: [pipeline-cog, api-service]
  description: >
    Services use uvloop as the asyncio event loop in production for
    consistent performance characteristics across the ecosystem.
  checkable: true
  check_notes: >
    DETERMINISTIC CHECK.
    Scan src/**/*.py for `import uvloop` and an explicit
    `uvloop.install()` or `asyncio.set_event_loop_policy` call. Flag
    any service missing both.
  origin: "deejay-cog and watcher-cog diverged on event loop policy,
           producing unrelated latency profiles on Railway."
```

### A gap rule

```yaml
- id: TEST-GAP-NNN
  title: "GAP: Integration tests absent from most cogs"
  status: gap
  dimension: testing_coverage
  severity: INFO
  applies_to: [pipeline-cog]
  description: >
    Most existing cogs lack integration tests for their primary external
    dependency. Per-repo remediation sequencing lives in BACKLOG.md.
  checkable: true
  check_notes: >
    DETERMINISTIC CHECK.
    Scan tests/ for any test file matching test_integration_*.py or
    a test class named Test*Integration. Flag if absent.
```

### A convention

```yaml
- id: CD-NNN
  title: Deploy logs tagged with release version
  status: convention
  dimension: cd_readiness
  severity: INFO
  applies_to: [pipeline-cog, api-service]
  description: >
    Deploy logs include the release version as a structured field so
    findings can be attributed to a specific deploy. Deviation requires
    a comment in the offending CI config explaining why the tag is
    omitted.
  checkable: true
  check_notes: >
    DETERMINISTIC CHECK.
    Scan .github/workflows/*.yml for a step that exports the release
    version into the runtime environment of the deploy command. Flag if
    no such step exists.
```

---

## See also

- `standards/meta.yaml` — the self-referential rules this playbook
  enforces (META-001 through META-005).
- `index.yaml` — canonical values for dimensions, severities, statuses,
  repo types, and traits.
- `playbooks/new-adr.md` — when to write an ADR instead of a rule.
- `playbooks/ecosystem-changes.md` — for edits outside `standards/`.
