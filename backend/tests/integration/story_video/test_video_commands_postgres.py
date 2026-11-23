"""FEAT-066 T-1b: ``video-unsuitable`` and ``complete`` on PostgreSQL (SRS l.1671-1672).

SRS l.395 and l.518 (the rejected video is hidden, kept internally until the run is deleted),
l.503 and FR-C-08 (the active lock is released at the end), l.573 (three requests), l.1671
(``video-unsuitable``), l.1672 (``complete``), l.1697-1699 (idempotency, stale protection). Runs
only against a disposable database whose name contains ``be1_acceptance`` and ``frc08_v3_t1b``.
The two admission ports are the local/test pair; object storage is in memory; no provider is
called. A run is built by direct inserts (a confirmed script with schema-valid content, its review,
its scenes) and a video is made ``READY`` through the real ``video-generations`` route and the
fixture runner, so the whole chain of T-1a is exercised.
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
from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError

from sketch2life.application.ports.core_foundation import LifecycleScope
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.object_storage import StoredObject
from sketch2life.application.ports.parent_story_inputs import StoryGenerationResult
from sketch2life.application.ports.story_video import StoryVideoAdapters, VideoRenderResult
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel
from sketch2life.infrastructure.persistence.core_lifecycle_store import (
    SqlCoreRunAssetPurge,
    build_plan,
)
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
from sketch2life.infrastructure.uploads.resolvers import parent_scope_ref
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult
from tests.unit.test_story_output import valid_story

ISSUER = "synthetic-t1b-issuer"
STORAGE_WORDS = ("bucket", "object_key", "presigned", "s3mock", "parent/", "output.mp4")
VG = story_tables.video_generations
RUNS = story_tables.story_runs
RECEIPTS = story_tables.story_command_receipts
UNSUITABLE = "MARK_VIDEO_UNSUITABLE"
COMPLETE = "COMPLETE_RUN"


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
    if "be1_acceptance" not in database_name or "frc08_v3_t1b" not in database_name:
        pytest.fail("BE1_TEST_DATABASE_URL must be a disposable frc08_v3_t1b*be1_acceptance db")
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
        "parent": f"synthetic-t1b-parent-{token}",
        "other_parent": f"synthetic-t1b-parent2-{token}",
        "teacher": f"synthetic-t1b-teacher-{token}",
        "manager": f"synthetic-t1b-manager-{token}",
        "admin": f"synthetic-t1b-admin-{token}",
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
        RECEIPTS.insert().values(
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


def _add_revision(
    db: Any, run_id: str, scope_ref: str, number: int, status: str, made: ScriptRun
) -> None:
    """One story revision with five schema-valid scenes and the review that confirmed it."""

    now = datetime.now(UTC)
    revision_id = str(uuid4())
    story_hash = sha(f"story-{run_id}-{number}")
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
            story_content={"opening": "mo dau", "middle": "giua", "ending": "ket"},
            schema_version="sketch2life.story-revision.v1",
            prompt_version="synthetic-prompt",
            model_id="synthetic-model",
            model_revision="1",
            request_sha256="e" * 64,
            created_at=now,
        )
    )
    for index in range(1, 6):
        db.execute(
            story_tables.story_scenes.insert().values(
                scene_id=str(uuid4()),
                story_revision_id=revision_id,
                scene_index=index,
                title=f"Scene {index}",
                action="action",
                visual_prompt="prompt",
                narration="narration",
                start_ms=(index - 1) * 12000,
                duration_ms=12000,
                character_anchors=[],
            )
        )
    made.revision_ids.append(revision_id)
    made.story_sha256 = story_hash
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


def new_script_run(
    api: VideoApi,
    owner: str | None = None,
    *,
    prior: int = 0,
    run_state: str = "SCRIPT_REVIEW",
    hold_slot: bool | None = None,
) -> ScriptRun:
    """A run at its script review: ``prior`` spent revisions (each with a FAILED accepted
    generation numbered 1..prior), then one confirmed revision with its review and scenes. The
    run content is schema-valid, so a run envelope can be built from it."""

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
                subject_label="dragon",
                understanding_revision=1,
                current_input_revision=1,
                active_owner_parent_account_id=str(account_id) if hold_slot else None,
                adult_wait_started_at=now,
                created_at=now,
                updated_at=now,
            )
        )
        profile_revision = str(uuid4())
        db.execute(
            story_tables.run_inputs.insert().values(
                run_input_id=str(uuid4()),
                run_id=run_id,
                input_revision=1,
                typed_idea="a friendly dragon",
                idea_source="TEXT",
                source_profile_revision_ref=profile_revision,
                context_revision=1,
                context_snapshot={
                    "schema_version": "sketch2life.parent-context.v1",
                    "profile_revision_ref": profile_revision,
                    "age_months": 72,
                    "interests_summary": "",
                    "topic": "",
                    "adult_confirmed_idea": "",
                },
                context_snapshot_sha256="c" * 64,
                context_confirmed_by=scope_ref,
                context_confirmed_at=now,
                created_at=now,
            )
        )
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
        for number in range(1, prior + 2):
            latest = number == prior + 1
            _add_revision(
                db, run_id, scope_ref, number, "CONFIRMED" if latest else "SUPERSEDED", made
            )
            if latest:
                continue
            generation_id = str(uuid4())
            db.execute(
                insert(VG).values(
                    video_generation_id=generation_id,
                    story_run_id=run_id,
                    story_revision_id=made.revision_ids[-1],
                    story_review_id=made.review_ids[-1] if made.review_ids else None,
                    generation_no=number,
                    generation_kind="INITIAL" if number == 1 else "QUALITY_REGEN",
                    state="FAILED",
                    request_idempotency_key_hash=sha(f"prior-{generation_id}"),
                    request_fingerprint_sha256=sha(f"fp-{generation_id}"),
                    target_script_hash=made.story_sha256,
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


def add_confirmed_revision(api: VideoApi, run: ScriptRun) -> None:
    """The next revision, confirmed with its own review, inserted directly (a shortcut for tests
    that are not about the rewrite route; ``rewrite_and_confirm`` goes through the real routes)."""

    with api.sessions().begin() as db:
        number = int(
            db.scalar(
                select(story_tables.story_revisions.c.revision_no)
                .where(story_tables.story_revisions.c.run_id == run.run_id)
                .order_by(story_tables.story_revisions.c.revision_no.desc())
                .limit(1)
            )
        )
        _add_revision(
            db, run.run_id, parent_scope_ref(principal_of(run.owner)), number + 1, "CONFIRMED", run
        )


class RewriteGenerator:
    """Answers every rewrite with a schema-valid draft (the story generator double of T-2d)."""

    def __init__(self) -> None:
        self.calls = 0

    def generate(self, worker_input: Any) -> StoryGenerationResult:
        self.calls += 1
        story = valid_story()
        story["title"] = f"Rong nho lan {self.calls}"
        return StoryGenerationResult(story, f"call-{self.calls}", "fixture-model", "1")


def make_rewritable(api: VideoApi, run: ScriptRun) -> RewriteGenerator:
    """What ``story-rewrites`` needs beyond the confirmed script: a drawing on the current input
    and an understanding revision with visible features; and the generator double composed."""

    now = datetime.now(UTC)
    with api.sessions().begin() as db:
        input_row = (
            db.execute(
                select(story_tables.run_inputs).where(
                    story_tables.run_inputs.c.run_id == run.run_id
                )
            )
            .mappings()
            .one()
        )
        db.execute(
            update(story_tables.run_inputs)
            .where(story_tables.run_inputs.c.run_input_id == input_row["run_input_id"])
            .values(
                original_asset_ref=f"synthetic/{run.run_id}/original",
                original_asset_version=1,
                original_sha256=sha(f"original-{run.run_id}"),
                original_media_type="image/png",
                original_size_bytes=100,
                derived_asset_ref=f"synthetic/{run.run_id}/normalized.png",
                derived_asset_version=1,
                derived_sha256=sha(f"derived-{run.run_id}"),
                derived_media_type="image/png",
                derived_size_bytes=90,
            )
        )
        db.execute(
            story_tables.understanding_revisions.insert().values(
                understanding_revision_id=str(uuid4()),
                run_id=run.run_id,
                run_input_id=input_row["run_input_id"],
                revision_no=1,
                subject_label="dragon",
                confidence=0.9,
                canonical_result_sha256="d" * 64,
                result_snapshot={
                    "result": {
                        "candidate_subject": "dragon",
                        "visible_features": ["wings", "tail"],
                        "confidence": 0.9,
                        "adult_confirmation_required": True,
                        "decision": "REVIEW_REQUIRED",
                    }
                },
                created_at=now,
            )
        )
    generator = RewriteGenerator()
    api.app.state.story_generator = generator
    return generator


def story_rows(run_id: str) -> list[Any]:
    assert _API is not None
    with _API.sessions()() as db:
        return list(
            db.execute(
                select(story_tables.story_revisions)
                .where(story_tables.story_revisions.c.run_id == run_id)
                .order_by(story_tables.story_revisions.c.revision_no)
            )
            .mappings()
            .all()
        )


def rewrite_route(api: VideoApi, run: ScriptRun, *, key: str | None = None) -> Any:
    latest = story_rows(run.run_id)[-1]
    return api.client.post(
        f"/v1/story-runs/{run.run_id}/story-rewrites",
        json={"expected_story_revision": int(latest["revision_no"])},
        headers=headers(run.owner, key or uuid4().hex),
    )


def confirm_route(api: VideoApi, run: ScriptRun) -> Any:
    latest = story_rows(run.run_id)[-1]
    run.story_sha256 = str(latest["story_sha256"])
    return api.client.post(
        f"/v1/story-runs/{run.run_id}/script-confirmation",
        json={
            "expected_revision": int(latest["revision_no"]),
            "story_sha256": latest["story_sha256"],
        },
        headers=headers(run.owner, uuid4().hex),
    )


def rewrite_and_confirm(api: VideoApi, run: ScriptRun) -> None:
    """The adult's way back after a rejected video: a rewrite, then the confirmation of it."""

    rewritten = rewrite_route(api, run)
    assert rewritten.status_code == 202, rewritten.text
    assert run_row(run.run_id)["run_state"] == "SCRIPT_REVIEW"  # the generator ran
    assert story_rows(run.run_id)[-1]["status"] == "DRAFT"
    confirmed = confirm_route(api, run)
    assert confirmed.status_code == 200, confirmed.text
    assert story_rows(run.run_id)[-1]["status"] == "CONFIRMED"


