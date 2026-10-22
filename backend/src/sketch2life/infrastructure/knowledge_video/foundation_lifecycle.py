"""BE2-08 lifecycle participant bound to a BE2-01-owned SQL transaction."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Connection

from sketch2life.application.knowledge_video_media import PreparedVideoMedia
from sketch2life.application.knowledge_video_worker import completion_key as video_completion_key
from sketch2life.application.ports.ai_jobs import (
    AiJobRepository,
    CompletionReceipt,
    Principal,
    PrincipalRole,
    WorkerDispatchEnvelope,
)
from sketch2life.application.ports.knowledge_video import (
    VIDEO_LIFECYCLE_CONTRACT,
    AtomicVideoSubmission,
    VideoCommandReceipt,
    VideoCreationLease,
    VideoLifecycleCreateV1,
    VideoLifecycleTransaction,
    VideoRequestContext,
    VideoSubmission,
)
from sketch2life.application.ports.knowledge_video_media import RenderAttempt
from sketch2life.application.ports.knowledge_video_worker import (
    AtomicVideoFinalizer,
    StagedVideo,
    VideoFinalizationReceipt,
    VideoWorkerAdmission,
)
from sketch2life.application.services.ai_jobs import (
    AiJobService,
    CreateJobCommand,
)
from sketch2life.domain.ai_jobs.completion import CompletionClaim
from sketch2life.domain.ai_jobs.completion import OutcomeKind, OutputRef
from sketch2life.domain.ai_jobs.model import (
    AiJob,
    JobState,
    RequestRef,
    ResultDisposition,
)
from sketch2life.domain.knowledge_video.model import (
    FinalArtifact,
    VideoError,
    VideoPin,
    VideoRun,
    require_hash,
)
from sketch2life.infrastructure.knowledge_video.sql import VideoRunRows


class SqlVideoLifecycleTransaction(VideoLifecycleTransaction):
    """Apply BE2-08 domain transitions using only BE2-08 rows on the caller's connection."""

    contract_version = VIDEO_LIFECYCLE_CONTRACT

    def __init__(self, rows: VideoRunRows) -> None:
        self._rows = rows

    def submit(
        self,
        job: AiJob,
        binding: VideoLifecycleCreateV1,
        *,
        video_id: str,
        now: datetime,
        replayed: bool = False,
    ) -> VideoRun:
        self._validate_pair(job, binding)
        if job.state is not JobState.QUEUED:
            raise VideoError("VIDEO_SUBMISSION_MISMATCH")

        context = binding.context
        prior = self._rows.get_receipt(
            context.session_id, context.principal_id, context.idempotency_key
        )
        if prior is not None:
            if prior.command_hash != binding.command_hash or prior.pin_digest != binding.pin.digest():
                raise VideoError("VIDEO_IDEMPOTENCY_CONFLICT")
            run = self._rows.get(prior.video_id)
            if run is None or run.job_id != job.job_id or run.pin.digest() != binding.pin.digest():
                raise VideoError("VIDEO_RECEIPT_MISMATCH")
            return run
        if replayed:
            raise VideoError("VIDEO_RECEIPT_MISSING")

        run = self._rows.find_semantic(context.session_id, binding.pin.digest())
        if run is None:
            run = VideoRun(video_id, 1, 1, 1, job.job_id, binding.pin, now)
            self._rows.insert(run)
        elif run.job_id != job.job_id or run.pin != binding.pin:
            raise VideoError("VIDEO_SEMANTIC_JOB_CONFLICT")

        self._rows.put_receipt(VideoCommandReceipt(
            context.organization_id,
            context.session_id,
            context.principal_id,
            context.idempotency_key,
            binding.command_hash,
            binding.pin.digest(),
            run.video_id,
            now,
        ))
        return run

    def start(self, before: AiJob, after: AiJob, *, attempt_id: str) -> VideoRun:
        if (before.state is not JobState.QUEUED or after.state is not JobState.RUNNING
                or before.job_id != after.job_id
                or before.active_attempt.attempt_id != attempt_id
                or after.active_attempt.attempt_id != attempt_id):
            raise VideoError("VIDEO_ATTEMPT_NOT_CURRENT")
        run = self._rows.find_job(before.job_id, for_update=True)
        if run is None:
            raise VideoError("VIDEO_RUN_MISSING")
        self._validate_job_pin(before, run)
        updated = run.start(run.run_revision, attempt_id)
        self._rows.save(updated, expected_revision=run.run_revision)
        return updated

    def accept(
        self,
        before: AiJob,
        after: AiJob,
        claim: CompletionClaim,
        artifact: FinalArtifact,
    ) -> VideoRun:
        attempt_id = claim.attempt_id
        if (before.state is not JobState.RUNNING or after.state is not JobState.SUCCEEDED
                or after.result_disposition is not ResultDisposition.ACCEPTED
                or before.job_id != after.job_id or claim.job_id != before.job_id
                or before.active_attempt.attempt_id != attempt_id
                or after.active_attempt.attempt_id != attempt_id):
            raise VideoError("VIDEO_ACCEPTANCE_MISMATCH")
        if (len(claim.outputs) != 1
                or claim.outputs[0].artifact_ref != artifact.artifact.ref
                or claim.outputs[0].sha256 != artifact.artifact.hash):
            raise VideoError("VIDEO_ARTIFACT_MISMATCH")
        if not any(
            ref.artifact_ref == artifact.artifact.ref
            and ref.sha256 == artifact.artifact.hash
            for ref in after.result_refs
        ):
            raise VideoError("VIDEO_ARTIFACT_MISMATCH")

        run = self._rows.find_job(before.job_id, for_update=True)
        if run is None:
            raise VideoError("VIDEO_RUN_MISSING")
        self._validate_job_pin(before, run)
        if (run.generation_state is not JobState.RUNNING or run.attempt_id != attempt_id
                or artifact.pin_digest != run.pin.digest()):
            raise VideoError("VIDEO_ATTEMPT_NOT_CURRENT")
        updated = run.finalize(run.run_revision, attempt_id, artifact)
        self._rows.save(updated, expected_revision=run.run_revision)
        return updated

    def find_job(self, job_id: str, *, for_update: bool = False) -> VideoRun | None:
        return self._rows.find_job(job_id, for_update=for_update)

    @staticmethod
    def _validate_pair(job: AiJob, binding: VideoLifecycleCreateV1) -> None:
        if job.job_type != binding.job_type:
            raise VideoError("VIDEO_JOB_TYPE_MISMATCH")
        if (job.organization_id != binding.context.organization_id
                or job.scope.session_id != binding.context.session_id):
            raise VideoError("VIDEO_SCOPE_MISMATCH")
        request = job.request_ref
        pin = binding.pin
        if ((request.request_id, request.request_revision, request.input_hash,
             request.context_revision)
                != (pin.bundle.ref, pin.bundle.version, pin.bundle.hash, pin.audience_revision)):
            raise VideoError("VIDEO_PIN_MISMATCH")

    @classmethod
    def _validate_job_pin(cls, job: AiJob, run: VideoRun) -> None:
        if (run.job_id != job.job_id
                or run.pin.organization_id != job.organization_id
                or run.pin.session_id != job.scope.session_id):
            raise VideoError("VIDEO_JOB_PIN_MISMATCH")
        request = job.request_ref
        pin = run.pin
        if ((request.request_id, request.request_revision, request.input_hash,
             request.context_revision)
                != (pin.bundle.ref, pin.bundle.version, pin.bundle.hash, pin.audience_revision)):
            raise VideoError("VIDEO_PIN_MISMATCH")


