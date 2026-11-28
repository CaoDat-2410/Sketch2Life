from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from sketch2life.contracts.schemas.lesson_feedback import ParentLessonFeedbackInputV1
from sketch2life.domain.platform_admin import AdminError
from sketch2life.infrastructure.lesson_library.feedback import (
    LessonFeedbackService,
    ParentLessonFeedbackService,
)
from sketch2life.infrastructure.lesson_library.service import (
    LessonLibraryError,
    LessonLibraryService,
)


def test_parent_feedback_input_strips_and_enforces_text_only_length() -> None:
    normalized = ParentLessonFeedbackInputV1(
        feedback_text="  Please add more leaves.  "
    ).feedback_text
    assert normalized == "Please add more leaves."
    assert len(ParentLessonFeedbackInputV1(feedback_text="x" * 1200).feedback_text) == 1200

    for invalid in (" ", "x" * 1201):
        with pytest.raises(ValidationError):
            ParentLessonFeedbackInputV1(feedback_text=invalid)


@pytest.mark.parametrize("field", ["profile_id", "media_url", "child_id"])
def test_parent_feedback_input_rejects_profile_child_and_media_fields(field: str) -> None:
    with pytest.raises(ValidationError):
        ParentLessonFeedbackInputV1.model_validate({"feedback_text": "A note", field: "x"})


def test_scope_and_fingerprint_are_stable_and_lesson_and_text_scoped() -> None:
    first_scope = ParentLessonFeedbackService.operation_scope("lesson-a")
    assert first_scope == ParentLessonFeedbackService.operation_scope("lesson-a")
    assert first_scope != ParentLessonFeedbackService.operation_scope("lesson-b")

    first = ParentLessonFeedbackService.command_fingerprint("lesson-a", "More examples")
    assert first == ParentLessonFeedbackService.command_fingerprint("lesson-a", "More examples")
    assert first != ParentLessonFeedbackService.command_fingerprint("lesson-b", "More examples")
    assert first != ParentLessonFeedbackService.command_fingerprint("lesson-a", "A new example")
    assert len(first) == 64


def test_receipt_conflict_detection_matches_be1_primary_key_only() -> None:
    matching = IntegrityError(
        "insert",
        {},
        SimpleNamespace(
            sqlstate="23505",
            diag=SimpleNamespace(constraint_name="pk_be1_command_receipts"),
        ),
    )
    other_unique = IntegrityError(
        "insert",
        {},
        SimpleNamespace(
            sqlstate="23505",
            diag=SimpleNamespace(constraint_name="uq_other"),
        ),
    )

    assert LessonLibraryService._is_remix_receipt_conflict(matching)
    assert not LessonLibraryService._is_remix_receipt_conflict(other_unique)


@pytest.mark.parametrize(
    ("receipt_org", "receipt_fingerprint", "expected_org", "expected_fingerprint"),
    [
        ("other-org", "a" * 64, "school-a", "a" * 64),
        ("school-a", "b" * 64, "school-a", "a" * 64),
    ],
)
def test_receipt_replay_rejects_other_organization_or_fingerprint(
    receipt_org: str,
    receipt_fingerprint: str,
    expected_org: str,
    expected_fingerprint: str,
) -> None:
    service = ParentLessonFeedbackService(SimpleNamespace(db=SimpleNamespace()))
    receipt = SimpleNamespace(
        organization_id=receipt_org,
        request_fingerprint=receipt_fingerprint,
        response_json={"feedback_id": "f-1", "message_id": "m-1", "revision": 1},
    )

    with pytest.raises(LessonLibraryError) as caught:
        service._rebuild_receipt(
            receipt,
            subject="parent-1",
            lesson_id="lesson-1",
            organization_id=expected_org,
            fingerprint=expected_fingerprint,
        )
    assert caught.value.status_code == 400
    assert caught.value.code == "INVALID_IDEMPOTENCY_KEY"


def test_feedback_response_has_no_actor_reference() -> None:
    service = ParentLessonFeedbackService(
        SimpleNamespace(db=SimpleNamespace(scalar=lambda _statement: 2))
    )
    now = datetime.now(UTC)
    body = service._feedback_response(
        {
            "thread_id": "feedback-1",
            "lesson_id": "lesson-1",
            "version_id": "version-1",
            "revision": 3,
            "created_by": "parent-1",
            "created_at": now,
        },
        {"body": "Please add another example", "actor_ref": "parent-1", "created_at": now},
    )

    assert body["feedback_text"] == "Please add another example"
    assert body["reply_count"] == 2
    assert "actor_ref" not in body
    assert "created_by" not in body


def test_platform_scope_uses_platform_sentinel() -> None:
    assert ParentLessonFeedbackService._organization_scope({"organization_id": None}) == "platform"
    assert ParentLessonFeedbackService._organization_scope(
        {"organization_id": "school-a"}
    ) == "school-a"


@pytest.mark.parametrize("role", ["platform_admin", "parent"])
def test_platform_feedback_authorization_keeps_platform_admin_and_parent_branches(
    role: str,
) -> None:
    account = SimpleNamespace(account_role=role)

    class NoOrganizationLookup:
        def get(self, *_args: object) -> None:
            raise AssertionError("platform feedback authorization must not query organizations")

    service = LessonFeedbackService(
        SimpleNamespace(identity=lambda **_kwargs: account, db=NoOrganizationLookup())
    )

    assert service.authorize("platform") is account


def test_non_admin_cannot_authorize_platform_feedback_scope() -> None:
    account = SimpleNamespace(account_role="teacher")

    class NoOrganizationLookup:
        def get(self, *_args: object) -> None:
            raise AssertionError("platform feedback authorization must not query organizations")

    service = LessonFeedbackService(
        SimpleNamespace(identity=lambda **_kwargs: account, db=NoOrganizationLookup())
    )

    with pytest.raises(AdminError) as caught:
        service.authorize("platform")
    assert caught.value.status == 404
    assert caught.value.code == "NOT_FOUND"
