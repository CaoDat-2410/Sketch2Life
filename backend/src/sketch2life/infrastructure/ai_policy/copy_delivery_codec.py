"""Strict delivery snapshot persistence, not authority or provider evidence verification."""

import json
from typing import Any

from sketch2life.contracts.schemas.ai_policy_copy import CopyReceiptReference
from sketch2life.contracts.schemas.ai_policy_copy_delivery import (
    CopyDeliveryRecord,
    CopyHookResponse,
)
from sketch2life.domain.ai_policy.copy_delivery import (
    DeliveryResponse,
    DeliveryState,
    DeliveryStatus,
    HookOutcome,
)
from sketch2life.domain.ai_policy.model import PolicyError


def encode_delivery(state: DeliveryState) -> dict[str, Any]:
    response = state.last_response
    record = CopyDeliveryRecord(
        operation_key=state.operation_key,
        binding_digest=state.binding_digest,
        revision=state.revision,
        status=state.status.value,
        claim_token=state.claim_token,
        claim_started_at=state.claim_started_at,
        claim_expires_at=state.claim_expires_at,
        used_tokens=state.used_tokens,
        last_response=CopyHookResponse(
            operation_key=response.operation_key,
            binding_digest=response.binding_digest,
            outcome=response.outcome.value,
            reason_code=response.reason_code,
            reference=CopyReceiptReference(ref=response.reference, hash=response.reference_hash)
            if response.reference is not None and response.reference_hash is not None
            else None,
        )
        if response
        else None,
    )
    return record.model_dump(mode="json")


def decode_delivery(snapshot: object) -> DeliveryState:
    try:
        record = CopyDeliveryRecord.model_validate_json(json.dumps(snapshot), strict=True)
        proof = record.last_response
        return DeliveryState(
            operation_key=record.operation_key,
            binding_digest=record.binding_digest,
            revision=record.revision,
            status=DeliveryStatus(record.status),
            claim_token=record.claim_token,
            claim_started_at=record.claim_started_at,
            claim_expires_at=record.claim_expires_at,
            used_tokens=record.used_tokens,
            last_response=DeliveryResponse(
                operation_key=proof.operation_key,
                binding_digest=proof.binding_digest,
                outcome=HookOutcome(proof.outcome),
                reason_code=proof.reason_code,
                reference=proof.reference.ref if proof.reference else None,
                reference_hash=proof.reference.hash if proof.reference else None,
            )
            if proof
            else None,
        )
    except (TypeError, ValueError, PolicyError):
        raise PolicyError("AI_POLICY_INVALID_COPY_DELIVERY_STORAGE") from None
