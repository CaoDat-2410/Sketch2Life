"""Provider-neutral identity verification boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class VerifiedPrincipal:
    """Identity claims accepted by the application after provider verification."""

    subject: str
    issuer: str
    roles: frozenset[str]
    token_id: str | None = None


class IdentityTokenVerifier(Protocol):
    """Implemented by infrastructure, initially with Firebase Authentication."""

    async def verify(self, encoded_token: str) -> VerifiedPrincipal:
        """Verify signature, issuer, audience, expiry, and approved role claims."""
        ...
