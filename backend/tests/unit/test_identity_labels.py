from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest

from sketch2life.application.ports.identity import IdentityAccountProvisioningUnavailable
from sketch2life.infrastructure.identity.identity_labels import (
    account_profiles,
    masked_email,
    safe_display_name,
    teacher_identity_fields,
    teacher_identity_label,
)
from sketch2life.infrastructure.lesson_library.feedback import LessonFeedbackService
from sketch2life.infrastructure.lesson_library.service import LessonLibraryService
from sketch2life.interfaces.http.routers import be1_billing


def test_identity_labels_follow_teacher_candidate_masking_and_hide_email_names() -> None:
    profile = SimpleNamespace(display_name="Lan", email="lan@example.test")
    fields = teacher_identity_fields(profile)

    assert fields == {"display_name": "Lan", "email_masked": "la***@example.test"}
    assert teacher_identity_label(fields) == "Lan · la***@example.test"
    assert safe_display_name("  lan@example.test ") is None
    assert safe_display_name("subject-123", subject="subject-123") is None
    assert masked_email("not-an-email") is None
    assert masked_email("a@") is None
    assert teacher_identity_label({"display_name": None, "email_masked": None}) == (
        "Teacher chưa có tên hiển thị"
    )


def test_account_profiles_batches_subjects_and_degrades_on_provider_unavailable() -> None:
    class Provisioner:
        def __init__(self) -> None:
            self.batches: list[list[str]] = []

        def get_account_profiles(self, subjects: list[str]) -> dict[str, Any]:
            self.batches.append(subjects)
            return {subject: subject for subject in subjects}

    provisioner = Provisioner()
    result = account_profiles(provisioner, [str(i) for i in range(101)] + ["0", ""])

    assert [len(batch) for batch in provisioner.batches] == [100, 1]
    assert result["100"] == "100"

    class Unavailable:
        def get_account_profiles(self, _subjects: list[str]) -> dict[str, Any]:
            raise IdentityAccountProvisioningUnavailable

    assert account_profiles(Unavailable(), ["subject"]) == {}


class _Result:
    def __init__(self, *, rows: list[Any] | None = None, row: Any = None) -> None:
        self.rows = rows or []
        self.row = row

    def mappings(self) -> _Result:
        return self

    def all(self) -> list[Any]:
        return self.rows

    def one_or_none(self) -> Any:
        return self.row


class _FeedbackDb:
    def __init__(self, role_rows: list[Any]) -> None:
        self.role_rows = role_rows
        self.calls = 0

    def execute(self, _statement: Any) -> _Result:
        self.calls += 1
        if self.calls == 1:
            return _Result(
                row={
                    "thread_id": "thread-1",
                    "lesson_id": "lesson-1",
                    "version_id": "version-2",
                    "revision": 3,
                }
            )
        if self.calls == 2:
            return _Result(
                rows=[
                    {
                        "message_id": "message-1",
                        "body": "A note",
                        "actor_ref": "parent-private-subject",
                        "created_at": datetime(2026, 11, 25, tzinfo=UTC),
                    }
                ]
            )
        if self.calls == 3:
            return _Result(row={"content_json": {"title": "Seed to Sprout"}, "version_no": 2})
        return _Result(rows=self.role_rows)

    def get(self, _model: Any, _ref: str) -> Any:
        return SimpleNamespace(state="active")

    def scalar(self, _statement: Any) -> int:
        return 1

    def get_bind(self) -> Any:
        return SimpleNamespace(dialect=SimpleNamespace(name="sqlite"))


def _feedback_service(role: str) -> LessonFeedbackService:
    account = SimpleNamespace(account_role=role, subject="staff-subject")
    db = _FeedbackDb(
        [SimpleNamespace(subject="parent-private-subject", account_role="parent")]
    )
    profile_provider = SimpleNamespace(
        get_account_profiles=lambda subjects: {
            "parent-private-subject": SimpleNamespace(
                display_name="Parent Lan", email="lan@example.test"
            )
        }
    )
    admin = SimpleNamespace(
        db=db,
        principal=SimpleNamespace(subject="staff-subject"),
        identity=lambda **_kwargs: account,
    )
    return LessonFeedbackService(
        admin,
        parent_lesson=lambda _lesson_id: None,
        identity_provisioner=profile_provider,
    )


def test_feedback_detail_adds_title_role_and_staff_name_without_subject() -> None:
    detail = _feedback_service("teacher").detail("org-1", "thread-1")

    assert detail["lesson_title"] == "Seed to Sprout"
    assert detail["version_no"] == 2
    assert detail["items"][0]["author_role"] == "parent"
    assert detail["items"][0]["author_display_name"] == "Parent Lan"
    assert "parent-private-subject" not in str(detail)
    assert "email" not in str(detail)


def test_parent_feedback_detail_hides_all_author_display_names() -> None:
    detail = _feedback_service("parent").detail("platform", "thread-1")

    assert detail["items"][0]["author_role"] == "parent"
    assert detail["items"][0]["author_display_name"] is None


def test_public_grant_response_includes_lesson_title_and_version_number() -> None:
    row = {
        "access_grant_id": "grant-1",
        "lesson_id": "lesson-1",
        "lesson_content_json": {"title": "Seed to Sprout"},
        "version_id": "version-2",
        "lesson_version_no": 2,
        "audience_kind": "PUBLIC",
        "audience_ref": None,
        "capability": "view",
        "state": "PENDING_REVIEW",
        "granted_by": "teacher-1",
        "approved_by": None,
        "approved_at": None,
        "expires_at": None,
        "revoked_at": None,
        "revision": 1,
    }

    response = LessonLibraryService._grant_response(row)

    assert response["lesson_title"] == "Seed to Sprout"
    assert response["version_no"] == 2


def test_quota_teacher_and_allocation_routes_keep_write_ids_and_mask_email(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    subject = "teacher-private-subject"
    profile = SimpleNamespace(display_name="Teacher Lan", email="lan.nguyen@example.test")
    provider = SimpleNamespace(get_account_profiles=lambda subjects: {subject: profile})
    request = SimpleNamespace(
        app=SimpleNamespace(
            state=SimpleNamespace(identity_account_provisioner=provider)
        )
    )
    principal = SimpleNamespace(subject="manager-private-subject")
    monkeypatch.setattr(
        be1_billing, "require_assignment", lambda *_args, **_kwargs: None
    )
    monkeypatch.setattr(
        be1_billing,
        "_commerce",
        lambda *_args: SimpleNamespace(
            allocations=lambda *_args: {
                "items": [
                    {
                        "allocation_id": "allocation-1",
                        "teacher_ref": subject,
                        "available_units": 7,
                        "active": True,
                        "revision": 2,
                        "updated_at": "2026-11-25T10:00:00Z",
                    }
                ],
                "total": 1,
            }
        ),
    )
    db = SimpleNamespace(scalars=lambda _statement: [subject])

    teachers = be1_billing.school_quota_teachers(
        "school-1", request, principal=principal, db=db
    )
    allocations = be1_billing.school_allocations(
        "school-1", request, principal=principal, db=db
    )

    assert teachers["items"][0]["teacher_ref"] == subject
    assert teachers["items"][0]["label"] == "Teacher Lan · la***@example.test"
    assert teachers["items"][0]["email_masked"] == "la***@example.test"
    assert "lan.nguyen@example.test" not in str(teachers)
    assert allocations["items"][0]["teacher_ref"] == subject
    assert allocations["items"][0]["display_name"] == "Teacher Lan"
    assert allocations["items"][0]["email_masked"] == "la***@example.test"
