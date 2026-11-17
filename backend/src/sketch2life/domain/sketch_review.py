"""BE2-05 Sketch review domain (offline component, FEAT-052, plan candidate R2).

Pure rules for the 05-owned review store: review target projection and identity, exact review
key, append-only entries with applicability state, the immutable version terminal marker
(OD-07-A), the composite ETag (OD-04) and the composed DATA-23 projection (D-3). No framework,
storage, provider or BE2-04 types: the adapter maps the producer's public values into
``ReviewTarget``.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import StrEnum

from sketch2life.domain.ai_jobs.model import require_aware
from sketch2life.domain.vision_context import strict_canonical_sha256

REVIEW_CONTRACT = "SketchProposalReviewV0"
REVIEW_CONTRACT_VERSION = "0.1-candidate"
TARGET_KIND = "sketch_proposal"
PENDING = "pending_teacher_review"
SHORT_TEXT_MAX = 128  # SRS LIMIT_TEXT_SHORT, PROPOSED (OD-02 binder refinement)

_REF = re.compile(r"^[A-Za-z0-9_.:-]{1,120}$")
_SHA = re.compile(r"^[0-9a-f]{64}$")
_CONTROL = re.compile(r"[\x00-\x1f\x7f-\x9f]")
_ETAG = re.compile(r'^"sketch-review:([A-Za-z0-9_.:-]{1,120}):(\d+):(\d+):(\d+)"$')


class SketchReviewRuleViolation(ValueError):
    """A domain invariant of the 05 review store was violated."""


class TerminalVersion(SketchReviewRuleViolation):
    """Approval of an exact version that already carries a terminal marker (OD-07-A)."""


class Decision(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_CHANGES = "request_changes"

    @property
    def terminal(self) -> bool:
        return self is not Decision.APPROVE


class EntryState(StrEnum):
    """Applicability state; equals the DATA-24 record ``state`` enum."""

    EFFECTIVE = "effective"
    REVOKED = "revoked"
    STALE = "stale"


class ModerationOutcome(StrEnum):
    PASSED = "passed"
    BLOCKED = "blocked"


def _ref(value: object, name: str) -> str:
    if not isinstance(value, str) or not _REF.match(value):
        raise SketchReviewRuleViolation(f"{name} is not an opaque reference")
    return value


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or not _SHA.match(value):
        raise SketchReviewRuleViolation(f"{name} is not a lowercase SHA-256")
    return value


def normalize_reason(value: object) -> str:
    """NFC + trim, 1..128 code points, no control characters (ShortText refinement, OD-02)."""

    if not isinstance(value, str):
        raise SketchReviewRuleViolation("reason must be a string")
    text = unicodedata.normalize("NFC", value).strip()
    if not text or len(text) > SHORT_TEXT_MAX or _CONTROL.search(text):
        raise SketchReviewRuleViolation("reason must be 1..128 printable code points")
    return text


# ------------------------------------------------------------------ review target
@dataclass(frozen=True, slots=True)
class TargetAsset:
    """Pinned producer metadata of one output artifact (ref, hash, media type, size)."""

    artifact_ref: str
    sha256: str
    media_type: str
    byte_size: int

    def __post_init__(self) -> None:
        _ref(self.artifact_ref, "artifact_ref")
        _sha(self.sha256, "artifact sha256")
        if not self.media_type or self.byte_size < 0:
            raise SketchReviewRuleViolation("asset media type and size are required")

    def canonical(self) -> dict[str, object]:
        return {"ref": self.artifact_ref, "sha256": self.sha256,
                "media_type": self.media_type, "byte_size": self.byte_size}


@dataclass(frozen=True, slots=True)
class ReviewTarget:
    """``SketchReviewTargetV1``: 05-owned projection of one producer snapshot (plan §4.5)."""

    proposal_id: str
    organization_id: str
    record_version: int
    review_revision: int
    proposal_version: int
    pipeline_state: str
    moderation_state: str
    status_reason: str | None
    level: str
    display_mode: str
    text: str | None = field(repr=False)
    asset: TargetAsset | None
    result_document: TargetAsset | None
    content_sha256: str | None
    producer: Mapping[str, str]
    job_id: str | None
    attempt_id: str | None
    session_id: str
    class_id: str
    canvas_id: str
    group_id: str | None
    audience: tuple[str, ...]
    contributor: str
    purpose_code: str
    context_revision: int
    roster_revision: int | None
    analysis_id: str
    analysis_revision: int
    meaning_digest: str
    source_snapshot_ref: str
    source_input_hash: str
    policy_ref: Mapping[str, str]

    def __post_init__(self) -> None:
        for name in ("proposal_id", "organization_id", "session_id", "class_id", "canvas_id",
                     "contributor"):
            _ref(getattr(self, name), name)
        if min(self.record_version, self.review_revision, self.proposal_version) < 1:
            raise SketchReviewRuleViolation("target revisions start at 1")
        if not self.audience or self.contributor not in self.audience:
            raise SketchReviewRuleViolation("target audience must contain the contributor")
        if self.reviewable and (self.result_document is None or self.content_sha256 is None):
            raise SketchReviewRuleViolation("a reviewable target has promoted content")
        if self.content_sha256 is not None:
            _sha(self.content_sha256, "content_sha256")

    @property
    def reviewable(self) -> bool:
        return self.pipeline_state == PENDING

    @property
    def assets(self) -> tuple[TargetAsset, ...]:
        found = [a for a in (self.result_document, self.asset) if a is not None]
        return tuple(sorted(found, key=lambda a: a.artifact_ref))

    @property
    def ref_set(self) -> tuple[str, ...]:
        """Every promoted output ref, result document included (text-only too)."""

        return tuple(a.artifact_ref for a in self.assets)

    @property
    def version_key(self) -> tuple[int, str]:
        assert self.content_sha256 is not None
        return (self.proposal_version, self.content_sha256)

    def identity(self) -> str:
        return target_identity(self)


def target_identity(target: ReviewTarget) -> str:
    """Coherent snapshot identity: producer revisions, exact content and the pinned ref set."""

    return strict_canonical_sha256({
        "proposal_id": target.proposal_id,
        "record_version": target.record_version,
        "review_revision": target.review_revision,
        "proposal_version": target.proposal_version,
        "content_sha256": target.content_sha256,
        "ref_set": [{"ref": a.artifact_ref, "sha256": a.sha256} for a in target.assets],
    })


# ------------------------------------------------------------------ audience and key
@dataclass(frozen=True, slots=True)
class ReviewAudience:
    session_id: str
    group_ids: tuple[str, ...]
    participant_ids: tuple[str, ...]
    audience_context_revision: int
    consent_refs: tuple[tuple[str, int], ...]

    def __post_init__(self) -> None:
        _ref(self.session_id, "session_id")
        for values, name in ((self.group_ids, "group_ids"),
                             (self.participant_ids, "participant_ids")):
            if len(set(values)) != len(values):
                raise SketchReviewRuleViolation(f"{name} must be unique")
        if not self.participant_ids:
            raise SketchReviewRuleViolation("an audience names at least one participant")
        if len({s for s, _ in self.consent_refs}) != len(self.consent_refs):
            raise SketchReviewRuleViolation("consent refs are unique per subject")

    def digest(self) -> str:
        return strict_canonical_sha256({
            "session_id": self.session_id,
            "group_ids": sorted(self.group_ids),
            "participant_ids": sorted(self.participant_ids),
            "audience_context_revision": self.audience_context_revision,
            "consent_refs": [[s, r] for s, r in sorted(self.consent_refs)],
        })


def review_key(*, proposal_id: str, version: int, content_sha256: str, audience: ReviewAudience,
               context_revision: int, policy_version: str) -> str:
    """B21.5 exact review uniqueness key."""

    return strict_canonical_sha256({
        "target_kind": TARGET_KIND,
        "target_id": proposal_id,
        "target_version": version,
        "target_hash": content_sha256,
        "audience": audience.digest(),
        "context_revision": context_revision,
        "policy_version": policy_version,
    })


# ------------------------------------------------------------------ store records
@dataclass(frozen=True, slots=True)
class ReviewEntry:
    review_id: str
    review_revision: int
    decision: Decision
    reason: str | None
    reviewer_principal_id: str
    reviewed_at: datetime
    proposal_id: str
    target_version: int
    target_hash: str
    source_context_revision: int
    audience: ReviewAudience
    policy_version: str
    producer_review_revision: int
    key: str
    state: EntryState = EntryState.EFFECTIVE
    # Monotonic 05 invalidation generation (review-policy/review-context epochs) pinned at the
    # decision; a later publication bumps it, so restoring old values never revives the entry.
    generation: tuple[tuple[str, int], ...] = ()

    def __post_init__(self) -> None:
        _ref(self.review_id, "review_id")
        _sha(self.target_hash, "target_hash")
        require_aware(self.reviewed_at, "reviewed_at")
        if self.review_revision < 1:
            raise SketchReviewRuleViolation("review_revision starts at 1")
        if self.decision.terminal and not self.reason:
            raise SketchReviewRuleViolation("reject/request_changes need a reason")

    @property
    def version_key(self) -> tuple[int, str]:
        return (self.target_version, self.target_hash)


@dataclass(frozen=True, slots=True)
class VersionTerminalMarker:
    """Immutable terminal history of one exact version; never updated or deleted (OD-07-A).

    ``first_decision`` is provenance only; current decisions come from review entries (D-3)."""

    proposal_id: str
    proposal_version: int
    content_sha256: str
    first_decision: Decision
    review_id: str
    recorded_at: datetime

    def __post_init__(self) -> None:
        if not self.first_decision.terminal:
            raise SketchReviewRuleViolation("only reject/request_changes create a marker")
        require_aware(self.recorded_at, "recorded_at")

    @property
    def version_key(self) -> tuple[int, str]:
        return (self.proposal_version, self.content_sha256)


ModerationKey = tuple[str, int, str, str, tuple[tuple[str, str], ...]]


@dataclass(frozen=True, slots=True)
class ModerationRecord:
    """Append-only assessment of one exact content under one moderation policy."""

    proposal_id: str
    proposal_version: int
    content_sha256: str
    refs: tuple[tuple[str, str], ...]
    outcome: ModerationOutcome
    reason_code: str | None
    policy_version: str
    decided_at: datetime

    @property
    def version_key(self) -> tuple[int, str]:
        return (self.proposal_version, self.content_sha256)

    @property
    def key(self) -> ModerationKey:
        return moderation_key(self.proposal_id, self.proposal_version, self.content_sha256,
                              self.policy_version, self.refs)


def moderation_key(proposal_id: str, version: int, content_sha256: str, policy_version: str,
                   refs: tuple[tuple[str, str], ...]) -> ModerationKey:
    """Complete applicable identity: exact content, pinned ref hashes and the policy (RV-CR01)."""

    return (proposal_id, version, content_sha256, policy_version, tuple(sorted(refs)))


def target_moderation_key(target: ReviewTarget, policy_version: str) -> ModerationKey:
    assert target.content_sha256 is not None
    return moderation_key(target.proposal_id, target.proposal_version, target.content_sha256,
                          policy_version, tuple((a.artifact_ref, a.sha256) for a in target.assets))


@dataclass(frozen=True, slots=True)
class ReviewHead:
    """Per-proposal head; ``current`` maps an exact version to its current entry (D-3)."""

    proposal_id: str
    organization_id: str
    decision_revision: int = 0
    current: tuple[tuple[int, str, str | None], ...] = ()

    def current_entry_id(self, version_key: tuple[int, str]) -> str | None:
        for version, digest, review_id in self.current:
            if (version, digest) == version_key:
                return review_id
        return None

    def with_current(self, version_key: tuple[int, str], review_id: str | None) -> ReviewHead:
        rest = tuple(c for c in self.current if (c[0], c[1]) != version_key)
        return replace(self, current=(*rest, (*version_key, review_id)))


def current_entry(entries: Iterable[ReviewEntry],
                  version_key: tuple[int, str]) -> ReviewEntry | None:
    """The effective entry with the highest review revision for the exact version, or None."""

    effective = [e for e in entries
                 if e.version_key == version_key and e.state is EntryState.EFFECTIVE]
    return max(effective, key=lambda e: e.review_revision, default=None)


@dataclass(frozen=True, slots=True)
class DecisionOutcome:
    """Result of applying one accepted decision to the entries of its exact version."""

    entries: tuple[ReviewEntry, ...]
    changed: tuple[ReviewEntry, ...]
    marker: VersionTerminalMarker | None
    current: ReviewEntry | None


def apply_decision(entries: tuple[ReviewEntry, ...], marker: VersionTerminalMarker | None,
                   new: ReviewEntry, now: datetime) -> DecisionOutcome:
    """Apply ``new`` (already validated) to all entries of its exact version.

    * approve is refused when the version carries a marker (OD-07-A);
    * an effective entry with the same exact key becomes ``revoked``;
    * the first terminal decision inserts the marker and revokes **every** effective approve of
      the exact version, whatever its audience/policy/context key (D-1).
    """

    if new.decision is Decision.APPROVE and marker is not None:
        raise TerminalVersion("the exact version is terminal")
    if any(e.review_id == new.review_id for e in entries):
        raise SketchReviewRuleViolation("review_id already recorded")
    changed: list[ReviewEntry] = []
    updated: list[ReviewEntry] = []
    for entry in entries:
        revoke = entry.version_key == new.version_key and entry.state is EntryState.EFFECTIVE and (
            entry.key == new.key
            or (new.decision.terminal and entry.decision is Decision.APPROVE))
        if revoke:
            entry = replace(entry, state=EntryState.REVOKED)
            changed.append(entry)
        updated.append(entry)
    updated.append(new)
    new_marker = None
    if new.decision.terminal and marker is None:
        new_marker = VersionTerminalMarker(new.proposal_id, new.target_version, new.target_hash,
                                           new.decision, new.review_id, now)
    return DecisionOutcome(tuple(updated), tuple(changed), new_marker,
                           current_entry(updated, new.version_key))


def mark_stale(entries: tuple[ReviewEntry, ...], stale_ids: frozenset[str]
               ) -> tuple[tuple[ReviewEntry, ...], tuple[ReviewEntry, ...]]:
    """Effective entries in ``stale_ids`` become ``stale``; markers are never touched."""

    changed: list[ReviewEntry] = []
    updated: list[ReviewEntry] = []
    for entry in entries:
        if entry.review_id in stale_ids and entry.state is EntryState.EFFECTIVE:
            entry = replace(entry, state=EntryState.STALE)
            changed.append(entry)
        updated.append(entry)
    return tuple(updated), tuple(changed)


def marker_matches_history(entries: Iterable[ReviewEntry], marker: VersionTerminalMarker | None,
                           version_key: tuple[int, str]) -> bool:
    """RV-N21: a marker exists iff a terminal entry exists for the version in any state."""

    terminal = any(e.version_key == version_key and e.decision.terminal for e in entries)
    return terminal == (marker is not None)


# ------------------------------------------------------------------ ETag (OD-04)
def review_etag(proposal_id: str, proposal_version: int, producer_review_revision: int,
                decision_revision: int) -> str:
    """Composite ETag issued by 05 (deliberate deviation from SRS "target review_revision")."""

    return (f'"sketch-review:{proposal_id}:{proposal_version}:{producer_review_revision}:'
            f'{decision_revision}"')


def parse_review_etag(value: str) -> tuple[str, int, int, int] | None:
    match = _ETAG.match(value.strip())
    if match is None:
        return None
    return match.group(1), int(match.group(2)), int(match.group(3)), int(match.group(4))


# ------------------------------------------------------------------ projection (D-3)
@dataclass(frozen=True, slots=True)
class Projection:
    pipeline_state: str
    moderation_state: str
    review_decision: str | None
    decision_applicable: bool
    version_terminal: bool
    approve_allowed: bool
    approval_ref: str | None


def compose_projection(target: ReviewTarget, *, current: ReviewEntry | None,
                       current_applicable: bool, entries: tuple[ReviewEntry, ...],
                       marker: VersionTerminalMarker | None,
                       moderation: ModerationRecord | None) -> Projection:
    """Plan §4.1 precedence table; the Teacher decision comes from the current entry only."""

    terminal = marker is not None
    if moderation is not None and moderation.outcome is ModerationOutcome.BLOCKED:
        return Projection("blocked_unsafe", "blocked", None, False, terminal, False, None)
    moderation_state = ("passed" if moderation is not None else target.moderation_state)
    if current is not None and current.decision is Decision.REJECT:
        return Projection("rejected", moderation_state, "reject", current_applicable, terminal,
                          False, None)
    if current is not None and current.decision is Decision.REQUEST_CHANGES:
        return Projection(target.pipeline_state, moderation_state, "request_changes",
                          current_applicable, terminal, False, None)
    if (current is not None and current.decision is Decision.APPROVE and current_applicable
            and not terminal):
        return Projection("approved", "passed", "approve", True, False, False, current.review_id)
    if terminal:
        latest_terminal = max(
            (e for e in entries if target.content_sha256 is not None
             and e.version_key == target.version_key and e.decision.terminal),
            key=lambda e: e.review_revision, default=None)
        state = ("rejected" if latest_terminal is not None
                 and latest_terminal.decision is Decision.REJECT else target.pipeline_state)
        return Projection(state, moderation_state, None, False, True, False, None)
    return Projection(target.pipeline_state, moderation_state,
                      None if current is None else str(current.decision),
                      current is not None and current_applicable, False,
                      target.reviewable, None)


def entries_by_version(entries: Iterable[ReviewEntry],
                       version_key: tuple[int, str]) -> tuple[ReviewEntry, ...]:
    return tuple(e for e in entries if e.version_key == version_key)


def policy_version_label(review_policy: Mapping[str, str],
                         producer_policy: Mapping[str, str]) -> str:
    return (f"{review_policy['policy_id']}@{review_policy['version']}|"
            f"{producer_policy['policy_id']}@{producer_policy['version']}")


__all__ = [
    "PENDING",
    "REVIEW_CONTRACT",
    "REVIEW_CONTRACT_VERSION",
    "SHORT_TEXT_MAX",
    "TARGET_KIND",
    "Decision",
    "DecisionOutcome",
    "EntryState",
    "ModerationKey",
    "ModerationOutcome",
    "ModerationRecord",
    "Projection",
    "ReviewAudience",
    "ReviewEntry",
    "ReviewHead",
    "ReviewTarget",
    "SketchReviewRuleViolation",
    "TargetAsset",
    "TerminalVersion",
    "VersionTerminalMarker",
    "apply_decision",
    "compose_projection",
    "current_entry",
    "entries_by_version",
    "mark_stale",
    "marker_matches_history",
    "moderation_key",
    "normalize_reason",
    "parse_review_etag",
    "policy_version_label",
    "review_etag",
    "review_key",
    "target_identity",
    "target_moderation_key",
]
