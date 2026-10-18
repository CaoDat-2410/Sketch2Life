"""Guarded CMD-40 create composition; no default owner/provider/job bridge."""

from __future__ import annotations

from dataclasses import replace

from sketch2life.application.ports.knowledge_video import (
    AtomicVideoSubmission,
    VideoCreationResolver,
    VideoRequestContext,
    VideoSubmission,
)
from sketch2life.contracts.schemas.knowledge_video import (
    CreateKnowledgeVideo,
    KnowledgeVideoView,
    VideoExactRef,
)
from sketch2life.domain.ai_jobs.model import JobState
from sketch2life.domain.knowledge_video.model import (
    ExactRef,
    VideoError,
    VideoPin,
    canonical_digest,
)


def validate_submission_view(result: VideoSubmission) -> KnowledgeVideoView | None:
    """Check an adapter-supplied snapshot inside the current creation lease.

    This is a commit-time snapshot, not a later status/approval guarantee. Missing
    projections stay usable for internal component work but cannot serve HTTP.
    """
    view = result.view
    if view is None:
        return None
    # Revalidate even if an adapter used model_construct/model_copy to skip checks.
    view = KnowledgeVideoView.model_validate_json(view.model_dump_json(warnings="error"))
    run = result.run
    expected_artifact = None if run.artifact is None else run.artifact.artifact
    actual_artifact = None if view.artifact_ref is None else ExactRef(
        view.artifact_ref.ref, view.artifact_ref.version, view.artifact_ref.hash
    )
    if ((view.video_id, view.video_version, view.video_run_revision, view.video_review_revision,
         view.organization_id, view.session_id, view.job_id, view.job_revision,
         view.generation_state, view.review_state, view.created_at)
            != (run.video_id, run.video_version, run.run_revision, run.review_revision,
                run.pin.organization_id, run.pin.session_id, run.job_id, result.job_revision,
                run.generation_state.value, run.review_state.value, run.created_at)
            or ExactRef(view.retry_policy_version.ref, view.retry_policy_version.version,
                        view.retry_policy_version.hash) != run.pin.retry_policy
            or actual_artifact != expected_artifact
            or not view.attempt_history
            or view.attempt_history[-1].attempt_id != result.attempt_id
            or view.attempt_history[-1].state != run.generation_state.value):
        raise VideoError("VIDEO_SUBMISSION_MISMATCH")
    return view


def _ref_matches(requested: VideoExactRef, selected_ref: str,
                 selected_version: int, selected_hash: str) -> bool:
    return (requested.ref, requested.version, requested.hash) == (
        selected_ref, selected_version, selected_hash
    )


def validate_resolved_pin(context: VideoRequestContext, command: CreateKnowledgeVideo,
                          pin: VideoPin) -> None:
    if (pin.organization_id != context.organization_id or pin.session_id != context.session_id
            or pin.bundle.ref != command.bundle_id or pin.bundle.version != command.bundle_version
            or pin.bundle.hash != command.bundle_hash
            or pin.audience_revision != command.audience_context_revision
            or pin.strategy.value != command.strategy):
        raise VideoError("VIDEO_RESOLUTION_MISMATCH")
    if command.requested_profile_ref is not None:
        profile = pin.content_profile
        if not _ref_matches(
            command.requested_profile_ref, profile.ref, profile.version, profile.hash
        ):
            raise VideoError("VIDEO_RESOLUTION_MISMATCH")
    if command.candidate_library_asset_ref is not None:
        asset = pin.library_asset
        if asset is None or not _ref_matches(
            command.candidate_library_asset_ref, asset.ref, asset.version, asset.hash
        ):
            raise VideoError("VIDEO_RESOLUTION_MISMATCH")


class VideoCreateService:
    def __init__(self, resolver: VideoCreationResolver, submission: AtomicVideoSubmission) -> None:
        self._resolver = resolver
        self._submission = submission

    def create(self, context: VideoRequestContext,
               command: CreateKnowledgeVideo) -> VideoSubmission:
        # Optional fields are always serialized, preserving one body fingerprint for
        # omitted vs explicit-null. Correlation is observability, not semantic identity.
        body_hash = canonical_digest(command.model_dump(mode="json"))
        with self._resolver.hold(context, command) as lease:
            lease.assert_current()
            if lease.context != context:
                raise VideoError("VIDEO_RESOLUTION_MISMATCH")
            pin = lease.pin
            validate_resolved_pin(context, command, pin)
            result = self._submission.submit(context=context, command_hash=body_hash, lease=lease)
            # These checks detect a broken adapter, not repair a bad durable commit.
            # Atomic adapter owes the same checks BEFORE commit and holds owner guards.
            lease.assert_current()
            if result.run.pin.digest() != pin.digest():
                raise VideoError("VIDEO_SUBMISSION_MISMATCH")
            if result.outcome == "created" and (
                result.run.generation_state is not JobState.QUEUED
                or result.run.artifact is not None
            ):
                raise VideoError("VIDEO_SUBMISSION_MISMATCH")
            return replace(result, view=validate_submission_view(result))
