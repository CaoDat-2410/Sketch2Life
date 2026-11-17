"""Offline BE2-07 → BE2-01 → BE2-08 flow on a test-owned PostgreSQL 17 database."""

from __future__ import annotations

import hashlib
import ipaddress
import os
import runpy
import socket
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterator

import psycopg
from psycopg import sql as psycopg_sql
import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.engine import Engine, URL
from sqlalchemy.pool import NullPool

from sketch2life.application.knowledge_video_media import (
    CheckedMediaValidator,
    PreparedVideoMedia,
    VideoMediaPipeline,
)
from sketch2life.application.knowledge_video_worker import VideoCompletionService, staging_key
from sketch2life.application.ports.ai_jobs import (
    OWNER_FENCE_CONTRACT,
    AuthorizationAction,
    FenceResult,
    OwnerFence,
    Principal,
    PrincipalRole,
    WorkerDispatchEnvelope,
)
from sketch2life.application.ports.knowledge_video import VideoRequestContext
from sketch2life.application.ports.knowledge_video_media import (
    MediaProfileResolver,
    RenderAttempt,
    RenderAuthority,
    VideoGenerator,
    VideoSourceMaterial,
    VideoSourceResolver,
)
from sketch2life.application.ports.knowledge_video_worker import (
    StagedVideo,
    VideoWorkerAdmission,
)
from sketch2life.application.services.ai_jobs import AiJobDependencies, AiJobService
from sketch2life.application.knowledge_video_create import VideoCreateService
from sketch2life.application.services.knowledge_bundle import CreateKnowledgeCommand
from sketch2life.domain.ai_jobs.model import JobState
from sketch2life.domain.knowledge_video.media import DecodedMedia, MediaBlob, MediaProfile
from sketch2life.domain.knowledge_video.model import ExactRef, Strategy, VideoError, VideoPin
from sketch2life.infrastructure.ai_jobs.fakes import (
    FakeArtifacts,
    FakeAudit,
    FakeAuthorization,
    FakeClock,
    FakeEligibility,
    FakeOwnerFences,
    FakeQueue,
    FakeWorkerCapability,
    SequentialIds,
)
from sketch2life.infrastructure.ai_jobs.sql import tables as ai_tables
from sketch2life.infrastructure.ai_jobs.sql.repository import SqlAiJobRepository
from sketch2life.infrastructure.ai_jobs.worker import DispatchWorker
from sketch2life.infrastructure.knowledge_bundle.harness import (
    TEACHER_A,
    build_knowledge_harness,
)
from sketch2life.infrastructure.knowledge_video.foundation_lifecycle import (
    FoundationVideoFinalizer,
    FoundationVideoSubmission,
    FoundationVideoWorkerAdmission,
    SqlVideoLifecycleFactory,
    SqlVideoLifecycleTransaction,
)
from sketch2life.infrastructure.knowledge_video.sql import VideoRunRows
from sketch2life.infrastructure.knowledge_video.tables import RECEIPT, RUN
from sketch2life.application.knowledge_video_worker import VideoWorker
from sketch2life.contracts.schemas.knowledge_video import CreateKnowledgeVideo
from sketch2life.domain.ai_jobs.model import RequestRef

BACKEND = Path(__file__).resolve().parents[3]
NOW = datetime(2026, 10, 22, 12, 0, tzinfo=UTC)
VIDEO_JOB_TYPE = "knowledge_video"
VIDEO_BYTES = b"synthetic offline video fixture"
VIDEO_HASH = hashlib.sha256(VIDEO_BYTES).hexdigest()


def _loopback_only(host: str) -> bool:
    try:
        values = {ipaddress.ip_address(host)}
    except ValueError:
        try:
            values = {
                ipaddress.ip_address(item[4][0])
                for item in socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
            }
        except OSError:
            return False
    return bool(values) and all(value.is_loopback for value in values)


