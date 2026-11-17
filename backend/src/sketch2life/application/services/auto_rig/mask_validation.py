"""Pixel admission for original-derived masks at the application boundary."""

from io import BytesIO

from PIL import Image


def subject_mask_rejection(source_bytes: bytes, mask_bytes: bytes) -> str | None:
    """Return a safe reason, using the renderer's exact foreground/area rules."""
    if len(mask_bytes) > 5_000_000 or not mask_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "MASK_ENCODING_INVALID"
    try:
        with Image.open(BytesIO(source_bytes)) as source:
            source_size = source.size
        with Image.open(BytesIO(mask_bytes)) as mask:
            width, height = mask.size
            if (
                mask.format != "PNG"
                or getattr(mask, "n_frames", 1) != 1
                or mask.size != source_size
                or width < 2
                or height < 2
                or width * height > 4_000_000
            ):
                return "MASK_DIMENSIONS_INVALID"
            # Binary and opaque grayscale are the worker's usual encoding. Histogram
            # admission avoids allocating RGBA tuples for millions of source pixels.
            if mask.mode in {"1", "L"} and "transparency" not in mask.info:
                count = sum(mask.convert("L").histogram()[9:])
            else:
                pixels = memoryview(mask.convert("RGBA").tobytes())
                count = sum(
                    1
                    for red, green, blue, alpha in zip(
                        pixels[0::4], pixels[1::4], pixels[2::4], pixels[3::4], strict=True
                    )
                    if ((red + green + blue + 1) // 3) * alpha / 255 > 8
                )
            area = count / (width * height)
            if not 0.001 <= area <= 0.75:
                return "MASK_AREA_INVALID"
    except (OSError, ValueError, Image.DecompressionBombError):
        return "MASK_ENCODING_INVALID"
    return None
