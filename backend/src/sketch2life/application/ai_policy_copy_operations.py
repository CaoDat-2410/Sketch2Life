"""Persist exact cancel/purge intents under current guards; NEVER calls provider hooks."""

from collections.abc import Callable
from datetime import UTC, datetime

from pydantic import TypeAdapter

from sketch2life.application.ai_policy_commands import _digest
from sketch2life.application.ai_policy_copy_authority import validate_copy_grant
from sketch2life.application.ports.ai_policy_copy import ProviderCopyVerificationBoundary
from sketch2life.application.ports.ai_policy_copy_registry import ProviderCopyInventoryStore
from sketch2life.contracts.schemas.ai_contract_candidates import OpaqueId
from sketch2life.contracts.schemas.ai_policy import PolicyDefinitionRef
from sketch2life.contracts.schemas.ai_policy_copy import ProviderCopyCommand
from sketch2life.contracts.schemas.ai_policy_copy_operation import (
    CopyOperationAuthorization,
    CopyOperationEnvelope,
)
from sketch2life.domain.ai_policy.model import PolicyError

_ID = TypeAdapter(OpaqueId)


def validate_operation(envelope: CopyOperationEnvelope) -> CopyOperationEnvelope:
    try:
        envelope = CopyOperationEnvelope.model_validate(
            envelope.model_dump(mode="python"), strict=True
        )
        if (envelope.binding_digest, envelope.operation_key) != (
            _digest(envelope.binding()),
            _digest(envelope.key_binding()),
        ):
            raise ValueError("invalid exact operation binding")
        return envelope
    except (ValueError, TypeError, AttributeError):
        raise PolicyError("AI_POLICY_INVALID_COPY_OPERATION") from None


def validate_operation_authorization(
    envelope: CopyOperationEnvelope, observation: CopyOperationAuthorization
) -> CopyOperationAuthorization:
    try:
        observation = CopyOperationAuthorization.model_validate(
            observation.model_dump(mode="python"), strict=True
        )
        grant = observation.authority
        if (
            observation.operation_key,
            grant.principal_id,
            grant.organization_id,
            grant.command_digest,
        ) != (
            envelope.operation_key,
            envelope.principal_id,
            envelope.organization_id,
            envelope.binding_digest,
        ):
            raise ValueError("operation observation binding mismatch")
        return observation
    except (ValueError, TypeError, AttributeError):
        raise PolicyError("AI_POLICY_INVALID_COPY_OPERATION_AUTHORITY") from None


class ProviderCopyOperationService:
    def __init__(
        self,
        store: ProviderCopyInventoryStore,
        boundary: ProviderCopyVerificationBoundary,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.store, self.boundary = store, boundary
        self.clock = clock or (lambda: datetime.now(UTC))

    def schedule(
        self, principal_id: str, organization_id: str, command: ProviderCopyCommand, copy_id: str
    ) -> CopyOperationEnvelope:
        try:
            command = ProviderCopyCommand.model_validate(
                command.model_dump(mode="python"), strict=True
            )
            for value in (principal_id, organization_id, copy_id):
                _ID.validate_python(value, strict=True)
        except (ValueError, TypeError, AttributeError):
            raise PolicyError("AI_POLICY_INVALID_COPY_OPERATION") from None
        try:
            with self.boundary.guard(principal_id, organization_id) as access:
                initial_digest = _digest(
                    dict(
                        principal_id=principal_id,
                        organization_id=organization_id,
                        command=command.model_dump(mode="json"),
                        copy_id=copy_id,
                    )
                )
                validate_copy_grant(
                    access.authorize(command, initial_digest),
                    principal_id,
                    organization_id,
                    initial_digest,
                    self.clock(),
                )
                with self.store.transaction(
                    organization_id, command.scope_ref, principal_id=principal_id
                ) as tx:
                    original = tx.get(copy_id)
                if original is None:
                    raise PolicyError("AI_POLICY_COPY_NOT_FOUND")
                profile = PolicyDefinitionRef.model_validate(
                    access.resolve_profile(original.initial_copy()).model_dump(mode="python"),
                    strict=True,
                )
                if profile != original.registration.original_profile_ref:
                    raise PolicyError("AI_POLICY_COPY_PROFILE_MISMATCH")
                target = original.registration
                digest = _digest(
                    dict(
                        principal_id=principal_id,
                        organization_id=organization_id,
                        command=command.model_dump(mode="json"),
                        target=target.model_dump(mode="json"),
                    )
                )
                grant = validate_copy_grant(
                    access.authorize(command, digest),
                    principal_id,
                    organization_id,
                    digest,
                    self.clock(),
                )
                key = _digest(
                    dict(
                        principal_id=principal_id,
                        organization_id=organization_id,
                        scope_ref=command.scope_ref,
                        client_request_id=command.client_request_id,
                        copy_id=copy_id,
                        operation=command.operation,
                    )
                )
                observed_at = self.clock()
                envelope = validate_operation(
                    CopyOperationEnvelope(
                        operation_key=key,
                        binding_digest=digest,
                        principal_id=principal_id,
                        organization_id=organization_id,
                        command=command,
                        target=target,
                        initial_authority=grant,
                        created_at=observed_at,
                    )
                )
                observation = CopyOperationAuthorization(
                    operation_key=key, authority=grant, observed_at=observed_at
                )
                with self.store.transaction(
                    organization_id, command.scope_ref, principal_id=principal_id, for_update=True
                ) as tx:
                    if tx.get(copy_id) != original:
                        raise PolicyError("AI_POLICY_COPY_REGISTRATION_CONFLICT")
                    result = tx.enqueue_operation(envelope, observation)
                    current = validate_copy_grant(
                        access.authorize(command, digest),
                        principal_id,
                        organization_id,
                        digest,
                        self.clock(),
                    )
                    if current != grant:
                        raise PolicyError("AI_POLICY_COPY_AUTHORITY_MISMATCH")
                return result
        except PolicyError:
            raise
        except Exception:
            raise PolicyError("AI_POLICY_COPY_DEPENDENCY_UNAVAILABLE") from None
