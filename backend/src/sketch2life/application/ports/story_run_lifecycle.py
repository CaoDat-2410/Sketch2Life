"""Story-owned lifecycle port for the FR-C-08 Parent StoryRun purge (DTR Draft 6 §4-§6).

The module holds the deterministic identifiers of DTR rule 6, the public run-state sets of
Contract Draft 11 §3 and the two Story ports the BE1 lifecycle consumer calls: the Story
lifecycle port (plan, purge content, finalize, state) and ``RunAssetReferencePort`` (port design
§5.2). Nothing here touches a framework, a database or object storage.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Final, Protocol
from uuid import UUID, uuid5

from sketch2life.application.ports.core_foundation import LifecycleScope

LIFECYCLE_NS: Final = UUID("3f6c1a52-9d4e-5b70-8c21-7a5e0b9d4f13")

CANCEL_EVENT_TYPE: Final = "StoryRunCancellationRequestedV1"
DELETE_EVENT_TYPE: Final = "StoryRunDeletedV1"
LIFECYCLE_EVENT_TYPES: Final = frozenset({CANCEL_EVENT_TYPE, DELETE_EVENT_TYPE})

AUDIT_CANCEL_ACCEPTED: Final = "lifecycle.cancel_accepted"
AUDIT_DELETE_ACCEPTED: Final = "lifecycle.delete_accepted"
AUDIT_COMPLETED: Final = "lifecycle.completed"
AUDIT_EXCEPTION: Final = "lifecycle.exception"
LIFECYCLE_WORKER_ACTOR: Final = "be1-lifecycle-worker"
AUDIT_RESOURCE_TYPE: Final = "story_run"

# SRS line 394: the 18 public StoryRun states, plus the two documented extensions that the
# frozen M2 contract stores (D-216 item 4).
SRS_RUN_STATES: Final = (
    "DRAFT",
    "INPUT_PROCESSING",
    "INPUT_REVIEW",
    "SUBJECT_REVIEW",
    "PREPARATION_REVIEW",
    "STORY_GENERATING",
    "SCRIPT_REVIEW",
    "VIDEO_ADMISSION_PENDING",
    "VIDEO_QUEUED",
    "VIDEO_GENERATING",
    "VIDEO_SAFETY_VALIDATING",
    "VIDEO_READY",
    "SAFETY_BLOCKED",
    "COMPLETED",
    "FAILED",
    "ABANDONED",
    "DELETE_PENDING",
    "DELETED",
)
EXTENSION_RUN_STATES: Final = ("SCRIPT_GENERATING", "SCRIPT_GENERATION_UNKNOWN")
PUBLIC_RUN_STATES: Final = SRS_RUN_STATES + EXTENSION_RUN_STATES

PURGE_STATES: Final = frozenset({"DELETE_PENDING", "DELETED"})
# SRS line 1518: cancel is allowed unless the run is COMPLETED, FAILED, ABANDONED,
# DELETE_PENDING or DELETED (13 SRS states plus the two extensions).
CANCEL_ELIGIBLE_STATES: Final = frozenset(
    state
    for state in PUBLIC_RUN_STATES
    if state not in {"COMPLETED", "FAILED", "ABANDONED", "DELETE_PENDING", "DELETED"}
)
# D-214 item 1: a user DELETE is allowed for COMPLETED, FAILED and ABANDONED.
DELETE_ELIGIBLE_STATES: Final = frozenset({"COMPLETED", "FAILED", "ABANDONED"})

PROJECTION_FIELDS: Final = frozenset(
    {"run_id", "run_state", "revision", "version", "lifecycle_request_ref", "purge_state"}
)

STORY_STEP: Final = "story"


class StoryLifecycleError(RuntimeError):
    """Typed Story lifecycle failure; only the code is ever logged (port design §8)."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _uuid5(name: str) -> str:
    return str(uuid5(LIFECYCLE_NS, name))


def lifecycle_request_id(run_id: str) -> str:
    """``request_id = UUIDv5(NS, 'story_run:' || run_id)`` (DTR rule 6)."""

    return _uuid5("story_run:" + run_id)


