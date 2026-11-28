"""Transactional Parent share-grant commands and scoped profile/history reads."""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Mapping
from datetime import UTC, datetime, timedelta
from functools import wraps
from typing import Any
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy import and_, or_, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.domain.profile_sharing import (
    ProfileShareConflict,
    ProfileShareInvalidRequest,
    ProfileShareNotFound,
    ProfileShareStaleRevision,
    ProfileShareUnavailable,
    ShareState,
    effective_state,
    generate_invitation_code,
    grant_window,
    invitation_code_sha256,
    invitation_window,
    request_fingerprint,
)
from sketch2life.infrastructure.persistence.be1_models import (
    Be1CommandReceiptModel,
    ClassroomModel,
    EnrollmentModel,
    ManagedProfileModel,
)
from sketch2life.infrastructure.persistence.core_models import CoreAuditEntryModel
from sketch2life.infrastructure.persistence.parent_models import (
    ParentChildProfileModel,
    ParentProfileRevisionModel,
)
from sketch2life.infrastructure.profile_sharing.tables import PROFILE_SHARE_GRANTS
from sketch2life.infrastructure.uploads.resolvers import parent_scope_ref

_GRANTS = PROFILE_SHARE_GRANTS
_RECEIPT_PK = "pk_be1_command_receipts"


def _db_errors[T](function: Callable[..., T]) -> Callable[..., T]:
    @wraps(function)
    def wrapped(db: Session, *args: object, **kwargs: object) -> T:
        try:
            return function(db, *args, **kwargs)
        except SQLAlchemyError:
            db.rollback()
            raise ProfileShareUnavailable() from None

    return wrapped


def _not_found() -> ProfileShareNotFound:
    return ProfileShareNotFound()


def _conflict() -> ProfileShareConflict:
    return ProfileShareConflict()


def _receipt_scope(value: str) -> str:
    if len(value) <= 256:
        return value
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _json_safe(value: object) -> object:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def _receipt(
    db: Session,
    *,
    principal_ref: str,
    operation_scope: str,
    idempotency_key: str,
) -> Be1CommandReceiptModel | None:
    return db.scalar(
        select(Be1CommandReceiptModel)
        .where(
            Be1CommandReceiptModel.principal_ref == principal_ref,
            Be1CommandReceiptModel.operation_scope == operation_scope,
            Be1CommandReceiptModel.idempotency_key == idempotency_key,
        )
        .with_for_update()
    )


def _replay(
    row: Be1CommandReceiptModel | None,
    *,
    fingerprint: str,
    organization_id: str | None,
) -> tuple[dict[str, object], str] | None:
    if row is None:
        return None
    if row.organization_id != organization_id or row.request_fingerprint != fingerprint:
        raise ProfileShareInvalidRequest("INVALID_IDEMPOTENCY_KEY")
    response = row.response_json
    body = response.get("body")
    etag = response.get("etag")
    if not isinstance(body, dict) or not isinstance(etag, str):
        raise ProfileShareUnavailable()
    return dict(body), etag


def _save_receipt(
    db: Session,
    *,
    principal_ref: str,
    operation_scope: str,
    idempotency_key: str,
    organization_id: str | None,
    fingerprint: str,
    body: dict[str, object],
    etag: str,
) -> None:
    db.add(
        Be1CommandReceiptModel(
            principal_ref=principal_ref,
            operation_scope=operation_scope,
            idempotency_key=idempotency_key,
            organization_id=organization_id,
            request_fingerprint=fingerprint,
            response_json={"body": _json_safe(body), "etag": etag},
        )
    )


def _commit(db: Session) -> bool:
    """Commit and return True only for the known idempotency-receipt race."""
    try:
        db.commit()
        return False
    except IntegrityError as exc:
        original = getattr(exc, "orig", None)
        sqlstate = getattr(original, "sqlstate", None) or getattr(original, "pgcode", None)
        diagnostic = getattr(original, "diag", None)
        constraint = getattr(diagnostic, "constraint_name", None)
        db.rollback()
        if sqlstate == "23505" and constraint == _RECEIPT_PK:
            return True
        raise _conflict() from None


