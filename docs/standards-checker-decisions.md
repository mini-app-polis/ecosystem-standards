# Standards Checker — Architectural Decisions
_MiniAppPolis ecosystem · March 2026_

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
