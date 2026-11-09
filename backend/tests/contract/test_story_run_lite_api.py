from __future__ import annotations

import json
import re
import socket
import threading
import time
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest
import uvicorn
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine

from sketch2life.application.ports.story_run_lite import (
    CommandResult,
    CoreAssetAdmissionPort,
    ImageNormalizerPort,
    ImageSafetyScannerPort,
    StoryRunLiteVisionPort,
    StoryRunReferencePort,
)
from sketch2life.application.services.story_run_lite import StoryRunLiteService
from sketch2life.domain.story_run_lite import StoryRunLiteError, parse_etag_version
from sketch2life.infrastructure.story_run_lite.quarantine import QuarantineStore
from sketch2life.infrastructure.story_run_lite.repository import SqlStoryRunLiteRepository
from sketch2life.interfaces.http.routers.story_run_lite import router
from sketch2life.interfaces.http.story_run_lite_app import create_app


class _StubService:
    def __init__(self) -> None:
        self.part: tuple[object, ...] | None = None

    def create_run(self, payload, *, idempotency_key: str) -> CommandResult:
        return CommandResult(
            201,
            {
                "profile": payload.profile_ref,
                "child_age_months": payload.child_age_months,
                "key": idempotency_key,
            },
            1,
        )

    def create_upload(self, payload, *, idempotency_key: str) -> CommandResult:
        return CommandResult(201, {"upload_ref": payload.target_ref, "key": idempotency_key}, 1)

    def get_run(self, run_id: str) -> CommandResult:
        if run_id == "explode":
            raise RuntimeError("synthetic unexpected handler failure")
        return CommandResult(200, {"run_ref": run_id}, 1)

    def generate_story_revision(
        self, *, run_id: str, if_match: str | None, idempotency_key: str, **_values: object
    ) -> CommandResult:
        parse_etag_version(if_match)
        return CommandResult(
            201,
            {
                "run_ref": run_id,
                "story_revision_ref": "00000000-0000-0000-0000-000000000042",
                "key": idempotency_key,
            },
            2,
        )

    def get_story_revision(self, *, run_id: str, story_revision_id: str) -> CommandResult:
        return CommandResult(200, {"run_ref": run_id, "story_revision_ref": story_revision_id}, 2)

    def confirm_story_revision(
        self,
        *,
        run_id: str,
        story_revision_id: str,
        if_match: str | None,
        idempotency_key: str,
        **_values: object,
    ) -> CommandResult:
        parse_etag_version(if_match)
        return CommandResult(
            200,
            {"run_ref": run_id, "story_revision_ref": story_revision_id, "key": idempotency_key},
            3,
        )

    def attach_asset(self, *, if_match: str | None, **_values: object) -> CommandResult:
        parse_etag_version(if_match)
        if _values.get("run_id") == "conflict":
            raise StoryRunLiteError(409, "STALE_REVISION", "The run revision is stale.")
        return CommandResult(202, {"run_ref": "run-42"}, 12)

    def confirm_subject(self, *, if_match: str | None, **_values: object) -> CommandResult:
        parse_etag_version(if_match)
        return CommandResult(202, {"run_ref": "run-42"}, 13)

    def cancel_run(self, *, if_match: str | None, **_values: object) -> CommandResult:
        parse_etag_version(if_match)
        return CommandResult(202, {"run_ref": "run-42"}, 14)

    def complete_upload(self, *, if_match: str | None, **_values: object) -> CommandResult:
        parse_etag_version(if_match)
        return CommandResult(202, {"upload_ref": "upload-42"}, 15)

    def abort_upload(self, *, if_match: str | None, **_values: object) -> CommandResult:
        parse_etag_version(if_match)
        return CommandResult(202, {"upload_ref": "upload-42"}, 16)

    def get_upload(self, _upload_id: str) -> CommandResult:
        if _upload_id == "receipt":
            return CommandResult(
                410,
                {
                    "code": "UPLOAD_EXPIRED",
                    "message": "Upload session has expired.",
                    "correlation_id": "synthetic-correlation",
                    "retryable": False,
                    "retry_after_seconds": None,
                    "field_errors": None,
                },
            )
        raise StoryRunLiteError(410, "UPLOAD_EXPIRED", "Upload session has expired.")

    def put_part(self, **values: object) -> CommandResult:
        self.part = tuple(
            values[key]
            for key in ("upload_id", "part_number", "payload", "declared_length", "declared_sha256")
        )
        return CommandResult(200, {"accepted": True}, 1)


