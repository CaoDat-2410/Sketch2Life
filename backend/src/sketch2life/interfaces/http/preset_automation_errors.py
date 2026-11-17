"""Safe preset branch errors for the existing CMD-48 transport only."""

from sketch2life.domain.preset_automation.model import PresetError

GROUPS = {
    403: {"FORBIDDEN", "SCOPE_DENIED", "REVOKED", "SEPARATION_REQUIRED"},
    404: {"NOT_FOUND"},
    409: {
        "STALE_REVISION",
        "STALE_TARGET",
        "IDEMPOTENCY_CONFLICT",
        "TRANSITION_DENIED",
        "RECEIPT_CONFLICT",
        "SOURCE_UNAVAILABLE",
        "STALE_CONTEXT",
    },
    422: {
        "INVALID_BODY",
        "INVALID_RULES",
        "INVALID_REVIEW",
        "INVALID_PUBLICATION",
        "INVALID_EDIT",
        "DUPLICATE_REVIEW",
        "REASON_REQUIRED",
        "UNSUPPORTED_RULE",
    },
    428: {"PRECONDITION_REQUIRED"},
    400: {"UNEXPECTED_PRECONDITION"},
    503: {"POLICY_UNAVAILABLE", "REVIEW_UNAVAILABLE", "STORAGE_CORRUPT"},
}


def preset_command_error(error: PresetError) -> tuple[int, str]:
    for status, codes in GROUPS.items():
        if str(error) in {"PRESET_" + code for code in codes}:
            return status, str(error)
    return 503, "PRESET_DEPENDENCY_UNAVAILABLE"
