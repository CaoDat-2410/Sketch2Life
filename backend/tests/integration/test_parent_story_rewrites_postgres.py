"""FEAT-066 T-2d: ``story-rewrites`` and the 202 subject confirmation on PostgreSQL.

SRS l.1666 (subject confirmation 202 or a VLM rerun), l.394 and l.1413 (an edited subject reruns the
VLM and returns to ``SUBJECT_REVIEW``), l.1668 and FR-P-07 l.516 (a rewrite of the story, at most
three), l.866 (``STORY_REWRITE_LIMIT_REACHED``), l.1697-1699 (replay and ``STALE_REVISION`` with the
current version), l.864-865 (one 404 for a caller out of scope). Runs only against a disposable
database whose name contains ``be1_acceptance`` and ``frc08_v3_t2d``.

The runs are seeded straight into the Story tables at the point the test needs (a drawing with an
understanding, a confirmed context), because the upload, normalization and analysis steps belong to
T-2a, T-2b and T-2c and have their own PostgreSQL tests. No object storage is used and no provider
is called: the drawing analyzer and the story generator are deterministic doubles.
"""

from __future__ import annotations

import hashlib
import os
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from threading import Barrier
from typing import Any
from uuid import uuid4

import pytest
from fastapi import FastAPI, Header
from fastapi.testclient import TestClient
from sqlalchemy import select, update

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_inputs import (
    DrawingAnalysisFailure,
    DrawingAnalysisResult,
    StoryGenerationFailure,
    StoryGenerationOutcomeUnknown,
    StoryGenerationResult,
    SubjectConfirmOutcome,
)
from sketch2life.application.ports.parent_story_runs import ParentStoryRunError
from sketch2life.application.services.story_output import normalize_story_output
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
    _parent_first_story_request_sha256,
    _sha256_json,
)
from sketch2life.infrastructure.persistence.story_first_start import latest_selection_row
from sketch2life.infrastructure.story_inputs.fixtures import (
    FixtureDrawingAnalyzer,
    FixtureStoryGenerator,
    worker_input_sha256,
)
from sketch2life.infrastructure.story_inputs.runner import ParentInputJobRunner
from sketch2life.infrastructure.story_inputs.story_generation import (
    REWRITE_NEUTRAL_INSTRUCTION_V1,
    ParentStoryRewriteRunner,
)
from sketch2life.infrastructure.story_run_lite import tables as story_tables
from sketch2life.infrastructure.uploads.resolvers import parent_scope_ref
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult
from tests.unit.test_story_output import valid_story

ISSUER = "synthetic-t2d-issuer"
TYPED = "A friendly dragon learns to share"
HINT = "HINT-SENTENCE make the dragon braver"
SUBJECT = "dragon"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class RecordingGenerator:
    """Answers every worker input with a valid draft; records what it was given."""

    def __init__(self) -> None:
        self.inputs: list[dict[str, Any]] = []

    def generate(self, worker_input: Any) -> StoryGenerationResult:
        self.inputs.append(dict(worker_input))
        story = valid_story()
        story["title"] = f"Rồng nhỏ lần {len(self.inputs)}"
        return StoryGenerationResult(story, f"call-{len(self.inputs)}", "fixture-model", "1")


@dataclass
class RewriteApi:
    app: FastAPI
    client: TestClient
    analyzer: FixtureDrawingAnalyzer
    generator: RecordingGenerator
    parent: str
    other_parent: str
    teacher: str

    def sessions(self) -> Any:
        return self.app.state.be1_runtime.session_factory


@pytest.fixture
def api(monkeypatch: pytest.MonkeyPatch) -> Iterator[RewriteApi]:
    database_url = os.environ.get("BE1_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("set BE1_TEST_DATABASE_URL to a disposable PostgreSQL database")
    database_name = database_url.rsplit("/", 1)[-1]
    if "be1_acceptance" not in database_name or "frc08_v3_t2d" not in database_name:
        pytest.fail("BE1_TEST_DATABASE_URL must be a disposable frc08_v3_t2d*be1_acceptance db")
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", database_url)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("SKETCH2LIFE_AUTH_PROVIDER", "development")
    monkeypatch.setenv("SKETCH2LIFE_AI_PROVIDER", "disabled")
    # These cases pin the v1 (Qwen3.5) story input; the Qwen3.8 default has its own tests.
    monkeypatch.delenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", raising=False)
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    app = create_app()
    runtime = app.state.be1_runtime
    if runtime.engine is None or runtime.session_factory is None:
        pytest.fail("PostgreSQL runtime did not initialize")
    token = uuid4().hex[:8]
    parent, other_parent = f"synthetic-t2d-parent-{token}", f"synthetic-t2d-parent2-{token}"
    teacher = f"synthetic-t2d-teacher-{token}"
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

    app.dependency_overrides[get_verified_adult] = verified
    try:
        with TestClient(app) as client:
            yield RewriteApi(
                app,
                client,
                FixtureDrawingAnalyzer(),
                RecordingGenerator(),
                parent,
                other_parent,
                teacher,
            )
    finally:
        app.dependency_overrides.clear()
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


def wire(response: Any) -> tuple[int, dict[str, Any]]:
    body = response.json()
    return response.status_code, {
        k: v for k, v in body.items() if k not in {"request_id", "correlation_id"}
    }


@dataclass
class Seeded:
    run_id: str
    drawing_input_id: str
    derived_sha256: str


@dataclass
class FailedFirstStorySeed:
    run_id: str
    selection_expected_revision: int
    activity_ref: dict[str, Any]
    old_selection_key: str


def seed_run(
    api: RewriteApi,
    owner: str,
    *,
    run_state: str = "SUBJECT_REVIEW",
    job_state: str = "SUCCEEDED",
    hold_slot: bool = True,
    suggested: str = SUBJECT,
) -> Seeded:
    """A run with a confirmed context, one drawing and its understanding revision 1."""
    run_id = str(uuid4())
    now = datetime.now(UTC)
    scope_ref = parent_scope_ref(principal_of(owner))
    token = uuid4().hex
    derived_sha = sha(f"derived-{run_id}".encode())
    input_one, input_two = str(uuid4()), str(uuid4())
    context = {
        "schema_version": "sketch2life.parent-context.v1",
        "profile_revision_ref": str(uuid4()),
        "age_months": 60,
        "interests_summary": "",
        "topic": "synthetic",
        "adult_confirmed_idea": TYPED,
    }
    candidate = {
        "candidate_subject": suggested,
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
                run_state=run_state,
                job_state=job_state,
                revision=5,
                version=5,
                current_input_revision=2,
                understanding_revision=1,
                subject_label=suggested,
                confidence=0.9,
                active_owner_parent_account_id=str(account_id) if hold_slot else None,
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
            "context_snapshot_sha256": "c" * 64,
            "context_confirmed_by": scope_ref,
            "context_confirmed_at": now,
            "created_at": now,
        }
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
                derived_sha256=derived_sha,
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
                subject_label=suggested,
                confidence=0.9,
                canonical_result_sha256="d" * 64,
                result_snapshot={"result": candidate},
                created_at=now,
            )
        )
    return Seeded(run_id, input_two, derived_sha)


def run_row(api: RewriteApi, run_id: str) -> Any:
    with api.sessions()() as db:
        return (
            db.execute(
                select(story_tables.story_runs).where(story_tables.story_runs.c.run_id == run_id)
            )
            .mappings()
            .one()
        )


def states(api: RewriteApi, run_id: str) -> tuple[str, str | None]:
    row = run_row(api, run_id)
    return str(row["run_state"]), row["job_state"]


def story_rows(api: RewriteApi, run_id: str) -> list[Any]:
    table = story_tables.story_revisions
    with api.sessions()() as db:
        return list(
            db.execute(select(table).where(table.c.run_id == run_id).order_by(table.c.revision_no))
            .mappings()
            .all()
        )


def understanding_rows(api: RewriteApi, run_id: str) -> list[Any]:
    table = story_tables.understanding_revisions
    with api.sessions()() as db:
        return list(
            db.execute(select(table).where(table.c.run_id == run_id).order_by(table.c.revision_no))
            .mappings()
            .all()
        )


def receipt_rows(api: RewriteApi, run_id: str, operation: str) -> list[Any]:
    table = story_tables.story_command_receipts
    with api.sessions()() as db:
        return list(
            db.execute(
                select(table).where(table.c.resource_ref == run_id, table.c.operation == operation)
            )
            .mappings()
            .all()
        )


