"""Parent-group membership accepts either unique identifier of the verified Parent."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from sqlalchemy import create_engine, insert
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from sketch2life.infrastructure.lesson_library.service import (
    LessonLibraryError,
    LessonLibraryService,
)
from sketch2life.infrastructure.lesson_library.tables import (
    ACCESS_GRANTS,
    COMMAND_RECEIPTS,
    LIBRARY_ITEMS,
    LIBRARY_VERSIONS,
    PARENT_GROUP_MEMBERS,
    PARENT_GROUPS,
)
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    OrganizationAssignmentModel,
    OrganizationModel,
)

ORG_ID = "parent-group-org"
MANAGER = "parent-group-manager"
PARENT_A = "parent-group-a-subject"
PARENT_A_ACCOUNT = "parent-group-a-account"
PARENT_B = "parent-group-b-subject"
PARENT_B_ACCOUNT = "parent-group-b-account"
NOW = datetime.now(UTC)
GROUPS = (
    "invite-account",
    "invite-subject",
    "invite-foreign",
    "member-account",
    "member-subject",
    "member-foreign",
    "grant-account",
    "grant-subject",
    "grant-foreign",
    "duplicate-account",
    "duplicate-subject",
    "new-invitation",
    "new-subject-invitation",
    "invalid-unknown",
    "invalid-teacher",
    "invalid-school-manager",
    "invalid-platform-admin",
    "invalid-no-role",
    "invalid-disabled",
    "invalid-inactive",
    "invalid-ambiguous",
    "active-staff",
    "replay-after-disable",
)
PARENT_NOT_FOUND_MESSAGE = "Parent account not found"


@compiles(JSONB, "sqlite")
def _jsonb_as_json_on_sqlite(_type: Any, _compiler: Any, **_kw: Any) -> str:
    return "JSON"


def _seed_group(db: Session, group_id: str) -> None:
    db.execute(
        insert(PARENT_GROUPS).values(
            parent_group_id=group_id,
            organization_id=ORG_ID,
            display_name=group_id,
            state="active",
            created_by=MANAGER,
            created_at=NOW,
        )
    )


def _seed_membership(
    db: Session,
    *,
    membership_id: str,
    group_id: str,
    parent_ref: str,
    state: str,
) -> None:
    db.execute(
        insert(PARENT_GROUP_MEMBERS).values(
            membership_id=membership_id,
            parent_group_id=group_id,
            parent_principal_ref=parent_ref,
            state=state,
            invited_by=MANAGER,
            invited_at=NOW,
            expires_at=NOW + timedelta(days=5),
            accepted_at=NOW if state == "active" else None,
            revision=1,
        )
    )


def _seed_group_lesson(db: Session, *, group_id: str, lesson_id: str) -> None:
    version_id = f"version-{lesson_id}"
    db.execute(
        insert(LIBRARY_ITEMS).values(
            lesson_id=lesson_id,
            organization_id=ORG_ID,
            owner_kind="ORGANIZATION",
            created_by=MANAGER,
            state="ACTIVE",
            visibility="SELECTED_AUDIENCE",
            internal_visibility="PRIVATE",
            moderation_state="VISIBLE",
            current_version_id=version_id,
            revision=1,
            created_at=NOW,
            updated_at=NOW,
        )
    )
    db.execute(
        insert(LIBRARY_VERSIONS).values(
            version_id=version_id,
            lesson_id=lesson_id,
            version_no=1,
            content_json={"title": lesson_id},
            structured_content_hash="d" * 64,
            review_state="DRAFT",
            authored_by=MANAGER,
            created_at=NOW,
        )
    )
    db.execute(
        insert(ACCESS_GRANTS).values(
            access_grant_id=f"access-{lesson_id}",
            lesson_id=lesson_id,
            version_id=version_id,
            organization_id=ORG_ID,
            audience_kind="PARENT_GROUP",
            audience_ref=group_id,
            capability="VIEW",
            state="ACTIVE",
            granted_by=MANAGER,
            expires_at=None,
            revision=1,
            created_at=NOW,
        )
    )


@pytest.fixture
def parent_groups():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    with engine.connect() as connection:
        connection.exec_driver_sql("ATTACH DATABASE ':memory:' AS lesson")
    OrganizationModel.__table__.create(engine)
    AdultIdentityModel.__table__.create(engine)
    OrganizationAssignmentModel.__table__.create(engine)
    PARENT_GROUPS.create(engine)
    PARENT_GROUP_MEMBERS.create(engine)
    COMMAND_RECEIPTS.create(engine)
    LIBRARY_ITEMS.create(engine)
    LIBRARY_VERSIONS.create(engine)
    ACCESS_GRANTS.create(engine)

    db = Session(engine)
    db.add_all(
        [
            OrganizationModel(organization_id=ORG_ID, display_name=ORG_ID),
            AdultIdentityModel(
                subject=PARENT_A,
                account_id=PARENT_A_ACCOUNT,
                issuer="test-issuer",
                state="active",
                account_role="parent",
            ),
            AdultIdentityModel(
                subject=PARENT_B,
                account_id=PARENT_B_ACCOUNT,
                issuer="test-issuer",
                state="active",
                account_role="parent",
            ),
        ]
    )
    db.flush()
    for group_id in GROUPS:
        _seed_group(db, group_id)

    _seed_membership(
        db, membership_id="invite-account-a", group_id="invite-account",
        parent_ref=PARENT_A_ACCOUNT, state="invited",
    )
    _seed_membership(
        db, membership_id="invite-subject-a", group_id="invite-subject",
        parent_ref=PARENT_A, state="invited",
    )
    _seed_membership(
        db, membership_id="invite-account-b", group_id="invite-foreign",
        parent_ref=PARENT_B_ACCOUNT, state="invited",
    )
    _seed_membership(
        db, membership_id="active-account-a", group_id="member-account",
        parent_ref=PARENT_A_ACCOUNT, state="active",
    )
    _seed_membership(
        db, membership_id="active-subject-a", group_id="member-subject",
        parent_ref=PARENT_A, state="active",
    )
    _seed_membership(
        db, membership_id="active-account-b", group_id="member-foreign",
        parent_ref=PARENT_B_ACCOUNT, state="active",
    )
    _seed_membership(
        db, membership_id="grant-account-a", group_id="grant-account",
        parent_ref=PARENT_A_ACCOUNT, state="active",
    )
    _seed_membership(
        db, membership_id="grant-subject-a", group_id="grant-subject",
        parent_ref=PARENT_A, state="active",
    )
    _seed_membership(
        db, membership_id="grant-account-b", group_id="grant-foreign",
        parent_ref=PARENT_B_ACCOUNT, state="active",
    )
    _seed_membership(
        db, membership_id="duplicate-existing-subject", group_id="duplicate-account",
        parent_ref=PARENT_A, state="active",
    )
    _seed_membership(
        db, membership_id="duplicate-existing-account", group_id="duplicate-subject",
        parent_ref=PARENT_A_ACCOUNT, state="invited",
    )
    _seed_group_lesson(db, group_id="grant-account", lesson_id="group-account-lesson")
    _seed_group_lesson(db, group_id="grant-subject", lesson_id="group-subject-lesson")
    _seed_group_lesson(db, group_id="grant-foreign", lesson_id="group-foreign-lesson")
    db.commit()

    service = LessonLibraryService(db, storage=object(), parser=object(), scanner=object())

    def run_idempotent(**values: Any) -> Any:
        result = values["execute"]()
        db.commit()
        return result

    service._idempotent = run_idempotent  # type: ignore[method-assign]
    service._emit_group_invitation = lambda **_values: None  # type: ignore[method-assign]
    service._audit = lambda *_args, **_kwargs: None  # type: ignore[method-assign]
    service._find_parent_group_receipt = lambda *_args, **_kwargs: None  # type: ignore[method-assign]
    service._commit_parent_group_receipt = (  # type: ignore[method-assign]
        lambda **values: values["response"]
    )
    service._full_content_from_access = lambda _row: {  # type: ignore[method-assign]
        "title": "Shared lesson",
        "topic": "drawing",
        "target_age_band_ref": "age-band",
        "target_age_band_version": 1,
        "activities": [{}],
    }
    service._parent_detail = lambda row, export=False: {  # type: ignore[method-assign]
        "contract": "LessonExportV1" if export else "ParentLessonDetailV1",
        "lesson_id": row["lesson_id"],
        "version_id": row["version_id"],
    }
    original_load_membership = service._load_membership

    def load_membership(*args: Any, **kwargs: Any) -> Any:
        row = original_load_membership(*args, **kwargs)
        expires_at = row["expires_at"]
        if expires_at.tzinfo is None:
            return {**row, "expires_at": expires_at.replace(tzinfo=UTC)}
        return row

    service._load_membership = load_membership  # type: ignore[method-assign]
    try:
        yield db, service
    finally:
        db.close()
        engine.dispose()


def test_parent_reads_actions_and_leave_accept_both_identity_forms_without_cross_parent_access(
    parent_groups: Any,
) -> None:
    _db, service = parent_groups

    invitations_a = service.list_parent_group_invitations(
        parent_principal_ref=PARENT_A, limit=25, cursor=None
    )
    invitations_b = service.list_parent_group_invitations(
        parent_principal_ref=PARENT_B, limit=25, cursor=None
    )
    assert {item["membership_id"] for item in invitations_a["items"]} == {
        "invite-account-a",
        "invite-subject-a",
        "duplicate-existing-account",
    }
    assert {item["membership_id"] for item in invitations_b["items"]} == {
        "invite-account-b",
    }

    memberships_a = service.list_parent_group_memberships(
        parent_principal_ref=PARENT_A, limit=25, cursor=None
    )
    memberships_b = service.list_parent_group_memberships(
        parent_principal_ref=PARENT_B, limit=25, cursor=None
    )
    assert {item["membership_id"] for item in memberships_a["items"]} == {
        "active-account-a",
        "active-subject-a",
        "grant-account-a",
        "grant-subject-a",
        "duplicate-existing-subject",
    }
    assert {item["membership_id"] for item in memberships_b["items"]} == {
        "active-account-b",
        "grant-account-b",
    }

    with pytest.raises(LessonLibraryError) as foreign_accept:
        service.accept_parent_group_invitation(
            membership_id="invite-account-a", actor=PARENT_B, idempotency_key="foreign-accept"
        )
    assert (foreign_accept.value.status_code, foreign_accept.value.code) == (
        404,
        "RESOURCE_NOT_FOUND",
    )

    accepted = service.accept_parent_group_invitation(
        membership_id="invite-account-a", actor=PARENT_A, idempotency_key="account-accept"
    )
    declined = service.decline_parent_group_invitation(
        membership_id="invite-subject-a",
        actor=PARENT_A,
        actor_issuer="test-issuer",
        idempotency_key="subject-decline",
    )
    assert accepted["state"] == "ACTIVE"
    assert declined["state"] == "DECLINED"

    with pytest.raises(LessonLibraryError) as foreign_leave:
        service.revoke_parent_group_membership(
            organization_id=ORG_ID,
            group_id="member-subject",
            membership_id="active-subject-a",
            actor=PARENT_B,
            actor_issuer="test-issuer",
            manager=False,
            expected_revision=1,
            idempotency_key="foreign-leave",
        )
    assert (foreign_leave.value.status_code, foreign_leave.value.code) == (
        404,
        "RESOURCE_NOT_FOUND",
    )

    left = service.revoke_parent_group_membership(
        organization_id=ORG_ID,
        group_id="member-account",
        membership_id="active-account-a",
        actor=PARENT_A,
        actor_issuer="test-issuer",
        manager=False,
        expected_revision=1,
        idempotency_key="account-leave",
    )
    assert left["state"] == "REVOKED"


def test_parent_group_lesson_access_accepts_account_and_subject_but_not_another_parent(
    parent_groups: Any,
) -> None:
    _db, service = parent_groups
    lessons_a = service.list_parent_lessons(
        parent_principal_ref=PARENT_A, source="SHARED", limit=25, cursor=None
    )
    lessons_b = service.list_parent_lessons(
        parent_principal_ref=PARENT_B, source="SHARED", limit=25, cursor=None
    )
    assert {item["lesson_id"] for item in lessons_a["items"]} == {
        "group-account-lesson",
        "group-subject-lesson",
    }
    assert {item["lesson_id"] for item in lessons_b["items"]} == {
        "group-foreign-lesson",
    }
    assert service.get_parent_lesson(
        parent_principal_ref=PARENT_A, lesson_id="group-account-lesson"
    )["lesson_id"] == "group-account-lesson"
    with pytest.raises(LessonLibraryError) as foreign_lesson:
        service.get_parent_lesson(
            parent_principal_ref=PARENT_B, lesson_id="group-account-lesson"
        )
    assert foreign_lesson.value.status_code == 404


@pytest.mark.parametrize(
    ("group_id", "requested_ref"),
    (
        ("duplicate-account", PARENT_A_ACCOUNT),
        ("duplicate-subject", PARENT_A),
    ),
)
def test_duplicate_invitation_check_unifies_the_parents_two_references(
    parent_groups: Any,
    group_id: str,
    requested_ref: str,
) -> None:
    _db, service = parent_groups
    with pytest.raises(LessonLibraryError) as duplicate:
        service.invite_parent_to_group(
            organization_id=ORG_ID,
            group_id=group_id,
            actor=MANAGER,
            parent_principal_ref=requested_ref,
            idempotency_key=f"duplicate-{group_id}",
        )
    assert (duplicate.value.status_code, duplicate.value.code) == (
        409,
        "INVITATION_EXISTS",
    )


def test_new_manager_invitation_accepts_and_stores_the_supplied_parent_subject(
    parent_groups: Any,
) -> None:
    db, service = parent_groups
    response = service.invite_parent_to_group(
        organization_id=ORG_ID,
        group_id="new-subject-invitation",
        actor=MANAGER,
        parent_principal_ref=PARENT_A,
        idempotency_key="new-parent-subject-invitation",
    )
    stored = db.execute(
        PARENT_GROUP_MEMBERS.select().where(
            PARENT_GROUP_MEMBERS.c.membership_id == response["membership_id"]
        )
    ).mappings().one()
    assert stored["parent_principal_ref"] == PARENT_A
    assert response["state"] == "INVITED"


def test_unusable_parent_references_have_one_error_and_write_nothing(
    parent_groups: Any,
) -> None:
    db, service = parent_groups
    delattr(service, "_idempotent")
    db.add_all(
        [
            AdultIdentityModel(
                subject="teacher-ref",
                account_id="teacher-account",
                issuer="test-issuer",
                state="active",
                account_role="teacher",
            ),
            AdultIdentityModel(
                subject="school-manager-ref",
                account_id="school-manager-account",
                issuer="test-issuer",
                state="active",
                account_role="school_manager",
            ),
            AdultIdentityModel(
                subject="platform-admin-ref",
                account_id="platform-admin-account",
                issuer="test-issuer",
                state="active",
                account_role="platform_admin",
            ),
            AdultIdentityModel(
                subject="no-role-ref",
                account_id="no-role-account",
                issuer="test-issuer",
                state="active",
                account_role=None,
            ),
            AdultIdentityModel(
                subject="disabled-parent-ref",
                account_id="disabled-parent-account",
                issuer="test-issuer",
                state="disabled",
                account_role="parent",
            ),
            AdultIdentityModel(
                subject="inactive-parent-ref",
                account_id="inactive-parent-account",
                issuer="test-issuer",
                state="inactive",
                account_role="parent",
            ),
            AdultIdentityModel(
                subject="ambiguous-ref",
                account_id="ambiguous-owner-account",
                issuer="test-issuer",
                state="active",
                account_role="parent",
            ),
            AdultIdentityModel(
                subject="ambiguous-account-owner",
                account_id="ambiguous-ref",
                issuer="test-issuer",
                state="active",
                account_role="parent",
            ),
        ]
    )
    db.flush()

    cases = (
        ("invalid-unknown", "unknown-parent-ref"),
        ("invalid-teacher", "teacher-ref"),
        ("invalid-school-manager", "school-manager-ref"),
        ("invalid-platform-admin", "platform-admin-ref"),
        ("invalid-no-role", "no-role-ref"),
        ("invalid-disabled", "disabled-parent-ref"),
        ("invalid-inactive", "inactive-parent-ref"),
        ("invalid-ambiguous", "ambiguous-ref"),
    )
    errors: list[tuple[int, str, str]] = []
    for index, (group_id, parent_ref) in enumerate(cases):
        key = f"invalid-parent-{index}"
        with pytest.raises(LessonLibraryError) as invalid:
            service.invite_parent_to_group(
                organization_id=ORG_ID,
                group_id=group_id,
                actor=MANAGER,
                parent_principal_ref=parent_ref,
                idempotency_key=key,
            )

        error = invalid.value
        errors.append((error.status_code, error.code, error.message))
        assert db.execute(
            PARENT_GROUP_MEMBERS.select().where(
                PARENT_GROUP_MEMBERS.c.parent_group_id == group_id
            )
        ).mappings().all() == []
        assert db.execute(
            COMMAND_RECEIPTS.select().where(
                COMMAND_RECEIPTS.c.organization_id == ORG_ID,
                COMMAND_RECEIPTS.c.principal_ref == MANAGER,
                COMMAND_RECEIPTS.c.operation_scope
                == f"POST /organizations/{ORG_ID}/parent-groups/{group_id}/invitations",
                COMMAND_RECEIPTS.c.idempotency_key == key,
            )
        ).mappings().all() == []

    assert errors == [(404, "PARENT_NOT_FOUND", PARENT_NOT_FOUND_MESSAGE)] * len(cases)


def test_active_staff_assignment_keeps_the_existing_422_rejection(
    parent_groups: Any,
) -> None:
    db, service = parent_groups
    db.add(
        AdultIdentityModel(
            subject="assigned-teacher-ref",
            account_id="assigned-teacher-account",
            issuer="test-issuer",
            state="active",
            account_role="teacher",
        )
    )
    db.add(
        OrganizationAssignmentModel(
            assignment_id="assigned-teacher-assignment",
            organization_id=ORG_ID,
            subject="assigned-teacher-ref",
            class_id=None,
            role="teacher",
            active=True,
        )
    )
    db.commit()

    with pytest.raises(LessonLibraryError) as rejected:
        service.invite_parent_to_group(
            organization_id=ORG_ID,
            group_id="active-staff",
            actor=MANAGER,
            parent_principal_ref="assigned-teacher-ref",
            idempotency_key="active-staff-rejected",
        )

    assert (rejected.value.status_code, rejected.value.code) == (422, "INVALID_REQUEST")


def test_successful_invitation_replays_after_parent_is_disabled(
    parent_groups: Any,
) -> None:
    db, service = parent_groups
    delattr(service, "_idempotent")
    first = service.invite_parent_to_group(
        organization_id=ORG_ID,
        group_id="replay-after-disable",
        actor=MANAGER,
        parent_principal_ref=PARENT_A,
        idempotency_key="parent-disabled-after-success",
    )
    identity = db.get(AdultIdentityModel, PARENT_A)
    assert identity is not None
    identity.state = "disabled"
    db.commit()

    replayed = service.invite_parent_to_group(
        organization_id=ORG_ID,
        group_id="replay-after-disable",
        actor=MANAGER,
        parent_principal_ref=PARENT_A,
        idempotency_key="parent-disabled-after-success",
    )
    assert LessonLibraryService._json_safe(replayed) == LessonLibraryService._json_safe(first)
    membership_rows = db.execute(
        PARENT_GROUP_MEMBERS.select().where(
            PARENT_GROUP_MEMBERS.c.parent_group_id == "replay-after-disable"
        )
    ).mappings().all()
    receipt_rows = db.execute(
        COMMAND_RECEIPTS.select().where(
            COMMAND_RECEIPTS.c.organization_id == ORG_ID,
            COMMAND_RECEIPTS.c.principal_ref == MANAGER,
            COMMAND_RECEIPTS.c.operation_scope
            == f"POST /organizations/{ORG_ID}/parent-groups/replay-after-disable/invitations",
            COMMAND_RECEIPTS.c.idempotency_key == "parent-disabled-after-success",
        )
    ).mappings().all()
    assert len(membership_rows) == 1
    assert len(receipt_rows) == 1

    with pytest.raises(LessonLibraryError) as mismatch:
        service.invite_parent_to_group(
            organization_id=ORG_ID,
            group_id="replay-after-disable",
            actor=MANAGER,
            parent_principal_ref=PARENT_B,
            idempotency_key="parent-disabled-after-success",
        )
    assert (mismatch.value.status_code, mismatch.value.code) == (
        400,
        "INVALID_IDEMPOTENCY_KEY",
    )


def test_new_manager_invitation_still_stores_the_supplied_account_id_and_response(
    parent_groups: Any,
) -> None:
    db, service = parent_groups
    response = service.invite_parent_to_group(
        organization_id=ORG_ID,
        group_id="new-invitation",
        actor=MANAGER,
        parent_principal_ref=PARENT_A_ACCOUNT,
        idempotency_key="new-parent-invitation",
    )
    stored = db.execute(
        PARENT_GROUP_MEMBERS.select().where(
            PARENT_GROUP_MEMBERS.c.membership_id == response["membership_id"]
        )
    ).mappings().one()
    assert stored["parent_principal_ref"] == PARENT_A_ACCOUNT
    assert response["state"] == "INVITED"
    assert response["parent_group_id"] == "new-invitation"
    assert "parent_principal_ref" not in response
