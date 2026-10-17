"""ASSUMED source/owner + MEMORY inventory, not actual BE1/provider/SQL integration."""

from datetime import timedelta

import pytest
from pydantic import ValidationError

from sketch2life.contracts.schemas.ai_policy_copy_inventory import CopyInventoryContext
from sketch2life.domain.ai_policy.model import PolicyError
from tests.ai_policy_copy_inventory_fixtures import (
    COVERAGE,
    PROFILE,
    SOURCE,
    context,
    read_request,
    registration,
    setup,
)
from tests.unit.test_ai_policy_domain import NOW


def register(service, **changes):
    return service.register("operator", "school", context(), registration(**changes), SOURCE)


def page(service, **changes):
    return service.page("operator", "school", read_request(**changes))


def coverage(service, revision=0):
    return service.coverage(
        "operator", "school", context(), expected_revision=revision, reference=COVERAGE
    )


def invoke(service, action):
    if action == "register":
        return register(service)
    if action == "read":
        return page(service)
    if action == "coverage":
        return coverage(service)
    return service.fence("operator", "school", context())


def test_register_authenticates_original_source_and_confirms_owner_through_commit():
    service, boundary, store = setup()
    result = register(service)
    assert result.registration.original_profile_ref == PROFILE
    assert not result.initial_copy().actual_deletion_proven
    assert store.commits == 1 and not boundary.held
    assert [call[3] for call in boundary.auth_calls] == [False, True]
    assert len(boundary.sources) == 1


def test_exact_registration_replay_rechecks_current_source_without_duplicate_audit():
    service, boundary, store = setup()
    first = register(service)
    assert register(service) == first
    assert len(boundary.sources) == 2 and page(service).revision == 1
    assert len(store.scopes["school", "scope"]["events"]) == 1
    boundary.allowed.remove("register")
    with pytest.raises(PolicyError, match="AI_POLICY_FORBIDDEN"):
        register(service)


def test_fence_replay_and_late_registration_remain_inventory_not_dispatch():
    service, boundary, _ = setup()
    register(service)
    revision = service.fence("operator", "school", context())
    assert service.fence("operator", "school", context()) == revision
    assert register(service, copy_id="late").initially_quarantined
    assert page(service).scope_purging
    boundary.allowed.remove("fence")
    with pytest.raises(PolicyError, match="AI_POLICY_FORBIDDEN"):
        service.fence("operator", "school", context())


def test_coverage_only_comes_from_backend_proof_and_is_invalidated_by_new_copy():
    service, boundary, _ = setup()
    register(service)
    assert coverage(service, 1) == 2
    reported = page(service)
    assert reported.coverage_status == "reported_complete"
    assert reported.coverage.attestation_ref == COVERAGE
    assert not reported.records[0].initial_copy().actual_deletion_proven
    register(service, copy_id="late")
    assert page(service).coverage_status == "unknown"
    assert boundary.sources[1][0] == "coverage"


def test_typed_keyset_page_rechecks_owner_and_stale_revision_fails():
    service, boundary, _ = setup()
    register(service, copy_id="a")
    register(service, copy_id="b")
    first = page(service, limit=1)
    assert first.next_after == "a"
    second = page(service, limit=1, after=first.next_after, expected_revision=first.revision)
    assert second.records[0].registration.copy_id == "b"
    register(service, copy_id="c")
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_REGISTRY_STALE"):
        page(service, limit=1, after=first.next_after, expected_revision=first.revision)
    boundary.allowed.remove("read")
    with pytest.raises(PolicyError, match="AI_POLICY_FORBIDDEN"):
        page(service)


@pytest.mark.parametrize("action", ["register", "read", "coverage", "fence"])
def test_each_action_requires_independent_current_authority(action):
    service, boundary, store = setup()
    boundary.allowed.remove(action)
    with pytest.raises(PolicyError, match="AI_POLICY_FORBIDDEN"):
        invoke(service, action)
    assert not store.scopes and not store.commits


@pytest.mark.parametrize(
    "change",
    [
        {"principal_id": "different"},
        {"organization_id": "different"},
        {"command_digest": "f" * 64},
        {"allowed": 1},
        {"authority_revision": True},
    ],
)
def test_identity_digest_or_native_grant_mismatch_denied_before_storage(change):
    service, boundary, store = setup()
    boundary.grant_changes = change
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_AUTHORITY_MISMATCH"):
        register(service)
    assert not store.scopes


@pytest.mark.parametrize("action", ["register", "read", "coverage", "fence"])
@pytest.mark.parametrize(
    "change,code",
    [
        ({"allowed": False}, "AI_POLICY_FORBIDDEN"),
        ({"authority_revision": "changed"}, "AI_POLICY_COPY_AUTHORITY_MISMATCH"),
        ({"expires_at": NOW}, "AI_POLICY_COPY_AUTHORITY_EXPIRED"),
    ],
)
def test_owner_changed_or_expired_before_commit_rolls_back(action, change, code):
    service, boundary, store = setup()
    boundary.confirm_changes = change
    with pytest.raises(PolicyError, match=code):
        invoke(service, action)
    assert not store.scopes and store.commits == 0


@pytest.mark.parametrize(
    "change,code",
    [
        ({"binding_digest": "f" * 64}, "AI_POLICY_COPY_SOURCE_MISMATCH"),
        (
            {"reference": SOURCE.model_copy(update={"hash": "f" * 64})},
            "AI_POLICY_COPY_SOURCE_MISMATCH",
        ),
        ({"verified": 1}, "AI_POLICY_COPY_SOURCE_MISMATCH"),
        ({"verified": False}, "AI_POLICY_COPY_SOURCE_UNVERIFIED"),
        ({"expires_at": NOW}, "AI_POLICY_COPY_SOURCE_EXPIRED"),
    ],
)
def test_registration_rejects_wrong_unverified_or_expired_source(change, code):
    service, boundary, store = setup()
    boundary.source_changes = change
    with pytest.raises(PolicyError, match=code):
        register(service)
    assert not store.scopes