def decision_rows(api: RewriteApi, run_id: str) -> list[Any]:
    table = story_tables.review_decisions
    with api.sessions()() as db:
        return list(db.execute(select(table).where(table.c.run_id == run_id)).mappings().all())


def code_of(response: Any) -> str:
    return str(response.json()["code"])


def subject_route(
    api: RewriteApi,
    owner: str,
    run_id: str,
    *,
    subject: str = SUBJECT,
    revision: int = 1,
    key: str | None = None,
) -> Any:
    return api.client.post(
        f"/v1/story-runs/{run_id}/subject-confirmation",
        json={"expected_understanding_revision": revision, "confirmed_subject": subject},
        headers=headers(owner, key or uuid4().hex),
    )


def rewrite(
    api: RewriteApi,
    owner: str,
    run_id: str,
    *,
    revision: int | None = None,
    key: str | None = None,
    **body: Any,
) -> Any:
    if revision is None:
        revision = int(story_rows(api, run_id)[-1]["revision_no"])
    return api.client.post(
        f"/v1/story-runs/{run_id}/story-rewrites",
        json={"expected_story_revision": revision, **body},
        headers=headers(owner, key or uuid4().hex),
    )


def cancel(api: RewriteApi, owner: str, run_id: str) -> Any:
    return api.client.post(
        f"/v1/story-runs/{run_id}/cancel",
        json={"expected_revision": int(run_row(api, run_id)["revision"])},
        headers=headers(owner, uuid4().hex),
    )


def first_story(api: RewriteApi, owner: str, run_id: str, *, key: str | None = None) -> None:
    """Confirm the subject, then make the first story the way the legacy route does."""
    assert subject_route(api, owner, run_id).status_code == 202
    with api.sessions()() as db:
        repository = SqlParentStoryRunRepository(db)
        reservation = repository.reserve_story_revision(
            principal=principal_of(owner),
            run_id=run_id,
            expected_understanding_revision=1,
            rewrite_instruction=None,
            idempotency_key=key or uuid4().hex,
            story_revision_id=str(uuid4()),
            model_id="synthetic-model",
            model_revision="1",
            prompt_version="synthetic-prompt",
        )
        story, digest = normalize_story_output(valid_story(), confirmed_subject=SUBJECT)
        repository.complete_story_revision(
            reservation=reservation,
            principal=principal_of(owner),
            story=story,
            story_sha256=digest,
            provider_call_id="legacy-call",
            model_id="synthetic-model",
            model_revision="1",
        )
    assert states(api, run_id) == ("SCRIPT_REVIEW", "SUCCEEDED")


def story_run(api: RewriteApi, owner: str | None = None, *, hold_slot: bool = True) -> str:
    owner = owner or api.parent
    seeded = seed_run(api, owner, hold_slot=hold_slot)
    first_story(api, owner, seeded.run_id)
    return seeded.run_id


def _append_activity_selection(
    db: Any,
    owner: str,
    run_id: str,
    *,
    key: str,
    selection_no: int,
    created_at: datetime,
    activity_snapshot: dict[str, Any] | None = None,
    activity_snapshot_sha256: str | None = None,
) -> tuple[int, dict[str, Any]]:
    principal = principal_of(owner)
    actor_scope_ref = parent_scope_ref(principal)
    activity_ref = {
        "lesson_id": str(uuid4()),
        "version_id": str(uuid4()),
        "content_sha256": "f" * 64,
        "activity_index": 0,
    }
    snapshot = activity_snapshot or {
        "schema": "sketch2life.parent-activity-pin.v1",
        "activity_ref": activity_ref,
        "title": "Synthetic plant activity",
        "objective": "Notice leaves",
        "materials_text": "",
        "preparation_text": "",
        "instructions_text": "Look closely",
        "observation_notes": "",
        "safety_notes": "Adult supervision",
        "activity_kind": "outdoor",
        "source": "PUBLIC",
        "lesson_title": "Synthetic lesson",
        "lesson_topic": "Synthetic topic",
        "selected_at": created_at.isoformat(),
    }
    if activity_snapshot is not None:
        activity_ref = dict(activity_snapshot["activity_ref"])
    run = db.execute(
        select(story_tables.story_runs).where(story_tables.story_runs.c.run_id == run_id)
    ).mappings().one()
    expected_revision = int(run["revision"])
    receipt_id = str(uuid4())
    new_version = int(run["version"]) + 1
    key_hash = sha(key.encode("utf-8"))
    fingerprint = _sha256_json(
        {"expected_revision": expected_revision, "activity_ref": activity_ref}
    )
    db.execute(
        story_tables.story_command_receipts.insert().values(
            receipt_id=receipt_id,
            actor_scope_kind="PARENT_ACCOUNT",
            actor_scope_ref=actor_scope_ref,
            operation="SELECT_ACTIVITY",
            idempotency_scope_kind="STORY_RUN",
            idempotency_scope_ref=run_id,
            idempotency_key_sha256=key_hash,
            request_fingerprint_sha256=fingerprint,
            state="FINAL",
            response_status=200,
            response_resource_version=new_version,
            response_body={
                "selection_no": selection_no,
                "activity_ref": activity_ref,
                "understanding_revision": 1,
            },
            resource_ref=run_id,
            resource_version=new_version,
            state_version=1,
            created_at=created_at,
            finalized_at=created_at,
        )
    )
    db.execute(
        story_tables.activity_selections.insert().values(
            selection_id=str(uuid4()),
            run_id=run_id,
            selection_no=selection_no,
            target_understanding_revision=1,
            source_kind="LESSON_ACTIVITY",
            lesson_id=activity_ref["lesson_id"],
            version_id=activity_ref["version_id"],
            content_sha256=activity_ref["content_sha256"],
            activity_index=activity_ref["activity_index"],
            activity_snapshot=snapshot,
            activity_snapshot_sha256=(
                activity_snapshot_sha256 or _sha256_json(snapshot)
            ),
            command_receipt_id=receipt_id,
            actor_scope_kind="PARENT_ACCOUNT",
            actor_scope_ref=actor_scope_ref,
            created_at=created_at,
        )
    )
    return expected_revision, activity_ref


