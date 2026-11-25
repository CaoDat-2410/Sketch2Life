"""Transactional PostgreSQL adapter for push endpoint ownership and command receipts (T-8b)."""

from __future__ import annotations

import contextlib
from typing import Any, NoReturn, cast

from sqlalchemy import CursorResult, RowMapping, insert, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.push_endpoints import (
    ConcurrentPushEndpointWrite,
    PushEndpointScopeNotFound,
    PushEndpointStoreUnavailable,
)
from sketch2life.domain.push_endpoints import (
    PushEndpointReceipt,
    PushEndpointRecord,
    PushEndpointState,
)
from sketch2life.infrastructure.notifications.tables import PUSH_ENDPOINTS
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    Be1CommandReceiptModel,
)


class SqlPushEndpointStore:
    """Implements the store port; every command commits its mutation and receipt together."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def authorize_parent(self, principal: VerifiedPrincipal) -> str:
        if not principal.subject or not principal.issuer:
            raise PushEndpointScopeNotFound()
        try:
            identity = self._session.get(AdultIdentityModel, principal.subject)
        except SQLAlchemyError:
            self._rollback_unavailable()
        if (
            identity is None
            or identity.state != "active"
            or identity.issuer != principal.issuer
            or identity.account_role != "parent"
        ):
            raise PushEndpointScopeNotFound()
        return str(identity.account_id)

    def get_receipt(
        self, *, principal_ref: str, operation_scope: str, idempotency_key: str
    ) -> PushEndpointReceipt | None:
        try:
            row = self._session.get(
                Be1CommandReceiptModel,
                (principal_ref, operation_scope, idempotency_key),
            )
        except SQLAlchemyError:
            self._rollback_unavailable()
        if row is None:
            return None
        return PushEndpointReceipt(
            request_fingerprint=row.request_fingerprint,
            response_json=dict(row.response_json),
        )

    def find_active(
        self, *, provider_kind: str, endpoint_fingerprint: str
    ) -> PushEndpointRecord | None:
        try:
            row = (
                self._session.execute(
                    select(PUSH_ENDPOINTS).where(
                        PUSH_ENDPOINTS.c.provider_kind == provider_kind,
                        PUSH_ENDPOINTS.c.endpoint_fingerprint == endpoint_fingerprint,
                        PUSH_ENDPOINTS.c.state == PushEndpointState.ACTIVE.value,
                    )
                )
                .mappings()
                .one_or_none()
            )
        except SQLAlchemyError:
            self._rollback_unavailable()
        return _record(row) if row is not None else None

    def find_owned(
        self, *, endpoint_id: str, recipient_account_id: str, for_update: bool
    ) -> PushEndpointRecord | None:
        query = select(PUSH_ENDPOINTS).where(
            PUSH_ENDPOINTS.c.push_endpoint_id == endpoint_id,
            PUSH_ENDPOINTS.c.recipient_account_id == recipient_account_id,
        )
        if for_update:
            query = query.with_for_update()
        try:
            row = self._session.execute(query).mappings().one_or_none()
        except SQLAlchemyError:
            self._rollback_unavailable()
        return _record(row) if row is not None else None

    def insert_endpoint(self, endpoint: PushEndpointRecord) -> None:
        try:
            self._session.execute(insert(PUSH_ENDPOINTS).values(**_values(endpoint)))
        except IntegrityError:
            self._session.rollback()
            raise ConcurrentPushEndpointWrite() from None
        except SQLAlchemyError:
            self._rollback_unavailable()

    def update_endpoint(self, endpoint: PushEndpointRecord) -> None:
        try:
            result = self._session.execute(
                update(PUSH_ENDPOINTS)
                .where(
                    PUSH_ENDPOINTS.c.push_endpoint_id == endpoint.endpoint_id,
                    PUSH_ENDPOINTS.c.recipient_account_id == endpoint.recipient_account_id,
                    PUSH_ENDPOINTS.c.version == endpoint.version - 1,
                )
                .values(
                    state=endpoint.state.value,
                    version=endpoint.version,
                    revoked_at=endpoint.revoked_at,
                )
            )
        except SQLAlchemyError:
            self._rollback_unavailable()
        if cast("CursorResult[Any]", result).rowcount != 1:
            raise ConcurrentPushEndpointWrite() from None

    def add_receipt(
        self,
        *,
        principal_ref: str,
        operation_scope: str,
        idempotency_key: str,
        request_fingerprint: str,
        response_json: dict[str, object],
    ) -> None:
        self._session.add(
            Be1CommandReceiptModel(
                principal_ref=principal_ref,
                operation_scope=operation_scope,
                idempotency_key=idempotency_key,
                organization_id=None,
                request_fingerprint=request_fingerprint,
                response_json=dict(response_json),
            )
        )

    def commit(self) -> None:
        try:
            self._session.commit()
        except IntegrityError:
            self._session.rollback()
            raise ConcurrentPushEndpointWrite() from None
        except SQLAlchemyError:
            self._rollback_unavailable()

    def rollback(self) -> None:
        self._session.rollback()

    def _rollback_unavailable(self) -> NoReturn:
        with contextlib.suppress(SQLAlchemyError):
            self._session.rollback()
        raise PushEndpointStoreUnavailable() from None


def _record(row: RowMapping) -> PushEndpointRecord:
    return PushEndpointRecord(
        endpoint_id=str(row["push_endpoint_id"]),
        recipient_account_id=str(row["recipient_account_id"]),
        platform_kind=str(row["platform_kind"]),
        provider_kind=str(row["provider_kind"]),
        endpoint_ciphertext=bytes(row["endpoint_ciphertext"]),
        endpoint_fingerprint=str(row["endpoint_fingerprint"]),
        state=PushEndpointState(row["state"]),
        version=int(row["version"]),
        registered_at=row["registered_at"],
        last_seen_at=row["last_seen_at"],
        revoked_at=row["revoked_at"],
        app_version=row["app_version"],
    )


def _values(endpoint: PushEndpointRecord) -> dict[str, object]:
    return {
        "push_endpoint_id": endpoint.endpoint_id,
        "recipient_account_id": endpoint.recipient_account_id,
        "platform_kind": endpoint.platform_kind,
        "provider_kind": endpoint.provider_kind,
        "endpoint_ciphertext": endpoint.endpoint_ciphertext,
        "endpoint_fingerprint": endpoint.endpoint_fingerprint,
        "state": endpoint.state.value,
        "version": endpoint.version,
        "registered_at": endpoint.registered_at,
        "last_seen_at": endpoint.last_seen_at,
        "revoked_at": endpoint.revoked_at,
        "app_version": endpoint.app_version,
    }


__all__ = ["SqlPushEndpointStore"]