def _owned_profile(
    db: Session, principal: VerifiedPrincipal, profile_id: UUID, *, lock: bool
) -> ParentChildProfileModel:
    statement = select(ParentChildProfileModel).where(
        ParentChildProfileModel.parent_profile_id == profile_id,
        ParentChildProfileModel.owner_issuer == principal.issuer,
        ParentChildProfileModel.owner_subject == principal.subject,
        ParentChildProfileModel.state == "ACTIVE",
    )
    if lock:
        statement = statement.with_for_update()
    row = db.scalar(statement)
    if row is None:
        raise _not_found()
    return row


def _grant_by_id(
    db: Session,
    *,
    share_grant_id: UUID,
    parent_profile_id: UUID,
    lock: bool = False,
) -> Mapping[Any, Any] | None:
    statement = select(_GRANTS).where(
        _GRANTS.c.share_grant_id == share_grant_id,
        _GRANTS.c.parent_profile_id == parent_profile_id,
    )
    if lock:
        statement = statement.with_for_update()
    return db.execute(statement).mappings().first()


def _grant_view(row: Mapping[Any, Any], now: datetime) -> dict[str, object]:
    return {
        "contract": "ParentShareGrantV1",
        "share_grant_id": row["share_grant_id"],
        "profile_id": row["parent_profile_id"],
        "state": effective_state(row, now).value,
        "granted_fields": list(row["granted_fields"]),
        "created_at": row["created_at"],
        "invitation_expires_at": row["invitation_expires_at"],
        "accepted_at": row["accepted_at"],
        "expires_at": row["expires_at"],
        "revoked_at": row["revoked_at"],
        "revision": row["revision"],
    }


def _parent_audit(
    db: Session, *, scope_ref: str, action: str, share_grant_id: UUID
) -> None:
    db.add(
        CoreAuditEntryModel(
            audit_id=str(uuid4()),
            organization_id=None,
            owner_scope_kind="PARENT_ACCOUNT",
            owner_scope_ref=scope_ref,
            actor_ref=scope_ref,
            action=action,
            resource_type="profile_share_grant",
            resource_id=str(share_grant_id),
            decision="allowed",
        )
    )


def _organization_audit(
    db: Session,
    *,
    organization_id: str,
    actor: str,
    action: str,
    share_grant_id: UUID,
) -> None:
    db.add(
        CoreAuditEntryModel(
            audit_id=str(uuid4()),
            organization_id=organization_id,
            owner_scope_kind="ORGANIZATION",
            owner_scope_ref=organization_id,
            actor_ref=actor,
            action=action,
            resource_type="profile_share_grant",
            resource_id=str(share_grant_id),
            decision="allowed",
        )
    )


