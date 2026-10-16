"""BE2-02 C1 Vision observation and meaning-correction model (DATA-22, 0.1-candidate).

Pure rules only: no framework, contract, storage, queue or provider imports. The original
observation is an immutable record with its own canonical hash; Child proposals and Teacher
confirmations are separate append-only records; the analysis head carries the CAS revision,
the pinned source/context/lineage and the pointer to the current confirmed meaning.
"""

from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from hashlib import sha256

from sketch2life.domain.ai_jobs.completion import canonical_sha256
from sketch2life.domain.ai_jobs.model import TERMINAL_STATES, JobState, require_aware

ANALYSIS_CONTRACT_VERSION = "0.1-candidate"
VISION_ANALYSIS_JOB_TYPE = "vision_analysis"
# SRS LIMIT_TEXT_SHORT / LIMIT_TEXT_LONG (both PROPOSED); 16 intended objects is a technical
# payload bound for the candidate, not a pedagogical rule.
SHORT_TEXT_MAX = 128
LONG_TEXT_MAX = 4000
INTENDED_OBJECTS_MAX = 16
# Candidate wire bounds shared with the DATA-22 contracts (C1-R04): an observation reference is
# an OpaqueId-sized token and each projected observation collection holds at most 256 items.
OBSERVATION_REF_MAX = 120
OBSERVATION_COLLECTION_MAX = 256
SUPPORTED_RENDER_MEDIA_TYPES = frozenset({"image/png", "image/jpeg"})

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_OBSERVATION_REF = re.compile(r"^[a-z0-9-]+$")
_CONTROL = re.compile(r"[\x00-\x1f\x7f-\x9f]")
_CONTROL_EXCEPT_NEWLINE = re.compile(r"[\x00-\x09\x0b-\x1f\x7f-\x9f]")
# If-Match uses strong comparison: a weak (W/) tag, a list or ``*`` never matches.
_ETAG = re.compile(r'^"analysis:([A-Za-z0-9_.:-]{1,120}):([1-9][0-9]{0,9})"$')


class AnalysisRuleViolation(ValueError):
    """A value or transition breaks a DATA-22 candidate invariant; never silently repaired."""


class ActorRole(StrEnum):
    TEACHER = "teacher"
    CHILD_DEVICE = "child_device"


class CorrectionKind(StrEnum):
    CHILD_PROPOSAL = "child_proposal"
    TEACHER_CONFIRMATION = "teacher_confirmation"


class MeaningStatus(StrEnum):
    PROPOSED = "proposed"
    CONFIRMED = "confirmed"


class AcceptedStatus(StrEnum):
    """Disposition of a stored analysis; deliberately not a job state. Rejected results are
    never stored, so they have no member here."""

    ACCEPTED = "accepted"
    STALE = "stale"


class ProviderContextMode(StrEnum):
    IMAGE_ONLY = "image_only"
    TYPED_CONTEXT = "typed_context"


class EvidenceKind(StrEnum):
    """How an observation was produced. There is no live member: C1 has no real inference."""

    SYNTHETIC_FAKE = "synthetic_fake"
    OFFLINE_LEGACY_BRIDGE = "offline_legacy_bridge"


class LexicalOutcome(StrEnum):
    PASSED = "passed"
    NOT_EXECUTED = "not_executed"


class InvalidationReason(StrEnum):
    CHILD_INTENT_PROPOSED = "child_intent_proposed"
    TEACHER_MEANING_CONFIRMED = "teacher_meaning_confirmed"
    SOURCE_CHANGED = "source_changed"
    CONTEXT_CHANGED = "context_changed"
    INTENT_CHANGED = "intent_changed"
    CONSENT_REVOKED = "consent_revoked"


OWNER_INVALIDATION_REASONS = frozenset(
    {
        InvalidationReason.SOURCE_CHANGED,
        InvalidationReason.CONTEXT_CHANGED,
        InvalidationReason.INTENT_CHANGED,
        InvalidationReason.CONSENT_REVOKED,
    }
)


# ------------------------------------------------------------------------- text rules
def normalize_short_text(value: object) -> str:
    """NFC + trim, 1..128 code points, no control characters (SRS ShortText candidate)."""

    return _normalize_text(value, SHORT_TEXT_MAX, _CONTROL)


def normalize_long_text(value: object) -> str:
    """NFC + trim, 1..4000 code points, newline is the only permitted control character."""

    return _normalize_text(value, LONG_TEXT_MAX, _CONTROL_EXCEPT_NEWLINE)


def _normalize_text(value: object, limit: int, forbidden: re.Pattern[str]) -> str:
    if not isinstance(value, str):
        raise AnalysisRuleViolation("text must be a string")
    normalized = unicodedata.normalize("NFC", value).strip()
    if not normalized:
        raise AnalysisRuleViolation("text must not be empty")
    if len(normalized) > limit:
        raise AnalysisRuleViolation(f"text exceeds {limit} code points")
    if forbidden.search(normalized):
        raise AnalysisRuleViolation("text contains control characters")
    return normalized


