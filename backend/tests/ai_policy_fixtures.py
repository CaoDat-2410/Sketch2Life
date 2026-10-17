"""Assumed BE2-14 owner/registry and transactional MEMORY fixtures, never production."""

import copy
import json
from contextlib import contextmanager
from dataclasses import replace

from sketch2life.application.ai_policy_commands import AiPolicyCommands
from sketch2life.application.ports.ai_policy import EffectivePolicyScope
from sketch2life.contracts.schemas.ai_policy import AiPolicyCommand
from sketch2life.domain.ai_policy.model import Authority, Capability, PolicyError
from tests.contract.test_ai_policy_contracts import BODY
from tests.unit.test_ai_policy_compatibility import AssumedRegistry
from tests.unit.test_ai_policy_domain import NOW


class AssumedCommandBoundary(AssumedRegistry):
    def __init__(self):
        super().__init__()
        self.review_policy_version = "fixture.governance"
        self.revoked_proofs = set()
        self.rights = {
            "author": {Capability.AUTHOR},
            "reviewer": {Capability.REVIEW_SAFETY, Capability.REVIEW_PEDAGOGICAL,
                         Capability.PUBLISH},
            "publisher": {Capability.PUBLISH}, "operator": {Capability.DISABLE},
        }

    @contextmanager
    def guard(self, principal_id, organization_id):
        self.authority = Authority(principal_id, "school",
                                   frozenset(self.rights.get(principal_id, ())))
        with super().guard(principal_id, organization_id) as access:
            yield access

    def review_effective(self, policy, proof):
        assert self.held
        return proof.review_id not in self.revoked_proofs


class MemoryPolicyStore:
    def __init__(self, boundary):
        self.boundary = boundary
        self.heads, self.versions, self.proofs, self.receipts, self.scopes = {}, {}, {}, {}, {}
        self.events, self.scope_events = [], []
        self.fail_receipt = False
        self.fail_commit = False
        self.fail_scope = False

    @contextmanager
    def transaction(self):
        assert self.boundary.held
        names = ("heads", "versions", "proofs", "receipts", "scopes", "events", "scope_events")
        snapshot = copy.deepcopy({name: getattr(self, name) for name in names})
        try:
            yield self
            assert self.boundary.held  # guard retained through simulated commit.
            if self.fail_commit:
                raise PolicyError("SYNTHETIC_COMMIT_FAILURE")
        except Exception:
            for name, value in snapshot.items():
                setattr(self, name, value)
            raise

    def load(self, organization_id, record_id, *, version=None, for_update=False):
        head = self.heads.get((organization_id, record_id))
        if head is None:
            return None
        item = self.versions.get((organization_id, record_id, head.version if version is None
                                  else version))
        return None if item is None else replace(item, revision=head.revision)

    def feature_scope(self, organization_id, record_id):
        item = self.load(organization_id, record_id)
        return None if item is None else json.loads(item.body_json)["feature_scope"]

    def stopped_since(self, organization_id, feature_scope, *, after_epoch):
        return any(scope.organization_id == organization_id
                   and scope.feature_scope == feature_scope and scope.epoch > after_epoch
                   and scope.disabled for scope, event in self.scope_events)

    def was_activated(self, expected):
        return any(scope == expected and scope.disabled is False
                   for scope, event in self.scope_events)

    def effective_scope(self, organization_id, feature_scope, *, for_update=False):
        key = organization_id, feature_scope
        if key not in self.scopes and for_update:
            self.scopes[key] = EffectivePolicyScope(*key)
        return self.scopes.get(key)

    def save_scope(self, scope, *, expected_epoch, event):
        key = scope.organization_id, scope.feature_scope
        assert self.scopes[key].epoch == expected_epoch
        assert scope.epoch == expected_epoch + 1
        self.scopes[key] = scope
        self.scope_events.append((scope, event))
        if self.fail_scope:
            raise PolicyError("SYNTHETIC_SCOPE_FAILURE")

    def save(self, policy, *, expected_revision, event):
        key = policy.organization_id, policy.record_id
        current = self.heads.get(key)
        if (current.revision if current else None) != expected_revision:
            raise PolicyError("AI_POLICY_STALE_REVISION")
        self.versions[(*key, policy.version)] = policy
        if current is None or policy.version >= current.version:
            self.heads[key] = policy
        else:
            self.heads[key] = replace(current, revision=policy.revision)
        for proof in policy.reviews:
            self.proofs[(policy.organization_id, proof.review_id)] = proof
        self.events.append(event)

    def receipt(self, organization_id, principal_id, request_id):
        return self.receipts.get((organization_id, principal_id, request_id))

    def add_receipt(self, receipt):
        if self.fail_receipt:
            raise PolicyError("SYNTHETIC_RECEIPT_FAILURE")
        key = receipt.organization_id, receipt.principal_id, receipt.request_id
        if key in self.receipts:
            raise PolicyError("AI_POLICY_WRITE_CONFLICT")
        self.receipts[key] = receipt


def harness():
    boundary = AssumedCommandBoundary()
    store = MemoryPolicyStore(boundary)
    return AiPolicyCommands(store, boundary, clock=lambda: NOW), boundary, store


def command(action, key, record=None, **fields):
    value = dict(record_kind="policy", policy_kind="ai", action=action, client_request_id=key)
    if record is not None:
        value.update(record_id=record.record_id, target_version=record.version,
                     target_hash=record.hash)
    value.update(fields)
    return AiPolicyCommand.model_validate_json(json.dumps(value))


def execute(service, actor, action, key, record=None, **fields):
    return service.execute(actor, "school", command(action, key, record, **fields),
                           expected_revision=None if record is None else record.revision)


def submitted(service, prefix="one"):
    result = execute(service, "author", "create", prefix + "-create", policy=BODY)
    return execute(service, "author", "submit_review", prefix + "-submit", result.record)


def reviewed(service, store, prefix="one", record=None):
    result = submitted(service, prefix) if record is None else record
    for dimension in ("safety", "pedagogical"):
        item = load_for_fixture(store, result.record.record_id)
        result = execute(service, "reviewer", "record_review", prefix + "-" + dimension,
                         result.record, review=dict(
                             target_kind="ai_policy", target_id=item.record_id,
                             target_version=item.version, target_hash=item.hash,
                             context_revision=item.context_revision,
                             expected_review_revision=item.review_revision,
                             dimension=dimension, decision="approve",
                             review_policy_version="fixture.governance"))
    return result


def published(service, store, prefix="one"):
    result = reviewed(service, store, prefix)
    return publish(service, store, result.record, prefix + "-publish")


def publish(service, store, record, key):
    item = load_for_fixture(store, record.record_id)
    return execute(service, "publisher", "publish", key, record, review_ref=dict(
        safety_review_id=item.reviews[0].review_id,
        pedagogical_review_id=item.reviews[1].review_id,
        review_policy_version="fixture.governance"))


def load_for_fixture(store, record_id):
    """Test inspection only, not a production authorization shortcut."""
    if isinstance(store, MemoryPolicyStore):
        return store.load("school", record_id)
    with store.transaction() as tx:
        return tx.load("school", record_id)