@_db_errors
def create_grant(
    db: Session,
    principal: VerifiedPrincipal,
    *,
    profile_id: UUID,
    granted_fields: tuple[str, ...],
    idempotency_key: str,
    now: datetime | None = None,
    _retry: bool = True,
) -> tuple[dict[str, object], str]:
    moment = now or datetime.now(UTC)
    profile = _owned_profile(db, principal, profile_id, lock=True)
    scope_ref = parent_scope_ref(principal)
    scope = "POST /v1/parent/share-grants"
    fingerprint = request_fingerprint(
        {
            "op": "parent_share.create.v1",
            "profile_id": str(profile_id),
            "granted_fields": list(granted_fields),
        }
    )
    replay = _replay(
        _receipt(
            db,
            principal_ref=scope_ref,
            operation_scope=scope,
            idempotency_key=idempotency_key,
        ),
        fingerprint=fingerprint,
        organization_id=None,
    )
    if replay is not None:
        body, etag = replay
        body["invitation_code"] = None
        return body, etag

    open_count = db.scalar(
        select(sa.func.count())
        .select_from(_GRANTS)
        .where(
            _GRANTS.c.parent_profile_id == profile.parent_profile_id,
            or_(
                and_(
                    _GRANTS.c.state == "INVITED",
                    _GRANTS.c.invitation_expires_at > moment,
                ),
                and_(_GRANTS.c.state == "ACTIVE", _GRANTS.c.expires_at > moment),
            ),
        )
    )
    if int(open_count or 0) >= 10:
        raise _conflict()

    code = generate_invitation_code()
    share_grant_id = uuid4()
    values = {
        "share_grant_id": share_grant_id,
        "parent_profile_id": profile.parent_profile_id,
        "grantor_scope_ref": scope_ref,
        "data_origin": profile.data_origin,
        "consent_basis": "PARENT_GRANT_ACT_V1",
        "granted_fields": list(granted_fields),
        "invitation_code_sha256": invitation_code_sha256(code),
        "state": "INVITED",
        "revision": 1,
        "created_at": moment,
        "invitation_expires_at": invitation_window(moment),
    }
    row = db.execute(_GRANTS.insert().values(**values).returning(*_GRANTS.c)).mappings().one()
    body = _grant_view(row, moment)
    etag = '"1"'
    _parent_audit(
        db, scope_ref=scope_ref, action="parent_share.grant.invite", share_grant_id=share_grant_id
    )
    _save_receipt(
        db,
        principal_ref=scope_ref,
        operation_scope=scope,
        idempotency_key=idempotency_key,
        organization_id=None,
        fingerprint=fingerprint,
        body=body,
        etag=etag,
    )
    if _commit(db):
        if _retry:
            return create_grant(
                db,
                principal,
                profile_id=profile_id,
                granted_fields=granted_fields,
                idempotency_key=idempotency_key,
                now=moment,
                _retry=False,
            )
        raise _conflict()
    body["invitation_code"] = code
    return body, etag


@_db_errors
def list_grants(
    db: Session,
    principal: VerifiedPrincipal,
    *,
    profile_id: UUID,
    limit: int,
    cursor: tuple[datetime, UUID] | None,
    now: datetime | None = None,
) -> tuple[dict[str, object], tuple[datetime, str] | None]:
    moment = now or datetime.now(UTC)
    _owned_profile(db, principal, profile_id, lock=False)
    statement = select(_GRANTS).where(_GRANTS.c.parent_profile_id == profile_id)
    if cursor:
        cursor_time, cursor_id = cursor
        statement = statement.where(
            or_(
                _GRANTS.c.created_at < cursor_time,
                and_(_GRANTS.c.created_at == cursor_time, _GRANTS.c.share_grant_id < cursor_id),
            )
        )
    rows = list(
        db.execute(
            statement.order_by(_GRANTS.c.created_at.desc(), _GRANTS.c.share_grant_id.desc())
            .limit(limit + 1)
        ).mappings()
    )
    more = len(rows) > limit
    rows = rows[:limit]
    next_cursor = (
        (rows[-1]["created_at"], str(rows[-1]["share_grant_id"]))
        if more and rows
        else None
    )
    return {
        "contract": "ParentShareGrantListV1",
        "items": [_grant_view(row, moment) for row in rows],
    }, next_cursor


@_db_errors
def get_grant(
    db: Session,
    principal: VerifiedPrincipal,
    *,
    share_grant_id: UUID,
    now: datetime | None = None,
) -> tuple[dict[str, object], str]:
    moment = now or datetime.now(UTC)
    row = db.execute(
        select(_GRANTS)
        .join(
            ParentChildProfileModel,
            ParentChildProfileModel.parent_profile_id == _GRANTS.c.parent_profile_id,
        )
        .where(
            _GRANTS.c.share_grant_id == share_grant_id,
            ParentChildProfileModel.owner_issuer == principal.issuer,
            ParentChildProfileModel.owner_subject == principal.subject,
            ParentChildProfileModel.state == "ACTIVE",
        )
    ).mappings().first()
    if row is None:
        raise _not_found()
    return _grant_view(row, moment), f'"{row["revision"]}"'


