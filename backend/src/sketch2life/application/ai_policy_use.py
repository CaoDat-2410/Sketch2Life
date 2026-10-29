"""Held current-use leases; request pins preserve provenance but never cache permission."""

from collections.abc import Iterator
from contextlib import contextmanager

from pydantic import TypeAdapter, ValidationError

from sketch2life.application.ai_policy_commands import _body, _digest, _proofs_current
from sketch2life.application.ai_policy_compatibility import bind_definitions
from sketch2life.application.ports.ai_policy import EffectivePolicyScope, PolicyStore
from sketch2life.application.ports.ai_policy_use import PolicyUseAccess, PolicyUseBoundary
from sketch2life.contracts.schemas.ai_policy import PolicyDefinitionRef
from sketch2life.contracts.schemas.ai_policy_use import (
    PolicyUseDecision,
    PolicyUseObservation,
    PolicyUsePhase,
    PolicyUsePin,
    PolicyUseRequest,
)
from sketch2life.domain.ai_policy.model import PolicyError, PolicyVersion, State

_PHASE: TypeAdapter[PolicyUsePhase] = TypeAdapter(PolicyUsePhase)


def _published_proofs(record: PolicyVersion, access: PolicyUseAccess) -> None:
    ids = record.publication_review_ids
    if (
        record.state != State.PUBLISHED
        or len(ids) != 2
        or len(set(ids)) != 2
        or record.publication_policy_version != access.review_policy_version
    ):
        raise PolicyError("AI_POLICY_NOT_ELIGIBLE")
    _proofs_current(record, access)
    for dimension, review_id in zip(("safety", "pedagogical"), ids, strict=True):
        proof = next((item for item in record.reviews if item.dimension == dimension), None)
        if (
            proof is None
            or proof.decision != "approve"
            or proof.reviewer_id == record.authored_by
            or (
                proof.review_id,
                proof.target_id,
                proof.target_version,
                proof.target_hash,
                proof.context_revision,
            )
            != (review_id, record.record_id, record.version, record.hash, record.context_revision)
        ):
            raise PolicyError("AI_POLICY_REVIEW_INEFFECTIVE")