def seed_failed_first_story(
    api: RewriteApi,
    owner: str | None = None,
    *,
    use_first_story_producer: bool = False,
) -> FailedFirstStorySeed:
    """Create an eligible failed first story and its activity receipt.

    The default helper reconstructs the first-story hash; the producer option uses the real
    FirstStoryStarter so a recovery test can catch drift in that input.
    """
    owner = owner or api.parent
    seeded = seed_run(api, owner)
    assert subject_route(api, owner, seeded.run_id).status_code == 202
    now = datetime.now(UTC)
    selection_time = now - timedelta(seconds=2)
    old_selection_key = f"first-story-selection-{uuid4().hex}"
    with api.sessions().begin() as db:
        selection_expected_revision, activity_ref = _append_activity_selection(
            db,
            owner,
            seeded.run_id,
            key=old_selection_key,
            selection_no=1,
            created_at=selection_time,
        )
    reservation = None
    with api.sessions().begin() as db:
        input_table = story_tables.run_inputs
        input_row = db.execute(
            select(input_table).where(
                input_table.c.run_id == seeded.run_id,
                input_table.c.input_revision == 2,
            )
        ).mappings().one()
        context = dict(input_row["context_snapshot"])
        context_hash = _sha256_json(context)
        db.execute(
            update(input_table)
            .where(input_table.c.run_input_id == input_row["run_input_id"])
            .values(context_snapshot_sha256=context_hash)
        )
        understanding_table = story_tables.understanding_revisions
        understanding = db.execute(
            select(understanding_table).where(
                understanding_table.c.run_id == seeded.run_id,
                understanding_table.c.revision_no == 1,
            )
        ).mappings().one()
        understanding_hash = _sha256_json(understanding["result_snapshot"])
        db.execute(
            update(understanding_table)
            .where(
                understanding_table.c.understanding_revision_id
                == understanding["understanding_revision_id"]
            )
            .values(canonical_result_sha256=understanding_hash)
        )
        run_table = story_tables.story_runs
        db.execute(
            update(run_table)
            .where(run_table.c.run_id == seeded.run_id)
            .values(result_sha256=understanding_hash)
        )
        run = db.execute(
            select(run_table).where(run_table.c.run_id == seeded.run_id)
        ).mappings().one()
        input_row = db.execute(
            select(input_table).where(input_table.c.run_input_id == input_row["run_input_id"])
        ).mappings().one()
        understanding = db.execute(
            select(understanding_table).where(
                understanding_table.c.understanding_revision_id
                == understanding["understanding_revision_id"]
            )
        ).mappings().one()
        selection = latest_selection_row(db, seeded.run_id, 1)
        assert selection is not None
        repository = SqlParentStoryRunRepository(db)
        if use_first_story_producer:
            reservation = repository._first_story_starter().start_if_ready(
                seeded.run_id,
                principal_of(owner),
                datetime.now(UTC),
            )
            assert reservation is not None
        else:
            _, _, idea_text, visible_features = repository._story_generation_basis(
                principal=principal_of(owner),
                run=run,
                expected_understanding_revision=1,
                subject_error=(422, "SUBJECT_NOT_CONFIRMED"),
            )
            request_hash = _parent_first_story_request_sha256(
                run=run,
                input_row=input_row,
                understanding_revision=1,
                idea_text=idea_text,
                visible_features=visible_features,
                selection=selection,
            )
            failed_at = datetime.now(UTC)
            db.execute(
                story_tables.story_revisions.insert().values(
                    story_revision_id=str(uuid4()),
                    run_id=seeded.run_id,
                    revision_no=1,
                    status="FAILED",
                    source_asset_sha256=input_row["original_sha256"],
                    understanding_revision=1,
                    context_revision=int(input_row["context_revision"]),
                    schema_version="sketch2life.story-revision.v1",
                    prompt_version="parent-story-rewrite.v1",
                    model_id="story-generator-port",
                    model_revision="unassigned",
                    request_sha256=request_hash,
                    created_at=failed_at,
                )
            )
            db.execute(
                update(run_table)
                .where(run_table.c.run_id == seeded.run_id)
                .values(
                    run_state="FAILED",
                    job_state="FAILED",
                    retryable=False,
                    error_code="STORY_OUTPUT_INVALID",
                    active_owner_parent_account_id=None,
                    version=int(run["version"]) + 3,
                    revision=int(run["revision"]) + 3,
                    finished_at=failed_at,
                    adult_wait_started_at=None,
                    updated_at=failed_at,
                )
            )
    if reservation is not None:
        with api.sessions()() as db:
            SqlParentStoryRunRepository(db).fail_story_revision(
                principal=principal_of(owner),
                reservation=reservation,
                error_code="STORY_OUTPUT_INVALID",
                outcome_unknown=False,
            )
    return FailedFirstStorySeed(
        seeded.run_id,
        selection_expected_revision,
        activity_ref,
        old_selection_key,
    )


def compose_generator(api: RewriteApi) -> None:
    api.app.state.story_generator = api.generator


def compose_analyzer(api: RewriteApi) -> None:
    api.app.state.drawing_analyzer = api.analyzer


# ============================================================================ story-rewrites
def test_three_rewrites_are_accepted_and_the_fourth_is_the_limit(api: RewriteApi) -> None:
    compose_generator(api)
    run_id = story_run(api)
    for number in (2, 3, 4):
        response = rewrite(api, api.parent, run_id, revision=number - 1)
        status, body = wire(response)
        assert status == 202, response.text
        assert body["story_revision_no"] == number and body["run_state"] == "SCRIPT_GENERATING"
        assert response.headers["Content-Location"] == f"/v1/story-runs/{run_id}"
        assert "job" not in body
        # the generator ran after the response: the new draft waits for the adult
        assert states(api, run_id) == ("SCRIPT_REVIEW", "SUCCEEDED")
        rows = story_rows(api, run_id)
        assert [row["status"] for row in rows] == ["SUPERSEDED"] * (number - 1) + ["DRAFT"]
        assert rows[-1]["title"] == f"Rồng nhỏ lần {number - 1}"
        assert rows[-1]["model_id"] == "fixture-model" and rows[-1]["provider_call_id"]
    assert [row["revision_no"] for row in story_rows(api, run_id)] == [1, 2, 3, 4]
    assert len(api.generator.inputs) == 3
    # the client holds revision 4 and asks again: the real reason, not a validation error
    refused = rewrite(api, api.parent, run_id, revision=4)
    assert refused.status_code == 409 and code_of(refused) == "STORY_REWRITE_LIMIT_REACHED"
    # a stale client at the limit learns the same real reason
    assert code_of(rewrite(api, api.parent, run_id, revision=2)) == "STORY_REWRITE_LIMIT_REACHED"
    assert len(story_rows(api, run_id)) == 4 and len(api.generator.inputs) == 3
    assert rewrite(api, api.parent, run_id, revision=5).status_code == 400


def test_the_worker_gets_the_constant_instruction_and_the_hint_only_as_data(
    api: RewriteApi,
) -> None:
    compose_generator(api)
    run_id = story_run(api)
    assert rewrite(api, api.parent, run_id, hint=f"  {HINT}  ").status_code == 202
    assert rewrite(api, api.parent, run_id).status_code == 202  # no hint
    with_hint, without_hint = api.generator.inputs
    for worker_input in (with_hint, without_hint):
        assert worker_input["rewrite_instruction"] == REWRITE_NEUTRAL_INSTRUCTION_V1
        assert worker_input["rewrite_instruction_version"] == "rewrite-neutral.v1"
        assert worker_input["confirmed_subject"] == SUBJECT
        assert worker_input["adult_confirmed_idea"] == TYPED
        assert worker_input["child_age_months"] == 60
        assert worker_input["visible_features"] == ["wings", "tail"]
        assert HINT not in worker_input["rewrite_instruction"]
    assert with_hint["adult_rewrite_hint"] == HINT
    assert without_hint["adult_rewrite_hint"] is None
    # the receipt and the revision rows hold no hint text
    assert HINT not in str([dict(row) for row in story_rows(api, run_id)])
    assert HINT not in str(
        [dict(row) for row in receipt_rows(api, run_id, "GENERATE_STORY_REVISION")]
    )


def test_a_stale_revision_or_hash_is_409_with_the_current_version(api: RewriteApi) -> None:
    compose_generator(api)
    run_id = story_run(api)
    assert rewrite(api, api.parent, run_id, revision=1).status_code == 202  # now at revision 2
    stale = rewrite(api, api.parent, run_id, revision=1)
    assert stale.status_code == 409 and code_of(stale) == "STALE_REVISION"
    assert stale.json()["current_version"] == 2
    wrong_hash = rewrite(api, api.parent, run_id, revision=2, expected_story_sha256="0" * 64)
    assert wrong_hash.status_code == 409 and code_of(wrong_hash) == "STALE_REVISION"
    assert wrong_hash.json()["current_version"] == 2
    current = story_rows(api, run_id)[-1]["story_sha256"]
    good = rewrite(api, api.parent, run_id, revision=2, expected_story_sha256=current)
    assert good.status_code == 202
    assert [row["revision_no"] for row in story_rows(api, run_id)] == [1, 2, 3]


def test_the_replay_while_generating_and_after_completion_returns_the_stored_202(
    api: RewriteApi,
) -> None:
    run_id = story_run(api)  # no generator composed: the accepted rewrite waits
    first = rewrite(api, api.parent, run_id, revision=1, key="rewrite-key", hint=HINT)
    assert first.status_code == 202
    assert states(api, run_id) == ("SCRIPT_GENERATING", "QUEUED")
    receipt = next(
        row
        for row in receipt_rows(api, run_id, "GENERATE_STORY_REVISION")
        if row["response_status"] == 202
    )
    assert receipt["state"] == "FINAL" and receipt["response_status"] == 202
    # the lost-202 retry meets a run that is still generating
    again = rewrite(api, api.parent, run_id, revision=1, key="rewrite-key", hint=HINT)
    assert wire(again) == wire(first)
    assert len(story_rows(api, run_id)) == 2
    # another key meets the state: one rewrite at a time
    other = rewrite(api, api.parent, run_id, revision=2)
    assert other.status_code == 409 and code_of(other) == "INVALID_STATE_TRANSITION"
    # a new body under the same key is a different request
    reused = rewrite(api, api.parent, run_id, revision=1, key="rewrite-key", hint="other hint")
    assert reused.status_code == 400 and code_of(reused) == "INVALID_IDEMPOTENCY_KEY"
    assert len(story_rows(api, run_id)) == 2