def normalize_intended_objects(values: object) -> tuple[str, ...]:
    if not isinstance(values, list | tuple) or not values:
        raise AnalysisRuleViolation("intended_objects needs at least one item")
    if len(values) > INTENDED_OBJECTS_MAX:
        raise AnalysisRuleViolation(f"intended_objects allows at most {INTENDED_OBJECTS_MAX} items")
    normalized = tuple(normalize_short_text(value) for value in values)
    folded = [value.casefold() for value in normalized]
    if len(set(folded)) != len(folded):
        raise AnalysisRuleViolation("intended_objects must be unique")
    return normalized


def require_confidence(value: object) -> float | None:
    """Null stays null; otherwise a finite non-bool number in [0, 1]. Nothing is synthesized."""

    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise AnalysisRuleViolation("confidence must be null or a number")
    if not math.isfinite(value) or not 0 <= value <= 1:
        raise AnalysisRuleViolation("confidence must be finite and within [0, 1]")
    return float(value)


def _require_sha(value: str, name: str) -> None:
    if not isinstance(value, str) or not _SHA256.match(value):
        raise AnalysisRuleViolation(f"{name} must be lowercase sha256 hex")


def _require_id(value: str, name: str) -> None:
    if not isinstance(value, str) or not value or len(value) > 120:
        raise AnalysisRuleViolation(f"{name} is required")


