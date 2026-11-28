"""PostgreSQL acceptance coverage for parent-scoped lesson feedback (E6 T-FBK1)."""

from __future__ import annotations

import json
import os
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

import pytest
from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete, func, select, update
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.infrastructure.lesson_library.feedback import ParentLessonFeedbackService
from sketch2life.infrastructure.lesson_library.feedback_tables import (
    FEEDBACK_MESSAGES,
    FEEDBACK_THREADS,
)
from sketch2life.infrastructure.lesson_library.service import LessonLibraryService
from sketch2life.infrastructure.lesson_library.tables import (
    ACCESS_GRANTS,
    LIBRARY_ITEMS,
    LIBRARY_VERSIONS,
    PARENT_GROUP_MEMBERS,
    PARENT_GROUPS,
    VERSION_ACTIVITIES,
)
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    Be1CommandReceiptModel,
    OrganizationAssignmentModel,
    OrganizationModel,
)
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult
from sketch2life.interfaces.http.routers.lesson_feedback import router as feedback_router
from sketch2life.interfaces.http.routers.lesson_library import (
    get_lesson_library_service,
)
from sketch2life.interfaces.http.routers.lesson_library import (
    router as lesson_library_router,
)

_BASE = "/api/lesson-library/v1"
_ISSUER = "synthetic-parent-feedback-issuer"


