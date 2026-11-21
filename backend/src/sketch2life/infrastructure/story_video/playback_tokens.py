"""Signed playback tokens of the Parent video stream (FEAT-066 T-1c; SRS l.575-576, l.1676, l.1691).

TD-07 recommended an opaque random token stored hashed, which needs a table outside DDL-B1. This is
the recorded deviation: a stateless MAC token whose every use is rechecked by the stream route
against the current run, generation and owner (so cancel, delete, complete, ``video-unsuitable``,
closeout and a foreign account end playback at the next request, l.576, l.1691). The token is short
lived, names one generation of one run and one actor digest, and is only ever sent in a request
header: never in a URL, a log line, a stored row or an error body (l.1693).

Format: ``ptk1.<header>.<payload>.<mac>``, three strict base64url parts (no padding), at most 512
bytes. The header holds the algorithm and a key id (rotation: a previous key may still verify). The
MAC is HMAC-SHA-256 over ``ptk1.<header>.<payload>`` and is compared in constant time. Expiry is
only reported for an authentic token; every other failure is ``INVALID_TOKEN``.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import logging
import re
import secrets
import time
from collections.abc import Callable, Mapping
from uuid import UUID

from sketch2life.application.ports.story_video import PlaybackGrant, PlaybackTokenError
from sketch2life.infrastructure.config.settings import Settings

GRANT_PREFIX = "ptk1"
MAX_GRANT_LENGTH = 512
_ALGORITHM = "HS256"
_PART = re.compile(r"[A-Za-z0-9_-]+")
_ACTOR_DIGEST = re.compile(r"[0-9a-f]{32}")
_LOG = logging.getLogger(__name__)


def actor_digest(scope_ref: str) -> str:
    """The token's actor binding: a domain-separated digest of the owner scope reference."""

    return hashlib.sha256(f"{GRANT_PREFIX}-actor:{scope_ref}".encode()).hexdigest()[:32]


def _encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _decode(part: str) -> bytes:
    """Strict base64url: charset, canonical padding and canonical re-encoding or it is invalid."""

    if not _PART.fullmatch(part):
        raise PlaybackTokenError("INVALID_TOKEN")
    try:
        raw = base64.urlsafe_b64decode(part + "=" * (-len(part) % 4))
    except (binascii.Error, ValueError):
        raise PlaybackTokenError("INVALID_TOKEN") from None
    if _encode(raw) != part:
        raise PlaybackTokenError("INVALID_TOKEN")
    return raw


def _json(raw: bytes) -> dict[str, object]:
    try:
        value = json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        raise PlaybackTokenError("INVALID_TOKEN") from None
    if not isinstance(value, dict):
        raise PlaybackTokenError("INVALID_TOKEN")
    return value


class PlaybackTokenCodec:
    """Issues and verifies ``ptk1`` tokens. ``keys`` maps a key id to its secret bytes; tokens are
    signed with ``active_key_id`` and verify under any listed key (rotation)."""

    def __init__(
        self,
        *,
        active_key_id: str,
        keys: Mapping[str, bytes],
        ttl_seconds: int = 300,
        clock: Callable[[], float] = time.time,
    ) -> None:
        if active_key_id not in keys or not 1 <= ttl_seconds <= 900:
            raise ValueError("invalid playback token codec configuration")
        self._active = active_key_id
        self._keys = dict(keys)
        self._ttl = ttl_seconds
        self._clock = clock

    def actor_binding(self, scope_ref: str) -> str:
        return actor_digest(scope_ref)

    def _mac(self, key_id: str, signing_input: str) -> bytes:
        return hmac.new(self._keys[key_id], signing_input.encode("ascii"), hashlib.sha256).digest()

    def issue(self, *, run_id: str, generation_id: str, actor_digest: str) -> tuple[str, int]:
        expires_at = int(self._clock()) + self._ttl
        header = _encode(
            json.dumps({"alg": _ALGORITHM, "kid": self._active}, separators=(",", ":")).encode()
        )
        payload = _encode(
            json.dumps(
                {"a": actor_digest, "e": expires_at, "g": generation_id, "r": run_id},
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        )
        signing_input = f"{GRANT_PREFIX}.{header}.{payload}"
        mac = _encode(self._mac(self._active, signing_input))
        return f"{signing_input}.{mac}", expires_at

    def verify(self, token: str) -> PlaybackGrant:
        if not token or len(token) > MAX_GRANT_LENGTH or not token.isascii():
            raise PlaybackTokenError("INVALID_TOKEN")
        parts = token.split(".")
        if len(parts) != 4 or parts[0] != GRANT_PREFIX:
            raise PlaybackTokenError("INVALID_TOKEN")
        _prefix, header_part, payload_part, mac_part = parts
        header = _json(_decode(header_part))
        key_id = header.get("kid")
        if (
            set(header) != {"alg", "kid"}
            or header.get("alg") != _ALGORITHM
            or not isinstance(key_id, str)
            or key_id not in self._keys
        ):
            raise PlaybackTokenError("INVALID_TOKEN")
        expected = self._mac(key_id, f"{GRANT_PREFIX}.{header_part}.{payload_part}")
        if not hmac.compare_digest(_decode(mac_part), expected):
            raise PlaybackTokenError("INVALID_TOKEN")
        payload = _json(_decode(payload_part))
        run_id, generation_id = payload.get("r"), payload.get("g")
        digest, expires_at = payload.get("a"), payload.get("e")
        if (
            set(payload) != {"a", "e", "g", "r"}
            or not _is_canonical_uuid(run_id)
            or not _is_canonical_uuid(generation_id)
            or not isinstance(digest, str)
            or not _ACTOR_DIGEST.fullmatch(digest)
            or type(expires_at) is not int
        ):
            raise PlaybackTokenError("INVALID_TOKEN")
        assert isinstance(run_id, str) and isinstance(generation_id, str)
        if self._clock() >= expires_at:
            raise PlaybackTokenError("TOKEN_EXPIRED")
        return PlaybackGrant(run_id, generation_id, digest, expires_at)


def _is_canonical_uuid(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return str(UUID(value)) == value
    except ValueError:
        return False


def build_playback_codec(settings: Settings) -> PlaybackTokenCodec | None:
    """The codec for the settings, or ``None``: with no signing secret the token and stream routes
    answer 503 (fail closed at the route, never at startup). ``local`` and ``test`` get a
    per-process random key, so a token minted by another worker is ``INVALID_TOKEN`` there."""

    secret = settings.story_playback_signing_secret
    keys: dict[str, bytes] = {}
    if secret is not None:
        keys[settings.story_playback_key_id] = secret.get_secret_value().encode("utf-8")
        previous = settings.story_playback_previous_secret
        previous_id = settings.story_playback_previous_key_id
        if previous is not None and previous_id is not None:
            keys[previous_id] = previous.get_secret_value().encode("utf-8")
        active = settings.story_playback_key_id
    elif settings.env in {"local", "test"}:
        active = "ephemeral"
        keys[active] = secrets.token_bytes(48)
    else:
        _LOG.warning(
            "story_playback_signing_secret_missing setting=story_playback_signing_secret "
            "playback_routes=unavailable"
        )
        return None
    return PlaybackTokenCodec(
        active_key_id=active, keys=keys, ttl_seconds=settings.story_playback_token_ttl_seconds
    )


__all__ = [
    "MAX_GRANT_LENGTH",
    "GRANT_PREFIX",
    "PlaybackTokenCodec",
    "actor_digest",
    "build_playback_codec",
]
