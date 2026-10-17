"""BE2-02 C2 typed Vision context: trusted snapshot, minimized projection and digests.

Pure rules only: no framework, contract, storage, queue or provider imports. A trusted owner
port reports one coherent ``VisionContextSnapshot`` (internal: identities, exact completed
months, consent/transfer/field-use decisions and their revisions, Teacher topic provenance).
``verify_context_snapshot`` checks it against the trusted assistance pin, the resolved source
and the existing context port, member by member, before any identity is removed.
``project_provider_context`` then builds the allowlisted provider projection (anonymous
per-member age bands, bounded Teacher topic, request enums, source image hash) and
``pin_context`` computes the two distinct digests. All of this is a 0.1/0.2-candidate component
contract with synthetic fixture facts (ASSUMED_CONTRACT), not an adopted pedagogical policy,
real transfer permission or owner sign-off.
"""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from itertools import pairwise

from sketch2life.domain.ai_jobs.completion import canonical_sha256
from sketch2life.domain.core_foundation import CoreRuleViolation, validate_age_months
from sketch2life.domain.vision_analysis import (
    AnalysisRuleViolation,
    AssistancePin,
    SourceSnapshot,
    TypedContextBinding,
    normalize_short_text,
)

TYPED_CONTEXT_CONTRACT = "VisionTypedContextV1"
TYPED_CONTEXT_VERSION = "0.1-candidate"
CANONICAL_RULES_VERSION = "vision-context-canonical-v1"
# Technical payload bound for the candidate (not a class-size rule).
CONTEXT_AUDIENCE_MAX = 64
# Provider-context field-use names. Every member must permit every field the capability
# consumes; C2 consumes all three and nothing else (Child text, Teacher feedback, confirmed
# meaning and action summaries are not fields of this contract at all).
FIELD_TEACHER_TOPIC = "teacher_topic"
FIELD_AUDIENCE_AGE_BANDS = "audience_age_bands"
FIELD_REQUEST_ENUMS = "request_enums"
PROVIDER_CONTEXT_FIELDS = (FIELD_TEACHER_TOPIC, FIELD_AUDIENCE_AGE_BANDS, FIELD_REQUEST_ENUMS)
OFFLINE_INJECTED_TRANSPORT = "offline_injected"

_REF = re.compile(r"[A-Za-z0-9_.:-]{1,120}")
_SHA256 = re.compile(r"[0-9a-f]{64}")
_BAND_LABEL = re.compile(r"[a-z0-9-]{1,40}")


class ContextRuleViolation(AnalysisRuleViolation):
    """Malformed trusted context facts; refused, never coerced or repaired."""


class RequestReason(StrEnum):
    """Candidate request enums (source-undefined; recorded in DECISIONS before code)."""

    DESCRIBE_DRAWING = "describe_drawing"
    SUPPORT_MEANING_CHECK = "support_meaning_check"


class TargetKind(StrEnum):
    WHOLE_CANVAS = "whole_canvas"
    CONTRIBUTOR_STROKES = "contributor_strokes"


class RequestedLevel(StrEnum):
    BRIEF = "brief"
    STANDARD = "standard"


class ContextCode(StrEnum):
    """Closed refusal tokens of the typed-context gate (never provider or owner text)."""

    CONTEXT_UNAVAILABLE = "CONTEXT_UNAVAILABLE"
    CONTEXT_MALFORMED = "CONTEXT_MALFORMED"
    CONTEXT_AUDIENCE_DUPLICATE = "CONTEXT_AUDIENCE_DUPLICATE"
    CONTEXT_AUDIENCE_MISMATCH = "CONTEXT_AUDIENCE_MISMATCH"
    CONTEXT_AUDIENCE_TOO_LARGE = "CONTEXT_AUDIENCE_TOO_LARGE"
    CONTEXT_SCOPE_MISMATCH = "CONTEXT_SCOPE_MISMATCH"
    CONTEXT_REQUEST_MISMATCH = "CONTEXT_REQUEST_MISMATCH"
    CONTEXT_SOURCE_MISMATCH = "CONTEXT_SOURCE_MISMATCH"
    CONTEXT_REVISION_MISMATCH = "CONTEXT_REVISION_MISMATCH"
    CONTEXT_POLICY_MISMATCH = "CONTEXT_POLICY_MISMATCH"
    CONTEXT_PORT_DISAGREEMENT = "CONTEXT_PORT_DISAGREEMENT"
    INVALID_STATE = "INVALID_STATE"
    AGE_NOT_SUPPORTED = "AGE_NOT_SUPPORTED"
    CONSENT_REQUIRED = "CONSENT_REQUIRED"
    TRANSFER_NOT_PERMITTED = "TRANSFER_NOT_PERMITTED"
    CONTEXT_FIELD_NOT_PERMITTED = "CONTEXT_FIELD_NOT_PERMITTED"