@pytest.fixture
def parent_feedback_acceptance() -> Any:
    database_url = os.environ.get("ADMIN_TEST_DATABASE_URL", "")
    if not database_url:
        pytest.skip("ADMIN_TEST_DATABASE_URL is required")
    if "admin_acceptance" not in database_url.rsplit("/", 1)[-1]:
        pytest.fail(
            "Parent feedback acceptance requires a disposable admin_acceptance database"
        )

    engine = create_engine(database_url)
    suffix = uuid4().hex
    organization_id = f"synthetic-feedback-org-{suffix}"
    subjects = {
        "teacher": f"synthetic-feedback-teacher-{suffix}",
        "manager": f"synthetic-feedback-manager-{suffix}",
        "parent": f"synthetic-feedback-parent-{suffix}",
        "other_parent": f"synthetic-feedback-other-parent-{suffix}",
        "platform_admin": f"synthetic-feedback-platform-admin-{suffix}",
    }
    group_id = str(uuid4())
    membership_id = str(uuid4())

    with Session(engine) as db:
        db.add(
            OrganizationModel(
                organization_id=organization_id,
                display_name=f"Synthetic feedback school {suffix}",
                state="active",
            )
        )
        for role, subject in subjects.items():
            account_role = {
                "teacher": "teacher",
                "manager": "school_manager",
                "parent": "parent",
                "other_parent": "parent",
                "platform_admin": "platform_admin",
            }[role]
            db.add(
                AdultIdentityModel(
                    subject=subject,
                    account_id=str(uuid4()),
                    issuer=_ISSUER,
                    account_role=account_role,
                    state="active",
                    role_revision=1,
                )
            )
        db.flush()
        db.add_all(
            [
                OrganizationAssignmentModel(
                    assignment_id=str(uuid4()),
                    organization_id=organization_id,
                    subject=subjects["teacher"],
                    class_id=None,
                    role="teacher",
                    active=True,
                ),
                OrganizationAssignmentModel(
                    assignment_id=str(uuid4()),
                    organization_id=organization_id,
                    subject=subjects["manager"],
                    class_id=None,
                    role="school_admin",
                    active=True,
                ),
            ]
        )
        db.flush()
        db.execute(
            PARENT_GROUPS.insert().values(
                parent_group_id=group_id,
                organization_id=organization_id,
                display_name=f"Feedback group {suffix}",
                state="active",
                created_by=subjects["parent"],
            )
        )
        now = datetime.now(UTC)
        db.execute(
            PARENT_GROUP_MEMBERS.insert().values(
                membership_id=membership_id,
                parent_group_id=group_id,
                parent_principal_ref=subjects["parent"],
                state="active",
                invited_by=subjects["parent"],
                expires_at=now + timedelta(days=30),
                accepted_at=now,
                revision=1,
            )
        )
        db.commit()

    app = FastAPI()
    app.include_router(lesson_library_router)
    app.include_router(feedback_router)

    def database() -> Iterator[Session]:
        with Session(engine) as db:
            yield db

    def lesson_reader(db: Session = Depends(get_db)) -> LessonLibraryService:  # noqa: B008
        return LessonLibraryService(db, storage=None, parser=None, scanner=None)

    def test_principal(request: Request) -> VerifiedPrincipal:
        subject = request.headers.get("X-Acceptance-Actor", subjects["parent"])
        return VerifiedPrincipal(
            subject=subject,
            issuer=_ISSUER,
            roles=frozenset(),
            token_id="synthetic-parent-feedback-token",
        )

    app.dependency_overrides[get_db] = database
    app.dependency_overrides[get_verified_adult] = test_principal
    app.dependency_overrides[get_lesson_library_service] = lesson_reader
    lesson_ids: set[str] = set()
    platform_lesson_ids: set[str] = set()

    try:
        with TestClient(app) as client:
            yield SimpleNamespace(
                app=app,
                client=client,
                engine=engine,
                organization_id=organization_id,
                subjects=subjects,
                group_id=group_id,
                membership_id=membership_id,
                lesson_ids=lesson_ids,
                platform_lesson_ids=platform_lesson_ids,
            )
    finally:
        app.dependency_overrides.clear()
        with engine.begin() as connection:
            all_ids = tuple(lesson_ids | platform_lesson_ids)
            thread_ids = select(FEEDBACK_THREADS.c.thread_id).where(
                FEEDBACK_THREADS.c.lesson_id.in_(all_ids)
            )
            connection.execute(
                delete(FEEDBACK_MESSAGES).where(FEEDBACK_MESSAGES.c.thread_id.in_(thread_ids))
            )
            connection.execute(
                delete(FEEDBACK_THREADS).where(FEEDBACK_THREADS.c.lesson_id.in_(all_ids))
            )
            connection.execute(
                delete(ACCESS_GRANTS).where(ACCESS_GRANTS.c.lesson_id.in_(all_ids))
            )
            version_ids = select(LIBRARY_VERSIONS.c.version_id).where(
                LIBRARY_VERSIONS.c.lesson_id.in_(all_ids)
            )
            connection.execute(
                delete(VERSION_ACTIVITIES).where(VERSION_ACTIVITIES.c.version_id.in_(version_ids))
            )
            connection.execute(
                update(LIBRARY_ITEMS)
                .where(LIBRARY_ITEMS.c.lesson_id.in_(all_ids))
                .values(current_version_id=None)
            )
            connection.execute(
                delete(LIBRARY_VERSIONS).where(LIBRARY_VERSIONS.c.lesson_id.in_(all_ids))
            )
            connection.execute(
                delete(LIBRARY_ITEMS).where(LIBRARY_ITEMS.c.lesson_id.in_(all_ids))
            )
            connection.execute(
                delete(Be1CommandReceiptModel).where(
                    Be1CommandReceiptModel.principal_ref.in_(tuple(subjects.values()))
                )
            )
            connection.execute(
                delete(PARENT_GROUP_MEMBERS).where(
                    PARENT_GROUP_MEMBERS.c.parent_group_id == group_id
                )
            )
            connection.execute(
                delete(PARENT_GROUPS).where(PARENT_GROUPS.c.parent_group_id == group_id)
            )
        engine.dispose()


def _headers(subject: str, **extra: str) -> dict[str, str]:
    return {"X-Acceptance-Actor": subject, **extra}


