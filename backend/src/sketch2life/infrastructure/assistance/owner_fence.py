"""Synthetic BE1 owner fences held on the accepting PostgreSQL transaction."""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import cast

from sqlalchemy import Connection, Table, and_, select, text
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.sql.selectable import Select

from sketch2life.application.ports.ai_jobs import (
    OWNER_FENCE_CONTRACT,
    FenceResult,
    OwnerFence,
    OwnerFencePort,
)
from sketch2life.domain.assistance import ResolvedFacts, SourcePin, TargetKind, TargetScope
from sketch2life.domain.eligibility import BASIS_VERSION, EligibilityBasis, EligibilityScope
from sketch2life.infrastructure.assistance.context_revision import context_revision
from sketch2life.infrastructure.persistence.be1_models import (
    ClassroomSessionModel,
    ManagedProfileModel,
    SessionGroupModel,
    SessionMembershipModel,
    SyntheticEligibilityProofModel,
)
from sketch2life.infrastructure.persistence.core_models import CoreAggregateRevisionModel

FENCE_SCOPE_VERSION = "be1-resolved-facts-owner-fence-v1"
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def resolved_facts_epoch(digest: str) -> int:
    """Use the existing signed-31-bit compatibility function over the full facts hash."""
    if not _SHA256.fullmatch(digest):
        raise ValueError("invalid resolved-facts digest")
    return context_revision(
        {"schema_version": FENCE_SCOPE_VERSION, "resolved_facts_digest": digest}
    )


@dataclass(frozen=True, slots=True)
class BE1OwnerFenceScope:
    organization_id: str
    class_id: str
    session_id: str
    canvas_id: str
    group_id: str
    audience: tuple[str, ...]
    contributor_participant_id: str
    purpose_code: str
    target: TargetScope
    region_id: str | None
    source: SourcePin
    proof_ids: tuple[str, ...]
    resolved_facts_digest: str

    def canonical(self) -> str:
        return json.dumps(
            {
                "version": FENCE_SCOPE_VERSION,
                "organization_id": self.organization_id,
                "class_id": self.class_id,
                "session_id": self.session_id,
                "canvas_id": self.canvas_id,
                "group_id": self.group_id,
                "audience": list(self.audience),
                "contributor_participant_id": self.contributor_participant_id,
                "purpose_code": self.purpose_code,
                "target": self.target.canonical(),
                "region_id": self.region_id,
                "source": self.source.canonical(),
                "proof_ids": list(self.proof_ids),
                "resolved_facts_digest": self.resolved_facts_digest,
            },
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )


def build_owner_fence(facts: ResolvedFacts) -> OwnerFence:
    """Pin complete synthetic request facts; this token grants no authority by itself."""
    if (
        not facts.group_id
        or not facts.audience
        or len(set(facts.audience)) != len(facts.audience)
        or tuple(member.participant_id for member in facts.members) != facts.audience
        or any(
            member.eligibility_basis != EligibilityBasis.SYNTHETIC_DEV
            or not member.evidence_ref
            or member.basis_version != BASIS_VERSION
            or member.eligibility_scope
            != EligibilityScope(
                facts.organization_id, facts.class_id, member.participant_id, facts.purpose_code
            )
            or member.consent_effective
            or member.purpose_granted
            or member.consent_record_ref is not None
            or member.consent_revision is not None
            for member in facts.members
        )
    ):
        raise ValueError("owner fence requires scoped synthetic facts")
    scope = BE1OwnerFenceScope(
        facts.organization_id,
        facts.class_id,
        facts.session_id,
        facts.canvas_id,
        facts.group_id,
        facts.audience,
        facts.contributor_participant_id,
        facts.purpose_code,
        facts.target,
        facts.region_id,
        facts.source,
        tuple(cast(str, member.evidence_ref) for member in facts.members),
        facts.digest(),
    )
    encoded = scope.canonical()
    if decode_owner_fence_scope(encoded) is None:
        raise ValueError("owner fence facts are malformed")
    return OwnerFence(encoded, resolved_facts_epoch(scope.resolved_facts_digest))


