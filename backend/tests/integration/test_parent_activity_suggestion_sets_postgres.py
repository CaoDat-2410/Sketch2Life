"""PostgreSQL coverage for immutable activity sets and the Phase A AI_DRAFT selection row.

This test requires the disposable BE1 acceptance database to have the current Alembic head
applied. It is intentionally not part of the database-free test commands.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Iterator, Sequence
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest
from fastapi import Header
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, update
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_activity_catalog import (
    ParentActivityCatalogPort,
    ParentActivityLesson,
)
from sketch2life.application.ports.parent_story_runs import ParentStoryRunError
from sketch2life.application.services.parent_activity_selection import (
    ParentActivitySelectionService,
)
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel
from sketch2life.infrastructure.persistence.parent_activity_suggestion_set_repository import (
    SqlParentActivitySuggestionSetRepository,
)
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
)
from sketch2life.infrastructure.persistence.story_lifecycle_store import SqlStoryLifecycleStore
from sketch2life.infrastructure.story_run_lite import tables as story_tables
from sketch2life.infrastructure.uploads.resolvers import parent_scope_ref
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult

_ISSUER = "synthetic-activity-set-issuer"
_RUN_ID = ""
_CONTEXT_HASH = "c" * 64


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_hash(value: Any) -> str:
    return _sha(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    )


class _EmptyCatalog(ParentActivityCatalogPort):
    def list_accessible_lessons(
        self, *, parent_principal_ref: str
    ) -> Sequence[ParentActivityLesson]:
        del parent_principal_ref
        return ()


def _draft(title: str) -> dict[str, Any]:
    return {
        "title": title,
        "objective": "The child observes a shape and describes one detail.",
        "materials_text": "Paper and colored pencils.",
        "preparation_text": "An adult prepares a clear outdoor space.",
        "instructions_text": (
            "Outside in the garden, the child chooses a safe place to observe and compare "
            "shapes, while an adult stays nearby to support."
        ),
        "observation_notes": "Record which detail the child chooses to describe.",
        "safety_notes": "Stay with an adult and use the clear path.",
        "activity_kind": "outdoor",
        "source": "AI_GENERATED_DRAFT",
        "source_lesson_id": None,
        "source_lesson_title": None,
        "source_lesson_version_id": None,
        "source_content_sha256": None,
        "source_activity_index": None,
        "match_reason": None,
    }


@pytest.fixture
def database_engine() -> Iterator[Engine]:
    database_url = os.environ.get("BE1_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("set BE1_TEST_DATABASE_URL to a disposable PostgreSQL database")
    database_name = database_url.rsplit("/", 1)[-1]
    if "be1_acceptance" not in database_name or "frc08_v4_t2ea" not in database_name:
        pytest.fail("BE1_TEST_DATABASE_URL must be a disposable frc08_v4_t2ea*be1_acceptance db")
    engine = create_engine(database_url, poolclass=NullPool)
    try:
        yield engine
    finally:
        engine.dispose()


def test_suggestion_set_is_immutable_and_ai_draft_uses_the_phase_a_selection_table(
    database_engine: Engine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_id = str(uuid4())
    parent_subject = f"synthetic-activity-set-parent-{uuid4().hex[:10]}"
    principal = VerifiedPrincipal(parent_subject, _ISSUER, frozenset())
    scope_ref = parent_scope_ref(principal)
    profile_revision_ref = str(uuid4())
    run_input_one, run_input_two = str(uuid4()), str(uuid4())
    now = datetime.now(UTC)
    topic_context = {
        "schema_version": "sketch2life.parent-context.v1",
        "profile_revision_ref": profile_revision_ref,
        "age_months": 84,
        "interests_summary": "",
        "topic": "shapes",
        "adult_confirmed_idea": "",
    }
    candidate = {
        "candidate_subject": "shapes",
        "visible_features": ["round outline", "small marks"],
        "confidence": 0.9,
        "adult_confirmation_required": True,
        "decision": "REVIEW_REQUIRED",
    }

    with Session(database_engine) as db:
        with db.begin():
            db.add(
                AdultIdentityModel(
                    subject=parent_subject,
                    issuer=_ISSUER,
                    state="active",
                    account_role="parent",
                )
            )
            db.flush()
            account_id = db.scalar(
                select(AdultIdentityModel.account_id).where(
                    AdultIdentityModel.subject == parent_subject
                )
            )
            db.execute(
                story_tables.story_runs.insert().values(
                    run_id=run_id,
                    actor_scope_kind="PARENT_ACCOUNT",
                    actor_scope_ref=scope_ref,
                    profile_ref=str(uuid4()),
                    run_state="SUBJECT_REVIEW",
                    job_state="SUCCEEDED",
                    retryable=False,
                    revision=5,
                    version=5,
                    current_input_revision=2,
                    understanding_revision=1,
                    subject_label="shapes",
                    confidence=0.9,
                    active_owner_parent_account_id=str(account_id),
                    created_at=now,
                    updated_at=now,
                )
            )
            common_input = {
                "run_id": run_id,
                "typed_idea": None,
                "idea_source": None,
                "source_profile_revision_ref": profile_revision_ref,
                "context_revision": 1,
                "context_snapshot": topic_context,
                "context_snapshot_sha256": _CONTEXT_HASH,
                "context_confirmed_by": None,
                "context_confirmed_at": None,
                "created_at": now,
            }
            db.execute(
                story_tables.run_inputs.insert().values(
                    run_input_id=run_input_one,
                    input_revision=1,
                    **common_input,
                )
            )
            db.execute(
                story_tables.run_inputs.insert().values(
                    run_input_id=run_input_two,
                    input_revision=2,
                    original_asset_ref=f"parent/{run_id}/original",
                    original_asset_version=1,
                    original_sha256=_sha(f"original-{run_id}".encode()),
                    original_media_type="image/png",
                    original_size_bytes=100,
                    derived_asset_ref=f"parent/{run_id}/normalized.png",
                    derived_asset_version=1,
                    derived_sha256=_sha(f"derived-{run_id}".encode()),
                    derived_media_type="image/png",
                    derived_size_bytes=90,
                    **common_input,
                )
            )
            db.execute(
                story_tables.understanding_revisions.insert().values(
                    understanding_revision_id=str(uuid4()),
                    run_id=run_id,
                    run_input_id=run_input_two,
                    revision_no=1,
                    subject_label="shapes",
                    confidence=0.9,
                    canonical_result_sha256="d" * 64,
                    result_snapshot={"result": candidate},
                    created_at=now,
                )
            )

        phase_a = SqlParentStoryRunRepository(db)
        phase_a.confirm_subject(
            principal=principal,
            run_id=run_id,
            expected_understanding_revision=1,
            confirmed_subject="shapes",
            idempotency_key="confirm-subject",
        )
        repository = SqlParentActivitySuggestionSetRepository(db)
        reservation = repository.reserve_activity_suggestion_set(
            principal=principal,
            run_id=run_id,
            expected_understanding_revision=1,
            idempotency_key="generate-set",
        )
        activities = [
            _draft("Observe a round shape"),
            _draft("Compare small marks"),
            _draft("Describe a curved line"),
        ]
        response = {
            "contract": "ParentActivitySuggestionSetV1",
            "request_id": str(uuid4()),
            "story_run_id": run_id,
            "suggestion_set_id": reservation.suggestion_set_id,
            "set_revision": reservation.set_revision,
            "understanding_revision": 1,
            "selection_mode": "AI_GENERATED_FALLBACK",
            "catalog_candidate_count": 0,
            "activities_snapshot_sha256": _canonical_hash(activities),
            "review_required": True,
            "modal_call_id": None,
            "activities": activities,
        }
        stored_response = repository.complete_activity_suggestion_set(
            principal=principal,
            reservation=reservation,
            response=response,
            provider_call_id=None,
        )
        replay = repository.reserve_activity_suggestion_set(
            principal=principal,
            run_id=run_id,
            expected_understanding_revision=1,
            idempotency_key="generate-set",
        )
        assert replay.replayed is True
        replay_body = dict(replay.replay_body or {})
        assert replay_body["activities"] == stored_response["activities"]
        assert replay_body["activities_snapshot_sha256"] == stored_response[
            "activities_snapshot_sha256"
        ]
        assert replay_body["suggestion_set_id"] == stored_response["suggestion_set_id"]
        assert "request_id" not in replay_body

        # Hardening: at most five suggestion sets per run; the sixth is a 409, while replays of
        # earlier sets keep working.
        for number in range(2, 6):
            extra = repository.reserve_activity_suggestion_set(
                principal=principal,
                run_id=run_id,
                expected_understanding_revision=1,
                idempotency_key=f"generate-set-{number}",
            )
            extra_activities = [
                _draft(f"Round {number} look closely"),
                _draft(f"Round {number} compare marks"),
                _draft(f"Round {number} describe lines"),
            ]
            repository.complete_activity_suggestion_set(
                principal=principal,
                reservation=extra,
                response={
                    **response,
                    "suggestion_set_id": extra.suggestion_set_id,
                    "set_revision": extra.set_revision,
                    "activities_snapshot_sha256": _canonical_hash(extra_activities),
                    "activities": extra_activities,
                },
                provider_call_id=None,
            )
        with pytest.raises(ParentStoryRunError) as sixth:
            repository.reserve_activity_suggestion_set(
                principal=principal,
                run_id=run_id,
                expected_understanding_revision=1,
                idempotency_key="generate-set-6",
            )
        assert sixth.value.status_code == 409 and sixth.value.code == "RESOURCE_CONFLICT"
        again = repository.reserve_activity_suggestion_set(
            principal=principal,
            run_id=run_id,
            expected_understanding_revision=1,
            idempotency_key="generate-set",
        )
        assert again.replayed is True

        service = ParentActivitySelectionService(
            phase_a,
            _EmptyCatalog(),
            suggestion_sets=repository,
        )
        selection = service.select_suggestion_set_activity(
            principal=principal,
            run_id=run_id,
            suggestion_set_id=reservation.suggestion_set_id,
            expected_understanding_revision=1,
            activity_index=1,
            idempotency_key="select-set-item",
        )
        assert selection.receipt_body["activity_index"] == 1

        stored_set = db.execute(
            select(story_tables.activity_suggestion_sets).where(
                story_tables.activity_suggestion_sets.c.suggestion_set_id
                == reservation.suggestion_set_id
            )
        ).mappings().one()
        selection_row = db.execute(
            select(story_tables.activity_selections).where(
                story_tables.activity_selections.c.run_id == run_id
            )
        ).mappings().one()
        assert stored_set["activities_snapshot_sha256"] == _canonical_hash(activities)
        assert selection_row["source_kind"] == "AI_DRAFT"
        assert selection_row["lesson_id"] is None
        assert selection_row["version_id"] is None
        assert selection_row["content_sha256"] is None
        assert selection_row["activity_index"] is None

    with pytest.raises(DBAPIError), Session(database_engine) as db, db.begin():
        db.execute(
            update(story_tables.activity_suggestion_sets)
            .where(
                story_tables.activity_suggestion_sets.c.suggestion_set_id
                == reservation.suggestion_set_id
            )
            .values(provider_call_id="forbidden-update")
        )

    monkeypatch.setenv(
        "SKETCH2LIFE_DATABASE_URL",
        database_engine.url.render_as_string(hide_password=False),
    )
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("SKETCH2LIFE_AUTH_PROVIDER", "development")
    monkeypatch.setenv("SKETCH2LIFE_AI_PROVIDER", "disabled")
    monkeypatch.delenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", raising=False)
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    app = create_app()
    runtime = app.state.be1_runtime
    if runtime.engine is None or runtime.session_factory is None:
        pytest.fail("PostgreSQL runtime did not initialize")

    async def verified(
        x_test_principal: str = Header(alias="X-Test-Principal"),
    ) -> VerifiedPrincipal:
        return VerifiedPrincipal(subject=x_test_principal, issuer=_ISSUER, roles=frozenset())

    app.dependency_overrides[get_verified_adult] = verified
    try:
        with TestClient(app) as client:
            response = client.get(
                f"/v1/story-runs/{run_id}",
                headers={"X-Test-Principal": parent_subject},
            )
            assert response.status_code == 200, response.text
            selected_activity = response.json()["story_run"]["main_activity"]["selected"]
            assert selected_activity["source"] == "AI_DRAFT"
            assert selected_activity["activity_ref"] is None
            assert selected_activity["title"] == "Compare small marks"
            run_revision = response.json()["story_run"]["run_revision"]
            cancel = client.post(
                f"/v1/story-runs/{run_id}/cancel",
                headers={"X-Test-Principal": parent_subject, "Idempotency-Key": "purge-set"},
                json={"expected_revision": run_revision},
            )
            assert cancel.status_code == 202, cancel.text

            lifecycle = SqlStoryLifecycleStore(sessionmaker(database_engine))
            purge_plan = lifecycle.plan_story_purge(run_id)
            assert f"activity_suggestion_sets:{reservation.suggestion_set_id}" in purge_plan.ids
            lifecycle.purge_story_content(purge_plan)
            assert lifecycle.plan_story_purge(run_id).ids == ()

            with Session(database_engine) as db:
                remaining_sets = db.execute(
                    select(story_tables.activity_suggestion_sets).where(
                        story_tables.activity_suggestion_sets.c.run_id == run_id
                    )
                ).all()
                receipts = db.execute(
                    select(story_tables.story_command_receipts.c.response_body).where(
                        story_tables.story_command_receipts.c.operation == "GENERATE_ACTIVITY_SET",
                        story_tables.story_command_receipts.c.resource_ref == run_id,
                    )
                ).scalars().all()
            assert remaining_sets == []
            assert receipts and all(item == {"purged": True} for item in receipts)

            replay_after_purge = client.post(
                f"/api/parent/v1/ai/story-runs/{run_id}/activity-suggestions",
                headers={
                    "X-Test-Principal": parent_subject,
                    "Idempotency-Key": "generate-set",
                },
                json={"expected_understanding_revision": 1},
            )
            assert replay_after_purge.status_code == 409
            assert replay_after_purge.json()["detail"]["code"] == "INVALID_STATE_TRANSITION"
            assert "activities" not in replay_after_purge.json()
    finally:
        app.dependency_overrides.clear()
        runtime.engine.dispose()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()
