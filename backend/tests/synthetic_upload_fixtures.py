"""Tiny deterministic synthetic upload bytes for T-2z tests (stdlib only, built in memory).

No real file, photo or child media is used. Every fixture is a few dozen bytes and its SHA-256 is
the only thing the local test scanner allowlist knows about it.
"""

from __future__ import annotations

import hashlib
import struct
import zlib
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SyntheticUpload:
    name: str
    media_type: str
    data: bytes

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.data).hexdigest()


def _png_chunk(kind: bytes, payload: bytes) -> bytes:
    body = kind + payload
    return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)


def synthetic_png() -> bytes:
    """A valid 1x1 RGB PNG."""
    header = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    pixels = zlib.compress(b"\x00\x10\x20\x30")
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", header)
        + _png_chunk(b"IDAT", pixels)
        + _png_chunk(b"IEND", b"")
    )


def synthetic_jpeg_prefix() -> bytes:
    """JPEG signature plus filler: enough for a signature check, not a decodable image."""
    return b"\xff\xd8\xff\xe0" + b"synthetic-jpeg-t2z"


def synthetic_pdf() -> bytes:
    return b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF\n"


def synthetic_wav() -> bytes:
    """A valid 8-bit mono WAV with four samples."""
    samples = b"\x80\x80\x80\x80"
    fmt = struct.pack("<HHIIHH", 1, 1, 8000, 8000, 1, 8)
    chunks = b"fmt " + struct.pack("<I", len(fmt)) + fmt
    chunks += b"data" + struct.pack("<I", len(samples)) + samples
    return b"RIFF" + struct.pack("<I", 4 + len(chunks)) + b"WAVE" + chunks


def synthetic_webp_prefix() -> bytes:
    return b"RIFF" + struct.pack("<I", 20) + b"WEBP" + b"VP8 " + b"synthetic-t2z"


def synthetic_zip_prefix() -> bytes:
    """A ZIP local-file-header signature plus filler (stands in for a DOCX or PPTX container)."""
    return b"PK\x03\x04" + b"synthetic-zip-t2z"


def synthetic_uploads() -> tuple[SyntheticUpload, ...]:
    return (
        SyntheticUpload("png", "image/png", synthetic_png()),
        SyntheticUpload("jpeg", "image/jpeg", synthetic_jpeg_prefix()),
        SyntheticUpload("pdf", "application/pdf", synthetic_pdf()),
        SyntheticUpload("wav", "audio/wav", synthetic_wav()),
    )