@_db_errors
def revoke_grant(
    db: Session,
    principal: VerifiedPrincipal,
    *,
    share_grant_id: UUID,
    expected_revision: int,
    idempotency_key: str,
    now: datetime | None = None,
    _retry: bool = True,
) -> tuple[dict[str, object], str]:
    moment = now or datetime.now(UTC)
    # Resolve ownership first, then preserve the global Parent-profile -> grant -> receipt
    # lock order.
    owner_row = db.scalar(
        select(_GRANTS.c.parent_profile_id)
        .join(
            ParentChildProfileModel,
            ParentChildProfileModel.parent_profile_id == _GRANTS.c.parent_profile_id,
        )
        .where(
            _GRANTS.c.share_grant_id == share_grant_id,
            ParentChildProfileModel.owner_issuer == principal.issuer,
            ParentChildProfileModel.owner_subject == principal.subject,
            ParentChildProfileModel.state == "ACTIVE",
        )
    )
    if owner_row is None:
        raise _not_found()
    profile = _owned_profile(db, principal, owner_row, lock=True)
    row = _grant_by_id(
        db,
        share_grant_id=share_grant_id,
        parent_profile_id=profile.parent_profile_id,
        lock=True,
    )
    if row is None:
        raise _not_found()
    scope_ref = parent_scope_ref(principal)
    scope = _receipt_scope(f"POST /v1/parent/share-grants/{share_grant_id}/revoke")
    fingerprint = request_fingerprint(
        {
            "op": "parent_share.revoke.v1",
            "share_grant_id": str(share_grant_id),
            "expected_revision": expected_revision,
        }
    )
    replay = _replay(
        _receipt(
            db,
            principal_ref=scope_ref,
            operation_scope=scope,
            idempotency_key=idempotency_key,
        ),
        fingerprint=fingerprint,
        organization_id=None,
    )
    if replay is not None:
        return replay
    if row["revision"] != expected_revision:
        raise ProfileShareStaleRevision(row["revision"])
    if effective_state(row, moment) not in {ShareState.INVITED, ShareState.ACTIVE}:
        raise ProfileShareConflict("INVALID_STATE_TRANSITION")
    updated = db.execute(
        update(_GRANTS)
        .where(
            _GRANTS.c.share_grant_id == share_grant_id,
            _GRANTS.c.revision == expected_revision,
        )
        .values(state="REVOKED", revoked_at=moment, revision=expected_revision + 1)
        .returning(*_GRANTS.c)
    ).mappings().first()
    if updated is None:
        current = db.scalar(
            select(_GRANTS.c.revision).where(_GRANTS.c.share_grant_id == share_grant_id)
        )
        raise ProfileShareStaleRevision(current or expected_revision)
    body = _grant_view(updated, moment)
    etag = f'"{updated["revision"]}"'
    _parent_audit(
        db, scope_ref=scope_ref, action="parent_share.grant.revoke", share_grant_id=share_grant_id
    )
    _save_receipt(
        db,
        principal_ref=scope_ref,
        operation_scope=scope,
        idempotency_key=idempotency_key,
        organization_id=None,
        fingerprint=fingerprint,
        body=body,
        etag=etag,
    )
    if _commit(db):
        if _retry:
            return revoke_grant(
                db,
                principal,
                share_grant_id=share_grant_id,
                expected_revision=expected_revision,
                idempotency_key=idempotency_key,
                now=moment,
                _retry=False,
            )
        raise _conflict()
    return body, etag