def _test_database_url(database: str) -> URL:
    host = os.environ["BE2_TEST_PG_HOST"]
    password_file = Path(os.environ["BE2_TEST_PG_PASSWORD_FILE"]).resolve()
    if password_file.is_relative_to(BACKEND):
        raise RuntimeError("test database credentials must be outside the repository")
    password = password_file.read_text(encoding="utf-8").strip()
    return URL.create(
        "postgresql+psycopg",
        username=os.environ.get("BE2_TEST_PG_USER", "be2_test"),
        password=password,
        host=host,
        port=int(os.environ.get("BE2_TEST_PG_PORT", "5432")),
        database=database,
    )


def _apply_existing_migration(engine: Engine, path: Path) -> None:
    module = runpy.run_path(str(path), run_name=f"offline_migration_{uuid.uuid4().hex}")
    with engine.connect() as connection:
        with connection.begin():
            with Operations.context(MigrationContext.configure(connection)):
                module["upgrade"]()


@pytest.fixture
def isolated_postgres17() -> Iterator[Engine]:
    host = os.environ.get("BE2_TEST_PG_HOST")
    password_file = os.environ.get("BE2_TEST_PG_PASSWORD_FILE")
    if not host or not password_file:
        pytest.skip("test-owned PostgreSQL 17 needs BE2_TEST_PG_HOST and a test-only password file")
    if not _loopback_only(host):
        pytest.fail("BE2_TEST_PG_HOST must resolve only to loopback addresses")

    maintenance_db = os.environ.get("BE2_TEST_PG_MAINTENANCE_DB", "postgres")
    maintenance_url = _test_database_url(maintenance_db)
    database_name = f"be2_xlane_{uuid.uuid4().hex[:16]}"
    if not database_name.startswith("be2_xlane_"):
        raise RuntimeError("unsafe test database name")

    created = False
    engine: Engine | None = None

    def admin() -> psycopg.Connection[tuple[object, ...]]:
        return psycopg.connect(
            host=maintenance_url.host,
            port=maintenance_url.port,
            user=maintenance_url.username,
            password=maintenance_url.password,
            dbname=maintenance_db,
            connect_timeout=5,
            autocommit=True,
        )

    try:
        with admin() as connection:
            version = str(connection.execute("SHOW server_version").fetchone()[0])
            if not version.startswith("17."):
                pytest.fail("the isolated flow requires PostgreSQL 17")
            exists = connection.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s", (database_name,)
            ).fetchone()
            if exists is not None:
                pytest.fail("random test database already exists; refusing to reuse it")
            connection.execute(
                "CREATE DATABASE " + psycopg_sql.Identifier(database_name).as_string(connection)
            )
            created = True

        target_url = maintenance_url.set(database=database_name)
        engine = create_engine(target_url, poolclass=NullPool, hide_parameters=True)
        with engine.connect() as connection:
            schemas = set(connection.execute(text(
                "SELECT schema_name FROM information_schema.schemata "
                "WHERE schema_name IN ('ai_jobs', 'knowledge_video')"
            )).scalars())
            if schemas:
                pytest.fail("fresh test database contains an existing feature schema")

        _apply_existing_migration(
            engine, BACKEND / "alembic/versions/20261015_ai_0001_ai_jobs_schema.py"
        )
        _apply_existing_migration(
            engine, BACKEND / "alembic/versions/20261018_kv_0001_knowledge_video.py"
        )
        yield engine
    finally:
        if engine is not None:
            engine.dispose()
        if created:
            with admin() as connection:
                connection.execute(
                    "DROP DATABASE "
                    + psycopg_sql.Identifier(database_name).as_string(connection)
                    + " WITH (FORCE)"
                )


class _FenceHold:
    contract_version = OWNER_FENCE_CONTRACT

    def __init__(self, fences: FakeOwnerFences) -> None:
        self._fences = fences

    def hold(self, requested: tuple[OwnerFence, ...]) -> FenceResult:
        return self._fences.hold(requested)


class _VideoResolver:
    def __init__(self, pin: VideoPin) -> None:
        self._pin = pin

    @contextmanager
    def hold(self, context: VideoRequestContext, command: CreateKnowledgeVideo):
        if (context.organization_id != self._pin.organization_id
                or context.session_id != self._pin.session_id
                or command.bundle_id != self._pin.bundle.ref
                or command.bundle_version != self._pin.bundle.version
                or command.bundle_hash != self._pin.bundle.hash):
            raise VideoError("VIDEO_RESOLUTION_MISMATCH")
        yield _VideoLease(context, self._pin)


