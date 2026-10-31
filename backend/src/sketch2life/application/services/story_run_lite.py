"""Use cases for the isolated synthetic Parent StoryRun-lite API."""

from __future__ import annotations

import hashlib
import uuid
from contextlib import suppress

from sketch2life.application.ports.story_run_lite import (
    CommandResult,
    CoreAssetAdmissionPort,
    ImageNormalizerPort,
    ImageSafetyScannerPort,
    StoryRunLiteRepositoryPort,
    StoryRunLiteVisionPort,
    StoryRunReferencePort,
    ValidatedVisionResult,
)
from sketch2life.contracts.schemas.story_run_lite import (
    AttachAssetRequest,
    CancelRunRequest,
    CompleteUploadRequest,
    ConfirmSubjectRequest,
    CreateRunRequest,
    CreateUploadRequest,
)
from sketch2life.domain.story_run_lite import (
    MAX_IMAGE_PIXELS,
    MODEL_INPUT_LIMIT_BYTES,
    OwnerScopeKind,
    StoryRunLiteError,
    canonical_fingerprint,
    parse_etag_version,
    validate_idempotency_key,
    validate_part_number,
)


class StoryRunLiteService:
    """Resolve identity server-side and coordinate Core admission with Story transitions."""

    def __init__(
        self,
        *,
        repository: StoryRunLiteRepositoryPort,
        scanner: ImageSafetyScannerPort,
        normalizer: ImageNormalizerPort,
        vision: StoryRunLiteVisionPort,
        story_references: StoryRunReferencePort,
        asset_admission: CoreAssetAdmissionPort,
        actor_scope_kind: OwnerScopeKind = OwnerScopeKind.PARENT_ACCOUNT,
        actor_scope_ref: str = "synthetic-parent-local-v1",
    ) -> None:
        if not actor_scope_ref or len(actor_scope_ref) > 128:
            raise ValueError("the server-owned synthetic actor reference is invalid")
        self._repository = repository
        self._scanner = scanner
        self._normalizer = normalizer
        self._vision = vision
        self._story_references = story_references
        self._asset_admission = asset_admission
        self._actor_scope_kind = actor_scope_kind
        self._actor_scope_ref = actor_scope_ref

    def create_run(self, request: CreateRunRequest, *, idempotency_key: str) -> CommandResult:
        key_hash = validate_idempotency_key(idempotency_key)
        fingerprint = canonical_fingerprint(
            method="POST", path="/v1/story-runs", request=request.model_dump(mode="json")
        )
        return self._repository.create_run(
            actor_scope_kind=self._actor_scope_kind,
            actor_scope_ref=self._actor_scope_ref,
            profile_ref=request.profile_ref,
            key_sha256=key_hash,
            fingerprint_sha256=fingerprint,
        )

    def create_upload(self, request: CreateUploadRequest, *, idempotency_key: str) -> CommandResult:
        key_hash = validate_idempotency_key(idempotency_key)
        fingerprint = canonical_fingerprint(
            method="POST",
            path="/v1/upload-sessions",
            request=request.model_dump(mode="json"),
        )
        return self._repository.create_upload(
            actor_scope_kind=self._actor_scope_kind,
            actor_scope_ref=self._actor_scope_ref,
            run_id=request.target_ref,
            media_type=request.media_type,
            expected_size_bytes=request.expected_size_bytes,
            expected_sha256=request.expected_sha256,
            key_sha256=key_hash,
            fingerprint_sha256=fingerprint,
        )

    def put_part(
        self,
        *,
        upload_id: str,
        part_number: int,
        payload: bytes,
        declared_length: int,
        declared_sha256: str,
    ) -> CommandResult:
        validate_part_number(part_number)
        return self._repository.put_part(
            actor_scope_kind=self._actor_scope_kind,
            actor_scope_ref=self._actor_scope_ref,
            upload_id=upload_id,
            part_number=part_number,
            payload=payload,
            declared_length=declared_length,
            declared_sha256=declared_sha256,
        )

    def complete_upload(
        self,
        *,
        upload_id: str,
        request: CompleteUploadRequest,
        if_match: str | None,
        idempotency_key: str,
    ) -> CommandResult:
        expected_version = parse_etag_version(if_match)
        key_hash = validate_idempotency_key(idempotency_key)
        fingerprint = canonical_fingerprint(
            method="POST",
            path=f"/v1/upload-sessions/{upload_id}/complete",
            request=request.model_dump(mode="json"),
            expected_version=expected_version,
        )
        reservation = self._repository.reserve_complete_upload(
            actor_scope_kind=self._actor_scope_kind,
            actor_scope_ref=self._actor_scope_ref,
            upload_id=upload_id,
            expected_size_bytes=request.expected_size_bytes,
            expected_sha256=request.expected_sha256,
            expected_version=expected_version,
            key_sha256=key_hash,
            fingerprint_sha256=fingerprint,
        )
        if reservation.upload_id is None or reservation.claim_version is None:
            return reservation.command_result
        if reservation.snapshot is None or reservation.expected_sha256 is None:
            raise StoryRunLiteError(
                409,
                "UPLOAD_SESSION_STATE_CONFLICT",
                "The completed upload snapshot is unavailable.",
            )

        accepted = self._repository.finalize_complete_upload(reservation, key_sha256=key_hash)
        if not self._repository.open_upload_gate(
            upload_id=reservation.upload_id, claim_version=reservation.claim_version
        ):
            self._repository.fail_upload_admission(
                upload_id=reservation.upload_id,
                claim_version=reservation.claim_version,
                error_code="UPLOAD_SESSION_STATE_CONFLICT",
            )
            self._repository.remove_upload_quarantine(upload_id)
            return accepted

        snapshot = reservation.snapshot
        expected_sha = reservation.expected_sha256
        try:
            verdict = self._scanner.scan(snapshot, expected_sha)
        except Exception:  # scanner availability is fail-closed
            self._repository.fail_upload_admission(
                upload_id=upload_id,
                claim_version=reservation.claim_version,
                error_code="SCANNER_UNAVAILABLE",
            )
            self._repository.remove_upload_quarantine(upload_id)
            return accepted
        if verdict.decision != "CLEAN" or verdict.sha256 != expected_sha:
            failure_code = (
                "IMAGE_INFECTED" if verdict.decision == "INFECTED" else "SCANNER_UNAVAILABLE"
            )
            self._repository.fail_upload_admission(
                upload_id=upload_id,
                claim_version=reservation.claim_version,
                error_code=failure_code,
            )
            self._repository.remove_upload_quarantine(upload_id)
            return accepted

        try:
            normalized = self._normalizer.normalize(
                snapshot,
                original_media_type=reservation.original_media_type or "",
                sha256=expected_sha,
            )
        except Exception as exc:
            error_code = getattr(exc, "code", "IMAGE_NORMALIZATION_FAILED")
            self._repository.fail_upload_admission(
                upload_id=upload_id,
                claim_version=reservation.claim_version,
                error_code=str(error_code)[:64],
            )
            self._repository.remove_upload_quarantine(upload_id)
            return accepted

        if (
            normalized.original_sha256 != expected_sha
            or normalized.original_size_bytes != len(snapshot)
            or normalized.original_media_type != reservation.original_media_type
            or normalized.width < 1
            or normalized.height < 1
            or normalized.width * normalized.height > MAX_IMAGE_PIXELS
            or normalized.derived_size_bytes < 1
            or normalized.derived_size_bytes > MODEL_INPUT_LIMIT_BYTES
            or normalized.derived_size_bytes != len(normalized.derived_bytes)
            or normalized.derived_media_type not in {"image/jpeg", "image/png"}
            or hashlib.sha256(normalized.derived_bytes).hexdigest() != normalized.derived_sha256
            or not 128 * 1024 * 1024 <= normalized.worker_memory_limit_bytes <= 1_073_741_824
            or not 1 <= normalized.worker_cpu_percent <= 25
            or not 1 <= normalized.worker_deadline_seconds <= 120
            or not 0 < normalized.worker_peak_memory_bytes <= normalized.worker_memory_limit_bytes
            or normalized.worker_cpu_hard_cap_percent != normalized.worker_cpu_percent
            or normalized.worker_elapsed_ms < 1
        ):
            self._repository.fail_upload_admission(
                upload_id=upload_id,
                claim_version=reservation.claim_version,
                error_code="IMAGE_NORMALIZATION_FAILED",
            )
            self._repository.remove_upload_quarantine(upload_id)
            return accepted

        original_ref, derived_ref = str(uuid.uuid4()), str(uuid.uuid4())
        stored: list[str] = []
        try:
            self._repository.store_asset(original_ref, snapshot)
            stored.append(original_ref)
            self._repository.store_asset(derived_ref, normalized.derived_bytes)
            stored.append(derived_ref)
        except Exception:
            for asset_ref in stored:
                with suppress(Exception):
                    self._repository.delete_asset(asset_ref)
            self._repository.fail_upload_admission(
                upload_id=upload_id,
                claim_version=reservation.claim_version,
                error_code="STAGING_UNAVAILABLE",
            )
            self._repository.remove_upload_quarantine(upload_id)
            return accepted

        try:
            committed = self._repository.finish_upload_admission(
                upload_id=upload_id,
                claim_version=reservation.claim_version,
                original_asset_ref=original_ref,
                derived_asset_ref=derived_ref,
                normalized=normalized,
                scanner=verdict,
                actor_scope_ref=self._actor_scope_ref,
            )
        except Exception:
            # A failed database commit can have an ambiguous outcome. Keep both bytes so a
            # committed READY row cannot point at a file removed by this process. Startup
            # recovery fails a still-PROCESSING session without redispatching it.
            return accepted
        if not committed:
            for asset_ref in stored:
                with suppress(Exception):
                    self._repository.delete_asset(asset_ref)
            self._repository.fail_upload_admission(
                upload_id=upload_id,
                claim_version=reservation.claim_version,
                error_code="UPLOAD_SESSION_STATE_CONFLICT",
            )
        self._repository.remove_upload_quarantine(upload_id)
        return accepted

    def get_upload(self, upload_id: str) -> CommandResult:
        return self._repository.get_upload(
            actor_scope_kind=self._actor_scope_kind,
            actor_scope_ref=self._actor_scope_ref,
            upload_id=upload_id,
        )

    def abort_upload(
        self, *, upload_id: str, if_match: str | None, idempotency_key: str
    ) -> CommandResult:
        expected_version = parse_etag_version(if_match)
        key_hash = validate_idempotency_key(idempotency_key)
        fingerprint = canonical_fingerprint(
            method="DELETE",
            path=f"/v1/upload-sessions/{upload_id}",
            request={},
            expected_version=expected_version,
        )
        return self._repository.abort_upload(
            actor_scope_kind=self._actor_scope_kind,
            actor_scope_ref=self._actor_scope_ref,
            upload_id=upload_id,
            expected_version=expected_version,
            key_sha256=key_hash,
            fingerprint_sha256=fingerprint,
        )

    def attach_asset(
        self,
        *,
        run_id: str,
        request: AttachAssetRequest,
        if_match: str | None,
        idempotency_key: str,
    ) -> CommandResult:
        expected_version = parse_etag_version(if_match)
        if not self._story_references.authorize_upload_target(
            actor_scope_kind=self._actor_scope_kind,
            actor_scope_ref=self._actor_scope_ref,
            run_id=run_id,
        ):
            raise StoryRunLiteError(404, "NOT_FOUND", "StoryRun not found in this Parent scope.")
        pair = self._asset_admission.resolve_story_artwork(
            actor_scope_kind=self._actor_scope_kind,
            actor_scope_ref=self._actor_scope_ref,
            asset_ref=request.asset_ref,
            run_id=run_id,
        )
        key_hash = validate_idempotency_key(idempotency_key)
        fingerprint = canonical_fingerprint(
            method="POST",
            path=f"/v1/story-runs/{run_id}/assets",
            request=request.model_dump(mode="json"),
            expected_version=expected_version,
        )
        reservation, provider_job_id, claimed_version = self._repository.attach_asset(
            actor_scope_kind=self._actor_scope_kind,
            actor_scope_ref=self._actor_scope_ref,
            run_id=run_id,
            pair=pair,
            expected_revision=request.expected_revision,
            expected_version=expected_version,
            key_sha256=key_hash,
            fingerprint_sha256=fingerprint,
        )
        if provider_job_id is None or claimed_version is None or reservation.status_code != 202:
            return reservation

        initial = self._repository.finalize_attach_command(
            run_id=run_id, key_sha256=key_hash, claimed_version=claimed_version
        )
        if not self._repository.open_story_dispatch_gate(
            run_id=run_id, claimed_version=claimed_version
        ):
            return initial

        def persist(result: ValidatedVisionResult) -> bool:
            return self._repository.commit_vision_success(
                run_id=run_id,
                claimed_version=claimed_version,
                result_snapshot=result.result_snapshot,
                subject_label=result.subject_label,
                confidence=result.confidence,
                canonical_result_sha256=result.canonical_result_sha256,
                raw_body_sha256=result.raw_body_sha256,
            )

        attempt = self._vision.analyze(
            run_id=run_id,
            binding=pair.derived,
            persist_success=persist,
        )
        if attempt.state == "UNKNOWN":
            self._repository.mark_vision_unknown(
                run_id=run_id,
                claimed_version=claimed_version,
                error_code=attempt.error_code or "VISION_OUTCOME_UNKNOWN",
            )
        elif attempt.state == "FAILED":
            self._repository.mark_vision_failed_before_send(
                run_id=run_id,
                claimed_version=claimed_version,
                error_code=attempt.error_code or "VISION_ATTEMPT_FAILED",
            )
        return initial

    def get_run(self, run_id: str) -> CommandResult:
        return self._repository.get_run(
            actor_scope_kind=self._actor_scope_kind,
            actor_scope_ref=self._actor_scope_ref,
            run_id=run_id,
        )

    def confirm_subject(
        self,
        *,
        run_id: str,
        request: ConfirmSubjectRequest,
        if_match: str | None,
        idempotency_key: str,
    ) -> CommandResult:
        expected_version = parse_etag_version(if_match)
        key_hash = validate_idempotency_key(idempotency_key)
        fingerprint = canonical_fingerprint(
            method="POST",
            path=f"/v1/story-runs/{run_id}/subject-confirmation",
            request=request.model_dump(mode="json"),
            expected_version=expected_version,
        )
        return self._repository.confirm_subject(
            actor_scope_kind=self._actor_scope_kind,
            actor_scope_ref=self._actor_scope_ref,
            run_id=run_id,
            expected_version=expected_version,
            expected_understanding_revision=request.expected_understanding_revision,
            key_sha256=key_hash,
            fingerprint_sha256=fingerprint,
        )

    def cancel_run(
        self,
        *,
        run_id: str,
        request: CancelRunRequest,
        if_match: str | None,
        idempotency_key: str,
    ) -> CommandResult:
        expected_version = parse_etag_version(if_match)
        key_hash = validate_idempotency_key(idempotency_key)
        fingerprint = canonical_fingerprint(
            method="POST",
            path=f"/v1/story-runs/{run_id}/cancel",
            request=request.model_dump(mode="json"),
            expected_version=expected_version,
        )
        return self._repository.cancel_run(
            actor_scope_kind=self._actor_scope_kind,
            actor_scope_ref=self._actor_scope_ref,
            run_id=run_id,
            expected_revision=request.expected_revision,
            expected_version=expected_version,
            key_sha256=key_hash,
            fingerprint_sha256=fingerprint,
        )


__all__ = ["StoryRunLiteService"]
