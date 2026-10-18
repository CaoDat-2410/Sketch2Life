"""Owned strategy preparation. Produces uncommitted media, NEVER ready/approved.

External work runs without a database transaction. P3 must accept/quarantine the
result under actual current-owner/foundation completion guards and one commit.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field, replace

from sketch2life.application.ports.knowledge_video_media import (
    LibraryComposer,
    LibraryMedia,
    LibraryResolver,
    MediaDecoder,
    MediaProfileResolver,
    MediaValidator,
    RenderAttempt,
    RenderAuthority,
    VideoGenerator,
    VideoSourceMaterial,
    VideoSourceResolver,
)
from sketch2life.domain.knowledge_video.media import (
    DecodedMedia,
    MediaBlob,
    MediaProfile,
    validate_decoded,
)
from sketch2life.domain.knowledge_video.model import Strategy, VideoError, canonical_digest


def _admit_blob(blob: MediaBlob, profile: MediaProfile) -> MediaBlob:
    if not isinstance(blob, MediaBlob) or not isinstance(profile, MediaProfile):
        raise VideoError("VIDEO_MEDIA_INVALID")
    # Bound size BEFORE hashing/decoder work. Recheck frozen native objects.
    blob = replace(blob)
    if len(blob.payload) > profile.max_bytes:
        raise VideoError("VIDEO_MEDIA_TOO_LARGE")
    if hashlib.sha256(blob.payload).hexdigest() != blob.sha256:
        raise VideoError("VIDEO_MEDIA_HASH_MISMATCH")
    return blob


class CheckedMediaValidator:
    def __init__(self, decoder: MediaDecoder) -> None:
        self._decoder = decoder

    def validate(self, blob: MediaBlob, profile: MediaProfile) -> DecodedMedia:
        if not isinstance(profile, MediaProfile):
            raise VideoError("VIDEO_PROFILE_UNAVAILABLE")
        profile = replace(profile)
        blob = _admit_blob(blob, profile)
        report = self._decoder.decode(blob, profile.encoding)
        if not isinstance(report, DecodedMedia):
            raise VideoError("VIDEO_MEDIA_INVALID")
        report = DecodedMedia(
            report.source_hash,
            report.container,
            report.video_codec,
            report.width,
            report.height,
            report.duration_ms,
            report.decoded_frames,
            report.audio_codecs,
            report.complete,
        )
        validate_decoded(report, profile, blob.sha256)
        return report


@dataclass(frozen=True, slots=True)
class PreparedVideoMedia:
    """Uncommitted internal output; NOT an artifact, completion receipt or bearer grant."""

    pin_digest: str
    operation_key: str
    blob: MediaBlob = field(repr=False)
    decoded: DecodedMedia
    strategy: Strategy


def _check_library(attempt: RenderAttempt, library: LibraryMedia) -> None:
    pin = attempt.run.pin
    if (
        not isinstance(library, LibraryMedia)
        or library.asset != pin.library_asset
        or library.pin_digest != pin.digest()
        or library.rights != pin.rights
        or library.content_profile != pin.content_profile
        or library.encoding != pin.encoding
    ):
        raise VideoError("VIDEO_LIBRARY_MISMATCH")


class VideoMediaPipeline:
    def __init__(
        self,
        authority: RenderAuthority,
        profiles: MediaProfileResolver,
        sources: VideoSourceResolver,
        validator: MediaValidator,
        *,
        library: LibraryResolver | None = None,
        generator: VideoGenerator | None = None,
        composer: LibraryComposer | None = None,
    ) -> None:
        self._authority, self._profiles, self._sources = authority, profiles, sources
        self._validator = validator
        self._library, self._generator, self._composer = library, generator, composer

    def prepare(self, attempt: RenderAttempt) -> PreparedVideoMedia:
        attempt = replace(attempt)
        self._authority.check(attempt, "prepare")
        pin = attempt.run.pin
        profile = self._profiles.resolve(attempt)
        if not isinstance(profile, MediaProfile):
            raise VideoError("VIDEO_PROFILE_UNAVAILABLE")
        profile = replace(profile)
        if (
            profile.content_profile != pin.content_profile
            or profile.encoding != pin.encoding
            or pin.strategy not in profile.strategies
        ):
            raise VideoError("VIDEO_PROFILE_UNAVAILABLE")
        operation_key = canonical_digest(
            {
                "schema": "BE2-08.MediaOperation/0.1-candidate",
                "pin": pin.digest(),
                "job_id": attempt.run.job_id,
                "attempt_id": attempt.run.attempt_id,
                "strategy": pin.strategy.value,
            }
        )
        if pin.strategy is Strategy.REVIEWED_LIBRARY:
            blob = self._resolve_library(attempt).blob
        else:
            if (pin.strategy is Strategy.GENERATE and self._generator is None) or (
                pin.strategy is Strategy.COMPOSE_LIBRARY and self._composer is None
            ):
                raise VideoError("VIDEO_STRATEGY_UNSUPPORTED")
            library = (
                self._resolve_library(attempt) if pin.strategy is Strategy.COMPOSE_LIBRARY else None
            )
            if library is not None:
                # Do not forward corrupt/oversized/unvalidated library input to
                # a composition provider, even if it might return a valid output.
                self._validate(attempt, library.blob, profile)
            self._authority.check(attempt, "source")
            source = self._sources.load(attempt)
            if (
                not isinstance(source, VideoSourceMaterial)
                or source.bundle != pin.bundle
                or source.pin_digest != pin.digest()
            ):
                raise VideoError("VIDEO_SOURCE_MISMATCH")
            source = replace(source)
            self._authority.check(attempt, "source_returned")
            self._authority.check(attempt, "generation")
            blob = self._generate(attempt, source, library, operation_key)
            self._authority.check(attempt, "generation_returned")
        report = self._validate(attempt, blob, profile)
        return PreparedVideoMedia(pin.digest(), operation_key, blob, report, pin.strategy)

    def _validate(
        self, attempt: RenderAttempt, blob: MediaBlob, profile: MediaProfile
    ) -> DecodedMedia:
        self._authority.check(attempt, "validation")
        blob = _admit_blob(blob, profile)
        report = self._validator.validate(blob, profile)
        # Even custom validators must return a complete matching report. Actual
        # decode trust remains an edge conformance obligation, not a boolean grant.
        if not isinstance(report, DecodedMedia):
            raise VideoError("VIDEO_MEDIA_INVALID")
        report = replace(report)
        validate_decoded(report, profile, blob.sha256)
        self._authority.check(attempt, "validation_returned")
        return report

    def _resolve_library(self, attempt: RenderAttempt) -> LibraryMedia:
        if self._library is None:
            raise VideoError("VIDEO_STRATEGY_UNSUPPORTED")
        self._authority.check(attempt, "library")
        library = self._library.resolve(attempt)
        _check_library(attempt, library)
        self._authority.check(attempt, "library_returned")
        return library

    def _generate(
        self,
        attempt: RenderAttempt,
        source: VideoSourceMaterial,
        library: LibraryMedia | None,
        operation_key: str,
    ) -> MediaBlob:
        if attempt.run.pin.strategy is Strategy.GENERATE and self._generator is not None:
            return self._generator.generate(attempt, source, operation_key)
        if library is not None and self._composer is not None:
            return self._composer.compose(attempt, source, library, operation_key)
        raise VideoError("VIDEO_STRATEGY_UNSUPPORTED")