def _lesson_content(title: str) -> dict[str, Any]:
    return {
        "locale": "vi-VN",
        "title": title,
        "topic": "Quan sát lá cây",
        "target_age_band_ref": "age-3-6",
        "target_age_band_version": 1,
        "objectives": ["Quan sát hình dáng của lá"],
        "drawing_subject": "Chiếc lá",
        "drawing_steps_text": "Vẽ đường viền và gân lá.",
        "subject_learning_notes": "Lá có nhiều hình dáng.",
        "script_direction": None,
        "script_following_allowed": False,
        "activities": [
            {
                "title": "Tìm lá",
                "objective": "Quan sát lá trong vườn.",
                "materials_text": "",
                "preparation_text": "Chọn nơi an toàn.",
                "instructions_text": "Quan sát và mô tả một chiếc lá.",
                "observation_notes": "",
                "safety_notes": "Không đưa lá vào miệng.",
                "activity_kind": "outdoor",
            }
        ],
    }


def _create_lesson(
    accepted: Any,
    *,
    title: str,
    visibility: str = "SCHOOL",
) -> dict[str, Any]:
    response = accepted.client.post(
        f"{_BASE}/organizations/{accepted.organization_id}/lessons",
        headers=_headers(
            accepted.subjects["teacher"],
            **{"Idempotency-Key": f"create-{uuid4()}"},
        ),
        json={
            "contract": "CreateLessonRequestV1",
            "content": _lesson_content(title),
            "visibility": visibility,
        },
    )
    assert response.status_code == 201, response.text
    lesson = response.json()
    accepted.lesson_ids.add(lesson["lesson_id"])
    return lesson


def _publish_public_lesson(accepted: Any, *, title: str) -> dict[str, Any]:
    lesson = _create_lesson(accepted, title=title, visibility="SCHOOL")
    lesson_id = lesson["lesson_id"]
    grant_response = accepted.client.post(
        f"{_BASE}/organizations/{accepted.organization_id}/lessons/{lesson_id}/access-grants",
        headers=_headers(
            accepted.subjects["teacher"],
            **{"Idempotency-Key": f"public-grant-{uuid4()}"},
        ),
        json={
            "contract": "CreateLessonAccessGrantRequestV1",
            "version_id": lesson["current_version"]["version_id"],
            "audience_kind": "PUBLIC",
            "audience_ref": None,
            "capability": "VIEW",
            "expires_at": None,
        },
    )
    assert grant_response.status_code == 201, grant_response.text
    grant = grant_response.json()
    approved = accepted.client.post(
        f"{_BASE}/organizations/{accepted.organization_id}/access-grants/"
        f"{grant['access_grant_id']}/decision",
        headers=_headers(
            accepted.subjects["manager"],
            **{"If-Match": '"1"', "Idempotency-Key": f"approve-{uuid4()}"},
        ),
        json={
            "contract": "DecideLessonAccessGrantRequestV1",
            "decision": "APPROVE",
            "reason": None,
        },
    )
    assert approved.status_code == 200, approved.text
    return lesson


def _post_feedback(
    accepted: Any,
    lesson_id: str,
    key: str,
    text: str,
    *,
    actor: str | None = None,
) -> Any:
    subject = actor or accepted.subjects["parent"]
    return accepted.client.post(
        f"{_BASE}/me/lessons/{lesson_id}/feedback",
        headers=_headers(subject, **{"Idempotency-Key": key}),
        json={"feedback_text": text},
    )


def _error_code(response: Any) -> str | None:
    body = response.json()
    if "code" in body:
        return body["code"]
    detail = body.get("detail")
    return detail.get("code") if isinstance(detail, dict) else None


