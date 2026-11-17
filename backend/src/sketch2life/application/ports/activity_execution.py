"""Candidate11 source/current authority/result consumer ports; no real defaults."""

from contextlib import AbstractContextManager
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Literal, Protocol

from sketch2life.domain.activity_execution.model import (
    Assignment,
    Audience,
    ChildAge,
    Confirmation,
    Definition,
    ExecutionProof,
    digest,
    exact,
    fail,
    ids,
)
from sketch2life.domain.knowledge_video.model import (
    ExactRef,
    require_id,
    require_revision,
    require_time,
)


@dataclass(frozen=True, slots=True)
class Actor:
    principal_id: str
    organization_id: str
    session_id: str
    client_key: str

    def __post_init__(self) -> None:
        for value in (self.principal_id, self.organization_id, self.session_id, self.client_key):
            require_id(value)

    def key(self) -> str:
        return digest((self.principal_id, self.organization_id, self.session_id, self.client_key))


@dataclass(frozen=True, slots=True)
class Receipt:
    actor: Actor
    body_digest: str
    assignment: Assignment

    def __post_init__(self) -> None:
        from sketch2life.domain.knowledge_video.model import require_hash

        if type(self.actor) is not Actor or type(self.assignment) is not Assignment:
            fail("INVALID_RECEIPT")
        a, row = replace(self.actor), replace(self.assignment)
        require_hash(self.body_digest)
        if (a.organization_id, a.session_id) != (row.organization_id, row.audience.session_id):
            fail("SCOPE_MISMATCH")


@dataclass(frozen=True, slots=True)
class OutcomeEvent:
    event_id: str
    assignment: Assignment
    created_at: datetime
    recorded_by: str

    def __post_init__(self) -> None:
        from sketch2life.domain.activity_execution.model import TERMINAL

        require_id(self.event_id)
        require_id(self.recorded_by)
        if type(self.assignment) is not Assignment:
            fail("INVALID_EVENT")
        row = replace(self.assignment)
        require_time(self.created_at)
        if row.state not in TERMINAL or self.created_at < row.updated_at:
            fail("INVALID_EVENT")

    def fingerprint(self) -> str:
        # BE1 must dedup on event ID and EXACT immutable payload digest. No
        # per-child observed/achieved claim, reflection or portfolio data created.
        return digest((self.event_id, self.assignment, self.created_at, self.recorded_by))


@dataclass(frozen=True, slots=True)
class OutcomeAck:
    event_id: str
    event_digest: str
    receipt_ref: ExactRef

    def __post_init__(self) -> None:
        from sketch2life.domain.knowledge_video.model import require_hash

        require_id(self.event_id)
        require_hash(self.event_digest)
        exact(self.receipt_ref)


class Access(Protocol):
    def selection(
        self, source: ExactRef, group_ids: tuple[str, ...]
    ) -> tuple[Definition, Audience, ExactRef]:
        """Current exact published/reviewed12 definition verified against asset bytes,
        authoritative session class/group membership/ages and current policy. Empty
        group list is class only if owning scope resolver explicitly permits it.
        No legacy curated ID/role/default boolean substitutes current authority.
        """
        ...

    def check(
        self,
        actor: Actor,
        row: Assignment,
        phase: Literal["select", "prepare", "commit", "replay", "notice", "deliver"],
    ) -> None:
        """Action-specific Teacher/current org/session/membership/grant/purpose
        consent/source publication/recall and policy fences through commit/effect.
        Replays reauthorize historical visibility, never reapply/reset state.
        Notice authenticated source/cause; deliver authorizes original result scope.
        In-progress invalidation/finish policy owned externally, not auto-stop.
        """
        ...

    def check_child(self, row: Assignment, child: ChildAge) -> None:
        """CURRENT per-child exact age/safety/material/prerequisite policy and
        adaptation review. Raise if unknown/denied. No group mean/legacy hardfilter.
        Called for EVERY audience child before confirm/start; no permissive adapter.
        """
        ...

    def preparation(self, row: Assignment, confirmation: Confirmation) -> ExecutionProof:
        """Authenticate current reviewed adaptation/real preparation proof bound to
        exact effective snapshot/audience/policy. True checkboxes alone NOT enough.
        Actual policy/age/current invalidation fences held through store commit.
        """
        ...


class Boundary(Protocol):
    def guard(self, actor: Actor) -> AbstractContextManager[Access]:
        """Acquire actual outer owner guards before own DB lock; no network/outer
        locks inside own UoW. Missing adoption closed; no production binding here.
        """
        ...


class Transaction(Protocol):
    def load(self, assignment_id: str) -> Assignment | None: ...
    def receipt(self, principal_id: str, client_key: str) -> Receipt | None: ...
    def write(
        self, before: Assignment | None, receipt: Receipt, event: OutcomeEvent | None
    ) -> None:
        """CAS assignment +immutable history/receipt/event/outcome intent one UoW;
        unique org/session/actor/key. No BE1/12 DB writes or partial commits.
        """
        ...

    def event(self, event_id: str) -> tuple[OutcomeEvent, OutcomeAck | None] | None: ...
    def acknowledge(self, event: OutcomeEvent, ack: OutcomeAck) -> None:
        """Idempotent exact original ACK, immutable, one UoW with delivery history."""
        ...


class Store(Protocol):
    def transaction(
        self, organization_id: str, session_id: str
    ) -> AbstractContextManager[Transaction]: ...


class OutcomeConsumer(Protocol):
    def send(self, event: OutcomeEvent) -> OutcomeAck:
        """Outside own tx; authenticated BE1 sink dedups event ID+body and returns
        receipt only for actual accepted result reference. No generated observation/
        individual achievement/reflection/portfolio, no implicit session advance.
        Lost ACK redelivery SAME event only; actual durable consumer dedup required.
        """
        ...


@dataclass(frozen=True, slots=True)
class DiscoveryQuery:
    topic_ids: tuple[str, ...]
    age_months: int
    preferences: tuple[str, ...]
    limit: int

    def __post_init__(self) -> None:
        ids(self.topic_ids, nonempty=True)
        ids(self.preferences)
        require_revision(self.age_months, minimum=0)
        require_revision(self.limit)
        if self.limit > 100:
            fail("INVALID_LIMIT")  # Bounded candidate transport, NOT ranking policy.


class DiscoveryAccess(Protocol):
    def candidates(self, query: DiscoveryQuery) -> tuple[Definition, ...]:
        """Current authorized published/reviewed full topic/exact age source rows.
        Do not filter readiness/material/history. Server verifies query age/context.
        """
        ...

    def warnings(self, definition: Definition) -> tuple[str, ...]: ...
    def check(self) -> None:
        """Current authorization/publication/revocation held through projection."""
        ...


class DiscoveryBoundary(Protocol):
    def guard(self, actor: Actor) -> AbstractContextManager[DiscoveryAccess]: ...


class Recommender(Protocol):
    def rank(
        self, query: DiscoveryQuery, rows: tuple[Definition, ...]
    ) -> tuple[tuple[ExactRef, str], ...]:
        """Bounded same-candidate exact refs/reasons, no changed instructions/scope.
        Provider optional/injected; no fake AI scores or hidden fallback activation.
        """
        ...
