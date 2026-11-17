"""Strict native hook response bridge, not authority or verified provider outcome."""

from sketch2life.application.ai_policy_copy_operations import validate_operation
from sketch2life.contracts.schemas.ai_policy_copy_delivery import CopyHookResponse
from sketch2life.contracts.schemas.ai_policy_copy_operation import CopyOperationEnvelope
from sketch2life.domain.ai_policy.copy_delivery import DeliveryResponse, HookOutcome
from sketch2life.domain.ai_policy.model import PolicyError


def delivery_response(envelope: CopyOperationEnvelope, raw: CopyHookResponse) -> DeliveryResponse:
    envelope = validate_operation(envelope)
    try:
        proof = CopyHookResponse.model_validate(raw.model_dump(mode="python"), strict=True)
        if (proof.operation_key, proof.binding_digest) != (
            envelope.operation_key,
            envelope.binding_digest,
        ):
            raise ValueError("wrong hook operation")
    except (ValueError, TypeError, AttributeError):
        raise PolicyError("AI_POLICY_COPY_DELIVERY_RESPONSE_MISMATCH") from None
    return DeliveryResponse(
        operation_key=proof.operation_key,
        binding_digest=proof.binding_digest,
        outcome=HookOutcome(proof.outcome),
        reference=proof.reference.ref if proof.reference else None,
        reference_hash=proof.reference.hash if proof.reference else None,
        reason_code=proof.reason_code,
    )