class _FakeProjectionResult:
    def __init__(self, *, row: Any = None, rows: list[Any] | None = None) -> None:
        self._row = row
        self._rows = rows

    def mappings(self) -> _FakeProjectionResult:
        return self

    def one_or_none(self) -> Any:
        return self._row

    def first(self) -> Any:
        return self._row

    def all(self) -> list[Any]:
        return self._rows or []


class _FakeProjectionConnection:
    def __init__(self, results: list[_FakeProjectionResult]) -> None:
        self._results = list(results)
        self.execute_count = 0

    def __enter__(self) -> _FakeProjectionConnection:
        return self

    def __exit__(self, *_exc_info: object) -> None:
        return None

    def execute(self, *_args: object, **_kwargs: object) -> _FakeProjectionResult:
        self.execute_count += 1
        if not self._results:
            raise AssertionError("production repository issued an unexpected query")
        return self._results.pop(0)


class _FakeProjectionEngine:
    def __init__(
        self,
        *,
        connect_results: list[_FakeProjectionResult] | None = None,
        begin_results: list[_FakeProjectionResult] | None = None,
    ) -> None:
        self._connect_results = connect_results
        self._begin_results = begin_results
        self.connection: _FakeProjectionConnection | None = None

    def connect(self) -> _FakeProjectionConnection:
        if self._connect_results is None:
            raise AssertionError("unexpected production repository connect()")
        self.connection = _FakeProjectionConnection(self._connect_results)
        return self.connection

    def begin(self) -> _FakeProjectionConnection:
        if self._begin_results is None:
            raise AssertionError("unexpected production repository begin()")
        self.connection = _FakeProjectionConnection(self._begin_results)
        return self.connection


def _production_projection_client(engine: _FakeProjectionEngine) -> TestClient:
    repository = SqlStoryRunLiteRepository(
        engine=cast(Engine, engine),
        quarantine=cast(QuarantineStore, object()),
    )
    unused = object()
    service = StoryRunLiteService(
        repository=repository,
        scanner=cast(ImageSafetyScannerPort, unused),
        normalizer=cast(ImageNormalizerPort, unused),
        vision=cast(StoryRunLiteVisionPort, unused),
        story_references=cast(StoryRunReferencePort, unused),
        asset_admission=cast(CoreAssetAdmissionPort, unused),
    )
    return TestClient(create_app(service=service))


