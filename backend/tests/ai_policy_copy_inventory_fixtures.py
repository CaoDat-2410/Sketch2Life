"""ASSUMED owner/source authority and transactional MEMORY inventory, never production."""

import copy
from contextlib import contextmanager
from datetime import timedelta

from sketch2life.application.ai_policy_copy_inventory import ProviderCopyInventoryService
from sketch2life.application.ports.ai_policy_copy_registry import (
    CopyRegistryPage,
    RegisteredProviderCopy,
)
from sketch2life.contracts.schemas.ai_policy import PolicyDefinitionRef
from sketch2life.contracts.schemas.ai_policy_copy import CopyAuthorityGrant, CopyReceiptReference
from sketch2life.contracts.schemas.ai_policy_copy_inventory import (
    CopyInventoryContext,
    CopyInventoryCoverageProof,
    CopyInventoryReadRequest,
    CopyInventorySourceProof,
)
from sketch2life.contracts.schemas.ai_policy_copy_registry import (
    CopyCoverageObservation,
    CopyRegistryRegistration,
)
from sketch2life.domain.ai_policy.model import PolicyError
from tests.unit.test_ai_policy_domain import NOW

PROFILE = PolicyDefinitionRef(ref="fixture-profile", version=1, hash="a" * 64)
SOURCE = CopyReceiptReference(ref="fixture-source", hash="b" * 64)
COVERAGE = CopyReceiptReference(ref="fixture-coverage", hash="c" * 64)


def context(**changes):
    return CopyInventoryContext.model_validate(
        dict(data_request_ref=PROFILE, scope_ref="scope") | changes
    )


def registration(**changes):
    return CopyRegistryRegistration.model_validate(
        dict(
            organization_id="school",
            scope_ref="scope",
            copy_id="copy",
            kind="input",
            original_profile_ref=PROFILE,
        )
        | changes
    )


def read_request(**changes):
    return CopyInventoryReadRequest.model_validate(
        context().model_dump(mode="python") | dict(limit=2) | changes
    )


class AssumedInventoryBoundary:
    def __init__(self):
        self.held, self.in_transaction = False, False
        self.allowed = {"register", "read", "coverage", "fence"}
        self.grant_changes, self.confirm_changes = {}, {}
        self.source_changes, self.coverage_changes, self.observation_changes = {}, {}, {}
        self.auth_calls, self.sources = [], []
        self.fail_source, self.fail_exit = False, False
        self.proof_expiry = NOW + timedelta(minutes=30)

    @contextmanager
    def guard(self, principal, organization, ctx):
        self.held = True
        try:
            yield self
            if self.fail_exit:
                raise RuntimeError("synthetic-private-owner-exit")
        finally:
            self.held = False

    def authorize(self, ctx, action, digest):
        assert self.held
        self.auth_calls.append((ctx, action, digest, self.in_transaction))
        return CopyAuthorityGrant(
            organization_id="school",
            principal_id="operator",
            command_digest=digest,
            authority_revision="fixture-owner-revision",
            expires_at=NOW + timedelta(hours=1),
            allowed=action in self.allowed,
        ).model_copy(
            update=self.grant_changes | (self.confirm_changes if self.in_transaction else {})
        )

    def registration_source(self, ctx, proposed, reference, digest):
        assert self.held and not self.in_transaction
        self.sources.append(("register", ctx, proposed, reference, digest))
        if self.fail_source:
            raise RuntimeError("synthetic-private-source-token")
        if reference != SOURCE:
            raise PolicyError("AI_POLICY_COPY_SOURCE_UNVERIFIED")
        return CopyInventorySourceProof(
            binding_digest=digest, reference=reference, verified=True, expires_at=self.proof_expiry
        ).model_copy(update=self.source_changes)

    def coverage_source(self, ctx, expected_revision, reference, digest):
        assert self.held and not self.in_transaction
        self.sources.append(("coverage", ctx, expected_revision, reference, digest))
        if self.fail_source:
            raise RuntimeError("synthetic-private-source-token")
        if reference != COVERAGE:
            raise PolicyError("AI_POLICY_COPY_SOURCE_UNVERIFIED")
        observation = CopyCoverageObservation(
            organization_id="school",
            scope_ref=ctx.scope_ref,
            expected_revision=expected_revision,
            registry_revision="fixture-registry",
            attestation_ref=reference,
            required_sources=("fixture-source",),
            observed_sources=("fixture-source",),
        ).model_copy(update=self.observation_changes)
        return CopyInventoryCoverageProof.model_construct(
            binding_digest=digest,
            reference=reference,
            verified=True,
            expires_at=self.proof_expiry,
            observation=observation,
        ).model_copy(update=self.coverage_changes)


class MemoryInventory:
    def __init__(self, boundary):
        self.boundary, self.scopes = boundary, {}
        self.fail_commit, self.commits = False, 0

    @contextmanager
    def transaction(self, org, scope, *, principal_id, for_update=False):
        assert self.boundary.held
        previous = copy.deepcopy(self.scopes)
        self.org, self.scope, self.write = org, scope, for_update
        self.boundary.in_transaction = True
        self.state = self.scopes.get(
            (org, scope), dict(revision=0, purging=False, rows={}, events=[], coverage=None)
        )
        if for_update:
            self.scopes[org, scope] = self.state
        try:
            yield self
            assert self.boundary.held
            if self.fail_commit:
                raise PolicyError("SYNTHETIC_INVENTORY_COMMIT_FAILURE")
            self.commits += 1
        except Exception:
            self.scopes = previous
            raise
        finally:
            self.boundary.in_transaction = False

    def _advance(self, kind):
        assert self.write and self.boundary.held
        self.state["revision"] += 1
        self.state["events"].append((self.state["revision"], kind))
        return self.state["revision"]

    def get(self, copy_id):
        return self.state["rows"].get(copy_id)

    def register(self, proposed):
        assert self.write
        old = self.get(proposed.copy_id)
        if old:
            if old.registration != proposed:
                raise PolicyError("AI_POLICY_COPY_REGISTRATION_CONFLICT")
            return old
        result = RegisteredProviderCopy(proposed, self.state["purging"])
        self.state["rows"][proposed.copy_id] = result
        self._advance("register")
        return result

    def mark_purging(self):
        assert self.write
        if not self.state["purging"]:
            self.state["purging"] = True
            self._advance("fence")
        return self.state["revision"]

    def record_coverage(self, observation):
        assert self.write
        if observation.expected_revision != self.state["revision"]:
            raise PolicyError("AI_POLICY_COPY_REGISTRY_STALE")
        revision = self._advance("coverage")
        self.state["coverage"] = revision, observation
        return revision

    def page(self, *, limit, after=None, expected_revision=None):
        revision = self.state["revision"]
        if expected_revision is not None and expected_revision != revision:
            raise PolicyError("AI_POLICY_COPY_REGISTRY_STALE")
        rows = sorted(key for key in self.state["rows"] if after is None or key > after)
        values = tuple(self.state["rows"][key] for key in rows[:limit])
        report = self.state["coverage"]
        return CopyRegistryPage(
            revision,
            self.state["purging"],
            values,
            rows[limit - 1] if len(rows) > limit else None,
            report[1] if report and report[0] == revision else None,
        )


def setup():
    boundary = AssumedInventoryBoundary()
    store = MemoryInventory(boundary)
    service = ProviderCopyInventoryService(store, boundary, clock=lambda: NOW)
    return service, boundary, store
