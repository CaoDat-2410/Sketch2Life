"""Ports for encrypted profile support needs (T-12c).

The cipher and the receipt MAC sit behind one port so that no repository and no route ever holds
a key. The production composition has no implementation until the owner approves a key source
(gate O-SEED-KEY); the routes then answer 503 ``SUPPORT_NEEDS_UNAVAILABLE``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.domain.support_needs import SupportNeedsFamily, SupportNeedsPayload


class SupportNeedsUnavailable(Exception):  # noqa: N818 - a condition, named like the 503 code
    """No key, an unknown key id or version, or a ciphertext that does not authenticate.

    The message never names a key, a record or a value.
    """


@dataclass(frozen=True, slots=True)
class SealedSupportNeeds:
    """What is stored: the opaque ciphertext (tag included), its nonce and its key label."""

    ciphertext: bytes
    nonce: bytes
    key_id: str
    algorithm_version: int


class SupportNeedsCrypto(Protocol):
    @property
    def fingerprint_key_id(self) -> str: ...

    def seal(
        self,
        *,
        family: SupportNeedsFamily,
        tenant: str,
        profile_id: str,
        revision: int,
        payload: SupportNeedsPayload,
    ) -> SealedSupportNeeds: ...

    def open(
        self,
        *,
        family: SupportNeedsFamily,
        tenant: str,
        profile_id: str,
        revision: int,
        sealed: SealedSupportNeeds,
    ) -> SupportNeedsPayload: ...

    def fingerprint(
        self,
        *,
        family: SupportNeedsFamily,
        tenant: str,
        profile_id: str,
        principal: str,
        expected_revision: int,
        payload: SupportNeedsPayload,
        key_id: str | None = None,
    ) -> bytes:
        """A keyed 32-byte MAC of the request (never an unkeyed digest of the values).

        ``key_id`` names the MAC key of a stored receipt, so an identical retry still matches
        after a rotation; absent, the current key is used. An unknown id fails closed.
        """
        ...


class ParentSupportNeedsRepository(Protocol):
    def assert_profile_owned(self, *, principal: VerifiedPrincipal, profile_id: UUID) -> None: ...

    def get_support_needs(
        self, *, principal: VerifiedPrincipal, profile_id: UUID, crypto: SupportNeedsCrypto
    ) -> dict[str, object]: ...

    def put_support_needs(
        self,
        *,
        principal: VerifiedPrincipal,
        profile_id: UUID,
        expected_revision: int,
        payload: SupportNeedsPayload,
        idempotency_key: str,
        crypto: SupportNeedsCrypto,
    ) -> dict[str, object]: ...


__all__ = [
    "ParentSupportNeedsRepository",
    "SealedSupportNeeds",
    "SupportNeedsCrypto",
    "SupportNeedsUnavailable",
]
