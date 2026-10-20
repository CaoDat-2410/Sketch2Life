"""ASSUMED delivery policy and MEMORY transaction/synthetic hook only, never adoption."""

from datetime import timedelta

from sketch2life.application.ai_policy_copy_dispatch import ProviderCopyDispatcher
from sketch2life.contracts.schemas.ai_policy_copy import CopyAuthorityGrant
from sketch2life.contracts.schemas.ai_policy_copy_delivery import (
    CopyDeliveryAuthority,
    CopyHookResponse,
)
from tests.ai_policy_copy_operation_fixtures import AssumedOperationBoundary, schedule
from tests.ai_policy_copy_operation_fixtures import setup as operation_setup
from tests.unit.test_ai_policy_domain import NOW


class AssumedDispatchBoundary(AssumedOperationBoundary):
    def __init__(self, inventory):
        super().__init__(inventory)
        self.delivery_calls = []
        self.denied_phase = None
        self.authority_changes = {}
        self.deadline = NOW + timedelta(minutes=1)
        self.on_authorize = None

    def authorize_delivery(self, envelope, state, phase, digest):
        assert self.inventory.held
        self.delivery_calls.append((phase, state, self.inventory.in_transaction))
        if self.on_authorize:
            self.on_authorize(phase, state)
        raw = CopyDeliveryAuthority(
            grant=CopyAuthorityGrant(
                principal_id="operator",
                organization_id="school",
                command_digest=digest,
                authority_revision="fixture-worker-policy",
                expires_at=NOW + timedelta(hours=1),
                allowed=phase != self.denied_phase,
            ),
            claim_deadline=self.deadline,
        )
        return raw.model_copy(update=self.authority_changes)


class SyntheticHook:
    def __init__(self, boundary):
        self.boundary, self.calls = boundary, []
        self.fail = False
        self.changes = {}
        self.on_call = None

    def dispatch(self, envelope):
        assert self.boundary.inventory.held
        assert not self.boundary.inventory.in_transaction
        self.calls.append(envelope)
        if self.on_call:
            self.on_call(envelope)
        if self.fail:
            raise RuntimeError("synthetic-private-provider-token-url")
        return CopyHookResponse(
            operation_key=envelope.operation_key,
            binding_digest=envelope.binding_digest,
            outcome="pending",
            reason_code="WAITING",
        ).model_copy(update=self.changes)


def setup(operation="purge"):
    scheduler, operation_boundary, store = operation_setup()
    envelope = schedule(scheduler, operation=operation)
    store.clock = lambda: NOW
    boundary = AssumedDispatchBoundary(operation_boundary.inventory)
    hook = SyntheticHook(boundary)
    dispatcher = ProviderCopyDispatcher(store, boundary, hook, clock=lambda: NOW)
    return dispatcher, boundary, hook, store, envelope


def dispatch(dispatcher, envelope, *, revision=0):
    return dispatcher.dispatch(
        "operator", "school", envelope.command, envelope.operation_key, expected_revision=revision
    )
