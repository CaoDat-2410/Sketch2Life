"""FEAT-066 goal v4 T-2e-a: the Parent main activity and the implicit first story, on PostgreSQL.

SRS l.386, l.394, l.514, l.1412-1414, l.1667, l.1697-1699 (replay and ``STALE_REVISION``), l.864-865
(one 404 for a caller out of scope). Runs only against a disposable database whose name contains
``be1_acceptance`` and ``frc08_v4_t2ea``. The migration round trip needs
``T2EA_ROUNDTRIP_DATABASE_URL`` naming a ``frc08_v4_t2ea*roundtrip*be1_acceptance`` database.

The runs are seeded straight into the Story tables (a drawing, an understanding, a context), because
the upload and analysis steps have their own PostgreSQL tests. The Lesson Library catalog is a fake
that the test mutates (unpublish, revoke, displace); the Story side is the real repository, so the
locks, the receipts, the selection rows and the story start are the production code. No object
storage and no provider is used; the story generator is a deterministic double.
"""

from __future__ import annotations

import hashlib
import os
from collections.abc import Iterator, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from threading import Barrier
from typing import Any
from uuid import uuid4

import pytest
from alembic.config import Config
from fastapi import FastAPI, Header, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, text, update
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError
from sqlalchemy.pool import NullPool

from alembic import command
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_activity_catalog import (
    ParentActivityCatalogPort,
    ParentActivityLesson,
)
from sketch2life.application.ports.parent_story_inputs import (
    StoryGenerationFailure,
    StoryGenerationOutcomeUnknown,
    StoryGenerationResult,
)
from sketch2life.application.ports.parent_story_runs import ParentStoryRunError
from sketch2life.application.services.parent_activity_selection import (
    ParentActivitySelectionService,
)
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.lesson_library.service import LessonLibraryError
from sketch2life.infrastructure.persistence import story_first_start
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
    _sha256_json,
)
from sketch2life.infrastructure.persistence.story_lifecycle_store import (
    SqlStoryLifecycleStore,
    tombstone_fingerprint,
)
from sketch2life.infrastructure.story_run_lite import tables as story_tables
from sketch2life.infrastructure.uploads.resolvers import parent_scope_ref
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult
from sketch2life.interfaces.http.routers import parent_story_activities as activity_routes
from sketch2life.interfaces.http.routers import parent_story_runs as story_routes
from tests.unit.test_story_output import valid_story

ISSUER = "synthetic-t2ea-issuer"
TYPED = "A friendly dragon learns to share"
SUBJECT = "dragon"
BACKEND = Path(__file__).resolve().parents[2]
CONTEXT_HASH = "c" * 64


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def activity(title: str, *, kind: str = "outdoor") -> dict[str, Any]:
    return {
        "title": title,
        "objective": "Observe the dragon wings and tail outside",
        "materials_text": "Paper",
        "preparation_text": "",
        "instructions_text": "Walk with the child and find dragon wings in the garden",
        "observation_notes": "",
        "safety_notes": "Stay with an adult",
        "activity_kind": kind,
    }


def lesson(lesson_id: str, *titles: str) -> ParentActivityLesson:
    return ParentActivityLesson(
        lesson_id=lesson_id,
        version_id=f"v-{lesson_id}",
        version_no=1,
        content_sha256=sha(lesson_id.encode()),
        title=f"Lesson {lesson_id}",
        topic="dragon wings",
        drawing_subject=SUBJECT,
        target_age_band_ref="age-36-71-months-v1",
        target_age_band_version=1,
        access_source="PUBLIC",
        activities=tuple(activity(title) for title in titles),
    )


class Catalog(ParentActivityCatalogPort):
    """The Lesson Library catalog double; ``calls`` records the arguments of every read."""

    def __init__(self) -> None:
        self.lessons: list[ParentActivityLesson] = []
        self.calls: list[dict[str, Any]] = []

    def list_accessible_lessons(self, **kwargs: Any) -> Sequence[ParentActivityLesson]:
        self.calls.append(kwargs)
        return list(self.lessons)


class RecordingGenerator:
    def __init__(self) -> None:
        self.inputs: list[dict[str, Any]] = []

    def generate(self, worker_input: Any) -> StoryGenerationResult:
        self.inputs.append(dict(worker_input))
        return StoryGenerationResult(valid_story(), f"call-{len(self.inputs)}", "fixture", "1")


class AccessSpy:
    """Replaces ``get_lesson_library_service`` for the post-video access check of a pinned run."""

    def __init__(self) -> None:
        self.checks: list[str] = []
        self.revoked = False
        self.unavailable = False

    def __call__(self, _request: Any, _db: Any) -> Any:
        if self.unavailable:
            raise HTTPException(status_code=503, detail={"code": "DEPENDENCY_UNAVAILABLE"})
        spy = self

        class Service:
            def get_parent_lesson(self, *, parent_principal_ref: str, lesson_id: str) -> Any:
                spy.checks.append(lesson_id)
                if spy.revoked:
                    raise LessonLibraryError(404, "LESSON_NOT_FOUND", "x")
                return {}

        return Service()


@dataclass
class ActivityApi:
    app: FastAPI
    client: TestClient
    catalog: Catalog
    generator: RecordingGenerator
    spy: AccessSpy
    parent: str
    other_parent: str
    teacher: str

    def sessions(self) -> Any:
        return self.app.state.be1_runtime.session_factory


