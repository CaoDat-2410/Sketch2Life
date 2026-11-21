"""Drawing normalization for the Parent run asset route (SRS l.983, l.1942, l.1943; T-2b).

The uploaded original is never resized or rewritten. The derived asset is an RGB PNG with the EXIF
orientation applied, scaled down (never up) to at most ``DERIVED_MAX_PIXELS``, and at most
``DERIVED_MAX_BYTES`` encoded (the database limit and the Modal worker contract).

Memory and time are bounded before any pixel is decoded: the encoded size is checked by the caller
(at most 20 MiB), the dimensions are read lazily from the header, and more than
``MAX_SOURCE_PIXELS`` (40 megapixels, l.983) is refused with ``IMAGE_DIMENSIONS_EXCEEDED``.
The limit is enforced by that check and by Pillow's own decompression-bomb error for far larger
declared sizes; this module never writes ``Image.MAX_IMAGE_PIXELS``, a process global that other
requests share.

Decoding runs in the API process. SRS l.1942 asks for an isolated, resource-limited worker (a
proposal for the synthetic demo); that hardening is parked (T-2b-DEC-8).
"""

from __future__ import annotations

import hashlib
import io
import math
import warnings
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Final

from PIL import Image, ImageOps, UnidentifiedImageError

MAX_SOURCE_PIXELS: Final = 40_000_000
DERIVED_MAX_PIXELS: Final = 2_000_000
DERIVED_MAX_BYTES: Final = 5_000_000
# Pixel budgets tried in order: the normal limit, then three reductions when the PNG is too large.
PIXEL_LADDER: Final = (DERIVED_MAX_PIXELS, 1_200_000, 700_000, 400_000)
ACCEPTED_FORMATS: Final = frozenset({"JPEG", "PNG", "WEBP"})
TRANSFORM_KIND: Final = "NORMALIZE_DRAWING_IMAGE"
TRANSFORM_VERSION: Final = "PILLOW_RGB_PNG_V2"
DERIVED_MEDIA_TYPE: Final = "image/png"
_FORMAT_TO_MEDIA_TYPE: Final = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}


class DrawingNormalizationError(RuntimeError):
    """A public outcome: status and code for the route envelope (no internal detail)."""

    def __init__(self, status_code: int, code: str) -> None:
        self.status_code = status_code
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class NormalizedDrawing:
    png_bytes: bytes
    sha256: str
    width: int
    height: int
    source_width: int
    source_height: int

    @property
    def size_bytes(self) -> int:
        return len(self.png_bytes)


@contextmanager
def _bomb_guard() -> Iterator[None]:
    """Turn Pillow's bomb warning into the bomb error for this call only (no global state)."""
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        try:
            yield
        except Image.DecompressionBombWarning:
            raise _dimensions_exceeded() from None


def _dimensions_exceeded() -> DrawingNormalizationError:
    return DrawingNormalizationError(422, "IMAGE_DIMENSIONS_EXCEEDED")


def _content_mismatch() -> DrawingNormalizationError:
    return DrawingNormalizationError(422, "UPLOAD_CONTENT_MISMATCH")


def check_source_dimensions(width: int, height: int) -> None:
    """Refuse an image whose declared size is not a positive area of at most 40 megapixels."""
    if width < 1 or height < 1:
        raise _content_mismatch()
    if width * height > MAX_SOURCE_PIXELS:
        raise _dimensions_exceeded()


def fit_within(width: int, height: int, max_pixels: int) -> tuple[int, int]:
    """Largest size with the same aspect ratio and at most ``max_pixels``; never larger."""
    if width * height <= max_pixels:
        return width, height
    factor = math.sqrt(max_pixels / (width * height))
    new_width = max(1, int(width * factor))
    new_height = max(1, int(height * factor))
    while new_width * new_height > max_pixels and (new_width > 1 or new_height > 1):
        if new_width >= new_height and new_width > 1:
            new_width -= 1
        else:
            new_height -= 1
    return new_width, new_height


def _flatten_to_rgb(image: Image.Image) -> Image.Image:
    """RGB with transparency composited on white (a drawing, not a cut-out)."""
    has_alpha = image.mode in {"RGBA", "LA", "PA"} or (
        image.mode == "P" and "transparency" in image.info
    )
    if has_alpha:
        rgba = image.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.getchannel("A"))
        return background
    return image.convert("RGB")


def _encode(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def normalize_drawing(source: bytes, *, declared_media_type: str) -> NormalizedDrawing:
    """Return the derived PNG of ``source`` or raise ``DrawingNormalizationError``.

    Order: header (lazy, no decode) -> format and dimension checks -> decode -> orientation ->
    RGB -> scale down -> encode, with the size ladder when the PNG is too large.
    """
    try:
        with _bomb_guard(), Image.open(io.BytesIO(source)) as probe:
            image_format = probe.format
            source_width, source_height = probe.size
    except Image.DecompressionBombError:
        raise _dimensions_exceeded() from None
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError):
        raise _content_mismatch() from None
    if image_format not in ACCEPTED_FORMATS:
        raise _content_mismatch()
    if _FORMAT_TO_MEDIA_TYPE[str(image_format)] != declared_media_type:
        raise _content_mismatch()
    check_source_dimensions(source_width, source_height)

    try:
        with _bomb_guard(), Image.open(io.BytesIO(source)) as opened:
            opened.load()
            oriented = ImageOps.exif_transpose(opened)
            flattened = _flatten_to_rgb(oriented)
    except Image.DecompressionBombError:
        raise _dimensions_exceeded() from None
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError):
        raise _content_mismatch() from None

    try:
        for budget in PIXEL_LADDER:
            width, height = fit_within(flattened.width, flattened.height, budget)
            candidate = (
                flattened
                if (width, height) == flattened.size
                else flattened.resize((width, height), Image.Resampling.LANCZOS)
            )
            encoded = _encode(candidate)
            if len(encoded) <= DERIVED_MAX_BYTES:
                return NormalizedDrawing(
                    png_bytes=encoded,
                    sha256=hashlib.sha256(encoded).hexdigest(),
                    width=width,
                    height=height,
                    source_width=source_width,
                    source_height=source_height,
                )
    except (OSError, ValueError):
        raise _content_mismatch() from None
    # The decoded image cannot be encoded within the normalized byte limit: documented as the
    # same code, because the cause is the decoded size of the image (T2B-D5).
    raise _dimensions_exceeded()


__all__ = [
    "ACCEPTED_FORMATS",
    "DERIVED_MAX_BYTES",
    "DERIVED_MAX_PIXELS",
    "DERIVED_MEDIA_TYPE",
    "MAX_SOURCE_PIXELS",
    "PIXEL_LADDER",
    "TRANSFORM_KIND",
    "TRANSFORM_VERSION",
    "DrawingNormalizationError",
    "NormalizedDrawing",
    "check_source_dimensions",
    "fit_within",
    "normalize_drawing",
]
