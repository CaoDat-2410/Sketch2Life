"""Explicit AI-policy owner binding into the existing sole CMD-48 dispatcher."""

from sketch2life.application.ai_policy_commands import AiPolicyCommands
from sketch2life.application.governance_dispatcher import StrictDelegateBinding
from sketch2life.contracts.schemas.ai_policy import AiPolicyCommand


def bind_ai_policy(service: AiPolicyCommands) -> StrictDelegateBinding[AiPolicyCommand]:
    """Caller must supply real store/authority/registry; no default app activation."""
    return StrictDelegateBinding(AiPolicyCommand, service)
