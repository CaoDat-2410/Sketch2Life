"""Pure resource accounting. Callers own verified quotes, authority and atomic storage."""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from enum import StrEnum

from sketch2life.domain.ai_policy.model import PolicyError

_ID = re.compile(r"[A-Za-z0-9_.:-]{1,120}\Z")
_HASH = re.compile(r"[0-9a-f]{64}\Z")


def _integer(value: int) -> None:
    if type(value) is not int or value < 0:
        raise PolicyError("AI_POLICY_INVALID_ACCOUNTING_QUANTITY")


def _identifier(value: str) -> None:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise PolicyError("AI_POLICY_INVALID_ACCOUNTING_ID")


def _digest(value: str) -> None:
    if not isinstance(value, str) or not _HASH.fullmatch(value):
        raise PolicyError("AI_POLICY_INVALID_ACCOUNTING_BINDING")


@dataclass(frozen=True, slots=True)
class DefinitionKey:
    ref: str
    version: int
    hash: str

    def __post_init__(self) -> None:
        _identifier(self.ref)
        _integer(self.version)
        if self.version < 1:
            raise PolicyError("AI_POLICY_INVALID_ACCOUNTING_BINDING")
        _digest(self.hash)


@dataclass(frozen=True, slots=True)
class BudgetKey:
    organization_id: str
    feature_scope: str
    definition: DefinitionKey
    unit: str
    window_id: str

    def __post_init__(self) -> None:
        for value in (self.organization_id, self.feature_scope, self.unit, self.window_id):
            _identifier(value)
        if not isinstance(self.definition, DefinitionKey):
            raise PolicyError("AI_POLICY_INVALID_ACCOUNTING_BINDING")


@dataclass(frozen=True, slots=True)
class LimitTerms:
    key: BudgetKey
    concurrency_definition: DefinitionKey
    budget_ceiling: int
    concurrency_ceiling: int

    def __post_init__(self) -> None:
        if not isinstance(self.key, BudgetKey) or not isinstance(
            self.concurrency_definition, DefinitionKey
        ):
            raise PolicyError("AI_POLICY_INVALID_ACCOUNTING_BINDING")
        _integer(self.budget_ceiling)
        _integer(self.concurrency_ceiling)


@dataclass(frozen=True, slots=True)
class LedgerSnapshot:
    """Atomic view: per-bucket held/spent, GLOBAL org/feature occupied slots."""

    key: BudgetKey
    held_units: int
    spent_units: int
    scope_occupied_slots: int

    def __post_init__(self) -> None:
        if not isinstance(self.key, BudgetKey):
            raise PolicyError("AI_POLICY_INVALID_ACCOUNTING_BINDING")
        for value in (self.held_units, self.spent_units, self.scope_occupied_slots):
            _integer(value)


class ReservationState(StrEnum):
    RESERVED = "reserved"
    CONSUMED = "consumed"
    RELEASED = "released"


class SettlementOutcome(StrEnum):
    CONSUME = "consume"
    RELEASE = "release"


class AccountingEvidence(StrEnum):
    FIXTURE = "fixture"
    RUNTIME = "verified_runtime"


@dataclass(frozen=True, slots=True)
class SettlementProof:
    receipt_id: str
    reservation_id: str
    request_digest: str
    attempt_id: str
    key: BudgetKey
    outcome: SettlementOutcome
    actual_units: int
    evidence_kind: AccountingEvidence
    verified: bool

    def __post_init__(self) -> None:
        for value in (self.receipt_id, self.reservation_id, self.attempt_id):
            _identifier(value)
        _digest(self.request_digest)
        _integer(self.actual_units)
        if (
            not isinstance(self.outcome, SettlementOutcome)
            or not isinstance(self.evidence_kind, AccountingEvidence)
            or not isinstance(self.key, BudgetKey)
            or type(self.verified) is not bool
        ):
            raise PolicyError("AI_POLICY_INVALID_ACCOUNTING_PROOF")