@_db_errors
def accept_teacher_share(
    db: Session,
    principal: VerifiedPrincipal,
    *,
    organization_id: str,
    class_id: str,
    child_id: str,
    invitation_code: str,
    idempotency_key: str,
    authorize_teacher: Callable[[], None],
    profile_released: Callable[[ManagedProfileModel], bool],
    profile_withdrawn: Callable[[ManagedProfileModel], bool],
    now: datetime | None = None,
    _retry: bool = True,
) -> tuple[dict[str, object], str]:
    moment = now or datetime.now(UTC)
    authorize_teacher()
    classroom = db.scalar(
        select(ClassroomModel)
        .where(
            ClassroomModel.organization_id == organization_id,
            ClassroomModel.class_id == class_id,
        )
        .with_for_update(read=True)
    )
    if classroom is None or classroom.state == "archived":
        raise _not_found()
    if classroom.state != "active":
        raise ProfileShareConflict("INVALID_STATE_TRANSITION")
    profile = db.scalar(
        select(ManagedProfileModel)
        .where(
            ManagedProfileModel.organization_id == organization_id,
            ManagedProfileModel.class_id == class_id,
            ManagedProfileModel.child_id == child_id,
            ManagedProfileModel.state == "active",
        )
        .with_for_update()
    )
    if profile is None:
        raise _not_found()
    if profile_withdrawn(profile):
        raise _not_found()
    if not profile_released(profile):
        raise ProfileShareConflict("CONSENT_NOT_EFFECTIVE")

    code_hash = invitation_code_sha256(invitation_code)
    grant_id = db.scalar(
        select(_GRANTS.c.share_grant_id).where(_GRANTS.c.invitation_code_sha256 == code_hash)
    )
    if grant_id is None:
        raise _not_found()
    parent_profile_id = db.scalar(
        select(_GRANTS.c.parent_profile_id).where(_GRANTS.c.share_grant_id == grant_id)
    )
    if parent_profile_id is None:
        raise _not_found()
    parent_profile = db.scalar(
        select(ParentChildProfileModel)
        .where(
            ParentChildProfileModel.parent_profile_id == parent_profile_id,
            ParentChildProfileModel.state == "ACTIVE",
        )
        .with_for_update(read=True)
    )
    if parent_profile is None:
        raise _not_found()
    row = db.execute(
        select(_GRANTS).where(_GRANTS.c.share_grant_id == grant_id).with_for_update()
    ).mappings().first()
    if row is None or row["parent_profile_id"] != parent_profile_id:
        raise _not_found()

    raw_scope = (
        f"POST /organizations/{organization_id}/classes/{class_id}/profiles/{child_id}"
        "/parent-share/accept"
    )
    scope = _receipt_scope(raw_scope)
    fingerprint = request_fingerprint(
        {
            "op": "parent_share.accept.v1",
            "organization_id": organization_id,
            "class_id": class_id,
            "child_id": child_id,
            "code_sha256": code_hash,
        }
    )
    previous = _receipt(
        db,
        principal_ref=principal.subject,
        operation_scope=scope,
        idempotency_key=idempotency_key,
    )
    if previous is not None:
        # A same-key replay is valid only for the same accepting Teacher and the same link scope.
        if (
            row["recipient_subject"] == principal.subject
            and row["organization_ref"] == organization_id
            and row["class_ref"] == class_id
            and row["managed_profile_ref"] == child_id
        ):
            replay = _replay(previous, fingerprint=fingerprint, organization_id=organization_id)
            if replay is not None:
                return replay
        raise ProfileShareInvalidRequest("INVALID_IDEMPOTENCY_KEY")
    if row["state"] != "INVITED":
        raise _not_found()
    if row["invitation_expires_at"] <= moment:
        raise ProfileShareConflict("INVITATION_EXPIRED")
    if (
        row["data_origin"] != profile.data_origin
        or parent_profile.data_origin != profile.data_origin
    ):
        raise ProfileShareConflict("CONSENT_NOT_EFFECTIVE")

    # Settle a due active link before inserting the new one so the partial unique index is free.
    active_links = db.execute(
        select(_GRANTS)
        .where(
            _GRANTS.c.organization_ref == organization_id,
            _GRANTS.c.managed_profile_ref == child_id,
            _GRANTS.c.state == "ACTIVE",
        )
        .with_for_update()
    ).mappings().all()
    for link in active_links:
        if effective_state(link, moment) is not ShareState.EXPIRED:
            raise _conflict()
        settled = db.execute(
            update(_GRANTS)
            .where(
                _GRANTS.c.share_grant_id == link["share_grant_id"],
                _GRANTS.c.revision == link["revision"],
            )
            .values(state="EXPIRED", expired_at=moment, revision=link["revision"] + 1)
            .returning(*_GRANTS.c)
        ).mappings().first()
        if settled is None:
            raise _conflict()
        _organization_audit(
            db,
            organization_id=organization_id,
            actor=principal.subject,
            action="parent_share.grant.expire",
            share_grant_id=link["share_grant_id"],
        )

    accepted_at = moment
    accepted = db.execute(
        update(_GRANTS)
        .where(
            _GRANTS.c.share_grant_id == grant_id,
            _GRANTS.c.state == "INVITED",
        )
        .values(
            state="ACTIVE",
            organization_ref=organization_id,
            class_ref=class_id,
            managed_profile_ref=child_id,
            recipient_subject=principal.subject,
            accepted_at=accepted_at,
            expires_at=grant_window(accepted_at),
            revision=row["revision"] + 1,
        )
        .returning(*_GRANTS.c)
    ).mappings().first()
    if accepted is None:
        raise _not_found()
    body = {
        "contract": "Be1ParentShareLinkV1",
        "share_grant_id": accepted["share_grant_id"],
        "child_id": child_id,
        "state": "ACTIVE",
        "granted_fields": list(accepted["granted_fields"]),
        "accepted_at": accepted_at,
        "expires_at": accepted["expires_at"],
        "revision": accepted["revision"],
    }
    etag = f'"{accepted["revision"]}"'
    _organization_audit(
        db,
        organization_id=organization_id,
        actor=principal.subject,
        action="parent_share.grant.accept",
        share_grant_id=grant_id,
    )
    _save_receipt(
        db,
        principal_ref=principal.subject,
        operation_scope=scope,
        idempotency_key=idempotency_key,
        organization_id=organization_id,
        fingerprint=fingerprint,
        body=body,
        etag=etag,
    )
    if _commit(db):
        if _retry:
            return accept_teacher_share(
                db,
                principal,
                organization_id=organization_id,
                class_id=class_id,
                child_id=child_id,
                invitation_code=invitation_code,
                idempotency_key=idempotency_key,
                authorize_teacher=authorize_teacher,
                profile_released=profile_released,
                profile_withdrawn=profile_withdrawn,
                now=moment,
                _retry=False,
            )
        raise _conflict()
    return body, etag