def test_the_replay_after_the_story_arrived_is_the_same_body(api: RewriteApi) -> None:
    compose_generator(api)
    run_id = story_run(api)
    first = rewrite(api, api.parent, run_id, revision=1, key="rewrite-key")
    assert first.status_code == 202 and states(api, run_id)[0] == "SCRIPT_REVIEW"
    again = rewrite(api, api.parent, run_id, revision=1, key="rewrite-key")
    assert wire(again) == wire(first)
    assert wire(first)[1]["run_state"] == "SCRIPT_GENERATING"  # the stored answer, as first given
    assert len(story_rows(api, run_id)) == 2 and len(api.generator.inputs) == 1
    assert len(receipt_rows(api, run_id, "GENERATE_STORY_REVISION")) == 2  # first story + rewrite


def test_the_legacy_replay_still_works_and_a_key_is_not_shared_between_the_routes(
    api: RewriteApi,
) -> None:
    compose_generator(api)
    seeded = seed_run(api, api.parent)
    first_story(api, api.parent, seeded.run_id, key="shared-key")
    with api.sessions()() as db:
        replay = SqlParentStoryRunRepository(db).reserve_story_revision(
            principal=principal_of(api.parent),
            run_id=seeded.run_id,
            expected_understanding_revision=1,
            rewrite_instruction=None,
            idempotency_key="shared-key",
            story_revision_id=str(uuid4()),
            model_id="synthetic-model",
            model_revision="1",
            prompt_version="synthetic-prompt",
        )
    assert replay.replayed is True and replay.replay_body is not None
    assert replay.replay_body["story_sha256"]
    # the same key on the SRS route is another request: 400, nothing written
    clash = rewrite(api, api.parent, seeded.run_id, revision=1, key="shared-key")
    assert clash.status_code == 400 and code_of(clash) == "INVALID_IDEMPOTENCY_KEY"
    assert len(story_rows(api, seeded.run_id)) == 1
    # and a hint-less rewrite through the legacy path stays refused (the SRS route owns it)
    with api.sessions()() as db, pytest.raises(ParentStoryRunError) as refused:
        SqlParentStoryRunRepository(db).reserve_story_revision(
            principal=principal_of(api.parent),
            run_id=seeded.run_id,
            expected_understanding_revision=1,
            rewrite_instruction=None,
            idempotency_key=uuid4().hex,
            story_revision_id=str(uuid4()),
            model_id="synthetic-model",
            model_revision="1",
            prompt_version="synthetic-prompt",
        )
    assert refused.value.code == "PARENT_STORY_REWRITE_NOT_ALLOWED"


def test_two_rewrites_racing_leave_one_winner(api: RewriteApi) -> None:
    for _round in range(3):
        run_id = story_run(api, hold_slot=False)
        barrier = Barrier(2)

        def send(run: str = run_id, gate: Barrier = barrier) -> Any:
            gate.wait(timeout=30)
            return rewrite(api, api.parent, run, revision=1)

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _i: send(), range(2)))
        statuses = sorted(response.status_code for response in results)
        assert statuses == [202, 409], [response.text for response in results]
        loser = next(response for response in results if response.status_code == 409)
        assert code_of(loser) in {"INVALID_STATE_TRANSITION", "STALE_REVISION"}
        assert [row["revision_no"] for row in story_rows(api, run_id)] == [1, 2]


def test_two_requests_with_the_same_key_are_one_command_and_one_replay(api: RewriteApi) -> None:
    run_id = story_run(api)
    barrier = Barrier(2)

    def send() -> Any:
        barrier.wait(timeout=30)
        return rewrite(api, api.parent, run_id, revision=1, key="race-key")

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _i: send(), range(2)))
    assert [response.status_code for response in results] == [202, 202]
    assert wire(results[0]) == wire(results[1])
    assert len(story_rows(api, run_id)) == 2


def test_a_rewrite_needs_a_story_in_review(api: RewriteApi) -> None:
    seeded = seed_run(api, api.parent)  # SUBJECT_REVIEW: no story yet
    refused = rewrite(api, api.parent, seeded.run_id, revision=1)
    assert refused.status_code == 409 and code_of(refused) == "INVALID_STATE_TRANSITION"
    assert subject_route(api, api.parent, seeded.run_id).status_code == 202  # PREPARATION_REVIEW
    refused = rewrite(api, api.parent, seeded.run_id, revision=1)
    assert refused.status_code == 409 and code_of(refused) == "INVALID_STATE_TRANSITION"
    assert story_rows(api, seeded.run_id) == []


def test_a_wrong_role_and_a_foreign_run_are_the_same_404(api: RewriteApi) -> None:
    compose_generator(api)
    run_id = story_run(api)
    reference = wire(rewrite(api, api.parent, str(uuid4()), revision=1))
    assert reference[0] == 404 and reference[1]["code"] == "RESOURCE_NOT_FOUND"
    for caller in (api.other_parent, api.teacher):
        assert wire(rewrite(api, caller, run_id, revision=1)) == reference
        assert wire(subject_route(api, caller, run_id)) == reference
    unknown = wire(subject_route(api, api.parent, str(uuid4())))
    assert unknown == reference
    outsider = api.client.post(
        f"/v1/story-runs/{run_id}/story-rewrites",
        json={"expected_story_revision": 1},
        headers=headers("synthetic-unknown-subject", uuid4().hex),
    )
    assert wire(outsider) == reference
    assert len(story_rows(api, run_id)) == 1  # nothing was written


def test_a_run_cancelled_while_waiting_or_generating_is_never_completed(api: RewriteApi) -> None:
    # (a) no worker composed: the run waits, the adult cancels
    run_id = story_run(api)
    assert rewrite(api, api.parent, run_id, revision=1, key="wait-key").status_code == 202
    assert states(api, run_id) == ("SCRIPT_GENERATING", "QUEUED")
    assert cancel(api, api.parent, run_id).status_code == 202
    assert states(api, run_id)[0] == "DELETE_PENDING"
    fresh = rewrite(api, api.parent, run_id, revision=1)
    assert fresh.status_code == 409 and code_of(fresh) == "INVALID_STATE_TRANSITION"
    replay = rewrite(api, api.parent, run_id, revision=1, key="wait-key")
    assert replay.status_code == 202 and set(replay.json()) == {"request_id", "lifecycle"}
    assert replay.json()["lifecycle"]["run_state"] == "DELETE_PENDING"
    assert "story_revision_no" not in replay.text

    # (b) the run is cancelled while the generator works: the late draft changes nothing
    second = story_run(api, hold_slot=False)

    class CancellingGenerator(RecordingGenerator):
        def generate(self, worker_input: Any) -> StoryGenerationResult:
            assert cancel(api, api.parent, second).status_code == 202
            return super().generate(worker_input)

    api.app.state.story_generator = CancellingGenerator()
    assert rewrite(api, api.parent, second, revision=1).status_code == 202
    assert states(api, second)[0] == "DELETE_PENDING"
    # T-2d-fix D3: the previous story is superseded only when the new one completes
    assert [row["status"] for row in story_rows(api, second)] == ["DRAFT", "GENERATING"]

    # (c) a stale start does not call the generator at all
    third = story_run(api, hold_slot=False)
    with api.sessions()() as db:
        account_id = db.scalar(
            select(AdultIdentityModel.account_id).where(
                AdultIdentityModel.subject == api.parent
            )
        )
        outcome = SqlParentStoryRunRepository(db).reserve_story_rewrite(
            principal=principal_of(api.parent),
            account_id=str(account_id),
            run_id=third,
            idempotency_key=uuid4().hex,
            expected_story_revision=1,
            expected_story_sha256=None,
            hint=None,
            story_revision_id=str(uuid4()),
            model_id="story-generator-port",
            model_revision="unassigned",
            prompt_version="parent-story-rewrite.v1",
            instruction_version="rewrite-neutral.v1",
            instruction=REWRITE_NEUTRAL_INSTRUCTION_V1,
        )
    assert outcome.reservation is not None
    assert cancel(api, api.parent, third).status_code == 202
    generator = RecordingGenerator()
    ParentStoryRewriteRunner(api.sessions(), generator).run(
        principal_of(api.parent), outcome.reservation
    )
    assert generator.inputs == [] and states(api, third)[0] == "DELETE_PENDING"


