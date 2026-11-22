"""Story-owned ports for the Parent video admission saga (FEAT-066 T-1a; SRS l.395, l.596-597).

Story owns the saga and the generation rows. Two seams belong to other owners and are only shaped
here, never implemented in production code:

* ``VideoComputeReservationPort`` reserves the platform compute budget of one request (AI Policy
  resource accounting; FR-B-11 l.597: "reserve budget ... trước Billing admission").
* ``VideoQuotaAdmissionPort`` admits one request against the monthly quota (Billing; FR-B-10
  l.596; Billing contract Draft 9 §7.2 ``VideoQuotaPortV1``). It has no balance read: Story never
  counts units, grants or months.

Both are idempotent on ``(request_ref, idempotency_key)``: the same key returns the same reference
and a different fingerprint under one key answers ``IDEMPOTENCY_MISMATCH``. A call that cannot be
answered returns ``UNAVAILABLE``; the saga then keeps the intent pending (SRS l.395) and the
reconciler asks again with the same key. No port call runs inside a database transaction (BR-38
l.282: the saga is not a SQL transaction across modules).

The only adapters in this task are the local/test pair of ``infrastructure/story_video``; a
production adapter for either port is owned elsewhere (OD-03: the owner's scope rule) and, until it
exists, the route answers 503 ``PROVIDER_UNAVAILABLE`` after its authorization and state checks.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Final, Literal, Protocol

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_runs import ParentStoryLifecycleRecord
from sketch2life.domain.ai_jobs.model import AiJob

QUOTA_CONTRACT_VERSION = "video-quota-port-v1"

ScopeKind = Literal["PARENT_ACCOUNT", "ORGANIZATION"]


@dataclass(frozen=True, slots=True)
class VideoRequestScope:
    """The owner scope of a request: an opaque kind and reference, never a name or an e-mail.

    ``PARENT_ACCOUNT`` for a Parent run; ``ORGANIZATION`` plus the organization id for a Teacher run
    (BR-38 l.282, T-4b3b). The ports only forward it; they never branch on the kind.
    """

    kind: ScopeKind
    ref: str


class ReservationStatus(StrEnum):
    RESERVED = "RESERVED"
    COST_LIMIT_REACHED = "COST_LIMIT_REACHED"
    UNAVAILABLE = "UNAVAILABLE"


class AckStatus(StrEnum):
    DONE = "DONE"
    UNAVAILABLE = "UNAVAILABLE"


class QuotaStatus(StrEnum):
    ACCEPTED = "ACCEPTED"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"
    SUBSCRIPTION_RESTRICTED = "SUBSCRIPTION_RESTRICTED"
    IDEMPOTENCY_MISMATCH = "IDEMPOTENCY_MISMATCH"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class ReservationResult:
    status: ReservationStatus
    reservation_ref: str | None = None


@dataclass(frozen=True, slots=True)
class QuotaResult:
    status: QuotaStatus
    usage_ref: str | None = None
    grant_ref: str | None = None


class VideoComputeReservationPort(Protocol):
    def reserve(
        self, *, scope: VideoRequestScope, request_ref: str, idempotency_key: str, fingerprint: str
    ) -> ReservationResult: ...

    def release(
        self, *, scope: VideoRequestScope, reservation_ref: str, idempotency_key: str
    ) -> AckStatus: ...

    def settle(
        self, *, scope: VideoRequestScope, reservation_ref: str, outcome: str, idempotency_key: str
    ) -> AckStatus: ...


class VideoQuotaAdmissionPort(Protocol):
    def admit_video_request(
        self,
        *,
        scope: VideoRequestScope,
        request_ref: str,
        idempotency_key: str,
        fingerprint: str,
        contract_version: str,
    ) -> QuotaResult: ...


@dataclass(frozen=True, slots=True)
class StoryVideoAdapters:
    """The two composed ports. ``None`` where this is expected means: not configured (503)."""

    reservation: VideoComputeReservationPort
    quota: VideoQuotaAdmissionPort


@dataclass(frozen=True, slots=True)
class VideoRenderRequest:
    generation_id: str
    run_id: str
    story_revision_id: str
    script_hash: str
    scene_count: int
    job_ref: str


@dataclass(frozen=True, slots=True)
class VideoRenderResult:
    """What the render port answers; the bytes never leave Story (no URL, no key)."""

    content: bytes
    media_type: str
    technical_passed: bool = True
    consistency_passed: bool = True
    safety_passed: bool = True
    safety_finding_codes: tuple[str, ...] = ()
    failure_code: str | None = None


class VideoRenderPort(Protocol):
    """The video job behind a port; a fixture adapter in tests, the first real worker later."""

    def render(self, request: VideoRenderRequest) -> VideoRenderResult: ...


# --------------------------------------------------------------------------- repository records
@dataclass(frozen=True, slots=True)
class GenerationRecord:
    """One generation row as the saga and the route see it (no storage key, no provider text)."""

    generation_id: str
    run_id: str
    scope_kind: str
    scope_ref: str
    state: str
    kind: str
    generation_no: int | None
    job_ref: str | None
    key_hash: str
    fingerprint: str
    script_hash: str
    story_revision_id: str
    review_id: str
    quality_reason_code: str | None
    compute_reservation_ref: str | None
    compute_released_at: object | None
    billing_quota_usage_ref: str | None
    safe_failure_code: str | None
    started: bool
    generation_revision: int
    run_state: str
    run_revision: int


@dataclass(frozen=True, slots=True)
class IntentResult:
    """Tx1: a stored intent, its replay, or the lifecycle projection of a purged run."""

    record: GenerationRecord | None
    replayed: bool
    projection: ParentStoryLifecycleRecord | None = None


@dataclass(frozen=True, slots=True)
class RunCommandResult:
    """T-1b: a run command that was applied or replayed; the route reads the run afterwards.

    ``projection`` is the content-free lifecycle projection of a replay on a run that is already
    in a purge state (DTR 6.5); otherwise the run view is read after the commit.
    """

    run_id: str
    replayed: bool
    projection: ParentStoryLifecycleRecord | None = None


@dataclass(frozen=True, slots=True)
class AdmissionDecision:
    """The saga's verdict for Tx2: both receipts clear, or one refusal."""

    accepted: bool
    reservation_ref: str | None = None
    usage_ref: str | None = None
    refusal_code: str | None = None