@_db_errors
def read_teacher_shared_profile(
    db: Session,
    principal: VerifiedPrincipal,
    *,
    organization_id: str,
    class_id: str,
    child_id: str,
    profile: ManagedProfileModel,
    now: datetime | None = None,
) -> dict[str, object]:
    moment = now or datetime.now(UTC)
    row = db.execute(
        select(_GRANTS).where(
            _GRANTS.c.organization_ref == organization_id,
            _GRANTS.c.class_ref == class_id,
            _GRANTS.c.managed_profile_ref == child_id,
            _GRANTS.c.recipient_subject == principal.subject,
            _GRANTS.c.state == "ACTIVE",
            _GRANTS.c.expires_at > moment,
            _GRANTS.c.data_origin == profile.data_origin,
        )
    ).mappings().first()
    if row is None:
        raise _not_found()
    parent_profile = db.scalar(
        select(ParentChildProfileModel).where(
            ParentChildProfileModel.parent_profile_id == row["parent_profile_id"],
            ParentChildProfileModel.state == "ACTIVE",
            ParentChildProfileModel.data_origin == profile.data_origin,
        )
    )
    if parent_profile is None:
        raise _not_found()
    revision = db.scalar(
        select(ParentProfileRevisionModel).where(
            ParentProfileRevisionModel.parent_profile_id == parent_profile.parent_profile_id,
            ParentProfileRevisionModel.revision_no == parent_profile.current_revision_no,
        )
    )
    if revision is None:
        raise _not_found()
    fields: dict[str, object] = {}
    for field in row["granted_fields"]:
        if field == "DISPLAY_NAME":
            fields["display_name"] = revision.display_name
        elif field == "AGE_BAND":
            fields["age_band"] = (
                None
                if revision.age_band_ref is None or revision.age_band_version is None
                else {"band_ref": revision.age_band_ref, "band_version": revision.age_band_version}
            )
        elif field == "INTERESTS_SUMMARY":
            fields["interests_summary"] = revision.interests_summary
    return {
        "contract": "Be1ParentSharedProfileV1",
        "share_grant_id": row["share_grant_id"],
        "child_id": child_id,
        "granted_fields": list(row["granted_fields"]),
        "expires_at": row["expires_at"],
        "fields": fields,
    }