def test_the_runner_records_each_failure_with_its_code(api: RewriteApi) -> None:
    class Failing:
        def __init__(self, error: Exception) -> None:
            self.error = error

        def generate(self, worker_input: Any) -> Any:
            raise self.error

    # T-2d-fix D1: a known failure of a rewrite returns to the previous story (its row is the last
    # one left, still a draft); an unknown outcome keeps the attempt's row for reconciliation
    for error, run_state, job_state, revision_state, code in (
        (
            StoryGenerationFailure(),
            "SCRIPT_REVIEW",
            "FAILED",
            "DRAFT",
            "STORY_GENERATION_UNAVAILABLE",
        ),
        (
            StoryGenerationOutcomeUnknown(),
            "SCRIPT_GENERATION_UNKNOWN",
            "AWAITING_RECONCILIATION",
            "AWAITING_RECONCILIATION",
            "STORY_OUTCOME_UNKNOWN",
        ),
        (
            RuntimeError("defect"),
            "SCRIPT_GENERATION_UNKNOWN",
            "AWAITING_RECONCILIATION",
            "AWAITING_RECONCILIATION",
            "STORY_OUTCOME_UNKNOWN",
        ),
    ):
        api.app.state.story_generator = Failing(error)
        run_id = story_run(api, hold_slot=False)
        response = rewrite(api, api.parent, run_id, revision=1, key="failing-key")
        assert response.status_code == 202  # the answer was given before the work
        assert states(api, run_id) == (run_state, job_state)
        row = run_row(api, run_id)
        assert row["error_code"] == code
        assert story_rows(api, run_id)[-1]["status"] == revision_state
        # the replay is still the stored 202 whatever the work did
        assert wire(rewrite(api, api.parent, run_id, revision=1, key="failing-key")) == wire(
            response
        )

    # an invalid draft is stored as a failure, not as a story
    class Broken(RecordingGenerator):
        def generate(self, worker_input: Any) -> StoryGenerationResult:
            return StoryGenerationResult({"title": "x"}, "call-x", "fixture-model", "1")

    api.app.state.story_generator = Broken()
    run_id = story_run(api, hold_slot=False)
    assert rewrite(api, api.parent, run_id, revision=1).status_code == 202
    assert states(api, run_id) == ("SCRIPT_REVIEW", "FAILED")
    assert run_row(api, run_id)["error_code"] == "STORY_OUTPUT_INVALID"
    rows = story_rows(api, run_id)
    assert [row["status"] for row in rows] == ["DRAFT"] and rows[-1]["story_sha256"] is not None


def test_failed_first_story_recovers_with_a_new_receipt_and_preserves_the_old_receipt(
    api: RewriteApi,
) -> None:
    compose_generator(api)
    seeded = seed_failed_first_story(api)
    failed_revision = dict(story_rows(api, seeded.run_id)[0])
    old_receipt = dict(receipt_rows(api, seeded.run_id, "SELECT_ACTIVITY")[0])

    response = rewrite(
        api,
        api.parent,
        seeded.run_id,
        revision=1,
        key="rev73-new-recovery-key",
    )

    status, body = wire(response)
    assert status == 202 and body["story_revision_no"] == 2
    assert body["run_state"] == "SCRIPT_GENERATING"
    assert states(api, seeded.run_id) == ("SCRIPT_REVIEW", "SUCCEEDED")
    rows = story_rows(api, seeded.run_id)
    assert [row["status"] for row in rows] == ["FAILED", "DRAFT"]
    assert dict(rows[0]) == failed_revision
    recovery_receipts = receipt_rows(api, seeded.run_id, "GENERATE_STORY_REVISION")
    assert len(recovery_receipts) == 1
    assert recovery_receipts[0]["idempotency_key_sha256"] == sha(
        b"rev73-new-recovery-key"
    )
    assert dict(receipt_rows(api, seeded.run_id, "SELECT_ACTIVITY")[0]) == old_receipt
    run = run_row(api, seeded.run_id)
    with api.sessions()() as db:
        account_id = db.scalar(
            select(AdultIdentityModel.account_id).where(
                AdultIdentityModel.subject == api.parent
            )
        )
    assert run["active_owner_parent_account_id"] == str(account_id)

    # The original selection command still replays its own receipt under its original key.
    selection_replay = api.client.post(
        f"/v1/story-runs/{seeded.run_id}/activity-selection",
        json={
            "expected_revision": seeded.selection_expected_revision,
            "activity": seeded.activity_ref,
        },
        headers=headers(api.parent, seeded.old_selection_key),
    )
    assert selection_replay.status_code == 200
    assert selection_replay.json()["story_run"]["run_state"] == "SCRIPT_REVIEW"
    assert dict(receipt_rows(api, seeded.run_id, "SELECT_ACTIVITY")[0]) == old_receipt

    replay = rewrite(
        api,
        api.parent,
        seeded.run_id,
        revision=1,
        key="rev73-new-recovery-key",
    )
    assert wire(replay) == wire(response)
    assert len(api.generator.inputs) == 1


def test_recovery_hash_matches_the_real_first_story_producer(api: RewriteApi) -> None:
    compose_generator(api)
    seeded = seed_failed_first_story(api, use_first_story_producer=True)
    first_revision = story_rows(api, seeded.run_id)[0]
    assert first_revision["status"] == "FAILED"
    assert first_revision["request_sha256"]

    # A first story created by the legacy reserve_story_revision route (schema v1) fails this hash
    # and is refused on purpose.
    response = rewrite(
        api,
        api.parent,
        seeded.run_id,
        revision=1,
        key="producer-hash-recovery",
    )

    assert response.status_code == 202, response.text
    assert states(api, seeded.run_id) == ("SCRIPT_REVIEW", "SUCCEEDED")
    assert [row["status"] for row in story_rows(api, seeded.run_id)] == ["FAILED", "DRAFT"]


def test_recovery_consumes_one_of_the_three_rewrite_slots(api: RewriteApi) -> None:
    compose_generator(api)
    seeded = seed_failed_first_story(api)

    assert rewrite(
        api,
        api.parent,
        seeded.run_id,
        revision=1,
        key="recovery-slot-one",
    ).status_code == 202
    for revision in (2, 3):
        response = rewrite(api, api.parent, seeded.run_id, revision=revision)
        assert response.status_code == 202, response.text
        assert states(api, seeded.run_id) == ("SCRIPT_REVIEW", "SUCCEEDED")
    assert [row["revision_no"] for row in story_rows(api, seeded.run_id)] == [1, 2, 3, 4]
    assert code_of(rewrite(api, api.parent, seeded.run_id, revision=4)) == (
        "STORY_REWRITE_LIMIT_REACHED"
    )
    assert len(api.generator.inputs) == 3


def test_a_second_quality_failure_is_terminal_and_releases_the_parent_lock(
    api: RewriteApi,
) -> None:
    class Broken(RecordingGenerator):
        def generate(self, worker_input: Any) -> StoryGenerationResult:
            return StoryGenerationResult({"title": "x"}, "call-x", "fixture-model", "1")

    api.app.state.story_generator = Broken()
    seeded = seed_failed_first_story(api)
    response = rewrite(api, api.parent, seeded.run_id, revision=1, key="recovery-fails")
    assert response.status_code == 202
    assert states(api, seeded.run_id) == ("FAILED", "FAILED")
    assert run_row(api, seeded.run_id)["error_code"] == "STORY_OUTPUT_INVALID"
    assert run_row(api, seeded.run_id)["active_owner_parent_account_id"] is None
    assert [row["status"] for row in story_rows(api, seeded.run_id)] == ["FAILED", "FAILED"]
    refused = rewrite(api, api.parent, seeded.run_id, revision=2, key="second-recovery")
    assert refused.status_code == 409
    assert len(story_rows(api, seeded.run_id)) == 2

    # The released lock allows the same Parent to begin another run.
    next_run = story_run(api, api.parent)
    assert run_row(api, next_run)["active_owner_parent_account_id"] is not None