@pytest.fixture
def api(monkeypatch: pytest.MonkeyPatch) -> Iterator[ActivityApi]:
    database_url = os.environ.get("BE1_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("set BE1_TEST_DATABASE_URL to a disposable PostgreSQL database")
    database_name = database_url.rsplit("/", 1)[-1]
    if "be1_acceptance" not in database_name or "frc08_v4_t2ea" not in database_name:
        pytest.fail("BE1_TEST_DATABASE_URL must be a disposable frc08_v4_t2ea*be1_acceptance db")
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", database_url)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("SKETCH2LIFE_AUTH_PROVIDER", "development")
    monkeypatch.setenv("SKETCH2LIFE_AI_PROVIDER", "disabled")
    monkeypatch.delenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", raising=False)
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    application = create_app()
    runtime = application.state.be1_runtime
    if runtime.engine is None or runtime.session_factory is None:
        pytest.fail("PostgreSQL runtime did not initialize")
    catalog, generator, spy = Catalog(), RecordingGenerator(), AccessSpy()
    monkeypatch.setattr(
        activity_routes,
        "_selection_service",
        lambda _request, db: ParentActivitySelectionService(
            SqlParentStoryRunRepository(db), catalog
        ),
    )
    monkeypatch.setattr(story_routes, "get_lesson_library_service", spy)
    application.state.story_generator = generator
    token = uuid4().hex[:8]
    parent, other_parent = f"synthetic-t2ea-parent-{token}", f"synthetic-t2ea-parent2-{token}"
    teacher = f"synthetic-t2ea-teacher-{token}"
    with runtime.session_factory.begin() as db:
        for subject, role in ((parent, "parent"), (other_parent, "parent"), (teacher, "teacher")):
            db.add(
                AdultIdentityModel(
                    subject=subject, issuer=ISSUER, state="active", account_role=role
                )
            )

    async def verified(
        x_test_principal: str = Header(alias="X-Test-Principal"),
    ) -> VerifiedPrincipal:
        return VerifiedPrincipal(subject=x_test_principal, issuer=ISSUER, roles=frozenset())

    application.dependency_overrides[get_verified_adult] = verified
    try:
        with TestClient(application) as client:
            yield ActivityApi(
                application, client, catalog, generator, spy, parent, other_parent, teacher
            )
    finally:
        application.dependency_overrides.clear()
        runtime.engine.dispose()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


# ----------------------------------------------------------------------------- helpers
def principal_of(subject: str) -> VerifiedPrincipal:
    return VerifiedPrincipal(subject=subject, issuer=ISSUER, roles=frozenset())


def headers(subject: str, key: str | None = None) -> dict[str, str]:
    result = {"X-Test-Principal": subject}
    if key is not None:
        result["Idempotency-Key"] = key
    return result


def code_of(response: Any) -> str:
    return str(response.json()["code"])


def ref_of(item: dict[str, Any]) -> dict[str, Any]:
    return dict(item["activity_ref"])


def seed_run(
    api: ActivityApi,
    owner: str,
    *,
    context_confirmed: bool = True,
    pin: dict[str, Any] | None = None,
) -> str:
    """A run in ``SUBJECT_REVIEW``: one drawing, understanding revision 1, a context."""

    run_id, now = str(uuid4()), datetime.now(UTC)
    scope_ref = parent_scope_ref(principal_of(owner))
    token = uuid4().hex
    input_one, input_two = str(uuid4()), str(uuid4())
    context = {
        "schema_version": "sketch2life.parent-context.v1",
        "profile_revision_ref": str(uuid4()),
        "age_months": 60,
        "interests_summary": "",
        "topic": "dragon wings",
        "adult_confirmed_idea": TYPED,
    }
    candidate = {
        "candidate_subject": SUBJECT,
        "visible_features": ["wings", "tail"],
        "confidence": 0.9,
        "adult_confirmation_required": True,
        "decision": "REVIEW_REQUIRED",
    }
    with api.sessions().begin() as db:
        account_id = db.scalar(
            select(AdultIdentityModel.account_id).where(AdultIdentityModel.subject == owner)
        )
        db.execute(
            story_tables.story_runs.insert().values(
                run_id=run_id,
                actor_scope_kind="PARENT_ACCOUNT",
                actor_scope_ref=scope_ref,
                profile_ref=str(uuid4()),
                run_state="SUBJECT_REVIEW",
                job_state="SUCCEEDED",
                revision=5,
                version=5,
                current_input_revision=2,
                understanding_revision=1,
                subject_label=SUBJECT,
                confidence=0.9,
                active_owner_parent_account_id=str(account_id),
                created_at=now,
                updated_at=now,
            )
        )
        common = {
            "run_id": run_id,
            "typed_idea": TYPED,
            "idea_source": "TEXT",
            "source_profile_revision_ref": str(uuid4()),
            "context_revision": 1,
            "context_snapshot": context,
            "context_snapshot_sha256": CONTEXT_HASH,
            "context_confirmed_by": scope_ref if context_confirmed else None,
            "context_confirmed_at": now if context_confirmed else None,
            "created_at": now,
        }
        if pin is not None:  # a JSONB ``None`` would be the JSON null, not SQL NULL
            common["lesson_pin_snapshot"] = pin
            common["lesson_pin_snapshot_sha256"] = sha(b"pin")
        db.execute(
            story_tables.run_inputs.insert().values(
                run_input_id=input_one, input_revision=1, **common
            )
        )
        db.execute(
            story_tables.run_inputs.insert().values(
                run_input_id=input_two,
                input_revision=2,
                original_asset_ref=f"parent/{run_id}/{token}/original",
                original_asset_version=1,
                original_sha256=sha(f"original-{run_id}".encode()),
                original_media_type="image/png",
                original_size_bytes=100,
                derived_asset_ref=f"parent/{run_id}/{token}/normalized.png",
                derived_asset_version=1,
                derived_sha256=sha(f"derived-{run_id}".encode()),
                derived_media_type="image/png",
                derived_size_bytes=90,
                **common,
            )
        )
        db.execute(
            story_tables.understanding_revisions.insert().values(
                understanding_revision_id=str(uuid4()),
                run_id=run_id,
                run_input_id=input_two,
                revision_no=1,
                subject_label=SUBJECT,
                confidence=0.9,
                canonical_result_sha256="d" * 64,
                result_snapshot={"result": candidate},
                created_at=now,
            )
        )
    return run_id


def ready_run(api: ActivityApi, owner: str | None = None, **seed: Any) -> str:
    """A run in ``PREPARATION_REVIEW``: the subject confirmed through the real route."""

    owner = owner or api.parent
    run_id = seed_run(api, owner, **seed)
    response = api.client.post(
        f"/v1/story-runs/{run_id}/subject-confirmation",
        json={"expected_understanding_revision": 1, "confirmed_subject": SUBJECT},
        headers=headers(owner, uuid4().hex),
    )
    assert response.status_code == 202, response.text
    return run_id


def run_row(api: ActivityApi, run_id: str) -> Any:
    with api.sessions()() as db:
        return (
            db.execute(
                select(story_tables.story_runs).where(story_tables.story_runs.c.run_id == run_id)
            )
            .mappings()
            .one()
        )


def rows(api: ActivityApi, table: Any, run_id: str, column: str = "run_id") -> list[Any]:
    with api.sessions()() as db:
        return list(db.execute(select(table).where(table.c[column] == run_id)).mappings().all())


def story_rows(api: ActivityApi, run_id: str) -> list[Any]:
    return rows(api, story_tables.story_revisions, run_id)


def selection_rows(api: ActivityApi, run_id: str) -> list[Any]:
    table = story_tables.activity_selections
    with api.sessions()() as db:
        return list(
            db.execute(select(table).where(table.c.run_id == run_id).order_by(table.c.selection_no))
            .mappings()
            .all()
        )


def receipts(api: ActivityApi, run_id: str, operation: str) -> list[Any]:
    table = story_tables.story_command_receipts
    with api.sessions()() as db:
        return list(
            db.execute(
                select(table).where(table.c.resource_ref == run_id, table.c.operation == operation)
            )
            .mappings()
            .all()
        )


def revision_of(api: ActivityApi, run_id: str) -> int:
    return int(run_row(api, run_id)["revision"])


def list_activities(api: ActivityApi, owner: str, run_id: str) -> Any:
    return api.client.get("/v1/activities", params={"story_run_id": run_id}, headers=headers(owner))


def select_activity(
    api: ActivityApi,
    owner: str,
    run_id: str,
    ref: dict[str, Any],
    *,
    revision: int | None = None,
    key: str | None = None,
) -> Any:
    return api.client.post(
        f"/v1/story-runs/{run_id}/activity-selection",
        json={
            "expected_revision": revision if revision is not None else revision_of(api, run_id),
            "activity": ref,
        },
        headers=headers(owner, key or uuid4().hex),
    )


def confirm_context(api: ActivityApi, owner: str, run_id: str, *, key: str | None = None) -> Any:
    return api.client.post(
        f"/v1/story-runs/{run_id}/context-confirmation",
        json={
            "expected_context_revision": 1,
            "context_snapshot_sha256": CONTEXT_HASH,
            "confirmed": True,
        },
        headers=headers(owner, key or uuid4().hex),
    )


def get_run(api: ActivityApi, owner: str, run_id: str) -> Any:
    return api.client.get(f"/v1/story-runs/{run_id}", headers=headers(owner))


def first_ref(api: ActivityApi, owner: str, run_id: str, index: int = 0) -> dict[str, Any]:
    response = list_activities(api, owner, run_id)
    assert response.status_code == 200, response.text
    return ref_of(response.json()["items"][index])


def stock(api: ActivityApi) -> None:
    api.catalog.lessons = [lesson("a", "Find dragon wings"), lesson("b", "Draw the dragon tail")]


# ============================================================================= the list
def test_the_list_returns_the_age_fit_activities_with_a_basis_and_no_provider_call(
    api: ActivityApi,
) -> None:
    stock(api)
    run_id = ready_run(api)
    response = list_activities(api, api.parent, run_id)
    assert response.status_code == 200
    body = response.json()
    assert [item["title"] for item in body["items"]] == [
        "Find dragon wings",
        "Draw the dragon tail",
    ]
    assert body["basis"] == {"age_band": "36-71", "pinned_lesson": False, "no_candidate": False}
    text_body = response.text.lower()
    for word in ("bucket", "object_key", "presigned", "amazonaws", "http"):
        assert word not in text_body, word
    # a read changes nothing: no selection, no receipt, no revision bump
    assert selection_rows(api, run_id) == [] and revision_of(api, run_id) == 6


def test_no_catalog_hit_is_an_empty_list_and_the_story_cannot_start(api: ActivityApi) -> None:
    run_id = ready_run(api)
    body = list_activities(api, api.parent, run_id).json()
    assert body["items"] == [] and body["basis"]["no_candidate"] is True
    # a context confirmation alone starts nothing: the adult must choose an activity first
    assert confirm_context(api, api.parent, run_id).status_code == 200
    assert run_row(api, run_id)["run_state"] == "PREPARATION_REVIEW"
    assert story_rows(api, run_id) == []


def test_the_catalog_receives_the_principal_reference_and_nothing_of_the_child(
    api: ActivityApi,
) -> None:
    stock(api)
    run_id = ready_run(api)
    assert list_activities(api, api.parent, run_id).status_code == 200
    assert len(api.catalog.calls) == 1
    assert set(api.catalog.calls[0]) == {"parent_principal_ref"}
    assert api.catalog.calls[0]["parent_principal_ref"] == api.parent


def test_the_list_refuses_an_input_phase_run_with_422_and_a_later_state_with_409(
    api: ActivityApi,
) -> None:
    stock(api)
    early = seed_run(api, api.parent)  # SUBJECT_REVIEW
    response = list_activities(api, api.parent, early)
    assert response.status_code == 422 and code_of(response) == "SUBJECT_NOT_CONFIRMED"
    ref = {"lesson_id": "a", "version_id": "v-a", "content_sha256": "0" * 64, "activity_index": 0}
    selected = select_activity(api, api.parent, early, ref)
    assert selected.status_code == 422 and code_of(selected) == "SUBJECT_NOT_CONFIRMED"
    with api.sessions().begin() as db:
        db.execute(
            update(story_tables.story_runs)
            .where(story_tables.story_runs.c.run_id == early)
            .values(run_state="SCRIPT_REVIEW")
        )
    response = list_activities(api, api.parent, early)
    assert response.status_code == 409 and code_of(response) == "INVALID_STATE_TRANSITION"


def test_a_caller_out_of_scope_gets_the_uniform_404(api: ActivityApi) -> None:
    stock(api)
    run_id = ready_run(api)
    ref = first_ref(api, api.parent, run_id)
    for caller in (api.other_parent, api.teacher, f"unknown-{uuid4().hex}"):
        for response in (
            list_activities(api, caller, run_id),
            select_activity(api, caller, run_id, ref, revision=6),
        ):
            assert response.status_code == 404, caller
            assert code_of(response) == "RESOURCE_NOT_FOUND"
    assert list_activities(api, api.parent, str(uuid4())).status_code == 404
    assert selection_rows(api, run_id) == []


# ============================================================================= the selection
def test_a_selection_stores_an_immutable_snapshot_and_bumps_the_run_revision(
    api: ActivityApi,
) -> None:
    stock(api)
    run_id = ready_run(api, context_confirmed=False)
    ref = first_ref(api, api.parent, run_id)
    before = run_row(api, run_id)
    response = select_activity(api, api.parent, run_id, ref)
    assert response.status_code == 200, response.text
    story_run = response.json()["story_run"]
    assert story_run["run_revision"] == before["revision"] + 1
    assert story_run["main_activity"]["state"] == "SELECTED"
    assert story_run["main_activity"]["selected"]["activity_ref"] == ref
    assert story_run["main_activity"]["selected_at"] is not None
    assert story_run["run_state"] == "PREPARATION_REVIEW"  # the context is not confirmed yet
    (row,) = selection_rows(api, run_id)
    assert row["selection_no"] == 1 and row["target_understanding_revision"] == 1
    assert (row["lesson_id"], row["version_id"], row["activity_index"]) == (
        ref["lesson_id"],
        ref["version_id"],
        ref["activity_index"],
    )
    assert (
        row["source_kind"] == "LESSON_ACTIVITY" and row["content_sha256"] == ref["content_sha256"]
    )
    assert row["activity_snapshot"]["schema"] == "sketch2life.parent-activity-pin.v1"
    assert row["activity_snapshot"]["title"] == "Find dragon wings"
    assert len(row["activity_snapshot_sha256"]) == 64
    (receipt,) = receipts(api, run_id, "SELECT_ACTIVITY")
    assert receipt["state"] == "FINAL" and receipt["response_status"] == 200
    assert receipt["response_body"] == {
        "selection_no": 1,
        "activity_ref": ref,
        "understanding_revision": 1,
    }  # ids and status only: no lesson text
    assert row["command_receipt_id"] == receipt["receipt_id"]
    # the row is append-only: an UPDATE is refused by the trigger
    with (
        pytest.raises(DBAPIError, match="ACTIVITY_SELECTION_UPDATE_FORBIDDEN"),
        api.sessions().begin() as db,
    ):
        db.execute(
            update(story_tables.activity_selections)
            .where(story_tables.activity_selections.c.run_id == run_id)
            .values(activity_index=1)
        )
    assert selection_rows(api, run_id)[0]["activity_index"] == ref["activity_index"]


def test_the_story_starts_when_the_context_is_confirmed_after_the_selection(
    api: ActivityApi,
) -> None:
    """SRS order (l.1412): choose, confirm the context, then the AI makes the script."""

    stock(api)
    run_id = ready_run(api, context_confirmed=False)
    assert (
        select_activity(api, api.parent, run_id, first_ref(api, api.parent, run_id)).status_code
        == 200
    )
    assert story_rows(api, run_id) == []
    response = confirm_context(api, api.parent, run_id)
    assert response.status_code == 200, response.text
    # the generator ran after the response (TestClient finishes the background task)
    (story,) = story_rows(api, run_id)
    assert story["revision_no"] == 1 and story["status"] == "DRAFT"
    row = run_row(api, run_id)
    assert (row["run_state"], row["job_state"]) == ("SCRIPT_REVIEW", "SUCCEEDED")
    assert len(api.generator.inputs) == 1
    assert receipts(api, run_id, "GENERATE_STORY_REVISION") == []  # the command's receipt only
    assert len(receipts(api, run_id, "CONFIRM_CONTEXT")) == 1


def test_the_story_starts_when_the_selection_is_the_last_gate(api: ActivityApi) -> None:
    stock(api)
    run_id = ready_run(api, context_confirmed=True)
    response = select_activity(api, api.parent, run_id, first_ref(api, api.parent, run_id))
    assert response.status_code == 200, response.text
    (story,) = story_rows(api, run_id)
    assert story["revision_no"] == 1 and story["understanding_revision"] == 1
    assert run_row(api, run_id)["run_state"] == "SCRIPT_REVIEW"
    worker = api.generator.inputs[0]
    assert worker["schema_version"] == "sketch2life.story-generation-input.v3"
    assert worker["context_entries"] == []  # T-12a: no selection, no entry
    assert worker["role"] == "PARENT" and worker["lesson_direction"] is None
    assert worker["confirmed_subject"] == SUBJECT and worker["child_age_months"] == 60
    assert worker["adult_confirmed_idea"] == TYPED
    assert worker["activity"]["title"] == "Find dragon wings"
    assert worker["activity"]["lesson_id"] == "a" and worker["activity"]["version_id"] == "v-a"
    assert set(worker["activity"]) == {
        "title",
        "objective",
        "instructions_text",
        "safety_notes",
        "activity_kind",
        "source",
        "lesson_id",
        "version_id",
        "content_sha256",
    }
    assert "rewrite_instruction" not in worker
    assert story["request_sha256"] == _sha256_json(worker)


def test_the_started_story_waits_in_the_queue_when_no_generator_is_composed(
    api: ActivityApi,
) -> None:
    stock(api)
    api.app.state.story_generator = None
    run_id = ready_run(api, context_confirmed=True)
    assert (
        select_activity(api, api.parent, run_id, first_ref(api, api.parent, run_id)).status_code
        == 200
    )
    row = run_row(api, run_id)
    assert (row["run_state"], row["job_state"]) == ("SCRIPT_GENERATING", "QUEUED")
    (story,) = story_rows(api, run_id)
    assert story["status"] == "GENERATING"
    assert story["model_id"] == story_first_start.FIRST_STORY_MODEL_ID
    assert story["prompt_version"] == story_first_start.FIRST_STORY_PROMPT_VERSION
    assert run_row(api, run_id)["version"] == 5 + 1 + 1 + 1  # subject, selection, start


def test_a_generator_failure_of_the_first_story_ends_the_run_failed_or_waits_for_reconciliation(
    api: ActivityApi,
) -> None:
    """D12: the first story has no previous story to return to (the T-2d-fix rule of revision 1)."""

    class Failing:
        def __init__(self, error: Exception) -> None:
            self.error = error

        def generate(self, worker_input: Any) -> Any:
            raise self.error

    stock(api)
    for error, run_state, code in (
        (StoryGenerationFailure(), "FAILED", "STORY_GENERATION_UNAVAILABLE"),
        (StoryGenerationOutcomeUnknown(), "SCRIPT_GENERATION_UNKNOWN", "STORY_OUTCOME_UNKNOWN"),
    ):
        api.app.state.story_generator = Failing(error)
        owner = f"synthetic-t2ea-failing-{uuid4().hex[:8]}"
        with api.sessions().begin() as db:
            db.add(
                AdultIdentityModel(
                    subject=owner, issuer=ISSUER, state="active", account_role="parent"
                )
            )
        run_id = ready_run(api, owner, context_confirmed=True)
        response = select_activity(api, owner, run_id, first_ref(api, owner, run_id))
        assert response.status_code == 200  # the answer was given before the work
        row = run_row(api, run_id)
        assert (row["run_state"], row["error_code"]) == (run_state, code)
        assert len(story_rows(api, run_id)) == 1


def test_a_reselection_is_allowed_until_the_story_starts_and_then_refused(
    api: ActivityApi,
) -> None:
    stock(api)
    run_id = ready_run(api, context_confirmed=False)
    first = first_ref(api, api.parent, run_id, 0)
    second = first_ref(api, api.parent, run_id, 1)
    assert select_activity(api, api.parent, run_id, first).status_code == 200
    assert select_activity(api, api.parent, run_id, second).status_code == 200
    assert [row["selection_no"] for row in selection_rows(api, run_id)] == [1, 2]
    body = get_run(api, api.parent, run_id).json()["story_run"]
    assert body["main_activity"]["selected"]["activity_ref"] == second  # the latest counts
    assert confirm_context(api, api.parent, run_id).status_code == 200
    assert api.generator.inputs[0]["activity"]["title"] == "Draw the dragon tail"
    changed = select_activity(api, api.parent, run_id, first)
    assert changed.status_code == 409 and code_of(changed) == "INVALID_STATE_TRANSITION"
    assert len(selection_rows(api, run_id)) == 2 and len(story_rows(api, run_id)) == 1


def test_an_unlisted_or_vanished_activity_is_404_and_writes_nothing(api: ActivityApi) -> None:
    stock(api)
    run_id = ready_run(api, context_confirmed=False)
    ref = first_ref(api, api.parent, run_id)
    for change in ({"lesson_id": "nope"}, {"content_sha256": "e" * 64}, {"activity_index": 7}):
        response = select_activity(api, api.parent, run_id, {**ref, **change})
        assert response.status_code == 404 and code_of(response) == "RESOURCE_NOT_FOUND"
    api.catalog.lessons = [
        lesson("b", "Draw the dragon tail")
    ]  # unpublished between list and select
    response = select_activity(api, api.parent, run_id, ref)
    assert response.status_code == 404
    assert selection_rows(api, run_id) == [] and receipts(api, run_id, "SELECT_ACTIVITY") == []
    assert revision_of(api, run_id) == 6  # a refusal changes nothing


def test_a_selection_replay_answers_the_same_run_and_never_recomputes_the_list(
    api: ActivityApi,
) -> None:
    stock(api)
    run_id = ready_run(api, context_confirmed=False)
    ref = first_ref(api, api.parent, run_id)
    first = select_activity(api, api.parent, run_id, ref, revision=6, key="replay-key")
    assert first.status_code == 200
    reads = len(api.catalog.calls)
    api.catalog.lessons = []  # the activity is gone and the revision moved: a replay still answers
    again = select_activity(api, api.parent, run_id, ref, revision=6, key="replay-key")
    assert again.status_code == 200
    assert again.json()["story_run"]["run_revision"] == first.json()["story_run"]["run_revision"]
    assert len(api.catalog.calls) == reads  # no catalog read on a replay
    assert (
        len(selection_rows(api, run_id)) == 1 and len(receipts(api, run_id, "SELECT_ACTIVITY")) == 1
    )


def test_an_activity_displaced_from_the_list_still_replays_but_is_not_selectable_again(
    api: ActivityApi,
) -> None:
    """Accessible and age-fit but ranked beyond twelve: the first answer is 404, a replay is 200."""

    stock(api)
    run_id = ready_run(api, context_confirmed=False)
    ref = first_ref(api, api.parent, run_id)  # lesson ``a``
    assert (
        select_activity(api, api.parent, run_id, ref, revision=6, key="displaced").status_code
        == 200
    )
    # thirteen lessons with the same text and ids that sort first take every place of the list
    api.catalog.lessons = [lesson(f"{index:04d}", "Find dragon wings") for index in range(13)] + (
        api.catalog.lessons
    )
    items = list_activities(api, api.parent, run_id).json()["items"]
    assert len(items) == 12 and ref not in [item["activity_ref"] for item in items]
    again = select_activity(api, api.parent, run_id, ref, revision=6, key="displaced")
    assert again.status_code == 200  # the replay never recomputes the list
    other = select_activity(api, api.parent, run_id, ref, revision=7, key="displaced-new")
    assert other.status_code == 404 and code_of(other) == "RESOURCE_NOT_FOUND"
    assert len(selection_rows(api, run_id)) == 1


def test_a_replay_after_the_story_started_still_answers_200_and_starts_nothing_more(
    api: ActivityApi,
) -> None:
    stock(api)
    run_id = ready_run(api, context_confirmed=True)
    ref = first_ref(api, api.parent, run_id)
    assert (
        select_activity(api, api.parent, run_id, ref, revision=6, key="k-start").status_code == 200
    )
    assert (
        select_activity(api, api.parent, run_id, ref, revision=6, key="k-start").status_code == 200
    )
    assert len(story_rows(api, run_id)) == 1 and len(api.generator.inputs) == 1


def test_a_key_reused_with_another_body_is_400_invalid_idempotency_key(api: ActivityApi) -> None:
    stock(api)
    run_id = ready_run(api, context_confirmed=False)
    first, second = first_ref(api, api.parent, run_id, 0), first_ref(api, api.parent, run_id, 1)
    assert (
        select_activity(api, api.parent, run_id, first, revision=6, key="same-key").status_code
        == 200
    )
    response = select_activity(api, api.parent, run_id, second, revision=6, key="same-key")
    assert response.status_code == 400 and code_of(response) == "INVALID_IDEMPOTENCY_KEY"
    assert len(selection_rows(api, run_id)) == 1


def test_an_invalid_or_missing_header_is_a_plain_400_invalid_request(api: ActivityApi) -> None:
    stock(api)
    run_id = ready_run(api, context_confirmed=False)
    ref = first_ref(api, api.parent, run_id)
    body = {"expected_revision": 6, "activity": ref}
    for header in (None, "", "x" * 129):
        extra = {} if header is None else {"Idempotency-Key": header}
        response = api.client.post(
            f"/v1/story-runs/{run_id}/activity-selection",
            json=body,
            headers={"X-Test-Principal": api.parent, **extra},
        )
        assert response.status_code == 400 and code_of(response) == "INVALID_REQUEST"
        assert not response.json().get("field_errors")
    assert selection_rows(api, run_id) == []


def test_a_stale_run_revision_is_409_with_the_current_revision(api: ActivityApi) -> None:
    stock(api)
    run_id = ready_run(api, context_confirmed=False)
    ref = first_ref(api, api.parent, run_id)
    response = select_activity(api, api.parent, run_id, ref, revision=5)
    assert response.status_code == 409 and code_of(response) == "STALE_REVISION"
    assert response.json()["current_version"] == 6
    assert selection_rows(api, run_id) == []


# ============================================================================= races
def test_two_parallel_selections_on_a_ready_run_give_one_story(api: ActivityApi) -> None:
    stock(api)
    api.app.state.story_generator = None  # keep the story in the queue; the start is what counts
    run_id = ready_run(api, context_confirmed=True)
    ref = first_ref(api, api.parent, run_id)
    revision = revision_of(api, run_id)
    barrier = Barrier(2)

    def post(_: int) -> Any:
        barrier.wait()
        return select_activity(api, api.parent, run_id, ref, revision=revision)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(post, range(2)))
    statuses = sorted(response.status_code for response in results)
    assert statuses == [200, 409]
    loser = next(response for response in results if response.status_code == 409)
    assert code_of(loser) in {"STALE_REVISION", "INVALID_STATE_TRANSITION"}
    assert len(story_rows(api, run_id)) == 1  # never a second story
    assert len(selection_rows(api, run_id)) == 1
    assert run_row(api, run_id)["run_state"] == "SCRIPT_GENERATING"