class SqlVideoLifecycleFactory:
    """Bind the BE2-08 participant to the BE2-01 transaction connection."""

    def __call__(self, connection: Connection, organization_id: str) -> (
        VideoLifecycleTransaction
    ):
        return SqlVideoLifecycleTransaction(VideoRunRows(connection, organization_id))


class FoundationVideoSubmission(AtomicVideoSubmission):
    """Create BE2-01 and BE2-08 A state through the BE2-01 service/UoW."""

    def __init__(
        self,
        service: AiJobService,
        repository: AiJobRepository,
        *,
        job_type: str,
        purpose_code: str = "video_generation",
    ) -> None:
        self._service = service
        self._repository = repository
        self._job_type = job_type
        self._purpose_code = purpose_code

    def submit(
        self,
        *,
        context: VideoRequestContext,
        command_hash: str,
        lease: VideoCreationLease,
    ) -> VideoSubmission:
        require_hash(command_hash)
        if lease.context != context:
            raise VideoError("VIDEO_RESOLUTION_MISMATCH")
        pin = lease.pin
        binding = VideoLifecycleCreateV1(self._job_type, context, command_hash, pin)
        command = CreateJobCommand(
            principal=Principal(context.principal_id, context.organization_id,
                                PrincipalRole.TEACHER),
            idempotency_key=context.idempotency_key,
            job_type=self._job_type,
            target_id=pin.bundle.ref,
            purpose_code=self._purpose_code,
            session_id=context.session_id,
            subject_refs=tuple(sorted(source.ref for source in pin.sources)),
            request_ref=RequestRef(
                pin.bundle.ref,
                pin.bundle.version,
                pin.bundle.hash,
                pin.audience_revision,
            ),
            correlation_id=context.correlation_id,
            video_lifecycle=binding,
        )
        result = self._service.create_job(command)
        with self._repository.transaction() as tx:
            job = tx.get_job(result.job_id)
            if job is None:
                raise VideoError("VIDEO_JOB_MISSING")
            participant = tx.video_lifecycle(context.organization_id)
            if participant.contract_version != VIDEO_LIFECYCLE_CONTRACT:
                raise VideoError("VIDEO_CONTRACT_MISMATCH")
            run = participant.find_job(result.job_id)
            if run is None or run.pin.digest() != pin.digest():
                raise VideoError("VIDEO_SUBMISSION_MISMATCH")
            if job.active_attempt.attempt_id is None:
                raise VideoError("VIDEO_SUBMISSION_MISMATCH")
            outcome = "replayed" if result.replayed else result.outcome
            if outcome not in {"created", "replayed", "deduplicated"}:
                raise VideoError("VIDEO_SUBMISSION_MISMATCH")
            return VideoSubmission(
                run,
                result.job_revision,
                job.active_attempt.attempt_id,
                outcome,
            )


