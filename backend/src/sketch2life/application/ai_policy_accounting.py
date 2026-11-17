"""Guarded resource accounting. Returned snapshots never authorize provider execution."""

from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime

from pydantic import TypeAdapter

from sketch2life.application.ai_policy_commands import _digest
from sketch2life.application.ai_policy_resource_quotes import (
    bind_resource_quote,
    resource_binding_digest,
)
from sketch2life.application.ai_policy_use import PolicyUseLeases
from sketch2life.application.ports.ai_policy_accounting import (
    ResourceAccountingAccess,
    ResourceAccountingBoundary,
)
from sketch2life.application.ports.ai_policy_ledger import (
    LedgerEvent,
    LedgerReceipt,
    ResourceLedgerStore,
    ResourceLedgerTransaction,
)
from sketch2life.contracts.schemas.ai_contract_candidates import OpaqueId
from sketch2life.contracts.schemas.ai_policy_accounting import (
    ResourceReservationRequest,
    ResourceSettlementRequest,
)
from sketch2life.domain.ai_policy.accounting import (
    AccountingChange,
    SettlementOutcome,
    SettlementProof,
)
from sketch2life.domain.ai_policy.model import PolicyError

_ID = TypeAdapter(OpaqueId)


def _identity(principal_id: str, organization_id: str, feature_scope: str) -> None:
    try:
        for value in (principal_id, organization_id, feature_scope):
            _ID.validate_python(value, strict=True)
    except (ValueError, TypeError):
        raise PolicyError("AI_POLICY_INVALID_ACCOUNTING_REQUEST") from None


def _authority(access: ResourceAccountingAccess, principal_id: str, organization_id: str) -> None:
    if (access.authority.principal_id, access.authority.organization_id) != (
        principal_id,
        organization_id,
    ):
        raise PolicyError("AI_POLICY_FORBIDDEN")


def _proof(raw: SettlementProof) -> SettlementProof:
    # A frozen dataclass instance can still have been constructed/mutated by an
    # adapter bypassing __post_init__. Rebuild every nested validated domain type.
    try:
        if not isinstance(raw, SettlementProof):
            raise TypeError("not a proof")
        key = replace(raw.key, definition=replace(raw.key.definition))
        return replace(raw, key=key)
    except (ValueError, TypeError, AttributeError):
        raise PolicyError("AI_POLICY_ACCOUNTING_PROOF_MISMATCH") from None


def _receipt(tx: ResourceLedgerTransaction, expected: LedgerReceipt) -> bool:
    previous = tx.receipt(expected.principal_id, expected.client_request_id)
    if previous is not None and previous != expected:
        raise PolicyError("AI_POLICY_RESOURCE_RECEIPT_CONFLICT")
    return previous is not None


