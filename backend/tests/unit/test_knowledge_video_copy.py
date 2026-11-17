"""Explicit MEMORY/ASSUMED guards/synthetic control, not actual copy lifecycle proof."""

from contextlib import contextmanager
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from sketch2life.application.ai_policy_commands import _digest
from sketch2life.application.knowledge_video_copy import VideoProviderCopyHook, video_copy_entry
from sketch2life.application.knowledge_video_media import media_operation_key
from sketch2life.contracts.schemas.ai_policy_copy import CopyReceiptReference
from sketch2life.contracts.schemas.ai_policy_copy_delivery import CopyHookResponse
from sketch2life.contracts.schemas.knowledge_video_copy import VideoCopyJournalEntry
from sketch2life.domain.ai_policy.copy_delivery import DeliveryStatus
from sketch2life.domain.knowledge_video.model import ExactRef, VideoError
from tests.ai_policy_copy_dispatch_fixtures import dispatch, setup
from tests.unit.test_knowledge_video_worker import harness


def entry(attempt=None, **changes):
    return video_copy_entry(
        attempt or harness().attempt,
        **dict(
            scope_ref="scope",
            original_provider_profile=ExactRef("fixture-profile", 1, "a" * 64),
            copy_id="copy",
            role="script",
            source_reference=CopyReceiptReference(ref="fixture-source", hash="b" * 64),
        )
        | changes,
    )


class AssumedVideoBoundary:
    """Fixture checks are NOT adopted authority/source/claim verification."""

    def __init__(self, original):
        self.record = original
        self.held = False
        self.fail_original = self.fail_exit = False
        self.fail_confirm = None
        self.confirmations = []

    @contextmanager
    def guard(self, envelope):
        self.held = True
        try:
            yield self
            if self.fail_exit:
                raise RuntimeError("synthetic-private-guard-exit")
        finally:
            self.held = False

    def original(self, envelope):
        assert self.held
        if self.fail_original:
            raise RuntimeError("synthetic-private-source")
        return self.record

    def confirm(self, envelope, original):
        assert self.held
        self.confirmations.append((envelope, original))
        if len(self.confirmations) == self.fail_confirm:
            raise RuntimeError("synthetic-current-authority-denied")


def hook_setup(operation="purge"):
    dispatcher, _, _, store, envelope = setup(operation)
    boundary = AssumedVideoBoundary(entry())
    control = Mock()
    control.dispatch.return_value = CopyHookResponse(
        operation_key=envelope.operation_key,
        binding_digest=envelope.binding_digest,
        outcome="pending",
        reason_code="FIXTURE_PENDING",
    )
    hook = VideoProviderCopyHook(boundary, control=control)
    dispatcher.hook = hook
    return SimpleNamespace(
        dispatcher=dispatcher,
        store=store,
        envelope=envelope,
        boundary=boundary,
        control=control,
        hook=hook,
    )


@pytest.mark.parametrize("role", ["input", "script", "output", "cache", "job"])
def test_original_copy_mapping_includes_script_without_new_shared_kind(role):
    attempt = harness().attempt
    record = entry(attempt, role=role)
    assert record.registration.kind == ("input" if role == "script" else role)
    assert record.pin_digest == attempt.run.pin.digest()
    assert record.media_operation_key == media_operation_key(attempt)
    assert record.registration.scope_ref != attempt.run.pin.session_id
    assert record.registration.original_profile_ref.ref == "fixture-profile"
    assert record.registration.original_profile_ref.ref != attempt.run.pin.model_profile.ref
    assert not hasattr(record, "actual_deletion_proven")
    assert attempt.capability not in repr(record)


def test_original_key_stable_across_progress_but_not_attempt_or_policy_generation():
    attempt = harness().attempt
    first = entry(attempt)
    assert entry(replace(attempt, job_revision=50)) == first
    other_attempt = replace(attempt, run=replace(attempt.run, attempt_id="next"))
    other_epoch = replace(
        attempt, run=replace(attempt.run, pin=replace(attempt.run.pin, policy_epoch=2))
    )
    assert entry(other_attempt).media_operation_key != first.media_operation_key
    assert entry(other_epoch).media_operation_key != first.media_operation_key


@pytest.mark.parametrize(
    "changes",
    [
        dict(scope_ref="https://not-a-scope"),
        dict(copy_id="https://private-copy"),
        dict(role="unknown"),
        dict(original_provider_profile=None),
        dict(source_reference=CopyReceiptReference.model_construct(ref="secret/url", hash="bad")),
    ],
)
def test_invalid_metadata_fails_closed_without_raw_diagnostics(changes):
    with pytest.raises(VideoError, match="^VIDEO_COPY_INVALID_SOURCE$"):
        entry(**changes)