@dataclass(frozen=True)
class _VideoLease:
    context: VideoRequestContext
    pin: VideoPin

    def assert_current(self) -> None:
        return None


class _OfflineAuthority(RenderAuthority):
    def check(self, attempt: RenderAttempt, phase: str) -> None:
        del attempt, phase


class _OfflineProfiles(MediaProfileResolver):
    def __init__(self, profile: MediaProfile) -> None:
        self.profile = profile

    def resolve(self, attempt: RenderAttempt) -> MediaProfile:
        if attempt.run.pin.content_profile != self.profile.content_profile:
            raise VideoError("VIDEO_PROFILE_UNAVAILABLE")
        return self.profile


class _BundleSourceResolver(VideoSourceResolver):
    def __init__(self, producer, principal: Principal) -> None:
        self._producer = producer
        self._principal = principal
        self.exports = []
        self.source_pins = []

    def load(self, attempt: RenderAttempt) -> VideoSourceMaterial:
        pin = attempt.run.pin
        resolved = self._producer.resolve_exact(
            self._principal, pin.bundle.ref, pin.bundle.version, pin.bundle.hash
        )
        if not resolved.ready or resolved.export is None:
            raise VideoError("VIDEO_SOURCE_UNAVAILABLE")
        export = resolved.export
        source_pins = tuple(sorted(
            (item.ref.source_id, item.ref.revision, item.ref.sha256)
            for item in export.source_records
        ))
        expected_pins = tuple(sorted((item.ref, item.version, item.hash) for item in pin.sources))
        if (source_pins != expected_pins
                or export.bundle_hash != pin.bundle.hash
                or export.bundle_id != pin.bundle.ref
                or export.bundle_version != pin.bundle.version):
            raise VideoError("VIDEO_SOURCE_MISMATCH")
        self.exports.append(export)
        self.source_pins.append(source_pins)
        return VideoSourceMaterial(pin.bundle, pin.digest(), export.script_text)


class _OfflineGenerator(VideoGenerator):
    def __init__(self) -> None:
        self.calls = 0
        self.sources: list[VideoSourceMaterial] = []

    def generate(self, attempt, source, operation_key) -> MediaBlob:
        del operation_key
        if source.bundle != attempt.run.pin.bundle:
            raise VideoError("VIDEO_SOURCE_MISMATCH")
        self.calls += 1
        self.sources.append(source)
        return MediaBlob(VIDEO_BYTES, VIDEO_HASH)


class _OfflineDecoder:
    def decode(self, blob: MediaBlob, encoding: ExactRef) -> DecodedMedia:
        del encoding
        return DecodedMedia(
            blob.sha256, "fixture", "fixture", 16, 16, 500, 12, (), True
        )


class _PrivateStaging:
    def __init__(self, artifacts: FakeArtifacts, *, tamper: str | None = None) -> None:
        self._artifacts = artifacts
        self._tamper = tamper
        self.calls = 0
        self.values: dict[tuple[str, str], StagedVideo] = {}
        self.quarantine_requests: list[str] = []

    def stage(
        self, attempt: RenderAttempt, media: PreparedVideoMedia, key: str
    ) -> StagedVideo:
        self.calls += 1
        output = self._artifacts.put(
            attempt.run.pin.organization_id,
            media.blob.payload,
            job_id=attempt.run.job_id,
            attempt_id=attempt.run.attempt_id,
        )
        artifact_hash = "b" * 64 if self._tamper == "hash" else output.sha256
        stage_pin = "b" * 64 if self._tamper == "pin" else attempt.run.pin.digest()
        staged = StagedVideo(
            ExactRef(output.artifact_ref, 1, artifact_hash),
            attempt.run.job_id,
            attempt.run.attempt_id or "",
            stage_pin,
            key,
        )
        self.values[(attempt.run.job_id, key)] = staged
        return staged

    def lookup(self, attempt: RenderAttempt, key: str) -> StagedVideo | None:
        return self.values.get((attempt.run.job_id, key))

    def request_quarantine(self, attempt, staged, completion_key: str) -> None:
        del attempt, staged
        self.quarantine_requests.append(completion_key)


