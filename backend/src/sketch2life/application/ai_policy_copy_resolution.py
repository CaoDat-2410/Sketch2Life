"""Atomic reconciliation; original copy lifecycle semantics remain foundation-owned."""

from collections.abc import Callable
from datetime import UTC, datetime

from sketch2life.application.ai_policy_commands import _digest
from sketch2life.application.ai_policy_copy_authority import validate_copy_grant
from sketch2life.application.ai_policy_copy_operations import validate_operation
from sketch2life.application.ai_policy_copy_reconciliation import (
    CopyOperationReceiptLease,
    ProviderCopyOperationReceiptVerifier,
)
from sketch2life.application.ports.ai_policy_copy_registry import ProviderCopyInventoryStore
from sketch2life.contracts.schemas.ai_policy_copy import ProviderCopyCommand
from sketch2life.contracts.schemas.ai_policy_copy_lifecycle import (
    CopyLifecycleRecord,
    CopyResolutionObservation,
)
from sketch2life.domain.ai_jobs.provider_copy import (
    CopyKind,
    CopyStatus,
    EvidenceKind,
    ProviderCopy,
    request_cancel,
)
from sketch2life.domain.ai_policy.copy_delivery import DeliveryStatus
from sketch2life.domain.ai_policy.model import PolicyError


def resolution_key(observation: CopyResolutionObservation) -> str:
    proof, binding = observation.proof, observation.binding
    return _digest(
        dict(
            envelope=binding.envelope.model_dump(mode="json"),
            delivery_revision=binding.delivery_revision,
            reference=binding.reference.model_dump(mode="json"),
            outcome=proof.outcome,
            verified=proof.verified,
            evidence_kind=proof.evidence_kind,
            reason_code=proof.reason_code,
        )
    )


def foundation_copy(record: CopyLifecycleRecord) -> ProviderCopy:
    item = record.registration
    return ProviderCopy(
        item.copy_id,
        item.organization_id,
        item.scope_ref,
        CopyKind(item.kind),
        item.original_profile_ref.ref,
        CopyStatus(record.status),
        record.purge_reference.ref if record.purge_reference else None,
        EvidenceKind(record.purge_evidence_kind) if record.purge_evidence_kind else None,
        record.reason_code,
    )


def validate_resolution(
    before: CopyLifecycleRecord, after: CopyLifecycleRecord, observation: CopyResolutionObservation
) -> CopyResolutionObservation:
    """Validate historical observation/transition only, not current execution authority."""
    try:
        observation = CopyResolutionObservation.model_validate(
            observation.model_dump(mode="python"), strict=True
        )
        before = CopyLifecycleRecord.model_validate(before.model_dump(mode="python"), strict=True)
        after = CopyLifecycleRecord.model_validate(after.model_dump(mode="python"), strict=True)
        binding, proof, authority = observation.binding, observation.proof, observation.authority
        envelope = validate_operation(binding.envelope)
        digest = _digest(
            dict(
                action="copy_receipt.verify",
                envelope=envelope.model_dump(mode="json"),
                delivery_revision=binding.delivery_revision,
                reference=binding.reference.model_dump(mode="json"),
            )
        )
        validate_copy_grant(
            authority,
            envelope.principal_id,
            envelope.organization_id,
            digest,
            observation.observed_at,
        )
        if (
            binding.authority_revision != authority.authority_revision
            or proof.binding_digest != _digest(binding.model_dump(mode="json"))
            or (proof.reference != binding.reference or proof.expires_at <= observation.observed_at)
        ):
            raise ValueError("wrong or expired resolution proof")
        if (envelope.command.operation == "purge" and proof.outcome == "cancel_confirmed") or (
            envelope.command.operation == "cancel" and proof.outcome == "deleted"
        ):
            raise ValueError("wrong operation outcome")
        lease = CopyOperationReceiptLease(binding, proof, authority, lambda: None)
        if resolve_lifecycle(lease, before) != after:
            raise ValueError("wrong resolution transition")
        return observation
    except (ValueError, TypeError, AttributeError, PolicyError):
        raise PolicyError("AI_POLICY_INVALID_COPY_RESOLUTION") from None


