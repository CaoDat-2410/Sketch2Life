"""Persistence mappings for Parent-owned profiles and data authorizations."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from sketch2life.infrastructure.persistence.core_models import CorePersistenceBase


class ParentChildProfileModel(CorePersistenceBase):
    __tablename__ = "child_profiles"
    __table_args__ = (
        CheckConstraint(
            "state IN ('ACTIVE', 'ARCHIVED', 'DELETED')",
            name="ck_parent_child_profile_state",
        ),
        UniqueConstraint(
            "parent_profile_id", "owner_subject", name="uq_parent_profile_owner_ref"
        ),
        ForeignKeyConstraint(
            ["parent_profile_id", "current_revision_ref"],
            ["parent.profile_revisions.parent_profile_id", "parent.profile_revisions.profile_revision_id"],
            name="fk_parent_profile_current_revision",
            use_alter=True,
        ),
        Index("ix_parent_profile_owner_state_updated", "owner_subject", "state", "updated_at"),
        {"schema": "parent"},
    )

    parent_profile_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_subject: Mapped[str] = mapped_column(String(256), nullable=False)
    state: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'ACTIVE'")
    )
    current_revision_ref: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ParentProfileRevisionModel(CorePersistenceBase):
    __tablename__ = "profile_revisions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["parent_profile_id"],
            ["parent.child_profiles.parent_profile_id"],
            ondelete="RESTRICT",
            name="fk_parent_profile_revision_profile",
        ),
        CheckConstraint(
            "age_months BETWEEN 36 AND 120", name="ck_parent_profile_revision_age_months"
        ),
        CheckConstraint("revision_no > 0", name="ck_parent_profile_revision_no"),
        CheckConstraint(
            "length(trim(display_name)) BETWEEN 1 AND 120",
            name="ck_parent_profile_revision_display_name",
        ),
        CheckConstraint(
            "length(interests_summary) <= 800",
            name="ck_parent_profile_revision_interests_length",
        ),
        CheckConstraint(
            "length(revision_hash) = 64", name="ck_parent_profile_revision_hash"
        ),
        UniqueConstraint(
            "parent_profile_id", "revision_no", name="uq_parent_profile_revision_no"
        ),
        UniqueConstraint(
            "parent_profile_id", "profile_revision_id", name="uq_parent_profile_revision_owner"
        ),
        {"schema": "parent"},
    )

    profile_revision_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    parent_profile_id: Mapped[str] = mapped_column(String(36), nullable=False)
    revision_no: Mapped[int] = mapped_column(Integer, nullable=False)
    age_months: Mapped[int] = mapped_column(Integer, nullable=False)
    age_band_ref: Mapped[str | None] = mapped_column(String(80), nullable=True)
    age_band_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    interests_summary: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    authored_by: Mapped[str] = mapped_column(String(256), nullable=False)
    revision_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ParentDataAuthorizationModel(CorePersistenceBase):
    __tablename__ = "data_authorizations"
    __table_args__ = (
        ForeignKeyConstraint(
            ["parent_profile_id"],
            ["parent.child_profiles.parent_profile_id"],
            ondelete="RESTRICT",
            name="fk_parent_authorization_profile",
        ),
        CheckConstraint(
            "purpose_code = 'PARENT_STORY_PERSONALIZATION'",
            name="ck_parent_authorization_purpose",
        ),
        CheckConstraint(
            "state IN ('GRANTED', 'REVOKED', 'EXPIRED')",
            name="ck_parent_authorization_state",
        ),
        CheckConstraint(
            "length(policy_version) BETWEEN 1 AND 80",
            name="ck_parent_authorization_policy_version",
        ),
        CheckConstraint(
            "length(evidence_ref) = 64", name="ck_parent_authorization_evidence_hash"
        ),
        Index(
            "uq_parent_authorization_active_policy",
            "parent_profile_id",
            "purpose_code",
            "policy_version",
            unique=True,
            postgresql_where=text("state = 'GRANTED'"),
        ),
        Index("ix_parent_authorization_profile_state", "parent_profile_id", "state"),
        {"schema": "parent"},
    )

    authorization_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    parent_profile_id: Mapped[str] = mapped_column(String(36), nullable=False)
    actor_subject: Mapped[str] = mapped_column(String(256), nullable=False)
    purpose_code: Mapped[str] = mapped_column(
        String(64), nullable=False, server_default=text("'PARENT_STORY_PERSONALIZATION'")
    )
    policy_version: Mapped[str] = mapped_column(String(80), nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False)
    source_kind: Mapped[str] = mapped_column(String(48), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    evidence_ref: Mapped[str] = mapped_column(String(64), nullable=False)
    synthetic_demo_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))


__all__ = [
    "ParentChildProfileModel",
    "ParentDataAuthorizationModel",
    "ParentProfileRevisionModel",
]
