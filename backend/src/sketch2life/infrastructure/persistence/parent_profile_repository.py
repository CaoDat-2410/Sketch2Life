"""Transactional PostgreSQL repository for Parent profiles and command receipts."""

from __future__ import annotations

import hashlib
import hmac
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_profiles import ParentCommandResult
from sketch2life.domain.parent_profiles import (
    ParentProfileError,
    ProfileSnapshot,
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

    def get_profile(
        self, *, principal: VerifiedPrincipal, profile_id: UUID
    ) -> dict[str, object]:
        profile = self._owned_profile(principal, profile_id, lock=False)
        revision = self._current_revision(profile)
        return self._view(profile, revision)

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
            replay = self._find_receipt(principal, operation, resource_scope, key_hash)
            if replay is not None:
                return self._replay_or_reject(replay, fingerprint)

            profile = self._owned_profile(principal, profile_id, lock=True)
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

    def _owned_profile(
        self, principal: VerifiedPrincipal, profile_id: UUID, *, lock: bool
    ) -> ParentChildProfileModel:
        statement = select(ParentChildProfileModel).where(
            ParentChildProfileModel.parent_profile_id == profile_id,
            ParentChildProfileModel.owner_issuer == principal.issuer,
            ParentChildProfileModel.owner_subject == principal.subject,
            ParentChildProfileModel.state == "ACTIVE",
            ParentChildProfileModel.deleted_at.is_(None),
        )
        if lock:
            statement = statement.with_for_update()
        profile = self._session.scalar(statement)
        if profile is None:
            raise ParentProfileError(404, "PROFILE_NOT_FOUND", "Profile was not found")
        return profile

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
