"""BE2-06 public-owner adapters and explicitly synthetic disclosure bindings.

Review metadata and optional Child content come from one public 05 eligibility result.
The device turn uses the existing 03 owner/authority ports; receipt disclosure deliberately
uses a separate binding because a closed turn does not revoke a historical receipt.
"""

from __future__ import annotations

from dataclasses import dataclass

from sketch2life.application.ports.ai_jobs import Principal, PrincipalRole
from sketch2life.application.ports.assistance import (
    AssistanceAuthorityPort,
    AssistanceOwnerPort,
)
from sketch2life.application.services.sketch_review import EligibilityDecision, SketchReviewService
from sketch2life.contracts.schemas.child_responses import (
    AuthorizedChildReadV1,
    ReviewAccessSnapshotV1,
    TurnSnapshotV1,
)
from sketch2life.contracts.schemas.sketch_reviews import SketchChildPayloadV0


class PublicSketchReviewAccess:
    """Allowlisted consumer of ``SketchReviewService.eligibility`` only.

    The full producer target remains local to this adapter. In particular, the command
    service never receives the target's text, artifacts, job or provider metadata.
    """

    def __init__(self, service: SketchReviewService) -> None:
        self._service = service

    def _decision(
        self, principal: Principal, proposal_id: str, *,
        expected_proposal_version: int | None, review_ref: str | None,
        content_sha256: str | None,
    ) -> EligibilityDecision | None:
        if principal.role is not PrincipalRole.DEVICE:
            return None
        try:
            decision = self._service.eligibility(
                principal, proposal_id, review_ref=review_ref,
                content_sha256=content_sha256)
        except Exception:  # noqa: BLE001 - owner failure cannot disclose a partial target
            return None
        target = decision.target
        if (not decision.eligible or target is None or decision.participant_id is None
                or decision.review_ref is None or target.content_sha256 is None
                or target.proposal_id != proposal_id
                or target.organization_id != principal.organization_id
                or decision.participant_id not in target.audience
                or (expected_proposal_version is not None
                    and target.proposal_version != expected_proposal_version)
                or (review_ref is not None and decision.review_ref != review_ref)
                or (content_sha256 is not None and target.content_sha256 != content_sha256)):
            return None
        return decision

    @staticmethod
    def _snapshot(decision: EligibilityDecision) -> ReviewAccessSnapshotV1:
        target = decision.target
        assert target is not None and target.content_sha256 is not None
        assert decision.participant_id is not None and decision.review_ref is not None
        return ReviewAccessSnapshotV1(
            organization_id=target.organization_id, class_id=target.class_id,
            session_id=target.session_id, canvas_id=target.canvas_id,
            proposal_id=target.proposal_id, proposal_version=target.proposal_version,
            content_sha256=target.content_sha256, participant_id=decision.participant_id,
            review_ref=decision.review_ref)

    def authorize(
        self, principal: Principal, proposal_id: str, *,
        expected_proposal_version: int | None = None, review_ref: str | None = None,
        content_sha256: str | None = None,
    ) -> ReviewAccessSnapshotV1 | None:
        decision = self._decision(
            principal, proposal_id, expected_proposal_version=expected_proposal_version,
            review_ref=review_ref, content_sha256=content_sha256)
        return None if decision is None else self._snapshot(decision)

    def read(
        self, principal: Principal, proposal_id: str, *,
        expected_proposal_version: int | None = None, review_ref: str | None = None,
        content_sha256: str | None = None,
    ) -> AuthorizedChildReadV1 | None:
        decision = self._decision(
            principal, proposal_id, expected_proposal_version=expected_proposal_version,
            review_ref=review_ref, content_sha256=content_sha256)
        if decision is None:
            return None
        target = decision.target
        assert target is not None
        access = self._snapshot(decision)
        payload = SketchChildPayloadV0(
            proposal_id=target.proposal_id, status="available",
            display_mode=target.display_mode,  # type: ignore[arg-type]
            text_or_question=target.text,
            overlay_asset_ref=None if target.asset is None else target.asset.artifact_ref,
            review_ref=decision.review_ref)
        return AuthorizedChildReadV1(access=access, payload=payload)


@dataclass(frozen=True, slots=True)
class DisclosureBinding:
    organization_id: str
    session_id: str
    canvas_id: str
    participant_id: str


@dataclass(frozen=True, slots=True)
class TeacherBinding:
    organization_id: str
    class_ids: frozenset[str]
    session_ids: frozenset[str]


class FixtureChildResponseAuthority:
    """ASSUMED_CONTRACT turn adapter plus separate FIXTURE_ONLY disclosure/Teacher grants.

    ``bindings`` and ``teachers`` model current read authorization, not real BE1 grants.
    The harness publishes changes explicitly; no provider storage or private 05 state is read.
    """

    def __init__(self, owner: AssistanceOwnerPort, authority: AssistanceAuthorityPort) -> None:
        self._owner = owner
        self._authority = authority
        self.bindings: dict[str, DisclosureBinding] = {}
        self.revoked: set[str] = set()
        self.teachers: dict[str, TeacherBinding] = {}

    def can_disclose(self, principal: Principal, access: ReviewAccessSnapshotV1) -> bool:
        if (principal.role is not PrincipalRole.DEVICE
                or principal.organization_id != access.organization_id
                or principal.principal_id in self.revoked):
            return False
        return self.bindings.get(principal.principal_id) == DisclosureBinding(
            access.organization_id, access.session_id, access.canvas_id, access.participant_id)

    def new_operation(
        self, principal: Principal, access: ReviewAccessSnapshotV1, turn_id: str | None,
    ) -> TurnSnapshotV1 | None:
        if not self.can_disclose(principal, access):
            return None
        canvas = self._owner.canvas(access.organization_id, access.canvas_id)
        if (canvas is None or not canvas.session_active
                or canvas.organization_id != access.organization_id
                or canvas.class_id != access.class_id
                or canvas.session_id != access.session_id or canvas.canvas_id != access.canvas_id):
            return None
        decision = self._authority.decide(principal, canvas)
        contributor = decision.contributor
        if (not decision.allowed or contributor is None or contributor.turn_id is None
                or contributor.participant_id != access.participant_id
                or (turn_id is not None and turn_id != contributor.turn_id)):
            return None
        return TurnSnapshotV1(
            participant_id=contributor.participant_id, turn_id=contributor.turn_id,
            turn_revision=contributor.turn_revision)

    def teacher_allowed(self, principal: Principal, access: ReviewAccessSnapshotV1) -> bool:
        if (principal.role is not PrincipalRole.TEACHER
                or principal.organization_id != access.organization_id
                or principal.principal_id in self.revoked):
            return False
        binding = self.teachers.get(principal.principal_id)
        return (binding is not None and binding.organization_id == access.organization_id
                and access.class_id in binding.class_ids
                and access.session_id in binding.session_ids)
