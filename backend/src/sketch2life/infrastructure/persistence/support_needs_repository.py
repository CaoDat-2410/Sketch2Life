"""Persistence of the encrypted support needs: the Parent table and the BE1 table (T-12c).

Both adapters keep the same rules. The ciphertext is built by the `SupportNeedsCrypto` port, so
no value and no key is handled here in the clear beyond handing the payload to the port. Receipts
store the new revision, the fingerprint format version and the MAC key id, never a value.
"""

from __future__ import annotations

import hashlib
import hmac
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.support_needs import (
    SealedSupportNeeds,
    SupportNeedsCrypto,
    SupportNeedsUnavailable,
)
from sketch2life.domain.parent_profiles import ParentProfileError, ProfileState
from sketch2life.domain.support_needs import (
    FINGERPRINT_VERSION,
    SupportNeedsPayload,
)
from sketch2life.infrastructure.persistence.be1_models import Be1ProfileSupportNeedsModel
from sketch2life.infrastructure.persistence.parent_models import (
    ParentCommandReceiptModel,
    ParentProfileSupportNeedsModel,
)
from sketch2life.infrastructure.persistence.parent_profile_repository import (
    SqlParentProfileRepository,
)

PARENT_PUT_OPERATION = "put_support_needs"
_UNAVAILABLE = "SUPPORT_NEEDS_UNAVAILABLE"
_UNAVAILABLE_MESSAGE = "Support needs are unavailable"


class SupportNeedsStale(Exception):  # noqa: N818 - the stale-revision condition
    """The expected revision differs from the stored one; carries the stored revision."""

    def __init__(self, current_version: int) -> None:
        super().__init__("stale support needs revision")
        self.current_version = current_version


def _parent_unavailable() -> ParentProfileError:
    return ParentProfileError(503, _UNAVAILABLE, _UNAVAILABLE_MESSAGE)


def _sealed(
    row: ParentProfileSupportNeedsModel | Be1ProfileSupportNeedsModel,
) -> SealedSupportNeeds:
    return SealedSupportNeeds(
        ciphertext=bytes(row.ciphertext),
        nonce=bytes(row.nonce),
        key_id=row.key_id,
        algorithm_version=row.algorithm_version,
    )


class SqlParentSupportNeedsRepository(SqlParentProfileRepository):
    """The Parent family: ownership, the profile row lock, the keyed receipt and the upsert."""

    def get_support_needs(
        self, *, principal: VerifiedPrincipal, profile_id: UUID, crypto: SupportNeedsCrypto
    ) -> dict[str, object]:
        profile = self._owned_profile(principal, profile_id, lock=False, include_pending=True)
        if profile.state == ProfileState.DELETE_PENDING.value:
            raise _pending()
        row = self._fresh_row(profile_id)
        if row is None:
            return _parent_view(profile_id, 0, None)
        try:
            payload = crypto.open(
                family="parent",
                tenant="",
                profile_id=str(profile_id),
                revision=row.revision,
                sealed=_sealed(row),
            )
        except SupportNeedsUnavailable:
            raise _parent_unavailable() from None
        return _parent_view(profile_id, row.revision, payload)

    def put_support_needs(
        self,
        *,
        principal: VerifiedPrincipal,
        profile_id: UUID,
        expected_revision: int,
        payload: SupportNeedsPayload,
        idempotency_key: str,
        crypto: SupportNeedsCrypto,
    ) -> dict[str, object]:
        resource_scope = str(profile_id)
        key_hash = hashlib.sha256(idempotency_key.encode("ascii")).digest()
        principal_ref = self._principal_ref(principal)
        try:
            fingerprint = crypto.fingerprint(
                family="parent",
                tenant="",
                profile_id=resource_scope,
                principal=principal_ref,
                expected_revision=expected_revision,
                payload=payload,
            )
        except SupportNeedsUnavailable:
            raise _parent_unavailable() from None
        with self._session.begin():
            self._lock_scope(principal, PARENT_PUT_OPERATION, resource_scope, key_hash)
            # The profile row lock serializes writers and a concurrent deletion request.
            profile = self._owned_profile(principal, profile_id, lock=True, include_pending=True)
            if profile.state != ProfileState.ACTIVE.value:
                raise _pending()
            replay = self._find_receipt(principal, PARENT_PUT_OPERATION, resource_scope, key_hash)
            if replay is not None:
                return self._replayed(
                    replay,
                    profile_id=profile_id,
                    principal_ref=principal_ref,
                    expected_revision=expected_revision,
                    payload=payload,
                    crypto=crypto,
                )
            row = self._fresh_row(profile_id)
            current = 0 if row is None else row.revision
            if expected_revision != current:
                raise ParentProfileError(
                    409,
                    "STALE_REVISION",
                    "The support needs revision is stale",
                    current_version=current,
                )
            revision = current + 1
            try:
                sealed = crypto.seal(
                    family="parent",
                    tenant="",
                    profile_id=resource_scope,
                    revision=revision,
                    payload=payload,
                )
            except SupportNeedsUnavailable:
                raise _parent_unavailable() from None
            try:
                if row is None:
                    self._session.add(
                        ParentProfileSupportNeedsModel(
                            parent_profile_id=profile_id,
                            revision=revision,
                            ciphertext=sealed.ciphertext,
                            nonce=sealed.nonce,
                            key_id=sealed.key_id,
                            algorithm_version=sealed.algorithm_version,
                        )
                    )
                else:
                    row.revision = revision
                    row.ciphertext = sealed.ciphertext
                    row.nonce = sealed.nonce
                    row.key_id = sealed.key_id
                    row.algorithm_version = sealed.algorithm_version
                    row.updated_at = datetime.now(UTC)
                self._session.flush()
            except IntegrityError:
                raise _parent_unavailable() from None
            self._session.add(
                ParentCommandReceiptModel(
                    receipt_id=uuid4(),
                    principal_issuer=principal.issuer,
                    principal_subject=principal.subject,
                    operation_scope=PARENT_PUT_OPERATION,
                    resource_scope=resource_scope,
                    key_hash=key_hash,
                    request_fingerprint=fingerprint,
                    response_status=200,
                    response_body={
                        "revision": revision,
                        "fp_v": FINGERPRINT_VERSION,
                        "fp_kid": crypto.fingerprint_key_id,
                    },
                )
            )
            return _parent_write(profile_id, revision)

    def _fresh_row(self, profile_id: UUID) -> ParentProfileSupportNeedsModel | None:
        return self._session.scalar(
            select(ParentProfileSupportNeedsModel)
            .where(ParentProfileSupportNeedsModel.parent_profile_id == profile_id)
            .execution_options(populate_existing=True)
        )

    def _replayed(
        self,
        receipt: ParentCommandReceiptModel,
        *,
        profile_id: UUID,
        principal_ref: str,
        expected_revision: int,
        payload: SupportNeedsPayload,
        crypto: SupportNeedsCrypto,
    ) -> dict[str, object]:
        """The stored first answer (ids only): no decryption and no re-encryption."""
        stored = receipt.response_body
        key_id = stored.get("fp_kid")
        revision = stored.get("revision")
        if (
            stored.get("fp_v") != FINGERPRINT_VERSION
            or not isinstance(key_id, str)
            or type(revision) is not int
        ):
            raise _mismatch()
        try:
            expected = crypto.fingerprint(
                family="parent",
                tenant="",
                profile_id=str(profile_id),
                principal=principal_ref,
                expected_revision=expected_revision,
                payload=payload,
                key_id=key_id,
            )
        except SupportNeedsUnavailable:
            raise _parent_unavailable() from None
        if not hmac.compare_digest(bytes(receipt.request_fingerprint), expected):
            raise _mismatch()
        return _parent_write(profile_id, revision)

    @staticmethod
    def _principal_ref(principal: VerifiedPrincipal) -> str:
        return hashlib.sha256(f"{principal.issuer}\n{principal.subject}".encode()).hexdigest()