def regenerate(api: VideoApi, run: ScriptRun, *, reason: str = "QUALITY_LOW") -> str:
    """Rewrite, confirm, ask for the next video and render it; returns its generation id."""

    rewrite_and_confirm(api, run)
    response = video_request(api, run, reason=reason)
    assert response.status_code == 202, response.text
    generation_id = str(response.json()["video_generation"]["generation_id"])
    final = runner(api).run_to_end(generation_id)
    assert final.record is not None and final.record.state == "READY"
    assert run_row(run.run_id)["run_state"] == "VIDEO_READY"
    return generation_id


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
                .order_by(VG.c.generation_no, VG.c.created_at)
            )
            .mappings()
            .all()
        )


def receipts(run_id: str, operation: str) -> list[Any]:
    assert _API is not None
    with _API.sessions()() as db:
        return list(
            db.execute(
                select(RECEIPTS).where(
                    RECEIPTS.c.resource_ref == run_id, RECEIPTS.c.operation == operation
                )
            )
            .mappings()
            .all()
        )


def code_of(response: Any) -> str:
    return str(response.json()["code"])


def video_request(api: VideoApi, run: ScriptRun, *, reason: str | None = None) -> Any:
    payload: dict[str, Any] = {
        "expected_revision": int(run_row(run.run_id)["revision"]),
        "story_sha256": run.story_sha256,
    }
    if reason is not None:
        payload["quality_reason_code"] = reason
    return api.client.post(
        f"/v1/story-runs/{run.run_id}/video-generations",
        json=payload,
        headers=headers(run.owner, uuid4().hex),
    )


