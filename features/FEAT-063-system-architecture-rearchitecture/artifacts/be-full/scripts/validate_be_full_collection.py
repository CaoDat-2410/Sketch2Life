"""Validate one-to-one parity between the runtime OpenAPI and Bruno files."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
COLLECTION = ROOT / "bruno"
SCHEMA_PATH = ROOT / "openapi.runtime.json"
COVERAGE_PATH = ROOT / "API_COVERAGE.csv"
METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"}


def runtime_operations(schema: dict[str, Any]) -> set[tuple[str, str]]:
    result: set[tuple[str, str]] = set()
    for path, path_item in schema.get("paths", {}).items():
        if not isinstance(path_item, dict):
            continue
        for method in path_item:
            method_upper = method.upper()
            if method_upper in METHODS:
                key = (method_upper, path)
                if key in result:
                    raise ValueError(f"duplicate OpenAPI method/path: {key}")
                result.add(key)
    return result


def fail(message: str) -> None:
    raise SystemExit(f"BE full Bruno validation FAILED: {message}")


def main() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    with COVERAGE_PATH.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    active = [row for row in rows if row["status"] == "mounted"]
    candidates = [row for row in rows if row["status"] == "unmounted-candidate"]
    expected = runtime_operations(schema)
    mapped = [(row["method"], row["path"]) for row in active]
    if len(active) != len(expected):
        fail(f"active coverage rows={len(active)}, runtime operations={len(expected)}")
    if len(set(mapped)) != len(mapped):
        fail("duplicate active method/path mapping")
    if set(mapped) != expected:
        fail(
            "coverage/runtime mismatch: "
            f"missing={sorted(expected - set(mapped))}; "
            f"extra={sorted(set(mapped) - expected)}"
        )
    operation_ids = [row["operation_id"] for row in active]
    if len(set(operation_ids)) != len(operation_ids):
        fail("duplicate operationId coverage row")
    if len(candidates) != 11:
        fail(f"expected 11 unmounted candidate rows, found {len(candidates)}")
    if any(row["request_file"] for row in candidates):
        fail("an unmounted candidate was assigned a runnable request")

    requested_files = [row["request_file"] for row in active]
    if len(set(requested_files)) != len(requested_files):
        fail("multiple operations map to the same Bruno request file")
    actual_files = {
        path.relative_to(COLLECTION).as_posix()
        for path in (COLLECTION / "requests").rglob("*.bru")
    }
    if actual_files != set(requested_files):
        fail(
            "request-file mismatch: "
            f"missing={sorted(set(requested_files) - actual_files)}; "
            f"extra={sorted(actual_files - set(requested_files))}"
        )

    all_bru_text: list[str] = []
    for row in active:
        path = COLLECTION / Path(row["request_file"])
        text = path.read_text(encoding="utf-8")
        all_bru_text.append(text)
        method = row["method"].lower()
        if not re.search(rf"(?m)^{method}\s*\{{", text):
            fail(
                f"{row['request_file']} does not contain the declared {method.upper()} method"
            )
        expected_path = re.sub(r"\{([^{}]+)\}", r"{{\1}}", row["path"])
        url_match = re.search(r"(?m)^\s*url:\s*(.+)$", text)
        if not url_match or not url_match.group(1).startswith(
            "{{baseUrl}}" + expected_path
        ):
            fail(f"request URL does not match OpenAPI path: {row['request_file']}")
        if "url: http://" in text or "url: https://" in text:
            fail(
                "request uses a literal endpoint instead of the local baseUrl: "
                f"{row['request_file']}"
            )
        if row["auth_required"] == "true":
            if "auth: bearer" not in text or "token: {{bearerToken}}" not in text:
                fail(f"bearer auth placeholder missing: {row['request_file']}")
        elif "auth: none" not in text:
            fail(
                f"unauthenticated operation does not explicitly disable auth: {row['request_file']}"
            )
        media_types = set(filter(None, row["request_content_types"].split(";")))
        if "application/json" in media_types and "body:json {" not in text:
            fail(f"JSON request body missing: {row['request_file']}")
        if "multipart/form-data" in media_types and "body:multipart-form {" not in text:
            fail(f"multipart request body missing: {row['request_file']}")
        if (
            row["side_effect_class"] == "provider-capable"
            and "PROVIDER-CAPABLE" not in text
        ):
            fail(
                f"provider-capable request is not visibly marked: {row['request_file']}"
            )
        if not row["expected_response_statuses"]:
            fail(f"no response contract recorded for {row['operation_id']}")

    env_path = COLLECTION / "environments" / "local.bru"
    env_text = env_path.read_text(encoding="utf-8")
    env_values = dict(
        re.findall(r"(?m)^\s*([A-Za-z_][A-Za-z0-9_]*):\s*(.*?)\s*$", env_text)
    )
    if env_values.get("baseUrl") != "http://127.0.0.1:8000":
        fail("local environment baseUrl must target 127.0.0.1:8000")
    for key, value in env_values.items():
        if key != "baseUrl" and not value.startswith("REPLACE_WITH_"):
            fail(f"local environment value must remain an obvious placeholder: {key}")
    all_text = "\n".join(
        [
            env_text,
            *all_bru_text,
            COVERAGE_PATH.read_text(encoding="utf-8-sig"),
            SCHEMA_PATH.read_text(encoding="utf-8"),
            (COLLECTION / "bruno.json").read_text(encoding="utf-8"),
            (ROOT / "README.md").read_text(encoding="utf-8"),
        ]
    )
    if re.search(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]", all_text):
        fail("absolute Windows filesystem path found in collection")
    if re.search(
        r"https?://(?!127\.0\.0\.1(?::\d+)?(?=/|\s|$|[`),;])|localhost(?::\d+)?(?=/|\s|$|[`),;])|\[::1\](?::\d+)?(?=/|\s|$|[`),;]))",
        all_text,
    ):
        fail("non-loopback URL found in a request or environment")

    profile_counts = Counter(
        profile
        for row in active
        for profile in filter(None, row["profiles"].split("|"))
    )
    if len(expected) != 136 or len(schema.get("paths", {})) != 122:
        fail(
            f"runtime schema count changed: {len(expected)} operations / "
            f"{len(schema.get('paths', {}))} paths"
        )
    if not all(
        (profile_counts[name] == count)
        for name, count in {
            "combined-default": 122,
            "combined-main-demo-storyrun": 133,
            "combined-local-storage": 125,
            "classroom": 57,
            "demo": 35,
        }.items()
    ):
        fail(f"unexpected profile exposure counts: {dict(profile_counts)}")

    print(
        "BE full Bruno validation PASS: "
        f"{len(active)} mounted operations / {len(actual_files)} requests, "
        f"{len(candidates)} unmounted candidates excluded, "
        f"{len(schema.get('paths', {}))} paths; profile counts={dict(profile_counts)}"
    )


if __name__ == "__main__":
    main()