def test_runtime_router_and_pinned_openapi_have_fourteen_operations() -> None:
    runtime_operations = {
        (route.path, method.lower())
        for route in router.routes
        if isinstance(route, APIRoute)
        for method in route.methods or set()
        if method not in {"HEAD", "OPTIONS"}
    }
    root = Path(__file__).resolve().parents[3]
    contract_path = (
        root
        / "features"
        / "FEAT-063-system-architecture-rearchitecture"
        / "artifacts"
        / "storyrun-lite"
        / "openapi.json"
    )
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    contract_operations = {
        (path, method)
        for path, item in contract["paths"].items()
        for method in item
        if method in {"get", "post", "put", "delete"}
    }
    assert len(runtime_operations) == 14
    assert runtime_operations == contract_operations
    assert len({path for path, _method in contract_operations}) == 13
    assert ("/v1/story-runs/readiness", "get") in contract_operations
    assert ("/v1/story-runs/{run_ref}", "get") in contract_operations
    assert ("/v1/upload-sessions/{upload_ref}", "get") in contract_operations
    assert ("/v1/story-runs/{run_ref}/story-revisions", "post") in contract_operations
    assert (
        "/v1/story-runs/{run_ref}/story-revisions/{story_revision_ref}",
        "get",
    ) in contract_operations
    assert (
        "/v1/story-runs/{run_ref}/story-revisions/{story_revision_ref}/confirmation",
        "post",
    ) in contract_operations
    create_run_schema = contract["components"]["schemas"]["CreateRunRequest"]
    assert "child_age_months" in create_run_schema["required"]
    assert "default" not in create_run_schema["properties"]["child_age_months"]
    upload_schema = contract["components"]["schemas"]["UploadSession"]
    assert "PENDING" in upload_schema["properties"]["state"]["enum"]
    assert "derived_asset_ref" in upload_schema["properties"]

    bruno_requests = (
        root
        / "features"
        / "FEAT-063-system-architecture-rearchitecture"
        / "artifacts"
        / "storyrun-lite"
        / "bruno"
        / "requests"
    )
    bruno_operations = set()
    for request_path in sorted(bruno_requests.glob("*.bru")):
        request_text = request_path.read_text(encoding="utf-8")
        method_match = re.search(r"(?m)^(get|post|put|delete) \{", request_text)
        url_match = re.search(r"(?m)^\s+url: \{\{baseUrl\}\}([^\r\n]+)", request_text)
        assert method_match is not None, request_path.name
        assert url_match is not None, request_path.name
        path = url_match.group(1)
        for variable, parameter in {
            "runRef": "run_ref",
            "uploadRef": "upload_ref",
            "partNo": "part_no",
            "storyRevisionRef": "story_revision_ref",
        }.items():
            path = path.replace("{{" + variable + "}}", "{" + parameter + "}")
        bruno_operations.add((path, method_match.group(1)))
    assert len(bruno_operations) == 14
    assert bruno_operations == contract_operations

    put_responses = contract["paths"]["/v1/upload-sessions/{upload_ref}/parts/{part_no}"]["put"][
        "responses"
    ]
    assert {"410", "411", "415"}.issubset(put_responses)
    assert (
        "410" in contract["paths"]["/v1/upload-sessions/{upload_ref}/complete"]["post"]["responses"]
    )
    precondition_operations = {
        ("/v1/story-runs/{run_ref}/assets", "post"),
        ("/v1/story-runs/{run_ref}/subject-confirmation", "post"),
        ("/v1/story-runs/{run_ref}/cancel", "post"),
        ("/v1/upload-sessions/{upload_ref}/complete", "post"),
        ("/v1/upload-sessions/{upload_ref}", "delete"),
    }
    for path, method in precondition_operations:
        item = contract["paths"][path]
        operation = item[method]
        parameters = [*item.get("parameters", []), *operation.get("parameters", [])]
        assert {"$ref": "#/components/parameters/IfMatch"} in parameters
        assert "428" in operation["responses"]

    validation_operations = {
        ("/v1/story-runs", "post"),
        ("/v1/story-runs/{run_ref}/assets", "post"),
        ("/v1/story-runs/{run_ref}/subject-confirmation", "post"),
        ("/v1/story-runs/{run_ref}/cancel", "post"),
        ("/v1/upload-sessions", "post"),
        ("/v1/upload-sessions/{upload_ref}/parts/{part_no}", "put"),
        ("/v1/upload-sessions/{upload_ref}/complete", "post"),
        ("/v1/upload-sessions/{upload_ref}", "delete"),
        ("/v1/story-runs/{run_ref}/story-revisions", "post"),
        (
            "/v1/story-runs/{run_ref}/story-revisions/{story_revision_ref}/confirmation",
            "post",
        ),
    }
    for path, method in validation_operations:
        assert "422" in contract["paths"][path][method]["responses"]

    for _path, path_item in contract["paths"].items():
        for method, operation in path_item.items():
            if method not in {"get", "post", "put", "delete"}:
                continue
            assert operation["responses"]["500"]["$ref"] == ("#/components/responses/InternalError")
            for status, response in operation.get("responses", {}).items():
                if status == "202":
                    headers = response.get("headers", {})
                    assert {"Location", "Retry-After", "ETag", "Cache-Control"}.issubset(headers)
                    assert headers["Cache-Control"]["schema"]["const"] == "no-store"

    error_codes = set(contract["components"]["schemas"]["Error"]["properties"]["code"]["enum"])
    expected_error_codes = {
        "ACTIVE_RUN_EXISTS",
        "ASSET_INVALID",
        "ASSET_SCOPE_MISMATCH",
        "CHILD_AGE_REQUIRED",
        "COMMAND_RECOVERY_HOLD",
        "CONTENT_LENGTH_MISMATCH",
        "CONTENT_LENGTH_REQUIRED",
        "EDUCATIONAL_FACT_CHECK_FAILED",
        "IMAGE_INFECTED",
        "IMAGE_INVALID",
        "IMAGE_NORMALIZATION_FAILED",
        "IMAGE_TOO_LARGE",
        "INTERNAL_ERROR",
        "INVALID_CONTENT_LENGTH",
        "INVALID_ETAG",
        "INVALID_IDEMPOTENCY_KEY",
        "INVALID_PART_NUMBER",
        "INVALID_REQUEST",
        "INVALID_STATE",
        "NOT_FOUND",
        "PART_CONFLICT",
        "PART_HASH_MISMATCH",
        "PART_HASH_REQUIRED",
        "PART_TOO_LARGE",
        "PRECONDITION_REQUIRED",
        "SCANNER_REJECTED",
        "SCANNER_UNAVAILABLE",
        "SCRIPT_GENERATION_UNKNOWN",
        "SERVICE_NOT_READY",
        "STAGING_UNAVAILABLE",
        "STALE_REVISION",
        "STALE_SUBJECT",
        "STORY_GENERATION_NOT_CONFIGURED",
        "STORY_OUTCOME_UNKNOWN",
        "STORY_OUTPUT_INVALID",
        "STORY_REWRITE_LIMIT_REACHED",
        "STORY_REWRITE_NOT_ALLOWED",
        "UNSUPPORTED_MEDIA_TYPE",
        "UPLOAD_EXPIRED",
        "UPLOAD_INCOMPLETE",
        "UPLOAD_METADATA_MISMATCH",
        "UPLOAD_PART_GAP",
        "UPLOAD_SESSION_STATE_CONFLICT",
        "VISION_ATTEMPT_HOLD",
        "VISION_OUTCOME_UNKNOWN",
        "WORKER_LIMITS_UNAVAILABLE",
    }
    assert expected_error_codes.issubset(error_codes)
    error_properties = contract["components"]["schemas"]["Error"]["properties"]
    assert error_properties["field_errors"]["type"] == ["array", "null"]
    assert error_properties["retry_after_seconds"]["type"] == ["integer", "null"]