def runner(api: VideoApi, renderer: Any = None) -> FixtureVideoRunner:
    return FixtureVideoRunner(api.sessions(), api.storage, api.adapters, renderer)


def video_ready(
    api: VideoApi, run: ScriptRun | None = None, *, reason: str | None = None
) -> tuple[ScriptRun, str]:
    """A run whose current video is READY, made by the real route and the fixture runner."""

    run = run or new_script_run(api)
    response = video_request(api, run, reason=reason)
    assert response.status_code == 202, response.text
    generation_id = str(response.json()["video_generation"]["generation_id"])
    final = runner(api).run_to_end(generation_id)
    assert final.record is not None and final.record.state == "READY"
    assert run_row(run.run_id)["run_state"] == "VIDEO_READY"
    return run, generation_id


def unsuitable(
    api: VideoApi,
    run: ScriptRun,
    generation_id: str,
    *,
    owner: str | None = None,
    key: str | None = None,
    revision: int | None = None,
    reason: str = "QUALITY_LOW",
) -> Any:
    expected = revision if revision is not None else int(run_row(run.run_id)["revision"])
    return api.client.post(
        f"/v1/story-runs/{run.run_id}/video-unsuitable",
        json={
            "expected_revision": expected,
            "generation_id": generation_id,
            "reason_code": reason,
        },
        headers=headers(owner or run.owner, key or uuid4().hex),
    )


def complete(
    api: VideoApi,
    run: ScriptRun,
    *,
    owner: str | None = None,
    key: str | None = None,
    revision: int | None = None,
) -> Any:
    expected = revision if revision is not None else int(run_row(run.run_id)["revision"])
    return api.client.post(
        f"/v1/story-runs/{run.run_id}/complete",
        json={"expected_revision": expected},
        headers=headers(owner or run.owner, key or uuid4().hex),
    )


def cancel(api: VideoApi, run: ScriptRun) -> Any:
    return api.client.post(
        f"/v1/story-runs/{run.run_id}/cancel",
        json={"expected_revision": int(run_row(run.run_id)["revision"])},
        headers=headers(run.owner, uuid4().hex),
    )


def _parallel(count: int, work: Callable[[int], Any]) -> list[Any]:
    barrier = Barrier(count)

    def start(index: int) -> Any:
        barrier.wait()
        return work(index)

    with ThreadPoolExecutor(max_workers=count) as pool:
        return [future.result() for future in [pool.submit(start, i) for i in range(count)]]


def snapshot(run_id: str) -> tuple[Any, ...]:
    """Everything a refused command must leave untouched."""

    row = run_row(run_id)
    return (
        row["run_state"],
        row["revision"],
        row["version"],
        row["active_owner_parent_account_id"],
        row["adult_wait_started_at"],
        row["current_video_generation_id"],
        tuple(
            (g["state"], g["generation_revision"], g["rejection_reason_code"])
            for g in generations(run_id)
        ),
    )


def purge_everything(api: VideoApi, run: ScriptRun) -> None:
    """The asset closure, then the story content, as the lifecycle consumer would."""

    scope = LifecycleScope("PARENT_ACCOUNT", parent_scope_ref(principal_of(run.owner)))
    purge = SqlCoreRunAssetPurge(api.sessions(), api.storage)
    plan = build_plan(purge.closure_candidates(scope, run.run_id), frozenset())
    purge.purge_objects(plan)
    purge.delete_rows(plan, frozenset())
    store = SqlStoryLifecycleStore(api.sessions())
    store.purge_story_content(store.plan_story_purge(run.run_id))


# ============================================================================== video-unsuitable
def test_unsuitable_returns_the_run_to_the_script_review_and_rejects_the_generation(
    api: VideoApi,
) -> None:
    run, gid = video_ready(api)
    before = run_row(run.run_id)
    generation_before = generations(run.run_id)[0]
    asset = generation_before["output_asset_ref"]
    reservation_calls = list(api.reservation.calls)
    response = unsuitable(api, run, gid, reason="NOT_MATCHING_STORY")
    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body) == {"request_id", "story_run"}
    assert body["story_run"]["run_state"] == "SCRIPT_REVIEW"
    assert body["story_run"]["run_revision"] == before["revision"] + 1
    assert body["story_run"]["story_status"] == "CONFIRMED"
    assert response.headers["Content-Location"] == f"/v1/story-runs/{run.run_id}"
    (row,) = generations(run.run_id)
    assert row["state"] == "REJECTED_BY_ADULT"
    assert row["rejection_reason_code"] == "NOT_MATCHING_STORY"
    assert row["generation_revision"] == generation_before["generation_revision"] + 1
    # hidden from the product, kept internally until the run is deleted (l.395, l.518)
    assert row["output_asset_ref"] == asset and asset in api.storage.objects
    after = run_row(run.run_id)
    assert after["run_state"] == "SCRIPT_REVIEW" and after["job_state"] == "SUCCEEDED"
    assert after["revision"] == before["revision"] + 1 and after["version"] == before["version"] + 1
    assert after["adult_wait_started_at"] is not None
    assert after["adult_wait_started_at"] > before["adult_wait_started_at"]
    assert after["last_meaningful_activity_at"] is not None
    assert after["active_owner_parent_account_id"] == before["active_owner_parent_account_id"]
    assert after["current_video_generation_id"] == gid and after["finished_at"] is None
    (receipt,) = receipts(run.run_id, UNSUITABLE)
    assert receipt["state"] == "FINAL" and receipt["response_status"] == 200
    assert set(receipt["response_body"]) == {"decision", "generation_id", "run_state"}
    # the compute reservation was settled at READY: no port is called again
    assert api.reservation.calls == reservation_calls


def test_the_answer_carries_no_storage_url_or_provider_detail(api: VideoApi) -> None:
    run, gid = video_ready(api)
    text_body = unsuitable(api, run, gid).text.lower()
    for word in (*STORAGE_WORDS, "http", "ptk1", "reservation", "usage", "balance"):
        assert word not in text_body, word


