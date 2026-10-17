"""BE2-03 assistance request domain (DATA-21, A1 ASSISTANCE_COMPONENT_OFFLINE, 0.1-candidate).

A request is BE2-03's own aggregate: it pins resolved owner facts and one source, owns its
budget reservation and settlement, and is distinct from the BE2-01 job it schedules and the
BE2-02 analysis that job produces. Transitions are pure; ``request_revision`` moves only on
invalidating transitions (cancel, stale — D2) while ``record_version`` is the internal CAS
version of every change. Policy values are injected fixtures, never adopted production limits.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from hashlib import sha256
from typing import Any

from sketch2life.domain.ai_jobs.model import require_aware
from sketch2life.domain.core_foundation import CoreRuleViolation, validate_age_months
from sketch2life.domain.vision_analysis import AnalysisRuleViolation, normalize_long_text
from sketch2life.domain.vision_context import CONTEXT_AUDIENCE_MAX, strict_canonical_sha256

ASSISTANCE_CONTRACT_VERSION = "0.1-candidate"
CREATE_CONTRACT = "AssistanceRequestCreateV1"
CANCEL_CONTRACT = "AssistanceRequestCancelV1"
SEMANTIC_RULES_VERSION = "assistance-semantic-v1"
AUDIENCE_MAX = CONTEXT_AUDIENCE_MAX
FIXTURE_POLICY_STATUS = "FIXTURE_ONLY_NOT_ADOPTED"

_REF = re.compile(r"[A-Za-z0-9_.:-]{1,120}")
_SHA256 = re.compile(r"[0-9a-f]{64}")


class AssistanceRuleViolation(ValueError):
    """A domain invariant was violated; refused, never coerced."""


class RequestReason(StrEnum):
    """Closed DATA-21 enum. There is deliberately no inactivity/idle value (FR028)."""

    CHILD_REQUEST = "child_request"
    TEACHER_REQUEST = "teacher_request"
    EXPLICIT_HELP_SIGNAL = "explicit_help_signal"


class TargetKind(StrEnum):
    INDIVIDUAL = "individual"
    GROUP = "group"


class ActorKind(StrEnum):
    TEACHER = "teacher"
    DEVICE = "device"


class RequestStatus(StrEnum):
    SCHEDULING = "scheduling"
    SCHEDULED = "scheduled"
    ANALYSIS_READY = "analysis_ready"
    FAILED = "failed"
    CANCELLED = "cancelled"
    STALE = "stale"


NON_TERMINAL = frozenset({RequestStatus.SCHEDULING, RequestStatus.SCHEDULED})


class Settlement(StrEnum):
    OPEN = "open"
    SETTLED = "settled"


class ReservationState(StrEnum):
    HELD = "held"
    CONSUMED = "consumed"
    RELEASED = "released"


class StatusReason(StrEnum):
    CANCELLED_BY_TEACHER = "CANCELLED_BY_TEACHER"
    CANCELLED_BY_CHILD = "CANCELLED_BY_CHILD"
    CONTEXT_CHANGED = "CONTEXT_CHANGED"
    SOURCE_CHANGED = "SOURCE_CHANGED"
    SUPERSEDED_BY_FACT_CHANGE = "SUPERSEDED_BY_FACT_CHANGE"
    CONSENT_REVOKED = "CONSENT_REVOKED"
    SESSION_ENDED = "SESSION_ENDED"
    TURN_REVOKED = "TURN_REVOKED"
    CANVAS_RESTORED = "CANVAS_RESTORED"
    SCHEDULE_REFUSED = "SCHEDULE_REFUSED"
    JOB_FAILED = "JOB_FAILED"
    JOB_CANCELLED = "JOB_CANCELLED"
    ANALYSIS_REJECTED = "ANALYSIS_REJECTED"


class DeviceStatus(StrEnum):
    """Coarse Child-device projection: AI output is never implied available."""

    PENDING = "pending"
    CANCELLED = "cancelled"
    UNAVAILABLE = "unavailable"


def _ref(value: object, name: str) -> str:
    if not isinstance(value, str) or not _REF.fullmatch(value):
        raise AssistanceRuleViolation(f"{name} must be an opaque ref")
    return value


def _int(value: object, name: str, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise AssistanceRuleViolation(f"{name} must be an integer >= {minimum}")
    return value


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise AssistanceRuleViolation(f"{name} must be lowercase sha256 hex")
    return value


# --------------------------------------------------------------------------- values
@dataclass(frozen=True, slots=True)
class CheckpointRef:
    """DATA-21 ``checkpoint_ref``; ``hash`` is the JSON checkpoint checksum, never a render."""

    checkpoint_id: str
    document_epoch: int
    server_sequence: int
    hash: str

    def __post_init__(self) -> None:
        _ref(self.checkpoint_id, "checkpoint_id")
        _int(self.document_epoch, "document_epoch", 0)
        _int(self.server_sequence, "server_sequence", 0)
        _sha(self.hash, "checkpoint hash")

    def canonical(self) -> dict[str, object]:
        return {"checkpoint_id": self.checkpoint_id, "document_epoch": self.document_epoch,
                "server_sequence": self.server_sequence, "hash": self.hash}


@dataclass(frozen=True, slots=True)
class TargetScope:
    kind: TargetKind
    ref_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, TargetKind):
            raise AssistanceRuleViolation("target kind must be individual or group")
        _ref(self.ref_id, "target id")

    def key(self) -> str:
        return f"{self.kind}:{self.ref_id}"

    def canonical(self) -> dict[str, object]:
        return {"kind": str(self.kind), "id": self.ref_id}


@dataclass(frozen=True, slots=True)
class MemberFact:
    """One audience member's authoritative owner facts; age is never inferred."""

    participant_id: str
    completed_age_months: int | None
    age_provenance_ref: str
    age_revision: int
    consent_record_ref: str
    consent_revision: int
    consent_effective: bool
    purpose_granted: bool

    def canonical(self) -> dict[str, object]:
        return {
            "participant_id": self.participant_id,
            "completed_age_months": self.completed_age_months,
            "age_provenance_ref": self.age_provenance_ref,
            "age_revision": self.age_revision,
            "consent_record_ref": self.consent_record_ref,
            "consent_revision": self.consent_revision,
            "consent_effective": self.consent_effective,
            "purpose_granted": self.purpose_granted,
        }


