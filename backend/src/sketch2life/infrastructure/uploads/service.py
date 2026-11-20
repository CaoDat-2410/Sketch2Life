"""Generic upload sessions (SRS FR-C-12, l.1654-1658; goal v3 T-2a).

The service owns the five session operations for the purposes in ``purposes.POLICIES``. The
session is durable in ``core_upload_sessions`` and ``core_upload_parts`` (resume state, never in
``core_asset_metadata``); every chunk is one object (PutObject, no S3 multipart API) and the final
asset is one PutObject of a known size (l.504, l.1935). An asset is usable exactly when its
``core_asset_metadata`` row exists and the session is ``COMPLETED``.

Failure semantics of ``complete`` (T-2a-DEC-3), so a client knows whether to retry:

* retryable, the session stays ``OPEN`` and nothing is written: incomplete parts, a request body
  that differs from the create-time size or hash, scanner unavailable, object store unavailable,
  a target that no longer accepts bytes;
* terminal, the session becomes ``FAILED`` with an ``error_code`` (committed before the error is
  raised) and the chunk objects are purged: stored bytes that fail their part or aggregate size
  and hash, a declared type the purpose does not accept, a signature that does not match the
  declared type, an infected or non-clean verdict.

Receipts hold successes only (C-D6), so a repeat of a terminal failure answers
``UPLOAD_SESSION_STATE_CONFLICT``. Part rows are kept after abort, expiry and completion (only the
objects are deleted) so the derived revision does not change when the bytes are purged.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from io import BytesIO
from tempfile import SpooledTemporaryFile
from typing import Any, BinaryIO, NoReturn, cast
from uuid import NAMESPACE_URL, uuid4, uuid5

from sqlalchemy import select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.lesson_documents import (
    MalwareDetected,
    MalwareScanner,
    MalwareScannerUnavailable,
)
from sketch2life.application.ports.object_storage import ObjectStorageFailure, ObjectStoragePort
from sketch2life.application.ports.upload_sessions import (
    PARENT_ACCOUNT_SCOPE,
    UPLOAD_PART_SIZE_BYTES,
    UPLOAD_TTL_SECONDS,
    UploadScope,
    UploadTargetNotAccepting,
    UploadTargetResolver,
)
from sketch2life.application.ports.upload_validation import (
    HEADER_BYTES,
    UNSUPPORTED_MEDIA_TYPE,
    UPLOAD_CONTENT_MISMATCH,
    UploadMediaRejected,
    UploadMediaValidator,
    header_matches_media_type,
    is_known_media_type,
    normalize_media_type,
)
from sketch2life.contracts.schemas.upload_sessions import CreateGenericUploadRequestV1
from sketch2life.infrastructure.lesson_library.service import upload_session_revision
from sketch2life.infrastructure.lesson_library.tables import UPLOAD_PARTS, UPLOAD_SESSIONS
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    Be1CommandReceiptModel,
)
from sketch2life.infrastructure.persistence.core_models import (
    CoreAssetMetadataModel,
    CoreAuditEntryModel,
)
from sketch2life.infrastructure.uploads.purposes import (
    GENERIC_PURPOSES,
    IMAGE_EXTENSIONS,
    POLICIES,
    UploadPurposePolicy,
    document_media_type_for,
    safe_document_name,
)
from sketch2life.infrastructure.uploads.resolvers import ResolverFactory

PART_READ_BYTES = 64 * 1024
ASSEMBLY_MEMORY_BYTES = 5 * 1024 * 1024
STATUS_RECEIPT_SCOPE = "POST /v1/upload-sessions"


class UploadSessionError(RuntimeError):
    """A request outcome with a public status and code; the router maps it to the envelope."""

    def __init__(
        self,
        status_code: int,
        code: str,
        *,
        field_errors: list[dict[str, str]] | None = None,
        current_revision: int | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.field_errors = field_errors
        self.current_revision = current_revision
        super().__init__(code)


def _not_found() -> UploadSessionError:
    return UploadSessionError(404, "RESOURCE_NOT_FOUND")


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _fingerprint(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(dict(payload)).encode("utf-8")).hexdigest()


def _json_safe(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def asset_key(prefix: str, upload_id: str) -> str:
    """Final object key and ``asset_ref``: ``{target prefix}{hex}/original`` (T-2a-DEC-2).

    The key is deterministic per session, so a retried complete overwrites instead of leaving an
    orphan, and for a Parent run it has the shape the FR-C-08 purge closure accepts
    (``parent/{run_id}/`` prefix, asset version 1).
    """
    token = uuid5(NAMESPACE_URL, f"sketch2life:upload-asset:{upload_id}").hex
    return f"{prefix}{token}/original"


ASSET_HANDLE_PREFIX = "upl_"


def public_asset_ref(upload_id: str) -> str:
    """The opaque ``asset_ref`` a client sees (SRS l.1692: no object key leaves the API).

    The physical key stays in ``core_upload_sessions.final_asset_ref`` and in
    ``core_asset_metadata.asset_ref`` (FR-C-08 purge keys on it). A consumer (T-2b, T-3b) resolves
    the handle with ``resolve_asset_key``.
    """
    return f"{ASSET_HANDLE_PREFIX}{upload_id}"


def resolve_asset_key(
    db: Session,
    asset_ref: str,
    *,
    owner_scope_kind: str,
    owner_scope_ref: str | None,
    organization_id: str | None,
) -> str | None:
    """Physical key of a completed upload in the given scope, else ``None`` (server side only)."""
    if not asset_ref.startswith(ASSET_HANDLE_PREFIX):
        return None
    row = (
        db.execute(
            select(UPLOAD_SESSIONS.c.final_asset_ref).where(
                UPLOAD_SESSIONS.c.upload_session_id == asset_ref[len(ASSET_HANDLE_PREFIX) :],
                UPLOAD_SESSIONS.c.state == "COMPLETED",
                UPLOAD_SESSIONS.c.purpose.in_(sorted(GENERIC_PURPOSES)),
                UPLOAD_SESSIONS.c.owner_scope_kind == owner_scope_kind,
                UPLOAD_SESSIONS.c.owner_scope_ref.is_not_distinct_from(owner_scope_ref),
                UPLOAD_SESSIONS.c.organization_id.is_not_distinct_from(organization_id),
            )
        )
        .scalars()
        .first()
    )
    return None if row is None else str(row)


def part_key(prefix: str, upload_id: str, part_no: int) -> str:
    """Chunk object key, under the target prefix so the run sweep also covers chunks."""
    return f"{prefix}upload/{upload_id}/parts/{part_no}"


class UploadSessionService:
    def __init__(
        self,
        db: Session,
        *,
        storage: ObjectStoragePort,
        scanner: MalwareScanner,
        validator: UploadMediaValidator | None,
        resolvers: Mapping[str, ResolverFactory],
    ) -> None:
        self.db = db
        self.storage = storage
        self.scanner = scanner
        self.validator = validator
        self._resolver_factories = resolvers

    # ------------------------------------------------------------------ authorization
    def _policy_for(self, purpose: str, principal: VerifiedPrincipal) -> UploadPurposePolicy:
        policy = POLICIES.get(purpose)
        if policy is None or purpose not in GENERIC_PURPOSES:
            raise _not_found()
        identity = self.db.get(AdultIdentityModel, principal.subject)
        if (
            identity is None
            or identity.state != "active"
            or identity.issuer != principal.issuer
            or identity.account_role != policy.account_role
        ):
            raise _not_found()
        return policy

    def _resolver(self, purpose: str) -> UploadTargetResolver:
        factory = self._resolver_factories.get(purpose)
        if factory is None:
            raise _not_found()
        return factory(self.db)

    def _scope_for(
        self, principal: VerifiedPrincipal, purpose: str, target_ref: str
    ) -> tuple[UploadTargetResolver, UploadScope]:
        resolver = self._resolver(purpose)
        scope = resolver.resolve(principal, target_ref)
        if scope is None:
            raise _not_found()
        return resolver, scope

    def _load(
        self, upload_id: str, principal: VerifiedPrincipal, *, for_update: bool
    ) -> tuple[Any, UploadPurposePolicy, UploadTargetResolver, UploadScope]:
        stmt = select(UPLOAD_SESSIONS).where(
            UPLOAD_SESSIONS.c.upload_session_id == upload_id,
            UPLOAD_SESSIONS.c.owner_principal_ref == principal.subject,
            UPLOAD_SESSIONS.c.purpose.in_(sorted(GENERIC_PURPOSES)),
        )
        if for_update:
            stmt = stmt.with_for_update()
        session = self.db.execute(stmt).mappings().one_or_none()
        if session is None:
            raise _not_found()
        policy = self._policy_for(session["purpose"], principal)
        if not policy.enabled:
            raise _not_found()
        resolver, scope = self._scope_for(principal, session["purpose"], session["target_ref"])
        if (
            session["owner_scope_kind"] != scope.owner_scope_kind
            or session["owner_scope_ref"] != scope.owner_scope_ref
            or session["organization_id"] != scope.organization_id
        ):
            raise _not_found()
        return session, policy, resolver, scope

    @staticmethod
    def _ensure_accepting(
        resolver: UploadTargetResolver, principal: VerifiedPrincipal, target_ref: str
    ) -> None:
        try:
            resolver.ensure_accepting(principal, target_ref)
        except UploadTargetNotAccepting:
            raise UploadSessionError(409, "INVALID_STATE_TRANSITION") from None

    # ------------------------------------------------------------------ shared helpers
    def _commit(self) -> None:
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise UploadSessionError(409, "RESOURCE_CONFLICT") from None
        except SQLAlchemyError:
            self.db.rollback()
            raise UploadSessionError(503, "PROVIDER_UNAVAILABLE") from None

    def _parts(self, upload_id: str) -> list[Any]:
        return list(
            self.db.execute(
                select(UPLOAD_PARTS)
                .where(UPLOAD_PARTS.c.upload_session_id == upload_id)
                .order_by(UPLOAD_PARTS.c.part_number)
            )
            .mappings()
            .all()
        )

    def _body(self, session: Any, parts: list[Any]) -> dict[str, Any]:
        body: dict[str, Any] = {
            "contract": "GenericUploadSessionV1",
            "upload_id": session["upload_session_id"],
            "purpose": session["purpose"],
            "target_ref": session["target_ref"],
            "state": session["state"],
            "part_size_bytes": session["chunk_size_bytes"],
            "expected_parts": session["expected_parts"],
            "accepted_parts": [
                {
                    "part_no": part["part_number"],
                    "byte_length": part["byte_size"],
                    "sha256": part["sha256"],
                }
                for part in parts
            ],
            "byte_count": sum(part["byte_size"] for part in parts),
            "expires_at": session["expires_at"],
            "revision": upload_session_revision(session["state"], len(parts)),
            "asset_ref": None,
            "asset_state": None,
            "error_code": None,
        }
        if session["state"] == "COMPLETED":
            body["asset_ref"] = public_asset_ref(session["upload_session_id"])
            body["asset_state"] = "READY"
        elif session["error_code"] is not None:
            body["error_code"] = session["error_code"]
        return body

    def _purge_part_objects(self, upload_id: str) -> None:
        """Delete chunk objects after a commit; the part rows stay (revision stability)."""
        refs = (
            self.db.execute(
                select(UPLOAD_PARTS.c.storage_object_ref).where(
                    UPLOAD_PARTS.c.upload_session_id == upload_id
                )
            )
            .scalars()
            .all()
        )
        for key in refs:
            try:
                self.storage.delete_object(key)
            except ObjectStorageFailure:
                # A leftover object sits under the target prefix: the FR-C-08 run sweep (or the
                # storage lifecycle) removes it; it is unreachable without an active session.
                continue

    def _expire_if_due(self, session: Any) -> bool:
        if session["state"] != "OPEN" or session["expires_at"] > datetime.now(UTC):
            return False
        result = cast(
            CursorResult[Any],
            self.db.execute(
                update(UPLOAD_SESSIONS)
                .where(
                    UPLOAD_SESSIONS.c.upload_session_id == session["upload_session_id"],
                    UPLOAD_SESSIONS.c.state == "OPEN",
                )
                .values(state="EXPIRED")
            ),
        )
        changed = result.rowcount
        self._commit()
        if not changed:
            return False
        self._purge_part_objects(session["upload_session_id"])
        return True

    def _require_open(self, session: Any) -> None:
        if session["state"] == "EXPIRED":
            raise UploadSessionError(410, "UPLOAD_SESSION_EXPIRED")
        if session["state"] != "OPEN":
            raise UploadSessionError(409, "UPLOAD_SESSION_STATE_CONFLICT")
        if self._expire_if_due(session):
            raise UploadSessionError(410, "UPLOAD_SESSION_EXPIRED")

    def _receipt(
        self, principal: VerifiedPrincipal, scope: str, key: str
    ) -> Be1CommandReceiptModel | None:
        return self.db.get(Be1CommandReceiptModel, (principal.subject, scope, key))

    @staticmethod
    def _replay(receipt: Be1CommandReceiptModel, fingerprint: str) -> dict[str, Any]:
        if receipt.request_fingerprint != fingerprint:
            raise UploadSessionError(400, "INVALID_IDEMPOTENCY_KEY")
        return dict(receipt.response_json)

    def _store_receipt(
        self,
        principal: VerifiedPrincipal,
        *,
        scope: str,
        key: str,
        organization_id: str | None,
        fingerprint: str,
        response: dict[str, Any],
    ) -> None:
        self.db.add(
            Be1CommandReceiptModel(
                principal_ref=principal.subject,
                operation_scope=scope,
                idempotency_key=key,
                organization_id=organization_id,
                request_fingerprint=fingerprint,
                response_json=_json_safe(response),
            )
        )

    def _audit(
        self, principal: VerifiedPrincipal, scope: UploadScope, action: str, upload_id: str
    ) -> None:
        # A Parent audit row carries the typed scope hash, never the raw subject (FR-C-08 §8).
        actor = (
            scope.owner_scope_ref
            if scope.owner_scope_kind == PARENT_ACCOUNT_SCOPE
            else principal.subject
        )
        values: dict[str, Any] = {
            "audit_id": str(uuid4()),
            "organization_id": scope.organization_id,
            "owner_scope_kind": scope.owner_scope_kind,
            "actor_ref": actor,
            "action": action,
            "resource_type": "upload_session",
            "resource_id": upload_id,
            "decision": "allowed",
        }
        if scope.owner_scope_ref is not None:
            values["owner_scope_ref"] = scope.owner_scope_ref
        self.db.add(CoreAuditEntryModel(**values))

    # ------------------------------------------------------------------ create
    def create_session(
        self,
        *,
        principal: VerifiedPrincipal,
        payload: CreateGenericUploadRequestV1,
        idempotency_key: str,
    ) -> dict[str, Any]:
        policy = self._policy_for(payload.purpose, principal)
        if not policy.enabled:
            # RUN_AUDIO waits for T-2c (no SRS audio type list, no decoder yet).
            raise UploadSessionError(
                400,
                "INVALID_REQUEST",
                field_errors=[{"field": "purpose", "code": "INVALID_FORMAT"}],
            )
        media_type = normalize_media_type(payload.media_type)
        safe_name = self._safe_name(policy, payload.file_name, media_type)
        if media_type not in policy.media_types:
            raise UploadSessionError(415, policy.unsupported_code)
        if payload.expected_size_bytes > policy.max_bytes:
            raise UploadSessionError(413, policy.too_large_code)
        resolver, scope = self._scope_for(principal, payload.purpose, payload.target_ref)

        receipt_scope = f"{STATUS_RECEIPT_SCOPE} {payload.purpose} {payload.target_ref}"
        fingerprint = _fingerprint(
            {
                "purpose": payload.purpose,
                "target_ref": payload.target_ref,
                "media_type": media_type,
                "expected_size_bytes": payload.expected_size_bytes,
                "expected_sha256": payload.expected_sha256,
                "file_name": safe_name,
            }
        )
        existing = self._receipt(principal, receipt_scope, idempotency_key)
        if existing is not None:
            replay = self._replay(existing, fingerprint)
            self.db.rollback()
            return replay
        self._ensure_accepting(resolver, principal, payload.target_ref)

        upload_id = str(uuid4())
        expires_at = datetime.now(UTC) + timedelta(seconds=UPLOAD_TTL_SECONDS)
        expected_parts = math.ceil(payload.expected_size_bytes / UPLOAD_PART_SIZE_BYTES)
        values: dict[str, Any] = {
            "upload_session_id": upload_id,
            "organization_id": scope.organization_id,
            "owner_scope_kind": scope.owner_scope_kind,
            "owner_principal_ref": principal.subject,
            "purpose": payload.purpose,
            "target_ref": payload.target_ref,
            "safe_file_name": safe_name,
            "expected_media_type": media_type,
            "expected_size_bytes": payload.expected_size_bytes,
            "expected_sha256": payload.expected_sha256,
            "chunk_size_bytes": UPLOAD_PART_SIZE_BYTES,
            "expected_parts": expected_parts,
            "state": "OPEN",
            "expires_at": expires_at,
        }
        if scope.owner_scope_ref is not None:
            values["owner_scope_ref"] = scope.owner_scope_ref
        self.db.execute(UPLOAD_SESSIONS.insert().values(**values))
        body = {
            "contract": "GenericUploadSessionV1",
            "upload_id": upload_id,
            "purpose": payload.purpose,
            "target_ref": payload.target_ref,
            "state": "OPEN",
            "part_size_bytes": UPLOAD_PART_SIZE_BYTES,
            "expected_parts": expected_parts,
            "accepted_parts": [],
            "byte_count": 0,
            "expires_at": expires_at,
            "revision": upload_session_revision("OPEN", 0),
            "asset_ref": None,
            "asset_state": None,
            "error_code": None,
        }
        self._store_receipt(
            principal,
            scope=receipt_scope,
            key=idempotency_key,
            organization_id=scope.organization_id,
            fingerprint=fingerprint,
            response=body,
        )
        try:
            self.db.commit()
        except IntegrityError:
            # A concurrent request with the same key committed first: its session and receipt
            # stand, this transaction (session row included) is rolled back.
            self.db.rollback()
            winner = self._receipt(principal, receipt_scope, idempotency_key)
            if winner is None:
                raise UploadSessionError(409, "RESOURCE_CONFLICT") from None
            replay = self._replay(winner, fingerprint)
            self.db.rollback()
            return replay
        except SQLAlchemyError:
            self.db.rollback()
            raise UploadSessionError(503, "PROVIDER_UNAVAILABLE") from None
        return _json_safe(body)  # type: ignore[no-any-return]

    @staticmethod
    def _safe_name(policy: UploadPurposePolicy, file_name: str | None, media_type: str) -> str:
        if not policy.needs_file_name:
            return "artwork" + IMAGE_EXTENSIONS.get(media_type, ".bin")
        if file_name is None:
            raise UploadSessionError(
                400, "INVALID_REQUEST", field_errors=[{"field": "file_name", "code": "REQUIRED"}]
            )
        safe = safe_document_name(file_name)
        if not safe or document_media_type_for(safe) != media_type:
            raise UploadSessionError(415, policy.unsupported_code)
        return safe

    # ------------------------------------------------------------------ status
    def get_session(self, *, principal: VerifiedPrincipal, upload_id: str) -> dict[str, Any]:
        session, _policy, _resolver, _scope = self._load(upload_id, principal, for_update=False)
        if session["state"] == "EXPIRED" or self._expire_if_due(session):
            raise UploadSessionError(410, "UPLOAD_SESSION_EXPIRED")
        return self._body(session, self._parts(upload_id))

    # ------------------------------------------------------------------ parts
    def put_part(
        self,
        *,
        principal: VerifiedPrincipal,
        upload_id: str,
        part_no: int,
        body: bytes,
        oversize: bool,
        part_sha256: str,
    ) -> dict[str, Any]:
        # Lock the session so no part row lands after a terminal transition (C4, R1-09).
        session, policy, resolver, scope = self._load(upload_id, principal, for_update=True)
        self._require_open(session)
        self._ensure_accepting(resolver, principal, session["target_ref"])
        if oversize:
            raise UploadSessionError(413, policy.too_large_code)
        if not 1 <= part_no <= session["expected_parts"]:
            raise UploadSessionError(
                400, "INVALID_REQUEST", field_errors=[{"field": "part_no", "code": "OUT_OF_RANGE"}]
            )
        start = (part_no - 1) * session["chunk_size_bytes"]
        expected_length = min(session["chunk_size_bytes"], session["expected_size_bytes"] - start)
        if len(body) != expected_length:
            raise UploadSessionError(
                400, "INVALID_REQUEST", field_errors=[{"field": "body", "code": "INVALID_FORMAT"}]
            )
        actual_hash = hashlib.sha256(body).hexdigest()
        if actual_hash != part_sha256:
            raise UploadSessionError(422, "UPLOAD_CHECKSUM_MISMATCH")
        parts = self._parts(upload_id)
        prior = next((part for part in parts if part["part_number"] == part_no), None)
        if prior is not None:
            if prior["sha256"] != actual_hash or prior["byte_size"] != len(body):
                raise UploadSessionError(409, "UPLOAD_PART_CONFLICT")
            return self._part_receipt(session, parts, prior)
        object_key = part_key(scope.object_prefix, upload_id, part_no)
        try:
            self.storage.put_object(
                object_key,
                BytesIO(body),
                content_type="application/octet-stream",
                content_length=len(body),
                metadata={"sha256": actual_hash, "upload-session": upload_id},
            )
        except ObjectStorageFailure:
            raise UploadSessionError(503, "STORAGE_UNAVAILABLE") from None
        self.db.execute(
            UPLOAD_PARTS.insert().values(
                upload_session_id=upload_id,
                part_number=part_no,
                byte_size=len(body),
                sha256=actual_hash,
                storage_object_ref=object_key,
            )
        )
        self._commit()
        stored = self._parts(upload_id)
        created = next(part for part in stored if part["part_number"] == part_no)
        return self._part_receipt(session, stored, created)

    @staticmethod
    def _part_receipt(session: Any, parts: list[Any], part: Any) -> dict[str, Any]:
        return {
            "contract": "GenericUploadPartReceiptV1",
            "upload_id": session["upload_session_id"],
            "part_no": part["part_number"],
            "byte_length": part["byte_size"],
            "sha256": part["sha256"],
            "accepted": True,
            "accepted_part_count": len(parts),
            "byte_count": sum(item["byte_size"] for item in parts),
            "revision": upload_session_revision("OPEN", len(parts)),
        }

    # ------------------------------------------------------------------ complete
    def complete_session(
        self,
        *,
        principal: VerifiedPrincipal,
        upload_id: str,
        expected_size_bytes: int,
        expected_sha256: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        session, policy, resolver, scope = self._load(upload_id, principal, for_update=True)
        receipt_scope = f"POST /v1/upload-sessions/{upload_id}/complete"
        fingerprint = _fingerprint(
            {"expected_size_bytes": expected_size_bytes, "expected_sha256": expected_sha256}
        )
        existing = self._receipt(principal, receipt_scope, idempotency_key)
        if existing is not None:
            replay = self._replay(existing, fingerprint)
            self.db.rollback()
            return replay
        self._require_open(session)
        self._ensure_accepting(resolver, principal, session["target_ref"])
        if (
            expected_size_bytes != session["expected_size_bytes"]
            or expected_sha256 != session["expected_sha256"]
        ):
            # A client error, not bad stored bytes: the session stays OPEN and can be retried.
            raise UploadSessionError(422, "UPLOAD_CHECKSUM_MISMATCH")
        parts = self._parts(upload_id)
        if [part["part_number"] for part in parts] != list(range(1, session["expected_parts"] + 1)):
            raise UploadSessionError(422, "UPLOAD_INCOMPLETE")

        assembled = SpooledTemporaryFile(  # noqa: SIM115 - closed in the finally below
            max_size=ASSEMBLY_MEMORY_BYTES, mode="w+b"
        )
        try:
            total, digest = self._assemble(parts, assembled, session)
            if total != session["expected_size_bytes"] or digest != session["expected_sha256"]:
                self._fail_terminal(upload_id, 422, "UPLOAD_CHECKSUM_MISMATCH")
            media_type = session["expected_media_type"]
            if media_type not in policy.media_types:
                self._fail_terminal(upload_id, 415, policy.unsupported_code)
            self._check_signature(assembled, upload_id, policy, media_type)
            verdict = self._scan(assembled, upload_id)
            self._ensure_accepting(resolver, principal, session["target_ref"])
            key = asset_key(scope.object_prefix, upload_id)
            assembled.seek(0)
            try:
                self.storage.put_object(
                    key,
                    cast(BinaryIO, assembled),
                    content_type=media_type,
                    content_length=total,
                    metadata={
                        "sha256": session["expected_sha256"],
                        "upload-session": upload_id,
                        "scan-verdict": verdict[0],
                    },
                )
            except ObjectStorageFailure:
                raise UploadSessionError(503, "STORAGE_UNAVAILABLE") from None
        finally:
            assembled.close()

        now = datetime.now(UTC)
        asset_values: dict[str, Any] = {
            "asset_ref": key,
            "asset_version": 1,
            "organization_id": scope.organization_id,
            "owner_scope_kind": scope.owner_scope_kind,
            "content_sha256": session["expected_sha256"],
            "media_type": media_type,
            "source_refs": [session["target_ref"]],
            "derived_from_ref": None,
        }
        if scope.owner_scope_ref is not None:
            asset_values["owner_scope_ref"] = scope.owner_scope_ref
        self.db.add(CoreAssetMetadataModel(**asset_values))
        self.db.execute(
            update(UPLOAD_SESSIONS)
            .where(UPLOAD_SESSIONS.c.upload_session_id == upload_id)
            .values(
                state="COMPLETED",
                final_asset_ref=key,
                completed_at=now,
                validated_at=now,
                scan_verdict=verdict[0],
                scanner_name=verdict[1],
                scanner_version=verdict[2],
            )
        )
        self._audit(principal, scope, "upload.complete", upload_id)
        completed = (
            self.db.execute(
                select(UPLOAD_SESSIONS).where(UPLOAD_SESSIONS.c.upload_session_id == upload_id)
            )
            .mappings()
            .one()
        )
        response = self._body(completed, parts)
        response["contract"] = "GenericUploadCompletionV1"
        response["scanner_name"] = verdict[1]
        response["scanner_version"] = verdict[2]
        self._store_receipt(
            principal,
            scope=receipt_scope,
            key=idempotency_key,
            organization_id=scope.organization_id,
            fingerprint=fingerprint,
            response=response,
        )
        self._commit()
        self._purge_part_objects(upload_id)
        return _json_safe(response)  # type: ignore[no-any-return]

    def _assemble(self, parts: list[Any], target: Any, session: Any) -> tuple[int, str]:
        """Stream the stored parts into ``target``; a part that fails its hash ends the session."""
        upload_id = session["upload_session_id"]
        whole = hashlib.sha256()
        total = 0
        for part in parts:
            try:
                stored = self.storage.get_object(part["storage_object_ref"])
            except ObjectStorageFailure:
                raise UploadSessionError(503, "STORAGE_UNAVAILABLE") from None
            if stored is None:
                raise UploadSessionError(503, "STORAGE_UNAVAILABLE")
            part_hash = hashlib.sha256()
            part_size = 0
            try:
                while chunk := stored.body.read(PART_READ_BYTES):
                    part_hash.update(chunk)
                    whole.update(chunk)
                    target.write(chunk)
                    part_size += len(chunk)
                    total += len(chunk)
                    if total > session["expected_size_bytes"]:
                        break
            except ObjectStorageFailure:
                raise UploadSessionError(503, "STORAGE_UNAVAILABLE") from None
            finally:
                stored.body.close()
            if part_size != part["byte_size"] or part_hash.hexdigest() != part["sha256"]:
                self._fail_terminal(upload_id, 422, "UPLOAD_CHECKSUM_MISMATCH")
            if total > session["expected_size_bytes"]:
                self._fail_terminal(upload_id, 422, "UPLOAD_CHECKSUM_MISMATCH")
        return total, whole.hexdigest()

    def _check_signature(
        self, assembled: Any, upload_id: str, policy: UploadPurposePolicy, media_type: str
    ) -> None:
        assembled.seek(0)
        if self.validator is not None:
            try:
                self.validator.validate(assembled, declared_media_type=media_type)
            except UploadMediaRejected as exc:
                if exc.code == UNSUPPORTED_MEDIA_TYPE:
                    self._fail_terminal(upload_id, 415, policy.unsupported_code)
                self._fail_terminal(upload_id, 422, UPLOAD_CONTENT_MISMATCH)
            return
        header = assembled.read(HEADER_BYTES)
        if not is_known_media_type(media_type):
            self._fail_terminal(upload_id, 415, policy.unsupported_code)
        if not header_matches_media_type(media_type, header):
            self._fail_terminal(upload_id, 422, UPLOAD_CONTENT_MISMATCH)

    def _scan(self, assembled: Any, upload_id: str) -> tuple[str, str, str]:
        assembled.seek(0)
        try:
            result = self.scanner.scan(assembled)
        except MalwareDetected:
            self._fail_terminal(upload_id, 422, "MALWARE_DETECTED", verdict="INFECTED")
        except MalwareScannerUnavailable:
            # A scanner is neither storage nor a model provider; fail closed and retryable.
            raise UploadSessionError(503, "PROVIDER_UNAVAILABLE") from None
        if result.verdict != "CLEAN":
            self._fail_terminal(upload_id, 422, "MALWARE_DETECTED", verdict=result.verdict[:16])
        return result.verdict, result.scanner_name, result.scanner_version

    def _fail_terminal(
        self, upload_id: str, status_code: int, code: str, *, verdict: str | None = None
    ) -> NoReturn:
        """Commit ``FAILED`` with a safe code, purge the chunk objects, then raise (F-03)."""
        values: dict[str, Any] = {
            "state": "FAILED",
            "error_code": code,
            "validated_at": datetime.now(UTC),
        }
        if verdict is not None:
            values["scan_verdict"] = verdict
        self.db.execute(
            update(UPLOAD_SESSIONS)
            .where(
                UPLOAD_SESSIONS.c.upload_session_id == upload_id,
                UPLOAD_SESSIONS.c.state == "OPEN",
            )
            .values(**values)
        )
        self._commit()
        self._purge_part_objects(upload_id)
        raise UploadSessionError(status_code, code)

    # ------------------------------------------------------------------ abort
    def abort_session(
        self,
        *,
        principal: VerifiedPrincipal,
        upload_id: str,
        expected_revision: int,
        idempotency_key: str,
    ) -> dict[str, Any]:
        session, _policy, _resolver, scope = self._load(upload_id, principal, for_update=True)
        receipt_scope = f"DELETE /v1/upload-sessions/{upload_id}"
        fingerprint = _fingerprint({"if_match": expected_revision})
        existing = self._receipt(principal, receipt_scope, idempotency_key)
        if existing is not None:
            replay = self._replay(existing, fingerprint)
            self.db.rollback()
            return replay
        if self._expire_if_due(session):
            raise UploadSessionError(410, "UPLOAD_SESSION_EXPIRED")
        if session["state"] == "EXPIRED":
            raise UploadSessionError(410, "UPLOAD_SESSION_EXPIRED")
        if session["state"] not in {"OPEN", "ABORTED"}:
            raise UploadSessionError(409, "UPLOAD_SESSION_STATE_CONFLICT")
        parts = self._parts(upload_id)
        current = upload_session_revision(session["state"], len(parts))
        if current != expected_revision:
            raise UploadSessionError(409, "STALE_REVISION", current_revision=current)
        aborting = session["state"] == "OPEN"
        if aborting:
            self.db.execute(
                update(UPLOAD_SESSIONS)
                .where(UPLOAD_SESSIONS.c.upload_session_id == upload_id)
                .values(state="ABORTED", aborted_at=datetime.now(UTC))
            )
            self._audit(principal, scope, "upload.abort", upload_id)
        refreshed = (
            self.db.execute(
                select(UPLOAD_SESSIONS).where(UPLOAD_SESSIONS.c.upload_session_id == upload_id)
            )
            .mappings()
            .one()
        )
        response = self._body(refreshed, parts)
        self._store_receipt(
            principal,
            scope=receipt_scope,
            key=idempotency_key,
            organization_id=scope.organization_id,
            fingerprint=fingerprint,
            response=response,
        )
        self._commit()
        if aborting:
            # Storage purge after the commit; partial bytes are never used (C4, R1-12).
            self._purge_part_objects(upload_id)
        return _json_safe(response)  # type: ignore[no-any-return]


__all__ = [
    "UploadSessionError",
    "UploadSessionService",
    "asset_key",
    "part_key",
    "public_asset_ref",
    "resolve_asset_key",
]
