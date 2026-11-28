"""Synthetic proof and key adapters for local/test verification only.

These adapters accept no live push-provider connection, use no production credentials, and are
guarded by ``SKETCH2LIFE_ENV``. The fake envelope is intentionally not cryptography and must never
be configured in staging or production.
"""

from __future__ import annotations

import hashlib
import hmac
import os
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from secrets import token_hex

from sketch2life.application.ports.push_endpoints import (
    InvalidPushRegistrationProof,
    VerifiedPushRegistration,
)


def _require_local_test() -> None:
    if os.environ.get("SKETCH2LIFE_ENV", "").lower() not in {"local", "test"}:
        raise RuntimeError("synthetic push adapters are restricted to local/test environments")


class SyntheticRegistrationProofVerifier:
    """In-memory actor/provider/consent-bound proofs with synthetic endpoint bytes."""

    test_only = True

    def __init__(self, clock: Callable[[], datetime] | None = None) -> None:
        _require_local_test()
        self._proofs: dict[str, VerifiedPushRegistration] = {}
        self._clock = clock or (lambda: datetime.now(UTC))

    def issue(
        self,
        *,
        actor_subject: str,
        provider_kind: str = "WEB_PUSH",
        endpoint: bytes | None = None,
        consent_granted: bool = True,
        now: datetime | None = None,
        lifetime: timedelta = timedelta(minutes=2),
    ) -> str:
        _require_local_test()
        issued_at = now or self._clock()
        proof = f"synthetic:{token_hex(16)}"
        self._proofs[proof] = VerifiedPushRegistration(
            endpoint=endpoint or f"https://push.invalid/{token_hex(12)}".encode("ascii"),
            actor_subject=actor_subject,
            provider_kind=provider_kind,
            consent_granted=consent_granted,
            verified_at=issued_at,
            expires_at=issued_at + lifetime,
        )
        return proof

    def verify(
        self, *, proof: str, actor_subject: str, provider_kind: str
    ) -> VerifiedPushRegistration:
        _require_local_test()
        result = self._proofs.get(proof)
        if (
            result is None
            or result.actor_subject != actor_subject
            or result.provider_kind != provider_kind
            or not result.consent_granted
            or result.expires_at <= self._clock()
        ):
            raise InvalidPushRegistrationProof("synthetic proof rejected") from None
        return result


class SyntheticEndpointFingerprinter:
    """HMAC-shaped endpoint fingerprint for tests; the key is synthetic and process-local."""

    test_only = True

    def __init__(self, key: bytes) -> None:
        _require_local_test()
        if len(key) < 32:
            raise ValueError("synthetic fingerprint key must contain at least 32 bytes")
        self._key = bytes(key)

    def fingerprint(self, *, provider_kind: str, endpoint: bytes) -> str:
        _require_local_test()
        message = (
            b"sketch2life:push-endpoint:v1\0"
            + provider_kind.encode("ascii")
            + b"\0"
            + len(endpoint).to_bytes(8, "big")
            + endpoint
        )
        return hmac.new(self._key, message, hashlib.sha256).hexdigest()


class SyntheticReceiptFingerprinter:
    """Separate test HMAC domain for receipt keys; never a plain request digest."""

    test_only = True

    def __init__(self, key: bytes) -> None:
        _require_local_test()
        if len(key) < 32:
            raise ValueError("synthetic receipt key must contain at least 32 bytes")
        self._key = bytes(key)

    def fingerprint(self, *, operation_scope: str, canonical_request: bytes) -> str:
        _require_local_test()
        message = (
            b"sketch2life:push-command-receipt:v1\0"
            + operation_scope.encode("ascii")
            + b"\0"
            + len(canonical_request).to_bytes(8, "big")
            + canonical_request
        )
        return hmac.new(self._key, message, hashlib.sha256).hexdigest()


class SyntheticEndpointEncryptor:
    """Non-reversible, non-cryptographic test envelope that verifies AAD binding."""

    test_only = True

    def __init__(self, key: bytes) -> None:
        _require_local_test()
        if len(key) < 32:
            raise ValueError("synthetic encryption key must contain at least 32 bytes")
        self._key = bytes(key)
        self._aad_digests: dict[bytes, bytes] = {}

    def encrypt(self, *, plaintext: bytes, associated_data: bytes) -> bytes:
        _require_local_test()
        nonce = os.urandom(16)
        tag = hmac.new(
            self._key,
            b"synthetic-aead-v1\0" + associated_data + b"\0" + nonce + plaintext,
            hashlib.sha256,
        ).digest()
        envelope = b"TEST-ONLY-AEAD-V1\0" + nonce + tag
        self._aad_digests[envelope] = hashlib.sha256(associated_data).digest()
        return envelope

    def matches_context(self, ciphertext: bytes, associated_data: bytes) -> bool:
        _require_local_test()
        return self._aad_digests.get(ciphertext) == hashlib.sha256(associated_data).digest()


__all__ = [
    "SyntheticEndpointEncryptor",
    "SyntheticEndpointFingerprinter",
    "SyntheticReceiptFingerprinter",
    "SyntheticRegistrationProofVerifier",
]
