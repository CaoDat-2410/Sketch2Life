# ruff: noqa: E501, F811, SIM117, B023
"""Missing PostgreSQL acceptance tests for E3 (T-SHARE1) named in IMPL_REVIEW_E_E3_R1_20261125.md."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import inspect, select, text, update
from sqlalchemy.exc import IntegrityError
from test_profile_sharing_postgres import (
    ShareApi,
    _accept,
    _freeze_share_clock,
    _invite,
    _parent_profile_id,
    share_api,  # noqa: F401
    share_roundtrip,  # noqa: F401
)

from alembic import command
from sketch2life.domain.profile_sharing import generate_invitation_code, invitation_code_sha256
from sketch2life.infrastructure.persistence.be1_models import (
    Be1CommandReceiptModel,
)
from sketch2life.infrastructure.persistence.core_models import CoreAuditEntryModel
from sketch2life.infrastructure.profile_sharing import service as profile_share_service
from sketch2life.infrastructure.profile_sharing.tables import PROFILE_SHARE_GRANTS

pytestmark = pytest.mark.integration


def test_forced_pk_race_on_revoke_and_accept_leaves_one_receipt_and_one_audit(
    share_api: ShareApi, monkeypatch: pytest.MonkeyPatch
) -> None:
    """covers: IMPL_REVIEW_E_E3_R1_20261125.md P2-3 (forced pk_be1_command_receipts race on accept & revoke)"""
    profile_id = _parent_profile_id(share_api)
    invite = _invite(share_api, profile_id, "e3-race-invite")
    grant_id = UUID(invite["share_grant_id"])
    code = invite["invitation_code"]

    # 1. Forced PK race on accept
    original_save_receipt = profile_share_service._save_receipt
    accept_raced = False

    def race_accept_receipt(db: Any, **values: Any) -> None:
        nonlocal accept_raced
        if not accept_raced and values["idempotency_key"] == "e3-race-accept":
            accept_raced = True
            db.rollback()
            now = datetime.now(UTC)
            with share_api.factory.begin() as winner_db:
                winner_db.execute(
                    update(PROFILE_SHARE_GRANTS)
                    .where(PROFILE_SHARE_GRANTS.c.share_grant_id == grant_id)
                    .values(
                        state="ACTIVE",
                        organization_ref=share_api.organization_id,
                        class_ref=share_api.class_id,
                        managed_profile_ref=share_api.child_id,
                        recipient_subject=share_api.teacher,
                        accepted_at=now,
                        expires_at=now + timedelta(days=90),
                        revision=2,
                    )
                )
                profile_share_service._organization_audit(
                    winner_db,
                    organization_id=share_api.organization_id,
                    actor=share_api.teacher,
                    action="parent_share.grant.accept",
                    share_grant_id=grant_id,
                )
                winner_db.add(
                    Be1CommandReceiptModel(
                        principal_ref=values["principal_ref"],
                        operation_scope=values["operation_scope"],
                        idempotency_key=values["idempotency_key"],
                        organization_id=values["organization_id"],
                        request_fingerprint=values["fingerprint"],
                        response_json={
                            "body": profile_share_service._json_safe(values["body"]),
                            "etag": values["etag"],
                        },
                    )
                )
            original_save_receipt(db, **values)
            return
        original_save_receipt(db, **values)

    monkeypatch.setattr(profile_share_service, "_save_receipt", race_accept_receipt)
    accept_res = _accept(share_api, share_api.teacher, code, "e3-race-accept")
    assert accept_res.status_code == 200, accept_res.text
    assert accept_raced is True

    # 2. Forced PK race on revoke
    revoke_raced = False

    def race_revoke_receipt(db: Any, **values: Any) -> None:
        nonlocal revoke_raced
        if not revoke_raced and values["idempotency_key"] == "e3-race-revoke":
            revoke_raced = True
            db.rollback()
            now = datetime.now(UTC)
            with share_api.factory.begin() as winner_db:
                winner_db.execute(
                    update(PROFILE_SHARE_GRANTS)
                    .where(PROFILE_SHARE_GRANTS.c.share_grant_id == grant_id)
                    .values(state="REVOKED", revoked_at=now, revision=3)
                )
                profile_share_service._parent_audit(
                    winner_db,
                    scope_ref=values["principal_ref"],
                    action="parent_share.grant.revoke",
                    share_grant_id=grant_id,
                )
                winner_db.add(
                    Be1CommandReceiptModel(
                        principal_ref=values["principal_ref"],
                        operation_scope=values["operation_scope"],
                        idempotency_key=values["idempotency_key"],
                        organization_id=None,
                        request_fingerprint=values["fingerprint"],
                        response_json={
                            "body": profile_share_service._json_safe(values["body"]),
                            "etag": values["etag"],
                        },
                    )
                )
            original_save_receipt(db, **values)
            return
        original_save_receipt(db, **values)

    monkeypatch.setattr(profile_share_service, "_save_receipt", race_revoke_receipt)
    revoke_res = share_api.client.post(
        f"/v1/parent/share-grants/{grant_id}/revoke",
        headers={**share_api.headers(share_api.parent, "e3-race-revoke"), "If-Match": '"2"'},
    )
    assert revoke_res.status_code == 200, revoke_res.text
    assert revoke_res.json()["state"] == "REVOKED"
    assert revoke_raced is True

    with share_api.factory() as db:
        accept_audits = db.scalars(
            select(CoreAuditEntryModel).where(
                CoreAuditEntryModel.resource_id == str(grant_id),
                CoreAuditEntryModel.action == "parent_share.grant.accept",
            )
        ).all()
        revoke_audits = db.scalars(
            select(CoreAuditEntryModel).where(
                CoreAuditEntryModel.resource_id == str(grant_id),
                CoreAuditEntryModel.action == "parent_share.grant.revoke",
            )
        ).all()
        receipts = db.scalars(
            select(Be1CommandReceiptModel).where(
                Be1CommandReceiptModel.idempotency_key.in_(("e3-race-accept", "e3-race-revoke"))
            )
        ).all()
    assert len(accept_audits) == 1
    assert len(revoke_audits) == 1
    assert len(receipts) == 2


def test_ten_open_grants_cap_and_terminal_revoke_conflict(
    share_api: ShareApi, monkeypatch: pytest.MonkeyPatch
) -> None:
    """covers: IMPL_REVIEW_E_E3_R1_20261125.md Checks-Receipts & P3-4 / Plan §3 (10 open grants cap & terminal revoke 409)"""
    profile_id = _parent_profile_id(share_api)
    created_ids: list[str] = []
    for idx in range(10):
        created_ids.append(
            _invite(share_api, profile_id, f"e3-cap-{idx}")["share_grant_id"]
        )

    eleventh = share_api.client.post(
        "/v1/parent/share-grants",
        json={"profile_id": profile_id, "granted_fields": ["DISPLAY_NAME"]},
        headers=share_api.headers(share_api.parent, "e3-cap-10"),
    )
    assert eleventh.status_code == 409
    assert eleventh.json()["code"] == "RESOURCE_CONFLICT"

    # Revoking one frees a slot; revoking again returns 409 INVALID_STATE_TRANSITION
    revoked = share_api.client.post(
        f"/v1/parent/share-grants/{created_ids[0]}/revoke",
        headers={**share_api.headers(share_api.parent, "e3-cap-revoke-1"), "If-Match": '"1"'},
    )
    assert revoked.status_code == 200
    second_revoke = share_api.client.post(
        f"/v1/parent/share-grants/{created_ids[0]}/revoke",
        headers={**share_api.headers(share_api.parent, "e3-cap-revoke-2"), "If-Match": '"2"'},
    )
    assert second_revoke.status_code == 409
    assert second_revoke.json()["code"] == "INVALID_STATE_TRANSITION"

    replacement = share_api.client.post(
        "/v1/parent/share-grants",
        json={"profile_id": profile_id, "granted_fields": ["DISPLAY_NAME"]},
        headers=share_api.headers(share_api.parent, "e3-cap-11-ok"),
    )
    assert replacement.status_code == 201

    # Derived-expired invitation cannot be revoked (409 INVALID_STATE_TRANSITION)
    now = datetime.now(UTC)
    _freeze_share_clock(monkeypatch, now + timedelta(days=91))
    expired_revoke = share_api.client.post(
        f"/v1/parent/share-grants/{created_ids[1]}/revoke",
        headers={**share_api.headers(share_api.parent, "e3-cap-revoke-expired"), "If-Match": '"1"'},
    )
    assert expired_revoke.status_code == 409
    assert expired_revoke.json()["code"] == "INVALID_STATE_TRANSITION"


def test_remaining_triggers_and_dst_timezone_2160_hour_check(share_api: ShareApi) -> None:
    """covers: IMPL_REVIEW_E_E3_R1_20261125.md P2-3 & P3-3 (remaining triggers & 2160h DST-safe CHECK)"""
    profile_id = _parent_profile_id(share_api)
    now = datetime(2026, 3, 7, 12, 0, tzinfo=UTC)  # Spans US DST spring-forward when +90d/+2160h
    with share_api.factory.begin() as db:
        db.execute(text("SET LOCAL TIME ZONE 'America/New_York'"))
        grant_id = uuid4()
        db.execute(
            PROFILE_SHARE_GRANTS.insert().values(
                share_grant_id=grant_id,
                parent_profile_id=UUID(profile_id),
                grantor_scope_ref="0" * 64,
                data_origin="SYNTHETIC_DEV",
                consent_basis="PARENT_GRANT_ACT_V1",
                granted_fields=["DISPLAY_NAME"],
                invitation_code_sha256=invitation_code_sha256(generate_invitation_code()),
                state="INVITED",
                revision=1,
                created_at=now,
                invitation_expires_at=now + timedelta(days=90),
            )
        )

    # Insert with non-INVITED state refused
    with pytest.raises(IntegrityError, match="PROFILE_SHARE_GRANT_INSERT_STATE"):
        with share_api.factory.begin() as db:
            db.execute(
                PROFILE_SHARE_GRANTS.insert().values(
                    share_grant_id=uuid4(),
                    parent_profile_id=UUID(profile_id),
                    grantor_scope_ref="0" * 64,
                    data_origin="SYNTHETIC_DEV",
                    consent_basis="PARENT_GRANT_ACT_V1",
                    granted_fields=["DISPLAY_NAME"],
                    invitation_code_sha256=invitation_code_sha256(generate_invitation_code()),
                    state="ACTIVE",
                    revision=1,
                    created_at=now,
                    invitation_expires_at=now + timedelta(days=90),
                    organization_ref=share_api.organization_id,
                    class_ref=share_api.class_id,
                    managed_profile_ref=share_api.child_id,
                    recipient_subject=share_api.teacher,
                    accepted_at=now,
                    expires_at=now + timedelta(days=90),
                )
            )

    invite = _invite(share_api, profile_id, "e3-trig-extra-create")
    accepted = _accept(
        share_api, share_api.teacher, invite["invitation_code"], "e3-trig-extra-accept"
    )
    assert accepted.status_code == 200
    acc_id = UUID(invite["share_grant_id"])

    with pytest.raises(IntegrityError, match="PROFILE_SHARE_GRANT_LINK_IMMUTABLE"):
        with share_api.factory.begin() as db:
            db.execute(
                update(PROFILE_SHARE_GRANTS)
                .where(PROFILE_SHARE_GRANTS.c.share_grant_id == acc_id)
                .values(recipient_subject="tampered", revision=3)
            )

    with pytest.raises(IntegrityError, match="PROFILE_SHARE_GRANT_REVISION"):
        with share_api.factory.begin() as db:
            db.execute(
                update(PROFILE_SHARE_GRANTS)
                .where(PROFILE_SHARE_GRANTS.c.share_grant_id == acc_id)
                .values(state="REVOKED", revoked_at=datetime.now(UTC), revision=99)
            )


def test_empty_share_grant_downgrade_succeeds_and_removes_table(share_roundtrip: Any) -> None:
    """covers: IMPL_REVIEW_E_E3_R1_20261125.md P2-3 & Plan §7 (empty downgrade succeeds)"""
    config, engine = share_roundtrip
    command.upgrade(config, "heads")
    command.downgrade(config, "20261126_sl_0001")
    with engine.connect() as conn:
        inspector = inspect(conn)
        assert not inspector.has_table("profile_share_grants", schema="parent")
        versions = conn.execute(text("SELECT version_num FROM alembic_version")).scalars().all()
        assert "20261126_sh_0001" not in versions
    command.upgrade(config, "heads")
