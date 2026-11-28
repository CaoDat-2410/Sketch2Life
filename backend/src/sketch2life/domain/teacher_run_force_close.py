"""Pure rules for a Manager's emergency close of a Teacher-owned StoryRun."""

from __future__ import annotations

import hashlib
import json
import unicodedata
from dataclasses import dataclass

FORCE_CLOSE_RUN_OPERATION = "FORCE_CLOSE_RUN"
FORCE_CLOSE_REQUEST_CONTRACT = "ManagerForceCloseStoryRunRequestV1"

FORCE_CLOSE_ELIGIBLE_STATES = frozenset(
    {
        "DRAFT",
        "INPUT_PROCESSING",
        "INPUT_REVIEW",
        "SUBJECT_REVIEW",
        "PREPARATION_REVIEW",
        "STORY_GENERATING",
        "SCRIPT_GENERATING",
        "SCRIPT_GENERATION_UNKNOWN",
        "SCRIPT_REVIEW",
        "VIDEO_ADMISSION_PENDING",
        "VIDEO_QUEUED",
        "VIDEO_GENERATING",
        "VIDEO_SAFETY_VALIDATING",
        "VIDEO_READY",
        "SAFETY_BLOCKED",
    }
)


@dataclass(frozen=True, slots=True)
class StoryRunForceCloseReceiptIdentity:
    idempotency_scope_ref: str
    idempotency_key_sha256: str
    request_fingerprint_sha256: str


@dataclass(frozen=True, slots=True)
class StoryRunForceCloseTransition:
    run_state: str
    revision: int
    version: int


class StoryRunForceCloseRuleError(ValueError):
    """A stable domain rejection without retaining the supplied reason."""

    def __init__(self, code: str, *, current_version: int | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.current_version = current_version


def normalize_force_close_reason(reason: str) -> str:
    if not isinstance(reason, str) or any(
        unicodedata.category(character) == "Cc" for character in reason
    ):
        raise StoryRunForceCloseRuleError("INVALID_REQUEST")
    normalized = reason.strip()
    if not 1 <= len(normalized) <= 500:
        raise StoryRunForceCloseRuleError("INVALID_REQUEST")
    return normalized


def build_force_close_receipt_identity(
    *,
    principal_ref: str,
    organization_id: str,
    run_id: str,
    expected_revision: int,
    reason: str,
    idempotency_key: str,
) -> StoryRunForceCloseReceiptIdentity:
    if (
        not principal_ref
        or not organization_id
        or not run_id
        or type(expected_revision) is not int
        or expected_revision < 1
        or not isinstance(idempotency_key, str)
        or not 1 <= len(idempotency_key) <= 128
        or any(ord(character) < 33 or ord(character) > 126 for character in idempotency_key)
    ):
        raise StoryRunForceCloseRuleError("INVALID_REQUEST")

    normalized_reason = normalize_force_close_reason(reason)
    scope_material = (
        b"story.teacher-run.force-close.scope.v1\0"
        + principal_ref.encode("utf-8")
        + b"\0"
        + run_id.encode("utf-8")
    )
    key_hash = hashlib.sha256(idempotency_key.encode("ascii")).hexdigest()
    fingerprint_material = json.dumps(
        {
            "contract": FORCE_CLOSE_REQUEST_CONTRACT,
            "expected_revision": expected_revision,
            "organization_id": organization_id,
            "principal_ref": principal_ref,
            "reason": normalized_reason,
            "run_id": run_id,
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    fingerprint = hashlib.sha256(
        b"story.teacher-run.force-close.request.v1\0" + fingerprint_material
    ).hexdigest()
    return StoryRunForceCloseReceiptIdentity(
        idempotency_scope_ref=hashlib.sha256(scope_material).hexdigest(),
        idempotency_key_sha256=key_hash,
        request_fingerprint_sha256=fingerprint,
    )


def force_close_transition(
    *,
    run_state: str,
    active_owner_teacher_id: str | None,
    expected_revision: int,
    current_revision: int,
    current_version: int,
) -> StoryRunForceCloseTransition:
    if (
        active_owner_teacher_id is None
        or run_state not in FORCE_CLOSE_ELIGIBLE_STATES
        or current_revision < 1
        or current_version < 1
    ):
        raise StoryRunForceCloseRuleError("INVALID_STATE_TRANSITION")
    if expected_revision != current_revision:
        raise StoryRunForceCloseRuleError(
            "STALE_REVISION", current_version=current_revision
        )
    return StoryRunForceCloseTransition(
        run_state="ABANDONED",
        revision=current_revision + 1,
        version=current_version + 1,
    )


__all__ = [
    "FORCE_CLOSE_ELIGIBLE_STATES",
    "FORCE_CLOSE_REQUEST_CONTRACT",
    "FORCE_CLOSE_RUN_OPERATION",
    "StoryRunForceCloseReceiptIdentity",
    "StoryRunForceCloseRuleError",
    "StoryRunForceCloseTransition",
    "build_force_close_receipt_identity",
    "force_close_transition",
    "normalize_force_close_reason",
]