def test_public_feedback_receipt_replay_append_teacher_reply_and_text_privacy(
    parent_feedback_acceptance: Any,
) -> None:
    accepted = parent_feedback_acceptance
    lesson = _publish_public_lesson(accepted, title="Public feedback lesson")
    lesson_id = lesson["lesson_id"]
    expected_version = lesson["current_version"]["version_id"]

    created = _post_feedback(accepted, lesson_id, "parent-feedback-1", "Add a leaf example")
    replay = _post_feedback(accepted, lesson_id, "parent-feedback-1", "Add a leaf example")
    changed = _post_feedback(accepted, lesson_id, "parent-feedback-1", "Use a different example")
    appended = _post_feedback(accepted, lesson_id, "parent-feedback-2", "Add a second example")

    assert created.status_code == replay.status_code == appended.status_code == 201
    assert created.json() == replay.json()
    assert created.json()["revision"] == 1
    assert created.json()["version_id"] == expected_version
    assert changed.status_code == 400
    assert _error_code(changed) == "INVALID_IDEMPOTENCY_KEY"
    assert appended.json()["feedback_id"] == created.json()["feedback_id"]
    assert appended.json()["revision"] == 2
    assert appended.json()["feedback_text"] == "Add a second example"

    reply = accepted.client.post(
        f"{_BASE}/organizations/{accepted.organization_id}/feedback/"
        f"{created.json()['feedback_id']}/replies",
        headers=_headers(
            accepted.subjects["teacher"],
            **{"If-Match": '"2"', "Idempotency-Key": "teacher-feedback-reply-1"},
        ),
        json={"body": "Compare the edges of two leaves."},
    )
    state = accepted.client.get(
        f"{_BASE}/me/lessons/{lesson_id}/feedback",
        headers=_headers(accepted.subjects["parent"]),
    )
    replies = accepted.client.get(
        f"{_BASE}/me/lessons/{lesson_id}/feedback/replies",
        headers=_headers(accepted.subjects["parent"]),
    )

    assert reply.status_code == 200, reply.text
    assert state.status_code == replies.status_code == 200
    assert state.json()["feedback"]["feedback_text"] == "Add a second example"
    assert state.json()["feedback"]["reply_count"] == 1
    assert replies.json()["feedback_id"] == created.json()["feedback_id"]
    assert replies.json()["items"][0]["reply_text"] == "Compare the edges of two leaves."
    assert "actor_ref" not in replies.json()["items"][0]

    operation_scope = ParentLessonFeedbackService.operation_scope(lesson_id)
    with Session(accepted.engine) as db:
        threads = db.execute(
            select(FEEDBACK_THREADS).where(
                FEEDBACK_THREADS.c.lesson_id == lesson_id,
                FEEDBACK_THREADS.c.created_by == accepted.subjects["parent"],
            )
        ).mappings().all()
        messages = db.execute(
            select(FEEDBACK_MESSAGES).where(
                FEEDBACK_MESSAGES.c.thread_id == created.json()["feedback_id"]
            )
        ).mappings().all()
        receipt = db.scalar(
            select(Be1CommandReceiptModel).where(
                Be1CommandReceiptModel.principal_ref == accepted.subjects["parent"],
                Be1CommandReceiptModel.operation_scope == operation_scope,
                Be1CommandReceiptModel.idempotency_key == "parent-feedback-1",
            )
        )

    assert len(threads) == 1
    assert len(messages) == 3
    assert receipt is not None
    assert receipt.organization_id == accepted.organization_id
    assert set(receipt.response_json) == {"feedback_id", "message_id", "revision"}
    assert "Add a leaf example" not in json.dumps(receipt.response_json)


