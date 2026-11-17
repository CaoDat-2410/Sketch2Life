"""Owned video copy metadata producer and guarded BE2-14 operation-hook consumer.

No automatic registration/coverage claim, provider activation or deletion verifier.
Production durable journal, inventory source and delivery guards remain adopters.
"""

from dataclasses import replace
from typing import Literal

from sketch2life.application.ai_policy_copy_operations import validate_operation
from sketch2life.application.knowledge_video_media import media_operation_key
from sketch2life.application.ports.knowledge_video_copy import (
    VideoCopyControl,
    VideoCopyHookBoundary,
)
from sketch2life.application.ports.knowledge_video_media import RenderAttempt
from sketch2life.contracts.schemas.ai_policy import PolicyDefinitionRef
from sketch2life.contracts.schemas.ai_policy_copy import CopyReceiptReference
from sketch2life.contracts.schemas.ai_policy_copy_delivery import CopyHookResponse
from sketch2life.contracts.schemas.ai_policy_copy_operation import CopyOperationEnvelope
from sketch2life.contracts.schemas.ai_policy_copy_registry import CopyRegistryRegistration
from sketch2life.contracts.schemas.knowledge_video_copy import VideoCopyJournalEntry
from sketch2life.domain.knowledge_video.model import ExactRef, VideoError


def video_copy_entry(
    attempt: RenderAttempt,
    *,
    scope_ref: str,
    original_provider_profile: ExactRef,
    copy_id: str,
    role: Literal["input", "script", "output", "cache", "job"],
    source_reference: CopyReceiptReference,
) -> VideoCopyJournalEntry:
    """Map observed original copy metadata, not proof that copy exists/is complete.

    scope_ref comes from adopted subject mapping, NOT assumed session ID. Provider
    profile must be resolved explicitly: model/content/encoding refs are NOT it.
    Journal must persist original planned keys before/with external effects and
    authenticate discoveries, including failed/ambiguous generation. This helper
    alone provides neither durability nor inventory source/coverage attestation.
    """
    try:
        attempt = replace(attempt)
        run = replace(attempt.run)
        if run.attempt_id is None:
            raise VideoError("VIDEO_COPY_INVALID_SOURCE")
        profile = PolicyDefinitionRef.model_validate(
            original_provider_profile.material(), strict=True
        )
        result = VideoCopyJournalEntry(
            registration=CopyRegistryRegistration(
                organization_id=run.pin.organization_id,
                scope_ref=scope_ref,
                copy_id=copy_id,
                kind="input" if role == "script" else role,
                original_profile_ref=profile,
            ),
            video_id=run.video_id,
            video_version=run.video_version,
            job_id=run.job_id,
            attempt_id=run.attempt_id,
            pin_digest=run.pin.digest(),
            media_operation_key=media_operation_key(attempt),
            role=role,
            source_reference=source_reference,
        )
        return VideoCopyJournalEntry.model_validate(result.model_dump(mode="python"), strict=True)
    except (ValueError, TypeError, AttributeError):
        raise VideoError("VIDEO_COPY_INVALID_SOURCE") from None


def _response(
    envelope: CopyOperationEnvelope,
    outcome: Literal["pending", "unsupported", "exception"],
    reason: str,
) -> CopyHookResponse:
    return CopyHookResponse(
        operation_key=envelope.operation_key,
        binding_digest=envelope.binding_digest,
        outcome=outcome,
        reason_code=reason,
    )


class VideoProviderCopyHook:
    """Implements14 ProviderCopyOperationHook shape; no actual provider selected."""

    def __init__(
        self, boundary: VideoCopyHookBoundary, *, control: VideoCopyControl | None
    ) -> None:
        self._boundary, self._control = boundary, control

    def dispatch(self, envelope: CopyOperationEnvelope) -> CopyHookResponse:
        try:
            envelope = validate_operation(envelope)
        except Exception:
            # Cannot return a trustworthy response key for a malformed envelope.
            raise VideoError("VIDEO_COPY_INVALID_OPERATION") from None
        dispatched = False
        try:
            with self._boundary.guard(envelope) as access:
                raw = access.original(envelope)
                original = VideoCopyJournalEntry.model_validate(
                    raw.model_dump(mode="python"), strict=True
                )
                if original.registration != envelope.target:
                    return _response(envelope, "exception", "VIDEO_COPY_ORIGINAL_MISMATCH")
                access.confirm(envelope, original)
                if self._control is None:
                    return _response(envelope, "unsupported", "VIDEO_COPY_CONTROL_UNAVAILABLE")
                dispatched = True
                response = self._control.dispatch(envelope, original)
                response = CopyHookResponse.model_validate(
                    response.model_dump(mode="python"), strict=True
                )
                if (response.operation_key, response.binding_digest) != (
                    envelope.operation_key,
                    envelope.binding_digest,
                ):
                    return _response(envelope, "pending", "VIDEO_COPY_RESPONSE_UNVERIFIED")
                access.confirm(envelope, original)
            return response
        except Exception:
            # An effect/commit may already exist, including guard-exit failure.
            # Never repeat here or claim rollback/cancellation/deletion occurred.
            return _response(
                envelope,
                "pending" if dispatched else "exception",
                "VIDEO_COPY_EFFECT_UNKNOWN" if dispatched else "VIDEO_COPY_BOUNDARY_UNAVAILABLE",
            )
