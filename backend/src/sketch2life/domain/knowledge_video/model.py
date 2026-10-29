"""Owned DATA-27 candidate: immutable pins and pre-review run transitions.

These rules are NOT identity/consent/current-eligibility checks. Application code
must hold owner guards and coordinate foundation job changes in the same commit.
BE2-09 owns approval/playback; BE2-10 owns exhausted dispositions.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum

from sketch2life.domain.ai_jobs.model import JobState

_ID = re.compile(r"[A-Za-z0-9_.:-]{1,120}\Z")
_HASH = re.compile(r"[0-9a-f]{64}\Z")


class VideoError(ValueError):
    """Stable public code only; do not include script/media or provider diagnostics."""


class Strategy(StrEnum):
    REVIEWED_LIBRARY = "reviewed_library"
    GENERATE = "generate"
    COMPOSE_LIBRARY = "compose_library"


class ReviewState(StrEnum):
    PENDING_MEDIA = "pending_media"
    READY_FOR_REVIEW = "ready_for_review"


def require_id(value: str) -> None:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise VideoError("VIDEO_INVALID_ID")


def require_hash(value: str) -> None:
    if not isinstance(value, str) or not _HASH.fullmatch(value):
        raise VideoError("VIDEO_INVALID_HASH")


def require_revision(value: int, *, minimum: int = 1) -> None:
    if type(value) is not int or value < minimum:
        raise VideoError("VIDEO_INVALID_REVISION")


def require_time(value: datetime) -> None:
    if not isinstance(value, datetime) or value.utcoffset() is None:
        raise VideoError("VIDEO_INVALID_TIME")


def canonical_digest(value: object) -> str:
    """v1: UTF-8 JSON, sorted keys, compact separators, no NaN or implicit casts.

    Callers build only typed scalar/list/dict trees, not arbitrary provider JSON.
    Unicode text is preserved exactly; no hidden NFC/content normalization.
    """
    try:
        payload = json.dumps(value, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":"), allow_nan=False)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
    except (TypeError, ValueError, UnicodeError):
        raise VideoError("VIDEO_INVALID_CANONICAL_INPUT") from None


@dataclass(frozen=True, slots=True)
class ExactRef:
    ref: str
    version: int
    hash: str

    def __post_init__(self) -> None:
        require_id(self.ref)
        require_revision(self.version)
        require_hash(self.hash)

    def material(self) -> dict[str, str | int]:
        return {"ref": self.ref, "version": self.version, "hash": self.hash}


@dataclass(frozen=True, slots=True)
class VideoPin:
    """Server-resolved lineage; a pin is provenance, never a lasting authorization.

    Bundle digest must have been verified by the BE2-07 resolver. This owned
    request digest is NOT a replacement for upstream bundle canonicalization.
    Source refs have set semantics; each (id,version) occurs once.
    """

    organization_id: str
    session_id: str
    bundle: ExactRef
    editorial_revision: int
    context_revision: int
    audience_revision: int
    sources: tuple[ExactRef, ...]
    strategy: Strategy
    content_profile: ExactRef
    encoding: ExactRef
    rights: ExactRef
    retry_policy: ExactRef
    policy: ExactRef
    policy_epoch: int
    model_profile: ExactRef | None = None
    library_asset: ExactRef | None = None

    def __post_init__(self) -> None:
        require_id(self.organization_id)
        require_id(self.session_id)
        for value in (self.editorial_revision, self.context_revision, self.audience_revision):
            require_revision(value, minimum=0)
        require_revision(self.policy_epoch)
        for exact_ref in (self.bundle, self.content_profile, self.encoding,
                      self.rights, self.retry_policy, self.policy):
            if not isinstance(exact_ref, ExactRef):
                raise VideoError("VIDEO_INVALID_REF")
        if (not isinstance(self.sources, tuple) or not self.sources
                or not all(isinstance(ref, ExactRef) for ref in self.sources)):
            raise VideoError("VIDEO_INVALID_SOURCES")
        if len({(ref.ref, ref.version) for ref in self.sources}) != len(self.sources):
            raise VideoError("VIDEO_DUPLICATE_SOURCE")
        if not isinstance(self.strategy, Strategy):
            raise VideoError("VIDEO_INVALID_STRATEGY")
        for optional in (self.model_profile, self.library_asset):
            if optional is not None and not isinstance(optional, ExactRef):
                raise VideoError("VIDEO_INVALID_REF")
        if self.strategy is Strategy.GENERATE:
            if self.model_profile is None or self.library_asset is not None:
                raise VideoError("VIDEO_STRATEGY_REF_MISMATCH")
        elif self.strategy is Strategy.REVIEWED_LIBRARY:
            if self.library_asset is None or self.model_profile is not None:
                raise VideoError("VIDEO_STRATEGY_REF_MISMATCH")
        elif self.library_asset is None:
            raise VideoError("VIDEO_STRATEGY_REF_MISMATCH")

    def digest(self) -> str:
        material: dict[str, object] = {
            "schema": "BE2-08.VideoPin/0.1-candidate",
            "organization_id": self.organization_id,
            "session_id": self.session_id,
            "editorial_revision": self.editorial_revision,
            "context_revision": self.context_revision,
            "audience_revision": self.audience_revision,
            "policy_epoch": self.policy_epoch,
            "strategy": self.strategy.value,
            "sources": [ref.material() for ref in sorted(
                self.sources, key=lambda ref: (ref.ref, ref.version, ref.hash))],
        }
        for name in ("bundle", "content_profile", "encoding", "rights", "retry_policy",
                     "policy", "model_profile", "library_asset"):
            ref = getattr(self, name)
            material[name] = None if ref is None else ref.material()
        return canonical_digest(material)


@dataclass(frozen=True, slots=True)
class FinalArtifact:
    """Validator-produced final reference. Construction alone is not decoder proof."""

    artifact: ExactRef
    pin_digest: str
    encoding: ExactRef
    content_profile: ExactRef

    def __post_init__(self) -> None:
        if not all(isinstance(ref, ExactRef) for ref in (
            self.artifact, self.encoding, self.content_profile
        )):
            raise VideoError("VIDEO_INVALID_REF")
        require_hash(self.pin_digest)


@dataclass(frozen=True, slots=True)
class VideoRun:
    video_id: str
    video_version: int
    run_revision: int
    review_revision: int
    job_id: str
    pin: VideoPin
    created_at: datetime
    generation_state: JobState = JobState.QUEUED
    review_state: ReviewState = ReviewState.PENDING_MEDIA
    attempt_id: str | None = None
    artifact: FinalArtifact | None = None

    def __post_init__(self) -> None:
        require_id(self.video_id)
        require_id(self.job_id)
        for rev in (self.video_version, self.run_revision, self.review_revision):
            require_revision(rev)
        require_time(self.created_at)
        if not isinstance(self.pin, VideoPin):
            raise VideoError("VIDEO_INVALID_PIN")
        if (not isinstance(self.generation_state, JobState)
                or not isinstance(self.review_state, ReviewState)):
            raise VideoError("VIDEO_INVALID_STATE")
        if self.attempt_id is not None:
            require_id(self.attempt_id)
        ready = self.generation_state is JobState.SUCCEEDED
        if (ready != (self.artifact is not None)
                or ready != (self.review_state is ReviewState.READY_FOR_REVIEW)):
            raise VideoError("VIDEO_INCONSISTENT_AXES")
        if (self.generation_state in {JobState.RUNNING, JobState.SUCCEEDED}
                and self.attempt_id is None):
            raise VideoError("VIDEO_ATTEMPT_REQUIRED")
        if self.artifact is not None:
            if not isinstance(self.artifact, FinalArtifact):
                raise VideoError("VIDEO_INVALID_ARTIFACT")
            if (self.artifact.pin_digest != self.pin.digest()
                    or self.artifact.encoding != self.pin.encoding
                    or self.artifact.content_profile != self.pin.content_profile):
                raise VideoError("VIDEO_ARTIFACT_MISMATCH")

    def _expect(self, expected_revision: int) -> None:
        require_revision(expected_revision)
        if expected_revision != self.run_revision:
            raise VideoError("VIDEO_STALE_RUN")

    def start(self, expected_revision: int, attempt_id: str) -> VideoRun:
        self._expect(expected_revision)
        require_id(attempt_id)
        if self.generation_state is not JobState.QUEUED:
            raise VideoError("VIDEO_INVALID_TRANSITION")
        return replace(self, run_revision=self.run_revision + 1,
                       generation_state=JobState.RUNNING, attempt_id=attempt_id)

    def finalize(self, expected_revision: int, attempt_id: str,
                 artifact: FinalArtifact) -> VideoRun:
        """Pure transition; caller still owes current guards, decoder and job atomicity."""
        self._expect(expected_revision)
        if self.generation_state is not JobState.RUNNING or self.attempt_id != attempt_id:
            raise VideoError("VIDEO_ATTEMPT_NOT_CURRENT")
        return replace(self, run_revision=self.run_revision + 1,
                       generation_state=JobState.SUCCEEDED,
                       review_state=ReviewState.READY_FOR_REVIEW, artifact=artifact)

    def cancel(self, expected_revision: int) -> VideoRun:
        self._expect(expected_revision)
        if self.generation_state not in {
            JobState.QUEUED, JobState.RUNNING, JobState.FAILED_RETRYABLE
        }:
            raise VideoError("VIDEO_INVALID_TRANSITION")
        return replace(self, run_revision=self.run_revision + 1,
                       generation_state=JobState.CANCELLED)
