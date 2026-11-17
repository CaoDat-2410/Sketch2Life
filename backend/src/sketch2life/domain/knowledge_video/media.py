"""Pure media admission under EXPLICIT adopted definitions, never render defaults."""

from __future__ import annotations

from dataclasses import dataclass, field

from sketch2life.domain.knowledge_video.model import (
    ExactRef,
    Strategy,
    VideoError,
    require_hash,
    require_id,
    require_revision,
)


def _codes(values: tuple[str, ...], *, empty: bool = False) -> None:
    if not isinstance(values, tuple) or (not values and not empty):
        raise VideoError("VIDEO_INVALID_MEDIA_PROFILE")
    for value in values:
        require_id(value)
    if len(set(values)) != len(values):
        raise VideoError("VIDEO_INVALID_MEDIA_PROFILE")


@dataclass(frozen=True, slots=True)
class MediaProfile:
    """Resolved registry terms, not permission merely because this object exists.

    Registry/authority adopter verifies definition bytes/hash/current adoption.
    All bounds are supplied; no production duration/size/codec values inferred.
    """

    content_profile: ExactRef
    encoding: ExactRef
    strategies: tuple[Strategy, ...]
    containers: tuple[str, ...]
    video_codecs: tuple[str, ...]
    dimensions: tuple[tuple[int, int], ...]
    min_duration_ms: int
    max_duration_ms: int
    max_bytes: int
    min_decoded_frames: int
    audio_codecs: tuple[str, ...]
    max_audio_streams: int

    def __post_init__(self) -> None:
        if not isinstance(self.content_profile, ExactRef) or not isinstance(
            self.encoding, ExactRef
        ):
            raise VideoError("VIDEO_INVALID_MEDIA_PROFILE")
        if (
            not isinstance(self.strategies, tuple)
            or not self.strategies
            or any(not isinstance(item, Strategy) for item in self.strategies)
            or len(set(self.strategies)) != len(self.strategies)
        ):
            raise VideoError("VIDEO_INVALID_MEDIA_PROFILE")
        for values in (self.containers, self.video_codecs):
            _codes(values)
        _codes(self.audio_codecs, empty=True)
        if not isinstance(self.dimensions, tuple) or not self.dimensions:
            raise VideoError("VIDEO_INVALID_MEDIA_PROFILE")
        for pair in self.dimensions:
            if not isinstance(pair, tuple) or len(pair) != 2:
                raise VideoError("VIDEO_INVALID_MEDIA_PROFILE")
            for size in pair:
                require_revision(size)
        if len(set(self.dimensions)) != len(self.dimensions):
            raise VideoError("VIDEO_INVALID_MEDIA_PROFILE")
        for value in (
            self.min_duration_ms,
            self.max_duration_ms,
            self.max_bytes,
            self.min_decoded_frames,
        ):
            require_revision(value)
        require_revision(self.max_audio_streams, minimum=0)
        if self.max_duration_ms < self.min_duration_ms or (
            self.max_audio_streams > 0 and not self.audio_codecs
        ):
            raise VideoError("VIDEO_INVALID_MEDIA_PROFILE")


@dataclass(frozen=True, slots=True)
class MediaBlob:
    payload: bytes = field(repr=False)
    sha256: str

    def __post_init__(self) -> None:
        if not isinstance(self.payload, bytes) or not self.payload:
            raise VideoError("VIDEO_MEDIA_INVALID")
        require_hash(self.sha256)


@dataclass(frozen=True, slots=True)
class DecodedMedia:
    """Decoder must decode complete bytes; probe/header-only data is insufficient."""

    source_hash: str
    container: str
    video_codec: str
    width: int
    height: int
    duration_ms: int
    decoded_frames: int
    audio_codecs: tuple[str, ...]
    complete: bool

    def __post_init__(self) -> None:
        require_hash(self.source_hash)
        require_id(self.container)
        require_id(self.video_codec)
        for value in (self.width, self.height, self.duration_ms, self.decoded_frames):
            require_revision(value)
        if not isinstance(self.audio_codecs, tuple):
            raise VideoError("VIDEO_MEDIA_INVALID")
        for codec in self.audio_codecs:
            require_id(codec)
        if self.complete is not True:
            raise VideoError("VIDEO_MEDIA_INCOMPLETE")


def validate_decoded(report: DecodedMedia, profile: MediaProfile, payload_hash: str) -> None:
    if (
        report.source_hash != payload_hash
        or report.container not in profile.containers
        or report.video_codec not in profile.video_codecs
        or (report.width, report.height) not in profile.dimensions
        or not profile.min_duration_ms <= report.duration_ms <= profile.max_duration_ms
        or report.decoded_frames < profile.min_decoded_frames
        or len(report.audio_codecs) > profile.max_audio_streams
        or any(codec not in profile.audio_codecs for codec in report.audio_codecs)
    ):
        raise VideoError("VIDEO_MEDIA_PROFILE_MISMATCH")
