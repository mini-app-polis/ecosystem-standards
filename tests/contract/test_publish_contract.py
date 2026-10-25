"""Live contract suite for the catalog publish call (TEST-016, ADR-0012).

scripts/publish_catalog.py makes one outbound call: POST
/v1/standards/catalog on api-kaianolevine-com, from the release job on
main. A drift between what it sends and what the API accepts surfaces only
there — after semantic-release has tagged, when a failed publish leaves a
released version with no catalog. This suite checks the same call against
the deployed development API before that, on every push to dev and every
dev API deploy:

  - the compiled catalog carries every field the API's published request
    schema requires, with the type it declares, and the response schema
    still has the ``created`` flag the publisher reads;
  - the publisher's own request — its User-Agent, headers and body, built by
    ``publish()`` itself — reaches the API rather than being blocked at the
    Cloudflare edge, and an unrecognised key is refused with 401 in the
    error envelope the publisher's failure branch reads;
  - with a dev publisher key (optional), the key is accepted and the API
    validates the body: a catalog with rule_count 0 is refused with 422
    before the handler runs, so nothing is stored.

Read-only throughout. The two posts are refused before the handler — the
first by authentication, the second by validation — so the dev store never
gains a version. A real publish is never made: published versions are
immutable, and dev reads production's catalog anyway.

It never points at production. Under kaianolevine.com only the hosts in
ALLOWED_DEV_HOSTS are called, so a production host is refused without a
change here — the same guard as common-python-utils' and the sites' harnesses.

Configuration:
    CONTRACT_API_URL                  the development API's base URL;
                                      contract.yml defaults it to
                                      https://dev-api.kaianolevine.com
    ECOSYSTEM_STANDARDS_API_KEY_DEV   optional; the publisher machine's key
                                      on the dev API. Without it the
                                      validation test skips.

Run by hand with:
    CONTRACT_API_URL=https://dev-api.kaianolevine.com \\
        python3 -m unittest discover -s tests/contract -v

Stdlib plus PyYAML (for the compiler), like the scripts it checks.
"""

from __future__ import annotations

import json
import os
import sys
import unittest
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from compile_catalog import compile_catalog  # noqa: E402
from publish_catalog import _ENDPOINT, _USER_AGENT, publish  # noqa: E402

PRODUCTION_DOMAIN = "kaianolevine.com"
ALLOWED_DEV_HOSTS = frozenset({"dev-api.kaianolevine.com"})

#: An API key no machine holds. Authentication refuses it before the handler.
_UNKNOWN_KEY = "contract-suite-not-a-real-key"


def resolve_api_url() -> str:
    raw = os.environ.get("CONTRACT_API_URL", "").strip()
    if not raw:
        raise RuntimeError(
            "CONTRACT_API_URL is not set — point it at the development API."
        )
    url = urllib.parse.urlsplit(raw)
    host = url.hostname or ""
    local = host in {"localhost", "127.0.0.1"}
    if url.scheme != "https" and not local:
        raise RuntimeError(
            f"CONTRACT_API_URL must be https (or a local API), got {url.scheme}"
        )
    under_production = host == PRODUCTION_DOMAIN or host.endswith(
        f".{PRODUCTION_DOMAIN}"
    )
    if under_production and host not in ALLOWED_DEV_HOSTS:
        raise RuntimeError(
            f"Refusing to run against {host}: only "
            f"{', '.join(sorted(ALLOWED_DEV_HOSTS))} may be called under "
            f"{PRODUCTION_DOMAIN}."
        )
    return f"{url.scheme}://{url.netloc}"


API = resolve_api_url()
CATALOG = compile_catalog()


def _get_json(path: str) -> Any:
    request = urllib.request.Request(
        API + path,
        headers={
            "Accept": "application/json",
            "User-Agent": _USER_AGENT.format(version=CATALOG["version"]),
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read())


def _resolve(spec: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    """Follow $ref (and a single-member allOf) to the schema it names."""
    while True:
        if "$ref" in schema:
            name = schema["$ref"].rsplit("/", 1)[-1]
            schema = spec["components"]["schemas"][name]
        elif len(schema.get("allOf", [])) == 1:
            schema = schema["allOf"][0]
        else:
            return schema


_JSON_TYPES = {
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "array": list,
    "object": dict,
}


class PublishContract(unittest.TestCase):
    spec: dict[str, Any]
    operation: dict[str, Any]

    @classmethod
    def setUpClass(cls) -> None:
        cls.spec = _get_json("/openapi.json")
        path = _ENDPOINT
        operation = cls.spec.get("paths", {}).get(path, {}).get("post")
        if operation is None:
            raise AssertionError(f"the API publishes no POST {path}")
        cls.operation = operation

    def test_catalog_satisfies_the_request_schema(self) -> None:
        body = self.operation["requestBody"]["content"]["application/json"]
        schema = _resolve(self.spec, body["schema"])
        properties = schema.get("properties", {})
        for field in schema.get("required", []):
            with self.subTest(field=field):
                self.assertIn(
                    field, CATALOG, f"the compiled catalog has no {field}"
                )
                declared = _resolve(self.spec, properties.get(field, {}))
                expected = _JSON_TYPES.get(declared.get("type", ""))
                if expected is None:
                    continue
                value = CATALOG[field]
                self.assertIsInstance(
                    value,
                    expected,
                    f"{field} should be {declared['type']}, "
                    f"got {type(value).__name__}",
                )
                self.assertFalse(
                    declared["type"] == "integer" and isinstance(value, bool),
                    f"{field} should be an integer, got a boolean",
                )
                if "minimum" in declared:
                    self.assertGreaterEqual(value, declared["minimum"], field)
                if "maxLength" in declared:
                    self.assertLessEqual(len(value), declared["maxLength"], field)
        # The API rejects a count that disagrees with the rules it carries.
        self.assertEqual(CATALOG["rule_count"], len(CATALOG["rules"]))

    def test_response_carries_the_created_flag(self) -> None:
        ok = self.operation["responses"]["200"]["content"]["application/json"]
        envelope = _resolve(self.spec, ok["schema"])
        data = _resolve(self.spec, envelope["properties"]["data"])
        self.assertIn(
            "created",
            data.get("properties", {}),
            "the publish receipt no longer says whether it stored the version",
        )

    def test_unknown_key_is_refused_in_the_error_envelope(self) -> None:
        status, payload = publish(API, _UNKNOWN_KEY, CATALOG)
        raw = str(payload.get("raw", "")) if isinstance(payload, dict) else ""
        self.assertFalse(
            raw,
            f"the publisher's request was answered with a non-JSON body "
            f"({status}) — likely blocked at the edge: {raw[:200]}",
        )
        self.assertEqual(status, 401, f"answered {status}: {payload}")
        self.assertIsInstance(payload.get("error", {}).get("code"), str, payload)

    def test_dev_key_is_accepted_and_the_body_validated(self) -> None:
        key = os.environ.get("ECOSYSTEM_STANDARDS_API_KEY_DEV", "").strip()
        if not key:
            self.skipTest("ECOSYSTEM_STANDARDS_API_KEY_DEV is not set")
        invalid = {**CATALOG, "rule_count": 0}
        status, payload = publish(API, key, invalid)
        self.assertNotIn(status, (401, 403), f"the dev key was refused: {payload}")
        self.assertEqual(status, 422, f"answered {status}: {payload}")
        self.assertEqual(payload.get("error", {}).get("code"), "validation_error")


if __name__ == "__main__":
    unittest.main()