def test_replaying_the_same_key_and_payload_repeats_the_answer_without_a_second_change(
    api: VideoApi,
) -> None:
    run, gid = video_ready(api)
    key = uuid4().hex
    revision = int(run_row(run.run_id)["revision"])
    first = unsuitable(api, run, gid, key=key, revision=revision)
    second = unsuitable(api, run, gid, key=key, revision=revision)
    assert first.status_code == 200 and second.status_code == 200
    assert second.json()["story_run"]["run_state"] == "SCRIPT_REVIEW"
    assert len(receipts(run.run_id, UNSUITABLE)) == 1
    assert run_row(run.run_id)["revision"] == revision + 1  # moved once


def test_the_same_key_with_another_payload_is_an_idempotency_error(api: VideoApi) -> None:
    run, gid = video_ready(api)
    key = uuid4().hex
    revision = int(run_row(run.run_id)["revision"])
    assert unsuitable(api, run, gid, key=key, revision=revision).status_code == 200
    other_reason = unsuitable(api, run, gid, key=key, revision=revision, reason="OTHER")
    assert other_reason.status_code == 400 and code_of(other_reason) == "INVALID_IDEMPOTENCY_KEY"
    other_revision = unsuitable(api, run, gid, key=key, revision=revision + 5)
    assert other_revision.status_code == 400
    assert code_of(other_revision) == "INVALID_IDEMPOTENCY_KEY"
    assert len(receipts(run.run_id, UNSUITABLE)) == 1


def test_a_missing_or_malformed_key_is_a_plain_400_before_any_lookup(api: VideoApi) -> None:
    run, gid = video_ready(api)
    path = f"/v1/story-runs/{run.run_id}/video-unsuitable"
    body = {
        "expected_revision": int(run_row(run.run_id)["revision"]),
        "generation_id": gid,
        "reason_code": "QUALITY_LOW",
    }
    missing = api.client.post(path, json=body, headers=headers(run.owner))
    assert missing.status_code == 400 and code_of(missing) == "INVALID_REQUEST"
    malformed = api.client.post(path, json=body, headers=headers(run.owner, "bad key"))
    assert malformed.status_code == 400 and code_of(malformed) == "INVALID_REQUEST"
    unknown = api.client.post(
        f"/v1/story-runs/{uuid4()}/video-unsuitable",
        json=body,
        headers=headers(run.owner, "bad key"),
    )
    assert unknown.status_code == 400 and code_of(unknown) == "INVALID_REQUEST"
    assert run_row(run.run_id)["run_state"] == "VIDEO_READY"


def test_another_parent_or_another_role_gets_the_uniform_404_and_nothing_changes(
    api: VideoApi,
) -> None:
    run, gid = video_ready(api)
    before = snapshot(run.run_id)
    for subject in (api.other_parent, api.teacher, api.manager, api.admin):
        response = unsuitable(api, run, gid, owner=subject)
        assert response.status_code == 404 and code_of(response) == "RESOURCE_NOT_FOUND", subject
    unknown = api.client.post(
        f"/v1/story-runs/{uuid4()}/video-unsuitable",
        json={"expected_revision": 6, "generation_id": gid, "reason_code": "OTHER"},
        headers=headers(api.parent, uuid4().hex),
    )
    assert unknown.status_code == 404 and code_of(unknown) == "RESOURCE_NOT_FOUND"
    assert snapshot(run.run_id) == before and receipts(run.run_id, UNSUITABLE) == []


def test_a_stale_run_revision_is_409_with_the_current_version_and_changes_nothing(
    api: VideoApi,
) -> None:
    run, gid = video_ready(api)
    before = snapshot(run.run_id)
    current = int(run_row(run.run_id)["revision"])
    for stale in (current - 1, current + 1, 1):
        response = unsuitable(api, run, gid, revision=stale)
        assert response.status_code == 409 and code_of(response) == "STALE_REVISION"
        assert response.json()["current_version"] == current
    assert snapshot(run.run_id) == before


def test_a_generation_that_is_not_the_current_one_is_stale(api: VideoApi) -> None:
    run, gid = video_ready(api)
    before = snapshot(run.run_id)
    current = int(run_row(run.run_id)["revision"])
    for wrong in (str(uuid4()), run.run_id):
        response = unsuitable(api, run, wrong)
        assert response.status_code == 409 and code_of(response) == "STALE_REVISION", wrong
        assert response.json()["current_version"] == current
    assert snapshot(run.run_id) == before
    assert gid not in {str(uuid4()), run.run_id}


def test_the_generation_of_another_run_is_stale_and_never_touched(api: VideoApi) -> None:
    first, first_gid = video_ready(api)
    second, second_gid = video_ready(api, new_script_run(api, owner=api.other_parent))
    response = unsuitable(api, first, second_gid)
    assert response.status_code == 409 and code_of(response) == "STALE_REVISION"
    assert {g["state"] for g in generations(second.run_id)} == {"READY"}
    assert {g["state"] for g in generations(first.run_id)} == {"READY"}
    assert first_gid != second_gid


@pytest.mark.parametrize(
    "state",
    [
        "INPUT_PROCESSING",
        "INPUT_REVIEW",
        "SUBJECT_REVIEW",
        "PREPARATION_REVIEW",
        "SCRIPT_GENERATING",
        "SCRIPT_REVIEW",
        "VIDEO_ADMISSION_PENDING",
        "VIDEO_QUEUED",
        "VIDEO_GENERATING",
        "VIDEO_SAFETY_VALIDATING",
        "SAFETY_BLOCKED",
        "COMPLETED",
        "FAILED",
        "ABANDONED",
    ],
)
def test_every_run_state_but_video_ready_refuses_both_commands(api: VideoApi, state: str) -> None:
    run = new_script_run(api, run_state=state, hold_slot=False)
    before = snapshot(run.run_id)
    gid = str(uuid4())
    for response in (unsuitable(api, run, gid), complete(api, run)):
        assert response.status_code == 409 and code_of(response) == "INVALID_STATE_TRANSITION"
    assert snapshot(run.run_id) == before
    assert receipts(run.run_id, UNSUITABLE) == [] and receipts(run.run_id, COMPLETE) == []


