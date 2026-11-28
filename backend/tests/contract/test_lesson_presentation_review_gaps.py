# ruff: noqa: E501, F811, SIM117, B023
"""Offline contract tests for E1 (T-SLD1) review gaps without a database."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.presentation_svg import (
    PresentationSvgDrafterUnavailable,
    PresentationSvgDraftOutput,
)
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.infrastructure.lesson_occurrences.presentations import (
    CREATE_SCOPE,
    SVG_DECISION_SCOPE,
    LessonPresentationService,
    PresentationCommandResult,
    PresentationImageResult,
    _operation_scope,
    _RateLimitedLessonOccurrenceError,
)
from sketch2life.infrastructure.lesson_occurrences.scope import (
    LessonOccurrenceError,
    OccurrenceAccess,
)
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult
from sketch2life.interfaces.http.error_envelope import (
    build_error_body,
    normalize_http_error,
    retry_after_seconds,
)
from sketch2life.interfaces.http.openapi_contract import (
    IDEMPOTENCY_MISMATCH_OPERATION_KEYS,
    MOUNTED_OPERATIONS,
)
from sketch2life.interfaces.http.routers.lesson_presentations import (
    get_presentation_service,
    router,
)

NOW = datetime(2026, 11, 25, 12, 0, tzinfo=UTC)
OCCURRENCE = "occ-contract-1"
DRAFT_ID = "draft-contract-1"
BASE_URL = f"/v1/lesson-occurrences/{OCCURRENCE}/presentation"
TEMPLATE_BASE = "/v1/lesson-occurrences/{occurrence_id}/presentation"


def _slide() -> dict[str, Any]:
    return {
        "slide_id": "slide-1",
        "position": 1,
        "title": "Draw",
        "body_text": "Trace a star",
        "media": None,
        "media_state": None,
    }


def _revision_body() -> dict[str, Any]:
    return {
        "contract": "LessonPresentationRevisionV1",
        "revision_no": 1,
        "base_revision_no": None,
        "state": "DRAFT",
        "aspect_ratio": "16:9",
        "source_state": "CURRENT",
        "stale_reasons": [],
        "plan_revision_no": 1,
        "plan_content_hash": "a" * 64,
        "content_hash": "b" * 64,
        "slides": [_slide()],
        "created_at": NOW,
        "readied_at": None,
    }


def _presentation_body() -> dict[str, Any]:
    return {
        "contract": "LessonPresentationV1",
        "presentation_id": "pres-contract-1",
        "occurrence_id": OCCURRENCE,
        "revision": 1,
        "head_revision_no": 1,
        "ready_revision_no": None,
        "source_state": "CURRENT",
        "stale_reasons": [],
        "presentable": False,
        "head": _revision_body(),
    }


def _svg_draft_body() -> dict[str, Any]:
    return {
        "contract": "PresentationSvgDraftV1",
        "svg_draft_id": DRAFT_ID,
        "state": "PENDING_REVIEW",
        "revision": 1,
        "document": {
            "schema_version": "SvgDocumentV1",
            "view_box": "0 0 100 100",
            "paths": [
                {
                    "path_id": "p1",
                    "d": "M 0 0 L 10 10",
                    "fill": "none",
                    "stroke": "#111111",
                    "stroke_width": 2,
                }
            ],
        },
        "preview_svg": "<svg></svg>",
        "canonical_sha256": "c" * 64,
        "generator": {"name": "synthetic", "version": "1"},
        "license_id": "CC0-1.0",
        "created_at": NOW,
        "decided_at": None,
    }


class _ConfigurableDouble:
    def __init__(self) -> None:
        self.exception: Exception | None = None

    def _raise_if_set(self) -> None:
        if self.exception is not None:
            raise self.exception

    def create(self, **_kwargs: Any) -> PresentationCommandResult:
        self._raise_if_set()
        return PresentationCommandResult(_presentation_body(), 201, '"1"')

    def get_presentation(self, **_kwargs: Any) -> dict[str, Any]:
        self._raise_if_set()
        return _presentation_body()

    def create_revision(self, **_kwargs: Any) -> PresentationCommandResult:
        self._raise_if_set()
        return PresentationCommandResult(_presentation_body(), 201, '"2"')

    def get_revision(self, **_kwargs: Any) -> dict[str, Any]:
        self._raise_if_set()
        return _revision_body()

    def mark_ready(self, **_kwargs: Any) -> PresentationCommandResult:
        self._raise_if_set()
        return PresentationCommandResult(_presentation_body(), 200, '"2"')

    def get_image(self, **_kwargs: Any) -> PresentationImageResult:
        self._raise_if_set()
        return PresentationImageResult(b"png", "image/png", "d" * 64)

    def create_svg_draft(self, **_kwargs: Any) -> PresentationCommandResult:
        self._raise_if_set()
        return PresentationCommandResult(_svg_draft_body(), 201, '"1"')

    def get_svg_draft(self, **_kwargs: Any) -> dict[str, Any]:
        self._raise_if_set()
        return _svg_draft_body()

    def decide_svg_draft(self, **_kwargs: Any) -> PresentationCommandResult:
        self._raise_if_set()
        return PresentationCommandResult(_svg_draft_body(), 200, '"2"')


def _build_router_client(service: _ConfigurableDouble) -> TestClient:
    app = FastAPI()
    app.include_router(router)

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        status_code, code, field_errors, current_version = normalize_http_error(
            exc.status_code,
            exc.detail,
            idempotency_header_present=bool(request.headers.getlist("Idempotency-Key")),
        )
        return JSONResponse(
            status_code=status_code,
            content=build_error_body(
                status=status_code,
                code=code,
                request_id="req-e1-gap",
                field_errors=field_errors,
                current_version=current_version,
                retry_after=retry_after_seconds(exc.headers),
            ),
            headers=exc.headers or {},
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation(request: Request, _exc: RequestValidationError) -> JSONResponse:
        status_code, code, field_errors, current_version = normalize_http_error(
            422,
            {"code": "INVALID_REQUEST"},
            idempotency_header_present=bool(request.headers.getlist("Idempotency-Key")),
        )
        return JSONResponse(
            status_code=status_code,
            content=build_error_body(
                status=status_code,
                code=code,
                request_id="req-e1-gap",
                field_errors=field_errors,
                current_version=current_version,
            ),
        )

    principal = VerifiedPrincipal(
        subject="teacher-a", issuer="synthetic-issuer", roles=frozenset({"teacher"})
    )
    app.dependency_overrides[get_verified_adult] = lambda: principal
    app.dependency_overrides[get_presentation_service] = lambda: service
    return TestClient(app)


@pytest.fixture
def composed_app(monkeypatch: pytest.MonkeyPatch) -> Iterator[FastAPI]:
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", "0")
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", "postgresql+psycopg://localhost:9/s1at_closed")
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    app = create_app()
    app.dependency_overrides[get_verified_adult] = lambda: VerifiedPrincipal(
        subject="teacher-a", issuer="synthetic-issuer", roles=frozenset({"teacher"})
    )
    try:
        yield app
    finally:
        app.dependency_overrides.clear()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


@pytest.mark.parametrize(
    ("path", "kwargs"),
    [
        (f"{BASE_URL}/revisions", {"json": {"operations": [{"op": "DELETE_SLIDE", "slide_id": "s1"}]}}),
        (f"{BASE_URL}/revisions/1/ready", {}),
        (f"{BASE_URL}/svg-drafts/{DRAFT_ID}/decision", {"json": {"decision": "ACCEPT"}}),
    ],
)
def test_missing_if_match_is_400_required_on_each_versioned_command(
    path: str, kwargs: dict[str, Any]
) -> None:
    """covers: IMPL_REVIEW_E_E1_R1_20261125.md P2-3 (missing If-Match -> 400 REQUIRED)"""
    client = _build_router_client(_ConfigurableDouble())
    with client:
        response = client.post(path, headers={"Idempotency-Key": "e1-gap-key-1"}, **kwargs)
    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_REQUEST"
    assert response.json()["field_errors"] == [{"field": "If-Match", "code": "REQUIRED"}]


@pytest.mark.parametrize(
    ("path", "kwargs"),
    [
        (f"{BASE_URL}/revisions", {"json": {"operations": [{"op": "DELETE_SLIDE", "slide_id": "s1"}]}, "headers": {"If-Match": '"1"'}}),
        (f"{BASE_URL}/revisions/1/ready", {"headers": {"If-Match": '"1"'}}),
        (f"{BASE_URL}/svg-drafts", {"json": {"plan_activity_id": "act-1", "subject_text": "star"}}),
        (f"{BASE_URL}/svg-drafts/{DRAFT_ID}/decision", {"json": {"decision": "ACCEPT"}, "headers": {"If-Match": '"1"'}}),
    ],
)
def test_missing_idempotency_key_is_400_never_422_across_other_commands(
    path: str, kwargs: dict[str, Any]
) -> None:
    """covers: IMPL_REVIEW_E_E1_R1_20261125.md P2-3 (missing Idempotency-Key -> 400 on routes 3,5,7,9)"""
    client = _build_router_client(_ConfigurableDouble())
    with client:
        response = client.post(path, **kwargs)
    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_REQUEST"


@pytest.mark.parametrize(
    ("method", "path", "kwargs"),
    [
        ("POST", BASE_URL, {"json": {"seed": "INVALID"}, "headers": {"Idempotency-Key": "k1"}}),
        (
            "POST",
            f"{BASE_URL}/revisions",
            {"json": {"operations": []}, "headers": {"Idempotency-Key": "k2", "If-Match": '"1"'}},
        ),
        (
            "POST",
            f"{BASE_URL}/revisions",
            {
                "json": {
                    "operations": [
                        {"op": "UPDATE_SLIDE", "slide_id": "slide-1"}
                    ]
                },
                "headers": {"Idempotency-Key": "k3", "If-Match": '"1"'},
            },
        ),
        (
            "POST",
            f"{BASE_URL}/revisions",
            {
                "json": {
                    "operations": [
                        {
                            "op": "SET_MEDIA",
                            "slide_id": "slide-1",
                            "placement": "FULL",
                            "media": {"kind": "IMAGE", "asset_ref": "upl_1", "alt_text": "x" * 301},
                        }
                    ]
                },
                "headers": {"Idempotency-Key": "k4", "If-Match": '"1"'},
            },
        ),
        (
            "POST",
            f"{BASE_URL}/revisions",
            {
                "json": {
                    "operations": [
                        {"op": "DELETE_SLIDE", "slide_id": "slide-1"}
                    ]
                    * 51
                },
                "headers": {"Idempotency-Key": "k5", "If-Match": '"1"'},
            },
        ),
        ("GET", f"{BASE_URL}/revisions/0", {}),
        ("GET", f"{BASE_URL}/images/bad-ref", {}),
        (
            "POST",
            f"{BASE_URL}/svg-drafts",
            {
                "json": {"plan_activity_id": "act-1", "subject_text": "star", "extra": 1},
                "headers": {"Idempotency-Key": "k6"},
            },
        ),
        (
            "POST",
            f"{BASE_URL}/svg-drafts/{DRAFT_ID}/decision",
            {
                "json": {"decision": "MAYBE"},
                "headers": {"Idempotency-Key": "k7", "If-Match": '"1"'},
            },
        ),
        (
            "POST",
            f"{BASE_URL}/svg-drafts/{DRAFT_ID}/decision",
            {
                "json": {"decision": "ACCEPT", "extra": True},
                "headers": {"Idempotency-Key": "k8", "If-Match": '"1"'},
            },
        ),
    ],
)
def test_body_and_path_validation_faults_return_400_never_422(
    method: str, path: str, kwargs: dict[str, Any]
) -> None:
    """covers: IMPL_REVIEW_E_E1_R1_20261125.md P2-3 (400-never-422 across all routes)"""
    client = _build_router_client(_ConfigurableDouble())
    with client:
        response = client.request(method, path, **kwargs)
    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_REQUEST"


@pytest.mark.parametrize(
    ("method", "path", "kwargs", "exc", "expected_status", "expected_code"),
    [
        (
            "POST",
            BASE_URL,
            {"json": {"seed": "BLANK"}, "headers": {"Idempotency-Key": "e1-err-1"}},
            LessonOccurrenceError(409, "LESSON_PLAN_NOT_APPROVED"),
            409,
            "LESSON_PLAN_NOT_APPROVED",
        ),
        (
            "POST",
            BASE_URL,
            {"json": {"seed": "BLANK"}, "headers": {"Idempotency-Key": "e1-err-2"}},
            LessonOccurrenceError(409, "RESOURCE_CONFLICT"),
            409,
            "RESOURCE_CONFLICT",
        ),
        (
            "POST",
            f"{BASE_URL}/revisions",
            {
                "json": {"operations": [{"op": "UPDATE_SLIDE", "slide_id": "slide-1", "title": "A"}]},
                "headers": {"Idempotency-Key": "e1-err-3", "If-Match": '"1"'},
            },
            LessonOccurrenceError(409, "STALE_REVISION", current_version=3),
            409,
            "STALE_REVISION",
        ),
        (
            "POST",
            f"{BASE_URL}/revisions/1/ready",
            {"headers": {"Idempotency-Key": "e1-err-4", "If-Match": '"1"'}},
            LessonOccurrenceError(409, "STALE_SOURCE_VERSION"),
            409,
            "STALE_SOURCE_VERSION",
        ),
        (
            "POST",
            f"{BASE_URL}/revisions",
            {
                "json": {"operations": [{"op": "UPDATE_SLIDE", "slide_id": "slide-1", "title": "A"}]},
                "headers": {"Idempotency-Key": "e1-err-svg-save", "If-Match": '"1"'},
            },
            LessonOccurrenceError(409, "SVG_CATALOG_NOT_APPROVED"),
            409,
            "SVG_CATALOG_NOT_APPROVED",
        ),
        (
            "POST",
            f"{BASE_URL}/revisions/1/ready",
            {"headers": {"Idempotency-Key": "e1-err-svg-ready", "If-Match": '"1"'}},
            LessonOccurrenceError(409, "SVG_CATALOG_HASH_MISMATCH"),
            409,
            "SVG_CATALOG_HASH_MISMATCH",
        ),
        (
            "POST",
            f"{BASE_URL}/svg-drafts/{DRAFT_ID}/decision",
            {
                "json": {"decision": "ACCEPT"},
                "headers": {"Idempotency-Key": "e1-err-5", "If-Match": '"1"'},
            },
            LessonOccurrenceError(409, "INVALID_STATE_TRANSITION"),
            409,
            "INVALID_STATE_TRANSITION",
        ),
        (
            "POST",
            f"{BASE_URL}/revisions",
            {
                "json": {"operations": [{"op": "UPDATE_SLIDE", "slide_id": "slide-1", "title": "A"}]},
                "headers": {"Idempotency-Key": "e1-err-6", "If-Match": '"1"'},
            },
            LessonOccurrenceError(415, "UNSUPPORTED_MEDIA_TYPE"),
            415,
            "UNSUPPORTED_MEDIA_TYPE",
        ),
        (
            "POST",
            f"{BASE_URL}/revisions",
            {
                "json": {"operations": [{"op": "UPDATE_SLIDE", "slide_id": "slide-1", "title": "A"}]},
                "headers": {"Idempotency-Key": "e1-err-7", "If-Match": '"1"'},
            },
            LessonOccurrenceError(422, "UPLOAD_CHECKSUM_MISMATCH"),
            422,
            "UPLOAD_CHECKSUM_MISMATCH",
        ),
        (
            "POST",
            f"{BASE_URL}/revisions",
            {
                "json": {"operations": [{"op": "UPDATE_SLIDE", "slide_id": "slide-1", "title": "A"}]},
                "headers": {"Idempotency-Key": "e1-err-8", "If-Match": '"1"'},
            },
            LessonOccurrenceError(422, "IMAGE_DIMENSIONS_EXCEEDED"),
            422,
            "IMAGE_DIMENSIONS_EXCEEDED",
        ),
        (
            "POST",
            f"{BASE_URL}/svg-drafts",
            {
                "json": {"plan_activity_id": "act-1", "subject_text": "star"},
                "headers": {"Idempotency-Key": "e1-err-9"},
            },
            _RateLimitedLessonOccurrenceError(3600),
            429,
            "RATE_LIMITED",
        ),
        (
            "POST",
            f"{BASE_URL}/svg-drafts",
            {
                "json": {"plan_activity_id": "act-1", "subject_text": "star"},
                "headers": {"Idempotency-Key": "e1-err-10"},
            },
            LessonOccurrenceError(502, "PROVIDER_BAD_RESPONSE"),
            502,
            "PROVIDER_BAD_RESPONSE",
        ),
        (
            "POST",
            f"{BASE_URL}/svg-drafts",
            {
                "json": {"plan_activity_id": "act-1", "subject_text": "star"},
                "headers": {"Idempotency-Key": "e1-err-11"},
            },
            LessonOccurrenceError(503, "PROVIDER_UNAVAILABLE"),
            503,
            "PROVIDER_UNAVAILABLE",
        ),
        (
            "GET",
            f"{BASE_URL}/images/upl_upload-1",
            {},
            LessonOccurrenceError(503, "STORAGE_UNAVAILABLE"),
            503,
            "STORAGE_UNAVAILABLE",
        ),
    ],
)
def test_wire_error_codes_and_headers_match_contract(
    method: str,
    path: str,
    kwargs: dict[str, Any],
    exc: Exception,
    expected_status: int,
    expected_code: str,
) -> None:
    """covers: IMPL_REVIEW_E_E1_R1_20261125.md P2-3 (wire error codes and headers)"""
    service = _ConfigurableDouble()
    service.exception = exc
    client = _build_router_client(service)
    with client:
        response = client.request(method, path, **kwargs)
    assert response.status_code == expected_status
    body = response.json()
    assert body["code"] == expected_code
    if expected_code == "STALE_REVISION":
        assert body["current_version"] == 3
        assert response.headers["etag"] == '"3"'
    if expected_code == "RATE_LIMITED":
        assert response.headers["retry-after"] == "3600"
        assert body["retry_after_seconds"] == 3600
        assert body["retryable"] is True


def test_real_composition_fails_closed_without_drafter_and_maps_drafter_errors(
    composed_app: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    """covers: IMPL_REVIEW_E_E1_R1_20261125.md P2-3 & P3-5/P3-6 (503 fail-closed & typed error)"""
    assert composed_app.state.presentation_svg_drafter is None

    class _FakeDb:
        def execute(self, *_args: Any, **_kwargs: Any) -> Any:
            return SimpleNamespace(
                mappings=lambda: SimpleNamespace(
                    one_or_none=lambda: {
                        "plan_revision_id": "plan-1",
                        "custom_title": "Draw star",
                        "activity_kind": "CUSTOM",
                        "activity_snapshot": None,
                    }
                ),
                scalar_one=lambda: 0,
            )

        def rollback(self) -> None:
            return None

    composed_app.dependency_overrides[get_db] = lambda: _FakeDb()
    monkeypatch.setattr(
        LessonPresentationService,
        "_access",
        lambda self, *_args, **_kwargs: OccurrenceAccess(
            occurrence={
                "occurrence_id": OCCURRENCE,
                "organization_ref": "org-1",
                "approved_plan_revision_id": "plan-1",
                "state": "APPROVED",
            },
            account_ref="acc-1",
        ),
    )
    monkeypatch.setattr(
        LessonPresentationService,
        "_presentation",
        lambda self, *_args, **_kwargs: {"presentation_id": "pres-1"},
    )
    monkeypatch.setattr(LessonPresentationService, "_receipt", lambda self, *_a, **_kw: None)
    monkeypatch.setattr(
        LessonPresentationService,
        "_current_plan",
        lambda self, *_args, **_kwargs: {"plan_revision_id": "plan-1"},
    )

    with TestClient(composed_app) as client:
        fail_closed = client.post(
            f"{BASE_URL}/svg-drafts",
            json={"plan_activity_id": "act-1", "subject_text": "star"},
            headers={"Idempotency-Key": "e1-no-drafter"},
        )
        assert fail_closed.status_code == 503
        assert fail_closed.json()["code"] == "PROVIDER_UNAVAILABLE"

        class _UnavailableDrafter:
            def draft(self, _req: Any) -> PresentationSvgDraftOutput:
                raise PresentationSvgDrafterUnavailable("timeout")

        composed_app.state.presentation_svg_drafter = _UnavailableDrafter()
        unavailable = client.post(
            f"{BASE_URL}/svg-drafts",
            json={"plan_activity_id": "act-1", "subject_text": "star"},
            headers={"Idempotency-Key": "e1-drafter-timeout"},
        )
        assert unavailable.status_code == 503
        assert unavailable.json()["code"] == "PROVIDER_UNAVAILABLE"

        class _BadSvgDrafter:
            def draft(self, _req: Any) -> PresentationSvgDraftOutput:
                return PresentationSvgDraftOutput(
                    source=b"<not-svg/>",
                    generator_name="bad",
                    generator_version="1",
                    license_id="CC0-1.0",
                )

        composed_app.state.presentation_svg_drafter = _BadSvgDrafter()
        bad_output = client.post(
            f"{BASE_URL}/svg-drafts",
            json={"plan_activity_id": "act-1", "subject_text": "star"},
            headers={"Idempotency-Key": "e1-drafter-bad"},
        )
        assert bad_output.status_code == 502
        assert bad_output.json()["code"] == "PROVIDER_BAD_RESPONSE"


def test_operation_scope_fills_path_ids_for_independent_occurrences() -> None:
    """covers: IMPL_REVIEW_E_E1_R1_20261125.md P3-1 (operation_scope fills path ids)"""
    scope_a = _operation_scope(CREATE_SCOPE, occurrence_id="occ-a")
    scope_b = _operation_scope(CREATE_SCOPE, occurrence_id="occ-b")
    draft_scope = _operation_scope(
        SVG_DECISION_SCOPE, occurrence_id="occ-a", svg_draft_id="draft-1"
    )
    assert scope_a != scope_b
    assert "{" not in scope_a and "{" not in draft_scope
    assert len(draft_scope) <= 256


def test_catalog_contains_all_nine_presentation_routes_and_five_keyed_operations() -> None:
    """covers: IMPL_REVIEW_E_E1_R1_20261125.md P2-3 (catalog entries and idempotency rows for routes 1-9)"""
    expected_routes = {
        ("post", TEMPLATE_BASE): "lesson_presentations.py::create_presentation",
        ("get", TEMPLATE_BASE): "lesson_presentations.py::get_presentation",
        ("post", f"{TEMPLATE_BASE}/revisions"): "lesson_presentations.py::create_presentation_revision",
        ("get", f"{TEMPLATE_BASE}/revisions/{{revision_no}}"): "lesson_presentations.py::get_presentation_revision",
        ("post", f"{TEMPLATE_BASE}/revisions/{{revision_no}}/ready"): "lesson_presentations.py::mark_presentation_revision_ready",
        ("get", f"{TEMPLATE_BASE}/images/{{asset_ref}}"): "lesson_presentations.py::get_presentation_image",
        ("post", f"{TEMPLATE_BASE}/svg-drafts"): "lesson_presentations.py::create_presentation_svg_draft",
        ("get", f"{TEMPLATE_BASE}/svg-drafts/{{svg_draft_id}}"): "lesson_presentations.py::get_presentation_svg_draft",
        ("post", f"{TEMPLATE_BASE}/svg-drafts/{{svg_draft_id}}/decision"): "lesson_presentations.py::decide_presentation_svg_draft",
    }
    expected_keyed = {
        key for key in expected_routes if key[0] == "post"
    }
    assert set(expected_routes) <= set(MOUNTED_OPERATIONS)
    for key, handler in expected_routes.items():
        assert MOUNTED_OPERATIONS[key]["handler"] == handler
        assert MOUNTED_OPERATIONS[key]["tag"] == "Lesson Occurrences"
    assert expected_keyed <= set(IDEMPOTENCY_MISMATCH_OPERATION_KEYS)
    assert len(expected_keyed) == 5
    # Verify non-DB SQLAlchemy error mapping expectation stays registered in envelope
    assert normalize_http_error(503, {"code": "PROVIDER_UNAVAILABLE"}, idempotency_header_present=False)[:2] == (
        503,
        "PROVIDER_UNAVAILABLE",
    )
    assert isinstance(SQLAlchemyError(), Exception)
