#!/usr/bin/env python3
"""Fail when catalog content changed but nothing will cut a version.

The catalog's identity is the version in ``package.json``, which
semantic-release bumps only for ``feat:`` and ``fix:``. Its *content*
comes from ``index.yaml`` and ``standards/*.yaml``. A commit type that
cuts no release can therefore change what the catalog says while leaving
it claiming to be the version already published — and a published version
is immutable, so the release job's publish is refused.

That refusal is correct and it arrives too late: semantic-release has
already tagged and pushed by the time the publish runs, so the mistake
costs a red release and a manual follow-up rather than a failed check.

This runs on every push and says the same thing before merge.

The trap is not obvious, which is why it is worth a check rather than a
convention. "Rewrite a rule's ``check_notes`` to say what its checker
actually does" reads like documentation — the prose is about the rule
rather than changing it. But ``check_notes`` is a compiled field, so the
catalog changes, so the version must. Anything under ``standards/`` or in
``index.yaml`` is catalog content whatever the commit message is about.

Exit codes: 0 clean, 1 content changed with no releasable commit,
2 git could not answer (never fails the build on that alone).

Usage:
    python3 scripts/check_release_type.py
"""

from __future__ import annotations

import re
import subprocess
import sys

from catalog_sources import REPO_ROOT

#: Paths whose content is compiled into the published catalog.
_CATALOG_PATHS = ("index.yaml", "standards/")

#: Conventional-commit types the angular preset turns into a release.
#: ``perf`` is included because the preset cuts a patch for it, even
#: though a perf change to a YAML rule file would be a strange thing.
_RELEASING_TYPES = ("feat", "fix", "perf")

_TYPE_RE = re.compile(r"^(?P<type>[a-z]+)(?:\([^)]*\))?(?P<breaking>!)?:", re.MULTILINE)


def _git(*args: str) -> str | None:
    """Run git in the repo. None when it cannot answer."""
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except Exception:  # noqa: BLE001 — git absent or unrunnable
        return None
    return result.stdout if result.returncode == 0 else None


def last_release_tag() -> str | None:
    """The highest version tag, or None when there are none yet."""
    output = _git("tag", "--sort=-v:refname")
    if output is None:
        return None
    for line in output.splitlines():
        if line.strip():
            return line.strip()
    return None


def catalog_files_changed(since: str) -> list[str]:
    """Catalog-content files touched since a ref."""
    output = _git("diff", "--name-only", f"{since}..HEAD")
    if output is None:
        return []
    return [
        path
        for path in (line.strip() for line in output.splitlines())
        if path.startswith(_CATALOG_PATHS)
    ]


def has_releasing_commit(since: str) -> bool:
    """Whether any commit since a ref will make semantic-release cut one.

    A ``!`` after the type, or a BREAKING CHANGE footer, releases whatever
    the type is — so those count too.
    """
    output = _git("log", "--format=%B%x00", f"{since}..HEAD")
    if output is None:
        return True  # cannot tell; do not fail the build on a git hiccup
    for message in output.split("\0"):
        if "BREAKING CHANGE" in message:
            return True
        match = _TYPE_RE.search(message.strip())
        if not match:
            continue
        if match.group("breaking") or match.group("type") in _RELEASING_TYPES:
            return True
    return False


def main() -> int:
    tag = last_release_tag()
    if tag is None:
        print("OK - no release tag yet; nothing to compare against.")
        return 0

    changed = catalog_files_changed(tag)
    if not changed:
        print(f"OK - no catalog content changed since {tag}.")
        return 0

    if has_releasing_commit(tag):
        print(
            f"OK - catalog content changed since {tag} "
            f"({len(changed)} file(s)) and a releasing commit is present."
        )
        return 0

    listed = "\n".join(f"    {path}" for path in sorted(set(changed)))
    print(
        f"\nFAIL - catalog content changed since {tag} but no commit will cut "
        f"a version:\n{listed}\n\n"
        f"  These files are compiled into the published catalog, so changing "
        f"them changes what the catalog says. A published version is "
        f"immutable, so the release job would be refused — after tagging.\n\n"
        f"  Use fix: (or feat:) for the commit that changes them. A docs: or "
        f"chore: commit is right only when nothing under standards/ or in "
        f"index.yaml is touched, whatever the prose is about: check_notes and "
        f"the statuses block are rule content, not commentary.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
