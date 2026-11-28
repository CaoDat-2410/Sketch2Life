"""Synthetic PostgreSQL acceptance coverage for T-SHARE1; intentionally not run in this task."""

from __future__ import annotations

import json
import os
import threading
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest
from alembic.config import Config
from fastapi import Request
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete, select, text, update
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool

from alembic import command
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.domain.parent_profiles import ProfileSnapshot
from sketch2life.domain.profile_sharing import (
    ProfileShareConflict,
    generate_invitation_code,
    invitation_code_sha256,
)
from sketch2life.domain.profile_sharing import (
    delivered_at as domain_delivered_at,
)
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.lesson_occurrences.tables import OCCURRENCES, PLAN_REVISIONS
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    Be1CommandReceiptModel,
    ClassroomModel,
    EnrollmentModel,
    ManagedProfileModel,
    OrganizationAssignmentModel,
    OrganizationModel,
)
from sketch2life.infrastructure.persistence.core_models import CoreAuditEntryModel
from sketch2life.infrastructure.persistence.parent_models import (
    ParentChildProfileModel,
    ParentProfileRevisionModel,
)
from sketch2life.infrastructure.persistence.parent_profile_repository import (
    SqlParentProfileRepository,
)
from sketch2life.infrastructure.profile_sharing import service as profile_share_service
from sketch2life.infrastructure.profile_sharing.tables import PROFILE_SHARE_GRANTS
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult

_ISSUER = "synthetic-t-share1-issuer"
_ACTOR_HEADER = "X-T-SHARE1-Actor"
_FORBIDDEN_PORTS = {5432, 5433, 8000, 55439}
_ALLOWED_TEST_PORTS = {55440, 55441, 55458}


class ShareApi:
    def __init__(
        self,
        client: TestClient,
        factory: Any,
        parent: str,
        teacher: str,
        other_teacher: str,
        manager: str,
        organization_id: str,
        class_id: str,
        child_id: str,
    ) -> None:
        self.client = client
        self.factory = factory
        self.parent = parent
        self.teacher = teacher
        self.other_teacher = other_teacher
        self.manager = manager
        self.organization_id = organization_id
        self.class_id = class_id
        self.child_id = child_id

    def headers(self, actor: str, key: str | None = None) -> dict[str, str]:
        result = {_ACTOR_HEADER: actor}
        if key is not None:
            result["Idempotency-Key"] = key
        return result

    @property
    def teacher_path(self) -> str:
        return (
            f"/api/be1/v1/organizations/{self.organization_id}/classes/{self.class_id}"
            f"/profiles/{self.child_id}/parent-share"
        )