def test_a_run_in_a_purge_state_refuses_both_commands_without_a_receipt(api: VideoApi) -> None:
    run, gid = video_ready(api)
    assert cancel(api, run).status_code == 202
    for response in (unsuitable(api, run, gid), complete(api, run)):
        assert response.status_code == 409 and code_of(response) == "INVALID_STATE_TRANSITION"
    assert receipts(run.run_id, UNSUITABLE) == [] and receipts(run.run_id, COMPLETE) == []


def test_the_state_is_checked_before_the_revision_and_the_generation(api: VideoApi) -> None:
    run = new_script_run(api)  # SCRIPT_REVIEW: wrong state, wrong revision and wrong generation
    response = unsuitable(api, run, str(uuid4()), revision=1)
    assert response.status_code == 409 and code_of(response) == "INVALID_STATE_TRANSITION"


# ------------------------------------------------------------------------- the regeneration cap
def test_the_cap_refuses_the_third_rejection_and_changes_nothing(api: VideoApi) -> None:
    run = new_script_run(api, prior=2)  # generations 1 and 2 were accepted and failed
    run, gid = video_ready(api, run, reason="QUALITY_LOW")
    assert [g["generation_no"] for g in generations(run.run_id)] == [1, 2, 3]
    before = snapshot(run.run_id)
    response = unsuitable(api, run, gid)
    assert response.status_code == 409 and code_of(response) == "VIDEO_REGENERATION_LIMIT_REACHED"
    assert response.json()["retryable"] is False
    assert snapshot(run.run_id) == before
    assert generations(run.run_id)[-1]["state"] == "READY"  # the video stays visible
    assert receipts(run.run_id, UNSUITABLE) == []
    assert complete(api, run).status_code == 200  # the adult can still finish the run


def test_the_second_video_can_still_be_rejected_with_one_regeneration_left(api: VideoApi) -> None:
    run = new_script_run(api, prior=1)
    run, gid = video_ready(api, run, reason="QUALITY_LOW")
    assert [g["generation_no"] for g in generations(run.run_id)] == [1, 2]
    assert unsuitable(api, run, gid).status_code == 200
    assert generations(run.run_id)[-1]["state"] == "REJECTED_BY_ADULT"


def test_a_rejected_video_counts_toward_the_cap_and_the_next_request_is_a_regeneration(
    api: VideoApi,
) -> None:
    run, first_gid = video_ready(api)
    assert unsuitable(api, run, first_gid).status_code == 200
    add_confirmed_revision(api, run)  # a confirmed revision, inserted as a shortcut
    second = video_request(api, run, reason="NOT_MATCHING_STORY")
    assert second.status_code == 202, second.text
    generation = second.json()["video_generation"]
    assert generation["kind"] == "QUALITY_REGEN" and generation["generation_no"] == 2
    states = [(g["generation_no"], g["state"]) for g in generations(run.run_id)]
    assert states == [(1, "REJECTED_BY_ADULT"), (2, "ACCEPTED")]
    assert run_row(run.run_id)["current_video_generation_id"] == generation["generation_id"]
    ready = runner(api).run_to_end(generation["generation_id"])
    assert ready.record is not None and ready.record.state == "READY"
    assert run_row(run.run_id)["run_state"] == "VIDEO_READY"
    # the old video is not playable again even though the new one is ready (l.395)
    assert generations(run.run_id)[0]["state"] == "REJECTED_BY_ADULT"
    # a stale id of the rejected generation cannot reject the new video
    stale = unsuitable(api, run, first_gid)
    assert stale.status_code == 409 and code_of(stale) == "STALE_REVISION"


# ------------------------------------------------- Q4: the way back after a rejected video (B2)
def test_after_unsuitable_a_rewrite_a_confirmation_and_the_next_video_work(api: VideoApi) -> None:
    """SRS l.416, BR-16 l.260: an AI rewrite after a video is marked unsuitable makes a new
    revision that needs confirmation again; the next video is then ``QUALITY_REGEN`` number 2."""

    run, gid = video_ready(api)
    generator = make_rewritable(api, run)
    assert unsuitable(api, run, gid).status_code == 200
    # before the rewrite nothing else leads out: the consumed review blocks a new request
    blocked = video_request(api, run, reason="QUALITY_LOW")
    assert blocked.status_code == 409 and code_of(blocked) == "INVALID_STATE_TRANSITION"
    rewritten = rewrite_route(api, run)
    assert rewritten.status_code == 202, rewritten.text
    assert generator.calls == 1 and rewritten.json()["story_revision_no"] == 2
    assert [row["status"] for row in story_rows(run.run_id)] == ["SUPERSEDED", "DRAFT"]
    assert run_row(run.run_id)["run_state"] == "SCRIPT_REVIEW"
    # a new revision must be confirmed before the next request (BR-14, BR-16)
    unconfirmed = video_request(api, run, reason="QUALITY_LOW")
    assert unconfirmed.status_code == 409, unconfirmed.text
    assert len(generations(run.run_id)) == 1
    confirmed = confirm_route(api, run)
    assert confirmed.status_code == 200, confirmed.text
    assert [row["status"] for row in story_rows(run.run_id)] == ["SUPERSEDED", "CONFIRMED"]
    second = video_request(api, run, reason="NOT_MATCHING_STORY")
    assert second.status_code == 202, second.text
    generation = second.json()["video_generation"]
    assert generation["kind"] == "QUALITY_REGEN" and generation["generation_no"] == 2
    assert [(g["generation_no"], g["state"]) for g in generations(run.run_id)] == [
        (1, "REJECTED_BY_ADULT"),
        (2, "ACCEPTED"),
    ]
    ready = runner(api).run_to_end(generation["generation_id"])
    assert ready.record is not None and ready.record.state == "READY"
    assert run_row(run.run_id)["run_state"] == "VIDEO_READY"
    # the adult can finish the run after the regeneration
    assert complete(api, run).status_code == 200
    assert run_row(run.run_id)["run_state"] == "COMPLETED"


