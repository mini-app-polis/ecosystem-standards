---
# Playbook: new cog

A cog is a Python service. This playbook covers both subtypes:
- **Pipeline cog** — a Lambda function behind its own SQS queue that
  processes one job per message (e.g. deejay-cog, evaluator-cog). Nothing
  runs between jobs. See ADR-0009.
- **Trigger cog** — a Lambda function on an EventBridge schedule that
  detects events and asks api-kaianolevine-com to run a job (e.g.
  watcher-cog). Nothing runs between ticks. The API is the only producer to
  any queue. See ADR-0011.

---

## Prerequisites

- Python 3.11+
- uv installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Access to the mini-app-polis GitHub org
- Doppler access to the mini-app-polis-ecosystem project, and the Doppler CLI:
  `brew install gnupg dopplerhq/cli/doppler`, then `doppler login` (once per
  machine)
- Sentry account (free tier)
- Write access to mini-app-polis/infra
- Trigger cogs: Healthchecks.io

---

## Step 1 — Create the repo

1. Create a new empty repo in the **mini-app-polis** GitHub org
2. Name it `{purpose}-cog` (e.g. `notes-cog`, `spotify-cog`)
3. Add a README and .gitignore (Python template)
4. Clone locally
5. Settings → Actions → General: enable Actions. A new repository in the
   org starts with Actions disabled, and nothing in the repository says
   so: pushes register the workflows, but none of them ever runs. Match an
   existing cog's settings there: allow all actions and reusable
   workflows, read and write workflow permissions, and allow GitHub
   Actions to create and approve pull requests (promote and automerge
   need it).
6. Settings → General: turn off the wiki, as the other repositories have.

---

## Step 2 — Bootstrap the project structure

Run in the repo root:
```bash
uv init --lib
uv add miniapppolis-common-utils httpx
uv add --dev pre-commit pytest pytest-asyncio pytest-cov ruff
```

Then restructure to src layout:
```bash
mkdir -p src/{package_name} tests
mv {package_name}/ src/
touch src/{package_name}/__init__.py tests/__init__.py
echo "3.11" > .python-version
```

Replace `{package_name}` with the snake_case version of the repo name
(e.g. `notes_cog`).

---

## Step 3 — pyproject.toml

Replace the generated pyproject.toml with this structure:
```toml
[project]
name = "{repo-name}"
dynamic = ["version"]
description = "{one line description}"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "miniapppolis-common-utils>=5.24,<6",
    "httpx",
]

[dependency-groups]
dev = [
    "pre-commit",
    "pytest",
    "pytest-asyncio",
    "pytest-cov",
    "ruff",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "ASYNC", "ANN"]

[tool.pytest.ini_options]
pythonpath = ["src"]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.hatch.version]
path = "src/{package_name}/_version.py"

[tool.hatch.build.targets.wheel]
packages = ["src/{package_name}"]
```

The version lives in `src/{package_name}/_version.py` (`__version__ = "0.0.0"`),
which the release writes (PY-017).

---

## Step 4 — Standard files

Create `doppler.yaml`, which pins the repo to its own Doppler project so
`doppler setup` asks nothing and `doppler run` injects `dev` (CD-011). The
project is the one infra's `doppler/` root makes for the cog (step 6), named
for the repository:
```yaml
# Pins this repo to its own Doppler project for local development: the
# names its code reads, as production has them, and no others.
# `doppler setup` reads it; `doppler run -- …` then injects the dev secrets.
# Local runs use dev only — prd is synced to the platforms, never run.
setup:
  - project: {purpose}-cog
    config: dev
```

Create `.env.example` — the names the cog reads, never values. Uncommented
names are required in Doppler's `dev` config; commented ones are optional
(the code has a default). `uv run check-doppler-keys` lists any required
name `dev` is missing:
```bash
# {cog} — the names this cog reads. Names only: the values live in Doppler
# ({purpose}-cog / dev locally, prd deployed). Run under
# `doppler run -- …`; do not copy this to .env — nothing reads it.

# {description of var}
{VAR_NAME}=
# SENTRY_DSN_COGS=
# LOGGING_LEVEL=INFO
# Healthchecks.io ping URL (trigger cogs only, where it is required: CD-007)
HEALTHCHECKS_URL_{COG}=
```

Nothing reads a `.env` file: no `python-dotenv`, no `load_dotenv()`, and no
`env_file` on a pydantic-settings config. Secrets come from the process
environment — `doppler run` locally, SSM or the Railway sync deployed.