def test_a_selection_and_a_context_confirmation_in_parallel_give_one_story(
    api: ActivityApi,
) -> None:
    stock(api)
    api.app.state.story_generator = None
    run_id = ready_run(api, context_confirmed=False)
    ref = first_ref(api, api.parent, run_id)
    revision = revision_of(api, run_id)
    barrier = Barrier(2)

    def call(index: int) -> Any:
        barrier.wait()
        if index == 0:
            return select_activity(api, api.parent, run_id, ref, revision=revision)
        return confirm_context(api, api.parent, run_id)

    with ThreadPoolExecutor(max_workers=2) as pool:
        selected, confirmed = list(pool.map(call, range(2)))
    # the context confirmation has no revision to go stale: it always answers
    assert confirmed.status_code == 200, confirmed.text
    state = run_row(api, run_id)["run_state"]
    if selected.status_code == 200:
        # both gates are met whichever ran second: the story exists exactly once
        assert state == "SCRIPT_GENERATING" and len(story_rows(api, run_id)) == 1
        assert len(selection_rows(api, run_id)) == 1
    else:
        # the confirmation ran first and moved the run revision: the selection is stale and
        # nothing started (no selection exists)
        assert (selected.status_code, code_of(selected)) == (409, "STALE_REVISION")
        assert state == "PREPARATION_REVIEW" and story_rows(api, run_id) == []
        assert selection_rows(api, run_id) == []


