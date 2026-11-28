"""Push endpoint commands: strict inputs, keyed canonical requests, and safe transitions."""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.push_endpoints import (
    ConcurrentPushEndpointWrite,
    InvalidPushRegistrationProof,
    PushEndpointEncryptor,
    PushEndpointFingerprinter,
    PushEndpointScopeNotFound,
    PushEndpointStore,
    PushReceiptFingerprinter,
    PushRegistrationProofVerifier,
    VerifiedPushRegistration,
)
from sketch2life.domain.push_endpoints import (
    PushEndpointReceipt,
    PushEndpointRecord,
    PushEndpointState,
    StalePushEndpointVersion,
    revoke_endpoint,
)

REGISTER_SCOPE = "POST /notifications/push-endpoints"
REVOKE_SCOPE = "DELETE /notifications/push-endpoints"
PROOF_MAX_BYTES = 8192
CIPHERTEXT_MAX_BYTES = 16384
PROOF_MAX_AGE = timedelta(minutes=5)
_APP_VERSION = re.compile(r"^[!-~]{1,64}$", re.ASCII)
_FINGERPRINT = re.compile(r"^[0-9a-f]{64}$", re.ASCII)
_IDEMPOTENCY_KEY = re.compile(r"^[!-~]{1,128}$", re.ASCII)


@dataclass(frozen=True, slots=True)
class PushEndpointRegistration:
    contract: str
    platform_kind: str
    provider_kind: str
    encrypted_registration_proof: str
    app_version: str | None


@dataclass(frozen=True, slots=True)
class PushEndpointResult:
    endpoint_id: str
    version: int