Create `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.8
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  # SEC-001
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.28.0
    hooks:
      - id: gitleaks
```

Create `.releaserc.json`:
```json
{
  "branches": ["main"],
  "plugins": [
    "@semantic-release/commit-analyzer",
    "@semantic-release/release-notes-generator",
    ["@semantic-release/changelog", { "changelogFile": "CHANGELOG.md" }],
    ["@semantic-release/exec", {
      "prepareCmd": "printf '__version__ = \"%s\"\\n' \"${nextRelease.version}\" > src/{package_name}/_version.py"
    }],
    ["@semantic-release/git", {
      "assets": ["CHANGELOG.md", "src/{package_name}/_version.py"],
      "message": "chore(release): ${nextRelease.version} [skip ci]"
    }],
    "@semantic-release/github"
  ]
}
```

Create `CHANGELOG.md` (empty, semantic-release will populate):

---

## Step 5 — GitHub Actions

Copy `.github/workflows/ci.yml` from deejay-cog and change only the
`deploy` job's inputs. The stages are the same in every cog, in this order:

- **security** — `mini-app-polis/.github/.github/workflows/security.yml@v3`
- **test** — `mini-app-polis/.github/.github/workflows/python-test.yml@v3`
  (lock check, ruff, format, pytest with coverage). Pass `typecheck` when
  the cog declares `[tool.mypy]`. No `terraform-dir`: a cog has no
  Terraform (ADR-0010).
- **release** — semantic-release, recording the tag it cut as a job output
- **deploy** — `lambda-deploy.yml@v3`, `needs: release`, run
  only when a tag was cut. A trigger cog passes `trigger: schedule`. It is a job rather than an `on: release`
  workflow because a release published with `GITHUB_TOKEN` starts no
  workflows. `handler`, `architecture` and `python-version` must match
  the cog's module block in mini-app-polis/infra `cogs.tf`.
- **evaluate** — `evaluate.yml@v3`, `needs: deploy`, so a release is
  graded only once it is running

The release job, for reference:
```yaml
  release:
    name: Release
    needs: [test, security]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    permissions:
      contents: write
      issues: write
      pull-requests: write
    steps:
      - uses: actions/checkout@v7
        with:
          fetch-depth: 0
          token: ${{ secrets.GITHUB_TOKEN }}
      - uses: actions/setup-node@v6
        with:
          node-version: "22"
      - name: Install semantic-release plugins
        run: |
          npm install --no-save \
            semantic-release \
            @semantic-release/changelog \
            @semantic-release/exec \
            @semantic-release/git \
            @semantic-release/github \
            @semantic-release/commit-analyzer \
            @semantic-release/release-notes-generator
      - name: Release
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: npx semantic-release
      - name: Record the release tag
        id: released
        run: echo "tag=$(git tag --points-at HEAD --list 'v*' | head -n1)" >> "$GITHUB_OUTPUT"
```

---

## Step 6 — Implement the cog

Use the watcher-cog repo as the reference implementation for trigger
cogs. Use deejay-cog as the reference implementation for pipeline cogs.

All cogs must include:
- Logging through `mini_app_polis.logger` — no `basicConfig` (the Lambda
  runtime has already configured the root logger, so it would do nothing)
- Sentry init before any application logic
- External API calls retried at the call site (PIPE-007): a
  common-python-utils client, the library's own retry, or tenacity. Queue
  redelivery is the backstop, not the retry.

Pipeline cogs:
- `worker.py` — `lambda_handler(event, context)` hands the records to
  `mini_app_polis.lambda_worker.process_records`, which runs each one and
  returns `{"batchItemFailures": [...]}` naming the records that raised.
  Each record's body is read with `parse_message` against the cog's
  message kind from `mini_app_polis.api.contract`; a malformed message
  raises `UnprocessableMessage` and goes to the dead-letter queue, and is
  reported only on its first receive — gate on the record's
  `ApproximateReceiveCount`, or five redeliveries become five identical
  findings for one message (PIPE-021). The flows report their own
  failures; the consumer reports only what never reached one.
  Copy deejay-cog's `worker.py`.
- Each record runs inside `mini_app_polis.lambda_worker.deadline(context)`,
  which stops the run a margin before the function timeout and lets the
  flow fail the ordinary way, so a run that would otherwise be killed
  mid-flight still reports (PIPE-020). Its `RunOutOfTime` is a
  `BaseException`, so a flow's `except Exception` cannot swallow it.
