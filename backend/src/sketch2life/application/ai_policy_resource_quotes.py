"""Exact quote binding for future ledger service; no reservation or numeric defaults here."""

from dataclasses import dataclass

from pydantic import TypeAdapter, ValidationError

from sketch2life.application.ai_policy_commands import _digest
from sketch2life.contracts.schemas.ai_contract_candidates import OpaqueId
from sketch2life.contracts.schemas.ai_policy_accounting import ResourceQuote
from sketch2life.contracts.schemas.ai_policy_use import PolicyUseObservation
from sketch2life.domain.ai_policy.accounting import BudgetKey, DefinitionKey, LimitTerms
from sketch2life.domain.ai_policy.model import PolicyError

_IDENTIFIER = TypeAdapter(OpaqueId)


@dataclass(frozen=True, slots=True)
class BoundResourceQuote:
    quote_id: str
    request_digest: str
    attempt_id: str
    terms: LimitTerms
    estimated_units: int


def resource_binding_digest(
    principal_id: str, organization_id: str, observation: PolicyUseObservation, attempt_id: str
) -> str:
    return _digest(
        dict(
            operation="resource_reserve",
            principal_id=principal_id,
            organization_id=organization_id,
            observation=observation.model_dump(mode="json"),
            attempt_id=attempt_id,
        )
    )


def bind_resource_quote(
    principal_id: str,
    organization_id: str,
    observation: PolicyUseObservation,
    attempt_id: str,
    quote: ResourceQuote,
) -> BoundResourceQuote:
    """Caller must retain current-use AND trusted accounting quote guards to ledger commit."""
    try:
        for value in (principal_id, organization_id, attempt_id):
            _IDENTIFIER.validate_python(value, strict=True)
        observation = PolicyUseObservation.model_validate(
            observation.model_dump(mode="python"), strict=True
        )
        quote = ResourceQuote.model_validate(quote.model_dump(mode="python"), strict=True)
    except (ValueError, TypeError, AttributeError, ValidationError):
        raise PolicyError("AI_POLICY_RESOURCE_QUOTE_MISMATCH") from None
    if (
        observation.pin.organization_id != organization_id
        or quote.observation != observation
        or quote.attempt_id != attempt_id
        or quote.binding_digest
        != resource_binding_digest(principal_id, organization_id, observation, attempt_id)
    ):
        raise PolicyError("AI_POLICY_RESOURCE_QUOTE_MISMATCH")
    budget = observation.required_budget_ref
    concurrency = observation.required_concurrency_ref
    terms = LimitTerms(
        BudgetKey(
            organization_id,
            observation.pin.request.feature_scope,
            DefinitionKey(budget.ref, budget.version, budget.hash),
            quote.unit,
            quote.window_id,
        ),
        DefinitionKey(concurrency.ref, concurrency.version, concurrency.hash),
        quote.budget_ceiling,
        quote.concurrency_ceiling,
    )
    # Stable original request/policy provenance, NOT current phase/epoch/actor:
    # rechecking a current lease must not silently turn one attempt into two holds.
    request_digest = _digest(observation.pin.model_dump(mode="json"))
    return BoundResourceQuote(
        quote.quote_id, request_digest, attempt_id, terms, quote.estimated_units
    )
