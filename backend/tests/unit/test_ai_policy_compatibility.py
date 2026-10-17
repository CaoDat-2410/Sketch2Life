"""Assumed current registry/identity component only; no real adoption or SQL fence."""

import json
from contextlib import contextmanager
from dataclasses import FrozenInstanceError, replace

import pytest

from sketch2life.application.ai_policy_compatibility import PolicyCompatibility
from sketch2life.application.ports.ai_policy_registry import DefinitionBinding
from sketch2life.contracts.schemas.ai_policy import AiPolicyWrite, PolicyDefinitionRef
from sketch2life.domain.ai_policy.model import Authority, Capability, PolicyError
from tests.contract.test_ai_policy_contracts import BODY, REF

KINDS = ("model_profile", "moderation", "retry", "budget", "concurrency")


class AssumedRegistry:
    def __init__(self):
        self.authority = Authority("author", "school", frozenset({Capability.AUTHOR}))
        self.registry_revision = "fixture-registry.1"
        self.feature = True
        self.missing = None
        self.mismatch = None
        self.change_epoch = False
        self.failure = None
        self.held = False
        self.calls = []
        self.feature_calls = 0
        self.reference_override = None

    @contextmanager
    def guard(self, principal_id, organization_id):
        if self.failure == "guard":
            raise RuntimeError("synthetic-private-token")
        self.held = True
        try:
            yield self
        finally:
            self.held = False

    def feature_available(self, feature_scope):
        assert self.held
        self.feature_calls += 1
        if self.failure == "feature":
            raise RuntimeError("synthetic-private-token")
        return self.feature

    def resolve(self, feature_scope, kind, reference):
        assert self.held
        self.calls.append((feature_scope, kind, reference))
        if self.failure == "resolve":
            raise RuntimeError("synthetic-private-token")
        if self.missing == kind:
            return None
        result = DefinitionBinding("school", feature_scope, kind,
                                   self.reference_override or reference, self.registry_revision)
        if self.change_epoch and kind == "concurrency":
            self.registry_revision = "fixture-registry.2"
        if self.mismatch and self.mismatch[0] == kind:
            result = replace(result, **self.mismatch[1])
        return result


def body():
    return AiPolicyWrite.model_validate_json(json.dumps(BODY))


def check(registry, value=None):
    return PolicyCompatibility(registry).check(
        "author", "school", body() if value is None else value)


def test_complete_exact_binding_under_guard_has_no_raw_settings():
    registry = AssumedRegistry()
    result = check(registry)
    assert result.organization_id == "school"
    assert tuple(item.kind for item in result.definitions) == KINDS
    assert result.registry_revision == "fixture-registry.1"
    assert not registry.held and len(registry.calls) == 5
    with pytest.raises(FrozenInstanceError):
        result.registry_revision = "changed"


@pytest.mark.parametrize("kind", KINDS)
def test_missing_revoked_or_incompatible_definition_denied(kind):
    registry = AssumedRegistry()
    registry.missing = kind
    with pytest.raises(PolicyError, match="AI_POLICY_DEFINITION_UNAVAILABLE"):
        check(registry)
    assert not registry.held


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("changes", [
    {"organization_id": "other-school"}, {"feature_scope": "other-feature"},
    {"kind": "unknown"}, {"registry_revision": "old-registry"},
    {"reference": PolicyDefinitionRef(**(REF | {"hash": "b" * 64}))},
    {"reference": PolicyDefinitionRef(**(REF | {"version": 2}))},
])
def test_registry_cannot_substitute_scope_role_ref_or_snapshot(kind, changes):
    registry = AssumedRegistry()
    registry.mismatch = (kind, changes)
    with pytest.raises(PolicyError, match="AI_POLICY_DEFINITION_MISMATCH"):
        check(registry)
    assert not registry.held


@pytest.mark.parametrize("value", [False, 1, "true", None])
def test_unavailable_feature_no_definition_calls(value):
    registry = AssumedRegistry()
    registry.feature = value
    with pytest.raises(PolicyError, match="AI_POLICY_FEATURE_UNAVAILABLE"):
        check(registry)
    assert not registry.calls and not registry.held


@pytest.mark.parametrize("failure", ["guard", "feature", "resolve"])
def test_registry_exception_redacted_and_no_fallback(failure):
    registry = AssumedRegistry()
    registry.failure = failure
    with pytest.raises(PolicyError, match="^AI_POLICY_REGISTRY_UNAVAILABLE$"):
        check(registry)
    assert not registry.held


@pytest.mark.parametrize("authority", [
    Authority("SuperAdmin", "school", frozenset({Capability.AUTHOR})),
    Authority("author", "other-school", frozenset({Capability.AUTHOR})),
    Authority("author", "school", frozenset({Capability.OPERATIONS_READ})),
    Authority("author", "school", frozenset()),
])
def test_identity_scope_and_capability_before_registry_queries(authority):
    registry = AssumedRegistry()
    registry.authority = authority
    with pytest.raises(PolicyError, match="AI_POLICY_FORBIDDEN"):
        check(registry)
    assert not registry.calls and registry.feature_calls == 0


def test_prior_observation_never_bypasses_current_authority_or_revocation():
    registry = AssumedRegistry()
    observed = check(registry)
    registry.missing = "budget"
    with pytest.raises(PolicyError, match="AI_POLICY_DEFINITION_UNAVAILABLE"):
        check(registry)
    assert observed.registry_revision == "fixture-registry.1"
    registry.authority = replace(registry.authority, capabilities=frozenset())
    with pytest.raises(PolicyError, match="AI_POLICY_FORBIDDEN"):
        check(registry)


def test_mid_resolution_epoch_change_fails_closed():
    registry = AssumedRegistry()
    registry.change_epoch = True
    with pytest.raises(PolicyError, match="AI_POLICY_REGISTRY_CHANGED"):
        check(registry)


@pytest.mark.parametrize("revision", ["", "private URL with spaces", None, 1])
def test_registry_revision_requires_safe_identifier(revision):
    registry = AssumedRegistry()
    registry.registry_revision = revision
    with pytest.raises(PolicyError, match="AI_POLICY_REGISTRY_UNAVAILABLE"):
        check(registry)


@pytest.mark.parametrize("value", [
    body().model_copy(update={"title": " "}),
    body().model_copy(update={"model_profile_refs": ()}),
    body().model_copy(update={"required_gates": body().required_gates.model_copy(
        update={"consent": False})}),
    body().model_copy(update={"budget_policy_ref":
                            PolicyDefinitionRef.model_construct(**(REF | {"version": True}))}),
])
def test_constructed_body_revalidated_before_registry_effect(value):
    registry = AssumedRegistry()
    with pytest.raises(PolicyError, match="AI_POLICY_INVALID_BODY"):
        check(registry, value)
    assert not registry.calls and registry.feature_calls == 0


def test_constructed_invalid_returned_reference_not_accepted_via_boolean_equality():
    registry = AssumedRegistry()
    registry.reference_override = PolicyDefinitionRef.model_construct(**(REF | {"version": True}))
    with pytest.raises(PolicyError, match="AI_POLICY_DEFINITION_MISMATCH"):
        check(registry)


def test_multiple_profiles_are_all_bound_exactly():
    registry = AssumedRegistry()
    value = AiPolicyWrite.model_validate_json(json.dumps(BODY | {
        "model_profile_refs": [REF, REF | {"ref": "second-synthetic-profile"}]}))
    result = check(registry, value)
    assert len(result.definitions) == 6
    assert result.definitions[1].reference.ref == "second-synthetic-profile"
