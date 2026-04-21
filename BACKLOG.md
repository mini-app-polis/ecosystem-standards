# Backlog

Open items worth revisiting. These are not standards yet — they are things
that need to be built, decided, or documented when the time is right.

---

## playbooks/ — bootstrap guides for new repos

The python-project-template is retired. Its replacement is a set of
playbooks in playbooks/ — one per artifact type. Each playbook
documents the exact steps to go from empty repo to first green CI.

Artifact types needing playbooks:
  - ✅ new-cog.md (Python worker service) — complete
  - new-fastapi-service.md
  - new-astro-site.md
  - new-react-app.md
  - new-hono-service.md

Priority: new-cog.md first — it is referenced by the new_cog DoD
checklist and watcher-cog was the first cog built without it.

---

## evaluators/ — agent scripts not yet built

The `evaluators/` folder exists as a placeholder. Agent scripts implementing
the check_notes from each rule live here.

First candidate: a DoD evaluator that reads `definitions-of-done.yaml`,
determines the artifact type being evaluated, and runs the appropriate
checklist post-PR or post-deploy.

Priority: build once the capture endpoint is live and the feedback loop
is established.

---

## Capture endpoint — backlog items not yet auto-routed here

The planned capture system (POST /capture on api-kaianolevine-com → GitHub Issue
in this repo) is not yet built. Until it is, new issues must be manually
added to this file or directly as GitHub Issues.

Once built, mid-flow captures will automatically land as labeled Issues
in this repo for processing into standards when there is headspace.

Reference: capture system design is in a separate conversation.

---

## Pipeline UI — shared finding card component

The finding card is rendered independently in two places:
`src/components/RecentFindings.astro` (homepage widget) and
`src/pages/pipeline/index.astro` (full findings browser). These have
already drifted — the repo badge fix had to be applied twice.

Remediation: extract card rendering into a shared JS module or make
`RecentFindings.astro` accept configuration (limit, filters) so the
pipeline page can reuse it.

Priority: low — functional but will drift further as UI evolves.

---

## PIPE-009 Remediation

PIPE-009 requires pipeline cogs to acquire a named Prefect concurrency slot
before scanning shared resources. notes-ingest-cog is compliant as of 2026-04.
The following cogs need remediation:

- [ ] **deejay-cog** — add `with concurrency("deejay-cog", occupy=1)` wrapping
  the flow body in `flow.py`. Create `deejay-cog` concurrency limit in Prefect
  Cloud (limit: 1).
- [ ] **evaluator-cog** — add `with concurrency("evaluator-cog", occupy=1)`
  wrapping the flow body in `flow.py`. Create `evaluator-cog` concurrency limit
  in Prefect Cloud (limit: 1).

---

## Candidate standards — additions considered during 2026-04 audit

The 2026-04 standards audit (which produced the DETERMINISTIC/LLM
check split, the META prefix, and zero remaining `requirement` +
`checkable: false` rules) surfaced several rule-addition candidates.
ADR-004 later removed the `evaluator-service` pseudo-type introduced
during that audit, and ADR-005 formalized the full rule-field schema
and trait structure. The additions below remain candidates; they are
not urgent and should land only when evaluator-cog is ready to honor
them.

Grouped by impact-to-effort ratio. Each group is independently
actionable.

### Tier 1 — highest-impact additions

- [ ] **Secret scanning (SEC-001, SEC-002).** No rule currently
  requires secret scanning anywhere in the ecosystem. Given Doppler-
  managed secrets, Clerk keys, Prefect API keys, Anthropic keys, and
  GitHub tokens all present across repos, this is the biggest
  material-risk gap in the catalog. Proposed:
  - SEC-001: pre-commit hook for secret scanning (gitleaks,
    detect-secrets, or trufflehog). Check: `.pre-commit-config.yaml`
    contains one of those hooks.
  - SEC-002: CI secret scanning on PR diffs (e.g. gitleaks-action
    in GitHub Actions). Check: workflow file present and running
    on pull_request events.

- [ ] **Lockfile integrity (PY-016, XSTACK-006).** No rule currently
  requires lockfile-in-sync. A stale `uv.lock` or `pnpm-lock.yaml`
  is a repeated source of "works on my machine" failures. Proposed:
  - PY-016: `uv lock --check` passes in CI.
  - XSTACK-006: `pnpm install --frozen-lockfile` passes in CI.
  Both are deterministic CI-workflow scans.

- [ ] **HTTP timeouts required (PIPE-016 or TEST-014).** `PIPE-007`
  requires retry on external API calls but not timeouts. An `httpx`
  call without a timeout can hang indefinitely, blocking the flow
  and consuming worker slots. Proposed single rule: every
  `httpx.get/post/put/delete` call has `timeout=` set, or the module
  uses a client configured with a default timeout.

