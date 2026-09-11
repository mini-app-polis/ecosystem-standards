#!/usr/bin/env python3
"""Publish the compiled catalog to the API. Run from the release job.

Compiles in-process rather than reading a `catalog.json` left by an earlier
step. The artifact and the version have to agree, and the version only
exists after semantic-release has bumped `package.json` — a file compiled
before that carries the previous version, and publishing it would silently
attribute a release's rules to the release before it.

**Runs after semantic-release, and only on `main`.** By then the working
tree holds the bumped `package.json`, so compiling reads the version just
cut.

**A no-release run is a no-op, not a special case.** When there were no
releasable commits, `package.json` is unchanged and the catalog it compiles
to is already published — the API answers 200 with `created: false` and
stores nothing. That falls out of publishes being immutable rather than
needing a branch here.

**A failed publish fails the job.** semantic-release has already tagged and
pushed by this point, so a silent failure leaves a released version that
nothing can be evaluated against — the catalog would simply be one release
behind, and every finding would pin the wrong rubric without anything
saying so. Re-running the job republishes safely.

Stdlib only. This repo declares no Python dependencies beyond PyYAML for
the catalog scripts, and a publisher is not a reason to grow that.

Environment:
    KAIANO_API_BASE_URL           e.g. https://api.kaianolevine.com
    ECOSYSTEM_STANDARDS_API_KEY   repository-level secret, this repo only

Usage:
    python3 scripts/publish_catalog.py [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import subprocess
import urllib.error
import urllib.request

from compile_catalog import compile_catalog

#: Path the API serves the catalog store at.
_ENDPOINT = "/v1/standards/catalog"

#: Generous, because the payload is a few hundred kilobytes and the cost of
#: a spurious timeout here is a released version with no catalog.
_TIMEOUT_SECONDS = 60

#: Identifies this client to the API's edge.
#:
#: Not cosmetic. The API sits behind Cloudflare, whose Browser Integrity
#: Check blocks requests whose User-Agent reads as unidentified automation —
#: urllib's default is one of those, and a publish with it is refused at the
#: edge with a 1010 that never reaches the API. A named product agent is
#: what the check is asking for, and it makes the caller legible in access
#: logs besides.
_USER_AGENT = (
    "ecosystem-standards-publisher/{version} "
    "(+https://github.com/mini-app-polis/ecosystem-standards)"
)

#: Markers that identify a response as the edge rejecting the request rather
#: than the API answering it.
_EDGE_BLOCK_MARKERS = (
    "error code: 10",
    "cloudflare",
    "just a moment",
    "<!doctype html",
)


def latest_tag() -> str | None:
    """The highest version tag in the repository, without its `v` prefix.

    Deliberately the newest tag in the repo rather than the newest tag
    *reachable from HEAD*. Reachability is useless here: on a development
    branch, and on a re-run that checked out the pre-release SHA, the
    reachable tag and `package.json` are both the previous release and
    agree with each other — so a reachability check would pass in exactly
    the two cases this guard exists to catch.

    None when there are no tags or git is unavailable — treated as "cannot
    tell" rather than "does not match", since refusing to publish because
    git was unreadable would be its own outage.
    """
    try:
        result = subprocess.run(
            ["git", "tag", "--sort=-v:refname"],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except Exception:  # noqa: BLE001 — git absent or unrunnable
        return None
    if result.returncode != 0:
        return None
    for line in result.stdout.splitlines():
        tag = line.strip().lstrip("v")
        if tag:
            return tag
    return None


def check_version_matches_tag(version: str) -> str | None:
    """Return an error message when the compiled version is not the released one.

    A published version is immutable, so publishing the wrong content under
    a version is not a mistake that can be corrected afterwards — the 409
    that protects the store also locks the error in. The two ways to make
    that mistake are both mismatches between the working tree and the
    release:

      - Running this from a development branch. `package.json` there still
        carries the last released version while the rule files have moved
        on, so it would store post-release rules under a released version.
      - Re-running a failed workflow. GitHub checks out the SHA that
        triggered the run, not the release commit semantic-release pushed
        afterwards, so the tree carries the *previous* version's
        package.json.

    Both look like ordinary runs. Comparing the compiled version against
    the latest tag catches them, because in a correct release the release
    commit is the tagged one.
    """
    tag = latest_tag()
    if tag is None:
        return None
    if tag != version:
        return (
            f"compiled version {version} does not match the latest tag "
            f"{tag}. This usually means the working tree is not the release "
            f"commit — a development branch, or a re-run that checked out "
            f"the pre-release SHA. Publishing would store the wrong content "
            f"under a released version, and a published version cannot be "
            f"corrected. Pass --allow-version-mismatch if this is "
            f"deliberate."
        )
    return None


def publish(base_url: str, api_key: str, catalog: dict) -> tuple[int, dict]:
    """POST the catalog. Returns (status, parsed body)."""
    body = json.dumps(catalog).encode("utf-8")
    request = urllib.request.Request(
        base_url.rstrip("/") + _ENDPOINT,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": _USER_AGENT.format(version=catalog.get("version", "0")),
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
            return response.status, json.loads(response.read() or b"{}")
    except urllib.error.HTTPError as exc:
        raw = exc.read() or b"{}"
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, {"raw": raw.decode("utf-8", "replace")[:500]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compile and report what would be published, without posting.",
    )
    parser.add_argument(
        "--allow-version-mismatch",
        action="store_true",
        help=(
            "Publish even when the compiled version is not the latest tag. "
            "Only for a deliberate backfill."
        ),
    )
    args = parser.parse_args(argv)

    try:
        catalog = compile_catalog()
    except Exception as exc:  # noqa: BLE001 — nothing publishable, stop here
        print(f"FATAL: could not compile catalog: {exc}", file=sys.stderr)
        return 2

    version = catalog["version"]
    rule_count = catalog["rule_count"]

    if args.dry_run:
        mismatch = check_version_matches_tag(version)
        if mismatch:
            print(f"DRY RUN - would REFUSE: {mismatch}")
        else:
            print(f"DRY RUN - would publish catalog v{version} ({rule_count} rules)")
        return 0

    if not args.allow_version_mismatch:
        mismatch = check_version_matches_tag(version)
        if mismatch:
            print(f"FATAL: {mismatch}", file=sys.stderr)
            return 2

    base_url = os.environ.get("KAIANO_API_BASE_URL", "").strip()
    api_key = os.environ.get("ECOSYSTEM_STANDARDS_API_KEY", "").strip()
    missing = [
        name
        for name, value in (
            ("KAIANO_API_BASE_URL", base_url),
            ("ECOSYSTEM_STANDARDS_API_KEY", api_key),
        )
        if not value
    ]
    if missing:
        # Named explicitly rather than left to a 401. An absent credential
        # and a rejected one are different problems and the message should
        # say which this is.
        print(f"FATAL: missing environment: {', '.join(missing)}", file=sys.stderr)
        return 2

    try:
        status, payload = publish(base_url, api_key, catalog)
    except Exception as exc:  # noqa: BLE001 — transport failure
        print(f"FATAL: publishing v{version} failed: {exc}", file=sys.stderr)
        return 1

    if status == 200:
        data = payload.get("data") or {}
        if data.get("created"):
            print(f"OK - published catalog v{version} ({rule_count} rules)")
        else:
            print(
                f"OK - catalog v{version} was already published with identical "
                f"content ({rule_count} rules); nothing stored"
            )
        return 0

    if status == 409:
        # The released version exists with different rules. Either a rule
        # file changed without a version bump, or someone republished by
        # hand. Neither is fixable by retrying, and neither should be
        # resolved by overwriting — the published version is what existing
        # findings are pinned to.
        print(
            f"FATAL: standards v{version} is already published with different "
            f"content. A published version is immutable; cut a new version "
            f"rather than changing this one.",
            file=sys.stderr,
        )
        return 1

    raw = str(payload.get("raw", "")) if isinstance(payload, dict) else ""
    if raw and any(marker in raw.lower() for marker in _EDGE_BLOCK_MARKERS):
        # An HTML body means the API never saw this request. Saying so is
        # the whole value of the branch: a 403 from the edge and a 403 from
        # authorization are the same status code and entirely different
        # problems, and dumping the challenge page leaves whoever reads the
        # log to work that out themselves.
        print(
            f"FATAL: publishing v{version} was blocked at the edge with "
            f"{status} before reaching the API — an HTML challenge or block "
            f"page came back, not a JSON response. This is not an "
            f"authentication failure. Check the User-Agent this client sends "
            f"and the WAF rules on the API hostname.",
            file=sys.stderr,
        )
        return 1

    error = (payload.get("error") or {}) if isinstance(payload, dict) else {}
    print(
        f"FATAL: publishing v{version} returned {status}: "
        f"{error.get('code', '?')} {error.get('message', payload)}",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
