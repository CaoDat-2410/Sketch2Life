"""Pure exact video-review head. Actual authority/fences/persistence live outside.

Own09 head does not mutate08 immutable run/review_revision or imply playing.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum

from sketch2life.domain.ai_jobs.model import JobState
from sketch2life.domain.knowledge_video.model import (
    ExactRef,
    VideoError,
    VideoRun,
    canonical_digest,
    require_hash,
    require_id,
    require_revision,
    require_time,
)


class Decision(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_CHANGES = "request_changes"


class Applicability(StrEnum):
    EFFECTIVE = "effective"
    STALE = "stale"
    REVOKED = "revoked"


class Invalidation(StrEnum):
    CONTENT_CHANGED = "content_changed"
    CONTEXT_CHANGED = "context_changed"
    AUDIENCE_CHANGED = "audience_changed"
    USAGE_REVOKED = "usage_revoked"


def _ids(values: tuple[str, ...]) -> None:
    if not isinstance(values, tuple) or len(values) > 64 or len(values) != len(set(values)):
        raise VideoError("VIDEO_REVIEW_INVALID_AUDIENCE")
    for value in values:
        require_id(value)


@dataclass(frozen=True, slots=True)
class TeachingAudience:
    session_id: str
    audience_revision: int
    group_ids: tuple[str, ...]
    participant_ids: tuple[str, ...]
    consent_revisions: tuple[tuple[str, int], ...]

    def __post_init__(self) -> None:
        require_id(self.session_id)
        require_revision(self.audience_revision, minimum=0)
        _ids(self.group_ids)
        _ids(self.participant_ids)
        if not isinstance(self.consent_revisions, tuple) or len(self.consent_revisions) > 64:
            raise VideoError("VIDEO_REVIEW_INVALID_AUDIENCE")
        subjects = []
        for pair in self.consent_revisions:
            if not isinstance(pair, tuple) or len(pair) != 2:
                raise VideoError("VIDEO_REVIEW_INVALID_AUDIENCE")
            require_id(pair[0])
            require_revision(pair[1], minimum=0)
            subjects.append(pair[0])
        if len(subjects) != len(set(subjects)):
            raise VideoError("VIDEO_REVIEW_INVALID_AUDIENCE")
        object.__setattr__(self, "group_ids", tuple(sorted(self.group_ids)))
        object.__setattr__(self, "participant_ids", tuple(sorted(self.participant_ids)))
        object.__setattr__(self, "consent_revisions", tuple(sorted(self.consent_revisions)))

    def digest(self) -> str:
        return canonical_digest(
            {
                "schema": "BE2-09.TeachingAudience/0.1-candidate",
                "session": self.session_id,
                "revision": self.audience_revision,
                "groups": sorted(self.group_ids),
                "participants": sorted(self.participant_ids),
                "consents": sorted(self.consent_revisions),
                "purpose": "teaching_delivery",
            }
        )


@dataclass(frozen=True, slots=True)
class ReviewSubject:
    organization_id: str
    video_id: str
    video_version: int
    artifact: ExactRef
    pin_digest: str
    source_context_revision: int
    audience: TeachingAudience
    policy: ExactRef

    def __post_init__(self) -> None:
        require_id(self.organization_id)
        require_id(self.video_id)
        require_revision(self.video_version)
        require_revision(self.source_context_revision, minimum=0)
        require_hash(self.pin_digest)
        if type(self.artifact) is not ExactRef or type(self.policy) is not ExactRef:
            raise VideoError("VIDEO_REVIEW_INVALID_SUBJECT")
        replace(self.artifact)
        replace(self.policy)
        if type(self.audience) is not TeachingAudience:
            raise VideoError("VIDEO_REVIEW_INVALID_AUDIENCE")
        replace(self.audience)

    def digest(self) -> str:
        return canonical_digest(
            {
                "schema": "BE2-09.ReviewSubject/0.1-candidate",
                "org": self.organization_id,
                "video": self.video_id,
                "version": self.video_version,
                "artifact": self.artifact.material(),
                "pin": self.pin_digest,
                "context": self.source_context_revision,
                "audience": self.audience.digest(),
                "policy": self.policy.material(),
            }
        )

    @classmethod
    def from_ready(cls, run: VideoRun, audience: TeachingAudience) -> ReviewSubject:
        run = replace(run)
        audience = replace(audience)
        if run.generation_state is not JobState.SUCCEEDED or run.artifact is None:
            raise VideoError("VIDEO_REVIEW_MEDIA_NOT_READY")
        if (audience.session_id, audience.audience_revision) != (
            run.pin.session_id,
            run.pin.audience_revision,
        ):
            raise VideoError("VIDEO_REVIEW_AUDIENCE_MISMATCH")
        # Pin digest captures source/script/bundle/encoding/model/rights/epoch.
        return cls(
            run.pin.organization_id,
            run.video_id,
            run.video_version,
            run.artifact.artifact,
            run.pin.digest(),
            run.pin.context_revision,
            audience,
            run.pin.policy,
        )


@dataclass(frozen=True, slots=True)
class ReviewEntry:
    review_id: str
    revision: int
    subject: ReviewSubject
    reviewer_id: str
    decision: Decision
    reason: str | None
    recorded_at: datetime

    def __post_init__(self) -> None:
        require_id(self.review_id)
        require_id(self.reviewer_id)
        require_revision(self.revision)
        require_time(self.recorded_at)
        if type(self.subject) is not ReviewSubject or not isinstance(self.decision, Decision):
            raise VideoError("VIDEO_REVIEW_INVALID_RECORD")
        replace(self.subject)
        if self.reason is not None and (
            not isinstance(self.reason, str) or not self.reason.strip() or len(self.reason) > 200
        ):
            raise VideoError("VIDEO_REVIEW_INVALID_REASON")
        if self.decision is not Decision.APPROVE and self.reason is None:
            raise VideoError("VIDEO_REVIEW_REASON_REQUIRED")


@dataclass(frozen=True, slots=True)
class ReviewHead:
    subject: ReviewSubject
    revision: int
    entry: ReviewEntry | None = None
    applicability: Applicability = Applicability.EFFECTIVE
    invalidation: Invalidation | None = None

    def __post_init__(self) -> None:
        require_revision(self.revision)
        if type(self.subject) is not ReviewSubject:
            raise VideoError("VIDEO_REVIEW_INVALID_SUBJECT")
        replace(self.subject)
        if not isinstance(self.applicability, Applicability):
            raise VideoError("VIDEO_REVIEW_INVALID_STATE")
        if self.entry is not None:
            if type(self.entry) is not ReviewEntry:
                raise VideoError("VIDEO_REVIEW_INVALID_RECORD")
            entry = replace(self.entry)
            if entry.subject != self.subject or entry.revision > self.revision:
                raise VideoError("VIDEO_REVIEW_INVALID_RECORD")
            if self.applicability is Applicability.EFFECTIVE and entry.revision != self.revision:
                raise VideoError("VIDEO_REVIEW_INVALID_RECORD")
        if (self.applicability is Applicability.EFFECTIVE) != (self.invalidation is None):
            raise VideoError("VIDEO_REVIEW_INVALID_STATE")
        if self.invalidation is not None and not isinstance(self.invalidation, Invalidation):
            raise VideoError("VIDEO_REVIEW_INVALID_STATE")

    def record(
        self,
        expected_revision: int,
        review_id: str,
        reviewer_id: str,
        decision: Decision,
        reason: str | None,
        recorded_at: datetime,
    ) -> ReviewHead:
        self._cas(expected_revision)
        require_time(recorded_at)
        if self.applicability is not Applicability.EFFECTIVE:
            raise VideoError("VIDEO_REVIEW_TARGET_NOT_CURRENT")
        if self.entry is not None and recorded_at < self.entry.recorded_at:
            raise VideoError("VIDEO_REVIEW_INVALID_TIME")
        entry = ReviewEntry(
            review_id, self.revision + 1, self.subject, reviewer_id, decision, reason, recorded_at
        )
        return replace(self, revision=self.revision + 1, entry=entry)

    def invalidate(self, expected_revision: int, reason: Invalidation) -> ReviewHead:
        self._cas(expected_revision)
        if not isinstance(reason, Invalidation):
            raise VideoError("VIDEO_REVIEW_INVALID_STATE")
        if self.applicability is not Applicability.EFFECTIVE:
            raise VideoError("VIDEO_REVIEW_TARGET_NOT_CURRENT")
        state = (
            Applicability.REVOKED if reason is Invalidation.USAGE_REVOKED else Applicability.STALE
        )
        return replace(self, revision=self.revision + 1, applicability=state, invalidation=reason)

    def permits_intent(self, current: ReviewSubject) -> bool:
        """Historical pure applicability only, NEVER current access authorization."""
        replace(self)
        current = replace(current)
        return (
            self.subject == current
            and self.applicability is Applicability.EFFECTIVE
            and self.entry is not None
            and self.entry.decision is Decision.APPROVE
        )

    def _cas(self, expected: int) -> None:
        replace(self)
        require_revision(expected)
        if expected != self.revision:
            raise VideoError("VIDEO_REVIEW_STALE_REVISION")