def decode_owner_fence_scope(encoded: str) -> BE1OwnerFenceScope | None:
    """Accept only the exact canonical, versioned representation generated above."""
    try:
        payload = json.loads(encoded)
        if not isinstance(payload, dict) or payload.get("version") != FENCE_SCOPE_VERSION:
            return None
        source = payload["source"]
        target = payload["target"]
        if not isinstance(source, dict) or not isinstance(target, dict):
            return None
        source_pin = SourcePin(**source)
        target_scope = TargetScope(TargetKind(target["kind"]), target["id"])
        strings = [
            payload[field]
            for field in (
                "organization_id",
                "class_id",
                "session_id",
                "canvas_id",
                "group_id",
                "contributor_participant_id",
                "purpose_code",
            )
        ]
        audience, proofs = payload["audience"], payload["proof_ids"]
        if (
            not all(isinstance(value, str) and 0 < len(value) <= 256 for value in strings)
            or not isinstance(audience, list)
            or not isinstance(proofs, list)
            or not 0 < len(audience) <= 32
            or len(audience) != len(proofs)
            or not all(
                isinstance(value, str) and 0 < len(value) <= 256 for value in audience + proofs
            )
            or len(set(audience)) != len(audience)
            or len(set(proofs)) != len(proofs)
            or payload["contributor_participant_id"] not in audience
            or (target_scope.kind is TargetKind.INDIVIDUAL and target_scope.ref_id not in audience)
            or (
                target_scope.kind is TargetKind.GROUP and target_scope.ref_id != payload["group_id"]
            )
            or (payload["region_id"] is not None and not isinstance(payload["region_id"], str))
            or not isinstance(payload["resolved_facts_digest"], str)
            or not _SHA256.fullmatch(payload["resolved_facts_digest"])
            or type(source_pin.document_epoch) is not int
            or source_pin.document_epoch < 1
            or type(source_pin.server_sequence) is not int
            or source_pin.server_sequence < 0
            or not all(
                isinstance(value, str) and bool(value)
                for value in (
                    source_pin.snapshot_ref,
                    source_pin.checkpoint_id,
                    source_pin.render_ref,
                )
            )
            or not all(
                isinstance(value, str) and _SHA256.fullmatch(value)
                for value in (
                    source_pin.checkpoint_checksum,
                    source_pin.render_sha256,
                    source_pin.input_hash,
                )
            )
        ):
            return None
        scope = BE1OwnerFenceScope(
            organization_id=strings[0],
            class_id=strings[1],
            session_id=strings[2],
            canvas_id=strings[3],
            group_id=strings[4],
            audience=tuple(audience),
            contributor_participant_id=strings[5],
            purpose_code=strings[6],
            target=target_scope,
            region_id=payload["region_id"],
            source=source_pin,
            proof_ids=tuple(proofs),
            resolved_facts_digest=payload["resolved_facts_digest"],
        )
        return scope if scope.canonical() == encoded else None
    except (KeyError, TypeError, ValueError):
        return None


ResolvedFactsResolver = Callable[[Connection, BE1OwnerFenceScope], ResolvedFacts | None]


@dataclass(frozen=True, slots=True)
class _LockTarget:
    table: Table
    primary_key: str
    key: str
    predicates: tuple[ColumnElement[bool], ...]

    def statement(self) -> Select[tuple[str]]:
        return (
            select(self.table.c[self.primary_key])
            .where(self.table.c[self.primary_key] == self.key, *self.predicates)
            .with_for_update(read=True)
        )


