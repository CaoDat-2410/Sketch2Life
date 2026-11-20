"""Ports for generic upload sessions (SRS FR-C-12, l.1654-1658; goal v3 T-2a).

An upload session belongs to one adult actor and one target (a Parent run or, later, a Teacher
lesson occurrence). Which targets exist and who may write to them is not known to the upload
service: each purpose registers a ``UploadTargetResolver`` that maps the verified principal and a
client ``target_ref`` to an ``UploadScope`` (or to ``None``, which the route answers as the uniform
404 of C-D4/CV-5). No Teacher occurrence table exists yet, so ``OCCURRENCE_DOCUMENT`` has no
default resolver; T-3a/T-3b register one.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Protocol

from sketch2life.application.ports.identity import VerifiedPrincipal

PARENT_ACCOUNT_SCOPE: Final = "PARENT_ACCOUNT"
ORGANIZATION_SCOPE: Final = "ORGANIZATION"

UPLOAD_PART_SIZE_BYTES: Final = 4 * 1024 * 1024
UPLOAD_MAX_PARTS: Final = 7
UPLOAD_TTL_SECONDS: Final = 24 * 60 * 60


@dataclass(frozen=True, slots=True)
class UploadScope:
    """Owner scope of a target, in the typed form of ``OWNER_SCOPE_CHECK`` (FR-C-08).

    ``PARENT_ACCOUNT`` carries a non-empty ``owner_scope_ref`` and no organization.
    ``ORGANIZATION`` carries the organization id. ``object_prefix`` is the storage key prefix that
    every object of this target lives under (it ends with ``/``); the Parent prefix is
    ``parent/{run_id}/`` so the FR-C-08 purge closure and prefix sweep cover chunks and assets.
    """

    owner_scope_kind: str
    owner_scope_ref: str | None
    organization_id: str | None
    object_prefix: str


class UploadTargetNotAccepting(RuntimeError):
    """The target exists in scope but no longer accepts bytes (run closing, wrong state)."""


class UploadTargetResolver(Protocol):
    def resolve(self, principal: VerifiedPrincipal, target_ref: str) -> UploadScope | None:
        """The scope of ``target_ref`` for this actor, or ``None`` when absent or out of scope."""
        ...

    def ensure_accepting(self, principal: VerifiedPrincipal, target_ref: str) -> None:
        """Raise ``UploadTargetNotAccepting`` unless the target still accepts an upload."""
        ...


__all__ = [
    "ORGANIZATION_SCOPE",
    "PARENT_ACCOUNT_SCOPE",
    "UPLOAD_MAX_PARTS",
    "UPLOAD_PART_SIZE_BYTES",
    "UPLOAD_TTL_SECONDS",
    "UploadScope",
    "UploadTargetNotAccepting",
    "UploadTargetResolver",
]
