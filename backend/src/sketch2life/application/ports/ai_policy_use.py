"""Candidate current-use guard; owner must verify request/purpose/phase, not role inference."""

from contextlib import AbstractContextManager
from typing import Protocol

from sketch2life.application.ports.ai_policy_registry import PolicyCommandAccess
from sketch2life.contracts.schemas.ai_policy_use import (
    PolicyUseDecision,
    PolicyUsePhase,
    PolicyUsePin,
    PolicyUseRequest,
)


class PolicyUseAccess(PolicyCommandAccess, Protocol):
    def decide_use(
        self,
        request: PolicyUseRequest,
        pin: PolicyUsePin,
        phase: PolicyUsePhase,
        binding_digest: str,
    ) -> PolicyUseDecision:
        """Authoritative CURRENT exact request and phase decision under held fence.

        Verify identity/organization/feature and request id/revision/input/purpose,
        source expiry/current consent/grants/session/request terminal state, selected
        profile and appropriate mandatory reviews. Initial proposed request need
        not already exist remotely; later phases must match its stored pin. Echo
        exact digest ONLY after authorizing these facts, never caller allowed=true.
        Reject unknown/revoked/expired facts. Actual budget reservation and worker/
        provider execution authorization remain separate, not implied by this port.
        """
        ...


class PolicyUseBoundary(Protocol):
    def guard(
        self, principal_id: str, organization_id: str
    ) -> AbstractContextManager[PolicyUseAccess]:
        """Hold current use/review/registry eligibility through enclosing consumer commit.

        Real durable owner adapter/composition needed; no permissive default here.
        Snapshot return alone is not proof of revocation fencing or all-system use.
        """
        ...
