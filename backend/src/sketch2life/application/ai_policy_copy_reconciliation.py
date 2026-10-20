"""Exact guarded proof lease; reuses foundation transitions, no persistence/provider execution."""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime

from pydantic import TypeAdapter

from sketch2life.application.ai_policy_commands import _digest
from sketch2life.application.ai_policy_copy_authority import validate_copy_grant
from sketch2life.application.ai_policy_copy_operations import validate_operation
from sketch2life.application.ports.ai_policy_copy_reconciliation import CopyOperationReceiptBoundary
from sketch2life.application.ports.ai_policy_copy_registry import ProviderCopyInventoryStore
from sketch2life.contracts.schemas.ai_contract_candidates import OpaqueId, Sha256Hex
from sketch2life.contracts.schemas.ai_policy import PolicyDefinitionRef
from sketch2life.contracts.schemas.ai_policy_copy import (
    CopyAuthorityGrant,
    CopyReceiptReference,
    ProviderCopyCommand,
)
from sketch2life.contracts.schemas.ai_policy_copy_reconciliation import (
    CopyOperationReceiptBinding,
    VerifiedOperationReceipt,
)
from sketch2life.domain.ai_jobs.provider_copy import (
    CopyKind,
    CopyStatus,
    EvidenceKind,
    ProviderCopy,
    PurgeReceipt,
    ReceiptOutcome,
    apply_receipt,
    request_purge,
)
from sketch2life.domain.ai_policy.copy_delivery import DeliveryStatus
from sketch2life.domain.ai_policy.model import PolicyError


@dataclass(frozen=True, slots=True)
class CopyOperationReceiptLease:
    binding: CopyOperationReceiptBinding
    proof: VerifiedOperationReceipt
    authority: CopyAuthorityGrant
    _confirm: Callable[[], None]
    _active: bool = True

    def confirm(self) -> None:
        if not self._active:
            raise PolicyError("AI_POLICY_COPY_RECEIPT_LEASE_CLOSED")
        self._confirm()

    def apply_purge(self, current: ProviderCopy) -> ProviderCopy:
        self.confirm()
        target = self.binding.envelope.target
        if not isinstance(current, ProviderCopy) or not isinstance(current.kind, CopyKind):
            raise PolicyError("AI_POLICY_COPY_SCOPE_MISMATCH")
        if (
            self.binding.envelope.command.operation != "purge"
            or (
                current.copy_id,
                current.organization_id,
                current.scope_ref,
                current.kind.value,
                current.provider_profile,
            )
            != (
                target.copy_id,
                target.organization_id,
                target.scope_ref,
                target.kind,
                target.original_profile_ref.ref,
            )
            or not isinstance(current.status, CopyStatus)
        ):
            raise PolicyError("AI_POLICY_COPY_SCOPE_MISMATCH")
        proof = self.proof
        return apply_receipt(
            request_purge(current),
            PurgeReceipt(
                proof.reference.ref,
                target.copy_id,
                ReceiptOutcome(proof.outcome),
                proof.verified,
                EvidenceKind(proof.evidence_kind),
                proof.reason_code,
            ),
        )

    def cancellation_confirmed(self, *, actual_only: bool = False) -> bool:
        self.confirm()
        if self.binding.envelope.command.operation != "cancel":
            raise PolicyError("AI_POLICY_COPY_RECEIPT_OPERATION_MISMATCH")
        return (
            self.proof.outcome == "cancel_confirmed"
            and self.proof.verified is True
            and (not actual_only or self.proof.evidence_kind == "provider")
        )


