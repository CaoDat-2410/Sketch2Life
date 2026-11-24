"""Contract-alignment checks for the published Swagger/OpenAPI surface."""

from __future__ import annotations

import json
import re
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.openapi_contract import (
    IDEMPOTENCY_MISMATCH_OPERATION_KEYS,
    MOUNTED_OPERATION_COUNT,
    MOUNTED_OPERATIONS,
    TAG_DESCRIPTIONS,
    UNMOUNTED_OPERATION_COUNT,
    UNMOUNTED_OPERATIONS,
)
from sketch2life.interfaces.http.openapi_contract_amendments import (
    BE1_KEPT_422_OPERATIONS,
    PORTFOLIO_OPERATION_KEY,
    RESTORE_CHECKPOINT_OPERATION_KEY,
    RESTORE_CHECKPOINT_RESPONSE_DESCRIPTIONS,
    public_tag_name,
    public_tags,
    published_responses,
)
from sketch2life.interfaces.http.openapi_srs_v22 import (
    SRS_V22_INCLUDED_OPERATIONS,
    SRS_V22_TAGS,
)
from sketch2life.interfaces.http.admin_contract import ADMIN_OPERATIONS
from sketch2life.interfaces.http.quota_contract import QUOTA_OPERATIONS

HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head"}
EXPECTED_IDEMPOTENCY_MISMATCH_OPERATION_KEYS = {
    ("post", "/api/lesson-library/v1/me/lesson-invitations/{access_grant_id}/accept"),
    ("post", "/api/lesson-library/v1/me/lesson-invitations/{access_grant_id}/decline"),
    ("post", "/api/lesson-library/v1/me/parent-group-invitations/{membership_id}/accept"),
    (
        "post",
        "/api/lesson-library/v1/organizations/{organization_id}/access-grants/{access_grant_id}/decision",
    ),
    ("post", "/api/lesson-library/v1/organizations/{organization_id}/lessons"),
    (
        "post",
        "/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}/access-grants",
    ),
    (
        "post",
        "/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}/upload-sessions",
    ),
    ("post", "/api/lesson-library/v1/organizations/{organization_id}/parent-groups"),
    (
        "post",
        "/api/lesson-library/v1/organizations/{organization_id}/parent-groups/{parent_group_id}/invitations",
    ),
    ("patch", "/api/lesson-library/v1/platform/lessons/{lesson_id}/moderation"),
    ("post", "/api/lesson-library/v1/upload-sessions/{upload_session_id}/complete"),
    # FEAT-066 C4 (SRS §21.4): lesson PATCH and archive, version create, grant revoke, abort.
    ("patch", "/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}"),
    ("delete", "/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}"),
    (
        "post",
        "/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}/versions",
    ),
    (
        "delete",
        "/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}"
        "/access-grants/{access_grant_id}",
    ),
    ("delete", "/api/lesson-library/v1/upload-sessions/{upload_session_id}"),
    # FEAT-066 M9-B: the first Teacher assignment command.
    ("post", "/api/be1/v1/classes/{class_id}/assignments"),
    # FEAT-066 T0.1: create class is a keyed command.
    ("post", "/api/be1/v1/organizations/{organization_id}/classes"),
    # FEAT-066 T-2a (SRS l.1697): the keyed generic upload commands.
    ("post", "/v1/upload-sessions"),
    ("post", "/v1/upload-sessions/{upload_id}/complete"),
    ("delete", "/v1/upload-sessions/{upload_id}"),
    # FEAT-066 T-3a (SRS l.1697): the keyed lesson occurrence create.
    ("post", "/v1/lesson-occurrences"),
    # FEAT-066 T-3b (SRS l.1697): the keyed document attach.
    ("post", "/v1/lesson-occurrences/{occurrence_id}/documents"),
    # FEAT-066 T-3c (SRS l.1697): the keyed text edit (a new immutable revision).
    ("post", "/v1/lesson-occurrences/{occurrence_id}/documents/{document_id}/revisions"),
    # FEAT-066 T-3d (SRS l.1697): the keyed plan revision create and confirm.
    ("post", "/v1/lesson-occurrences/{occurrence_id}/plan-revisions"),
    ("post", "/v1/lesson-occurrences/{occurrence_id}/plan-revisions/{revision_no}/confirm"),
    # FEAT-066 T-4b1 (SRS l.1697): the keyed child selection and its confirmation.
    ("post", "/v1/lesson-occurrences/{occurrence_id}/child-selections"),
    ("post", "/v1/lesson-occurrences/{occurrence_id}/child-selections/{selection_id}/confirmation"),
    # FEAT-066 T-5a (SRS l.1697): the keyed class projection confirmation.
    ("post", "/v1/lesson-occurrences/{occurrence_id}/projection-confirmation"),
    # FEAT-066 T-8a (SRS l.1697): the keyed notification mark-read commands.
    ("post", "/v1/notifications/{inbox_item_id}/read"),
    ("post", "/v1/notifications/read-all"),
    # FEAT-066 T-7b (SRS l.1697): the keyed class suspend and archive commands.
    ("post", "/api/be1/v1/classes/{class_id}/suspend"),
    ("post", "/api/be1/v1/classes/{class_id}/archive"),
    # FEAT-066 T-7c (SRS l.1697): the keyed Teacher profile create.
    ("post", "/api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles"),
    # FEAT-066 T-7d (SRS l.1697): the keyed Teacher enrollment move.
    ("post", "/api/be1/v1/classes/{class_id}/profiles/{child_id}/move"),
}