def test_two_regenerations_work_and_the_third_is_the_limit(api: VideoApi) -> None:
    """AC-06: one video and two regenerations; each one passes a rewrite and a confirmation."""

    run, first = video_ready(api)
    make_rewritable(api, run)
    assert unsuitable(api, run, first).status_code == 200
    second = regenerate(api, run)
    assert unsuitable(api, run, second).status_code == 200
    third = regenerate(api, run, reason="CONTENT_CONCERN")
    numbers = [(g["generation_no"], g["state"]) for g in generations(run.run_id)]
    assert numbers == [(1, "REJECTED_BY_ADULT"), (2, "REJECTED_BY_ADULT"), (3, "READY")]
    assert [row["status"] for row in story_rows(run.run_id)] == [
        "SUPERSEDED",
        "SUPERSEDED",
        "CONFIRMED",
    ]
    before = snapshot(run.run_id)
    # a third regeneration would need the mark of the third video: the cap refuses it
    refused = unsuitable(api, run, third)
    assert refused.status_code == 409 and code_of(refused) == "VIDEO_REGENERATION_LIMIT_REACHED"
    assert snapshot(run.run_id) == before
    assert complete(api, run).status_code == 200


def test_a_confirmed_script_without_a_rejected_video_is_still_refused_by_rewrites(
    api: VideoApi,
) -> None:
    # confirmed, no video at all
    plain = new_script_run(api)
    make_rewritable(api, plain)
    refused = rewrite_route(api, plain)
    assert refused.status_code == 409 and code_of(refused) == "INVALID_STATE_TRANSITION"
    assert [row["status"] for row in story_rows(plain.run_id)] == ["CONFIRMED"]
    # confirmed, only an older revision has a (failed) generation: same refusal
    older = new_script_run(api, owner=api.other_parent, prior=1)
    make_rewritable(api, older)
    refused_again = rewrite_route(api, older)
    assert refused_again.status_code == 409
    assert code_of(refused_again) == "INVALID_STATE_TRANSITION"
    assert [row["status"] for row in story_rows(older.run_id)] == ["SUPERSEDED", "CONFIRMED"]
    # a video that is ready is not rewritable either (the run is not in script review)
    ready, _gid = video_ready(api, new_script_run(api, owner=api.other_parent))
    make_rewritable(api, ready)
    assert code_of(rewrite_route(api, ready)) == "INVALID_STATE_TRANSITION"


def test_the_revision_four_corner_has_a_way_back_through_the_confirmation(api: VideoApi) -> None:
    """V4-A T-1b-fix (SRS l.406, l.1728): an adult who used all three rewrites before the second
    video and then marks that video unsuitable cannot rewrite (409 ``STORY_REWRITE_LIMIT_REACHED``),
    but keeps the current story and confirms it again (a new review epoch), then asks for the
    third video."""

    run, first = video_ready(api)
    make_rewritable(api, run)
    assert unsuitable(api, run, first).status_code == 200
    for _ in range(3):  # three rewrites in a row: revisions 2, 3 and 4
        assert rewrite_route(api, run).status_code == 202
    assert [row["revision_no"] for row in story_rows(run.run_id)] == [1, 2, 3, 4]
    assert confirm_route(api, run).status_code == 200
    response = video_request(api, run, reason="QUALITY_LOW")
    assert response.status_code == 202, response.text
    second = str(response.json()["video_generation"]["generation_id"])
    ready = runner(api).run_to_end(second)
    assert ready.record is not None and ready.record.state == "READY"
    assert unsuitable(api, run, second).status_code == 200
    before = snapshot(run.run_id)
    refused = rewrite_route(api, run)
    assert refused.status_code == 409 and code_of(refused) == "STORY_REWRITE_LIMIT_REACHED"
    assert snapshot(run.run_id) == before and len(story_rows(run.run_id)) == 4
    assert story_rows(run.run_id)[-1]["status"] == "CONFIRMED"
    # the way back: the same story, confirmed again (a fresh key), then the third request
    again = confirm_route(api, run)
    assert again.status_code == 200, again.text
    assert again.json()["story_run"]["story_confirmation_required"] is False
    assert story_rows(run.run_id)[-1]["status"] == "CONFIRMED" and len(story_rows(run.run_id)) == 4
    third = video_request(api, run, reason="QUALITY_LOW")
    assert third.status_code == 202, third.text
    assert third.json()["video_generation"]["generation_no"] == 3
    assert cancel(api, run).status_code == 202


def test_cancel_after_unsuitable_purges_the_rejected_generation_and_its_asset(
    api: VideoApi,
) -> None:
    run, gid = video_ready(api)
    key = generations(run.run_id)[0]["output_asset_ref"]
    assert unsuitable(api, run, gid).status_code == 200
    assert key in api.storage.objects  # kept internally until the run is deleted
    assert cancel(api, run).status_code == 202
    purge_everything(api, run)
    assert generations(run.run_id) == [] and api.storage.list_keys(f"parent/{run.run_id}/") == ()


def test_a_replay_after_the_run_was_deleted_is_the_content_free_projection(api: VideoApi) -> None:
    run, gid = video_ready(api)
    key = uuid4().hex
    revision = int(run_row(run.run_id)["revision"])
    assert unsuitable(api, run, gid, key=key, revision=revision).status_code == 200
    assert cancel(api, run).status_code == 202
    replay = unsuitable(api, run, gid, key=key, revision=revision)
    assert replay.status_code == 200 and set(replay.json()) == {"request_id", "lifecycle"}
    assert replay.json()["lifecycle"]["run_state"] == "DELETE_PENDING"
    assert "story_run" not in replay.text
    other_key = unsuitable(api, run, gid)
    assert other_key.status_code == 409 and code_of(other_key) == "INVALID_STATE_TRANSITION"


