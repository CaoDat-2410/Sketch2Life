"""Guarded epoch-CAS emergency stop; intent creation is not cancellation completion."""

from collections.abc import Callable
from dataclasses import asdict, replace
from datetime import UTC, datetime

from pydantic import ValidationError

from sketch2life.application.ai_policy_commands import _digest
from sketch2life.application.ports.ai_policy import (
    EffectivePolicyScope,
    PolicyReceipt,
    PolicyStore,
    PolicyTransaction,
    ScopeTransition,
)
from sketch2life.application.ports.ai_policy_registry import PolicyRegistryBoundary
from sketch2life.contracts.schemas.ai_policy_control import (
    EmergencyStopCommand,
    EmergencyStopResult,
)
from sketch2life.domain.ai_policy.model import Capability, PolicyError, authorize


def _scope_result(scope: EffectivePolicyScope) -> EmergencyStopResult:
    if type(scope.disabled) is not bool or type(scope.epoch) is not int:
        raise PolicyError("AI_POLICY_SCOPE_MISMATCH")
    try:
        return EmergencyStopResult.model_validate(asdict(scope), strict=True)
    except (ValidationError, ValueError):
        raise PolicyError("AI_POLICY_SCOPE_MISMATCH") from None


def _replay(
    receipt: PolicyReceipt,
    fingerprint: str,
    organization_id: str,
    principal_id: str,
    command: EmergencyStopCommand,
    scope: EffectivePolicyScope,
) -> EmergencyStopResult:
    if receipt.fingerprint != fingerprint:
        raise PolicyError("AI_POLICY_COMMAND_CONFLICT")
    if (receipt.organization_id, receipt.principal_id, receipt.request_id) != (
        organization_id,
        principal_id,
        command.client_request_id,
    ):
        raise PolicyError("AI_POLICY_SCOPE_MISMATCH")
    try:
        result = EmergencyStopResult.model_validate_json(receipt.result_json)
    except (ValidationError, ValueError):
        raise PolicyError("AI_POLICY_RECEIPT_INEFFECTIVE") from None
    if scope.disabled is not True:
        raise PolicyError("AI_POLICY_RECEIPT_INEFFECTIVE")
    current = _scope_result(scope)
    if result.model_copy(update={"replayed": False}) != current:
        raise PolicyError("AI_POLICY_RECEIPT_INEFFECTIVE")
    return result.model_copy(update={"replayed": True})


class AiPolicyEmergencyStop:
    def __init__(
        self,
        store: PolicyStore,
        boundary: PolicyRegistryBoundary,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.store, self.boundary = store, boundary
        self.clock = clock or (lambda: datetime.now(UTC))

    def execute(
        self, principal_id: str, organization_id: str, command: EmergencyStopCommand
    ) -> EmergencyStopResult:
        try:
            command = EmergencyStopCommand.model_validate(
                command.model_dump(mode="python"), strict=True
            )
        except (ValidationError, ValueError, TypeError):
            raise PolicyError("AI_POLICY_INVALID_COMMAND") from None
        fingerprint = _digest(
            dict(
                operation="emergency_stop",
                principal_id=principal_id,
                organization_id=organization_id,
                command=command.model_dump(mode="json"),
            )
        )
        identity = _digest([organization_id, principal_id, command.client_request_id])
        try:
            with self.boundary.guard(principal_id, organization_id) as access:
                if access.authority.principal_id != principal_id:
                    raise PolicyError("AI_POLICY_FORBIDDEN")
                authorize(access.authority, organization_id, Capability.DISABLE)
                try:
                    with self.store.transaction() as tx:
                        scope = self._scope(tx, organization_id, command.feature_scope)
                        receipt = tx.receipt(
                            organization_id, principal_id, command.client_request_id
                        )
                        if receipt is not None:
                            result = _replay(
                                receipt, fingerprint, organization_id, principal_id, command, scope
                            )
                        else:
                            if scope.epoch != command.expected_epoch:
                                raise PolicyError("AI_POLICY_STALE_SCOPE")
                            if (
                                scope.epoch == 0
                                and access.feature_available(command.feature_scope) is not True
                            ):
                                raise PolicyError("AI_POLICY_FEATURE_UNAVAILABLE")
                            if not scope.disabled:
                                now = self.clock()
                                if now.utcoffset() is None:
                                    raise PolicyError("AI_POLICY_INVALID_TIME")
                                updated = replace(scope, epoch=scope.epoch + 1, disabled=True)
                                tx.save_scope(
                                    updated,
                                    expected_epoch=scope.epoch,
                                    event=ScopeTransition(
                                        "stop-" + identity, principal_id, now, command.reason
                                    ),
                                )
                                scope = updated
                            result = _scope_result(scope)
                            tx.add_receipt(
                                PolicyReceipt(
                                    organization_id,
                                    principal_id,
                                    command.client_request_id,
                                    fingerprint,
                                    result.model_dump_json(),
                                )
                            )
                except PolicyError as error:
                    if str(error) != "AI_POLICY_WRITE_CONFLICT":
                        raise
                    with self.store.transaction() as tx:
                        scope = self._scope(tx, organization_id, command.feature_scope)
                        receipt = tx.receipt(
                            organization_id, principal_id, command.client_request_id
                        )
                        if receipt is None:
                            raise error
                        result = _replay(
                            receipt, fingerprint, organization_id, principal_id, command, scope
                        )
            return result
        except PolicyError:
            raise
        except Exception:
            raise PolicyError("AI_POLICY_DEPENDENCY_UNAVAILABLE") from None

    @staticmethod
    def _scope(
        tx: PolicyTransaction, organization_id: str, feature_scope: str
    ) -> EffectivePolicyScope:
        scope = tx.effective_scope(organization_id, feature_scope, for_update=True)
        if scope is None or (scope.organization_id, scope.feature_scope) != (
            organization_id,
            feature_scope,
        ):
            raise PolicyError("AI_POLICY_SCOPE_MISMATCH")
        return scope
