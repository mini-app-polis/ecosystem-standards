#!/usr/bin/env python3
"""Validate the standards catalog.

Previously a ~200-line heredoc inside ``.github/workflows/ci.yml``. Moved
here so it can be linted, tested, and — most of all — run by hand before
pushing, which the embedded version could not be.

Every check is enforced against the canonical sources rather than a
hardcoded allowlist: valid dimensions, statuses, repo types and rule
fields are read from ``index.yaml``, and valid ``dod_type`` values from
``definitions-of-done.yaml``. Adding a dimension to ``index.yaml`` is
therefore all it takes for rules to use it — there is no second list to
keep in step.

Enforces:
  - YAML parses, and every rule carries the fields ``schema.rule_fields``
    marks ``required: true``
  - canonical enums: status, severity, dimension, applies_to, dod_type
  - META-002: no ``added:`` on rules, no ``# Version:`` headers, no
    top-level ``updated:`` / ``maintainer:`` fields
  - META-005: a checkable rule's ``check_notes`` opens with
    ``DETERMINISTIC CHECK.`` or ``LLM CHECK.``
  - META-006: a rule's ID prefix is one declared for its file in
    ``index.yaml``
  - META-007 (lightweight): no duplicate IDs. The full append-only history
    walk is not enforced anywhere; author discipline per
    playbooks/new-standard.md Step 4 is the primary control
  - ``modifies:`` points at rule IDs that exist
  - a checkable rule does not declare ``applies_to: []`` — an explicitly
    empty scope that no consumer honours as written

Exit codes: 0 clean, 1 problems found, 2 a canonical source would not load.

Usage:  python3 scripts/validate_catalog.py
"""

from __future__ import annotations

import re
import sys

from catalog_sources import (
    ECOSYSTEM_PATH,
    REPO_ROOT,
    classify_check_mode,
    first_nonblank_line,
    iter_rules,
    load_dod,
    load_ecosystem,
    load_index,
    load_package_json,
    rel,
    standards_files,
)

#: Severities a rule definition may carry. CRITICAL and SUCCESS are
#: emission-only — the evaluator produces them, rules never declare them.
VALID_RULE_SEVERITIES = frozenset({"ERROR", "WARN", "INFO"})

#: `PREFIX-NNN`, or `PREFIX-GAP-NNN` for gap rules.
RULE_ID_RE = re.compile(r"^([A-Z]+)-(?:GAP-)?\d{3}$")

#: Files scanned for the file-level META-002 prohibitions.
_META_002_EXTRA_TARGETS = ("index.yaml", "ecosystem.yaml", "definitions-of-done.yaml")


class Errors(list):
    """Collected problems. Every check appends; nothing raises."""

    def add(self, message: str) -> None:
        self.append(message)


def _required_rule_fields(index: dict) -> list[str]:
    """Field names ``schema.rule_fields`` marks ``required: true``.

    Only the boolean ``True`` counts. ``required: false`` and conditional
    values such as ``"when checkable is true"`` are not enforced here —
    conditional requirements have their own dedicated checks below.
    """
    fields = (index.get("schema") or {}).get("rule_fields") or {}
    return [
        name
        for name, spec in fields.items()
        if isinstance(spec, dict) and spec.get("required") is True
    ]


def _prefixes_by_file(index: dict) -> dict[str, set[str]]:
    """``{file path: {allowed rule prefixes}}`` from ``index.yaml`` files:."""
    out: dict[str, set[str]] = {}
    for entry in index.get("files") or []:
        if not isinstance(entry, dict):
            continue
        path = entry.get("file")
        prefix = entry.get("rule_prefix")
        if path and prefix is not None:
            out[str(path)] = set(prefix) if isinstance(prefix, list) else {str(prefix)}
    return out