@pytest.mark.parametrize(
    "change",
    [
        {"organization_id": "other"},
        {"scope_ref": "other"},
        {"expected_revision": 1},
        {"expected_revision": True},
        {"attestation_ref": SOURCE},
        {"required_sources": ("duplicate", "duplicate")},
    ],
)
def test_coverage_output_cannot_substitute_scope_revision_attestation_or_source_set(change):
    service, boundary, store = setup()
    boundary.observation_changes = change
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_SOURCE_MISMATCH"):
        coverage(service)
    assert not store.scopes


@pytest.mark.parametrize(
    "change,code",
    [
        ({"verified": 1}, "AI_POLICY_COPY_SOURCE_MISMATCH"),
        ({"verified": False}, "AI_POLICY_COPY_SOURCE_UNVERIFIED"),
        ({"expires_at": NOW}, "AI_POLICY_COPY_SOURCE_EXPIRED"),
    ],
)
def test_coverage_requires_current_strict_source_proof(change, code):
    service, boundary, store = setup()
    boundary.coverage_changes = change
    with pytest.raises(PolicyError, match=code):
        coverage(service)
    assert not store.scopes


def test_expired_source_at_precommit_check_rolls_back_new_registration():
    service, boundary, store = setup()
    # Entry grant, source, final grant, final source deadline.
    ticks = iter((NOW, NOW, NOW, NOW + timedelta(minutes=31)))
    service.clock = lambda: next(ticks)
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_SOURCE_EXPIRED"):
        register(service)
    assert not store.scopes and len(boundary.auth_calls) == 2


@pytest.mark.parametrize("change", [{"organization_id": "other"}, {"scope_ref": "other"}])
def test_cross_scope_registration_rejected_before_owner_or_source_calls(change):
    service, boundary, store = setup()
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_SCOPE_MISMATCH"):
        register(service, **change)
    assert not boundary.auth_calls and not boundary.sources and not store.scopes


@pytest.mark.parametrize("action", ["register", "fence", "coverage"])
def test_commit_failure_rolls_back_inventory_audit_coverage_fence(action):
    service, _, store = setup()
    store.fail_commit = True
    with pytest.raises(PolicyError, match="SYNTHETIC_INVENTORY_COMMIT_FAILURE"):
        invoke(service, action)
    assert not store.scopes


@pytest.mark.parametrize("action", ["register", "coverage"])
def test_private_source_error_is_sanitized(action):
    service, boundary, store = setup()
    boundary.fail_source = True
    with pytest.raises(PolicyError, match="^AI_POLICY_COPY_DEPENDENCY_UNAVAILABLE$"):
        invoke(service, action)
    assert not store.scopes


def test_guard_exit_error_after_commit_does_not_fabricate_rollback_or_duplicate():
    service, boundary, store = setup()
    boundary.fail_exit = True
    with pytest.raises(PolicyError, match="^AI_POLICY_COPY_DEPENDENCY_UNAVAILABLE$"):
        register(service)
    assert store.scopes["school", "scope"]["revision"] == 1
    boundary.fail_exit = False
    register(service)
    assert page(service).revision == 1


@pytest.mark.parametrize("extra", ["verified", "allowed", "observed_sources"])
def test_client_context_cannot_supply_authority_or_coverage_assertions(extra):
    with pytest.raises(ValidationError):
        CopyInventoryContext.model_validate(context().model_dump(mode="python") | {extra: True})


def test_bad_native_request_and_cursor_fail_before_authority():
    service, boundary, store = setup()
    bad = read_request().model_copy(update={"limit": True})
    with pytest.raises(PolicyError, match="AI_POLICY_INVALID_COPY_REGISTRY_REQUEST"):
        service.page("operator", "school", bad)
    with pytest.raises(PolicyError, match="AI_POLICY_INVALID_COPY_REGISTRY_REQUEST"):
        service.page("operator", "school", read_request().model_copy(update={"after": "copy"}))
    with pytest.raises(PolicyError, match="AI_POLICY_INVALID_COPY_REGISTRY_REQUEST"):
        service.coverage(
            "operator", "school", context(), expected_revision=True, reference=COVERAGE
        )
    assert not boundary.auth_calls and not store.scopes


def test_expired_owner_grant_denies_before_source_or_storage():
    service, boundary, store = setup()
    boundary.grant_changes = {"expires_at": NOW}
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_AUTHORITY_EXPIRED"):
        register(service)
    assert not boundary.sources and not store.scopes


def test_stale_verified_coverage_cannot_overwrite_newer_inventory():
    service, _, store = setup()
    register(service)
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_REGISTRY_STALE"):
        coverage(service, 0)
    assert page(service).coverage_status == "unknown"
    assert store.scopes["school", "scope"]["revision"] == 1


def test_full_operation_binding_changes_with_target_or_data_request_provenance():
    service, boundary, _ = setup()
    register(service)
    original = boundary.sources[-1][-1]
    register(service, copy_id="another")
    assert boundary.sources[-1][-1] != original
    changed_context = context(data_request_ref=PROFILE.model_copy(update={"version": 2}))
    service.register("operator", "school", changed_context, registration(), SOURCE)
    assert boundary.sources[-1][-1] != original
