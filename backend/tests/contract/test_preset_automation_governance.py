"""Existing sole dispatcher +closed preset DTO; no production route mount."""

import json
from dataclasses import asdict

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from sketch2life.application.governance_dispatcher import GovernanceDispatcher
from sketch2life.application.preset_governance import bind_preset
from sketch2life.contracts.schemas.preset_automation import PresetCommand
from sketch2life.domain.learning_content.model import ContentError
from sketch2life.domain.preset_automation.model import PresetError, State
from sketch2life.interfaces.http.preset_automation_errors import preset_command_error
from sketch2life.interfaces.http.routers.learning_content import (
    GovernanceIdentity,
    build_governance_commands_router,
)
from tests.preset_automation_fixtures import body, command, environment


def published(env):
    memory, _, _, _, _, service = env
    service.execute("author", "school", command(), expected_revision=None)
    current = memory.data["school", "library", "preset"]
    for index, (action, actor, extra) in enumerate(
        [
            ("submit_review", "author", {}),
            (
                "record_review",
                "reviewer",
                {
                    "review": {
                        "review_id": "safety",
                        "dimension": "safety",
                        "policy_ref": "assumed-review-v1",
                        "decision": "approve",
                    }
                },
            ),
            (
                "record_review",
                "reviewer",
                {
                    "review": {
                        "review_id": "pedagogical",
                        "dimension": "pedagogical",
                        "policy_ref": "assumed-review-v1",
                        "decision": "approve",
                    }
                },
            ),
            (
                "publish",
                "publisher",
                {
                    "review_ref": {
                        "safety_review_id": "safety",
                        "pedagogical_review_id": "pedagogical",
                        "review_policy_version": "assumed-review-v1",
                    }
                },
            ),
        ]
    ):
        service.execute(
            actor,
            "school",
            command(action, key=f"cmd-{index}", record=current, **extra),
            expected_revision=current.revision,
        )
        current = memory.data["school", "library", "preset"]
    return current


def test_all_eight_actions_through_existing_strict_binding():
    env = environment()
    current = published(env)
    service = env[-1]
    dispatcher = GovernanceDispatcher(None, preset=bind_preset(service))
    result = dispatcher.execute_json(
        "publisher",
        "school",
        command("recall", record=current, reason="Source recalled").model_dump_json().encode(),
        expected_revision=current.revision,
    )
    assert result.record.state == "recalled" and result.record.hash == body().hash
    result = dispatcher.execute_json(
        "publisher",
        "school",
        command("archive", reason="No longer used").model_dump_json().encode(),
        expected_revision=result.current_revision,
    )
    assert result.record.state == "archived"
    assert len(dispatcher.request_schemas()) == 2


def test_request_changes_edit_and_old_version_recall():
    env = environment()
    memory, _, _, _, _, service = env
    current = published(env)
    edited = service.execute(
        "author",
        "school",
        command("edit", record=current, body=asdict(body(title="Edited"))),
        expected_revision=current.revision,
    )
    assert edited.record.version == 2 and edited.record.state == "draft"
    service.execute(
        "publisher",
        "school",
        command("recall", record=current, reason="Old version recalled"),
        expected_revision=edited.current_revision,
    )
    assert memory.data["school", "library", "preset"].versions[0].state is State.RECALLED
    current = memory.data["school", "library", "preset"]
    service.execute(
        "author",
        "school",
        command("submit_review", key="submit-v2", record=current, version=2),
        expected_revision=current.revision,
    )
    service.execute(
        "reviewer",
        "school",
        command("request_changes", record=current, version=2, reason="Change rule"),
        expected_revision=current.revision + 1,
    )
    assert memory.data["school", "library", "preset"].reason == "Change rule"


def test_replay_returns_historical_result_and_truthful_current_state():
    env = environment()
    current = published(env)
    result = env[-1].execute("author", "school", command(), expected_revision=None)
    assert result.replayed and result.record.state == "draft"
    assert result.current_state == "published" and result.current_revision == current.revision


