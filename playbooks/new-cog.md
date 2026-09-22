---
# Playbook: new cog

A cog is a Python service. This playbook covers both subtypes:
- **Pipeline cog** — a Lambda function behind its own SQS queue that
  processes one job per message (e.g. deejay-cog, evaluator-cog). Nothing
  runs between jobs. See ADR-009.
- **Trigger cog** — an always-on worker on Railway that detects events and
  asks api-kaianolevine-com to run a job (e.g. watcher-cog). The API is the
  only producer to any queue.

---

## Prerequisites

- Python 3.11+
- uv installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Access to the mini-app-polis GitHub org
- Doppler access to the cog's project
- Sentry account (free tier)
- Pipeline cogs: AWS CLI with the `miniapppolis` profile, Terraform
- Trigger cogs: Railway access to the ecosystem project, Healthchecks.io

---

## Step 1 — Create the repo

1. Create a new empty repo in the **mini-app-polis** GitHub org
2. Name it `{purpose}-cog` (e.g. `notes-cog`, `spotify-cog`)
3. Add a README and .gitignore (Python template)
4. Clone locally

---

## Step 2 — Bootstrap the project structure

Run in the repo root:
```bash
uv init --lib
uv add common-python-utils httpx python-dotenv
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
version = "0.1.0"
description = "{one line description}"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "common-python-utils",
    "httpx",
    "python-dotenv",
]

[dependency-groups]
dev = [
    "pre-commit",
    "pytest",
    "pytest-asyncio",
    "pytest-cov",
    "ruff",
]

[tool.uv.sources]
common-python-utils = { git = "https://github.com/mini-app-polis/common-python-utils.git", rev = "main" }

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

[tool.hatch.build.targets.wheel]
packages = ["src/{package_name}"]
```

---

## Step 4 — Standard files

Create `.env.example`:
{description of var}
{VAR_NAME}=
SENTRY_DSN=
LOG_LEVEL=INFO
Healthchecks.io ping URL (worker services only)
HEALTHCHECKS_URL=

Create `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.8
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

Create `.releaserc.json`:
```json
{
  "branches": ["main"],
  "plugins": [
    "@semantic-release/commit-analyzer",
    "@semantic-release/release-notes-generator",
    ["@semantic-release/changelog", { "changelogFile": "CHANGELOG.md" }],
    ["@semantic-release/git", {
      "assets": ["CHANGELOG.md"],
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
  the cog declares `[tool.mypy]`, and `terraform-dir: infra` when it has
  an `infra/` — `fmt -check` and `validate` need neither state nor
  credentials, and CD-027 wants them run on every push.
- **release** — semantic-release, recording the tag it cut as a job output
- **deploy** (pipeline cogs) — `lambda-deploy.yml@v3`, `needs: release`, run
  only when a tag was cut. It is a job rather than an `on: release`
  workflow because a release published with `GITHUB_TOKEN` starts no
  workflows. `handler`, `architecture` and `python-version` must match
  `infra/worker.tf`.
- **evaluate** — `evaluate.yml@v3`, `needs: deploy`, so a release is
  graded only once it is running

The release job, for reference:
```yaml
  release:
    name: Release
    needs: test
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
- Logging through `mini_app_polis.logging` — no `basicConfig` (the Lambda
  runtime has already configured the root logger, so it would do nothing)
- Sentry init before any application logic
- External API calls retried at the call site (PIPE-007): a
  common-python-utils client, the library's own retry, or tenacity. Queue
  redelivery is the backstop, not the retry.

Pipeline cogs:
- `worker.py` — `lambda_handler(event, context)` iterates the SQS records,
  runs `process_message(body, run_id=record["messageId"])` for each, and
  returns `{"batchItemFailures": [...]}` naming the records that raised.
  A malformed message is reported and dropped (never retried), and
  reported only on its first receive — gate on the record's
  `ApproximateReceiveCount`, or five redeliveries become five identical
  findings for one message (PIPE-021). The flows report their own
  failures; the consumer reports only what never reached one.
  Copy deejay-cog's `worker.py`.
- `_deadline.py` — the handler stops the run a margin before the function
  timeout and lets the flow fail the ordinary way, so a run that would
  otherwise be killed mid-flight still reports (PIPE-020). Copy
  transcription-cog's.
- `infra/` — copied from deejay-cog: queue and DLQ with a redrive policy,
  the function, the event source mapping with `ReportBatchItemFailures`,
  a DLQ alarm with an action, and the `tf` wrapper that feeds Doppler
  secrets in as `TF_VAR_*`. State the concurrency ceiling once, on one
  side or the other: `reserved_concurrent_executions` on the function, or
  `scaling_config.maximum_concurrency` on the mapping. A cog that sweeps
  a shared resource needs 1, which means the reservation and no
  `scaling_config` at all — the mapping's maximum cannot go below 2, and
  AWS refuses a mapping maximum above the function's reservation
  (PIPE-018).
  Queue names are `<cog>-jobs` in production and `<cog>-dev-jobs`
  elsewhere; api-kaianolevine-com derives them the same way.
- An API dispatch path in api-kaianolevine-com (`services/<cog>_dispatch.py`
  plus a `POST /v1/<cog>/runs` route) — the queue has no other producer.
- An ADR recording the move, if the cog existed before.

Trigger cogs:
- `main.py` — entry point, loads env, initialises Sentry, starts the loop
- `config.py` — config dataclass, empty config list by default
- Healthchecks.io ping on every work cycle
- Runs are started with a POST to api-kaianolevine-com through
  `KaianoApiClient`, never by sending to a queue (PIPE-019)

---

## Step 7 — Docs

Create `docs/PIPELINE.md` — where this cog fits in the ecosystem flow.
Create `docs/CONFIGURATION.md` — every environment variable documented.

---

## Step 8 — Post-deploy setup

Pipeline cogs:
1. Sentry — create the project and put `SENTRY_DSN` in Doppler
2. `cd infra && ./tf init && ./tf plan -out tfplan && ./tf apply tfplan`.
   Secrets come from Doppler; `terraform.tfvars` holds only non-secret
   settings. Terraform never creates access keys — mint any by hand with
   `aws iam create-access-key` and put them straight into Doppler.
3. Confirm the SNS subscription email for the DLQ alarm
4. Set the repo variables the deploy job reads (`AWS_DEPLOY_ROLE_ARN`,
   `AWS_REGION`, `AWS_FUNCTION_NAME`)

Trigger cogs, after deploying to Railway:
1. Healthchecks.io — create check, set HEALTHCHECKS_URL in Doppler
2. Sentry — create project, set SENTRY_DSN in Doppler

---

## Step 9 — Install pre-commit and verify
```bash
uv sync
uv run pre-commit install
uv run pre-commit run --all-files
uv run pytest
```

All checks must pass before first commit to main.

---

## Definition of done

Run through the `new_cog` checklist in `definitions-of-done.yaml`
before considering the cog production-ready.
