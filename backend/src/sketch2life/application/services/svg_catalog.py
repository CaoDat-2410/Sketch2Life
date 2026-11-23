"""Use cases for safe SVG sources, manual guide revisions, and exact-hash review."""

from __future__ import annotations

import hashlib
import json
from typing import Any
from urllib.parse import urlsplit
from uuid import uuid4

from sketch2life.application.ports.svg_catalog import SvgCatalogPort, SvgSanitizerPort
from sketch2life.domain.svg_engine import SvgRuleError, validate_guide_v3


class SvgCatalogError(RuntimeError):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(code)


class SvgCatalogApplicationService:
    def __init__(self, *, catalog: SvgCatalogPort, sanitizer: SvgSanitizerPort) -> None:
        self.catalog = catalog
        self.sanitizer = sanitizer

    def create_asset(
        self,
        *,
        scope_kind: str,
        organization_id: str | None,
        actor: str,
        request: dict[str, Any],
    ) -> dict[str, Any]:
        for field in ("source_uri", "license_uri"):
            parsed = urlsplit(str(request.get(field, "")))
            if parsed.scheme != "https" or not parsed.hostname:
                raise SvgCatalogError(422, "SVG_PROVENANCE_URL_INVALID", "Source and license URLs must use HTTPS")
        try:
            sanitized = self.sanitizer.sanitize(str(request["source_svg"]).encode("utf-8"))
        except (KeyError, UnicodeError, ValueError) as exc:
            code = getattr(exc, "code", "SVG_SOURCE_INVALID")
            raise SvgCatalogError(422, str(code), "SVG source was rejected by the safe parser") from None
        return self.catalog.create_asset(
            catalog_entry_id=str(uuid4()),
            scope_kind=scope_kind,
            organization_id=organization_id,
            actor=actor,
            metadata={key: value for key, value in request.items() if key != "source_svg"},
            sanitized=sanitized,
        )

    def list_parent_guides(self, *, topic_key: str | None, limit: int) -> dict[str, Any]:
        if not 1 <= limit <= 100:
            raise SvgCatalogError(422, "INVALID_REQUEST", "limit must be between 1 and 100")
        return self.catalog.list_parent_guides(topic_key=topic_key, limit=limit)

    def list_teacher_assets(self, *, organization_id: str, limit: int) -> dict[str, Any]:
        if not 1 <= limit <= 100:
            raise SvgCatalogError(422, "INVALID_REQUEST", "limit must be between 1 and 100")
        return self.catalog.list_teacher_assets(organization_id=organization_id, limit=limit)

    def create_guide_revision(
        self,
        *,
        asset: dict[str, Any],
        actor: str,
        organization_id: str | None,
        guide: dict[str, Any],
    ) -> dict[str, Any]:
        source_ref = str(asset["asset_ref"])
        source_version = int(asset["asset_version"])
        source_hash = str(asset["source_sha256"])
        document = asset["document"]
        path_ids = [path["path_id"] for path in document["paths"]]
        if guide.get("source_asset_ref") != source_ref or guide.get("source_asset_version") != source_version:
            raise SvgCatalogError(422, "SVG_GUIDE_SOURCE_MISMATCH", "Guide must reference the selected source revision")
        try:
            normalized = validate_guide_v3(
                guide,
                source_path_ids=path_ids,
                expected_source_sha256=source_hash,
            )
        except SvgRuleError as exc:
            raise SvgCatalogError(422, exc.code, "Guide does not match the canonical source paths") from None
        guide_bytes = json.dumps(
            normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        return self.catalog.create_guide_revision(
            asset=asset,
            actor=actor,
            organization_id=organization_id,
            guide=normalized,
            guide_sha256=hashlib.sha256(guide_bytes).hexdigest(),
        )

    def record_review(self, **values: Any) -> dict[str, Any]:
        return self.catalog.record_review(**values)

    def get_guide_revision(self, *, catalog_entry_id: str, guide_revision_id: str) -> dict[str, Any]:
        return self.catalog.get_guide_revision(
            catalog_entry_id=catalog_entry_id,
            guide_revision_id=guide_revision_id,
        )

    def list_guide_revisions(
        self, *, organization_id: str, catalog_entry_id: str, limit: int
    ) -> dict[str, Any]:
        if not 1 <= limit <= 100:
            raise SvgCatalogError(422, "INVALID_REQUEST", "limit must be between 1 and 100")
        return self.catalog.list_guide_revisions(
            organization_id=organization_id,
            catalog_entry_id=catalog_entry_id,
            limit=limit,
        )


__all__ = ["SvgCatalogApplicationService", "SvgCatalogError"]