def test_get_projection_runtime_error_codes_are_declared_by_openapi() -> None:
    root = Path(__file__).resolve().parents[3]
    contract_path = (
        root
        / "features"
        / "FEAT-063-system-architecture-rearchitecture"
        / "artifacts"
        / "storyrun-lite"
        / "openapi.json"
    )
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    schemas = contract["components"]["schemas"]
    declared_codes = set(schemas["Error"]["properties"]["code"]["enum"])
    cases = {
        "StoryRun": {
            "path": "/v1/story-runs/{run_ref}",
            "error_code": "VISION_LOOPBACK_NOT_CONFIGURED",
            "runtime_codes": {
                "MODEL_INPUT_NOT_ADMITTED",
                "STORY_RESULT_PERSISTENCE_UNKNOWN",
                "VISION_ADAPTER_FAILURE",
                "VISION_ATTEMPT_FAILED",
                "VISION_ATTEMPT_HOLD",
                "VISION_ENDPOINT_NOT_ALLOWED",
                "VISION_INPUT_NOT_VALIDATED",
                "VISION_LEDGER_FINALIZATION_UNKNOWN",
                "VISION_LOOPBACK_NOT_CONFIGURED",
                "VISION_OUTCOME_UNKNOWN",
                "VISION_PROHIBITED_CLAIM_DETECTED",
                "VISION_RESPONSE_INVALID",
                "VISION_RESULT_CAS_LOST",
                "VISION_VISION_MODEL_UNAVAILABLE",
                "VISION_VISION_PROVIDER_FAILURE",
                "VISION_VISION_SCHEMA_INVALID",
                "VISION_VISION_TIMEOUT",
            },
        },
        "UploadSession": {
            "path": "/v1/upload-sessions/{upload_ref}",
            "error_code": "MODEL_INPUT_TOO_LARGE",
            "runtime_codes": {
                "IMAGE_DECODER_UNAVAILABLE",
                "IMAGE_HASH_MISMATCH",
                "IMAGE_INFECTED",
                "IMAGE_INVALID",
                "IMAGE_NORMALIZATION_FAILED",
                "IMAGE_TOO_LARGE",
                "IMAGE_WORKER_FAILED",
                "MODEL_INPUT_TOO_LARGE",
                "QUARANTINE_UNAVAILABLE",
                "SCANNER_UNAVAILABLE",
                "STAGING_UNAVAILABLE",
                "UNSUPPORTED_MEDIA_TYPE",
                "UPLOAD_EXPIRED",
                "UPLOAD_SESSION_STATE_CONFLICT",
                "WORKER_GATE_CLOSED",
                "WORKER_LIMITS_UNAVAILABLE",
                "WORKER_TIMEOUT",
            },
        },
    }
    for schema_name, case in cases.items():
        operation = contract["paths"][case["path"]]["get"]
        response_schema = operation["responses"]["200"]["content"]["application/json"]["schema"]
        assert response_schema["$ref"] == f"#/components/schemas/{schema_name}"
        error_schema = schemas[schema_name]["properties"]["error"]
        assert error_schema["oneOf"][0]["$ref"] == "#/components/schemas/Error"
        assert error_schema["oneOf"][1] == {"type": "null"}
        assert case["runtime_codes"].issubset(declared_codes)
        assert case["error_code"] in declared_codes