class _RecordingAdmission(VideoWorkerAdmission):
    def __init__(self, inner: FoundationVideoWorkerAdmission) -> None:
        self._inner = inner
        self.envelopes: list[WorkerDispatchEnvelope] = []
        self.attempts: list[RenderAttempt] = []

    def begin(self, envelope: WorkerDispatchEnvelope) -> RenderAttempt | None:
        self.envelopes.append(envelope)
        attempt = self._inner.begin(envelope)
        if attempt is not None:
            self.attempts.append(attempt)
        return attempt


class _FailingLifecycle:
    def __init__(self, inner: SqlVideoLifecycleTransaction, fail_at: str) -> None:
        self._inner = inner
        self._fail_at = fail_at
        self.contract_version = inner.contract_version

    def __getattr__(self, name: str):
        return getattr(self._inner, name)

    def submit(self, *args, **kwargs):
        result = self._inner.submit(*args, **kwargs)
        if self._fail_at == "submit":
            raise VideoError("INJECTED_VIDEO_SUBMIT_FAILURE")
        return result

    def start(self, *args, **kwargs):
        result = self._inner.start(*args, **kwargs)
        if self._fail_at == "start":
            raise VideoError("INJECTED_VIDEO_START_FAILURE")
        return result

    def accept(self, *args, **kwargs):
        result = self._inner.accept(*args, **kwargs)
        if self._fail_at == "accept":
            raise VideoError("INJECTED_VIDEO_ACCEPT_FAILURE")
        return result


class _LifecycleFactory:
    def __init__(self, fail_at: str | None = None) -> None:
        self._fail_at = fail_at

    def __call__(self, connection, organization_id):
        participant = SqlVideoLifecycleTransaction(VideoRunRows(connection, organization_id))
        if self._fail_at is None:
            return participant
        return _FailingLifecycle(participant, self._fail_at)


@dataclass
class _Scenario:
    service: AiJobService
    repository: SqlAiJobRepository
    queue: FakeQueue
    artifacts: FakeArtifacts
    producer: object
    export: object
    pin: VideoPin
    context: VideoRequestContext
    create_body: CreateKnowledgeVideo
    create_service: VideoCreateService
    dispatcher: DispatchWorker
    worker: VideoWorker
    admission: _RecordingAdmission
    generator: _OfflineGenerator
    staging: _PrivateStaging
    finalizer: FoundationVideoFinalizer

    def create(self):
        return self.create_service.create(self.context, self.create_body)

    def submit_and_dispatch(self):
        submission = self.create()
        assert self.service.dispatch_outbox() == 1
        envelope = self.queue.receive()
        assert envelope is not None
        return submission, envelope

    def read_pair(self, job_id: str):
        with self.repository.transaction() as tx:
            job = tx.get_job(job_id)
            assert job is not None
            run = tx.video_lifecycle(job.organization_id).find_job(job_id)
            assert run is not None
            receipt = tx.get_completion_receipt(job_id, job.active_attempt.attempt_id)
        return job, run, receipt


def _pin_from_export(export) -> VideoPin:
    sources = tuple(sorted(
        (
            ExactRef(item.ref.source_id, item.ref.revision, item.ref.sha256)
            for item in export.source_records
        ),
        key=lambda item: (item.ref, item.version, item.hash),
    ))
    return VideoPin(
        export.organization_id,
        export.session_id,
        ExactRef(export.bundle_id, export.bundle_version, export.bundle_hash),
        export.editorial_revision,
        export.context_revision,
        export.audience_revision,
        sources,
        Strategy.GENERATE,
        ExactRef("profile.synthetic", 1, "a" * 64),
        ExactRef("encoding.synthetic", 1, "b" * 64),
        ExactRef("rights.synthetic", 1, "c" * 64),
        ExactRef("retry.synthetic", 1, "d" * 64),
        ExactRef("policy.synthetic", 1, "e" * 64),
        1,
        ExactRef("model.synthetic", 1, "f" * 64),
    )


