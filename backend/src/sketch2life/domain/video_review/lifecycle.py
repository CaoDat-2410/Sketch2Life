"""Pure09 invalidate/rebind event, retaining historical heads; not owner adoption."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum

from sketch2life.domain.knowledge_video.model import (
    VideoError,
    require_id,
    require_revision,
    require_time,
)
from sketch2life.domain.video_review.model import (
    Applicability,
    Invalidation,
    ReviewHead,
    ReviewSubject,
)


class ReviewChangeAction(StrEnum):
    INVALIDATE = "invalidate"
    REBIND = "rebind"


@dataclass(frozen=True, slots=True)
class ReviewChangeRequest:
    """Internal exact owner notice, not client authority or a new public route."""

    action: ReviewChangeAction
    reason: Invalidation
    target: ReviewSubject | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.action, ReviewChangeAction) or not isinstance(
            self.reason, Invalidation
        ):
            raise VideoError("VIDEO_REVIEW_INVALID_CHANGE")
        if self.action is ReviewChangeAction.INVALIDATE:
            if self.target is not None:
                raise VideoError("VIDEO_REVIEW_INVALID_CHANGE")
        elif type(self.target) is not ReviewSubject:
            raise VideoError("VIDEO_REVIEW_INVALID_CHANGE")
        else:
            replace(self.target)


def changed_heads(
    before: ReviewHead, request: ReviewChangeRequest
) -> tuple[ReviewHead, ReviewHead]:
    before, request = replace(before), replace(request)
    if request.action is ReviewChangeAction.INVALIDATE:
        if before.applicability is Applicability.EFFECTIVE:
            archived = before.invalidate(before.revision, request.reason)
        elif (
            before.applicability is Applicability.STALE
            and request.reason is Invalidation.USAGE_REVOKED
        ):
            # Revocation must strengthen a stale head, not accidentally revive it.
            archived = replace(
                before,
                revision=before.revision + 1,
                applicability=Applicability.REVOKED,
                invalidation=request.reason,
            )
        else:
            raise VideoError("VIDEO_REVIEW_TARGET_NOT_CURRENT")
        return archived, archived
    target = request.target
    if target is None:
        raise VideoError("VIDEO_REVIEW_INVALID_CHANGE")
    old = before.subject
    if (old.organization_id, old.audience.session_id, old.video_id) != (
        target.organization_id,
        target.audience.session_id,
        target.video_id,
    ):
        raise VideoError("VIDEO_REVIEW_SCOPE_MISMATCH")
    if target == old:
        if before.applicability is Applicability.EFFECTIVE:
            raise VideoError("VIDEO_REVIEW_CHANGE_REQUIRED")
        if request.reason is not before.invalidation:
            raise VideoError("VIDEO_REVIEW_CHANGE_REASON_MISMATCH")
        # Owner-authorized restoration can reopen the SAME exact bytes, but
        # starts EMPTY: historical approval never becomes effective again.
        return before, ReviewHead(target, before.revision + 1)
    if request.reason is Invalidation.USAGE_REVOKED:
        raise VideoError("VIDEO_REVIEW_INVALID_CHANGE")
    if (
        target.video_version < old.video_version
        or target.source_context_revision < old.source_context_revision
        or target.audience.audience_revision < old.audience.audience_revision
    ):
        raise VideoError("VIDEO_REVIEW_BACKWARD_CHANGE")
    if target.artifact != old.artifact and target.video_version <= old.video_version:
        raise VideoError("VIDEO_REVIEW_NEW_CONTENT_VERSION_REQUIRED")
    if (
        request.reason is Invalidation.CONTENT_CHANGED
        and target.pin_digest != old.pin_digest
        and target.video_version == old.video_version
        and target.source_context_revision == old.source_context_revision
        and target.audience == old.audience
        and target.policy == old.policy
    ):
        # CONTENT_CHANGED is an authenticated source notice. A pin hash ALONE
        # may also change for policy epoch, not necessarily script/media bytes.
        raise VideoError("VIDEO_REVIEW_NEW_CONTENT_VERSION_REQUIRED")
    if request.reason is Invalidation.AUDIENCE_CHANGED and target.audience == old.audience:
        raise VideoError("VIDEO_REVIEW_CHANGE_REASON_MISMATCH")
    if request.reason is Invalidation.CONTENT_CHANGED and (
        target.video_version == old.video_version
        and target.artifact == old.artifact
        and target.pin_digest == old.pin_digest
    ):
        raise VideoError("VIDEO_REVIEW_CHANGE_REASON_MISMATCH")
    if request.reason is Invalidation.CONTEXT_CHANGED and (
        target.source_context_revision == old.source_context_revision
        and target.policy == old.policy
        and target.pin_digest == old.pin_digest
    ):
        raise VideoError("VIDEO_REVIEW_CHANGE_REASON_MISMATCH")
    archived = (
        before.invalidate(before.revision, request.reason)
        if before.applicability is Applicability.EFFECTIVE
        else before
    )
    # One monotonic canonical revision across target changes; old approval is
    # retained only in archived head/history, never copied into the new head.
    return archived, ReviewHead(target, before.revision + 1)


@dataclass(frozen=True, slots=True)
class ReviewChange:
    event_id: str
    principal_id: str
    request: ReviewChangeRequest
    before: ReviewHead
    archived: ReviewHead
    after: ReviewHead
    recorded_at: datetime

    def __post_init__(self) -> None:
        require_id(self.event_id)
        require_id(self.principal_id)
        require_time(self.recorded_at)
        if (
            type(self.before) is not ReviewHead
            or type(self.archived) is not ReviewHead
            or type(self.after) is not ReviewHead
            or type(self.request) is not ReviewChangeRequest
        ):
            raise VideoError("VIDEO_REVIEW_INVALID_CHANGE")
        before, archived, after = replace(self.before), replace(self.archived), replace(self.after)
        if before.entry is not None and self.recorded_at < before.entry.recorded_at:
            raise VideoError("VIDEO_REVIEW_INVALID_TIME")
        if changed_heads(before, self.request) != (archived, after):
            raise VideoError("VIDEO_REVIEW_INVALID_CHANGE")

    @classmethod
    def create(
        cls,
        event_id: str,
        principal_id: str,
        before: ReviewHead,
        request: ReviewChangeRequest,
        expected_revision: int,
        recorded_at: datetime,
    ) -> ReviewChange:
        require_revision(expected_revision)
        before = replace(before)
        if before.revision != expected_revision:
            raise VideoError("VIDEO_REVIEW_STALE_REVISION")
        archived, after = changed_heads(before, request)
        return cls(event_id, principal_id, request, before, archived, after, recorded_at)
