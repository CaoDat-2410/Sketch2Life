"""Current-authorized allowlisted metadata only; no use/dispatch permission."""

from collections.abc import Callable
from datetime import UTC, datetime

from sketch2life.application.ai_policy_commands import _body
from sketch2life.application.ai_policy_telemetry import telemetry_view
from sketch2life.application.ports.ai_policy import PolicyStore
from sketch2life.application.ports.ai_policy_operations import ResourceOperationsReader
from sketch2life.application.ports.ai_policy_registry import PolicyRegistryBoundary
from sketch2life.application.ports.ai_policy_telemetry import OperationsTelemetryReader
from sketch2life.contracts.schemas.ai_policy import PolicyDefinitionRef
from sketch2life.contracts.schemas.ai_policy_operations import (
    LedgerOperationsSnapshot,
    PolicyOperationsRequest,
    PolicyOperationsView,
    PolicyScopeMetadata,
)
from sketch2life.domain.ai_policy.model import Capability, PolicyError, authorize


class AiPolicyOperations:
    def __init__(
        self,
        store: PolicyStore,
        boundary: PolicyRegistryBoundary,
        ledger: ResourceOperationsReader | None = None,
        *,
        telemetry: OperationsTelemetryReader | None = None,
        telemetry_source: PolicyDefinitionRef | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if (telemetry is None) != (telemetry_source is None):
            raise ValueError("telemetry reader and source profile must be bound together")
        if telemetry_source is not None:
            try:
                telemetry_source = PolicyDefinitionRef.model_validate(
                    telemetry_source.model_dump(mode="python"), strict=True
                )
            except (ValueError, TypeError, AttributeError):
                raise ValueError("invalid telemetry source profile") from None
        self.store, self.boundary, self.ledger = store, boundary, ledger
        self.telemetry, self.telemetry_source = telemetry, telemetry_source
        self.clock = clock or (lambda: datetime.now(UTC))

    def read(
        self, principal_id: str, organization_id: str, request: PolicyOperationsRequest
    ) -> PolicyOperationsView:
        try:
            request = PolicyOperationsRequest.model_validate(
                request.model_dump(mode="python"), strict=True
            )
        except (ValueError, TypeError, AttributeError):
            raise PolicyError("AI_POLICY_INVALID_OPERATIONS_QUERY") from None
        try:
            with self.boundary.guard(principal_id, organization_id) as access:
                if access.authority.principal_id != principal_id:
                    raise PolicyError("AI_POLICY_FORBIDDEN")
                authorize(access.authority, organization_id, Capability.OPERATIONS_READ)
                observation = None
                bound_source = self.telemetry_source
                if self.telemetry is not None:
                    observation = self.telemetry.snapshot(organization_id, request.feature_scope)
                # Validate outside own DB locks; later re-evaluate freshness at response.
                telemetry_view(
                    observation,
                    organization_id,
                    request.feature_scope,
                    bound_source,
                    self.clock(),
                )
                if access.authority.principal_id != principal_id:
                    raise PolicyError("AI_POLICY_FORBIDDEN")
                authorize(access.authority, organization_id, Capability.OPERATIONS_READ)
                with self.store.transaction() as tx:
                    source = tx.effective_scope(organization_id, request.feature_scope)
                    scope = None
                    if source is not None:
                        if (source.organization_id, source.feature_scope) != (
                            organization_id,
                            request.feature_scope,
                        ):
                            raise PolicyError("AI_POLICY_SCOPE_MISMATCH")
                        pin, state = None, None
                        if source.record_id is not None:
                            pin = PolicyDefinitionRef.model_validate(
                                dict(
                                    ref=source.record_id, version=source.version, hash=source.hash
                                ),
                                strict=True,
                            )
                            record = tx.load(organization_id, pin.ref, version=pin.version)
                            if record is None or (
                                record.organization_id,
                                record.record_id,
                                record.version,
                                record.hash,
                                _body(record).feature_scope,
                            ) != (
                                organization_id,
                                source.record_id,
                                source.version,
                                source.hash,
                                request.feature_scope,
                            ):
                                raise PolicyError("AI_POLICY_PIN_MISMATCH")
                            state = record.state.value
                        elif source.version is not None or source.hash is not None:
                            raise PolicyError("AI_POLICY_PIN_MISMATCH")
                        scope = PolicyScopeMetadata.model_validate(
                            dict(
                                epoch=source.epoch,
                                disabled=source.disabled,
                                policy_ref=pin,
                                policy_state=state,
                            ),
                            strict=True,
                        )
                    ledger = LedgerOperationsSnapshot(
                        organization_id=organization_id, request=request
                    )
                    if self.ledger is not None:
                        raw = self.ledger.snapshot(organization_id, request)
                        ledger = LedgerOperationsSnapshot.model_validate(
                            raw.model_dump(mode="python"), strict=True
                        )
                result = PolicyOperationsView(
                    organization_id=organization_id,
                    request=request,
                    scope=scope,
                    ledger=ledger,
                    telemetry=telemetry_view(
                        observation,
                        organization_id,
                        request.feature_scope,
                        bound_source,
                        self.clock(),
                    ),
                )
                if access.authority.principal_id != principal_id:
                    raise PolicyError("AI_POLICY_FORBIDDEN")
                authorize(access.authority, organization_id, Capability.OPERATIONS_READ)
            return result
        except PolicyError as error:
            if str(error) in {
                "AI_POLICY_FORBIDDEN",
                "AI_POLICY_SCOPE_MISMATCH",
                "AI_POLICY_PIN_MISMATCH",
                "AI_POLICY_HASH_MISMATCH",
                "AI_POLICY_INVALID_BODY",
                "AI_POLICY_INVALID_LEDGER_STORAGE",
                "AI_POLICY_OPERATIONS_UNAVAILABLE",
            }:
                raise
            raise PolicyError("AI_POLICY_OPERATIONS_UNAVAILABLE") from None
        except Exception:
            raise PolicyError("AI_POLICY_OPERATIONS_UNAVAILABLE") from None
