"""Validate historical authority against immutable before-state and current transition."""

from sketch2life.application.ai_policy_copy_authority import validate_copy_grant
from sketch2life.application.ai_policy_copy_dispatch import dispatch_binding
from sketch2life.application.ai_policy_copy_operations import validate_operation
from sketch2life.contracts.schemas.ai_policy_copy_delivery import CopyDeliveryAuthorityEvidence
from sketch2life.contracts.schemas.ai_policy_copy_operation import CopyOperationEnvelope
from sketch2life.domain.ai_policy.copy_delivery import (
    DeliveryState,
    DeliveryStatus,
    claim_delivery,
    finish_delivery,
)
from sketch2life.domain.ai_policy.model import PolicyError


def validate_delivery_evidence(
    evidence: CopyDeliveryAuthorityEvidence,
    envelope: CopyOperationEnvelope,
    before: DeliveryState,
    current: DeliveryState,
) -> CopyDeliveryAuthorityEvidence:
    try:
        evidence = CopyDeliveryAuthorityEvidence.model_validate(
            evidence.model_dump(mode="python"), strict=True
        )
        envelope = validate_operation(envelope)
        if (
            evidence.principal_id,
            evidence.organization_id,
            evidence.scope_ref,
            evidence.operation_key,
            evidence.state_revision,
        ) != (
            envelope.principal_id,
            envelope.organization_id,
            envelope.command.scope_ref,
            envelope.operation_key,
            before.revision,
        ) or (before.operation_key, before.binding_digest) != (
            envelope.operation_key,
            envelope.binding_digest,
        ):
            raise ValueError("wrong phase source")
        validate_copy_grant(
            evidence.authority.grant,
            envelope.principal_id,
            envelope.organization_id,
            dispatch_binding(envelope, before, evidence.phase),
            evidence.observed_at,
        )
        if evidence.authority.claim_deadline <= evidence.observed_at:
            raise ValueError("expired phase deadline")
        if evidence.phase == "claim":
            if current.claim_token is None or current.claim_started_at is None:
                raise ValueError("claim missing")
            expected = claim_delivery(
                before,
                expected_revision=before.revision,
                token=current.claim_token,
                now=current.claim_started_at,
                expires_at=evidence.authority.claim_deadline,
            )
            if current.claim_started_at > evidence.observed_at:
                raise ValueError("future claim")
        else:
            if (
                before.status is not DeliveryStatus.IN_FLIGHT
                or before.claim_started_at is None
                or (
                    before.claim_expires_at is None
                    or not before.claim_started_at <= evidence.observed_at < before.claim_expires_at
                )
            ):
                raise ValueError("invalid phase interval")
            if evidence.phase == "dispatch":
                expected = before
            else:
                if current.last_response is None or before.claim_token is None:
                    raise ValueError("response missing")
                expected = finish_delivery(
                    before,
                    current.last_response,
                    expected_revision=before.revision,
                    token=before.claim_token,
                    now=evidence.observed_at,
                )
        if expected != current:
            raise ValueError("phase state mismatch")
        return evidence
    except (ValueError, TypeError, AttributeError, PolicyError):
        raise PolicyError("AI_POLICY_INVALID_DELIVERY_AUTHORITY_EVIDENCE") from None
