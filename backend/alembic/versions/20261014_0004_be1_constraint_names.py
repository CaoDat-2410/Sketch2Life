"""Name BE1 check constraints consistently with SQLAlchemy metadata."""

from __future__ import annotations

from alembic import op

revision = "20261014_0004"
down_revision = "20261014_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    renames = (
        (
            "be1_organization_assignments",
            "be1_organization_assignments_role_check",
            "ck_be1_assignment_role",
        ),
        (
            "be1_managed_profiles",
            "be1_managed_profiles_age_months_check",
            "ck_be1_profile_age_months",
        ),
        ("be1_enrollments", "be1_enrollments_state_check", "ck_be1_enrollment_state"),
        ("be1_consent_records", "be1_consent_records_state_check", "ck_be1_consent_state"),
        ("be1_device_grants", "be1_device_grants_state_check", "ck_be1_device_grant_state"),
        ("be1_sessions", "be1_sessions_state_check", "ck_be1_session_state"),
        ("be1_sessions", "be1_sessions_revision_check", "ck_be1_session_revision"),
        (
            "be1_session_memberships",
            "be1_session_memberships_state_check",
            "ck_be1_membership_state",
        ),
        ("be1_session_groups", "be1_session_groups_state_check", "ck_be1_group_state"),
        ("be1_child_turns", "be1_child_turns_state_check", "ck_be1_turn_state"),
        ("be1_child_turns", "be1_child_turns_document_epoch_check", "ck_be1_turn_epoch"),
        ("be1_gallery_snapshots", "be1_gallery_snapshots_state_check", "ck_be1_gallery_state"),
        (
            "be1_data_lifecycle_requests",
            "be1_data_lifecycle_requests_state_check",
            "ck_be1_data_request_state",
        ),
        (
            "be1_data_lifecycle_requests",
            "be1_data_lifecycle_requests_unresolved_items_check",
            "ck_be1_data_request_unresolved",
        ),
    )
    for table, old_name, new_name in renames:
        op.execute(f"ALTER TABLE {table} RENAME CONSTRAINT {old_name} TO {new_name}")


def downgrade() -> None:
    renames = (
        (
            "be1_data_lifecycle_requests",
            "ck_be1_data_request_unresolved",
            "be1_data_lifecycle_requests_unresolved_items_check",
        ),
        (
            "be1_data_lifecycle_requests",
            "ck_be1_data_request_state",
            "be1_data_lifecycle_requests_state_check",
        ),
        ("be1_gallery_snapshots", "ck_be1_gallery_state", "be1_gallery_snapshots_state_check"),
        ("be1_child_turns", "ck_be1_turn_epoch", "be1_child_turns_document_epoch_check"),
        ("be1_child_turns", "ck_be1_turn_state", "be1_child_turns_state_check"),
        ("be1_session_groups", "ck_be1_group_state", "be1_session_groups_state_check"),
        (
            "be1_session_memberships",
            "ck_be1_membership_state",
            "be1_session_memberships_state_check",
        ),
        ("be1_sessions", "ck_be1_session_revision", "be1_sessions_revision_check"),
        ("be1_sessions", "ck_be1_session_state", "be1_sessions_state_check"),
        ("be1_device_grants", "ck_be1_device_grant_state", "be1_device_grants_state_check"),
        ("be1_consent_records", "ck_be1_consent_state", "be1_consent_records_state_check"),
        ("be1_enrollments", "ck_be1_enrollment_state", "be1_enrollments_state_check"),
        (
            "be1_managed_profiles",
            "ck_be1_profile_age_months",
            "be1_managed_profiles_age_months_check",
        ),
        (
            "be1_organization_assignments",
            "ck_be1_assignment_role",
            "be1_organization_assignments_role_check",
        ),
    )
    for table, old_name, new_name in renames:
        op.execute(f"ALTER TABLE {table} RENAME CONSTRAINT {old_name} TO {new_name}")