def _pending() -> ParentProfileError:
    return ParentProfileError(
        409, "INVALID_STATE_TRANSITION", "The profile cannot be changed in its current state"
    )


def _mismatch() -> ParentProfileError:
    return ParentProfileError(
        400,
        "INVALID_IDEMPOTENCY_KEY",
        "The idempotency key was already used for a different request",
    )


def _parent_view(
    profile_id: UUID, revision: int, payload: SupportNeedsPayload | None
) -> dict[str, object]:
    return {
        "contract": "ParentSupportNeedsV1",
        "profile_id": str(profile_id),
        "revision": revision,
        "category": None if payload is None else payload.category,
        "note": None if payload is None else payload.note,
    }


def _parent_write(profile_id: UUID, revision: int) -> dict[str, object]:
    return {
        "contract": "ParentSupportNeedsWriteV1",
        "profile_id": str(profile_id),
        "revision": revision,
    }


class Be1SupportNeedsStore:
    """The BE1 row: read and decrypt, or seal and upsert. Authorization is the router's."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def _fresh_row(self, child_id: str) -> Be1ProfileSupportNeedsModel | None:
        return self._db.scalar(
            select(Be1ProfileSupportNeedsModel)
            .where(Be1ProfileSupportNeedsModel.child_id == child_id)
            .execution_options(populate_existing=True)
        )

    def current_revision(self, child_id: str) -> int:
        revision = self._db.scalar(
            select(Be1ProfileSupportNeedsModel.revision).where(
                Be1ProfileSupportNeedsModel.child_id == child_id
            )
        )
        return 0 if revision is None else int(revision)

    def read(
        self, *, crypto: SupportNeedsCrypto, organization_id: str, child_id: str
    ) -> tuple[int, SupportNeedsPayload | None]:
        row = self._fresh_row(child_id)
        if row is None:
            return 0, None
        payload = crypto.open(
            family="be1",
            tenant=organization_id,
            profile_id=child_id,
            revision=row.revision,
            sealed=_sealed(row),
        )
        return row.revision, payload

    def write(
        self,
        *,
        crypto: SupportNeedsCrypto,
        organization_id: str,
        child_id: str,
        expected_revision: int,
        payload: SupportNeedsPayload,
    ) -> int:
        """Seal under the next revision and store it. The caller holds the profile row lock."""
        row = self._fresh_row(child_id)
        current = 0 if row is None else row.revision
        if expected_revision != current:
            raise SupportNeedsStale(current)
        revision = current + 1
        sealed = crypto.seal(
            family="be1",
            tenant=organization_id,
            profile_id=child_id,
            revision=revision,
            payload=payload,
        )
        if row is None:
            self._db.add(
                Be1ProfileSupportNeedsModel(
                    child_id=child_id,
                    revision=revision,
                    ciphertext=sealed.ciphertext,
                    nonce=sealed.nonce,
                    key_id=sealed.key_id,
                    algorithm_version=sealed.algorithm_version,
                )
            )
        else:
            row.revision = revision
            row.ciphertext = sealed.ciphertext
            row.nonce = sealed.nonce
            row.key_id = sealed.key_id
            row.algorithm_version = sealed.algorithm_version
            row.updated_at = datetime.now(UTC)
        self._db.flush()
        return revision


__all__ = [
    "PARENT_PUT_OPERATION",
    "Be1SupportNeedsStore",
    "SqlParentSupportNeedsRepository",
    "SupportNeedsStale",
]