@dataclass(frozen=True, slots=True)
class ProgressEvent:
    """One step of the video job as reported by a worker (D11)."""

    expected_state: str
    target_state: str
    output_asset_ref: str | None = None
    output_asset_version: int | None = None
    safe_failure_code: str | None = None
    safety_finding_codes: tuple[str, ...] = ()
    video_profile_ref: str | None = None
    model_revision: str | None = None
    config_hash: str | None = None
    safety_policy_version: str | None = None
    # T-1d1-fix (SRS l.2120, BR-11 l.255, FR-AI-07 l.573): a ``FAILED`` accepted request that still
    # counts toward the three-request cap returns the run to ``SCRIPT_REVIEW`` with a new adult
    # wait, unless the cap is spent (then the run ends ``FAILED``, l.2119). Only the generation
    # deadline asks for it; every other failure keeps the T-1a outcome (the run ``FAILED``).
    return_to_script_review: bool = False


@dataclass(frozen=True, slots=True)
class ProgressResult:
    applied: bool
    record: GenerationRecord | None
    reason: str | None = None


# ------------------------------------------------------------------ playback and detail (T-1c)
PLAYBACK_MEDIA_TYPE: Final = "video/mp4"


class PlaybackStatus(StrEnum):
    PLAYABLE = "PLAYABLE"
    NOT_FOUND = "NOT_FOUND"  # no such run for this owner, or a run being deleted
    NOT_PLAYABLE = "NOT_PLAYABLE"  # the run or the generation is not at a playable state


@dataclass(frozen=True, slots=True)
class PlaybackTarget:
    """What a playable video resolves to. ``storage_key`` stays inside Story: it is never
    serialized, logged or shown (SRS l.1692); it is excluded from ``repr``."""

    run_id: str
    generation_id: str
    scope_ref: str = field(repr=False)
    storage_key: str = field(repr=False)


@dataclass(frozen=True, slots=True)
class PlaybackResolution:
    status: PlaybackStatus
    target: PlaybackTarget | None = None


@dataclass(frozen=True, slots=True)
class PlaybackGrant:
    """What a verified playback token says: one video of one run for one actor, until ``expires_at``
    (epoch seconds). The actor is a digest, never an identity."""

    run_id: str
    generation_id: str
    actor_digest: str
    expires_at: int
    # T-5a: a class projection token also names its audience, the occurrence and the confirmation
    # it was issued under (SRS l.1662, l.1691). All three are ``None`` for an owner-view token.
    audience: str | None = None
    occurrence_id: str | None = None
    confirmed_ms: int | None = None


PROJECTION_AUDIENCE_CLAIM: Final = "projection"


@dataclass(frozen=True, slots=True)
class ProjectionClaims:
    """The extra signed claims of a class projection token (T-5a): the occurrence and the
    confirmation time (whole milliseconds, truncated) the token was issued under."""

    occurrence_id: str
    confirmed_ms: int


