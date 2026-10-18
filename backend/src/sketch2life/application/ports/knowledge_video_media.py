"""Owned08 candidate rendering boundaries; no default provider/authority/decoder."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Protocol

from sketch2life.domain.ai_jobs.model import JobState
from sketch2life.domain.knowledge_video.media import DecodedMedia, MediaBlob, MediaProfile
from sketch2life.domain.knowledge_video.model import (
    ExactRef,
    VideoError,
    VideoRun,
    require_hash,
    require_revision,
)

RenderPhase = Literal[
    "prepare",
    "library",
    "library_returned",
    "source",
    "source_returned",
    "generation",
    "generation_returned",
    "validation",
    "validation_returned",
    "before_stage",
    "after_stage",
    "before_finalize",
]


@dataclass(frozen=True, slots=True)
class RenderAttempt:
    run: VideoRun
    job_revision: int
    capability: str = field(repr=False)

    def __post_init__(self) -> None:
        if (
            not isinstance(self.run, VideoRun)
            or self.run.generation_state is not JobState.RUNNING
            or self.run.attempt_id is None
        ):
            raise VideoError("VIDEO_ATTEMPT_NOT_CURRENT")
        require_revision(self.job_revision)
        if not isinstance(self.capability, str) or not self.capability:
            raise VideoError("VIDEO_WORKER_CAPABILITY_REQUIRED")


@dataclass(frozen=True, slots=True)
class VideoSourceMaterial:
    """BE2-07 resolver verifies stored bundle bytes + current exact script lineage."""

    bundle: ExactRef
    pin_digest: str
    script: str = field(repr=False)

    def __post_init__(self) -> None:
        if (
            not isinstance(self.bundle, ExactRef)
            or not isinstance(self.script, str)
            or not self.script.strip()
        ):
            raise VideoError("VIDEO_SOURCE_INVALID")
        require_hash(self.pin_digest)


@dataclass(frozen=True, slots=True)
class LibraryMedia:
    """Resolved published/rights-eligible library asset bound to THIS request pin.

    asset hash identifies the catalog/content version; blob.sha256 identifies
    actual media bytes. Do not conflate these two hash namespaces.
    """

    asset: ExactRef
    pin_digest: str
    rights: ExactRef
    content_profile: ExactRef
    encoding: ExactRef
    blob: MediaBlob = field(repr=False)

    def __post_init__(self) -> None:
        for ref in (self.asset, self.rights, self.content_profile, self.encoding):
            if not isinstance(ref, ExactRef):
                raise VideoError("VIDEO_LIBRARY_MISMATCH")
        require_hash(self.pin_digest)
        if not isinstance(self.blob, MediaBlob):
            raise VideoError("VIDEO_MEDIA_INVALID")


class RenderAuthority(Protocol):
    def check(self, attempt: RenderAttempt, phase: RenderPhase) -> None:
        """Verify foundation attempt capability/current attempt/run revision, owner
        scope/consent/source/rights, adopted definitions and policy/profile epoch
        eligibility/kill/budget gates. No DB transaction held across external work.
        Checkpoints detect changes; NOT an atomic finalization/exposure fence.
        """
        ...


class MediaProfileResolver(Protocol):
    def resolve(self, attempt: RenderAttempt) -> MediaProfile: ...


class VideoSourceResolver(Protocol):
    def load(self, attempt: RenderAttempt) -> VideoSourceMaterial: ...


class LibraryResolver(Protocol):
    def resolve(self, attempt: RenderAttempt) -> LibraryMedia:
        """Resolve exact asset with current publication/recall/usage rights/content/
        profile/encoding/audience checks. No generation model needed for library.
        Returned descriptor is not a human approval or permanent usage grant.
        """
        ...


class VideoGenerator(Protocol):
    def generate(
        self, attempt: RenderAttempt, source: VideoSourceMaterial, operation_key: str
    ) -> MediaBlob:
        """Original pinned profile and stable key; errors/ambiguous acceptance are
        explicit. Adapter owns request/copy registration, cancellation/progress
        and approved deadlines. Never silently switches provider/model/strategy.
        """
        ...


class LibraryComposer(Protocol):
    def compose(
        self,
        attempt: RenderAttempt,
        source: VideoSourceMaterial,
        library: LibraryMedia,
        operation_key: str,
    ) -> MediaBlob: ...


class MediaDecoder(Protocol):
    def decode(self, blob: MediaBlob, encoding: ExactRef) -> DecodedMedia:
        """Decode full bounded bytes with approved runtime/resource/deadline profile.
        Metadata-only probe or provider success is not a valid implementation.
        """
        ...


class MediaValidator(Protocol):
    def validate(self, blob: MediaBlob, profile: MediaProfile) -> DecodedMedia: ...