class PushEndpointError(Exception):
    """Safe API refusal; it never carries proof, endpoint, ciphertext, or key material."""

    def __init__(
        self, status_code: int, code: str, *, current_version: int | None = None
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.current_version = current_version
        super().__init__(code)


Clock = Callable[[], datetime]


def utc_now() -> datetime:
    return datetime.now(UTC)


def canonical_registration_request(command: PushEndpointRegistration) -> bytes:
    return json.dumps(
        {
            "app_version": command.app_version,
            "contract": command.contract,
            "encrypted_registration_proof": command.encrypted_registration_proof,
            "platform_kind": command.platform_kind,
            "provider_kind": command.provider_kind,
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def canonical_revoke_request(endpoint_id: str, expected_version: int) -> bytes:
    return json.dumps(
        {
            "contract": "PushEndpointRevokeV1",
            "endpoint_id": endpoint_id,
            "expected_version": expected_version,
        },
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


def endpoint_associated_data(
    *, provider_kind: str, recipient_account_id: str, endpoint_id: str
) -> bytes:
    return json.dumps(
        {
            "endpoint_id": endpoint_id,
            "provider_kind": provider_kind,
            "recipient_account_id": recipient_account_id,
        },
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


class PushEndpointCommandService:
    def __init__(
        self,
        *,
        store: PushEndpointStore,
        proof_verifier: PushRegistrationProofVerifier | None = None,
        encryptor: PushEndpointEncryptor | None = None,
        endpoint_fingerprinter: PushEndpointFingerprinter | None = None,
        receipt_fingerprinter: PushReceiptFingerprinter | None = None,
        clock: Clock = utc_now,
    ) -> None:
        self._store = store
        self._proof_verifier = proof_verifier
        self._encryptor = encryptor
        self._endpoint_fingerprinter = endpoint_fingerprinter
        self._receipt_fingerprinter = receipt_fingerprinter
        self._clock = clock

    def authorize_parent(self, principal: VerifiedPrincipal) -> None:
        try:
            self._store.authorize_parent(principal)
        except PushEndpointScopeNotFound:
            raise _not_found() from None
        finally:
            self._store.rollback()

    def register(
        self,
        *,
        principal: VerifiedPrincipal,
        command: PushEndpointRegistration,
        idempotency_key: str,
    ) -> PushEndpointResult:
        recipient_account_id = self._authorize(principal)
        try:
            _validate_idempotency_key(idempotency_key)
        except PushEndpointError:
            self._store.rollback()
            raise
        try:
            self._validate_registration(command)
        except PushEndpointError:
            self._store.rollback()
            raise
        if command.platform_kind == "ANDROID":
            self._store.rollback()
            raise PushEndpointError(422, "PUSH_PLATFORM_UNSUPPORTED")
        receipt_fingerprint = self._receipt_fingerprint(
            REGISTER_SCOPE, canonical_registration_request(command)
        )
        receipt = self._store.get_receipt(
            principal_ref=principal.subject,
            operation_scope=REGISTER_SCOPE,
            idempotency_key=idempotency_key,
        )
        if receipt is not None:
            try:
                result = self._registration_replay(receipt, receipt_fingerprint)
            finally:
                self._store.rollback()
            return result

        self._require_registration_adapters()
        now = self._clock()
        if now.tzinfo is None:
            self._store.rollback()
            raise _unavailable()
        proof = self._verify_proof(command, principal, now)
        endpoint_fingerprint = self._fingerprint_endpoint(command.provider_kind, proof.endpoint)
        existing = self._store.find_active(
            provider_kind=command.provider_kind,
            endpoint_fingerprint=endpoint_fingerprint,
        )
        if existing is not None:
            if existing.recipient_account_id != recipient_account_id:
                self._store.rollback()
                raise _not_found()
            result = PushEndpointResult(existing.endpoint_id, existing.version)
            self._store.add_receipt(
                principal_ref=principal.subject,
                operation_scope=REGISTER_SCOPE,
                idempotency_key=idempotency_key,
                request_fingerprint=receipt_fingerprint,
                response_json=self._registration_receipt(result),
            )
            self._commit_registration_race(
                principal=principal,
                recipient_account_id=recipient_account_id,
                idempotency_key=idempotency_key,
                request_fingerprint=receipt_fingerprint,
                provider_kind=command.provider_kind,
                endpoint_fingerprint=endpoint_fingerprint,
            )
            return result

        endpoint_id = str(uuid4())
        associated_data = endpoint_associated_data(
            provider_kind=command.provider_kind,
            recipient_account_id=recipient_account_id,
            endpoint_id=endpoint_id,
        )
        ciphertext = self._encrypt(proof.endpoint, associated_data)
        if not 1 <= len(ciphertext) <= CIPHERTEXT_MAX_BYTES:
            self._store.rollback()
            raise _unavailable()
        endpoint = PushEndpointRecord(
            endpoint_id=endpoint_id,
            recipient_account_id=recipient_account_id,
            platform_kind=command.platform_kind,
            provider_kind=command.provider_kind,
            endpoint_ciphertext=ciphertext,
            endpoint_fingerprint=endpoint_fingerprint,
            state=PushEndpointState.ACTIVE,
            version=1,
            registered_at=now,
            last_seen_at=now,
            revoked_at=None,
            app_version=command.app_version,
        )
        result = PushEndpointResult(endpoint_id, 1)
        try:
            self._store.insert_endpoint(endpoint)
            self._store.add_receipt(
                principal_ref=principal.subject,
                operation_scope=REGISTER_SCOPE,
                idempotency_key=idempotency_key,
                request_fingerprint=receipt_fingerprint,
                response_json=self._registration_receipt(result),
            )
            self._store.commit()
        except ConcurrentPushEndpointWrite:
            return self._resolve_registration_race(
                principal=principal,
                recipient_account_id=recipient_account_id,
                idempotency_key=idempotency_key,
                request_fingerprint=receipt_fingerprint,
                provider_kind=command.provider_kind,
                endpoint_fingerprint=endpoint_fingerprint,
            )
        return result

    def revoke(
        self,
        *,
        principal: VerifiedPrincipal,
        endpoint_id: str,
        expected_version: int,
        idempotency_key: str,
    ) -> None:
        recipient_account_id = self._authorize(principal)
        try:
            _validate_idempotency_key(idempotency_key)
        except PushEndpointError:
            self._store.rollback()
            raise
        try:
            endpoint_id = _parse_endpoint_id(endpoint_id)
        except PushEndpointError:
            self._store.rollback()
            raise
        if type(expected_version) is not int or expected_version < 1:
            self._store.rollback()
            raise _invalid_request()
        endpoint = self._store.find_owned(
            endpoint_id=endpoint_id,
            recipient_account_id=recipient_account_id,
            for_update=True,
        )
        if endpoint is None:
            self._store.rollback()
            raise _not_found()
        request_fingerprint = self._receipt_fingerprint(
            REVOKE_SCOPE, canonical_revoke_request(endpoint_id, expected_version)
        )
        receipt = self._store.get_receipt(
            principal_ref=principal.subject,
            operation_scope=REVOKE_SCOPE,
            idempotency_key=idempotency_key,
        )
        if receipt is not None:
            try:
                self._revoke_replay(receipt, request_fingerprint)
            finally:
                self._store.rollback()
            return
        try:
            changed = revoke_endpoint(
                endpoint, expected_version=expected_version, now=self._clock()
            )
        except StalePushEndpointVersion as exc:
            self._store.rollback()
            raise PushEndpointError(
                409, "STALE_REVISION", current_version=exc.current_version
            ) from None
        self._store.add_receipt(
            principal_ref=principal.subject,
            operation_scope=REVOKE_SCOPE,
            idempotency_key=idempotency_key,
            request_fingerprint=request_fingerprint,
            response_json={"status": 204},
        )
        try:
            if changed is not endpoint:
                self._store.update_endpoint(changed)
            self._store.commit()
        except ConcurrentPushEndpointWrite:
            # A locked row plus the unique receipt key makes this exceptional. Re-load with the
            # same scope before deciding whether this was a safe replay.
            self._store.rollback()
            self._authorize(principal)
            current = self._store.find_owned(
                endpoint_id=endpoint_id,
                recipient_account_id=recipient_account_id,
                for_update=True,
            )
            if current is None:
                self._store.rollback()
                raise _not_found() from None
            receipt = self._store.get_receipt(
                principal_ref=principal.subject,
                operation_scope=REVOKE_SCOPE,
                idempotency_key=idempotency_key,
            )
            if receipt is not None:
                try:
                    self._revoke_replay(receipt, request_fingerprint)
                finally:
                    self._store.rollback()
                return
            if current.version != expected_version:
                self._store.rollback()
                raise PushEndpointError(
                    409, "STALE_REVISION", current_version=current.version
                ) from None
            self._store.rollback()
            raise _unavailable() from None

    def _authorize(self, principal: VerifiedPrincipal) -> str:
        try:
            return self._store.authorize_parent(principal)
        except PushEndpointScopeNotFound:
            self._store.rollback()
            raise _not_found() from None

    @staticmethod
    def _validate_registration(command: PushEndpointRegistration) -> None:
        if not isinstance(command, PushEndpointRegistration):
            raise _invalid_request()
        if (
            not isinstance(command.contract, str)
            or command.contract != "PushEndpointRegistrationV1"
            or not isinstance(command.platform_kind, str)
            or not isinstance(command.provider_kind, str)
            or not isinstance(command.encrypted_registration_proof, str)
        ):
            raise _invalid_request()
        allowed_pairs = {("WEB", "WEB_PUSH"), ("ANDROID", "ANDROID_PUSH")}
        if (command.platform_kind, command.provider_kind) not in allowed_pairs:
            raise _invalid_request()
        try:
            proof_size = len(command.encrypted_registration_proof.encode("utf-8"))
        except (AttributeError, UnicodeEncodeError):
            raise _invalid_request() from None
        if not 1 <= proof_size <= PROOF_MAX_BYTES:
            raise _invalid_request()
        if command.app_version is not None and (
            not isinstance(command.app_version, str)
            or not _APP_VERSION.fullmatch(command.app_version)
        ):
            raise _invalid_request()

    def _receipt_fingerprint(self, scope: str, request: bytes) -> str:
        adapter = self._receipt_fingerprinter
        if adapter is None:
            self._store.rollback()
            raise _unavailable()
        try:
            value = adapter.fingerprint(operation_scope=scope, canonical_request=request)
        except Exception:
            self._store.rollback()
            raise _unavailable() from None
        if not isinstance(value, str) or not _FINGERPRINT.fullmatch(value):
            self._store.rollback()
            raise _unavailable()
        return value

    def _require_registration_adapters(self) -> None:
        if any(
            adapter is None
            for adapter in (
                self._proof_verifier,
                self._encryptor,
                self._endpoint_fingerprinter,
            )
        ):
            self._store.rollback()
            raise _unavailable()

    def _verify_proof(
        self,
        command: PushEndpointRegistration,
        principal: VerifiedPrincipal,
        now: datetime,
    ) -> VerifiedPushRegistration:
        assert self._proof_verifier is not None
        try:
            proof = self._proof_verifier.verify(
                proof=command.encrypted_registration_proof,
                actor_subject=principal.subject,
                provider_kind=command.provider_kind,
            )
        except InvalidPushRegistrationProof:
            self._store.rollback()
            raise _invalid_request() from None
        except Exception:
            self._store.rollback()
            raise _unavailable() from None
        if not isinstance(proof, VerifiedPushRegistration):
            self._store.rollback()
            raise _unavailable()
        if (
            proof.actor_subject != principal.subject
            or proof.provider_kind != command.provider_kind
            or proof.consent_granted is not True
            or not isinstance(proof.endpoint, bytes)
            or not proof.endpoint
            or len(proof.endpoint) > PROOF_MAX_BYTES
            or not isinstance(proof.verified_at, datetime)
            or proof.verified_at.tzinfo is None
            or not isinstance(proof.expires_at, datetime)
            or proof.expires_at.tzinfo is None
            or proof.verified_at > now
            or proof.expires_at <= now
            or now - proof.verified_at > PROOF_MAX_AGE
        ):
            self._store.rollback()
            raise _invalid_request()
        return proof

    def _fingerprint_endpoint(self, provider_kind: str, endpoint: bytes) -> str:
        adapter = self._endpoint_fingerprinter
        if adapter is None:
            self._store.rollback()
            raise _unavailable()
        try:
            value = adapter.fingerprint(provider_kind=provider_kind, endpoint=endpoint)
        except Exception:
            self._store.rollback()
            raise _unavailable() from None
        if not isinstance(value, str) or not _FINGERPRINT.fullmatch(value):
            self._store.rollback()
            raise _unavailable()
        return value

    def _encrypt(self, endpoint: bytes, associated_data: bytes) -> bytes:
        assert self._encryptor is not None
        try:
            ciphertext = self._encryptor.encrypt(
                plaintext=endpoint, associated_data=associated_data
            )
        except Exception:
            self._store.rollback()
            raise _unavailable() from None
        if not isinstance(ciphertext, bytes):
            self._store.rollback()
            raise _unavailable()
        return ciphertext

    @staticmethod
    def _registration_receipt(result: PushEndpointResult) -> dict[str, object]:
        return {"endpoint_id": result.endpoint_id, "status": 201, "version": result.version}

    @staticmethod
    def _registration_replay(
        receipt: PushEndpointReceipt, fingerprint: str
    ) -> PushEndpointResult:
        if receipt.request_fingerprint != fingerprint:
            raise PushEndpointError(400, "INVALID_IDEMPOTENCY_KEY")
        body = receipt.response_json
        endpoint_id, version = body.get("endpoint_id"), body.get("version")
        if (
            body.get("status") != 201
            or not isinstance(endpoint_id, str)
            or type(version) is not int
            or version < 1
        ):
            raise _unavailable()
        try:
            if str(UUID(endpoint_id)) != endpoint_id:
                raise ValueError
        except (ValueError, AttributeError, TypeError):
            raise _unavailable() from None
        return PushEndpointResult(endpoint_id, version)

    @staticmethod
    def _revoke_replay(receipt: PushEndpointReceipt, fingerprint: str) -> None:
        if receipt.request_fingerprint != fingerprint:
            raise PushEndpointError(400, "INVALID_IDEMPOTENCY_KEY")
        if receipt.response_json.get("status") != 204:
            raise _unavailable()

    def _commit_registration_race(
        self,
        *,
        principal: VerifiedPrincipal,
        recipient_account_id: str,
        idempotency_key: str,
        request_fingerprint: str,
        provider_kind: str,
        endpoint_fingerprint: str,
    ) -> None:
        try:
            self._store.commit()
        except ConcurrentPushEndpointWrite:
            self._resolve_registration_race(
                principal=principal,
                recipient_account_id=recipient_account_id,
                idempotency_key=idempotency_key,
                request_fingerprint=request_fingerprint,
                provider_kind=provider_kind,
                endpoint_fingerprint=endpoint_fingerprint,
            )

    def _resolve_registration_race(
        self,
        *,
        principal: VerifiedPrincipal,
        recipient_account_id: str,
        idempotency_key: str,
        request_fingerprint: str,
        provider_kind: str,
        endpoint_fingerprint: str,
    ) -> PushEndpointResult:
        self._store.rollback()
        current_account = self._authorize(principal)
        if current_account != recipient_account_id:
            self._store.rollback()
            raise _not_found()
        receipt = self._store.get_receipt(
            principal_ref=principal.subject,
            operation_scope=REGISTER_SCOPE,
            idempotency_key=idempotency_key,
        )
        if receipt is not None:
            try:
                result = self._registration_replay(receipt, request_fingerprint)
            finally:
                self._store.rollback()
            return result
        existing = self._store.find_active(
            provider_kind=provider_kind,
            endpoint_fingerprint=endpoint_fingerprint,
        )
        if existing is None:
            self._store.rollback()
            raise _unavailable()
        if existing.recipient_account_id != recipient_account_id:
            self._store.rollback()
            raise _not_found()
        result = PushEndpointResult(existing.endpoint_id, existing.version)
        self._store.add_receipt(
            principal_ref=principal.subject,
            operation_scope=REGISTER_SCOPE,
            idempotency_key=idempotency_key,
            request_fingerprint=request_fingerprint,
            response_json=self._registration_receipt(result),
        )
        try:
            self._store.commit()
        except ConcurrentPushEndpointWrite:
            self._store.rollback()
            receipt = self._store.get_receipt(
                principal_ref=principal.subject,
                operation_scope=REGISTER_SCOPE,
                idempotency_key=idempotency_key,
            )
            if receipt is None:
                raise _unavailable() from None
            result = self._registration_replay(receipt, request_fingerprint)
            self._store.rollback()
        return result


def _parse_endpoint_id(value: str) -> str:
    try:
        parsed = UUID(value)
    except (ValueError, AttributeError, TypeError):
        raise _invalid_request() from None
    canonical = str(parsed)
    if value.lower() != canonical:
        raise _invalid_request()
    return canonical


def _validate_idempotency_key(value: str) -> None:
    if not isinstance(value, str) or not _IDEMPOTENCY_KEY.fullmatch(value):
        raise _invalid_request()


def _invalid_request() -> PushEndpointError:
    return PushEndpointError(400, "INVALID_REQUEST")


def _not_found() -> PushEndpointError:
    return PushEndpointError(404, "RESOURCE_NOT_FOUND")


def _unavailable() -> PushEndpointError:
    return PushEndpointError(503, "PUSH_REGISTRATION_UNAVAILABLE")


__all__ = [
    "PushEndpointCommandService",
    "PushEndpointError",
    "PushEndpointRegistration",
    "PushEndpointResult",
    "REGISTER_SCOPE",
    "REVOKE_SCOPE",
    "canonical_registration_request",
    "canonical_revoke_request",
    "endpoint_associated_data",
]
