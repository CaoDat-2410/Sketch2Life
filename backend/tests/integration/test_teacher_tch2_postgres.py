"""T-TCH2 PostgreSQL acceptance for portfolio, activity/history, and own-profile reads.

Runs only against a disposable ``frc08*be1_acceptance`` database. All people, lesson text, and
child records are synthetic; Firebase Authentication is replaced by a test identity provider.
"""

from __future__ import annotations

import hashlib
import os
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from sqlalchemy import select, update

from sketch2life.application.ports.identity import IdentityAccountProfile, VerifiedPrincipal
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.lesson_library.tables import (
    LIBRARY_ITEMS,
    LIBRARY_VERSIONS,
    VERSION_ACTIVITIES,
)
from sketch2life.infrastructure.lesson_occurrences.tables import OCCURRENCES
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    ClassroomModel,
    ClassroomSessionModel,
    ConsentRecordModel,
    ManagedProfileModel,
    ObservationModel,
    OrganizationAssignmentModel,
    OrganizationModel,
)
from sketch2life.infrastructure.persistence.core_models import CoreAuditEntryModel
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult

ISSUER = "synthetic-tch2-issuer"
ACTOR_HEADER = "X-TCH2-Actor"


class _FakeIdentityProvider:
    def __init__(self, subjects: dict[str, str]) -> None:
        self.subjects = subjects
        self.display_names = {subject: f"Synthetic {label}" for label, subject in subjects.items()}

    def get_account_profiles(self, subjects: list[str]) -> dict[str, IdentityAccountProfile]:
        return {
            subject: IdentityAccountProfile(
                subject=subject,
                email=f"{self.subjects.get(subject, 'adult')}@example.test",
                display_name=self.display_names.get(subject),
            )
            for subject in subjects
        }

@dataclass
class Tch2:
    app: FastAPI
    client: TestClient
    organization_id: str
    foreign_organization_id: str
    classes: dict[str, str] = field(default_factory=dict)
    subjects: dict[str, str] = field(default_factory=dict)
    accounts: dict[str, str] = field(default_factory=dict)
    principals: dict[str, VerifiedPrincipal] = field(default_factory=dict)
    children: dict[str, str] = field(default_factory=dict)
    sessions: dict[str, str] = field(default_factory=dict)
    activities: dict[str, dict[str, str]] = field(default_factory=dict)
    occurrences: dict[str, str] = field(default_factory=dict)
    provider: _FakeIdentityProvider | None = None

    @property
    def factory(self) -> Any:
        return self.app.state.be1_runtime.session_factory

    def get(self, actor: str, path: str) -> Any:
        return self.client.get(path, headers={ACTOR_HEADER: actor})

    def portfolio(self, child_key: str = "synthetic", class_key: str = "a") -> str:
        return (
            f"/api/be1/v1/organizations/{self.organization_id}/classes/"
            f"{self.classes[class_key]}/profiles/{self.children[child_key]}/portfolio"
        )


def _identity(
    db: Any,
    directory: Tch2,
    label: str,
    account_role: str,
    organization_id: str,
    assignments: tuple[tuple[str | None, str], ...],
) -> None:
    subject = f"synthetic-tch2-{label}-{uuid4().hex[:10]}"
    identity = AdultIdentityModel(
        subject=subject,
        issuer=ISSUER,
        state="active",
        account_role=account_role,
    )
    db.add(identity)
    db.flush()
    directory.subjects[label] = subject
    directory.accounts[label] = identity.account_id
    directory.principals[label] = VerifiedPrincipal(
        subject=subject,
        issuer=ISSUER,
        roles=frozenset(),
    )
    for class_id, assignment_role in assignments:
        db.add(
            OrganizationAssignmentModel(
                assignment_id=str(uuid4()),
                organization_id=organization_id,
                subject=subject,
                class_id=class_id,
                role=assignment_role,
                active=True,
            )
        )


def _add_profile(
    db: Any,
    *,
    organization_id: str,
    class_id: str,
    child_id: str,
    creator: str,
    data_origin: str,
    consent_id: str | None = None,
    purpose_ref: str | None = None,
) -> None:
    db.add(
        ManagedProfileModel(
            child_id=child_id,
            organization_id=organization_id,
            class_id=class_id,
            display_name=f"Synthetic profile {child_id[-6:]}",
            age_months=72,
            age_revision=1,
            age_source="SYNTHETIC_FIXTURE" if data_origin == "SYNTHETIC_DEV" else "ADULT_DECLARED",
            data_origin=data_origin,
            consent_id=consent_id,
            consent_purpose_ref=purpose_ref,
            state="active",
            created_by=creator,
        )
    )


