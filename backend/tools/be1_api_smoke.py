"""Read-only HTTP smoke checks for a running BE1 API and PostgreSQL database."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def request_json(
    base_url: str,
    path: str,
    *,
    method: str = "GET",
    request_id: str | None = None,
    body: bytes | None = None,
) -> tuple[int, Mapping[str, str], object]:
    headers = {"Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    if request_id:
        headers["X-Request-ID"] = request_id
    request = Request(
        f"{base_url.rstrip('/')}{path}", data=body, headers=headers, method=method
    )
    try:
        response = urlopen(request, timeout=10)
    except HTTPError as exc:
        response = exc
    except URLError as exc:
        raise RuntimeError(f"Could not reach BE1 API: {exc.reason}") from None
    with response:
        body = response.read()
        try:
            payload: object = json.loads(body) if body else None
        except json.JSONDecodeError:
            payload = {"non_json_response": body[:256].decode("utf-8", errors="replace")}
        return response.status, response.headers, payload


def assert_error_response(
    *, status: int, headers: Mapping[str, str], payload: object, expected_status: int, code: str
) -> None:
    if status != expected_status or not isinstance(payload, dict):
        raise RuntimeError(f"Expected HTTP {expected_status} JSON error; got {status}: {payload!r}")
    if "application/json" not in headers.get("Content-Type", ""):
        raise RuntimeError("BE1 error response is missing application/json content type")
    if payload.get("code") != code:
        raise RuntimeError(f"Expected error code {code}; got {payload!r}")
    response_request_id = payload.get("request_id")
    if (
        not isinstance(response_request_id, str)
        or headers.get("X-Request-ID") != response_request_id
    ):
        raise RuntimeError("Error body request_id did not match the X-Request-ID response header")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    results: list[dict[str, object]] = []
    status, headers, payload = request_json(args.base_url, "/api/be1/v1/health")
    if status != 200 or payload != {
        "status": "ready",
        "database": "postgresql",
        "api": "be1-v1",
    }:
        raise RuntimeError(f"BE1 health/DB probe failed: HTTP {status}, {payload!r}")
    if not headers.get("X-Request-ID"):
        raise RuntimeError("Successful BE1 response is missing X-Request-ID")
    results.append({"case": "postgresql_health", "status": status, "response": payload})

    supplied_request_id = "be1-smoke-unauthenticated"
    status, headers, payload = request_json(
        args.base_url,
        "/api/be1/v1/organizations/smoke-scope/classes",
        request_id=supplied_request_id,
    )
    assert_error_response(
        status=status,
        headers=headers,
        payload=payload,
        expected_status=401,
        code="AUTHENTICATION_REQUIRED",
    )
    if payload.get("request_id") != supplied_request_id:
        raise RuntimeError("BE1 API did not preserve a valid caller-supplied request ID")
    results.append({"case": "missing_bearer_token", "status": status, "response": payload})

    status, headers, payload = request_json(
        args.base_url,
        "/api/be1/v1/organizations/smoke-scope/sessions",
        method="POST",
        body=b"{",
    )
    assert_error_response(
        status=status,
        headers=headers,
        payload=payload,
        expected_status=422,
        code="REQUEST_VALIDATION_FAILED",
    )
    results.append({"case": "malformed_json", "status": status, "response": payload})

    status, headers, payload = request_json(args.base_url, "/api/be1/v1/no-such-resource")
    assert_error_response(
        status=status,
        headers=headers,
        payload=payload,
        expected_status=404,
        code="NOT_FOUND",
    )
    results.append({"case": "unknown_be1_route", "status": status, "response": payload})

    status, _headers, openapi = request_json(args.base_url, "/openapi.json")
    if status != 200 or not isinstance(openapi, dict):
        raise RuntimeError("OpenAPI document is unavailable")
    paths = openapi.get("paths")
    schemas = openapi.get("components", {}).get("schemas", {})
    if not isinstance(paths, dict) or not isinstance(schemas, dict):
        raise RuntimeError("OpenAPI document is missing paths or schemas")
    be1_paths = [path for path in paths if path.startswith("/api/be1/v1/")]
    if not be1_paths or "Be1Error" not in schemas:
        raise RuntimeError("OpenAPI is missing BE1 routes or the standard Be1Error schema")
    health_operation = paths.get("/api/be1/v1/health", {}).get("get", {})
    if "503" not in health_operation.get("responses", {}):
        raise RuntimeError("BE1 health does not document its unavailable-DB response")
    session_create = paths.get("/api/be1/v1/organizations/{organization_id}/sessions", {}).get(
        "post", {}
    )
    if "422" not in session_create.get("responses", {}):
        raise RuntimeError("BE1 commands do not document validation error responses")
    class_list = paths.get("/api/be1/v1/organizations/{organization_id}/classes", {}).get(
        "get", {}
    )
    session_transition = paths.get(
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/start", {}
    ).get("post", {})
    if "401" not in class_list.get("responses", {}) or "409" not in session_transition.get(
        "responses", {}
    ):
        raise RuntimeError("OpenAPI is missing authentication or conflict responses")
    results.append(
        {
            "case": "openapi_contract",
            "status": status,
            "be1_path_count": len(be1_paths),
            "error_schema": "Be1Error",
        }
    )

    print(json.dumps({"result": "passed", "checks": results}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(json.dumps({"result": "failed", "message": str(exc)}, indent=2), file=sys.stderr)
        raise SystemExit(1) from None
