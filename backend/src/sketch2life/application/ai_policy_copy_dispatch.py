"""Current-authorized durable claim -> hook outside DB -> guarded response recording."""

from collections.abc import Callable
from dataclasses import asdict
from datetime import UTC, datetime
from uuid import uuid4

from pydantic import TypeAdapter

from sketch2life.application.ai_policy_commands import _digest
from sketch2life.application.ai_policy_copy_authority import validate_copy_grant
from sketch2life.application.ai_policy_copy_delivery import delivery_response
from sketch2life.application.ai_policy_copy_operations import validate_operation
from sketch2life.application.ports.ai_policy_copy_dispatch import (
    CopyDispatchAccess,
    CopyDispatchBoundary,
    DeliveryPhase,
)
from sketch2life.application.ports.ai_policy_copy_hook import ProviderCopyOperationHook
from sketch2life.application.ports.ai_policy_copy_registry import ProviderCopyInventoryStore
from sketch2life.contracts.schemas.ai_contract_candidates import OpaqueId, Sha256Hex
from sketch2life.contracts.schemas.ai_policy import PolicyDefinitionRef
from sketch2life.contracts.schemas.ai_policy_copy import ProviderCopyCommand
from sketch2life.contracts.schemas.ai_policy_copy_delivery import CopyDeliveryAuthority
from sketch2life.contracts.schemas.ai_policy_copy_operation import CopyOperationEnvelope
from sketch2life.domain.ai_policy.copy_delivery import DeliveryResponse, DeliveryState, HookOutcome
from sketch2life.domain.ai_policy.model import PolicyError


def dispatch_binding(
    envelope: CopyOperationEnvelope, state: DeliveryState, phase: DeliveryPhase
) -> str:
    return _digest(
        dict(
            action="copy_delivery." + phase,
            envelope=envelope.model_dump(mode="json"),
            revision=state.revision,
            status=state.status.value,
            claim_token=state.claim_token,
            claim_started_at=state.claim_started_at.isoformat() if state.claim_started_at else None,
            claim_expires_at=state.claim_expires_at.isoformat() if state.claim_expires_at else None,
            used_tokens=state.used_tokens,
            last_response=asdict(state.last_response) if state.last_response else None,
        )
    )


