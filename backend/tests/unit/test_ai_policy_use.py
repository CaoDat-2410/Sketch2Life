"""Current-use component with assumed authority and MEMORY UoW, not durable fences."""

from dataclasses import replace

import pytest
from pydantic import ValidationError

from sketch2life.application.ai_policy_commands import AiPolicyCommands
from sketch2life.application.ai_policy_control import AiPolicyEmergencyStop
from sketch2life.application.ai_policy_use import PolicyUseLeases
from sketch2life.contracts.schemas.ai_policy import PolicyDefinitionRef
from sketch2life.contracts.schemas.ai_policy_control import EmergencyStopCommand
from sketch2life.contracts.schemas.ai_policy_use import PolicyUseDecision, PolicyUseRequest
from sketch2life.domain.ai_policy.model import PolicyError
from tests.ai_policy_fixtures import AssumedCommandBoundary, MemoryPolicyStore, execute, published
from tests.contract.test_ai_policy_contracts import REF
from tests.unit.test_ai_policy_domain import NOW

PHASES = ("dispatch", "retry", "completion", "exposure")


class AssumedUseBoundary(AssumedCommandBoundary):
    def __init__(self):
        super().__init__()
        self.use_allowed = True
        self.decision_changes = {}
        self.use_calls = []
        self.fail_use = False

    def decide_use(self, request, pin, phase, digest):
        assert self.held
        self.use_calls.append((request, pin, phase, digest))
        if self.fail_use:
            raise RuntimeError("synthetic-private-owner-token")
        return PolicyUseDecision.model_construct(
            **(
                dict(
                    organization_id="school",
                    principal_id=self.authority.principal_id,
                    binding_digest=digest,
                    allowed=self.use_allowed,
                )
                | self.decision_changes
            )
        )


def request(**changes):
    return PolicyUseRequest.model_validate(
        dict(
            request_id="synthetic-request",
            request_revision=1,
            input_hash="b" * 64,
            purpose_code="classroom",
            feature_scope="fixture.feature",
            model_profile_ref=PolicyDefinitionRef(**REF),
        )
        | changes
    )


def setup(*, activate=True):
    boundary = AssumedUseBoundary()
    store = MemoryPolicyStore(boundary)
    service = AiPolicyCommands(store, boundary, clock=lambda: NOW)
    if activate:
        published(service, store)
    return PolicyUseLeases(store, boundary), service, boundary, store


def pin_once(leases):
    with leases.begin("worker", "school", request()) as observation:
        return observation.pin


def test_initial_pin_exact_provenance_guard_held_and_no_write_or_usage_grant():
    leases, _, boundary, store = setup()
    counts = len(store.events), len(store.scope_events), len(store.receipts)
    with leases.begin("worker", "school", request()) as observation:
        assert boundary.held
        assert observation.pin.activation_epoch == 1
        assert (
            observation.pin.policy_ref.ref == store.scopes[("school", "fixture.feature")].record_id
        )
        assert observation.pin.request.model_profile_ref.ref == REF["ref"]
        assert observation.required_budget_ref.hash == REF["hash"]
        assert observation.phase == "create" and observation.current_scope_epoch == 1
    assert not boundary.held
    assert counts == (len(store.events), len(store.scope_events), len(store.receipts))


@pytest.mark.parametrize("phase", PHASES)
def test_every_phase_rechecks_original_pin_and_current_owner(phase):
    leases, _, boundary, _ = setup()
    original = pin_once(leases)
    with leases.continue_use("worker", "school", request(), original, phase) as observation:
        assert observation.pin == original and observation.phase == phase
        assert boundary.held
    assert boundary.use_calls[-1][2] == phase and not boundary.held


@pytest.mark.parametrize("phase", PHASES)
def test_previous_pin_survives_ordinary_policy_replacement_without_repinning(phase):
    leases, service, _, store = setup()
    old = pin_once(leases)
    new = published(service, store, "replacement").record
    assert new.record_id != old.policy_ref.ref
    with leases.continue_use("worker", "school", request(), old, phase) as current:
        assert current.pin == old and current.current_scope_epoch == 2
    with leases.begin("worker", "school", request()) as fresh:
        assert fresh.pin.policy_ref.ref == new.record_id and fresh.pin.activation_epoch == 2


@pytest.mark.parametrize("phase", PHASES)
def test_any_intervening_stop_permanently_revokes_old_pin_even_after_reactivation(phase):
    leases, service, boundary, store = setup()
    old = pin_once(leases)
    AiPolicyEmergencyStop(store, boundary, clock=lambda: NOW).execute(
        "operator",
        "school",
        EmergencyStopCommand(
            client_request_id="stop",
            feature_scope="fixture.feature",
            expected_epoch=1,
            reason="synthetic emergency",
        ),
    )
    published(service, store, "after-stop")
    with (
        pytest.raises(PolicyError, match="AI_POLICY_PIN_REVOKED"),
        leases.continue_use("worker", "school", request(), old, phase),
    ):
        pytest.fail("old pre-stop pin cannot be used")
    with leases.begin("worker", "school", request()) as fresh:
        assert fresh.pin.activation_epoch == 3


