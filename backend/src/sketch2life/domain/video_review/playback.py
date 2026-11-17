"""Owned09 playback intent/history terms, not bearer grants or live player state."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum

from sketch2life.domain.knowledge_video.model import (
    VideoError,
    canonical_digest,
    require_hash,
    require_id,
    require_revision,
    require_time,
)
from sketch2life.domain.video_review.model import ReviewSubject


def playback_operation_key(principal_id: str, client_key: str, subject: ReviewSubject) -> str:
    """Scoped identity is independent of request body, for durable dedup/projection."""
    require_id(principal_id)
    require_id(client_key)
    if type(subject) is not ReviewSubject:
        raise VideoError("VIDEO_PLAYBACK_INVALID_TARGET")
    subject = replace(subject)
    return canonical_digest(
        {
            "schema": "BE2-09.PlaybackOperation/0.1-candidate",
            "org": subject.organization_id,
            "session": subject.audience.session_id,
            "principal": principal_id,
            "key": client_key,
        }
    )


@dataclass(frozen=True, slots=True)
class PlaybackRequest:
    """Internal exact resolved target; not an HTTP client authority assertion."""

    subject: ReviewSubject
    review_id: str
    review_revision: int
    expected_session_revision: int

    def __post_init__(self) -> None:
        if type(self.subject) is not ReviewSubject:
            raise VideoError("VIDEO_PLAYBACK_INVALID_TARGET")
        replace(self.subject)
        require_id(self.review_id)
        require_revision(self.review_revision)
        require_revision(self.expected_session_revision, minimum=0)

    def digest(self) -> str:
        return canonical_digest(
            {
                "schema": "BE2-09.PlaybackRequest/0.1-candidate",
                "subject": self.subject.digest(),
                "review": self.review_id,
                "review_revision": self.review_revision,
                "session_revision": self.expected_session_revision,
            }
        )


class PlaybackState(StrEnum):
    PENDING = "pending"
    PLAYING = "playing"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class PlaybackReceipt:
    """Actual BE1 bridge must authenticate this output; bool alone is not proof."""

    receipt_id: str
    operation_key: str
    request_digest: str
    principal_id: str
    session_revision_before: int
    session_revision_after: int
    accepted: bool
    recorded_at: datetime
    authoritative: bool

    def __post_init__(self) -> None:
        require_id(self.receipt_id)
        require_id(self.principal_id)
        require_hash(self.operation_key)
        require_hash(self.request_digest)
        require_revision(self.session_revision_before, minimum=0)
        require_revision(self.session_revision_after, minimum=0)
        require_time(self.recorded_at)
        if type(self.accepted) is not bool or self.authoritative is not True:
            raise VideoError("VIDEO_PLAYBACK_RECEIPT_UNVERIFIED")
        if (self.accepted and self.session_revision_after <= self.session_revision_before) or (
            not self.accepted and self.session_revision_after != self.session_revision_before
        ):
            raise VideoError("VIDEO_PLAYBACK_RECEIPT_MISMATCH")


@dataclass(frozen=True, slots=True)
class PlaybackIntent:
    principal_id: str
    client_key: str
    request: PlaybackRequest
    created_at: datetime
    revision: int = 1
    state: PlaybackState = PlaybackState.PENDING
    receipt: PlaybackReceipt | None = None

    def __post_init__(self) -> None:
        require_id(self.principal_id)
        require_id(self.client_key)
        require_time(self.created_at)
        require_revision(self.revision)
        if type(self.request) is not PlaybackRequest:
            raise VideoError("VIDEO_PLAYBACK_INVALID_TARGET")
        replace(self.request)
        if not isinstance(self.state, PlaybackState):
            raise VideoError("VIDEO_PLAYBACK_INVALID_STATE")
        if self.state is PlaybackState.PENDING:
            if self.revision != 1 or self.receipt is not None:
                raise VideoError("VIDEO_PLAYBACK_INVALID_STATE")
        else:
            if type(self.receipt) is not PlaybackReceipt or self.revision != 2:
                raise VideoError("VIDEO_PLAYBACK_INVALID_STATE")
            self._bind(replace(self.receipt))
            if (self.state is PlaybackState.PLAYING) != self.receipt.accepted:
                raise VideoError("VIDEO_PLAYBACK_INVALID_STATE")

    def operation_key(self) -> str:
        # Key scope and request body digest deliberately separate: changed body
        # under same key conflicts instead of creating a second external request.
        return playback_operation_key(self.principal_id, self.client_key, self.request.subject)

    def _bind(self, receipt: PlaybackReceipt) -> None:
        if (
            receipt.operation_key != self.operation_key()
            or receipt.request_digest != self.request.digest()
            or receipt.principal_id != self.principal_id
            or receipt.session_revision_before != self.request.expected_session_revision
            or receipt.recorded_at < self.created_at
        ):
            raise VideoError("VIDEO_PLAYBACK_RECEIPT_MISMATCH")

    def settle(self, receipt: PlaybackReceipt) -> PlaybackIntent:
        replace(self)
        receipt = replace(receipt)
        self._bind(receipt)
        if self.receipt is not None:
            if self.receipt == receipt:
                return self
            raise VideoError("VIDEO_PLAYBACK_RECEIPT_CONFLICT")
        return replace(
            self,
            revision=2,
            receipt=receipt,
            state=PlaybackState.PLAYING if receipt.accepted else PlaybackState.REJECTED,
        )