class ProviderCopyDispatcher:
    def __init__(
        self,
        store: ProviderCopyInventoryStore,
        boundary: CopyDispatchBoundary,
        hook: ProviderCopyOperationHook | None,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.store, self.boundary, self.hook = store, boundary, hook
        self.clock = clock or (lambda: datetime.now(UTC))

    def _authority(
        self,
        access: CopyDispatchAccess,
        envelope: CopyOperationEnvelope,
        state: DeliveryState,
        phase: DeliveryPhase,
    ) -> CopyDeliveryAuthority:
        digest = dispatch_binding(envelope, state, phase)
        raw = access.authorize_delivery(envelope, state, phase, digest)
        try:
            result = CopyDeliveryAuthority.model_validate(
                raw.model_dump(mode="python"), strict=True
            )
        except (ValueError, TypeError, AttributeError):
            raise PolicyError("AI_POLICY_COPY_AUTHORITY_MISMATCH") from None
        validate_copy_grant(
            result.grant, envelope.principal_id, envelope.organization_id, digest, self.clock()
        )
        if result.claim_deadline <= self.clock():
            raise PolicyError("AI_POLICY_COPY_DELIVERY_EXPIRED")
        return result

    def dispatch(
        self,
        principal_id: str,
        organization_id: str,
        command: ProviderCopyCommand,
        operation_key: str,
        *,
        expected_revision: int,
    ) -> DeliveryState:
        try:
            command = ProviderCopyCommand.model_validate(
                command.model_dump(mode="python"), strict=True
            )
            for value in (principal_id, organization_id):
                TypeAdapter(OpaqueId).validate_python(value, strict=True)
            TypeAdapter(Sha256Hex).validate_python(operation_key, strict=True)
            if type(expected_revision) is not int or expected_revision < 0:
                raise ValueError("invalid delivery revision")
        except (ValueError, TypeError, AttributeError):
            raise PolicyError("AI_POLICY_INVALID_COPY_OPERATION") from None
        try:
            with self.boundary.guard(principal_id, organization_id) as access:
                digest = _digest(
                    dict(
                        action="copy_delivery.read",
                        principal_id=principal_id,
                        organization_id=organization_id,
                        command=command.model_dump(mode="json"),
                        operation_key=operation_key,
                    )
                )
                validate_copy_grant(
                    access.authorize(command, digest),
                    principal_id,
                    organization_id,
                    digest,
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
                    state = tx.get_delivery(operation_key)
                    original = tx.get(envelope.target.copy_id)
                if original is None or original.registration != envelope.target:
                    raise PolicyError("AI_POLICY_COPY_REGISTRATION_CONFLICT")
                profile = PolicyDefinitionRef.model_validate(
                    access.resolve_profile(original.initial_copy()).model_dump(mode="python"),
                    strict=True,
                )
                if profile != envelope.target.original_profile_ref:
                    raise PolicyError("AI_POLICY_COPY_PROFILE_MISMATCH")
                authority = self._authority(access, envelope, state, "claim")
                token = "delivery." + uuid4().hex
                with self.store.transaction(
                    organization_id, command.scope_ref, principal_id=principal_id, for_update=True
                ) as tx:
                    if (
                        tx.get_delivery(operation_key) != state
                        or tx.get(envelope.target.copy_id) != original
                    ):
                        raise PolicyError("AI_POLICY_COPY_DELIVERY_STALE")
                    claimed = tx.claim_delivery(
                        operation_key,
                        expected_revision=expected_revision,
                        token=token,
                        expires_at=authority.claim_deadline,
                    )
                    if self._authority(access, envelope, state, "claim") != authority:
                        raise PolicyError("AI_POLICY_COPY_AUTHORITY_MISMATCH")
                # Own claim committed; subsequent failure MUST NOT pretend to roll it back.
                dispatch_auth = self._authority(access, envelope, claimed, "dispatch")
                with self.store.transaction(
                    organization_id, command.scope_ref, principal_id=principal_id
                ) as tx:
                    if tx.get_delivery(operation_key) != claimed:
                        raise PolicyError("AI_POLICY_COPY_DELIVERY_STALE")
                    if self._authority(access, envelope, claimed, "dispatch") != dispatch_auth:
                        raise PolicyError("AI_POLICY_COPY_AUTHORITY_MISMATCH")
                if self._authority(access, envelope, claimed, "dispatch") != dispatch_auth:
                    raise PolicyError("AI_POLICY_COPY_AUTHORITY_MISMATCH")
                if claimed.claim_expires_at is None or claimed.claim_expires_at <= self.clock():
                    raise PolicyError("AI_POLICY_COPY_DELIVERY_EXPIRED")
                if self.hook is None:
                    response = DeliveryResponse(
                        operation_key,
                        envelope.binding_digest,
                        HookOutcome.UNSUPPORTED,
                        reason_code="HOOK_UNAVAILABLE",
                    )
                else:
                    try:
                        raw = self.hook.dispatch(envelope)
                    except Exception:
                        response = DeliveryResponse(
                            operation_key,
                            envelope.binding_digest,
                            HookOutcome.EXCEPTION,
                            reason_code="HOOK_EXCEPTION",
                        )
                    else:
                        try:
                            response = delivery_response(envelope, raw)
                        except PolicyError:
                            response = DeliveryResponse(
                                operation_key,
                                envelope.binding_digest,
                                HookOutcome.EXCEPTION,
                                reason_code="HOOK_RESPONSE_INVALID",
                            )
                completion = self._authority(access, envelope, claimed, "completion")
                with self.store.transaction(
                    organization_id, command.scope_ref, principal_id=principal_id, for_update=True
                ) as tx:
                    if tx.get_delivery(operation_key) != claimed:
                        raise PolicyError("AI_POLICY_COPY_DELIVERY_STALE")
                    result = tx.finish_delivery(
                        response, expected_revision=claimed.revision, token=token
                    )
                    if self._authority(access, envelope, claimed, "completion") != completion:
                        raise PolicyError("AI_POLICY_COPY_AUTHORITY_MISMATCH")
                return result
        except PolicyError:
            raise
        except Exception:
            raise PolicyError("AI_POLICY_COPY_DEPENDENCY_UNAVAILABLE") from None