- A `module "<cog>"` block in mini-app-polis/infra `cogs.tf` (ADR-0010),
  through a pull request there — the queue and DLQ with a redrive policy,
  the function, the event source mapping with `ReportBatchItemFailures`,
  the alarms and the deploy role all come from `modules/cog-worker`.
  Set `timeout_seconds` above the slowest job you expect; the module's
  duration alarm fires when a job crosses `duration_alarm_ratio` of it,
  which is the cue to raise the timeout or bound the job (PIPE-022).
  State the concurrency ceiling once: `reserved_concurrency = 1` for a cog
  that sweeps a shared resource and must run alone, otherwise
  `max_concurrency = N` (at least 2) — the module refuses both or neither
  (PIPE-018). List the secrets the worker needs by name in
  `ssm_parameters` / `ssm_optional_parameters` — every uncommented
  `.env.example` name, and the Sentry DSN and any Healthchecks URL the code
  reads (CD-037). Each maps the name the code reads to the name of its value
  in Doppler's `mini-app-polis-ecosystem` / `prd`. infra's `doppler/` root
  gives the cog a Doppler project of its own whose `prd` config references
  those values and syncs to the cog's Parameter Store prefix: apply it, and
  run its references script, before the function first deploys.
  The cog's package `__init__.py` calls `mini_app_polis.load_secrets()`
  before anything else, so they are in the environment before any module
  reads it, and the handler calls `load_secrets(refresh=True)` at the top
  of every invocation, so a value changed in Doppler applies to the next
  run without a deploy.
  A repository created now presents GitHub's id-based OIDC subject
  (`repo:mini-app-polis@<id>/<name>@<id>`); the module's deploy-role trust
  must match it (see ADR-0010, Negative).
  Queue names are `<cog>-jobs`; api-kaianolevine-com derives them the same
  way.
- An API dispatch path in api-kaianolevine-com (`services/<cog>_dispatch.py`
  plus a `POST /v1/<cog>/runs` route) — the queue has no other producer.
- An ADR recording the move, if the cog existed before.

Trigger cogs:
- `handler.py` — `lambda_handler(event, context)` runs one tick;
  Sentry is initialised at import
- `main.py` — runs a tick outside Lambda (`--once`), for local runs
- `config.py` — config dataclass, empty config list by default
- Healthchecks.io ping after every tick
- A `module "<cog>"` block in mini-app-polis/infra `cogs.tf` calling
  `modules/scheduled-worker` (ADR-0011)
- Runs are started with a POST to api-kaianolevine-com through
  `KaianoApiClient`, never by sending to a queue (PIPE-019)

---

## Step 7 — Docs

Create `docs/PIPELINE.md` — where this cog fits in the ecosystem flow.
Create `docs/CONFIGURATION.md` — every environment variable documented.

---

## Step 8 — Post-deploy setup

Pipeline cogs:
1. Sentry — no new project: add `SENTRY_DSN_COGS` to the cog's
   `ssm_optional_parameters` and set the `service` tag after `sentry_sdk.init`
2. Merge the module block's pull request in mini-app-polis/infra; CI
   applies it. Terraform never creates access keys — mint any by hand
   with `aws iam create-access-key` and put them straight into Doppler.
3. Confirm the SNS subscription email for the DLQ alarm
4. Set the repo variables the deploy job reads (`AWS_DEPLOY_ROLE_ARN`,
   `AWS_REGION`, `AWS_FUNCTION_NAME`) from `terraform output cogs` in
   mini-app-polis/infra

Trigger cogs, after the module block is applied:
1. Healthchecks.io — create check, set `HEALTHCHECKS_URL_{COG}` in Doppler
2. Sentry — no new project: read `SENTRY_DSN_COGS` and set the `service`
   tag after `sentry_sdk.init`

---

## Step 9 — Install pre-commit and verify
```bash
doppler setup                 # reads doppler.yaml
uv sync
uv run pre-commit install
uv run pre-commit run --all-files
uv run pytest                 # needs no Doppler and no secrets
uv run check-doppler-keys     # every required .env.example name is in dev
```

Run the cog itself under Doppler: `doppler run -- uv run python -m {package_name}.main`.

All checks must pass before first commit to main.

---

## Definition of done

Run through the `new_cog` checklist in `definitions-of-done.yaml`
before considering the cog production-ready.
