"""Consume shared05 DATA-24 without forking it; pure binding, not owner authority."""

from dataclasses import replace

from sketch2life.contracts.schemas.ai_contract_candidates import (
    ExactContentReviewCommandV1,
    SessionAudienceV1,
    SessionContentContextV1,
)
from sketch2life.domain.knowledge_video.model import VideoError
from sketch2life.domain.video_review.model import Decision, ReviewSubject, TeachingAudience


def bind_video_review(
    command: ExactContentReviewCommandV1, subject: ReviewSubject
) -> ExactContentReviewCommandV1:
    """Subject/audience already resolved by trusted owner in future P2 guard.

    This helper neither resolves authority nor checks actual consent/moderation.
    Client audience is matched exactly to resolved subset, not accepted as grant.
    """
    try:
        subject = replace(subject)
        command = ExactContentReviewCommandV1.model_validate(
            command.model_dump(mode="python"), strict=True
        )
        if (
            command.target_kind != "knowledge_video"
            or not isinstance(command.review_context, SessionContentContextV1)
            or not isinstance(command.audience_scope, SessionAudienceV1)
            or command.review_dimension is not None
            or command.expected_review_revision is not None
        ):
            raise VideoError("VIDEO_REVIEW_INVALID_CONTEXT")
        context, audience = command.review_context, command.audience_scope
        resolved = TeachingAudience(
            audience.session_id,
            context.audience_context_revision,
            tuple(sorted(audience.group_ids)),
            tuple(sorted(audience.participant_ids)),
            tuple(
                sorted((item.subject_ref, item.revision) for item in context.consent_revision_refs)
            ),
        )
        if (
            command.target_id != subject.video_id
            or command.target_version != subject.video_version
            or command.target_hash != subject.artifact.hash
            or command.source_context_revision != subject.source_context_revision
            or resolved.digest() != subject.audience.digest()
        ):
            raise VideoError("VIDEO_REVIEW_TARGET_MISMATCH")
        if Decision(command.decision) is not Decision.APPROVE and (
            command.reason is None or not command.reason.strip()
        ):
            raise VideoError("VIDEO_REVIEW_REASON_REQUIRED")
        return command
    except VideoError:
        raise
    except (ValueError, TypeError, AttributeError):
        raise VideoError("VIDEO_REVIEW_INVALID_COMMAND") from None
