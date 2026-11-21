"""FEAT-066 T-1a: ``POST /v1/story-runs/{id}/video-generations`` and the video saga on PostgreSQL.

SRS l.395 (VideoGeneration: intent first, ``ACCEPTED`` only after both receipts), l.500 and FR-C-08
(cancel meets the saga), l.573 (three requests), l.596-597 (quota and budget), l.1670 (the route),
l.1697-1699 (idempotency, stale protection). Runs only against a disposable database whose name
contains ``be1_acceptance`` and ``frc08_v3_t1a``. The two admission ports are the local/test pair
with a fixed-outcome script; object storage is in memory; no provider is called. A run is built by
direct inserts (a confirmed script, its review, its scenes) because the earlier steps are other
tasks' routes.
"""

from __future__ import annotations

import hashlib
import io
import os
from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime
from threading import Barrier
from typing import Any
from uuid import uuid4

import pytest
from fastapi import FastAPI, Header
from fastapi.testclient import TestClient
from sqlalchemy import event, insert, select, text, update
from sqlalchemy.exc import DataError, IntegrityError

from sketch2life.application.ports.core_foundation import LifecycleScope
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.object_storage import StoredObject
from sketch2life.application.ports.story_run_lifecycle import (
    StoryLifecycleError,
    lifecycle_request_id,
)
from sketch2life.application.ports.story_video import (
    AckStatus,
    ProgressEvent,
    QuotaResult,
    QuotaStatus,
    ReservationStatus,
    StoryVideoAdapters,
    VideoRenderResult,
)
from sketch2life.application.services.story_run_video import (
    StoryVideoAdmissionService,
    StoryVideoProgressService,
)
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel
from sketch2life.infrastructure.persistence.core_lifecycle_store import (
    SqlCoreRunAssetPurge,
    build_plan,
)
from sketch2life.infrastructure.persistence.core_models import CoreAssetMetadataModel
from sketch2life.infrastructure.persistence.story_lifecycle_store import SqlStoryLifecycleStore
from sketch2life.infrastructure.story_run_lite import tables as story_tables
from sketch2life.infrastructure.story_video.fixture_runner import (
    FixtureVideoRenderer,
    FixtureVideoRunner,
)
from sketch2life.infrastructure.story_video.local_adapters import (
    LocalVideoComputeReservation,
    LocalVideoQuotaAdmission,
    VideoAdmissionScript,
    build_local_video_adapters,
)
from sketch2life.infrastructure.story_video.repository import SqlStoryVideoRepository
from sketch2life.infrastructure.uploads.resolvers import parent_scope_ref
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult

ISSUER = "synthetic-t1a-issuer"
STORAGE_WORDS = ("bucket", "object_key", "presigned", "s3mock", "parent/", "output.mp4")
VG = story_tables.video_generations
VGS = story_tables.video_generation_scenes
RUNS = story_tables.story_runs


def sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class InMemoryStorage:
    def __init__(self) -> None:
        self.objects: dict[str, tuple[bytes, str]] = {}

    def put_object(
        self, key: str, body: Any, *, content_type: str, content_length: int, metadata: Any
    ) -> None:
        content = body.read()
        assert len(content) == content_length
        self.objects[key] = (content, content_type)

    def get_object(self, key: str) -> StoredObject | None:
        item = self.objects.get(key)
        if item is None:
            return None
        content, content_type = item
        return StoredObject(io.BytesIO(content), len(content), content_type, {})

    def delete_object(self, key: str) -> None:
        self.objects.pop(key, None)

    def list_keys(self, prefix: str) -> tuple[str, ...]:
        return tuple(sorted(key for key in self.objects if key.startswith(prefix)))


@dataclass
class VideoApi:
    app: FastAPI
    client: TestClient
    storage: InMemoryStorage
    script: VideoAdmissionScript
    adapters: StoryVideoAdapters
    parent: str
    other_parent: str
    teacher: str
    manager: str
    admin: str

    def sessions(self) -> Any:
        return self.app.state.be1_runtime.session_factory

    def use_adapters(self, adapters: StoryVideoAdapters | None) -> None:
        self.app.state.story_video_ports = adapters

    @property
    def reservation(self) -> LocalVideoComputeReservation:
        return self.adapters.reservation  # type: ignore[return-value]

    @property
    def quota(self) -> LocalVideoQuotaAdmission:
        return self.adapters.quota  # type: ignore[return-value]


