"""HMAC worker capability issuer/verifier for BE2-01 Phase B batch B5 (ADR-0018 D6, plan Δ8/Δ14).

A capability is a stateless, attempt-bound token minted per publish right before enqueue:

    wcap.v1.<key_id>.<base64url(claims JSON)>.<base64url(HMAC-SHA256(key, signing input))>

The claims bind ``job_id``, ``attempt_id``, ``issued_at`` and ``expires_at`` (epoch milliseconds).
``verify`` returns a typed ``VerifiedCapability`` only for a well-formed token signed by a known
key and not yet expired on the verifier's clock; otherwise ``None``. The caller compares both
ids with the request. The token travels only inside the transient ``WorkerDispatchEnvelope``;
it is never persisted, and neither the token nor the key is put in an exception or log message.

Keys are supplied by the caller. The fixture TTL (40 s = start timeout 5 s + attempt timeout
30 s + slack 5 s, decision record §5.1) is PROPOSED. Production key provisioning and ``key_id``
rotation belong to INTG-02; this module only accepts several verification keys.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import re
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta

from sketch2life.application.ports.ai_jobs import ClockPort, VerifiedCapability

CAPABILITY_PREFIX = "wcap.v1"
# Log scrubbing (worker.py, B5-R02): anything that starts like a capability, up to whitespace or
# a quote/bracket/separator, including malformed or non-canonical representations.
CAPABILITY_PATTERN = re.compile(r"wcap\.v1\.[^\s'\"<>()\[\]{},;]*", re.IGNORECASE)
# Acceptance shape (B5-R02): the whole token, strict base64url segments, a 32-byte MAC.
_CAPABILITY_SHAPE = re.compile(r"wcap\.v1\.[a-z0-9_]{1,32}\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]{43}")
_B64URL = re.compile(r"[A-Za-z0-9_-]*")
FIXTURE_CAPABILITY_TTL = timedelta(seconds=40)
_KEY_ID = re.compile(r"^[a-z0-9_]{1,32}$")
_MIN_KEY_BYTES = 32
_MAX_CAPABILITY_CHARS = 2048
_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)


class CapabilityKey:
    """One HMAC signing/verification key. ``repr``/``str`` never show the key bytes."""

    __slots__ = ("_secret", "key_id")

    def __init__(self, key_id: str, secret: bytes) -> None:
        if not _KEY_ID.match(key_id):
            raise ValueError("key_id must match ^[a-z0-9_]{1,32}$")
        if not isinstance(secret, bytes) or len(secret) < _MIN_KEY_BYTES:
            raise ValueError("capability key must be at least 32 bytes")
        self.key_id = key_id
        self._secret = secret

    def sign(self, message: bytes) -> bytes:
        return hmac.new(self._secret, message, hashlib.sha256).digest()

    def __repr__(self) -> str:
        return f"CapabilityKey(key_id={self.key_id!r}, secret=<redacted>)"

    __str__ = __repr__


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _unb64(text: str) -> bytes:
    """Strict, canonical unpadded base64url (B5-R02): no other characters, no padding, no
    ignored trailing bits. Anything else raises ValueError."""

    if not _B64URL.fullmatch(text) or len(text) % 4 == 1:
        raise ValueError("not canonical base64url")
    decoded = base64.b64decode(text.translate(_TO_STANDARD) + "=" * (-len(text) % 4),
                               validate=True)
    if _b64(decoded) != text:
        raise ValueError("not canonical base64url")
    return decoded


_TO_STANDARD = str.maketrans("-_", "+/")


def _millis(value: datetime) -> int:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("capability times must be timezone-aware")
    return (value - _EPOCH) // timedelta(milliseconds=1)


def _at(millis: int) -> datetime:
    return _EPOCH + timedelta(milliseconds=millis)


class HmacCapabilityIssuer:
    """``WorkerCapabilityIssuer``: signs with the current key."""

    def __init__(self, key: CapabilityKey, *, ttl: timedelta = FIXTURE_CAPABILITY_TTL) -> None:
        if ttl <= timedelta(0):
            raise ValueError("capability ttl must be positive")
        self._key = key
        self._ttl = ttl

    def issue(self, job_id: str, attempt_id: str, now: datetime) -> str:
        issued = _millis(now)
        claims = {
            "a": attempt_id,
            "exp": issued + self._ttl // timedelta(milliseconds=1),
            "iat": issued,
            "j": job_id,
        }
        body = _b64(json.dumps(claims, sort_keys=True, separators=(",", ":")).encode("utf-8"))
        signing_input = f"{CAPABILITY_PREFIX}.{self._key.key_id}.{body}".encode("ascii")
        return f"{signing_input.decode('ascii')}.{_b64(self._key.sign(signing_input))}"

    def __repr__(self) -> str:
        return f"HmacCapabilityIssuer(key_id={self._key.key_id!r})"


class HmacCapabilityVerifier:
    """``WorkerCapabilityVerifier``: any configured key may verify (rotation overlap)."""

    def __init__(self, keys: Mapping[str, CapabilityKey] | CapabilityKey, clock: ClockPort) -> None:
        if isinstance(keys, CapabilityKey):
            keys = {keys.key_id: keys}
        if not keys or any(key_id != key.key_id for key_id, key in keys.items()):
            raise ValueError("verification keys must be indexed by their key_id")
        self._keys = dict(keys)
        self._clock = clock

    def verify(self, capability: str) -> VerifiedCapability | None:
        if not isinstance(capability, str) or len(capability) > _MAX_CAPABILITY_CHARS:
            return None
        if not _CAPABILITY_SHAPE.fullmatch(capability):
            return None  # whole-token shape first: no stray characters anywhere (B5-R02)
        parts = capability.split(".")
        if len(parts) != 5 or ".".join(parts[:2]) != CAPABILITY_PREFIX:
            return None
        _, _, key_id, body, signature = parts
        key = self._keys.get(key_id)
        if key is None:
            return None
        signing_input = f"{CAPABILITY_PREFIX}.{key_id}.{body}".encode("ascii")
        try:
            presented = _unb64(signature)
        except (binascii.Error, ValueError):
            return None
        # Authenticate before parsing anything the caller supplied.
        if not hmac.compare_digest(presented, key.sign(signing_input)):
            return None
        try:
            claims = json.loads(_unb64(body))
        except (binascii.Error, ValueError, UnicodeDecodeError):
            return None
        if not isinstance(claims, dict) or set(claims) != {"a", "exp", "iat", "j"}:
            return None
        job_id, attempt_id = claims["j"], claims["a"]
        issued, expires = claims["iat"], claims["exp"]
        if not (
            isinstance(job_id, str) and job_id
            and isinstance(attempt_id, str) and attempt_id
            and type(issued) is int and type(expires) is int and issued < expires
        ):
            return None
        if _millis(self._clock.now()) >= expires:
            return None
        return VerifiedCapability(job_id, attempt_id, _at(issued), _at(expires), key_id)

    def __repr__(self) -> str:
        return f"HmacCapabilityVerifier(key_ids={sorted(self._keys)!r})"


__all__ = [
    "FIXTURE_CAPABILITY_TTL",
    "CAPABILITY_PATTERN",
    "CAPABILITY_PREFIX",
    "CapabilityKey",
    "HmacCapabilityIssuer",
    "HmacCapabilityVerifier",
]
