#!/usr/bin/env python3
"""
scripts/check_drift.py

Cross-repo drift detector for ecosystem-standards ↔ evaluator-cog.

Usage:
    python scripts/check_drift.py \
        --standards-dir <path-to-ecosystem-standards> \
        --evaluator-dir <path-to-evaluator-cog>

Reads:
  - All standards/*.yaml files in ecosystem-standards, extracts rules
    where checkable: true and reads their `id` fields.
  - evaluator-cog/src/evaluator_cog/engine/deterministic.py, extracts
    CHECK_ID constants or @check(id=...) decorator arguments.

Diffs the two sets and reports:
  - unimplemented_standards: checkable rules with no corresponding check
  - orphaned_checks: evaluator checks with no backing standard

Submits findings to api-kaianolevine-com if drift is detected.
Exits 0 always (drift is advisory, not a hard CI failure).
"""

import argparse
import json
import os
import re
import sys
import tomllib
from pathlib import Path



# ── Rule extraction ────────────────────────────────────────────────────────


def extract_checkable_rule_ids(standards_dir: Path) -> dict[str, str]:
    """
    Walk all standards/*.yaml files and return a dict of
    {rule_id: file_path} for every rule with checkable: true.
    """
    import yaml

    checkable = {}
    standards_path = standards_dir / "standards"
    for yaml_file in sorted(standards_path.glob("*.yaml")):
        with open(yaml_file) as f:
            data = yaml.safe_load(f)
        if not data or "standards" not in data:
            continue
        for rule in data["standards"]:
            if rule.get("checkable") is True:
                checkable[rule["id"]] = str(yaml_file.relative_to(standards_dir))
    return checkable


def extract_implemented_check_ids(evaluator_dir: Path) -> dict[str, str]:
    """
    Parse evaluator-cog's deterministic.py and return a dict of
    {check_id: location} for every implemented check.

    Supports two declaration styles:
      1. CHECK_ID = "STD-CI-001"          (module-level constant)
      2. @check(id="STD-CI-001")          (decorator argument)
      3. check_id = "STD-CI-001"          (inline constant, any case)
    """
    implemented = {}

    # Primary location — adjust this path if the evaluator restructures.
    deterministic_path = (
        evaluator_dir
        / "src"
        / "evaluator_cog"
        / "engine"
        / "deterministic.py"
    )

    if not deterministic_path.exists():
        print(
            f"WARNING: deterministic.py not found at {deterministic_path}. "
            "Cannot extract implemented check IDs.",
            file=sys.stderr,
        )
        return implemented

    source = deterministic_path.read_text()

    # Pattern 1: CHECK_ID = "STD-XXX-000" or check_id = "STD-XXX-000"
    for match in re.finditer(
        r'(?i)check_id\s*=\s*["\']([A-Z]+-\d+)["\']', source
    ):
        rule_id = match.group(1)
        implemented[rule_id] = str(deterministic_path)

    # Pattern 2: @check(id="STD-XXX-000")
    for match in re.finditer(
        r'@check\s*\(\s*id\s*=\s*["\']([A-Z]+-\d+)["\']', source
    ):
        rule_id = match.group(1)
        implemented[rule_id] = str(deterministic_path)

    return implemented


# ── Finding construction ───────────────────────────────────────────────────


def build_finding(
    unimplemented: list[str],
    orphaned: list[str],
    triggered_by: str,
    standards_version: str,
    evaluator_version: str,
) -> dict | None:
    """
    Build a pipeline_evaluations finding payload if drift exists.
    Returns None if no drift detected.
    """
    if not unimplemented and not orphaned:
        return None

    severity = "error" if orphaned else "warn"
    parts = []
    if unimplemented:
        parts.append(
            f"{len(unimplemented)} checkable standard(s) have no evaluator implementation: "
            + ", ".join(unimplemented)
        )
    if orphaned:
        parts.append(
            f"{len(orphaned)} evaluator check(s) have no backing standard: "
            + ", ".join(orphaned)
        )

    return {
        "source": "standards_drift",
        "dimension": "standards_currency",
        "severity": severity,
        "repo": "ecosystem-standards",
        "title": f"Standards/evaluator drift detected — {triggered_by}",
        "summary": " | ".join(parts),
        "details": {
            "unimplemented_standards": unimplemented,
            "orphaned_checks": orphaned,
            "triggered_by": triggered_by,
            "standards_version": standards_version,
            "evaluator_version_checked": evaluator_version,
        },
        "standards_version": standards_version,
    }


