"""Durable BE1 runtime records. Every child-owned record carries an organization scope."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from sketch2life.infrastructure.persistence.core_models import CorePersistenceBase


class OrganizationModel(CorePersistenceBase):
    __tablename__ = "be1_organizations"

    organization_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    state: Mapped[str] = mapped_column(String(24), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class AdultIdentityModel(CorePersistenceBase):
    __tablename__ = "be1_adult_identities"

    subject: Mapped[str] = mapped_column(String(256), primary_key=True)
    issuer: Mapped[str] = mapped_column(String(512), nullable=False)
    state: Mapped[str] = mapped_column(String(24), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class OrganizationAssignmentModel(CorePersistenceBase):
    __tablename__ = "be1_organization_assignments"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "subject", "class_id", "role", name="uq_be1_assignment"
        ),
        CheckConstraint(
            "role IN ('school_admin', 'teacher', 'guide', 'observer')",
            name="ck_be1_assignment_role",
        ),
        Index("ix_be1_assignment_subject", "subject", "organization_id"),
    )

    assignment_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    organization_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("be1_organizations.organization_id", ondelete="RESTRICT"),
        nullable=False,
    )
    subject: Mapped[str] = mapped_column(
        String(256), ForeignKey("be1_adult_identities.subject", ondelete="RESTRICT"), nullable=False
    )
    class_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ClassroomModel(CorePersistenceBase):
    __tablename__ = "be1_classrooms"
    __table_args__ = (
        UniqueConstraint("organization_id", "class_id", name="uq_be1_class_org"),
        Index("ix_be1_class_org_state", "organization_id", "state"),
    )

    class_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    organization_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("be1_organizations.organization_id", ondelete="RESTRICT"),
        nullable=False,
    )
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    state: Mapped[str] = mapped_column(String(24), nullable=False, default="active")
    created_by: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ManagedProfileModel(CorePersistenceBase):
    __tablename__ = "be1_managed_profiles"
    __table_args__ = (
        UniqueConstraint("organization_id", "child_id", name="uq_be1_profile_org_child"),
        CheckConstraint("age_months BETWEEN 36 AND 155", name="ck_be1_profile_age_months"),
        Index("ix_be1_profile_org_class", "organization_id", "class_id"),
    )

    child_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    organization_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("be1_organizations.organization_id", ondelete="RESTRICT"),
        nullable=False,
    )
    class_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("be1_classrooms.class_id", ondelete="RESTRICT"), nullable=False
    )
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    age_months: Mapped[int] = mapped_column(Integer, nullable=False)
    consent_id: Mapped[str] = mapped_column(String(36), nullable=False)
    consent_purpose_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    state: Mapped[str] = mapped_column(String(24), nullable=False, default="active")
    created_by: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class EnrollmentModel(CorePersistenceBase):
    __tablename__ = "be1_enrollments"
    __table_args__ = (
        UniqueConstraint("organization_id", "class_id", "child_id", name="uq_be1_enrollment"),
        CheckConstraint("state IN ('active', 'withdrawn')", name="ck_be1_enrollment_state"),
    )

    enrollment_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(128), nullable=False)
    class_id: Mapped[str] = mapped_column(String(128), nullable=False)
    child_id: Mapped[str] = mapped_column(String(128), nullable=False)
    state: Mapped[str] = mapped_column(String(24), nullable=False, default="active")
    created_by: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ConsentRecordModel(CorePersistenceBase):
    __tablename__ = "be1_consent_records"
    __table_args__ = (
        CheckConstraint("state IN ('pending', 'revoked')", name="ck_be1_consent_state"),
        Index("ix_be1_consent_child", "organization_id", "child_id", "state"),
    )

    consent_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(128), nullable=False)
    class_id: Mapped[str] = mapped_column(String(128), nullable=False)
    child_id: Mapped[str] = mapped_column(String(128), nullable=False)
    purpose_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    evidence_ref: Mapped[str | None] = mapped_column(String(512), nullable=True)
    state: Mapped[str] = mapped_column(String(24), nullable=False, default="pending")
    recorded_by: Mapped[str] = mapped_column(String(256), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    verification_note: Mapped[str | None] = mapped_column(Text, nullable=True)


class DeviceGrantModel(CorePersistenceBase):
    __tablename__ = "be1_device_grants"
    __table_args__ = (
        CheckConstraint(
            "state IN ('pending', 'admitted', 'revoked')", name="ck_be1_device_grant_state"
        ),
        Index("ix_be1_device_session_state", "organization_id", "session_id", "state"),
    )

    grant_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(128), nullable=False)
    session_id: Mapped[str] = mapped_column(String(128), nullable=False)
    device_key_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    state: Mapped[str] = mapped_column(String(24), nullable=False, default="pending")
    requested_by: Mapped[str] = mapped_column(String(256), nullable=False)
    admitted_child_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    admitted_by: Mapped[str | None] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ClassroomSessionModel(CorePersistenceBase):
    __tablename__ = "be1_sessions"
    __table_args__ = (
        CheckConstraint(
            "state IN ('configured', 'lobby', 'active', 'paused', 'finished')",
            name="ck_be1_session_state",
        ),
        CheckConstraint("revision > 0", name="ck_be1_session_revision"),
        Index("ix_be1_session_class_state", "organization_id", "class_id", "state"),
    )

    session_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(128), nullable=False)
    class_id: Mapped[str] = mapped_column(String(128), nullable=False)
    created_by: Mapped[str] = mapped_column(String(256), nullable=False)
    state: Mapped[str] = mapped_column(String(24), nullable=False, default="configured")
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    configuration: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    active_phase: Mapped[str] = mapped_column(String(64), nullable=False, default="lobby")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retain_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retention_enqueued_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __mapper_args__ = {"version_id_col": revision, "version_id_generator": False}


class SessionMembershipModel(CorePersistenceBase):
    __tablename__ = "be1_session_memberships"
    __table_args__ = (
        UniqueConstraint("organization_id", "session_id", "child_id", name="uq_be1_membership"),
        CheckConstraint(
            "state IN ('join_pending', 'admitted', 'left', 'removed')",
            name="ck_be1_membership_state",
        ),
        Index("ix_be1_membership_session", "organization_id", "session_id", "state"),
    )

    membership_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(128), nullable=False)
    session_id: Mapped[str] = mapped_column(String(128), nullable=False)
    class_id: Mapped[str] = mapped_column(String(128), nullable=False)
    child_id: Mapped[str] = mapped_column(String(128), nullable=False)
    state: Mapped[str] = mapped_column(String(24), nullable=False, default="join_pending")
    group_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    device_grant_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    progress: Mapped[str] = mapped_column(String(32), nullable=False, default="not_started")
    help_requested: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    admitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SessionGroupModel(CorePersistenceBase):
    __tablename__ = "be1_session_groups"
    __table_args__ = (
        UniqueConstraint("organization_id", "session_id", "group_id", name="uq_be1_group"),
        CheckConstraint("state IN ('active', 'locked', 'archived')", name="ck_be1_group_state"),
    )

    group_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(128), nullable=False)
    session_id: Mapped[str] = mapped_column(String(128), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    state: Mapped[str] = mapped_column(String(24), nullable=False, default="active")
    created_by: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ChildTurnModel(CorePersistenceBase):
    __tablename__ = "be1_child_turns"
    __table_args__ = (
        CheckConstraint("document_epoch > 0", name="ck_be1_turn_epoch"),
        CheckConstraint("state IN ('active', 'closed', 'revoked')", name="ck_be1_turn_state"),
        Index("ix_be1_turn_session_state", "organization_id", "session_id", "state"),
    )

    turn_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(128), nullable=False)
    session_id: Mapped[str] = mapped_column(String(128), nullable=False)
    child_id: Mapped[str] = mapped_column(String(128), nullable=False)
    group_id: Mapped[str] = mapped_column(String(128), nullable=False)
    canvas_id: Mapped[str] = mapped_column(String(128), nullable=False)
    document_epoch: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    device_grant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    state: Mapped[str] = mapped_column(String(24), nullable=False, default="active")
    created_by: Mapped[str] = mapped_column(String(256), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class GallerySnapshotModel(CorePersistenceBase):
    __tablename__ = "be1_gallery_snapshots"
    __table_args__ = (
        CheckConstraint("state IN ('draft', 'published', 'recalled')", name="ck_be1_gallery_state"),
        Index("ix_be1_gallery_org_state", "organization_id", "state"),
    )

    gallery_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(128), nullable=False)
    session_id: Mapped[str] = mapped_column(String(128), nullable=False)
    artifact_ref: Mapped[str] = mapped_column(String(256), nullable=False)
    audience: Mapped[str] = mapped_column(String(64), nullable=False)
    contributor_refs: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    caption: Mapped[str | None] = mapped_column(String(500), nullable=True)
    annotations: Mapped[list[dict[str, str]]] = mapped_column(JSONB, nullable=False, default=list)
    state: Mapped[str] = mapped_column(String(24), nullable=False, default="draft")
    created_by: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ObservationModel(CorePersistenceBase):
    __tablename__ = "be1_observations"
    __table_args__ = (
        Index("ix_be1_observation_child", "organization_id", "child_id", "created_at"),
    )

    observation_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(128), nullable=False)
    session_id: Mapped[str] = mapped_column(String(128), nullable=False)
    child_id: Mapped[str] = mapped_column(String(128), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    source_refs: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    created_by: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class DataLifecycleRequestModel(CorePersistenceBase):
    __tablename__ = "be1_data_lifecycle_requests"
    __table_args__ = (
        CheckConstraint(
            "state IN ('requested', 'running', 'awaiting_external_purge', "
            "'completed', 'exception')",
            name="ck_be1_data_request_state",
        ),
        CheckConstraint("unresolved_items >= 0", name="ck_be1_data_request_unresolved"),
        Index("ix_be1_data_request_org_state", "organization_id", "state"),
    )

    request_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(128), nullable=False)
    request_type: Mapped[str] = mapped_column(String(24), nullable=False)
    target_ref: Mapped[str] = mapped_column(String(256), nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False, default="requested")
    unresolved_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    result_ref: Mapped[str | None] = mapped_column(String(512), nullable=True)
    requested_by: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


__all__ = [
    "AdultIdentityModel",
    "ChildTurnModel",
    "ClassroomModel",
    "ClassroomSessionModel",
    "ConsentRecordModel",
    "DataLifecycleRequestModel",
    "DeviceGrantModel",
    "EnrollmentModel",
    "GallerySnapshotModel",
    "ManagedProfileModel",
    "ObservationModel",
    "OrganizationAssignmentModel",
    "OrganizationModel",
    "SessionGroupModel",
    "SessionMembershipModel",
]
