# Backlog

Open items worth revisiting. These are not standards yet — they are things
that need to be built, decided, or documented when the time is right.

---

## pipeline-eval-deprecation — retire evaluator-cog's pipeline_eval path

`evaluator_cog/flows/pipeline_eval.py` exists for two reasons that the
May 2026 self-report refactor made redundant:

  1. `evaluate_pipeline_run` — LLM-scores CSV / collection runs by
     calling Claude with a structured prompt. Cogs now self-report
     SUCCESS/WARN/ERROR with concrete counters via
     `mini_app_polis.pipeline_status.post_run_finding`. The LLM's
     output adds latency, cost, and an extra place the payload shape
     can drift; the cog itself is the authoritative source.
  2. `handle_prefect_flow_run_event` — Prefect Cloud webhook fallback
     for flow-run state changes the cog never reported on. With the
     failure hooks (`make_failure_hook` in
     `mini_app_polis.pipeline_status`) wired into every production
     flow's `on_failure` / `on_crashed`, this webhook is also
     redundant for any cog using the library.

Plan:

  - [x] Confirm every production flow (deejay-cog, transcription-cog)
        is wired through the library shim with a failure hook.
        (deejay-cog: done. transcription-cog: done. evaluator-cog:
        retains for conformance_check_flow only.)
  - [ ] Stand the Prefect Cloud webhook automation down (or repoint at
        a no-op endpoint) so `handle_prefect_flow_run_event` stops
        receiving traffic.
  - [ ] Delete `evaluate_pipeline_run`, `handle_prefect_flow_run_event`,
        `_FLOW_REPO_MAP`, `_flow_name_to_repo`, related helpers, and
        the corresponding test files (`test_webhook.py`,
        `test_llm.py::test_flow_name_to_repo_*`, related
        `_build_prompt_*` test scaffolding).
  - [ ] Drop unused `evaluator_cog.engine.llm._build_prompt_csv` /
        `_build_prompt_collection` if no other caller remains.
  - [ ] Remove evaluator-cog as a runtime dependency of any cog that
        no longer needs it (the conformance-checking flow stays;
        pipeline_eval comes out).

See the module-level TODO in
`evaluator-cog/src/evaluator_cog/flows/pipeline_eval.py` for the
inline plan.

**Coverage note before deleting the webhook path.** The argument above
is that failure hooks make `handle_prefect_flow_run_event` redundant.
That holds for *flow-run* state changes, which is all the webhook ever
covered. It does not extend to the pre-flow window: a cog that dies
during `prefect.serve()` deployment registration has no flow run, so
neither the hooks nor the webhook ever fired. That window is now
covered separately by `serve_with_retry`
(`mini_app_polis.serve_resilience`, CD-016, ADR-006), which emits a
`source="startup"` CRITICAL finding. Recording it here so the webhook
deletion isn't later blamed for a gap it never filled.

---

## Nobody notices a service that exhausted its restart budget

Deferred from ADR-007's recovery contract, recorded here rather than
solved there.

CD-016 (in-process retry ceiling) times CD-017 (`ON_FAILURE`, max
retries 10) gives roughly five hours of unattended coverage for a
service that cannot start. After that the service stays down until a
human redeploys it, and **nothing in the ecosystem observes that**.

The gap is monitoring, not restart policy — deliberately so. Unbounded
restarts would erase the distinction between "the world is broken" and
"we shipped a broken build", and the second is the case that needs to
stop churning (see deejay-cog's 2026-08-19 `ModuleNotFoundError`
crash-loop). More restarts is the wrong fix.

What is actually needed is something watching from *outside* the
failing service, which does not exist today. Sketch of the options:

  - [ ] **Silence detection in evaluator-cog's conformance flow.** It
        already runs daily against every repo. It could assert that
        each active cog has posted *some* finding within its expected
        window and raise one when a cog has gone quiet. Cheapest —
        reuses a scheduled component that already exists. Weak for
        deejay-cog specifically, which is exempt from CD-010 precisely
        because it has no expected cadence (ADR-003) — silence there
        is normal.
  - [ ] **Railway deployment-status polling.** Query the Railway API
        for services in a crashed/stopped state. Direct and
        unambiguous — it observes the actual condition rather than
        inferring it from absence — but adds a Railway API dependency
        and a place to run the poll.
  - [ ] **External uptime check.** Third-party pinger against a
        liveness surface. Cogs bind no port (they are not HTTP
        services), so this needs a heartbeat push rather than a pull,
        which is CD-010/Healthchecks.io — already exempted for
        on-demand cogs for the same cadence reason.

Note the recurring obstacle: every option that infers liveness from
*activity* breaks on cogs that are legitimately idle for weeks. The
Railway-status option is the only one that observes the condition
directly, which is probably the tell.

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
before scanning shared resources. transcription-cog (which absorbed the
former notes-ingest-cog as its `wcs-transcripts` mode in May 2026) is
compliant as of 2026-04. The following cogs need remediation:

- [ ] **deejay-cog** — add `with concurrency("deejay-cog", occupy=1)` wrapping
  the flow body. Create `deejay-cog` concurrency limit in Prefect Cloud
  (limit: 1). Verified still open as of 2026-08-19 (no `concurrency(` call
  anywhere in `src/`). Note there is no `flow.py` in this repo — the flow
  bodies live in `process_new_files.py` and `ingest_live_history.py`, and
  the router in `main.py`; wrap the two dispatched flows, not the router,
  or the slot is held for the lifetime of the dispatch.
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
- Honor per-repo `downgrades:` on `schema.evaluator_yaml` — the
  per-repo counterpart to trait-level downgrades. Added in v4.1.0;
  used for repo-specific checker limitations not covered by a
  shared trait. Currently unused by any repo, so the gap is latent
  rather than actively broken.
- Honor the optional `modifies:` field on rules (ADR-005, MONO-001
  and MONO-002 are the current consumers).
- Implement the eight-step dispatch precedence defined in
  `index.yaml` `schema.dispatch.precedence` (ADR-005 introduced
  seven; v4.1.0 inserted `repo_downgrade` as step 6 between
  `trait_downgrade` and `rule_modifier`).
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
