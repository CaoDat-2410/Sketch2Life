"""Persistence port for Parent profiles and explicit data authorizations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from sketch2life.domain.parent_profiles import ParentProfileRevisionInput


class ParentProfileRepositoryError(RuntimeError):
    def __init__(self, status_code: int, code: str) -> None:
        self.status_code = status_code
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class ParentProfileRevisionRecord:
    profile_revision_id: str
    revision_no: int
    age_months: int
    display_name: str
    interests_summary: str
    revision_hash: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class ParentProfileRecord:
    parent_profile_id: str
    state: str
    current_revision: ParentProfileRevisionRecord
    authorization_state: str | None
    authorization_policy_version: str | None
    created_at: datetime
    updated_at: datetime


class ParentProfileRepositoryPort(Protocol):
    def list_profiles(self, *, owner_subject: str) -> list[ParentProfileRecord]: ...

    def get_profile(
        self, *, owner_subject: str, parent_profile_id: str
    ) -> ParentProfileRecord | None: ...

    def create_profile(
        self,
        *,
        owner_subject: str,
        profile_id: str,
        revision_id: str,
        authorization_id: str,
        revision: ParentProfileRevisionInput,
        revision_hash: str,
        policy_version: str,
        consent_text_sha256: str,
    ) -> ParentProfileRecord: ...

    def revise_profile(
        self,
        *,
        owner_subject: str,
        parent_profile_id: str,
        expected_revision: int,
        revision_id: str,
        revision: ParentProfileRevisionInput,
        revision_hash: str,
        policy_version: str,
    ) -> ParentProfileRecord: ...

    def grant_authorization(
        self,
        *,
        owner_subject: str,
        parent_profile_id: str,
        authorization_id: str,
        policy_version: str,
        consent_text_sha256: str,
    ) -> ParentProfileRecord: ...

    def revoke_authorization(
        self, *, owner_subject: str, parent_profile_id: str
    ) -> ParentProfileRecord: ...

    def archive_profile(self, *, owner_subject: str, parent_profile_id: str) -> ParentProfileRecord: ...


__all__ = [
    "ParentProfileRecord",
    "ParentProfileRepositoryError",
    "ParentProfileRepositoryPort",
    "ParentProfileRevisionRecord",
]
