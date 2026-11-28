"""PostgreSQL/S3 adapter for immutable SVG catalog assets and review decisions."""

from __future__ import annotations

import contextlib
import hashlib
import json
from datetime import UTC, datetime
from io import BytesIO
from typing import Any, NoReturn
from uuid import uuid4

from sqlalchemy import func, insert, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from sketch2life.application.ports.object_storage import ObjectStorageFailure, ObjectStoragePort
from sketch2life.application.ports.svg_catalog import SvgSanitizationReceipt
from sketch2life.domain.svg_engine import classify_svg_source
from sketch2life.infrastructure.persistence.core_models import CoreAssetMetadataModel
from sketch2life.infrastructure.persistence.svg_catalog_tables import (
    CORE_ASSET_LINEAGE,
    SVG_CATALOG_ASSETS,
    SVG_CATALOG_GUIDE_REVISIONS,
    SVG_CATALOG_REVIEWS,
)
from sketch2life.infrastructure.svg.sanitizer import (
    SANITIZER_CODE_SHA256,
    SvgInputRejected,
    canonical_json_bytes,
    sanitize_svg_source,
)


class SvgCatalogPersistenceError(RuntimeError):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(code)


class SqlSvgSanitizer:
    def sanitize(self, source: bytes) -> SvgSanitizationReceipt:
        try:
            clean = sanitize_svg_source(source)
        except SvgInputRejected:
            raise
        return SvgSanitizationReceipt(
            source_bytes=source,
            document=clean.document,
            source_sha256=clean.source_sha256,
            canonical_sha256=clean.canonical_sha256,
            readiness=clean.readiness,
            canonical_bytes=canonical_json_bytes(clean.document),
            sanitizer_version=clean.sanitizer_version,
        )


