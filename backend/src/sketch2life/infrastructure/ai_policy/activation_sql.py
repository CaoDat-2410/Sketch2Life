"""Own scope operations on the SAME connection/transaction as lifecycle/receipts."""

import json
from dataclasses import asdict

from sqlalchemy import Connection, insert, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from sketch2life.application.ports.ai_policy import EffectivePolicyScope, ScopeTransition
from sketch2life.domain.ai_policy.model import PolicyError
from sketch2life.infrastructure.ai_policy.activation_tables import SCOPE, SCOPE_EVENT
from sketch2life.infrastructure.ai_policy.tables import RECORD, VERSION


def _feature(encoded: str) -> str:
    try:
        value = json.loads(encoded)["feature_scope"]
        if not isinstance(value, str) or not value:
            raise ValueError("missing feature scope")
        return value
    except (ValueError, KeyError, TypeError):
        raise PolicyError("AI_POLICY_INVALID_BODY") from None


class SqlActivationQueries:
    connection: Connection
    _scope_locks: set[tuple[str, str]]

    def was_activated(self, scope: EffectivePolicyScope) -> bool:
        if (
            type(scope.epoch) is not int
            or scope.epoch < 1
            or scope.disabled is not False
            or scope.record_id is None
            or scope.version is None
            or scope.hash is None
        ):
            raise PolicyError("AI_POLICY_PIN_MISMATCH")
        return (
            self.connection.execute(
                select(SCOPE_EVENT.c.epoch).where(
                    SCOPE_EVENT.c.organization_id == scope.organization_id,
                    SCOPE_EVENT.c.feature_scope == scope.feature_scope,
                    SCOPE_EVENT.c.epoch == scope.epoch,
                    SCOPE_EVENT.c.payload["kind"].as_string() == "ai_policy.activated",
                    SCOPE_EVENT.c.payload["disabled"].as_boolean().is_(False),
                    SCOPE_EVENT.c.payload["record_id"].as_string() == scope.record_id,
                    SCOPE_EVENT.c.payload["version"].as_integer() == scope.version,
                    SCOPE_EVENT.c.payload["hash"].as_string() == scope.hash,
                )
            ).scalar_one_or_none()
            is not None
        )

    def stopped_since(self, organization_id: str, feature_scope: str, *, after_epoch: int) -> bool:
        if type(after_epoch) is not int or after_epoch < 1:
            raise PolicyError("AI_POLICY_INVALID_EPOCH")
        # Caller first holds feature SHARE/UPDATE lock through this read and use.
        # Immutable stop history prevents old pins reviving after later activation.
        return (
            self.connection.execute(
                select(SCOPE_EVENT.c.epoch)
                .where(
                    SCOPE_EVENT.c.organization_id == organization_id,
                    SCOPE_EVENT.c.feature_scope == feature_scope,
                    SCOPE_EVENT.c.epoch > after_epoch,
                    SCOPE_EVENT.c.payload["disabled"].as_boolean().is_(True),
                )
                .limit(1)
            ).scalar_one_or_none()
            is not None
        )

    def feature_scope(self, organization_id: str, record_id: str) -> str | None:
        # Discovery only, no parent SHARE lock before scope UPDATE. Caller must
        # reload exact target and verify feature after acquiring scope/record locks.
        encoded = self.connection.execute(
            select(VERSION.c.body_json)
            .join(
                RECORD,
                (
                    (VERSION.c.organization_id == RECORD.c.organization_id)
                    & (VERSION.c.record_id == RECORD.c.record_id)
                    & (VERSION.c.version == RECORD.c.current_version)
                ),
            )
            .where(
                RECORD.c.organization_id == organization_id,
                RECORD.c.record_id == record_id,
            )
        ).scalar_one_or_none()
        return None if encoded is None else _feature(encoded)

    def effective_scope(
        self, organization_id: str, feature_scope: str, *, for_update: bool = False
    ) -> EffectivePolicyScope | None:
        if for_update:
            self.connection.execute(
                pg_insert(SCOPE)
                .values(
                    organization_id=organization_id,
                    feature_scope=feature_scope,
                    epoch=0,
                    disabled=False,
                )
                .on_conflict_do_nothing()
            )
        query = select(SCOPE).where(
            SCOPE.c.organization_id == organization_id, SCOPE.c.feature_scope == feature_scope
        )
        row = (
            self.connection.execute(query.with_for_update(read=not for_update))
            .mappings()
            .one_or_none()
        )
        if for_update:
            self._scope_locks.add((organization_id, feature_scope))
        return None if row is None else EffectivePolicyScope(**row)

    def save_scope(
        self, scope: EffectivePolicyScope, *, expected_epoch: int, event: ScopeTransition
    ) -> None:
        if (
            (scope.organization_id, scope.feature_scope) not in self._scope_locks
            or type(expected_epoch) is not int
            or type(scope.epoch) is not int
            or type(scope.disabled) is not bool
            or scope.epoch != expected_epoch + 1
        ):
            raise PolicyError("AI_POLICY_STALE_SCOPE")
        if event.occurred_at.utcoffset() is None:
            raise PolicyError("AI_POLICY_INVALID_TIME")
        if scope.record_id is not None:
            row = (
                self.connection.execute(
                    select(VERSION).where(
                        VERSION.c.organization_id == scope.organization_id,
                        VERSION.c.record_id == scope.record_id,
                        VERSION.c.version == scope.version,
                        VERSION.c.hash == scope.hash,
                    )
                )
                .mappings()
                .one_or_none()
            )
            if (
                row is None
                or _feature(row["body_json"]) != scope.feature_scope
                or (not scope.disabled and row["state"] != "published")
            ):
                raise PolicyError("AI_POLICY_PIN_MISMATCH")
        elif not scope.disabled or scope.version is not None or scope.hash is not None:
            raise PolicyError("AI_POLICY_PIN_MISMATCH")
        result = self.connection.execute(
            update(SCOPE)
            .where(
                SCOPE.c.organization_id == scope.organization_id,
                SCOPE.c.feature_scope == scope.feature_scope,
                SCOPE.c.epoch == expected_epoch,
            )
            .values(**asdict(scope))
        )
        if result.rowcount != 1:
            raise PolicyError("AI_POLICY_STALE_SCOPE")
        payload = asdict(scope) | {
            "kind": "ai_policy.disabled" if scope.disabled else "ai_policy.activated",
            "reason": event.reason,
        }
        self.connection.execute(
            insert(SCOPE_EVENT).values(
                organization_id=scope.organization_id,
                feature_scope=scope.feature_scope,
                epoch=scope.epoch,
                event_id=event.event_id,
                principal_id=event.principal_id,
                occurred_at=event.occurred_at,
                payload=payload,
            )
        )