def _require_int(value: int, name: str, minimum: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise AnalysisRuleViolation(f"{name} must be an integer >= {minimum}")


# ------------------------------------------------------------------------ source binding
@dataclass(frozen=True, slots=True)
class CheckpointBinding:
    """BE1 canvas checkpoint metadata. ``checksum_sha256`` hashes the JSON checkpoint document;
    it is never an image hash and never proves media admission."""

    checkpoint_id: str
    canvas_id: str
    document_epoch: int
    checkpoint_revision: int
    checksum_sha256: str

    def __post_init__(self) -> None:
        _require_id(self.checkpoint_id, "checkpoint_id")
        _require_id(self.canvas_id, "canvas_id")
        _require_int(self.document_epoch, "document_epoch", 0)
        _require_int(self.checkpoint_revision, "checkpoint_revision", 1)
        _require_sha(self.checksum_sha256, "checkpoint checksum")


@dataclass(frozen=True, slots=True)
class RenderBinding:
    """Rendered PNG/JPEG derived from exactly one checkpoint; ``render_sha256`` hashes bytes."""

    render_ref: str
    render_sha256: str
    media_type: str
    source_checkpoint_id: str
    source_checkpoint_checksum: str
    renderer_version: str

    def __post_init__(self) -> None:
        _require_id(self.render_ref, "render_ref")
        _require_sha(self.render_sha256, "render_sha256")
        _require_sha(self.source_checkpoint_checksum, "source_checkpoint_checksum")
        _require_id(self.source_checkpoint_id, "source_checkpoint_id")
        _require_id(self.renderer_version, "renderer_version")


@dataclass(frozen=True, slots=True)
class AdmissionReceipt:
    """Trusted media-admission receipt; it binds one exact render ref and hash."""

    receipt_id: str
    receipt_sha256: str
    render_ref: str
    render_sha256: str
    decision: str
    policy_version: str

    def __post_init__(self) -> None:
        _require_id(self.receipt_id, "receipt_id")
        _require_sha(self.receipt_sha256, "receipt_sha256")
        _require_sha(self.render_sha256, "admission render_sha256")
        if self.decision not in {"PASS", "RECAPTURE"}:
            raise AnalysisRuleViolation("admission decision must be PASS or RECAPTURE")


@dataclass(frozen=True, slots=True)
class SourceSnapshot:
    """What an opaque ``input_snapshot_ref`` resolves to on the trusted source port."""

    snapshot_ref: str
    organization_id: str
    checkpoint: CheckpointBinding
    render: RenderBinding

    def input_hash(self) -> str:
        """Candidate request input hash: exact pinned source identity (ASSUMED_CONTRACT)."""

        return canonical_sha256(
            {
                "snapshot_ref": self.snapshot_ref,
                "checkpoint": {
                    "checkpoint_id": self.checkpoint.checkpoint_id,
                    "canvas_id": self.checkpoint.canvas_id,
                    "document_epoch": self.checkpoint.document_epoch,
                    "checkpoint_revision": self.checkpoint.checkpoint_revision,
                    "checksum_sha256": self.checkpoint.checksum_sha256,
                },
                "render": {
                    "render_ref": self.render.render_ref,
                    "render_sha256": self.render.render_sha256,
                },
            }
        )


class SourceVerdict(StrEnum):
    PROCEED = "proceed"
    SOURCE_NOT_FOUND = "SOURCE_NOT_FOUND"
    CHECKPOINT_CANVAS_MISMATCH = "CHECKPOINT_CANVAS_MISMATCH"
    RENDER_NOT_DERIVED_FROM_CHECKPOINT = "RENDER_NOT_DERIVED_FROM_CHECKPOINT"
    CHECKSUM_CONFUSED = "CHECKSUM_CONFUSED"
    MEDIA_TYPE_UNSUPPORTED = "MEDIA_TYPE_UNSUPPORTED"
    ADMISSION_MISSING = "ADMISSION_MISSING"
    ADMISSION_NOT_BOUND = "ADMISSION_NOT_BOUND"
    ADMISSION_NOT_PASSED = "ADMISSION_NOT_PASSED"


def verify_source(
    snapshot: SourceSnapshot | None,
    admission: AdmissionReceipt | None,
    *,
    organization_id: str,
    canvas_id: str,
) -> SourceVerdict:
    """Checkpoint, render and admission are three independent bindings, checked in order."""

    if snapshot is None or snapshot.organization_id != organization_id:
        return SourceVerdict.SOURCE_NOT_FOUND
    checkpoint, render = snapshot.checkpoint, snapshot.render
    if checkpoint.canvas_id != canvas_id:
        return SourceVerdict.CHECKPOINT_CANVAS_MISMATCH
    if (
        render.source_checkpoint_id != checkpoint.checkpoint_id
        or render.source_checkpoint_checksum != checkpoint.checksum_sha256
    ):
        return SourceVerdict.RENDER_NOT_DERIVED_FROM_CHECKPOINT
    if render.render_sha256 == checkpoint.checksum_sha256:
        return SourceVerdict.CHECKSUM_CONFUSED
    if render.media_type not in SUPPORTED_RENDER_MEDIA_TYPES:
        return SourceVerdict.MEDIA_TYPE_UNSUPPORTED
    if admission is None:
        return SourceVerdict.ADMISSION_MISSING
    if admission.render_ref != render.render_ref or admission.render_sha256 != render.render_sha256:
        return SourceVerdict.ADMISSION_NOT_BOUND
    if admission.decision != "PASS":
        return SourceVerdict.ADMISSION_NOT_PASSED
    return SourceVerdict.PROCEED


# ------------------------------------------------------------------------ scope / lineage
@dataclass(frozen=True, slots=True)
class AnalysisScope:
    """Server-resolved scope from the trusted request pin; never taken from a client body."""

    organization_id: str
    class_id: str
    session_id: str
    canvas_id: str
    group_id: str | None
    contributor_participant_id: str
    audience_participant_ids: tuple[str, ...]
    purpose_code: str

    def __post_init__(self) -> None:
        for name in ("organization_id", "class_id", "session_id", "canvas_id",
                     "contributor_participant_id", "purpose_code"):
            _require_id(getattr(self, name), name)
        if self.contributor_participant_id not in self.audience_participant_ids:
            raise AnalysisRuleViolation("contributor must be part of the audience")


@dataclass(frozen=True, slots=True)
class AssistancePin:
    """BE2-03 assistance request identity as consumed here (lifecycle not implemented)."""

    assistance_id: str
    request_revision: int
    input_snapshot_ref: str
    context_revision: int
    scope: AnalysisScope


@dataclass(frozen=True, slots=True)
class JobLineageView:
    """Read-only view of BE2-01 job lineage and ownership scope; never written by this card.

    Scope fields are the foundation ``JobScope`` as stored; ``job_scope_matches`` maps them to
    the trusted assistance pin (C1-R03 candidate mapping)."""

    job_id: str
    organization_id: str
    job_type: str
    state: JobState
    active_attempt_id: str
    request_id: str
    request_revision: int
    input_hash: str
    context_revision: int
    session_id: str | None
    subject_refs: tuple[str, ...]
    purpose_code: str
    target_id: str


@dataclass(frozen=True, slots=True)
class ObservationClaim:
    """Worker-side DATA-22 identity: which pinned request/job attempt the result is for."""

    job_id: str
    job_attempt_id: str
    assistance_id: str
    expected_request_revision: int
    input_snapshot_ref: str
    context_revision: int


class LineageVerdict(StrEnum):
    PROCEED = "proceed"
    REQUEST_NOT_FOUND = "REQUEST_NOT_FOUND"
    REQUEST_MISMATCH = "REQUEST_MISMATCH"
    JOB_NOT_FOUND = "JOB_NOT_FOUND"
    JOB_TYPE_MISMATCH = "JOB_TYPE_MISMATCH"
    JOB_SCOPE_MISMATCH = "JOB_SCOPE_MISMATCH"
    JOB_CANCELLED = "JOB_CANCELLED"
    JOB_TERMINAL = "JOB_TERMINAL"
    ATTEMPT_SUPERSEDED = "ATTEMPT_SUPERSEDED"
    INVALID_STATE = "INVALID_STATE"
    INPUT_MISMATCH = "INPUT_MISMATCH"


def check_lineage(
    claim: ObservationClaim, pin: AssistancePin | None, job: JobLineageView | None
) -> LineageVerdict:
    """Ordered guards; only a running active attempt of the pinned request may proceed."""

    if pin is None:
        return LineageVerdict.REQUEST_NOT_FOUND
    if (
        claim.assistance_id != pin.assistance_id
        or claim.expected_request_revision != pin.request_revision
        or claim.input_snapshot_ref != pin.input_snapshot_ref
        or claim.context_revision != pin.context_revision
    ):
        return LineageVerdict.REQUEST_MISMATCH
    if job is None or job.job_id != claim.job_id:
        return LineageVerdict.JOB_NOT_FOUND
    if job.organization_id != pin.scope.organization_id:
        return LineageVerdict.JOB_NOT_FOUND
    if job.job_type != VISION_ANALYSIS_JOB_TYPE:
        return LineageVerdict.JOB_TYPE_MISMATCH
    if not job_scope_matches(job, pin):
        return LineageVerdict.JOB_SCOPE_MISMATCH
    if job.state is JobState.CANCELLED:
        return LineageVerdict.JOB_CANCELLED
    if job.state in TERMINAL_STATES:
        return LineageVerdict.JOB_TERMINAL
    if job.active_attempt_id != claim.job_attempt_id:
        return LineageVerdict.ATTEMPT_SUPERSEDED
    if job.state is not JobState.RUNNING:
        return LineageVerdict.INVALID_STATE
    if (
        job.request_id != pin.assistance_id
        or job.request_revision != pin.request_revision
        or job.context_revision != pin.context_revision
    ):
        return LineageVerdict.REQUEST_MISMATCH
    return LineageVerdict.PROCEED


def job_scope_matches(job: JobLineageView, pin: AssistancePin) -> bool:
    """C1 candidate mapping of foundation ``JobScope`` to the assistance pin: same session,
    subjects = audience participants (order-insensitive, duplicates kept), same purpose and
    target = assistance id. Class/canvas are not part of the foundation job contract."""

    scope = pin.scope
    return (
        job.session_id == scope.session_id
        and sorted(job.subject_refs) == sorted(scope.audience_participant_ids)
        and job.purpose_code == scope.purpose_code
        and job.target_id == pin.assistance_id
    )


def check_input_hash(job: JobLineageView, snapshot: SourceSnapshot) -> LineageVerdict:
    if job.input_hash != snapshot.input_hash():
        return LineageVerdict.INPUT_MISMATCH
    return LineageVerdict.PROCEED


# ------------------------------------------------------------------- original observation
@dataclass(frozen=True, slots=True)
class ObservedLabel:
    value: str
    language_status: str
    language_tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value:
            raise AnalysisRuleViolation("observed label must not be empty")


@dataclass(frozen=True, slots=True)
class EntityObservation:
    observation_id: str
    label: ObservedLabel
    confidence: float | None

    def __post_init__(self) -> None:
        require_confidence(self.confidence)


@dataclass(frozen=True, slots=True)
class ActionObservation:
    observation_id: str
    label: ObservedLabel
    actor_ref: str | None
    object_ref: str | None
    confidence: float | None

    def __post_init__(self) -> None:
        require_confidence(self.confidence)


@dataclass(frozen=True, slots=True)
class RelationObservation:
    observation_id: str
    predicate: ObservedLabel
    subject_ref: str
    object_ref: str
    confidence: float | None

    def __post_init__(self) -> None:
        require_confidence(self.confidence)


@dataclass(frozen=True, slots=True)
class ThemeObservation:
    observation_id: str
    label: ObservedLabel
    evidence_refs: tuple[str, ...]
    confidence: float | None

    def __post_init__(self) -> None:
        require_confidence(self.confidence)


@dataclass(frozen=True, slots=True)
class AmbiguousRegionObservation:
    observation_id: str
    note: ObservedLabel


@dataclass(frozen=True, slots=True)
class OriginalObservation:
    """The whole typed model output; no field is a ground-truth claim."""

    entities: tuple[EntityObservation, ...]
    actions: tuple[ActionObservation, ...]
    relations: tuple[RelationObservation, ...]
    themes: tuple[ThemeObservation, ...]
    ambiguous_regions: tuple[AmbiguousRegionObservation, ...]

    def canonical(self) -> dict[str, object]:
        def label(value: ObservedLabel) -> dict[str, object]:
            return {"value": value.value, "language_status": value.language_status,
                    "language_tags": list(value.language_tags)}

        return {
            "entities": [{"observation_id": e.observation_id, "label": label(e.label),
                          "confidence": e.confidence} for e in self.entities],
            "actions": [{"observation_id": a.observation_id, "label": label(a.label),
                         "actor_ref": a.actor_ref, "object_ref": a.object_ref,
                         "confidence": a.confidence} for a in self.actions],
            "relations": [{"observation_id": r.observation_id, "predicate": label(r.predicate),
                           "subject_ref": r.subject_ref, "object_ref": r.object_ref,
                           "confidence": r.confidence} for r in self.relations],
            "themes": [{"observation_id": t.observation_id, "label": label(t.label),
                        "evidence_refs": list(t.evidence_refs), "confidence": t.confidence}
                       for t in self.themes],
            "ambiguous_regions": [{"observation_id": g.observation_id, "note": label(g.note)}
                                  for g in self.ambiguous_regions],
        }


def observation_bounds_violation(observation: OriginalObservation) -> str | None:
    """Closed token when a mapped observation cannot be projected through the DATA-22
    candidate contracts (C1-R04); checked before acceptance, never repaired or truncated."""

    ids = [e.observation_id for e in observation.entities]
    ids += [a.observation_id for a in observation.actions]
    ids += [r.observation_id for r in observation.relations]
    ids += [t.observation_id for t in observation.themes]
    ids += [g.observation_id for g in observation.ambiguous_regions]
    # Only ``None`` means "absent" for an optional action ref; an empty string is checked (and
    # rejected) like any other reference.
    refs = [ref for a in observation.actions for ref in (a.actor_ref, a.object_ref)
            if ref is not None]
    refs += [ref for r in observation.relations for ref in (r.subject_ref, r.object_ref)]
    refs += [ref for t in observation.themes for ref in t.evidence_refs]
    for ref in (*ids, *refs):
        # ``fullmatch``: a ``$`` anchor with ``match`` would accept a trailing newline that the
        # DATA-22 contract pattern rejects.
        if not isinstance(ref, str) or not _OBSERVATION_REF.fullmatch(ref):
            return "OBSERVATION_REF_INVALID"
        if len(ref) > OBSERVATION_REF_MAX:
            return "OBSERVATION_REF_TOO_LONG"
    for entity in observation.entities:
        try:
            if normalize_short_text(entity.label.value) != entity.label.value:
                return "LABEL_NOT_SHORT_TEXT"
        except AnalysisRuleViolation:
            return "LABEL_NOT_SHORT_TEXT"
    if len(observation.entities) > OBSERVATION_COLLECTION_MAX:
        return "TOO_MANY_OBJECT_CANDIDATES"
    if len(derive_uncertainty(observation).unknown_confidence_refs) > OBSERVATION_COLLECTION_MAX:
        return "TOO_MANY_UNKNOWN_CONFIDENCE_REFS"
    if len(observation.ambiguous_regions) > OBSERVATION_COLLECTION_MAX:
        return "TOO_MANY_AMBIGUOUS_REGIONS"
    return None


@dataclass(frozen=True, slots=True)
class ProviderResultRecord:
    """Immutable retained full provider result (C1-R06): canonical JSON of the whole typed
    result, resolvable by ``result_ref``; the hash always matches the retained content."""

    result_ref: str
    analysis_id: str
    organization_id: str
    result_contract: str
    canonical_json: str
    result_sha256: str

    def __post_init__(self) -> None:
        _require_id(self.result_ref, "result_ref")
        _require_sha(self.result_sha256, "result_sha256")
        if not isinstance(self.canonical_json, str) or not self.canonical_json:
            raise AnalysisRuleViolation("provider result content is required")
        if document_sha256(self.canonical_json) != self.result_sha256:
            raise AnalysisRuleViolation("provider result hash does not match its content")


def document_sha256(document: str) -> str:
    return sha256(document.encode("utf-8")).hexdigest()


def provider_result_ref(analysis_id: str) -> str:
    return f"result:{analysis_id}"


@dataclass(frozen=True, slots=True)
class ObjectCandidate:
    """DATA-22 ``object_candidates`` item: a model candidate, never the child's intent."""

    label: str
    confidence: float | None
    observation_ref: str


def object_candidates(observation: OriginalObservation) -> tuple[ObjectCandidate, ...]:
    """Entities only; label value and nullable confidence copied as observed, order kept."""

    return tuple(
        ObjectCandidate(entity.label.value, entity.confidence, entity.observation_id)
        for entity in observation.entities
    )


@dataclass(frozen=True, slots=True)
class Uncertainty:
    """Candidate DATA-22 ``uncertainty``. No calibration evidence exists for any C1 profile,
    so calibration is always ``uncalibrated`` and a null confidence is never zero/certain."""

    unknown_confidence_refs: tuple[str, ...]
    ambiguous_region_refs: tuple[str, ...]
    calibration: str = "uncalibrated"
    requires_meaning_confirmation: bool = True


def derive_uncertainty(observation: OriginalObservation) -> Uncertainty:
    unknown = [e.observation_id for e in observation.entities if e.confidence is None]
    unknown += [a.observation_id for a in observation.actions if a.confidence is None]
    unknown += [r.observation_id for r in observation.relations if r.confidence is None]
    unknown += [t.observation_id for t in observation.themes if t.confidence is None]
    return Uncertainty(
        unknown_confidence_refs=tuple(unknown),
        ambiguous_region_refs=tuple(g.observation_id for g in observation.ambiguous_regions),
    )


@dataclass(frozen=True, slots=True)
class ObservationEvidence:
    """Provenance of one observation. A legacy bridge result is always image-only; a typed
    context envelope is only ever consumed by the synthetic fake."""

    evidence_kind: EvidenceKind
    provider_context_mode: ProviderContextMode
    adapter_id: str
    result_contract: str
    result_sha256: str
    executed_at: datetime
    transport_attempts: int
    profile_id: str | None = None
    profile_catalog_hash: str | None = None
    config_hash: str | None = None
    adapter_version: str | None = None
    model_identifier: str | None = None
    model_revision: str | None = None
    content_policy_version: str | None = None
    policy_match_view_version: str | None = None

    def __post_init__(self) -> None:
        require_aware(self.executed_at, "executed_at")
        _require_sha(self.result_sha256, "result_sha256")
        if self.transport_attempts not in {0, 1}:
            raise AnalysisRuleViolation("an observation uses at most one provider attempt")
        if self.evidence_kind is EvidenceKind.OFFLINE_LEGACY_BRIDGE:
            if self.provider_context_mode is not ProviderContextMode.IMAGE_ONLY:
                raise AnalysisRuleViolation("the legacy bridge is image_only")
            required = (self.profile_id, self.profile_catalog_hash, self.config_hash,
                        self.adapter_version, self.model_identifier, self.model_revision,
                        self.content_policy_version, self.policy_match_view_version)
            if any(value is None for value in required):
                raise AnalysisRuleViolation("legacy bridge evidence needs full model provenance")
            if self.transport_attempts != 1:
                raise AnalysisRuleViolation("legacy bridge evidence records exactly one call")


@dataclass(frozen=True, slots=True)
class ModerationOutcome:
    """Candidate moderation record. A lexical regression pass is not overall clearance."""

    lexical: LexicalOutcome
    lexical_policy_version: str | None
    match_view_version: str | None
    comprehensive_moderation: str = "not_run"
    child_visibility: str = "withheld"


@dataclass(frozen=True, slots=True)
class VisionObservation:
    """Immutable original observation record; storage offers no update for it."""

    analysis_id: str
    organization_id: str
    observation: OriginalObservation
    evidence: ObservationEvidence
    moderation: ModerationOutcome
    recorded_at: datetime
    observation_sha256: str

    def __post_init__(self) -> None:
        require_aware(self.recorded_at, "recorded_at")
        if self.observation_sha256 != observation_hash(self.observation, self.evidence):
            raise AnalysisRuleViolation("observation hash does not match its content")


def observation_hash(observation: OriginalObservation, evidence: ObservationEvidence) -> str:
    return canonical_sha256(
        {
            "observation": observation.canonical(),
            "result_sha256": evidence.result_sha256,
            "evidence_kind": str(evidence.evidence_kind),
            "provider_context_mode": str(evidence.provider_context_mode),
        }
    )


def new_observation(
    *,
    analysis_id: str,
    organization_id: str,
    observation: OriginalObservation,
    evidence: ObservationEvidence,
    moderation: ModerationOutcome,
    now: datetime,
) -> VisionObservation:
    return VisionObservation(
        analysis_id=analysis_id,
        organization_id=organization_id,
        observation=observation,
        evidence=evidence,
        moderation=moderation,
        recorded_at=now,
        observation_sha256=observation_hash(observation, evidence),
    )


# ---------------------------------------------------------------- corrections and head
@dataclass(frozen=True, slots=True)
class ActorRef:
    """Server-resolved author; a device participant/turn binding is never client-asserted."""

    principal_id: str
    role: ActorRole
    participant_id: str | None = None
    turn_id: str | None = None

    def __post_init__(self) -> None:
        _require_id(self.principal_id, "principal_id")
        if self.role is ActorRole.CHILD_DEVICE and (not self.participant_id or not self.turn_id):
            raise AnalysisRuleViolation("a child device author needs its bound participant/turn")
        if self.role is ActorRole.TEACHER and (self.participant_id or self.turn_id):
            raise AnalysisRuleViolation("a teacher author has no participant/turn binding")


@dataclass(frozen=True, slots=True)
class MeaningCorrection:
    """Append-only Child proposal or Teacher confirmation; never edits the observation."""

    correction_id: str
    analysis_id: str
    correction_version: int
    kind: CorrectionKind
    author: ActorRef
    intended_objects: tuple[str, ...]
    child_explanation: str | None
    correction_reason: str
    expected_context_revision: int
    basis_correction_ref: str | None
    recorded_at: datetime

    def __post_init__(self) -> None:
        require_aware(self.recorded_at, "recorded_at")
        _require_id(self.correction_id, "correction_id")
        _require_int(self.correction_version, "correction_version", 2)
        _require_int(self.expected_context_revision, "expected_context_revision", 0)
        if normalize_intended_objects(self.intended_objects) != self.intended_objects:
            raise AnalysisRuleViolation("intended_objects must be normalized")
        if normalize_short_text(self.correction_reason) != self.correction_reason:
            raise AnalysisRuleViolation("correction_reason must be normalized")
        if self.child_explanation is not None and (
            normalize_long_text(self.child_explanation) != self.child_explanation
        ):
            raise AnalysisRuleViolation("child_explanation must be normalized")
        if self.kind is CorrectionKind.CHILD_PROPOSAL:
            if self.author.role is not ActorRole.CHILD_DEVICE:
                raise AnalysisRuleViolation("only a bound child device records a proposal")
            if self.basis_correction_ref is not None:
                raise AnalysisRuleViolation("a child proposal has no basis correction")
        else:
            if self.author.role is not ActorRole.TEACHER:
                raise AnalysisRuleViolation("only a scoped teacher confirms meaning")
            if self.child_explanation is not None:
                raise AnalysisRuleViolation("a teacher cannot author the child's explanation")

    @property
    def meaning_status(self) -> MeaningStatus:
        if self.kind is CorrectionKind.TEACHER_CONFIRMATION:
            return MeaningStatus.CONFIRMED
        return MeaningStatus.PROPOSED


@dataclass(frozen=True, slots=True)
class AnalysisLineage:
    assistance_id: str
    request_revision: int
    job_id: str
    job_attempt_id: str
    input_hash: str


@dataclass(frozen=True, slots=True)
class AnalysisHead:
    """Aggregate root: CAS revision, pinned bindings and pointers. Original observation and
    corrections are referenced, never embedded or rewritten."""

    analysis_id: str
    analysis_revision: int
    scope: AnalysisScope
    lineage: AnalysisLineage
    source: SourceSnapshot
    admission: AdmissionReceipt
    context_revision: int
    observation_sha256: str
    accepted_status: AcceptedStatus
    status_reason: str | None
    correction_refs: tuple[str, ...]
    current_meaning_ref: str | None
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        _require_int(self.analysis_revision, "analysis_revision", 1)
        require_aware(self.created_at, "created_at")
        require_aware(self.updated_at, "updated_at")
        if self.current_meaning_ref is not None and (
            self.current_meaning_ref not in self.correction_refs
        ):
            raise AnalysisRuleViolation("current meaning must be one of the corrections")
        if (self.accepted_status is AcceptedStatus.STALE) != (self.status_reason is not None):
            raise AnalysisRuleViolation("a stale analysis needs a reason and only then")

    @property
    def organization_id(self) -> str:
        return self.scope.organization_id

    @property
    def etag(self) -> str:
        return analysis_etag(self.analysis_id, self.analysis_revision)


def new_head(
    *,
    analysis_id: str,
    scope: AnalysisScope,
    lineage: AnalysisLineage,
    source: SourceSnapshot,
    admission: AdmissionReceipt,
    context_revision: int,
    observation_sha256: str,
    stale_reason: InvalidationReason | None,
    now: datetime,
) -> AnalysisHead:
    if stale_reason is not None and stale_reason not in OWNER_INVALIDATION_REASONS:
        raise AnalysisRuleViolation("a new analysis is only stale for an owner change")
    return AnalysisHead(
        analysis_id=analysis_id,
        analysis_revision=1,
        scope=scope,
        lineage=lineage,
        source=source,
        admission=admission,
        context_revision=context_revision,
        observation_sha256=observation_sha256,
        accepted_status=AcceptedStatus.STALE if stale_reason else AcceptedStatus.ACCEPTED,
        status_reason=None if stale_reason is None else str(stale_reason),
        correction_refs=(),
        current_meaning_ref=None,
        created_at=now,
        updated_at=now,
    )


def apply_correction(
    head: AnalysisHead, correction: MeaningCorrection, now: datetime
) -> AnalysisHead:
    """Append one correction. Only a teacher confirmation moves the current meaning."""

    if head.accepted_status is not AcceptedStatus.ACCEPTED:
        raise AnalysisRuleViolation("a stale analysis cannot take new corrections")
    if correction.analysis_id != head.analysis_id:
        raise AnalysisRuleViolation("correction belongs to another analysis")
    if correction.correction_version != head.analysis_revision + 1:
        raise AnalysisRuleViolation("correction version must be the next analysis revision")
    if correction.correction_id in head.correction_refs:
        raise AnalysisRuleViolation("correction already recorded")
    if (
        correction.basis_correction_ref is not None
        and correction.basis_correction_ref not in head.correction_refs
    ):
        raise AnalysisRuleViolation("basis correction is not part of this analysis")
    confirmed = correction.kind is CorrectionKind.TEACHER_CONFIRMATION
    return replace(
        head,
        analysis_revision=head.analysis_revision + 1,
        correction_refs=(*head.correction_refs, correction.correction_id),
        current_meaning_ref=correction.correction_id if confirmed else head.current_meaning_ref,
        updated_at=now,
    )


def mark_stale(head: AnalysisHead, reason: InvalidationReason, now: datetime) -> AnalysisHead:
    """Owner notice: the analysis stops being applicable; history and pointers are kept."""

    if reason not in OWNER_INVALIDATION_REASONS:
        raise AnalysisRuleViolation("only owner source/context/intent/consent changes invalidate")
    if head.accepted_status is AcceptedStatus.STALE:
        raise AnalysisRuleViolation("analysis is already stale")
    return replace(
        head,
        analysis_revision=head.analysis_revision + 1,
        accepted_status=AcceptedStatus.STALE,
        status_reason=str(reason),
        updated_at=now,
    )


def is_applicable(head: AnalysisHead, *, current_context_revision: int,
                  current_input_hash: str | None) -> bool:
    """Accepted, pinned context still current and the snapshot still resolves identically."""

    return (
        head.accepted_status is AcceptedStatus.ACCEPTED
        and head.context_revision == current_context_revision
        and current_input_hash == head.lineage.input_hash
    )


@dataclass(frozen=True, slots=True)
class InvalidationIntent:
    """Versioned downstream notice written with the mutation; delivery is out of C1 scope."""

    event_id: str
    organization_id: str
    analysis_id: str
    previous_revision: int
    analysis_revision: int
    reason: InvalidationReason
    correction_ref: str | None
    occurred_at: datetime


def invalidation_event_id(analysis_id: str, analysis_revision: int, reason: str) -> str:
    digest = canonical_sha256(
        {"analysis_id": analysis_id, "analysis_revision": analysis_revision, "reason": reason}
    )
    return f"inv_{digest[:32]}"


def analysis_etag(analysis_id: str, analysis_revision: int) -> str:
    return f'"analysis:{analysis_id}:{analysis_revision}"'


def parse_analysis_etag(value: str, analysis_id: str) -> int | None:
    """Revision of an ``analysis`` family ETag for this id; anything else is ``None``."""

    match = _ETAG.match(value.strip())
    if match is None or match.group(1) != analysis_id:
        return None
    return int(match.group(2))


__all__ = [
    "ANALYSIS_CONTRACT_VERSION",
    "INTENDED_OBJECTS_MAX",
    "LONG_TEXT_MAX",
    "OBSERVATION_COLLECTION_MAX",
    "OBSERVATION_REF_MAX",
    "OWNER_INVALIDATION_REASONS",
    "SHORT_TEXT_MAX",
    "SUPPORTED_RENDER_MEDIA_TYPES",
    "VISION_ANALYSIS_JOB_TYPE",
    "AcceptedStatus",
    "ActionObservation",
    "ActorRef",
    "ActorRole",
    "AdmissionReceipt",
    "AmbiguousRegionObservation",
    "AnalysisHead",
    "AnalysisLineage",
    "AnalysisRuleViolation",
    "AnalysisScope",
    "AssistancePin",
    "CheckpointBinding",
    "CorrectionKind",
    "EntityObservation",
    "EvidenceKind",
    "InvalidationIntent",
    "InvalidationReason",
    "JobLineageView",
    "LexicalOutcome",
    "LineageVerdict",
    "MeaningCorrection",
    "MeaningStatus",
    "ModerationOutcome",
    "ObjectCandidate",
    "ObservationClaim",
    "ObservationEvidence",
    "ObservedLabel",
    "OriginalObservation",
    "ProviderContextMode",
    "ProviderResultRecord",
    "RelationObservation",
    "RenderBinding",
    "SourceSnapshot",
    "SourceVerdict",
    "ThemeObservation",
    "Uncertainty",
    "VisionObservation",
    "analysis_etag",
    "apply_correction",
    "check_input_hash",
    "check_lineage",
    "derive_uncertainty",
    "document_sha256",
    "invalidation_event_id",
    "is_applicable",
    "job_scope_matches",
    "mark_stale",
    "new_head",
    "new_observation",
    "normalize_intended_objects",
    "normalize_long_text",
    "normalize_short_text",
    "object_candidates",
    "observation_bounds_violation",
    "observation_hash",
    "parse_analysis_etag",
    "provider_result_ref",
    "require_confidence",
]
