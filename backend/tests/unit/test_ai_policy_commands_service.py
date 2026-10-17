"""C3b application behavior using assumed guard/registry and MEMORY UoW only."""

from dataclasses import replace

import pytest

from sketch2life.domain.ai_policy.model import Capability, PolicyError
from tests.ai_policy_fixtures import (
    BODY,
    command,
    execute,
    harness,
    publish,
    published,
    reviewed,
    submitted,
)


def test_publish_activates_and_recall_disables_atomically_without_rewriting_history():
    service, boundary, store = harness()
    result = published(service, store)
    scope = store.scopes[("school", "fixture.feature")]
    assert (scope.epoch, scope.record_id, scope.version, scope.disabled) == (
        1, result.record.record_id, 1, False)
    retired = execute(service, "operator", "recall", "recall", result.record, reason="synthetic")
    assert retired.record.state == "recalled"
    assert store.scopes[("school", "fixture.feature")].disabled
    assert len(store.scope_events) == 2 and len(store.events) == 6
    assert len(store.proofs) == 2 and len(store.receipts) == 6
    assert not boundary.held and result.record.state == "published"


@pytest.mark.parametrize("action", ["create", "edit", "submit_review", "record_review",
                                    "publish", "recall", "archive"])
def test_duplicate_returns_recorded_result_without_second_effect(action):
    service, boundary, store = harness()
    actor, fields, record = "author", {}, None
    if action == "create":
        fields = {"policy": BODY}
    elif action in {"edit", "submit_review", "archive"}:
        record = execute(service, "author", "create", "seed", policy=BODY).record
        if action == "edit":
            fields = {"policy": BODY | {"title": "Synthetic edit"}}
        if action == "archive":
            actor, fields = "operator", {"reason": "synthetic"}
    elif action == "record_review":
        record = submitted(service).record
        item = store.load("school", record.record_id)
        actor, fields = "reviewer", {"review": dict(
            target_kind="ai_policy", target_id=item.record_id, target_version=item.version,
            target_hash=item.hash, context_revision=item.context_revision,
            expected_review_revision=item.review_revision, dimension="safety", decision="approve",
            review_policy_version="fixture.governance")}
    elif action == "publish":
        record = reviewed(service, store).record
        item = store.load("school", record.record_id)
        actor, fields = "publisher", {"review_ref": dict(
            safety_review_id=item.reviews[0].review_id,
            pedagogical_review_id=item.reviews[1].review_id,
            review_policy_version="fixture.governance")}
    else:
        record = published(service, store).record
        actor, fields = "operator", {"reason": "synthetic"}
    cmd = command(action, "duplicate", record, **fields)
    expected = None if record is None else record.revision
    first = service.execute(actor, "school", cmd, expected_revision=expected)
    counts = len(store.events), len(store.scope_events), len(store.receipts)
    second = service.execute(actor, "school", cmd, expected_revision=expected)
    assert second.replayed and second.record == first.record
    assert counts == (len(store.events), len(store.scope_events), len(store.receipts))
    assert not boundary.held


def test_changed_body_under_same_scoped_key_conflicts():
    service, _, store = harness()
    execute(service, "author", "create", "same", policy=BODY)
    with pytest.raises(PolicyError, match="AI_POLICY_COMMAND_CONFLICT"):
        execute(service, "author", "create", "same", policy=BODY | {"title": "different"})
    assert len(store.events) == 1


@pytest.mark.parametrize("principal,organization", [("unknown", "school"), ("author", "other")])
def test_unverified_or_cross_org_cannot_mutate(principal, organization):
    service, _, store = harness()
    with pytest.raises(PolicyError, match="AI_POLICY_FORBIDDEN"):
        service.execute(principal, organization, command("create", "key", policy=BODY))
    assert not store.events


def test_author_cannot_self_publish_even_with_all_caps():
    service, boundary, store = harness()
    record = reviewed(service, store).record
    boundary.rights["author"] = set(Capability)
    item = store.load("school", record.record_id)
    with pytest.raises(PolicyError, match="AI_POLICY_SEPARATION_REQUIRED"):
        execute(service, "author", "publish", "self-publish", record, review_ref=dict(
            safety_review_id=item.reviews[0].review_id,
            pedagogical_review_id=item.reviews[1].review_id,
            review_policy_version="fixture.governance"))
    assert not store.scope_events


@pytest.mark.parametrize("failure", ["fail_receipt", "fail_scope", "fail_commit"])
def test_failure_rolls_back_lifecycle_activation_receipt_and_intent(failure):
    service, _, store = harness()
    record = reviewed(service, store).record
    before = len(store.events), len(store.scope_events), len(store.receipts)
    setattr(store, failure, True)
    with pytest.raises(PolicyError, match="SYNTHETIC_"):
        publish(service, store, record, "failed-publish")
    assert before == (len(store.events), len(store.scope_events), len(store.receipts))
    assert store.load("school", record.record_id).state == "submitted"
    assert store.scopes[("school", "fixture.feature")].epoch == 0


def test_edit_makes_fresh_version_and_old_pin_is_not_rewritten():
    service, _, store = harness()
    old = published(service, store).record
    new = execute(service, "author", "edit", "edit", old,
                  policy=BODY | {"title": "new synthetic"}).record
    assert new.version == 2 and new.state == "draft"
    assert not store.load("school", new.record_id).reviews
    assert store.scopes[("school", "fixture.feature")].version == 1
    assert store.load("school", old.record_id, version=1).state == "published"