def _add_observation(
    db: Any,
    *,
    organization_id: str,
    session_id: str,
    child_id: str,
    created_by: str,
    note: str,
    created_at: datetime,
) -> str:
    observation_id = str(uuid4())
    db.add(
        ObservationModel(
            observation_id=observation_id,
            organization_id=organization_id,
            session_id=session_id,
            child_id=child_id,
            kind="observation",
            content={"note": note},
            source_refs=["synthetic-private-source-ref"],
            created_by=created_by,
            created_at=created_at,
        )
    )
    return observation_id


def _add_activity_lesson(
    db: Any,
    *,
    organization_id: str,
    creator: str,
    label: str,
    visibility: str = "SCHOOL",
    state: str = "ACTIVE",
    moderation: str = "VISIBLE",
    review_state: str = "APPROVED",
) -> dict[str, str]:
    lesson_id, version_id, activity_id = str(uuid4()), str(uuid4()), str(uuid4())
    content_hash = hashlib.sha256(label.encode("utf-8")).hexdigest()
    db.execute(
        LIBRARY_ITEMS.insert().values(
            lesson_id=lesson_id,
            organization_id=organization_id,
            created_by=creator,
            state=state,
            visibility=visibility,
            internal_visibility="PRIVATE" if visibility == "PRIVATE" else "SCHOOL",
            moderation_state=moderation,
            current_version_id=None,
        )
    )
    db.execute(
        LIBRARY_VERSIONS.insert().values(
            version_id=version_id,
            lesson_id=lesson_id,
            version_no=1,
            content_json={"title": f"Synthetic lesson {label}", "topic": "shapes"},
            structured_content_hash=content_hash,
            review_state=review_state,
            authored_by=creator,
        )
    )
    db.execute(
        VERSION_ACTIVITIES.insert().values(
            activity_id=activity_id,
            version_id=version_id,
            activity_order=1,
            activity_json={
                "title": f"Synthetic activity {label}",
                "objective": "Practice shapes",
                "activity_kind": "mixed",
                "materials_text": "Paper",
                "preparation_text": "Prepare paper",
                "instructions_text": "Draw a shape",
                "observation_notes": "Observe the outline",
                "safety_notes": "Use child-safe materials",
            },
        )
    )
    db.execute(
        update(LIBRARY_ITEMS)
        .where(LIBRARY_ITEMS.c.lesson_id == lesson_id)
        .values(current_version_id=version_id)
    )
    return {
        "lesson_id": lesson_id,
        "version_id": version_id,
        "activity_id": activity_id,
    }


def _add_occurrence(
    db: Any,
    *,
    organization_id: str,
    class_id: str,
    teacher_account: str,
    title: str,
    created_at: datetime,
) -> str:
    occurrence_id = str(uuid4())
    db.execute(
        OCCURRENCES.insert().values(
            occurrence_id=occurrence_id,
            organization_ref=organization_id,
            class_ref=class_id,
            responsible_teacher_ref=teacher_account,
            created_by=teacher_account,
            title=title,
            scheduled_date=None,
            state="DRAFT",
            revision=1,
            approved_plan_revision_id=None,
            source_lesson_id=None,
            source_lesson_version_id=None,
            source_lesson_version_no=None,
            source_lesson_version_hash=None,
            sample_slot_state="AVAILABLE",
            successful_sample_run_ref=None,
            created_at=created_at,
            updated_at=created_at,
        )
    )
    return occurrence_id


