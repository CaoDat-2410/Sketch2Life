"""HTTP contract checks for Teacher presentations, without a database."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from starlette.exceptions import HTTPException as StarletteHTTPException

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.infrastructure.lesson_occurrences.presentations import (
    PresentationCommandResult,
    PresentationImageResult,
)
from sketch2life.infrastructure.lesson_occurrences.scope import LessonOccurrenceError
from sketch2life.interfaces.http.be1_runtime import get_verified_adult
from sketch2life.interfaces.http.error_envelope import (
    MESSAGES,
    build_error_body,
    normalize_http_error,
)
from sketch2life.interfaces.http.middleware.bounded_image_upload import (
    _BOUNDED_JSON_ROUTES,
    MAX_PRESENTATION_CREATE_BODY_BYTES,
    MAX_PRESENTATION_READY_BODY_BYTES,
    MAX_PRESENTATION_REVISION_BODY_BYTES,
    MAX_PRESENTATION_SVG_DECISION_BODY_BYTES,
    MAX_PRESENTATION_SVG_DRAFT_BODY_BYTES,
    BoundedImageUploadMiddleware,
)
from sketch2life.interfaces.http.routers.lesson_presentations import (
    get_presentation_service,
    router,
)

NOW = datetime.now(UTC)
OCCURRENCE = "occurrence-1"
DRAFT_ID = "draft-1"
BASE_URL = f"/v1/lesson-occurrences/{OCCURRENCE}/presentation"
_IMAGE_BYTES = b"synthetic presentation image"


def _catalog_media(media_state: str = "CURRENT") -> dict[str, Any]:
    return {
        "slide_id": "slide-1",
        "position": 1,
        "title": "",
        "body_text": "",
        "media": {
            "kind": "SVG_CATALOG",
            "catalog_entry_id": "catalog-1",
            "alt_text": "",
            "canonical_sha256": "a" * 64,
            "placement": "FULL",
        },
        "media_state": media_state,
    }


def _revision_body(*, stale: bool = False, media_stale: bool = False) -> dict[str, Any]:
    return {
        "contract": "LessonPresentationRevisionV1",
        "revision_no": 1,
        "base_revision_no": None,
        "state": "READY",
        "aspect_ratio": "16:9",
        "source_state": "STALE" if stale or media_stale else "CURRENT",
        "stale_reasons": (
            ["PLAN_REVISION_CHANGED"] if stale else ["MEDIA_SOURCE_CHANGED"] if media_stale else []
        ),
        "plan_revision_no": 1,
        "plan_content_hash": "a" * 64,
        "content_hash": "b" * 64,
        "slides": [_catalog_media("STALE" if media_stale else "CURRENT")],
        "created_at": NOW,
        "readied_at": NOW,
    }


def _presentation_body(*, stale: bool = False) -> dict[str, Any]:
    return {
        "contract": "LessonPresentationV1",
        "presentation_id": "presentation-1",
        "occurrence_id": OCCURRENCE,
        "revision": 1,
        "head_revision_no": 1,
        "ready_revision_no": 1,
        "source_state": "STALE" if stale else "CURRENT",
        "stale_reasons": ["PLAN_REVISION_CHANGED"] if stale else [],
        "presentable": not stale,
        "head": _revision_body(stale=stale),
    }


def _svg_draft_body(state: str = "PENDING_REVIEW", revision: int = 1) -> dict[str, Any]:
    return {
        "contract": "PresentationSvgDraftV1",
        "svg_draft_id": DRAFT_ID,
        "state": state,
        "revision": revision,
        "document": {
            "schema_version": "SvgDocumentV1",
            "view_box": "0 0 100 100",
            "paths": [
                {
                    "path_id": "stroke-1",
                    "d": "M 1 1 L 20 20",
                    "fill": "none",
                    "stroke": "#000000",
                    "stroke_width": 2,
                }
            ],
        },
        "preview_svg": "<svg></svg>",
        "canonical_sha256": "c" * 64,
        "generator": {"name": "synthetic", "version": "1"},
        "license_id": "CC0-1.0",
        "created_at": NOW,
        "decided_at": NOW if state != "PENDING_REVIEW" else None,
    }


class PresentationServiceDouble:
    def __init__(self) -> None:
        self.failure: tuple[int, str] | None = None
        self.stale = False
        self.media_stale = False
        self.calls: list[str] = []

    def _call(self, name: str) -> None:
        self.calls.append(name)
        if self.failure is not None:
            raise LessonOccurrenceError(*self.failure)

    def create(self, **_kwargs: Any) -> PresentationCommandResult:
        self._call("create")
        return PresentationCommandResult(_presentation_body(), 201, '"1"')

    def get_presentation(self, **_kwargs: Any) -> dict[str, Any]:
        self._call("get_presentation")
        return _presentation_body(stale=self.stale)

    def create_revision(self, **_kwargs: Any) -> PresentationCommandResult:
        self._call("create_revision")
        return PresentationCommandResult(_presentation_body(), 201, '"2"')

    def get_revision(self, **_kwargs: Any) -> dict[str, Any]:
        self._call("get_revision")
        return _revision_body(media_stale=self.media_stale)

    def mark_ready(self, **_kwargs: Any) -> PresentationCommandResult:
        self._call("mark_ready")
        return PresentationCommandResult(_presentation_body(), 200, '"2"')

    def get_image(self, **_kwargs: Any) -> PresentationImageResult:
        self._call("get_image")
        return PresentationImageResult(
            _IMAGE_BYTES, "image/png", hashlib.sha256(_IMAGE_BYTES).hexdigest()
        )

    def create_svg_draft(self, **_kwargs: Any) -> PresentationCommandResult:
        self._call("create_svg_draft")
        return PresentationCommandResult(_svg_draft_body(), 201, '"1"')

    def get_svg_draft(self, **_kwargs: Any) -> dict[str, Any]:
        self._call("get_svg_draft")
        return _svg_draft_body()

    def decide_svg_draft(self, **_kwargs: Any) -> PresentationCommandResult:
        self._call("decide_svg_draft")
        return PresentationCommandResult(_svg_draft_body("ACCEPTED", 2), 200, '"2"')


def _client(
    service: PresentationServiceDouble | None = None, *, bounded: bool = False
) -> tuple[TestClient, PresentationServiceDouble]:
    app = FastAPI()
    app.include_router(router)
    if bounded:
        app.add_middleware(BoundedImageUploadMiddleware)

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        error_status, code, fields, current_version = normalize_http_error(
            exc.status_code,
            exc.detail,
            idempotency_header_present=bool(request.headers.getlist("Idempotency-Key")),
        )
        request_id = "presentation-contract"
        return JSONResponse(
            status_code=error_status,
            content=build_error_body(
                status=error_status,
                code=code,
                request_id=request_id,
                field_errors=fields,
                current_version=current_version,
            ),
            headers={**(exc.headers or {}), "X-Request-ID": request_id},
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        _request: Request, _exc: RequestValidationError
    ) -> JSONResponse:
        request_id = "presentation-validation"
        return JSONResponse(
            status_code=400,
            content=build_error_body(
                status=400, code="INVALID_REQUEST", request_id=request_id
            ),
        )

    principal = VerifiedPrincipal(
        subject="synthetic-teacher", issuer="synthetic-issuer", roles=frozenset({"teacher"})
    )
    instance = service or PresentationServiceDouble()
    app.dependency_overrides[get_verified_adult] = lambda: principal
    app.dependency_overrides[get_presentation_service] = lambda: instance
    return TestClient(app), instance


def _route_requests() -> list[tuple[str, str, dict[str, Any]]]:
    return [
        (
            "POST",
            BASE_URL,
            {"json": {"seed": "BLANK"}, "headers": {"Idempotency-Key": "create-1"}},
        ),
        ("GET", BASE_URL, {}),
        (
            "POST",
            f"{BASE_URL}/revisions",
            {
                "json": {
                    "operations": [
                        {"op": "UPDATE_SLIDE", "slide_id": "slide-1", "title": "Updated"}
                    ]
                },
                "headers": {"Idempotency-Key": "revision-1", "If-Match": '"1"'},
            },
        ),
        ("GET", f"{BASE_URL}/revisions/1", {}),
        (
            "POST",
            f"{BASE_URL}/revisions/1/ready",
            {"headers": {"Idempotency-Key": "ready-1", "If-Match": '"1"'}},
        ),
        ("GET", f"{BASE_URL}/images/upl_upload-1", {}),
        (
            "POST",
            f"{BASE_URL}/svg-drafts",
            {
                "json": {"plan_activity_id": "activity-1", "subject_text": "butterfly"},
                "headers": {"Idempotency-Key": "svg-create-1"},
            },
        ),
        ("GET", f"{BASE_URL}/svg-drafts/{DRAFT_ID}", {}),
        (
            "POST",
            f"{BASE_URL}/svg-drafts/{DRAFT_ID}/decision",
            {
                "json": {"decision": "ACCEPT"},
                "headers": {"Idempotency-Key": "svg-decision-1", "If-Match": '"1"'},
            },
        ),
    ]


def _send(client: TestClient, method: str, path: str, kwargs: dict[str, Any]):
    return client.request(method, path, **kwargs)


def test_every_route_family_has_a_valid_success_contract() -> None:
    client, _service = _client()
    with client:
        responses = [
            _send(client, method, path, kwargs)
            for method, path, kwargs in _route_requests()
        ]
    assert [response.status_code for response in responses] == [
        201, 200, 201, 200, 200, 200, 201, 200, 200
    ]
    assert responses[0].headers["location"].endswith("/presentation")
    assert responses[2].headers["content-location"].endswith("/revisions/1")
    assert responses[5].headers["x-content-type-options"] == "nosniff"


@pytest.mark.parametrize("error", [(404, "RESOURCE_NOT_FOUND"), (403, "ACTION_NOT_ALLOWED")])
def test_all_route_families_return_uniform_authorization_error_envelopes(
    error: tuple[int, str],
) -> None:
    bodies: list[dict[str, Any]] = []
    for method, path, kwargs in _route_requests():
        service = PresentationServiceDouble()
        service.failure = error
        client, _service = _client(service)
        with client:
            response = _send(client, method, path, kwargs)
        assert response.status_code == error[0]
        bodies.append(response.json())
    expected_fields = {
        "code",
        "message",
        "correlation_id",
        "retryable",
        "retry_after_seconds",
        "field_errors",
        "request_id",
    }
    assert all(body["code"] == error[1] for body in bodies)
    assert all(set(body) == expected_fields for body in bodies)
    assert len({body["message"] for body in bodies}) == 1


@pytest.mark.parametrize("route_index", [0, 2, 4, 6, 8])
def test_idempotency_mismatch_wire_code_on_each_command_route(route_index: int) -> None:
    method, path, kwargs = _route_requests()[route_index]
    service = PresentationServiceDouble()
    service.failure = (400, "INVALID_IDEMPOTENCY_KEY")
    client, _service = _client(service)
    with client:
        response = _send(client, method, path, kwargs)
    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_IDEMPOTENCY_KEY"
    assert response.json()["retryable"] is False


@pytest.mark.parametrize("route_index", [2, 4, 8])
def test_malformed_if_match_is_400_never_422(route_index: int) -> None:
    method, path, kwargs = _route_requests()[route_index]
    kwargs["headers"]["If-Match"] = "weak-or-malformed"
    client, _service = _client()
    with client:
        response = _send(client, method, path, kwargs)
    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_REQUEST"
    assert response.json()["field_errors"] == [
        {"field": "If-Match", "code": "INVALID_FORMAT"}
    ]


@pytest.mark.parametrize("route_index", [2, 4, 8])
def test_missing_if_match_is_400_never_422(route_index: int) -> None:
    method, path, kwargs = _route_requests()[route_index]
    kwargs["headers"].pop("If-Match")
    client, _service = _client()
    with client:
        response = _send(client, method, path, kwargs)
    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_REQUEST"
    assert response.json()["field_errors"] == [{"field": "If-Match", "code": "REQUIRED"}]


@pytest.mark.parametrize("route_index", [0, 2, 4, 6, 8])
def test_missing_idempotency_key_is_400_on_every_command_family(route_index: int) -> None:
    method, path, kwargs = _route_requests()[route_index]
    kwargs["headers"].pop("Idempotency-Key")
    client, _service = _client()
    with client:
        response = _send(client, method, path, kwargs)
    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_REQUEST"


@pytest.mark.parametrize(
    "path,payload,headers",
    [
        (BASE_URL, {"seed": "BLANK", "unknown": True}, {"Idempotency-Key": "body-create"}),
        (
            f"{BASE_URL}/revisions",
            {"operations": [{"op": "NOT_AN_OPERATION"}]},
            {"Idempotency-Key": "body-revision", "If-Match": '"1"'},
        ),
        (
            f"{BASE_URL}/svg-drafts",
            {
                "plan_activity_id": "activity-1",
                "subject_text": "butterfly",
                "unknown": True,
            },
            {"Idempotency-Key": "body-svg-create"},
        ),
        (
            f"{BASE_URL}/svg-drafts/{DRAFT_ID}/decision",
            {"decision": "UNKNOWN"},
            {"Idempotency-Key": "body-svg-decision", "If-Match": '"1"'},
        ),
    ],
)
def test_invalid_body_for_each_schema_route_is_400_not_422(
    path: str, payload: dict[str, Any], headers: dict[str, str]
) -> None:
    client, _service = _client()
    with client:
        response = client.post(path, json=payload, headers=headers)
    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_REQUEST"


@pytest.mark.parametrize(
    "path,payload,headers",
    [
        (BASE_URL, {"seed": "BLANK", "unknown": True}, {"Idempotency-Key": "create-2"}),
        (
            f"{BASE_URL}/revisions",
            {"operations": [{"op": "NOT_AN_OPERATION"}]},
            {"Idempotency-Key": "revision-2", "If-Match": '"1"'},
        ),
    ],
)
def test_unknown_fields_and_bad_operations_are_400_not_422(
    path: str, payload: dict[str, Any], headers: dict[str, str]
) -> None:
    client, _service = _client()
    with client:
        response = client.post(path, json=payload, headers=headers)
    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_REQUEST"


def test_missing_idempotency_key_is_400_not_422() -> None:
    client, _service = _client()
    with client:
        response = client.post(BASE_URL, json={"seed": "BLANK"})
    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_REQUEST"


def test_image_route_has_private_no_store_nosniff_and_inline_headers() -> None:
    client, _service = _client()
    with client:
        response = client.get(f"{BASE_URL}/images/upl_upload-1")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "private, no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["content-disposition"] == "inline"
    assert response.headers["etag"] == f'"{hashlib.sha256(_IMAGE_BYTES).hexdigest()}"'


def test_body_etags_include_aggregate_freshness_and_revision_media_state() -> None:
    service = PresentationServiceDouble()
    client, _service = _client(service)
    with client:
        aggregate_current = client.get(BASE_URL)
        old_aggregate_etag = aggregate_current.headers["etag"]
        service.stale = True
        aggregate_stale = client.get(
            BASE_URL, headers={"If-None-Match": old_aggregate_etag}
        )
        assert aggregate_stale.status_code == 200
        assert aggregate_stale.json()["presentable"] is False
        assert aggregate_stale.json()["source_state"] == "STALE"
        assert aggregate_stale.headers["etag"] != old_aggregate_etag
        aggregate_not_modified = client.get(
            BASE_URL, headers={"If-None-Match": aggregate_stale.headers["etag"]}
        )
        assert aggregate_not_modified.status_code == 304

        revision_current = client.get(f"{BASE_URL}/revisions/1")
        old_revision_etag = revision_current.headers["etag"]
        revision_not_modified = client.get(
            f"{BASE_URL}/revisions/1", headers={"If-None-Match": old_revision_etag}
        )
        assert revision_not_modified.status_code == 304
        service.media_stale = True
        revision_stale = client.get(
            f"{BASE_URL}/revisions/1", headers={"If-None-Match": old_revision_etag}
        )
        assert revision_stale.status_code == 200
        assert revision_stale.json()["source_state"] == "STALE"
        assert revision_stale.json()["slides"][0]["media_state"] == "STALE"
        assert revision_stale.headers["etag"] != old_revision_etag


@pytest.mark.parametrize(
    "path,limit",
    [
        (BASE_URL, MAX_PRESENTATION_CREATE_BODY_BYTES),
        (f"{BASE_URL}/revisions", MAX_PRESENTATION_REVISION_BODY_BYTES),
        (f"{BASE_URL}/revisions/1/ready", MAX_PRESENTATION_READY_BODY_BYTES),
        (f"{BASE_URL}/svg-drafts", MAX_PRESENTATION_SVG_DRAFT_BODY_BYTES),
        (
            f"{BASE_URL}/svg-drafts/{DRAFT_ID}/decision",
            MAX_PRESENTATION_SVG_DECISION_BODY_BYTES,
        ),
    ],
)
def test_each_bounded_request_route_returns_413_over_its_cap(path: str, limit: int) -> None:
    client, _service = _client(bounded=True)
    with client:
        response = client.post(
            path,
            content=b"x" * (limit + 1),
            headers={"Content-Type": "application/json"},
        )
    assert response.status_code == 413
    assert response.json()["code"] == "MEDIA_TOO_LARGE"


def test_bounded_route_registry_contains_exactly_the_five_presentation_commands() -> None:
    presentation_patterns = {
        pattern.pattern
        for method, pattern, _limit, _message in _BOUNDED_JSON_ROUTES
        if method == "POST" and "presentation" in pattern.pattern
    }
    assert len(presentation_patterns) == 5
    assert "PROVIDER_UNAVAILABLE" in MESSAGES
    assert "INVALID_STATE_TRANSITION" in MESSAGES
