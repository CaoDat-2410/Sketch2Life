"""CONV-1 unit tests for the shared §9.8 error envelope (FEAT-066 D-066-68, D-066-71)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from sketch2life.interfaces.http import error_envelope as envelope

SRC = Path(__file__).resolve().parents[2] / "src" / "sketch2life"
SCANNED_MODULES = (
    "interfaces/http/routers/be1_common.py",
    "interfaces/http/routers/be1_runtime.py",
    "interfaces/http/routers/be1_sessions.py",
    "interfaces/http/routers/be1_registry.py",
    "interfaces/http/routers/be1_canvas.py",
    "interfaces/http/routers/be1_artifacts.py",
    "interfaces/http/routers/be1_records.py",
    "interfaces/http/routers/pilot_assistance.py",
    "interfaces/http/routers/lesson_library.py",
    "interfaces/http/routers/platform_admin_accounts.py",
    "interfaces/http/routers/auth_registration.py",
    "interfaces/http/routers/teacher_ai.py",
    "interfaces/http/be1_runtime.py",
    "infrastructure/lesson_library/service.py",
)
SIX_FIELDS = {
    "code",
    "message",
    "correlation_id",
    "retryable",
    "retry_after_seconds",
    "field_errors",
}


def _literal_codes(tree: ast.AST) -> set[tuple[int | None, str]]:
    found: set[tuple[int | None, str]] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = (
            func.id
            if isinstance(func, ast.Name)
            else func.attr if isinstance(func, ast.Attribute) else None
        )
        if name in {"failure", "fail"} and len(node.args) >= 2:
            status_node, code_node = node.args[0], node.args[1]
            status = status_node.value if isinstance(status_node, ast.Constant) else None
            if isinstance(code_node, ast.Constant) and isinstance(code_node.value, str):
                found.add((status if isinstance(status, int) else None, code_node.value))
        if name == "HTTPException":
            status = None
            for keyword in node.keywords:
                if keyword.arg == "status_code" and isinstance(keyword.value, ast.Constant):
                    status = keyword.value.value
            for keyword in node.keywords:
                if keyword.arg == "detail" and isinstance(keyword.value, ast.Dict):
                    for key, value in zip(keyword.value.keys, keyword.value.values, strict=True):
                        if (
                            isinstance(key, ast.Constant)
                            and key.value == "code"
                            and isinstance(value, ast.Constant)
                            and isinstance(value.value, str)
                        ):
                            found.add((status if isinstance(status, int) else None, value.value))
    return found


def test_envelope_always_has_the_six_fields_and_request_id_alias() -> None:
    body = envelope.build_error_body(status=404, code="RESOURCE_NOT_FOUND", request_id="req-1")
    assert set(body) >= SIX_FIELDS
    assert body["correlation_id"] == body["request_id"] == "req-1"
    assert body["retryable"] is False
    assert body["retry_after_seconds"] is None
    assert body["field_errors"] is None
    assert "current_version" not in body


@pytest.mark.parametrize("status", [429, 502, 503, 504])
def test_retryable_statuses(status: int) -> None:
    body = envelope.build_error_body(status=status, code="X_CODE", request_id="r")
    assert body["retryable"] is True


def test_retry_after_is_read_only_from_digit_headers() -> None:
    assert envelope.retry_after_seconds({"Retry-After": "30"}) == 30
    assert envelope.retry_after_seconds({"retry-after": "soon"}) is None
    assert envelope.retry_after_seconds(None) is None


def test_current_version_only_with_stale_revision() -> None:
    stale = envelope.build_error_body(
        status=409, code="STALE_REVISION", request_id="r", current_version=7
    )
    other = envelope.build_error_body(
        status=409, code="INVALID_STATE_TRANSITION", request_id="r", current_version=7
    )
    assert stale["current_version"] == 7
    assert "current_version" not in other


@pytest.mark.parametrize(
    ("status", "code", "expected"),
    [
        (401, "AUTHENTICATION_REQUIRED", "AUTH_REQUIRED"),
        (401, "UNAUTHENTICATED", "AUTH_REQUIRED"),
        (401, "INVALID_IDENTITY_TOKEN", "INVALID_TOKEN"),
        (403, "FORBIDDEN", "ACTION_NOT_ALLOWED"),
        (404, "NOT_FOUND", "RESOURCE_NOT_FOUND"),
        (404, "CLASS_NOT_FOUND", "RESOURCE_NOT_FOUND"),
        (404, "JOIN_UNAVAILABLE", "JOIN_UNAVAILABLE"),
        (409, "CONFLICT", "INVALID_STATE_TRANSITION"),
        (409, "INVALID_TRANSITION", "INVALID_STATE_TRANSITION"),
        (409, "IDEMPOTENCY_KEY_REUSED", "IDEMPOTENCY_KEY_REUSED"),
        (413, "REQUEST_TOO_LARGE", "REQUEST_TOO_LARGE"),
        (503, "DEPENDENCY_UNAVAILABLE", "PROVIDER_UNAVAILABLE"),
        (418, None, "INVALID_REQUEST"),
        (507, None, "INTERNAL_SERVER_ERROR"),
        (405, None, "ACTION_NOT_ALLOWED"),
    ],
)
def test_code_mapping(status: int, code: str | None, expected: str) -> None:
    assert envelope.map_code(status, code) == expected


def test_validation_422_is_remapped_to_400() -> None:
    assert envelope.normalize_http_error(
        422, {"code": "INVALID_REQUEST", "message": "route text"}, idempotency_header_present=False
    ) == (400, "INVALID_REQUEST", None, None)
    assert envelope.normalize_http_error(
        422, "string detail", idempotency_header_present=False
    ) == (400, "INVALID_REQUEST", None, None)


@pytest.mark.parametrize(("present", "field_code"), [(False, "REQUIRED"), (True, "INVALID_FORMAT")])
def test_idempotency_key_required_becomes_invalid_request(present: bool, field_code: str) -> None:
    status, code, field_errors, _ = envelope.normalize_http_error(
        422, {"code": "IDEMPOTENCY_KEY_REQUIRED"}, idempotency_header_present=present
    )
    assert (status, code) == (400, "INVALID_REQUEST")
    assert field_errors == [{"field": "Idempotency-Key", "code": field_code}]


def test_domain_422_codes_keep_their_status() -> None:
    status, code, _, _ = envelope.normalize_http_error(
        422, {"code": "MALWARE_DETECTED"}, idempotency_header_present=False
    )
    assert (status, code) == (422, "MALWARE_DETECTED")


def test_route_field_errors_are_whitelisted() -> None:
    detail = {
        "code": "INVALID_REQUEST",
        "field_errors": [
            {"field": "If-Match", "code": "REQUIRED"},
            {"field": "x", "code": "ECHOED_INPUT"},
            {"field": "y" * 121, "code": "REQUIRED"},
            "not-a-mapping",
        ],
    }
    _, _, field_errors, _ = envelope.normalize_http_error(
        400, detail, idempotency_header_present=False
    )
    assert field_errors == [{"field": "If-Match", "code": "REQUIRED"}]


def test_messages_are_vietnamese_table_values_never_route_text() -> None:
    body = envelope.build_error_body(status=404, code="RESOURCE_NOT_FOUND", request_id="r")
    assert body["message"] == envelope.MESSAGES["RESOURCE_NOT_FOUND"]
    unknown = envelope.build_error_body(status=409, code="SOME_DOMAIN_CODE", request_id="r")
    assert unknown["message"] == envelope.STATUS_MESSAGES[409]
    odd = envelope.build_error_body(status=451, code="X", request_id="r")
    assert odd["message"]


def test_every_scanned_code_literal_is_classified() -> None:
    """A new code fails this test until it is worded or listed as status-message-only."""
    unclassified: list[str] = []
    for relative in SCANNED_MODULES:
        tree = ast.parse((SRC / relative).read_text(encoding="utf-8"))
        for status, code in _literal_codes(tree):
            public = (
                envelope.normalize_http_error(
                    status, {"code": code}, idempotency_header_present=False
                )[1]
                if status
                else code
            )
            if code in envelope.GENERIC_CODE_MAP or code in envelope.MESSAGES:
                continue
            if public == "RESOURCE_NOT_FOUND" or public in envelope.MESSAGES:
                continue
            if code in envelope.STATUS_MESSAGE_ONLY:
                continue
            unclassified.append(f"{relative}: {status} {code}")
    assert unclassified == []


def test_conv1_families() -> None:
    assert envelope.is_conv1_path("/api/be1/v1/organizations/x/classes")
    assert envelope.is_conv1_path("/api/lesson-library/v1/me/lessons")
    assert envelope.is_conv1_path("/api/platform-admin/v1/accounts")
    assert envelope.is_conv1_path("/api/auth/v1/me")
    assert envelope.is_conv1_path("/api/teacher/v1/organizations/o/ai/lesson-plan-suggestions")
    assert not envelope.is_conv1_path("/api/parent/v1/ai/drawing-understandings")
    assert not envelope.is_conv1_path("/v1/parent/profiles")
    assert not envelope.is_conv1_path("/v1/story-runs")
    assert not envelope.is_conv1_path("/v1/sessions/s/media/image")