@pytest.fixture
def tch2(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> Iterator[Tch2]:
    database_url = os.environ.get("BE1_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("set BE1_TEST_DATABASE_URL to a disposable PostgreSQL database")
    database_name = database_url.rsplit("/", 1)[-1]
    if "be1_acceptance" not in database_name or "frc08" not in database_name:
        pytest.fail(
            "BE1_TEST_DATABASE_URL must point to a disposable frc08*be1_acceptance database"
        )
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", database_url)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("SKETCH2LIFE_AUTH_PROVIDER", "development")
    monkeypatch.setenv("SKETCH2LIFE_AI_PROVIDER", "disabled")
    monkeypatch.setenv("SKETCH2LIFE_SYNTHETIC_PILOT_ENABLED", "true")
    monkeypatch.setenv("SKETCH2LIFE_ROOM_CODE_HMAC_KEY", "synthetic-test-key-" + "x" * 40)
    monkeypatch.setenv("SKETCH2LIFE_BE1_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    monkeypatch.delenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", raising=False)
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()

    app = create_app()
    runtime = app.state.be1_runtime
    if runtime.engine is None or runtime.session_factory is None:
        pytest.fail("PostgreSQL runtime did not initialize")
    token = uuid4().hex[:10]
    organization_id = f"synthetic-tch2-org-{token}"
    foreign_organization_id = f"synthetic-tch2-foreign-{token}"
    directory = Tch2(
        app=app,
        client=TestClient(app),
        organization_id=organization_id,
        foreign_organization_id=foreign_organization_id,
    )
    directory.classes = {
        key: f"synthetic-tch2-class-{key}-{token}"
        for key in ("a", "b", "archived", "unassigned", "foreign")
    }
    directory.children = {
        key: f"synthetic-tch2-child-{key}-{token}"
        for key in ("synthetic", "other", "pending", "legacy", "revoked")
    }
    with runtime.session_factory.begin() as db:
        db.add_all(
            [
                OrganizationModel(organization_id=organization_id, display_name=organization_id),
                OrganizationModel(
                    organization_id=foreign_organization_id,
                    display_name=foreign_organization_id,
                ),
            ]
        )
        db.flush()
        for key, organization, state in (
            ("a", organization_id, "active"),
            ("b", organization_id, "active"),
            ("archived", organization_id, "archived"),
            ("unassigned", organization_id, "active"),
            ("foreign", foreign_organization_id, "active"),
        ):
            db.add(
                ClassroomModel(
                    class_id=directory.classes[key],
                    organization_id=organization,
                    display_name=f"Synthetic {key}",
                    state=state,
                    created_by="synthetic-tch2-fixture",
                )
            )
        db.flush()
        _identity(
            db,
            directory,
            "teacher",
            "teacher",
            organization_id,
            ((directory.classes["a"], "teacher"), (directory.classes["b"], "teacher"),
             (directory.classes["archived"], "teacher")),
        )
        _identity(
            db,
            directory,
            "other_teacher",
            "teacher",
            organization_id,
            ((directory.classes["b"], "teacher"),),
        )
        _identity(
            db,
            directory,
            "orgwide",
            "teacher",
            organization_id,
            ((None, "teacher"),),
        )
        _identity(
            db,
            directory,
            "guide",
            "teacher",
            organization_id,
            ((directory.classes["a"], "guide"),),
        )
        _identity(
            db,
            directory,
            "observer",
            "teacher",
            organization_id,
            ((directory.classes["a"], "observer"),),
        )
        _identity(
            db,
            directory,
            "manager",
            "school_manager",
            organization_id,
            ((None, "school_admin"),),
        )
        _identity(
            db,
            directory,
            "foreign_teacher",
            "teacher",
            foreign_organization_id,
            ((directory.classes["foreign"], "teacher"),),
        )
        _identity(db, directory, "unassigned", "teacher", organization_id, ())
        db.flush()

        for key in ("a", "b"):
            session_id = f"synthetic-tch2-session-{key}-{token}"
            directory.sessions[key] = session_id
            db.add(
                ClassroomSessionModel(
                    session_id=session_id,
                    organization_id=organization_id,
                    class_id=directory.classes[key],
                    created_by=directory.subjects["teacher"],
                    state="finished",
                    revision=1,
                    configuration={},
                )
            )
        pending_child = directory.children["pending"]
        pending_consent = str(uuid4())
        pending_purpose = f"synthetic-tch2-purpose-{token}"
        revoked_child = directory.children["revoked"]
        revoked_consent = str(uuid4())
        revoked_purpose = f"synthetic-tch2-revoked-purpose-{token}"
        db.add_all(
            [
                ConsentRecordModel(
                    consent_id=pending_consent,
                    organization_id=organization_id,
                    class_id=directory.classes["a"],
                    child_id=pending_child,
                    purpose_ref=pending_purpose,
                    state="pending",
                    recorded_by=directory.subjects["manager"],
                ),
                ConsentRecordModel(
                    consent_id=revoked_consent,
                    organization_id=organization_id,
                    class_id=directory.classes["a"],
                    child_id=revoked_child,
                    purpose_ref=revoked_purpose,
                    state="revoked",
                    recorded_by=directory.subjects["manager"],
                ),
            ]
        )
        db.flush()
        for key, origin, consent_id, purpose_ref in (
            ("synthetic", "SYNTHETIC_DEV", None, None),
            ("other", "SYNTHETIC_DEV", None, None),
            ("pending", "REAL", pending_consent, pending_purpose),
            ("legacy", "LEGACY_UNCLASSIFIED", None, None),
            ("revoked", "REAL", revoked_consent, revoked_purpose),
        ):
            _add_profile(
                db,
                organization_id=organization_id,
                class_id=directory.classes["a"],
                child_id=directory.children[key],
                creator=directory.subjects["manager"],
                data_origin=origin,
                consent_id=consent_id,
                purpose_ref=purpose_ref,
            )
        _add_observation(
            db,
            organization_id=organization_id,
            session_id=directory.sessions["a"],
            child_id=directory.children["synthetic"],
            created_by=directory.subjects["teacher"],
            note="Synthetic class A note one",
            created_at=datetime(2026, 11, 1, tzinfo=UTC),
        )
        observation_two = _add_observation(
            db,
            organization_id=organization_id,
            session_id=directory.sessions["a"],
            child_id=directory.children["synthetic"],
            created_by=directory.subjects["teacher"],
            note="Synthetic class A note two",
            created_at=datetime(2026, 11, 2, tzinfo=UTC),
        )
        _add_observation(
            db,
            organization_id=organization_id,
            session_id=directory.sessions["b"],
            child_id=directory.children["synthetic"],
            created_by=directory.subjects["teacher"],
            note="Synthetic moved-child class B note",
            created_at=datetime(2026, 11, 3, tzinfo=UTC),
        )
        _add_observation(
            db,
            organization_id=organization_id,
            session_id=directory.sessions["a"],
            child_id=directory.children["other"],
            created_by=directory.subjects["teacher"],
            note="Synthetic other-child note",
            created_at=datetime(2026, 11, 4, tzinfo=UTC),
        )
        directory.children["latest_observation"] = observation_two

        directory.activities = {
            "own_private": _add_activity_lesson(
                db,
                organization_id=organization_id,
                creator=directory.subjects["teacher"],
                label="own-private",
                visibility="PRIVATE",
            ),
            "other_private": _add_activity_lesson(
                db,
                organization_id=organization_id,
                creator=directory.subjects["other_teacher"],
                label="other-private",
                visibility="PRIVATE",
            ),
            "school": _add_activity_lesson(
                db,
                organization_id=organization_id,
                creator=directory.subjects["other_teacher"],
                label="school",
                visibility="SCHOOL",
            ),
            "hidden": _add_activity_lesson(
                db,
                organization_id=organization_id,
                creator=directory.subjects["teacher"],
                label="hidden",
                moderation="HIDDEN",
            ),
            "archived": _add_activity_lesson(
                db,
                organization_id=organization_id,
                creator=directory.subjects["teacher"],
                label="archived",
                state="ARCHIVED",
            ),
            "unapproved": _add_activity_lesson(
                db,
                organization_id=organization_id,
                creator=directory.subjects["teacher"],
                label="unapproved",
                review_state="DRAFT",
            ),
            "foreign": _add_activity_lesson(
                db,
                organization_id=foreign_organization_id,
                creator=directory.subjects["foreign_teacher"],
                label="foreign-org",
            ),
        }
        base_time = datetime(2026, 11, 1, tzinfo=UTC)
        directory.occurrences = {
            "a": _add_occurrence(
                db,
                organization_id=organization_id,
                class_id=directory.classes["a"],
                teacher_account=directory.accounts["teacher"],
                title="Synthetic class A occurrence",
                created_at=base_time,
            ),
            "b": _add_occurrence(
                db,
                organization_id=organization_id,
                class_id=directory.classes["b"],
                teacher_account=directory.accounts["teacher"],
                title="Synthetic class B occurrence",
                created_at=datetime(2026, 11, 2, tzinfo=UTC),
            ),
            "archived": _add_occurrence(
                db,
                organization_id=organization_id,
                class_id=directory.classes["archived"],
                teacher_account=directory.accounts["teacher"],
                title="Synthetic archived class occurrence",
                created_at=datetime(2026, 11, 3, tzinfo=UTC),
            ),
            "unassigned": _add_occurrence(
                db,
                organization_id=organization_id,
                class_id=directory.classes["unassigned"],
                teacher_account=directory.accounts["teacher"],
                title="Synthetic unassigned class occurrence",
                created_at=datetime(2026, 11, 4, tzinfo=UTC),
            ),
        }

    provider = _FakeIdentityProvider(directory.subjects)
    app.state.identity_account_provisioner = provider
    app.state.lesson_library_storage = SimpleNamespace()
    app.state.lesson_document_parser = SimpleNamespace()
    app.state.lesson_document_scanner = SimpleNamespace()

    async def verified_actor(request: Request) -> VerifiedPrincipal:
        return directory.principals[request.headers[ACTOR_HEADER]]

    app.dependency_overrides[get_verified_adult] = verified_actor
    directory.provider = provider
    try:
        with directory.client:
            yield directory
    finally:
        app.dependency_overrides.clear()
        runtime.engine.dispose()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def test_portfolio_only_returns_current_class_observations_and_pages(tch2: Tch2) -> None:
    path = tch2.portfolio()
    first = tch2.get("teacher", f"{path}?limit=1")
    assert first.status_code == 200, first.text
    first_body = first.json()
    assert first_body["contract"] == "Be1PortfolioPageV1"
    assert first_body["child_id"] == tch2.children["synthetic"]
    assert first.headers["cache-control"] == "private, no-store"
    assert len(first_body["items"]) == 1
    assert first_body["items"][0]["observation_id"] == tch2.children["latest_observation"]
    assert set(first_body["items"][0]) == {
        "observation_id",
        "session_id",
        "kind",
        "content",
        "created_at",
    }
    assert "created_by" not in first.text and "source_refs" not in first.text
    assert "synthetic-private-source-ref" not in first.text
    assert "Synthetic class B note" not in first.text
    assert "Synthetic other-child note" not in first.text
    assert "display_name" not in first_body
    cursor = first_body["next_cursor"]
    assert isinstance(cursor, str) and cursor

    second = tch2.get("teacher", f"{path}?limit=1&cursor={cursor}")
    assert second.status_code == 200, second.text
    assert len(second.json()["items"]) == 1
    assert second.json()["items"][0]["observation_id"] != first_body["items"][0]["observation_id"]
    other_child = tch2.get(
        "teacher",
        f"{tch2.portfolio('other')}?limit=1&cursor={cursor}",
    )
    assert other_child.status_code == 400
    assert other_child.json()["code"] == "INVALID_REQUEST"


def test_portfolio_consent_and_withdrawal_decisions_are_audited_correctly(tch2: Tch2) -> None:
    for child_key in ("pending", "legacy"):
        response = tch2.get("teacher", tch2.portfolio(child_key))
        assert response.status_code == 409
        assert response.json()["code"] == "CONSENT_NOT_EFFECTIVE"
        with tch2.factory() as db:
            audit_rows = db.scalars(
                select(CoreAuditEntryModel).where(
                    CoreAuditEntryModel.organization_id == tch2.organization_id,
                    CoreAuditEntryModel.resource_id == tch2.children[child_key],
                    CoreAuditEntryModel.action == "portfolio.read",
                )
            ).all()
        assert len(audit_rows) == 1
        assert audit_rows[0].decision == "denied_consent_pending"

    revoked = tch2.get("teacher", tch2.portfolio("revoked"))
    assert revoked.status_code == 404
    assert revoked.json()["code"] == "RESOURCE_NOT_FOUND"
    with tch2.factory() as db:
        revoked_audits = db.scalars(
            select(CoreAuditEntryModel).where(
                CoreAuditEntryModel.resource_id == tch2.children["revoked"],
                CoreAuditEntryModel.action == "portfolio.read",
            )
        ).all()
    assert revoked_audits == []

    for actor in ("manager", "orgwide"):
        forbidden = tch2.get(actor, tch2.portfolio())
        assert forbidden.status_code == 403
        assert forbidden.json()["code"] == "ACTION_NOT_ALLOWED"
    outside_scope = tch2.get(
        "foreign_teacher",
        f"/api/be1/v1/organizations/{tch2.organization_id}/classes/"
        f"{tch2.classes['a']}/profiles/{tch2.children['synthetic']}/portfolio",
    )
    assert outside_scope.status_code == 404
    assert outside_scope.json()["code"] == "RESOURCE_NOT_FOUND"


def test_activity_list_enforces_version_visibility_and_pages(tch2: Tch2) -> None:
    path = f"/api/lesson-library/v1/organizations/{tch2.organization_id}/activities"
    first = tch2.get("teacher", f"{path}?limit=1")
    assert first.status_code == 200, first.text
    assert first.json()["contract"] == "TeacherActivityPageV1"
    assert first.headers["cache-control"] == "private, no-cache"
    item = first.json()["items"][0]
    assert item["lesson_title"].startswith("Synthetic lesson ")
    assert item["lesson_activity_id"]
    assert "created_by" not in item
    page_ids = {item["lesson_id"]}
    next_cursor = first.json()["next_cursor"]
    assert next_cursor
    second = tch2.get("teacher", f"{path}?limit=1&cursor={next_cursor}")
    assert second.status_code == 200, second.text
    page_ids.update(row["lesson_id"] for row in second.json()["items"])
    assert page_ids == {
        tch2.activities["own_private"]["lesson_id"],
        tch2.activities["school"]["lesson_id"],
    }

    manager = tch2.get("manager", path)
    assert manager.status_code == 200, manager.text
    manager_ids = {row["lesson_id"] for row in manager.json()["items"]}
    assert manager_ids == {
        tch2.activities[key]["lesson_id"] for key in ("own_private", "other_private", "school")
    }
    foreign = tch2.get(
        "teacher",
        f"/api/lesson-library/v1/organizations/{tch2.foreign_organization_id}/activities",
    )
    assert foreign.status_code == 404


def test_teacher_history_merges_only_current_readable_classes(tch2: Tch2) -> None:
    path = f"/api/teacher/v1/organizations/{tch2.organization_id}/history?state=DRAFT&limit=1"
    first = tch2.get("teacher", path)
    assert first.status_code == 200, first.text
    assert first.json()["contract"] == "LessonOccurrencePageV1"
    assert first.headers["cache-control"] == "private, no-cache"
    first_item = first.json()["items"][0]
    assert first_item["occurrence_id"] == tch2.occurrences["b"]
    cursor = first.json()["next_cursor"]
    assert cursor
    second = tch2.get(
        "teacher",
        f"/api/teacher/v1/organizations/{tch2.organization_id}/history"
        f"?state=DRAFT&limit=1&cursor={cursor}",
    )
    assert second.status_code == 200, second.text
    ids = {first_item["occurrence_id"], *(row["occurrence_id"] for row in second.json()["items"])}
    assert ids == {tch2.occurrences["a"], tch2.occurrences["b"]}

    orgwide = tch2.get(
        "orgwide", f"/api/teacher/v1/organizations/{tch2.organization_id}/history"
    )
    assert orgwide.status_code == 200, orgwide.text
    orgwide_ids = {row["occurrence_id"] for row in orgwide.json()["items"]}
    assert orgwide_ids == {
        tch2.occurrences[key] for key in ("a", "b", "unassigned")
    }
    for actor in ("guide", "observer"):
        scoped = tch2.get(
            actor, f"/api/teacher/v1/organizations/{tch2.organization_id}/history"
        )
        assert scoped.status_code == 200
        assert {row["occurrence_id"] for row in scoped.json()["items"]} == {
            tch2.occurrences["a"]
        }
    other_organization = tch2.get(
        "teacher",
        f"/api/teacher/v1/organizations/{tch2.foreign_organization_id}/history",
    )
    assert other_organization.status_code == 404


def test_teacher_profile_read_returns_identity_provider_fields(tch2: Tch2) -> None:
    profile = tch2.get("teacher", "/api/teacher/v1/me/profile")
    assert profile.status_code == 200, profile.text
    assert profile.json()["account_ref"] == tch2.accounts["teacher"]
    assert profile.json()["email"].endswith("@example.test")