def test_concurrent_keys_and_same_key_create_one_thread_and_one_replay_message(
    parent_feedback_acceptance: Any,
) -> None:
    accepted = parent_feedback_acceptance
    lesson = _publish_public_lesson(accepted, title="Concurrent feedback lesson")
    lesson_id = lesson["lesson_id"]

    with ThreadPoolExecutor(max_workers=2) as pool:
        distinct = list(
            pool.map(
                lambda item: _post_feedback(accepted, lesson_id, item[0], item[1]),
                [("concurrent-key-a", "First note"), ("concurrent-key-b", "Second note")],
            )
        )
    assert all(response.status_code == 201 for response in distinct)
    assert {response.json()["revision"] for response in distinct} == {1, 2}
    assert len({response.json()["feedback_id"] for response in distinct}) == 1

    with ThreadPoolExecutor(max_workers=2) as pool:
        same_key = list(
            pool.map(
                lambda _index: _post_feedback(
                    accepted, lesson_id, "concurrent-same-key", "One immutable message"
                ),
                range(2),
            )
        )
    assert all(response.status_code == 201 for response in same_key)
    assert same_key[0].json() == same_key[1].json()

    with Session(accepted.engine) as db:
        thread_count = db.scalar(
            select(func.count()).select_from(FEEDBACK_THREADS).where(
                FEEDBACK_THREADS.c.lesson_id == lesson_id,
                FEEDBACK_THREADS.c.created_by == accepted.subjects["parent"],
            )
        )
        message_count = db.scalar(
            select(func.count()).select_from(FEEDBACK_MESSAGES).where(
                FEEDBACK_MESSAGES.c.thread_id == same_key[0].json()["feedback_id"]
            )
        )
    assert thread_count == 1
    assert message_count == 3


def test_parent_group_access_revoke_and_denied_lessons_are_uniform_404(
    parent_feedback_acceptance: Any,
) -> None:
    accepted = parent_feedback_acceptance
    group_lesson = _create_lesson(accepted, title="Group feedback lesson", visibility="SCHOOL")
    group_grant = accepted.client.post(
        f"{_BASE}/organizations/{accepted.organization_id}/lessons/"
        f"{group_lesson['lesson_id']}/access-grants",
        headers=_headers(
            accepted.subjects["teacher"],
            **{"Idempotency-Key": "parent-group-feedback-grant"},
        ),
        json={
            "contract": "CreateLessonAccessGrantRequestV1",
            "version_id": group_lesson["current_version"]["version_id"],
            "audience_kind": "PARENT_GROUP",
            "audience_ref": accepted.group_id,
            "capability": "VIEW",
            "expires_at": None,
        },
    )
    assert group_grant.status_code == 201, group_grant.text

    parent_state = accepted.client.get(
        f"{_BASE}/me/lessons/{group_lesson['lesson_id']}/feedback",
        headers=_headers(accepted.subjects["parent"]),
    )
    parent_replies = accepted.client.get(
        f"{_BASE}/me/lessons/{group_lesson['lesson_id']}/feedback/replies",
        headers=_headers(accepted.subjects["parent"]),
    )
    parent_post = _post_feedback(
        accepted,
        group_lesson["lesson_id"],
        "group-feedback-before-revoke",
        "Shared lesson note",
    )
    assert parent_state.status_code == parent_replies.status_code == 200
    assert parent_state.json()["feedback"] is None
    assert parent_replies.json()["items"] == []
    assert parent_post.status_code == 201

    other_parent = accepted.client.get(
        f"{_BASE}/me/lessons/{group_lesson['lesson_id']}/feedback",
        headers=_headers(accepted.subjects["other_parent"]),
    )

    with Session(accepted.engine) as db:
        db.execute(
            update(PARENT_GROUP_MEMBERS)
            .where(PARENT_GROUP_MEMBERS.c.membership_id == accepted.membership_id)
            .values(state="revoked", revision=2)
        )
        db.commit()

    revoked_responses = [
        accepted.client.get(
            f"{_BASE}/me/lessons/{group_lesson['lesson_id']}/feedback",
            headers=_headers(accepted.subjects["parent"]),
        ),
        accepted.client.get(
            f"{_BASE}/me/lessons/{group_lesson['lesson_id']}/feedback/replies",
            headers=_headers(accepted.subjects["parent"]),
        ),
        _post_feedback(
            accepted,
            group_lesson["lesson_id"],
            "group-feedback-before-revoke",
            "Shared lesson note",
        ),
    ]
    assert all(response.status_code == 404 for response in revoked_responses)
    assert revoked_responses[0].json() == revoked_responses[1].json() == revoked_responses[2].json()

    private_lesson = _create_lesson(accepted, title="Private feedback lesson", visibility="PRIVATE")
    hidden_lesson = _publish_public_lesson(accepted, title="Hidden feedback lesson")
    with Session(accepted.engine) as db:
        db.execute(
            update(LIBRARY_ITEMS)
            .where(LIBRARY_ITEMS.c.lesson_id == hidden_lesson["lesson_id"])
            .values(moderation_state="HIDDEN")
        )
        db.commit()

    private_denied = accepted.client.get(
        f"{_BASE}/me/lessons/{private_lesson['lesson_id']}/feedback",
        headers=_headers(accepted.subjects["parent"]),
    )
    hidden_denied = accepted.client.get(
        f"{_BASE}/me/lessons/{hidden_lesson['lesson_id']}/feedback",
        headers=_headers(accepted.subjects["parent"]),
    )
    assert (
        other_parent.status_code
        == private_denied.status_code
        == hidden_denied.status_code
        == 404
    )
    assert other_parent.json() == private_denied.json() == hidden_denied.json()


