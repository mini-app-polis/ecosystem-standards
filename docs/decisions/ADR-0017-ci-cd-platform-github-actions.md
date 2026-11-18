# ADR-0017: The Canonical Pipeline Runs on GitHub Actions, From .github

**Date:** 2026-11-17
**Status:** Accepted
**Repo:** ecosystem-standards

---

## Context

Every mini-app-polis repository runs its own copy of CI/CD. The inventory
of 2026-11-17 (`.github` `docs/workflow-inventory-2026-11-17.md`) found
that the copies share a skeleton (`security` and `test`, then `release`
and `evaluate` on `main`) and differ in ways nobody chose:

- `evaluate` runs alongside `release` in 18 of the 20 `ci.yml` files, so
  it cannot receive the release's version or commit. It sleeps a fixed
  time and evaluates the default branch, which is the failure that started
  this work (evaluations do not get the release's data).
- Railway services and Cloudflare Pages sites deploy through the
  platforms' branch integrations on every push, outside CI, ungated by
  tests or a release.
- Within one repository type the same stage is written inline in some
  repositories and as the shared reusable workflow in others, with
  differing triggers and inputs.
- No CI job has a timeout, no action is pinned by commit, and
  `cancel-in-progress` can cancel a release on `main` partway.

The program's goals, which decide the platform rather than familiarity:

1. **One pipeline every repository subscribes to.** A repository declares
   its profile and inputs; it does not copy stages.
2. **Controls every repository inherits and cannot skip**, such as the
   security scans.
3. **Explicit stages**, each type of test its own stage, with branched
   pre-release and post-release evaluation that receives the release's
   data in the same run.
4. **One commit's whole build is one flow with one view** of every stage,
   not chained workflow runs.
5. **Recovery inside the pipeline.** Platform outages and the pipeline's
   own failures are recovered by resuming the original run, never by work
   done outside it (no laptop release, no dashboard deploy).
6. **Enterprise-grade design and practice at a one-person scale**, at a
   cost that fits one person.

Platform reliability is not scored on its own: GitHub Actions and
GitLab.com both had frequent incidents in 2026, so recovery is designed
into the pipeline (goal 5) instead.

The organization is on GitHub Free today (infra's `github_repos.tf`).
All repositories but wcs-wiki are public.

---

## Decision

**The canonical pipeline is built on GitHub Actions as reusable workflows
in `mini-app-polis/.github`, versioned with semantic-release and a moving
major tag, and enforced with organization rulesets on the GitHub Team
plan. GitLab CI and Dagger are not adopted.**

### Scores against the goals

| Goal | GitHub Actions (reusable workflows + org rulesets) | GitLab CI (include/extends + pipeline execution policies) | Dagger on Actions |
|---|---|---|---|
| 1. One pipeline to subscribe to | Yes: a thin caller per repository runs the shared `ci.yml` at the major tag, with inputs for its profile. Already the shape of 20 repositories at `@v3` | Yes: `include:` a shared template, `extends:` for variations | Yes: one Dagger module called from a thin workflow, but Actions still holds triggers, secrets and checks |
| 2. Controls that cannot be skipped | Yes, on Team: organization rulesets can require workflows and status checks across all repositories (available on Team since June 2025). Ruleset workflows run on `pull_request`, `pull_request_target` and `merge_group` events, not on `GITHUB_TOKEN` events | Yes, but only on Ultimate: pipeline execution policies inject jobs a project cannot remove. On Premium, an `include` can be edited out by the project | Not on its own: enforcement still comes from the CI platform underneath |
| 3. Explicit stages, release data downstream | Yes: one workflow's jobs pass outputs through `needs` (the shared `release.yml` already exposes `tag`) | Yes: stages and `needs`, artifacts and dotenv reports between jobs | Yes, inside the module, as function return values |
| 4. One commit, one flow, one view | Yes, when every stage is a job of one `ci.yml` run calling reusable workflows: the run's graph shows each job. Today's separate `deployed.yml`, `contract.yml` and `site.yml` runs, and deploys outside Actions, are what break the view, and the pipeline moves them in | Yes, natively: one pipeline per commit with a stage graph | Partly: the Actions run shows one job; the stage detail is in Dagger's own trace (Dagger Cloud for a shared view) |
| 5. Recovery inside the pipeline | Yes: failed or skipped jobs of a run can be re-run in the same run (UI and REST), which is what the release reconciler drives | Yes: jobs can be retried in the same pipeline | Same as the platform underneath, plus Dagger's cache |
| 6. Practice at one-person cost | Team plan at $4 per user a month for one user | Premium $29 per user a month, and Ultimate (needed for goal 2) at about $99 per user a month or by quote | Engine free; Dagger Cloud Team $50 a month for its trace view |

### Migration cost

| Integration | GitHub Actions | GitLab CI | Dagger on Actions |
|---|---|---|---|
| Railway | Kept: deploys move into the pipeline through the Railway CLI or API, branch auto-deploy turned off through Railway's IaC | Railway's repository integration is with GitHub; from GitLab every deploy goes through the CLI | As GitHub Actions |
| Dependabot | Kept | Replaced (Renovate, or GitLab dependency scanning) | Kept |
| The agent workflows (`agent.yml`, the agent GitHub App) | Kept | Rewritten for GitLab, with a new bot identity | Kept, plus the module |
| The repository status dashboard (api-kaianolevine-com reads the GitHub API) | Kept | Rewritten against the GitLab API | Kept |
| Rulesets as code (infra's GitHub provider) | Kept, extended to organization rulesets | Rewritten with the GitLab provider (protected branches, policies) | Kept |
| Doppler secret sync to GitHub | Kept | Re-pointed at GitLab CI variables | Kept |
| The promote and signals GitHub Apps, GitHub Issues from Sentry and CI signals | Kept | Rewritten | Kept |
| Cloudflare Pages Git integration | Turned off in favour of pipeline deploys either way | Same | Same |

### Where the pipeline lives and how it is versioned

- **In `mini-app-polis/.github`**, the repository that already holds the
  fleet's reusable workflows, the shared actions and the fleet-wide jobs,
  and that 20 repositories already call at `@v3`. A dedicated repository
  would only move those callers and the org-level access settings for no
  gain.
- **Versioned with semantic-release tags plus a moving major tag.**
  Repositories call the pipeline at its major (`@v4` once the canonical
  pipeline ships). A breaking change ships only in a new major, with a
  deprecation window for the old one; rolling back means re-pointing the
  major tag. The canary repository moves first, then the fleet.

### Plan and tier each option needs

- **GitHub Actions:** GitHub Team for organization rulesets (required
  workflows and status checks across repositories, and rulesets on the
  private wcs-wiki). Free covers per-repository rulesets on public
  repositories only, which is what infra manages today.
- **GitLab CI:** Ultimate for pipeline execution policies; Premium does
  not enforce shared jobs.
- **Dagger:** no plan for the engine; Dagger Cloud Team for a shared trace
  view.

---

## Consequences

**Positive:**

- The program's later work (the stage contracts, the release reconciler,
  deploys moved into the pipeline, rulesets as code) builds on the
  reusable workflows, Apps and Terraform that exist today rather than
  re-creating them on another platform.
- The fix for evaluations missing release data is a `needs` edge in one
  shared workflow, which every repository inherits on its next major.
- Controls become unskippable once the organization moves to Team and
  infra declares the organization rulesets.

**Negative / trade-offs:**

- The organization moves from GitHub Free to GitHub Team ($4 a month for
  one user).
- Ruleset workflows do not run on events made with `GITHUB_TOKEN`, and
  run only on pull request and merge-queue events, so the organization
  ruleset holds only `main`, which every change reaches through the
  promotion pull request; `dev` keeps its direct pushes. The pipeline's
  own automation (promotion, release commits) uses the promote App's
  token, and the App is the `main` ruleset's one bypass for the release
  commit: GitHub does not accept GitHub Actions as a bypass actor.
- The one-view goal holds only while every stage stays a job of the one
  `ci.yml` run; any stage added as a separate workflow breaks it, so the
  conformance rules have to forbid that.
- GitHub's YAML and reusable-workflow limits (nesting depth, inputs as
  strings) remain; the shared workflows carry that complexity so callers
  do not.

---

## What would change this decision

- GitHub removes organization rulesets or required workflows from the
  Team plan, or prices them out of reach for one person.
- The pipeline cannot be shown as one run per commit on Actions after
  deploys and post-deploy checks move into `ci.yml` (MINI-1008, MINI-1009).
- GitLab makes pipeline execution policies, or an equivalent enforced
  shared pipeline, available below Ultimate.
- A move off GitHub for other reasons (repositories, Issues, Apps) makes
  GitLab's migration cost already paid.

---

## Alternatives Considered

### GitLab CI with includes and pipeline execution policies

The strongest fit for goal 4: one pipeline per commit is GitLab's native
model. Rejected because goal 2 needs pipeline execution policies, which
are Ultimate only, and because the migration replaces nearly every
integration the fleet has built on GitHub (the agent, the Apps, the
status dashboard, Dependabot, Issues from Sentry and CI signals, rulesets
in Terraform) for a capability Actions can reach once deploys move into
the pipeline.

### Dagger running on GitHub Actions

Writes the pipeline as code and runs it the same locally and in CI.
Rejected for now because it does not remove the CI platform underneath:
triggers, secrets, required checks and rulesets stay on Actions, and the
one-run view becomes one Actions job with the stages inside Dagger's own
trace. It adds an engine and a module language for a portability the
fleet does not need while it stays on GitHub. Revisit if a platform move
becomes likely, when portability would pay for itself.

### Staying with per-repository workflows on GitHub Free

The status quo. Rejected because it is the drift the inventory found, and
nothing enforces the shared controls.