# ============================================================================== complete
def test_complete_ends_the_run_and_releases_the_active_lock(api: VideoApi) -> None:
    run, gid = video_ready(api)
    before = run_row(run.run_id)
    assert before["active_owner_parent_account_id"] is not None
    # while the lock is held the same parent cannot own a second active run
    with pytest.raises(IntegrityError):
        new_script_run(api, hold_slot=True)
    reservation_calls = list(api.reservation.calls)
    response = complete(api, run)
    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body) == {"request_id", "story_run"}
    assert body["story_run"]["run_state"] == "COMPLETED"
    assert body["story_run"]["run_revision"] == before["revision"] + 1
    assert response.headers["Content-Location"] == f"/v1/story-runs/{run.run_id}"
    after = run_row(run.run_id)
    assert after["run_state"] == "COMPLETED" and after["active_owner_parent_account_id"] is None
    assert after["finished_at"] is not None and after["adult_wait_started_at"] is None
    assert after["last_meaningful_activity_at"] > before["last_meaningful_activity_at"]
    assert after["revision"] == before["revision"] + 1 and after["version"] == before["version"] + 1
    # the generation stays READY: completing is not a video approval (l.1672)
    (generation,) = generations(run.run_id)
    assert generation["video_generation_id"] == gid and generation["state"] == "READY"
    assert generation["rejection_reason_code"] is None
    (receipt,) = receipts(run.run_id, COMPLETE)
    assert receipt["state"] == "FINAL" and receipt["response_status"] == 200
    assert api.reservation.calls == reservation_calls
    # the lock is free: the same parent can now own a new active run
    successor = new_script_run(api, hold_slot=True)
    assert run_row(successor.run_id)["active_owner_parent_account_id"] is not None


def test_complete_replays_with_the_same_key_and_refuses_another_payload(api: VideoApi) -> None:
    run, _gid = video_ready(api)
    key = uuid4().hex
    revision = int(run_row(run.run_id)["revision"])
    first = complete(api, run, key=key, revision=revision)
    second = complete(api, run, key=key, revision=revision)
    assert first.status_code == 200 and second.status_code == 200
    assert second.json()["story_run"]["run_state"] == "COMPLETED"
    assert len(receipts(run.run_id, COMPLETE)) == 1
    assert run_row(run.run_id)["revision"] == revision + 1
    changed = complete(api, run, key=key, revision=revision + 3)
    assert changed.status_code == 400 and code_of(changed) == "INVALID_IDEMPOTENCY_KEY"


def test_complete_with_a_stale_revision_is_409_and_changes_nothing(api: VideoApi) -> None:
    run, _gid = video_ready(api)
    before = snapshot(run.run_id)
    current = int(run_row(run.run_id)["revision"])
    response = complete(api, run, revision=current - 1)
    assert response.status_code == 409 and code_of(response) == "STALE_REVISION"
    assert response.json()["current_version"] == current
    assert snapshot(run.run_id) == before and receipts(run.run_id, COMPLETE) == []


def test_complete_is_for_the_owner_only(api: VideoApi) -> None:
    run, _gid = video_ready(api)
    before = snapshot(run.run_id)
    for subject in (api.other_parent, api.teacher, api.manager, api.admin):
        response = complete(api, run, owner=subject)
        assert response.status_code == 404 and code_of(response) == "RESOURCE_NOT_FOUND", subject
    assert snapshot(run.run_id) == before


def test_complete_a_missing_or_malformed_key_is_a_plain_400(api: VideoApi) -> None:
    run, _gid = video_ready(api)
    path = f"/v1/story-runs/{run.run_id}/complete"
    body = {"expected_revision": int(run_row(run.run_id)["revision"])}
    for bad in (None, "bad key", "k" * 129):
        response = api.client.post(path, json=body, headers=headers(run.owner, bad))
        assert response.status_code == 400 and code_of(response) == "INVALID_REQUEST"
    assert run_row(run.run_id)["run_state"] == "VIDEO_READY"


def test_after_complete_the_run_cannot_be_rejected_cancelled_or_completed_again(
    api: VideoApi,
) -> None:
    run, gid = video_ready(api)
    assert complete(api, run).status_code == 200
    again = complete(api, run)
    assert again.status_code == 409 and code_of(again) == "INVALID_STATE_TRANSITION"
    late = unsuitable(api, run, gid)
    assert late.status_code == 409 and code_of(late) == "INVALID_STATE_TRANSITION"
    cancelled = cancel(api, run)
    assert cancelled.status_code == 409 and code_of(cancelled) == "INVALID_STATE_TRANSITION"
    assert run_row(run.run_id)["run_state"] == "COMPLETED"


def test_a_completed_run_can_be_deleted_and_the_video_row_and_asset_are_purged(
    api: VideoApi,
) -> None:
    run, _gid = video_ready(api)
    key = generations(run.run_id)[0]["output_asset_ref"]
    assert complete(api, run).status_code == 200
    assert key in api.storage.objects  # the content stays until the user deletes the run
    deleted = api.client.delete(
        f"/v1/story-runs/{run.run_id}", headers=headers(run.owner, uuid4().hex)
    )
    assert deleted.status_code == 202, deleted.text
    assert run_row(run.run_id)["run_state"] == "DELETE_PENDING"
    purge_everything(api, run)
    assert generations(run.run_id) == [] and api.storage.list_keys(f"parent/{run.run_id}/") == ()


def test_a_replay_of_complete_after_the_run_was_deleted_is_the_projection(api: VideoApi) -> None:
    run, _gid = video_ready(api)
    key = uuid4().hex
    revision = int(run_row(run.run_id)["revision"])
    assert complete(api, run, key=key, revision=revision).status_code == 200
    deleted = api.client.delete(
        f"/v1/story-runs/{run.run_id}", headers=headers(run.owner, uuid4().hex)
    )
    assert deleted.status_code == 202
    replay = complete(api, run, key=key, revision=revision)
    assert replay.status_code == 200 and set(replay.json()) == {"request_id", "lifecycle"}
    assert replay.json()["lifecycle"]["run_state"] == "DELETE_PENDING"


def test_a_blocked_video_can_be_neither_completed_nor_rejected(api: VideoApi) -> None:
    run = new_script_run(api)
    response = video_request(api, run)
    gid = str(response.json()["video_generation"]["generation_id"])
    renderer = FixtureVideoRenderer()
    renderer.results[gid] = VideoRenderResult(
        content=b"x", media_type="video/mp4", safety_passed=False, safety_finding_codes=("F-1",)
    )
    runner(api, renderer).run_to_end(gid)
    assert run_row(run.run_id)["run_state"] == "SCRIPT_REVIEW"  # V4-A: back at the script review
    for response in (complete(api, run), unsuitable(api, run, gid)):
        assert response.status_code == 409 and code_of(response) == "INVALID_STATE_TRANSITION"