def test_get_run_projects_saved_error_code_through_production_repository() -> None:
    error_code = "VISION_LOOPBACK_NOT_CONFIGURED"
    now = datetime(2026, 11, 2, tzinfo=UTC)
    run_row = {
        "run_id": "run-projection-test",
        "child_age_months": 60,
        "run_state": "FAILED",
        "revision": 1,
        "version": 2,
        "understanding_revision": None,
        "created_at": now,
        "updated_at": now,
        "job_state": "FAILED",
        "retryable": False,
        "action_required": "OPERATOR_REVIEW",
        "error_code": error_code,
    }
    engine = _FakeProjectionEngine(connect_results=[_FakeProjectionResult(row=run_row)])
    client = _production_projection_client(engine)
    openapi_path = (
        Path(__file__).resolve().parents[3]
        / "features"
        / "FEAT-063-system-architecture-rearchitecture"
        / "artifacts"
        / "storyrun-lite"
        / "openapi.json"
    )
    openapi = json.loads(openapi_path.read_text(encoding="utf-8"))
    declared_codes = set(openapi["components"]["schemas"]["Error"]["properties"]["code"]["enum"])

    response = client.get("/v1/story-runs/run-projection-test")

    assert response.status_code == 200
    assert engine.connection is not None
    assert engine.connection.execute_count == 1
    assert response.json()["error"]["code"] == run_row["error_code"]
    assert response.json()["error"]["code"] in declared_codes


def test_get_upload_projects_saved_error_code_through_production_repository() -> None:
    error_code = "MODEL_INPUT_TOO_LARGE"
    upload_id = "upload-projection-test"
    run_id = "run-for-upload-projection-test"
    now = datetime(2026, 11, 2, tzinfo=UTC)
    upload_row = {
        "upload_session_id": upload_id,
        "target_kind": "STORY_RUN",
        "target_ref": run_id,
        "state": "FAILED",
        "state_version": 3,
        "part_size_bytes": 4_194_304,
        "max_total_bytes": 20_971_520,
        "max_parts": 5,
        "asset_ref": None,
        "derived_asset_ref": None,
        "expires_at": now,
        "error_code": error_code,
    }
    engine = _FakeProjectionEngine(
        begin_results=[
            _FakeProjectionResult(row=SimpleNamespace(target_kind="STORY_RUN", target_ref=run_id)),
            _FakeProjectionResult(row={"run_id": run_id}),
            _FakeProjectionResult(row=upload_row),
            _FakeProjectionResult(rows=[]),
        ]
    )
    client = _production_projection_client(engine)
    openapi_path = (
        Path(__file__).resolve().parents[3]
        / "features"
        / "FEAT-063-system-architecture-rearchitecture"
        / "artifacts"
        / "storyrun-lite"
        / "openapi.json"
    )
    openapi = json.loads(openapi_path.read_text(encoding="utf-8"))
    declared_codes = set(openapi["components"]["schemas"]["Error"]["properties"]["code"]["enum"])

    response = client.get(f"/v1/upload-sessions/{upload_id}")

    assert response.status_code == 200
    assert engine.connection is not None
    assert engine.connection.execute_count == 4
    assert response.json()["parts"] == []
    assert response.json()["error"]["code"] == upload_row["error_code"]
    assert response.json()["error"]["code"] in declared_codes