def _required_targets(connection: Connection, scope: BE1OwnerFenceScope) -> list[_LockTarget]:
    targets: list[_LockTarget] = []

    def add(table: Table, pk: str, key: str, *predicates: ColumnElement[bool]) -> None:
        targets.append(_LockTarget(table, pk, key, tuple(predicates)))

    aggregate = cast(Table, CoreAggregateRevisionModel.__table__)
    for key in sorted({scope.canvas_id, scope.session_id}):
        add(aggregate, "aggregate_id", key, aggregate.c.organization_id == scope.organization_id)
    session = cast(Table, ClassroomSessionModel.__table__)
    add(
        session,
        "session_id",
        scope.session_id,
        session.c.organization_id == scope.organization_id,
        session.c.class_id == scope.class_id,
    )
    group = cast(Table, SessionGroupModel.__table__)
    add(
        group,
        "group_id",
        scope.group_id,
        group.c.organization_id == scope.organization_id,
        group.c.session_id == scope.session_id,
    )
    membership = cast(Table, SessionMembershipModel.__table__)
    for child in scope.audience:
        predicate = and_(
            membership.c.organization_id == scope.organization_id,
            membership.c.class_id == scope.class_id,
            membership.c.session_id == scope.session_id,
            membership.c.child_id == child,
            membership.c.group_id == scope.group_id,
        )
        ids = (
            connection.execute(select(membership.c.membership_id).where(predicate)).scalars().all()
        )
        if len(ids) != 1 or not isinstance(ids[0], str):
            raise ValueError("missing or ambiguous owner membership")
        add(membership, "membership_id", ids[0], predicate)
    profile = cast(Table, ManagedProfileModel.__table__)
    proof = cast(Table, SyntheticEligibilityProofModel.__table__)
    for child, proof_id in zip(scope.audience, scope.proof_ids, strict=True):
        add(
            profile,
            "child_id",
            child,
            profile.c.organization_id == scope.organization_id,
            profile.c.class_id == scope.class_id,
        )
        add(
            proof,
            "evidence_id",
            proof_id,
            proof.c.organization_id == scope.organization_id,
            proof.c.class_id == scope.class_id,
            proof.c.child_profile_id == child,
            proof.c.session_id == scope.session_id,
            proof.c.purpose_ref == scope.purpose_code,
        )
    return targets


class PostgresBE1OwnerFence:
    """FOR SHARE protects existing rows, with a full-digest recheck for prior INSERTs.

    Membership INSERTs after ``hold`` returns remain outside this row-lock guarantee.
    The caller owns the transaction and must finish acceptance before calling a provider.
    """

    contract_version = OWNER_FENCE_CONTRACT

    def __init__(
        self,
        connection: Connection,
        resolver: ResolvedFactsResolver,
        *,
        lock_timeout_ms: int = 1000,
    ) -> None:
        if type(lock_timeout_ms) is not int or not 1 <= lock_timeout_ms <= 5000:
            raise ValueError("lock timeout must be between 1 and 5000 milliseconds")
        self._connection = connection
        self._resolver = resolver
        self._lock_timeout_ms = lock_timeout_ms

    def hold(self, fences: tuple[OwnerFence, ...]) -> FenceResult:
        if not fences:
            return FenceResult(current=True)
        try:
            if (
                self._connection.dialect.name != "postgresql"
                or not self._connection.in_transaction()
                or len({fence.fence_scope for fence in fences}) != len(fences)
            ):
                return FenceResult(False, fences)
            scopes = [decode_owner_fence_scope(fence.fence_scope) for fence in fences]
            if any(scope is None for scope in scopes):
                return FenceResult(False, fences)
            valid = cast(list[BE1OwnerFenceScope], scopes)
            if len({scope.organization_id for scope in valid}) != 1:
                return FenceResult(False, fences)
            if any(
                type(fence.epoch) is not int
                or fence.epoch != resolved_facts_epoch(scope.resolved_facts_digest)
                for fence, scope in zip(fences, valid, strict=True)
            ):
                return FenceResult(False, fences)
            self._connection.execute(
                text("SELECT set_config('lock_timeout', :timeout, true)"),
                {"timeout": f"{self._lock_timeout_ms}ms"},
            )
            targets = [
                target for scope in valid for target in _required_targets(self._connection, scope)
            ]
            unique = {(target.table.name, target.key): target for target in targets}
            for key in sorted(unique):
                target = unique[key]
                if self._connection.execute(target.statement()).scalar_one_or_none() != target.key:
                    return FenceResult(False, fences)
            stale = []
            for fence, scope in zip(fences, valid, strict=True):
                facts = self._resolver(self._connection, scope)
                if facts is None or build_owner_fence(facts) != fence:
                    stale.append(fence)
            return FenceResult(not stale, tuple(stale))
        except Exception:
            # A fence is an acceptance boundary: no database or injected-source failure
            # may be interpreted as a current owner decision. The caller rolls back.
            return FenceResult(False, fences)


def owner_fence_factory(
    resolver: ResolvedFactsResolver, *, lock_timeout_ms: int = 1000
) -> Callable[[Connection], OwnerFencePort]:
    """Construct exactly the adapter factory consumed by ``SqlAiJobRepository``."""
    return lambda connection: PostgresBE1OwnerFence(
        connection, resolver, lock_timeout_ms=lock_timeout_ms
    )