@pytest.mark.parametrize(
    ("run_state", "job_state", "error_code", "revision_state"),
    [
        ("FAILED", "FAILED", "STORY_GENERATION_UNAVAILABLE", "FAILED"),
        ("FAILED", "FAILED", "SAFETY_BLOCKED", "FAILED"),
        ("FAILED", "FAILED", "CONSENT_REVOKED", "FAILED"),
        (
            "SCRIPT_GENERATION_UNKNOWN",
            "AWAITING_RECONCILIATION",
            "STORY_OUTCOME_UNKNOWN",
            "AWAITING_RECONCILIATION",
        ),
        ("ABANDONED", "FAILED", "STORY_OUTPUT_INVALID", "FAILED"),
        ("DELETE_PENDING", "FAILED", "STORY_OUTPUT_INVALID", "FAILED"),
    ],
)
def test_non_quality_unknown_abandoned_and_purging_runs_stay_terminal(
    api: RewriteApi,
    run_state: str,
    job_state: str,
    error_code: str,
    revision_state: str,
) -> None:
    seeded = seed_failed_first_story(api)
    with api.sessions().begin() as db:
        db.execute(
            update(story_tables.story_runs)
            .where(story_tables.story_runs.c.run_id == seeded.run_id)
            .values(run_state=run_state, job_state=job_state, error_code=error_code)
        )
        db.execute(
            update(story_tables.story_revisions)
            .where(
                story_tables.story_revisions.c.run_id == seeded.run_id,
                story_tables.story_revisions.c.revision_no == 1,
            )
            .values(status=revision_state)
        )

    response = rewrite(api, api.parent, seeded.run_id, revision=1, key="terminal-recovery")

    assert response.status_code >= 400
    assert [row["revision_no"] for row in story_rows(api, seeded.run_id)] == [1]
    assert receipt_rows(api, seeded.run_id, "GENERATE_STORY_REVISION") == []


@pytest.mark.parametrize(
    "stale_field",
    [
        "context",
        "context_hash",
        "subject",
        "understanding",
        "understanding_hash",
        "drawing",
        "activity",
        "activity_hash",
    ],
)
def test_stale_first_story_generation_inputs_refuse_recovery(
    api: RewriteApi,
    stale_field: str,
) -> None:
    seeded = seed_failed_first_story(api)
    with api.sessions().begin() as db:
        input_row = db.execute(
            select(story_tables.run_inputs).where(
                story_tables.run_inputs.c.run_id == seeded.run_id,
                story_tables.run_inputs.c.input_revision == 2,
            )
        ).mappings().one()
        if stale_field == "context":
            context = {**input_row["context_snapshot"], "age_months": 61}
            db.execute(
                update(story_tables.run_inputs)
                .where(story_tables.run_inputs.c.run_input_id == input_row["run_input_id"])
                .values(
                    context_snapshot=context,
                    context_snapshot_sha256=_sha256_json(context),
                )
            )
        elif stale_field == "context_hash":
            db.execute(
                update(story_tables.run_inputs)
                .where(story_tables.run_inputs.c.run_input_id == input_row["run_input_id"])
                .values(context_snapshot_sha256="e" * 64)
            )
        elif stale_field == "subject":
            db.execute(
                update(story_tables.story_runs)
                .where(story_tables.story_runs.c.run_id == seeded.run_id)
                .values(subject_label="changed subject")
            )
        elif stale_field in {"understanding", "understanding_hash"}:
            understanding = db.execute(
                select(story_tables.understanding_revisions).where(
                    story_tables.understanding_revisions.c.run_id == seeded.run_id,
                    story_tables.understanding_revisions.c.revision_no == 1,
                )
            ).mappings().one()
            if stale_field == "understanding":
                snapshot = deepcopy(understanding["result_snapshot"])
                snapshot["result"]["visible_features"] = ["changed feature"]
                understanding_hash = _sha256_json(snapshot)
            else:
                snapshot = understanding["result_snapshot"]
                understanding_hash = "e" * 64
            db.execute(
                update(story_tables.understanding_revisions)
                .where(
                    story_tables.understanding_revisions.c.understanding_revision_id
                    == understanding["understanding_revision_id"]
                )
                .values(
                    result_snapshot=snapshot,
                    canonical_result_sha256=understanding_hash,
                )
            )
            db.execute(
                update(story_tables.story_runs)
                .where(story_tables.story_runs.c.run_id == seeded.run_id)
                .values(result_sha256=understanding_hash)
            )
        elif stale_field == "drawing":
            db.execute(
                update(story_tables.run_inputs)
                .where(story_tables.run_inputs.c.run_input_id == input_row["run_input_id"])
                .values(original_sha256=sha(b"changed drawing digest"))
            )
        else:
            selection = db.execute(
                select(story_tables.activity_selections).where(
                    story_tables.activity_selections.c.run_id == seeded.run_id,
                    story_tables.activity_selections.c.selection_no == 1,
                )
            ).mappings().one()
            snapshot = deepcopy(selection["activity_snapshot"])
            snapshot_hash = _sha256_json(snapshot)
            if stale_field == "activity":
                snapshot["title"] = "Changed activity"
                snapshot_hash = _sha256_json(snapshot)
            elif stale_field == "activity_hash":
                snapshot_hash = "e" * 64
            _append_activity_selection(
                db,
                api.parent,
                seeded.run_id,
                key=f"stale-selection-{uuid4().hex}",
                selection_no=2,
                created_at=selection["created_at"] - timedelta(seconds=1),
                activity_snapshot=snapshot,
                activity_snapshot_sha256=snapshot_hash,
            )

    response = rewrite(api, api.parent, seeded.run_id, revision=1, key="stale-recovery")
    assert response.status_code == 409
    assert code_of(response) == "INVALID_STATE_TRANSITION"
    assert len(story_rows(api, seeded.run_id)) == 1
    assert receipt_rows(api, seeded.run_id, "GENERATE_STORY_REVISION") == []


def test_two_concurrent_recoveries_have_one_winner_and_active_run_conflict(
    api: RewriteApi,
) -> None:
    seeded = seed_failed_first_story(api)
    barrier = Barrier(2)

    def send(key: str) -> Any:
        barrier.wait(timeout=30)
        return rewrite(api, api.parent, seeded.run_id, revision=1, key=key)

    keys = ("parallel-recovery-one", "parallel-recovery-two")
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(send, keys))

    assert sorted(response.status_code for response in responses) == [202, 409]
    loser = next(response for response in responses if response.status_code == 409)
    # The loser finds the same run already recovering: the ordinary in-flight rewrite code applies;
    # ACTIVE_RUN_EXISTS is kept for another active run of the same Parent.
    assert code_of(loser) == "INVALID_STATE_TRANSITION"
    assert [row["revision_no"] for row in story_rows(api, seeded.run_id)] == [1, 2]
    assert len(receipt_rows(api, seeded.run_id, "GENERATE_STORY_REVISION")) == 1


def test_a_different_active_parent_run_blocks_recovery_before_dispatch(api: RewriteApi) -> None:
    seeded = seed_failed_first_story(api)
    other_run = story_run(api, api.parent)

    response = rewrite(api, api.parent, seeded.run_id, revision=1, key="blocked-recovery")

    assert response.status_code == 409 and code_of(response) == "ACTIVE_RUN_EXISTS"
    assert states(api, other_run)[0] == "SCRIPT_REVIEW"
    assert [row["revision_no"] for row in story_rows(api, seeded.run_id)] == [1]
    assert receipt_rows(api, seeded.run_id, "GENERATE_STORY_REVISION") == []


def test_the_keyed_fixture_generator_is_used_by_the_hash_of_the_exact_input(
    api: RewriteApi,
) -> None:
    run_id = story_run(api)
    with api.sessions()() as db:
        account_id = db.scalar(
            select(AdultIdentityModel.account_id).where(
                AdultIdentityModel.subject == api.parent
            )
        )
        outcome = SqlParentStoryRunRepository(db).reserve_story_rewrite(
            principal=principal_of(api.parent),
            account_id=str(account_id),
            run_id=run_id,
            idempotency_key=uuid4().hex,
            expected_story_revision=1,
            expected_story_sha256=None,
            hint=HINT,
            story_revision_id=str(uuid4()),
            model_id="story-generator-port",
            model_revision="unassigned",
            prompt_version="parent-story-rewrite.v1",
            instruction_version="rewrite-neutral.v1",
            instruction=REWRITE_NEUTRAL_INSTRUCTION_V1,
        )
    reservation = outcome.reservation
    assert reservation is not None
    assert worker_input_sha256(reservation.worker_input) == reservation.request_sha256
    keyed = FixtureStoryGenerator(
        {
            reservation.request_sha256: StoryGenerationResult(
                valid_story(), "keyed-call", "fixture-model", "2"
            )
        }
    )
    ParentStoryRewriteRunner(api.sessions(), keyed).run(principal_of(api.parent), reservation)
    assert states(api, run_id) == ("SCRIPT_REVIEW", "SUCCEEDED")
    row = story_rows(api, run_id)[-1]
    assert (row["status"], row["provider_call_id"], row["model_revision"]) == (
        "DRAFT",
        "keyed-call",
        "2",
    )
    assert row["request_sha256"] == reservation.request_sha256