class PolicyUseLeases:
    def __init__(self, store: PolicyStore, boundary: PolicyUseBoundary) -> None:
        self.store, self.boundary = store, boundary

    @contextmanager
    def begin(
        self, principal_id: str, organization_id: str, request: PolicyUseRequest
    ) -> Iterator[PolicyUseObservation]:
        """Initial proposed request: persist returned pin in consumer's guarded commit."""
        with self._hold(principal_id, organization_id, request, "create", None) as observation:
            yield observation

    @contextmanager
    def continue_use(
        self,
        principal_id: str,
        organization_id: str,
        request: PolicyUseRequest,
        pin: PolicyUsePin,
        phase: PolicyUsePhase,
    ) -> Iterator[PolicyUseObservation]:
        """Recheck stored ORIGINAL request pin at dispatch/retry/completion/exposure."""
        if phase == "create":
            raise PolicyError("AI_POLICY_INVALID_USE_PHASE")
        with self._hold(principal_id, organization_id, request, phase, pin) as observation:
            yield observation

    @contextmanager
    def _hold(
        self,
        principal_id: str,
        organization_id: str,
        request: PolicyUseRequest,
        phase: PolicyUsePhase,
        pin: PolicyUsePin | None,
    ) -> Iterator[PolicyUseObservation]:
        try:
            request = PolicyUseRequest.model_validate(
                request.model_dump(mode="python"), strict=True
            )
            phase = _PHASE.validate_python(phase, strict=True)
            if pin is not None:
                pin = PolicyUsePin.model_validate(pin.model_dump(mode="python"), strict=True)
                if pin.organization_id != organization_id or pin.request != request:
                    raise PolicyError("AI_POLICY_PIN_MISMATCH")
        except (ValidationError, ValueError, TypeError) as error:
            if isinstance(error, PolicyError):
                raise
            raise PolicyError("AI_POLICY_INVALID_USE_REQUEST") from None
        try:
            with self.boundary.guard(principal_id, organization_id) as access:
                if (
                    access.authority.principal_id != principal_id
                    or access.authority.organization_id != organization_id
                ):
                    raise PolicyError("AI_POLICY_FORBIDDEN")
                with self.store.transaction() as tx:
                    scope = tx.effective_scope(organization_id, request.feature_scope)
                    if (
                        scope is None
                        or scope.disabled is not False
                        or type(scope.epoch) is not int
                        or scope.epoch < 1
                        or scope.record_id is None
                        or scope.version is None
                        or scope.hash is None
                    ):
                        raise PolicyError("AI_POLICY_NOT_ELIGIBLE")
                    if (scope.organization_id, scope.feature_scope) != (
                        organization_id,
                        request.feature_scope,
                    ):
                        raise PolicyError("AI_POLICY_SCOPE_MISMATCH")
                    target = (
                        PolicyDefinitionRef(
                            ref=scope.record_id, version=scope.version, hash=scope.hash
                        )
                        if pin is None
                        else pin.policy_ref
                    )
                    if pin is not None and (
                        pin.activation_epoch > scope.epoch
                        or tx.stopped_since(
                            organization_id, request.feature_scope, after_epoch=pin.activation_epoch
                        )
                        is not False
                    ):
                        raise PolicyError("AI_POLICY_PIN_REVOKED")
                    origin = EffectivePolicyScope(
                        organization_id,
                        request.feature_scope,
                        scope.epoch if pin is None else pin.activation_epoch,
                        target.ref,
                        target.version,
                        target.hash,
                        False,
                    )
                    if tx.was_activated(origin) is not True:
                        raise PolicyError("AI_POLICY_PIN_MISMATCH")
                    record = tx.load(organization_id, target.ref, version=target.version)
                    if record is None:
                        raise PolicyError("AI_POLICY_NOT_ELIGIBLE")
                    if (record.organization_id, record.record_id, record.version, record.hash) != (
                        organization_id,
                        target.ref,
                        target.version,
                        target.hash,
                    ):
                        raise PolicyError("AI_POLICY_PIN_MISMATCH")
                    body = _body(record)
                    if body.feature_scope != request.feature_scope:
                        raise PolicyError("AI_POLICY_PIN_MISMATCH")
                    _published_proofs(record, access)
                    compatibility = bind_definitions(body, organization_id, access)
                    if request.model_profile_ref not in body.model_profile_refs:
                        raise PolicyError("AI_POLICY_PROFILE_DENIED")
                    if pin is None:
                        pin = PolicyUsePin(
                            organization_id=organization_id,
                            request=request,
                            policy_ref=target,
                            activation_epoch=scope.epoch,
                            registry_revision=compatibility.registry_revision,
                        )
                    digest = _digest(
                        dict(
                            principal_id=principal_id,
                            organization_id=organization_id,
                            request=request.model_dump(mode="json"),
                            pin=pin.model_dump(mode="json"),
                            phase=phase,
                        )
                    )
                    raw_decision = access.decide_use(request, pin, phase, digest)
                    if not isinstance(raw_decision, PolicyUseDecision):
                        raise PolicyError("AI_POLICY_USE_DECISION_MISMATCH")
                    try:
                        decision = PolicyUseDecision.model_validate(
                            raw_decision.model_dump(mode="python"), strict=True
                        )
                    except (ValueError, TypeError):
                        raise PolicyError("AI_POLICY_USE_DECISION_MISMATCH") from None
                    if (
                        decision.organization_id,
                        decision.principal_id,
                        decision.binding_digest,
                    ) != (organization_id, principal_id, digest):
                        raise PolicyError("AI_POLICY_USE_DECISION_MISMATCH")
                    if decision.allowed is not True:
                        raise PolicyError("AI_POLICY_USE_DENIED")
                    yield PolicyUseObservation(
                        pin=pin,
                        phase=phase,
                        current_scope_epoch=scope.epoch,
                        current_registry_revision=compatibility.registry_revision,
                        required_budget_ref=body.budget_policy_ref,
                        required_concurrency_ref=body.concurrency_policy_ref,
                        required_retry_ref=body.retry_policy_ref,
                    )
                    # Scope SHARE and external owner guard remain held through
                    # caller's nested work/commit. Exiting doesn't create a grant.
        except PolicyError:
            raise
        except Exception:
            raise PolicyError("AI_POLICY_DEPENDENCY_UNAVAILABLE") from None