@_db_errors
def list_deliveries(
    db: Session,
    principal: VerifiedPrincipal,
    *,
    share_grant_id: UUID,
    limit: int,
    cursor: tuple[datetime, str] | None,
    now: datetime | None = None,
) -> tuple[dict[str, object], tuple[datetime, str] | None]:
    moment = now or datetime.now(UTC)
    row = db.execute(
        select(_GRANTS)
        .join(
            ParentChildProfileModel,
            ParentChildProfileModel.parent_profile_id == _GRANTS.c.parent_profile_id,
        )
        .where(
            _GRANTS.c.share_grant_id == share_grant_id,
            ParentChildProfileModel.owner_issuer == principal.issuer,
            ParentChildProfileModel.owner_subject == principal.subject,
            ParentChildProfileModel.state == "ACTIVE",
        )
    ).mappings().first()
    if row is None:
        raise _not_found()
    state = effective_state(row, moment)
    content_access = "AVAILABLE" if state is ShareState.ACTIVE else "ENDED"
    if state is ShareState.INVITED or row["accepted_at"] is None:
        return {
            "contract": "ParentShareDeliveryListV1",
            "share_grant_id": share_grant_id,
            "content_access": "ENDED",
            "items": [],
        }, None

    access_ends_at = min(row["revoked_at"] or row["expires_at"], row["expires_at"])
    occurrence_id = None
    delivered_cursor = None
    if cursor:
        delivered_cursor, occurrence_id = cursor

    from sketch2life.infrastructure.lesson_occurrences.tables import OCCURRENCES

    delivered_expr = sa.func.coalesce(
        OCCURRENCES.c.sample_claimed_at,
        sa.func.timezone("UTC", OCCURRENCES.c.scheduled_date.cast(sa.DateTime())),
    )
    statement = (
        select(
            OCCURRENCES.c.occurrence_id,
            OCCURRENCES.c.title,
            delivered_expr.label("delivered_at"),
        )
        .select_from(
            OCCURRENCES.join(
                EnrollmentModel,
                and_(
                    EnrollmentModel.organization_id == OCCURRENCES.c.organization_ref,
                    EnrollmentModel.class_id == OCCURRENCES.c.class_ref,
                    EnrollmentModel.child_id == row["managed_profile_ref"],
                    EnrollmentModel.state == "active",
                    EnrollmentModel.created_at <= delivered_expr,
                ),
            )
        )
        .where(
            OCCURRENCES.c.organization_ref == row["organization_ref"],
            OCCURRENCES.c.class_ref == row["class_ref"],
            OCCURRENCES.c.state.in_(("APPROVED", "SAMPLE_AVAILABLE", "SAMPLE_USED")),
            delivered_expr.is_not(None),
            delivered_expr <= moment,
            delivered_expr >= row["accepted_at"],
            delivered_expr < access_ends_at,
            delivered_expr > moment - timedelta(days=30),
        )
    )
    if delivered_cursor is not None and occurrence_id is not None:
        statement = statement.where(
            or_(
                delivered_expr < delivered_cursor,
                and_(
                    delivered_expr == delivered_cursor,
                    OCCURRENCES.c.occurrence_id < occurrence_id,
                ),
            )
        )
    rows = list(
        db.execute(
            statement.order_by(delivered_expr.desc(), OCCURRENCES.c.occurrence_id.desc())
            .limit(limit + 1)
        ).mappings()
    )
    more = len(rows) > limit
    rows = rows[:limit]
    items = [
        {
            "delivered_at": item["delivered_at"],
            "title": item["title"] if content_access == "AVAILABLE" else None,
        }
        for item in rows
    ]
    next_cursor = (
        (rows[-1]["delivered_at"], str(rows[-1]["occurrence_id"]))
        if more and rows
        else None
    )
    return {
        "contract": "ParentShareDeliveryListV1",
        "share_grant_id": share_grant_id,
        "content_access": content_access,
        "items": items,
    }, next_cursor


__all__ = [
    "accept_teacher_share",
    "create_grant",
    "get_grant",
    "list_deliveries",
    "list_grants",
    "read_teacher_shared_profile",
    "revoke_grant",
]
