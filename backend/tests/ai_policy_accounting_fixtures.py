"""ASSUMED accounting boundary + transactional MEMORY ledger, never runtime adapters."""

import copy
from contextlib import contextmanager
from dataclasses import replace

from sketch2life.application.ai_policy_accounting import ResourceAccountingService
from sketch2life.contracts.schemas.ai_policy_accounting import AccountingEvidenceRef, ResourceQuote
from sketch2life.domain.ai_policy import accounting as domain
from sketch2life.domain.ai_policy.model import Authority, PolicyError
from tests.unit.test_ai_policy_domain import NOW
from tests.unit.test_ai_policy_use import pin_once, setup

EVIDENCE = AccountingEvidenceRef(ref="fixture-terminal", hash="e" * 64)


class AssumedAccountingBoundary:
    def __init__(self):
        self.held, self.allowed = False, True
        self.authority_changes = {}
        self.quote_changes, self.proof_changes = {}, {}
        self.native_proof_changes = {}
        self.quote_calls, self.proof_calls = [], []
        self.quote_error, self.proof_error = False, False
        self.fail_exit = False

    @contextmanager
    def guard(self, principal_id, organization_id):
        if not self.allowed:
            raise PolicyError("AI_POLICY_FORBIDDEN")
        self.authority = replace(
            Authority(principal_id, organization_id, frozenset()), **self.authority_changes
        )
        self.held = True
        try:
            yield self
            if self.fail_exit:
                raise RuntimeError("synthetic-private-guard-exit")
        finally:
            self.held = False

    def quote(self, observation, attempt_id, binding_digest):
        assert self.held
        self.quote_calls.append((observation, attempt_id, binding_digest))
        if self.quote_error:
            raise RuntimeError("synthetic-private-adapter-token")
        return ResourceQuote(
            quote_id="fixture-quote",
            binding_digest=binding_digest,
            observation=observation,
            attempt_id=attempt_id,
            unit="fixture-unit",
            window_id="fixture-window",
            budget_ceiling=10,
            concurrency_ceiling=2,
            estimated_units=4,
        ).model_copy(update=self.quote_changes)

    def verify_settlement(self, reservation, evidence_ref, operation):
        assert self.held
        self.proof_calls.append((reservation, evidence_ref, operation))
        if self.proof_error:
            raise RuntimeError("synthetic-private-adapter-token")
        if evidence_ref != EVIDENCE:
            raise PolicyError("AI_POLICY_ACCOUNTING_PROOF_UNVERIFIED")
        proof = domain.SettlementProof(
            "fixture-proof",
            reservation.reservation_id,
            reservation.request_digest,
            reservation.attempt_id,
            reservation.terms.key,
            domain.SettlementOutcome.CONSUME,
            3,
            domain.AccountingEvidence.FIXTURE,
            True,
        )
        proof = replace(proof, **self.proof_changes)
        for field, value in self.native_proof_changes.items():
            object.__setattr__(proof, field, value)
        return proof


class MemoryResourceLedger:
    def __init__(self, accounting_boundary, use_boundary):
        self.accounting_boundary, self.use_boundary = accounting_boundary, use_boundary
        self.slots, self.buckets, self.reservations, self.receipts, self.events = {}, {}, {}, {}, {}
        self.fail_receipt, self.fail_commit = False, False
        self.commit_count = 0

    @contextmanager
    def transaction(self, organization_id, feature_scope):
        assert self.accounting_boundary.held
        self.org, self.feature = organization_id, feature_scope
        self.reserved_in_transaction = False
        names = ("slots", "buckets", "reservations", "receipts", "events")
        previous = copy.deepcopy({name: getattr(self, name) for name in names})
        try:
            yield self
            assert self.accounting_boundary.held
            if self.reserved_in_transaction:
                assert self.use_boundary.held  # Commit remains inside current-use fence.
            if self.fail_commit:
                raise PolicyError("SYNTHETIC_LEDGER_COMMIT_FAILURE")
            self.commit_count += 1
        except Exception:
            for name, value in previous.items():
                setattr(self, name, value)
            raise

    def snapshot(self, terms):
        key = terms.key
        if (key.organization_id, key.feature_scope) != (self.org, self.feature):
            raise PolicyError("AI_POLICY_ACCOUNTING_SCOPE_MISMATCH")
        held, spent = self.buckets.get(key, (0, 0))
        return domain.LedgerSnapshot(key, held, spent, self.slots.get((self.org, self.feature), 0))

    def reservation(self, reservation_id):
        value = self.reservations.get((self.org, reservation_id))
        if value and value.terms.key.feature_scope != self.feature:
            raise PolicyError("AI_POLICY_ACCOUNTING_SCOPE_MISMATCH")
        return value

    def attempt(self, request_digest, attempt_id):
        return next(
            (
                value
                for (org, _), value in self.reservations.items()
                if org == self.org
                and value.request_digest == request_digest
                and value.attempt_id == attempt_id
            ),
            None,
        )

    def receipt(self, principal_id, client_request_id):
        value = self.receipts.get((self.org, principal_id, client_request_id))
        if value is None:
            return None
        if value[0] != self.feature:
            raise PolicyError("AI_POLICY_RESOURCE_RECEIPT_CONFLICT")
        return value[1]

    def add_receipt(self, receipt):
        if self.fail_receipt:
            raise PolicyError("SYNTHETIC_LEDGER_RECEIPT_FAILURE")
        key = self.org, receipt.principal_id, receipt.client_request_id
        if key in self.receipts:
            raise PolicyError("AI_POLICY_RESOURCE_WRITE_CONFLICT")
        self.receipts[key] = (self.feature, receipt)

    def reserve(self, terms, *, reservation_id, request_digest, attempt_id, estimated_units, event):
        assert self.use_boundary.held  # Current use retained through mutation, not just quote.
        self.reserved_in_transaction = True
        previous = self.reservation(reservation_id)
        by_attempt = self.attempt(request_digest, attempt_id)
        if by_attempt is not None and by_attempt != previous:
            raise PolicyError("AI_POLICY_RESERVATION_CONFLICT")
        change = domain.reserve(
            self.snapshot(terms),
            terms,
            reservation_id=reservation_id,
            request_digest=request_digest,
            attempt_id=attempt_id,
            estimated_units=estimated_units,
            existing=previous,
        )
        self._save(change, event)
        return change

    def settle(self, reservation_id, proof, *, event):
        previous = self.reservation(reservation_id)
        if previous is None:
            raise PolicyError("AI_POLICY_RESERVATION_NOT_FOUND")
        change = domain.settle(self.snapshot(previous.terms), previous, proof)
        self._save(change, event)
        return change

    def _save(self, change, event):
        assert self.accounting_boundary.held
        if change.replayed:
            return
        key = self.org, event.event_id
        if key in self.events:
            raise PolicyError("AI_POLICY_RESOURCE_WRITE_CONFLICT")
        self.events[key] = (event, change)
        self.reservations[self.org, change.reservation.reservation_id] = change.reservation
        self.buckets[change.snapshot.key] = change.snapshot.held_units, change.snapshot.spent_units
        self.slots[self.org, self.feature] = change.snapshot.scope_occupied_slots


def accounting_setup():
    leases, policy_service, use_boundary, policy_store = setup()
    pin = pin_once(leases)
    boundary = AssumedAccountingBoundary()
    store = MemoryResourceLedger(boundary, use_boundary)
    service = ResourceAccountingService(store, boundary, leases, clock=lambda: NOW)
    return service, boundary, store, pin, policy_service, use_boundary, policy_store
