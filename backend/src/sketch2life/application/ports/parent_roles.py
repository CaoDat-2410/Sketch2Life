"""Application boundary for checking the verified principal's Parent role."""

from __future__ import annotations

from typing import Protocol

from sketch2life.application.ports.identity import VerifiedPrincipal


class ParentRoleStoreUnavailable(Exception):
    """The configured role store could not safely answer the Parent-role query."""


class ParentRoleReader(Protocol):
    def has_active_parent_role(self, *, principal: VerifiedPrincipal) -> bool: ...
