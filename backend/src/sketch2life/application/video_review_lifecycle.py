"""Guarded own09 change composition; persistence/real invalidation fence not supplied."""

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime

from sketch2life.application.ports.video_review_lifecycle import (
    ReviewChangeReceipt,
    ReviewLifecycleBoundary,
    ReviewLifecycleStore,
    change_fingerprint,
)
from sketch2life.application.ports.video_review_write import ReviewWriteContext
from sketch2life.domain.knowledge_video.model import VideoError
from sketch2life.domain.video_review.lifecycle import ReviewChange, ReviewChangeRequest


@dataclass(frozen=True, slots=True)
class ReviewChangeOutcome:
    event_id: str
    applied_review_revision: int
    replayed: bool
    # Historical application receipt only; no effective approval/playback/access ref.


class VideoReviewLifecycleService:
    def __init__(
        self,
        boundary: ReviewLifecycleBoundary,
        store: ReviewLifecycleStore,
        *,
        clock: Callable[[], datetime],
        event_ids: Callable[[], str],
    ) -> None:
        self._boundary, self._store, self._clock, self._event_ids = (
            boundary,
            store,
            clock,
            event_ids,
        )

    def apply(
        self, context: ReviewWriteContext, request: ReviewChangeRequest
    ) -> ReviewChangeOutcome:
        try:
            context, request = replace(context), replace(request)
        except (ValueError, TypeError, AttributeError):
            raise VideoError("VIDEO_REVIEW_INVALID_CHANGE") from None
        try:
            with self._boundary.guard(context) as access:
                # Read original receipt first: after a successful rebind the old
                # head is no longer current. Replay never reapplies the transition.
                with self._store.transaction(
                    context.organization_id, context.session_id, context.video_id
                ) as tx:
                    prior = tx.change_receipt(context.principal_id, context.client_key)
                if prior is not None:
                    prior = replace(prior)
                    if prior.context != context or change_fingerprint(
                        context, request
                    ) != change_fingerprint(prior.context, prior.request):
                        raise VideoError("VIDEO_REVIEW_IDEMPOTENCY_CONFLICT")
                    access.check(prior, "replay")
                    outcome = ReviewChangeOutcome(
                        prior.change.event_id, prior.change.after.revision, True
                    )
                else:
                    before = replace(access.resolve(context, request))
                    subject = before.subject
                    if (subject.organization_id, subject.audience.session_id, subject.video_id) != (
                        context.organization_id,
                        context.session_id,
                        context.video_id,
                    ):
                        raise VideoError("VIDEO_REVIEW_SCOPE_MISMATCH")
                    change = ReviewChange.create(
                        self._event_ids(),
                        context.principal_id,
                        before,
                        request,
                        context.expected_review_revision,
                        self._clock(),
                    )
                    receipt = ReviewChangeReceipt(context, request, change)
                    access.check(receipt, "prepare")
                    with self._store.transaction(
                        context.organization_id, context.session_id, context.video_id
                    ) as tx:
                        current = tx.head()
                        if current is None or replace(current) != before:
                            raise VideoError("VIDEO_REVIEW_HEAD_NOT_CURRENT")
                        access.check(receipt, "commit")
                        tx.change(receipt)
                        access.check(receipt, "commit")
                    outcome = ReviewChangeOutcome(change.event_id, change.after.revision, False)
            return outcome
        except VideoError:
            raise
        except Exception:
            # Could be committed already; retry original key under current guards.
            raise VideoError("VIDEO_REVIEW_DEPENDENCY_UNAVAILABLE") from None
