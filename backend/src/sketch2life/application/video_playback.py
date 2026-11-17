"""Guarded09 intent-first start/recovery component; no actual gateway/default binding."""

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Literal

from sketch2life.application.ports.video_playback import (
    PlaybackAccess,
    PlaybackBoundary,
    PlaybackBridge,
    PlaybackStore,
)
from sketch2life.domain.knowledge_video.model import VideoError
from sketch2life.domain.video_review.playback import (
    PlaybackIntent,
    PlaybackReceipt,
    PlaybackRequest,
    PlaybackState,
)


@dataclass(frozen=True, slots=True)
class PlaybackOutcome:
    status: Literal["pending", "confirmed", "rejected"]
    operation_key: str
    reason_code: Literal[
        "VIDEO_PLAYBACK_PENDING", "VIDEO_PLAYBACK_CONFIRMED", "VIDEO_PLAYBACK_REJECTED"
    ]
    receipt_id: str | None = None
    # Historical confirmation only: NEVER bearer URL/access grant or current player status.


def _outcome(intent: PlaybackIntent) -> PlaybackOutcome:
    if intent.receipt is None:
        return PlaybackOutcome("pending", intent.operation_key(), "VIDEO_PLAYBACK_PENDING")
    accepted = intent.state is PlaybackState.PLAYING
    return PlaybackOutcome(
        "confirmed" if accepted else "rejected",
        intent.operation_key(),
        "VIDEO_PLAYBACK_CONFIRMED" if accepted else "VIDEO_PLAYBACK_REJECTED",
        intent.receipt.receipt_id,
    )


class VideoPlaybackService:
    def __init__(
        self,
        boundary: PlaybackBoundary,
        store: PlaybackStore,
        bridge: PlaybackBridge,
        *,
        clock: Callable[[], datetime],
    ) -> None:
        self._boundary, self._store, self._bridge, self._clock = boundary, store, bridge, clock

    def start(
        self, principal_id: str, client_key: str, request: PlaybackRequest
    ) -> PlaybackOutcome:
        intent = PlaybackIntent(principal_id, client_key, replace(request), self._clock())
        subject = request.subject
        try:
            with self._boundary.guard(
                principal_id, subject.organization_id, subject.audience.session_id
            ) as access:
                # Original receipt/body recovery does NOT require stale current
                # review to become effective again, or authorize another effect.
                with self._store.transaction(
                    subject.organization_id, subject.audience.session_id
                ) as tx:
                    previous = tx.get(principal_id, client_key)
                if previous is not None:
                    previous = replace(previous)
                    if (previous.operation_key(), previous.request.digest()) != (
                        intent.operation_key(),
                        request.digest(),
                    ):
                        raise VideoError("VIDEO_PLAYBACK_IDEMPOTENCY_CONFLICT")
                    return self._recover(access, previous)
                access.check(intent, "prepare")
                head = replace(access.review_head(request))
                if (
                    not head.permits_intent(subject)
                    or head.entry is None
                    or head.revision != request.review_revision
                    or head.entry.review_id != request.review_id
                ):
                    raise VideoError("VIDEO_PLAYBACK_REVIEW_NOT_EFFECTIVE")
                # An insert commit failure can be ambiguous. Never call bridge
                # after such an exception. Original key lets later read recover.
                with self._store.transaction(
                    subject.organization_id, subject.audience.session_id
                ) as tx:
                    access.check(intent, "commit_intent")
                    tx.insert(intent)
                    access.check(intent, "commit_intent")
                access.check(intent, "dispatch")
                try:
                    receipt = self._bridge.start(intent)
                except Exception:
                    return _outcome(intent)
                return self._record(access, intent, receipt)
        except VideoError:
            raise
        except Exception:
            # No raw diagnostics/claim of rollback, no hidden retry/fallback.
            return _outcome(intent)

    def _recover(self, access: PlaybackAccess, intent: PlaybackIntent) -> PlaybackOutcome:
        access.check(intent, "recover")
        if intent.receipt is not None:
            return _outcome(intent)
        try:
            receipt = self._bridge.lookup(intent)
        except Exception:
            return _outcome(intent)
        if receipt is None:
            # A durable adoption/scheduler may reconcile a never-sent intent;
            # this request NEVER guesses and redispatches a possible prior effect.
            return _outcome(intent)
        return self._record(access, intent, receipt)

    def _record(
        self, access: PlaybackAccess, intent: PlaybackIntent, receipt: PlaybackReceipt
    ) -> PlaybackOutcome:
        try:
            settled = intent.settle(receipt)
            access.check(intent, "record_receipt")
            subject = intent.request.subject
            with self._store.transaction(
                subject.organization_id, subject.audience.session_id
            ) as tx:
                current = tx.get(intent.principal_id, intent.client_key)
                if current is None:
                    raise VideoError("VIDEO_PLAYBACK_INTENT_MISSING")
                current = replace(current)
                if current != intent:
                    if current == settled:
                        access.check(intent, "record_receipt")
                        return _outcome(current)
                    raise VideoError("VIDEO_PLAYBACK_STALE_INTENT")
                tx.save(settled, expected_revision=intent.revision)
                access.check(intent, "record_receipt")
            return _outcome(settled)
        except Exception:
            # Effect may have happened; recovery retains original key. No fake
            # deletion/revoke/cancel or grant after receipt/storage uncertainty.
            return _outcome(intent)
