"""Own read-only metadata adapter; never use mutating ledger UoW for monitoring."""

from dataclasses import asdict

from sqlalchemy import Engine, select

from sketch2life.contracts.schemas.ai_policy_operations import (
    LedgerOperationsSnapshot,
    PolicyOperationsRequest,
)
from sketch2life.domain.ai_policy.accounting import BudgetKey, DefinitionKey
from sketch2life.domain.ai_policy.model import PolicyError, canonical_json
from sketch2life.infrastructure.ai_policy.accounting_sql import bucket_id
from sketch2life.infrastructure.ai_policy.accounting_tables import BUCKET, RESOURCE_SCOPE


class SqlResourceOperationsReader:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def snapshot(
        self, organization_id: str, request: PolicyOperationsRequest
    ) -> LedgerOperationsSnapshot:
        try:
            request = PolicyOperationsRequest.model_validate(
                request.model_dump(mode="python"), strict=True
            )
            empty = LedgerOperationsSnapshot(organization_id=organization_id, request=request)
            with self.engine.begin() as connection:
                scope = (
                    connection.execute(
                        select(RESOURCE_SCOPE)
                        .where(
                            RESOURCE_SCOPE.c.organization_id == organization_id,
                            RESOURCE_SCOPE.c.feature_scope == request.feature_scope,
                        )
                        .with_for_update(read=True)
                    )
                    .mappings()
                    .one_or_none()
                )
                if scope is None:
                    return empty
                if (scope["organization_id"], scope["feature_scope"]) != (
                    organization_id,
                    request.feature_scope,
                ):
                    raise PolicyError("AI_POLICY_SCOPE_MISMATCH")
                values = empty.model_dump(mode="python") | dict(
                    occupied_slots=scope["occupied_slots"]
                )
                if request.budget_window is not None:
                    window = request.budget_window
                    key = BudgetKey(
                        organization_id,
                        request.feature_scope,
                        DefinitionKey(
                            window.definition.ref, window.definition.version, window.definition.hash
                        ),
                        window.unit,
                        window.window_id,
                    )
                    row = (
                        connection.execute(
                            select(BUCKET)
                            .where(
                                BUCKET.c.organization_id == organization_id,
                                BUCKET.c.feature_scope == request.feature_scope,
                                BUCKET.c.bucket_id == bucket_id(key),
                            )
                            .with_for_update(read=True)
                        )
                        .mappings()
                        .one_or_none()
                    )
                    if row is not None:
                        if canonical_json(row["key"]) != canonical_json(asdict(key)):
                            raise PolicyError("AI_POLICY_INVALID_LEDGER_STORAGE")
                        values |= dict(
                            bucket_available=True,
                            recorded_held_units=row["held_units"],
                            recorded_spent_units=row["spent_units"],
                        )
                return LedgerOperationsSnapshot.model_validate(values, strict=True)
        except PolicyError:
            raise
        except Exception:
            raise PolicyError("AI_POLICY_OPERATIONS_UNAVAILABLE") from None