def test_platform_lesson_uses_sentinel_and_platform_admin_reads_thread(
    parent_feedback_acceptance: Any,
) -> None:
    accepted = parent_feedback_acceptance
    lesson_id = str(uuid4())
    version_id = str(uuid4())
    grant_id = str(uuid4())
    accepted.platform_lesson_ids.add(lesson_id)
    now = datetime.now(UTC)
    with Session(accepted.engine) as db:
        db.execute(
            LIBRARY_ITEMS.insert().values(
                lesson_id=lesson_id,
                organization_id=None,
                owner_kind="PLATFORM",
                created_by=accepted.subjects["platform_admin"],
                state="ACTIVE",
                visibility="PUBLIC",
                internal_visibility="PRIVATE",
                moderation_state="VISIBLE",
                revision=1,
            )
        )
        db.execute(
            LIBRARY_VERSIONS.insert().values(
                version_id=version_id,
                lesson_id=lesson_id,
                version_no=1,
                content_json={},
                structured_content_hash="a" * 64,
                review_state="APPROVED",
                authored_by=accepted.subjects["platform_admin"],
                approved_at=now,
            )
        )
        db.execute(
            update(LIBRARY_ITEMS)
            .where(LIBRARY_ITEMS.c.lesson_id == lesson_id)
            .values(current_version_id=version_id)
        )
        db.execute(
            ACCESS_GRANTS.insert().values(
                access_grant_id=grant_id,
                lesson_id=lesson_id,
                version_id=version_id,
                organization_id="platform",
                audience_kind="PUBLIC",
                audience_ref=None,
                capability="VIEW",
                state="ACTIVE",
                granted_by=accepted.subjects["platform_admin"],
                approved_by=accepted.subjects["platform_admin"],
                approved_at=now,
                revision=1,
            )
        )
        db.commit()

    submitted = _post_feedback(accepted, lesson_id, "platform-feedback-key", "Platform lesson note")
    assert submitted.status_code == 201, submitted.text
    with Session(accepted.engine) as db:
        thread = db.execute(
            select(FEEDBACK_THREADS).where(
                FEEDBACK_THREADS.c.thread_id == submitted.json()["feedback_id"]
            )
        ).mappings().one()
    assert thread["organization_id"] == "platform"

    admin_read = accepted.client.get(
        f"{_BASE}/organizations/platform/feedback/{submitted.json()['feedback_id']}",
        headers=_headers(accepted.subjects["platform_admin"]),
    )
    assert admin_read.status_code == 200, admin_read.text
    assert admin_read.json()["organization_id"] == "platform"
    assert "Platform lesson note" in [item["body"] for item in admin_read.json()["items"]]