### Tier 2 — solid value, lower urgency

- [ ] **Dependency vulnerability scanning.** `pip-audit` on Python,
  `pnpm audit` on TypeScript, fail on HIGH/CRITICAL in CI. One rule
  per ecosystem (or one cross-stack rule with two branches).

- [ ] **Unused dependency detection.** `deptry` for Python, `knip`
  for TypeScript. Less urgent than lockfile integrity — unused deps
  are slow accumulation, not active breakage.

- [ ] **.env.example value hygiene (CFG-003).** `DOC-004` requires
  the file to exist and `CFG-002` requires keys to match Settings,
  but nothing covers the values inside. Proposed: secrets must use
  placeholder patterns (`CHANGE_ME`, `<your-*>`, empty string). Non-
  secret keys should have plausible example values. This is about
  developer onboarding quality more than security.

- [ ] **Pre-commit hook enforcement in CI.** `PY-008` requires
  pre-commit to be configured locally, but developers can bypass
  with `--no-verify` and push broken code. CI should run
  `pre-commit run --all-files` as a gate. This turns pre-commit
  from a suggestion into a contract.

### Tier 3 — worth considering, opinionated

- [ ] **Database migration reversibility.** Every Alembic migration
  has both `upgrade()` and a non-trivial `downgrade()`. Low-urgency
  until it's suddenly high-urgency (a bad migration that can't be
  rolled back).

- [ ] **Migration tests.** Migrations that alter schema should have
  a test applying the migration to a fixture DB and asserting the
  end state.

- [ ] **Rate limiting on public endpoints.** `api-kaianolevine-com`
  has public POST endpoints (contact form, capture) with no declared
  rate-limiting standard. Proposed: advisory-level rule naming
  `slowapi` (FastAPI) or equivalent as the ecosystem standard for
  rate limiting, with a check that all public POST endpoints have
  rate-limiting middleware applied.

- [ ] **Type-checking strictness baseline.** `TEST-012` requires
  mypy in CI if `[tool.mypy]` is declared, but doesn't specify
  when that section should be declared or what strictness level
  it should use. Stronger version: `strict = true` required for
  new libraries and api-services.

### Tier 4 — flaky/operational, only matters at scale

- [ ] **Flaky test quarantine rule.** A test that fails
  intermittently is marked `@pytest.mark.flaky` with a ticket
  reference, or is deleted. No silent intermittent failures.

- [ ] **Test isolation rule.** No `os.environ` mutation in tests
  without a cleanup fixture; no module-level state in test files.

### Meta-invariant candidates flagged during audit

These would enforce the structural patterns established by the
2026-04 audit, so that the invariants stay invariant as the catalog
grows:

- [ ] **META-008: requirements must be verifiable.** Every rule
  with `status: requirement` has `checkable: true`. No conscious
  carve-outs after the audit cleanup. (This would prevent the
  pattern we just finished cleaning up from re-emerging.)
  Note: the META-005 check-notes-prefix proposal and the META-006
  prefix-matches-file proposal both shipped under those IDs — this
  candidate would land under the next available META ID.

## Evaluator-cog follow-up

Cross-repo follow-up tracked in the evaluator-cog repo. Summary of
what that repo needs in order to fully honor the current standards
schema:

- Honor structured trait fields — `exempts:` and `downgrades:` on
  `schema.traits` (ADR-005).
- Honor the optional `modifies:` field on rules (ADR-005, MONO-001
  and MONO-002 are the current consumers).
- Implement the seven-step dispatch precedence defined in
  `index.yaml` `schema.dispatch.precedence` (ADR-005).
- Implement runtime data-quality checks for rules that omit
  `applies_to` — currently EVAL-003, MONO-003, and EVAL-007
  (ADR-004).
- Reject rules carrying `status: advisory` or `status: idea` —
  both statuses were removed in ADR-005.

These are not standards-repo work. Listed here only so a future
audit can cross-check that the catalog and evaluator stay in sync.

## Open structural questions surfaced by the audit

These are conversations, not tickets. Worth addressing before the
next major audit round.

- [ ] **Is `applies_to: [all]` ever the right scope?** A handful
  of rules use it. Going through each, several are really
  "applies to every deployable service" (which is not the same
  as "all") or "applies to every Python repo." Worth a pass to
  see if the catalog would be clearer with explicit type lists
  everywhere.

- [ ] **Should severity flow from dimension?** Currently rules
  set severity independently. But the relationship is usually
  predictable — `structural_conformance` rules are usually WARN,
  `pipeline_reliability` rules are usually ERROR. Possible
  convention: default severity per dimension, with explicit
  override when needed. Would reduce the "why is this a WARN
  vs an ERROR" conversations during rule authoring.