@pytest.fixture
def share_api(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[ShareApi]:
    database_url = os.environ.get("BE1_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("set BE1_TEST_DATABASE_URL to an isolated T-SHARE1 PostgreSQL database")
    parsed = make_url(database_url)
    database_name = parsed.database or ""
    if not all(token in database_name for token in ("be1_acceptance", "frc08_v4_e3_share")):
        pytest.fail("BE1_TEST_DATABASE_URL must name a frc08_v4_e3_share*be1_acceptance database")
    if parsed.port in _FORBIDDEN_PORTS or parsed.port not in _ALLOWED_TEST_PORTS:
        pytest.fail("T-SHARE1 tests require an isolated database on port 55440 or 55441")
    if parsed.host not in {"localhost", "127.0.0.1", "::1"}:
        pytest.fail("T-SHARE1 acceptance tests are restricted to a local disposable database")

    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", database_url)
    monkeypatch.setenv("SKETCH2LIFE_AUTH_PROVIDER", "development")
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("SKETCH2LIFE_SYNTHETIC_PILOT_ENABLED", "true")
    monkeypatch.setenv("SKETCH2LIFE_ROOM_CODE_HMAC_KEY", "synthetic-test-key-" + "x" * 40)
    monkeypatch.setenv("SKETCH2LIFE_BE1_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    app = create_app()
    runtime = app.state.be1_runtime
    if runtime.engine is None or runtime.session_factory is None:
        pytest.fail("The disposable PostgreSQL runtime did not initialize")

    run = uuid4().hex
    parent, teacher, other_teacher, manager = (str(uuid4()) for _ in range(4))
    organization_id, class_id, child_id = (str(uuid4()) for _ in range(3))
    with runtime.session_factory.begin() as db:
        db.add(
            OrganizationModel(
                organization_id=organization_id,
                display_name="Synthetic T-SHARE1 school",
                state="active",
            )
        )
        db.flush()
        db.add(
            ClassroomModel(
                class_id=class_id,
                organization_id=organization_id,
                display_name="Synthetic T-SHARE1 class",
                state="active",
                created_by=manager,
            )
        )
        db.add_all(
            [
                AdultIdentityModel(
                    subject=subject,
                    issuer=_ISSUER,
                    state="active",
                    account_role=role,
                )
                for subject, role in (
                    (parent, "parent"),
                    (teacher, "teacher"),
                    (other_teacher, "teacher"),
                    (manager, "school_manager"),
                )
            ]
        )
        db.flush()
        db.add_all(
            [
                OrganizationAssignmentModel(
                    assignment_id=str(uuid4()),
                    organization_id=organization_id,
                    subject=teacher,
                    class_id=class_id,
                    role="teacher",
                    active=True,
                ),
                OrganizationAssignmentModel(
                    assignment_id=str(uuid4()),
                    organization_id=organization_id,
                    subject=other_teacher,
                    class_id=class_id,
                    role="teacher",
                    active=True,
                ),
                OrganizationAssignmentModel(
                    assignment_id=str(uuid4()),
                    organization_id=organization_id,
                    subject=manager,
                    class_id=class_id,
                    role="school_admin",
                    active=True,
                ),
            ]
        )
        db.add(
            ManagedProfileModel(
                child_id=child_id,
                organization_id=organization_id,
                class_id=class_id,
                display_name="Synthetic managed profile",
                age_months=60,
                age_revision=1,
                age_source="SYNTHETIC_FIXTURE",
                consent_id=None,
                consent_purpose_ref=None,
                data_origin="SYNTHETIC_DEV",
                state="active",
                created_by=teacher,
                created_at=datetime.now(UTC),
            )
        )
        db.add(
            EnrollmentModel(
                enrollment_id=str(uuid4()),
                organization_id=organization_id,
                class_id=class_id,
                child_id=child_id,
                state="active",
                created_by=teacher,
                created_at=datetime.now(UTC) - timedelta(days=1),
            )
        )

    parent_principal = VerifiedPrincipal(subject=parent, issuer=_ISSUER, roles=frozenset())
    with runtime.session_factory() as db:
        SqlParentProfileRepository(db).create_profile(
            principal=parent_principal,
            snapshot=ProfileSnapshot("Synthetic Mina", 60, "likes drawing"),
            idempotency_key=f"t-share1-profile-{run}",
            request_id="t-share1",
        )
    principals = {
        subject: VerifiedPrincipal(subject=subject, issuer=_ISSUER, roles=frozenset())
        for subject in (parent, teacher, other_teacher, manager)
    }

    async def verified_actor(request: Request) -> VerifiedPrincipal:
        return principals[request.headers[_ACTOR_HEADER]]

    app.dependency_overrides[get_verified_adult] = verified_actor
    try:
        with TestClient(app, client=("127.0.0.1", 12700)) as client:
            yield ShareApi(
                client,
                runtime.session_factory,
                parent,
                teacher,
                other_teacher,
                manager,
                organization_id,
                class_id,
                child_id,
            )
    finally:
        app.dependency_overrides.clear()
        runtime.engine.dispose()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def test_invite_accept_scoped_read_revoke_and_neutral_delivery_history(share_api: ShareApi) -> None:
    parent = share_api.parent
    teacher = share_api.teacher
    other_teacher = share_api.other_teacher
    manager = share_api.manager
    create_path = "/v1/parent/share-grants"
    teacher_path = share_api.teacher_path
    create_body = {
        "profile_id": "",  # replaced after retrieving the parent-owned profile below
        "granted_fields": ["DISPLAY_NAME", "AGE_BAND"],
    }
    with share_api.factory() as db:
        profile = db.execute(
            select(ParentProfileRevisionModel.parent_profile_id)
            .where(ParentProfileRevisionModel.authored_by_subject == parent)
            .order_by(ParentProfileRevisionModel.created_at.desc())
            .limit(1)
        ).scalar_one()
    create_body["profile_id"] = str(profile)

    created = share_api.client.post(
        create_path,
        json=create_body,
        headers=share_api.headers(parent, "t-share1-create-key"),
    )
    assert created.status_code == 201, created.text
    grant = created.json()
    code = grant["invitation_code"]
    assert isinstance(code, str) and 16 <= len(code) <= 64
    assert created.headers["location"].endswith(grant["share_grant_id"])
    assert created.headers["etag"] == '"1"'
    assert created.headers["vary"] == "Authorization"

    replay = share_api.client.post(
        create_path,
        json=create_body,
        headers=share_api.headers(parent, "t-share1-create-key"),
    )
    assert replay.status_code == 201
    assert replay.json()["invitation_code"] is None

    before_accept = share_api.client.get(teacher_path, headers=share_api.headers(teacher))
    assert before_accept.status_code == 404
    accept_path = f"{teacher_path}/accept"
    accepted = share_api.client.post(
        accept_path,
        json={"invitation_code": code},
        headers=share_api.headers(teacher, "t-share1-accept-key"),
    )
    assert accepted.status_code == 200, accepted.text
    accepted_at = datetime.fromisoformat(accepted.json()["accepted_at"])
    assert accepted.json()["expires_at"]
    assert accepted.headers["vary"] == "Authorization"

    teacher_read = share_api.client.get(teacher_path, headers=share_api.headers(teacher))
    assert teacher_read.status_code == 200, teacher_read.text
    assert set(teacher_read.json()["fields"]) == {"display_name", "age_band"}
    assert teacher_read.headers["cache-control"] == "private, no-store"
    assert teacher_read.headers["vary"] == "Authorization"
    assert share_api.client.get(
        teacher_path, headers=share_api.headers(other_teacher)
    ).status_code == 404
    assert share_api.client.get(teacher_path, headers=share_api.headers(manager)).status_code == 403
    assert share_api.client.get(teacher_path, headers=share_api.headers(parent)).status_code == 404
    for organization_id, class_id in (
        (share_api.organization_id, "synthetic-other-class"),
        ("synthetic-other-organization", share_api.class_id),
    ):
        foreign_path = (
            f"/api/be1/v1/organizations/{organization_id}/classes/{class_id}"
            f"/profiles/{share_api.child_id}/parent-share"
        )
        assert share_api.client.get(
            foreign_path, headers=share_api.headers(teacher)
        ).status_code == 404

    with share_api.factory.begin() as db:
        occurrence_id = str(uuid4())
        plan_revision_id = str(uuid4())
        db.execute(
            OCCURRENCES.insert().values(
                occurrence_id=occurrence_id,
                organization_ref=share_api.organization_id,
                class_ref=share_api.class_id,
                responsible_teacher_ref=teacher,
                created_by=teacher,
                title="Synthetic drawing lesson",
                scheduled_date=accepted_at.date(),
            )
        )
        db.execute(
            PLAN_REVISIONS.insert().values(
                plan_revision_id=plan_revision_id,
                occurrence_id=occurrence_id,
                revision_no=1,
                source_document_revision_id=None,
                objectives=["Draw a synthetic shape"],
                teacher_direction="Use paper and crayons.",
                safety_notes=None,
                state="DRAFT",
                content_hash="0" * 64,
                source_lesson_id=None,
                source_lesson_version_id=None,
                source_lesson_version_no=None,
                source_lesson_version_hash=None,
                created_by=teacher,
            )
        )
        db.execute(
            update(PLAN_REVISIONS)
            .where(PLAN_REVISIONS.c.plan_revision_id == plan_revision_id)
            .values(state="APPROVED", approved_by=teacher, approved_at=accepted_at)
        )
        db.execute(
            update(OCCURRENCES)
            .where(OCCURRENCES.c.occurrence_id == occurrence_id)
            .values(
                approved_plan_revision_id=plan_revision_id,
                state="APPROVED",
                revision=2,
            )
        )
        db.execute(
            update(OCCURRENCES)
            .where(OCCURRENCES.c.occurrence_id == occurrence_id)
            .values(
                sample_slot_state="CLAIMED",
                sample_claimed_at=accepted_at,
                successful_sample_run_ref="synthetic-t-share1-run",
            )
        )
    delivery_path = f"/v1/parent/share-grants/{grant['share_grant_id']}/deliveries"
    deliveries = share_api.client.get(delivery_path, headers=share_api.headers(parent))
    assert deliveries.status_code == 200, deliveries.text
    assert deliveries.json()["content_access"] == "AVAILABLE"
    assert deliveries.json()["items"][0]["title"] == "Synthetic drawing lesson"

    current_grant = share_api.client.get(
        f"/v1/parent/share-grants/{grant['share_grant_id']}",
        headers=share_api.headers(parent),
    )
    assert current_grant.status_code == 200
    assert current_grant.headers["cache-control"] == "private, no-cache"
    assert current_grant.headers["vary"] == "Authorization"
    stale_revoke = share_api.client.post(
        f"/v1/parent/share-grants/{grant['share_grant_id']}/revoke",
        headers={
            **share_api.headers(parent, "t-share1-stale-revoke-key"),
            "If-Match": '"1"',
        },
    )
    assert stale_revoke.status_code == 409
    assert stale_revoke.json()["code"] == "STALE_REVISION"
    assert stale_revoke.json()["current_version"] == 2
    assert stale_revoke.headers["etag"] == '"2"'
    revoke = share_api.client.post(
        f"/v1/parent/share-grants/{grant['share_grant_id']}/revoke",
        headers={
            **share_api.headers(parent, "t-share1-revoke-key"),
            "If-Match": current_grant.headers["etag"],
        },
    )
    assert revoke.status_code == 200, revoke.text
    assert revoke.headers["vary"] == "Authorization"
    assert share_api.client.get(teacher_path, headers=share_api.headers(teacher)).status_code == 404
    ended = share_api.client.get(delivery_path, headers=share_api.headers(parent))
    assert ended.status_code == 200
    assert ended.json()["content_access"] == "ENDED"
    ended_item = ended.json()["items"][0]
    assert datetime.fromisoformat(ended_item["delivered_at"]) == accepted_at
    assert ended_item["title"] is None


def _parent_profile_id(api: ShareApi) -> str:
    with api.factory() as db:
        return str(
            db.execute(
                select(ParentProfileRevisionModel.parent_profile_id)
                .where(ParentProfileRevisionModel.authored_by_subject == api.parent)
                .order_by(ParentProfileRevisionModel.created_at.desc())
                .limit(1)
            ).scalar_one()
        )


def _invite(api: ShareApi, profile_id: str, key: str) -> dict[str, Any]:
    response = api.client.post(
        "/v1/parent/share-grants",
        json={"profile_id": profile_id, "granted_fields": ["DISPLAY_NAME", "AGE_BAND"]},
        headers=api.headers(api.parent, key),
    )
    assert response.status_code == 201, response.text
    return response.json()


def _accept(api: ShareApi, actor: str, code: str, key: str) -> Any:
    return api.client.post(
        f"{api.teacher_path}/accept",
        json={"invitation_code": code},
        headers=api.headers(actor, key),
    )


def _freeze_share_clock(monkeypatch: pytest.MonkeyPatch, moment: datetime) -> None:
    class _FrozenMeta(type(datetime)):  # type: ignore[misc]
        def __instancecheck__(cls, instance: object) -> bool:
            return isinstance(instance, datetime)

    class FrozenDateTime(datetime, metaclass=_FrozenMeta):
        @classmethod
        def now(cls, tz: Any = None) -> datetime:
            return moment if tz is not None else moment.replace(tzinfo=None)

    monkeypatch.setattr(profile_share_service, "datetime", FrozenDateTime)


def _insert_approved_occurrence(
    api: ShareApi,
    *,
    delivered_at: datetime,
    teacher: str,
    claimed_at: datetime | None = None,
) -> str:
    occurrence_id = str(uuid4())
    plan_revision_id = str(uuid4())
    with api.factory.begin() as db:
        db.execute(
            OCCURRENCES.insert().values(
                occurrence_id=occurrence_id,
                organization_ref=api.organization_id,
                class_ref=api.class_id,
                responsible_teacher_ref=teacher,
                created_by=teacher,
                title="Synthetic T-SHARE1 lesson",
                scheduled_date=delivered_at.date(),
            )
        )
        db.execute(
            PLAN_REVISIONS.insert().values(
                plan_revision_id=plan_revision_id,
                occurrence_id=occurrence_id,
                revision_no=1,
                source_document_revision_id=None,
                objectives=["Draw a synthetic shape"],
                teacher_direction="Use paper and crayons.",
                safety_notes=None,
                state="DRAFT",
                content_hash="0" * 64,
                source_lesson_id=None,
                source_lesson_version_id=None,
                source_lesson_version_no=None,
                source_lesson_version_hash=None,
                created_by=teacher,
            )
        )
        db.execute(
            update(PLAN_REVISIONS)
            .where(PLAN_REVISIONS.c.plan_revision_id == plan_revision_id)
            .values(state="APPROVED", approved_by=teacher, approved_at=delivered_at)
        )
        db.execute(
            update(OCCURRENCES)
            .where(OCCURRENCES.c.occurrence_id == occurrence_id)
            .values(
                approved_plan_revision_id=plan_revision_id,
                state="APPROVED",
                revision=2,
            )
        )
        if claimed_at is not None:
            db.execute(
                update(OCCURRENCES)
                .where(OCCURRENCES.c.occurrence_id == occurrence_id)
                .values(
                    sample_slot_state="CLAIMED",
                    sample_claimed_at=claimed_at,
                    successful_sample_run_ref="synthetic-t-share1-history",
                )
            )
    return occurrence_id


def test_archived_class_and_moved_profile_cannot_accept_or_read(
    share_api: ShareApi,
) -> None:
    profile_id = _parent_profile_id(share_api)
    archived_invite = _invite(share_api, profile_id, "t-share1-archived-create")
    with share_api.factory.begin() as db:
        db.execute(
            update(ClassroomModel)
            .where(ClassroomModel.class_id == share_api.class_id)
            .values(state="archived")
        )
    archived_accept = _accept(
        share_api,
        share_api.teacher,
        archived_invite["invitation_code"],
        "t-share1-archived-accept",
    )
    assert archived_accept.status_code == 404
    with share_api.factory.begin() as db:
        db.execute(
            update(ClassroomModel)
            .where(ClassroomModel.class_id == share_api.class_id)
            .values(state="active")
        )

    archived_profile_invite = _invite(
        share_api, profile_id, "t-share1-archived-profile-create"
    )
    with share_api.factory.begin() as db:
        db.execute(
            update(ManagedProfileModel)
            .where(ManagedProfileModel.child_id == share_api.child_id)
            .values(state="archived")
        )
    archived_profile_accept = _accept(
        share_api,
        share_api.teacher,
        archived_profile_invite["invitation_code"],
        "t-share1-archived-profile-accept",
    )
    archived_profile_read = share_api.client.get(
        share_api.teacher_path, headers=share_api.headers(share_api.teacher)
    )
    assert archived_profile_accept.status_code == 404
    assert archived_profile_read.status_code == 404
    with share_api.factory.begin() as db:
        db.execute(
            update(ManagedProfileModel)
            .where(ManagedProfileModel.child_id == share_api.child_id)
            .values(state="active")
        )

    accepted_invite = _invite(share_api, profile_id, "t-share1-moved-create-a")
    accepted = _accept(
        share_api,
        share_api.teacher,
        accepted_invite["invitation_code"],
        "t-share1-moved-accept-a",
    )
    assert accepted.status_code == 200, accepted.text
    moved_class_id = str(uuid4())
    with share_api.factory.begin() as db:
        db.add(
            ClassroomModel(
                class_id=moved_class_id,
                organization_id=share_api.organization_id,
                display_name="Synthetic moved profile class",
                state="active",
                created_by=share_api.manager,
            )
        )
        db.flush()
        db.execute(
            update(ManagedProfileModel)
            .where(ManagedProfileModel.child_id == share_api.child_id)
            .values(class_id=moved_class_id)
        )
    moved_read = share_api.client.get(
        share_api.teacher_path, headers=share_api.headers(share_api.teacher)
    )
    assert moved_read.status_code == 404
    next_invite = _invite(share_api, profile_id, "t-share1-moved-create-b")
    with share_api.factory.begin() as db:
        db.add(
            OrganizationAssignmentModel(
                assignment_id=str(uuid4()),
                organization_id=share_api.organization_id,
                subject=share_api.other_teacher,
                class_id=moved_class_id,
                role="teacher",
                active=True,
            )
        )
    moved_teacher_path = (
        f"/api/be1/v1/organizations/{share_api.organization_id}/classes/{moved_class_id}"
        f"/profiles/{share_api.child_id}/parent-share"
    )
    moved_teacher_read = share_api.client.get(
        moved_teacher_path, headers=share_api.headers(share_api.other_teacher)
    )
    assert moved_teacher_read.status_code == 404
    moved_accept = share_api.client.post(
        f"{moved_teacher_path}/accept",
        json={"invitation_code": next_invite["invitation_code"]},
        headers=share_api.headers(share_api.other_teacher, "t-share1-moved-accept-b"),
    )
    assert moved_accept.status_code == 409


def test_delete_pending_parent_profile_cannot_accept_an_invitation(
    share_api: ShareApi,
) -> None:
    profile_id = _parent_profile_id(share_api)
    invite = _invite(share_api, profile_id, "t-share1-parent-delete-create")
    with share_api.factory.begin() as db:
        db.execute(
            update(ParentChildProfileModel)
            .where(ParentChildProfileModel.parent_profile_id == UUID(profile_id))
            .values(state="DELETE_PENDING")
        )
    refused = _accept(
        share_api,
        share_api.teacher,
        invite["invitation_code"],
        "t-share1-parent-delete-accept",
    )
    assert refused.status_code == 404
    assert refused.json()["code"] == "RESOURCE_NOT_FOUND"


def test_create_accept_and_revoke_receipts_replay_without_bearer_code(share_api: ShareApi) -> None:
    profile_id = _parent_profile_id(share_api)
    invite = _invite(share_api, profile_id, "t-share1-replay-create")
    code = invite["invitation_code"]
    grant_id = invite["share_grant_id"]
    create_replay = _invite(share_api, profile_id, "t-share1-replay-create")
    assert create_replay["invitation_code"] is None

    accepted = _accept(share_api, share_api.teacher, code, "t-share1-replay-accept")
    assert accepted.status_code == 200, accepted.text
    accept_replay = _accept(share_api, share_api.teacher, code, "t-share1-replay-accept")
    assert accept_replay.status_code == 200
    assert accept_replay.json() == accepted.json()
    second_teacher = _accept(
        share_api, share_api.other_teacher, code, "t-share1-second-teacher"
    )
    assert second_teacher.status_code == 404
    assert second_teacher.json()["code"] == "RESOURCE_NOT_FOUND"

    different_invite = _invite(share_api, profile_id, "t-share1-replay-other-invite")
    mismatched_accept = _accept(
        share_api,
        share_api.teacher,
        different_invite["invitation_code"],
        "t-share1-replay-accept",
    )
    assert mismatched_accept.status_code == 400
    assert mismatched_accept.json()["code"] == "INVALID_IDEMPOTENCY_KEY"

    current = share_api.client.get(
        f"/v1/parent/share-grants/{grant_id}", headers=share_api.headers(share_api.parent)
    )
    assert current.status_code == 200
    revoke_headers = {
        **share_api.headers(share_api.parent, "t-share1-replay-revoke"),
        "If-Match": current.headers["etag"],
    }
    revoked = share_api.client.post(
        f"/v1/parent/share-grants/{grant_id}/revoke", headers=revoke_headers
    )
    assert revoked.status_code == 200
    revoke_replay = share_api.client.post(
        f"/v1/parent/share-grants/{grant_id}/revoke", headers=revoke_headers
    )
    assert revoke_replay.status_code == 200
    assert revoke_replay.json() == revoked.json()
    accept_after_revoke = _accept(
        share_api, share_api.teacher, code, "t-share1-replay-accept"
    )
    assert accept_after_revoke.status_code == 200
    assert accept_after_revoke.json() == accepted.json()

    with share_api.factory() as db:
        code_hash = db.execute(
            select(PROFILE_SHARE_GRANTS.c.invitation_code_sha256).where(
                PROFILE_SHARE_GRANTS.c.share_grant_id == UUID(grant_id)
            )
        ).scalar_one()
        receipts = db.scalars(
            select(Be1CommandReceiptModel).where(
                Be1CommandReceiptModel.principal_ref.in_(
                    {
                        profile_share_service.parent_scope_ref(
                            VerifiedPrincipal(
                                subject=share_api.parent,
                                issuer=_ISSUER,
                                roles=frozenset(),
                            )
                        ),
                        share_api.teacher,
                        share_api.other_teacher,
                    }
                ),
                Be1CommandReceiptModel.idempotency_key.in_(
                    {
                        "t-share1-replay-create",
                        "t-share1-replay-accept",
                        "t-share1-replay-revoke",
                        "t-share1-replay-other-invite",
                    }
                )
            )
        ).all()
        audit_rows = db.execute(
            select(
                CoreAuditEntryModel.action,
                CoreAuditEntryModel.owner_scope_ref,
                CoreAuditEntryModel.resource_id,
            ).where(CoreAuditEntryModel.resource_id == grant_id)
        ).all()
    receipt_dump = json.dumps(
        [
            {
                "operation_scope": receipt.operation_scope,
                "request_fingerprint": receipt.request_fingerprint,
                "response_json": receipt.response_json,
            }
            for receipt in receipts
        ],
        sort_keys=True,
    )
    audit_dump = json.dumps([tuple(row) for row in audit_rows], sort_keys=True)
    assert code not in receipt_dump and code not in audit_dump
    assert code_hash not in receipt_dump and code_hash not in audit_dump
    assert "Synthetic Mina" not in receipt_dump and "likes drawing" not in audit_dump


def test_receipt_pk_race_replays_the_committed_winner_and_rolls_back_loser(
    share_api: ShareApi, monkeypatch: pytest.MonkeyPatch
) -> None:
    profile_id = _parent_profile_id(share_api)
    profile_uuid = UUID(profile_id)
    parent_principal = VerifiedPrincipal(
        subject=share_api.parent, issuer=_ISSUER, roles=frozenset()
    )
    with share_api.factory() as db:
        profile = db.get(ParentChildProfileModel, profile_uuid)
        assert profile is not None
        profile_origin = profile.data_origin

    original_owned_profile = profile_share_service._owned_profile
    original_save_receipt = profile_share_service._save_receipt
    inserted_winner = False

    def without_profile_lock(
        db: Session, principal: VerifiedPrincipal, requested_id: UUID, *, lock: bool
    ) -> ParentChildProfileModel:
        return original_owned_profile(db, principal, requested_id, lock=False)

    def save_winning_receipt(db: Session, **values: Any) -> None:
        nonlocal inserted_winner
        original_save_receipt(db, **values)
        if inserted_winner:
            return
        inserted_winner = True
        winner_id = uuid4()
        winner_code = generate_invitation_code()
        scope_ref = profile_share_service.parent_scope_ref(parent_principal)
        source_body = values["body"]
        winner_body = dict(source_body)
        winner_body["share_grant_id"] = winner_id
        with share_api.factory.begin() as winner_db:
            winner_db.execute(
                PROFILE_SHARE_GRANTS.insert().values(
                    share_grant_id=winner_id,
                    parent_profile_id=profile_uuid,
                    grantor_scope_ref=scope_ref,
                    data_origin=profile_origin,
                    consent_basis="PARENT_GRANT_ACT_V1",
                    granted_fields=list(source_body["granted_fields"]),
                    invitation_code_sha256=invitation_code_sha256(winner_code),
                    state="INVITED",
                    revision=1,
                    created_at=source_body["created_at"],
                    invitation_expires_at=source_body["invitation_expires_at"],
                )
            )
            profile_share_service._parent_audit(
                winner_db,
                scope_ref=scope_ref,
                action="parent_share.grant.invite",
                share_grant_id=winner_id,
            )
            winner_db.add(
                Be1CommandReceiptModel(
                    principal_ref=values["principal_ref"],
                    operation_scope=values["operation_scope"],
                    idempotency_key=values["idempotency_key"],
                    organization_id=None,
                    request_fingerprint=values["fingerprint"],
                    response_json={
                        "body": profile_share_service._json_safe(winner_body),
                        "etag": values["etag"],
                    },
                )
            )

    monkeypatch.setattr(profile_share_service, "_owned_profile", without_profile_lock)
    monkeypatch.setattr(profile_share_service, "_save_receipt", save_winning_receipt)
    response = share_api.client.post(
        "/v1/parent/share-grants",
        json={"profile_id": profile_id, "granted_fields": ["DISPLAY_NAME", "AGE_BAND"]},
        headers=share_api.headers(share_api.parent, "t-share1-forced-pk-race"),
    )
    assert response.status_code == 201, response.text
    assert response.json()["invitation_code"] is None
    with share_api.factory() as db:
        grants = db.execute(
            select(PROFILE_SHARE_GRANTS.c.share_grant_id).where(
                PROFILE_SHARE_GRANTS.c.parent_profile_id == profile_uuid
            )
        ).all()
        receipts = db.scalars(
            select(Be1CommandReceiptModel).where(
                Be1CommandReceiptModel.idempotency_key == "t-share1-forced-pk-race",
                Be1CommandReceiptModel.principal_ref
                == profile_share_service.parent_scope_ref(parent_principal),
            )
        ).all()
        audits = db.scalars(
            select(CoreAuditEntryModel).where(
                CoreAuditEntryModel.resource_id == str(response.json()["share_grant_id"]),
                CoreAuditEntryModel.action == "parent_share.grant.invite",
            )
        ).all()
    assert len(grants) == len(receipts) == len(audits) == 1
    assert str(grants[0][0]) == response.json()["share_grant_id"]


def test_concurrent_accepts_leave_one_active_link_and_one_accept_audit(
    share_api: ShareApi,
) -> None:
    profile_id = _parent_profile_id(share_api)
    first = _invite(share_api, profile_id, "t-share1-concurrent-create-a")
    second = _invite(share_api, profile_id, "t-share1-concurrent-create-b")
    barrier = threading.Barrier(2)

    def accept(subject: str, code: str, key: str) -> object:
        principal = VerifiedPrincipal(subject=subject, issuer=_ISSUER, roles=frozenset())
        barrier.wait(timeout=10)
        with share_api.factory() as db:
            try:
                return profile_share_service.accept_teacher_share(
                    db,
                    principal,
                    organization_id=share_api.organization_id,
                    class_id=share_api.class_id,
                    child_id=share_api.child_id,
                    invitation_code=code,
                    idempotency_key=key,
                    authorize_teacher=lambda: None,
                    profile_released=lambda profile: True,
                    profile_withdrawn=lambda profile: False,
                )
            except ProfileShareConflict as error:
                return error

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(
            executor.map(
                lambda args: accept(*args),
                [
                    (share_api.teacher, first["invitation_code"], "t-share1-concurrent-accept-a"),
                    (
                        share_api.other_teacher,
                        second["invitation_code"],
                        "t-share1-concurrent-accept-b",
                    ),
                ],
            )
        )
    assert sum(not isinstance(outcome, ProfileShareConflict) for outcome in outcomes) == 1
    with share_api.factory() as db:
        active = db.execute(
            select(PROFILE_SHARE_GRANTS.c.share_grant_id).where(
                PROFILE_SHARE_GRANTS.c.organization_ref == share_api.organization_id,
                PROFILE_SHARE_GRANTS.c.managed_profile_ref == share_api.child_id,
                PROFILE_SHARE_GRANTS.c.state == "ACTIVE",
            )
        ).all()
        accept_audits = db.scalars(
            select(CoreAuditEntryModel).where(
                CoreAuditEntryModel.action == "parent_share.grant.accept",
                CoreAuditEntryModel.resource_id.in_(
                    (first["share_grant_id"], second["share_grant_id"])
                ),
            )
        ).all()
        accept_receipts = db.scalars(
            select(Be1CommandReceiptModel).where(
                Be1CommandReceiptModel.principal_ref.in_(
                    {share_api.teacher, share_api.other_teacher}
                ),
                Be1CommandReceiptModel.idempotency_key.in_(
                    {"t-share1-concurrent-accept-a", "t-share1-concurrent-accept-b"}
                )
            )
        ).all()
    assert len(active) == len(accept_audits) == len(accept_receipts) == 1


def test_share_grant_trigger_refuses_delete_fixed_fields_and_illegal_transition(
    share_api: ShareApi,
) -> None:
    invite = _invite(
        share_api, _parent_profile_id(share_api), "t-share1-trigger-create"
    )
    accepted = _accept(
        share_api,
        share_api.teacher,
        invite["invitation_code"],
        "t-share1-trigger-accept",
    )
    assert accepted.status_code == 200, accepted.text
    grant_id = UUID(invite["share_grant_id"])
    with share_api.factory() as db:
        revision = db.execute(
            select(PROFILE_SHARE_GRANTS.c.revision).where(
                PROFILE_SHARE_GRANTS.c.share_grant_id == grant_id
            )
        ).scalar_one()

    refusals = (
        (
            delete(PROFILE_SHARE_GRANTS).where(
                PROFILE_SHARE_GRANTS.c.share_grant_id == grant_id
            ),
            "PROFILE_SHARE_GRANT_DELETE_FORBIDDEN",
        ),
        (
            update(PROFILE_SHARE_GRANTS)
            .where(PROFILE_SHARE_GRANTS.c.share_grant_id == grant_id)
            .values(granted_fields=["INTERESTS_SUMMARY"], revision=revision + 1),
            "PROFILE_SHARE_GRANT_IMMUTABLE",
        ),
        (
            update(PROFILE_SHARE_GRANTS)
            .where(PROFILE_SHARE_GRANTS.c.share_grant_id == grant_id)
            .values(state="INVITED", revision=revision + 1),
            "PROFILE_SHARE_GRANT_ILLEGAL_TRANSITION",
        ),
    )
    for statement, trigger_message in refusals:
        with (
            pytest.raises(IntegrityError, match=trigger_message),
            share_api.factory.begin() as db,
        ):
            db.execute(statement)


def test_legacy_and_real_profiles_fail_the_d066100_release_predicate(
    share_api: ShareApi,
) -> None:
    profile_id = _parent_profile_id(share_api)
    with share_api.factory.begin() as db:
        profile = db.scalar(
            select(ManagedProfileModel).where(
                ManagedProfileModel.child_id == share_api.child_id
            )
        )
        assert profile is not None
        original_origin = profile.data_origin

    for index, origin in enumerate(("LEGACY_UNCLASSIFIED", "REAL")):
        invite = _invite(
            share_api,
            profile_id,
            f"t-share1-origin-create-{index}",
        )
        with share_api.factory.begin() as db:
            values: dict[str, object] = {"data_origin": origin}
            if origin == "REAL":
                values["consent_id"] = str(uuid4())
                values["consent_purpose_ref"] = "synthetic-release-check"
            db.execute(
                update(ManagedProfileModel)
                .where(ManagedProfileModel.child_id == share_api.child_id)
                .values(**values)
            )
        refused = _accept(
            share_api,
            share_api.teacher,
            invite["invitation_code"],
            f"t-share1-origin-accept-{index}",
        )
        assert refused.status_code == 409
        assert refused.json()["code"] == "CONSENT_NOT_EFFECTIVE"
        with share_api.factory.begin() as db:
            db.execute(
                update(ManagedProfileModel)
                .where(ManagedProfileModel.child_id == share_api.child_id)
                .values(
                    data_origin=original_origin,
                    consent_id=None,
                    consent_purpose_ref=None,
                )
            )


def test_expired_invitation_is_rejected_at_the_exact_boundary(
    share_api: ShareApi, monkeypatch: pytest.MonkeyPatch
) -> None:
    created_at = datetime.now(UTC)
    _freeze_share_clock(monkeypatch, created_at)
    invite = _invite(
        share_api, _parent_profile_id(share_api), "t-share1-expired-invite-create"
    )
    _freeze_share_clock(monkeypatch, created_at + timedelta(days=90))
    refused = _accept(
        share_api,
        share_api.teacher,
        invite["invitation_code"],
        "t-share1-expired-invite-accept",
    )
    assert refused.status_code == 409
    assert refused.json()["code"] == "INVITATION_EXPIRED"
    with share_api.factory() as db:
        row = db.execute(
            select(PROFILE_SHARE_GRANTS.c.state).where(
                PROFILE_SHARE_GRANTS.c.share_grant_id == UUID(invite["share_grant_id"])
            )
        ).scalar_one()
        acceptance_receipts = db.scalars(
            select(Be1CommandReceiptModel).where(
                Be1CommandReceiptModel.idempotency_key == "t-share1-expired-invite-accept",
                Be1CommandReceiptModel.principal_ref == share_api.teacher,
            )
        ).all()
    assert row == "INVITED" and acceptance_receipts == []


def test_settled_expiry_does_not_extend_history_and_history_has_a_30_day_cut(
    share_api: ShareApi, monkeypatch: pytest.MonkeyPatch
) -> None:
    start = datetime.now(UTC).replace(microsecond=0)
    _freeze_share_clock(monkeypatch, start)
    profile_id = _parent_profile_id(share_api)
    first = _invite(share_api, profile_id, "t-share1-expiry-history-create-a")
    accepted = _accept(
        share_api,
        share_api.teacher,
        first["invitation_code"],
        "t-share1-expiry-history-accept-a",
    )
    assert accepted.status_code == 200, accepted.text
    claimed_delivery = start + timedelta(days=55, hours=8)
    _insert_approved_occurrence(
        share_api,
        delivered_at=claimed_delivery,
        teacher=share_api.teacher,
        claimed_at=claimed_delivery,
    )
    fallback_recent_date = (start + timedelta(days=65)).date()
    _insert_approved_occurrence(
        share_api,
        delivered_at=start + timedelta(days=65),
        teacher=share_api.teacher,
    )
    _insert_approved_occurrence(
        share_api,
        delivered_at=start + timedelta(days=39),
        teacher=share_api.teacher,
    )
    _insert_approved_occurrence(
        share_api,
        delivered_at=start + timedelta(days=92),
        teacher=share_api.teacher,
        claimed_at=start + timedelta(days=92),
    )

    _freeze_share_clock(monkeypatch, start + timedelta(days=70))
    history_path = f"/v1/parent/share-grants/{first['share_grant_id']}/deliveries"
    within_window = share_api.client.get(
        history_path, headers=share_api.headers(share_api.parent)
    )
    assert within_window.status_code == 200
    visible_times = [
        datetime.fromisoformat(item["delivered_at"])
        for item in within_window.json()["items"]
    ]
    assert visible_times == [
        domain_delivered_at(None, fallback_recent_date),
        domain_delivered_at(claimed_delivery, claimed_delivery.date()),
    ]

    settled_at = start + timedelta(days=95)
    _freeze_share_clock(monkeypatch, settled_at)
    second = _invite(share_api, profile_id, "t-share1-expiry-history-create-b")
    second_accept = _accept(
        share_api,
        share_api.other_teacher,
        second["invitation_code"],
        "t-share1-expiry-history-accept-b",
    )
    assert second_accept.status_code == 200, second_accept.text
    with share_api.factory() as db:
        expired_row = db.execute(
            select(
                PROFILE_SHARE_GRANTS.c.expires_at,
                PROFILE_SHARE_GRANTS.c.expired_at,
                PROFILE_SHARE_GRANTS.c.state,
            ).where(PROFILE_SHARE_GRANTS.c.share_grant_id == UUID(first["share_grant_id"]))
        ).one()
    assert expired_row.state == "EXPIRED"
    assert expired_row.expires_at == start + timedelta(days=90)
    assert expired_row.expired_at == settled_at
    settled_replay = _accept(
        share_api,
        share_api.teacher,
        first["invitation_code"],
        "t-share1-expiry-history-accept-a",
    )
    assert settled_replay.status_code == 200
    assert settled_replay.json() == accepted.json()

    after_settlement = share_api.client.get(
        history_path, headers=share_api.headers(share_api.parent)
    )
    assert after_settlement.status_code == 200
    assert after_settlement.json()["items"] == []


def test_history_excludes_occurrences_after_enrollment_withdrawal(share_api: ShareApi) -> None:
    invite = _invite(
        share_api, _parent_profile_id(share_api), "t-share1-withdrawal-create"
    )
    accepted = _accept(
        share_api,
        share_api.teacher,
        invite["invitation_code"],
        "t-share1-withdrawal-accept",
    )
    assert accepted.status_code == 200, accepted.text
    # History only shows deliveries at or after the acceptance instant.
    delivered_at = datetime.fromisoformat(accepted.json()["accepted_at"]) + timedelta(
        microseconds=1
    )
    _insert_approved_occurrence(
        share_api,
        delivered_at=delivered_at,
        teacher=share_api.teacher,
        claimed_at=delivered_at,
    )
    history_path = f"/v1/parent/share-grants/{invite['share_grant_id']}/deliveries"
    before = share_api.client.get(history_path, headers=share_api.headers(share_api.parent))
    assert before.status_code == 200
    assert len(before.json()["items"]) == 1
    with share_api.factory.begin() as db:
        db.execute(
            update(EnrollmentModel)
            .where(
                EnrollmentModel.organization_id == share_api.organization_id,
                EnrollmentModel.class_id == share_api.class_id,
                EnrollmentModel.child_id == share_api.child_id,
            )
            .values(state="withdrawn")
        )
    after = share_api.client.get(history_path, headers=share_api.headers(share_api.parent))
    assert after.status_code == 200
    assert after.json()["items"] == []


@pytest.fixture
def share_roundtrip(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[tuple[Config, Engine]]:
    database_url = os.environ.get("T_SHARE1_ROUNDTRIP_DATABASE_URL")
    if not database_url:
        pytest.skip(
            "set T_SHARE1_ROUNDTRIP_DATABASE_URL to a disposable T-SHARE1 round-trip database"
        )
    parsed = make_url(database_url)
    database_name = parsed.database or ""
    if not all(
        token in database_name
        for token in ("frc08_v4_e3_share", "roundtrip", "be1_acceptance")
    ):
        pytest.fail(
            "T_SHARE1_ROUNDTRIP_DATABASE_URL must name a "
            "frc08_v4_e3_share*roundtrip*be1_acceptance database"
        )
    if parsed.port in _FORBIDDEN_PORTS or parsed.port not in _ALLOWED_TEST_PORTS:
        pytest.fail("T-SHARE1 round-trip tests require an isolated database on port 55440 or 55441")
    if parsed.host not in {"localhost", "127.0.0.1", "::1"}:
        pytest.fail("T-SHARE1 round-trip tests are restricted to a local disposable database")

    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", database_url)
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    backend = Path(__file__).resolve().parents[2]
    config = Config(str(backend / "alembic.ini"))
    engine = create_engine(database_url, poolclass=NullPool)
    try:
        yield config, engine
    finally:
        engine.dispose()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def test_downgrade_refuses_when_a_share_grant_row_exists(
    share_roundtrip: tuple[Config, Engine],
) -> None:
    config, engine = share_roundtrip
    command.upgrade(config, "heads")
    principal = VerifiedPrincipal(
        subject=f"t-share1-downgrade-{uuid4()}", issuer=_ISSUER, roles=frozenset()
    )
    with Session(engine) as db:
        created = SqlParentProfileRepository(db).create_profile(
            principal=principal,
            snapshot=ProfileSnapshot("Synthetic downgrade profile", 60, None),
            idempotency_key=f"t-share1-downgrade-{uuid4()}",
            request_id="t-share1-downgrade",
        )
    parent_profile_id = UUID(str(created.body["profile_id"]))
    created_at = datetime.now(UTC).replace(microsecond=0)
    with engine.begin() as connection:
        connection.execute(
            PROFILE_SHARE_GRANTS.insert().values(
                share_grant_id=uuid4(),
                parent_profile_id=parent_profile_id,
                grantor_scope_ref=profile_share_service.parent_scope_ref(principal),
                data_origin="SYNTHETIC_DEV",
                consent_basis="PARENT_GRANT_ACT_V1",
                granted_fields=["DISPLAY_NAME"],
                invitation_code_sha256=invitation_code_sha256(generate_invitation_code()),
                state="INVITED",
                revision=1,
                created_at=created_at,
                invitation_expires_at=created_at + timedelta(days=90),
            )
        )

    with pytest.raises(Exception, match="T-SHARE1 downgrade refused"):
        command.downgrade(config, "20261126_sl_0001")
    with engine.connect() as connection:
        assert connection.scalar(
            select(PROFILE_SHARE_GRANTS.c.share_grant_id).limit(1)
        ) is not None
        assert "20261126_dc_0001" in connection.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalars().all()