class ProviderCopyOperationReceiptVerifier:
    def __init__(
        self,
        store: ProviderCopyInventoryStore,
        boundary: CopyOperationReceiptBoundary,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.store, self.boundary = store, boundary
        self.clock = clock or (lambda: datetime.now(UTC))

    @contextmanager
    def verify(
        self,
        principal_id: str,
        organization_id: str,
        command: ProviderCopyCommand,
        operation_key: str,
        *,
        expected_revision: int,
    ) -> Iterator[CopyOperationReceiptLease]:
        try:
            command = ProviderCopyCommand.model_validate(
                command.model_dump(mode="python"), strict=True
            )
            for value in (principal_id, organization_id):
                TypeAdapter(OpaqueId).validate_python(value, strict=True)
            TypeAdapter(Sha256Hex).validate_python(operation_key, strict=True)
            if type(expected_revision) is not int or expected_revision < 1:
                raise ValueError("invalid receipt revision")
        except (ValueError, TypeError, AttributeError):
            raise PolicyError("AI_POLICY_INVALID_COPY_REQUEST") from None
        try:
            with self.boundary.guard(principal_id, organization_id) as access:
                read_digest = _digest(
                    dict(
                        action="copy_receipt.read",
                        principal_id=principal_id,
                        organization_id=organization_id,
                        command=command.model_dump(mode="json"),
                        operation_key=operation_key,
                        expected_revision=expected_revision,
                    )
                )
                validate_copy_grant(
                    access.authorize(command, read_digest),
                    principal_id,
                    organization_id,
                    read_digest,
                    self.clock(),
                )
                with self.store.transaction(
                    organization_id, command.scope_ref, principal_id=principal_id
                ) as tx:
                    operation = tx.get_operation(operation_key)
                    if operation is None:
                        raise PolicyError("AI_POLICY_COPY_OPERATION_NOT_FOUND")
                    envelope = validate_operation(operation)
                    if (
                        envelope.principal_id,
                        envelope.organization_id,
                        envelope.command,
                        envelope.operation_key,
                    ) != (principal_id, organization_id, command, operation_key):
                        raise PolicyError("AI_POLICY_COPY_SCOPE_MISMATCH")
                    delivery = tx.get_delivery(operation_key)
                    original = tx.get(envelope.target.copy_id)
                if delivery.revision != expected_revision:
                    raise PolicyError("AI_POLICY_COPY_DELIVERY_STALE")
                response = delivery.last_response
                if (
                    delivery.status is not DeliveryStatus.RECEIPT_AVAILABLE
                    or response is None
                    or (response.reference is None or response.reference_hash is None)
                ):
                    raise PolicyError("AI_POLICY_COPY_RECEIPT_NOT_AVAILABLE")
                if original is None or original.registration != envelope.target:
                    raise PolicyError("AI_POLICY_COPY_REGISTRATION_CONFLICT")
                profile = PolicyDefinitionRef.model_validate(
                    access.resolve_profile(original.initial_copy()).model_dump(mode="python"),
                    strict=True,
                )
                if profile != envelope.target.original_profile_ref:
                    raise PolicyError("AI_POLICY_COPY_PROFILE_MISMATCH")
                reference = CopyReceiptReference(
                    ref=response.reference, hash=response.reference_hash
                )
                digest = _digest(
                    dict(
                        action="copy_receipt.verify",
                        envelope=envelope.model_dump(mode="json"),
                        delivery_revision=delivery.revision,
                        reference=reference.model_dump(mode="json"),
                    )
                )
                grant = validate_copy_grant(
                    access.authorize(command, digest),
                    principal_id,
                    organization_id,
                    digest,
                    self.clock(),
                )
                binding = CopyOperationReceiptBinding(
                    envelope=envelope,
                    delivery_revision=delivery.revision,
                    reference=reference,
                    authority_revision=grant.authority_revision,
                )
                binding_digest = _digest(binding.model_dump(mode="json"))
                raw = access.verify_operation_receipt(binding, binding_digest)
                try:
                    proof = VerifiedOperationReceipt.model_validate(
                        raw.model_dump(mode="python"), strict=True
                    )
                except (ValueError, TypeError, AttributeError):
                    raise PolicyError("AI_POLICY_COPY_RECEIPT_MISMATCH") from None
                if proof.binding_digest != binding_digest or proof.reference != reference:
                    raise PolicyError("AI_POLICY_COPY_RECEIPT_MISMATCH")
                if (command.operation == "cancel" and proof.outcome == "deleted") or (
                    command.operation == "purge" and proof.outcome == "cancel_confirmed"
                ):
                    raise PolicyError("AI_POLICY_COPY_RECEIPT_OPERATION_MISMATCH")

                def confirm() -> None:
                    current = validate_copy_grant(
                        access.authorize(command, digest),
                        principal_id,
                        organization_id,
                        digest,
                        self.clock(),
                    )
                    if current != grant:
                        raise PolicyError("AI_POLICY_COPY_AUTHORITY_MISMATCH")
                    if proof.expires_at <= self.clock():
                        raise PolicyError("AI_POLICY_COPY_RECEIPT_EXPIRED")

                lease = CopyOperationReceiptLease(binding, proof, grant, confirm)
                try:
                    lease.confirm()
                    yield lease
                    lease.confirm()
                finally:
                    object.__setattr__(lease, "_active", False)
        except PolicyError:
            raise
        except Exception:
            raise PolicyError("AI_POLICY_COPY_DEPENDENCY_UNAVAILABLE") from None