@dataclass(frozen=True, slots=True)
class Contributor:
    participant_id: str
    turn_id: str | None
    turn_revision: int | None


@dataclass(frozen=True, slots=True)
class Requester:
    principal_id: str
    kind: ActorKind


@dataclass(frozen=True, slots=True)
class PolicySnapshot:
    """Consumer view of the BE2-14-owned policy (D10 proposal); values are fixtures."""

    policy_id: str
    version: str
    status: str
    assistance_enabled: bool
    allowed_levels: frozenset[str]
    debounce_seconds: int
    per_target_limit: int
    per_session_limit: int
    cache_enabled: bool
    purpose_code: str

    def __post_init__(self) -> None:
        _ref(self.policy_id, "policy_id")
        _ref(self.version, "policy version")
        _ref(self.purpose_code, "purpose_code")
        _int(self.debounce_seconds, "debounce_seconds", 0)
        _int(self.per_target_limit, "per_target_limit", 0)
        _int(self.per_session_limit, "per_session_limit", 0)

    def ref(self) -> dict[str, object]:
        return {"policy_id": self.policy_id, "version": self.version, "status": self.status}


@dataclass(frozen=True, slots=True)
class SourcePin:
    snapshot_ref: str
    checkpoint_id: str
    document_epoch: int
    server_sequence: int
    checkpoint_checksum: str
    render_ref: str
    render_sha256: str
    input_hash: str

    def canonical(self) -> dict[str, object]:
        return {
            "snapshot_ref": self.snapshot_ref,
            "checkpoint_id": self.checkpoint_id,
            "document_epoch": self.document_epoch,
            "server_sequence": self.server_sequence,
            "checkpoint_checksum": self.checkpoint_checksum,
            "render_ref": self.render_ref,
            "render_sha256": self.render_sha256,
            "input_hash": self.input_hash,
        }