class FoundationVideoWorkerAdmission(VideoWorkerAdmission):
    """Validate the envelope and atomically start its persisted job/run pair."""

    def __init__(self, service: AiJobService, *, job_type: str) -> None:
        self._service = service
        self._job_type = job_type

    def begin(self, envelope: WorkerDispatchEnvelope) -> RenderAttempt | None:
        result = self._service.start_video_attempt(
            envelope, expected_job_type=self._job_type
        )
        if not result.started:
            return None
        if result.video_run is None or result.job_revision is None:
            raise VideoError("VIDEO_ADMISSION_MISMATCH")
        return RenderAttempt(result.video_run, result.job_revision, envelope.capability)


class FoundationVideoFinalizer(AtomicVideoFinalizer):
    """Accept BE2-01 results and BE2-08 artifacts in one BE2-01-owned UoW."""

    def __init__(
        self,
        service: AiJobService,
        repository: AiJobRepository,
        *,
        job_type: str,
    ) -> None:
        self._service = service
        self._repository = repository
        self._job_type = job_type

    def lookup(
        self,
        attempt: RenderAttempt,
        media: PreparedVideoMedia,
        staged: StagedVideo,
        completion_key: str,
    ) -> VideoFinalizationReceipt | None:
        if completion_key != video_completion_key(attempt, media, staged):
            raise VideoError("VIDEO_COMPLETION_KEY_MISMATCH")
        claim = self._claim(attempt, staged)
        expected_artifact = FinalArtifact(
            staged.artifact,
            attempt.run.pin.digest(),
            attempt.run.pin.encoding,
            attempt.run.pin.content_profile,
        )
        with self._repository.transaction() as tx:
            job = tx.get_job(attempt.run.job_id)
            receipt = tx.get_completion_receipt(attempt.run.job_id, attempt.run.attempt_id or "")
            if receipt is None:
                return None
            if (job is None or job.job_type != self._job_type
                    or receipt.fingerprint != claim.fingerprint()):
                raise VideoError("VIDEO_RECEIPT_MISMATCH")
            if receipt.disposition is ResultDisposition.ACCEPTED:
                run = tx.video_lifecycle(job.organization_id).find_job(job.job_id)
                if (not receipt.authoritative or job.state is not JobState.SUCCEEDED
                        or run is None or run.generation_state is not JobState.SUCCEEDED
                        or run.attempt_id != attempt.run.attempt_id
                        or run.artifact != expected_artifact):
                    raise VideoError("VIDEO_RECEIPT_MISMATCH")
                return VideoFinalizationReceipt(completion_key, receipt, run, job.state)
            return VideoFinalizationReceipt(completion_key, receipt, None, job.state)

    def finish(
        self,
        attempt: RenderAttempt,
        staged: StagedVideo,
        media: PreparedVideoMedia,
        completion_key: str,
    ) -> VideoFinalizationReceipt:
        artifact = FinalArtifact(
            staged.artifact,
            attempt.run.pin.digest(),
            attempt.run.pin.encoding,
            attempt.run.pin.content_profile,
        )
        self._service.accept_completion(
            attempt.capability,
            self._claim(attempt, staged),
            video_artifact=artifact,
        )
        result = self.lookup(attempt, media, staged, completion_key)
        if result is None:
            raise VideoError("VIDEO_RESULT_NOT_FINALIZED")
        return result

    def _claim(self, attempt: RenderAttempt, staged: StagedVideo) -> CompletionClaim:
        pin = attempt.run.pin
        return CompletionClaim(
            job_id=attempt.run.job_id,
            attempt_id=attempt.run.attempt_id or "",
            expected_request_revision=pin.bundle.version,
            input_hash=pin.bundle.hash,
            context_revision=pin.audience_revision,
            kind=OutcomeKind.SUCCESS,
            outputs=(OutputRef(staged.artifact.ref, staged.artifact.hash),),
        )


__all__ = [
    "FoundationVideoFinalizer",
    "FoundationVideoSubmission",
    "FoundationVideoWorkerAdmission",
    "SqlVideoLifecycleFactory",
    "SqlVideoLifecycleTransaction",
]
