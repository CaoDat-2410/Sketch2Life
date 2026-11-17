"""Shared deterministic equality fence for trusted BE1-to-BE2 context facts."""

from __future__ import annotations

import json
from collections.abc import Mapping
from hashlib import sha256
from typing import cast

CONTEXT_REVISION_DOMAIN = b"sketch2life/context-revision/v1\n"
CONTEXT_REVISION_SCHEMA_VERSION = "be1-fact-context-v2"
CONTEXT_REVISION_MAX = 0x7FFFFFFF


def _context_digest_bytes(payload: Mapping[str, object]) -> bytes:
    """Hash strict scalar canonical JSON with the stable equality-fence domain separator."""

    if not isinstance(payload, Mapping):
        raise TypeError("context revision payload must be a mapping")

    normalized: dict[str, str | int | bool | None] = {}
    for key, value in payload.items():
        if not isinstance(key, str):
            raise TypeError("context revision keys must be strings")
        if value is not None and type(value) not in (str, int, bool):
            raise TypeError("context revision values must be str, int, bool, or None")
        normalized[key] = cast(str | int | bool | None, value)

    canonical = json.dumps(
        normalized,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(CONTEXT_REVISION_DOMAIN + canonical).digest()


def context_digest(payload: Mapping[str, object]) -> str:
    """Return the versioned full SHA-256 digest for one canonical fact context.

    The payload's ``schema_version`` identifies the fact shape. This value is an opaque,
    equality-only freshness token, not a signature, credential or authorization decision.
    """
    return f"sha256:{_context_digest_bytes(payload).hex()}"


def context_revision(payload: Mapping[str, object]) -> int:
    """Return the compatibility positive signed-31-bit revision from the same full digest."""
    first_31 = int.from_bytes(_context_digest_bytes(payload)[:4], "big")
    revision = first_31 & CONTEXT_REVISION_MAX
    return revision or 1


__all__ = [
    "CONTEXT_REVISION_DOMAIN",
    "CONTEXT_REVISION_MAX",
    "CONTEXT_REVISION_SCHEMA_VERSION",
    "context_digest",
    "context_revision",
]