# ============================================================================= the legacy route
def test_the_legacy_first_story_needs_the_selection_only_when_the_route_asks(
    api: ActivityApi,
) -> None:
    stock(api)
    run_id = ready_run(api, context_confirmed=True)
    owner = principal_of(api.parent)

    def reserve(**extra: Any) -> Any:
        with api.sessions()() as db:
            return SqlParentStoryRunRepository(db).reserve_story_revision(
                principal=owner,
                run_id=run_id,
                expected_understanding_revision=1,
                rewrite_instruction=None,
                idempotency_key=uuid4().hex,
                story_revision_id=str(uuid4()),
                model_id="synthetic",
                model_revision="1",
                prompt_version="synthetic",
                **extra,
            )

    with pytest.raises(ParentStoryRunError) as raised:
        reserve(require_activity_selection=True)
    assert (raised.value.status_code, raised.value.code) == (
        409,
        "PARENT_ACTIVITY_SELECTION_REQUIRED",
    )
    assert (
        story_rows(api, run_id) == [] and run_row(api, run_id)["run_state"] == "PREPARATION_REVIEW"
    )
    # without the flag (every other caller) the legacy reservation is unchanged
    reservation = reserve()
    assert reservation.revision_no == 1 and reservation.worker_input["schema_version"] == (
        "sketch2life.story-generation-input.v1"
    )