# ---------------------------------------------------------------------------- the gates (422)
def test_the_first_story_gates_apply_to_a_rewrite(api: RewriteApi) -> None:
    compose_generator(api)
    # SUBJECT_NOT_CONFIRMED: the review decision is gone
    run_id = story_run(api)
    with api.sessions().begin() as db:
        db.execute(
            story_tables.review_decisions.delete().where(
                story_tables.review_decisions.c.run_id == run_id
            )
        )
    refused = rewrite(api, api.parent, run_id, revision=1)
    assert refused.status_code == 422 and code_of(refused) == "SUBJECT_NOT_CONFIRMED"
    # PROFILE_CONTEXT_NOT_CONFIRMED: the confirmation of the current input is gone
    run_id = story_run(api, hold_slot=False)
    with api.sessions().begin() as db:
        db.execute(
            update(story_tables.run_inputs)
            .where(story_tables.run_inputs.c.run_id == run_id)
            .values(context_confirmed_by=None, context_confirmed_at=None)
        )
    refused = rewrite(api, api.parent, run_id, revision=1)
    assert refused.status_code == 422 and code_of(refused) == "PROFILE_CONTEXT_NOT_CONFIRMED"
    # TRANSCRIPT_NOT_CONFIRMED: the current input carries a voice idea whose text is not confirmed
    run_id = story_run(api, hold_slot=False)
    voice_ref = f"parent/{run_id}/voice/original"
    with api.sessions().begin() as db:
        db.execute(
            update(story_tables.run_inputs)
            .where(
                story_tables.run_inputs.c.run_id == run_id,
                story_tables.run_inputs.c.input_revision == 2,
            )
            .values(
                voice_asset_ref=voice_ref,
                voice_asset_version=1,
                voice_duration_ms=2000,
                idea_source="TEXT_AND_VOICE",
            )
        )
        db.execute(
            story_tables.transcript_revisions.insert().values(
                transcript_revision_id=str(uuid4()),
                run_id=run_id,
                run_input_id=story_rows_input_id(db, run_id),
                source_asset_ref=voice_ref,
                revision_no=1,
                origin="ASR",
                state="NEEDS_CONFIRMATION",
                raw_transcript="a spoken idea",
                transcript_sha256=sha(b"a spoken idea"),
                created_at=datetime.now(UTC),
            )
        )
    refused = rewrite(api, api.parent, run_id, revision=1)
    assert refused.status_code == 422 and code_of(refused) == "TRANSCRIPT_NOT_CONFIRMED"
    assert refused.json()["message"] not in {"", "Không thể hoàn tất yêu cầu."}
    assert len(story_rows(api, run_id)) == 1 and api.generator.inputs == []


def story_rows_input_id(db: Any, run_id: str) -> str:
    return str(
        db.scalar(
            select(story_tables.run_inputs.c.run_input_id).where(
                story_tables.run_inputs.c.run_id == run_id,
                story_tables.run_inputs.c.input_revision == 2,
            )
        )
    )


# ======================================================================= subject confirmation
def test_a_plain_confirmation_is_202_and_moves_to_preparation_review(api: RewriteApi) -> None:
    compose_analyzer(api)
    seeded = seed_run(api, api.parent)
    response = subject_route(api, api.parent, seeded.run_id, key="subject-key")
    status, body = wire(response)
    assert status == 202
    row = run_row(api, seeded.run_id)
    assert body == {
        "story_run_id": seeded.run_id,
        "understanding_revision": 1,
        "decision": "CONFIRMED",
        "run_revision": int(row["revision"]),
    }
    assert response.headers["Content-Location"] == f"/v1/story-runs/{seeded.run_id}"
    assert states(api, seeded.run_id) == ("PREPARATION_REVIEW", "SUCCEEDED")
    assert len(decision_rows(api, seeded.run_id)) == 1
    read = api.client.get(
        f"/v1/story-runs/{seeded.run_id}", headers=headers(api.parent)
    )
    assert read.status_code == 200
    projected = read.json()["story_run"]
    assert projected["candidate"]["decision"] == "CONFIRMED_BY_ADULT"
    assert projected["candidate"]["candidate_subject"] == SUBJECT
    # Confirmation is a separate review record; it does not rewrite the immutable VLM snapshot.
    assert understanding_rows(api, seeded.run_id)[0]["result_snapshot"]["result"]["decision"] == "REVIEW_REQUIRED"
    assert api.analyzer.calls == []
    (receipt,) = receipt_rows(api, seeded.run_id, "CONFIRM_SUBJECT")
    assert receipt["response_status"] == 202
    assert receipt["response_body"] == {
        "decision": "CONFIRMED",
        "understanding_revision": 1,
        "run_revision": int(row["revision"]),
    }
    # the replay is the same answer and writes nothing
    again = subject_route(api, api.parent, seeded.run_id, key="subject-key")
    assert wire(again) == wire(response)
    assert len(decision_rows(api, seeded.run_id)) == 1
    assert len(receipt_rows(api, seeded.run_id, "CONFIRM_SUBJECT")) == 1


def test_an_edit_reruns_the_vlm_and_the_adult_confirms_the_new_revision(api: RewriteApi) -> None:
    compose_analyzer(api)
    seeded = seed_run(api, api.parent)
    api.analyzer.register(
        seeded.derived_sha256,
        DrawingAnalysisResult("fire dragon", ("flame", "wings"), 0.8),
        subject_hint="the fire dragon",
    )
    first = subject_route(api, api.parent, seeded.run_id, subject="the fire dragon", key="edit-key")
    status, body = wire(first)
    assert status == 202
    assert (body["decision"], body["understanding_revision"]) == ("RERUN_REQUESTED", 1)
    # the runner ran after the response: revision 2 is recorded for the same drawing
    request = api.analyzer.calls[-1]
    assert request.subject_hint == "the fire dragon"
    assert request.derived_sha256 == seeded.derived_sha256
    rows = understanding_rows(api, seeded.run_id)
    assert [row["revision_no"] for row in rows] == [1, 2]
    assert rows[1]["run_input_id"] == seeded.drawing_input_id
    assert rows[1]["result_snapshot"]["result"]["decision"] == "REVIEW_REQUIRED"
    assert rows[1]["subject_label"] == "fire dragon"
    assert states(api, seeded.run_id) == ("SUBJECT_REVIEW", "SUCCEEDED")
    assert run_row(api, seeded.run_id)["understanding_revision"] == 2
    assert decision_rows(api, seeded.run_id) == []  # nothing is confirmed yet
    # the receipt kept the edited subject only for the runner
    (receipt,) = receipt_rows(api, seeded.run_id, "CONFIRM_SUBJECT")
    assert receipt["response_body"]["subject_hint"] == "the fire dragon"
    # the replay of the edit is the stored answer and starts no second analysis
    calls = len(api.analyzer.calls)
    assert wire(
        subject_route(api, api.parent, seeded.run_id, subject="the fire dragon", key="edit-key")
    ) == wire(first)
    assert len(api.analyzer.calls) == calls
    # the old revision is stale now; the new one is confirmed through the plain path
    stale = subject_route(api, api.parent, seeded.run_id, subject="fire dragon", revision=1)
    assert stale.status_code == 409 and code_of(stale) == "STALE_REVISION"
    assert stale.json()["current_version"] == 2
    plain = subject_route(api, api.parent, seeded.run_id, subject="fire dragon", revision=2)
    assert plain.status_code == 202 and plain.json()["decision"] == "CONFIRMED"
    assert plain.json()["understanding_revision"] == 2
    assert states(api, seeded.run_id) == ("PREPARATION_REVIEW", "SUCCEEDED")
    (decision,) = decision_rows(api, seeded.run_id)
    assert decision["target_understanding_revision"] == 2
    assert run_row(api, seeded.run_id)["subject_label"] == "fire dragon"