@pytest.mark.parametrize(
    "field,value",
    [
        ("extra", True),
        ("policy_kind", "ai"),
        ("record_kind", "learning_content"),
        ("body", None),
        ("review", {}),
        ("record_id", "preset"),
        ("target_version", 1),
        ("target_hash", "a" * 64),
        ("reason", "unexpected"),
        ("action", "override"),
    ],
)
def test_closed_create_schema(field, value):
    data = command().model_dump(mode="json") | {field: value}
    with pytest.raises(ValidationError):
        PresetCommand.model_validate_json(json.dumps(data))


@pytest.mark.parametrize(
    "actor,org",
    [("child", "school"), ("author", "other"), ("teacher", "school"), ("publisher", "school")],
)
def test_action_capability_not_generic_authority(actor, org):
    env = environment()
    with pytest.raises(PresetError):
        env[-1].execute(actor, org, command(), expected_revision=None)
    assert not env[0].data


@pytest.mark.parametrize("denied", ["body", "create"])
def test_missing_adopted_schema_or_current_capability_denies(denied):
    env = environment()
    env[1].denied.add(denied)
    with pytest.raises(PresetError):
        env[-1].execute("author", "school", command(), expected_revision=None)
    assert not env[0].data


def test_failed_current_guard_rolls_back_whole_command():
    env = environment()
    env[1].fail_check_number = 3
    with pytest.raises(PresetError):
        env[-1].execute("author", "school", command(), expected_revision=None)
    assert not env[0].data and not env[0].history_data


def test_exact_preconditions_conflict_and_body_replay():
    env = environment()
    service = env[-1]
    service.execute("author", "school", command(), expected_revision=None)
    with pytest.raises(PresetError, match="IDEMPOTENCY_CONFLICT"):
        service.execute(
            "author", "school", command(body=asdict(body(title="Changed"))), expected_revision=None
        )
    with pytest.raises(PresetError, match="STALE_REVISION"):
        service.execute("author", "school", command("submit_review"), expected_revision=9)


def test_dispatcher_unbound_and_bad_payload_have_no_effect():
    env = environment()
    with pytest.raises(ContentError, match="UNAVAILABLE"):
        GovernanceDispatcher(None).execute_json(
            "author", "school", command().model_dump_json().encode()
        )
    dispatcher = GovernanceDispatcher(None, preset=bind_preset(env[-1]))
    data = command().model_dump(mode="json") | {"unknown": "no"}
    with pytest.raises(ContentError, match="INVALID"):
        dispatcher.execute_json("author", "school", json.dumps(data).encode())
    assert not env[0].data


def test_preset_uses_same_http_route_etag_and_safe_business_errors():
    env = environment()
    app = FastAPI()
    app.include_router(
        build_governance_commands_router(
            GovernanceDispatcher(None, preset=bind_preset(env[-1])),
            lambda _: GovernanceIdentity("author", "school"),
            max_body_bytes=8192,
        )
    )
    client = TestClient(app)
    url = "/api/collaboration/v1/governance/records"
    result = client.post(url, json=command().model_dump(mode="json"))
    assert result.status_code == 200 and result.headers["etag"] == '"1"'
    bad = client.post(
        url, json=command("submit_review").model_dump(mode="json"), headers={"if-match": '"8"'}
    )
    assert bad.status_code == 409 and bad.json()["error"]["code"] == "PRESET_STALE_REVISION"
    env[1].current = False
    denied = client.post(url, json=command().model_dump(mode="json"))
    assert denied.status_code == 403 and denied.headers["cache-control"] == "no-store"


@pytest.mark.parametrize(
    "code,status",
    [
        ("FORBIDDEN", 403),
        ("NOT_FOUND", 404),
        ("INVALID_BODY", 422),
        ("PRECONDITION_REQUIRED", 428),
        ("POLICY_UNAVAILABLE", 503),
        ("STORAGE_CORRUPT", 503),
    ],
)
def test_preset_http_safe_error_allowlist(code, status):
    assert preset_command_error(PresetError("PRESET_" + code)) == (status, "PRESET_" + code)


def test_unknown_adapter_error_not_exposed_in_public_envelope():
    assert preset_command_error(PresetError("synthetic_sensitive")) == (
        503,
        "PRESET_DEPENDENCY_UNAVAILABLE",
    )