@pytest.fixture(autouse=True)
def _disable_dotenv_for_composition_tests(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", "0")
    monkeypatch.setenv(
        "SKETCH2LIFE_DATABASE_URL", "postgresql+psycopg://localhost:9/s1at_closed"
    )
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    assert Settings.model_config.get("env_file") is None
    assert CoreDatabaseSettings.model_config.get("env_file") is None
    try:
        yield
    finally:
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


UPLOAD_TRANSPORT_TOO_LARGE_OPERATIONS = {
    ("post", "/v1/sessions/{session_id}/media/audio"),
    ("post", "/v1/sessions/{session_id}/media/image"),
}
# T9's local/test-only candidate lookup is intentionally outside the pinned Rev37 catalog.
PILOT_ONLY_OPERATIONS = {
    (
        "get",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/pilot-profiles",
    ),
    ("post", "/api/be1/v1/assistance-requests"),
    ("post", "/api/be1/v1/assistance-requests/{assistance_id}/cancel"),
    (
        "get",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/assistance-requests/{assistance_id}/status",
    ),
    (
        "get",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/teacher/assistance-requests/pending",
    ),
}
PR22_UNCATALOGUED_OPERATIONS = {
    # Mounted routes intentionally outside the Rev37 metadata map.
    # FEAT-066 M9-B: the Teacher candidate list stays runtime-only like the C5 account routes.
    ("get", "/api/be1/v1/organizations/{organization_id}/teacher-candidates"),
    # FEAT-066 T0.3: the public liveness probe; /health/ready and /metrics are not in the schema.
    ("get", "/health/live"),
    ("post", "/api/auth/v1/registrations"),
    ("get", "/api/auth/v1/me"),
    # FEAT-066 T0.4: the live job poll route stays runtime-only until the first producer (T-3b).
    ("get", "/v1/jobs/{job_id}"),
    ("get", "/api/platform-admin/v1/accounts"),
    ("post", "/api/platform-admin/v1/accounts"),
    ("patch", "/api/platform-admin/v1/accounts/{account_id}"),
    ("post", "/api/parent/v1/ai/sketch-guides"),
    ("post", "/api/parent/v1/ai/drawing-understandings"),
    ("post", "/api/parent/v1/ai/story-runs/{run_id}/story-revisions"),
    ("post", "/v1/story-runs/{run_id}/cancel"),
    # FR-C-08 (Contract Draft 11 §3.7): the Parent delete route stays uncatalogued.
    ("delete", "/v1/story-runs/{run_id}"),
    (
        "post",
        "/api/teacher/v1/organizations/{organization_id}/ai/lesson-plan-suggestions",
    ),
    ("post", "/api/teacher/v1/organizations/{organization_id}/ai/sketch-decks"),
}
CONTRACT_PARAMETER = re.compile(r"\b(path|query|header|cookie)\s+`([^`]+)`:\s*([^;]+)")
CONTRACT_REQUEST_BODY = re.compile(
    r"([A-Za-z0-9.+_-]+/[A-Za-z0-9.+_-]+)(?:\s+\((required|optional)\))?:\s*"
    r"([A-Za-z][A-Za-z0-9_]*)"
)


def _schema_refs(value: Any) -> set[str]:
    if isinstance(value, dict):
        refs = {value["$ref"].rsplit("/", maxsplit=1)[-1]} if "$ref" in value else set()
        for child in value.values():
            refs.update(_schema_refs(child))
        return refs
    if isinstance(value, list):
        refs: set[str] = set()
        for child in value:
            refs.update(_schema_refs(child))
        return refs
    return set()


def _extension_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        keys = {key for key in value if key.startswith("x-")}
        for child in value.values():
            keys.update(_extension_keys(child))
        return keys
    if isinstance(value, list):
        keys: set[str] = set()
        for child in value:
            keys.update(_extension_keys(child))
        return keys
    return set()


def test_swagger_ui_and_openapi_json_are_published(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SKETCH2LIFE_ENV", "local")
    monkeypatch.setenv("SKETCH2LIFE_STORAGE_EXAMPLE_ENABLED", "true")
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    app = create_app()
    runtime = getattr(app.state, "be1_runtime", None)
    try:
        client = TestClient(app)
        docs_response = client.get("/docs")
        openapi_response = client.get("/openapi.json")
        assert docs_response.status_code == 200
        assert "swagger-ui" in docs_response.text
        assert openapi_response.status_code == 200
        published_spec = openapi_response.json()
        assert published_spec["openapi"] == "3.1.0"
        assert published_spec["info"]["title"] == "Sketch2Life FE API"
        assert published_spec["tags"] == SRS_V22_TAGS + [{"name": "Admin", "description": "Administration, identity and school-scoped feedback."}]
        assert len(published_spec["info"]["description"].split()) <= 55
        assert all(len(tag["description"].split()) <= 9 for tag in published_spec["tags"])
        assert "ApiError" in published_spec["components"]["schemas"]
        assert "Be1Error" not in published_spec["components"]["schemas"]
        assert all(
            "BE1" not in response.get("description", "")
            for path_item in published_spec["paths"].values()
            for operation in path_item.values()
            for response in operation.get("responses", {}).values()
        )
        published_operations = {
            (method.lower(), path)
            for path, path_item in published_spec["paths"].items()
            for method in path_item
            if method.lower() in HTTP_METHODS
        }
        assert published_operations == set(SRS_V22_INCLUDED_OPERATIONS) | ADMIN_OPERATIONS
    finally:
        if runtime is not None and runtime.engine is not None:
            runtime.engine.dispose()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


@pytest.fixture
def runtime_openapi(monkeypatch: pytest.MonkeyPatch) -> Iterator[dict[str, Any]]:
    monkeypatch.setenv("SKETCH2LIFE_ENV", "local")
    monkeypatch.setenv("SKETCH2LIFE_SYNTHETIC_PILOT_ENABLED", "true")
    monkeypatch.setenv("SKETCH2LIFE_STORAGE_EXAMPLE_ENABLED", "true")
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    app = create_app()
    runtime = getattr(app.state, "be1_runtime", None)
    try:
        app.openapi()
        yield app.state.runtime_openapi_schema
    finally:
        if runtime is not None and runtime.engine is not None:
            runtime.engine.dispose()
        monkeypatch.undo()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def test_runtime_openapi_preserves_local_synthetic_examples(
    runtime_openapi: dict[str, Any],
) -> None:
    session_example = runtime_openapi["paths"]["/v1/sessions"]["post"]["requestBody"][
        "content"
    ]["application/json"]["examples"]["localSyntheticSession"]["value"]
    assert session_example["actor_ref"] == "demo:local"
    assert session_example["expected_session_version"] == 0
    assert session_example["payload"] == {"operation": "CREATE_SESSION"}

    image_operation = runtime_openapi["paths"]["/v1/sessions/{session_id}/media/image"]["post"]
    image_example = image_operation["requestBody"]["content"]["multipart/form-data"]["examples"][
        "localSyntheticPng"
    ]["value"]
    assert image_example["image"] == "synthetic-demo.png"
    assert image_example["normalization_policy"] == "IDENTITY_V1"
    image_headers = {
        parameter["name"]: parameter["example"]
        for parameter in image_operation["parameters"]
        if parameter.get("in") == "header" and "example" in parameter
    }
    assert image_headers["X-Actor-Ref"] == "demo:local"
    assert image_headers["X-Synthetic-Non-Child-Confirmed"] is True
    assert "without invoking an AI provider" in image_operation["description"]


def test_runtime_openapi_matches_all_mounted_rev37_operations_and_records_unmounted_candidates(
    runtime_openapi: dict[str, Any],
) -> None:
    spec = runtime_openapi
    operations = {
        (method.lower(), path): operation
        for path, path_item in spec["paths"].items()
        for method, operation in path_item.items()
        if method.lower() in HTTP_METHODS
    }

    assert spec["openapi"] == "3.1.0"
    assert spec["tags"] == public_tags(TAG_DESCRIPTIONS)
    assert len(operations) == 197 + len(ADMIN_OPERATIONS - PR22_UNCATALOGUED_OPERATIONS) + len(QUOTA_OPERATIONS)
    catalog_operations = set(MOUNTED_OPERATIONS)
    catalog_paths = {path for _method, path in catalog_operations}
    # FEAT-066 T-2a: five generic upload-session operations (four paths) join the catalog.
    # FEAT-066 T-3a: three lesson occurrence operations (two paths) join it too.
    # FEAT-066 T-3b: five document operations (four paths) join it as well.
    # FEAT-066 T-3c: the keyed text edit is one more operation on an existing path.
    # FEAT-066 T-3d: four plan operations (create, list, read, confirm) on three new paths.
    # FEAT-066 T-7b: the class suspend and archive commands, two new paths.
    # FEAT-066 T-7d: the enrollment move, one new path.
    # FEAT-066 T-2b: the Parent run drawing attach, one new path.
    # FEAT-066 T-2c: the run idea, the transcript read and its confirmation, three new paths.
    # FEAT-066 T-2d: the story rewrite, one new path.
    # FEAT-066 T-1a: the Parent video request, one new path.
    # FEAT-066 T-1b: the video-unsuitable and complete commands, two new paths.
    # FEAT-066 T-1c: the playback grant and the stream route, two new paths (the run detail read
    # stays one catalogued operation).
    # FEAT-066 T-8a: the notification inbox page and the two mark-read commands, three new paths.
    # FEAT-066 T-4b1: the child selection, its read and its confirmation, three new paths.
    # FEAT-066 T-5a: the class projection confirmation and its token, two new paths.
    # FEAT-066 goal v4 T-2e-a: the activity list and the activity selection, two new paths.
    assert len(catalog_paths) == 154
    assert MOUNTED_OPERATION_COUNT == 135
    assert (
        len(catalog_operations)
        == MOUNTED_OPERATION_COUNT
        + 5 + 3 + 5 + 1 + 4 + 2 + 1 + 1 + 3 + 1 + 1 + 2 + 2 + 3 + 3 + 2 + 2
        == 176
    )
    assert set(operations) - catalog_operations == (
        PILOT_ONLY_OPERATIONS | PR22_UNCATALOGUED_OPERATIONS | ADMIN_OPERATIONS | QUOTA_OPERATIONS
    )
    assert PILOT_ONLY_OPERATIONS.isdisjoint(MOUNTED_OPERATIONS)
    assert PR22_UNCATALOGUED_OPERATIONS.isdisjoint(MOUNTED_OPERATIONS)
    profile_lookup = operations[
        (
            "get",
            "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/pilot-profiles",
        )
    ]
    assert "x-contract-surface" not in profile_lookup
    assert len(PILOT_ONLY_OPERATIONS) == 5
    assert len(PR22_UNCATALOGUED_OPERATIONS) == 16

    assert (
        "post",
        "/api/be1/v1/organizations/{organization_id}/assignments",
    ) not in operations
    assert (
        "delete",
        "/api/be1/v1/organizations/{organization_id}/assignments/{assignment_id}",
    ) not in operations
    assignment_key = ("post", "/api/be1/v1/classes/{class_id}/assignments")
    assert assignment_key in operations
    assignment_body = operations[assignment_key]["requestBody"]["content"][
        "application/json"
    ]
    assignment_schema_name = next(iter(_schema_refs(assignment_body["schema"])))
    assert set(spec["components"]["schemas"][assignment_schema_name]["properties"]) == {
        "candidate_ref"
    }

    profile_key = (
        "post",
        "/api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles",
    )
    profile_body = operations[profile_key]["requestBody"]["content"][
        "application/json"
    ]
    profile_schema_name = next(iter(_schema_refs(profile_body["schema"])))
    profile_schema = spec["components"]["schemas"][profile_schema_name]
    # T-7c: the class is the path only; `consent_id` is the optional real-data reference.
    assert set(profile_schema["properties"]) == {
        "display_name",
        "age_months",
        "consent_id",
    }
    assert set(profile_schema["required"]) == {"display_name", "age_months"}
    assert profile_schema["properties"]["age_months"]["minimum"] == 36
    assert profile_schema["properties"]["age_months"]["maximum"] == 120

    for key, contract in MOUNTED_OPERATIONS.items():
        operation = operations[key]
        if key in {
            ("post", "/v1/sessions"),
            ("post", "/v1/sessions/{session_id}/media/image"),
            RESTORE_CHECKPOINT_OPERATION_KEY,
            PORTFOLIO_OPERATION_KEY,
            (
                "get",
                "/api/be1/v1/organizations/{organization_id}/classes/"
                "{class_id}/profiles/{child_id}/portfolio",
            ),
        }:
            assert operation["description"].startswith(contract["purpose"])
        else:
            assert operation["description"] == contract["purpose"]
        assert operation["tags"] == [public_tag_name(contract["tag"])]
        assert contract["tag"] in TAG_DESCRIPTIONS
        if contract["authentication"] == "HTTPBearer (bearer)":
            assert operation["security"] == [{"HTTPBearer": []}]
        else:
            assert "security" not in operation
        assert operation.get("responses")
        assert operation.get("operationId")
        declared_responses = {
            response["status"]: response
            for response in published_responses(key, contract["responses"])
        }
        assert set(operation["responses"]) == set(declared_responses)
        for status, response_contract in declared_responses.items():
            runtime_response = operation["responses"][status]
            expected_response_description = (
                RESTORE_CHECKPOINT_RESPONSE_DESCRIPTIONS.get(
                    status, response_contract["description"]
                )
                if key == RESTORE_CHECKPOINT_OPERATION_KEY
                else response_contract["description"]
            )
            assert runtime_response["description"] == expected_response_description
            media_type = response_contract["media_type"]
            if media_type:
                assert set(runtime_response["content"]) == {media_type}
                response_schema = runtime_response["content"][media_type]["schema"]
                schema_name = response_contract["schema_name"]
                if schema_name == "object":
                    assert response_schema.get("type") == "object"
                elif schema_name == "binary":
                    assert response_schema == {"type": "string", "format": "binary"}
                elif schema_name:
                    list_schema = re.match(r"^list\[([A-Za-z][A-Za-z0-9_]*)", schema_name)
                    expected_schema = list_schema.group(1) if list_schema else schema_name
                    assert expected_schema in _schema_refs(response_schema)
                    if list_schema:
                        assert response_schema.get("type") == "array"
            else:
                assert not runtime_response.get("content")

        expected_parameters = {}
        for location, raw_name, _type in CONTRACT_PARAMETER.findall(contract["request_inputs"]):
            required = raw_name.endswith("*")
            name = raw_name.removesuffix("*")
            expected_parameters[(location, name)] = required
        actual_parameters = {
            (parameter["in"], parameter["name"]): bool(parameter.get("required"))
            for parameter in operation.get("parameters", [])
        }
        assert actual_parameters == expected_parameters

        expected_bodies = CONTRACT_REQUEST_BODY.findall(contract["request_inputs"])
        request_body = operation.get("requestBody")
        assert bool(request_body) == bool(expected_bodies)
        for media_type, requiredness, schema_name in expected_bodies:
            assert media_type in request_body["content"]
            assert bool(request_body.get("required")) == (requiredness == "required")
            if schema_name == "object":
                assert request_body["content"][media_type]["schema"].get("type") == "object"
            elif schema_name == "binary":
                # FEAT-066 T-2a: the raw upload part is a binary body, not a component.
                assert request_body["content"][media_type]["schema"] == {
                    "type": "string",
                    "format": "binary",
                }
            else:
                assert schema_name in _schema_refs(request_body["content"][media_type]["schema"])

        if key in UPLOAD_TRANSPORT_TOO_LARGE_OPERATIONS:
            response_413 = operation["responses"]["413"]
            assert "x-contract-runtime-mismatch" not in response_413
            schema = response_413["content"]["application/json"]["schema"]
            assert schema == {"$ref": "#/components/schemas/MobileWorkflowResultV1"}

        if key[1].startswith("/api/be1/v1/"):
            # CONV-1 (FEAT-066 D-066-71): 400 replaces the validation 422; 404 is explicit;
            # 422 stays only on the named kept-422 operations (grouped under "default").
            kept_422 = key in BE1_KEPT_422_OPERATIONS
            if key == RESTORE_CHECKPOINT_OPERATION_KEY:
                expected_statuses = {
                    "200", "400", "401", "403", "404", "409", "410", "500", "503"
                }
                expected_default_codes = None
            elif key == PORTFOLIO_OPERATION_KEY:
                expected_statuses = {"400", "401", "403", "404", "409", "default"}
                expected_default_codes = "410, 413, 415, 429, 500, 503"
            else:
                success_status = next(
                    row["status"]
                    for row in declared_responses.values()
                    if row["status"] not in {"400", "401", "403", "404", "default"}
                )
                expected_statuses = {
                    success_status,
                    "400",
                    "401",
                    "403",
                    "404",
                    "default",
                }
                expected_default_codes = (
                    "409, 410, 413, 415, 422, 429, 500, 503"
                    if kept_422
                    else "409, 410, 413, 415, 429, 500, 503"
                )
            assert set(operation["responses"]) == expected_statuses
            if expected_default_codes is not None:
                default_response = operation["responses"]["default"]
                assert expected_default_codes in default_response["description"]
                assert default_response["content"]["application/json"]["schema"] == {
                    "$ref": "#/components/schemas/Be1Error"
                }

    parent_get = operations[("get", "/v1/parent/profiles/{profile_id}")]
    invalid_uuid_response = parent_get["responses"]["400"]
    assert "ParentErrorResponse" in _schema_refs(
        invalid_uuid_response["content"]["application/json"]["schema"]
    )
    parent_patch = operations[("patch", "/v1/parent/profiles/{profile_id}")]
    assert "ParentProfileView" in _schema_refs(
        parent_patch["responses"]["200"]["content"]["application/json"]["schema"]
    )
    parent_get_schemas = _schema_refs(
        parent_get["responses"]["200"]["content"]["application/json"]["schema"]
    )
    assert {"ParentProfileView", "ParentProfileDeletePendingView"} <= parent_get_schemas
    parent_list = operations[("get", "/v1/parent/profiles")]
    assert "ParentProfileListView" in _schema_refs(
        parent_list["responses"]["200"]["content"]["application/json"]["schema"]
    )
    parent_delete = operations[("delete", "/v1/parent/profiles/{profile_id}")]
    assert "ParentProfileDeletePendingView" in _schema_refs(
        parent_delete["responses"]["202"]["content"]["application/json"]["schema"]
    )
    # FEAT-066 T0.9: a caller who is not an active Parent is out of scope (SRS l.864-865), so
    # every M2 Parent profile and StoryRun operation documents the uniform 404 and no 403.
    assert "404" in parent_list["responses"]
    assert "404" in parent_delete["responses"]
    assert "403" not in parent_list["responses"]
    assert "403" not in parent_delete["responses"]
    for (method, path), operation in operations.items():
        if path.startswith(("/v1/parent/profiles", "/v1/story-runs")):
            assert "404" in operation["responses"], (method, path)
            assert "403" not in operation["responses"], (method, path)

    # FR-C-08 (Contract Draft 11 §3.3-§3.4): GET and the four replaying operations declare the
    # union of their current envelope and the content-free lifecycle envelope.
    for (method, path), status, current in (
        (("get", "/v1/story-runs/{run_id}"), "200", "ParentStoryRunEnvelopeV1"),
        (("post", "/v1/story-runs"), "201", "ParentStoryRunEnvelopeV1"),
        (
            ("post", "/v1/story-runs/{run_id}/context-confirmation"),
            "200",
            "ParentStoryRunEnvelopeV1",
        ),
        (
            # FEAT-066 T-2d (SRS l.1666): the subject confirmation answers 202.
            ("post", "/v1/story-runs/{run_id}/subject-confirmation"),
            "202",
            "ParentSubjectConfirmationResponseV1",
        ),
        (
            ("post", "/v1/story-runs/{run_id}/script-confirmation"),
            "200",
            "ParentStoryRunEnvelopeV1",
        ),
    ):
        success = operations[(method, path)]["responses"][status]["content"]["application/json"]
        assert {current, "ParentStoryRunLifecycleEnvelopeV1"} <= _schema_refs(success["schema"])
    lifecycle_schema = spec["components"]["schemas"]["ParentStoryRunLifecycleProjectionV1"]
    assert set(lifecycle_schema["properties"]) == {
        "run_id",
        "run_state",
        "revision",
        "version",
        "lifecycle_request_ref",
        "purge_state",
    }
    for key in (("post", "/v1/story-runs/{run_id}/cancel"), ("delete", "/v1/story-runs/{run_id}")):
        accepted = operations[key]["responses"]["202"]["content"]["application/json"]
        assert _schema_refs(accepted["schema"]) == {"ParentStoryRunLifecycleEnvelopeV1"}
        key_parameter = next(
            parameter
            for parameter in operations[key]["parameters"]
            if parameter["in"] == "header" and parameter["name"] == "Idempotency-Key"
        )
        assert key_parameter.get("required") is not True
        assert "maxLength" not in str(key_parameter["schema"])

    # T0.1 (C-D5): the four keyed Parent StoryRun commands publish a required key of 1-128
    # characters; create class publishes a required key too.
    for key in (
        ("post", "/v1/story-runs"),
        ("post", "/v1/story-runs/{run_id}/context-confirmation"),
        ("post", "/v1/story-runs/{run_id}/subject-confirmation"),
        ("post", "/v1/story-runs/{run_id}/script-confirmation"),
        ("post", "/api/be1/v1/organizations/{organization_id}/classes"),
    ):
        key_parameter = next(
            parameter
            for parameter in operations[key]["parameters"]
            if parameter["in"] == "header" and parameter["name"] == "Idempotency-Key"
        )
        assert key_parameter["required"] is True
        assert key_parameter["schema"]["minLength"] == 1
        assert key_parameter["schema"]["maxLength"] == 128

    candidate_keys = {(item["method"], item["path"]) for item in UNMOUNTED_OPERATIONS}
    assert len(candidate_keys) == UNMOUNTED_OPERATION_COUNT == 11
    assert not candidate_keys.intersection(operations)

    for list_key in (
        (
            "get",
            "/api/lesson-library/v1/organizations/{organization_id}/access-grants",
        ),
        (
            "get",
            "/api/lesson-library/v1/organizations/{organization_id}/parent-groups",
        ),
        # SRS 21.1: every cursor list defaults to 25 (goal v2 task C4).
        ("get", "/api/lesson-library/v1/organizations/{organization_id}/lessons"),
        ("get", "/api/lesson-library/v1/me/lessons"),
        ("get", "/api/lesson-library/v1/me/lesson-invitations"),
        ("get", "/api/lesson-library/v1/me/parent-group-invitations"),
    ):
        limit_parameter = next(
            parameter
            for parameter in operations[list_key]["parameters"]
            if parameter["in"] == "query" and parameter["name"] == "limit"
        )
        assert limit_parameter["schema"]["default"] == 25
        assert limit_parameter["schema"]["minimum"] == 1
        assert limit_parameter["schema"]["maximum"] == 100

    for operation_key in IDEMPOTENCY_MISMATCH_OPERATION_KEYS:
        mismatch_response = operations[operation_key]["responses"]["400"]
        assert "INVALID_IDEMPOTENCY_KEY" in mismatch_response["description"]
        assert "Be1Error" in _schema_refs(
            mismatch_response["content"]["application/json"]["schema"]
        )
    assert len(IDEMPOTENCY_MISMATCH_OPERATION_KEYS) == 35
    assert set(IDEMPOTENCY_MISMATCH_OPERATION_KEYS) == (
        EXPECTED_IDEMPOTENCY_MISMATCH_OPERATION_KEYS
    )

    assert not _extension_keys(spec)

    assert len(spec["tags"]) == 23
    assert all(tag.get("description") for tag in spec["tags"])

    operation_ids = [operation["operationId"] for operation in operations.values()]
    assert len(operation_ids) == len(set(operation_ids))
    json.dumps(spec, ensure_ascii=False)


DESCRIPTION_SUFFIXES = {
    ("post", "/v1/sessions"): (
        "**Local synthetic Try it out:** use a fresh UUIDv4 for `session_id`. "
        "Copy `observed_session_version` from the response into the next request. "
        "This demo session is process-local and makes no persistent database write."
    ),
    ("post", "/v1/sessions/{session_id}/media/image"): (
        "**Local synthetic Try it out:** first call `POST /v1/sessions`, then use its "
        "`session_id` and `observed_session_version`. Select the supplied synthetic "
        "non-child PNG above, keep `normalization_policy` as `IDENTITY_V1`, and set "
        "`X-Synthetic-Non-Child-Confirmed` to `true`. The upload is processed locally "
        "without invoking an AI provider."
    ),
    PORTFOLIO_OPERATION_KEY: (
        "**Implementation gap:** the Rev37 catalog lists a 200 response, but the current "
        "handler has no success path. After profile lookup it returns `409 "
        "CONSENT_NOT_EFFECTIVE` until an approved portfolio-purpose verifier is available."
    ),
    RESTORE_CHECKPOINT_OPERATION_KEY: (
        "**Access:** a valid bearer token and a Teacher or School Admin "
        "assignment for the class. Effective group consent and an existing "
        "checkpoint are required. This operation is available in local/test "
        "until production checkpoint storage is configured."
    ),
}


def test_runtime_openapi_descriptions_equal_catalog_purpose_and_known_suffixes(
    runtime_openapi: dict[str, Any],
) -> None:
    assert set(DESCRIPTION_SUFFIXES) <= set(MOUNTED_OPERATIONS)
    for key, contract in MOUNTED_OPERATIONS.items():
        method, path = key
        operation = runtime_openapi["paths"][path][method]
        suffix = DESCRIPTION_SUFFIXES.get(key)
        expected = contract["purpose"] if suffix is None else f"{contract['purpose']}\n\n{suffix}"
        assert operation["description"] == expected, key
        assert operation["tags"] == [public_tag_name(contract["tag"])], key


def test_runtime_openapi_operation_ids_are_non_empty_and_unique(
    runtime_openapi: dict[str, Any],
) -> None:
    operation_ids = [
        operation.get("operationId")
        for path_item in runtime_openapi["paths"].values()
        for method, operation in path_item.items()
        if method.lower() in HTTP_METHODS
    ]
    assert len(operation_ids) == 197 + len(ADMIN_OPERATIONS - PR22_UNCATALOGUED_OPERATIONS) + len(QUOTA_OPERATIONS)
    assert all(isinstance(value, str) and value for value in operation_ids)
    assert len(set(operation_ids)) == len(operation_ids)


def test_platform_admin_account_routes_publish_cursor_key_and_mismatch(
    runtime_openapi: dict[str, Any],
) -> None:
    """The uncatalogued account routes publish cursor paging and the Idempotency-Key header."""
    base = "/api/platform-admin/v1/accounts"
    listing = runtime_openapi["paths"][base]["get"]
    names = {parameter["name"]: parameter for parameter in listing["parameters"]}
    assert "cursor" in names
    assert names["limit"]["schema"]["default"] == 25
    assert names["limit"]["schema"]["maximum"] == 100
    for method, path in (("post", base), ("patch", base + "/{account_id}")):
        operation = runtime_openapi["paths"][path][method]
        assert any(p["name"] == "Idempotency-Key" for p in operation["parameters"])


def test_teacher_candidate_route_publishes_paging(runtime_openapi: dict[str, Any]) -> None:
    """FEAT-066 M9-B: the runtime-only candidate list shows limit 25/100 and an opaque cursor."""
    operation = runtime_openapi["paths"][
        "/api/be1/v1/organizations/{organization_id}/teacher-candidates"
    ]["get"]
    names = {parameter["name"]: parameter for parameter in operation["parameters"]}
    assert names["limit"]["schema"]["default"] == 25
    assert names["limit"]["schema"]["maximum"] == 100
    assert "cursor" in names


def test_t7a_class_and_consent_lists_publish_paging(runtime_openapi: dict[str, Any]) -> None:
    """T-7a (SRS l.1640): A07 and A10 show limit 25/1/100, an opaque cursor and the 400 row."""
    base = "/api/be1/v1/organizations/{organization_id}/classes"
    for path in (base, base + "/{class_id}/consents"):
        operation = runtime_openapi["paths"][path]["get"]
        names = {parameter["name"]: parameter for parameter in operation["parameters"]}
        assert names["limit"]["schema"]["default"] == 25
        assert names["limit"]["schema"]["minimum"] == 1
        assert names["limit"]["schema"]["maximum"] == 100
        assert names["cursor"]["in"] == "query"
        assert not names["cursor"].get("required")
        assert "400" in operation["responses"]
        success = operation["responses"]["200"]["content"]["application/json"]["schema"]
        listing = success["oneOf"][0] if "oneOf" in success else success
        assert listing["properties"]["next_cursor"]["type"] == ["string", "null"]
        assert "next_cursor" in listing["required"]


def test_t7a_roster_and_consent_reads_publish_both_role_bodies(
    runtime_openapi: dict[str, Any],
) -> None:
    """T-7a (D-066-75 CM-3, CM-4): A09 and A10 publish a Teacher and a Manager body under oneOf."""
    base = "/api/be1/v1/organizations/{organization_id}/classes/{class_id}"
    expected = {
        base + "/profiles": ("Be1ManagedProfileListV1", "Be1ClassRosterSummaryV1"),
        base + "/consents": ("Be1ConsentListV1", "Be1ConsentListManagerV1"),
    }
    for path, (teacher_contract, manager_contract) in expected.items():
        media = runtime_openapi["paths"][path]["get"]["responses"]["200"]["content"][
            "application/json"
        ]
        variants = media["schema"]["oneOf"]
        assert media["schema"]["type"] == "object"
        assert [variant["properties"]["contract"]["enum"] for variant in variants] == [
            [teacher_contract],
            [manager_contract],
        ]
        assert {"syntheticResponse"} < set(media["examples"])
        assert len(media["examples"]) == 2
        values = {example["value"]["contract"] for example in media["examples"].values()}
        assert values == {teacher_contract, manager_contract}
    summary_schema = runtime_openapi["paths"][base + "/profiles"]["get"]["responses"]["200"][
        "content"
    ]["application/json"]["schema"]["oneOf"][1]
    assert set(summary_schema["properties"]) == {"contract", "class_id", "active_profile_count"}
    manager_items = runtime_openapi["paths"][base + "/consents"]["get"]["responses"]["200"][
        "content"
    ]["application/json"]["schema"]["oneOf"][1]["properties"]["items"]["items"]
    assert set(manager_items["properties"]) == {"consent_id", "state", "effective"}


def test_t7a2_child_profile_reads_publish_the_403_and_404_rows(
    runtime_openapi: dict[str, Any],
) -> None:
    """T-7a2: the pilot-profiles list, the session roster and the portfolio read keep a 403 row
    (in scope, not the class's own Teacher) and a 404 row (out of scope); no catalog edit."""
    base = "/api/be1/v1/organizations/{organization_id}"
    for path in (
        base + "/sessions/{session_id}/pilot-profiles",
        base + "/sessions/{session_id}/roster",
        base + "/classes/{class_id}/profiles/{child_id}/portfolio",
    ):
        responses = runtime_openapi["paths"][path]["get"]["responses"]
        assert "403" in responses, path
        assert "404" in responses, path
