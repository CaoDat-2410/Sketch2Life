"""Transactional PostgreSQL repository for Parent profiles and command receipts."""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import and_, or_, select, text
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_profiles import (
    ParentCommandResult,
    ParentProfileListResult,
)
from sketch2life.domain.parent_profiles import (
    ParentProfileError,
    ProfileSnapshot,
    ProfileState,
    request_fingerprint,
)
from sketch2life.infrastructure.persistence.parent_models import (
    ParentChildProfileModel,
    ParentCommandReceiptModel,
    ParentProfileRevisionModel,
)


class SqlParentProfileRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create_profile(
        self,
        *,
        principal: VerifiedPrincipal,
        snapshot: ProfileSnapshot,
        idempotency_key: str,
        request_id: str,
    ) -> ParentCommandResult:
        operation = "create_profile"
        resource_scope = "collection"
        key_hash = hashlib.sha256(idempotency_key.encode("ascii")).digest()
        fingerprint = request_fingerprint(
            operation=operation,
            resource_scope=resource_scope,
            payload=snapshot.normalized_payload(),
        )
        with self._session.begin():
            self._lock_scope(principal, operation, resource_scope, key_hash)
            replay = self._find_receipt(principal, operation, resource_scope, key_hash)
            if replay is not None:
                return self._replay_or_reject(replay, fingerprint)

            profile_id = uuid4()
            revision_hash = snapshot.revision_hash()
            profile = ParentChildProfileModel(
                parent_profile_id=profile_id,
                owner_issuer=principal.issuer,
                owner_subject=principal.subject,
                current_revision_no=1,
                data_origin="SYNTHETIC_DEV",
                state="ACTIVE",
                deleted_at=None,
            )
            revision = self._revision(
                profile_id=profile_id,
                revision_no=1,
                principal=principal,
                snapshot=snapshot,
                revision_hash=revision_hash,
            )
            self._session.add_all((profile, revision))
            self._session.flush()
            body: dict[str, object] = {
                "profile_id": str(profile_id),
                "revision_no": 1,
                "revision_hash": revision_hash,
            }
            self._store_receipt(
                principal,
                operation,
                resource_scope,
                key_hash,
                fingerprint,
                201,
                body,
            )
            return ParentCommandResult(201, body)

    def assert_profile_owned(
        self, *, principal: VerifiedPrincipal, profile_id: UUID
    ) -> None:
        with self._session.begin():
            self._owned_profile(principal, profile_id, lock=False, include_pending=True)

    def get_profile(
        self,
        *,
        principal: VerifiedPrincipal,
        profile_id: UUID,
        request_id: str,
    ) -> dict[str, object]:
        profile = self._owned_profile(
            principal, profile_id, lock=False, include_pending=True
        )
        if profile.state == ProfileState.DELETE_PENDING:
            return {
                "profile_id": str(profile.parent_profile_id),
                "state": ProfileState.DELETE_PENDING.value,
                "request_id": request_id,
            }
        if profile.state != ProfileState.ACTIVE:
            raise ParentProfileError(404, "PROFILE_NOT_FOUND", "Profile was not found")
        revision = self._current_revision(profile)
        return self._view(profile, revision)

    def list_profiles(
        self,
        *,
        principal: VerifiedPrincipal,
        limit: int,
        cursor: str | None,
    ) -> ParentProfileListResult:
        if not 1 <= limit <= 100:
            raise ParentProfileError(
                400,
                "INVALID_REQUEST",
                "The request is invalid",
                field_errors=[{"field": "limit", "code": "OUT_OF_RANGE"}],
            )
        cursor_position = self._decode_cursor(cursor) if cursor is not None else None
        statement = select(ParentChildProfileModel).where(
            ParentChildProfileModel.owner_issuer == principal.issuer,
            ParentChildProfileModel.owner_subject == principal.subject,
            ParentChildProfileModel.state == ProfileState.ACTIVE.value,
            ParentChildProfileModel.deleted_at.is_(None),
        )
        if cursor_position is not None:
            created_at, profile_id = cursor_position
            statement = statement.where(
                or_(
                    ParentChildProfileModel.created_at > created_at,
                    and_(
                        ParentChildProfileModel.created_at == created_at,
                        ParentChildProfileModel.parent_profile_id > profile_id,
                    ),
                )
            )
        profiles = list(
            self._session.scalars(
                statement.order_by(
                    ParentChildProfileModel.created_at,
                    ParentChildProfileModel.parent_profile_id,
                ).limit(limit + 1)
            )
        )
        has_more = len(profiles) > limit
        page = profiles[:limit]
        items = [self._view(profile, self._current_revision(profile)) for profile in page]
        next_cursor = None
        if has_more and page:
            last = page[-1]
            next_cursor = self._encode_cursor(last.created_at, last.parent_profile_id)
        return ParentProfileListResult(items=items, next_cursor=next_cursor)

    def patch_profile(
        self,
        *,
        principal: VerifiedPrincipal,
        profile_id: UUID,
        expected_revision: int,
        snapshot: ProfileSnapshot,
        idempotency_key: str,
        request_id: str,
    ) -> ParentCommandResult:
        operation = "patch_profile"
        resource_scope = str(profile_id)
        key_hash = hashlib.sha256(idempotency_key.encode("ascii")).digest()
        fingerprint = request_fingerprint(
            operation=operation,
            resource_scope=resource_scope,
            payload={
                "expected_revision": expected_revision,
                **snapshot.normalized_payload(),
            },
        )
        with self._session.begin():
            self._lock_scope(principal, operation, resource_scope, key_hash)
            profile = self._owned_profile(
                principal, profile_id, lock=True, include_pending=True
            )
            replay = self._find_receipt(principal, operation, resource_scope, key_hash)
            if replay is not None:
                if (
                    profile.state == ProfileState.DELETE_PENDING
                    and replay.response_status == 200
                    and hmac.compare_digest(replay.request_fingerprint, fingerprint)
                ):
                    return ParentCommandResult(
                        409,
                        self._error_body(
                            "INVALID_STATE_TRANSITION",
                            "The profile cannot be changed in its current state",
                            request_id,
                        ),
                    )
                return self._replay_or_reject(replay, fingerprint)

            if profile.state == ProfileState.DELETE_PENDING:
                pending_body = self._error_body(
                    "INVALID_STATE_TRANSITION",
                    "The profile cannot be changed in its current state",
                    request_id,
                )
                return ParentCommandResult(409, pending_body)
            if profile.state != ProfileState.ACTIVE:
                raise ParentProfileError(404, "PROFILE_NOT_FOUND", "Profile was not found")

            if profile.current_revision_no != expected_revision:
                request_body = self._error_body(
                    "STALE_REVISION",
                    "The profile revision is stale",
                    request_id,
                    current_version=profile.current_revision_no,
                )
                self._store_receipt(
                    principal,
                    operation,
                    resource_scope,
                    key_hash,
                    fingerprint,
                    409,
                    request_body,
                )
                return ParentCommandResult(409, request_body)

            revision_no = expected_revision + 1
            revision_hash = snapshot.revision_hash()
            revision = self._revision(
                profile_id=profile_id,
                revision_no=revision_no,
                principal=principal,
                snapshot=snapshot,
                revision_hash=revision_hash,
            )
            self._session.add(revision)
            profile.current_revision_no = revision_no
            profile.updated_at = datetime.now(UTC)
            self._session.flush()
            body = self._view(profile, revision)
            self._store_receipt(
                principal,
                operation,
                resource_scope,
                key_hash,
                fingerprint,
                200,
                body,
            )
            return ParentCommandResult(200, body)

    def delete_profile(
        self,
        *,
        principal: VerifiedPrincipal,
        profile_id: UUID,
        idempotency_key: str,
        request_id: str,
    ) -> ParentCommandResult:
        operation = "delete_profile"
        resource_scope = str(profile_id)
        key_hash = hashlib.sha256(idempotency_key.encode("ascii")).digest()
        fingerprint = request_fingerprint(
            operation=operation,
            resource_scope=resource_scope,
            payload={"profile_id": str(profile_id)},
        )
        with self._session.begin():
            self._lock_scope(principal, operation, resource_scope, key_hash)
            replay = self._find_receipt(principal, operation, resource_scope, key_hash)
            if replay is not None:
                return self._replay_or_reject(replay, fingerprint)

            profile = self._owned_profile(
                principal, profile_id, lock=True, include_pending=True
            )
            if profile.state == ProfileState.DELETE_PENDING:
                conflict_body = self._error_body(
                    "INVALID_STATE_TRANSITION",
                    "The profile cannot be changed in its current state",
                    request_id,
                )
                return ParentCommandResult(409, conflict_body)
            if profile.state != ProfileState.ACTIVE:
                raise ParentProfileError(404, "PROFILE_NOT_FOUND", "Profile was not found")

            profile.state = ProfileState.DELETE_PENDING.value
            profile.updated_at = datetime.now(UTC)
            body: dict[str, object] = {
                "profile_id": str(profile.parent_profile_id),
                "state": ProfileState.DELETE_PENDING.value,
                "request_id": request_id,
            }
            self._store_receipt(
                principal,
                operation,
                resource_scope,
                key_hash,
                fingerprint,
                202,
                body,
            )
            return ParentCommandResult(202, body)

    def _owned_profile(
        self,
        principal: VerifiedPrincipal,
        profile_id: UUID,
        *,
        lock: bool,
        include_pending: bool = False,
    ) -> ParentChildProfileModel:
        statement = select(ParentChildProfileModel).where(
            ParentChildProfileModel.parent_profile_id == profile_id,
            ParentChildProfileModel.owner_issuer == principal.issuer,
            ParentChildProfileModel.owner_subject == principal.subject,
            ParentChildProfileModel.deleted_at.is_(None),
        )
        if not include_pending:
            statement = statement.where(
                ParentChildProfileModel.state == ProfileState.ACTIVE.value
            )
        if lock:
            statement = statement.with_for_update()
        profile = self._session.scalar(statement)
        if profile is None:
            raise ParentProfileError(404, "PROFILE_NOT_FOUND", "Profile was not found")
        return profile

    @staticmethod
    def _encode_cursor(created_at: datetime, profile_id: UUID) -> str:
        payload = json.dumps(
            {
                "created_at": created_at.isoformat(),
                "profile_id": str(profile_id),
                "v": 1,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")

    @staticmethod
    def _decode_cursor(cursor: str) -> tuple[datetime, UUID]:
        try:
            if not cursor or len(cursor) > 2048:
                raise ValueError
            encoded = cursor.encode("ascii")
            payload = base64.b64decode(
                encoded + b"=" * (-len(encoded) % 4), altchars=b"-_", validate=True
            )
            decoded = json.loads(payload)
            if not isinstance(decoded, dict) or set(decoded) != {
                "created_at",
                "profile_id",
                "v",
            }:
                raise ValueError
            if type(decoded["v"]) is not int or decoded["v"] != 1:
                raise ValueError
            raw_created_at = decoded["created_at"]
            raw_profile_id = decoded["profile_id"]
            if not isinstance(raw_created_at, str) or not isinstance(raw_profile_id, str):
                raise ValueError
            created_at = datetime.fromisoformat(raw_created_at)
            if created_at.tzinfo is None or created_at.utcoffset() is None:
                raise ValueError
            return created_at, UUID(raw_profile_id)
        except (
            binascii.Error,
            json.JSONDecodeError,
            UnicodeEncodeError,
            ValueError,
        ) as exc:
            raise ParentProfileError(
                400,
                "INVALID_REQUEST",
                "The request is invalid",
                field_errors=[{"field": "cursor", "code": "INVALID_FORMAT"}],
            ) from exc

    def _current_revision(self, profile: ParentChildProfileModel) -> ParentProfileRevisionModel:
        revision = self._session.scalar(
            select(ParentProfileRevisionModel).where(
                ParentProfileRevisionModel.parent_profile_id == profile.parent_profile_id,
                ParentProfileRevisionModel.revision_no == profile.current_revision_no,
            )
        )
        if revision is None:
            raise RuntimeError("Parent profile current revision invariant is broken")
        return revision

    @staticmethod
    def _view(
        profile: ParentChildProfileModel, revision: ParentProfileRevisionModel
    ) -> dict[str, object]:
        return {
            "profile_id": str(profile.parent_profile_id),
            "revision_no": revision.revision_no,
            "revision_hash": revision.revision_hash,
            "display_name": revision.display_name,
            "age_months": revision.age_months,
            "age_band_ref": revision.age_band_ref,
            "age_band_version": revision.age_band_version,
            "interests_summary": revision.interests_summary,
            "state": profile.state,
            "data_origin": profile.data_origin,
        }

    @staticmethod
    def _revision(
        *,
        profile_id: UUID,
        revision_no: int,
        principal: VerifiedPrincipal,
        snapshot: ProfileSnapshot,
        revision_hash: str,
    ) -> ParentProfileRevisionModel:
        return ParentProfileRevisionModel(
            profile_revision_id=uuid4(),
            parent_profile_id=profile_id,
            revision_no=revision_no,
            age_months=snapshot.age_months,
            age_band_ref=None,
            age_band_version=None,
            display_name=snapshot.display_name,
            interests_summary=snapshot.interests_summary,
            authored_by_issuer=principal.issuer,
            authored_by_subject=principal.subject,
            revision_hash=revision_hash,
        )

    def _lock_scope(
        self,
        principal: VerifiedPrincipal,
        operation: str,
        resource_scope: str,
        key_hash: bytes,
    ) -> None:
        material = "|".join(
            (
                principal.issuer,
                principal.subject,
                operation,
                resource_scope,
                key_hash.hex(),
            )
        ).encode("utf-8")
        lock_key = int.from_bytes(hashlib.sha256(material).digest()[:8], "big", signed=True)
        self._session.execute(
            text("SELECT pg_advisory_xact_lock(:lock_key)"), {"lock_key": lock_key}
        )

    def _find_receipt(
        self,
        principal: VerifiedPrincipal,
        operation: str,
        resource_scope: str,
        key_hash: bytes,
    ) -> ParentCommandReceiptModel | None:
        return self._session.scalar(
            select(ParentCommandReceiptModel).where(
                ParentCommandReceiptModel.principal_issuer == principal.issuer,
                ParentCommandReceiptModel.principal_subject == principal.subject,
                ParentCommandReceiptModel.operation_scope == operation,
                ParentCommandReceiptModel.resource_scope == resource_scope,
                ParentCommandReceiptModel.key_hash == key_hash,
            )
        )

    @staticmethod
    def _replay_or_reject(
        receipt: ParentCommandReceiptModel, fingerprint: bytes
    ) -> ParentCommandResult:
        if not hmac.compare_digest(receipt.request_fingerprint, fingerprint):
            raise ParentProfileError(
                400,
                "INVALID_IDEMPOTENCY_KEY",
                "The idempotency key was already used for a different request",
            )
        return ParentCommandResult(receipt.response_status, dict(receipt.response_body))

    def _store_receipt(
        self,
        principal: VerifiedPrincipal,
        operation: str,
        resource_scope: str,
        key_hash: bytes,
        fingerprint: bytes,
        status_code: int,
        body: dict[str, object],
    ) -> None:
        self._session.add(
            ParentCommandReceiptModel(
                receipt_id=uuid4(),
                principal_issuer=principal.issuer,
                principal_subject=principal.subject,
                operation_scope=operation,
                resource_scope=resource_scope,
                key_hash=key_hash,
                request_fingerprint=fingerprint,
                response_status=status_code,
                response_body=body,
            )
        )

    @staticmethod
    def _error_body(
        code: str,
        message: str,
        request_id: str,
        *,
        current_version: int | None = None,
    ) -> dict[str, object]:
        body: dict[str, object] = {
            "code": code,
            "message": message,
            "correlation_id": request_id,
            "retryable": False,
            "request_id": request_id,
        }
        if current_version is not None:
            body["current_version"] = current_version
        return body
