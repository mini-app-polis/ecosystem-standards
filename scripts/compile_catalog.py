#!/usr/bin/env python3
"""Compile the standards catalog into one normalized JSON document.

Consumers fetch this instead of walking the repo. Before it existed, a
conformance run made one request per standards file per service — the index
to resolve the domain list, then every domain file, repeated for each repo
under evaluation — and re-derived the same structure each time. One
document, fetched once, replaces all of it.

Two things are resolved at build time rather than at evaluation time:

  ``check_mode``
      Parsed from the ``DETERMINISTIC CHECK.`` / ``LLM CHECK.`` marker on
      each checkable rule's ``check_notes``. The evaluator no longer reads
      prose to decide which engine a rule belongs to.

  ``domain``
      Taken from the rule's file entry in ``index.yaml``, so a rule knows
      its own domain without the consumer reconstructing it from a path.

Rules with ``checkable: false`` ARE included, carrying the flag. They were
filtered out at fetch previously, which made them invisible rather than
visibly unverified — ``index.yaml`` states that gap rules "emit an INFO
finding on every run noting the gap", and a catalog that omits them makes
that impossible to honour. Shipping them lets the consumer decide.

The output is a build artifact, not a committed file. ``package.json`` is
the version source and semantic-release owns it, so a meaningful version
only exists after a release — compile and validate on every push, publish
only from the release job.

Usage:
    python3 scripts/compile_catalog.py [--out catalog.json] [--stdout]
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path
from typing import Any

from catalog_sources import (
    REPO_ROOT,
    classify_check_mode,
    iter_rules,
    load_index,
    load_package_json,
    rel,
    standards_files,
)

#: Rule fields carried through to the compiled catalog, in output order.
#: Provenance fields (``origin``, ``decision``, ``supersedes``) are carried
#: only when present — they are documentation for whoever investigates a
#: finding, and absent on most rules.
_RULE_FIELDS: tuple[str, ...] = (
    "title",
    "status",
    "dimension",
    "severity",
    "description",
    "checkable",
    "check_notes",
    "applies_to",
    "modifies",
    "origin",
    "decision",
    "supersedes",
)

#: ``schema`` sub-blocks the catalog carries.
#:
#: ``rule_fields`` is authoring metadata — the validator reads it straight
#: from ``index.yaml`` and no consumer needs it at evaluation time.
#: ``service_fields``, ``monorepo_fields`` and ``ecosystem_sections``
#: describe the shape of ``ecosystem.yaml``, which is being removed; a
#: repo's own ``evaluator.yaml`` is becoming the only source of its
#: context, and this repo is to carry no repo or org knowledge at all.
_SCHEMA_BLOCKS: tuple[str, ...] = (
    "repo_types",
    "traits",
    "dispatch",
    "evaluator_yaml",
)

#: Top-level ``index.yaml`` blocks carried verbatim. ``files`` is omitted:
#: it is the manifest of what to compile, and means nothing once compiled.
_INDEX_BLOCKS: tuple[str, ...] = (
    "dimensions",
    "severities",
    "statuses",
    "vulnerability_severities",
    "vulnerability_response",
)


def _domains_by_file(index: dict[str, Any]) -> dict[str, str]:
    """``{file path: domain}`` from ``index.yaml`` files:."""
    out: dict[str, str] = {}
    for entry in index.get("files") or []:
        if isinstance(entry, dict) and entry.get("file"):
            out[str(entry["file"])] = str(entry.get("domain") or "")
    return out


def _normalize_applies_to(rule: dict[str, Any]) -> list[str] | None:
    """Resolve ``applies_to`` to a list of type names, or ``None``.

    ``None`` means the rule is not a repo-source scan (ADR-004) — its check
    reads the evaluations table, the evaluator's own registry, or another
    non-per-repo source, and ``check_notes`` is authoritative for what.

    An explicit empty list is treated as ``None`` for the same reason: a
    rule that applies to no repo type is not a repo scan. ``["all"]`` is
    carried verbatim rather than expanded, because its documented meaning
    is "every member of ``repo_types``, including ones added later" — and
    expanding here would freeze it at compile time.
    """
    raw = rule.get("applies_to")
    if not isinstance(raw, list) or not raw:
        return None
    return [str(item) for item in raw]


def compile_catalog() -> dict[str, Any]:
    """Build the catalog document."""
    index = load_index()
    package = load_package_json()
    domains = _domains_by_file(index)

    version = str(package.get("version") or "")
    if not version:
        raise ValueError("package.json has no version — cannot key a catalog")

    rules: list[dict[str, Any]] = []
    for path, rule in iter_rules():
        where = rel(path)
        entry: dict[str, Any] = {
            "id": str(rule.get("id") or ""),
            "domain": domains.get(where, ""),
            "file": where,
        }
        for field in _RULE_FIELDS:
            if field in ("origin", "decision", "supersedes"):
                if rule.get(field):
                    entry[field] = rule[field]
                continue
            if field == "applies_to":
                entry[field] = _normalize_applies_to(rule)
                continue
            if field == "modifies":
                raw = rule.get("modifies") or []
                entry[field] = [str(x) for x in raw] if isinstance(raw, list) else []
                continue
            if field == "checkable":
                entry[field] = bool(rule.get("checkable"))
                continue
            entry[field] = rule.get(field)
        entry["check_mode"] = classify_check_mode(rule)
        rules.append(entry)

    catalog: dict[str, Any] = {
        "version": version,
        "compiled_at": datetime.datetime.now(datetime.timezone.utc).isoformat(
            timespec="seconds"
        ),
        "rule_count": len(rules),
    }
    for block in _INDEX_BLOCKS:
        if block in index:
            catalog[block] = index[block]
    schema = index.get("schema") or {}
    catalog["schema"] = {b: schema[b] for b in _SCHEMA_BLOCKS if b in schema}
    catalog["rules"] = rules
    return catalog


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        default=str(REPO_ROOT / "catalog.json"),
        help="Where to write the compiled catalog (default: repo root catalog.json)",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Write to stdout instead of a file",
    )
    args = parser.parse_args(argv)

    try:
        catalog = compile_catalog()
    except Exception as exc:  # noqa: BLE001 — any compile failure is fatal
        print(f"FATAL: could not compile catalog: {exc}", file=sys.stderr)
        return 2

    payload = json.dumps(catalog, indent=2, sort_keys=False, ensure_ascii=False)

    if args.stdout:
        try:
            print(payload)
        except BrokenPipeError:
            # `--stdout | head` closes the pipe early. Not a failure.
            return 0
        return 0

    out_path = Path(args.out)
    out_path.write_text(payload + "\n")

    checkable = sum(1 for r in catalog["rules"] if r["checkable"])
    deterministic = sum(1 for r in catalog["rules"] if r["check_mode"] == "deterministic")
    llm = sum(1 for r in catalog["rules"] if r["check_mode"] == "llm")
    print(
        f"OK - catalog v{catalog['version']}: {catalog['rule_count']} rules "
        f"({checkable} checkable / {deterministic} deterministic, {llm} LLM, "
        f"{catalog['rule_count'] - checkable} not checkable) "
        f"across {len(standards_files())} files -> {out_path.name}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