def test_after_the_implicit_start_the_legacy_route_answers_the_existing_not_ready_code(
    api: ActivityApi,
) -> None:
    stock(api)
    api.app.state.story_generator = None
    run_id = ready_run(api, context_confirmed=True)
    assert (
        select_activity(api, api.parent, run_id, first_ref(api, api.parent, run_id)).status_code
        == 200
    )
    assert run_row(api, run_id)["run_state"] == "SCRIPT_GENERATING"
    with api.sessions()() as db, pytest.raises(ParentStoryRunError) as raised:
        SqlParentStoryRunRepository(db).reserve_story_revision(
            principal=principal_of(api.parent),
            run_id=run_id,
            expected_understanding_revision=1,
            rewrite_instruction=None,
            idempotency_key=uuid4().hex,
            story_revision_id=str(uuid4()),
            model_id="synthetic",
            model_revision="1",
            prompt_version="synthetic",
            require_activity_selection=True,
        )
    assert (raised.value.status_code, raised.value.code) == (
        409,
        "PARENT_STORY_RUN_NOT_READY_FOR_SCRIPT",
    )
    assert len(story_rows(api, run_id)) == 1


# ============================================================================= atomicity
class _RefusedRevisionInsert:
    """An insert of ``story.story_revisions`` that the database refuses (``revision_no`` 9)."""

    def __init__(self, real: Any) -> None:
        self._real = real

    def values(self, **values: Any) -> Any:
        return self._real.values(**{**values, "revision_no": 9})


