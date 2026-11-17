"""Closed command error projection; never return arbitrary dependency messages."""

from sketch2life.domain.ai_policy.model import PolicyError

_STATUS = {
    "AI_POLICY_FORBIDDEN": 403,
    "AI_POLICY_SEPARATION_REQUIRED": 403,
    "AI_POLICY_NOT_FOUND": 404,
    "AI_POLICY_PRECONDITION_REQUIRED": 428,
    "AI_POLICY_UNEXPECTED_PRECONDITION": 400,
    "AI_POLICY_INVALID_COMMAND": 422,
    "AI_POLICY_INVALID_BODY": 422,
    "AI_POLICY_INVALID_REVIEW": 422,
    "AI_POLICY_REASON_REQUIRED": 422,
    "AI_POLICY_STALE_REVISION": 409,
    "AI_POLICY_STALE_REVIEW": 409,
    "AI_POLICY_COMMAND_CONFLICT": 409,
    "AI_POLICY_WRITE_CONFLICT": 409,
    "AI_POLICY_SUPERSEDED_VERSION": 409,
    "AI_POLICY_HASH_MISMATCH": 409,
    "AI_POLICY_REVIEW_REQUIRED": 409,
    "AI_POLICY_REVIEW_MISMATCH": 409,
    "AI_POLICY_REVIEW_INEFFECTIVE": 409,
    "AI_POLICY_RECEIPT_INEFFECTIVE": 409,
    "AI_POLICY_TRANSITION_DENIED": 409,
    "AI_POLICY_FEATURE_CHANGE_DENIED": 409,
    "AI_POLICY_FEATURE_UNAVAILABLE": 409,
    "AI_POLICY_DEFINITION_UNAVAILABLE": 409,
    "AI_POLICY_REGISTRY_CHANGED": 409,
    "AI_POLICY_REGISTRY_UNAVAILABLE": 503,
    "AI_POLICY_DEPENDENCY_UNAVAILABLE": 503,
}


def policy_command_error(error: PolicyError) -> tuple[int, str]:
    code = str(error)
    if code not in _STATUS:
        # Scope/definition/time/storage mismatch may be an adapter defect. Never
        # leak internal metadata or invent a caller validation error from it.
        return 503, "AI_POLICY_DEPENDENCY_UNAVAILABLE"
    return _STATUS[code], code