def test_without_a_composed_analyzer_an_edit_is_confirmed_at_once_dev_1(api: RewriteApi) -> None:
    assert api.app.state.drawing_analyzer is None
    seeded = seed_run(api, api.parent)
    response = subject_route(api, api.parent, seeded.run_id, subject="the fire dragon")
    status, body = wire(response)
    assert status == 202 and body["decision"] == "CONFIRMED"
    assert body["understanding_revision"] == 2
    assert states(api, seeded.run_id) == ("PREPARATION_REVIEW", "SUCCEEDED")
    rows = understanding_rows(api, seeded.run_id)
    assert [row["revision_no"] for row in rows] == [1, 2]
    assert rows[1]["result_snapshot"]["result"]["decision"] == "CORRECTED_BY_ADULT"
    (decision,) = decision_rows(api, seeded.run_id)
    assert decision["target_understanding_revision"] == 2


def test_the_switch_turns_the_rerun_off_even_with_an_analyzer(api: RewriteApi) -> None:
    compose_analyzer(api)
    api.app.state.subject_edit_reruns_vlm = False
    seeded = seed_run(api, api.parent)
    response = subject_route(api, api.parent, seeded.run_id, subject="the fire dragon")
    assert response.status_code == 202 and response.json()["decision"] == "CONFIRMED"
    assert response.json()["understanding_revision"] == 2
    assert api.analyzer.calls == []
    assert states(api, seeded.run_id)[0] == "PREPARATION_REVIEW"


def test_an_input_during_the_rerun_does_not_settle_the_run_early(api: RewriteApi) -> None:
    """While the rerun is queued the earlier understanding is being replaced (SRS l.394)."""
    seeded = seed_run(api, api.parent)
    with api.sessions()() as db:
        outcome = SqlParentStoryRunRepository(db).confirm_subject(
            principal=principal_of(api.parent),
            run_id=seeded.run_id,
            expected_understanding_revision=1,
            confirmed_subject="the fire dragon",
            idempotency_key=uuid4().hex,
            rerun_on_edit=True,
        )
    assert isinstance(outcome, SubjectConfirmOutcome)
    assert outcome.decision == "RERUN_REQUESTED" and outcome.input_revision == 2
    assert states(api, seeded.run_id) == ("INPUT_PROCESSING", "QUEUED")
    # a typed idea recomputes the run state: the rerun has not reported, so it keeps waiting
    revision = int(run_row(api, seeded.run_id)["revision"])
    idea = api.client.post(
        f"/v1/story-runs/{seeded.run_id}/idea",
        json={"expected_run_revision": revision, "text": "a second idea"},
        headers=headers(api.parent, uuid4().hex),
    )
    assert idea.status_code == 202, idea.text
    assert idea.json()["run_state"] == "INPUT_PROCESSING"
    assert states(api, seeded.run_id) == ("INPUT_PROCESSING", "QUEUED")
    with api.sessions()() as db:
        hint = SqlParentStoryRunRepository(db).read_subject_rerun_hint(
            principal=principal_of(api.parent), run_id=seeded.run_id
        )
    assert hint == "the fire dragon"
    # the subject cannot be confirmed while the rerun waits
    waiting = subject_route(api, api.parent, seeded.run_id, subject="the fire dragon")
    assert waiting.status_code == 409 and code_of(waiting) == "INVALID_STATE_TRANSITION"
    # the runner reports: revision 2, back to SUBJECT_REVIEW, and the hint is consumed
    api.analyzer.register(
        seeded.derived_sha256,
        DrawingAnalysisResult("fire dragon", ("flame",), 0.7),
        subject_hint="the fire dragon",
    )
    ParentInputJobRunner(api.sessions(), api.analyzer).run(
        principal_of(api.parent), seeded.run_id, 3
    )
    assert states(api, seeded.run_id) == ("SUBJECT_REVIEW", "SUCCEEDED")
    assert api.analyzer.calls[-1].subject_hint == "the fire dragon"
    with api.sessions()() as db:
        assert (
            SqlParentStoryRunRepository(db).read_subject_rerun_hint(
                principal=principal_of(api.parent), run_id=seeded.run_id
            )
            is None
        )


def test_a_failed_rerun_returns_to_subject_review_and_the_old_revision_still_confirms(
    api: RewriteApi,
) -> None:
    class Failing:
        calls = 0

        def analyze(self, request: Any) -> Any:
            type(self).calls += 1
            raise DrawingAnalysisFailure()

    api.app.state.drawing_analyzer = Failing()
    seeded = seed_run(api, api.parent)
    response = subject_route(api, api.parent, seeded.run_id, subject="the fire dragon")
    assert response.status_code == 202 and response.json()["decision"] == "RERUN_REQUESTED"
    assert Failing.calls == 1
    row = run_row(api, seeded.run_id)
    assert (row["run_state"], row["job_state"], row["retryable"]) == (
        "SUBJECT_REVIEW",
        "FAILED",
        True,
    )
    assert row["error_code"] == "DRAWING_ANALYSIS_UNAVAILABLE"
    assert [item["revision_no"] for item in understanding_rows(api, seeded.run_id)] == [1]
    # the adult confirms the first revision; the failure marks are closed
    plain = subject_route(api, api.parent, seeded.run_id, subject=SUBJECT, revision=1)
    assert plain.status_code == 202 and plain.json()["decision"] == "CONFIRMED"
    row = run_row(api, seeded.run_id)
    assert (row["run_state"], row["job_state"], row["error_code"]) == (
        "PREPARATION_REVIEW",
        "SUCCEEDED",
        None,
    )


def test_the_state_and_stale_answers_of_the_subject_confirmation(api: RewriteApi) -> None:
    seeded = seed_run(api, api.parent)
    stale = subject_route(api, api.parent, seeded.run_id, revision=3)
    assert stale.status_code == 409 and code_of(stale) == "STALE_REVISION"
    assert stale.json()["current_version"] == 1
    for state in ("INPUT_PROCESSING", "INPUT_REVIEW", "PREPARATION_REVIEW", "SCRIPT_REVIEW"):
        other = seed_run(api, api.parent, run_state=state, hold_slot=False)
        refused = subject_route(api, api.parent, other.run_id)
        assert refused.status_code == 409, state
        assert code_of(refused) == "INVALID_STATE_TRANSITION"
        assert "current_version" not in refused.json()
    assert decision_rows(api, seeded.run_id) == []


def test_a_purged_run_replays_the_lifecycle_projection_under_202(api: RewriteApi) -> None:
    seeded = seed_run(api, api.parent)
    first = subject_route(api, api.parent, seeded.run_id, key="subject-key")
    assert first.status_code == 202
    assert cancel(api, api.parent, seeded.run_id).status_code == 202
    replay = subject_route(api, api.parent, seeded.run_id, key="subject-key")
    assert replay.status_code == 202 and set(replay.json()) == {"request_id", "lifecycle"}
    assert replay.json()["lifecycle"]["run_state"] == "DELETE_PENDING"
    fresh = subject_route(api, api.parent, seeded.run_id)
    assert fresh.status_code == 409 and code_of(fresh) == "INVALID_STATE_TRANSITION"


def test_a_receipt_from_before_t_2d_replays_with_the_current_run_revision(api: RewriteApi) -> None:
    seeded = seed_run(api, api.parent)
    first = subject_route(api, api.parent, seeded.run_id, key="old-key")
    assert first.status_code == 202
    receipt = receipt_rows(api, seeded.run_id, "CONFIRM_SUBJECT")[0]
    with api.sessions().begin() as db:  # the body the repository wrote before T-2d
        db.execute(
            story_tables.story_command_receipts.update()
            .where(story_tables.story_command_receipts.c.receipt_id == receipt["receipt_id"])
            .values(
                response_body={"decision": "CONFIRMED", "understanding_revision": 1},
                response_status=200,
            )
        )
    replay = subject_route(api, api.parent, seeded.run_id, key="old-key")
    assert replay.status_code == 202
    assert replay.json()["run_revision"] == int(run_row(api, seeded.run_id)["revision"])
    assert replay.json()["decision"] == "CONFIRMED"


def test_the_legacy_ai_routes_answer_the_404_guard_on_the_real_database(api: RewriteApi) -> None:
    seeded = seed_run(api, api.parent)
    for caller in (api.teacher, "synthetic-unknown-subject"):
        response = api.client.post(
            f"/api/parent/v1/ai/story-runs/{seeded.run_id}/story-revisions",
            json={"expected_understanding_revision": 1},
            headers=headers(caller, uuid4().hex),
        )
        assert response.status_code == 404 and code_of(response) == "RESOURCE_NOT_FOUND"
