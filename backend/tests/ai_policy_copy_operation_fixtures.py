"""ASSUMED operation authority on transactional MEMORY inventory, not real providers."""

from contextlib import contextmanager
from datetime import timedelta

from sketch2life.application.ai_policy_copy_operations import ProviderCopyOperationService
from sketch2life.contracts.schemas.ai_policy_copy import CopyAuthorityGrant, ProviderCopyCommand
from tests.ai_policy_copy_inventory_fixtures import PROFILE, SOURCE, context, registration
from tests.ai_policy_copy_inventory_fixtures import setup as inventory_setup
from tests.unit.test_ai_policy_domain import NOW


def command(**changes):
    return ProviderCopyCommand.model_validate(
        dict(
            client_request_id="fixture-request",
            data_request_ref=PROFILE,
            scope_ref="scope",
            operation="purge",
        )
        | changes
    )


class AssumedOperationBoundary:
    def __init__(self, inventory_boundary):
        self.inventory = inventory_boundary
        self.changes, self.final_changes = {}, {}
        self.profile, self.calls, self.profile_calls = PROFILE, [], []
        self.fail_profile, self.fail_exit = False, False

    @contextmanager
    def guard(self, principal, org):
        self.inventory.held = True
        try:
            yield self
            if self.fail_exit:
                raise RuntimeError("synthetic-private-guard-exit")
        finally:
            self.inventory.held = False

    def authorize(self, request, digest):
        assert self.inventory.held
        self.calls.append((request, digest, self.inventory.in_transaction))
        return CopyAuthorityGrant(
            principal_id="operator",
            organization_id="school",
            command_digest=digest,
            authority_revision="fixture-owner",
            expires_at=NOW + timedelta(hours=1),
            allowed=True,
        ).model_copy(
            update=self.changes | (self.final_changes if self.inventory.in_transaction else {})
        )

    def resolve_profile(self, copy):
        assert self.inventory.held and not self.inventory.in_transaction
        self.profile_calls.append(copy)
        if self.fail_profile:
            raise RuntimeError("synthetic-private-profile-error")
        return self.profile


def setup():
    inventory, boundary, store = inventory_setup()
    inventory.register("operator", "school", context(), registration(), SOURCE)
    authority = AssumedOperationBoundary(boundary)
    service = ProviderCopyOperationService(store, authority, clock=lambda: NOW)
    return service, authority, store


def schedule(service, **changes):
    return service.schedule("operator", "school", command(**changes), "copy")