# ============================================================================== concurrency
def test_complete_and_cancel_in_parallel_leave_one_winner_and_a_consistent_run(
    api: VideoApi,
) -> None:
    for _ in range(6):
        run, _gid = video_ready(api, new_script_run(api, hold_slot=False))
        revision = int(run_row(run.run_id)["revision"])

        def work(index: int, run: ScriptRun = run, revision: int = revision) -> Any:
            if index == 0:
                return complete(api, run, revision=revision)
            return api.client.post(
                f"/v1/story-runs/{run.run_id}/cancel",
                json={"expected_revision": revision},
                headers=headers(run.owner, uuid4().hex),
            )

        completed, cancelled = _parallel(2, work)
        statuses = (completed.status_code, cancelled.status_code)
        assert statuses in {(200, 409), (409, 202)}, statuses
        final = run_row(run.run_id)
        if statuses == (200, 409):
            assert final["run_state"] == "COMPLETED" and len(receipts(run.run_id, COMPLETE)) == 1
            assert code_of(cancelled) in {"STALE_REVISION", "INVALID_STATE_TRANSITION"}
        else:
            assert final["run_state"] == "DELETE_PENDING" and receipts(run.run_id, COMPLETE) == []
            assert code_of(completed) in {"STALE_REVISION", "INVALID_STATE_TRANSITION"}
        assert final["revision"] == revision + 1  # exactly one command won


def test_unsuitable_twice_with_one_key_changes_the_run_once(api: VideoApi) -> None:
    run, gid = video_ready(api)
    key = uuid4().hex
    revision = int(run_row(run.run_id)["revision"])
    responses = _parallel(2, lambda _i: unsuitable(api, run, gid, key=key, revision=revision))
    assert [response.status_code for response in responses] == [200, 200]
    assert len(receipts(run.run_id, UNSUITABLE)) == 1
    assert run_row(run.run_id)["revision"] == revision + 1
    assert [g["state"] for g in generations(run.run_id)] == ["REJECTED_BY_ADULT"]


def test_unsuitable_twice_with_two_keys_gives_one_200_and_one_409(api: VideoApi) -> None:
    run, gid = video_ready(api)
    revision = int(run_row(run.run_id)["revision"])
    responses = _parallel(2, lambda _i: unsuitable(api, run, gid, revision=revision))
    assert sorted(response.status_code for response in responses) == [200, 409]
    loser = next(response for response in responses if response.status_code == 409)
    assert code_of(loser) == "INVALID_STATE_TRANSITION"
    assert len(receipts(run.run_id, UNSUITABLE)) == 1
    assert run_row(run.run_id)["revision"] == revision + 1


def test_complete_twice_with_one_key_changes_the_run_once(api: VideoApi) -> None:
    run, _gid = video_ready(api)
    key = uuid4().hex
    revision = int(run_row(run.run_id)["revision"])
    responses = _parallel(2, lambda _i: complete(api, run, key=key, revision=revision))
    assert [response.status_code for response in responses] == [200, 200]
    assert len(receipts(run.run_id, COMPLETE)) == 1
    assert run_row(run.run_id)["revision"] == revision + 1
    assert run_row(run.run_id)["run_state"] == "COMPLETED"


def test_complete_and_unsuitable_in_parallel_leave_one_winner(api: VideoApi) -> None:
    run, gid = video_ready(api)
    revision = int(run_row(run.run_id)["revision"])

    def work(index: int) -> Any:
        if index == 0:
            return complete(api, run, revision=revision)
        return unsuitable(api, run, gid, revision=revision)

    completed, rejected = _parallel(2, work)
    statuses = (completed.status_code, rejected.status_code)
    assert statuses in {(200, 409), (409, 200)}, statuses
    final = run_row(run.run_id)
    assert final["revision"] == revision + 1
    if completed.status_code == 200:
        assert final["run_state"] == "COMPLETED" and generations(run.run_id)[0]["state"] == "READY"
    else:
        assert final["run_state"] == "SCRIPT_REVIEW"
        assert generations(run.run_id)[0]["state"] == "REJECTED_BY_ADULT"


def test_unsuitable_and_cancel_in_parallel_leave_one_winner(api: VideoApi) -> None:
    for _ in range(4):
        run, gid = video_ready(api, new_script_run(api, hold_slot=False))
        revision = int(run_row(run.run_id)["revision"])

        def work(index: int, run: ScriptRun = run, gid: str = gid, revision: int = revision) -> Any:
            if index == 0:
                return unsuitable(api, run, gid, revision=revision)
            return api.client.post(
                f"/v1/story-runs/{run.run_id}/cancel",
                json={"expected_revision": revision},
                headers=headers(run.owner, uuid4().hex),
            )

        rejected, cancelled = _parallel(2, work)
        statuses = (rejected.status_code, cancelled.status_code)
        assert statuses in {(200, 409), (409, 202)}, statuses
        final = run_row(run.run_id)
        assert final["revision"] == revision + 1  # exactly one command won
        if statuses == (200, 409):
            assert final["run_state"] == "SCRIPT_REVIEW"
            assert generations(run.run_id)[0]["state"] == "REJECTED_BY_ADULT"
        else:
            assert final["run_state"] == "DELETE_PENDING" and receipts(run.run_id, UNSUITABLE) == []


def test_a_stale_revision_never_overwrites_a_newer_head(api: VideoApi) -> None:
    run, gid = video_ready(api)
    revision = int(run_row(run.run_id)["revision"])
    version = int(run_row(run.run_id)["version"])
    with api.sessions().begin() as db:
        db.execute(
            update(RUNS)
            .where(RUNS.c.run_id == run.run_id)
            .values(revision=revision + 1, version=version + 1)
        )
    for response in (
        unsuitable(api, run, gid, revision=revision),
        complete(api, run, revision=revision),
    ):
        assert response.status_code == 409 and code_of(response) == "STALE_REVISION"
        assert response.json()["current_version"] == revision + 1
    assert run_row(run.run_id)["run_state"] == "VIDEO_READY"