@dataclass(frozen=True, slots=True)
class ResolvedFacts:
    """Everything BE2-03 checked for one request, as resolved from owner ports."""

    organization_id: str
    class_id: str
    session_id: str
    canvas_id: str
    group_id: str | None
    roster_revision: int | None
    target: TargetScope
    region_id: str | None
    region_policy_revision: int
    contributor_participant_id: str
    audience: tuple[str, ...]
    members: tuple[MemberFact, ...]
    purpose_code: str
    age_policy_ref: str
    policy_id: str
    policy_version: str
    context_revision: int
    source: SourcePin

    def digest(self) -> str:
        """``assistance_context_digest`` (TC-08): strict canonical binding of the facts."""

        return strict_canonical_sha256({
            "rules": SEMANTIC_RULES_VERSION,
            "organization_id": self.organization_id,
            "class_id": self.class_id,
            "session_id": self.session_id,
            "canvas_id": self.canvas_id,
            "group_id": self.group_id,
            "roster_revision": self.roster_revision,
            "target": self.target.canonical(),
            "region_id": self.region_id,
            "region_policy_revision": self.region_policy_revision,
            "contributor": self.contributor_participant_id,
            "members": [m.canonical() for m in sorted(self.members,
                                                      key=lambda m: m.participant_id)],
            "purpose_code": self.purpose_code,
            "age_policy_ref": self.age_policy_ref,
            "policy": {"policy_id": self.policy_id, "version": self.policy_version},
            "context_revision": self.context_revision,
            "source": self.source.canonical(),
        })


def reason_class(reason: RequestReason, requester: ActorKind) -> str:
    return "teacher" if requester is ActorKind.TEACHER else "device"


def semantic_identity(
    facts: ResolvedFacts,
    *,
    digest: str,
    checkpoint_ref: CheckpointRef,
    requested_level: str,
    requester: ActorKind,
    reason: RequestReason,
    child_intent: str | None,
) -> str:
    """TC-04: operation identities (ids, keys, principals, turns, times) are excluded."""

    intent = None if child_intent is None else sha256(child_intent.encode("utf-8")).hexdigest()
    return strict_canonical_sha256({
        "rules": SEMANTIC_RULES_VERSION,
        "organization_id": facts.organization_id,
        "session_id": facts.session_id,
        "canvas_id": facts.canvas_id,
        "target": facts.target.canonical(),
        "region_id": facts.region_id,
        "checkpoint_ref": checkpoint_ref.canonical(),
        "input_hash": facts.source.input_hash,
        "audience": sorted(facts.audience),
        "purpose_code": facts.purpose_code,
        "requested_level": requested_level,
        "reason_class": reason_class(reason, requester),
        "child_intent_sha256": intent,
        "context_revision": facts.context_revision,
        "policy": {"policy_id": facts.policy_id, "version": facts.policy_version},
        "assistance_context_digest": digest,
    })


def operation_target(canvas_id: str, target: TargetScope, region_id: str | None,
                     checkpoint_ref: CheckpointRef, requested_level: str) -> str:
    """Operation-level target used for fact-change supersession (§8.3)."""

    return strict_canonical_sha256({
        "canvas_id": canvas_id, "target": target.canonical(), "region_id": region_id,
        "checkpoint_ref": checkpoint_ref.canonical(), "requested_level": requested_level,
    })


def debounce_key(canvas_id: str, target: TargetScope) -> str:
    return f"{canvas_id}|{target.key()}"


def normalize_child_intent(value: str | None) -> str | None:
    if value is None:
        return None
    try:
        return normalize_long_text(value)
    except AnalysisRuleViolation as exc:
        raise AssistanceRuleViolation("child_intent must be bounded long text") from exc


def audience_refusal(audience: tuple[str, ...], members: tuple[MemberFact, ...]) -> str | None:
    """Per-member gate before any dict/set conversion; one failing member refuses all (D4).

    Returns an internal reason token or ``None``. Ages are authoritative 36–155 completed
    months; nothing is averaged or inferred."""

    ids = [m.participant_id for m in members]
    if len(audience) != len(set(audience)) or len(ids) != len(set(ids)):
        return "AUDIENCE_DUPLICATE"
    if not audience or len(audience) > AUDIENCE_MAX:
        return "AUDIENCE_SIZE"
    if sorted(ids) != sorted(audience):
        return "AUDIENCE_MISMATCH"
    for member in members:
        months = member.completed_age_months
        if months is None:
            return "AGE_NOT_SUPPORTED"
        try:
            validate_age_months(months)
        except CoreRuleViolation:
            return "AGE_NOT_SUPPORTED"
        if not member.consent_effective or not member.purpose_granted:
            return "CONSENT_REQUIRED"
    return None