def resolve_lifecycle(
    lease: CopyOperationReceiptLease, current: CopyLifecycleRecord
) -> CopyLifecycleRecord:
    current = CopyLifecycleRecord.model_validate(current.model_dump(mode="python"), strict=True)
    if current.registration != lease.binding.envelope.target:
        raise PolicyError("AI_POLICY_COPY_SCOPE_MISMATCH")
    lease.confirm()
    if lease.binding.envelope.command.operation == "purge":
        if (
            current.purge_reference is not None
            and current.purge_reference.ref == lease.proof.reference.ref
            and (current.purge_reference != lease.proof.reference)
        ):
            raise PolicyError("AI_POLICY_COPY_RECEIPT_MISMATCH")
        result = lease.apply_purge(foundation_copy(current))
        return CopyLifecycleRecord.model_validate(
            current.model_dump(mode="python")
            | dict(
                revision=current.revision + 1,
                status=result.status.value,
                purge_reference=current.purge_reference
                if current.status == "deleted"
                else lease.proof.reference,
                purge_evidence_kind=result.evidence_kind.value if result.evidence_kind else None,
                reason_code=result.reason_code,
            ),
            strict=True,
        )
    confirmed = lease.cancellation_confirmed()
    kind = current.cancel_evidence_kind
    if confirmed and (kind is None or lease.proof.evidence_kind == "provider"):
        kind = lease.proof.evidence_kind
    return CopyLifecycleRecord.model_validate(
        current.model_dump(mode="python")
        | dict(
            revision=current.revision + 1,
            status=request_cancel(foundation_copy(current)).status.value,
            cancel_confirmed=current.cancel_confirmed or confirmed,
            cancel_evidence_kind=kind,
        ),
        strict=True,
    )


class ProviderCopyReconciliationService:
    def __init__(
        self,
        store: ProviderCopyInventoryStore,
        verifier: ProviderCopyOperationReceiptVerifier,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.store, self.verifier = store, verifier
        self.clock = clock or (lambda: datetime.now(UTC))

    def reconcile(
        self,
        principal_id: str,
        organization_id: str,
        command: ProviderCopyCommand,
        operation_key: str,
        *,
        expected_delivery_revision: int,
        expected_copy_revision: int,
    ) -> CopyLifecycleRecord:
        if type(expected_copy_revision) is not int or expected_copy_revision < 0:
            raise PolicyError("AI_POLICY_INVALID_COPY_LIFECYCLE")
        with self.verifier.verify(
            principal_id,
            organization_id,
            command,
            operation_key,
            expected_revision=expected_delivery_revision,
        ) as lease:
            with self.store.transaction(
                organization_id, command.scope_ref, principal_id=principal_id, for_update=True
            ) as tx:
                if tx.get_operation(operation_key) != lease.binding.envelope:
                    raise PolicyError("AI_POLICY_COPY_OPERATION_CONFLICT")
                delivery = tx.get_delivery(operation_key)
                if (
                    delivery.revision != expected_delivery_revision
                    or delivery.status is not DeliveryStatus.RECEIPT_AVAILABLE
                    or (
                        delivery.last_response is None
                        or delivery.last_response.reference != lease.binding.reference.ref
                        or delivery.last_response.reference_hash != lease.binding.reference.hash
                    )
                ):
                    raise PolicyError("AI_POLICY_COPY_DELIVERY_STALE")
                observation = CopyResolutionObservation(
                    binding=lease.binding,
                    proof=lease.proof,
                    authority=lease.authority,
                    observed_at=self.clock(),
                )
                previous = tx.get_resolution(resolution_key(observation))
                current = tx.get_copy_lifecycle(lease.binding.envelope.target.copy_id)
                if previous is not None:
                    result = current
                else:
                    if current.revision != expected_copy_revision:
                        raise PolicyError("AI_POLICY_COPY_LIFECYCLE_STALE")
                    result = resolve_lifecycle(lease, current)
                    tx.save_resolution(current, result, observation)
                lease.confirm()
            return result