def test_native_boolean_version_and_forged_nested_profile_rejected():
    attempt = harness().attempt
    forged = replace(attempt.run)
    object.__setattr__(forged, "video_version", True)
    with pytest.raises(VideoError, match="VIDEO_COPY_INVALID_SOURCE"):
        entry(replace(attempt, run=forged))
    record = entry()
    bad_profile = record.registration.original_profile_ref.model_copy(update={"version": True})
    forged = record.model_copy(
        update={
            "registration": record.registration.model_copy(
                update={"original_profile_ref": bad_profile}
            )
        }
    )
    with pytest.raises(ValidationError):
        VideoCopyJournalEntry.model_validate(forged.model_dump(mode="python"), strict=True)


@pytest.mark.parametrize("operation", ["cancel", "purge"])
def test_composes_with14_dispatcher_after_claim_outside_db_and_no_deletion_claim(operation):
    h = hook_setup(operation)
    seen = []

    def control(envelope, original):
        assert h.boundary.held
        assert not h.dispatcher.boundary.inventory.in_transaction
        scope = h.store.scopes["school", "scope"]
        assert scope["deliveries"][envelope.operation_key].status is DeliveryStatus.IN_FLIGHT
        seen.append((envelope, original))
        return h.control.dispatch.return_value

    h.control.dispatch.side_effect = control
    result = dispatch(h.dispatcher, h.envelope)
    assert result.status is DeliveryStatus.PENDING
    assert seen == [(h.envelope, h.boundary.record)]
    assert seen[0][0].command.operation == operation
    assert len(h.boundary.confirmations) == 2
    assert not h.boundary.held and not hasattr(result, "actual_deletion_proven")


def test_missing_control_explicit_unsupported_after_original_and_current_guard():
    h = hook_setup()
    h.hook = VideoProviderCopyHook(h.boundary, control=None)
    response = h.hook.dispatch(h.envelope)
    assert response.outcome == "unsupported"
    assert response.reason_code == "VIDEO_COPY_CONTROL_UNAVAILABLE"
    assert len(h.boundary.confirmations) == 1
    h.control.dispatch.assert_not_called()


@pytest.mark.parametrize(
    "name,value",
    [
        ("organization_id", "foreign"),
        ("scope_ref", "foreign"),
        ("copy_id", "foreign"),
        ("kind", "output"),
    ],
)
def test_foreign_original_never_dispatched(name, value):
    h = hook_setup()
    original = h.boundary.record
    h.boundary.record = original.model_copy(
        update={
            "registration": original.registration.model_copy(update={name: value}),
            "role": "output" if name == "kind" else original.role,
        }
    )
    assert h.hook.dispatch(h.envelope).outcome == "exception"
    h.control.dispatch.assert_not_called()


def test_latest_profile_alias_cannot_replace_original_version_hash():
    h = hook_setup()
    original = h.boundary.record
    profile = original.registration.original_profile_ref.model_copy(update={"version": 2})
    h.boundary.record = original.model_copy(
        update={
            "registration": original.registration.model_copy(
                update={"original_profile_ref": profile}
            )
        }
    )
    assert h.hook.dispatch(h.envelope).reason_code == "VIDEO_COPY_ORIGINAL_MISMATCH"
    h.control.dispatch.assert_not_called()


@pytest.mark.parametrize("field", ["operation_key", "binding_digest"])
def test_forged_envelope_rejected_before_boundary_or_control(field):
    h = hook_setup()
    bad = h.envelope.model_copy(update={field: "f" * 64})
    with pytest.raises(VideoError, match="^VIDEO_COPY_INVALID_OPERATION$"):
        h.hook.dispatch(bad)
    assert not h.boundary.confirmations
    h.control.dispatch.assert_not_called()


@pytest.mark.parametrize("phase", [1, 2])
def test_current_denial_before_effect_or_after_effect_stays_truthful(phase):
    h = hook_setup()
    h.boundary.fail_confirm = phase
    result = h.hook.dispatch(h.envelope)
    assert result.outcome == ("exception" if phase == 1 else "pending")
    assert h.control.dispatch.call_count == phase - 1
    assert result.reference is None


@pytest.mark.parametrize("error", [TimeoutError, RuntimeError])
def test_lost_ack_or_provider_error_no_retry_fallback_raw_diagnostic_or_fake_rollback(error):
    h = hook_setup()
    h.control.dispatch.side_effect = error("private-provider-token")
    result = h.hook.dispatch(h.envelope)
    assert result.outcome == "pending" and result.reason_code == "VIDEO_COPY_EFFECT_UNKNOWN"
    assert "private-provider-token" not in repr(result)
    h.control.dispatch.assert_called_once_with(h.envelope, h.boundary.record)