@pytest.mark.parametrize("phase", PHASES)
def test_disabled_scope_denies_before_owner_approval(phase):
    leases, _, boundary, store = setup()
    original = pin_once(leases)
    AiPolicyEmergencyStop(store, boundary, clock=lambda: NOW).execute(
        "operator",
        "school",
        EmergencyStopCommand(
            client_request_id="stop",
            feature_scope="fixture.feature",
            expected_epoch=1,
            reason="synthetic emergency",
        ),
    )
    before = len(boundary.use_calls)
    with (
        pytest.raises(PolicyError, match="AI_POLICY_NOT_ELIGIBLE"),
        leases.continue_use("worker", "school", request(), original, phase),
    ):
        pytest.fail("disabled")
    assert len(boundary.use_calls) == before and not boundary.held


@pytest.mark.parametrize("phase", PHASES)
def test_current_consent_source_session_terminal_or_access_denial_fails_closed(phase):
    leases, _, boundary, _ = setup()
    pin = pin_once(leases)
    boundary.use_allowed = False
    with (
        pytest.raises(PolicyError, match="AI_POLICY_USE_DENIED"),
        leases.continue_use("worker", "school", request(), pin, phase),
    ):
        pytest.fail("owner denied")


@pytest.mark.parametrize(
    "changes",
    [
        {"organization_id": "wrong-school"},
        {"principal_id": "wrong-worker"},
        {"binding_digest": "0" * 64},
        {"allowed": 1},
    ],
)
def test_current_use_decision_must_match_exact_binding_and_actual_boolean(changes):
    leases, _, boundary, _ = setup()
    boundary.decision_changes = changes
    with (
        pytest.raises(PolicyError, match="AI_POLICY_USE_DECISION_MISMATCH"),
        leases.begin("worker", "school", request()),
    ):
        pytest.fail("invalid decision")


@pytest.mark.parametrize(
    "changes",
    [
        {"request_id": "other"},
        {"request_revision": 2},
        {"input_hash": "c" * 64},
        {"purpose_code": "other-purpose"},
    ],
)
def test_continuation_cannot_change_original_request_binding(changes):
    leases, _, _, _ = setup()
    pin = pin_once(leases)
    with (
        pytest.raises(PolicyError, match="AI_POLICY_PIN_MISMATCH"),
        leases.continue_use("worker", "school", request(**changes), pin, "dispatch"),
    ):
        pytest.fail("request substitution")


@pytest.mark.parametrize("kind", ["model_profile", "moderation", "retry", "budget", "concurrency"])
def test_current_definition_withdrawal_invalidates_use(kind):
    leases, _, boundary, _ = setup()
    original = pin_once(leases)
    boundary.missing = kind
    with (
        pytest.raises(PolicyError, match="AI_POLICY_DEFINITION_UNAVAILABLE"),
        leases.continue_use("worker", "school", request(), original, "exposure"),
    ):
        pytest.fail("revoked registry definition")


def test_no_effective_policy_denies_and_never_creates_scope():
    leases, _, _, store = setup(activate=False)
    with (
        pytest.raises(PolicyError, match="AI_POLICY_NOT_ELIGIBLE"),
        leases.begin("worker", "school", request()),
    ):
        pytest.fail("no pin")
    assert not store.scopes


@pytest.mark.parametrize("invalid", [None, 0, True])
def test_uninitialized_scope_epoch_never_authorizes(invalid):
    leases, _, _, store = setup()
    key = "school", "fixture.feature"
    store.scopes[key] = replace(store.scopes[key], epoch=invalid)
    with (
        pytest.raises(PolicyError, match="AI_POLICY_NOT_ELIGIBLE"),
        leases.begin("worker", "school", request()),
    ):
        pytest.fail("uninitialized scope")


def test_missing_selected_profile_no_automatic_provider_selection():
    leases, _, _, _ = setup()
    other = PolicyDefinitionRef(**(REF | {"ref": "not-in-policy"}))
    with (
        pytest.raises(PolicyError, match="AI_POLICY_PROFILE_DENIED"),
        leases.begin("worker", "school", request(model_profile_ref=other)),
    ):
        pytest.fail("do not auto-select a profile")