class SqlSvgCatalogRepository:
    def __init__(self, db: Session, storage: ObjectStoragePort) -> None:
        self.db = db
        self.storage = storage

    def create_asset(
        self,
        *,
        catalog_entry_id: str,
        scope_kind: str,
        organization_id: str | None,
        actor: str,
        metadata: dict[str, Any],
        sanitized: SvgSanitizationReceipt,
    ) -> dict[str, Any]:
        source_bytes = sanitized.source_bytes
        if not source_bytes:
            raise SvgCatalogPersistenceError(
                500, "SVG_SOURCE_BYTES_UNAVAILABLE", "Source bytes were not preserved"
            )
        source_ref = f"svg-source-{uuid4().hex}"
        canonical_ref = f"svg-canonical-{uuid4().hex}"
        source_version = canonical_version = 1
        source_key = self._object_key(source_ref, source_version, "source.svg")
        canonical_key = self._object_key(canonical_ref, canonical_version, "canonical.json")
        canonical_bytes = sanitized.canonical_bytes
        source_written = False
        canonical_written = False
        try:
            self.storage.put_object(
                source_key,
                BytesIO(source_bytes),
                content_type="image/svg+xml",
                content_length=len(source_bytes),
                metadata={"sha256": sanitized.source_sha256, "asset-ref": source_ref},
            )
            source_written = True
            self.storage.put_object(
                canonical_key,
                BytesIO(canonical_bytes),
                content_type="application/vnd.sketch2life.svg-document+json",
                content_length=len(canonical_bytes),
                metadata={"sha256": sanitized.canonical_sha256, "asset-ref": canonical_ref},
            )
            canonical_written = True
            owner_ref = organization_id if scope_kind == "ORGANIZATION" else "PLATFORM"
            for (
                asset_ref,
                version,
                owner_kind,
                content_sha256,
                media_type,
                source_refs,
                derived_from,
            ) in (
                (
                    source_ref,
                    source_version,
                    scope_kind,
                    sanitized.source_sha256,
                    "image/svg+xml",
                    [metadata["source_uri"]],
                    None,
                ),
                (
                    canonical_ref,
                    canonical_version,
                    scope_kind,
                    sanitized.canonical_sha256,
                    "application/vnd.sketch2life.svg-document+json",
                    [metadata["source_uri"]],
                    source_ref,
                ),
            ):
                self.db.add(
                    CoreAssetMetadataModel(
                        asset_ref=asset_ref,
                        asset_version=version,
                        organization_id=organization_id if scope_kind == "ORGANIZATION" else None,
                        owner_scope_kind=owner_kind,
                        owner_scope_ref=owner_ref,
                        content_sha256=content_sha256,
                        media_type=media_type,
                        source_refs=source_refs,
                        derived_from_ref=derived_from,
                    )
                )
            self.db.flush()
            self.db.execute(
                insert(SVG_CATALOG_ASSETS).values(
                    asset_ref=source_ref,
                    asset_version=source_version,
                    catalog_entry_id=catalog_entry_id,
                    visibility_scope=scope_kind,
                    organization_id=organization_id,
                    canonical_asset_ref=canonical_ref,
                    canonical_asset_version=canonical_version,
                    topic_key=metadata["topic_key"],
                    title_vi=metadata["title_vi"],
                    alt_text_vi=metadata["alt_text_vi"],
                    source_uri=metadata["source_uri"],
                    license_id=metadata["license_id"],
                    license_uri=metadata["license_uri"],
                    source_sha256=sanitized.source_sha256,
                    canonical_sha256=sanitized.canonical_sha256,
                    sanitizer_version=sanitized.sanitizer_version,
                    readiness_class=sanitized.readiness["classification"],
                    structural_facts=sanitized.readiness["facts"],
                    catalog_state="ACTIVE",
                    created_by=actor,
                    created_at=datetime.now(UTC),
                )
            )
            self.db.execute(
                insert(CORE_ASSET_LINEAGE).values(
                    lineage_id=str(uuid4()),
                    source_asset_ref=source_ref,
                    source_asset_version=source_version,
                    derived_asset_ref=canonical_ref,
                    derived_asset_version=canonical_version,
                    source_sha256=sanitized.source_sha256,
                    derived_sha256=sanitized.canonical_sha256,
                    source_size_bytes=len(source_bytes),
                    derived_size_bytes=len(canonical_bytes),
                    transform_kind="SVG_SANITIZE",
                    transform_version=sanitized.sanitizer_version,
                    scanner_name="SVG_SANITIZER",
                    scanner_version=sanitized.sanitizer_version,
                    scanner_sha256=SANITIZER_CODE_SHA256,
                )
            )
            self.db.commit()
        except (SQLAlchemyError, ObjectStorageFailure, KeyError, ValueError) as exc:
            self.db.rollback()
            self._delete_if_written(source_key, source_written)
            self._delete_if_written(canonical_key, canonical_written)
            if isinstance(exc, ObjectStorageFailure):
                raise SvgCatalogPersistenceError(
                    503, "OBJECT_STORAGE_UNAVAILABLE", "SVG object storage is unavailable"
                ) from None
            if isinstance(exc, KeyError):
                raise SvgCatalogPersistenceError(
                    422, "SVG_METADATA_INVALID", "Required provenance fields are missing"
                ) from None
            raise SvgCatalogPersistenceError(
                409, "SVG_ASSET_PERSISTENCE_FAILED", "SVG catalog item could not be saved"
            ) from None
        return self._asset_response(self._load_asset(catalog_entry_id), include_document=True)

    def list_parent_guides(self, *, topic_key: str | None, limit: int) -> dict[str, Any]:
        stmt = select(SVG_CATALOG_ASSETS).where(
            SVG_CATALOG_ASSETS.c.visibility_scope == "PLATFORM",
            SVG_CATALOG_ASSETS.c.catalog_state == "ACTIVE",
            SVG_CATALOG_ASSETS.c.readiness_class != "STATIC_ONLY",
        )
        if topic_key:
            stmt = stmt.where(SVG_CATALOG_ASSETS.c.topic_key == topic_key)
        rows = (
            self.db.execute(
                stmt.order_by(SVG_CATALOG_ASSETS.c.topic_key, SVG_CATALOG_ASSETS.c.title_vi).limit(
                    limit * 4
                )
            )
            .mappings()
            .all()
        )
        items: list[dict[str, Any]] = []
        for asset in rows:
            if not self._review_approved(
                asset, subject_kind="SOURCE_ASSET", review_kind="EDUCATOR", grouping=False
            ):
                continue
            if not self._review_approved(
                asset, subject_kind="SOURCE_ASSET", review_kind="CURATOR", grouping=False
            ):
                continue
            guide = self._latest_approved_guide(asset)
            if guide is None:
                continue
            detail = self._asset_response(asset, include_document=True)
            items.append(
                {
                    "contract": "SvgGuideCatalogItemV1",
                    "catalog_entry_id": asset["catalog_entry_id"],
                    "guide_revision_id": guide["guide_revision_id"],
                    "topic_key": asset["topic_key"],
                    "title_vi": asset["title_vi"],
                    "alt_text_vi": asset["alt_text_vi"],
                    "source_sha256": asset["source_sha256"],
                    "guide_sha256": guide["guide_sha256"],
                    "document": detail["document"],
                    "guide": guide["guide_json"],
                    "source_uri": asset["source_uri"],
                    "license_id": asset["license_id"],
                    "license_uri": asset["license_uri"],
                }
            )
            if len(items) >= limit:
                break
        return {"contract": "SvgGuideCatalogPageV1", "items": items}

    def list_teacher_assets(self, *, organization_id: str, limit: int) -> dict[str, Any]:
        rows = (
            self.db.execute(
                select(SVG_CATALOG_ASSETS)
                .where(
                    SVG_CATALOG_ASSETS.c.catalog_state != "ARCHIVED",
                    SVG_CATALOG_ASSETS.c.catalog_state != "REJECTED",
                    (SVG_CATALOG_ASSETS.c.visibility_scope == "PLATFORM")
                    | (
                        (SVG_CATALOG_ASSETS.c.visibility_scope == "ORGANIZATION")
                        & (SVG_CATALOG_ASSETS.c.organization_id == organization_id)
                    ),
                )
                .order_by(SVG_CATALOG_ASSETS.c.created_at.desc())
                .limit(limit)
            )
            .mappings()
            .all()
        )
        return {
            "contract": "SvgCatalogPageV1",
            "items": [self._asset_response(row, include_document=True) for row in rows],
        }

    def get_asset_for_teacher(
        self, *, organization_id: str, catalog_entry_id: str
    ) -> dict[str, Any]:
        row = self._load_asset_for_teacher(
            organization_id=organization_id, catalog_entry_id=catalog_entry_id
        )
        return self._asset_response(row, include_document=True)

    def get_asset_record_for_teacher(
        self, *, organization_id: str, catalog_entry_id: str
    ) -> dict[str, Any]:
        return dict(
            self._load_asset_for_teacher(
                organization_id=organization_id, catalog_entry_id=catalog_entry_id
            )
        )

    def _load_asset_for_teacher(
        self, *, organization_id: str, catalog_entry_id: str
    ) -> Any:
        row = self._load_asset(catalog_entry_id)
        if row["catalog_state"] in {"ARCHIVED", "REJECTED"} or (
            row["visibility_scope"] == "ORGANIZATION" and row["organization_id"] != organization_id
        ):
            self._not_found()
        return row

    def get_asset_for_platform(self, *, catalog_entry_id: str) -> dict[str, Any]:
        row = self._load_asset_for_platform(catalog_entry_id=catalog_entry_id)
        return self._asset_response(row, include_document=True)

    def get_asset_record_for_platform(self, *, catalog_entry_id: str) -> dict[str, Any]:
        return dict(self._load_asset_for_platform(catalog_entry_id=catalog_entry_id))

    def _load_asset_for_platform(self, *, catalog_entry_id: str) -> Any:
        row = self._load_asset(catalog_entry_id)
        if row["visibility_scope"] != "PLATFORM" or row["catalog_state"] == "ARCHIVED":
            self._not_found()
        return row

    def get_asset_by_source_ref(self, *, asset_ref: str, asset_version: int) -> dict[str, Any]:
        row = (
            self.db.execute(
                select(SVG_CATALOG_ASSETS).where(
                    SVG_CATALOG_ASSETS.c.asset_ref == asset_ref,
                    SVG_CATALOG_ASSETS.c.asset_version == asset_version,
                    SVG_CATALOG_ASSETS.c.catalog_state == "ACTIVE",
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            self._not_found()
        return self._asset_response(row, include_document=True)

    def create_guide_revision(
        self,
        *,
        asset: dict[str, Any],
        actor: str,
        organization_id: str | None,
        guide: dict[str, Any],
        guide_sha256: str,
    ) -> dict[str, Any]:
        if organization_id is None:
            scope_kind = "PLATFORM"
            scope_ref = "platform"
        else:
            scope_kind = "ORGANIZATION"
            scope_ref = organization_id
        if (
            asset["visibility_scope"] == "ORGANIZATION"
            and asset["organization_id"] != organization_id
        ):
            self._not_found()
        if asset["catalog_state"] != "ACTIVE":
            raise SvgCatalogPersistenceError(
                409, "SVG_ASSET_UNAVAILABLE", "This SVG source is not available for authoring"
            )
        guide_identity = f"{asset['asset_ref']}:{scope_ref}"
        guide_ref = f"guide-{hashlib.sha256(guide_identity.encode('utf-8')).hexdigest()[:32]}"
        existing = (
            self.db.execute(
                select(SVG_CATALOG_GUIDE_REVISIONS)
                .where(
                    SVG_CATALOG_GUIDE_REVISIONS.c.guide_ref == guide_ref,
                    SVG_CATALOG_GUIDE_REVISIONS.c.asset_ref == asset["asset_ref"],
                    SVG_CATALOG_GUIDE_REVISIONS.c.asset_version == asset["asset_version"],
                    SVG_CATALOG_GUIDE_REVISIONS.c.source_sha256 == asset["source_sha256"],
                    SVG_CATALOG_GUIDE_REVISIONS.c.guide_sha256 == guide_sha256,
                    SVG_CATALOG_GUIDE_REVISIONS.c.authored_by == actor,
                )
                .order_by(SVG_CATALOG_GUIDE_REVISIONS.c.guide_revision.desc())
                .limit(1)
            )
            .mappings()
            .one_or_none()
        )
        review = self._latest_guide_review(asset, existing) if existing is not None else None
        if existing is not None and (review is None or review["decision"] != "REJECT"):
            return {
                "guide_revision_id": existing["guide_revision_id"],
                "guide_ref": existing["guide_ref"],
                "guide_revision": existing["guide_revision"],
                "source_sha256": existing["source_sha256"],
                "guide_sha256": existing["guide_sha256"],
                "guide": existing["guide_json"],
                "authored_by": existing["authored_by"],
                "visibility_scope": existing["visibility_scope"],
                "organization_id": existing["organization_id"],
                "review_state": "PENDING"
                if review is None
                else review["decision"]
                .replace("APPROVE", "APPROVED")
                .replace("REJECT", "REJECTED"),
            }
        current = self.db.scalar(
            select(func.max(SVG_CATALOG_GUIDE_REVISIONS.c.guide_revision)).where(
                SVG_CATALOG_GUIDE_REVISIONS.c.guide_ref == guide_ref
            )
        )
        revision = int(current or 0) + 1
        guide_revision_id = str(uuid4())
        try:
            self.db.execute(
                insert(SVG_CATALOG_GUIDE_REVISIONS).values(
                    guide_revision_id=guide_revision_id,
                    guide_ref=guide_ref,
                    guide_revision=revision,
                    asset_ref=asset["asset_ref"],
                    asset_version=asset["asset_version"],
                    visibility_scope=scope_kind,
                    organization_id=organization_id,
                    source_sha256=asset["source_sha256"],
                    guide_sha256=guide_sha256,
                    schema_version=guide["schema_version"],
                    guide_json=guide,
                    authored_by=actor,
                    created_at=datetime.now(UTC),
                )
            )
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise SvgCatalogPersistenceError(
                409, "SVG_GUIDE_REVISION_CONFLICT", "A guide revision could not be saved"
            ) from None
        return {
            "guide_revision_id": guide_revision_id,
            "guide_ref": guide_ref,
            "guide_revision": revision,
            "source_sha256": asset["source_sha256"],
            "guide_sha256": guide_sha256,
            "guide": guide,
            "authored_by": actor,
            "visibility_scope": scope_kind,
            "organization_id": organization_id,
            "review_state": "PENDING",
        }

    def get_guide_revision(
        self, *, catalog_entry_id: str, guide_revision_id: str
    ) -> dict[str, Any]:
        asset = self._load_asset(catalog_entry_id)
        row = (
            self.db.execute(
                select(SVG_CATALOG_GUIDE_REVISIONS).where(
                    SVG_CATALOG_GUIDE_REVISIONS.c.guide_revision_id == guide_revision_id,
                    SVG_CATALOG_GUIDE_REVISIONS.c.asset_ref == asset["asset_ref"],
                    SVG_CATALOG_GUIDE_REVISIONS.c.asset_version == asset["asset_version"],
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            self._not_found()
        return dict(row)

    def list_guide_revisions(
        self, *, organization_id: str, catalog_entry_id: str, limit: int
    ) -> dict[str, Any]:
        asset = self._load_asset(catalog_entry_id)
        if asset["catalog_state"] in {"ARCHIVED", "REJECTED"} or (
            asset["visibility_scope"] == "ORGANIZATION"
            and asset["organization_id"] != organization_id
        ):
            self._not_found()
        rows = (
            self.db.execute(
                select(SVG_CATALOG_GUIDE_REVISIONS)
                .where(
                    SVG_CATALOG_GUIDE_REVISIONS.c.asset_ref == asset["asset_ref"],
                    SVG_CATALOG_GUIDE_REVISIONS.c.asset_version == asset["asset_version"],
                    (
                        (SVG_CATALOG_GUIDE_REVISIONS.c.visibility_scope == "PLATFORM")
                        | (
                            (SVG_CATALOG_GUIDE_REVISIONS.c.visibility_scope == "ORGANIZATION")
                            & (SVG_CATALOG_GUIDE_REVISIONS.c.organization_id == organization_id)
                        )
                    ),
                )
                .order_by(
                    SVG_CATALOG_GUIDE_REVISIONS.c.created_at.desc(),
                    SVG_CATALOG_GUIDE_REVISIONS.c.guide_revision.desc(),
                )
                .limit(limit)
            )
            .mappings()
            .all()
        )
        items = []
        for row in rows:
            review = self._latest_guide_review(asset, row)
            items.append(
                {
                    "contract": "SvgGuideRevisionReceiptV1",
                    "guide_revision_id": row["guide_revision_id"],
                    "guide_ref": row["guide_ref"],
                    "guide_revision": row["guide_revision"],
                    "source_sha256": row["source_sha256"],
                    "guide_sha256": row["guide_sha256"],
                    "guide": row["guide_json"],
                    "authored_by": row["authored_by"],
                    "visibility_scope": row["visibility_scope"],
                    "organization_id": row["organization_id"],
                    "review_state": "PENDING"
                    if review is None
                    else review["decision"]
                    .replace("APPROVE", "APPROVED")
                    .replace("REJECT", "REJECTED"),
                }
            )
        return {"contract": "SvgGuideRevisionPageV1", "items": items}

    def record_review(
        self,
        *,
        asset: dict[str, Any],
        actor: str,
        review_subject_kind: str,
        review_kind: str,
        source_sha256: str,
        decision: str,
        reason: str | None,
        grouping_allowed: bool = False,
        guide_revision: dict[str, Any] | None = None,
        guide_sha256: str | None = None,
    ) -> dict[str, Any]:
        if source_sha256 != asset["source_sha256"]:
            raise SvgCatalogPersistenceError(
                409, "SVG_REVIEW_SOURCE_STALE", "Review targets a different source revision"
            )
        if review_subject_kind == "GUIDE":
            if (
                guide_revision is None
                or guide_revision["source_sha256"] != source_sha256
                or guide_revision["guide_sha256"] != guide_sha256
            ):
                raise SvgCatalogPersistenceError(
                    409, "SVG_REVIEW_GUIDE_STALE", "Review targets a different guide revision"
                )
        elif guide_revision is not None or guide_sha256 is not None:
            raise SvgCatalogPersistenceError(
                422, "SVG_REVIEW_SUBJECT_INVALID", "Source review cannot include guide fields"
            )
        review_id = str(uuid4())
        try:
            self.db.execute(
                insert(SVG_CATALOG_REVIEWS).values(
                    review_id=review_id,
                    asset_ref=asset["asset_ref"],
                    asset_version=asset["asset_version"],
                    guide_revision_id=guide_revision["guide_revision_id"]
                    if guide_revision
                    else None,
                    review_subject_kind=review_subject_kind,
                    review_kind=review_kind,
                    source_sha256=source_sha256,
                    guide_sha256=guide_sha256,
                    reviewer_ref=actor,
                    decision=decision,
                    grouping_allowed=grouping_allowed,
                    reason=reason,
                    created_at=datetime.now(UTC),
                )
            )
            if decision == "REJECT" and review_subject_kind == "SOURCE_ASSET":
                self.db.execute(
                    update(SVG_CATALOG_ASSETS)
                    .where(
                        SVG_CATALOG_ASSETS.c.asset_ref == asset["asset_ref"],
                        SVG_CATALOG_ASSETS.c.asset_version == asset["asset_version"],
                    )
                    .values(catalog_state="REJECTED")
                )
            elif review_kind == "CURATOR" and decision == "APPROVE":
                self.db.execute(
                    update(SVG_CATALOG_ASSETS)
                    .where(
                        SVG_CATALOG_ASSETS.c.asset_ref == asset["asset_ref"],
                        SVG_CATALOG_ASSETS.c.asset_version == asset["asset_version"],
                    )
                    .values(catalog_state="ACTIVE")
                )
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise SvgCatalogPersistenceError(
                409, "SVG_REVIEW_CONFLICT", "Review decision could not be saved"
            ) from None
        return {
            "review_id": review_id,
            "catalog_entry_id": asset["catalog_entry_id"],
            "review_subject_kind": review_subject_kind,
            "review_kind": review_kind,
            "decision": decision,
            "source_sha256": source_sha256,
            "guide_sha256": guide_sha256,
            "grouping_allowed": grouping_allowed,
            "reviewer_ref": actor,
            "created_at": datetime.now(UTC),
        }

    def _asset_response(self, row: Any, *, include_document: bool) -> dict[str, Any]:
        source_review = self._review_approved(
            row, subject_kind="SOURCE_ASSET", review_kind="EDUCATOR", grouping=False
        )
        curator_approval = self._review_approved(
            row, subject_kind="SOURCE_ASSET", review_kind="CURATOR", grouping=False
        )
        curator_grouping_allowed = self._review_approved(
            row, subject_kind="SOURCE_ASSET", review_kind="CURATOR", grouping=True
        )
        if row["catalog_state"] == "REJECTED":
            review_state = "REJECTED"
        elif source_review and (row["visibility_scope"] == "ORGANIZATION" or curator_approval):
            review_state = "APPROVED"
        elif source_review:
            review_state = "PENDING_CURATOR_REVIEW"
        else:
            review_state = "PENDING_EDUCATOR_REVIEW"
        document = self._read_canonical(row) if include_document else None
        readiness = (
            classify_svg_source(
                drawable_path_ids=[path["path_id"] for path in (document or {}).get("paths", [])],
                filled_shape_count=int(row["structural_facts"].get("filled_shape_count", 0)),
                educator_approved=source_review,
                curator_grouping_allowed=curator_grouping_allowed,
            )
            if document is not None
            else {
                "classification": row["readiness_class"],
                "reason_codes": [],
                "facts": dict(row["structural_facts"]),
            }
        )
        return {
            "contract": "SvgCatalogAssetResponseV1",
            "catalog_entry_id": row["catalog_entry_id"],
            "source_asset_ref": row["asset_ref"],
            "source_asset_version": row["asset_version"],
            "canonical_asset_ref": row["canonical_asset_ref"],
            "canonical_asset_version": row["canonical_asset_version"],
            "source_sha256": row["source_sha256"],
            "canonical_sha256": row["canonical_sha256"],
            "topic_key": row["topic_key"],
            "title_vi": row["title_vi"],
            "alt_text_vi": row["alt_text_vi"],
            "source_uri": row["source_uri"],
            "license_id": row["license_id"],
            "license_uri": row["license_uri"],
            "visibility_scope": row["visibility_scope"],
            "organization_id": row["organization_id"],
            "created_by": row["created_by"],
            "readiness": readiness["classification"],
            "readiness_reasons": readiness["reason_codes"],
            "structural_facts": dict(row["structural_facts"]),
            "review_state": review_state,
            "document": document,
        }

    def _read_canonical(self, asset: Any) -> dict[str, Any]:
        key = self._object_key(
            asset["canonical_asset_ref"], asset["canonical_asset_version"], "canonical.json"
        )
        try:
            stored = self.storage.get_object(key)
        except ObjectStorageFailure:
            raise SvgCatalogPersistenceError(
                503, "OBJECT_STORAGE_UNAVAILABLE", "SVG object storage is unavailable"
            ) from None
        if stored is None:
            raise SvgCatalogPersistenceError(
                503, "SVG_CANONICAL_OBJECT_MISSING", "Canonical SVG asset is unavailable"
            )
        try:
            content = stored.body.read(6_000_000)
        finally:
            stored.body.close()
        if hashlib.sha256(content).hexdigest() != asset["canonical_sha256"]:
            raise SvgCatalogPersistenceError(
                503,
                "SVG_CANONICAL_HASH_MISMATCH",
                "Canonical SVG asset failed integrity validation",
            )
        try:
            value = json.loads(content)
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise SvgCatalogPersistenceError(
                503, "SVG_CANONICAL_JSON_INVALID", "Canonical SVG asset is invalid"
            ) from None
        if not isinstance(value, dict) or value.get("schema_version") != "SvgDocumentV1":
            raise SvgCatalogPersistenceError(
                503, "SVG_CANONICAL_SCHEMA_INVALID", "Canonical SVG asset is invalid"
            )
        return value

    def _load_asset(self, catalog_entry_id: str) -> Any:
        row = (
            self.db.execute(
                select(SVG_CATALOG_ASSETS).where(
                    SVG_CATALOG_ASSETS.c.catalog_entry_id == catalog_entry_id
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            self._not_found()
        return row

    def _latest_guide(
        self, *, asset_ref: str, visibility_scope: str, organization_id: str | None
    ) -> Any:
        stmt = select(SVG_CATALOG_GUIDE_REVISIONS).where(
            SVG_CATALOG_GUIDE_REVISIONS.c.asset_ref == asset_ref,
            SVG_CATALOG_GUIDE_REVISIONS.c.visibility_scope == visibility_scope,
        )
        if organization_id is None:
            stmt = stmt.where(SVG_CATALOG_GUIDE_REVISIONS.c.organization_id.is_(None))
        else:
            stmt = stmt.where(SVG_CATALOG_GUIDE_REVISIONS.c.organization_id == organization_id)
        return (
            self.db.execute(
                stmt.order_by(SVG_CATALOG_GUIDE_REVISIONS.c.guide_revision.desc()).limit(1)
            )
            .mappings()
            .one_or_none()
        )

    def _latest_approved_guide(self, asset: Any) -> Any:
        rows = (
            self.db.execute(
                select(SVG_CATALOG_GUIDE_REVISIONS)
                .where(
                    SVG_CATALOG_GUIDE_REVISIONS.c.asset_ref == asset["asset_ref"],
                    SVG_CATALOG_GUIDE_REVISIONS.c.asset_version == asset["asset_version"],
                    SVG_CATALOG_GUIDE_REVISIONS.c.visibility_scope == "PLATFORM",
                    SVG_CATALOG_GUIDE_REVISIONS.c.organization_id.is_(None),
                    SVG_CATALOG_GUIDE_REVISIONS.c.source_sha256 == asset["source_sha256"],
                )
                .order_by(SVG_CATALOG_GUIDE_REVISIONS.c.guide_revision.desc())
            )
            .mappings()
            .all()
        )
        for guide in rows:
            if self._review_approved(
                asset,
                subject_kind="GUIDE",
                review_kind="EDUCATOR",
                grouping=False,
                guide_revision_id=guide["guide_revision_id"],
                guide_sha256=guide["guide_sha256"],
            ):
                return guide
        return None

    def _review_approved(
        self,
        asset: Any,
        *,
        subject_kind: str,
        review_kind: str,
        grouping: bool,
        guide_revision_id: str | None = None,
        guide_sha256: str | None = None,
    ) -> bool:
        stmt = select(SVG_CATALOG_REVIEWS).where(
            SVG_CATALOG_REVIEWS.c.asset_ref == asset["asset_ref"],
            SVG_CATALOG_REVIEWS.c.asset_version == asset["asset_version"],
            SVG_CATALOG_REVIEWS.c.review_subject_kind == subject_kind,
            SVG_CATALOG_REVIEWS.c.review_kind == review_kind,
            SVG_CATALOG_REVIEWS.c.source_sha256 == asset["source_sha256"],
        )
        if guide_revision_id is None:
            stmt = stmt.where(SVG_CATALOG_REVIEWS.c.guide_revision_id.is_(None))
        else:
            stmt = stmt.where(
                SVG_CATALOG_REVIEWS.c.guide_revision_id == guide_revision_id,
                SVG_CATALOG_REVIEWS.c.guide_sha256 == guide_sha256,
            )
        row = (
            self.db.execute(
                stmt.order_by(
                    SVG_CATALOG_REVIEWS.c.created_at.desc(), SVG_CATALOG_REVIEWS.c.review_id.desc()
                ).limit(1)
            )
            .mappings()
            .one_or_none()
        )
        return bool(
            row
            and row["decision"] == "APPROVE"
            and (not grouping or row["grouping_allowed"] is True)
        )

    def _latest_guide_review(self, asset: Any, guide: Any) -> Any:
        return (
            self.db.execute(
                select(SVG_CATALOG_REVIEWS)
                .where(
                    SVG_CATALOG_REVIEWS.c.asset_ref == asset["asset_ref"],
                    SVG_CATALOG_REVIEWS.c.asset_version == asset["asset_version"],
                    SVG_CATALOG_REVIEWS.c.guide_revision_id == guide["guide_revision_id"],
                    SVG_CATALOG_REVIEWS.c.review_subject_kind == "GUIDE",
                    SVG_CATALOG_REVIEWS.c.review_kind == "EDUCATOR",
                    SVG_CATALOG_REVIEWS.c.source_sha256 == guide["source_sha256"],
                    SVG_CATALOG_REVIEWS.c.guide_sha256 == guide["guide_sha256"],
                )
                .order_by(
                    SVG_CATALOG_REVIEWS.c.created_at.desc(), SVG_CATALOG_REVIEWS.c.review_id.desc()
                )
                .limit(1)
            )
            .mappings()
            .one_or_none()
        )

    @staticmethod
    def _object_key(asset_ref: str, version: int, file_name: str) -> str:
        return f"svg-catalog/{asset_ref}/v{version}/{file_name}"

    def _delete_if_written(self, key: str, written: bool) -> None:
        if written:
            with contextlib.suppress(ObjectStorageFailure):
                self.storage.delete_object(key)

    @staticmethod
    def _not_found() -> NoReturn:
        raise SvgCatalogPersistenceError(
            404, "SVG_CATALOG_ITEM_NOT_FOUND", "SVG catalog item was not found"
        )


__all__ = ["SqlSvgCatalogRepository", "SqlSvgSanitizer", "SvgCatalogPersistenceError"]