def _make_the_start_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    real_insert = story_first_start.insert
    monkeypatch.setattr(
        story_first_start, "insert", lambda table: _RefusedRevisionInsert(real_insert(table))
    )


def _stamp(api: ActivityApi, run_id: str) -> Any:
    with api.sessions()() as db:
        return db.scalar(
            select(story_tables.run_inputs.c.context_confirmed_by).where(
                story_tables.run_inputs.c.run_id == run_id,
                story_tables.run_inputs.c.input_revision == 2,
            )
        )


def test_a_real_start_failure_rolls_the_confirmation_back_and_answers_503(
    api: ActivityApi, monkeypatch: pytest.MonkeyPatch
) -> None:
    stock(api)
    run_id = ready_run(api, context_confirmed=False)
    assert (
        select_activity(api, api.parent, run_id, first_ref(api, api.parent, run_id)).status_code
        == 200
    )
    before = run_row(api, run_id)
    with monkeypatch.context() as patch:
        _make_the_start_fail(patch)
        response = confirm_context(api, api.parent, run_id)
    assert response.status_code == 503
    assert code_of(response) == "PARENT_STORY_RUN_STORE_UNAVAILABLE"  # not a 409 key conflict
    after = run_row(api, run_id)
    assert (after["revision"], after["version"], after["run_state"]) == (
        before["revision"],
        before["version"],
        before["run_state"],
    )
    assert _stamp(api, run_id) is None  # the stamp was rolled back with the failed insert
    assert receipts(api, run_id, "CONFIRM_CONTEXT") == [] and story_rows(api, run_id) == []
    assert confirm_context(api, api.parent, run_id).status_code == 200  # the run is not stuck
    assert len(story_rows(api, run_id)) == 1


def test_a_real_start_failure_leaves_no_selection_and_no_receipt(
    api: ActivityApi, monkeypatch: pytest.MonkeyPatch
) -> None:
    stock(api)
    run_id = ready_run(api, context_confirmed=True)
    ref = first_ref(api, api.parent, run_id)
    before = run_row(api, run_id)
    _make_the_start_fail(monkeypatch)
    response = select_activity(api, api.parent, run_id, ref, revision=int(before["revision"]))
    assert response.status_code == 503
    assert code_of(response) == "PARENT_STORY_RUN_STORE_UNAVAILABLE"
    after = run_row(api, run_id)
    assert (after["revision"], after["version"], after["run_state"]) == (
        before["revision"],
        before["version"],
        before["run_state"],
    )
    assert selection_rows(api, run_id) == [] and receipts(api, run_id, "SELECT_ACTIVITY") == []
    assert story_rows(api, run_id) == []


# ============================================================================= the envelope
def seed_state(api: ActivityApi, run_id: str, state: str) -> None:
    with api.sessions().begin() as db:
        db.execute(
            update(story_tables.story_runs)
            .where(story_tables.story_runs.c.run_id == run_id)
            .values(run_state=state, job_state="SUCCEEDED")
        )


def pin_snapshot() -> dict[str, Any]:
    return {
        "schema_version": "sketch2life.parent-lesson-pin.v1",
        "lesson_id": "a",
        "version_id": "v-a",
        "version_no": 1,
        "content_sha256": sha(b"a"),
        "target_age_band_ref": "age-36-71-months-v1",
        "target_age_band_version": 1,
        "title": "Lesson a",
        "topic": "dragon wings",
        "drawing_subject": SUBJECT,
        "subject_learning_notes": "notes",
        "script_direction": None,
        "script_following_allowed": True,
        "activities": [activity("Find dragon wings"), activity("Draw the dragon tail")],
    }


