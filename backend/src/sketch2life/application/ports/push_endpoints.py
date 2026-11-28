"""Ports for actor-bound push registration and endpoint protection (T-8b)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.domain.push_endpoints import PushEndpointReceipt, PushEndpointRecord


class PushAdapterUnavailable(RuntimeError):
    """A required proof, key, or fingerprint adapter is not configured."""


class PushEndpointStoreUnavailable(RuntimeError):
    """The endpoint store could not complete a safe read or transaction."""


class InvalidPushRegistrationProof(ValueError):
    """The proof is invalid, stale, or not bound to the requested actor/provider/consent."""


class ConcurrentPushEndpointWrite(RuntimeError):
    """A unique endpoint or receipt insert was won by a concurrent command."""


class PushEndpointScopeNotFound(LookupError):
    """No current active Parent identity exists for the verified principal."""


@dataclass(frozen=True, slots=True)
class VerifiedPushRegistration:
    endpoint: bytes
    actor_subject: str
    provider_kind: str
    consent_granted: bool
    verified_at: datetime
    expires_at: datetime


class PushRegistrationProofVerifier(Protocol):
    def verify(
        self, *, proof: str, actor_subject: str, provider_kind: str
    ) -> VerifiedPushRegistration:
        """Validate fresh device proof and return its bound endpoint bytes."""
        ...


class PushEndpointEncryptor(Protocol):
    def encrypt(self, *, plaintext: bytes, associated_data: bytes) -> bytes:
        """Return an authenticated ciphertext envelope; never return plaintext fallback."""
        ...


class PushEndpointFingerprinter(Protocol):
    def fingerprint(self, *, provider_kind: str, endpoint: bytes) -> str:
        """Return lowercase HMAC-SHA-256 for provider and canonical endpoint bytes."""
        ...


class PushReceiptFingerprinter(Protocol):
    def fingerprint(self, *, operation_scope: str, canonical_request: bytes) -> str:
        """Return HMAC-SHA-256 using a key separate from endpoint fingerprinting."""
        ...


class PushEndpointStore(Protocol):
    def authorize_parent(self, principal: VerifiedPrincipal) -> str:
        """Return the current recipient account or raise the uniform scoped 404."""
        ...

    def get_receipt(
        self, *, principal_ref: str, operation_scope: str, idempotency_key: str
    ) -> PushEndpointReceipt | None:
        ...

    def find_active(
        self, *, provider_kind: str, endpoint_fingerprint: str
    ) -> PushEndpointRecord | None:
        ...

    def find_owned(
        self, *, endpoint_id: str, recipient_account_id: str, for_update: bool
    ) -> PushEndpointRecord | None:
        ...

    def insert_endpoint(self, endpoint: PushEndpointRecord) -> None:
        ...

    def update_endpoint(self, endpoint: PushEndpointRecord) -> None:
        ...

    def add_receipt(
        self,
        *,
        principal_ref: str,
        operation_scope: str,
        idempotency_key: str,
        request_fingerprint: str,
        response_json: dict[str, object],
    ) -> None:
        ...

    def commit(self) -> None:
        ...

    def rollback(self) -> None:
        ...


__all__ = [
    "ConcurrentPushEndpointWrite",
    "InvalidPushRegistrationProof",
    "PushAdapterUnavailable",
    "PushEndpointEncryptor",
    "PushEndpointFingerprinter",
    "PushEndpointStore",
    "PushEndpointStoreUnavailable",
    "PushEndpointScopeNotFound",
    "PushReceiptFingerprinter",
    "PushRegistrationProofVerifier",
    "VerifiedPushRegistration",
]
