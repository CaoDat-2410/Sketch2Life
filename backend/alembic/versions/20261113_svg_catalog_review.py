"""Add provenance-bound SVG catalog, guide revisions, and append-only review decisions."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20261113_svg_catalog_review"
down_revision = "20261110_parent_lesson_pin"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("ck_core_asset_owner_scope", "core_asset_metadata", type_="check")
    op.create_check_constraint(
        "ck_core_asset_owner_scope",
        "core_asset_metadata",
        "(owner_scope_kind = 'PARENT_ACCOUNT' AND owner_scope_ref IS NOT NULL "
        "AND length(owner_scope_ref) > 0 AND organization_id IS NULL) OR "
        "(owner_scope_kind = 'ORGANIZATION' AND organization_id IS NOT NULL AND "
        "(owner_scope_ref IS NULL OR (length(owner_scope_ref) > 0 AND owner_scope_ref = organization_id))) OR "
        "(owner_scope_kind = 'PLATFORM' AND organization_id IS NULL "
        "AND owner_scope_ref IS NOT NULL AND owner_scope_ref = 'PLATFORM')",
    )
    op.execute(
        sa.text(
            """
            CREATE OR REPLACE FUNCTION core_asset_metadata_owner_scope_guard()
            RETURNS trigger AS $$
            BEGIN
              IF NEW.owner_scope_kind = 'ORGANIZATION' THEN
                IF NEW.organization_id IS NULL THEN
                  RAISE EXCEPTION 'organization asset scope must match organization_id'
                    USING ERRCODE = '23514';
                END IF;
                IF NEW.owner_scope_ref IS NULL OR length(NEW.owner_scope_ref) = 0 THEN
                  IF TG_OP = 'UPDATE' AND OLD.owner_scope_kind = 'ORGANIZATION'
                    AND OLD.owner_scope_ref IS NULL AND OLD.organization_id = NEW.organization_id THEN
                    RETURN NEW;
                  END IF;
                  RAISE EXCEPTION 'new organization asset rows require owner_scope_ref'
                    USING ERRCODE = '23514';
                END IF;
                IF NEW.owner_scope_ref <> NEW.organization_id THEN
                  RAISE EXCEPTION 'organization asset scope must match organization_id'
                    USING ERRCODE = '23514';
                END IF;
              ELSIF NEW.owner_scope_kind = 'PARENT_ACCOUNT' THEN
                IF NEW.organization_id IS NOT NULL OR NEW.owner_scope_ref IS NULL
                  OR length(NEW.owner_scope_ref) = 0 THEN
                  RAISE EXCEPTION 'Parent scope requires a typed ref and no organization_id'
                    USING ERRCODE = '23514';
                END IF;
              ELSIF NEW.owner_scope_kind = 'PLATFORM' THEN
                IF NEW.organization_id IS NOT NULL OR NEW.owner_scope_ref IS NULL
                  OR NEW.owner_scope_ref <> 'PLATFORM' THEN
                  RAISE EXCEPTION 'Platform scope requires PLATFORM ref and no organization_id'
                    USING ERRCODE = '23514';
                END IF;
              ELSE
                RAISE EXCEPTION 'unsupported asset owner scope kind' USING ERRCODE = '23514';
              END IF;
              RETURN NEW;
            END;
            $$ LANGUAGE plpgsql
            """
        )
    )

    op.create_table(
        "core_svg_catalog_assets",
        sa.Column("asset_ref", sa.String(256), nullable=False),
        sa.Column("asset_version", sa.Integer(), nullable=False),
        sa.Column("catalog_entry_id", sa.String(36), nullable=False),
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
        sa.Column("structural_facts", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("catalog_state", sa.String(24), server_default=sa.text("'ACTIVE'"), nullable=False),
        sa.Column("created_by", sa.String(256), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("asset_ref", "asset_version", name="pk_core_svg_catalog_assets"),
        sa.UniqueConstraint("catalog_entry_id", name="uq_svg_catalog_entry"),
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
    )
    op.create_index(
        "ix_svg_catalog_scope_topic_state",
        "core_svg_catalog_assets",
        ["visibility_scope", "organization_id", "topic_key", "catalog_state"],
    )

    op.create_table(
        "core_svg_catalog_guide_revisions",
        sa.Column("guide_revision_id", sa.String(36), nullable=False),
        sa.Column("guide_ref", sa.String(256), nullable=False),
        sa.Column("guide_revision", sa.Integer(), nullable=False),
        sa.Column("asset_ref", sa.String(256), nullable=False),
        sa.Column("asset_version", sa.Integer(), nullable=False),
        sa.Column("visibility_scope", sa.String(16), nullable=False),
        sa.Column("organization_id", sa.String(128)),
        sa.Column("source_sha256", sa.String(64), nullable=False),
        sa.Column("guide_sha256", sa.String(64), nullable=False),
        sa.Column("schema_version", sa.String(48), nullable=False),
        sa.Column("guide_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("authored_by", sa.String(256), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("guide_revision_id", name="pk_core_svg_catalog_guide_revisions"),
        sa.UniqueConstraint("guide_ref", "guide_revision", name="uq_svg_guide_revision"),
        sa.ForeignKeyConstraint(
            ["asset_ref", "asset_version"],
            ["core_svg_catalog_assets.asset_ref", "core_svg_catalog_assets.asset_version"],
            ondelete="RESTRICT",
            name="fk_svg_guide_catalog_asset",
        ),
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
    )
    op.create_index(
        "ix_svg_guide_asset_scope_created",
        "core_svg_catalog_guide_revisions",
        ["asset_ref", "asset_version", "visibility_scope", "organization_id", "created_at"],
    )

    op.create_table(
        "core_svg_catalog_reviews",
        sa.Column("review_id", sa.String(36), nullable=False),
        sa.Column("asset_ref", sa.String(256), nullable=False),
        sa.Column("asset_version", sa.Integer(), nullable=False),
        sa.Column("guide_revision_id", sa.String(36)),
        sa.Column("review_subject_kind", sa.String(16), nullable=False),
        sa.Column("review_kind", sa.String(16), nullable=False),
        sa.Column("source_sha256", sa.String(64), nullable=False),
        sa.Column("guide_sha256", sa.String(64)),
        sa.Column("reviewer_ref", sa.String(256), nullable=False),
        sa.Column("decision", sa.String(16), nullable=False),
        sa.Column("grouping_allowed", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("reason", sa.String(1000)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("review_id", name="pk_core_svg_catalog_reviews"),
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
    )
    op.create_index(
        "ix_svg_review_exact_source",
        "core_svg_catalog_reviews",
        ["asset_ref", "asset_version", "review_subject_kind", "review_kind", "source_sha256", "created_at"],
    )
    op.create_index(
        "ix_svg_review_exact_guide",
        "core_svg_catalog_reviews",
        ["guide_revision_id", "review_kind", "guide_sha256", "created_at"],
    )
    op.execute(
        sa.text(
            """
            CREATE OR REPLACE FUNCTION core_svg_catalog_immutable_row_guard()
            RETURNS trigger AS $$
            BEGIN
              RAISE EXCEPTION '% rows are immutable', TG_TABLE_NAME
                USING ERRCODE = '55000';
            END;
            $$ LANGUAGE plpgsql
            """
        )
    )
    for table_name in ("core_svg_catalog_guide_revisions", "core_svg_catalog_reviews"):
        op.execute(
            sa.text(
                f"CREATE TRIGGER trg_{table_name}_immutable "
                f"BEFORE UPDATE OR DELETE ON {table_name} "
                "FOR EACH ROW EXECUTE FUNCTION core_svg_catalog_immutable_row_guard()"
            )
        )


def downgrade() -> None:
    has_catalog_or_platform_assets = op.get_bind().execute(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM core_asset_metadata WHERE owner_scope_kind = 'PLATFORM') "
            "OR EXISTS (SELECT 1 FROM core_svg_catalog_assets)"
        )
    ).scalar_one()
    if has_catalog_or_platform_assets:
        raise RuntimeError(
            "Cannot downgrade SVG catalog migration while catalog assets or Core PLATFORM assets exist; "
            "remove/migrate those records through an approved data-retention procedure first."
        )

    op.execute(sa.text("DROP TRIGGER trg_core_svg_catalog_reviews_immutable ON core_svg_catalog_reviews"))
    op.execute(sa.text("DROP TRIGGER trg_core_svg_catalog_guide_revisions_immutable ON core_svg_catalog_guide_revisions"))
    op.execute(sa.text("DROP FUNCTION core_svg_catalog_immutable_row_guard()"))
    op.drop_index("ix_svg_review_exact_guide", table_name="core_svg_catalog_reviews")
    op.drop_index("ix_svg_review_exact_source", table_name="core_svg_catalog_reviews")
    op.drop_table("core_svg_catalog_reviews")
    op.drop_index("ix_svg_guide_asset_scope_created", table_name="core_svg_catalog_guide_revisions")
    op.drop_table("core_svg_catalog_guide_revisions")
    op.drop_index("ix_svg_catalog_scope_topic_state", table_name="core_svg_catalog_assets")
    op.drop_table("core_svg_catalog_assets")
    op.drop_constraint("ck_core_asset_owner_scope", "core_asset_metadata", type_="check")
    op.create_check_constraint(
        "ck_core_asset_owner_scope",
        "core_asset_metadata",
        "(owner_scope_kind = 'PARENT_ACCOUNT' AND owner_scope_ref IS NOT NULL "
        "AND length(owner_scope_ref) > 0 AND organization_id IS NULL) OR "
        "(owner_scope_kind = 'ORGANIZATION' AND organization_id IS NOT NULL AND "
        "(owner_scope_ref IS NULL OR (length(owner_scope_ref) > 0 AND owner_scope_ref = organization_id)))",
    )
    op.execute(
        sa.text(
            """
            CREATE OR REPLACE FUNCTION core_asset_metadata_owner_scope_guard()
            RETURNS trigger AS $$
            BEGIN
              IF NEW.owner_scope_kind = 'ORGANIZATION' THEN
                IF NEW.organization_id IS NULL THEN
                  RAISE EXCEPTION 'organization asset scope requires organization_id' USING ERRCODE = '23514';
                END IF;
                IF NEW.owner_scope_ref IS NULL OR length(NEW.owner_scope_ref) = 0 THEN
                  IF TG_OP = 'UPDATE' AND OLD.owner_scope_kind = 'ORGANIZATION'
                    AND OLD.owner_scope_ref IS NULL AND OLD.organization_id = NEW.organization_id THEN
                    RETURN NEW;
                  END IF;
                  RAISE EXCEPTION 'new organization asset rows require owner_scope_ref' USING ERRCODE = '23514';
                END IF;
                IF NEW.owner_scope_ref <> NEW.organization_id THEN
                  RAISE EXCEPTION 'organization owner scope must match organization_id' USING ERRCODE = '23514';
                END IF;
              ELSIF NEW.owner_scope_kind = 'PARENT_ACCOUNT' THEN
                IF NEW.organization_id IS NOT NULL OR NEW.owner_scope_ref IS NULL
                  OR length(NEW.owner_scope_ref) = 0 THEN
                  RAISE EXCEPTION 'Parent scope requires a typed ref and no organization_id' USING ERRCODE = '23514';
                END IF;
              ELSE
                RAISE EXCEPTION 'unsupported asset owner scope kind' USING ERRCODE = '23514';
              END IF;
              RETURN NEW;
            END;
            $$ LANGUAGE plpgsql
            """
        )
    )