class ResourceAccountingService:
    def __init__(
        self,
        store: ResourceLedgerStore,
        boundary: ResourceAccountingBoundary,
        leases: PolicyUseLeases,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.store, self.boundary, self.leases = store, boundary, leases
        self.clock = clock or (lambda: datetime.now(UTC))

    def _event(self, principal_id: str, fingerprint: str, client_request_id: str) -> LedgerEvent:
        return LedgerEvent(
            "resource."
            + _digest(
                dict(
                    principal_id=principal_id,
                    fingerprint=fingerprint,
                    client_request_id=client_request_id,
                )
            ),
            principal_id,
            self.clock(),
        )

    def reserve(
        self,
        principal_id: str,
        organization_id: str,
        command: ResourceReservationRequest,
    ) -> AccountingChange:
        try:
            command = ResourceReservationRequest.model_validate(
                command.model_dump(mode="python"),
                strict=True,
            )
            feature = command.request.feature_scope
            _identity(principal_id, organization_id, feature)
        except (ValueError, TypeError, AttributeError):
            raise PolicyError("AI_POLICY_INVALID_ACCOUNTING_REQUEST") from None
        fingerprint = _digest(
            dict(
                operation="reserve",
                principal_id=principal_id,
                organization_id=organization_id,
                feature_scope=feature,
                command=command.model_dump(mode="json"),
            )
        )
        lease = (
            self.leases.begin(principal_id, organization_id, command.request)
            if command.phase == "create"
            else self.leases.continue_use(
                principal_id,
                organization_id,
                command.request,
                command.pin,
                command.phase,
            )
        )
        try:
            with lease as observation:
                if observation.pin != command.pin:
                    raise PolicyError("AI_POLICY_PIN_MISMATCH")
                with self.boundary.guard(principal_id, organization_id) as access:
                    _authority(access, principal_id, organization_id)
                    digest = resource_binding_digest(
                        principal_id,
                        organization_id,
                        observation,
                        command.attempt_id,
                    )
                    quote = bind_resource_quote(
                        principal_id,
                        organization_id,
                        observation,
                        command.attempt_id,
                        access.quote(observation, command.attempt_id, digest),
                    )
                    reservation_id = "resource." + _digest(
                        dict(
                            organization_id=organization_id,
                            request_digest=quote.request_digest,
                            attempt_id=quote.attempt_id,
                        )
                    )
                    receipt = LedgerReceipt(
                        principal_id,
                        command.client_request_id,
                        fingerprint,
                        reservation_id,
                        "reserve",
                    )
                    with self.store.transaction(organization_id, feature) as tx:
                        replay = _receipt(tx, receipt)
                        if replay and tx.reservation(reservation_id) is None:
                            raise PolicyError("AI_POLICY_INVALID_LEDGER_STORAGE")
                        result = tx.reserve(
                            quote.terms,
                            reservation_id=reservation_id,
                            request_digest=quote.request_digest,
                            attempt_id=quote.attempt_id,
                            estimated_units=quote.estimated_units,
                            event=self._event(principal_id, fingerprint, command.client_request_id),
                        )
                        if not replay:
                            tx.add_receipt(receipt)
                    return result
        except PolicyError:
            raise
        except Exception:
            raise PolicyError("AI_POLICY_DEPENDENCY_UNAVAILABLE") from None

    def settle(
        self,
        principal_id: str,
        organization_id: str,
        feature_scope: str,
        command: ResourceSettlementRequest,
    ) -> AccountingChange:
        """Backend-scoped accounting cleanup, including after AI eligibility withdrawal."""
        try:
            _identity(principal_id, organization_id, feature_scope)
            command = ResourceSettlementRequest.model_validate(
                command.model_dump(mode="python"),
                strict=True,
            )
        except (ValueError, TypeError, AttributeError):
            raise PolicyError("AI_POLICY_INVALID_ACCOUNTING_REQUEST") from None
        fingerprint = _digest(
            dict(
                operation=command.operation,
                principal_id=principal_id,
                organization_id=organization_id,
                feature_scope=feature_scope,
                command=command.model_dump(mode="json"),
            )
        )
        receipt = LedgerReceipt(
            principal_id,
            command.client_request_id,
            fingerprint,
            command.reservation_id,
            command.operation,
        )
        try:
            with self.boundary.guard(principal_id, organization_id) as access:
                _authority(access, principal_id, organization_id)
                with self.store.transaction(organization_id, feature_scope) as tx:
                    original = tx.reservation(command.reservation_id)
                    if original is None:
                        raise PolicyError("AI_POLICY_RESERVATION_NOT_FOUND")
                    if (original.terms.key.organization_id, original.terms.key.feature_scope) != (
                        organization_id,
                        feature_scope,
                    ):
                        raise PolicyError("AI_POLICY_ACCOUNTING_SCOPE_MISMATCH")
                    proof = _proof(
                        access.verify_settlement(
                            original,
                            command.evidence_ref,
                            command.operation,
                        )
                    )
                    if (
                        command.operation == "consume"
                        and proof.outcome != SettlementOutcome.CONSUME
                    ) or (
                        command.operation == "release"
                        and proof.outcome != SettlementOutcome.RELEASE
                    ):
                        raise PolicyError("AI_POLICY_ACCOUNTING_PROOF_MISMATCH")
                    replay = _receipt(tx, receipt)
                    result = tx.settle(
                        command.reservation_id,
                        proof,
                        event=self._event(principal_id, fingerprint, command.client_request_id),
                    )
                    if replay and not result.replayed:
                        raise PolicyError("AI_POLICY_INVALID_LEDGER_STORAGE")
                    if not replay:
                        tx.add_receipt(receipt)
                return result
        except PolicyError:
            raise
        except Exception:
            raise PolicyError("AI_POLICY_DEPENDENCY_UNAVAILABLE") from None
