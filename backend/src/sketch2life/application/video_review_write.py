"""Guarded exact-session CMD-41 review component; no real authority/store binding."""

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime

from sketch2life.application.ports.video_review_write import (
    ReviewWriteBoundary,
    ReviewWriteContext,
    ReviewWriteReceipt,
    ReviewWriteSnapshot,
    ReviewWriteStore,
)
from sketch2life.application.video_review_contract import bind_video_review
from sketch2life.contracts.schemas.ai_contract_candidates import (
    ExactContentReviewCommandV1,
    ExactContentReviewRecordV1,
)
from sketch2life.domain.knowledge_video.model import VideoError, canonical_digest
from sketch2life.domain.video_review.model import Decision, ReviewHead


@dataclass(frozen=True, slots=True)
class ReviewWriteOutcome:
    record: ExactContentReviewRecordV1
    current_review_revision: int
    replayed: bool
    # Shared record state refreshed from CURRENT head; no playback/access grant.


def review_fingerprint(
    context: ReviewWriteContext,
    command: ExactContentReviewCommandV1,
    snapshot: ReviewWriteSnapshot,
) -> str:
    # Subject contains canonical set-ordered audience+consent refs/lineage; do not
    # hash caller ordering or the moving head revision on replay. If-Match remains
    # original request precondition; changed key/body/precondition must conflict.
    return canonical_digest(
        {
            "schema": "BE2-09.ReviewWrite/0.1-candidate",
            "principal": context.principal_id,
            "org": context.organization_id,
            "session": context.session_id,
            "video": context.video_id,
            "expected_review_revision": context.expected_review_revision,
            "subject": snapshot.head.subject.digest(),
            "decision": command.decision,
            "reason": command.reason,
        }
    )


def _project(receipt: ReviewWriteReceipt, head: ReviewHead, replayed: bool) -> ReviewWriteOutcome:
    # An immutable original receipt is historical, not an eternally effective
    # approval. A later reject/new review supersedes it; stale/revoked stays so.
    state = "stale"
    if head.entry == receipt.entry:
        state = head.applicability.value
    record = ExactContentReviewRecordV1.model_validate(
        receipt.record.model_dump(mode="python") | {"state": state}, strict=True
    )
    return ReviewWriteOutcome(record, head.revision, replayed)


class VideoReviewWriteService:
    def __init__(
        self,
        boundary: ReviewWriteBoundary,
        store: ReviewWriteStore,
        *,
        clock: Callable[[], datetime],
        review_ids: Callable[[], str],
    ) -> None:
        self._boundary, self._store = boundary, store
        self._clock, self._review_ids = clock, review_ids

    def record(
        self, context: ReviewWriteContext, command: ExactContentReviewCommandV1
    ) -> ReviewWriteOutcome:
        try:
            context = replace(context)
            command = ExactContentReviewCommandV1.model_validate(
                command.model_dump(mode="python"), strict=True
            )
        except (TypeError, ValueError, AttributeError):
            raise VideoError("VIDEO_REVIEW_INVALID_COMMAND") from None
        try:
            with self._boundary.guard(context) as access:
                snapshot = replace(access.resolve(context, command))
                subject = snapshot.head.subject
                if (subject.organization_id, subject.audience.session_id, subject.video_id) != (
                    context.organization_id,
                    context.session_id,
                    context.video_id,
                ):
                    raise VideoError("VIDEO_REVIEW_SCOPE_MISMATCH")
                command = bind_video_review(command, subject)
                access.check(context, command, snapshot, "prepare")
                fingerprint = review_fingerprint(context, command, snapshot)
                with self._store.transaction(
                    context.organization_id, context.session_id, context.video_id
                ) as tx:
                    before = tx.head()
                    current = snapshot.head if before is None else replace(before)
                    if (before is None and current.entry is not None) or current != snapshot.head:
                        raise VideoError("VIDEO_REVIEW_HEAD_NOT_CURRENT")
                    stored = tx.receipt(context.principal_id, context.client_key)
                    if stored is not None:
                        stored = replace(stored)
                        if stored.context != context or stored.fingerprint != fingerprint:
                            raise VideoError("VIDEO_REVIEW_IDEMPOTENCY_CONFLICT")
                        if (
                            stored.entry.subject != subject
                            or stored.entry.revision > current.revision
                            or (
                                stored.entry.revision == current.revision
                                and stored.entry != current.entry
                            )
                            or stored.entry.decision.value != command.decision
                            or stored.entry.reason != command.reason
                        ):
                            raise VideoError("VIDEO_REVIEW_INVALID_RECEIPT")
                        access.check(context, command, snapshot, "replay")
                        outcome = _project(stored, current, True)
                        access.check(context, command, snapshot, "replay")
                    else:
                        after = current.record(
                            context.expected_review_revision,
                            self._review_ids(),
                            context.principal_id,
                            Decision(command.decision),
                            command.reason,
                            self._clock(),
                        )
                        if after.entry is None:
                            raise VideoError("VIDEO_REVIEW_INVALID_RECORD")
                        shared = ExactContentReviewRecordV1(
                            review_id=after.entry.review_id,
                            review_revision=after.revision,
                            reviewer_principal_id=context.principal_id,
                            reviewed_at=after.entry.recorded_at,
                            policy_version=snapshot.policy_version,
                            state="effective",
                        )
                        receipt = ReviewWriteReceipt(context, fingerprint, after.entry, shared)
                        access.check(context, command, snapshot, "commit")
                        tx.write(before, after, receipt)
                        outcome = _project(receipt, after, False)
                        access.check(context, command, snapshot, "commit")
            return outcome
        except VideoError:
            raise
        except Exception:
            # A commit/guard-exit error may follow successful commit. Caller must
            # replay original key/body under current guards; never claim rollback.
            raise VideoError("VIDEO_REVIEW_DEPENDENCY_UNAVAILABLE") from None
