"""Typed DATA-33 content branch tests; no real authority or SQL execution."""

from __future__ import annotations

import json
from copy import deepcopy

import pytest
from pydantic import ValidationError

from sketch2life.contracts.schemas.ai_contract_candidates import ExactContentReviewCommandV1
from sketch2life.contracts.schemas.learning_content import (
    CONTENT_COMMAND_ADAPTER,
    ContentWrite,
    CreateContent,
    RecordContentReview,
)


def body() -> dict:
    return {
        "content_kind": "knowledge", "title": "Butterfly", "asset_refs": [],
        "source_refs": [{"ref": "source", "version": 1, "hash": "a" * 64}],
        "age_eligibility": {"min_months": 36, "max_months": 155, "age_policy_ref": "age-v1"},
        "purpose_codes": ["classroom"], "editorial_note": "", "content_policy_ref": "content-v1"}


def review() -> dict:
    return {
        "target_kind": "learning_content", "target_id": "record", "target_version": 1,
        "target_hash": "a" * 64, "source_context_revision": 1, "decision": "approve",
        "review_context": {"kind": "generic_library", "content_kind": "knowledge",
                           "age_policy_ref": "age-v1", "content_policy_ref": "content-v1",
                           "publication_scope": "school_library",
                           "review_purpose": "library_publication"},
        "audience_scope": {"publication_scope": "school_library", "age_policy_ref": "age-v1",
                          "purpose_codes": ["classroom"]},
        "review_dimension": "safety", "expected_review_revision": 1}


def command(action: str) -> dict:
    result = {"action": action, "record_kind": "learning_content", "client_request_id": "cmd-1"}
    if action == "create":
        return {**result, "content": body()}
    result.update(record_id="record", target_version=1, target_hash="a" * 64)
    if action == "edit":
        result["content"] = body()
    if action == "record_review":
        result["review"] = review()
    if action == "request_changes":
        changes = review()
        changes.update(decision="request_changes", reason="Needs changes")
        result.update(review=changes, reason="Needs changes")
    if action in {"recall", "archive"}:
        result["reason"] = "Content corrected"
    if action == "publish":
        result["review_ref"] = {"safety_review_id": "safety", "pedagogical_review_id": "teaching",
                                "review_policy_version": "policy"}
    return result


@pytest.mark.parametrize("action", [
    "create", "edit", "submit_review", "record_review",
    "request_changes", "publish", "recall", "archive",
])
def test_all_eight_actions(action: str) -> None:
    parsed = CONTENT_COMMAND_ADAPTER.validate_json(json.dumps(command(action)))
    assert parsed.action == action and parsed.record_kind == "learning_content"


def test_shared_review_type_is_not_reimplemented() -> None:
    parsed = CONTENT_COMMAND_ADAPTER.validate_json(json.dumps(command("record_review")))
    assert isinstance(parsed, RecordContentReview)
    assert type(parsed.review) is ExactContentReviewCommandV1
    assert "session_id" not in parsed.review.review_context.model_dump()


@pytest.mark.parametrize(("field", "value"), [
    ("organization_id", "other"), ("authored_by", "fake"), ("state", "published"),
    ("classification", "generic"), ("token", "not-a-credential"),
])
def test_client_cannot_set_server_authority_fields(field: str, value: str) -> None:
    payload = command("create")
    payload[field] = value
    with pytest.raises(ValidationError):
        CONTENT_COMMAND_ADAPTER.validate_json(json.dumps(payload))


@pytest.mark.parametrize("field", ["target_id", "target_version", "target_hash"])
def test_exact_review_target_must_match_envelope(field: str) -> None:
    payload = command("record_review")
    payload["review"][field] = 2 if field == "target_version" else (
        "b" * 64 if field == "target_hash" else "other")
    with pytest.raises(ValidationError):
        CONTENT_COMMAND_ADAPTER.validate_json(json.dumps(payload))


@pytest.mark.parametrize("value", [None, 1, True, "bogus", "activate"])
def test_unknown_or_wrong_type_action_denied(value: object) -> None:
    payload = command("create")
    payload["action"] = value
    with pytest.raises(ValidationError):
        CONTENT_COMMAND_ADAPTER.validate_json(json.dumps(payload))


@pytest.mark.parametrize("field", ["target_version", "expected_review_revision"])
def test_numeric_strings_not_coerced(field: str) -> None:
    payload = command("record_review")
    target = payload if field == "target_version" else payload["review"]
    target[field] = "1"
    with pytest.raises(ValidationError):
        CONTENT_COMMAND_ADAPTER.validate_json(json.dumps(payload))


@pytest.mark.parametrize(("field", "value"), [
    ("title", " "), ("purpose_codes", ["classroom", "classroom"]),
    ("source_refs", []), ("content_kind", "preset"),
])
def test_invalid_content_fields(field: str, value: object) -> None:
    payload = body()
    payload[field] = value
    with pytest.raises(ValidationError):
        ContentWrite.model_validate_json(json.dumps(payload))


@pytest.mark.parametrize(("minimum", "maximum"), [(0, 155), (36, 156), (100, 50), (True, 50)])
def test_age_interval_is_explicit_and_within_new_scope(minimum: object, maximum: int) -> None:
    payload = body()
    payload["age_eligibility"].update(min_months=minimum, max_months=maximum)
    with pytest.raises(ValidationError):
        ContentWrite.model_validate_json(json.dumps(payload))


def test_serialization_does_not_mutate_input() -> None:
    payload = command("create")
    original = deepcopy(payload)
    parsed = CONTENT_COMMAND_ADAPTER.validate_json(json.dumps(payload))
    assert isinstance(parsed, CreateContent) and payload == original
    assert parsed.model_dump(mode="json")["content"] == original["content"]


def test_request_changes_must_carry_matching_review_decision_and_reason() -> None:
    payload = command("request_changes")
    payload["review"]["reason"] = "Different"
    with pytest.raises(ValidationError):
        CONTENT_COMMAND_ADAPTER.validate_json(json.dumps(payload))
