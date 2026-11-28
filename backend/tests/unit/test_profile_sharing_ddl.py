from __future__ import annotations

import ast
from pathlib import Path

from sqlalchemy import CheckConstraint, ForeignKeyConstraint, PrimaryKeyConstraint

from sketch2life.infrastructure.profile_sharing.tables import PROFILE_SHARE_GRANTS

_BACKEND = Path(__file__).resolve().parents[2]
_MIGRATION = (
    _BACKEND
    / "alembic"
    / "versions"
    / "20261126_sh_0001_parent_profile_share_grants.py"
)
_COLUMNS = (
    "share_grant_id",
    "parent_profile_id",
    "grantor_scope_ref",
    "data_origin",
    "consent_basis",
    "granted_fields",
    "invitation_code_sha256",
    "state",
    "revision",
    "created_at",
    "invitation_expires_at",
    "organization_ref",
    "class_ref",
    "managed_profile_ref",
    "recipient_subject",
    "accepted_at",
    "expires_at",
    "revoked_at",
    "expired_at",
)
_CHECKS = {
    "ck_psg_grantor_ref",
    "ck_psg_data_origin",
    "ck_psg_consent_basis",
    "ck_psg_fields",
    "ck_psg_code_hash",
    "ck_psg_state",
    "ck_psg_revision",
    "ck_psg_invitation_window",
    "ck_psg_link_fields",
    "ck_psg_state_fields",
}


def _constants(source: str) -> dict[str, object]:
    module = ast.parse(source)
    result: dict[str, object] = {}
    for node in module.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id in {
                "revision",
                "down_revision",
                "depends_on",
                "branch_labels",
            }:
                result[target.id] = ast.literal_eval(node.value)
    return result


def test_migration_revision_dependency_and_encoding_are_pinned() -> None:
    raw = _MIGRATION.read_bytes()
    source = raw.decode("ascii")
    assert b"\r\n" not in raw
    assert _constants(source) == {
        "revision": "20261126_sh_0001",
        "down_revision": "20261126_sl_0001",
        "branch_labels": None,
        "depends_on": ("20261121_psn_0001",),
    }


def test_orm_table_mirrors_only_parent_owned_share_metadata() -> None:
    assert PROFILE_SHARE_GRANTS.schema == "parent"
    assert PROFILE_SHARE_GRANTS.name == "profile_share_grants"
    assert tuple(PROFILE_SHARE_GRANTS.columns.keys()) == _COLUMNS
    checks = {
        constraint.name
        for constraint in PROFILE_SHARE_GRANTS.constraints
        if isinstance(constraint, CheckConstraint)
    }
    assert checks == _CHECKS
    primary_key = next(
        constraint
        for constraint in PROFILE_SHARE_GRANTS.constraints
        if isinstance(constraint, PrimaryKeyConstraint)
    )
    assert primary_key.name == "pk_parent_profile_share_grants"
    foreign_keys = [
        constraint
        for constraint in PROFILE_SHARE_GRANTS.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    ]
    assert len(foreign_keys) == 1
    assert [element.target_fullname for element in foreign_keys[0].elements] == [
        "parent.child_profiles.parent_profile_id"
    ]
    assert not ({"display_name", "age_months", "interests_summary"} & set(_COLUMNS))


def test_migration_has_revocation_guards_indexes_and_data_safe_downgrade() -> None:
    source = _MIGRATION.read_text(encoding="ascii")
    for index in (
        "uq_psg_one_active_link",
        "ix_psg_profile_created",
        "ix_psg_recipient_link",
    ):
        assert index in source
    for message in (
        "PROFILE_SHARE_GRANT_DELETE_FORBIDDEN",
        "PROFILE_SHARE_GRANT_IMMUTABLE",
        "PROFILE_SHARE_GRANT_ILLEGAL_TRANSITION",
        "PROFILE_SHARE_GRANT_REVISION",
    ):
        assert message in source
    assert "T-SHARE1 downgrade refused" in source
    assert "IF EXISTS (SELECT 1 FROM parent.profile_share_grants)" in source
    assert source.count("interval '2160 hours'") == 2
    assert "interval '90 days'" not in source