def test_create_run_returns_a_strong_etag_and_validation_uses_error_envelope() -> None:
    service = _StubService()
    client = TestClient(create_app(service=cast(StoryRunLiteService, service)))

    response = client.post(
        "/v1/story-runs",
        headers={"Idempotency-Key": "contract-run-1"},
        json={"profile_ref": "synthetic-parent-demo", "child_age_months": 60},
    )
    assert response.status_code == 201
    assert response.headers["ETag"] == '"v1"'
    assert response.json()["key"] == "contract-run-1"

    invalid = client.post("/v1/story-runs", json={"profile_ref": "unapproved"})
    assert invalid.status_code == 422
    assert invalid.json()["code"] == "INVALID_REQUEST"

    missing_age = client.post(
        "/v1/story-runs",
        headers={"Idempotency-Key": "contract-run-missing-age"},
        json={"profile_ref": "synthetic-parent-demo"},
    )
    assert missing_age.status_code == 422
    assert missing_age.json()["code"] == "INVALID_REQUEST"


def test_parent_story_revision_routes_validate_and_return_versioned_resources() -> None:
    client = TestClient(create_app(service=cast(StoryRunLiteService, _StubService())))
    run_ref = "00000000-0000-0000-0000-000000000001"
    revision_ref = "00000000-0000-0000-0000-000000000042"
    generated = client.post(
        f"/v1/story-runs/{run_ref}/story-revisions",
        headers={"Idempotency-Key": "generate-story-1", "If-Match": '"v1"'},
        json={
            "expected_understanding_revision": 1,
            "adult_confirmed_idea": "A butterfly visits flowers",
        },
    )
    assert generated.status_code == 201
    assert generated.headers["ETag"] == '"v2"'
    assert generated.json()["story_revision_ref"] == revision_ref

    fetched = client.get(f"/v1/story-runs/{run_ref}/story-revisions/{revision_ref}")
    assert fetched.status_code == 200
    assert fetched.json()["story_revision_ref"] == revision_ref

    confirmed = client.post(
        f"/v1/story-runs/{run_ref}/story-revisions/{revision_ref}/confirmation",
        headers={"Idempotency-Key": "confirm-story-1", "If-Match": '"v2"'},
        json={
            "expected_revision": 1,
            "story_sha256": "a" * 64,
        },
    )
    assert confirmed.status_code == 200
    assert confirmed.headers["ETag"] == '"v3"'

    invalid = client.post(
        f"/v1/story-runs/{run_ref}/story-revisions",
        headers={"Idempotency-Key": "generate-story-invalid", "If-Match": '"v1"'},
        json={"expected_understanding_revision": 1, "activities": ["ACT-01"]},
    )
    assert invalid.status_code == 422
    assert invalid.json()["code"] == "INVALID_REQUEST"
    assert "correlation_id" in invalid.json()
    assert invalid.json()["field_errors"]
    assert invalid.headers["Cache-Control"] == "no-store"


def test_story_generation_http_accepts_before_background_ai_task_finishes() -> None:
    class BackgroundService(_StubService):
        def __init__(self) -> None:
            super().__init__()
            self.started = threading.Event()
            self.finished = threading.Event()

        def generate_story_revision(
            self, *, run_id: str, idempotency_key: str, **values: object
        ) -> CommandResult:
            schedule = values["schedule"]
            assert callable(schedule)
            schedule(self.run_slow_worker, ())
            return CommandResult(
                202,
                {
                    "run_ref": run_id,
                    "story_revision_ref": "00000000-0000-0000-0000-000000000042",
                    "state": "GENERATING",
                    "key": idempotency_key,
                },
                2,
            )

        def run_slow_worker(self) -> None:
            self.started.set()
            time.sleep(1.5)
            self.finished.set()

    service = BackgroundService()
    application = create_app(service=cast(StoryRunLiteService, service))
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", 0))
    sock.listen(128)
    host, port = sock.getsockname()
    server = uvicorn.Server(
        uvicorn.Config(application, log_level="critical", lifespan="off", access_log=False)
    )
    thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
    thread.start()
    try:
        deadline = time.monotonic() + 5
        while not server.started and time.monotonic() < deadline:
            time.sleep(0.01)
        assert server.started
        request = urllib.request.Request(
            f"http://{host}:{port}/v1/story-runs/run-42/story-revisions",
            data=json.dumps(
                {
                    "expected_understanding_revision": 1,
                    "adult_confirmed_idea": "A butterfly visits a flower",
                }
            ).encode(),
            headers={
                "Content-Type": "application/json",
                "Idempotency-Key": "async-story-acceptance",
                "If-Match": '"v1"',
            },
            method="POST",
        )
        started_at = time.monotonic()
        with urllib.request.urlopen(request, timeout=5) as response:
            elapsed = time.monotonic() - started_at
            body = json.loads(response.read())
            assert response.status == 202
            assert response.headers["Location"].endswith(body["story_revision_ref"])
        assert elapsed < 1.0
        assert service.started.wait(timeout=1)
        assert not service.finished.is_set()
        assert service.finished.wait(timeout=3)
    finally:
        server.should_exit = True
        thread.join(timeout=5)
        sock.close()


