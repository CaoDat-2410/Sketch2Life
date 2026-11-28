"""Current BE1 authorization port for Manager StoryRun metadata and commands."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol


class ManagerStoryRunScopeDecision(StrEnum):
    AUTHORIZED = "AUTHORIZED"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    ROLE_DENIED = "ROLE_DENIED"


@dataclass(frozen=True, slots=True)
class ManagerStoryRunAuthorization:
    decision: ManagerStoryRunScopeDecision
    audit_actor_ref: str | None = None


class ManagerStoryRunScope(Protocol):
    def authorize_manager(
        self,
        *,
        principal_subject: str,
        principal_issuer: str,
        organization_id: str,
        lock: bool,
    ) -> ManagerStoryRunAuthorization: ...


__all__ = [
    "ManagerStoryRunAuthorization",
    "ManagerStoryRunScope",
    "ManagerStoryRunScopeDecision",
]
