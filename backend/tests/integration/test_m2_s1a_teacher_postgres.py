"""Owner-launcher-only PostgreSQL acceptance for S1a-T (R7)."""

from __future__ import annotations

import os
import re
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    ClassroomModel,
    OrganizationAssignmentModel,
    OrganizationModel,
)
from sketch2life.interfaces.http.app import create_app


def _error_core(response) -> dict[str, str]:
    """Error envelope without the per-request ``request_id`` field."""
    body = response.json()
    return {"code": body["code"], "message": body["message"]}


@pytest.fixture
def s1a_t_client(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> Iterator[SimpleNamespace]:
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    database_url = os.environ.get("S1A_T_TEST_DATABASE_URL")
    run_id = os.environ.get("S1A_T_RUN_ID")
    if not database_url or not run_id or not re.fullmatch(r"[0-9a-f]{32}", run_id):
        pytest.fail("owner launcher database target or run marker is missing")
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", database_url)
    monkeypatch.setenv("SKETCH2LIFE_BE1_ARTIFACT_ROOT", str(tmp_path))
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("SKETCH2LIFE_AUTH_PROVIDER", "development")
    monkeypatch.setenv("SKETCH2LIFE_SYNTHETIC_PILOT_ENABLED", "true")
    monkeypatch.setenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", "0")
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()

    app = create_app()
    runtime = app.state.be1_runtime
    if runtime.engine is None or runtime.session_factory is None:
        if runtime.engine is not None:
            runtime.engine.dispose()
        pytest.fail("the S1a-T runtime did not initialize")
    try:
        with runtime.engine.connect() as connection:
            identity = connection.execute(
                text(
                    "SELECT current_database(), current_user, inet_server_port(), "
                    "host(inet_server_addr()), current_setting('server_version_num')"
                )
            ).one()
    except Exception:
        runtime.engine.dispose()
        pytest.fail("the application engine identity check did not complete")
    if (
        identity[0] != "sketch2life_m2_s1a"
        or identity[1] != "postgres"
        or identity[2] != 5433
        or identity[3] not in {"127.0.0.1", "::1"}
        or not str(identity[4]).startswith("17")
    ):
        runtime.engine.dispose()
        pytest.fail("the application engine did not match the approved S1a-T target")

    organization_id = f"synthetic-s1at-{run_id}-org-target"
    foreign_organization_id = f"synthetic-s1at-{run_id}-org-foreign"
    manager_subject = f"synthetic-s1at-{run_id}-teacher-admin"
    teacher_a = f"synthetic-s1at-{run_id}-teacher-race-a"
    teacher_b = f"synthetic-s1at-{run_id}-teacher-race-b"
    teacher_orgwide = f"synthetic-s1at-{run_id}-teacher-orgwide"
    teacher_other_class = f"synthetic-s1at-{run_id}-teacher-other-class"
    teacher_other_org = f"synthetic-s1at-{run_id}-teacher-other-org"
    target_class_id = f"synthetic-s1at-{run_id}-class-{uuid4().hex[:8]}"
    other_class_id = f"synthetic-s1at-{run_id}-class-{uuid4().hex[:8]}"
    foreign_class_id = f"synthetic-s1at-{run_id}-class-{uuid4().hex[:8]}"
    issuer = "synthetic-s1at-test-issuer"
    subjects = (
        manager_subject,
        teacher_a,
        teacher_b,
        teacher_orgwide,
        teacher_other_class,
        teacher_other_org,
    )
    principals = {
        subject: VerifiedPrincipal(
            subject=subject,
            issuer=issuer,
            roles=frozenset(),
            token_id=f"synthetic-s1at-token-{index}",
        )
        for index, subject in enumerate(subjects)
    }
    tokens = {subject: f"s1at-{index}" for index, subject in enumerate(subjects)}
    principal_by_token = {
        token: principals[subject] for subject, token in tokens.items()
    }

    class _Verifier:
        async def verify(self, token: str) -> VerifiedPrincipal:
            principal = principal_by_token.get(token)
            if principal is None:
                raise ValueError("unrecognized synthetic bearer token")
            return principal

    runtime.identity_verifier = _Verifier()  # type: ignore[assignment]
    with runtime.session_factory.begin() as db:
        db.add_all(
            [
                OrganizationModel(
                    organization_id=organization_id,
                    display_name=f"Synthetic S1AT {run_id} organization",
                    state="active",
                ),
                OrganizationModel(
                    organization_id=foreign_organization_id,
                    display_name=f"Synthetic S1AT {run_id} foreign organization",
                    state="active",
                ),
            ]
        )
        db.flush()
        db.add_all(
            [
                ClassroomModel(
                    class_id=target_class_id,
                    organization_id=organization_id,
                    display_name=f"Synthetic S1AT {run_id} target class",
                    state="active",
                    created_by=manager_subject,
                ),
                ClassroomModel(
                    class_id=other_class_id,
                    organization_id=organization_id,
                    display_name=f"Synthetic S1AT {run_id} other class",
                    state="active",
                    created_by=manager_subject,
                ),
                ClassroomModel(
                    class_id=foreign_class_id,
                    organization_id=foreign_organization_id,
                    display_name=f"Synthetic S1AT {run_id} foreign class",
                    state="active",
                    created_by=manager_subject,
                ),
            ]
        )
        db.flush()
        db.add_all(
            [
                AdultIdentityModel(subject=subject, issuer=issuer, state="active")
                for subject in subjects
            ]
        )
        db.flush()
        db.add_all(
            [
                OrganizationAssignmentModel(
                    assignment_id=str(uuid4()),
                    organization_id=organization_id,
                    subject=manager_subject,
                    class_id=None,
                    role="school_admin",
                    active=True,
                ),
                OrganizationAssignmentModel(
                    assignment_id=str(uuid4()),
                    organization_id=organization_id,
                    subject=teacher_orgwide,
                    class_id=None,
                    role="teacher",
                    active=True,
                ),
                OrganizationAssignmentModel(
                    assignment_id=str(uuid4()),
                    organization_id=organization_id,
                    subject=teacher_other_class,
                    class_id=other_class_id,
                    role="teacher",
                    active=True,
                ),
                OrganizationAssignmentModel(
                    assignment_id=str(uuid4()),
                    organization_id=foreign_organization_id,
                    subject=teacher_other_org,
                    class_id=foreign_class_id,
                    role="teacher",
                    active=True,
                ),
            ]
        )

    with TestClient(app) as client:
        yield SimpleNamespace(
            app=app,
            client=client,
            organization_id=organization_id,
            target_class_id=target_class_id,
            run_id=run_id,
            manager_subject=manager_subject,
            teacher_a=teacher_a,
            teacher_b=teacher_b,
            teacher_orgwide=teacher_orgwide,
            teacher_other_class=teacher_other_class,
            teacher_other_org=teacher_other_org,
            tokens=tokens,
            runtime=runtime,
        )
    runtime.engine.dispose()
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()


def test_teacher_postgres_contract_and_marker_accounting(s1a_t_client: SimpleNamespace) -> None:
    accepted = s1a_t_client
    client = accepted.client
    organization_id = accepted.organization_id
    class_id = accepted.target_class_id
    run_id = accepted.run_id

    def headers(subject: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {accepted.tokens[subject]}"}

    barrier = Barrier(2)

    def assign_teacher(subject: str):
        barrier.wait(timeout=15)
        return client.post(
            f"/api/be1/v1/classes/{class_id}/assignments",
            headers=headers(accepted.manager_subject),
            json={"subject": subject},
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(assign_teacher, accepted.teacher_a),
            executor.submit(assign_teacher, accepted.teacher_b),
        ]
        race_responses = [future.result(timeout=45) for future in futures]

    created = [response for response in race_responses if response.status_code == 201]
    conflicts = [response for response in race_responses if response.status_code == 409]
    assert len(created) == 1
    assert len(conflicts) == 1
    assert created[0].json()["role"] == "teacher"
    assert created[0].json()["class_id"] == class_id
    assert _error_core(conflicts[0]) == {
        "code": "CLASS_TEACHER_EXISTS",
        "message": "Class already has an active Teacher",
    }
    assert accepted.teacher_a not in conflicts[0].text
    assert accepted.teacher_b not in conflicts[0].text
    winning_subject = created[0].json()["subject"]
    assert winning_subject in {accepted.teacher_a, accepted.teacher_b}
    with accepted.runtime.engine.connect() as connection:
        active_teachers = connection.execute(
            text(
                "SELECT subject FROM be1_organization_assignments "
                "WHERE organization_id = :organization_id AND class_id = :class_id "
                "AND role = 'teacher' AND active IS TRUE"
            ),
            {"organization_id": organization_id, "class_id": class_id},
        ).scalars().all()
    assert active_teachers == [winning_subject]

    def profile_request(subject: str, age_months: int, suffix: str):
        return client.post(
            f"/api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles",
            headers=headers(subject),
            json={
                "class_id": class_id,
                "display_name": f"Synthetic S1AT {run_id} {suffix}",
                "age_months": age_months,
            },
        )

    denied_profiles = [
        profile_request(accepted.manager_subject, 60, "school-admin-denied"),
        profile_request(accepted.teacher_orgwide, 60, "orgwide-teacher-denied"),
        profile_request(accepted.teacher_other_class, 60, "other-class-teacher-denied"),
        profile_request(accepted.teacher_other_org, 60, "other-org-teacher-denied"),
    ]
    for response in denied_profiles:
        assert response.status_code == 403
        assert _error_core(response) == {
            "code": "SCOPE_DENIED",
            "message": "Access to this resource is not permitted",
        }
    first_denial = _error_core(denied_profiles[0])
    assert all(_error_core(response) == first_denial for response in denied_profiles)

    too_young = profile_request(winning_subject, 35, "age-35-rejected")
    too_old = profile_request(winning_subject, 121, "age-121-rejected")
    assert too_young.status_code == 422
    assert too_old.status_code == 422

    created_profiles = []
    for age_months in (36, 120):
        response = profile_request(winning_subject, age_months, f"age-{age_months}")
        assert response.status_code == 201, response.text
        profile = response.json()
        assert re.fullmatch(r"synthetic-[0-9a-f]{24}", profile["child_id"])
        assert profile["class_id"] == class_id
        assert profile["age_months"] == age_months
        assert profile["data_origin"] == "SYNTHETIC_DEV"
        assert "consent_state" not in profile
        created_profiles.append((profile, f"Synthetic S1AT {run_id} age-{age_months}"))

    for profile, display_name in created_profiles:
        with accepted.runtime.engine.connect() as connection:
            persisted = connection.execute(
                text(
                    "SELECT data_origin, consent_id, consent_purpose_ref, age_source, age_months "
                    "FROM be1_managed_profiles WHERE child_id = :child_id "
                    "AND organization_id = :organization_id AND class_id = :class_id"
                ),
                {
                    "child_id": profile["child_id"],
                    "organization_id": organization_id,
                    "class_id": class_id,
                },
            ).one()
        assert persisted == (
            "SYNTHETIC_DEV",
            None,
            None,
            "SYNTHETIC_FIXTURE",
            profile["age_months"],
        )
        portfolio = client.get(
            f"/api/be1/v1/organizations/{organization_id}/classes/{class_id}/"
            f"profiles/{profile['child_id']}/portfolio",
            headers=headers(winning_subject),
        )
        assert portfolio.status_code == 409
        assert portfolio.json()["code"] == "CONSENT_NOT_EFFECTIVE"
        assert "PROFILE_NOT_FOUND" not in portfolio.text
        assert profile["child_id"] not in portfolio.text
        assert display_name not in portfolio.text
