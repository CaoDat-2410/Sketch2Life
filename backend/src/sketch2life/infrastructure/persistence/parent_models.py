"""Parent-owned persistence metadata, isolated from Core and BE1 tables."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKeyConstraint,
    Index,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import BYTEA, JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class ParentPersistenceBase(DeclarativeBase):
    """Metadata for tables owned by the Parent profile module."""


class ParentChildProfileModel(ParentPersistenceBase):
    __tablename__ = "child_profiles"
    __table_args__ = (
        CheckConstraint(
            "current_revision_no > 0",
            name="ck_parent_child_profiles_current_revision_no_positive",
        ),
        CheckConstraint(
            "data_origin = 'SYNTHETIC_DEV'",
            name="ck_parent_child_profiles_data_origin_synthetic_dev",
        ),
        ForeignKeyConstraint(
            ["parent_profile_id", "current_revision_no"],
            ["parent.profile_revisions.parent_profile_id", "parent.profile_revisions.revision_no"],
            name="fk_parent_child_profiles_current_revision",
            deferrable=True,
            initially="DEFERRED",
        ),
        {"schema": "parent"},
    )

    parent_profile_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, name="parent_profile_id"
    )
    owner_issuer: Mapped[str] = mapped_column(Text, nullable=False)
    owner_subject: Mapped[str] = mapped_column(Text, nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False, server_default=text("'ACTIVE'"))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    current_revision_no: Mapped[int] = mapped_column(BigInteger, nullable=False)
    data_origin: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default=text("'SYNTHETIC_DEV'")
    )


class ParentProfileRevisionModel(ParentPersistenceBase):
    __tablename__ = "profile_revisions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["parent_profile_id"],
            ["parent.child_profiles.parent_profile_id"],
            name="fk_parent_profile_revisions_parent_profile",
            ondelete="RESTRICT",
        ),
        CheckConstraint("revision_no > 0", name="ck_parent_profile_revisions_revision_no_positive"),
        UniqueConstraint(
            "parent_profile_id",
            "revision_no",
            name="uq_parent_profile_revisions_parent_revision_no",
        ),
        CheckConstraint(
            "age_months BETWEEN 36 AND 120",
            name="ck_parent_profile_revisions_age_months_36_120",
        ),
        CheckConstraint(
            "(age_band_ref IS NULL AND age_band_version IS NULL) OR "
            "(age_band_ref IS NOT NULL AND age_band_version IS NOT NULL)",
            name="ck_parent_profile_revisions_age_band_pair",
        ),
        CheckConstraint(
            "revision_hash ~ '^[0-9a-f]{64}$'",
            name="ck_parent_profile_revisions_revision_hash_sha256",
        ),
        {"schema": "parent"},
    )

    profile_revision_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, name="profile_revision_id"
    )
    parent_profile_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    revision_no: Mapped[int] = mapped_column(BigInteger, nullable=False)
    age_months: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    age_band_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    age_band_version: Mapped[str | None] = mapped_column(Text, nullable=True)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    interests_summary: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    authored_by_issuer: Mapped[str] = mapped_column(Text, nullable=False)
    authored_by_subject: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    revision_hash: Mapped[str] = mapped_column(String(64), nullable=False)


class ParentDataAuthorizationModel(ParentPersistenceBase):
    """Versioned authorization record referenced by Parent Story inputs and sharing."""

    __tablename__ = "data_authorizations"
    __table_args__ = (
        ForeignKeyConstraint(
            ["parent_profile_id"],
            ["parent.child_profiles.parent_profile_id"],
            name="fk_parent_authorization_profile",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "purpose_code = 'PARENT_STORY_PERSONALIZATION'",
            name="ck_parent_authorization_purpose",
        ),
        CheckConstraint(
            "state IN ('GRANTED','REVOKED','EXPIRED')",
            name="ck_parent_authorization_state",
        ),
        CheckConstraint(
            "length(policy_version) BETWEEN 1 AND 80",
            name="ck_parent_authorization_policy_version",
        ),
        CheckConstraint(
            "length(evidence_ref) = 64",
            name="ck_parent_authorization_evidence_hash",
        ),
        Index(
            "uq_parent_authorization_active_policy",
            "parent_profile_id",
            "purpose_code",
            "policy_version",
            unique=True,
            postgresql_where=text("state = 'GRANTED'"),
        ),
        Index(
            "ix_parent_authorization_profile_state",
            "parent_profile_id",
            "state",
        ),
        {"schema": "parent"},
    )

    authorization_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    parent_profile_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
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
    synthetic_demo_flag: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )


class ParentConsentPolicyModel(ParentPersistenceBase):
    """Platform-managed consent policy text and activation metadata."""

    __tablename__ = "consent_policies"
    __table_args__ = (
        CheckConstraint(
            "state IN ('DRAFT', 'ACTIVE', 'RETIRED')",
            name="ck_parent_consent_policy_state",
        ),
        CheckConstraint(
            "purpose_code = 'PARENT_STORY_PERSONALIZATION'",
            name="ck_parent_consent_policy_purpose",
        ),
        CheckConstraint(
            "length(trim(consent_text)) BETWEEN 1 AND 4000",
            name="ck_parent_consent_policy_text_length",
        ),
        CheckConstraint(
            "length(consent_text_sha256) = 64",
            name="ck_parent_consent_policy_text_sha256",
        ),
        UniqueConstraint("policy_version", name="uq_parent_consent_policy_version"),
        Index(
            "uq_parent_consent_policy_one_active",
            "state",
            unique=True,
            postgresql_where=text("state = 'ACTIVE'"),
        ),
        Index("ix_parent_consent_policy_state_created", "state", "created_at"),
        {"schema": "parent"},
    )

    policy_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    policy_version: Mapped[str] = mapped_column(String(80), nullable=False)
    purpose_code: Mapped[str] = mapped_column(String(80), nullable=False)
    consent_text: Mapped[str] = mapped_column(Text, nullable=False)
    consent_text_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False, server_default=text("'DRAFT'"))
    created_by: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    activated_by: Mapped[str | None] = mapped_column(String(256), nullable=True)
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ParentCommandReceiptModel(ParentPersistenceBase):
    __tablename__ = "command_receipts"
    __table_args__ = (
        CheckConstraint(
            "octet_length(key_hash) = 32", name="ck_parent_command_receipts_key_hash_len"
        ),
        CheckConstraint(
            "octet_length(request_fingerprint) = 32",
            name="ck_parent_command_receipts_fingerprint_len",
        ),
        UniqueConstraint(
            "principal_issuer",
            "principal_subject",
            "operation_scope",
            "resource_scope",
            "key_hash",
            name="uq_parent_command_receipts_scope_key",
        ),
        Index(
            "ix_parent_command_receipts_owner_created_at",
            "principal_issuer",
            "principal_subject",
            "created_at",
        ),
        {"schema": "parent"},
    )

    receipt_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    principal_issuer: Mapped[str] = mapped_column(Text, nullable=False)
    principal_subject: Mapped[str] = mapped_column(Text, nullable=False)
    operation_scope: Mapped[str] = mapped_column(Text, nullable=False)
    resource_scope: Mapped[str] = mapped_column(Text, nullable=False)
    key_hash: Mapped[bytes] = mapped_column(BYTEA, nullable=False)
    request_fingerprint: Mapped[bytes] = mapped_column(BYTEA, nullable=False)
    response_status: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    response_body: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ParentProfileContextEntryModel(ParentPersistenceBase):
    """T-12a: an adult-entered, append-only entry of a stable profile (DDL-D, ``pce_0001``)."""

    __tablename__ = "profile_context_entries"
    __table_args__ = (
        ForeignKeyConstraint(
            ["parent_profile_id"],
            ["parent.child_profiles.parent_profile_id"],
            name="fk_parent_profile_context_entries_profile",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "entry_kind IN ('OBSERVATION','ACHIEVEMENT','OUTSIDE_EXPERIENCE')",
            name="ck_parent_profile_context_entries_kind",
        ),
        CheckConstraint(
            "char_length(btrim(short_text)) BETWEEN 1 AND 500 "
            "AND octet_length(short_text) <= 2000 "
            "AND short_text !~ '[\\x01-\\x08\\x0b-\\x1f\\x7f]'",
            name="ck_parent_profile_context_entries_text",
        ),
        CheckConstraint(
            "source_kind ~ '^[A-Z][A-Z0-9_]{0,31}$'",
            name="ck_parent_profile_context_entries_source_kind",
        ),
        CheckConstraint(
            "source_ref IS NULL OR (char_length(btrim(source_ref)) BETWEEN 1 AND 256 "
            "AND source_ref !~ '[\\x01-\\x1f\\x7f]')",
            name="ck_parent_profile_context_entries_source_ref",
        ),
        CheckConstraint(
            "char_length(created_by) BETWEEN 1 AND 256",
            name="ck_parent_profile_context_entries_created_by",
        ),
        Index(
            "ix_parent_profile_context_entries_page",
            "parent_profile_id",
            "created_at",
            "context_entry_id",
        ),
        {"schema": "parent"},
    )

    context_entry_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    parent_profile_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    entry_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    short_text: Mapped[str] = mapped_column(String(500), nullable=False)
    source_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    source_ref: Mapped[str | None] = mapped_column(String(256), nullable=True)
    approximate_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_by: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ParentProfileSupportNeedsModel(ParentPersistenceBase):
    """T-12c: the encrypted support needs of a stable profile (DDL-D, ``psn_0001``).

    A singleton current record. ``ciphertext`` holds the category and the note (AES-256-GCM, the
    authentication tag included); no column holds a value in the clear. A trigger refuses a
    DELETE and any UPDATE that does not raise the revision by exactly one.
    """

    __tablename__ = "profile_support_needs"
    __table_args__ = (
        ForeignKeyConstraint(
            ["parent_profile_id"],
            ["parent.child_profiles.parent_profile_id"],
            name="fk_parent_profile_support_needs_profile",
            ondelete="RESTRICT",
        ),
        CheckConstraint("revision >= 1", name="ck_parent_profile_support_needs_revision"),
        CheckConstraint(
            "octet_length(ciphertext) BETWEEN 16 AND 16384",
            name="ck_parent_profile_support_needs_ciphertext",
        ),
        CheckConstraint("octet_length(nonce) = 12", name="ck_parent_profile_support_needs_nonce"),
        CheckConstraint(
            "char_length(key_id) BETWEEN 1 AND 128", name="ck_parent_profile_support_needs_key_id"
        ),
        CheckConstraint("algorithm_version = 1", name="ck_parent_profile_support_needs_algorithm"),
        UniqueConstraint("key_id", "nonce", name="uq_parent_profile_support_needs_key_nonce"),
        {"schema": "parent"},
    )

    parent_profile_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    revision: Mapped[int] = mapped_column(BigInteger, nullable=False)
    ciphertext: Mapped[bytes] = mapped_column(BYTEA, nullable=False)
    nonce: Mapped[bytes] = mapped_column(BYTEA, nullable=False)
    key_id: Mapped[str] = mapped_column(String(128), nullable=False)
    algorithm_version: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ParentTopicRotationStateModel(ParentPersistenceBase):
    """The ordered, privacy-minimal card cycle for one Parent account and scope."""

    __tablename__ = "topic_rotation_states"
    __table_args__ = (
        UniqueConstraint(
            "account_id",
            "catalog_revision",
            "rotation_kind",
            "scope_id",
            name="uq_parent_topic_rotation_state_scope",
        ),
        CheckConstraint(
            "rotation_kind IN ('TOPIC', 'SUBJECT')", name="ck_parent_topic_rotation_kind"
        ),
        CheckConstraint("cycle_number >= 1", name="ck_parent_topic_rotation_cycle"),
        CheckConstraint("cursor_position >= 0", name="ck_parent_topic_rotation_cursor"),
        CheckConstraint(
            "jsonb_typeof(ordered_ids) = 'array' AND octet_length(ordered_ids::text) <= 8192",
            name="ck_parent_topic_rotation_ordered_ids",
        ),
        Index(
            "ix_parent_topic_rotation_account_updated",
            "account_id",
            "updated_at",
        ),
        {"schema": "parent"},
    )

    rotation_state_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    account_id: Mapped[str] = mapped_column(String(36), nullable=False)
    catalog_revision: Mapped[str] = mapped_column(String(80), nullable=False)
    rotation_kind: Mapped[str] = mapped_column(String(12), nullable=False)
    scope_id: Mapped[str] = mapped_column(String(64), nullable=False)
    ordered_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    cycle_number: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("1"))
    cursor_position: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default=text("0")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ParentTopicRotationReceiptModel(ParentPersistenceBase):
    """Idempotent response receipt; contains catalog IDs, never user-entered text."""

    __tablename__ = "topic_rotation_receipts"
    __table_args__ = (
        UniqueConstraint(
            "account_id", "request_id", name="uq_parent_topic_rotation_receipt_request"
        ),
        CheckConstraint(
            "octet_length(request_fingerprint) = 32", name="ck_parent_topic_rotation_fingerprint"
        ),
        CheckConstraint(
            "jsonb_typeof(selected_ids) = 'array' AND octet_length(selected_ids::text) <= 2048",
            name="ck_parent_topic_rotation_selected_ids",
        ),
        Index("ix_parent_topic_rotation_receipt_created", "created_at"),
        {"schema": "parent"},
    )

    rotation_receipt_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    account_id: Mapped[str] = mapped_column(String(36), nullable=False)
    request_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    draft_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    catalog_revision: Mapped[str] = mapped_column(String(80), nullable=False)
    rotation_kind: Mapped[str] = mapped_column(String(12), nullable=False)
    scope_id: Mapped[str] = mapped_column(String(64), nullable=False)
    request_fingerprint: Mapped[bytes] = mapped_column(BYTEA, nullable=False)
    cycle_number: Mapped[int] = mapped_column(BigInteger, nullable=False)
    set_id: Mapped[str] = mapped_column(String(32), nullable=False)
    selected_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
