# ruff: noqa: E501, F811, SIM117, B023
"""Missing PostgreSQL acceptance tests for E6 T-FBK1 named in IMPL_REVIEW_E_E6_R1_20261125.md and E6_PROMPT.md."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session
from test_parent_lesson_feedback_postgres import (  # noqa: F401
    _BASE,
    _create_lesson,
    _error_code,
    _headers,
    _post_feedback,
    _publish_public_lesson,
    parent_feedback_acceptance,
)

from sketch2life.infrastructure.lesson_library.feedback import ParentLessonFeedbackService
from sketch2life.infrastructure.lesson_library.feedback_tables import (
    FEEDBACK_MESSAGES,
    FEEDBACK_THREADS,
)
from sketch2life.infrastructure.lesson_library.tables import (
    ACCESS_GRANTS,
    LIBRARY_ITEMS,
    LIBRARY_VERSIONS,
    PARENT_GROUP_MEMBERS,
)
from sketch2life.infrastructure.persistence.be1_models import Be1CommandReceiptModel
from sketch2life.infrastructure.persistence.core_models import CoreAuditEntryModel
from sketch2life.infrastructure.persistence.platform_models import (
    AdminCommandReceiptModel,
    InboxItemModel,
)

pytestmark = pytest.mark.integration


def test_audit_inbox_and_logs_carry_ids_only_without_feedback_text(
    parent_feedback_acceptance: object,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """covers: IMPL_REVIEW_E_E6_R1_20261125.md Finding 5 (audit, inbox, and logs omit feedback_text)"""
    accepted = parent_feedback_acceptance
    lesson = _publish_public_lesson(accepted, title="Audit privacy feedback lesson")
    lesson_id = lesson["lesson_id"]
    secret_phrase = "Sensitive child note phrase"

    caplog.set_level(logging.DEBUG)
    first = _post_feedback(accepted, lesson_id, "audit-priv-1", f"{secret_phrase} one")
    second = _post_feedback(accepted, lesson_id, "audit-priv-2", f"{secret_phrase} two")
    assert first.status_code == second.status_code == 201
    feedback_id = first.json()["feedback_id"]

    try:
        with Session(accepted.engine) as db:  # type: ignore[attr-defined]
            audits = db.scalars(
                select(CoreAuditEntryModel).where(
                    CoreAuditEntryModel.resource_type == "lesson_feedback",
                    CoreAuditEntryModel.resource_id == feedback_id,
                )
            ).all()
            inboxes = db.scalars(
                select(InboxItemModel).where(InboxItemModel.resource_ref == feedback_id)
            ).all()

        assert {row.action for row in audits} == {
            "LESSON_FEEDBACK_CREATED",
            "LESSON_FEEDBACK_FOLLOW_UP",
        }
        assert all(row.organization_id == accepted.organization_id for row in audits)  # type: ignore[attr-defined]
        assert len(inboxes) >= 2
        assert all(row.kind == "LESSON_FEEDBACK_CREATED" for row in inboxes)
        assert all(row.recipient_ref == accepted.subjects["teacher"] for row in inboxes)  # type: ignore[attr-defined]

        for audit in audits:
            assert secret_phrase not in (
                f"{audit.action} {audit.resource_type} {audit.resource_id} {audit.decision}"
            )
        for inbox in inboxes:
            assert secret_phrase not in f"{inbox.kind} {inbox.resource_ref}"
        assert secret_phrase not in caplog.text
    finally:
        with accepted.engine.begin() as conn:  # type: ignore[attr-defined]
            conn.execute(
                delete(CoreAuditEntryModel).where(
                    CoreAuditEntryModel.resource_type == "lesson_feedback",
                    CoreAuditEntryModel.resource_id == feedback_id,
                )
            )
            conn.execute(delete(InboxItemModel).where(InboxItemModel.resource_ref == feedback_id))


def test_forced_pk_receipt_race_replays_winner_with_single_message(
    parent_feedback_acceptance: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """covers: IMPL_REVIEW_E_E6_R1_20261125.md Checked (forced pk_be1_command_receipts race rollback & replay)"""
    accepted = parent_feedback_acceptance
    lesson = _publish_public_lesson(accepted, title="PK race feedback lesson")
    lesson_id = lesson["lesson_id"]

    winner = _post_feedback(accepted, lesson_id, "forced-pk-race-key", "Race immutable message")
    assert winner.status_code == 201

    real_load = ParentLessonFeedbackService._load_receipt
    calls = {"n": 0}

    def miss_first_receipt(
        self: ParentLessonFeedbackService, subject: str, scope: str, key: str
    ) -> object:
        calls["n"] += 1
        if calls["n"] == 1:
            return None
        return real_load(self, subject, scope, key)

    monkeypatch.setattr(ParentLessonFeedbackService, "_load_receipt", miss_first_receipt)
    loser = _post_feedback(accepted, lesson_id, "forced-pk-race-key", "Race immutable message")

    assert loser.status_code == 201
    assert loser.json() == winner.json()
    assert calls["n"] == 2

    with Session(accepted.engine) as db:  # type: ignore[attr-defined]
        thread_count = db.scalar(
            select(func.count()).select_from(FEEDBACK_THREADS).where(
                FEEDBACK_THREADS.c.lesson_id == lesson_id,
                FEEDBACK_THREADS.c.created_by == accepted.subjects["parent"],  # type: ignore[attr-defined]
            )
        )
        message_count = db.scalar(
            select(func.count()).select_from(FEEDBACK_MESSAGES).where(
                FEEDBACK_MESSAGES.c.thread_id == winner.json()["feedback_id"]
            )
        )
        receipt_count = db.scalar(
            select(func.count()).select_from(Be1CommandReceiptModel).where(
                Be1CommandReceiptModel.principal_ref == accepted.subjects["parent"],  # type: ignore[attr-defined]
                Be1CommandReceiptModel.operation_scope
                == ParentLessonFeedbackService.operation_scope(lesson_id),
                Be1CommandReceiptModel.idempotency_key == "forced-pk-race-key",
            )
        )
    assert thread_count == message_count == receipt_count == 1


def test_reply_pagination_ordering_and_invalid_or_cross_lesson_cursor(
    parent_feedback_acceptance: object,
) -> None:
    """covers: IMPL_REVIEW_E_E6_R1_20261125.md Checked (reply pagination ordering & INVALID_CURSOR 400)"""
    accepted = parent_feedback_acceptance
    lesson_a = _publish_public_lesson(accepted, title="Paginated replies lesson A")
    lesson_b = _publish_public_lesson(accepted, title="Paginated replies lesson B")
    lesson_a_id = lesson_a["lesson_id"]
    lesson_b_id = lesson_b["lesson_id"]

    created = _post_feedback(accepted, lesson_a_id, "paging-create-1", "Parent initial question")
    assert created.status_code == 201
    thread_id = created.json()["feedback_id"]

    expected_replies = ["First staff reply", "Second staff reply", "Third staff reply"]
    try:
        for idx, reply_text in enumerate(expected_replies, start=1):
            reply = accepted.client.post(  # type: ignore[attr-defined]
                f"{_BASE}/organizations/{accepted.organization_id}/feedback/{thread_id}/replies",  # type: ignore[attr-defined]
                headers=_headers(
                    accepted.subjects["teacher"],  # type: ignore[attr-defined]
                    **{"If-Match": f'"{idx}"', "Idempotency-Key": f"paging-reply-{idx}"},
                ),
                json={"body": reply_text},
            )
            assert reply.status_code == 200, reply.text

        collected: list[str] = []
        cursor: str | None = None
        captured_cursor: str | None = None
        for page_no in range(3):
            url = f"{_BASE}/me/lessons/{lesson_a_id}/feedback/replies?limit=1"
            if cursor is not None:
                url += f"&cursor={cursor}"
            page = accepted.client.get(url, headers=_headers(accepted.subjects["parent"]))  # type: ignore[attr-defined]
            assert page.status_code == 200
            body = page.json()
            assert body["feedback_id"] == thread_id
            assert len(body["items"]) == 1
            assert "actor_ref" not in body["items"][0]
            collected.append(body["items"][0]["reply_text"])
            cursor = body["next_cursor"]
            if page_no == 0:
                captured_cursor = cursor
                assert captured_cursor is not None
            if page_no < 2:
                assert cursor is not None
            else:
                assert cursor is None

        assert collected == expected_replies

        for bad_url in (
            f"{_BASE}/me/lessons/{lesson_a_id}/feedback/replies?cursor=not-a-valid-cursor",
            f"{_BASE}/me/lessons/{lesson_b_id}/feedback/replies?cursor={captured_cursor}",
        ):
            bad = accepted.client.get(bad_url, headers=_headers(accepted.subjects["parent"]))  # type: ignore[attr-defined]
            assert bad.status_code == 400
            assert _error_code(bad) == "INVALID_REQUEST"
            detail = bad.json().get("detail", bad.json())
            assert detail["field_errors"] == [{"field": "cursor", "code": "INVALID_FORMAT"}]
    finally:
        with accepted.engine.begin() as conn:  # type: ignore[attr-defined]
            conn.execute(
                delete(AdminCommandReceiptModel).where(
                    AdminCommandReceiptModel.actor_ref == accepted.subjects["teacher"]  # type: ignore[attr-defined]
                )
            )


def test_existing_org_route_thread_reused_and_version_pinned_across_lesson_update(
    parent_feedback_acceptance: object,
) -> None:
    """covers: IMPL_REVIEW_E_E6_R1_20261125.md Checked & Finding 5 (org thread reused, version_id pinned on follow-up)"""
    accepted = parent_feedback_acceptance
    lesson = _publish_public_lesson(accepted, title="Org thread reuse lesson")
    lesson_id = lesson["lesson_id"]
    v1 = lesson["current_version"]["version_id"]

    try:
        org_created = accepted.client.post(  # type: ignore[attr-defined]
            f"{_BASE}/organizations/{accepted.organization_id}/lessons/{lesson_id}/feedback",  # type: ignore[attr-defined]
            headers=_headers(
                accepted.subjects["parent"],  # type: ignore[attr-defined]
                **{"Idempotency-Key": "org-route-thread-create"},
            ),
            json={"body": "Created on org route"},
        )
        assert org_created.status_code == 201, org_created.text
        thread_id = org_created.json()["thread_id"]

        v2 = str(uuid4())
        now = datetime.now(UTC)
        with Session(accepted.engine) as db:  # type: ignore[attr-defined]
            db.execute(
                LIBRARY_VERSIONS.insert().values(
                    version_id=v2,
                    lesson_id=lesson_id,
                    version_no=2,
                    content_json={},
                    structured_content_hash="b" * 64,
                    review_state="APPROVED",
                    authored_by=accepted.subjects["teacher"],  # type: ignore[attr-defined]
                    approved_at=now,
                )
            )
            db.execute(
                update(LIBRARY_ITEMS)
                .where(LIBRARY_ITEMS.c.lesson_id == lesson_id)
                .values(current_version_id=v2, revision=2)
            )
            db.execute(
                update(ACCESS_GRANTS)
                .where(ACCESS_GRANTS.c.lesson_id == lesson_id)
                .values(version_id=v2, revision=2)
            )
            db.commit()

        follow_up = _post_feedback(
            accepted,
            lesson_id,
            "me-route-follow-up",
            "Follow-up via me route",
        )
        assert follow_up.status_code == 201
        body = follow_up.json()
        assert body["feedback_id"] == thread_id
        assert body["revision"] == 2
        assert body["version_id"] == v1
    finally:
        with accepted.engine.begin() as conn:  # type: ignore[attr-defined]
            conn.execute(
                delete(AdminCommandReceiptModel).where(
                    AdminCommandReceiptModel.actor_ref == accepted.subjects["parent"]  # type: ignore[attr-defined]
                )
            )


def test_expired_group_unapproved_public_and_archived_lesson_return_uniform_404(
    parent_feedback_acceptance: object,
) -> None:
    """covers: IMPL_REVIEW_E_E6_R1_20261125.md Checked (E6_PROMPT §2 D-7 expired/unapproved/archived uniform 404)"""
    accepted = parent_feedback_acceptance

    # 1. Unapproved PUBLIC grant (PENDING)
    unapproved = _create_lesson(accepted, title="Pending public lesson", visibility="SCHOOL")
    grant_res = accepted.client.post(  # type: ignore[attr-defined]
        f"{_BASE}/organizations/{accepted.organization_id}/lessons/{unapproved['lesson_id']}/access-grants",  # type: ignore[attr-defined]
        headers=_headers(
            accepted.subjects["teacher"],  # type: ignore[attr-defined]
            **{"Idempotency-Key": "unapproved-public-grant"},
        ),
        json={
            "contract": "CreateLessonAccessGrantRequestV1",
            "version_id": unapproved["current_version"]["version_id"],
            "audience_kind": "PUBLIC",
            "audience_ref": None,
            "capability": "VIEW",
            "expires_at": None,
        },
    )
    assert grant_res.status_code == 201

    # 2. Archived public lesson
    archived = _publish_public_lesson(accepted, title="Archived public lesson")
    with Session(accepted.engine) as db:  # type: ignore[attr-defined]
        db.execute(
            update(LIBRARY_ITEMS)
            .where(LIBRARY_ITEMS.c.lesson_id == archived["lesson_id"])
            .values(state="ARCHIVED")
        )
        db.commit()

    # 3. Expired PARENT_GROUP membership
    group_lesson = _create_lesson(accepted, title="Expired group lesson", visibility="SCHOOL")
    group_grant = accepted.client.post(  # type: ignore[attr-defined]
        f"{_BASE}/organizations/{accepted.organization_id}/lessons/{group_lesson['lesson_id']}/access-grants",  # type: ignore[attr-defined]
        headers=_headers(
            accepted.subjects["teacher"],  # type: ignore[attr-defined]
            **{"Idempotency-Key": "expired-group-grant"},
        ),
        json={
            "contract": "CreateLessonAccessGrantRequestV1",
            "version_id": group_lesson["current_version"]["version_id"],
            "audience_kind": "PARENT_GROUP",
            "audience_ref": accepted.group_id,  # type: ignore[attr-defined]
            "capability": "VIEW",
            "expires_at": None,
        },
    )
    assert group_grant.status_code == 201
    with Session(accepted.engine) as db:  # type: ignore[attr-defined]
        db.execute(
            update(PARENT_GROUP_MEMBERS)
            .where(PARENT_GROUP_MEMBERS.c.membership_id == accepted.membership_id)  # type: ignore[attr-defined]
            .values(expires_at=datetime.now(UTC) - timedelta(minutes=5))
        )
        db.commit()

    denied_bodies = []
    for lid in (unapproved["lesson_id"], archived["lesson_id"], group_lesson["lesson_id"]):
        for res in (
            accepted.client.get(
                f"{_BASE}/me/lessons/{lid}/feedback",
                headers=_headers(accepted.subjects["parent"]),  # type: ignore[attr-defined]
            ),
            accepted.client.get(
                f"{_BASE}/me/lessons/{lid}/feedback/replies",
                headers=_headers(accepted.subjects["parent"]),  # type: ignore[attr-defined]
            ),
            _post_feedback(accepted, lid, f"denied-{lid}", "Should not write"),
        ):
            assert res.status_code == 404
            assert _error_code(res) == "LESSON_NOT_FOUND"
            denied_bodies.append(res.json())
    assert all(body == denied_bodies[0] for body in denied_bodies)


def test_platform_lesson_blocks_school_staff_and_admin_reply_appears_for_parent(
    parent_feedback_acceptance: object,
) -> None:
    """covers: IMPL_REVIEW_E_E6_R1_20261125.md Checked (E6_PROMPT §2 D-8 platform staff denied, admin reply visible)"""
    accepted = parent_feedback_acceptance
    lesson_id = str(uuid4())
    version_id = str(uuid4())
    grant_id = str(uuid4())
    accepted.platform_lesson_ids.add(lesson_id)  # type: ignore[attr-defined]
    now = datetime.now(UTC)
    with Session(accepted.engine) as db:  # type: ignore[attr-defined]
        db.execute(
            LIBRARY_ITEMS.insert().values(
                lesson_id=lesson_id,
                organization_id=None,
                owner_kind="PLATFORM",
                created_by=accepted.subjects["platform_admin"],  # type: ignore[attr-defined]
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
                authored_by=accepted.subjects["platform_admin"],  # type: ignore[attr-defined]
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
                granted_by=accepted.subjects["platform_admin"],  # type: ignore[attr-defined]
                approved_by=accepted.subjects["platform_admin"],  # type: ignore[attr-defined]
                approved_at=now,
                revision=1,
            )
        )
        db.commit()

    try:
        submitted = _post_feedback(accepted, lesson_id, "platform-staff-check", "Platform note")
        assert submitted.status_code == 201
        thread_id = submitted.json()["feedback_id"]

        for staff_role in ("teacher", "manager"):
            denied = accepted.client.get(  # type: ignore[attr-defined]
                f"{_BASE}/organizations/platform/feedback/{thread_id}",
                headers=_headers(accepted.subjects[staff_role]),  # type: ignore[attr-defined]
            )
            assert denied.status_code == 404

        admin_reply = accepted.client.post(  # type: ignore[attr-defined]
            f"{_BASE}/organizations/platform/feedback/{thread_id}/replies",
            headers=_headers(
                accepted.subjects["platform_admin"],  # type: ignore[attr-defined]
                **{"If-Match": '"1"', "Idempotency-Key": "platform-admin-reply-1"},
            ),
            json={"body": "Thank you from platform admin"},
        )
        assert admin_reply.status_code == 200, admin_reply.text

        parent_replies = accepted.client.get(  # type: ignore[attr-defined]
            f"{_BASE}/me/lessons/{lesson_id}/feedback/replies",
            headers=_headers(accepted.subjects["parent"]),  # type: ignore[attr-defined]
        )
        assert parent_replies.status_code == 200
        items = parent_replies.json()["items"]
        assert len(items) == 1
        assert items[0]["reply_text"] == "Thank you from platform admin"
        assert "actor_ref" not in items[0]
    finally:
        with accepted.engine.begin() as conn:  # type: ignore[attr-defined]
            conn.execute(
                delete(AdminCommandReceiptModel).where(
                    AdminCommandReceiptModel.actor_ref == accepted.subjects["platform_admin"]  # type: ignore[attr-defined]
                )
            )