def _build_scenario(engine: Engine, *, fail_at: str | None = None,
                    stage_tamper: str | None = None) -> _Scenario:
    knowledge = build_knowledge_harness()
    created = knowledge.service.create(
        CreateKnowledgeCommand(TEACHER_A, "synthetic-source", knowledge.create_body())
    )
    resolved = knowledge.service.resolve_exact(
        TEACHER_A, created.record.bundle_id, created.record.bundle_version,
        created.record.bundle_hash,
    )
    assert resolved.ready and resolved.export is not None
    export = resolved.export
    pin = _pin_from_export(export)

    fences = FakeOwnerFences()
    authorization = FakeAuthorization(fences)
    authorization.grant(
        TEACHER_A.principal_id,
        {AuthorizationAction.CREATE_JOB, AuthorizationAction.READ_JOB},
        target_ids={pin.bundle.ref},
        session_ids={pin.session_id},
    )
    eligibility = FakeEligibility(fences)
    artifacts = FakeArtifacts(fences)
    queue = FakeQueue()
    capabilities = FakeWorkerCapability()
    lifecycle_factory = (
        SqlVideoLifecycleFactory() if fail_at is None else _LifecycleFactory(fail_at)
    )
    repository = SqlAiJobRepository(
        engine,
        lambda _connection: _FenceHold(fences),
        video_lifecycle_factory=lifecycle_factory,
    )
    service = AiJobService(AiJobDependencies(
        repository=repository,
        authorization=authorization,
        eligibility=eligibility,
        worker_capability=capabilities,
        clock=FakeClock(NOW),
        ids=SequentialIds(),
        artifacts=artifacts,
        audit=FakeAudit(),
        queue=queue,
        capability_issuer=capabilities,
        video_job_type=VIDEO_JOB_TYPE,
    ))
    context = VideoRequestContext(
        TEACHER_A.principal_id, export.organization_id, export.session_id,
        "video-key", "video-correlation",
    )
    body = CreateKnowledgeVideo(
        bundle_id=export.bundle_id,
        bundle_version=export.bundle_version,
        bundle_hash=export.bundle_hash,
        audience_context_revision=export.audience_revision,
        strategy="generate",
    )
    create_service = VideoCreateService(
        _VideoResolver(pin),
        FoundationVideoSubmission(service, repository, job_type=VIDEO_JOB_TYPE),
    )

    media_profile = MediaProfile(
        pin.content_profile,
        pin.encoding,
        tuple(Strategy),
        ("fixture",),
        ("fixture",),
        ((16, 16),),
        100,
        1000,
        128,
        2,
        (),
        0,
    )
    generator = _OfflineGenerator()
    source_resolver = _BundleSourceResolver(knowledge.service, TEACHER_A)
    authority = _OfflineAuthority()
    profiles = _OfflineProfiles(media_profile)
    pipeline = VideoMediaPipeline(
        authority,
        profiles,
        source_resolver,
        CheckedMediaValidator(_OfflineDecoder()),
        generator=generator,
    )
    staging = _PrivateStaging(artifacts, tamper=stage_tamper)
    finalizer = FoundationVideoFinalizer(service, repository, job_type=VIDEO_JOB_TYPE)
    completion = VideoCompletionService(authority, profiles, staging, finalizer)
    admission = _RecordingAdmission(
        FoundationVideoWorkerAdmission(service, job_type=VIDEO_JOB_TYPE)
    )
    worker = VideoWorker(admission, pipeline, completion, job_type=VIDEO_JOB_TYPE)
    dispatcher = DispatchWorker(
        service,
        provider=object(),
        video_job_type=VIDEO_JOB_TYPE,
        video_worker=worker,
    )
    return _Scenario(
        service, repository, queue, artifacts, knowledge.service, export, pin, context,
        body, create_service, dispatcher, worker, admission, generator, staging, finalizer,
    )