@pytest.mark.parametrize(
    "changes",
    [
        dict(operation_key="f" * 64),
        dict(binding_digest="f" * 64),
        dict(outcome="deleted"),
        dict(outcome="cancelled"),
        dict(reason_code="raw/private"),
    ],
)
def test_malformed_control_response_never_cancellation_or_deletion_proof(changes):
    h = hook_setup()
    h.control.dispatch.return_value = h.control.dispatch.return_value.model_copy(update=changes)
    result = h.hook.dispatch(h.envelope)
    assert result.outcome == "pending" and result.reference is None
    assert result.reason_code in {"VIDEO_COPY_RESPONSE_UNVERIFIED", "VIDEO_COPY_EFFECT_UNKNOWN"}
    assert h.control.dispatch.call_count == 1


def test_receipt_available_passes_reference_only_to14_for_separate_verification():
    h = hook_setup()
    response = CopyHookResponse(
        operation_key=h.envelope.operation_key,
        binding_digest=h.envelope.binding_digest,
        outcome="receipt_available",
        reference=CopyReceiptReference(ref="receipt", hash="c" * 64),
    )
    h.control.dispatch.return_value = response
    result = dispatch(h.dispatcher, h.envelope)
    assert result.status is DeliveryStatus.RECEIPT_AVAILABLE
    assert result.last_response.reference == "receipt"
    assert not hasattr(result, "actual_deletion_proven")


def test_recovery_reuses_exact_original_key_body_without_hook_retry_loop():
    h = hook_setup()
    h.control.dispatch.side_effect = TimeoutError("synthetic lost ACK")
    assert h.hook.dispatch(h.envelope).outcome == "pending"
    h.control.dispatch.side_effect = None
    assert h.hook.dispatch(h.envelope).outcome == "pending"
    assert h.control.dispatch.call_args_list[0] == h.control.dispatch.call_args_list[1]
    # External durable dedup and current authorized14 retry remain adopter duties.


@pytest.mark.parametrize("failure", ["fail_original", "fail_exit"])
def test_source_or_guard_exit_outage_never_claims_completed_effect(failure):
    h = hook_setup()
    setattr(h.boundary, failure, True)
    result = h.hook.dispatch(h.envelope)
    assert result.outcome == ("exception" if failure == "fail_original" else "pending")
    assert h.control.dispatch.call_count == (0 if failure == "fail_original" else 1)


def test_copy_entry_has_no_coverage_claim_and_strict_extra_fields():
    original = entry()
    assert not hasattr(original, "coverage_status")
    with pytest.raises(ValidationError):
        VideoCopyJournalEntry.model_validate(original.model_dump() | {"verified": True})


@pytest.mark.parametrize("operation", ["cancel", "purge"])
@pytest.mark.parametrize("role", ["input", "script", "output", "cache", "job"])
def test_hook_routes_each_exact_copy_kind_and_action_with_original_profile(role, operation):
    h = hook_setup(operation)
    original = entry(role=role)
    envelope = h.envelope.model_copy(update={"target": original.registration})
    digest, key = _digest(envelope.binding()), _digest(envelope.key_binding())
    envelope = envelope.model_copy(
        update={
            "binding_digest": digest,
            "operation_key": key,
            "initial_authority": envelope.initial_authority.model_copy(
                update={"command_digest": digest}
            ),
        }
    )
    h.boundary.record = original
    h.control.dispatch.return_value = CopyHookResponse(
        operation_key=key, binding_digest=digest, outcome="pending", reason_code="FIXTURE_PENDING"
    )
    result = h.hook.dispatch(envelope)
    assert result.outcome == "pending" and result.operation_key == key
    h.control.dispatch.assert_called_once_with(envelope, original)


def test_native_original_with_extra_field_or_wrong_role_never_reaches_control():
    h = hook_setup()
    h.boundary.record = h.boundary.record.model_copy(update={"role": "output"})
    result = h.hook.dispatch(h.envelope)
    assert result.outcome == "exception"
    h.control.dispatch.assert_not_called()


def test_source_reference_is_not_self_authenticated_by_model_or_initial_authority():
    h = hook_setup()
    assert h.envelope.initial_authority.allowed is True
    h.boundary.fail_original = True
    result = h.hook.dispatch(h.envelope)
    assert result.outcome == "exception" and result.reference is None
    h.control.dispatch.assert_not_called()