# ------------------------------------------------------------------------ aggregate
@dataclass(frozen=True, slots=True)
class CacheHit:
    assistance_id: str
    request_revision: int
    job_id: str
    analysis_id: str
    analysis_revision: int


@dataclass(frozen=True, slots=True)
class HandoffRef:
    analysis_id: str
    analysis_revision: int
    job_id: str
    attempt_id: str


@dataclass(frozen=True, slots=True)
class ScheduleIdentity:
    """Frozen at commit (TC-10): every create attempt re-sends exactly this command."""

    create_key: str
    principal_id: str
    principal_kind: ActorKind
    request_revision: int


@dataclass(frozen=True, slots=True)
class AssistanceRequest:
    assistance_id: str
    request_revision: int
    record_version: int
    facts: ResolvedFacts
    checkpoint_ref: CheckpointRef
    requested_level: str
    request_reason: RequestReason
    child_intent: str | None
    client_request_id: str
    requester: Requester
    contributor: Contributor
    assistance_context_digest: str
    semantic_identity: str
    operation_target: str
    debounce_key: str
    status: RequestStatus
    status_reason: StatusReason | None
    job_id: str | None
    schedule: ScheduleIdentity | None
    reservation_id: str | None
    reservation: ReservationState | None
    settlement: Settlement
    cleanup_job_ids: tuple[str, ...]
    cancelled_by: Requester | None
    counts_for_debounce: bool
    cache_hit_of: CacheHit | None
    handoff: HandoffRef | None
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        _ref(self.assistance_id, "assistance_id")
        _int(self.request_revision, "request_revision", 1)
        _int(self.record_version, "record_version", 1)
        require_aware(self.created_at, "created_at")
        require_aware(self.updated_at, "updated_at")
        needs_reason = self.status in {RequestStatus.CANCELLED, RequestStatus.STALE,
                                       RequestStatus.FAILED}
        if needs_reason != (self.status_reason is not None):
            raise AssistanceRuleViolation(
                "cancelled/stale/failed need a reason, and only they carry one")
        if self.status is RequestStatus.SCHEDULED and self.job_id is None:
            raise AssistanceRuleViolation("a scheduled request is linked to one job")
        if (self.reservation_id is None) != (self.reservation is None):
            raise AssistanceRuleViolation("reservation id and state go together")

    @property
    def terminal(self) -> bool:
        return self.status not in NON_TERMINAL

    @property
    def audience(self) -> tuple[str, ...]:
        return self.facts.audience

    def etag(self) -> str:
        return assistance_etag(self.assistance_id, self.request_revision)

    def device_status(self) -> DeviceStatus:
        if self.status in NON_TERMINAL or self.status is RequestStatus.ANALYSIS_READY:
            # analysis_ready is not Child availability; Teacher review still gates any output.
            return DeviceStatus.PENDING
        if self.status is RequestStatus.CANCELLED:
            return DeviceStatus.CANCELLED
        return DeviceStatus.UNAVAILABLE


def assistance_etag(assistance_id: str, request_revision: int) -> str:
    return f'"assistance:{assistance_id}:{request_revision}"'


def create_key(assistance_id: str, request_revision: int) -> str:
    return f"assist:{assistance_id}:{request_revision}:vision"


class InvalidAssistanceTransition(AssistanceRuleViolation):
    pass


def _bump(request: AssistanceRequest, now: datetime, **changes: Any) -> AssistanceRequest:
    return replace(request, record_version=request.record_version + 1, updated_at=now,
                   **changes)


def link_job(request: AssistanceRequest, job_id: str, now: datetime) -> AssistanceRequest:
    if request.status is not RequestStatus.SCHEDULING:
        raise InvalidAssistanceTransition(f"cannot link a job from {request.status}")
    return _bump(request, now, status=RequestStatus.SCHEDULED, job_id=_ref(job_id, "job_id"))