def test_retiring_prior_version_does_not_disable_new_effective_version():
    service, _, store = harness()
    old = published(service, store).record
    new = execute(service, "author", "edit", "new-edit", old, policy=BODY).record
    new = execute(service, "author", "submit_review", "new-submit", new)
    new = reviewed(service, store, "new", new)
    new = publish(service, store, new.record, "new-publish").record
    execute(service, "operator", "recall", "retire-old",
            old.model_copy(update={"revision": new.revision}), reason="synthetic")
    scope = store.scopes[("school", "fixture.feature")]
    assert scope.epoch == 2 and scope.version == 2 and not scope.disabled


def test_retirement_allowed_after_definition_withdrawal_but_publish_replay_denied():
    service, boundary, store = harness()
    old = published(service, store).record
    boundary.missing = "budget"
    retired = execute(service, "operator", "recall", "retire", old, reason="withdrawn")
    assert retired.record.state == "recalled"
    item = store.load("school", old.record_id, version=1)
    cmd = command("publish", "one-publish", old, review_ref=dict(
        safety_review_id=item.reviews[0].review_id, pedagogical_review_id=item.reviews[1].review_id,
        review_policy_version="fixture.governance"))
    with pytest.raises(PolicyError, match="AI_POLICY_RECEIPT_INEFFECTIVE"):
        service.execute("publisher", "school", cmd, expected_revision=4)
    assert store.scopes[("school", "fixture.feature")].disabled


@pytest.mark.parametrize("change", ["capability", "proof", "registry"])
def test_publish_replay_rechecks_current_decisions(change):
    service, boundary, store = harness()
    result = published(service, store)
    item = store.load("school", result.record.record_id)
    refs = dict(safety_review_id=item.reviews[0].review_id,
                pedagogical_review_id=item.reviews[1].review_id,
                review_policy_version="fixture.governance")
    if change == "capability":
        boundary.rights["publisher"] = set()
    elif change == "proof":
        boundary.revoked_proofs.add(item.reviews[0].review_id)
    else:
        boundary.missing = "model_profile"
    with pytest.raises(PolicyError):
        service.execute("publisher", "school", command("publish", "one-publish", result.record,
                                                        review_ref=refs), expected_revision=4)
    assert len(store.scope_events) == 1


def test_edit_cannot_move_record_to_different_effective_scope():
    service, _, store = harness()
    record = published(service, store).record
    with pytest.raises(PolicyError, match="AI_POLICY_FEATURE_CHANGE_DENIED"):
        execute(service, "author", "edit", "bad-edit", record,
                policy=BODY | {"feature_scope": "different-feature"})
    assert len(store.scopes) == 1 and store.load("school", record.record_id).version == 1


@pytest.mark.parametrize("expected", [None, True, 0, 999])
def test_missing_or_stale_record_precondition_denied(expected):
    service, _, store = harness()
    record = execute(service, "author", "create", "seed", policy=BODY).record
    with pytest.raises(PolicyError):
        service.execute("author", "school", command("submit_review", "bad", record),
                        expected_revision=expected)
    assert len(store.events) == 1


def test_negative_review_can_request_changes_with_withdrawn_definition_and_resubmit_fresh():
    service, boundary, store = harness()
    record = submitted(service).record
    item = store.load("school", record.record_id)
    boundary.missing = "model_profile"
    fields = dict(target_kind="ai_policy", target_id=item.record_id, target_version=item.version,
                  target_hash=item.hash, context_revision=item.context_revision,
                  expected_review_revision=item.review_revision, dimension="safety",
                  decision="request_changes", reason="synthetic change",
                  review_policy_version="fixture.governance")
    cmd = command("request_changes", "changes", record, review=fields, reason="synthetic change")
    result = service.execute("reviewer", "school", cmd, expected_revision=record.revision)
    assert result.record.state == "changes_requested"
    assert service.execute("reviewer", "school", cmd,
                           expected_revision=record.revision).replayed
    boundary.missing = None
    execute(service, "author", "submit_review", "resubmit", result.record)
    assert not store.load("school", record.record_id).reviews


def test_request_replay_cannot_use_another_scope_receipt():
    service, _, store = harness()
    execute(service, "author", "create", "key", policy=BODY)
    key = "school", "author", "key"
    store.receipts[key] = replace(store.receipts[key], organization_id="wrong-school")
    with pytest.raises(PolicyError, match="AI_POLICY_SCOPE_MISMATCH"):
        execute(service, "author", "create", "key", policy=BODY)


def test_service_can_bind_existing_cmd48_without_second_router():
    import json

    from sketch2life.application.governance_dispatcher import (
        GovernanceDispatcher,
        StrictDelegateBinding,
    )
    from sketch2life.application.learning_content_commands import ContentCommands
    from sketch2life.contracts.schemas.ai_policy import AiPolicyCommand
    from sketch2life.domain.learning_content.model import ContentError
    from tests.learning_content_fixtures import AssumedBoundary, ComponentStore

    service, _, store = harness()
    content_boundary = AssumedBoundary()
    dispatcher = GovernanceDispatcher(ContentCommands(
        ComponentStore(content_boundary), content_boundary),
                                       ai_policy=StrictDelegateBinding(AiPolicyCommand, service))
    raw = command("create", "bound-create", policy=BODY).model_dump_json().encode()
    result = dispatcher.execute_json("author", "school", raw)
    assert result.record.policy_kind == "ai" and len(store.events) == 1
    value = json.loads(raw)
    value["unexpected"] = True
    with pytest.raises(ContentError, match="INVALID_GOVERNANCE_COMMAND"):
        dispatcher.execute_json("author", "school", json.dumps(value).encode())
    assert len(store.events) == 1
