"""Authored tiny animation/full-frame fixture adapter, NOT a production decoder.

Rights: project-authored synthetic solid RGB frames, no external/user/child media.
Only Pillow already declared by the backend; no executable/model/provider calls.
"""

import hashlib
from io import BytesIO

from PIL import Image, ImageSequence, UnidentifiedImageError

from sketch2life.domain.knowledge_video.media import DecodedMedia, MediaBlob, MediaProfile
from sketch2life.domain.knowledge_video.model import ExactRef, Strategy, VideoError

RIGHTS = {
    "origin": "project_authored_synthetic_rgb_frames",
    "purpose": "BE2_08_decoder_conformance_fixture_only",
    "external_media": False,
    "personal_data": False,
    "production_profile": False,
}
ENCODING = ExactRef("fixture.gif.encoding", 1, hashlib.sha256(b"fixture-gif-v1").hexdigest())
CONTENT = ExactRef("fixture.animation", 1, hashlib.sha256(b"fixture-animation-v1").hexdigest())


def animation() -> bytes:
    """Two authored8x8 frames, red then blue,250ms each; no external files."""
    output = BytesIO()
    first = Image.new("RGB", (8, 8), (255, 0, 0))
    second = Image.new("RGB", (8, 8), (0, 0, 255))
    first.save(
        output,
        format="GIF",
        save_all=True,
        append_images=[second],
        duration=[250, 250],
        loop=0,
        optimize=False,
    )
    return output.getvalue()


def blob(payload: bytes) -> MediaBlob:
    return MediaBlob(payload, hashlib.sha256(payload).hexdigest())


def profile() -> MediaProfile:
    # Deliberately narrow fixture-only bounds, NEVER product defaults.
    return MediaProfile(
        CONTENT, ENCODING, tuple(Strategy), ("gif",), ("gif",), ((8, 8),), 500, 500, 4096, 2, (), 0
    )


class PillowFixtureDecoder:
    """Fully load each frame of the tiny synthetic GIF, not a metadata probe.

    No claim of video/audio codec coverage, sandboxing, production resource/deadline
    limits or arbitrary untrusted-input safety. ONLY used under fixture byte bounds.
    """

    def __init__(self) -> None:
        self.loaded_frames: list[tuple[int, int, int]] = []

    def decode(self, media: MediaBlob, encoding: ExactRef) -> DecodedMedia:
        if encoding != ENCODING:
            raise VideoError("VIDEO_FIXTURE_ENCODING_UNSUPPORTED")
        try:
            with Image.open(BytesIO(media.payload)) as image:
                if image.format != "GIF":
                    raise VideoError("VIDEO_FIXTURE_ENCODING_UNSUPPORTED")
                dimensions = image.size
                duration, count = 0, 0
                for frame in ImageSequence.Iterator(image):
                    frame.load()
                    self.loaded_frames.append(frame.convert("RGB").getpixel((0, 0)))
                    duration += int(frame.info.get("duration", 0))
                    count += 1
        except (OSError, ValueError, UnidentifiedImageError):
            raise VideoError("VIDEO_FIXTURE_DECODE_FAILED") from None
        return DecodedMedia(media.sha256, "gif", "gif", *dimensions, duration, count, (), True)
