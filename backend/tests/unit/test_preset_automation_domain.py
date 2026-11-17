"""Pure candidate rules, not policy adoption or actual classroom evidence."""

from dataclasses import replace
from itertools import product

import pytest

from sketch2life.domain.preset_automation.model import (
    EffectReceipt,
    Intent,
    IntentState,
    PresetError,
    Review,
    Rule,
    Source,
    Stamp,
    State,
    matches,
)
from sketch2life.infrastructure.preset_automation.sql import validate_change
from tests.preset_automation_fixtures import NOW, body, library


def intent():
    return Intent(
        "intent",
        "school",
        "session",
        "teacher",
        1,
        "override",
        Source("preset", 1, body()),
        Stamp(1, 1, 1, 1),
        "assumed-policy",
        "set_tool_policy",
        "assumed-tools-v2",
        "Teacher change",
        NOW,
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("title", ""),
        ("tool_policy_ref", ""),
        ("canvas_mode", "<script>"),
        ("stage_rules", (Rule("x", "stage_is", "x", "notify_teacher"),) * 2),
        ("notification_rules", (Rule("x", "stage_is", "x", "notify_teacher"),) * 33),
    ],
)
def test_body_closed_limits(field, value):
    with pytest.raises(PresetError):
        body(**{field: value})


@pytest.mark.parametrize(
    "condition,expected,stage,help_pending,result",
    [
        ("stage_is", "drawing", "drawing", False, True),
        ("stage_is", "drawing", "reflection", True, False),
        ("help_pending", "yes", "drawing", True, True),
        ("help_pending", "no", "drawing", True, False),
    ],
)
def test_condition_semantics(condition, expected, stage, help_pending, result):
    assert (
        matches(
            Rule("rule", condition, expected, "notify_teacher"),
            stage=stage,
            help_pending=help_pending,
        )
        is result
    )


@pytest.mark.parametrize(
    "condition,action",
    [
        ("script", "notify_teacher"),
        ("stage_is", "approve_sketch"),
        ("stage_is", "complete_session"),
        ("stage_is", "purge"),
        ("stage_is", "play_unreviewed_video"),
    ],
)
def test_no_unsafe_registry(condition, action):
    with pytest.raises(PresetError):
        Rule("r", condition, "drawing", action)


@pytest.mark.parametrize("before,after", list(product(IntentState, repeat=2)))
def test_full_intent_state_matrix(before, after):
    row = replace(intent(), state=before)
    allowed = {
        "queued": {"sending", "stale", "cancelled", "deferred"},
        "deferred": {"sending", "stale", "cancelled"},
        "sending": {"applied", "stale", "rejected"},
    }
    if after.value in allowed.get(before.value, set()):
        result = row.transition(after, "assumed-reason")
        assert result.hash == row.hash and result.revision == row.revision + 1
        validate_change(row, result)
    else:
        with pytest.raises(PresetError):
            row.transition(after, "assumed-reason")


def test_library_edit_retains_old_published_version_and_reviews():
    before = library(True)
    after = before.change("edit", 1, 1, body().hash, "author", NOW, body=body(title="New"))
    assert after.versions[0] == before.versions[0]
    assert after.versions[1].state is State.DRAFT and not after.versions[1].reviews
    validate_change(before, after)
    recalled = after.change("recall", 2, 1, body().hash, "publisher", NOW, why="Unsafe")
    assert recalled.versions[0].state is State.RECALLED
    assert recalled.versions[1] == after.versions[1] and recalled.reason == "Unsafe"
    validate_change(after, recalled)


@pytest.mark.parametrize("mutation", ["revision", "organization", "author", "body", "state"])
def test_storage_rejects_impossible_change(mutation):
    before = library()
    after = before.change("submit_review", 1, 1, body().hash, "author", NOW)
    if mutation == "revision":
        after = replace(after, revision=8)
    elif mutation == "organization":
        after = replace(after, organization_id="other")
    else:
        v = after.versions[0]
        v = replace(
            v,
            **{"author": "intruder"}
            if mutation == "author"
            else {"body": body(title="Tamper")}
            if mutation == "body"
            else {"state": State.ARCHIVED},
        )
        after = replace(after, versions=(v,))
    with pytest.raises(PresetError):
        validate_change(before, after)


@pytest.mark.parametrize(
    "field,value",
    [
        ("session_id", "other"),
        ("intent_hash", "a" * 64),
        ("intent_id", "other"),
        ("organization_id", "other"),
        ("observed", Stamp(2, 1, 1, 1)),
        ("effective", Stamp(1, 1, 1, 1)),
    ],
)
def test_exact_receipt_identity_and_effective_config(field, value):
    row = intent()
    receipt = EffectReceipt(
        "intent",
        "school",
        "session",
        row.hash,
        "applied",
        row.observed,
        Stamp(1, 2, 1, 2),
        "native",
        "applied",
    )
    with pytest.raises(PresetError):
        replace(receipt, **{field: value}).validate_for(row)


@pytest.mark.parametrize("decision", ["reject", "request_changes"])
def test_review_reason_required(decision):
    with pytest.raises(PresetError):
        Review("r", "preset", 1, body().hash, "safety", "reviewer", "policy", decision)


@pytest.mark.parametrize("field", ["session", "config", "stage", "automation"])
def test_automation_native_receipt_must_not_regress_any_observed_axis(field):
    row = replace(intent(), kind="automation", action="notify_teacher", observed=Stamp(2, 2, 2, 2))
    receipt = EffectReceipt(
        row.intent_id,
        row.organization_id,
        row.session_id,
        row.hash,
        "applied",
        row.observed,
        replace(row.observed, **{field: 1}),
        "native",
        "applied",
    )
    with pytest.raises(PresetError, match="INVALID_RECEIPT"):
        receipt.validate_for(row)
