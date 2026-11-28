"""Parent lesson grants work for either verified Parent identifier on SQLite."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any

import pytest
from sqlalchemy import create_engine, insert
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.infrastructure.lesson_library.feedback import ParentLessonFeedbackService
from sketch2life.infrastructure.lesson_library.service import (
    LessonLibraryError,
    LessonLibraryService,
)
from sketch2life.infrastructure.lesson_library.tables import (
    ACCESS_GRANTS,
    LIBRARY_ITEMS,
    LIBRARY_VERSIONS,
    PARENT_GROUP_MEMBERS,
    PARENT_GROUPS,
)
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel

ORG_ID = "share-org"
TEACHER = "share-teacher"
PARENT_A = "parent-a-subject"
PARENT_A_ACCOUNT = "parent-a-account"
PARENT_B = "parent-b-subject"
PARENT_B_ACCOUNT = "parent-b-account"
CONTENT_HASH = "c" * 64
NOW = datetime.now(UTC)


@compiles(JSONB, "sqlite")
def _jsonb_as_json_on_sqlite(_type: Any, _compiler: Any, **_kw: Any) -> str:
    return "JSON"


def _seed_lesson(db: Session, lesson_id: str) -> str:
    version_id = f"version-{lesson_id}"
    db.execute(
        insert(LIBRARY_ITEMS).values(
            lesson_id=lesson_id,
            organization_id=ORG_ID,
            owner_kind="ORGANIZATION",
            created_by=TEACHER,
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
            structured_content_hash=CONTENT_HASH,
            review_state="DRAFT",
            authored_by=TEACHER,
            created_at=NOW,
        )
    )
    return version_id


def _seed_grant(
    db: Session,
    *,
    grant_id: str,
    lesson_id: str,
    version_id: str,
    audience_ref: str,
    state: str,
    capability: str = "VIEW",
    expires_at: datetime | None = None,
) -> None:
    db.execute(
        insert(ACCESS_GRANTS).values(
            access_grant_id=grant_id,
            lesson_id=lesson_id,
            version_id=version_id,
            organization_id=ORG_ID,
            audience_kind="PRINCIPAL",
            audience_ref=audience_ref,
            capability=capability,
            state=state,
            granted_by=TEACHER,
            expires_at=expires_at,
            revision=1,
            created_at=NOW,
        )
    )


@pytest.fixture
def parent_library():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    with engine.connect() as connection:
        connection.exec_driver_sql("ATTACH DATABASE ':memory:' AS lesson")
    AdultIdentityModel.__table__.create(engine)
    LIBRARY_ITEMS.create(engine)
    LIBRARY_VERSIONS.create(engine)
    PARENT_GROUPS.create(engine)
    PARENT_GROUP_MEMBERS.create(engine)
    ACCESS_GRANTS.create(engine)

    db = Session(engine)
    db.add_all(
        [
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
    lesson_versions = {
        lesson_id: _seed_lesson(db, lesson_id)
        for lesson_id in (
            "teacher-account-invite",
            "legacy-subject-invite",
            "foreign-account-invite",
            "expired-account-invite",
            "account-view-a",
            "subject-view-a",
            "account-view-b",
            "account-download-a",
        )
    }
    _seed_grant(
        db,
        grant_id="legacy-subject-invite",
        lesson_id="legacy-subject-invite",
        version_id=lesson_versions["legacy-subject-invite"],
        audience_ref=PARENT_A,
        state="INVITED",
    )
    _seed_grant(
        db,
        grant_id="foreign-account-invite",
        lesson_id="foreign-account-invite",
        version_id=lesson_versions["foreign-account-invite"],
        audience_ref=PARENT_B_ACCOUNT,
        state="INVITED",
    )
    _seed_grant(
        db,
        grant_id="expired-account-invite",
        lesson_id="expired-account-invite",
        version_id=lesson_versions["expired-account-invite"],
        audience_ref=PARENT_A_ACCOUNT,
        state="INVITED",
        expires_at=NOW - timedelta(days=1),
    )
    for grant_id, lesson_id, audience_ref, capability in (
        ("account-view-a", "account-view-a", PARENT_A_ACCOUNT, "VIEW"),
        ("subject-view-a", "subject-view-a", PARENT_A, "VIEW"),
        ("account-view-b", "account-view-b", PARENT_B_ACCOUNT, "VIEW"),
        ("account-download-a", "account-download-a", PARENT_A_ACCOUNT, "DOWNLOAD"),
    ):
        _seed_grant(
            db,
            grant_id=grant_id,
            lesson_id=lesson_id,
            version_id=lesson_versions[lesson_id],
            audience_ref=audience_ref,
            state="ACTIVE",
            capability=capability,
        )
    db.commit()

    service = LessonLibraryService(db, storage=object(), parser=object(), scanner=object())

    def run_idempotent(**values: Any) -> Any:
        result = values["execute"]()
        db.commit()
        return result

    service._idempotent = run_idempotent  # type: ignore[method-assign]
    service._replay = lambda **_values: None  # type: ignore[method-assign]
    service._audit = lambda *_args, **_kwargs: None  # type: ignore[method-assign]
    service._recalculate_visibility = lambda *_args, **_kwargs: None  # type: ignore[method-assign]
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
    try:
        yield db, service, lesson_versions
    finally:
        db.close()
        engine.dispose()


def test_account_id_and_subject_invites_work_without_cross_parent_access(
    parent_library: Any,
) -> None:
    db, service, lesson_versions = parent_library
    created = service.create_access_grant(
        organization_id=ORG_ID,
        lesson_id="teacher-account-invite",
        actor=TEACHER,
        version_id=lesson_versions["teacher-account-invite"],
        audience_kind="PRINCIPAL",
        audience_ref=PARENT_A_ACCOUNT,
        capability="VIEW",
        expires_at=None,
        idempotency_key="teacher-share-account-id",
    )
    assert created["audience_ref"] == PARENT_A_ACCOUNT

    invited_a = service.list_lesson_invitations(
        parent_principal_ref=PARENT_A, limit=25, cursor=None
    )
    invited_b = service.list_lesson_invitations(
        parent_principal_ref=PARENT_B, limit=25, cursor=None
    )
    assert {item["access_grant_id"] for item in invited_a["items"]} == {
        created["access_grant_id"],
        "legacy-subject-invite",
    }
    assert {item["access_grant_id"] for item in invited_b["items"]} == {
        "foreign-account-invite",
    }
    assert "expired-account-invite" not in {
        item["access_grant_id"] for item in invited_a["items"]
    }

    accepted = service.respond_to_lesson_invitation(
        access_grant_id=created["access_grant_id"],
        actor=PARENT_A,
        accept=True,
        idempotency_key="parent-accept-account-id",
    )
    declined = service.respond_to_lesson_invitation(
        access_grant_id="legacy-subject-invite",
        actor=PARENT_A,
        accept=False,
        idempotency_key="parent-decline-subject",
    )
    assert accepted["state"] == "ACTIVE"
    assert declined["state"] == "DECLINED"

    with pytest.raises(LessonLibraryError) as foreign_response:
        service.respond_to_lesson_invitation(
            access_grant_id=created["access_grant_id"],
            actor=PARENT_B,
            accept=True,
            idempotency_key="other-parent-accept",
        )
    assert (foreign_response.value.status_code, foreign_response.value.code) == (
        404,
        "RESOURCE_NOT_FOUND",
    )

    assert db.execute(
        ACCESS_GRANTS.select().where(ACCESS_GRANTS.c.access_grant_id == "expired-account-invite")
    ).mappings().one()["state"] == "INVITED"


def test_account_id_and_legacy_subject_grants_cover_parent_reads_and_revoke(
    parent_library: Any,
) -> None:
    _db, service, _lesson_versions = parent_library
    listed_a = service.list_parent_lessons(
        parent_principal_ref=PARENT_A,
        source="SHARED",
        limit=25,
        cursor=None,
    )
    listed_b = service.list_parent_lessons(
        parent_principal_ref=PARENT_B,
        source="SHARED",
        limit=25,
        cursor=None,
    )
    assert {item["lesson_id"] for item in listed_a["items"]} == {
        "account-view-a",
        "subject-view-a",
    }
    assert {item["lesson_id"] for item in listed_b["items"]} == {"account-view-b"}

    assert service.get_parent_lesson(
        parent_principal_ref=PARENT_A, lesson_id="account-view-a"
    )["lesson_id"] == "account-view-a"
    assert service.get_parent_lesson(
        parent_principal_ref=PARENT_A, lesson_id="subject-view-a"
    )["lesson_id"] == "subject-view-a"
    assert service.get_parent_lesson_export(
        parent_principal_ref=PARENT_A, lesson_id="account-download-a"
    )["contract"] == "LessonExportV1"
    assert {row["lesson_id"] for row in service.list_parent_activity_catalog(
        parent_principal_ref=PARENT_A
    )} == {"account-view-a", "subject-view-a"}

    feedback_a = ParentLessonFeedbackService(
        SimpleNamespace(
            db=service.db,
            principal=VerifiedPrincipal(PARENT_A, "test-issuer", frozenset()),
        ),
        parent_lesson=lambda lesson_id: service.get_parent_lesson(
            parent_principal_ref=PARENT_A, lesson_id=lesson_id
        ),
    )
    _item, feedback_version = feedback_a._authorize_lesson("account-view-a")
    assert feedback_version == "version-account-view-a"

    with pytest.raises(LessonLibraryError) as foreign_detail:
        service.get_parent_lesson(parent_principal_ref=PARENT_B, lesson_id="account-view-a")
    assert foreign_detail.value.status_code == 404
    with pytest.raises(LessonLibraryError) as foreign_download:
        service.get_parent_lesson_export(
            parent_principal_ref=PARENT_B, lesson_id="account-download-a"
        )
    assert foreign_download.value.status_code == 404

    revoked = service.revoke_access_grant(
        organization_id=ORG_ID,
        lesson_id="account-view-a",
        grant_id="account-view-a",
        actor=TEACHER,
        manager=False,
        expected_revision=1,
        idempotency_key="teacher-revoke-account-share",
    )
    assert revoked["state"] == "REVOKED"