# ------------------------------------------------------------------------- value rules
def _ref(value: object, name: str) -> None:
    """Opaque ref: full-string match, so empty, newline-terminated or control refs fail."""

    if not isinstance(value, str) or not _REF.fullmatch(value):
        raise ContextRuleViolation(f"{name} must be an opaque ref")


def _optional_ref(value: object, name: str) -> None:
    if value is not None:
        _ref(value, name)


def _int(value: object, name: str, minimum: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ContextRuleViolation(f"{name} must be an integer >= {minimum}")


def _bool(value: object, name: str) -> None:
    if not isinstance(value, bool):
        raise ContextRuleViolation(f"{name} must be a boolean")


def _sha(value: object, name: str) -> None:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise ContextRuleViolation(f"{name} must be lowercase sha256 hex")


# ------------------------------------------------------------------------ age bands
@dataclass(frozen=True, slots=True)
class AgeBand:
    label: str
    min_months: int
    max_months: int

    def __post_init__(self) -> None:
        if not isinstance(self.label, str) or not _BAND_LABEL.fullmatch(self.label):
            raise ContextRuleViolation("age band label must be a short lowercase token")
        _int(self.min_months, "min_months", 0)
        _int(self.max_months, "max_months", 0)
        if self.max_months < self.min_months:
            raise ContextRuleViolation("age band bounds are inverted")


@dataclass(frozen=True, slots=True)
class AgeBandPolicy:
    """Injected band policy. It must cover the owner-confirmed eligibility window 36–155
    completed months exactly, contiguously and without overlap; ``status`` states whether it
    is adopted (the C2 fixture is not)."""

    policy_ref: str
    version: str
    status: str
    bands: tuple[AgeBand, ...]

    def __post_init__(self) -> None:
        _ref(self.policy_ref, "policy_ref")
        _ref(self.version, "policy version")
        _ref(self.status, "policy status")
        if not self.bands:
            raise ContextRuleViolation("an age band policy needs bands")
        labels = [band.label for band in self.bands]
        if len(labels) != len(set(labels)):
            raise ContextRuleViolation("age band labels must be unique")
        if self.bands[0].min_months != 36 or self.bands[-1].max_months != 155:
            raise ContextRuleViolation("age bands must cover exactly 36..155 completed months")
        for previous, current in pairwise(self.bands):
            if current.min_months != previous.max_months + 1:
                raise ContextRuleViolation("age bands must be contiguous without overlap")

    def band_for(self, completed_months: int) -> str:
        """The single band containing an authoritative completed-month age; never inferred."""

        _int(completed_months, "completed_months", 0)
        for band in self.bands:
            if band.min_months <= completed_months <= band.max_months:
                return band.label
        raise ContextRuleViolation("age outside the band policy")


FIXTURE_AGE_BAND_POLICY = AgeBandPolicy(
    policy_ref="fixture-completed-years-v1",
    version="1",
    status="FIXTURE_ONLY_NOT_PEDAGOGICALLY_ADOPTED",
    bands=tuple(
        AgeBand(f"completed-years-{years}", years * 12, years * 12 + 11)
        for years in range(3, 13)
    ),
)


# --------------------------------------------------------------------- trusted snapshot
@dataclass(frozen=True, slots=True)
class MemberContextFact:
    """One audience member's internal owner facts. Identity, exact months and consent records
    stay internal; only the derived band label can reach the provider."""

    participant_id: str
    completed_age_months: int | None
    age_provenance_ref: str
    age_revision: int
    consent_effective: bool
    consent_record_ref: str
    purpose_granted: bool
    provider_transfer_permitted: bool
    permitted_fields: frozenset[str]
    permission_revision: int

    def __post_init__(self) -> None:
        _ref(self.participant_id, "participant_id")
        if self.completed_age_months is not None:
            _int(self.completed_age_months, "completed_age_months", 0)
        _ref(self.age_provenance_ref, "age_provenance_ref")
        _int(self.age_revision, "age_revision", 1)
        _bool(self.consent_effective, "consent_effective")
        _ref(self.consent_record_ref, "consent_record_ref")
        _bool(self.purpose_granted, "purpose_granted")
        _bool(self.provider_transfer_permitted, "provider_transfer_permitted")
        if not isinstance(self.permitted_fields, frozenset) or not (
            self.permitted_fields <= set(PROVIDER_CONTEXT_FIELDS)
        ):
            raise ContextRuleViolation("permitted_fields must name known provider fields")
        _int(self.permission_revision, "permission_revision", 1)

    def canonical(self) -> dict[str, object]:
        return {
            "participant_id": self.participant_id,
            "completed_age_months": self.completed_age_months,
            "age_provenance_ref": self.age_provenance_ref,
            "age_revision": self.age_revision,
            "consent_effective": self.consent_effective,
            "consent_record_ref": self.consent_record_ref,
            "purpose_granted": self.purpose_granted,
            "provider_transfer_permitted": self.provider_transfer_permitted,
            "permitted_fields": sorted(self.permitted_fields),
            "permission_revision": self.permission_revision,
        }


@dataclass(frozen=True, slots=True)
class TeacherTopicFact:
    """Teacher-authored bounded topic with provenance; never a Child statement."""

    topic_ref: str
    topic_revision: int
    text: str
    author_role: str
    author_ref: str

    def __post_init__(self) -> None:
        _ref(self.topic_ref, "topic_ref")
        _int(self.topic_revision, "topic_revision", 1)
        try:
            normalized = normalize_short_text(self.text)
        except AnalysisRuleViolation:
            raise ContextRuleViolation("topic must be short text") from None
        if normalized != self.text:
            raise ContextRuleViolation("topic must be normalized short text")
        if self.author_role != "teacher":
            raise ContextRuleViolation("only a Teacher authors the context topic")
        _ref(self.author_ref, "author_ref")

    def canonical(self) -> dict[str, object]:
        return {
            "topic_ref": self.topic_ref,
            "topic_revision": self.topic_revision,
            "text": self.text,
            "author_role": self.author_role,
            "author_ref": self.author_ref,
        }


@dataclass(frozen=True, slots=True)
class RequestContextFact:
    """Bounded request enums from the trusted request owner; never caller-supplied text."""

    reason: RequestReason
    target_kind: TargetKind
    requested_level: RequestedLevel

    def __post_init__(self) -> None:
        if (
            not isinstance(self.reason, RequestReason)
            or not isinstance(self.target_kind, TargetKind)
            or not isinstance(self.requested_level, RequestedLevel)
        ):
            raise ContextRuleViolation("request facts must be the bounded enums")

    def canonical(self) -> dict[str, object]:
        return {
            "reason": str(self.reason),
            "target_kind": str(self.target_kind),
            "requested_level": str(self.requested_level),
        }


@dataclass(frozen=True, slots=True)
class VisionContextSnapshot:
    """One coherent internal context snapshot as reported by the trusted owner port."""

    organization_id: str
    class_id: str
    session_id: str
    canvas_id: str
    group_id: str | None
    contributor_participant_id: str
    audience_participant_ids: tuple[str, ...]
    purpose_code: str
    assistance_id: str
    request_revision: int
    snapshot_ref: str
    checkpoint_id: str
    checkpoint_checksum: str
    render_ref: str
    render_sha256: str
    context_revision: int
    session_active: bool
    members: tuple[MemberContextFact, ...]
    topic: TeacherTopicFact | None
    request: RequestContextFact
    age_band_policy_ref: str
    age_band_policy_version: str
    field_policy_revision: int
    canonical_rules_version: str

    def __post_init__(self) -> None:
        for name in ("organization_id", "class_id", "session_id", "canvas_id",
                     "contributor_participant_id", "purpose_code", "assistance_id",
                     "snapshot_ref", "checkpoint_id", "render_ref", "age_band_policy_ref",
                     "age_band_policy_version", "canonical_rules_version"):
            _ref(getattr(self, name), name)
        _optional_ref(self.group_id, "group_id")
        if not isinstance(self.audience_participant_ids, tuple) or not (
            self.audience_participant_ids
        ):
            raise ContextRuleViolation("audience_participant_ids must be a non-empty tuple")
        for participant in self.audience_participant_ids:
            _ref(participant, "audience participant")
        _int(self.request_revision, "request_revision", 1)
        _sha(self.checkpoint_checksum, "checkpoint_checksum")
        _sha(self.render_sha256, "render_sha256")
        _int(self.context_revision, "context_revision", 0)
        _bool(self.session_active, "session_active")
        if not isinstance(self.members, tuple) or not all(
            isinstance(member, MemberContextFact) for member in self.members
        ):
            raise ContextRuleViolation("members must be member facts")
        if self.topic is not None and not isinstance(self.topic, TeacherTopicFact):
            raise ContextRuleViolation("topic must be a Teacher topic fact or absent")
        if not isinstance(self.request, RequestContextFact):
            raise ContextRuleViolation("request must be the bounded request facts")
        _int(self.field_policy_revision, "field_policy_revision", 1)


@dataclass(frozen=True, slots=True)
class ContextPortFacts:
    """What the existing C1 ``AnalysisContextPort`` reports, for the coherence check."""

    context_revision: int
    consent_effective: bool
    purpose_granted: bool
    session_active: bool
    audience_age_months: tuple[tuple[str, int | None], ...]


def _duplicates(values: list[str]) -> bool:
    return len(values) != len(set(values))


def verify_context_snapshot(
    snapshot: VisionContextSnapshot,
    *,
    pin: AssistancePin,
    source: SourceSnapshot,
    policy: AgeBandPolicy,
    port: ContextPortFacts,
    expected_context_revision: int | None,
) -> ContextCode | None:
    """Ordered typed-context gate; ``None`` means every binding and every member passed.

    Duplicates are rejected before any dict/set conversion; every member is checked
    individually before identity is removed. ``expected_context_revision`` is the pinned
    revision before the call; after the call it is ``None`` and revision movement is judged by
    the caller as staleness instead of a refusal."""

    scope = pin.scope
    member_ids = [member.participant_id for member in snapshot.members]
    port_ids = [participant for participant, _ in port.audience_age_months]
    if (
        _duplicates(list(snapshot.audience_participant_ids))
        or _duplicates(member_ids)
        or _duplicates(list(scope.audience_participant_ids))
        or _duplicates(port_ids)
    ):
        return ContextCode.CONTEXT_AUDIENCE_DUPLICATE
    if len(scope.audience_participant_ids) > CONTEXT_AUDIENCE_MAX:
        return ContextCode.CONTEXT_AUDIENCE_TOO_LARGE
    expected_audience = sorted(scope.audience_participant_ids)
    if sorted(snapshot.audience_participant_ids) != expected_audience or (
        sorted(member_ids) != expected_audience
    ):
        return ContextCode.CONTEXT_AUDIENCE_MISMATCH
    if (
        snapshot.organization_id != scope.organization_id
        or snapshot.class_id != scope.class_id
        or snapshot.session_id != scope.session_id
        or snapshot.canvas_id != scope.canvas_id
        or snapshot.group_id != scope.group_id
        or snapshot.contributor_participant_id != scope.contributor_participant_id
        or snapshot.purpose_code != scope.purpose_code
    ):
        return ContextCode.CONTEXT_SCOPE_MISMATCH
    if (
        snapshot.assistance_id != pin.assistance_id
        or snapshot.request_revision != pin.request_revision
        or snapshot.snapshot_ref != pin.input_snapshot_ref
    ):
        return ContextCode.CONTEXT_REQUEST_MISMATCH
    if (
        snapshot.snapshot_ref != source.snapshot_ref
        or snapshot.checkpoint_id != source.checkpoint.checkpoint_id
        or snapshot.checkpoint_checksum != source.checkpoint.checksum_sha256
        or snapshot.render_ref != source.render.render_ref
        or snapshot.render_sha256 != source.render.render_sha256
    ):
        return ContextCode.CONTEXT_SOURCE_MISMATCH
    if (
        snapshot.age_band_policy_ref != policy.policy_ref
        or snapshot.age_band_policy_version != policy.version
        or snapshot.canonical_rules_version != CANONICAL_RULES_VERSION
    ):
        return ContextCode.CONTEXT_POLICY_MISMATCH
    if expected_context_revision is not None and (
        snapshot.context_revision != expected_context_revision
    ):
        return ContextCode.CONTEXT_REVISION_MISMATCH
    if not snapshot.session_active:
        return ContextCode.INVALID_STATE
    # Each member individually, before any identity is dropped from the projection.
    for member in snapshot.members:
        months = member.completed_age_months
        if months is None:
            return ContextCode.AGE_NOT_SUPPORTED
        try:
            validate_age_months(months)
            policy.band_for(months)
        except (CoreRuleViolation, ContextRuleViolation):
            return ContextCode.AGE_NOT_SUPPORTED
        if not member.consent_effective or not member.purpose_granted:
            return ContextCode.CONSENT_REQUIRED
        if not member.provider_transfer_permitted:
            return ContextCode.TRANSFER_NOT_PERMITTED
        if not set(PROVIDER_CONTEXT_FIELDS) <= member.permitted_fields:
            return ContextCode.CONTEXT_FIELD_NOT_PERMITTED
    # The old and new owner ports must describe the same facts; any disagreement refuses.
    port_ages = dict(port.audience_age_months)
    member_ages = {m.participant_id: m.completed_age_months for m in snapshot.members}
    if (
        port.context_revision != snapshot.context_revision
        or port.session_active != snapshot.session_active
        or port.consent_effective != all(m.consent_effective for m in snapshot.members)
        or port.purpose_granted != all(m.purpose_granted for m in snapshot.members)
        or port_ages != member_ages
    ):
        return ContextCode.CONTEXT_PORT_DISAGREEMENT
    return None


# ---------------------------------------------------------------- provider projection
@dataclass(frozen=True, slots=True)
class ProviderContextProjection:
    """The only typed context a provider may receive (``VisionTypedContextV1``): no member,
    profile, actor, device or grant id, no exact months, consent records, Child text,
    feedback or action history. ``audience_age_bands`` keeps one label per member, sorted."""

    context_revision: int
    teacher_topic: str | None
    audience_age_bands: tuple[str, ...]
    age_band_policy_ref: str
    age_band_policy_version: str
    request_reason: RequestReason
    target_kind: TargetKind
    requested_level: RequestedLevel
    source_image_sha256: str

    def __post_init__(self) -> None:
        _int(self.context_revision, "context_revision", 0)
        if self.teacher_topic is not None and (
            normalize_short_text(self.teacher_topic) != self.teacher_topic
        ):
            raise ContextRuleViolation("topic must be normalized short text")
        if not self.audience_age_bands or len(self.audience_age_bands) > CONTEXT_AUDIENCE_MAX:
            raise ContextRuleViolation("one age band per audience member is required")
        if list(self.audience_age_bands) != sorted(self.audience_age_bands) or not all(
            _BAND_LABEL.fullmatch(label) for label in self.audience_age_bands
        ):
            raise ContextRuleViolation("age bands are sorted short labels")
        _ref(self.age_band_policy_ref, "age_band_policy_ref")
        _ref(self.age_band_policy_version, "age_band_policy_version")
        _sha(self.source_image_sha256, "source_image_sha256")

    def canonical(self) -> dict[str, object]:
        """Exactly the ``VisionTypedContextV1`` wire document (allowlist, no dataclass dump)."""

        return {
            "contract_name": TYPED_CONTEXT_CONTRACT,
            "contract_version": TYPED_CONTEXT_VERSION,
            "context_revision": self.context_revision,
            "teacher_topic": self.teacher_topic,
            "audience_age_bands": list(self.audience_age_bands),
            "age_band_policy_ref": self.age_band_policy_ref,
            "age_band_policy_version": self.age_band_policy_version,
            "request_reason": str(self.request_reason),
            "target_kind": str(self.target_kind),
            "requested_level": str(self.requested_level),
            "source_image_sha256": self.source_image_sha256,
        }


def project_provider_context(
    snapshot: VisionContextSnapshot, policy: AgeBandPolicy
) -> ProviderContextProjection:
    """Allowlisted projection of an already verified snapshot. No mean/aggregate age."""

    bands: list[str] = []
    for member in snapshot.members:
        if member.completed_age_months is None:
            raise ContextRuleViolation("an unverified member cannot be projected")
        bands.append(policy.band_for(member.completed_age_months))
    return ProviderContextProjection(
        context_revision=snapshot.context_revision,
        teacher_topic=None if snapshot.topic is None else snapshot.topic.text,
        audience_age_bands=tuple(sorted(bands)),
        age_band_policy_ref=policy.policy_ref,
        age_band_policy_version=policy.version,
        request_reason=snapshot.request.reason,
        target_kind=snapshot.request.target_kind,
        requested_level=snapshot.request.requested_level,
        source_image_sha256=snapshot.render_sha256,
    )


# ------------------------------------------------------------------------- digests
def _strict(value: object, path: str = "$") -> None:
    """Only JSON-native values; floats (incl. NaN/inf) are not part of a context document."""

    if value is None or isinstance(value, bool | str):
        return
    if isinstance(value, int):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ContextRuleViolation(f"{path}: non-finite number")
        raise ContextRuleViolation(f"{path}: context documents carry no floats")
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ContextRuleViolation(f"{path}: keys must be strings")
            _strict(item, f"{path}.{key}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _strict(item, f"{path}[{index}]")
        return
    raise ContextRuleViolation(f"{path}: unsupported value type")


def strict_canonical_sha256(document: Mapping[str, object]) -> str:
    """SHA256 of the foundation canonical JSON (NFC, sorted keys, compact) after a strict
    type walk; malformed values are refused, never stringified."""

    _strict(document)
    return canonical_sha256(document)


def payload_digest(projection: ProviderContextProjection) -> str:
    """Independently recomputable from the ``VisionTypedContextV1`` document alone."""

    return strict_canonical_sha256(projection.canonical())


def context_digest(snapshot: VisionContextSnapshot, payload_sha256: str) -> str:
    """Internal binding digest. Excludes itself, execution/observation time and correlation
    ids; members are sorted by id so reordering is stable, duplicates refuse first."""

    _sha(payload_sha256, "payload_digest")
    member_ids = [member.participant_id for member in snapshot.members]
    if _duplicates(member_ids) or _duplicates(list(snapshot.audience_participant_ids)):
        raise ContextRuleViolation("duplicate audience facts cannot be hashed")
    body: dict[str, object] = {
        "canonical_rules_version": snapshot.canonical_rules_version,
        "binding": {
            "organization_id": snapshot.organization_id,
            "class_id": snapshot.class_id,
            "session_id": snapshot.session_id,
            "canvas_id": snapshot.canvas_id,
            "group_id": snapshot.group_id,
            "contributor_participant_id": snapshot.contributor_participant_id,
            "audience_participant_ids": sorted(snapshot.audience_participant_ids),
            "purpose_code": snapshot.purpose_code,
            "assistance_id": snapshot.assistance_id,
            "request_revision": snapshot.request_revision,
            "snapshot_ref": snapshot.snapshot_ref,
            "checkpoint_id": snapshot.checkpoint_id,
            "checkpoint_checksum": snapshot.checkpoint_checksum,
            "render_ref": snapshot.render_ref,
            "render_sha256": snapshot.render_sha256,
        },
        "context_revision": snapshot.context_revision,
        "session_active": snapshot.session_active,
        "members": [
            member.canonical()
            for member in sorted(snapshot.members, key=lambda m: m.participant_id)
        ],
        "teacher_topic": None if snapshot.topic is None else snapshot.topic.canonical(),
        "request": snapshot.request.canonical(),
        "age_band_policy": {
            "policy_ref": snapshot.age_band_policy_ref,
            "version": snapshot.age_band_policy_version,
        },
        "field_policy_revision": snapshot.field_policy_revision,
        "payload_digest": payload_sha256,
    }
    return strict_canonical_sha256(body)


@dataclass(frozen=True, slots=True)
class ProviderTypedContext:
    """What a typed-context provider receives: the projection plus the pinned binding."""

    projection: ProviderContextProjection
    binding: TypedContextBinding


def pin_context(
    snapshot: VisionContextSnapshot, policy: AgeBandPolicy
) -> ProviderTypedContext:
    """Project a verified snapshot and pin both digests before any provider call."""

    projection = project_provider_context(snapshot, policy)
    payload = payload_digest(projection)
    return ProviderTypedContext(
        projection=projection,
        binding=TypedContextBinding(
            context_contract=TYPED_CONTEXT_CONTRACT,
            context_contract_version=TYPED_CONTEXT_VERSION,
            canonical_rules_version=CANONICAL_RULES_VERSION,
            context_revision=snapshot.context_revision,
            payload_digest=payload,
            context_digest=context_digest(snapshot, payload),
            age_band_policy_ref=policy.policy_ref,
            age_band_policy_version=policy.version,
        ),
    )


# ---------------------------------------------------------------------- capability
@dataclass(frozen=True, slots=True)
class ContextCapability:
    """Static reviewed provider capability for typed context (no runtime negotiation)."""

    contract: str
    contract_version: str
    fields: tuple[str, ...]
    transport_kind: str


C2_CONTEXT_CAPABILITY = ContextCapability(
    contract=TYPED_CONTEXT_CONTRACT,
    contract_version=TYPED_CONTEXT_VERSION,
    fields=PROVIDER_CONTEXT_FIELDS,
    transport_kind=OFFLINE_INJECTED_TRANSPORT,
)


__all__ = [
    "C2_CONTEXT_CAPABILITY",
    "CANONICAL_RULES_VERSION",
    "CONTEXT_AUDIENCE_MAX",
    "FIELD_AUDIENCE_AGE_BANDS",
    "FIELD_REQUEST_ENUMS",
    "FIELD_TEACHER_TOPIC",
    "FIXTURE_AGE_BAND_POLICY",
    "OFFLINE_INJECTED_TRANSPORT",
    "PROVIDER_CONTEXT_FIELDS",
    "TYPED_CONTEXT_CONTRACT",
    "TYPED_CONTEXT_VERSION",
    "AgeBand",
    "AgeBandPolicy",
    "ContextCapability",
    "ContextCode",
    "ContextPortFacts",
    "ContextRuleViolation",
    "MemberContextFact",
    "ProviderContextProjection",
    "ProviderTypedContext",
    "RequestContextFact",
    "RequestReason",
    "RequestedLevel",
    "TargetKind",
    "TeacherTopicFact",
    "VisionContextSnapshot",
    "context_digest",
    "payload_digest",
    "pin_context",
    "project_provider_context",
    "strict_canonical_sha256",
    "verify_context_snapshot",
]
