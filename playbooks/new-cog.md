---
# Playbook: new cog

A cog is an always-on Python worker service deployed on Railway. This
playbook covers both subtypes:
- **Pipeline cog** — runs a Prefect @flow to process data (e.g. deejay-cog)
- **Trigger cog** — detects events and fires Prefect flow runs (e.g. watcher-cog)

---

## Prerequisites

- Python 3.11+
- uv installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Access to the mini-app-polis GitHub org
- Railway account with access to the ecosystem project
- Prefect Cloud account
- Sentry account (free tier)
- Healthchecks.io account (free tier)

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

Create `.github/workflows/ci.yml`:
```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: astral-sh/setup-uv@v7
        with:
          enable-cache: true
      - run: uv sync --all-extras
      - run: uv run ruff check src tests
      - run: uv run ruff format --check src tests
      - run: uv run pytest --cov={package_name} --cov-report=term-missing

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
      - uses: actions/checkout@v6
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
```

---

## Step 6 — Implement the cog

Use the watcher-cog repo as the reference implementation for trigger
cogs. Use deejay-cog as the reference implementation for pipeline cogs.

All cogs must include:
- `logger.py` — imports logger from `mini_app_polis.logging`
- `main.py` — entry point, loads env, initialises Sentry, starts loop
- `config.py` — config dataclass, empty config list by default
- Sentry init at entry point before any application logic
- Healthchecks.io ping on every work cycle

For pipeline cogs, wrap external API calls in `@task` with retries per PIPE-007. Retry delays must use the `PYTEST_CURRENT_TEST` guard (PIPE-010):

```python
@task(
    retries=2,
    retry_delay_seconds=0 if os.getenv("PYTEST_CURRENT_TEST") else 30,
)
```

---

## Step 7 — Docs

Create `docs/PIPELINE.md` — where this cog fits in the ecosystem flow.
Create `docs/CONFIGURATION.md` — every environment variable documented.

---

## Step 8 — Post-deploy setup

After deploying to Railway, complete the manual setup documented in
the README "Post-deploy setup" section:
1. Healthchecks.io — create check, set HEALTHCHECKS_URL in Railway
2. Prefect Cloud — create automation per deployment for failure alerts
3. Sentry — create project, set SENTRY_DSN in Railway

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
