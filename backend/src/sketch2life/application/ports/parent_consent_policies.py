"""Persistence contract for versioned Parent consent policies."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


class ParentConsentPolicyRepositoryError(RuntimeError):
    def __init__(self, status_code: int, code: str) -> None:
        self.status_code = status_code
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class ParentConsentPolicyRecord:
    policy_id: str
    version: str
    purpose_code: str
    text: str
    text_sha256: str
    state: str
    created_by: str
    created_at: datetime
    activated_by: str | None
    activated_at: datetime | None


class ParentConsentPolicyRepositoryPort(Protocol):
    def get_active_policy(self) -> ParentConsentPolicyRecord | None: ...

    def list_policies(self) -> list[ParentConsentPolicyRecord]: ...

    def create_draft(
        self,
        *,
        policy_id: str,
        version: str,
        purpose_code: str,
        text: str,
        text_sha256: str,
        actor_subject: str,
    ) -> ParentConsentPolicyRecord: ...

    def activate(
        self, *, policy_id: str, actor_subject: str
    ) -> ParentConsentPolicyRecord: ...


__all__ = [
    "ParentConsentPolicyRecord",
    "ParentConsentPolicyRepositoryError",
    "ParentConsentPolicyRepositoryPort",
]