# ── API submission ─────────────────────────────────────────────────────────


def submit_finding(finding: dict, api_base_url: str, api_key: str) -> None:
    import requests

    url = f"{api_base_url}/v1/pipeline-evaluations"
    headers = {
        "Content-Type": "application/json",
        "X-Internal-API-Key": api_key,
    }
    resp = requests.post(url, headers=headers, json=finding, timeout=15)
    resp.raise_for_status()
    print(f"Finding submitted: {resp.status_code}")


def read_version(path: Path, key: str = "version") -> str:
    """Read a version string from package.json, index.yaml, or pyproject.toml."""
    try:
        if path.suffix == ".toml":
            with open(path, "rb") as f:
                data = tomllib.load(f)
            project = data.get("project", {})
            if key in project:
                return str(project[key])
            tool_poetry = data.get("tool", {}).get("poetry", {})
            if key in tool_poetry:
                return str(tool_poetry[key])
            return "unknown"
        if path.suffix == ".json":
            with open(path) as f:
                data = json.load(f)
            return str(data.get(key, "unknown"))
        import yaml

        with open(path) as f:
            data = yaml.safe_load(f)
        return str(data.get(key, "unknown"))
    except Exception:
        return "unknown"


# ── Main ───────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="Drift detector: standards ↔ evaluator-cog")
    parser.add_argument("--standards-dir", required=True, type=Path)
    parser.add_argument("--evaluator-dir", required=True, type=Path)
    args = parser.parse_args()

    standards_dir: Path = args.standards_dir
    evaluator_dir: Path = args.evaluator_dir

    # Versions for finding metadata
    standards_version = read_version(standards_dir / "package.json")
    evaluator_version = read_version(evaluator_dir / "pyproject.toml", key="version")

    triggered_by = os.environ.get("TRIGGERED_BY", "manual")
    dry_run = os.environ.get("DRY_RUN", "false").lower() == "true"
    api_base_url = os.environ.get("API_BASE_URL", "")
    api_key = os.environ.get("INTERNAL_API_KEY", "")

    print(f"Standards version:  {standards_version}")
    print(f"Evaluator version:  {evaluator_version}")
    print(f"Triggered by:       {triggered_by}")
    print(f"Dry run:            {dry_run}")
    print()

    # Extract rule sets
    checkable = extract_checkable_rule_ids(standards_dir)
    implemented = extract_implemented_check_ids(evaluator_dir)

    checkable_ids = set(checkable.keys())
    implemented_ids = set(implemented.keys())

    unimplemented = sorted(checkable_ids - implemented_ids)
    orphaned = sorted(implemented_ids - checkable_ids)

    # Report
    print(f"Checkable standards:       {len(checkable_ids)}")
    print(f"Implemented checks:        {len(implemented_ids)}")
    print(f"Unimplemented standards:   {len(unimplemented)}")
    print(f"Orphaned checks:           {len(orphaned)}")

    if unimplemented:
        print("\nUnimplemented (standard exists, no check):")
        for r in unimplemented:
            print(f"  WARN  {r}  ({checkable[r]})")

    if orphaned:
        print("\nOrphaned (check exists, no standard):")
        for r in orphaned:
            print(f"  ERROR {r}  ({implemented[r]})")

    if not unimplemented and not orphaned:
        print("\n✓ No drift detected.")
        return

    # Build and submit finding
    finding = build_finding(
        unimplemented=unimplemented,
        orphaned=orphaned,
        triggered_by=triggered_by,
        standards_version=standards_version,
        evaluator_version=evaluator_version,
    )

    print(f"\nFinding payload:\n{json.dumps(finding, indent=2)}")

    if dry_run:
        print("\nDry run — skipping API submission.")
        return

    if not api_base_url or not api_key:
        print(
            "WARNING: API_BASE_URL or INTERNAL_API_KEY not set. Skipping submission.",
            file=sys.stderr,
        )
        return

    submit_finding(finding, api_base_url, api_key)


if __name__ == "__main__":
    main()
