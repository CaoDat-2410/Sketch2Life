"""BE2-05 fixture ports (FIXTURE_ONLY; no provider, network, database or real policy).

* ``FixtureReviewPolicy`` / ``fixture_review_policy`` — review/moderation policy [FX].
* ``FixtureSketchModeration`` — deterministic moderation over text and pinned metadata [FX].
* ``FakeReviewAuthority`` / ``FakeReviewContext`` — BE1 authority/context candidates [FX].
* ``FakeTicketIssuer`` / ``FakeReadModelDispatcher`` / ``FakeChildCache`` — consumers that must ask
  05 eligibility; they prove fail-closed behaviour of 05 only, not a BE1 gateway or read model.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field, replace
from typing import Any

from sketch2life.application.ports.ai_jobs import ArtifactDescriptor, Principal, PrincipalRole
from sketch2life.application.ports.sketch_review import (
    EligibilityChangedIntent,
    ModerationVerdict,
    ReviewAction,
    ReviewContextSnapshot,
    ReviewPolicy,
    ReviewScope,
)
from sketch2life.domain.sketch_review import ModerationOutcome, ReviewTarget

FIXTURE_POLICY_STATUS = "FIXTURE_ONLY_NOT_ADOPTED"
FIXTURE_BLOCKED_TERM = "fixture-unsafe-term"


def fixture_review_policy(**changes: Any) -> ReviewPolicy:
    values: dict[str, Any] = {
        "policy_id": "fixture.sketch_review.v0",
        "version": "1",
        "status": FIXTURE_POLICY_STATUS,
        "enabled": True,
        "text_max_chars": 4000,  # SRS LIMIT_TEXT_LONG, PROPOSED
        "blocked_terms": frozenset({FIXTURE_BLOCKED_TERM}),
        "asset_media_types": frozenset({"image/png"}),
        "asset_max_bytes": 10_485_760,  # SRS LIMIT_ASSET_BYTES, PROPOSED
        "consent_purpose": "ai_sketch",  # SRS purpose candidate (OD-09 fixture)
        **changes,
    }
    return ReviewPolicy(**values)


class FixtureReviewPolicy:
    def __init__(self, snapshot: ReviewPolicy | None) -> None:
        self.snapshot = snapshot

    def current(self, organization_id: str, session_id: str) -> ReviewPolicy | None:
        return self.snapshot


class FixtureSketchModeration:
    """Deterministic fixture rules; never reads image bytes (real moderation is a gate)."""

    def __init__(self) -> None:
        self.calls = 0

    def moderate(self, target: ReviewTarget, descriptors: tuple[ArtifactDescriptor | None, ...],
                 policy: ReviewPolicy) -> ModerationVerdict:
        self.calls += 1
        text = (target.text or "").casefold()
        if any(term.casefold() in text for term in policy.blocked_terms):
            return ModerationVerdict(ModerationOutcome.BLOCKED, "UNSAFE_TEXT")
        if len(target.text or "") > policy.text_max_chars:
            return ModerationVerdict(ModerationOutcome.BLOCKED, "TEXT_LIMIT")
        if target.asset is not None:
            if target.asset.media_type not in policy.asset_media_types:
                return ModerationVerdict(ModerationOutcome.BLOCKED, "MEDIA_TYPE")
            if target.asset.byte_size > policy.asset_max_bytes:
                return ModerationVerdict(ModerationOutcome.BLOCKED, "ASSET_SIZE")
        for descriptor, asset in zip(descriptors, target.assets, strict=True):
            if descriptor is None or descriptor.sha256 != asset.sha256:
                return ModerationVerdict(ModerationOutcome.BLOCKED, "ASSET_HASH_MISMATCH")
        return ModerationVerdict(ModerationOutcome.PASSED, None)


@dataclass(frozen=True, slots=True)
class DeviceBinding:
    organization_id: str
    session_id: str
    participant_id: str


class FakeReviewAuthority:
    """Teachers by class scope; devices bound to one participant; Admin never reviews."""

    def __init__(self) -> None:
        self.teachers: dict[str, tuple[str, frozenset[str]]] = {}
        self.devices: dict[str, DeviceBinding] = {}

    def allowed(self, principal: Principal, scope: ReviewScope, action: ReviewAction) -> bool:
        if principal.organization_id != scope.organization_id:
            return False
        if principal.role is PrincipalRole.TEACHER and action in {ReviewAction.REVIEW,
                                                                 ReviewAction.QUEUE_READ}:
            grant = self.teachers.get(principal.principal_id)
            return grant is not None and grant[0] == scope.organization_id and (
                scope.class_id in grant[1])
        if principal.role is PrincipalRole.DEVICE and action is ReviewAction.CHILD_VIEW:
            return self.participant_for(principal, scope) is not None
        return False

    def participant_for(self, principal: Principal, scope: ReviewScope) -> str | None:
        if principal.role is not PrincipalRole.DEVICE:
            return None
        device = self.devices.get(principal.principal_id)
        if (device is None or device.organization_id != scope.organization_id
                or device.session_id != scope.session_id):
            return None
        return device.participant_id


@dataclass
class _SessionContext:
    audience_context_revision: int
    consent_revisions: dict[str, int]
    consent_effective: set[str]
    admitted: set[str]
    session_active: bool = True


class FakeReviewContext:
    """Audience/consent revisions of the review context (fixture for BE1 facts)."""

    def __init__(self) -> None:
        self.sessions: dict[tuple[str, str], _SessionContext] = {}

    def set_session(self, organization_id: str, session_id: str, *, revision: int,
                    members: tuple[str, ...]) -> None:
        self.sessions[(organization_id, session_id)] = _SessionContext(
            revision, {m: 1 for m in members}, set(members), set(members))

    def current(self, organization_id: str, session_id: str,
                subjects: tuple[str, ...]) -> ReviewContextSnapshot | None:
        context = self.sessions.get((organization_id, session_id))
        if context is None:
            return None
        refs = tuple(sorted((s, context.consent_revisions[s]) for s in subjects
                            if s in context.consent_revisions))
        return ReviewContextSnapshot(context.audience_context_revision, refs,
                                     frozenset(context.consent_effective),
                                     frozenset(context.admitted), context.session_active)


# ------------------------------------------------------------------ fail-closed consumers
@dataclass
class FakeTicketIssuer:
    """Stand-in for BE1 CMD-60: asks 05 eligibility before issuing a fake handle."""

    eligibility: Callable[..., Any]
    issued: list[str] = field(default_factory=list)
    refused: list[str] = field(default_factory=list)

    def issue(self, principal: Principal, proposal_id: str, *, asset_ref: str,
              content_sha256: str, review_ref: str | None) -> str | None:
        decision = self.eligibility(principal, proposal_id, asset_ref=asset_ref,
                                    content_sha256=content_sha256, review_ref=review_ref)
        if not decision.eligible:
            self.refused.append(asset_ref)
            return None
        handle = f"fake_ticket_{principal.principal_id}_{asset_ref}"
        self.issued.append(handle)
        return handle


@dataclass
class FakeChildCache:
    """Content cache that **reauthorizes every hit** (RV-CR03).

    A hit is reused only when 05 eligibility for this device is granted *now* with the same
    review ref and the 05 epoch is unchanged; otherwise the entry is evicted and the current
    payload is returned. Callers never need a manual refresh to stop stale content."""

    payload: Callable[[Principal, str], dict[str, Any]]
    epoch: Callable[[str, str], int]
    eligibility: Callable[..., Any]
    entries: dict[tuple[str, str], tuple[int, str | None, dict[str, Any]]] = field(
        default_factory=dict)
    misses: int = 0
    reauthorized_hits: int = 0

    def get(self, principal: Principal, proposal_id: str) -> dict[str, Any]:
        key = (principal.principal_id, proposal_id)
        current = self.epoch(principal.organization_id, proposal_id)
        cached = self.entries.get(key)
        if cached is not None:
            decision = self.eligibility(principal, proposal_id)
            reusable = (cached[0] == current and cached[2]["status"] == "available"
                        and decision.eligible and decision.review_ref == cached[1])
            if reusable:
                self.reauthorized_hits += 1
                return cached[2]
            del self.entries[key]
        self.misses += 1
        value = self.payload(principal, proposal_id)
        review_ref = value.get("review_ref") if value["status"] == "available" else None
        self.entries[key] = (current, review_ref, value)
        return value


@dataclass
class FakeReadModelDispatcher:
    """Consumes 05 intents and re-asks eligibility before pushing anything to a device."""

    payload: Callable[[Principal, str], dict[str, Any]]
    devices: tuple[Principal, ...]
    pushed: list[tuple[str, str, str]] = field(default_factory=list)
    seen: set[str] = field(default_factory=set)

    def deliver(self, intents: list[EligibilityChangedIntent]) -> int:
        count = 0
        for intent in intents:
            if intent.event_id in self.seen:
                continue
            self.seen.add(intent.event_id)
            for device in self.devices:
                body = self.payload(device, intent.proposal_id)
                if body["status"] == "available":
                    self.pushed.append((device.principal_id, intent.proposal_id,
                                        str(body.get("review_ref"))))
                    count += 1
        return count


def with_changes(policy: ReviewPolicy, **changes: Any) -> ReviewPolicy:
    return replace(policy, **changes)


__all__ = [
    "FIXTURE_BLOCKED_TERM",
    "FIXTURE_POLICY_STATUS",
    "DeviceBinding",
    "FakeChildCache",
    "FakeReadModelDispatcher",
    "FakeReviewAuthority",
    "FakeReviewContext",
    "FakeTicketIssuer",
    "FixtureReviewPolicy",
    "FixtureSketchModeration",
    "fixture_review_policy",
    "with_changes",
]