def _counts(engine: Engine) -> tuple[int, int, int, int, int, int, int]:
    with engine.connect() as connection:
        ai_job_count = connection.execute(select(func.count()).select_from(ai_tables.job)).scalar_one()
        dispatch_count = connection.execute(
            select(func.count()).select_from(ai_tables.outbox).where(
                ai_tables.outbox.c.kind == "dispatch"
            )
        ).scalar_one()
        audit_intent_count = connection.execute(
            select(func.count()).select_from(ai_tables.outbox).where(
                ai_tables.outbox.c.kind == "audit"
            )
        ).scalar_one()
        quarantine_intent_count = connection.execute(
            select(func.count()).select_from(ai_tables.outbox).where(
                ai_tables.outbox.c.kind == "quarantine"
            )
        ).scalar_one()
        run_count = connection.execute(select(func.count()).select_from(RUN)).scalar_one()
        video_receipts = connection.execute(select(func.count()).select_from(RECEIPT)).scalar_one()
        completion_receipts = connection.execute(
            select(func.count()).select_from(ai_tables.completion_receipt)
        ).scalar_one()
    return (
        ai_job_count, dispatch_count, audit_intent_count, quarantine_intent_count,
        run_count, video_receipts, completion_receipts,
    )


def test_real_bundle_to_persisted_video_worker_and_authoritative_receipt(isolated_postgres17):
    scenario = _build_scenario(isolated_postgres17)
    submission, envelope = scenario.submit_and_dispatch()
    assert submission.run.generation_state is JobState.QUEUED
    assert submission.run.pin.bundle == ExactRef(
        scenario.export.bundle_id, scenario.export.bundle_version, scenario.export.bundle_hash
    )
    assert tuple(sorted(
        (item.ref, item.version, item.hash) for item in submission.run.pin.sources
    )) == tuple(sorted(
        (item.ref.source_id, item.ref.revision, item.ref.sha256)
        for item in scenario.export.source_records
    ))
    assert envelope.message.job_type == VIDEO_JOB_TYPE
    assert envelope.message.request_ref == RequestRef(
        scenario.export.bundle_id,
        scenario.export.bundle_version,
        scenario.export.bundle_hash,
        scenario.export.audience_revision,
    )

    outcome = scenario.dispatcher.handle(envelope)
    assert outcome.status == "accepted"
    assert scenario.admission.envelopes == [envelope]
    assert scenario.admission.envelopes[0] is envelope
    assert len(scenario.admission.attempts) == 1
    attempt = scenario.admission.attempts[0]
    assert outcome.completion_key is not None
    media = _media_for(attempt)
    staged = scenario.staging.values[(attempt.run.job_id, staging_key(attempt, media))]

    job, run, receipt = scenario.read_pair(submission.run.job_id)
    assert job.state is JobState.SUCCEEDED
    assert job.result_disposition.value == "accepted"
    assert len(job.result_refs) == 1
    assert run.generation_state is JobState.SUCCEEDED
    assert run.artifact is not None
    assert run.artifact.artifact == staged.artifact
    assert run.pin.digest() == submission.run.pin.digest()
    assert receipt is not None and receipt.authoritative
    assert receipt.disposition.value == "accepted"
    assert receipt.job_id == run.job_id and receipt.attempt_id == run.attempt_id
    assert scenario.generator.calls == scenario.staging.calls == 1
    assert len(scenario.generator.sources) == 1

    repeated = scenario.dispatcher.handle(envelope)
    assert repeated.status == "ignored"
    assert scenario.generator.calls == scenario.staging.calls == 1
    recovered = scenario.finalizer.finish(
        attempt,
        staged,
        media,
        outcome.completion_key,
    )
    assert recovered.job_receipt.receipt_id == receipt.receipt_id
    assert recovered.video_run == run
    assert _counts(isolated_postgres17) == (1, 1, 2, 0, 1, 1, 1)


