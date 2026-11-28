"""PostgreSQL checks for Sketch Deck revision immutability and plan completeness.

Run only with ``BE1_TEST_DATABASE_URL`` pointing to a disposable database whose name contains
both ``frc08`` and ``be1_acceptance``. The test creates only synthetic teacher, class, occurrence
and plan data. It does not call a provider.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest
from fastapi import Header
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.infrastructure.lesson_occurrences.sketch_deck_tables import (
    SKETCH_DECK_REVISIONS,
)
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    ClassroomModel,
    OrganizationAssignmentModel,
    OrganizationModel,
)
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult

_ISSUER = "synthetic-sketch-deck-issuer"


@pytest.fixture
def deck_api(monkeypatch: pytest.MonkeyPatch) -> Iterator[dict[str, Any]]:
    database_url = os.environ.get("BE1_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("set BE1_TEST_DATABASE_URL to a disposable PostgreSQL database")
    database_name = database_url.rsplit("/", 1)[-1]
    if "be1_acceptance" not in database_name or "frc08" not in database_name:
        pytest.fail("BE1_TEST_DATABASE_URL must point to a disposable frc08*be1_acceptance db")
    parsed_url = make_url(database_url)
    if parsed_url.database in {"sketch2life", "sketch2life_m2_s1a"} or (
        parsed_url.port or 5432
    ) in {
        5432,
        5433,
        8000,
        55439,
    }:
        pytest.fail("BE1_TEST_DATABASE_URL points to a database or port excluded for this job")

    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", database_url)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("SKETCH2LIFE_AUTH_PROVIDER", "development")
    monkeypatch.setenv("SKETCH2LIFE_AI_PROVIDER", "disabled")
    monkeypatch.setenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", "0")
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()

    application = create_app()
    runtime = application.state.be1_runtime
    if runtime.engine is None or runtime.session_factory is None:
        pytest.fail("PostgreSQL runtime did not initialize")
    token = uuid4().hex
    organization_id = f"synthetic-sketch-deck-org-{token}"
    class_id = f"synthetic-sketch-deck-class-{token}"
    subject = f"synthetic-sketch-deck-teacher-{token}"
    with runtime.session_factory.begin() as db:
        db.add(
            OrganizationModel(
                organization_id=organization_id,
                display_name=organization_id,
                state="active",
            )
        )
        db.flush()
        db.add(
            ClassroomModel(
                class_id=class_id,
                organization_id=organization_id,
                display_name=class_id,
                state="active",
                created_by="synthetic-sketch-deck-test",
            )
        )
        identity = AdultIdentityModel(
            subject=subject,
            issuer=_ISSUER,
            state="active",
            account_role="teacher",
        )
        db.add(identity)
        db.flush()
        db.add(
            OrganizationAssignmentModel(
                assignment_id=str(uuid4()),
                organization_id=organization_id,
                subject=subject,
                class_id=class_id,
                role="teacher",
                active=True,
            )
        )
        account_id = identity.account_id

    async def verified(
        x_test_principal: str = Header(alias="X-Test-Principal"),
    ) -> VerifiedPrincipal:
        return VerifiedPrincipal(subject=x_test_principal, issuer=_ISSUER, roles=frozenset())

    application.dependency_overrides[get_verified_adult] = verified
    try:
        with TestClient(application) as client:
            yield {
                "app": application,
                "client": client,
                "runtime": runtime,
                "subject": subject,
                "class_id": class_id,
                "account_id": account_id,
            }
    finally:
        application.dependency_overrides.clear()
        runtime.engine.dispose()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def test_revision_inputs_are_immutable_and_get_returns_them(
    deck_api: dict[str, Any],
) -> None:
    client: TestClient = deck_api["client"]
    headers = {
        "X-Test-Principal": deck_api["subject"],
        "Idempotency-Key": uuid4().hex,
    }
    created = client.post(
        "/v1/lesson-occurrences",
        headers=headers,
        json={"class_id": deck_api["class_id"], "title": "Synthetic drawing lesson"},
    )
    assert created.status_code == 201, created.text
    occurrence_id = created.json()["occurrence_id"]
    plan_response = client.post(
        f"/v1/lesson-occurrences/{occurrence_id}/plan-revisions",
        headers={**headers, "Idempotency-Key": uuid4().hex},
        json={
            "expected_head_revision_no": 0,
            "objectives": ["Recognize a circle"],
            "teacher_direction": "Use a simple shape activity.",
        },
    )
    assert plan_response.status_code == 201, plan_response.text
    plan = plan_response.json()
    confirm_path = (
        f"/v1/lesson-occurrences/{occurrence_id}/plan-revisions/"
        f"{plan['revision_no']}/confirm"
    )
    confirmed = client.post(
        confirm_path,
        headers={**headers, "Idempotency-Key": uuid4().hex},
        json={"expected_plan_hash": plan["content_hash"]},
    )
    assert confirmed.status_code == 200, confirmed.text
    confirmed_plan = confirmed.json()
    assert confirmed_plan["plan_revision_id"] == plan["plan_revision_id"]

    incomplete = client.post(
        f"/v1/lesson-occurrences/{occurrence_id}/sketch-decks",
        headers={**headers, "Idempotency-Key": uuid4().hex},
        json={
            "expected_plan_revision_id": confirmed_plan["plan_revision_id"],
            "expected_plan_hash": confirmed_plan["content_hash"],
            "review_confirmed": True,
            "topic": "Tree",
            "drawing_steps": [
                {"action": f"Draw part {index}", "placement": f"Place part {index}"}
                for index in range(1, 5)
            ],
            "subject_knowledge": ["Trees have trunks and leaves."],
        },
    )
    assert incomplete.status_code == 409, incomplete.text
    assert incomplete.json()["code"] == "SKETCH_DECK_PLAN_INCOMPLETE"

    with deck_api["runtime"].session_factory() as db:
        assert db.scalar(
            select(SKETCH_DECK_REVISIONS.c.sketch_deck_revision_id).where(
                SKETCH_DECK_REVISIONS.c.occurrence_id == occurrence_id
            )
        ) is None

    revision_id = str(uuid4())
    with deck_api["runtime"].session_factory.begin() as db:
        db.execute(
            SKETCH_DECK_REVISIONS.insert().values(
                sketch_deck_revision_id=revision_id,
                occurrence_id=occurrence_id,
                plan_revision_id=confirmed_plan["plan_revision_id"],
                revision_no=1,
                plan_content_hash=confirmed_plan["content_hash"],
                review_confirmed=True,
                topic="Tree",
                drawing_steps=[
                    {"action": f"Draw part {index}", "placement": f"Place part {index}"}
                    for index in range(1, 5)
                ],
                subject_knowledge=["Trees have trunks and leaves."],
                target_age_band="age-36-71-months-v1",
                deck_schema_version="sketch2life.teacher-sketch-deck.v1",
                state="GENERATING",
                model_profile_ref="synthetic-model",
                model_profile_version="synthetic-revision",
                prompt_template_version="NOT_VERIFIED",
                config_hash="a" * 64,
                compute_reservation_ref=None,
                content_hash=None,
                created_by=deck_api["account_id"],
                created_at=datetime.now(UTC),
                ready_at=None,
                superseded_at=None,
            )
        )

    with deck_api["runtime"].session_factory() as db:
        with pytest.raises(DBAPIError):
            db.execute(
                SKETCH_DECK_REVISIONS.update()
                .where(SKETCH_DECK_REVISIONS.c.sketch_deck_revision_id == revision_id)
                .values(topic="mutated-content")
            )
        db.rollback()

    with deck_api["runtime"].session_factory.begin() as db:
        db.execute(
            SKETCH_DECK_REVISIONS.update()
            .where(SKETCH_DECK_REVISIONS.c.sketch_deck_revision_id == revision_id)
            .values(state="FAILED")
        )
        state = db.scalar(
            select(SKETCH_DECK_REVISIONS.c.state).where(
                SKETCH_DECK_REVISIONS.c.sketch_deck_revision_id == revision_id
            )
        )
    assert state == "FAILED"

    fetched = client.get(
        f"/v1/lesson-occurrences/{occurrence_id}/sketch-decks",
        headers={"X-Test-Principal": deck_api["subject"]},
    )
    assert fetched.status_code == 200, fetched.text
    current = fetched.json()["current_revision"]
    assert current["review_confirmed"] is True
    assert current["topic"] == "Tree"
    assert current["drawing_steps"] == [
        {"action": f"Draw part {index}", "placement": f"Place part {index}"}
        for index in range(1, 5)
    ]
    assert current["subject_knowledge"] == ["Trees have trunks and leaves."]
