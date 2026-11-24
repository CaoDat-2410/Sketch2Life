"""Core persistence mappings for SVG source catalog assets and append-only reviews."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from sketch2life.infrastructure.persistence.core_models import CorePersistenceBase


METADATA = CorePersistenceBase.metadata

CORE_ASSET_LINEAGE = sa.Table(
    "core_asset_lineage",
    METADATA,
    sa.Column("lineage_id", sa.String(36), primary_key=True),
    sa.Column("source_asset_ref", sa.String(256), nullable=False),
    sa.Column("source_asset_version", sa.Integer(), nullable=False),
    sa.Column("derived_asset_ref", sa.String(256), nullable=False),
    sa.Column("derived_asset_version", sa.Integer(), nullable=False),
    sa.Column("source_sha256", sa.String(64), nullable=False),
    sa.Column("derived_sha256", sa.String(64), nullable=False),
    sa.Column("source_size_bytes", sa.BigInteger(), nullable=False),
    sa.Column("derived_size_bytes", sa.BigInteger(), nullable=False),
    sa.Column("transform_kind", sa.String(48), nullable=False),
    sa.Column("transform_version", sa.String(48), nullable=False),
    sa.Column("scanner_name", sa.String(64), nullable=False),
    sa.Column("scanner_version", sa.String(128), nullable=False),
    sa.Column("scanner_sha256", sa.String(64), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    sa.ForeignKeyConstraint(
        ["source_asset_ref", "source_asset_version"],
        ["core_asset_metadata.asset_ref", "core_asset_metadata.asset_version"],
        ondelete="RESTRICT",
    ),
    sa.ForeignKeyConstraint(
        ["derived_asset_ref", "derived_asset_version"],
        ["core_asset_metadata.asset_ref", "core_asset_metadata.asset_version"],
        ondelete="RESTRICT",
    ),
    sa.UniqueConstraint(
        "source_asset_ref", "source_asset_version", "derived_asset_ref", "derived_asset_version",
        "transform_kind", name="uq_core_asset_lineage_edge",
    ),
)

SVG_CATALOG_ASSETS = sa.Table(
    "core_svg_catalog_assets",
    METADATA,
    sa.Column("asset_ref", sa.String(256), primary_key=True),
    sa.Column("asset_version", sa.Integer(), primary_key=True),
    sa.Column("catalog_entry_id", sa.String(36), nullable=False, unique=True),
    sa.Column("visibility_scope", sa.String(16), nullable=False),
    sa.Column("organization_id", sa.String(128)),
    sa.Column("canonical_asset_ref", sa.String(256), nullable=False),
    sa.Column("canonical_asset_version", sa.Integer(), nullable=False),
    sa.Column("topic_key", sa.String(120), nullable=False),
    sa.Column("title_vi", sa.String(300), nullable=False),
    sa.Column("alt_text_vi", sa.String(500), nullable=False),
    sa.Column("source_uri", sa.String(2048), nullable=False),
    sa.Column("license_id", sa.String(120), nullable=False),
    sa.Column("license_uri", sa.String(2048), nullable=False),
    sa.Column("source_sha256", sa.String(64), nullable=False),
    sa.Column("canonical_sha256", sa.String(64), nullable=False),
    sa.Column("sanitizer_version", sa.String(64), nullable=False),
    sa.Column("readiness_class", sa.String(40), nullable=False),
    sa.Column("structural_facts", JSONB, nullable=False),
    sa.Column("catalog_state", sa.String(24), nullable=False, server_default="ACTIVE"),
    sa.Column("created_by", sa.String(256), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    sa.CheckConstraint("asset_version > 0 AND canonical_asset_version > 0", name="ck_svg_catalog_asset_versions"),
    sa.CheckConstraint("length(source_sha256) = 64 AND length(canonical_sha256) = 64", name="ck_svg_catalog_asset_hashes"),
    sa.CheckConstraint("visibility_scope IN ('PLATFORM','ORGANIZATION')", name="ck_svg_catalog_scope"),
    sa.CheckConstraint(
        "(visibility_scope = 'PLATFORM' AND organization_id IS NULL) OR "
        "(visibility_scope = 'ORGANIZATION' AND organization_id IS NOT NULL AND length(organization_id) > 0)",
        name="ck_svg_catalog_scope_owner",
    ),
    sa.CheckConstraint(
        "readiness_class IN ('STROKE_READY','REQUIRES_MANUAL_AUTHORING','STATIC_ONLY')",
        name="ck_svg_catalog_readiness",
    ),
    sa.CheckConstraint("catalog_state IN ('ACTIVE','REJECTED','ARCHIVED')", name="ck_svg_catalog_state"),
    sa.CheckConstraint("octet_length(structural_facts::text) <= 4096", name="ck_svg_catalog_facts_size"),
    sa.ForeignKeyConstraint(
        ["asset_ref", "asset_version"],
        ["core_asset_metadata.asset_ref", "core_asset_metadata.asset_version"],
        ondelete="RESTRICT",
        name="fk_svg_catalog_source_asset",
    ),
    sa.ForeignKeyConstraint(
        ["canonical_asset_ref", "canonical_asset_version"],
        ["core_asset_metadata.asset_ref", "core_asset_metadata.asset_version"],
        ondelete="RESTRICT",
        name="fk_svg_catalog_canonical_asset",
    ),
    sa.Index("ix_svg_catalog_scope_topic_state", "visibility_scope", "organization_id", "topic_key", "catalog_state"),
)

SVG_CATALOG_GUIDE_REVISIONS = sa.Table(
    "core_svg_catalog_guide_revisions",
    METADATA,
    sa.Column("guide_revision_id", sa.String(36), primary_key=True),
    sa.Column("guide_ref", sa.String(256), nullable=False),
    sa.Column("guide_revision", sa.Integer(), nullable=False),
    sa.Column("asset_ref", sa.String(256), nullable=False),
    sa.Column("asset_version", sa.Integer(), nullable=False),
    sa.Column("visibility_scope", sa.String(16), nullable=False),
    sa.Column("organization_id", sa.String(128)),
    sa.Column("source_sha256", sa.String(64), nullable=False),
    sa.Column("guide_sha256", sa.String(64), nullable=False),
    sa.Column("schema_version", sa.String(48), nullable=False),
    sa.Column("guide_json", JSONB, nullable=False),
    sa.Column("authored_by", sa.String(256), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    sa.UniqueConstraint("guide_ref", "guide_revision", name="uq_svg_guide_revision"),
    sa.CheckConstraint("guide_revision > 0", name="ck_svg_guide_revision_positive"),
    sa.CheckConstraint("length(source_sha256) = 64 AND length(guide_sha256) = 64", name="ck_svg_guide_hashes"),
    sa.CheckConstraint("schema_version = 'SketchStrokeGuideV3'", name="ck_svg_guide_schema"),
    sa.CheckConstraint("visibility_scope IN ('PLATFORM','ORGANIZATION')", name="ck_svg_guide_scope"),
    sa.CheckConstraint(
        "(visibility_scope = 'PLATFORM' AND organization_id IS NULL) OR "
        "(visibility_scope = 'ORGANIZATION' AND organization_id IS NOT NULL AND length(organization_id) > 0)",
        name="ck_svg_guide_scope_owner",
    ),
    sa.CheckConstraint("octet_length(guide_json::text) <= 262144", name="ck_svg_guide_json_size"),
    sa.ForeignKeyConstraint(
        ["asset_ref", "asset_version"],
        ["core_svg_catalog_assets.asset_ref", "core_svg_catalog_assets.asset_version"],
        ondelete="RESTRICT",
        name="fk_svg_guide_catalog_asset",
    ),
    sa.Index("ix_svg_guide_asset_scope_created", "asset_ref", "asset_version", "visibility_scope", "organization_id", "created_at"),
)

SVG_CATALOG_REVIEWS = sa.Table(
    "core_svg_catalog_reviews",
    METADATA,
    sa.Column("review_id", sa.String(36), primary_key=True),
    sa.Column("asset_ref", sa.String(256), nullable=False),
    sa.Column("asset_version", sa.Integer(), nullable=False),
    sa.Column("guide_revision_id", sa.String(36)),
    sa.Column("review_subject_kind", sa.String(16), nullable=False),
    sa.Column("review_kind", sa.String(16), nullable=False),
    sa.Column("source_sha256", sa.String(64), nullable=False),
    sa.Column("guide_sha256", sa.String(64)),
    sa.Column("reviewer_ref", sa.String(256), nullable=False),
    sa.Column("decision", sa.String(16), nullable=False),
    sa.Column("grouping_allowed", sa.Boolean(), nullable=False, server_default=sa.false()),
    sa.Column("reason", sa.String(1000)),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    sa.CheckConstraint("review_subject_kind IN ('SOURCE_ASSET','GUIDE')", name="ck_svg_review_subject"),
    sa.CheckConstraint("review_kind IN ('EDUCATOR','CURATOR')", name="ck_svg_review_kind"),
    sa.CheckConstraint("decision IN ('APPROVE','REJECT')", name="ck_svg_review_decision"),
    sa.CheckConstraint("length(source_sha256) = 64", name="ck_svg_review_source_hash"),
    sa.CheckConstraint("guide_sha256 IS NULL OR length(guide_sha256) = 64", name="ck_svg_review_guide_hash"),
    sa.CheckConstraint(
        "(review_subject_kind = 'SOURCE_ASSET' AND guide_revision_id IS NULL AND guide_sha256 IS NULL) OR "
        "(review_subject_kind = 'GUIDE' AND guide_revision_id IS NOT NULL AND guide_sha256 IS NOT NULL)",
        name="ck_svg_review_subject_fields",
    ),
    sa.CheckConstraint("NOT grouping_allowed OR (review_kind = 'CURATOR' AND decision = 'APPROVE')", name="ck_svg_review_grouping"),
    sa.ForeignKeyConstraint(
        ["asset_ref", "asset_version"],
        ["core_svg_catalog_assets.asset_ref", "core_svg_catalog_assets.asset_version"],
        ondelete="RESTRICT",
        name="fk_svg_review_catalog_asset",
    ),
    sa.ForeignKeyConstraint(
        ["guide_revision_id"],
        ["core_svg_catalog_guide_revisions.guide_revision_id"],
        ondelete="RESTRICT",
        name="fk_svg_review_guide_revision",
    ),
    sa.Index("ix_svg_review_exact_source", "asset_ref", "asset_version", "review_subject_kind", "review_kind", "source_sha256", "created_at"),
    sa.Index("ix_svg_review_exact_guide", "guide_revision_id", "review_kind", "guide_sha256", "created_at"),
)


__all__ = [
    "CORE_ASSET_LINEAGE",
    "SVG_CATALOG_ASSETS",
    "SVG_CATALOG_GUIDE_REVISIONS",
    "SVG_CATALOG_REVIEWS",
]