def _media_for(attempt: RenderAttempt) -> PreparedVideoMedia:
    from sketch2life.application.knowledge_video_media import media_operation_key

    profile = MediaProfile(
        attempt.run.pin.content_profile,
        attempt.run.pin.encoding,
        tuple(Strategy), ("fixture",), ("fixture",), ((16, 16),),
        100, 1000, 128, 2, (), 0,
    )
    decoder = _OfflineDecoder()
    blob = MediaBlob(VIDEO_BYTES, VIDEO_HASH)
    return PreparedVideoMedia(
        attempt.run.pin.digest(),
        media_operation_key(attempt),
        blob,
        decoder.decode(blob, profile.encoding),
        attempt.run.pin.strategy,
    )


@pytest.mark.parametrize("fail_at", ["submit", "start", "accept"])
def test_participant_failure_rolls_back_its_whole_a_s_or_b_transaction(
    isolated_postgres17, fail_at
):
    scenario = _build_scenario(isolated_postgres17, fail_at=fail_at)
    if fail_at == "submit":
        with pytest.raises(VideoError, match="INJECTED_VIDEO_SUBMIT_FAILURE"):
            scenario.create()
        assert _counts(isolated_postgres17) == (0, 0, 0, 0, 0, 0, 0)
        return

    submission, envelope = scenario.submit_and_dispatch()
    if fail_at == "start":
        result = scenario.dispatcher.handle(envelope)
        assert result.status == "pending"
        job, run, receipt = scenario.read_pair(submission.run.job_id)
        assert job.state is JobState.QUEUED
        assert run.generation_state is JobState.QUEUED
        assert run.artifact is None and receipt is None
        assert _counts(isolated_postgres17) == (1, 1, 1, 0, 1, 1, 0)
        return

    result = scenario.dispatcher.handle(envelope)
    assert result.status == "pending"
    job, run, receipt = scenario.read_pair(submission.run.job_id)
    assert job.state is JobState.RUNNING
    assert run.generation_state is JobState.RUNNING
    assert run.artifact is None and receipt is None
    assert _counts(isolated_postgres17) == (1, 1, 1, 0, 1, 1, 0)


@pytest.mark.parametrize("mismatch", ["job_id", "attempt_id", "request_ref"])
def test_envelope_identity_and_pin_mismatches_fail_closed_without_final_artifact(
    isolated_postgres17, mismatch
):
    scenario = _build_scenario(isolated_postgres17)
    submission, envelope = scenario.submit_and_dispatch()
    if mismatch == "job_id":
        mismatched = replace(
            envelope, message=replace(envelope.message, job_id="job_mismatched")
        )
    elif mismatch == "attempt_id":
        mismatched = replace(
            envelope, message=replace(envelope.message, attempt_id="attempt_mismatched")
        )
    else:
        mismatched_ref = replace(envelope.message.request_ref, input_hash="b" * 64)
        mismatched = replace(
            envelope,
            message=replace(envelope.message, request_ref=mismatched_ref),
        )
    rejected = scenario.dispatcher.handle(mismatched)
    assert rejected.status == ("ignored" if mismatch == "request_ref" else "pending")
    job, run, receipt = scenario.read_pair(submission.run.job_id)
    assert job.state is JobState.QUEUED
    assert run.generation_state is JobState.QUEUED
    assert run.artifact is None and receipt is None
    assert scenario.generator.calls == 0
    assert _counts(isolated_postgres17) == (1, 1, 1, 0, 1, 1, 0)


@pytest.mark.parametrize("tamper", ["pin", "hash"])
def test_finalization_pin_or_hash_mismatch_cannot_be_reported_successful(
    isolated_postgres17, tamper
):
    scenario = _build_scenario(isolated_postgres17, stage_tamper=tamper)
    submission, envelope = scenario.submit_and_dispatch()
    result = scenario.dispatcher.handle(envelope)
    assert result.status == "pending"
    job, run, receipt = scenario.read_pair(submission.run.job_id)
    assert job.state is JobState.RUNNING
    assert run.generation_state is JobState.RUNNING
    assert run.artifact is None and receipt is None
    assert _counts(isolated_postgres17) == (1, 1, 1, 0, 1, 1, 0)

