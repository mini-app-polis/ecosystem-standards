# Standards Checker — Architectural Decisions

*MiniAppPolis ecosystem · March 2026*

## Context

Next phase after the evaluator-cog PoC: automated detection of whether
repos meet ecosystem standards. The checker is advisory only — no
automated remediation.

Two complementary layers:

- `evaluator-cog / flows / pipeline_eval` — **behavioral**: did this pipeline run correctly?
- `evaluator-cog / flows / conformance` — **structural**: does this repo conform to standards?

## Decisions

**Findings destination**
Reuse `pipeline_evaluations` table with `source=conformance_check`. No new
table needed — the `source` field already exists.

**Invocation**
Centralized — conformance flow lives inside `evaluator-cog` and runs on a
Prefect schedule. Clones repos from the ecosystem inventory in `ecosystem.yaml`.
Per-repo GHA can be added later as a thin trigger if needed, but core logic
stays in one place.

**LLM involvement**
Hybrid:

- Deterministic for structural rules (file presence, pyproject.toml, CI YAML,
AST) — covers ~40 of 50 checkable rules
- LLM for soft rules (docstrings, dead code, report narrative) and to generate
actionable suggestions per finding

Since findings are advisory with no automated remediation, LLM adds real value
on interpretation and recommendations without risk of acting on bad output.

## First artifact

`src/evaluator_cog/flows/conformance.py` inside `evaluator-cog`, backed by
`src/evaluator_cog/engine/deterministic.py` and `engine/llm.py`.

## Checker known issues / decisions

### FE-003 Tailwind check — `.mjs` config and Astro integration pattern (April 2026)

**Finding:** `website-astro-software` reported a Tailwind WARN despite
`tailwindcss` being present in `dependencies`, `tailwind.config.mjs` existing,
`@astrojs/tailwind` being declared in `astro.config.mjs`, and
`postcss.config.cjs` being wired.

**Root cause (checker):** The deterministic check for FE-003 searches for
`tailwind.config.js` or `tailwind.config.ts` — it does not match
`tailwind.config.mjs`. The Astro integration pattern (`@astrojs/tailwind` in
`astro.config.mjs`) is also a valid signal that the check does not evaluate.

**Decision:** FE-003 `check_notes` to be updated to include `.mjs` config
filename and the Astro integration pattern as valid signals. Until the checker
is updated, the finding is a false positive and should be suppressed for repos
where all three signals are present: (1) `tailwindcss` in `dependencies`,
(2) `tailwind.config.mjs` at root, (3) `@astrojs/tailwind` in `astro.config.`*.

**Note:** FE-003 `applies_to` is `[new_react_app]` — it should not fire for
`new_frontend_site` at all. This is a secondary checker bug: the conformance
flow is not filtering rules by `applies_to` correctly. Track as a bug in
`evaluator-cog` conformance engine.