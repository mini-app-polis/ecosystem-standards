# Backlog

Open items worth revisiting. These are not standards yet — they are things
that need to be built, decided, or documented when the time is right.

---

## pipeline-eval-deprecation — retire evaluator-cog's pipeline_eval path

**Mostly done.** `evaluator_cog/flows/pipeline_eval.py` has been deleted;
cogs report their own runs through `mini_app_polis.pipeline_status`.
What remains:

  - [ ] Drop `evaluator_cog.engine.llm._build_prompt_csv` /
        `_build_prompt_collection`, which nothing in `src/` calls any
        more, and the stale `evaluate_pipeline_run` / `_flow_name_to_repo`
        section comments left in `tests/unit/test_llm.py`.

---

## Nobody notices a Railway service that exhausted its restart budget

Deferred from ADR-007's recovery contract, recorded here rather than
solved there.

The cogs no longer have this problem: a Lambda pipeline cog's failed job
is redelivered and dead-lettered behind an alarm (PIPE-017, CD-010), a
trigger cog's missed tick is caught by its Healthchecks ping (CD-007),
and the Railway one-shot cogs declare their own liveness signal in their
CD-010 exemption (ADR-013). What is left is an API service on Railway:
CD-017 (`ON_FAILURE`, max retries 10) restarts it, and once that budget
is spent it stays down until a human redeploys it, and **nothing in the
ecosystem observes that**.

The gap is monitoring, not restart policy — deliberately so. Unbounded
restarts would erase the distinction between "the world is broken" and
"we shipped a broken build", and the second is the case that needs to
stop churning. More restarts is the wrong fix.

  - [ ] **Railway deployment-status polling.** Query the Railway API
        for services in a crashed/stopped state. Observes the condition
        directly rather than inferring it from absence, but adds a
        Railway API dependency and a place to run the poll.
  - [ ] **External uptime check** against each API's `/health`
        (API-010). An API binds a port, so a pull check works.

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

## Pipeline concurrency (PIPE-018)

PIPE-009's Prefect concurrency slot is retired (ADR-009); PIPE-018 asks for
the ceiling in each cog's module block in mini-app-polis/infra (ADR-010).

- [x] **deejay-cog** — `reserved_concurrency = 1`: the quota increase was
  approved, and sweeps run one at a time.
- [x] **evaluator-cog** — `max_concurrency = 20`.
- [x] **transcription-cog** — `reserved_concurrency = 1`.
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
  managed secrets, Clerk keys, Anthropic keys, and
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
  - Python: `uv lock --check` passes in CI. (PY-016 was taken by the
    external-interface error-class rule; use the next free PY id.)
  - XSTACK-006: `pnpm install --frozen-lockfile` passes in CI.
  Both are deterministic CI-workflow scans.

  **Scope warning — this does not cover stale `rev = "main"` git
  deps.** `uv lock --check` verifies the lock agrees with
  `pyproject.toml`; it says nothing about whether a git dependency
  pinned at `rev = "main"` still resolves to the current `main`. Those
  are different failures. On 2026-08-19 deejay-cog deployed with a
  `uv.lock` that was internally consistent and had been for months,
  but pinned `common-python-utils` at a SHA from before
  `serve_resilience` existed; `main.py` died at import on Railway and
  the container crash-looped. `uv lock --check` would have passed.
  If PY-016 lands, do not treat it as covering that case — the
  remedy there is per-repo (relock as part of the change that needs
  the new code, plus an import smoke test on the entry point so CI
  catches it), not a catalog rule.

- [ ] **HTTP timeouts required (a new TEST rule).** `PIPE-007`
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
  every Python repo in scope to declare `[tool.mypy]` and run mypy
  in CI, but not what strictness level it should use. The fleet
  runs `strict = false` with `ignore_missing_imports = true`.
  Stronger version: `strict = true` required for new libraries and
  api-services.

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
- Honor per-repo `downgrades:` on `schema.evaluator_yaml` — the
  per-repo counterpart to trait-level downgrades. Added in v4.1.0;
  used for repo-specific checker limitations not covered by a
  shared trait. Currently unused by any repo, so the gap is latent
  rather than actively broken.
- Honor the optional `modifies:` field on rules (ADR-005). No rule
  currently declares it.
- Implement the eight-step dispatch precedence defined in
  `index.yaml` `schema.dispatch.precedence` (ADR-005 introduced
  seven; v4.1.0 inserted `repo_downgrade` as step 6 between
  `trait_downgrade` and `rule_modifier`).
- Implement runtime data-quality checks for rules that omit
  `applies_to` — currently EVAL-003 and EVAL-007
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
