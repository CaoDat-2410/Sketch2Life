"""Actual full-frame synthetic GIF fixture only, NOT selected runtime video decode."""

from dataclasses import replace
from io import BytesIO

import pytest
from PIL import Image

from sketch2life.application.knowledge_video_media import CheckedMediaValidator
from sketch2life.domain.knowledge_video.model import ExactRef, VideoError
from tests.knowledge_video_decoder_fixtures import (
    RIGHTS,
    PillowFixtureDecoder,
    animation,
    blob,
    profile,
)


def test_real_fixture_bytes_load_all_frames_with_recorded_synthetic_rights():
    decoder = PillowFixtureDecoder()
    report = CheckedMediaValidator(decoder).validate(blob(animation()), profile())
    assert report.complete and report.decoded_frames == 2 and report.duration_ms == 500
    assert decoder.loaded_frames == [(255, 0, 0), (0, 0, 255)]
    assert RIGHTS["external_media"] is RIGHTS["personal_data"] is False
    assert RIGHTS["production_profile"] is False


@pytest.mark.parametrize(
    "payload",
    [b"not-media", animation()[:20], animation()[: len(animation()) // 2]],
    ids=["not-media", "header-only", "truncated-frame"],
)
def test_corrupt_or_truncated_fixture_not_accepted_as_complete(payload):
    with pytest.raises(VideoError):
        CheckedMediaValidator(PillowFixtureDecoder()).validate(blob(payload), profile())


def test_metadata_header_alone_not_full_decode():
    with pytest.raises(VideoError):
        CheckedMediaValidator(PillowFixtureDecoder()).validate(blob(animation()[:13]), profile())


@pytest.mark.parametrize(
    "change",
    [
        {"video_codecs": ("h264",)},
        {"dimensions": ((16, 16),)},
        {"min_duration_ms": 1000, "max_duration_ms": 1000},
        {"min_decoded_frames": 3},
    ],
)
def test_full_decoded_fixture_still_must_match_exact_profile(change):
    decoder = PillowFixtureDecoder()
    with pytest.raises(VideoError, match="VIDEO_MEDIA_PROFILE_MISMATCH"):
        CheckedMediaValidator(decoder).validate(blob(animation()), replace(profile(), **change))
    assert len(decoder.loaded_frames) == 2


def test_wrong_hash_fails_before_any_frame_decode():
    decoder = PillowFixtureDecoder()
    with pytest.raises(VideoError, match="VIDEO_MEDIA_HASH_MISMATCH"):
        CheckedMediaValidator(decoder).validate(
            replace(blob(animation()), sha256="f" * 64), profile()
        )
    assert not decoder.loaded_frames


def test_oversized_fixture_bounded_before_any_frame_decode():
    decoder = PillowFixtureDecoder()
    with pytest.raises(VideoError, match="VIDEO_MEDIA_TOO_LARGE"):
        CheckedMediaValidator(decoder).validate(blob(animation()), replace(profile(), max_bytes=8))
    assert not decoder.loaded_frames


def test_wrong_container_cannot_use_gif_fixture_encoding():
    output = BytesIO()
    Image.new("RGB", (8, 8), "red").save(output, format="PNG")
    with pytest.raises(VideoError):
        CheckedMediaValidator(PillowFixtureDecoder()).validate(blob(output.getvalue()), profile())


def test_unknown_encoding_is_not_silently_replaced_by_fixture_profile():
    with pytest.raises(VideoError):
        CheckedMediaValidator(PillowFixtureDecoder()).validate(
            blob(animation()), replace(profile(), encoding=ExactRef("other", 1, "a" * 64))
        )
