# ruff: noqa: E501, F811, SIM117, B023
"""Missing PostgreSQL acceptance tests for E2 (T-TCH2) named in IMPL_REVIEW_E_E2_R1_20261125.md."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import select, text, update
from test_teacher_tch2_postgres import Tch2, tch2  # noqa: F401

from sketch2life.infrastructure.lesson_library.tables import (
    LIBRARY_ITEMS,
    LIBRARY_VERSIONS,
    VERSION_ACTIVITIES,
)
from sketch2life.infrastructure.persistence.be1_models import DataLifecycleRequestModel
from sketch2life.infrastructure.persistence.core_models import CoreAuditEntryModel

pytestmark = pytest.mark.integration


def test_portfolio_pending_deletion_archived_class_and_guide_observer(tch2: Tch2) -> None:
    """covers: IMPL_REVIEW_E_E2_R1_20261125.md P2-1 / E2_PROMPT §5 (pending deletion 404 no audit, archived class 404, guide/observer 403)"""
    for actor in ("guide", "observer"):
        forbidden = tch2.get(actor, tch2.portfolio())
        assert forbidden.status_code == 403
        assert forbidden.json()["code"] == "ACTION_NOT_ALLOWED"

    archived_class_res = tch2.get(
        "teacher", tch2.portfolio(child_key="synthetic", class_key="archived")
    )
    assert archived_class_res.status_code == 404
    assert archived_class_res.json()["code"] == "RESOURCE_NOT_FOUND"

    with tch2.factory.begin() as db:
        db.add(
            DataLifecycleRequestModel(
                request_id=str(uuid4()),
                organization_id=tch2.organization_id,
                owner_scope_kind="ORGANIZATION",
                owner_scope_ref=None,
                request_type="delete",
                target_ref=tch2.children["synthetic"],
                state="requested",
                unresolved_items=1,
                requested_by=tch2.subjects["manager"],
            )
        )
    deleted_res = tch2.get("teacher", tch2.portfolio("synthetic"))
    assert deleted_res.status_code == 404
    assert deleted_res.json()["code"] == "RESOURCE_NOT_FOUND"
    with tch2.factory() as db:
        audits = db.scalars(
            select(CoreAuditEntryModel).where(
                CoreAuditEntryModel.resource_id == tch2.children["synthetic"],
                CoreAuditEntryModel.action == "portfolio.read",
            )
        ).all()
    assert audits == []


def test_portfolio_real_profile_consent_check_constraint_leaves_effective_unreachable(
    tch2: Tch2,
) -> None:
    """covers: IMPL_REVIEW_E_E2_R1_20261125.md P2-1 (REAL consent unreachable today due to ck_be1_consent_state)"""
    pending = tch2.get("teacher", tch2.portfolio("pending"))
    assert pending.status_code == 409
    assert pending.json()["code"] == "CONSENT_NOT_EFFECTIVE"
    with tch2.factory() as db:
        constraint_def = db.execute(
            text(
                "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                "WHERE conname = 'ck_be1_consent_state'"
            )
        ).scalar_one()
    assert "pending" in str(constraint_def) and "revoked" in str(constraint_def)
    assert "effective" not in str(constraint_def)


def test_activities_within_one_lesson_follow_activity_order_and_bad_cursor_is_400(
    tch2: Tch2,
) -> None:
    """covers: IMPL_REVIEW_E_E2_R1_20261125.md P3-1 (activity_order ASC inside a lesson and bad cursor 400)"""
    lesson_id, version_id = str(uuid4()), str(uuid4())
    with tch2.factory.begin() as db:
        db.execute(
            LIBRARY_ITEMS.insert().values(
                lesson_id=lesson_id,
                organization_id=tch2.organization_id,
                created_by=tch2.subjects["teacher"],
                state="ACTIVE",
                visibility="SCHOOL",
                internal_visibility="SCHOOL",
                moderation_state="VISIBLE",
                current_version_id=None,
                updated_at=datetime(2026, 11, 25, 12, 0, tzinfo=UTC),
            )
        )
        db.execute(
            LIBRARY_VERSIONS.insert().values(
                version_id=version_id,
                lesson_id=lesson_id,
                version_no=1,
                content_json={"title": "Synthetic ordered lesson", "topic": "shapes"},
                structured_content_hash=hashlib.sha256(b"ordered").hexdigest(),
                review_state="APPROVED",
                authored_by=tch2.subjects["teacher"],
            )
        )
        # Insert in intentionally reversed UUID order vs activity_order (1, 2, 3)
        for order, act_id in (
            (1, f"ffff0001-{uuid4().hex[9:]}"),
            (2, f"aaaa0002-{uuid4().hex[9:]}"),
            (3, f"00000003-{uuid4().hex[9:]}"),
        ):
            db.execute(
                VERSION_ACTIVITIES.insert().values(
                    activity_id=act_id,
                    version_id=version_id,
                    activity_order=order,
                    activity_json={
                        "title": f"Step {order}",
                        "objective": "Order",
                        "activity_kind": "indoor",
                        "materials_text": "Paper",
                        "preparation_text": "None",
                        "instructions_text": "Draw",
                        "observation_notes": "Watch",
                        "safety_notes": "Safe",
                    },
                )
            )
        db.execute(
            update(LIBRARY_ITEMS)
            .where(LIBRARY_ITEMS.c.lesson_id == lesson_id)
            .values(current_version_id=version_id)
        )

    path = f"/api/lesson-library/v1/organizations/{tch2.organization_id}/activities"
    res = tch2.get("teacher", f"{path}?limit=10")
    assert res.status_code == 200, res.text
    ordered = [
        item["activity_order"]
        for item in res.json()["items"]
        if item["lesson_id"] == lesson_id
    ]
    assert ordered == [1, 2, 3]

    bad_cursor = tch2.get("teacher", f"{path}?cursor=bad-cursor")
    assert bad_cursor.status_code == 400
    assert bad_cursor.json()["code"] == "INVALID_REQUEST"


def test_history_excludes_archived_class_and_unassigned_teacher_gets_404(tch2: Tch2) -> None:
    """covers: IMPL_REVIEW_E_E2_R1_20261125.md Checked-(b) & E2_PROMPT §5 (archived excluded, unassigned 404)"""
    res = tch2.get(
        "teacher", f"/api/teacher/v1/organizations/{tch2.organization_id}/history"
    )
    assert res.status_code == 200
    returned_ids = {item["occurrence_id"] for item in res.json()["items"]}
    assert tch2.occurrences["archived"] not in returned_ids
    assert tch2.occurrences["unassigned"] not in returned_ids

    unassigned = tch2.get(
        "unassigned", f"/api/teacher/v1/organizations/{tch2.organization_id}/history"
    )
    assert unassigned.status_code == 404
    assert unassigned.json()["code"] == "RESOURCE_NOT_FOUND"