def test_a_run_without_a_selection_reports_not_selected(api: ActivityApi) -> None:
    run_id = ready_run(api)
    body = get_run(api, api.parent, run_id).json()["story_run"]
    assert body["main_activity"] == {"state": "NOT_SELECTED", "selected": None, "selected_at": None}
    assert body["post_video_activities"] is None


def test_post_video_activities_of_a_run_without_a_pin_come_from_the_stored_snapshot_only(
    api: ActivityApi,
) -> None:
    stock(api)
    run_id = ready_run(api, context_confirmed=False)
    ref = first_ref(api, api.parent, run_id)
    assert select_activity(api, api.parent, run_id, ref).status_code == 200
    seed_state(api, run_id, "VIDEO_READY")
    api.catalog.calls.clear()
    api.catalog.lessons = []  # even an unpublished lesson does not change what was chosen
    response = get_run(api, api.parent, run_id)
    body = response.json()["story_run"]
    assert [item["activity_ref"] for item in body["post_video_activities"]] == [ref]
    assert body["post_video_activities"][0]["is_main"] is True
    assert body["main_activity"]["state"] == "SELECTED"
    assert api.catalog.calls == [] and api.spy.checks == []  # no catalog and no access read


def test_post_video_activities_of_a_pinned_run_list_the_pinned_version_after_one_access_check(
    api: ActivityApi,
) -> None:
    run_id = ready_run(api, context_confirmed=False, pin=pin_snapshot())
    ref = first_ref(api, api.parent, run_id, 1)
    assert ref["lesson_id"] == "a" and ref["activity_index"] == 1
    assert select_activity(api, api.parent, run_id, ref).status_code == 200
    seed_state(api, run_id, "COMPLETED")
    api.spy.checks.clear()
    body = get_run(api, api.parent, run_id).json()["story_run"]
    items = body["post_video_activities"]
    assert [item["activity_ref"]["activity_index"] for item in items] == [0, 1]
    assert [item["is_main"] for item in items] == [False, True]
    assert {item["source"] for item in items} == {"PINNED_LESSON"}
    assert api.spy.checks == ["a"]  # one check by lesson id, not a catalog list
    assert api.catalog.calls == []
    first_etag = get_run(api, api.parent, run_id).headers["ETag"]
    # access revoked: the list is withheld, the stored selection stays, the read does not fail
    api.spy.revoked = True
    revoked = get_run(api, api.parent, run_id)
    assert revoked.status_code == 200
    assert revoked.json()["story_run"]["post_video_activities"] is None
    assert revoked.json()["story_run"]["main_activity"]["state"] == "SELECTED"
    assert revoked.headers["ETag"] != first_etag  # the strong ETag follows the body
    api.spy.revoked, api.spy.unavailable = False, True  # storage not composed: withheld as well
    withheld = get_run(api, api.parent, run_id)
    assert withheld.status_code == 200
    assert withheld.json()["story_run"]["post_video_activities"] is None


def test_complete_answers_the_pinned_list_only_while_the_lesson_is_still_viewable(
    api: ActivityApi,
) -> None:
    """``POST /complete`` answers the run envelope, so it is guarded like the run reads (D11)."""

    for revoked in (False, True):
        owner = f"synthetic-t2ea-complete-{uuid4().hex[:8]}"
        with api.sessions().begin() as db:
            db.add(
                AdultIdentityModel(
                    subject=owner, issuer=ISSUER, state="active", account_role="parent"
                )
            )
        run_id = ready_run(api, owner, context_confirmed=False, pin=pin_snapshot())
        ref = first_ref(api, owner, run_id, 1)
        assert select_activity(api, owner, run_id, ref).status_code == 200
        seed_state(api, run_id, "VIDEO_READY")
        api.spy.checks.clear()
        api.spy.revoked = revoked
        key = uuid4().hex
        revision = revision_of(api, run_id)
        first = api.client.post(
            f"/v1/story-runs/{run_id}/complete",
            json={"expected_revision": revision},
            headers=headers(owner, key),
        )
        # the replay of the same command answers the same guarded envelope
        replay = api.client.post(
            f"/v1/story-runs/{run_id}/complete",
            json={"expected_revision": revision},
            headers=headers(owner, key),
        )
        for response in (first, replay):
            assert response.status_code == 200, response.text
            body = response.json()["story_run"]
            assert body["run_state"] == "COMPLETED"
            assert body["main_activity"]["state"] == "SELECTED"
            if revoked:
                assert body["post_video_activities"] is None
            else:
                assert [i["is_main"] for i in body["post_video_activities"]] == [False, True]
        assert api.spy.checks == ["a", "a"]  # one access check per answer
        api.spy.revoked = False


# ============================================================================= the purge
def test_the_purge_deletes_the_selections_and_keeps_only_the_tombstoned_receipt(
    api: ActivityApi,
) -> None:
    stock(api)
    run_id = ready_run(api, context_confirmed=False)
    assert (
        select_activity(api, api.parent, run_id, first_ref(api, api.parent, run_id)).status_code
        == 200
    )
    assert len(selection_rows(api, run_id)) == 1
    cancel = api.client.post(
        f"/v1/story-runs/{run_id}/cancel",
        json={"expected_revision": revision_of(api, run_id)},
        headers=headers(api.parent, uuid4().hex),
    )
    assert cancel.status_code == 202, cancel.text
    store = SqlStoryLifecycleStore(api.sessions())
    plan = store.plan_story_purge(run_id)
    assert any(item.startswith("activity_selections:") for item in plan.ids)
    store.purge_story_content(plan)
    assert selection_rows(api, run_id) == []  # the lesson text copy is gone with the run content
    (receipt,) = receipts(api, run_id, "SELECT_ACTIVITY")
    assert receipt["request_fingerprint_sha256"] == tombstone_fingerprint(
        str(receipt["receipt_id"])
    )
    assert run_row(api, run_id)["run_state"] == "DELETE_PENDING"


# ============================================================================= the round trip
@pytest.fixture
def roundtrip(monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[Config, Engine]]:
    url = os.environ.get("T2EA_ROUNDTRIP_DATABASE_URL")
    if not url:
        pytest.skip(
            "set T2EA_ROUNDTRIP_DATABASE_URL to a disposable round-trip PostgreSQL database"
        )
    name = url.rsplit("/", 1)[-1]
    if not all(part in name for part in ("be1_acceptance", "frc08_v4_t2ea", "roundtrip")):
        pytest.fail(
            "T2EA_ROUNDTRIP_DATABASE_URL must name a frc08_v4_t2ea*roundtrip*be1_acceptance db"
        )
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", url)
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    config = Config(str(BACKEND / "alembic.ini"))
    command.upgrade(config, "heads")
    engine = create_engine(url, poolclass=NullPool)
    try:
        yield config, engine
    finally:
        engine.dispose()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def _versions(engine: Engine) -> set[str]:
    with engine.connect() as connection:
        return {
            row[0] for row in connection.execute(text("select version_num from alembic_version"))
        }


