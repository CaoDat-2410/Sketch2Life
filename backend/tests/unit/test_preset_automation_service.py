"""Synthetic BE1 atomic comparison/dedup conformance and recoverable own records."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import pytest

from sketch2life.domain.preset_automation.model import IntentState, PresetError, Stamp
from tests.contract.test_preset_automation_governance import published
from tests.preset_automation_fixtures import body, command, environment, request


def prepare(env, kind="override", key="control"):
    return env[4].prepare("school", "session", "teacher", request(kind, key))


@pytest.mark.parametrize("kind", ["pin", "override", "disable"])
def test_intent_first_no_effect_until_verified_owner_receipt(kind):
    env = environment()
    if kind == "pin":
        published(env)
    row = prepare(env, kind)
    assert env[2].count == 0 and row.state is IntentState.QUEUED
    done = env[4].dispatch("school", "session", "teacher", row.intent_id)
    assert done.state is IntentState.APPLIED and env[2].count == 1
    assert env[1].view.observed == Stamp(1, 2, 1, 2)
    assert prepare(env, kind) == done
    assert env[4].dispatch("school", "session", "teacher", row.intent_id) == done
    assert env[2].count == 1


@pytest.mark.parametrize("outcome", ["queued", "deferred", "unsupported"])
def test_evaluate_bounded_queue_outcome_is_persisted_not_effect(outcome):
    env = environment()
    env[3].result = outcome
    decision = env[4].evaluate("school", "session", "teacher", "event", "stage-help")
    assert decision.outcome == outcome and env[2].count == 0
    assert env[4].evaluate("school", "session", "teacher", "event", "stage-help") == decision
    if decision.intent_id:
        row = env[0].data["school", "session", decision.intent_id]
        assert row.state.value == outcome


@pytest.mark.parametrize("mode,expected", [("disabled", "disabled"), ("unmatched", "not_matched")])
def test_no_implicit_scheduling_or_effect(mode, expected):
    env = environment()
    env[1].view = replace(
        env[1].view,
        automation_enabled=mode != "disabled",
        stage="reflection" if mode == "unmatched" else "drawing",
    )
    result = env[4].evaluate("school", "session", "teacher", "event", "stage-help")
    assert result.outcome == expected and result.intent_id is None and env[2].count == 0


@pytest.mark.parametrize("denied", ["source", "body", "rule", "intent", "evaluate"])
def test_unknown_policy_rights_or_mandatory_gate_fails_closed(denied):
    env = environment()
    env[1].denied.add(denied)
    with pytest.raises(PresetError):
        env[4].evaluate("school", "session", "teacher", "event", "stage-help")
    assert not env[0].data and env[2].count == 0


def test_unsupported_queue_value_not_silent_drop():
    env = environment()
    env[3].result = "autoapprove"
    with pytest.raises(PresetError, match="QUEUE"):
        env[4].evaluate("school", "session", "teacher", "event", "stage-help")
    assert not env[0].data


def test_override_stales_queued_automation_and_reconcile_does_not_send():
    env = environment()
    decision = env[4].evaluate("school", "session", "teacher", "event", "stage-help")
    manual = prepare(env)
    assert (
        env[4].reconcile("school", "session", "teacher", decision.intent_id).state
        is IntentState.QUEUED
    )
    assert env[2].count == 0
    env[4].dispatch("school", "session", "teacher", manual.intent_id)
    stale = env[4].reconcile("school", "session", "teacher", decision.intent_id)
    assert stale.state is IntentState.STALE and env[2].count == 1


def test_override_wins_at_fake_owner_effect_boundary_after_send_started():
    env = environment()
    decision = env[4].evaluate("school", "session", "teacher", "event", "stage-help")
    env[2].hook = lambda: setattr(env[1], "view", replace(env[1].view, observed=Stamp(1, 2, 1, 2)))
    result = env[4].dispatch("school", "session", "teacher", decision.intent_id)
    assert result.state is IntentState.STALE and env[2].count == 0


def test_timeout_after_effect_recovers_original_receipt_even_after_epoch_change():
    env = environment()
    row = prepare(env)
    env[2].timeout_after = True
    unknown = env[4].dispatch("school", "session", "teacher", row.intent_id)
    assert unknown.state is IntentState.SENDING and env[2].count == 1
    env[2].timeout_after = False
    recovered = env[4].dispatch("school", "session", "teacher", row.intent_id)
    assert recovered.state is IntentState.APPLIED and env[2].count == 1


def test_lost_ack_unknown_after_override_not_fabricated_cancelled():
    env = environment()
    row = prepare(env)
    env[2].timeout_before = True
    result = env[4].dispatch("school", "session", "teacher", row.intent_id)
    env[1].view = replace(env[1].view, observed=Stamp(1, 2, 1, 2))
    env[2].timeout_before = False
    assert env[4].dispatch("school", "session", "teacher", row.intent_id) == result
    assert env[4].reconcile("school", "session", "teacher", row.intent_id) == result
    assert result.state is IntentState.SENDING and env[2].count == 0


def test_failed_ack_write_recovers_without_second_effect():
    env = environment()
    row = prepare(env)
    env[0].fail_effect_write = True
    with pytest.raises(RuntimeError):
        env[4].dispatch("school", "session", "teacher", row.intent_id)
    assert env[0].data["school", "session", row.intent_id].state is IntentState.SENDING
    assert ("school", "session", "effect-" + row.intent_id) not in env[0].data
    env[0].fail_effect_write = False
    assert (
        env[4].dispatch("school", "session", "teacher", row.intent_id).state is IntentState.APPLIED
    )
    assert env[2].count == 1


def test_foreign_receipt_keeps_pending_then_native_recovery():
    env = environment()
    row = prepare(env)
    env[2].foreign = True
    assert (
        env[4].dispatch("school", "session", "teacher", row.intent_id).state is IntentState.SENDING
    )
    assert (
        env[4].dispatch("school", "session", "teacher", row.intent_id).state is IntentState.APPLIED
    )
    assert env[2].count == 1


@pytest.mark.parametrize("change", ["stage", "source", "disabled", "policy"])
def test_dispatch_revalidates_not_only_enqueue(change):
    env = environment()
    decision = env[4].evaluate("school", "session", "teacher", "event", "stage-help")
    if change == "stage":
        env[1].view = replace(env[1].view, stage="reflection")
    elif change == "source":
        env[1].recalled = True
    elif change == "disabled":
        env[1].view = replace(env[1].view, automation_enabled=False)
    else:
        env[1].view = replace(env[1].view, policy_ref="changed-policy")
    if change == "source":
        with pytest.raises(PresetError):
            env[4].dispatch("school", "session", "teacher", decision.intent_id)
    else:
        assert (
            env[4].dispatch("school", "session", "teacher", decision.intent_id).state
            is IntentState.STALE
        )
    assert env[2].count == 0


def test_pin_exact_published_version_recall_and_library_edit_independence():
    env = environment()
    lib = published(env)
    pin = prepare(env, "pin")
    env[-1].execute(
        "author",
        "school",
        command(
            "edit", record=lib, body=__import__("dataclasses").asdict(body(title="Changed library"))
        ),
        expected_revision=lib.revision,
    )
    assert (
        env[4].dispatch("school", "session", "teacher", pin.intent_id).state is IntentState.APPLIED
    )
    assert env[1].view.source.body.title == body().title
    env[1].recalled = True
    with pytest.raises(PresetError):
        env[4].prepare(
            "school", "session", "teacher", request("pin", "new-pin", env[1].view.observed)
        )


@pytest.mark.parametrize(
    "org,session,actor",
    [
        ("other", "session", "teacher"),
        ("school", "other", "teacher"),
        ("school", "session", "child"),
    ],
)
def test_wrong_scope_has_no_write(org, session, actor):
    env = environment()
    with pytest.raises(PresetError):
        env[4].prepare(org, session, actor, request())
    assert not env[0].data


def test_same_key_conflicting_body_and_bypass_value_denied():
    env = environment()
    prepare(env)
    with pytest.raises(PresetError, match="CONFLICT"):
        env[4].prepare("school", "session", "teacher", replace(request(), value="changed"))
    with pytest.raises(PresetError, match="POLICY"):
        env[4].prepare(
            "school", "session", "teacher", replace(request(key="bypass"), value="bypass-review")
        )


def test_duplicate_event_concurrent_own_enqueues_one_intent():
    env = environment()
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(
            executor.map(
                lambda _: env[4].evaluate(
                    "school", "session", "teacher", "same-event", "stage-help"
                ),
                range(2),
            )
        )
    assert results[0] == results[1]
    assert len(env[0].data) == 2 and env[2].count == 0


def test_existing_pin_receipt_replays_after_library_recall_without_new_pin():
    env = environment()
    current = published(env)
    original = prepare(env, "pin")
    env[-1].execute(
        "publisher",
        "school",
        command("recall", record=current, reason="Recall"),
        expected_revision=current.revision,
    )
    assert prepare(env, "pin") == original
    with pytest.raises(PresetError, match="SOURCE_UNAVAILABLE"):
        prepare(env, "pin", "new-key")


def test_native_historical_receipt_does_not_restore_newer_effective_config():
    env = environment()
    original = prepare(env)
    env[2].timeout_after = True
    assert (
        env[4].dispatch("school", "session", "teacher", original.intent_id).state
        is IntentState.SENDING
    )
    env[1].view = replace(env[1].view, observed=Stamp(1, 5, 1, 5), automation_enabled=False)
    before = env[1].view
    recovered = env[4].dispatch("school", "session", "teacher", original.intent_id)
    assert recovered.state is IntentState.APPLIED and env[1].view == before
    assert env[2].count == 1


def test_disable_makes_old_queued_action_stale_not_applied():
    env = environment()
    decision = env[4].evaluate("school", "session", "teacher", "event", "stage-help")
    disabled = prepare(env, "disable")
    env[4].dispatch("school", "session", "teacher", disabled.intent_id)
    assert not env[1].view.automation_enabled
    assert (
        env[4].dispatch("school", "session", "teacher", decision.intent_id).state
        is IntentState.STALE
    )
    assert env[2].count == 1


def test_revoked_current_authority_never_replays_terminal_as_allowed():
    env = environment()
    original = prepare(env)
    env[4].dispatch("school", "session", "teacher", original.intent_id)
    env[1].current = False
    with pytest.raises(PresetError, match="REVOKED"):
        env[4].dispatch("school", "session", "teacher", original.intent_id)


def test_native_reconciliation_resolves_stale_only_with_durable_owner_barrier():
    env = environment()
    original = prepare(env)
    env[2].timeout_before = True
    env[4].dispatch("school", "session", "teacher", original.intent_id)
    env[1].view = replace(env[1].view, observed=Stamp(1, 2, 1, 2))
    env[2].resolve_stale = True
    env[2].timeout_before = False
    result = env[4].reconcile("school", "session", "teacher", original.intent_id)
    assert result.state is IntentState.STALE and env[2].count == 0
    assert (
        env[0].data["school", "session", "effect-" + original.intent_id].receipt_ref
        == "native-fence-receipt"
    )


@pytest.mark.parametrize(
    "field,value", [("source", None), ("observed", Stamp(2, 1, 1, 1)), ("draft", False)]
)
def test_missing_pin_stale_context_or_non_draft_pin_denied(field, value):
    env = environment()
    if field == "draft":
        published(env)
    env[1].view = replace(env[1].view, **{field: value})
    with pytest.raises(PresetError):
        prepare(env, "pin" if field == "draft" else "override")
    assert env[2].count == 0
