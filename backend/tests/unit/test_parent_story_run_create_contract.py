from __future__ import annotations

from pydantic import ValidationError
import pytest

from sketch2life.contracts.schemas.parent_story_runs import ParentStoryRunCreateRequestV1
from sketch2life.infrastructure.story_run_lite.tables import run_inputs


def _payload() -> dict[str, object]:
    return {
        "parent_profile_id": "07a28e67-e233-4b02-9cfa-0abb3907224b",
        "expected_profile_revision_id": "7a499fcb-c6d5-40d9-9c62-5e3a6dcd8cf3",
        "consent_policy_version": "local-synthetic-demo-v1",
        "topic": "deer",
        "adult_confirmed_idea": "",
        "context_confirmed": True,
    }


def test_create_contract_accepts_uuid_strings_from_json_body() -> None:
    request = ParentStoryRunCreateRequestV1.model_validate(_payload())

    assert str(request.parent_profile_id) == "07a28e67-e233-4b02-9cfa-0abb3907224b"
    assert str(request.expected_profile_revision_id) == "7a499fcb-c6d5-40d9-9c62-5e3a6dcd8cf3"


def test_create_contract_remains_strict_for_non_uuid_fields() -> None:
    payload = _payload()
    payload["context_confirmed"] = "true"

    with pytest.raises(ValidationError):
        ParentStoryRunCreateRequestV1.model_validate(payload)


def test_optional_lesson_pin_none_is_persisted_as_sql_null() -> None:
    column_type = run_inputs.c.lesson_pin_snapshot.type

    assert column_type.none_as_null is True
