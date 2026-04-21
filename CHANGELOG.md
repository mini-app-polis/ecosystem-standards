# [3.8.0](https://github.com/mini-app-polis/ecosystem-standards/compare/v3.7.0...v3.8.0) (2026-04-21)


### Features

* splitting prefixes to correct files and formal clean up restructure ([cc4a839](https://github.com/mini-app-polis/ecosystem-standards/commit/cc4a839e7ba5cab12ead48ab9d20552a6d57d73d))

# [3.7.0](https://github.com/mini-app-polis/ecosystem-standards/compare/v3.6.0...v3.7.0) (2026-04-21)


### Features

* **ci:** enforce META-002, META-005, META-006 in validation; read enums from source ([f32f01e](https://github.com/mini-app-polis/ecosystem-standards/commit/f32f01e157c430529fc5897486560aac2c4a1ba2))

# [3.6.0](https://github.com/mini-app-polis/ecosystem-standards/compare/v3.5.1...v3.6.0) (2026-04-21)


### Features

* **meta:** add META-006 prefix/file correlation and META-007 append-only IDs. ([e96ea35](https://github.com/mini-app-polis/ecosystem-standards/commit/e96ea35d9f454bf5d44d7dfde474393738b53af4))

## [3.5.1](https://github.com/mini-app-polis/ecosystem-standards/compare/v3.5.0...v3.5.1) (2026-04-21)


### Bug Fixes

* refactor(standards) apply review clarifications ([fe91cbe](https://github.com/mini-app-polis/ecosystem-standards/commit/fe91cbe355c6742794bf1280c9d72de1a12ed46d))

# [3.5.0](https://github.com/mini-app-polis/ecosystem-standards/compare/v3.4.2...v3.5.0) (2026-04-21)


### Features

* feat(CD-012), feat(META-005), refactor(standards): prefix sweep, refactor(standards): reorder rules, chore: delete drift tooling, docs: README + ADR-003 ([7eba66e](https://github.com/mini-app-polis/ecosystem-standards/commit/7eba66e59f07aad49f3fbcf244c57c2239bbc6db))

## [3.4.2](https://github.com/mini-app-polis/ecosystem-standards/compare/v3.4.1...v3.4.2) (2026-04-20)


### Bug Fixes

* api spec ([808a3c5](https://github.com/mini-app-polis/ecosystem-standards/commit/808a3c54af88e0a9923a340df292140f537f895c))

## [3.4.1](https://github.com/mini-app-polis/ecosystem-standards/compare/v3.4.0...v3.4.1) (2026-04-20)


### Bug Fixes

* clarifying intent on api definitions ([c0b8ed3](https://github.com/mini-app-polis/ecosystem-standards/commit/c0b8ed3fdc30946929c87618a29bc5ef063eddf5))
* yaml ([7bccf94](https://github.com/mini-app-polis/ecosystem-standards/commit/7bccf94d3ce0797defb22ba22a1ae5299820db71))

# [3.4.0](https://github.com/mini-app-polis/ecosystem-standards/compare/v3.3.0...v3.4.0) (2026-04-19)


### Features

* sharpen 15 fuzzy rules, promote CD-012 (Keystone done), EVAL-003 + MONO-003 (new evaluator-service type), demote 8 principles ([edf5e01](https://github.com/mini-app-polis/ecosystem-standards/commit/edf5e01cb69d28e3ec131da9ac46557f3ccb4763))

# [3.3.0](https://github.com/mini-app-polis/ecosystem-standards/compare/v3.2.0...v3.3.0) (2026-04-19)


### Features

* sharpen 15 fuzzy rules, promote CD-012 (Keystone done), EVAL-003 + MONO-003 (new evaluator-service type), demote 8 principles ([0230c4e](https://github.com/mini-app-polis/ecosystem-standards/commit/0230c4ec1e3d27d3e40ffa1c2ee67ca17fae91b5))

# [3.2.0](https://github.com/mini-app-polis/ecosystem-standards/compare/v3.1.1...v3.2.0) (2026-04-19)


### Features

* four rule splits, META prefix for standards-repo rules, DOC-012 deletion, EVAL-007 scope fix, sharpen eleven rules to checkable, rewrite CD-012 for clarity, upgrade dimensions manifest ([05698ba](https://github.com/mini-app-polis/ecosystem-standards/commit/05698ba4e393bed754d66bd366d9af2bc9e187d5))

## [3.1.1](https://github.com/mini-app-polis/ecosystem-standards/compare/v3.1.0...v3.1.1) (2026-04-19)


### Bug Fixes

* realign package.json with latest release and fix changelog duplicate ([39b82f6](https://github.com/mini-app-polis/ecosystem-standards/commit/39b82f695eaf2306e4eaac36247bfac39fbe904a))

# [3.1.0](https://github.com/mini-app-polis/ecosystem-standards/compare/v3.0.1...v3.1.0) (2026-04-19)


### Features

* document canonical severity and source enums, runtime-resolution pattern for standards_version ([f701aa0](https://github.com/mini-app-polis/ecosystem-standards/commit/f701aa0f8c5aa1247fd29174aa05f54697433174))

## [3.0.1](https://github.com/mini-app-polis/ecosystem-standards/compare/v3.0.0...v3.0.1) (2026-04-06)


### Bug Fixes

* removing exceptions in this repo. each repo now owns their exceptions ([5c7da81](https://github.com/mini-app-polis/ecosystem-standards/commit/5c7da81e7ab45a1a746d75fcac30ba36e5236386))

# [3.0.0](https://github.com/mini-app-polis/ecosystem-standards/compare/v2.5.1...v3.0.0) (2026-04-06)


* feat!: v3.0.0 — type/trait taxonomy, federated evaluator.yaml schema, EVAL-008 ([8fe3d42](https://github.com/mini-app-polis/ecosystem-standards/commit/8fe3d422b7d3c2dd255e1455bbe1df3cb0633972))


### Bug Fixes

* update CI applies_to validation to v3.0.0 type names ([8389da2](https://github.com/mini-app-polis/ecosystem-standards/commit/8389da294bd86e70b01b98a7dc8ec1c56dee5a8b))


### BREAKING CHANGES

* applies_to values in all standards files updated from dod_type names to repo type names (new_cog → pipeline-cog, new_fastapi_service → api-service, new_hono_service → api-service, new_frontend_site → static-site, new_react_app → react-app, library → shared-library). Evaluator-cog versions pinned to standards < v3.0.0 will not correctly scope rules by type until updated.

## [2.5.1](https://github.com/mini-app-polis/ecosystem-standards/compare/v2.5.0...v2.5.1) (2026-04-06)


### Bug Fixes

* **DOC-013:** extend applies_to to frontend site and React app ([59938e6](https://github.com/mini-app-polis/ecosystem-standards/commit/59938e64b2533d374a21892b2459350d7fb7347e))

# [2.5.0](https://github.com/mini-app-polis/ecosystem-standards/compare/v2.4.2...v2.5.0) (2026-04-05)


### Features

* findings quality pass — false positive fixes, deduplication, missing rules ([48ddf81](https://github.com/mini-app-polis/ecosystem-standards/commit/48ddf8179cb7d3c44a9aca507cd590a92d6c3d60))

## [2.4.2](https://github.com/mini-app-polis/ecosystem-standards/compare/v2.4.1...v2.4.2) (2026-04-05)


### Bug Fixes

* removing workspace dep causing false positive ([23edf88](https://github.com/mini-app-polis/ecosystem-standards/commit/23edf88cfe46306a5e759970ab92e5d65a71cdc8))

## [2.4.1](https://github.com/mini-app-polis/ecosystem-standards/compare/v2.4.0...v2.4.1) (2026-04-05)


### Bug Fixes

* updating with monorepo ([2ab79a7](https://github.com/mini-app-polis/ecosystem-standards/commit/2ab79a730c1a4fd5ad631e7e39a7fba29fa4f375))

# [2.4.0](https://github.com/mini-app-polis/ecosystem-standards/compare/v2.3.1...v2.4.0) (2026-04-05)


### Features

* add monorepo evaluation schema and standards/evaluator drift detection ([3ab2bb9](https://github.com/mini-app-polis/ecosystem-standards/commit/3ab2bb964da1c0e7b6559811a13e3967c30ef1e4))

## [2.3.1](https://github.com/mini-app-polis/ecosystem-standards/compare/v2.3.0...v2.3.1) (2026-04-05)


### Bug Fixes

* uprev ([5d3471b](https://github.com/mini-app-polis/ecosystem-standards/commit/5d3471b8f9e2162743177665bae91a63bb92189d))

# [2.3.0](https://github.com/mini-app-polis/ecosystem-standards/compare/v2.2.0...v2.3.0) (2026-04-05)


### Features

* addressing false positives ([86f242d](https://github.com/mini-app-polis/ecosystem-standards/commit/86f242d8371099aa4f347fe2475a99200b2454e2))

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