def test_common_internal_error_handler_matches_openapi_500_envelope() -> None:
    client = TestClient(
        create_app(service=cast(StoryRunLiteService, _StubService())),
        raise_server_exceptions=False,
    )

    response = client.get("/v1/story-runs/explode")

    assert response.status_code == 500
    assert response.headers["Cache-Control"] == "no-store"
    body = response.json()
    assert body["code"] == "INTERNAL_ERROR"
    assert body["message"] == "The request could not be completed."
    assert isinstance(body["correlation_id"], str)
    assert body["retryable"] is False


@pytest.mark.parametrize(
    ("method", "path", "payload", "headers", "content"),
    [
        ("post", "/v1/story-runs", {}, {}, None),
        (
            "post",
            "/v1/story-runs/run-42/assets",
            {},
            {"Idempotency-Key": "validation-attach", "If-Match": '"v1"'},
            None,
        ),
        (
            "post",
            "/v1/story-runs/run-42/subject-confirmation",
            {},
            {"Idempotency-Key": "validation-confirm", "If-Match": '"v1"'},
            None,
        ),
        (
            "post",
            "/v1/story-runs/run-42/cancel",
            {},
            {"Idempotency-Key": "validation-cancel", "If-Match": '"v1"'},
            None,
        ),
        ("post", "/v1/upload-sessions", {}, {}, None),
        (
            "put",
            "/v1/upload-sessions/upload-42/parts/not-an-integer",
            None,
            {
                "Content-Type": "application/octet-stream",
                "Content-Length": "1",
                "Content-SHA256": "a" * 64,
            },
            b"x",
        ),
        (
            "post",
            "/v1/upload-sessions/upload-42/complete",
            {},
            {"Idempotency-Key": "validation-complete", "If-Match": '"v1"'},
            None,
        ),
        (
            "delete",
            "/v1/upload-sessions/upload-42",
            None,
            {"If-Match": '"v1"'},
            None,
        ),
    ],
)
def test_all_validated_operations_return_the_documented_error_envelope(
    method: str,
    path: str,
    payload: dict[str, object] | None,
    headers: dict[str, str],
    content: bytes | None,
) -> None:
    client = TestClient(create_app(service=cast(StoryRunLiteService, _StubService())))
    kwargs: dict[str, object] = {"headers": headers}
    if payload is not None:
        kwargs["json"] = payload
    if content is not None:
        kwargs["content"] = content

    response = getattr(client, method)(path, **kwargs)

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "INVALID_REQUEST"
    assert isinstance(body["correlation_id"], str)
    assert body["retryable"] is False
    assert isinstance(body["field_errors"], list)
    assert body["field_errors"]
    assert response.headers["Cache-Control"] == "no-store"


def test_part_endpoint_streams_bounded_raw_bytes_without_json_encoding() -> None:
    service = _StubService()
    client = TestClient(create_app(service=cast(StoryRunLiteService, service)))
    payload = b"synthetic-binary-part\x00\x01"
    response = client.put(
        "/v1/upload-sessions/00000000-0000-0000-0000-000000000001/parts/1",
        content=payload,
        headers={
            "Content-Type": "application/octet-stream",
            "Content-Length": str(len(payload)),
            "Content-SHA256": "a" * 64,
        },
    )
    assert response.status_code == 200
    assert service.part is not None
    assert service.part[2] == payload
    assert service.part[3] == len(payload)


