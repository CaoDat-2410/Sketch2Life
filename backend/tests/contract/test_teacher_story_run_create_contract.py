"""FEAT-066 T-4b2: ``POST /v1/story-runs`` for a Teacher, at the HTTP and the document level.

Plan D1 and D10 (SRS l.1445-1449, l.1663), the R2 findings N-2 (a valid OpenAPI document) and N-6
(golden answers that include the header combinations). The Parent side is pinned against
``golden/story_run_create_head.json``, recorded at HEAD ``82c59bdb`` with
``story_run_create_matrix``:
every combination of role, body, key and content type that a Parent, a Manager, a Platform Admin, an
unauthenticated caller or a Teacher with a non-Teacher body can send must answer byte for byte as
before (request and correlation ids masked). No database is used: a fake session knows the identity
rows and nothing else, so a case that would reach a repository fails the test.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
import story_run_create_matrix as matrix  # type: ignore[import-not-found]
from fastapi import FastAPI
from fastapi.testclient import TestClient

import sketch2life.interfaces.http.app as app_module
import sketch2life.interfaces.http.be1_runtime as runtime_module
from sketch2life.contracts.schemas.parent_story_runs import ParentStoryRunCreateRequestV1
from sketch2life.contracts.schemas.teacher_story_runs import TeacherStoryRunCreateRequestV1
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.interfaces.http.routers.story_run_create_dispatch import (
    RoleDispatchedCreateRoute,
)

GOLDEN = Path(__file__).parent / "golden" / "story_run_create_head.json"


@pytest.fixture(scope="module")
def application() -> Iterator[FastAPI]:
    patcher = pytest.MonkeyPatch()
    patcher.setitem(Settings.model_config, "env_file", None)
    patcher.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    patcher.setenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", "0")
    settings = Settings(
        env="test",
        auth_provider="firebase",
        firebase_project_id="synthetic-t4b2-project",
        _env_file=None,  # type: ignore[call-arg]
    )
    patcher.setattr(app_module, "get_settings", lambda: settings)
    patcher.setattr(
        runtime_module, "get_core_database_settings", lambda: SimpleNamespace(database_url=None)
    )
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    try:
        built = app_module.create_app()
        matrix.install_overrides(built, runtime_module)
        yield built
    finally:
        patcher.undo()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


@pytest.fixture(scope="module")
def client(application: FastAPI) -> Iterator[TestClient]:
    with TestClient(application, raise_server_exceptions=False) as test_client:
        yield test_client


# ----------------------------------------------------------------------------- Parent golden
def test_every_non_teacher_answer_equals_the_golden_recorded_at_head(client: TestClient) -> None:
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    current = matrix.run_matrix(client, include_teacher_branch=False)
    assert set(current) == set(golden), "the matrix changed: record the golden again at HEAD"
    different = [key for key in golden if current[key] != golden[key]]
    assert different == [], different[:5]
    # the matrix is not trivial: validation, auth and role answers are all in it
    assert {entry["status"] for entry in golden.values()} == {400, 401, 404}
    assert len(golden) > 600


def test_the_golden_covers_the_header_and_content_combinations_of_the_review() -> None:
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    # R2 N-6: a non-Teacher with a Teacher-shaped body AND a missing or bad header, an
    # unauthenticated Teacher-shaped body (401 before any body error), and a Teacher with an
    # empty body
    for role in ("parent", "manager", "platform", "inactive_teacher", "other_issuer_teacher"):
        for key in ("key_missing", "key_bad", "key_ok"):
            assert f"{role}|teacher_full|{key}|json" in golden
    assert golden["anonymous|teacher_full|key_ok|json"]["status"] == 401
    assert golden["teacher|empty|key_ok|json"]["status"] == 400
    assert golden["teacher|parent_valid|key_ok|json"]["status"] == 404  # OPEN-7, as today


# ----------------------------------------------------------------------------- Teacher branch
def _post(client: TestClient, body: object, *, key: str | None = "key-1") -> Any:
    headers = {"X-Test-Principal": "teacher", "Content-Type": "application/json"}
    if key is not None:
        headers["Idempotency-Key"] = key
    payload = body if isinstance(body, bytes) else json.dumps(body).encode()
    return client.post("/v1/story-runs", content=payload, headers=headers)


def test_a_multi_child_body_is_422_before_the_model_is_validated(client: TestClient) -> None:
    variants = (
        {**matrix.TEACHER_BODY, "profile_refs": ["a", "b"]},
        {**matrix.TEACHER_BODY, "child_ids": ["a"]},
        {**matrix.TEACHER_BODY, "children": []},
        {**matrix.TEACHER_BODY, "profiles": {}},
        {**matrix.TEACHER_BODY, "profile_ref": [matrix.TEACHER_BODY["profile_ref"]]},
        {**matrix.TEACHER_BODY, "profile_ref": {"kind": "MANAGED_PROFILE", "id": ["a", "b"]}},
        {"profile_refs": ["a", "b"]},
    )
    for body in variants:
        response = _post(client, body)
        assert response.status_code == 422, body
        assert response.json()["code"] == "MULTI_CHILD_NOT_SUPPORTED"
        assert response.json()["message"] == "Mỗi lượt kể chuyện chỉ dành cho một trẻ."


def test_an_invalid_teacher_body_is_400_with_field_names_and_no_values(client: TestClient) -> None:
    response = _post(client, {"profile_ref": {"kind": "MANAGED_PROFILE", "id": "child"}})
    assert response.status_code == 400
    body = response.json()
    assert body["code"] == "INVALID_REQUEST"
    fields = {item["field"] for item in body["field_errors"]}
    assert {"occurrence_id", "plan", "activity_id", "selection_id", "selection_sha256"} <= fields
    assert "child" not in response.text
    extra = _post(client, {**matrix.TEACHER_BODY, "child_name": "x"})
    assert extra.status_code == 400
    assert {item["field"] for item in extra.json()["field_errors"]} == {"child_name"}
    bad_plan = _post(
        client, {**matrix.TEACHER_BODY, "plan": {"revision_no": "1", "plan_hash": "x"}}
    )
    assert {item["field"] for item in bad_plan.json()["field_errors"]} == {
        "plan.revision_no",
        "plan.plan_hash",
    }
    bad_selection = _post(client, {**matrix.TEACHER_BODY, "selection_id": "not-a-uuid"})
    assert {item["field"] for item in bad_selection.json()["field_errors"]} == {"selection_id"}


def test_a_teacher_key_error_is_a_plain_400_without_a_field_item(client: TestClient) -> None:
    for key in (None, "bad key"):
        response = _post(client, matrix.TEACHER_BODY, key=key)
        assert response.status_code == 400
        assert response.json()["code"] == "INVALID_REQUEST"
        assert response.json()["field_errors"] is None


def test_a_teacher_with_a_parent_shaped_or_unreadable_body_gets_todays_answers(
    client: TestClient,
) -> None:
    valid_parent = _post(client, {"parent_profile_id": matrix.GOOD_UUID})
    assert valid_parent.status_code == 404  # the uniform 404 of the Parent route (OPEN-7)
    assert valid_parent.json()["code"] == "RESOURCE_NOT_FOUND"
    for raw in (b"", b"{", b"[1]", b'"x"'):
        assert _post(client, raw).status_code == 400


# ----------------------------------------------------------------------------- the route table
def test_the_create_route_is_one_route_with_the_dispatch_class(application: FastAPI) -> None:
    creates = [
        candidate
        for route in application.routes
        for candidate in (
            getattr(route, "original_router", None) or SimpleNamespace(routes=[route])
        ).routes
        if getattr(candidate, "path", None) == "/v1/story-runs"
        and "POST" in (getattr(candidate, "methods", None) or set())
    ]
    assert len(creates) == 1
    assert isinstance(creates[0], RoleDispatchedCreateRoute)
    assert creates[0].status_code == 201
    # the hidden Teacher route is not mounted and not published
    assert creates[0]._teacher_route.include_in_schema is False
    assert creates[0]._teacher_route not in application.routes


# ----------------------------------------------------------------------------- the document
def _refs(value: Any, found: set[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "$ref" and isinstance(child, str):
                found.add(child)
            else:
                _refs(child, found)
    elif isinstance(value, list):
        for child in value:
            _refs(child, found)


def test_the_published_document_has_no_dangling_ref_and_a_proper_one_of(
    application: FastAPI,
) -> None:
    document = application.openapi()
    components = document["components"]["schemas"]
    found: set[str] = set()
    _refs(document, found)
    dangling = sorted(
        ref
        for ref in found
        if not ref.startswith("#/components/schemas/") or ref.rsplit("/", 1)[-1] not in components
    )
    assert dangling == []

    operation = document["paths"]["/v1/story-runs"]["post"]
    request_schema = operation["requestBody"]["content"]["application/json"]["schema"]
    # a oneOf of two refs, and nothing next to it (R2 N-2: no $ref with a sibling oneOf)
    assert set(request_schema) == {"oneOf"}
    assert request_schema["oneOf"] == [
        {"$ref": "#/components/schemas/ParentStoryRunCreateRequestV1"},
        {"$ref": "#/components/schemas/TeacherStoryRunCreateRequestV1"},
    ]
    assert operation["requestBody"]["required"] is True
    created = operation["responses"]["201"]["content"]["application/json"]["schema"]
    assert {member["$ref"].rsplit("/", 1)[-1] for member in created["anyOf"]} == {
        "ParentStoryRunEnvelopeV1",
        "ParentStoryRunLifecycleEnvelopeV1",
        "TeacherStoryRunEnvelopeV1",
    }
    # the Parent request schema itself is unchanged and the two bodies are disjoint
    parent = components["ParentStoryRunCreateRequestV1"]
    assert parent["required"] == ["parent_profile_id"]
    assert parent["additionalProperties"] is False
    teacher = components["TeacherStoryRunCreateRequestV1"]
    assert teacher["additionalProperties"] is False
    assert set(teacher["required"]) == {
        "profile_ref",
        "occurrence_id",
        "plan",
        "activity_id",
        "selection_id",
        "selection_sha256",
    }
    assert set(parent["properties"]).isdisjoint(set(teacher["properties"]))
    # the models that carry the schema stay the ones the route validates with
    assert set(ParentStoryRunCreateRequestV1.model_fields).isdisjoint(
        TeacherStoryRunCreateRequestV1.model_fields
    )


def test_the_teacher_view_is_published_on_every_route_that_can_return_it(
    application: FastAPI,
) -> None:
    document = application.openapi()
    teacher_envelope = "#/components/schemas/TeacherStoryRunEnvelopeV1"
    for path, method in (
        ("/v1/story-runs/{run_id}", "get"),
        ("/v1/story-runs/{run_id}/context-confirmation", "post"),
        ("/v1/story-runs/{run_id}/script-confirmation", "post"),
        ("/v1/story-runs", "post"),
    ):
        responses = document["paths"][path][method]["responses"]
        success = next(status for status in responses if status.startswith("2"))
        found: set[str] = set()
        _refs(responses[success], found)
        assert teacher_envelope in found, (path, method)
        assert "#/components/schemas/ParentStoryRunEnvelopeV1" in found, (path, method)
    active: set[str] = set()
    _refs(document["paths"]["/v1/story-runs/active/current"]["get"]["responses"]["200"], active)
    assert "#/components/schemas/TeacherActiveStoryRunEnvelopeV1" in active
    assert "#/components/schemas/ParentActiveStoryRunEnvelopeV1" in active


def test_no_teacher_schema_names_a_child_name_a_media_ref_or_a_seed(application: FastAPI) -> None:
    components = application.openapi()["components"]["schemas"]
    names = {
        field
        for name, schema in components.items()
        if "Teacher" in name
        for field in schema.get("properties", {})
    }
    assert names, "no Teacher schema was found"
    for forbidden in ("display_name", "child_name", "name", "seed", "draw_index", "asset_ref"):
        assert forbidden not in names, forbidden
    # the child is named by its opaque ref only
    assert {"profile_ref", "id"} <= names
