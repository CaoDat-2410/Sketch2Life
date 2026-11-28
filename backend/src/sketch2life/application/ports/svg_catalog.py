"""Provider-neutral ports for reviewed SVG catalog assets and guides."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class SvgSanitizationReceipt:
    source_bytes: bytes
    document: dict[str, Any]
    source_sha256: str
    canonical_sha256: str
    readiness: dict[str, Any]
    canonical_bytes: bytes
    sanitizer_version: str


class SvgSanitizerPort(Protocol):
    def sanitize(self, source: bytes) -> SvgSanitizationReceipt: ...


class SvgCatalogPort(Protocol):
    def create_asset(
        self, *, catalog_entry_id: str, scope_kind: str, organization_id: str | None,
        actor: str, metadata: dict[str, Any], sanitized: SvgSanitizationReceipt,
    ) -> dict[str, Any]: ...

    def list_parent_guides(self, *, topic_key: str | None, limit: int) -> dict[str, Any]: ...

    def list_teacher_assets(self, *, organization_id: str, limit: int) -> dict[str, Any]: ...

    def get_asset_for_teacher(
        self, *, organization_id: str, catalog_entry_id: str
    ) -> dict[str, Any]: ...

    def get_asset_for_platform(self, *, catalog_entry_id: str) -> dict[str, Any]: ...

    def get_asset_record_for_teacher(
        self, *, organization_id: str, catalog_entry_id: str
    ) -> dict[str, Any]: ...

    def get_asset_record_for_platform(self, *, catalog_entry_id: str) -> dict[str, Any]: ...

    def get_guide_revision(
        self, *, catalog_entry_id: str, guide_revision_id: str
    ) -> dict[str, Any]: ...

    def list_guide_revisions(
        self, *, organization_id: str, catalog_entry_id: str, limit: int
    ) -> dict[str, Any]: ...

    def create_guide_revision(
        self, *, asset: dict[str, Any], actor: str, organization_id: str | None,
        guide: dict[str, Any], guide_sha256: str,
    ) -> dict[str, Any]: ...

    def record_review(
        self, *, asset: dict[str, Any], actor: str, review_subject_kind: str,
        review_kind: str, source_sha256: str, decision: str, reason: str | None,
        grouping_allowed: bool = False, guide_revision: dict[str, Any] | None = None,
        guide_sha256: str | None = None,
    ) -> dict[str, Any]: ...


__all__ = ["SvgCatalogPort", "SvgSanitizationReceipt", "SvgSanitizerPort"]
