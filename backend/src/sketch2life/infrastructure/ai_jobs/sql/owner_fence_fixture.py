"""ASSUMED_CONTRACT owner-fence fixture for BE2-01 Phase B batch B3 tests only.

Implements the assumed ``OwnerFenceV1/0.1-candidate`` contract (ADR-0018 D7, O-09 Q2/Q8) in a
throw-away PostgreSQL schema ``owner_fence_fixture`` on a disposable synthetic database:

* owner side (P2 stand-in): ``OwnerFixture.change`` locks the fence row ``FOR UPDATE``, bumps
  the epoch, updates the decision and records a withheld notice in one transaction;
* BE2 side: ``FixtureFenceHold`` reads the fence rows ``FOR SHARE`` on the BE2 unit-of-work
  connection, so the hold lasts until the BE2 transaction ends;
* fixture owner ports (eligibility, authorization, artifacts) return decisions together with
  the fence epoch they were read at.

This is not a P2 adapter, is never wired into the live app or an Alembic revision, and
creates its DDL only on databases named like the integration conftest's disposable ones.
Real owner integration remains plan acceptance B-12.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from sqlalchemy import (
    BigInteger,
    Column,
    Connection,
    Engine,
    ForeignKey,
    MetaData,
    String,
    Table,
    func,
    insert,
    select,
    text,
    update,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.schema import CreateSchema

from sketch2life.application.ports.ai_jobs import (
    OWNER_FENCE_CONTRACT,
    ArtifactDescriptor,
    AuthorizationAction,
    AuthorizationDecision,
    EligibilityDecision,
    FenceResult,
    OwnerFence,
    Principal,
)
from sketch2life.domain.ai_jobs.model import JobScope, RequestRef

ASSUMED_CONTRACT = "ASSUMED_CONTRACT"
FIXTURE_SCHEMA = "owner_fence_fixture"
DISPOSABLE_DATABASE = re.compile(r"^be2_b2_[0-9a-f]{16}$")

FIXTURE_METADATA = MetaData(schema=FIXTURE_SCHEMA)
fence = Table(
    "fence",
    FIXTURE_METADATA,
    Column("fence_scope", String(256), primary_key=True),
    Column("epoch", BigInteger, nullable=False),
)
decision = Table(
    "decision",
    FIXTURE_METADATA,
    Column("fence_scope", String(256), ForeignKey(fence.c.fence_scope), primary_key=True),
    Column("payload", JSONB, nullable=False),
)
notice = Table(
    "notice",
    FIXTURE_METADATA,
    Column("notice_id", String(128), primary_key=True),
    Column("fence_scope", String(256), ForeignKey(fence.c.fence_scope), nullable=False),
    Column("epoch", BigInteger, nullable=False),
    Column("payload", JSONB, nullable=False),
    Column("status", String(16), nullable=False, server_default=text("'WITHHELD'")),
)


def eligibility_scope(organization_id: str, request_id: str) -> str:
    return f"eligibility:{organization_id}:{request_id}"


def grant_scope(organization_id: str, principal_id: str) -> str:
    return f"grant:{organization_id}:{principal_id}"


def artifact_scope(artifact_ref: str) -> str:
    return f"artifact:{artifact_ref}"


def create_fixture_schema(connection: Connection) -> None:
    """Create the fixture DDL; refuses any database that is not a disposable test database."""

    name = connection.execute(select(func.current_database())).scalar_one()
    if not DISPOSABLE_DATABASE.match(str(name)):
        raise RuntimeError("owner fence fixture DDL is allowed only on disposable test databases")
    connection.execute(CreateSchema(FIXTURE_SCHEMA, if_not_exists=True))
    FIXTURE_METADATA.create_all(connection)


class FixtureFenceHold:
    """BE2-side ``OwnerFencePort`` bound to the BE2 unit-of-work connection."""

    contract_version = OWNER_FENCE_CONTRACT
    label = ASSUMED_CONTRACT

    def __init__(
        self, connection: Connection, observe: Callable[[FenceResult], None] | None = None
    ) -> None:
        self._connection = connection
        self._observe = observe

    def hold(self, fences: tuple[OwnerFence, ...]) -> FenceResult:
        scopes = sorted({f.fence_scope for f in fences})
        rows = self._connection.execute(
            select(fence.c.fence_scope, fence.c.epoch)
            .where(fence.c.fence_scope.in_(scopes))
            .order_by(fence.c.fence_scope)
            .with_for_update(read=True)
        ).all()
        current = {row.fence_scope: row.epoch for row in rows}
        # An unknown fence row is stale, never current.
        stale = tuple(f for f in fences if current.get(f.fence_scope) != f.epoch)
        result = FenceResult(not stale, stale)
        if self._observe is not None:
            self._observe(result)
        return result


class OwnerFixture:
    """Owner-side state (P2 stand-in). Every decision change is one owner transaction."""

    label = ASSUMED_CONTRACT

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def set(self, scope: str, payload: dict[str, Any]) -> int:
        """Create or replace a decision as an owner change; returns the new epoch."""

        return self.change(scope, payload, notice_id=None)

    def change(
        self,
        scope: str,
        payload: dict[str, Any],
        *,
        notice_id: str | None,
        after_lock: Callable[[], None] | None = None,
    ) -> int:
        with self._engine.begin() as connection:
            connection.execute(
                pg_insert(fence).values(fence_scope=scope, epoch=0).on_conflict_do_nothing()
            )
            epoch = connection.execute(
                select(fence.c.epoch).where(fence.c.fence_scope == scope).with_for_update()
            ).scalar_one()
            if after_lock is not None:
                after_lock()
            new_epoch = int(epoch) + 1
            connection.execute(
                update(fence).where(fence.c.fence_scope == scope).values(epoch=new_epoch)
            )
            connection.execute(
                pg_insert(decision)
                .values(fence_scope=scope, payload=payload)
                .on_conflict_do_update(
                    index_elements=[decision.c.fence_scope], set_={"payload": payload}
                )
            )
            if notice_id is not None:
                connection.execute(
                    insert(notice).values(
                        notice_id=notice_id, fence_scope=scope, epoch=new_epoch, payload=payload
                    )
                )
        return new_epoch

    def read(self, scope: str) -> tuple[dict[str, Any], OwnerFence] | None:
        """Decision and the epoch it belongs to, read in one statement."""

        with self._engine.connect() as connection:
            row = connection.execute(
                select(decision.c.payload, fence.c.epoch)
                .join(fence, fence.c.fence_scope == decision.c.fence_scope)
                .where(decision.c.fence_scope == scope)
            ).one_or_none()
        if row is None:
            return None
        return dict(row.payload), OwnerFence(scope, int(row.epoch))

    def epoch(self, scope: str) -> int | None:
        with self._engine.connect() as connection:
            value = connection.execute(
                select(fence.c.epoch).where(fence.c.fence_scope == scope)
            ).scalar_one_or_none()
        return None if value is None else int(value)

    def withheld_notices(self) -> int:
        with self._engine.connect() as connection:
            return int(
                connection.execute(
                    select(func.count()).select_from(notice).where(notice.c.status == "WITHHELD")
                ).scalar_one()
            )


class FixtureEligibility:
    """Eligibility owner port backed by ``OwnerFixture``; payload
    ``{"eligible": bool, "reason_code": str | None, "context_revision": int | None}``."""

    def __init__(self, owner: OwnerFixture) -> None:
        self._owner = owner

    def check(
        self, *, scope: JobScope, request_ref: RequestRef, job_type: str
    ) -> EligibilityDecision:
        found = self._owner.read(eligibility_scope(scope.organization_id, request_ref.request_id))
        if found is None:
            return EligibilityDecision(False, "CONSENT_REVOKED", request_ref.context_revision)
        payload, owner_fence = found
        context = payload.get("context_revision")
        return EligibilityDecision(
            bool(payload["eligible"]),
            payload.get("reason_code"),
            request_ref.context_revision if context is None else int(context),
            owner_fence,
        )


class FixtureAuthorization:
    """Authorization owner port; payload ``{"actions": [...]}`` per principal grant."""

    def __init__(self, owner: OwnerFixture) -> None:
        self._owner = owner

    def decide(
        self, principal: Principal, action: AuthorizationAction, scope: JobScope
    ) -> AuthorizationDecision:
        found = self._owner.read(grant_scope(principal.organization_id, principal.principal_id))
        if found is None:
            return AuthorizationDecision(False, "FORBIDDEN_SCOPE")
        payload, owner_fence = found
        if str(action) in payload.get("actions", []):
            return AuthorizationDecision(True, None, owner_fence)
        return AuthorizationDecision(False, "GRANT_REVOKED", owner_fence)


class FixtureArtifacts:
    """Artifact owner port; payload holds sha256, organization, producer lineage and
    quarantine state. ``quarantine`` is an owner change that bumps the artifact fence."""

    def __init__(self, owner: OwnerFixture) -> None:
        self._owner = owner

    def describe(self, artifact_ref: str) -> ArtifactDescriptor | None:
        found = self._owner.read(artifact_scope(artifact_ref))
        if found is None:
            return None
        payload, owner_fence = found
        return ArtifactDescriptor(
            artifact_ref,
            payload["sha256"],
            payload["organization_id"],
            payload.get("producer_job_id"),
            payload.get("producer_attempt_id"),
            payload.get("quarantine_reason"),
            owner_fence,
        )

    def quarantine(self, artifact_refs: tuple[str, ...], reason_code: str) -> None:
        for ref in artifact_refs:
            found = self._owner.read(artifact_scope(ref))
            if found is None or found[0].get("quarantine_reason") is not None:
                continue
            self._owner.change(
                artifact_scope(ref), {**found[0], "quarantine_reason": reason_code}, notice_id=None
            )


__all__ = [
    "ASSUMED_CONTRACT",
    "FIXTURE_SCHEMA",
    "FixtureArtifacts",
    "FixtureAuthorization",
    "FixtureEligibility",
    "FixtureFenceHold",
    "OwnerFixture",
    "artifact_scope",
    "create_fixture_schema",
    "eligibility_scope",
    "grant_scope",
]