def check_rules(index: dict, errors: Errors) -> list[str]:
    """Validate every rule. Returns the list of IDs seen, in catalog order."""
    required_fields = _required_rule_fields(index)
    prefixes_by_file = _prefixes_by_file(index)

    valid_repo_types = set(
        ((index.get("schema") or {}).get("repo_types") or {}).keys()
    ) | {"all"}
    valid_dimensions = set((index.get("dimensions") or {}).keys())
    valid_statuses = set((index.get("statuses") or {}).keys())

    seen_ids: list[str] = []
    declared_ids: set[str] = set()
    modifies_refs: list[tuple[str, str]] = []

    for path in standards_files():
        if not prefixes_by_file.get(rel(path)):
            errors.add(f"{rel(path)}: no rule_prefix entry in index.yaml files:")

    for path, rule in iter_rules():
        where = rel(path)
        rule_id = rule.get("id")
        if not rule_id:
            errors.add(f"{where}: rule missing id")
            continue
        rule_id = str(rule_id)
        seen_ids.append(rule_id)
        declared_ids.add(rule_id)

        for field in required_fields:
            if field != "id" and field not in rule:
                errors.add(f"{rule_id}: missing '{field}'")

        # META-006 — ID shape, and prefix declared for this file.
        match = RULE_ID_RE.match(rule_id)
        declared = prefixes_by_file.get(where, set())
        if not match:
            errors.add(
                f"META-006: {rule_id} does not match PREFIX-NNN or "
                f"PREFIX-GAP-NNN shape"
            )
        elif declared and match.group(1) not in declared:
            errors.add(
                f"META-006: {rule_id} prefix '{match.group(1)}' not in "
                f"{sorted(declared)} declared for {where}"
            )

        status = rule.get("status")
        if status and status not in valid_statuses:
            errors.add(
                f"{rule_id}: invalid status '{status}' "
                f"(allowed: {sorted(valid_statuses)})"
            )

        severity = rule.get("severity")
        if severity and severity not in VALID_RULE_SEVERITIES:
            errors.add(
                f"{rule_id}: invalid rule-level severity '{severity}' "
                f"(allowed: {sorted(VALID_RULE_SEVERITIES)})"
            )

        dimension = rule.get("dimension")
        if dimension and dimension not in valid_dimensions:
            errors.add(
                f"{rule_id}: invalid dimension '{dimension}' "
                f"(allowed: {sorted(valid_dimensions)})"
            )

        # An omitted `applies_to` means "not a repo-source scan" (ADR-004)
        # and is legitimate. An explicit empty list declares that the rule
        # applies to no repo type — which nothing honours as written. The
        # deterministic runner dispatches these anyway, scoping them in
        # code; the LLM path filters on `applies_to` and so drops them
        # entirely. Either way the declaration does not describe what
        # happens, which is the drift the catalog exists to prevent.
        if rule.get("checkable") is True and rule.get("applies_to") == []:
            errors.add(
                f"{rule_id}: checkable: true with 'applies_to: []' — an empty "
                f"declared scope. Omit the field if the rule is not a "
                f"repo-source scan, or list the repo types it applies to."
            )

        for applies in rule.get("applies_to") or []:
            if applies not in valid_repo_types:
                errors.add(
                    f"{rule_id}: applies_to has invalid value '{applies}' "
                    f"(allowed: {sorted(valid_repo_types)})"
                )

        for target in rule.get("modifies") or []:
            modifies_refs.append((rule_id, str(target)))

        # META-005 — the dispatch marker.
        if rule.get("checkable") is True:
            notes = rule.get("check_notes") or ""
            if not notes:
                errors.add(f"{rule_id}: checkable: true but missing check_notes")
            elif classify_check_mode(rule) is None:
                first = first_nonblank_line(str(notes))
                errors.add(
                    f"META-005: {rule_id} check_notes does not start with "
                    f"'DETERMINISTIC CHECK.' or 'LLM CHECK.' (got: {first[:60]!r})"
                )

        # META-002 — history belongs in git, not in the rule.
        if "added" in rule:
            errors.add(f"META-002: {rule_id} has forbidden 'added' field")

    # `modifies:` is a structural pointer the evaluator follows to resolve
    # precedence. A dangling target is a silent no-op: the modifier never
    # fires and the rule it was meant to alter runs unmodified.
    for source_id, target in modifies_refs:
        if target not in declared_ids:
            errors.add(
                f"{source_id}: modifies '{target}', which is not a rule in "
                f"the catalog"
            )

    # META-007, lightweight.
    duplicates = sorted({i for i in seen_ids if seen_ids.count(i) > 1})
    if duplicates:
        errors.add(f"Duplicate rule IDs: {duplicates}")

    return seen_ids


def check_file_level_meta_002(errors: Errors) -> None:
    """No ``# Version:`` headers, no top-level ``updated:`` / ``maintainer:``."""
    targets = [rel(p) for p in standards_files()] + list(_META_002_EXTRA_TARGETS)
    for target in targets:
        path = REPO_ROOT / target
        if not path.exists():
            continue
        for number, line in enumerate(path.read_text().splitlines(), 1):
            if re.match(r"^# Version:", line):
                errors.add(f"META-002: {target}:{number} has '# Version:' header")
            if re.match(r"^(updated|maintainer):", line):
                key = line.split(":", 1)[0]
                errors.add(
                    f"META-002: {target}:{number} has top-level '{key}:' field"
                )


def check_services(ecosystem: dict, dod: dict, errors: Errors) -> None:
    """Every active service declares a valid ``dod_type``.

    Scoped to ``ecosystem.yaml``, which is slated for removal. When the
    registry goes, this check goes with it — there is no service list left
    to validate, and the per-repo ``evaluator.yaml`` is checked by the
    evaluator against the repo it lives in.
    """
    if not ECOSYSTEM_PATH.exists():
        return
    valid_dod = set((dod.get("definitions_of_done") or {}).keys()) | {None}
    for service in ecosystem.get("services") or []:
        if service.get("status") != "active":
            continue
        service_id = service.get("id")
        if "dod_type" not in service:
            errors.add(f"{service_id}: missing dod_type")
        elif service["dod_type"] not in valid_dod:
            allowed = sorted(v for v in valid_dod if v is not None)
            errors.add(
                f"{service_id}: invalid dod_type '{service['dod_type']}' "
                f"(allowed: {allowed} or null)"
            )


def main() -> int:
    try:
        index = load_index()
        dod = load_dod()
        ecosystem = load_ecosystem()
        package = load_package_json()
    except Exception as exc:  # noqa: BLE001 — any load failure is fatal
        print(f"FATAL: could not load canonical sources: {exc}")
        return 2

    errors = Errors()

    if "files" not in index:
        errors.add("index.yaml missing 'files'")
    if ECOSYSTEM_PATH.exists() and "services" not in ecosystem:
        errors.add("ecosystem.yaml missing 'services'")
    if "definitions_of_done" not in dod:
        errors.add("definitions-of-done.yaml missing 'definitions_of_done'")
    if "version" not in package or "name" not in package:
        errors.add("package.json missing version or name")

    try:
        rule_ids = check_rules(index, errors)
    except ValueError as exc:
        print(f"FATAL: {exc}")
        return 2

    check_file_level_meta_002(errors)
    check_services(ecosystem, dod, errors)

    if errors:
        print(f"\nFAIL - {len(errors)} problem(s):")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(
        f"\nOK - {len(rule_ids)} rules across {len(standards_files())} files, "
        f"no issues."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
