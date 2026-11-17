"""BE2-04 SK1 SketchProposal domain (DATA-23 producer, offline component, fixtures only).

Pure rules: proposal versions and states, level/output rules, output validation, currency
verdicts, decision tokens and canonical hashes. No framework, provider, storage or BE2-03
types. Approval, moderation ``passed`` and Child responses are never produced here.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import StrEnum
from hashlib import sha256

from sketch2life.domain.ai_jobs.model import require_aware
from sketch2life.domain.vision_context import strict_canonical_sha256

SKETCH_CONTRACT_VERSION = "0.1-candidate"
SKETCH_JOB_TYPE = "sketch_generation"
CONTENT_RULES_VERSION = "sketch-proposal-content-v1"
GENERATION_RULES_VERSION = "sketch-generation-input-v1"
FIXTURE_POLICY_STATUS = "FIXTURE_ONLY_NOT_ADOPTED"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
RESULT_DOCUMENT_MEDIA_TYPE = "application/json"

_REF = re.compile(r"^[A-Za-z0-9_.:-]{1,120}$")
_SHA = re.compile(r"^[0-9a-f]{64}$")
_CONTROL = re.compile(r"[\x00-\x09\x0b-\x1f\x7f-\x9f]")


class SketchRuleViolation(ValueError):
    """A proposal invariant or transition rule was broken."""


class InvalidSketchTransition(SketchRuleViolation):
    pass


class PipelineState(StrEnum):
    """Exact DATA-23 ``pipeline_state`` enum; 04 never writes approved/rejected."""

    REQUESTED = "requested"
    ANALYZING = "analyzing"
    PENDING_TEACHER_REVIEW = "pending_teacher_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    BLOCKED_UNSAFE = "blocked_unsafe"
    CANCELLED = "cancelled"
    STALE = "stale"
    FAILED = "failed"


ACTIVE_STATES = frozenset({PipelineState.REQUESTED, PipelineState.ANALYZING})
INVALIDATABLE_STATES = frozenset({PipelineState.REQUESTED, PipelineState.ANALYZING,
                                  PipelineState.PENDING_TEACHER_REVIEW})
REVIEW_OWNED_STATES = frozenset({PipelineState.APPROVED, PipelineState.REJECTED})


class ModerationState(StrEnum):
    """DATA-20 enum; 04 writes only not_applicable, pending and blocked."""

    NOT_APPLICABLE = "not_applicable"
    PENDING = "pending"
    PASSED = "passed"
    BLOCKED = "blocked"


class DisplayMode(StrEnum):
    SIDE_REFERENCE = "side_reference"
    OVERLAY = "overlay"


class PartRequirement(StrEnum):
    REQUIRED = "required"
    OPTIONAL = "optional"
    FORBIDDEN = "forbidden"


class HandoffKind(StrEnum):
    ANALYSIS = "analysis"
    CACHE_HIT = "cache_hit"


class LevelSource(StrEnum):
    REQUEST = "request"
    REVISION = "revision"


class StatusReason(StrEnum):
    """Closed reason tokens (TC-02, TC-23)."""

    CANCELLED_BY_TEACHER = "CANCELLED_BY_TEACHER"
    CONSENT_REVOKED = "CONSENT_REVOKED"
    SESSION_ENDED = "SESSION_ENDED"
    TURN_REVOKED = "TURN_REVOKED"
    CANVAS_RESTORED = "CANVAS_RESTORED"
    CONTEXT_CHANGED = "CONTEXT_CHANGED"
    SOURCE_CHANGED = "SOURCE_CHANGED"
    MEANING_CHANGED = "MEANING_CHANGED"
    AUDIENCE_CHANGED = "AUDIENCE_CHANGED"
    ANALYSIS_NOT_APPLICABLE = "ANALYSIS_NOT_APPLICABLE"
    POLICY_CHANGED = "POLICY_CHANGED"
    POLICY_UNRESOLVED = "POLICY_UNRESOLVED"
    POLICY_DISABLED = "POLICY_DISABLED"
    LEVEL_NOT_ALLOWED = "LEVEL_NOT_ALLOWED"
    SCHEDULE_REFUSED = "SCHEDULE_REFUSED"
    JOB_CANCELLED = "JOB_CANCELLED"
    UNSAFE_CONTENT = "UNSAFE_CONTENT"
    PROVIDER_TIMEOUT = "PROVIDER_TIMEOUT"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    OUTPUT_MALFORMED = "OUTPUT_MALFORMED"
    ARTIFACT_QUARANTINED = "ARTIFACT_QUARANTINED"
    SUPERSEDED_BY_REVISION = "SUPERSEDED_BY_REVISION"


FAILURE_REASONS: Mapping[str, StatusReason] = {
    "PROVIDER_TIMEOUT": StatusReason.PROVIDER_TIMEOUT,
    "PROVIDER_UNAVAILABLE": StatusReason.PROVIDER_UNAVAILABLE,
    "PROVIDER_ERROR": StatusReason.PROVIDER_ERROR,
    "OUTPUT_MALFORMED": StatusReason.OUTPUT_MALFORMED,
}


def _ref(value: object, name: str) -> str:
    if not isinstance(value, str) or not _REF.fullmatch(value):
        raise SketchRuleViolation(f"{name} must be an opaque id")
    return value


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or not _SHA.fullmatch(value):
        raise SketchRuleViolation(f"{name} must be lowercase sha256 hex")
    return value


# ------------------------------------------------------------------- policy (fixture)
@dataclass(frozen=True, slots=True)
class LevelOutputRule:
    """Fixture rule for one opaque level token; never an adopted taxonomy (Q2)."""

    level: str
    display_mode: DisplayMode
    text: PartRequirement
    asset: PartRequirement

    def __post_init__(self) -> None:
        _ref(self.level, "level")
        if self.text is PartRequirement.FORBIDDEN and self.asset is PartRequirement.FORBIDDEN:
            raise SketchRuleViolation("a level rule must allow text or a reference asset")

    def canonical(self) -> dict[str, object]:
        return {"level": self.level, "display_mode": str(self.display_mode),
                "text": str(self.text), "asset": str(self.asset)}


@dataclass(frozen=True, slots=True)
class SketchPolicySnapshot:
    """Consumer view of a BE2-14-owned policy (proposal); every value is a fixture."""

    policy_id: str
    version: str
    status: str
    enabled: bool
    purpose_code: str
    rules: Mapping[str, LevelOutputRule]
    asset_media_types: frozenset[str]
    asset_max_bytes: int
    text_max_chars: int
    generator_profile_ref: str

    def __post_init__(self) -> None:
        for name in ("policy_id", "version", "purpose_code", "generator_profile_ref"):
            _ref(getattr(self, name), name)
        if self.asset_max_bytes < 1 or self.text_max_chars < 1:
            raise SketchRuleViolation("policy bounds must be positive")
        for level, rule in self.rules.items():
            if rule.level != level:
                raise SketchRuleViolation("rule key must equal its level")

    def rule_for(self, level: str) -> LevelOutputRule | None:
        return self.rules.get(level)

    def ref(self) -> dict[str, object]:
        return {"policy_id": self.policy_id, "version": self.version, "status": self.status}


def policy_verdict(policy: SketchPolicySnapshot | None, *, level: str, purpose_code: str,
                   opening: bool) -> StatusReason | None:
    """Open uses specific reasons; a later re-check reports POLICY_CHANGED."""

    if policy is None or policy.purpose_code != purpose_code:
        return StatusReason.POLICY_UNRESOLVED if opening else StatusReason.POLICY_CHANGED
    if not policy.enabled:
        return StatusReason.POLICY_DISABLED if opening else StatusReason.POLICY_CHANGED
    if policy.rule_for(level) is None:
        return StatusReason.LEVEL_NOT_ALLOWED if opening else StatusReason.POLICY_CHANGED
    return None


# ------------------------------------------------------------------- handoff binding
@dataclass(frozen=True, slots=True)
class MeaningBasis:
    """What of the analysis meaning is projected to the generator (TC-07)."""

    state: str
    confirmation_ref: str | None
    concepts: tuple[str, ...]

    def projected_concepts(self) -> tuple[str, ...]:
        return self.concepts if self.state == "confirmed" else ()

    def digest(self) -> str:
        return strict_canonical_sha256({
            "state": self.state,
            "confirmation_ref": self.confirmation_ref,
            "concepts": list(self.projected_concepts()),
        })


@dataclass(frozen=True, slots=True)
class SourcePin:
    snapshot_ref: str
    checkpoint_id: str
    document_epoch: int
    server_sequence: int
    checkpoint_checksum: str
    render_ref: str
    render_sha256: str
    render_media_type: str
    admission_receipt_id: str
    input_hash: str

    def __post_init__(self) -> None:
        for name in ("snapshot_ref", "checkpoint_id", "render_ref", "admission_receipt_id"):
            _ref(getattr(self, name), name)
        for name in ("checkpoint_checksum", "render_sha256", "input_hash"):
            _sha(getattr(self, name), name)


@dataclass(frozen=True, slots=True)
class HandoffBinding:
    """Everything 04 pins from one BE2-03 analysis_ready request (plan §3.2, N01)."""

    assistance_id: str
    request_revision: int
    handoff_kind: HandoffKind
    cache_source_assistance_id: str | None
    analysis_id: str
    analysis_revision: int
    vision_job_id: str
    vision_attempt_id: str
    organization_id: str
    class_id: str
    session_id: str
    canvas_id: str
    group_id: str | None
    target_kind: str
    target_ref: str
    audience: tuple[str, ...]
    roster_revision: int | None
    contributor_participant_id: str
    purpose_code: str
    source: SourcePin
    context_revision: int
    requested_level: str
    request_policy_id: str
    request_policy_version: str
    requester_principal_id: str
    requester_kind: str
    assistance_context_digest: str
    meaning: MeaningBasis

    def __post_init__(self) -> None:
        for name in ("assistance_id", "analysis_id", "vision_job_id", "vision_attempt_id",
                     "organization_id", "class_id", "session_id", "canvas_id", "purpose_code",
                     "requested_level", "requester_principal_id"):
            _ref(getattr(self, name), name)
        if self.request_revision < 1 or self.analysis_revision < 1 or self.context_revision < 0:
            raise SketchRuleViolation("binding revisions are invalid")
        if not self.audience or len(set(self.audience)) != len(self.audience):
            raise SketchRuleViolation("audience must be non-empty and unique")
        if self.contributor_participant_id not in self.audience:
            raise SketchRuleViolation("contributor must be part of the audience")
        if (self.handoff_kind is HandoffKind.CACHE_HIT) != (
            self.cache_source_assistance_id is not None
        ):
            raise SketchRuleViolation("only a cache-hit handoff names a cache source")
        _sha(self.assistance_context_digest, "assistance_context_digest")


@dataclass(frozen=True, slots=True)
class CurrentFacts:
    """Current owner/03/02 facts read for one binding (never cached)."""

    handoff_unchanged: bool
    session_active: bool
    consent_ok: bool
    audience_unchanged: bool
    context_revision: int | None
    source_input_hash: str | None
    analysis_accepted: bool
    meaning: MeaningBasis | None


def current_verdict(binding: HandoffBinding, current: CurrentFacts) -> StatusReason | None:
    """Ordered currency check of a pinned binding (plan §7.2, TC-07)."""

    if not current.handoff_unchanged:
        return StatusReason.CONTEXT_CHANGED
    if not current.session_active:
        return StatusReason.SESSION_ENDED
    if not current.consent_ok:
        return StatusReason.CONSENT_REVOKED
    if not current.audience_unchanged:
        return StatusReason.AUDIENCE_CHANGED
    if current.context_revision != binding.context_revision:
        return StatusReason.CONTEXT_CHANGED
    if current.source_input_hash != binding.source.input_hash:
        return StatusReason.SOURCE_CHANGED
    if (not current.analysis_accepted or current.meaning is None
            or current.meaning.state == "not_applicable"):
        return StatusReason.ANALYSIS_NOT_APPLICABLE
    if current.meaning.digest() != binding.meaning.digest():
        return StatusReason.MEANING_CHANGED
    return None


# ------------------------------------------------------------------- decision token
@dataclass(frozen=True, slots=True)
class DecisionToken:
    """Committed epochs (owner, analysis, policy, artifact refs) + the pinned ref-set id."""

    organization_id: str
    epochs: tuple[tuple[str, int], ...]
    ref_set_id: str


def ref_set_id(proposal_id: str, record_version: int, version: int, staged_key: str | None,
               refs: tuple[str, ...]) -> str:
    """TC-22: identity of the artifact refs a decision depends on."""

    return strict_canonical_sha256({
        "proposal_id": proposal_id,
        "record_version": record_version,
        "version": version,
        "staged_key": staged_key,
        "refs": sorted(refs),
    })


# ------------------------------------------------------------------- outputs
@dataclass(frozen=True, slots=True)
class OutputPart:
    """Untrusted generator part; only two kinds are valid (no drawing commands)."""

    kind: str
    text: str | None = None
    body: bytes | None = field(default=None, repr=False)
    media_type: str | None = None
    reported_sha256: str | None = None


@dataclass(frozen=True, slots=True)
class ValidatedOutput:
    text: str | None
    asset_body: bytes | None = field(repr=False)
    asset_media_type: str | None
    asset_sha256: str | None


def normalize_text(value: str, limit: int) -> str | None:
    """NFC, no control characters, non-empty, bounded; never truncated silently."""

    text = unicodedata.normalize("NFC", value).strip()
    if not text or len(text) > limit or _CONTROL.search(text):
        return None
    return text


def validate_output(parts: tuple[OutputPart, ...], rule: LevelOutputRule,
                    policy: SketchPolicySnapshot, *, render_sha256: str) -> ValidatedOutput | None:
    """Exact output shape for the rule; ``None`` means OUTPUT_MALFORMED (SK-N11)."""

    texts = [p for p in parts if p.kind == "text_or_question"]
    images = [p for p in parts if p.kind == "reference_image"]
    if len(texts) + len(images) != len(parts) or len(texts) > 1 or len(images) > 1:
        return None
    if not _requirement_met(rule.text, bool(texts)) or not _requirement_met(rule.asset,
                                                                             bool(images)):
        return None
    text: str | None = None
    if texts:
        raw = texts[0].text
        if not isinstance(raw, str):
            return None
        text = normalize_text(raw, policy.text_max_chars)
        if text is None:
            return None
    body: bytes | None = None
    media_type: str | None = None
    digest: str | None = None
    if images:
        image = images[0]
        body, media_type = image.body, image.media_type
        if not isinstance(body, bytes) or media_type not in policy.asset_media_types:
            return None
        if not 0 < len(body) <= policy.asset_max_bytes:
            return None
        if media_type == "image/png" and not body.startswith(PNG_SIGNATURE):
            return None
        digest = sha256(body).hexdigest()
        if image.reported_sha256 is not None and image.reported_sha256 != digest:
            return None
        if digest == render_sha256:  # TC-15: an AI output identical to the child's source
            return None
    return ValidatedOutput(text, body, media_type, digest)


def _requirement_met(requirement: PartRequirement, present: bool) -> bool:
    if requirement is PartRequirement.REQUIRED:
        return present
    if requirement is PartRequirement.FORBIDDEN:
        return not present
    return True


# ------------------------------------------------------------------- versions
@dataclass(frozen=True, slots=True)
class AssetRef:
    artifact_ref: str
    sha256: str
    media_type: str
    byte_size: int

    def canonical(self) -> dict[str, object]:
        return {"ref": self.artifact_ref, "sha256": self.sha256, "media_type": self.media_type,
                "byte_size": self.byte_size}


@dataclass(frozen=True, slots=True)
class ProducerRef:
    adapter_id: str
    model_profile_version: str
    configuration_version: str
    evidence_kind: str

    def canonical(self) -> dict[str, object]:
        return {"adapter_id": self.adapter_id,
                "model_profile_version": self.model_profile_version,
                "configuration_version": self.configuration_version}


@dataclass(frozen=True, slots=True)
class PromotedOutput:
    job_id: str
    attempt_id: str
    text: str | None
    asset: AssetRef | None
    result_document: AssetRef
    producer: ProducerRef
    content_sha256: str

    def refs(self) -> tuple[str, ...]:
        refs = [self.result_document.artifact_ref]
        if self.asset is not None:
            refs.append(self.asset.artifact_ref)
        return tuple(refs)


@dataclass(frozen=True, slots=True)
class ProposalVersion:
    version: int
    level: str
    level_source: LevelSource
    level_source_ref: str | None
    rule: LevelOutputRule
    generation_digest: str
    policy_id: str
    policy_version: str
    policy_status: str
    generator_profile_ref: str
    pipeline_state: PipelineState
    moderation_state: ModerationState
    status_reason: StatusReason | None
    create_key: str
    job_id: str | None = None
    cleanup_job_ids: tuple[str, ...] = ()
    promoted: PromotedOutput | None = None

    def __post_init__(self) -> None:
        if self.version < 1:
            raise SketchRuleViolation("proposal_version starts at 1")
        if self.rule.level != self.level:
            raise SketchRuleViolation("version rule must belong to its level")
        if (self.level_source is LevelSource.REVISION) != (self.level_source_ref is not None):
            raise SketchRuleViolation("only a revision version names its revision receipt")
        terminal_needs_reason = self.pipeline_state in {
            PipelineState.CANCELLED, PipelineState.STALE, PipelineState.FAILED,
            PipelineState.BLOCKED_UNSAFE}
        if terminal_needs_reason != (self.status_reason is not None):
            raise SketchRuleViolation("stale/cancelled/failed/blocked need a reason, only they")
        if self.pipeline_state in REVIEW_OWNED_STATES:
            raise SketchRuleViolation("approved/rejected are written by BE2-05 only")
        if self.moderation_state is ModerationState.PASSED:
            raise SketchRuleViolation("moderation passed is decided by BE2-05 only")
        if (self.pipeline_state is PipelineState.PENDING_TEACHER_REVIEW) and self.promoted is None:
            raise SketchRuleViolation("a reviewable version has promoted output")


@dataclass(frozen=True, slots=True)
class SketchProposal:
    proposal_id: str
    organization_id: str
    record_version: int
    review_revision: int
    binding: HandoffBinding
    policy_id: str
    policy_version: str
    policy_status: str
    generator_profile_ref: str
    versions: tuple[ProposalVersion, ...]
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        _ref(self.proposal_id, "proposal_id")
        if self.record_version < 1 or self.review_revision < 1:
            raise SketchRuleViolation("record_version and review_revision start at 1")
        if not self.versions or [v.version for v in self.versions] != list(
            range(1, len(self.versions) + 1)
        ):
            raise SketchRuleViolation("versions are contiguous from 1")
        first = self.versions[0]
        if first.level_source is not LevelSource.REQUEST or (
            first.level != self.binding.requested_level
        ):
            raise SketchRuleViolation("version 1 level equals the BE2-03 requested level")
        require_aware(self.created_at, "created_at")
        require_aware(self.updated_at, "updated_at")

    @property
    def current(self) -> ProposalVersion:
        return self.versions[-1]

    def etag(self) -> str:
        return sketch_etag(self.proposal_id, self.current.version, self.review_revision)


def sketch_etag(proposal_id: str, version: int, review_revision: int) -> str:
    return f'"sketch-proposal:{proposal_id}:{version}:{review_revision}"'


def create_key(proposal_id: str, version: int) -> str:
    return f"sketch:{proposal_id}:{version}:generate"


def generation_digest(binding: HandoffBinding, *, proposal_id: str, version: int,
                      rule: LevelOutputRule, policy_ref: Mapping[str, object],
                      generator_profile_ref: str) -> str:
    """TC-05: the sketch job ``RequestRef.input_hash`` (effective level of this version)."""

    return strict_canonical_sha256({
        "rules": GENERATION_RULES_VERSION,
        "proposal_id": proposal_id,
        "proposal_version": version,
        "source_input_hash": binding.source.input_hash,
        "render_sha256": binding.source.render_sha256,
        "assistance_level": rule.level,
        "display_mode": str(rule.display_mode),
        "output_rule": rule.canonical(),
        "meaning_basis_digest": binding.meaning.digest(),
        "policy_ref": dict(policy_ref),
        "generator_profile_ref": generator_profile_ref,
    })


def content_sha256(proposal: SketchProposal, version: ProposalVersion, *, text: str | None,
                   asset: AssetRef | None, producer: ProducerRef) -> str:
    """TC-04: exact reviewable content identity (DATA-24 target_hash)."""

    binding = proposal.binding
    return strict_canonical_sha256({
        "rules": CONTENT_RULES_VERSION,
        "proposal_id": proposal.proposal_id,
        "proposal_version": version.version,
        "assistance_id": binding.assistance_id,
        "request_revision": binding.request_revision,
        "source_snapshot_ref": binding.source.snapshot_ref,
        "source_input_hash": binding.source.input_hash,
        "context_revision": binding.context_revision,
        "assistance_level": version.level,
        "display_mode": str(version.rule.display_mode),
        "text_or_question": text,
        "asset": None if asset is None else asset.canonical(),
        "editable_bounds": None,
        "analysis_ref": {"analysis_id": binding.analysis_id,
                         "analysis_revision": binding.analysis_revision},
        "producer_ref": producer.canonical(),
        "policy_ref": {"policy_id": version.policy_id, "version": version.policy_version,
                       "status": version.policy_status},
    })


# ------------------------------------------------------------------- transitions
def open_proposal(*, proposal_id: str, binding: HandoffBinding, policy: SketchPolicySnapshot,
                  now: datetime, refusal: StatusReason | None) -> SketchProposal:
    """Version 1 at the BE2-03 requested level; a traceable stale/failed record on refusal."""

    rule = policy.rule_for(binding.requested_level)
    if rule is None:  # a refused open still needs a version shape for the record
        if refusal is None:
            raise SketchRuleViolation("an accepted open needs a rule for the requested level")
        rule = LevelOutputRule(binding.requested_level, DisplayMode.SIDE_REFERENCE,
                               PartRequirement.OPTIONAL, PartRequirement.OPTIONAL)
    digest = generation_digest(binding, proposal_id=proposal_id, version=1, rule=rule,
                               policy_ref=policy.ref(),
                               generator_profile_ref=policy.generator_profile_ref)
    version = ProposalVersion(
        1, binding.requested_level, LevelSource.REQUEST, None, rule, digest, policy.policy_id,
        policy.version, policy.status, policy.generator_profile_ref, _open_state(refusal),
        ModerationState.NOT_APPLICABLE, refusal, create_key(proposal_id, 1))
    return SketchProposal(proposal_id, binding.organization_id, 1, 1, binding, policy.policy_id,
                          policy.version, policy.status, policy.generator_profile_ref,
                          (version,), now, now)


def _open_state(refusal: StatusReason | None) -> PipelineState:
    if refusal is None:
        return PipelineState.REQUESTED
    if refusal in {StatusReason.POLICY_UNRESOLVED, StatusReason.POLICY_DISABLED,
                   StatusReason.LEVEL_NOT_ALLOWED}:
        return PipelineState.FAILED
    return PipelineState.STALE


def refused_open_proposal(*, proposal_id: str, binding: HandoffBinding, now: datetime,
                          refusal: StatusReason) -> SketchProposal:
    """Traceable refused record when no policy is resolvable at all."""

    rule = LevelOutputRule(binding.requested_level, DisplayMode.SIDE_REFERENCE,
                           PartRequirement.OPTIONAL, PartRequirement.OPTIONAL)
    policy_ref = {"policy_id": "unresolved", "version": "0", "status": "UNRESOLVED"}
    digest = generation_digest(binding, proposal_id=proposal_id, version=1, rule=rule,
                               policy_ref=policy_ref, generator_profile_ref="unresolved")
    version = ProposalVersion(
        1, binding.requested_level, LevelSource.REQUEST, None, rule, digest,
        "unresolved", "0", "UNRESOLVED", "unresolved", _open_state(refusal),
        ModerationState.NOT_APPLICABLE, refusal, create_key(proposal_id, 1))
    return SketchProposal(proposal_id, binding.organization_id, 1, 1, binding, "unresolved",
                          "0", "UNRESOLVED", "unresolved", (version,), now, now)


def _with_current(proposal: SketchProposal, version: ProposalVersion, now: datetime, *,
                  invalidate: bool = False, versions: tuple[ProposalVersion, ...] | None = None,
                  ) -> SketchProposal:
    new_versions = versions if versions is not None else (*proposal.versions[:-1], version)
    return replace(proposal, versions=new_versions, record_version=proposal.record_version + 1,
                   review_revision=proposal.review_revision + (1 if invalidate else 0),
                   updated_at=now)


def link_job(proposal: SketchProposal, job_id: str, now: datetime) -> SketchProposal:
    current = proposal.current
    if current.pipeline_state not in ACTIVE_STATES:
        raise InvalidSketchTransition(f"cannot link a job from {current.pipeline_state}")
    if current.job_id == job_id:
        return proposal
    if current.job_id is not None:
        raise InvalidSketchTransition("version already linked to another job")
    return _with_current(proposal, replace(current, job_id=_ref(job_id, "job_id")), now)


def add_cleanup_job(proposal: SketchProposal, job_id: str, now: datetime) -> SketchProposal:
    current = proposal.current
    if job_id == current.job_id or job_id in current.cleanup_job_ids:
        return proposal
    return _with_current(proposal, replace(current,
                                           cleanup_job_ids=(*current.cleanup_job_ids, job_id)),
                         now)


def mark_analyzing(proposal: SketchProposal, job_id: str, now: datetime) -> SketchProposal:
    current = proposal.current
    if current.pipeline_state is PipelineState.ANALYZING and current.job_id == job_id:
        return proposal
    if current.pipeline_state is not PipelineState.REQUESTED:
        raise InvalidSketchTransition(f"cannot start generation from {current.pipeline_state}")
    if current.job_id not in {None, job_id}:
        raise InvalidSketchTransition("generation job is not the linked job")
    return _with_current(proposal, replace(current, pipeline_state=PipelineState.ANALYZING,
                                           job_id=job_id), now)


def terminate(proposal: SketchProposal, state: PipelineState, reason: StatusReason,
              now: datetime, *, cleanup_job_id: str | None = None) -> SketchProposal:
    """stale/failed/cancelled/blocked of the current version; invalidation bumps review."""

    current = proposal.current
    if state not in {PipelineState.STALE, PipelineState.FAILED, PipelineState.CANCELLED,
                     PipelineState.BLOCKED_UNSAFE}:
        raise InvalidSketchTransition(f"{state} is not a termination")
    allowed = INVALIDATABLE_STATES if state is PipelineState.STALE else ACTIVE_STATES
    if current.pipeline_state not in allowed:
        raise InvalidSketchTransition(f"cannot move {current.pipeline_state} to {state}")
    moderation = (ModerationState.BLOCKED if state is PipelineState.BLOCKED_UNSAFE
                  else current.moderation_state)
    cleanup_job_ids = current.cleanup_job_ids
    if cleanup_job_id is not None and cleanup_job_id not in cleanup_job_ids:
        cleanup_job_ids = (*cleanup_job_ids, _ref(cleanup_job_id, "cleanup_job_id"))
    return _with_current(proposal, replace(current, pipeline_state=state, status_reason=reason,
                                           moderation_state=moderation,
                                           cleanup_job_ids=cleanup_job_ids), now,
                         invalidate=True)


def promote(proposal: SketchProposal, output: PromotedOutput, now: datetime) -> SketchProposal:
    current = proposal.current
    if current.pipeline_state is not PipelineState.ANALYZING:
        raise InvalidSketchTransition(f"cannot promote from {current.pipeline_state}")
    if current.job_id != output.job_id:
        raise InvalidSketchTransition("promoted output belongs to another job")
    return _with_current(proposal, replace(
        current, pipeline_state=PipelineState.PENDING_TEACHER_REVIEW,
        moderation_state=ModerationState.PENDING, promoted=output), now)


def revise_level(proposal: SketchProposal, *, rule: LevelOutputRule, receipt_ref: str,
                 policy: SketchPolicySnapshot, now: datetime) -> SketchProposal:
    """Support-level revision (SK-PR03): new version at the revised level; history kept."""

    current = proposal.current
    if current.pipeline_state is not PipelineState.PENDING_TEACHER_REVIEW:
        raise InvalidSketchTransition(f"cannot revise from {current.pipeline_state}")
    superseded = replace(current, pipeline_state=PipelineState.STALE,
                         status_reason=StatusReason.SUPERSEDED_BY_REVISION)
    number = current.version + 1
    digest = generation_digest(proposal.binding, proposal_id=proposal.proposal_id,
                               version=number, rule=rule, policy_ref=policy.ref(),
                               generator_profile_ref=policy.generator_profile_ref)
    revised = ProposalVersion(
        number, rule.level, LevelSource.REVISION, _ref(receipt_ref, "receipt_ref"), rule, digest,
        policy.policy_id, policy.version, policy.status, policy.generator_profile_ref,
        PipelineState.REQUESTED, ModerationState.NOT_APPLICABLE, None,
        create_key(proposal.proposal_id, number))
    return _with_current(proposal, revised, now, invalidate=True,
                         versions=(*proposal.versions[:-1], superseded, revised))


def device_status(state: PipelineState) -> str:
    """Coarse Child view: content is never implied (DATA-23 pending projection)."""

    return "pending" if state in INVALIDATABLE_STATES else "unavailable"


# ------------------------------------------------------------------- staging
class StagedStatus(StrEnum):
    STAGED = "staged"
    PROMOTED = "promoted"
    SUPERSEDED = "superseded"


@dataclass(frozen=True, slots=True)
class StagedGeneration:
    """Attempt-keyed generation output before the C8 visibility gate (plan §7.1 C6)."""

    job_id: str
    attempt_id: str
    proposal_id: str
    version: int
    generation_digest: str
    unsafe: bool
    text: str | None
    asset: AssetRef | None
    result_document: AssetRef
    producer: ProducerRef
    copy_ids: tuple[str, ...]
    status: StagedStatus = StagedStatus.STAGED

    @property
    def key(self) -> str:
        return f"{self.job_id}:{self.attempt_id}"

    def refs(self) -> tuple[str, ...]:
        refs = [self.result_document.artifact_ref]
        if self.asset is not None:
            refs.append(self.asset.artifact_ref)
        return tuple(refs)

    def output_pairs(self) -> tuple[tuple[str, str], ...]:
        pairs = [(self.result_document.artifact_ref, self.result_document.sha256)]
        if self.asset is not None:
            pairs.append((self.asset.artifact_ref, self.asset.sha256))
        return tuple(sorted(pairs))


def event_id(proposal_id: str, version: int, event_type: str, discriminator: str) -> str:
    digest = sha256(f"{proposal_id}|{version}|{event_type}|{discriminator}".encode())
    return "sketch_evt_" + digest.hexdigest()[:24]


__all__ = [
    "ACTIVE_STATES",
    "CONTENT_RULES_VERSION",
    "FAILURE_REASONS",
    "FIXTURE_POLICY_STATUS",
    "GENERATION_RULES_VERSION",
    "INVALIDATABLE_STATES",
    "PNG_SIGNATURE",
    "RESULT_DOCUMENT_MEDIA_TYPE",
    "SKETCH_CONTRACT_VERSION",
    "SKETCH_JOB_TYPE",
    "AssetRef",
    "CurrentFacts",
    "DecisionToken",
    "DisplayMode",
    "HandoffBinding",
    "HandoffKind",
    "InvalidSketchTransition",
    "LevelOutputRule",
    "LevelSource",
    "MeaningBasis",
    "ModerationState",
    "OutputPart",
    "PartRequirement",
    "PipelineState",
    "ProducerRef",
    "PromotedOutput",
    "ProposalVersion",
    "SketchPolicySnapshot",
    "SketchProposal",
    "SketchRuleViolation",
    "SourcePin",
    "StagedGeneration",
    "StagedStatus",
    "StatusReason",
    "ValidatedOutput",
    "add_cleanup_job",
    "content_sha256",
    "create_key",
    "current_verdict",
    "device_status",
    "event_id",
    "generation_digest",
    "link_job",
    "mark_analyzing",
    "normalize_text",
    "open_proposal",
    "policy_verdict",
    "promote",
    "ref_set_id",
    "refused_open_proposal",
    "revise_level",
    "sketch_etag",
    "terminate",
    "validate_output",
]
