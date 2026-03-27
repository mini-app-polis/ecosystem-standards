# 1.0.0 (2026-03-27)


### Bug Fixes

* moving definition of done ([0822b79](https://github.com/mini-app-polis/ecosystem-standards/commit/0822b79a2cc164ac0aaf628fb8b9aa9a6a332c5c))


### Features

* first workable draft ([974f5d0](https://github.com/mini-app-polis/ecosystem-standards/commit/974f5d0b5e4ce5fd1be4a2979615888e7bc614c1))

# Changelog

## 1.0.0 — 2026-03

Initial release. Migrated from `ecosystem_standards_v10.docx` into
machine-readable YAML split across ten domain files.

**Added from code review audit of `kaianolevine-api` and `kaiano-common-utils`:**
- AUTH-001 — No unverified write endpoints reachable from the public internet
- AUTH-002 — API auth scheme and HTTP client must match
- CFG-001 — No getattr() access for undeclared Settings fields
- CFG-002 — Every key in .env.example must be declared in Settings
- PY-009 — hatchling as build backend (decision: hatchling over setuptools)
- PY-010 — ruff line length is 88 (decision: 88 over 100)
- TEST-012 — mypy must run in CI if [tool.mypy] is declared
- CD-004 — GitHub Actions version tags must be valid
- DOC-009 — Split package identity documented at entry point

**Decisions recorded:**
- Build backend: hatchling (March 2026)
- ruff line length: 88 (March 2026)