def test_old_policy_recall_denies_old_pin_without_disabling_replacement():
    leases, service, _, store = setup()
    old = pin_once(leases)
    new = published(service, store, "replacement").record
    original = store.load("school", old.policy_ref.ref, version=1)
    execute(
        service,
        "operator",
        "recall",
        "retire-old",
        new.model_copy(
            update=dict(
                record_id=original.record_id,
                version=original.version,
                hash=original.hash,
                revision=original.revision,
            )
        ),
        reason="synthetic",
    )
    with (
        pytest.raises(PolicyError, match="AI_POLICY_NOT_ELIGIBLE"),
        leases.continue_use("worker", "school", request(), old, "completion"),
    ):
        pytest.fail("retired old pin")
    assert not store.scopes[("school", "fixture.feature")].disabled


def test_reviewer_revocation_denies_current_use():
    leases, _, boundary, store = setup()
    pin = pin_once(leases)
    record = store.load("school", pin.policy_ref.ref)
    boundary.revoked_proofs.add(record.reviews[0].review_id)
    with (
        pytest.raises(PolicyError, match="AI_POLICY_REVIEW_INEFFECTIVE"),
        leases.continue_use("worker", "school", request(), pin, "retry"),
    ):
        pytest.fail("review revoked")


def test_callback_failure_releases_guard_without_exposing_sensitive_exception():
    leases, _, boundary, _ = setup()
    with (
        pytest.raises(PolicyError, match="^AI_POLICY_DEPENDENCY_UNAVAILABLE$"),
        leases.begin("worker", "school", request()),
    ):
        assert boundary.held
        raise RuntimeError("private callback token")
    assert not boundary.held


def test_owner_exception_is_safe_and_not_allowed():
    leases, _, boundary, _ = setup()
    boundary.fail_use = True
    with (
        pytest.raises(PolicyError, match="^AI_POLICY_DEPENDENCY_UNAVAILABLE$"),
        leases.begin("worker", "school", request()),
    ):
        pytest.fail("owner dependency failed")


def test_monitor_or_author_role_does_not_imply_runtime_use():
    leases, _, boundary, _ = setup()
    boundary.use_allowed = False
    for actor in ("author", "operator", "publisher"):
        with (
            pytest.raises(PolicyError, match="AI_POLICY_USE_DENIED"),
            leases.begin(actor, "school", request()),
        ):
            pytest.fail("no implicit role grant")


def test_native_invalid_pin_and_request_cannot_bypass_type_validation():
    leases, _, _, _ = setup()
    pin = pin_once(leases)
    malformed = request().model_copy(update={"request_revision": True})
    with (
        pytest.raises(PolicyError, match="AI_POLICY_INVALID_USE_REQUEST"),
        leases.continue_use("worker", "school", malformed, pin, "retry"),
    ):
        pytest.fail("boolean request revision")
    with (
        pytest.raises(PolicyError, match="AI_POLICY_INVALID_USE_REQUEST"),
        leases.continue_use(
            "worker",
            "school",
            request(),
            pin.model_copy(update={"activation_epoch": True}),
            "retry",
        ),
    ):
        pytest.fail("boolean epoch")


@pytest.mark.parametrize("phase", ["create", "unknown", "play"])
def test_continuation_does_not_allow_wrong_phase(phase):
    leases, _, _, _ = setup()
    pin = pin_once(leases)
    with (
        pytest.raises(PolicyError, match="AI_POLICY_INVALID_USE_"),
        leases.continue_use("worker", "school", request(), pin, phase),
    ):
        pytest.fail("wrong phase")


@pytest.mark.parametrize(
    "field,value",
    [("request_revision", True), ("input_hash", "bad"), ("organization_id", "client-spoof")],
)
def test_request_strict_schema(field, value):
    with pytest.raises(ValidationError):
        request(**{field: value})


def test_fake_later_epoch_cannot_resurrect_old_policy_after_stop():
    leases, service, boundary, store = setup()
    pin = pin_once(leases)
    AiPolicyEmergencyStop(store, boundary, clock=lambda: NOW).execute(
        "operator",
        "school",
        EmergencyStopCommand(
            client_request_id="stop",
            feature_scope="fixture.feature",
            expected_epoch=1,
            reason="synthetic emergency",
        ),
    )
    published(service, store, "replacement")
    spoofed = pin.model_copy(update={"activation_epoch": 3})
    with (
        pytest.raises(PolicyError, match="AI_POLICY_PIN_MISMATCH"),
        leases.continue_use("worker", "school", request(), spoofed, "exposure"),
    ):
        pytest.fail("old record was not activated at the replacement epoch")


def test_no_matching_activation_history_is_not_a_valid_scope_pin():
    leases, _, _, store = setup()
    store.scope_events.clear()
    with (
        pytest.raises(PolicyError, match="AI_POLICY_PIN_MISMATCH"),
        leases.begin("worker", "school", request()),
    ):
        pytest.fail("no activation proof")