def terminate(
    request: AssistanceRequest,
    status: RequestStatus,
    reason: StatusReason,
    now: datetime,
    *,
    cancelled_by: Requester | None = None,
    counts_for_debounce: bool | None = None,
) -> AssistanceRequest:
    """Cancel or stale: an invalidating transition that bumps ``request_revision`` (D2)."""

    if status not in {RequestStatus.CANCELLED, RequestStatus.STALE}:
        raise InvalidAssistanceTransition("terminate only cancels or stales")
    if request.terminal:
        raise InvalidAssistanceTransition(f"cannot {status} from {request.status}")
    return _bump(
        request, now, status=status, status_reason=reason,
        request_revision=request.request_revision + 1, cancelled_by=cancelled_by,
        counts_for_debounce=(request.counts_for_debounce if counts_for_debounce is None
                             else counts_for_debounce),
    )


def fail(request: AssistanceRequest, reason: StatusReason, now: datetime) -> AssistanceRequest:
    if request.status is not RequestStatus.SCHEDULED:
        raise InvalidAssistanceTransition(f"cannot fail from {request.status}")
    return _bump(request, now, status=RequestStatus.FAILED, status_reason=reason)


def hand_off(request: AssistanceRequest, ref: HandoffRef, now: datetime) -> AssistanceRequest:
    if request.status is not RequestStatus.SCHEDULED:
        raise InvalidAssistanceTransition(f"cannot hand off from {request.status}")
    return _bump(request, now, status=RequestStatus.ANALYSIS_READY, handoff=ref)


def add_cleanup_job(request: AssistanceRequest, job_id: str, now: datetime) -> AssistanceRequest:
    if job_id in request.cleanup_job_ids or job_id == request.job_id:
        return request
    return _bump(request, now, cleanup_job_ids=(*request.cleanup_job_ids, job_id))


def consume(request: AssistanceRequest, now: datetime) -> AssistanceRequest:
    """Monotonic: a started attempt makes the unit consumed forever (§9.1)."""

    if request.reservation is None or request.reservation is ReservationState.CONSUMED:
        return request
    if request.reservation is ReservationState.RELEASED:
        raise InvalidAssistanceTransition("a released unit cannot be consumed afterwards")
    return _bump(request, now, reservation=ReservationState.CONSUMED)


def settle(request: AssistanceRequest, now: datetime, *, any_started: bool) -> AssistanceRequest:
    """Close settlement; release a still-held unit only when no attempt ever started."""

    if not request.terminal:
        raise InvalidAssistanceTransition("only a terminal request settles")
    if request.settlement is Settlement.SETTLED:
        return request
    reservation = request.reservation
    if any_started:
        if reservation is ReservationState.RELEASED:
            raise InvalidAssistanceTransition("a released unit cannot be consumed afterwards")
        if reservation is ReservationState.HELD:
            reservation = ReservationState.CONSUMED
    elif reservation is ReservationState.HELD:
        reservation = ReservationState.RELEASED
    return _bump(request, now, settlement=Settlement.SETTLED, reservation=reservation)


__all__ = [
    "ASSISTANCE_CONTRACT_VERSION",
    "AUDIENCE_MAX",
    "CANCEL_CONTRACT",
    "CREATE_CONTRACT",
    "FIXTURE_POLICY_STATUS",
    "NON_TERMINAL",
    "ActorKind",
    "AssistanceRequest",
    "AssistanceRuleViolation",
    "CacheHit",
    "CheckpointRef",
    "Contributor",
    "DeviceStatus",
    "HandoffRef",
    "InvalidAssistanceTransition",
    "MemberFact",
    "PolicySnapshot",
    "RequestReason",
    "RequestStatus",
    "Requester",
    "ReservationState",
    "ResolvedFacts",
    "ScheduleIdentity",
    "Settlement",
    "SourcePin",
    "StatusReason",
    "TargetKind",
    "TargetScope",
    "add_cleanup_job",
    "assistance_etag",
    "audience_refusal",
    "consume",
    "create_key",
    "debounce_key",
    "fail",
    "hand_off",
    "link_job",
    "normalize_child_intent",
    "operation_target",
    "reason_class",
    "semantic_identity",
    "settle",
    "terminate",
]