@pytest.mark.parametrize(
    ("method", "path", "payload", "extra_headers", "location", "etag_value"),
    [
        (
            "post",
            "/v1/story-runs/run-42/assets",
            {"asset_ref": "asset-1", "expected_revision": 1},
            {"If-Match": '"v1"'},
            "/v1/story-runs/run-42",
            '"v12"',
        ),
        (
            "post",
            "/v1/story-runs/run-42/subject-confirmation",
            {"decision": "CONFIRM", "expected_understanding_revision": 1},
            {"If-Match": '"v1"'},
            "/v1/story-runs/run-42",
            '"v13"',
        ),
        (
            "post",
            "/v1/story-runs/run-42/cancel",
            {"expected_revision": 1},
            {"If-Match": '"v1"'},
            "/v1/story-runs/run-42",
            '"v14"',
        ),
        (
            "post",
            "/v1/upload-sessions/upload-42/complete",
            {"expected_size_bytes": 1, "expected_sha256": "a" * 64},
            {"If-Match": '"v1"'},
            "/v1/upload-sessions/upload-42",
            '"v15"',
        ),
        (
            "delete",
            "/v1/upload-sessions/upload-42",
            None,
            {"If-Match": '"v1"'},
            "/v1/upload-sessions/upload-42",
            '"v16"',
        ),
    ],
)
def test_every_202_route_emits_location_retry_after_and_etag(
    method: str,
    path: str,
    payload: dict[str, object] | None,
    extra_headers: dict[str, str],
    location: str,
    etag_value: str,
) -> None:
    service = _StubService()
    client = TestClient(create_app(service=cast(StoryRunLiteService, service)))
    headers = {"Idempotency-Key": "review-fix-202", **extra_headers}
    if payload is None:
        response = getattr(client, method)(path, headers=headers)
    else:
        response = getattr(client, method)(path, headers=headers, json=payload)

    assert response.status_code == 202
    assert response.headers["Location"] == location
    assert response.headers["Retry-After"] == "1"
    assert response.headers["ETag"] == etag_value
    assert response.headers["Cache-Control"] == "no-store"


def test_runtime_precondition_error_and_upload_expiry_are_http_errors() -> None:
    service = _StubService()
    client = TestClient(create_app(service=cast(StoryRunLiteService, service)))

    missing_if_match = client.post(
        "/v1/upload-sessions/upload-42/complete",
        headers={"Idempotency-Key": "missing-if-match"},
        json={"expected_size_bytes": 1, "expected_sha256": "a" * 64},
    )
    assert missing_if_match.status_code == 428
    assert missing_if_match.json()["code"] == "PRECONDITION_REQUIRED"
    assert missing_if_match.json()["field_errors"] is None
    assert isinstance(missing_if_match.json()["correlation_id"], str)
    assert missing_if_match.json()["retryable"] is False

    conflict = client.post(
        "/v1/story-runs/conflict/assets",
        headers={"Idempotency-Key": "conflict", "If-Match": '"v1"'},
        json={"asset_ref": "asset-1", "expected_revision": 1},
    )
    assert conflict.status_code == 409
    assert conflict.json()["code"] == "STALE_REVISION"
    assert conflict.json()["field_errors"] is None
    assert conflict.headers["Cache-Control"] == "no-store"

    expired = client.get("/v1/upload-sessions/upload-42")
    assert expired.status_code == 410
    assert expired.json()["code"] == "UPLOAD_EXPIRED"
    assert expired.json()["field_errors"] is None

    receipt_error = client.get("/v1/upload-sessions/receipt")
    assert receipt_error.status_code == 410
    assert receipt_error.json()["field_errors"] is None
    assert receipt_error.json()["retry_after_seconds"] is None


def test_part_transport_errors_match_documented_status_and_code() -> None:
    service = _StubService()
    client = TestClient(create_app(service=cast(StoryRunLiteService, service)))
    path = "/v1/upload-sessions/upload-42/parts/1"
    common = {"Content-SHA256": "a" * 64}

    missing_length = client.put(
        path,
        content=iter([b"x"]),
        headers={"Content-Type": "application/octet-stream", **common},
    )
    assert missing_length.status_code == 411
    assert missing_length.json()["code"] == "CONTENT_LENGTH_REQUIRED"
    assert isinstance(missing_length.json()["correlation_id"], str)
    assert missing_length.headers["Cache-Control"] == "no-store"

    missing_hash = client.put(
        path,
        content=b"x",
        headers={"Content-Type": "application/octet-stream", "Content-Length": "1"},
    )
    assert missing_hash.status_code == 400
    assert missing_hash.json()["code"] == "PART_HASH_REQUIRED"
    assert missing_hash.headers["Cache-Control"] == "no-store"

    unsupported = client.put(
        path,
        content=b"x",
        headers={
            "Content-Type": "image/png",
            "Content-Length": "1",
            **common,
        },
    )
    assert unsupported.status_code == 415
    assert unsupported.json()["code"] == "UNSUPPORTED_MEDIA_TYPE"
    assert unsupported.headers["Cache-Control"] == "no-store"