@dataclass(frozen=True, slots=True)
class Reservation:
    reservation_id: str
    request_digest: str
    attempt_id: str
    terms: LimitTerms
    estimated_units: int
    state: ReservationState = ReservationState.RESERVED
    settlement: SettlementProof | None = None

    def __post_init__(self) -> None:
        _identifier(self.reservation_id)
        _identifier(self.attempt_id)
        _digest(self.request_digest)
        _integer(self.estimated_units)
        if not isinstance(self.terms, LimitTerms):
            raise PolicyError("AI_POLICY_INVALID_ACCOUNTING_BINDING")
        if not isinstance(self.state, ReservationState):
            raise PolicyError("AI_POLICY_INVALID_RESERVATION")
        if (self.state == ReservationState.RESERVED) != (self.settlement is None):
            raise PolicyError("AI_POLICY_INVALID_RESERVATION")
        if self.settlement is not None:
            proof = self.settlement
            if not isinstance(proof, SettlementProof):
                raise PolicyError("AI_POLICY_INVALID_RESERVATION")
            expected_state = (
                ReservationState.CONSUMED
                if proof.outcome == SettlementOutcome.CONSUME
                else ReservationState.RELEASED
            )
            if (
                proof.verified is not True
                or self.state != expected_state
                or (proof.reservation_id, proof.request_digest, proof.attempt_id, proof.key)
                != (self.reservation_id, self.request_digest, self.attempt_id, self.terms.key)
                or (proof.outcome == SettlementOutcome.RELEASE and proof.actual_units != 0)
            ):
                raise PolicyError("AI_POLICY_INVALID_RESERVATION")

    @property
    def actual_usage_proven(self) -> bool:
        return bool(
            self.state == ReservationState.CONSUMED
            and self.settlement is not None
            and self.settlement.verified is True
            and self.settlement.evidence_kind == AccountingEvidence.RUNTIME
        )

    @property
    def overrun(self) -> bool:
        return self.settlement is not None and self.settlement.actual_units > self.estimated_units


@dataclass(frozen=True, slots=True)
class AccountingChange:
    snapshot: LedgerSnapshot
    reservation: Reservation
    replayed: bool = False


def reserve(
    snapshot: LedgerSnapshot,
    terms: LimitTerms,
    *,
    reservation_id: str,
    request_digest: str,
    attempt_id: str,
    estimated_units: int,
    existing: Reservation | None = None,
) -> AccountingChange:
    _integer(estimated_units)
    proposed = Reservation(reservation_id, request_digest, attempt_id, terms, estimated_units)
    if snapshot.key != terms.key:
        raise PolicyError("AI_POLICY_ACCOUNTING_SCOPE_MISMATCH")
    if existing is not None:
        if existing.state != ReservationState.RESERVED:
            raise PolicyError("AI_POLICY_RESERVATION_TERMINAL")
        if existing != proposed:
            raise PolicyError("AI_POLICY_RESERVATION_CONFLICT")
        return AccountingChange(snapshot, existing, True)
    if (
        terms.budget_ceiling == 0
        or snapshot.held_units + snapshot.spent_units + estimated_units > terms.budget_ceiling
    ):
        raise PolicyError("AI_POLICY_BUDGET_EXCEEDED")
    if snapshot.scope_occupied_slots + 1 > terms.concurrency_ceiling:
        raise PolicyError("AI_POLICY_CONCURRENCY_EXCEEDED")
    return AccountingChange(
        replace(
            snapshot,
            held_units=snapshot.held_units + estimated_units,
            scope_occupied_slots=snapshot.scope_occupied_slots + 1,
        ),
        proposed,
    )


def settle(
    snapshot: LedgerSnapshot, reservation: Reservation, proof: SettlementProof
) -> AccountingChange:
    """Also used by reconciliation after authoritative terminal disposition verification."""
    if snapshot.key != reservation.terms.key:
        raise PolicyError("AI_POLICY_ACCOUNTING_SCOPE_MISMATCH")
    if (proof.reservation_id, proof.request_digest, proof.attempt_id, proof.key) != (
        reservation.reservation_id,
        reservation.request_digest,
        reservation.attempt_id,
        reservation.terms.key,
    ):
        raise PolicyError("AI_POLICY_ACCOUNTING_PROOF_MISMATCH")
    if proof.verified is not True:
        raise PolicyError("AI_POLICY_ACCOUNTING_PROOF_UNVERIFIED")
    if proof.outcome == SettlementOutcome.RELEASE and proof.actual_units != 0:
        raise PolicyError("AI_POLICY_INVALID_ACCOUNTING_PROOF")
    if reservation.state != ReservationState.RESERVED:
        if reservation.settlement != proof:
            raise PolicyError("AI_POLICY_SETTLEMENT_CONFLICT")
        return AccountingChange(snapshot, reservation, True)
    if snapshot.held_units < reservation.estimated_units or snapshot.scope_occupied_slots < 1:
        raise PolicyError("AI_POLICY_ACCOUNTING_BALANCE_CONFLICT")
    state = (
        ReservationState.CONSUMED
        if proof.outcome == SettlementOutcome.CONSUME
        else ReservationState.RELEASED
    )
    # Actual incurred usage is never capped/hidden by the estimate or ceiling.
    # A resulting over-budget snapshot rejects future reserves, not history.
    updated = replace(
        snapshot,
        held_units=snapshot.held_units - reservation.estimated_units,
        spent_units=snapshot.spent_units + proof.actual_units,
        scope_occupied_slots=snapshot.scope_occupied_slots - 1,
    )
    return AccountingChange(updated, replace(reservation, state=state, settlement=proof))
