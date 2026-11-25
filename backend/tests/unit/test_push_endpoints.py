"""Pure and in-memory coverage for the T-8b endpoint command rules."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

import pytest

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.push_endpoints import (
    ConcurrentPushEndpointWrite,
    PushEndpointScopeNotFound,
)
from sketch2life.application.services.push_endpoints import (
    REGISTER_SCOPE,
    REVOKE_SCOPE,
    PushEndpointCommandService,
    PushEndpointError,
    PushEndpointRegistration,
    canonical_revoke_request,
    endpoint_associated_data,
)
from sketch2life.domain.push_endpoints import (
    PushEndpointReceipt,
    PushEndpointRecord,
    PushEndpointState,
    StalePushEndpointVersion,
    revoke_endpoint,
)
from sketch2life.infrastructure.notifications.push_endpoint_fakes import (
    SyntheticEndpointEncryptor,
    SyntheticEndpointFingerprinter,
    SyntheticReceiptFingerprinter,
    SyntheticRegistrationProofVerifier,
)

NOW = datetime(2026, 11, 24, 12, 0, tzinfo=UTC)
PRINCIPAL = VerifiedPrincipal(subject="parent-subject", issuer="issuer", roles=frozenset())
COMMAND = PushEndpointRegistration(
    contract="PushEndpointRegistrationV1",
    platform_kind="WEB",
    provider_kind="WEB_PUSH",
    encrypted_registration_proof="synthetic:proof",
    app_version="1.2.3",
)


class MemoryStore:
    def __init__(self) -> None:
        self.identities = {
            "parent-subject": ("account-parent", "issuer", "parent", "active"),
            "other-subject": ("account-other", "issuer", "parent", "active"),
            "teacher-subject": ("account-teacher", "issuer", "teacher", "active"),
            "disabled-subject": ("account-disabled", "issuer", "parent", "disabled"),
        }
        self.endpoints: dict[str, PushEndpointRecord] = {}
        self.receipts: dict[tuple[str, str, str], PushEndpointReceipt] = {}
        self._pending_endpoints: list[PushEndpointRecord] = []
        self._pending_updates: list[PushEndpointRecord] = []
        self._pending_receipts: list[tuple[tuple[str, str, str], PushEndpointReceipt]] = []

    def authorize_parent(self, principal: VerifiedPrincipal) -> str:
        row = self.identities.get(principal.subject)
        if (
            row is None
            or row[1] != principal.issuer
            or row[2] != "parent"
            or row[3] != "active"
        ):
            raise PushEndpointScopeNotFound()
        return row[0]

    def get_receipt(
        self, *, principal_ref: str, operation_scope: str, idempotency_key: str
    ) -> PushEndpointReceipt | None:
        return self.receipts.get((principal_ref, operation_scope, idempotency_key))

    def find_active(self, *, provider_kind: str, endpoint_fingerprint: str):
        return next(
            (
                endpoint
                for endpoint in self.endpoints.values()
                if endpoint.provider_kind == provider_kind
                and endpoint.endpoint_fingerprint == endpoint_fingerprint
                and endpoint.state is PushEndpointState.ACTIVE
            ),
            None,
        )

    def find_owned(self, *, endpoint_id: str, recipient_account_id: str, for_update: bool):
        endpoint = self.endpoints.get(endpoint_id)
        if endpoint is None or endpoint.recipient_account_id != recipient_account_id:
            return None
        return endpoint

    def insert_endpoint(self, endpoint: PushEndpointRecord) -> None:
        self._pending_endpoints.append(endpoint)

    def update_endpoint(self, endpoint: PushEndpointRecord) -> None:
        self._pending_updates.append(endpoint)

    def add_receipt(
        self,
        *,
        principal_ref: str,
        operation_scope: str,
        idempotency_key: str,
        request_fingerprint: str,
        response_json: dict[str, object],
    ) -> None:
        key = (principal_ref, operation_scope, idempotency_key)
        self._pending_receipts.append(
            (key, PushEndpointReceipt(request_fingerprint, dict(response_json)))
        )

    def commit(self) -> None:
        if any(key in self.receipts for key, _ in self._pending_receipts):
            self.rollback()
            raise ConcurrentPushEndpointWrite()
        for endpoint in self._pending_endpoints:
            collision = self.find_active(
                provider_kind=endpoint.provider_kind,
                endpoint_fingerprint=endpoint.endpoint_fingerprint,
            )
            if collision is not None:
                self.rollback()
                raise ConcurrentPushEndpointWrite()
        for endpoint in self._pending_updates:
            self.endpoints[endpoint.endpoint_id] = endpoint
        for endpoint in self._pending_endpoints:
            self.endpoints[endpoint.endpoint_id] = endpoint
        self.receipts.update(self._pending_receipts)
        self.rollback()

    def rollback(self) -> None:
        self._pending_endpoints.clear()
        self._pending_updates.clear()
        self._pending_receipts.clear()


def _service(
    monkeypatch: pytest.MonkeyPatch,
    *,
    store: MemoryStore | None = None,
    receipt_fingerprinter: SyntheticReceiptFingerprinter | None = None,
    proof_verifier: SyntheticRegistrationProofVerifier | None = None,
    encryptor: SyntheticEndpointEncryptor | None = None,
    endpoint_fingerprinter: SyntheticEndpointFingerprinter | None = None,
) -> tuple[PushEndpointCommandService, MemoryStore]:
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    repository = store or MemoryStore()
    verifier = proof_verifier or SyntheticRegistrationProofVerifier(clock=lambda: NOW)
    receipt = receipt_fingerprinter or SyntheticReceiptFingerprinter(b"r" * 32)
    crypto = encryptor or SyntheticEndpointEncryptor(b"e" * 32)
    endpoint_hmac = endpoint_fingerprinter or SyntheticEndpointFingerprinter(b"f" * 32)
    return (
        PushEndpointCommandService(
            store=repository,
            proof_verifier=verifier,
            encryptor=crypto,
            endpoint_fingerprinter=endpoint_hmac,
            receipt_fingerprinter=receipt,
            clock=lambda: NOW,
        ),
        repository,
    )


def _valid_proof(
    verifier: SyntheticRegistrationProofVerifier,
    *,
    actor_subject: str = "parent-subject",
    endpoint: bytes = b"https://push.invalid/test-token",
    consent_granted: bool = True,
) -> str:
    return verifier.issue(
        actor_subject=actor_subject,
        provider_kind="WEB_PUSH",
        endpoint=endpoint,
        consent_granted=consent_granted,
        now=NOW,
    )


def test_proof_binds_actor_provider_endpoint_and_consent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    verifier = SyntheticRegistrationProofVerifier(clock=lambda: NOW)
    service, store = _service(monkeypatch, proof_verifier=verifier)
    wrong_actor = _valid_proof(verifier, actor_subject="other-subject")
    with pytest.raises(PushEndpointError) as actor_error:
        service.register(
            principal=PRINCIPAL,
            command=replace(COMMAND, encrypted_registration_proof=wrong_actor),
            idempotency_key="actor",
        )
    assert (actor_error.value.status_code, actor_error.value.code) == (400, "INVALID_REQUEST")

    no_consent = _valid_proof(verifier, consent_granted=False)
    with pytest.raises(PushEndpointError) as consent_error:
        service.register(
            principal=PRINCIPAL,
            command=replace(COMMAND, encrypted_registration_proof=no_consent),
            idempotency_key="consent",
        )
    assert (consent_error.value.status_code, consent_error.value.code) == (400, "INVALID_REQUEST")
    assert store.endpoints == {} and store.receipts == {}


def test_fake_verifier_rejected_outside_test(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SKETCH2LIFE_ENV", "production")
    with pytest.raises(RuntimeError, match="local/test"):
        SyntheticRegistrationProofVerifier()


def test_proof_and_key_unavailable_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    store = MemoryStore()
    no_receipt_key = PushEndpointCommandService(store=store, clock=lambda: NOW)
    with pytest.raises(PushEndpointError) as missing_key:
        no_receipt_key.register(principal=PRINCIPAL, command=COMMAND, idempotency_key="no-key")
    assert (missing_key.value.status_code, missing_key.value.code) == (
        503,
        "PUSH_REGISTRATION_UNAVAILABLE",
    )
    assert store.endpoints == {} and store.receipts == {}

    service = PushEndpointCommandService(
        store=store,
        receipt_fingerprinter=SyntheticReceiptFingerprinter(b"r" * 32),
        clock=lambda: NOW,
    )
    with pytest.raises(PushEndpointError) as missing_adapters:
        service.register(principal=PRINCIPAL, command=COMMAND, idempotency_key="no-adapters")
    assert missing_adapters.value.code == "PUSH_REGISTRATION_UNAVAILABLE"


def test_hmac_domains_are_distinct(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    endpoint = SyntheticEndpointFingerprinter(b"k" * 32)
    receipt = SyntheticReceiptFingerprinter(b"k" * 32)
    endpoint_mac = endpoint.fingerprint(provider_kind="WEB_PUSH", endpoint=b"same")
    receipt_mac = receipt.fingerprint(
        operation_scope=REGISTER_SCOPE, canonical_request=b"same"
    )
    assert endpoint_mac != receipt_mac


def test_ciphertext_aad_rejects_wrong_owner(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    encryptor = SyntheticEndpointEncryptor(b"e" * 32)
    associated_data = endpoint_associated_data(
        provider_kind="WEB_PUSH", recipient_account_id="account-a", endpoint_id="endpoint-a"
    )
    ciphertext = encryptor.encrypt(plaintext=b"synthetic-endpoint", associated_data=associated_data)
    wrong_owner = endpoint_associated_data(
        provider_kind="WEB_PUSH", recipient_account_id="account-b", endpoint_id="endpoint-a"
    )
    assert encryptor.matches_context(ciphertext, associated_data)
    assert not encryptor.matches_context(ciphertext, wrong_owner)


def test_response_and_logs_redact_secrets(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    verifier = SyntheticRegistrationProofVerifier(clock=lambda: NOW)
    proof = _valid_proof(verifier)
    service, store = _service(monkeypatch, proof_verifier=verifier)
    request = replace(COMMAND, encrypted_registration_proof=proof)
    result = service.register(principal=PRINCIPAL, command=request, idempotency_key="safe")
    serialized_response = f"{result.endpoint_id}:{result.version}"
    receipt_text = str(store.receipts[(PRINCIPAL.subject, REGISTER_SCOPE, "safe")].response_json)
    endpoint = store.endpoints[result.endpoint_id]
    assert proof not in serialized_response
    assert proof not in receipt_text
    assert proof not in caplog.text
    assert b"push.invalid" not in endpoint.endpoint_ciphertext
    assert set(store.receipts[(PRINCIPAL.subject, REGISTER_SCOPE, "safe")].response_json) == {
        "endpoint_id", "status", "version"
    }


def test_version_transition_and_no_reactivation() -> None:
    endpoint = PushEndpointRecord(
        endpoint_id="endpoint-id",
        recipient_account_id="account-parent",
        platform_kind="WEB",
        provider_kind="WEB_PUSH",
        endpoint_ciphertext=b"ciphertext",
        endpoint_fingerprint="a" * 64,
        state=PushEndpointState.ACTIVE,
        version=1,
        registered_at=NOW,
        last_seen_at=NOW,
        revoked_at=None,
        app_version=None,
    )
    revoked = revoke_endpoint(endpoint, expected_version=1, now=NOW)
    assert revoked.state is PushEndpointState.REVOKED and revoked.version == 2
    assert revoke_endpoint(revoked, expected_version=2, now=NOW) is revoked
    with pytest.raises(StalePushEndpointVersion):
        revoke_endpoint(revoked, expected_version=1, now=NOW)


def test_fingerprint_canonicalization(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    fingerprinter = SyntheticEndpointFingerprinter(b"f" * 32)
    first = fingerprinter.fingerprint(provider_kind="WEB_PUSH", endpoint=b"endpoint bytes")
    repeat = fingerprinter.fingerprint(provider_kind="WEB_PUSH", endpoint=b"endpoint bytes")
    other_provider = fingerprinter.fingerprint(provider_kind="OTHER", endpoint=b"endpoint bytes")
    assert first == repeat and first != other_provider


def test_receipt_scope_includes_target_in_fingerprint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    receipt = SyntheticReceiptFingerprinter(b"r" * 32)
    first = receipt.fingerprint(
        operation_scope=REVOKE_SCOPE,
        canonical_request=canonical_revoke_request("00000000-0000-4000-8000-000000000001", 1),
    )
    other_target = receipt.fingerprint(
        operation_scope=REVOKE_SCOPE,
        canonical_request=canonical_revoke_request("00000000-0000-4000-8000-000000000002", 1),
    )
    other_version = receipt.fingerprint(
        operation_scope=REVOKE_SCOPE,
        canonical_request=canonical_revoke_request("00000000-0000-4000-8000-000000000001", 2),
    )
    other_scope = receipt.fingerprint(operation_scope=REGISTER_SCOPE, canonical_request=b"same")
    assert len({first, other_target, other_version, other_scope}) == 4


def test_duplicate_owner_reuses_reference_and_foreign_collision_is_404(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    verifier = SyntheticRegistrationProofVerifier(clock=lambda: NOW)
    service, store = _service(monkeypatch, proof_verifier=verifier)
    proof = _valid_proof(verifier)
    first = service.register(
        principal=PRINCIPAL,
        command=replace(COMMAND, encrypted_registration_proof=proof),
        idempotency_key="first",
    )
    duplicate_proof = _valid_proof(verifier)
    duplicate = service.register(
        principal=PRINCIPAL,
        command=replace(COMMAND, encrypted_registration_proof=duplicate_proof),
        idempotency_key="second",
    )
    assert duplicate == first and len(store.endpoints) == 1

    foreign_principal = VerifiedPrincipal(
        subject="other-subject", issuer="issuer", roles=frozenset()
    )
    foreign_proof = _valid_proof(verifier, actor_subject=foreign_principal.subject)
    with pytest.raises(PushEndpointError) as collision:
        service.register(
            principal=foreign_principal,
            command=replace(COMMAND, encrypted_registration_proof=foreign_proof),
            idempotency_key="foreign",
        )
    assert (collision.value.status_code, collision.value.code) == (404, "RESOURCE_NOT_FOUND")
    assert len(store.endpoints) == 1
    assert (foreign_principal.subject, REGISTER_SCOPE, "foreign") not in store.receipts


def test_revoke_replay_after_version_increment_and_revoked_reregister(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    verifier = SyntheticRegistrationProofVerifier(clock=lambda: NOW)
    service, store = _service(monkeypatch, proof_verifier=verifier)
    proof = _valid_proof(verifier)
    command = replace(COMMAND, encrypted_registration_proof=proof)
    registered = service.register(principal=PRINCIPAL, command=command, idempotency_key="reg-1")
    service.revoke(
        principal=PRINCIPAL,
        endpoint_id=registered.endpoint_id,
        expected_version=1,
        idempotency_key="del-1",
    )
    assert store.endpoints[registered.endpoint_id].version == 2
    service.revoke(
        principal=PRINCIPAL,
        endpoint_id=registered.endpoint_id,
        expected_version=1,
        idempotency_key="del-1",
    )
    second_proof = _valid_proof(verifier)
    renewed = service.register(
        principal=PRINCIPAL,
        command=replace(COMMAND, encrypted_registration_proof=second_proof),
        idempotency_key="reg-2",
    )
    assert renewed.endpoint_id != registered.endpoint_id and renewed.version == 1
