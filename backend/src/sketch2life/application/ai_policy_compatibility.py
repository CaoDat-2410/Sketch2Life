"""Fail-closed exact definition binding; validation observations are not usage grants."""

from dataclasses import dataclass

from pydantic import TypeAdapter, ValidationError

from sketch2life.application.ports.ai_policy_registry import (
    DefinitionBinding,
    DefinitionKind,
    PolicyRegistryAccess,
    PolicyRegistryBoundary,
)
from sketch2life.contracts.schemas.ai_contract_candidates import OpaqueId
from sketch2life.contracts.schemas.ai_policy import AiPolicyWrite, PolicyDefinitionRef
from sketch2life.domain.ai_policy.model import Capability, PolicyError, authorize

_IDENTIFIER = TypeAdapter(OpaqueId)


@dataclass(frozen=True, slots=True)
class PolicyCompatibilityResult:
    organization_id: str
    feature_scope: str
    registry_revision: str
    definitions: tuple[DefinitionBinding, ...]


def validated_policy_body(body: AiPolicyWrite) -> AiPolicyWrite:
    try:
        # Reject malformed instances made via construct/copy, not only raw JSON.
        return AiPolicyWrite.model_validate(body.model_dump(mode="python"), strict=True)
    except (ValidationError, ValueError, TypeError):
        raise PolicyError("AI_POLICY_INVALID_BODY") from None


def bind_definitions(body: AiPolicyWrite, organization_id: str,
                     access: PolicyRegistryAccess) -> PolicyCompatibilityResult:
    """Caller holds an entered current access guard, through any subsequent commit."""
    body = validated_policy_body(body)
    if access.authority.organization_id != organization_id:
        raise PolicyError("AI_POLICY_FORBIDDEN")
    try:
        revision = _IDENTIFIER.validate_python(access.registry_revision, strict=True)
        available = access.feature_available(body.feature_scope)
    except Exception:
        raise PolicyError("AI_POLICY_REGISTRY_UNAVAILABLE") from None
    if available is not True:
        raise PolicyError("AI_POLICY_FEATURE_UNAVAILABLE")
    references: tuple[tuple[DefinitionKind, PolicyDefinitionRef], ...] = (
        *(("model_profile", ref) for ref in body.model_profile_refs),
        ("moderation", body.moderation_policy_ref), ("retry", body.retry_policy_ref),
        ("budget", body.budget_policy_ref), ("concurrency", body.concurrency_policy_ref),
    )
    bindings: list[DefinitionBinding] = []
    for kind, reference in references:
        try:
            binding = access.resolve(body.feature_scope, kind, reference)
        except Exception:
            raise PolicyError("AI_POLICY_REGISTRY_UNAVAILABLE") from None
        if binding is None:
            raise PolicyError("AI_POLICY_DEFINITION_UNAVAILABLE")
        try:
            if not isinstance(binding, DefinitionBinding):
                raise ValueError("typed definition binding required")
            PolicyDefinitionRef.model_validate(binding.reference.model_dump(mode="python"),
                                                strict=True)
        except (ValidationError, ValueError, TypeError, AttributeError):
            raise PolicyError("AI_POLICY_DEFINITION_MISMATCH") from None
        if (not isinstance(binding, DefinitionBinding)
                or (binding.organization_id, binding.feature_scope, binding.kind,
                    binding.reference, binding.registry_revision) != (
                        organization_id, body.feature_scope, kind, reference, revision)):
            raise PolicyError("AI_POLICY_DEFINITION_MISMATCH")
        bindings.append(binding)
    # Do not accept a registry which changed its visible epoch mid-resolution.
    if access.registry_revision != revision:
        raise PolicyError("AI_POLICY_REGISTRY_CHANGED")
    return PolicyCompatibilityResult(organization_id, body.feature_scope, revision, tuple(bindings))


class PolicyCompatibility:
    """Read-only validation for authors; does not create/publish/activate any policy."""

    def __init__(self, boundary: PolicyRegistryBoundary) -> None:
        self.boundary = boundary

    def check(self, principal_id: str, organization_id: str,
              body: AiPolicyWrite) -> PolicyCompatibilityResult:
        try:
            context = self.boundary.guard(principal_id, organization_id)
            with context as access:
                if access.authority.principal_id != principal_id:
                    raise PolicyError("AI_POLICY_FORBIDDEN")
                authorize(access.authority, organization_id, Capability.AUTHOR)
                return bind_definitions(body, organization_id, access)
        except PolicyError:
            raise
        except Exception:
            raise PolicyError("AI_POLICY_REGISTRY_UNAVAILABLE") from None
