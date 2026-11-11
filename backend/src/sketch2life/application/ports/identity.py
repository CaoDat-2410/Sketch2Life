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
    email: str | None = None
    display_name: str | None = None
    email_verified: bool = False


@dataclass(frozen=True, slots=True)
class ProvisionedIdentity:
    """Provider identity returned internally after server-side Firebase creation."""

    subject: str
    issuer: str


@dataclass(frozen=True, slots=True)
class IdentityAccountProfile:
    """Minimal Firebase Auth profile fields for an authorized account-list response."""

    subject: str
    email: str | None
    display_name: str | None


class IdentityTokenVerifier(Protocol):
    """Implemented by infrastructure, initially with Firebase Authentication."""

    async def verify(self, encoded_token: str) -> VerifiedPrincipal:
        """Verify signature, issuer, audience, expiry, and approved role claims."""
        ...


class IdentityAccountConflict(RuntimeError):
    """The requested identity cannot be created under the generic public contract."""


class IdentityAccountProvisioningUnavailable(RuntimeError):
    """The configured identity provider could not complete account provisioning."""


class IdentityAccountProvisioner(Protocol):
    """Create an identity at the configured authentication provider."""

    def create_password_account(self, *, email: str, password: str) -> ProvisionedIdentity:
        """Create an unverified Firebase identity; app role assignment is separate."""
        ...

    def create_account(
        self, *, email: str, display_name: str | None = None
    ) -> ProvisionedIdentity:
        """Create an identity without a password for recovery-based account activation."""
        ...

    def delete_account(self, subject: str) -> None:
        """Delete a provider identity when its database provisioning transaction fails."""
        ...

    def set_account_disabled(self, subject: str, disabled: bool) -> None:
        """Synchronize account availability with the identity provider."""
        ...

    def get_account_profiles(self, subjects: list[str]) -> dict[str, IdentityAccountProfile]:
        """Read minimal provider profile fields for a bounded account-list page."""
        ...

    def find_account_by_email(self, email: str) -> ProvisionedIdentity | None:
        """Resolve an email to its Firebase UID for one-time bootstrap only."""
        ...
