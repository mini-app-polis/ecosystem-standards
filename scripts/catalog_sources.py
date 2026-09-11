"""Shared loading of the catalog's source files.

Both the validator and the compiler read the same five files. Keeping the
loading in one place means the two cannot disagree about what the catalog
*is* — a validator that passed over a file the compiler then shipped would
be worse than no validator.

Every path is resolved against the repo root, so the scripts run from any
working directory.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent

INDEX_PATH = REPO_ROOT / "index.yaml"
DOD_PATH = REPO_ROOT / "definitions-of-done.yaml"
ECOSYSTEM_PATH = REPO_ROOT / "ecosystem.yaml"
PACKAGE_JSON_PATH = REPO_ROOT / "package.json"
STANDARDS_DIR = REPO_ROOT / "standards"


def load_yaml(path: Path) -> dict[str, Any]:
    """Parse a YAML file into a dict. Raises on parse failure."""
    with path.open() as fh:
        return yaml.safe_load(fh) or {}


def load_index() -> dict[str, Any]:
    """The catalog manifest: dimensions, severities, statuses, schema, files."""
    return load_yaml(INDEX_PATH)


def load_dod() -> dict[str, Any]:
    """Per-artifact definitions of done. Human-facing; not compiled."""
    return load_yaml(DOD_PATH)


def load_ecosystem() -> dict[str, Any]:
    """The service registry.

    Slated for removal — the per-repo ``evaluator.yaml`` is becoming the
    single source of a repo's own context, and this repo is to hold rules
    with no repo or org knowledge. Until then the validator still checks
    ``dod_type`` on active services.
    """
    return load_yaml(ECOSYSTEM_PATH)


def load_package_json() -> dict[str, Any]:
    """package.json — the source of the catalog version (owned by semantic-release)."""
    with PACKAGE_JSON_PATH.open() as fh:
        return json.load(fh)


def standards_files() -> list[Path]:
    """Every rule file, sorted, so output ordering is stable across runs."""
    return sorted(STANDARDS_DIR.glob("*.yaml"))


def rel(path: Path) -> str:
    """Repo-relative POSIX path, as index.yaml spells it."""
    return path.relative_to(REPO_ROOT).as_posix()


def iter_rules() -> list[tuple[Path, dict[str, Any]]]:
    """Every rule in the catalog, paired with the file that declares it.

    A file that fails to parse, or that is missing its ``standards:`` key,
    raises — both scripts treat an unreadable rule file as fatal rather
    than quietly compiling or validating a partial catalog.
    """
    out: list[tuple[Path, dict[str, Any]]] = []
    for path in standards_files():
        data = load_yaml(path)
        rules = data.get("standards")
        if not isinstance(rules, list):
            raise ValueError(f"{rel(path)}: missing or malformed 'standards' key")
        for rule in rules:
            if isinstance(rule, dict):
                out.append((path, rule))
    return out


#: The two markers a checkable rule's ``check_notes`` may open with.
#: META-005 requires one of them; the compiler turns it into a field so the
#: evaluator no longer parses prose at runtime to decide where a rule goes.
CHECK_MODE_MARKERS: dict[str, str] = {
    "DETERMINISTIC CHECK.": "deterministic",
    "LLM CHECK.": "llm",
}


def first_nonblank_line(text: str) -> str:
    """The first line with content, stripped. '' when there is none."""
    for line in (text or "").splitlines():
        if line.strip():
            return line.strip()
    return ""


def classify_check_mode(rule: dict[str, Any]) -> str | None:
    """Resolve a rule's engine from its ``check_notes`` marker.

    Returns ``"deterministic"``, ``"llm"``, or ``None``.

    ``None`` means the rule has no check to route — it is not checkable, or
    its marker is missing. Missing is never silently defaulted to
    deterministic here: META-005 makes that state a CI failure, and a
    compiler that papered over it would restore exactly the ambiguity the
    marker exists to remove. A rule that reaches the evaluator with a null
    ``check_mode`` and ``checkable: true`` is a bug upstream of the
    evaluator, and should look like one.
    """
    if not rule.get("checkable"):
        return None
    first = first_nonblank_line(str(rule.get("check_notes") or ""))
    for marker, mode in CHECK_MODE_MARKERS.items():
        if first.startswith(marker):
            return mode
    return None
