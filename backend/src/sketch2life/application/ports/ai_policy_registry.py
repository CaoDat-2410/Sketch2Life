"""Candidate authoritative registry boundary, not a production adopted definition store."""

from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Literal, Protocol

from sketch2life.contracts.schemas.ai_policy import PolicyDefinitionRef
from sketch2life.domain.ai_policy.model import Authority, PolicyVersion, Review

DefinitionKind = Literal["model_profile", "moderation", "retry", "budget", "concurrency"]


@dataclass(frozen=True, slots=True)
class DefinitionBinding:
    organization_id: str
    feature_scope: str
    kind: DefinitionKind
    reference: PolicyDefinitionRef
    registry_revision: str


class PolicyRegistryAccess(Protocol):
    authority: Authority
    registry_revision: str

    def feature_available(self, feature_scope: str) -> bool: ...

    def resolve(self, feature_scope: str, kind: DefinitionKind,
                reference: PolicyDefinitionRef) -> DefinitionBinding | None:
        """Only CURRENT adopted/compatible definitions, exact scope/ref/revision.

        Implementer validates real approved units/windows/ceilings/retry semantics,
        required safety ceilings and backend profile compatibility before returning.
        Unknown/revoked/incompatible/expired means None, not raw config or fallback.
        No provider credentials/endpoints in the response. This is authoritative
        backend resolution, never an adapter trusting a caller's approved boolean.
        """
        ...


class PolicyRegistryBoundary(Protocol):
    def guard(self, principal_id: str,
              organization_id: str) -> AbstractContextManager[PolicyRegistryAccess]:
        """Verify identity/current org rights and hold registry/current-authority fence.

        Mutation callers must retain this guard through SQL commit/rollback. A
        snapshot/boolean or process lock does not prove durable revocation fencing.
        No real adapter supplied by the local component/fixture checkpoint.
        """
        ...


class PolicyCommandAccess(PolicyRegistryAccess, Protocol):
    review_policy_version: str

    def review_effective(self, policy: PolicyVersion, proof: Review) -> bool:
        """Current exact reviewer/policy/safety approval check, including proposed proof.

        Must support proofs just created in this transaction, not assume a separate
        remote review service already persisted them. Hold real decisions through
        commit. Unknown/revoked decisions are false; no permissive default adapter.
        """
        ...


class PolicyCommandBoundary(Protocol):
    def guard(self, principal_id: str,
              organization_id: str) -> AbstractContextManager[PolicyCommandAccess]: ...
