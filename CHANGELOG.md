# [2.2.0](https://github.com/mini-app-polis/ecosystem-standards/compare/v2.1.0...v2.2.0) (2026-04-05)


### Features

* add PIPE-009 runtime concurrency slot requirement for pipeline cogs ([a278caa](https://github.com/mini-app-polis/ecosystem-standards/commit/a278caa606e3b2dd29c1919406c4f6391e37972f))

# [2.1.0](https://github.com/mini-app-polis/ecosystem-standards/compare/v2.0.0...v2.1.0) (2026-04-04)


### Features

* add PIPE-010 and TEST-013 — retry delays and operational waits sourced from config ([b9f86f6](https://github.com/mini-app-polis/ecosystem-standards/commit/b9f86f666d4595a0dfd50b3a82bc1b019b13ff40))

# [2.0.0](https://github.com/mini-app-polis/ecosystem-standards/compare/v1.9.1...v2.0.0) (2026-04-04)


* feat!: structured check_exceptions, dod_type mapping, applies_to on all rules ([f1e3ec5](https://github.com/mini-app-polis/ecosystem-standards/commit/f1e3ec5fb74c2342d45660717a615225e35b42b7))


### Features

* add 9 new rules — CORS, health endpoint, migrations, async SQLAlchemy, pnpm, env var naming, Cloudflare Pages, Prefect serve(), releaserc assets ([438e47a](https://github.com/mini-app-polis/ecosystem-standards/commit/438e47af7ab1444629fbee1b28e3fe5127688310))


### BREAKING CHANGES

* check_exceptions migrated from flat string list to
{rule, reason} objects. ecosystem.yaml adds dod_type to all active
services. All standards rules now have applies_to field. Evaluator-cog
must be updated to handle new schema before conformance checks resume.

Made-with: Cursor

## [1.9.1](https://github.com/mini-app-polis/ecosystem-standards/compare/v1.9.0...v1.9.1) (2026-04-04)


### Bug Fixes

* remove hand-written CHANGELOG section, add repo to ecosystem inventory, enforce checkable/check_notes in CI ([dfff725](https://github.com/mini-app-polis/ecosystem-standards/commit/dfff725104bc7f51b45c1a6d41cb17bc9a6bc41c))

# [1.9.0](https://github.com/mini-app-polis/ecosystem-standards/compare/v1.8.0...v1.9.0) (2026-04-04)


### Features

* add check_notes to 14 LLM-assisted rules — checkable coverage 65% → 77% ([f874824](https://github.com/mini-app-polis/ecosystem-standards/commit/f87482485c95d847ab9e564e174175619bd166b7))

# [1.8.0](https://github.com/mini-app-polis/ecosystem-standards/compare/v1.7.2...v1.8.0) (2026-04-04)


### Features

* add check_notes to 20 uncheckable rules — checkable coverage 46% → 65% ([9530f3f](https://github.com/mini-app-polis/ecosystem-standards/commit/9530f3ff889946b976f32f02ad68a40476cf8054))

## [1.7.2](https://github.com/mini-app-polis/ecosystem-standards/compare/v1.7.1...v1.7.2) (2026-04-04)


### Bug Fixes

* ecosystem cleanup — check_exceptions, retired services, index changelog, rule ordering ([3aee88b](https://github.com/mini-app-polis/ecosystem-standards/commit/3aee88b2c434f4d50f75056fceed5d2750444169))

## [1.7.1](https://github.com/mini-app-polis/ecosystem-standards/compare/v1.7.0...v1.7.1) (2026-04-04)


### Bug Fixes

* cleanup ([b3633a5](https://github.com/mini-app-polis/ecosystem-standards/commit/b3633a5ce4572c079aa0172de5a4bae7107b62e4))
* cleanup ([c8df968](https://github.com/mini-app-polis/ecosystem-standards/commit/c8df96813319cee46f5ab3d6fd60ca2da145204c))
* cleanup ([8770b53](https://github.com/mini-app-polis/ecosystem-standards/commit/8770b539ac6a99453b82d8caf39aee657cac3871))

# [1.7.0](https://github.com/mini-app-polis/ecosystem-standards/compare/v1.6.3...v1.7.0) (2026-04-04)


### Bug Fixes

* yaml formatting ([a831641](https://github.com/mini-app-polis/ecosystem-standards/commit/a8316410769b14e7a911ae37feac947f489f67a5))


### Features

* add notes-ingest-cog to ecosystem inventory and fix: scope CD-007 to trigger cogs only ([c6a809f](https://github.com/mini-app-polis/ecosystem-standards/commit/c6a809f2c283367bebce29baa04182cdf2a62aca))

## [1.6.3](https://github.com/mini-app-polis/ecosystem-standards/compare/v1.6.2...v1.6.3) (2026-04-03)


### Bug Fixes

* scope CD-007 to trigger cogs only ([5ee6718](https://github.com/mini-app-polis/ecosystem-standards/commit/5ee6718524f790d08c4182f3531e1f4973acd534))

## [1.6.2](https://github.com/mini-app-polis/ecosystem-standards/compare/v1.6.1...v1.6.2) (2026-04-02)


### Bug Fixes

* static site detection ([d54f674](https://github.com/mini-app-polis/ecosystem-standards/commit/d54f67456e2d24714408aa6f032ff5b7082c7444))

## [1.6.1](https://github.com/mini-app-polis/ecosystem-standards/compare/v1.6.0...v1.6.1) (2026-04-02)


### Bug Fixes

* suppress DOC-013 Python README check on TypeScript services ([4139e96](https://github.com/mini-app-polis/ecosystem-standards/commit/4139e96648b64f3f6df298061fad5a3580476436))

# [1.6.0](https://github.com/mini-app-polis/ecosystem-standards/compare/v1.5.0...v1.6.0) (2026-03-31)


### Features

* add check_exceptions and cog_subtype to ecosystem inventory ([a390c27](https://github.com/mini-app-polis/ecosystem-standards/commit/a390c270ea6fe73fd3fe28cd20f8a4476f57bf9a))

# [1.5.0](https://github.com/mini-app-polis/ecosystem-standards/compare/v1.4.0...v1.5.0) (2026-03-30)


### Features

* add deejaytools-com to ecosystem inventory, mark kaiano-ts-utils active. ([228c6f2](https://github.com/mini-app-polis/ecosystem-standards/commit/228c6f235b9be15e8a8b44a32db0b447f5331da7))

# [1.4.0](https://github.com/mini-app-polis/ecosystem-standards/compare/v1.3.1...v1.4.0) (2026-03-29)


### Features

* mark kaiano-ts-utils as active ([3a68ca1](https://github.com/mini-app-polis/ecosystem-standards/commit/3a68ca142724fc28789e1cc290cedbc9514e1e5f))

## [1.3.1](https://github.com/mini-app-polis/ecosystem-standards/compare/v1.3.0...v1.3.1) (2026-03-29)


### Bug Fixes

* updating plans for evaluation ([9b5a5d9](https://github.com/mini-app-polis/ecosystem-standards/commit/9b5a5d97d57c21962706460f605402910132db8a))

# [1.3.0](https://github.com/mini-app-polis/ecosystem-standards/compare/v1.2.5...v1.3.0) (2026-03-29)


### Features

* adding content for feature flag and secret management ([f9d0166](https://github.com/mini-app-polis/ecosystem-standards/commit/f9d0166e8d747dadb7c907dc524e603a910e30e8))

## [1.2.5](https://github.com/mini-app-polis/ecosystem-standards/compare/v1.2.4...v1.2.5) (2026-03-28)


### Bug Fixes

* use findngs update ([87a6c2f](https://github.com/mini-app-polis/ecosystem-standards/commit/87a6c2f4cc5d6cc0b54ecd67f8bb200cc84b33dd))

## [1.2.4](https://github.com/mini-app-polis/ecosystem-standards/compare/v1.2.3...v1.2.4) (2026-03-28)


### Bug Fixes

* update gap findings ([3e8d279](https://github.com/mini-app-polis/ecosystem-standards/commit/3e8d27902df407fd1183362e825c9aea82fd34c5))

## [1.2.3](https://github.com/mini-app-polis/ecosystem-standards/compare/v1.2.2...v1.2.3) (2026-03-28)


### Bug Fixes

* updating with use findings ([d15384e](https://github.com/mini-app-polis/ecosystem-standards/commit/d15384e539c4371be9a06b12e04a1ea70cda51bc))

## [1.2.2](https://github.com/mini-app-polis/ecosystem-standards/compare/v1.2.1...v1.2.2) (2026-03-28)


### Bug Fixes

* updating with use findings ([32b3e32](https://github.com/mini-app-polis/ecosystem-standards/commit/32b3e32235939d2c80fb896df8e835d1105d71f0))

## [1.2.1](https://github.com/mini-app-polis/ecosystem-standards/compare/v1.2.0...v1.2.1) (2026-03-28)


### Bug Fixes

* minor clean up of terminology references ([15a46fc](https://github.com/mini-app-polis/ecosystem-standards/commit/15a46fcb61330695c20cd2677852c2c29af52622))

# [1.2.0](https://github.com/mini-app-polis/ecosystem-standards/compare/v1.1.0...v1.2.0) (2026-03-28)


### Features

* adding terminology and new project expectations ([5ef303a](https://github.com/mini-app-polis/ecosystem-standards/commit/5ef303abd4c821553851deba512d21504cf6d880))

# [1.1.0](https://github.com/mini-app-polis/ecosystem-standards/compare/v1.0.1...v1.1.0) (2026-03-28)


### Features

* orchestration architecture, logging standards, ecosystem inventory, service renames ([5250010](https://github.com/mini-app-polis/ecosystem-standards/commit/5250010800a354cd94bb33a7f7bdf75b668d27fe))

## [1.0.1](https://github.com/mini-app-polis/ecosystem-standards/compare/v1.0.0...v1.0.1) (2026-03-27)


### Bug Fixes

* clean up ([d5e5559](https://github.com/mini-app-polis/ecosystem-standards/commit/d5e5559cbf9c8c00352a7e14eefbcb06fab0e326))

# 1.0.0 (2026-03-27)


### Bug Fixes

* moving definition of done ([0822b79](https://github.com/mini-app-polis/ecosystem-standards/commit/0822b79a2cc164ac0aaf628fb8b9aa9a6a332c5c))


### Features

* first workable draft ([974f5d0](https://github.com/mini-app-polis/ecosystem-standards/commit/974f5d0b5e4ce5fd1be4a2979615888e7bc614c1))