def _scalar(engine: Engine, sql: str) -> Any:
    with engine.connect() as connection:
        return connection.execute(text(sql)).scalar()


def _table_exists(engine: Engine) -> bool:
    return _scalar(engine, "select to_regclass('story.activity_selections')") is not None


def _receipt_names(engine: Engine) -> str:
    return str(
        _scalar(
            engine,
            "select pg_get_constraintdef(oid) from pg_constraint "
            "where conname = 'ck_story_receipt_operation'",
        )
    )


def _insert_run_with_receipt(engine: Engine, operation: str) -> tuple[str, str]:
    run_id, receipt_id, now = str(uuid4()), str(uuid4()), datetime.now(UTC)
    with engine.begin() as connection:
        connection.execute(
            text(
                "insert into story.runs (run_id, actor_scope_kind, actor_scope_ref, profile_ref, "
                "run_state, revision, version, retryable, dispatch_gate_open, created_at, "
                "updated_at) values (:r, 'PARENT_ACCOUNT', :s, :p, 'INPUT_PROCESSING', 1, 1, "
                "false, false, :n, :n)"
            ),
            {"r": run_id, "s": "s" * 64, "p": str(uuid4()), "n": now},
        )
        connection.execute(
            text(
                "insert into story.command_receipts (receipt_id, actor_scope_kind, "
                "actor_scope_ref, operation, idempotency_scope_kind, idempotency_scope_ref, "
                "idempotency_key_sha256, request_fingerprint_sha256, state, response_status, "
                "response_body, resource_ref, created_at, finalized_at) values (:id, "
                "'PARENT_ACCOUNT', :s, :op, 'STORY_RUN', :r, repeat('a', 64), repeat('b', 64), "
                "'FINAL', 200, '{}'::jsonb, :r, :n, :n)"
            ),
            {"id": receipt_id, "s": "s" * 64, "op": operation, "r": run_id, "n": now},
        )
    return run_id, receipt_id


def _insert_selection(engine: Engine, run_id: str, receipt_id: str) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                "insert into story.activity_selections (selection_id, run_id, selection_no, "
                "target_understanding_revision, source_kind, lesson_id, version_id, "
                "content_sha256, activity_index, activity_snapshot, activity_snapshot_sha256, "
                "command_receipt_id, actor_scope_kind, actor_scope_ref) values (:id, :r, 1, 1, "
                "'LESSON_ACTIVITY', 'l', "
                "'v', repeat('a', 64), 0, '{}'::jsonb, repeat('b', 64), :rc, 'PARENT_ACCOUNT', 's')"
            ),
            {"id": str(uuid4()), "r": run_id, "rc": receipt_id},
        )


def test_the_head_is_the_new_revision_and_the_objects_exist(
    roundtrip: tuple[Config, Engine],
) -> None:
    _config, engine = roundtrip
    versions = _versions(engine)
    # V4-A T-1b-fix: DDL-B1c (``20261123_rv_0001``) follows this revision; V4-B T-12b:
    # ``20261121_bpr_0001`` follows that; V4-B T-12c: ``20261121_psn_0002`` follows it and
    # is the live head.
    assert "20261123_ppg_0001" in versions
    assert {"20261123_as_0001", "20261120_b2_0001"}.isdisjoint(versions)
    assert _table_exists(engine) and "SELECT_ACTIVITY" in _receipt_names(engine)
    assert (
        _scalar(
            engine,
            "select count(*) from pg_trigger "
            "where tgrelid = to_regclass('story.activity_selections') "
            "and tgname = 'trg_story_activity_selection_append_only' and not tgisinternal",
        )
        == 1
    )


def test_the_explicit_downgrade_removes_every_object_and_the_upgrade_restores_them(
    roundtrip: tuple[Config, Engine],
) -> None:
    config, engine = roundtrip
    try:
        command.downgrade(config, "20261120_b2_0001")  # explicit revision, never -1
        assert "20261120_b2_0001" in _versions(engine)
        assert not _table_exists(engine) and "SELECT_ACTIVITY" not in _receipt_names(engine)
        command.upgrade(config, "heads")
        assert "20261123_ppg_0001" in _versions(engine) and _table_exists(engine)
        assert "SELECT_ACTIVITY" in _receipt_names(engine)
    finally:
        command.upgrade(config, "heads")


def test_the_downgrade_refuses_while_a_selection_row_or_a_receipt_exists(
    roundtrip: tuple[Config, Engine],
) -> None:
    config, engine = roundtrip
    run_id, receipt_id = _insert_run_with_receipt(engine, "SELECT_ACTIVITY")
    try:
        # only the receipt survives (the state after a purge): refused
        with pytest.raises(Exception, match="DDL-B3 downgrade refused"):
            command.downgrade(config, "20261120_b2_0001")
        assert "20261123_ppg_0001" in _versions(engine) and _table_exists(engine)
        _insert_selection(engine, run_id, receipt_id)
        with pytest.raises(Exception, match="DDL-B3 downgrade refused"):
            command.downgrade(config, "20261120_b2_0001")
        assert _table_exists(engine)
        # the append-only trigger and the shape check
        with (
            pytest.raises(DBAPIError, match="ACTIVITY_SELECTION_UPDATE_FORBIDDEN"),
            engine.begin() as connection,
        ):
            connection.execute(
                text("update story.activity_selections set activity_index = 1 where run_id = :r"),
                {"r": run_id},
            )
        with pytest.raises(DBAPIError, match="ck_as_shape"), engine.begin() as connection:
            connection.execute(
                text(
                    "insert into story.activity_selections (selection_id, run_id, selection_no, "
                    "target_understanding_revision, source_kind, activity_snapshot, "
                    "activity_snapshot_sha256, command_receipt_id, actor_scope_kind, "
                    "actor_scope_ref) values (:id, :r, 2, 1, 'LESSON_ACTIVITY', '{}'::jsonb, "
                    "repeat('b', 64), :rc, 'PARENT_ACCOUNT', 's')"
                ),
                {"id": str(uuid4()), "r": run_id, "rc": receipt_id},
            )
    finally:
        with engine.begin() as connection:
            connection.execute(
                text("delete from story.activity_selections where run_id = :r"), {"r": run_id}
            )
            connection.execute(
                text("delete from story.command_receipts where receipt_id = :id"),
                {"id": receipt_id},
            )
            connection.execute(text("delete from story.runs where run_id = :r"), {"r": run_id})
        command.upgrade(config, "heads")