def lifecycle_event_id(request_id: str, event_type: str) -> str:
    return _uuid5(request_id + ":" + event_type)


def lifecycle_audit_id(request_id: str, action: str) -> str:
    """Request-keyed audit id for the accepted and completed actions."""

    return _uuid5(request_id + ":" + action)


def lifecycle_exception_audit_id(processed_event_id: str) -> str:
    """Event-keyed audit id for ``lifecycle.exception`` (a re-open has a new event id)."""

    return _uuid5(processed_event_id + ":" + AUDIT_EXCEPTION)


def lifecycle_target_ref(run_id: str) -> str:
    return "story_run:" + run_id


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def lifecycle_projection_body(
    *, run_id: str, run_state: str, revision: int, version: int
) -> dict[str, Any]:
    """The content-free projection of DTR §6.5 / Contract §3.4, as stored and returned."""

    if run_state not in PURGE_STATES:
        raise ValueError("a lifecycle projection exists only from DELETE_PENDING on")
    return {
        "run_id": run_id,
        "run_state": run_state,
        "revision": int(revision),
        "version": int(version),
        "lifecycle_request_ref": lifecycle_request_id(run_id),
        "purge_state": "COMPLETED" if run_state == "DELETED" else "PENDING",
    }


def is_projection_body(body: object) -> bool:
    """DTR §6.5 predicate: the key set equals the projection field set, no ``story_run``."""

    return isinstance(body, dict) and set(body) == PROJECTION_FIELDS and "story_run" not in body


@dataclass(frozen=True, slots=True)
class StoryPurgePlan:
    """Story step plan (DTR T2): sorted ``table:pk``, ``receipt:<id>`` and ``run:<id>`` ids."""

    run_ref: str
    ids: tuple[str, ...]

    @property
    def empty(self) -> bool:
        return not self.ids


class StoryLifecyclePort(Protocol):
    """Story-owned purge operations (DTR §5.8); every call is scoped to one run."""

    def lifecycle_state(self, run_ref: str) -> str | None: ...

    def plan_story_purge(self, run_ref: str) -> StoryPurgePlan: ...

    def purge_story_content(self, plan: StoryPurgePlan) -> None:
        """One Story transaction (DTR step 4); raises when the plan no longer matches."""
        ...

    def finalize_deleted(self, run_ref: str, request_id: str) -> bool:
        """``DELETED``, revision/version +1, aggregate revision, ``lifecycle.completed``.

        Idempotent on the run id: a run already ``DELETED`` returns ``False``.
        """
        ...


class RunAssetReferencePort(Protocol):
    def assets_referenced_by_other_runs(
        self, scope: LifecycleScope, run_ref: str, asset_refs: frozenset[str]
    ) -> frozenset[str]: ...


__all__ = [
    "AUDIT_CANCEL_ACCEPTED",
    "AUDIT_COMPLETED",
    "AUDIT_DELETE_ACCEPTED",
    "AUDIT_EXCEPTION",
    "AUDIT_RESOURCE_TYPE",
    "CANCEL_ELIGIBLE_STATES",
    "CANCEL_EVENT_TYPE",
    "DELETE_ELIGIBLE_STATES",
    "DELETE_EVENT_TYPE",
    "EXTENSION_RUN_STATES",
    "LIFECYCLE_EVENT_TYPES",
    "LIFECYCLE_NS",
    "LIFECYCLE_WORKER_ACTOR",
    "PROJECTION_FIELDS",
    "PUBLIC_RUN_STATES",
    "PURGE_STATES",
    "RunAssetReferencePort",
    "SRS_RUN_STATES",
    "STORY_STEP",
    "StoryLifecycleError",
    "StoryLifecyclePort",
    "StoryPurgePlan",
    "canonical_json",
    "is_projection_body",
    "lifecycle_audit_id",
    "lifecycle_event_id",
    "lifecycle_exception_audit_id",
    "lifecycle_projection_body",
    "lifecycle_request_id",
    "lifecycle_target_ref",
    "sha256_hex",
]