class PlaybackTokenError(Exception):
    """A playback token that is not accepted: ``INVALID_TOKEN`` (shape, signature, key) or
    ``TOKEN_EXPIRED`` (authentic but past its expiry). The message never holds the token."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class PlaybackTokenPort(Protocol):
    def issue(
        self,
        *,
        run_id: str,
        generation_id: str,
        actor_digest: str,
        projection: ProjectionClaims | None = None,
    ) -> tuple[str, int]:
        """A new token and its expiry (epoch seconds); with ``projection`` a class projection
        token (T-5a), without it the owner-view token of T-1c."""
        ...

    def verify(self, token: str) -> PlaybackGrant:
        """The grant of an authentic, unexpired token; ``PlaybackTokenError`` otherwise."""
        ...

    def actor_binding(self, scope_ref: str) -> str:
        """The digest a token carries for an owner scope reference."""
        ...


class ProjectionAuthorizationPort(Protocol):
    """The Lesson-owned half of every projection stream request (T-5a; SRS l.1691-1693).

    Story asks one question and gets one boolean: is the confirmation the token was issued under
    still the current one? Lesson answers from the occurrence, the CURRENT assignment and the class
    state; any doubt is ``False`` (the stream then answers the uniform 404).
    """

    def confirmation_is_current(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        generation_id: str,
        occurrence_id: str,
        confirmed_ms: int,
    ) -> bool: ...


@dataclass(frozen=True, slots=True)
class SampleFacts:
    """What the class projection needs to know about one run (T-5a): read by ``sample_facts``, the
    only Story read of Lesson code. No storage key, no name, no seed.

    ``playable`` is the single T-1a/T-1c predicate (``is_playable``: run ``VIDEO_READY``, current
    generation ``READY``, every validation ``PASSED``, an output). The plan pin is read from the
    CURRENT input revision (T-4b2 D3: copied forward into every revision).
    """

    run_id: str
    occurrence_ref: str | None
    run_state: str
    generation_id: str | None
    ready_at: datetime | None
    playable: bool
    plan_revision_id: str | None
    plan_revision_no: int | None
    plan_hash: str | None


@dataclass(frozen=True, slots=True)
class DetailScene:
    scene_index: int
    state: str


@dataclass(frozen=True, slots=True)
class DetailGeneration:
    """One generation row as the run detail needs it: ids, states, clock values and the job.

    No prompt, no storage key and no provider text (``has_output`` only says an output exists).
    """

    generation_id: str
    generation_no: int | None
    kind: str
    state: str
    technical_validation_state: str
    consistency_validation_state: str
    safety_validation_state: str
    has_output: bool
    admission_started_at: datetime
    accepted_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    updated_at: datetime
    job: AiJob | None


@dataclass(frozen=True, slots=True)
class RunVideoRows:
    """The bounded Story-owned read behind the video part of ``GET /v1/story-runs/{id}``:
    the accepted rows and the pending intent (at most four), and the scenes of the current one."""

    current_generation_id: str
    generations: tuple[DetailGeneration, ...]
    scenes: tuple[DetailScene, ...]


def port_fingerprint(record: GenerationRecord) -> str:
    """Fingerprint sent to both ports: run, script hash, kind and reason (plan D7)."""

    canonical = json.dumps(
        {
            "run_id": record.run_id,
            "script_hash": record.script_hash,
            "kind": record.kind,
            "reason": record.quality_reason_code,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class StoryVideoRepository(Protocol):
    def begin_intent(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        expected_revision: int,
        story_sha256: str,
        quality_reason_code: str | None,
        idempotency_key: str,
        adapters_available: bool,
    ) -> IntentResult: ...

    def finish_admission(
        self, generation_id: str, decision: AdmissionDecision
    ) -> GenerationRecord | None: ...

    def mark_compute_closed(self, generation_id: str) -> None: ...

    def get_generation(self, generation_id: str) -> GenerationRecord | None: ...

    def pending_intents(self, limit: int, run_id: str | None = None) -> list[GenerationRecord]: ...

    def pending_compute_closures(self, limit: int) -> list[GenerationRecord]: ...

    def open_generations(self, run_id: str) -> list[GenerationRecord]: ...

    def orphaned_in_flight(self, limit: int) -> list[GenerationRecord]: ...

    def advance(self, generation_id: str, event: ProgressEvent) -> ProgressResult: ...

    def fail_for_cancelled_run(self, generation_id: str) -> ProgressResult: ...

    def mark_unsuitable(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        expected_revision: int,
        generation_id: str,
        reason_code: str,
        idempotency_key: str,
    ) -> RunCommandResult: ...

    def complete_run(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        expected_revision: int,
        idempotency_key: str,
    ) -> RunCommandResult: ...

    def resolve_playback(
        self, *, principal: VerifiedPrincipal, run_id: str, generation_id: str | None
    ) -> PlaybackResolution: ...


__all__ = [
    "AckStatus",
    "AdmissionDecision",
    "DetailGeneration",
    "DetailScene",
    "GenerationRecord",
    "IntentResult",
    "PLAYBACK_MEDIA_TYPE",
    "PlaybackGrant",
    "PlaybackResolution",
    "PlaybackStatus",
    "PlaybackTokenError",
    "PlaybackTokenPort",
    "PlaybackTarget",
    "PROJECTION_AUDIENCE_CLAIM",
    "ProgressEvent",
    "ProgressResult",
    "ProjectionAuthorizationPort",
    "ProjectionClaims",
    "QUOTA_CONTRACT_VERSION",
    "QuotaResult",
    "QuotaStatus",
    "ReservationResult",
    "ReservationStatus",
    "RunCommandResult",
    "RunVideoRows",
    "SampleFacts",
    "ScopeKind",
    "StoryVideoAdapters",
    "StoryVideoRepository",
    "VideoComputeReservationPort",
    "VideoQuotaAdmissionPort",
    "VideoRenderPort",
    "VideoRenderRequest",
    "VideoRenderResult",
    "VideoRequestScope",
    "port_fingerprint",
]
