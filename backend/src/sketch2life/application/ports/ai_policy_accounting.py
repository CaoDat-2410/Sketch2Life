"""Authoritative accounting evidence/quote port; no permissive runtime adapter supplied."""

from contextlib import AbstractContextManager
from typing import Literal, Protocol

from sketch2life.contracts.schemas.ai_policy_accounting import AccountingEvidenceRef, ResourceQuote
from sketch2life.contracts.schemas.ai_policy_use import PolicyUseObservation
from sketch2life.domain.ai_policy.accounting import Reservation, SettlementProof
from sketch2life.domain.ai_policy.model import Authority


class ResourceAccountingAccess(Protocol):
    authority: Authority

    def quote(
        self, observation: PolicyUseObservation, attempt_id: str, binding_digest: str
    ) -> ResourceQuote:
        """Resolve exact approved units/window/ceilings/estimate for CURRENT held lease.

        Verify request/pin/attempt authority and actual adopted budget/concurrency
        definitions/current profile compatibility. Returned observation, digest,
        attempt and all exact references must match. No production defaults or
        caller numeric override. Keep decisions/definition values stable to commit.
        Caller independently validates response, then atomically reserves counters.
        """
        ...

    def verify_settlement(
        self,
        reservation: Reservation,
        evidence_ref: AccountingEvidenceRef,
        operation: Literal["consume", "release", "reconcile"],
    ) -> SettlementProof:
        """Verify CURRENT accounting rights and exact immutable terminal usage/disposition.

        Bind org/feature/request/attempt/reservation/original unit/window/digest.
        Resolve backend evidence bytes/hash, authenticated issuer/receipt and final
        outcome, not a client verified flag/units/claim. Unknown/ongoing outcome
        must not refund or settle. Keep fixture vs actual-runtime evidence distinct.
        Reconcile translates only a verified terminal outcome to consume/release.
        Cleanup may remain permitted after AI eligibility withdrawal, NEVER grants
        another attempt. Original bucket/unit/window retained; no invented expiry.
        """
        ...


class ResourceAccountingBoundary(Protocol):
    def guard(
        self, principal_id: str, organization_id: str
    ) -> AbstractContextManager[ResourceAccountingAccess]:
        """Verified accounting identity/scope, authoritative quote/proof guards to commit.

        Real owner adapter must adopt consistent lock order with current-use fence
        and own ledger UoW. Role/monitor/author alone is not accounting authority.
        This candidate protocol is not runtime fencing or actual cost evidence.
        """
        ...