@pytest.fixture
def api(monkeypatch: pytest.MonkeyPatch) -> Iterator[VideoApi]:
    database_url = os.environ.get("BE1_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("set BE1_TEST_DATABASE_URL to a disposable PostgreSQL database")
    database_name = database_url.rsplit("/", 1)[-1]
    if "be1_acceptance" not in database_name or "frc08_v3_t1a" not in database_name:
        pytest.fail("BE1_TEST_DATABASE_URL must be a disposable frc08_v3_t1a*be1_acceptance db")
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", database_url)
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
    token = uuid4().hex[:8]
    subjects = {
        "parent": f"synthetic-t1a-parent-{token}",
        "other_parent": f"synthetic-t1a-parent2-{token}",
        "teacher": f"synthetic-t1a-teacher-{token}",
        "manager": f"synthetic-t1a-manager-{token}",
        "admin": f"synthetic-t1a-admin-{token}",
    }
    roles = {
        "parent": "parent",
        "other_parent": "parent",
        "teacher": "teacher",
        "manager": "school_manager",
        "admin": "platform_admin",
    }
    with runtime.session_factory.begin() as db:
        for key, subject in subjects.items():
            db.add(
                AdultIdentityModel(
                    subject=subject, issuer=ISSUER, state="active", account_role=roles[key]
                )
            )

    async def verified(
        x_test_principal: str = Header(alias="X-Test-Principal"),
    ) -> VerifiedPrincipal:
        return VerifiedPrincipal(subject=x_test_principal, issuer=ISSUER, roles=frozenset())

    script = VideoAdmissionScript()
    adapters = build_local_video_adapters(env="test", script=script)
    storage = InMemoryStorage()
    app.state.story_video_ports = adapters
    app.state.lesson_library_storage = storage
    app.dependency_overrides[get_verified_adult] = verified
    try:
        with TestClient(app) as client:
            yield VideoApi(
                app,
                client,
                storage,
                script,
                adapters,
                subjects["parent"],
                subjects["other_parent"],
                subjects["teacher"],
                subjects["manager"],
                subjects["admin"],
            )
    finally:
        app.dependency_overrides.clear()
        runtime.engine.dispose()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


# ----------------------------------------------------------------------------- builders
@dataclass
class ScriptRun:
    run_id: str
    owner: str
    story_sha256: str  # the latest revision, the one a request asks a video for
    revision_ids: list[str] = field(default_factory=list)
    review_ids: list[str] = field(default_factory=list)
    generation_ids: list[str] = field(default_factory=list)


def principal_of(subject: str) -> VerifiedPrincipal:
    return VerifiedPrincipal(subject=subject, issuer=ISSUER, roles=frozenset())


def headers(subject: str, key: str | None = None) -> dict[str, str]:
    result = {"X-Test-Principal": subject}
    if key is not None:
        result["Idempotency-Key"] = key
    return result


def _receipt(db: Any, run_id: str, scope_ref: str, operation: str) -> str:
    receipt_id = str(uuid4())
    db.execute(
        story_tables.story_command_receipts.insert().values(
            receipt_id=receipt_id,
            actor_scope_kind="PARENT_ACCOUNT",
            actor_scope_ref=scope_ref,
            operation=operation,
            idempotency_scope_kind="STORY_RUN",
            idempotency_scope_ref=run_id,
            idempotency_key_sha256=sha(receipt_id),
            request_fingerprint_sha256=sha("fp" + receipt_id),
            state="FINAL",
            response_status=200,
            response_body={"decision": "CONFIRMED"},
            resource_ref=run_id,
            resource_version=1,
            state_version=1,
            created_at=datetime.now(UTC),
            finalized_at=datetime.now(UTC),
        )
    )
    return receipt_id


def new_script_run(
    api: VideoApi,
    owner: str | None = None,
    *,
    prior: int = 0,
    run_state: str = "SCRIPT_REVIEW",
    latest_status: str = "CONFIRMED",
    hold_slot: bool | None = None,
    scenes: int = 3,
    context_confirmed: bool = True,
    subject_confirmed: bool = True,
) -> ScriptRun:
    """A run at its script review: ``prior`` spent revisions (each with a FAILED accepted
    generation), then one confirmed (or ``latest_status``) revision with its review and scenes."""

    owner = owner or api.parent
    run_id = str(uuid4())
    now = datetime.now(UTC)
    scope_ref = parent_scope_ref(principal_of(owner))
    made = ScriptRun(run_id, owner, "")
    with api.sessions().begin() as db:
        account_id = db.scalar(
            select(AdultIdentityModel.account_id).where(AdultIdentityModel.subject == owner)
        )
        if hold_slot is None:
            # one active run per Parent: the first run of a test holds the slot, later ones do not
            hold_slot = run_state not in {"COMPLETED", "FAILED", "ABANDONED"} and not db.scalar(
                select(RUNS.c.run_id).where(
                    RUNS.c.active_owner_parent_account_id == str(account_id)
                )
            )
        db.execute(
            RUNS.insert().values(
                run_id=run_id,
                actor_scope_kind="PARENT_ACCOUNT",
                actor_scope_ref=scope_ref,
                profile_ref=str(uuid4()),
                run_state=run_state,
                revision=5,
                version=5,
                job_state="SUCCEEDED",
                understanding_revision=1,
                current_input_revision=1,
                active_owner_parent_account_id=str(account_id) if hold_slot else None,
                adult_wait_started_at=now,
                created_at=now,
                updated_at=now,
            )
        )
        db.execute(
            story_tables.run_inputs.insert().values(
                run_input_id=str(uuid4()),
                run_id=run_id,
                input_revision=1,
                typed_idea="a friendly dragon",
                idea_source="TEXT",
                source_profile_revision_ref=str(uuid4()),
                context_revision=1,
                context_snapshot={"schema_version": "sketch2life.parent-context.v1"},
                context_snapshot_sha256="c" * 64,
                context_confirmed_by=scope_ref if context_confirmed else None,
                context_confirmed_at=now if context_confirmed else None,
                created_at=now,
            )
        )
        if subject_confirmed:
            db.execute(
                story_tables.review_decisions.insert().values(
                    decision_id=str(uuid4()),
                    run_id=run_id,
                    command_receipt_id=_receipt(db, run_id, scope_ref, "CONFIRM_SUBJECT"),
                    stage="SUBJECT",
                    decision="CONFIRM",
                    actor_scope_kind="PARENT_ACCOUNT",
                    actor_scope_ref=scope_ref,
                    target_understanding_revision=1,
                    created_at=now,
                )
            )
        total = prior + 1
        for number in range(1, total + 1):
            latest = number == total
            revision_id = str(uuid4())
            story_hash = sha(f"story-{run_id}-{number}")
            status = latest_status if latest else "SUPERSEDED"
            db.execute(
                story_tables.story_revisions.insert().values(
                    story_revision_id=revision_id,
                    run_id=run_id,
                    revision_no=number,
                    status=status,
                    source_asset_sha256="d" * 64,
                    understanding_revision=1,
                    context_revision=1,
                    story_sha256=story_hash,
                    language="vi",
                    title="Chuyen rong nho",
                    duration_ms=60000,
                    story_content={"beginning": "b", "middle": "m", "end": "e"},
                    schema_version="sketch2life.story.v1",
                    prompt_version="synthetic-prompt",
                    model_id="synthetic-model",
                    model_revision="1",
                    request_sha256="e" * 64,
                    created_at=now,
                )
            )
            for index in range(1, scenes + 1):
                db.execute(
                    story_tables.story_scenes.insert().values(
                        scene_id=str(uuid4()),
                        story_revision_id=revision_id,
                        scene_index=index,
                        title=f"Scene {index}",
                        action="action",
                        visual_prompt="prompt",
                        narration="narration",
                        start_ms=(index - 1) * 5000,
                        duration_ms=5000,
                        character_anchors=[],
                    )
                )
            made.revision_ids.append(revision_id)
            if latest and latest_status != "CONFIRMED":
                made.story_sha256 = story_hash
                continue
            review_id = str(uuid4())
            db.execute(
                story_tables.story_revision_reviews.insert().values(
                    review_id=review_id,
                    run_id=run_id,
                    story_revision_id=revision_id,
                    command_receipt_id=_receipt(db, run_id, scope_ref, "CONFIRM_STORY_REVISION"),
                    actor_scope_kind="PARENT_ACCOUNT",
                    actor_scope_ref=scope_ref,
                    decision="CONFIRM",
                    target_story_sha256=story_hash,
                    created_at=now,
                )
            )
            made.review_ids.append(review_id)
            if latest:
                made.story_sha256 = story_hash
                continue
            generation_id = str(uuid4())
            db.execute(
                insert(VG).values(
                    video_generation_id=generation_id,
                    story_run_id=run_id,
                    story_revision_id=revision_id,
                    story_review_id=review_id,
                    generation_no=number,
                    generation_kind="INITIAL" if number == 1 else "QUALITY_REGEN",
                    state="FAILED",
                    request_idempotency_key_hash=sha(f"prior-{generation_id}"),
                    request_fingerprint_sha256=sha(f"fp-{generation_id}"),
                    target_script_hash=story_hash,
                    quality_reason_code=None if number == 1 else "QUALITY_LOW",
                    compute_reservation_ref=f"res-{number}",
                    compute_released_at=now,
                    billing_quota_usage_ref=f"usage-{number}",
                    job_ref=f"vjob_{uuid4().hex}",
                    admission_started_at=now,
                    accepted_at=now,
                    completed_at=now,
                    safe_failure_code="VIDEO_GENERATION_FAILED",
                    generation_revision=3,
                    created_at=now,
                    updated_at=now,
                )
            )
            made.generation_ids.append(generation_id)
    return made


def body_of(run: ScriptRun, **override: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "expected_revision": int(run_row(run.run_id)["revision"]),
        "story_sha256": run.story_sha256,
    }
    payload.update(override)
    return payload


_API: VideoApi | None = None


@pytest.fixture(autouse=True)
def _bind_api(api: VideoApi) -> Iterator[None]:
    global _API
    _API = api
    yield
    _API = None


def run_row(run_id: str) -> Any:
    assert _API is not None
    with _API.sessions()() as db:
        return db.execute(select(RUNS).where(RUNS.c.run_id == run_id)).mappings().one()


def generations(run_id: str) -> list[Any]:
    assert _API is not None
    with _API.sessions()() as db:
        return list(
            db.execute(
                select(VG)
                .where(VG.c.story_run_id == run_id)
                .order_by(VG.c.admission_started_at, VG.c.created_at)
            )
            .mappings()
            .all()
        )


def scenes_of(generation_id: str) -> list[Any]:
    assert _API is not None
    with _API.sessions()() as db:
        return list(
            db.execute(select(VGS).where(VGS.c.video_generation_id == generation_id))
            .mappings()
            .all()
        )


def receipts(run_id: str, operation: str = "CREATE_VIDEO_GENERATION") -> list[Any]:
    assert _API is not None
    table = story_tables.story_command_receipts
    with _API.sessions()() as db:
        return list(
            db.execute(
                select(table).where(table.c.resource_ref == run_id, table.c.operation == operation)
            )
            .mappings()
            .all()
        )


def request(
    api: VideoApi,
    run: ScriptRun,
    *,
    owner: str | None = None,
    key: str | None = None,
    body: dict[str, Any] | None = None,
) -> Any:
    return api.client.post(
        f"/v1/story-runs/{run.run_id}/video-generations",
        json=body if body is not None else body_of(run),
        headers=headers(owner or run.owner, key or uuid4().hex),
    )


def code_of(response: Any) -> str:
    return str(response.json()["code"])


def generation_of(response: Any) -> dict[str, Any]:
    assert response.status_code == 202, response.text
    return dict(response.json()["video_generation"])


def cancel(api: VideoApi, run: ScriptRun, *, key: str | None = None) -> Any:
    return api.client.post(
        f"/v1/story-runs/{run.run_id}/cancel",
        json={"expected_revision": int(run_row(run.run_id)["revision"])},
        headers=headers(run.owner, key or uuid4().hex),
    )


def runner(api: VideoApi, renderer: Any = None) -> FixtureVideoRunner:
    return FixtureVideoRunner(api.sessions(), api.storage, api.adapters, renderer)


def accepted(api: VideoApi, run: ScriptRun | None = None) -> tuple[ScriptRun, dict[str, Any]]:
    run = run or new_script_run(api)
    return run, generation_of(request(api, run))


# ============================================================================== happy path
def test_both_receipts_clear_accepts_the_request_and_queues_the_run(api: VideoApi) -> None:
    run = new_script_run(api)
    before = run_row(run.run_id)
    response = request(api, run)
    generation = generation_of(response)
    assert generation["state"] == "ACCEPTED" and generation["generation_no"] == 1
    assert generation["kind"] == "INITIAL" and generation["run_state"] == "VIDEO_QUEUED"
    assert generation["job_id"].startswith("vjob_")
    assert response.headers["Content-Location"] == f"/v1/story-runs/{run.run_id}"
    (row,) = generations(run.run_id)
    assert row["state"] == "ACCEPTED" and row["generation_no"] == 1
    assert row["story_review_id"] == run.review_ids[0]
    assert row["compute_reservation_ref"] and row["billing_quota_usage_ref"]
    assert row["accepted_at"] is not None and row["rejected_at"] is None
    assert row["job_ref"] == generation["job_id"]
    assert row["compute_released_at"] is None  # accepted: held until settle
    after = run_row(run.run_id)
    assert after["run_state"] == "VIDEO_QUEUED" and after["job_state"] == "QUEUED"
    assert after["current_video_generation_id"] == row["video_generation_id"]
    # two commits: the intent and the verdict
    assert after["revision"] == before["revision"] + 2 and after["version"] == before["version"] + 2
    assert after["adult_wait_started_at"] is None  # system work, not adult wait
    assert after["active_owner_parent_account_id"] is not None  # the lock is kept
    assert after["last_meaningful_activity_at"] is not None
    # the scenes of the pinned revision were copied
    scenes = scenes_of(row["video_generation_id"])
    assert len(scenes) == 3 and {scene["state"] for scene in scenes} == {"QUEUED"}
    # the receipt is final and holds no content
    (receipt,) = receipts(run.run_id)
    assert receipt["state"] == "FINAL" and receipt["response_status"] == 202
    # reserve first, then the quota admission, each called once with the generation id
    assert api.reservation.calls == [("reserve", row["video_generation_id"])]
    assert api.quota.calls == [row["video_generation_id"]]


def test_the_response_and_the_job_carry_no_storage_or_quota_detail(api: VideoApi) -> None:
    run = new_script_run(api)
    response = request(api, run)
    text_body = response.text.lower()
    for word in (*STORAGE_WORDS, "usage", "reservation", "usd", "balance", "units"):
        assert word not in text_body, word
    assert set(response.json()) == {"request_id", "video_generation"}


def test_replaying_the_same_key_and_payload_returns_the_same_request_without_new_rows(
    api: VideoApi,
) -> None:
    run = new_script_run(api)
    key = uuid4().hex
    payload = body_of(run)
    first = generation_of(request(api, run, key=key, body=payload))
    second = generation_of(request(api, run, key=key, body=payload))
    assert second == first
    assert len(generations(run.run_id)) == 1 and len(receipts(run.run_id)) == 1
    assert len(api.reservation.calls) == 1 and len(api.quota.calls) == 1
    # the run revision moved on, yet the original answer is repeated (the replay precedes checks)
    assert run_row(run.run_id)["revision"] == payload["expected_revision"] + 2


def test_the_same_key_with_another_payload_is_an_idempotency_error(api: VideoApi) -> None:
    run = new_script_run(api)
    key = uuid4().hex
    generation_of(request(api, run, key=key))
    changed = request(api, run, key=key, body=body_of(run, story_sha256="f" * 64))
    assert changed.status_code == 400 and code_of(changed) == "INVALID_IDEMPOTENCY_KEY"
    assert len(generations(run.run_id)) == 1


def test_a_missing_or_malformed_key_is_a_plain_400_before_any_lookup(api: VideoApi) -> None:
    run = new_script_run(api)
    missing = api.client.post(
        f"/v1/story-runs/{run.run_id}/video-generations",
        json=body_of(run),
        headers=headers(run.owner),
    )
    assert missing.status_code == 400 and code_of(missing) == "INVALID_REQUEST"
    # even for a run that does not exist: the key error does not depend on the run
    unknown = api.client.post(
        f"/v1/story-runs/{uuid4()}/video-generations",
        json=body_of(run),
        headers=headers(run.owner, "bad key"),
    )
    assert unknown.status_code == 400 and code_of(unknown) == "INVALID_REQUEST"
    assert generations(run.run_id) == []


# ============================================================================== authorization
def test_another_parent_or_another_role_gets_the_uniform_404_and_no_row(api: VideoApi) -> None:
    run = new_script_run(api)
    for subject in (api.other_parent, api.teacher, api.manager, api.admin):
        response = request(api, run, owner=subject)
        assert response.status_code == 404 and code_of(response) == "RESOURCE_NOT_FOUND", subject
    unknown = api.client.post(
        f"/v1/story-runs/{uuid4()}/video-generations",
        json=body_of(run),
        headers=headers(api.parent, uuid4().hex),
    )
    assert unknown.status_code == 404
    assert generations(run.run_id) == [] and api.reservation.calls == []


def test_a_foreign_actor_never_sees_503_first_even_with_no_adapters(api: VideoApi) -> None:
    run = new_script_run(api)
    api.use_adapters(None)
    foreign = request(api, run, owner=api.other_parent)
    assert foreign.status_code == 404 and code_of(foreign) == "RESOURCE_NOT_FOUND"
    wrong_state = new_script_run(api, run_state="INPUT_PROCESSING")
    state = request(api, wrong_state)
    assert state.status_code == 409 and code_of(state) == "INVALID_STATE_TRANSITION"
    stale = request(api, run, body=body_of(run, expected_revision=1))
    assert stale.status_code == 409 and code_of(stale) == "STALE_REVISION"
    # only a request that passed every other check reaches the 503
    final = request(api, run)
    assert final.status_code == 503 and code_of(final) == "PROVIDER_UNAVAILABLE"
    assert final.json()["retryable"] is True
    assert generations(run.run_id) == []  # nothing stored, nothing moved
    assert run_row(run.run_id)["run_state"] == "SCRIPT_REVIEW"
    assert receipts(run.run_id) == []


# ============================================================================== state gates
def test_the_run_state_the_revision_and_the_hash_are_checked_in_that_order(api: VideoApi) -> None:
    run = new_script_run(api)
    current = int(run_row(run.run_id)["revision"])
    revision = request(api, run, body=body_of(run, expected_revision=current - 1))
    assert revision.status_code == 409 and code_of(revision) == "STALE_REVISION"
    assert revision.json()["current_version"] == current
    stale_hash = request(api, run, body=body_of(run, story_sha256="b" * 64))
    assert stale_hash.status_code == 409 and code_of(stale_hash) == "STALE_REVISION"
    assert stale_hash.json()["current_version"] == current
    for state in ("INPUT_PROCESSING", "SUBJECT_REVIEW", "COMPLETED", "FAILED"):
        other = new_script_run(api, run_state=state)
        response = request(api, other)
        assert response.status_code == 409 and code_of(response) == "INVALID_STATE_TRANSITION"
    assert generations(run.run_id) == []


def test_an_unconfirmed_script_is_a_state_error_and_a_run_with_no_script_too(api: VideoApi) -> None:
    draft = new_script_run(api, latest_status="DRAFT")
    response = request(api, draft)
    assert response.status_code == 409 and code_of(response) == "INVALID_STATE_TRANSITION"
    assert generations(draft.run_id) == []


def test_the_defensive_422_when_the_subject_or_the_context_is_not_confirmed(api: VideoApi) -> None:
    subject = new_script_run(api, subject_confirmed=False)
    response = request(api, subject)
    assert response.status_code == 422 and code_of(response) == "SUBJECT_NOT_CONFIRMED"
    context = new_script_run(api, context_confirmed=False)
    response = request(api, context)
    assert response.status_code == 422 and code_of(response) == "PROFILE_CONTEXT_NOT_CONFIRMED"
    assert generations(subject.run_id) == [] and generations(context.run_id) == []


def test_an_older_confirmed_script_hash_is_stale_not_accepted(api: VideoApi) -> None:
    run = new_script_run(api, prior=1)
    old_hash = sha(f"story-{run.run_id}-1")
    response = request(api, run, body=body_of(run, story_sha256=old_hash))
    assert response.status_code == 409 and code_of(response) == "STALE_REVISION"


# ============================================================================== cap and reason
def test_the_second_accepted_request_needs_a_reason_and_is_a_quality_regeneration(
    api: VideoApi,
) -> None:
    run = new_script_run(api, prior=1)
    missing = request(api, run)
    assert missing.status_code == 400 and code_of(missing) == "INVALID_REQUEST"
    assert missing.json()["field_errors"][0]["field"] == "quality_reason_code"
    bad = request(api, run, body=body_of(run, quality_reason_code="NOT_A_REASON"))
    assert bad.status_code == 400 and code_of(bad) == "INVALID_REQUEST"
    assert generations(run.run_id)[-1]["state"] == "FAILED"  # only the prior row exists
    ok = request(api, run, body=body_of(run, quality_reason_code="QUALITY_LOW"))
    generation = generation_of(ok)
    assert generation["kind"] == "QUALITY_REGEN" and generation["generation_no"] == 2
    rows = generations(run.run_id)
    assert [row["generation_no"] for row in rows] == [1, 2]
    assert rows[1]["quality_reason_code"] == "QUALITY_LOW"


def test_the_first_request_refuses_a_reason(api: VideoApi) -> None:
    run = new_script_run(api)
    response = request(api, run, body=body_of(run, quality_reason_code="QUALITY_LOW"))
    assert response.status_code == 400 and code_of(response) == "INVALID_REQUEST"
    assert response.json()["field_errors"][0]["field"] == "quality_reason_code"
    assert generations(run.run_id) == []


def test_a_fourth_request_after_three_accepted_ones_is_refused(api: VideoApi) -> None:
    run = new_script_run(api, prior=3)
    response = request(api, run, body=body_of(run, quality_reason_code="QUALITY_LOW"))
    assert response.status_code == 409 and code_of(response) == "VIDEO_REGENERATION_LIMIT_REACHED"
    assert len(generations(run.run_id)) == 3 and api.reservation.calls == []


def test_a_refused_intent_does_not_count_toward_the_cap(api: VideoApi) -> None:
    run = new_script_run(api, prior=2)
    api.script.quotas.append(QuotaStatus.QUOTA_EXCEEDED)
    refused = request(api, run, body=body_of(run, quality_reason_code="QUALITY_LOW"))
    assert refused.status_code == 409
    again = request(api, run, body=body_of(run, quality_reason_code="OTHER"))
    generation = generation_of(again)
    assert generation["generation_no"] == 3  # the refused row took no number


# ============================================================================== review consumed
def test_a_script_rejected_by_the_adult_keeps_its_review_consumed(api: VideoApi) -> None:
    run, generation = accepted(api)
    with api.sessions().begin() as db:
        db.execute(
            update(VG)
            .where(VG.c.video_generation_id == generation["generation_id"])
            .values(
                state="REJECTED_BY_ADULT",
                rejection_reason_code="QUALITY_LOW",
                completed_at=datetime.now(UTC),
                technical_validation_state="PASSED",
                consistency_validation_state="PASSED",
                safety_validation_state="PASSED",
            )
        )
        db.execute(
            update(RUNS)
            .where(RUNS.c.run_id == run.run_id)
            .values(run_state="SCRIPT_REVIEW", adult_wait_started_at=datetime.now(UTC))
        )
    again = request(api, run, body=body_of(run, quality_reason_code="QUALITY_LOW"))
    # the same confirmed script needs a new confirmation (l.395): its review is spent
    assert again.status_code == 409 and code_of(again) == "INVALID_STATE_TRANSITION"


def test_a_refused_intent_leaves_the_review_reusable_and_the_run_waiting_again(
    api: VideoApi,
) -> None:
    run = new_script_run(api)
    before = run_row(run.run_id)
    api.script.quotas.append(QuotaStatus.QUOTA_EXCEEDED)
    refused = request(api, run)
    assert refused.status_code == 409 and code_of(refused) == "VIDEO_QUOTA_EXCEEDED"
    (rejected,) = generations(run.run_id)
    assert rejected["state"] == "ADMISSION_REJECTED" and rejected["generation_no"] is None
    assert rejected["job_ref"] is None and rejected["billing_quota_usage_ref"] is None
    assert rejected["accepted_at"] is None and rejected["rejected_at"] is not None
    assert rejected["safe_failure_code"] == "VIDEO_QUOTA_EXCEEDED"
    row = run_row(run.run_id)
    assert row["run_state"] == "SCRIPT_REVIEW" and row["current_video_generation_id"] is None
    assert row["adult_wait_started_at"] is not None  # a new adult-wait start
    assert row["adult_wait_started_at"] > before["adult_wait_started_at"]
    assert row["revision"] == before["revision"] + 2
    assert row["active_owner_parent_account_id"] is not None
    # the same review is used again by the next request with a new key
    accepted_again = generation_of(request(api, run))
    assert accepted_again["generation_no"] == 1 and accepted_again["state"] == "ACCEPTED"
    assert {row["state"] for row in generations(run.run_id)} == {"ADMISSION_REJECTED", "ACCEPTED"}


# ============================================================================== refusals
@pytest.mark.parametrize(
    ("quota", "code"),
    [
        (QuotaStatus.QUOTA_EXCEEDED, "VIDEO_QUOTA_EXCEEDED"),
        (QuotaStatus.SUBSCRIPTION_RESTRICTED, "SUBSCRIPTION_RESTRICTED"),
    ],
)
def test_a_quota_refusal_is_a_409_releases_the_reservation_and_replays_the_same_error(
    api: VideoApi, quota: QuotaStatus, code: str
) -> None:
    run = new_script_run(api)
    api.script.quotas.append(quota)
    key = uuid4().hex
    original = body_of(run)
    refused = request(api, run, key=key, body=original)
    assert refused.status_code == 409 and code_of(refused) == code
    (row,) = generations(run.run_id)
    assert row["state"] == "ADMISSION_REJECTED" and row["compute_reservation_ref"]
    assert row["compute_released_at"] is not None  # released outside any transaction
    assert [call[0] for call in api.reservation.calls] == ["reserve", "release"]
    (receipt,) = receipts(run.run_id)
    assert receipt["state"] == "FINAL" and receipt["response_status"] == 409
    assert receipt["response_body"] == {"code": code}
    calls = (len(api.reservation.calls), len(api.quota.calls))
    replay = request(api, run, key=key, body=body_of(run, expected_revision=1))  # stale body
    # a different body under the same key is an idempotency error, the same body repeats the error
    assert replay.status_code == 400 and code_of(replay) == "INVALID_IDEMPOTENCY_KEY"
    again = request(api, run, key=key, body=original)  # the same body repeats the same error
    assert again.status_code == 409 and code_of(again) == code
    assert (len(api.reservation.calls), len(api.quota.calls)) == calls  # no port call


def test_a_cost_refusal_is_a_503_before_the_quota_and_leaves_no_reservation(api: VideoApi) -> None:
    run = new_script_run(api)
    api.script.reservations.append(ReservationStatus.COST_LIMIT_REACHED)
    refused = request(api, run)
    assert refused.status_code == 503 and code_of(refused) == "AI_COST_LIMIT_REACHED"
    assert refused.json()["retryable"] is True
    (row,) = generations(run.run_id)
    assert row["state"] == "ADMISSION_REJECTED" and row["compute_reservation_ref"] is None
    assert api.quota.calls == []  # the quota is never asked after a cost refusal
    assert [call[0] for call in api.reservation.calls] == ["reserve"]
    assert row["job_ref"] is None and row["generation_no"] is None
    assert run_row(run.run_id)["run_state"] == "SCRIPT_REVIEW"


def test_an_unreadable_answer_keeps_the_intent_pending_and_the_run_in_admission(
    api: VideoApi,
) -> None:
    run = new_script_run(api)
    api.script.quotas.append(QuotaStatus.UNAVAILABLE)
    response = request(api, run)
    generation = generation_of(response)
    assert generation["state"] == "ADMISSION_PENDING" and generation["job_id"] is None
    assert generation["generation_no"] is None
    assert generation["run_state"] == "VIDEO_ADMISSION_PENDING"
    (row,) = generations(run.run_id)
    assert row["state"] == "ADMISSION_PENDING" and row["accepted_at"] is None
    assert row["compute_reservation_ref"] is None and row["job_ref"] is None
    assert run_row(run.run_id)["active_owner_parent_account_id"] is not None
    assert run_row(run.run_id)["adult_wait_started_at"] is None  # system work, not adult wait
    (receipt,) = receipts(run.run_id)
    assert receipt["state"] == "PENDING" and receipt["response_status"] is None


def test_a_changed_payload_at_the_quota_port_is_a_key_error_and_the_intent_stays(
    api: VideoApi,
) -> None:
    run = new_script_run(api)
    api.script.quotas.append(QuotaStatus.IDEMPOTENCY_MISMATCH)
    response = request(api, run)
    assert response.status_code == 400 and code_of(response) == "INVALID_IDEMPOTENCY_KEY"
    (row,) = generations(run.run_id)
    assert row["state"] == "ADMISSION_PENDING"


def test_a_replay_resolves_a_pending_intent_with_the_same_key(api: VideoApi) -> None:
    run = new_script_run(api)
    api.script.quotas.append(QuotaStatus.UNAVAILABLE)
    key = uuid4().hex
    payload = body_of(run)
    first = generation_of(request(api, run, key=key, body=payload))
    assert first["state"] == "ADMISSION_PENDING"
    second = generation_of(request(api, run, key=key, body=payload))
    assert second["state"] == "ACCEPTED" and second["generation_id"] == first["generation_id"]
    assert len(generations(run.run_id)) == 1
    (receipt,) = receipts(run.run_id)
    assert receipt["state"] == "FINAL"


def test_the_reconciler_finishes_an_intent_left_by_a_crash_after_the_first_commit(
    api: VideoApi,
) -> None:
    run = new_script_run(api)
    with api.sessions()() as db:
        intent = SqlStoryVideoRepository(db).begin_intent(
            principal=principal_of(run.owner),
            run_id=run.run_id,
            expected_revision=int(run_row(run.run_id)["revision"]),
            story_sha256=run.story_sha256,
            quality_reason_code=None,
            idempotency_key=uuid4().hex,
            adapters_available=True,
        )
    assert intent.record is not None and intent.record.state == "ADMISSION_PENDING"
    assert api.reservation.calls == []  # the process died before any port call
    with api.sessions()() as db:
        service = StoryVideoAdmissionService(SqlStoryVideoRepository(db), api.adapters)
        report = service.reconcile_pending_admissions(run_id=run.run_id)
    assert report.resolved == 1 and report.still_pending == 0
    (row,) = generations(run.run_id)
    assert row["state"] == "ACCEPTED" and row["generation_no"] == 1
    assert run_row(run.run_id)["run_state"] == "VIDEO_QUEUED"


def test_the_reconciler_rejects_nothing_on_its_own_and_keeps_asking(api: VideoApi) -> None:
    run = new_script_run(api)
    api.script.quotas.extend([QuotaStatus.UNAVAILABLE, QuotaStatus.UNAVAILABLE])
    generation_of(request(api, run))
    with api.sessions()() as db:
        service = StoryVideoAdmissionService(SqlStoryVideoRepository(db), api.adapters)
        assert service.reconcile_pending_admissions(run_id=run.run_id).still_pending == 1
    assert generations(run.run_id)[0]["state"] == "ADMISSION_PENDING"
    with api.sessions()() as db:
        service = StoryVideoAdmissionService(SqlStoryVideoRepository(db), api.adapters)
        assert service.reconcile_pending_admissions(run_id=run.run_id).resolved == 1


def test_a_refused_release_is_retried_by_the_reconciler_and_the_ref_is_never_lost(
    api: VideoApi,
) -> None:
    run = new_script_run(api)
    api.script.quotas.append(QuotaStatus.QUOTA_EXCEEDED)
    api.script.releases.append(AckStatus.UNAVAILABLE)
    assert request(api, run).status_code == 409
    (row,) = generations(run.run_id)
    assert row["compute_reservation_ref"] and row["compute_released_at"] is None
    with api.sessions()() as db:
        report = StoryVideoAdmissionService(
            SqlStoryVideoRepository(db), api.adapters
        ).reconcile_pending_admissions(run_id=run.run_id)
    assert report.compute_closed >= 1
    assert generations(run.run_id)[0]["compute_released_at"] is not None


# ============================================================================== concurrency
def _parallel(count: int, work: Callable[[int], Any]) -> list[Any]:
    barrier = Barrier(count)

    def start(index: int) -> Any:
        barrier.wait()
        return work(index)

    with ThreadPoolExecutor(max_workers=count) as pool:
        return [future.result() for future in [pool.submit(start, i) for i in range(count)]]


def test_two_requests_with_one_key_make_one_intent(api: VideoApi) -> None:
    run = new_script_run(api)
    key = uuid4().hex
    payload = body_of(run)
    responses = _parallel(2, lambda _i: request(api, run, key=key, body=payload))
    assert sorted(response.status_code for response in responses) == [202, 202]
    ids = {response.json()["video_generation"]["generation_id"] for response in responses}
    assert len(ids) == 1
    assert len(generations(run.run_id)) == 1 and len(receipts(run.run_id)) == 1
    assert generations(run.run_id)[0]["state"] == "ACCEPTED"
    assert generations(run.run_id)[0]["generation_no"] == 1


def test_two_different_keys_in_parallel_give_one_202_and_one_409(api: VideoApi) -> None:
    run = new_script_run(api)
    payload = body_of(run)
    responses = _parallel(2, lambda _i: request(api, run, body=payload))
    statuses = sorted(response.status_code for response in responses)
    assert statuses == [202, 409]
    loser = next(response for response in responses if response.status_code == 409)
    assert code_of(loser) in {"INVALID_STATE_TRANSITION", "STALE_REVISION"}
    open_rows = [row for row in generations(run.run_id) if row["state"] != "ADMISSION_REJECTED"]
    assert len(open_rows) == 1
    assert len(generations(run.run_id)) == 1


# =========================================================================== cancel meets the saga
class CancellingQuota:
    """A quota adapter that makes the Parent cancel while the port call is in flight."""

    def __init__(self, api: VideoApi, run: ScriptRun, inner: LocalVideoQuotaAdmission) -> None:
        self._api, self._run, self._inner = api, run, inner
        self.cancel_status: int | None = None

    def admit_video_request(self, **kwargs: Any) -> QuotaResult:
        if self.cancel_status is None:
            self.cancel_status = cancel(self._api, self._run).status_code
        return self._inner.admit_video_request(**kwargs)


def test_cancel_during_the_port_call_fails_the_admitted_unit_and_releases_the_reservation(
    api: VideoApi,
) -> None:
    run = new_script_run(api)
    hook = CancellingQuota(api, run, api.quota)
    api.use_adapters(StoryVideoAdapters(reservation=api.reservation, quota=hook))
    response = request(api, run)
    assert hook.cancel_status == 202
    generation = generation_of(response)
    assert generation["state"] == "FAILED"  # the unit was admitted before the cancel won
    (row,) = generations(run.run_id)
    assert row["state"] == "FAILED" and row["safe_failure_code"] == "RUN_CANCELLED"
    assert row["generation_no"] == 1 and row["billing_quota_usage_ref"]  # consumed, no refund
    assert row["compute_released_at"] is not None  # nothing started: released
    assert "release" in [call[0] for call in api.reservation.calls]
    assert run_row(run.run_id)["run_state"] == "DELETE_PENDING"  # the cancel is untouched
    # nothing is unsettled: the purge plan is available
    SqlStoryLifecycleStore(api.sessions()).plan_story_purge(run.run_id)


def test_cancel_with_an_unreadable_admission_blocks_the_purge_until_the_reconciler_settles(
    api: VideoApi,
) -> None:
    run = new_script_run(api)
    api.script.quotas.extend([QuotaStatus.UNAVAILABLE, QuotaStatus.UNAVAILABLE])
    generation_of(request(api, run))
    assert cancel(api, run).status_code == 202  # the cancel hook asks again: still unreadable
    (row,) = generations(run.run_id)
    assert row["state"] == "ADMISSION_PENDING"
    store = SqlStoryLifecycleStore(api.sessions())
    with pytest.raises(StoryLifecycleError, match="VIDEO_GENERATION_UNSETTLED"):
        store.plan_story_purge(run.run_id)
    with api.sessions()() as db:
        report = StoryVideoAdmissionService(
            SqlStoryVideoRepository(db), api.adapters
        ).reconcile_pending_admissions(run_id=run.run_id)
    assert report.resolved == 1
    (settled,) = generations(run.run_id)
    assert settled["state"] == "FAILED" and settled["safe_failure_code"] == "RUN_CANCELLED"
    assert settled["generation_no"] == 1 and settled["compute_released_at"] is not None
    plan = store.plan_story_purge(run.run_id)
    kinds = {item.split(":")[0] for item in plan.ids}
    assert {"video_generations", "story_revisions", "story_scenes"} <= kinds
    store.purge_story_content(plan)
    assert generations(run.run_id) == []
    assert store.plan_story_purge(run.run_id).empty
    assert store.finalize_deleted(run.run_id, lifecycle_request_id(run.run_id)) is True
    assert run_row(run.run_id)["run_state"] == "DELETED"
    assert run_row(run.run_id)["current_video_generation_id"] is None


def test_a_cancel_hook_that_never_ran_is_settled_by_the_reconciler_sweep(
    api: VideoApi, monkeypatch: pytest.MonkeyPatch
) -> None:
    run, generation = accepted(api)
    gid = generation["generation_id"]
    fixture = runner(api)
    while generations(run.run_id)[0]["state"] != "GENERATING":
        assert fixture.step(gid).applied

    def hook_down(self: Any, run_id: str) -> None:
        raise RuntimeError("the cancel hook did not run")

    monkeypatch.setattr(StoryVideoProgressService, "on_run_cancelled", hook_down)
    assert cancel(api, run).status_code == 202  # the cancel is durable; the hook error is swallowed
    assert generations(run.run_id)[0]["state"] == "GENERATING"  # nobody failed it
    assert fixture.step(gid).applied is False  # a worker cannot move a cancelled run either
    store = SqlStoryLifecycleStore(api.sessions())
    with pytest.raises(StoryLifecycleError, match="VIDEO_GENERATION_UNSETTLED"):
        store.plan_story_purge(run.run_id)
    with api.sessions()() as db:
        report = StoryVideoAdmissionService(
            SqlStoryVideoRepository(db), api.adapters
        ).reconcile_pending_admissions()
    assert report.cancelled_settled >= 1
    (row,) = generations(run.run_id)
    assert row["state"] == "FAILED" and row["safe_failure_code"] == "RUN_CANCELLED"
    assert row["compute_released_at"] is not None
    assert "settle:FAILED" in [call[0] for call in api.reservation.calls]  # it had started
    plan = store.plan_story_purge(run.run_id)  # no longer blocked
    store.purge_story_content(plan)
    assert generations(run.run_id) == []
    with api.sessions()() as db:  # a second sweep finds nothing left to do
        again = StoryVideoAdmissionService(
            SqlStoryVideoRepository(db), api.adapters
        ).reconcile_pending_admissions()
    assert again.cancelled_settled == 0


def test_cancel_with_a_pending_intent_that_the_ports_refuse_is_a_rejected_intent(
    api: VideoApi,
) -> None:
    run = new_script_run(api)
    api.script.quotas.append(QuotaStatus.UNAVAILABLE)
    generation_of(request(api, run))
    api.script.quotas.append(QuotaStatus.QUOTA_EXCEEDED)
    assert cancel(api, run).status_code == 202  # the hook resolves it: refused, not consumed
    (row,) = generations(run.run_id)
    assert row["state"] == "ADMISSION_REJECTED" and row["generation_no"] is None
    assert row["compute_released_at"] is not None
    assert run_row(run.run_id)["run_state"] == "DELETE_PENDING"  # not moved back to review
    SqlStoryLifecycleStore(api.sessions()).plan_story_purge(run.run_id)


@pytest.mark.parametrize(
    "stop_after",
    ["ACCEPTED", "QUEUED", "GENERATING", "TECHNICAL_VALIDATING", "SAFETY_VALIDATING"],
)
def test_cancel_in_each_in_flight_state_fails_the_generation_and_the_purge_proceeds(
    api: VideoApi, stop_after: str
) -> None:
    run, generation = accepted(api)
    gid = generation["generation_id"]
    fixture = runner(api)
    while generations(run.run_id)[0]["state"] != stop_after:
        assert fixture.step(gid).applied
    started = generations(run.run_id)[0]["started_at"] is not None
    assert cancel(api, run).status_code == 202
    (row,) = generations(run.run_id)
    assert row["state"] == "FAILED" and row["safe_failure_code"] == "RUN_CANCELLED"
    assert row["compute_released_at"] is not None
    calls = [call[0] for call in api.reservation.calls]
    assert ("settle:FAILED" in calls) is started and ("release" in calls) is not started
    assert {scene["state"] for scene in scenes_of(gid)} <= {"FAILED", "READY"}
    # a late worker result is a recorded no-op, never a move
    late = fixture.step(gid)
    assert late.applied is False
    assert generations(run.run_id)[0]["state"] == "FAILED"
    store = SqlStoryLifecycleStore(api.sessions())
    plan = store.plan_story_purge(run.run_id)
    store.purge_story_content(plan)
    assert generations(run.run_id) == [] and scenes_of(gid) == []


def test_cancel_after_ready_purges_the_video_row_and_its_asset(api: VideoApi) -> None:
    run, generation = accepted(api)
    gid = generation["generation_id"]
    final = runner(api).run_to_end(gid)
    assert final.record is not None and final.record.state == "READY"
    key = generations(run.run_id)[0]["output_asset_ref"]
    assert key in api.storage.objects
    assert cancel(api, run).status_code == 202
    assert generations(run.run_id)[0]["state"] == "READY"  # settled: nothing to resolve
    scope = LifecycleScope("PARENT_ACCOUNT", parent_scope_ref(principal_of(run.owner)))
    purge = SqlCoreRunAssetPurge(api.sessions(), api.storage)
    plan = build_plan(purge.closure_candidates(scope, run.run_id), frozenset())
    assert key in {item.asset_ref for item in plan.removable} and not plan.retained
    purge.purge_objects(plan)
    assert purge.sweep_run_prefix(scope, run.run_id).swept_count == 0
    purge.delete_rows(plan, frozenset())
    store = SqlStoryLifecycleStore(api.sessions())
    store.purge_story_content(store.plan_story_purge(run.run_id))
    assert generations(run.run_id) == [] and api.storage.list_keys(f"parent/{run.run_id}/") == ()


# ======================================================================== progress (fixture runner)
def test_the_fixture_runner_walks_a_request_to_ready_with_an_asset_and_a_new_wait(
    api: VideoApi,
) -> None:
    run, generation = accepted(api)
    gid = generation["generation_id"]
    fixture = runner(api)
    seen: list[tuple[str, str]] = []
    for _ in range(12):
        row = generations(run.run_id)[0]
        seen.append((row["state"], run_row(run.run_id)["run_state"]))
        if row["state"] == "READY":
            break
        assert fixture.step(gid).applied
    assert seen == [
        ("ACCEPTED", "VIDEO_QUEUED"),
        ("QUEUED", "VIDEO_QUEUED"),
        ("GENERATING", "VIDEO_GENERATING"),
        ("TECHNICAL_VALIDATING", "VIDEO_SAFETY_VALIDATING"),
        ("SAFETY_VALIDATING", "VIDEO_SAFETY_VALIDATING"),
        ("READY", "VIDEO_READY"),
    ]
    (row,) = generations(run.run_id)
    assert row["output_asset_ref"].startswith(f"parent/{run.run_id}/video/{gid}/")
    assert row["output_asset_version"] == 1 and row["completed_at"] is not None
    assert (
        row["technical_validation_state"],
        row["consistency_validation_state"],
        row["safety_validation_state"],
    ) == ("PASSED", "PASSED", "PASSED")
    assert row["started_at"] is not None and row["compute_released_at"] is not None
    assert "settle:COMPLETED" in [call[0] for call in api.reservation.calls]
    after = run_row(run.run_id)
    assert after["run_state"] == "VIDEO_READY" and after["job_state"] == "SUCCEEDED"
    assert after["adult_wait_started_at"] is not None  # READY waits for the adult
    assert {scene["state"] for scene in scenes_of(gid)} == {"READY"}
    with api.sessions()() as db:
        assets = [
            asset
            for asset in db.scalars(select(CoreAssetMetadataModel)).all()
            if run.run_id in asset.source_refs
        ]
    assert [asset.asset_ref for asset in assets] == [row["output_asset_ref"]]
    assert assets[0].owner_scope_kind == "PARENT_ACCOUNT" and assets[0].media_type == "video/mp4"
    assert api.storage.objects[row["output_asset_ref"]][1] == "video/mp4"
    assert fixture.step(gid).reason == "SETTLED"  # a settled request never moves again


def test_a_blocked_video_waits_for_the_adult_and_a_failed_one_frees_the_lock(
    api: VideoApi,
) -> None:
    blocked_run, blocked = accepted(api)
    renderer = FixtureVideoRenderer()
    renderer.results[blocked["generation_id"]] = VideoRenderResult(
        content=b"x", media_type="video/mp4", safety_passed=False, safety_finding_codes=("F-1",)
    )
    final = runner(api, renderer).run_to_end(blocked["generation_id"])
    assert final.record is not None and final.record.state == "SAFETY_BLOCKED"
    row = generations(blocked_run.run_id)[0]
    assert row["safety_validation_state"] == "FAILED" and row["safety_finding_codes"] == ["F-1"]
    assert row["output_asset_ref"] is None
    state = run_row(blocked_run.run_id)
    assert state["run_state"] == "SAFETY_BLOCKED" and state["adult_wait_started_at"] is not None
    assert state["active_owner_parent_account_id"] is not None

    failed_run, failing = accepted(api, new_script_run(api, owner=api.other_parent))
    renderer.results[failing["generation_id"]] = VideoRenderResult(
        content=b"", media_type="video/mp4", failure_code="PROVIDER_FAILED"
    )
    done = runner(api, renderer).run_to_end(failing["generation_id"])
    assert done.record is not None and done.record.state == "FAILED"
    frow = generations(failed_run.run_id)[0]
    assert frow["safe_failure_code"] == "PROVIDER_FAILED" and frow["output_asset_ref"] is None
    fstate = run_row(failed_run.run_id)
    assert fstate["run_state"] == "FAILED" and fstate["job_state"] == "FAILED"
    assert fstate["active_owner_parent_account_id"] is None  # the active lock is released
    assert fstate["finished_at"] is not None and fstate["error_code"] == "PROVIDER_FAILED"
    # no refund: the usage ref is still there and the quota port was never asked again
    assert frow["billing_quota_usage_ref"] and len(api.quota.calls) == 2


def test_a_stale_progress_event_is_a_no_op(api: VideoApi) -> None:
    run, generation = accepted(api)
    gid = generation["generation_id"]
    with api.sessions()() as db:
        service = StoryVideoProgressService(SqlStoryVideoRepository(db), api.adapters)
        wrong = service.apply(
            gid, ProgressEvent(expected_state="GENERATING", target_state="TECHNICAL_VALIDATING")
        )
        assert wrong.applied is False and wrong.reason == "STALE"
        ok = service.apply(gid, ProgressEvent(expected_state="ACCEPTED", target_state="QUEUED"))
        assert ok.applied
        again = service.apply(gid, ProgressEvent(expected_state="ACCEPTED", target_state="QUEUED"))
        assert again.applied is False
        with pytest.raises(ValueError):
            service.apply(
                gid,
                ProgressEvent(expected_state="QUEUED", target_state="READY"),
            )
    assert generations(run.run_id)[0]["state"] == "QUEUED"


# ============================================================================== job projection
def get_job(api: VideoApi, subject: str, job_id: str) -> Any:
    return api.client.get(f"/v1/jobs/{job_id}", headers=headers(subject))


def test_the_owner_polls_the_job_and_nobody_else_can(api: VideoApi) -> None:
    run, generation = accepted(api)
    job_id = generation["job_id"]
    response = get_job(api, run.owner, job_id)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["job_id"] == job_id and body["target_kind"] == "VIDEO_GENERATION"
    assert body["target_ref"] == generation["generation_id"]
    assert body["state"] == "queued" and body["attempt_number"] == 1
    assert body["input_hash"] == run.story_sha256 and body["target_revision"] == 1
    assert body["job_revision"] == generations(run.run_id)[0]["generation_revision"]
    assert body["result_refs"] == [] and body["failure"] is None
    assert body["poll_after_ms"] is not None
    assert response.headers["ETag"]
    text_body = response.text.lower()
    for word in (*STORAGE_WORDS, "organization", "reservation", "usage"):
        assert word not in text_body, word
    uniform = {"code": "RESOURCE_NOT_FOUND", "retryable": False}
    for subject in (api.other_parent, api.teacher, api.manager, api.admin):
        denied = get_job(api, subject, job_id)
        assert denied.status_code == 404, subject
        assert {key: denied.json()[key] for key in uniform} == uniform
    missing = get_job(api, run.owner, "vjob_" + "0" * 32)
    assert missing.status_code == 404
    shapes = {
        json_shape(get_job(api, subject, job_id).json())
        for subject in (api.other_parent, api.teacher, api.manager, api.admin)
    } | {json_shape(missing.json())}
    assert len(shapes) == 1  # one shape for every refusal (SRS l.865)


def json_shape(body: dict[str, Any]) -> tuple[str, ...]:
    return tuple(sorted(f"{key}:{type(value).__name__}" for key, value in body.items()))


def test_the_job_follows_the_generation_to_every_public_state(api: VideoApi) -> None:
    run, generation = accepted(api)
    gid, job_id = generation["generation_id"], generation["job_id"]
    fixture = runner(api)
    expected = {
        "QUEUED": "queued",
        "GENERATING": "running",
        "TECHNICAL_VALIDATING": "running",
        "SAFETY_VALIDATING": "running",
        "READY": "succeeded",
    }
    for _ in range(5):
        assert fixture.step(gid).applied
        state = generations(run.run_id)[0]["state"]
        body = get_job(api, run.owner, job_id).json()
        assert body["state"] == expected[state], state
        assert body["result_refs"] == []
    assert body["result_disposition"] == "accepted" and body["poll_after_ms"] is None
    assert body["completed_at"] is not None and body["started_at"] is not None


def test_a_failed_and_a_blocked_job_show_a_safe_failure_and_a_closed_run_stays_readable(
    api: VideoApi,
) -> None:
    run, generation = accepted(api)
    renderer = FixtureVideoRenderer()
    renderer.results[generation["generation_id"]] = VideoRenderResult(
        content=b"", media_type="video/mp4", failure_code="PROVIDER_FAILED"
    )
    runner(api, renderer).run_to_end(generation["generation_id"])
    assert run_row(run.run_id)["active_owner_parent_account_id"] is None  # closed: no lock column
    body = get_job(api, run.owner, generation["job_id"]).json()
    assert body["state"] == "failed_exhausted"
    assert body["failure"]["code"] == "VIDEO_TECHNICAL_FAILURE"  # T-1c D8: the closed public set
    assert body["failure"]["retryable"] is False
    assert get_job(api, api.other_parent, generation["job_id"]).status_code == 404

    blocked_run, blocked = accepted(api, new_script_run(api))
    blocking = FixtureVideoRenderer()
    blocking.results[blocked["generation_id"]] = VideoRenderResult(
        content=b"x", media_type="video/mp4", safety_passed=False
    )
    runner(api, blocking).run_to_end(blocked["generation_id"])
    body = get_job(api, blocked_run.owner, blocked["job_id"]).json()
    assert body["state"] == "blocked_unsafe" and body["failure"]["code"] == "VIDEO_SAFETY_BLOCKED"


def test_an_intent_and_a_refused_request_are_not_jobs_and_a_purged_run_is_gone(
    api: VideoApi,
) -> None:
    pending_run = new_script_run(api)
    api.script.quotas.append(QuotaStatus.UNAVAILABLE)
    pending = generation_of(request(api, pending_run))
    assert pending["job_id"] is None
    refused_run = new_script_run(api, owner=api.other_parent)
    api.script.quotas.append(QuotaStatus.QUOTA_EXCEEDED)
    assert request(api, refused_run).status_code == 409
    assert generations(refused_run.run_id)[0]["job_ref"] is None
    # a purged run: the generation row is deleted with it
    run, generation = accepted(api)
    assert cancel(api, run).status_code == 202
    assert get_job(api, run.owner, generation["job_id"]).status_code == 404  # DELETE_PENDING
    store = SqlStoryLifecycleStore(api.sessions())
    store.purge_story_content(store.plan_story_purge(run.run_id))
    assert get_job(api, run.owner, generation["job_id"]).status_code == 404


class _StatementCounter:
    def __init__(self, engine: Any) -> None:
        self.engine = engine
        self.statements: list[str] = []

    def __enter__(self) -> _StatementCounter:
        event.listen(self.engine, "before_cursor_execute", self._record)
        return self

    def __exit__(self, *_exc: object) -> None:
        event.remove(self.engine, "before_cursor_execute", self._record)

    def _record(self, _conn: Any, _cursor: Any, statement: str, *_args: Any) -> None:
        self.statements.append(statement.lower())

    def count(self, needle: str) -> int:
        return sum(1 for statement in self.statements if needle in statement)


def test_a_missing_id_a_foreign_parent_and_an_organization_actor_each_cost_one_read(
    api: VideoApi,
) -> None:
    """T0.4-DEBT-2: the cost of a refusal does not tell the cases apart."""

    run, generation = accepted(api)
    job_id = generation["job_id"]
    engine = api.app.state.be1_runtime.engine
    get_job(api, run.owner, job_id)  # builds the lazy reader outside the counted window

    def costs(subject: str, requested: str) -> tuple[int, int]:
        with _StatementCounter(engine) as counter:
            assert get_job(api, subject, requested).status_code == 404
        return counter.count("video_generations"), counter.count("ai_jobs")

    missing_parent = costs(api.parent, "vjob_" + "9" * 32)
    foreign_parent = costs(api.other_parent, job_id)
    assert missing_parent == foreign_parent == (1, 0)
    organization_actor = {costs(api.teacher, job_id), costs(api.manager, job_id)}
    missing_for_org = costs(api.teacher, "vjob_" + "9" * 32)
    assert organization_actor == {missing_for_org}
    assert missing_for_org[0] == 0 and missing_for_org[1] >= 1  # one read of the other store


# ============================================================================== constraints
def _insert_generation(db: Any, run: ScriptRun, **override: Any) -> str:
    generation_id = str(uuid4())
    now = datetime.now(UTC)
    values: dict[str, Any] = {
        "video_generation_id": generation_id,
        "story_run_id": run.run_id,
        "story_revision_id": run.revision_ids[-1],
        "story_review_id": run.review_ids[-1],
        "generation_no": None,
        "generation_kind": "INITIAL",
        "state": "ADMISSION_PENDING",
        "request_idempotency_key_hash": sha(generation_id),
        "request_fingerprint_sha256": sha("fp" + generation_id),
        "target_script_hash": run.story_sha256,
        "admission_started_at": now,
        "created_at": now,
        "updated_at": now,
    }
    values.update(override)
    db.execute(insert(VG).values(**values))
    return generation_id


def _accepted_values(number: int = 1, **override: Any) -> dict[str, Any]:
    now = datetime.now(UTC)
    values: dict[str, Any] = {
        "state": "ACCEPTED",
        "generation_no": number,
        "accepted_at": now,
        "compute_reservation_ref": "res",
        "billing_quota_usage_ref": "usage",
        "job_ref": f"vjob_{uuid4().hex}",
    }
    values.update(override)
    return values


def _rejected(api: VideoApi, run: ScriptRun, name: str, **override: Any) -> None:
    with pytest.raises((IntegrityError, DataError)) as raised, api.sessions().begin() as db:
        _insert_generation(db, run, **override)
    assert name in str(raised.value), str(raised.value)[:300]


def test_the_database_refuses_bad_generation_rows(api: VideoApi) -> None:
    run = new_script_run(api)
    other = new_script_run(api, owner=api.other_parent)
    # ADMISSION_PENDING with a number, a job or a usage ref
    _rejected(api, run, "ck_vg_shape", generation_no=1)
    _rejected(api, run, "ck_vg_shape", job_ref="vjob_x")
    _rejected(api, run, "ck_vg_shape", billing_quota_usage_ref="u")
    # ADMISSION_REJECTED needs rejected_at and a code and no job
    _rejected(api, run, "ck_vg_shape", state="ADMISSION_REJECTED", safe_failure_code="X")
    _rejected(
        api, run, "ck_vg_failure_code", state="ADMISSION_REJECTED", rejected_at=datetime.now(UTC)
    )
    # an accepted row needs a number from 1 to 3, both refs and a job
    _rejected(api, run, "ck_vg_shape", **_accepted_values(4))
    _rejected(api, run, "ck_vg_shape", **_accepted_values(0))
    _rejected(api, run, "ck_vg_shape", **_accepted_values(compute_reservation_ref=None))
    _rejected(api, run, "ck_vg_shape", **_accepted_values(billing_quota_usage_ref=None))
    _rejected(api, run, "ck_vg_shape", **_accepted_values(job_ref=None))
    _rejected(api, run, "ck_vg_shape", **_accepted_values(rejected_at=datetime.now(UTC)))
    # READY needs the asset, three PASSED states and completed_at
    _rejected(
        api, run, "ck_vg_ready", **_accepted_values(state="READY", completed_at=datetime.now(UTC))
    )
    _rejected(
        api,
        run,
        "ck_vg_ready",
        **_accepted_values(
            state="READY",
            output_asset_ref="k",
            output_asset_version=1,
            completed_at=datetime.now(UTC),
            technical_validation_state="PASSED",
        ),
    )
    # a regeneration needs its reason, an adult rejection needs its reason, a failure its code
    _rejected(api, run, "ck_vg_reason", generation_kind="QUALITY_REGEN")
    _rejected(api, run, "ck_vg_rejected_by_adult", **_accepted_values(state="REJECTED_BY_ADULT"))
    _rejected(api, run, "ck_vg_failure_code", **_accepted_values(state="FAILED"))
    # states, kinds, validation states, hashes and the asset pair are closed sets
    _rejected(api, run, "ck_vg_state", **_accepted_values(state="DONE"))
    _rejected(api, run, "ck_vg_kind", generation_kind="OTHER")
    _rejected(api, run, "ck_vg_validation_states", safety_validation_state="MAYBE")
    _rejected(api, run, "ck_vg_hashes", target_script_hash="short")
    _rejected(api, run, "ck_vg_output", output_asset_ref="k")
    # the review of another run or another revision is not accepted (composite keys)
    _rejected(api, run, "fk_vg_story_review", story_review_id=other.review_ids[0])
    _rejected(api, run, "fk_vg_story_revision", story_revision_id=other.revision_ids[0])
    with api.sessions().begin() as db:
        _insert_generation(db, run)  # the legal row exists after all of the above
    assert len(generations(run.run_id)) == 1


def test_the_partial_uniques_allow_one_open_one_ready_one_review_use_and_one_number(
    api: VideoApi,
) -> None:
    run = new_script_run(api)
    with api.sessions().begin() as db:
        first = _insert_generation(
            db,
            run,
            state="ADMISSION_REJECTED",
            rejected_at=datetime.now(UTC),
            safe_failure_code="VIDEO_QUOTA_EXCEEDED",
        )
        # a rejected row does not use the review: a second rejected row and an open one are fine
        _insert_generation(
            db,
            run,
            state="ADMISSION_REJECTED",
            rejected_at=datetime.now(UTC),
            safe_failure_code="VIDEO_QUOTA_EXCEEDED",
        )
        open_id = _insert_generation(db, run)
    assert first and open_id
    # a second open row on the run, or another use of the review, is refused
    with pytest.raises(IntegrityError, match="uq_vg_one_open"), api.sessions().begin() as db:
        _insert_generation(db, run)
    with api.sessions().begin() as db:
        db.execute(
            update(VG)
            .where(VG.c.video_generation_id == open_id)
            .values(
                **_accepted_values(1, state="FAILED", completed_at=datetime.now(UTC)),
                safe_failure_code="X",
            )
        )
    # the review is spent by the settled accepted row
    with pytest.raises(IntegrityError, match="uq_vg_review_consumed"), api.sessions().begin() as db:
        _insert_generation(db, run)
    # the generation number is unique per run
    other_run = new_script_run(api, prior=1)
    with pytest.raises(IntegrityError, match="uq_vg_number"), api.sessions().begin() as db:
        _insert_generation(
            db,
            other_run,
            **_accepted_values(1, state="FAILED", completed_at=datetime.now(UTC)),
            safe_failure_code="X",
        )
    # one READY per run
    ready_run = new_script_run(api, prior=1)
    ready_values = _accepted_values(
        state="READY",
        output_asset_ref="k",
        output_asset_version=1,
        completed_at=datetime.now(UTC),
        technical_validation_state="PASSED",
        consistency_validation_state="PASSED",
        safety_validation_state="PASSED",
    )
    with api.sessions().begin() as db:
        db.execute(
            update(VG)
            .where(VG.c.video_generation_id == ready_run.generation_ids[0])
            .values(**{**ready_values, "generation_no": 1, "job_ref": f"vjob_{uuid4().hex}"})
        )
    with pytest.raises(IntegrityError, match="uq_vg_one_ready"), api.sessions().begin() as db:
        _insert_generation(
            db,
            ready_run,
            **{**ready_values, "generation_no": 2, "job_ref": f"vjob_{uuid4().hex}"},
        )


def test_the_key_and_the_job_ref_are_unique_and_the_scene_keys_are_composite(
    api: VideoApi,
) -> None:
    run = new_script_run(api)
    with api.sessions().begin() as db:
        first = _insert_generation(db, run)
    stored = generations(run.run_id)[0]
    with pytest.raises(IntegrityError, match="uq_vg_run_key"), api.sessions().begin() as db:
        _insert_generation(
            db,
            run,
            state="ADMISSION_REJECTED",
            rejected_at=datetime.now(UTC),
            safe_failure_code="X",
            request_idempotency_key_hash=stored["request_idempotency_key_hash"],
        )
    # a scene of another revision cannot be pinned to this generation
    other = new_script_run(api, owner=api.other_parent)
    with api.sessions()() as db:
        foreign_scene = db.scalar(
            select(story_tables.story_scenes.c.scene_id).where(
                story_tables.story_scenes.c.story_revision_id == other.revision_ids[0]
            )
        )
        own_scene = db.scalar(
            select(story_tables.story_scenes.c.scene_id).where(
                story_tables.story_scenes.c.story_revision_id == run.revision_ids[0]
            )
        )
    with pytest.raises(IntegrityError, match="fk_vgs_scene"), api.sessions().begin() as db:
        db.execute(
            insert(VGS).values(
                generation_scene_id=str(uuid4()),
                video_generation_id=first,
                story_revision_id=run.revision_ids[0],
                story_scene_id=foreign_scene,
                state="QUEUED",
            )
        )
    with pytest.raises(IntegrityError, match="fk_vgs_generation"), api.sessions().begin() as db:
        db.execute(
            insert(VGS).values(
                generation_scene_id=str(uuid4()),
                video_generation_id=first,
                story_revision_id=other.revision_ids[0],  # not the revision pinned on the row
                story_scene_id=own_scene,
                state="QUEUED",
            )
        )
    with api.sessions().begin() as db:
        db.execute(
            insert(VGS).values(
                generation_scene_id=str(uuid4()),
                video_generation_id=first,
                story_revision_id=run.revision_ids[0],
                story_scene_id=own_scene,
                state="QUEUED",
            )
        )
    with (
        pytest.raises(IntegrityError, match="uq_vgs_generation_scene"),
        api.sessions().begin() as db,
    ):
        db.execute(
            insert(VGS).values(
                generation_scene_id=str(uuid4()),
                video_generation_id=first,
                story_revision_id=run.revision_ids[0],
                story_scene_id=own_scene,
                state="QUEUED",
            )
        )
    with pytest.raises(IntegrityError, match="ck_vgs_clip"), api.sessions().begin() as db:
        db.execute(
            update(VGS)
            .where(VGS.c.video_generation_id == first)
            .values(clip_asset_ref="only-the-ref")
        )


def test_the_run_pointer_is_set_null_with_its_generation_and_always_names_its_own_run(
    api: VideoApi,
) -> None:
    run, generation = accepted(api)
    row = run_row(run.run_id)
    assert row["current_video_generation_id"] == generation["generation_id"]
    for item in generations(run.run_id):
        assert item["story_run_id"] == run.run_id  # the code never points at another run's row
    with api.sessions().begin() as db:
        db.execute(delete_scenes(generation["generation_id"]))
        db.execute(delete_generation(generation["generation_id"]))
    assert run_row(run.run_id)["current_video_generation_id"] is None  # ON DELETE SET NULL


def delete_scenes(generation_id: str) -> Any:
    return VGS.delete().where(VGS.c.video_generation_id == generation_id)


def delete_generation(generation_id: str) -> Any:
    return VG.delete().where(VG.c.video_generation_id == generation_id)


def test_the_new_run_states_and_receipt_operations_are_accepted_and_others_refused(
    api: VideoApi,
) -> None:
    run = new_script_run(api)
    for state in (
        "VIDEO_QUEUED",
        "VIDEO_GENERATING",
        "VIDEO_SAFETY_VALIDATING",
        "VIDEO_READY",
        "SAFETY_BLOCKED",
        "ABANDONED",
    ):
        with api.sessions().begin() as db:
            db.execute(update(RUNS).where(RUNS.c.run_id == run.run_id).values(run_state=state))
    for state in ("DRAFT", "STORY_GENERATING", "VIDEO_DONE"):
        with (
            pytest.raises(IntegrityError, match="ck_story_run_state"),
            api.sessions().begin() as db,
        ):
            db.execute(update(RUNS).where(RUNS.c.run_id == run.run_id).values(run_state=state))
    for operation in ("CREATE_VIDEO_GENERATION", "MARK_VIDEO_UNSUITABLE", "COMPLETE_RUN"):
        with api.sessions().begin() as db:
            _receipt(db, run.run_id, "a" * 64, operation)
    with (
        pytest.raises(IntegrityError, match="ck_story_receipt_operation"),
        api.sessions().begin() as db,
    ):
        _receipt(db, run.run_id, "a" * 64, "SOMETHING_ELSE")


def test_the_purge_sees_the_video_tables_as_child_rows(api: VideoApi) -> None:
    run, generation = accepted(api)
    assert cancel(api, run).status_code == 202
    plan = SqlStoryLifecycleStore(api.sessions())
    # the generation is in flight and the hook failed it: it is settled, so the plan is available
    ids = plan.plan_story_purge(run.run_id).ids
    kinds = [item.split(":")[0] for item in ids]
    assert kinds.count("video_generations") == 1 and kinds.count("video_generation_scenes") == 3
    assert any(item == f"video_generations:{generation['generation_id']}" for item in ids)
    assert "run:" + run.run_id in ids  # the run pointer counts as run-owned content
    plan.purge_story_content(plan.plan_story_purge(run.run_id))
    assert plan.plan_story_purge(run.run_id).empty
    assert scenes_of(generation["generation_id"]) == []
    # the receipt of the request is tombstoned like every other non-lifecycle receipt (DTR S12)
    (receipt,) = receipts(run.run_id)
    assert receipt["request_fingerprint_sha256"] != sha("anything-the-client-sent")


def test_the_event_and_the_audit_of_the_lifecycle_are_untouched_by_a_video_request(
    api: VideoApi,
) -> None:
    run, _generation = accepted(api)
    with api.sessions()() as db:
        count = db.scalar(
            text("select count(*) from core_outbox_events where aggregate_id = :run"),
            {"run": run.run_id},
        )
    assert count == 0  # a video request writes no lifecycle event (the cancel does)
