"""Synthetic backend quote/evidence shape; not adopted numeric definitions or actual costs."""

from dataclasses import replace

import pytest
from pydantic import ValidationError

from sketch2life.application.ai_policy_resource_quotes import (
    bind_resource_quote,
    resource_binding_digest,
)
from sketch2life.contracts.schemas.ai_policy import PolicyDefinitionRef
from sketch2life.contracts.schemas.ai_policy_accounting import (
    AccountingEvidenceRef,
    ResourceQuote,
    ResourceReservationRequest,
    ResourceSettlementRequest,
)
from sketch2life.contracts.schemas.ai_policy_use import PolicyUseObservation, PolicyUsePin
from sketch2life.domain.ai_policy.model import PolicyError
from tests.unit.test_ai_policy_use import request

REF = PolicyDefinitionRef(ref="fixture-definition", version=1, hash="a" * 64)


def observation():
    pin = PolicyUsePin(
        organization_id="school",
        request=request(),
        policy_ref=REF,
        activation_epoch=1,
        registry_revision="fixture-origin-registry",
    )
    return PolicyUseObservation(
        pin=pin,
        phase="dispatch",
        current_scope_epoch=1,
        current_registry_revision="fixture-registry",
        required_budget_ref=REF,
        required_concurrency_ref=REF,
        required_retry_ref=REF,
    )


def quote(**changes):
    observed = observation()
    return ResourceQuote.model_validate(
        dict(
            quote_id="fixture-quote",
            binding_digest=resource_binding_digest("worker", "school", observed, "attempt"),
            observation=observed,
            attempt_id="attempt",
            unit="fixture-units",
            window_id="fixture-window",
            budget_ceiling=10,
            concurrency_ceiling=2,
            estimated_units=4,
        )
        | changes
    )


def bind(
    value=None, *, observed=None, principal="worker", organization="school", attempt="attempt"
):
    return bind_resource_quote(
        principal,
        organization,
        observation() if observed is None else observed,
        attempt,
        quote() if value is None else value,
    )


def test_exact_trusted_quote_maps_to_original_terms_without_defaults():
    result = bind()
    assert result.terms.key.organization_id == "school"
    assert (
        result.terms.key.unit == "fixture-units" and result.terms.key.window_id == "fixture-window"
    )
    assert result.terms.budget_ceiling == 10 and result.estimated_units == 4
    assert result.terms.concurrency_ceiling == 2 and result.attempt_id == "attempt"
    assert result.terms.key.definition.hash == REF.hash


@pytest.mark.parametrize("field", ["budget_ceiling", "concurrency_ceiling", "estimated_units"])
@pytest.mark.parametrize("value", [True, -1, "10", 1.5])
def test_numeric_terms_strict_not_client_coercions(field, value):
    with pytest.raises(ValidationError):
        quote(**{field: value})


@pytest.mark.parametrize("field", ["unit", "window_id", "budget_ceiling", "estimated_units"])
def test_quote_requires_explicit_values_never_production_defaults(field):
    raw = quote().model_dump(mode="python")
    del raw[field]
    with pytest.raises(ValidationError):
        ResourceQuote.model_validate(raw)


@pytest.mark.parametrize(
    "field,value",
    [
        ("binding_digest", "b" * 64),
        ("attempt_id", "different-attempt"),
        ("observation", observation().model_copy(update={"current_scope_epoch": 2})),
    ],
)
def test_trusted_response_cannot_substitute_digest_attempt_or_held_snapshot(field, value):
    with pytest.raises(PolicyError, match="AI_POLICY_RESOURCE_QUOTE_MISMATCH"):
        bind(quote(**{field: value}))


@pytest.mark.parametrize(
    "kwargs",
    [
        {"principal": "other-worker"},
        {"organization": "other-school"},
        {"attempt": "other-attempt"},
    ],
)
def test_quote_cannot_replay_for_different_identity_scope_or_attempt(kwargs):
    with pytest.raises(PolicyError, match="AI_POLICY_RESOURCE_QUOTE_MISMATCH"):
        bind(**kwargs)


def test_native_constructed_boolean_quote_amount_rejected_before_ledger():
    malformed = quote().model_copy(update={"estimated_units": True})
    with pytest.raises(PolicyError, match="AI_POLICY_RESOURCE_QUOTE_MISMATCH"):
        bind(malformed)


def test_fresh_quote_after_scope_phase_registry_change_keeps_original_request_digest():
    old = bind()
    current = observation().model_copy(
        update={
            "current_scope_epoch": 2,
            "current_registry_revision": "fixture-registry.2",
            "phase": "retry",
        }
    )
    updated = quote(
        observation=current,
        binding_digest=resource_binding_digest("worker", "school", current, "attempt"),
    )
    assert bind(updated, observed=current).request_digest == old.request_digest
    with pytest.raises(PolicyError, match="AI_POLICY_RESOURCE_QUOTE_MISMATCH"):
        bind(quote(), observed=current)


@pytest.mark.parametrize("phase", ["completion", "exposure"])
def test_cannot_create_new_reservation_quote_in_final_exposure_phase(phase):
    with pytest.raises(ValidationError):
        quote(observation=observation().model_copy(update={"phase": phase}))


def test_reservation_request_exact_original_pin_and_no_numeric_override():
    pin = observation().pin
    values = dict(
        client_request_id="reserve",
        request=pin.request,
        pin=pin,
        attempt_id="attempt",
        phase="dispatch",
    )
    assert ResourceReservationRequest.model_validate(values).pin == pin
    with pytest.raises(ValidationError):
        ResourceReservationRequest.model_validate(values | {"estimated_units": 0})
    with pytest.raises(ValidationError):
        ResourceReservationRequest.model_validate(values | {"request": request(request_revision=2)})


@pytest.mark.parametrize("field", ["verified", "actual_units", "allowed", "unit", "window_id"])
def test_settlement_request_cannot_claim_proof_or_change_original_terms(field):
    value = dict(
        client_request_id="settle",
        reservation_id="reservation",
        operation="reconcile",
        evidence_ref=AccountingEvidenceRef(ref="fixture-evidence", hash="c" * 64),
    )
    assert ResourceSettlementRequest.model_validate(value).operation == "reconcile"
    with pytest.raises(ValidationError):
        ResourceSettlementRequest.model_validate(value | {field: "synthetic"})


def test_explicit_zero_ceiling_remains_zero_not_unlimited():
    result = bind(quote(budget_ceiling=0, concurrency_ceiling=0, estimated_units=0))
    assert replace(result.terms, budget_ceiling=0) == result.terms
