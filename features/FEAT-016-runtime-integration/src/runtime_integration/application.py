"""Application-owned session aggregate and command handlers."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from typing import Any

from .contracts import (
    ArtifactRef,
    CommandEnvelope,
    GateAConfirmation,
    GateBApproval,
    RuntimeRejected,
    SessionSnapshot,
    SessionState,
)


class SessionAggregate:
    """In-memory aggregate used by fixture-only runtime tests."""

    def __init__(self, session_id: str) -> None:
        self._snapshot = SessionSnapshot(session_id=session_id, state=SessionState.CREATED, version=0)
        self._processed: dict[str, SessionSnapshot] = {}

    @property
    def snapshot(self) -> SessionSnapshot:
        return self._snapshot

    def _replay(self, envelope: CommandEnvelope) -> SessionSnapshot | None:
        envelope.validate()
        if envelope.session_id != self._snapshot.session_id:
            raise RuntimeRejected("SESSION_ID_MISMATCH")
        return self._processed.get(envelope.command_id)

    def _apply(self, envelope: CommandEnvelope, *, state: SessionState, **changes: Any) -> SessionSnapshot:
        envelope.validate()
        if envelope.session_id != self._snapshot.session_id:
            raise RuntimeRejected("SESSION_ID_MISMATCH")
        previous = self._processed.get(envelope.command_id)
        if previous is not None:
            return previous
        if envelope.expected_session_version != self._snapshot.version:
            raise RuntimeRejected("STALE_SESSION_VERSION")
        self._snapshot = replace(self._snapshot, state=state, version=self._snapshot.version + 1, **changes)
        self._processed[envelope.command_id] = self._snapshot
        return self._snapshot

    def submit_media(self, envelope: CommandEnvelope, artifacts: tuple[ArtifactRef, ...], *, validation_passed: bool) -> SessionSnapshot:
        if (replay := self._replay(envelope)) is not None:
            return replay
        if self._snapshot.state not in {SessionState.CREATED, SessionState.MEDIA_RECAPTURE}:
            raise RuntimeRejected("MEDIA_SUBMISSION_NOT_ALLOWED")
        if not artifacts:
            raise RuntimeRejected("SOURCE_ARTIFACT_REQUIRED")
        return self._apply(envelope, state=SessionState.CREATED if validation_passed else SessionState.MEDIA_RECAPTURE, source_artifacts=artifacts)

    def record_understanding(self, envelope: CommandEnvelope, proposal: Mapping[str, Any]) -> SessionSnapshot:
        if (replay := self._replay(envelope)) is not None:
            return replay
        if self._snapshot.state is not SessionState.CREATED:
            raise RuntimeRejected("UNDERSTANDING_NOT_ALLOWED")
        if not proposal.get("claims"):
            raise RuntimeRejected("UNDERSTANDING_CLAIMS_REQUIRED")
        return self._apply(envelope, state=SessionState.GATE_A_PENDING, raw_understanding=dict(proposal))

    def confirm_gate_a(self, envelope: CommandEnvelope, confirmation: GateAConfirmation) -> SessionSnapshot:
        if (replay := self._replay(envelope)) is not None:
            return replay
        if self._snapshot.state is not SessionState.GATE_A_PENDING:
            raise RuntimeRejected("GATE_A_REQUIRED")
        proposal = self._snapshot.raw_understanding or {}
        available = {str(claim.get("claim_id")) for claim in proposal.get("claims", ())}
        if not set(confirmation.confirmed_claim_ids).issubset(available):
            raise RuntimeRejected("GATE_A_CLAIM_NOT_FOUND")
        return self._apply(envelope, state=SessionState.UNDERSTANDING_PROPOSED, gate_a=confirmation)

    def request_context(self, envelope: CommandEnvelope) -> SessionSnapshot:
        if (replay := self._replay(envelope)) is not None:
            return replay
        if self._snapshot.state not in {SessionState.UNDERSTANDING_PROPOSED, SessionState.CONTEXT_REQUIRED}:
            raise RuntimeRejected("CONTEXT_REQUEST_NOT_ALLOWED")
        return self._apply(envelope, state=SessionState.CONTEXT_REQUIRED)

    def filter_candidates(self, envelope: CommandEnvelope, context: Mapping[str, Any], *, activity_id: str, activity_version: int, objective_id: str, objective_version: int) -> SessionSnapshot:
        if (replay := self._replay(envelope)) is not None:
            return replay
        if self._snapshot.state not in {SessionState.UNDERSTANDING_PROPOSED, SessionState.CONTEXT_REQUIRED}:
            if self._snapshot.state in {SessionState.CREATED, SessionState.MEDIA_RECAPTURE}:
                raise RuntimeRejected("GATE_A_REQUIRED")
            raise RuntimeRejected("P1_FILTER_NOT_ALLOWED")
        required = {"age_months", "readiness_ids", "available_material_option_ids", "supervision_level", "policy_flags", "candidate_status"}
        if required.difference(context):
            return self._apply(envelope, state=SessionState.CONTEXT_REQUIRED, p1_context=dict(context))
        if context["candidate_status"] != "ACTIVE_FIXTURE" or not context["readiness_ids"] or not context["available_material_option_ids"]:
            return self._apply(envelope, state=SessionState.CONTEXT_REQUIRED, p1_context=dict(context))
        proposal = dict(self._snapshot.raw_understanding or {})
        proposal["candidate"] = {"activity_id": activity_id, "activity_version": activity_version, "objective_id": objective_id, "objective_version": objective_version}
        return self._apply(envelope, state=SessionState.GATE_B_PENDING, raw_understanding=proposal, p1_context=dict(context))

    def approve_gate_b(self, envelope: CommandEnvelope, approval: GateBApproval) -> SessionSnapshot:
        if (replay := self._replay(envelope)) is not None:
            return replay
        if self._snapshot.state is not SessionState.GATE_B_PENDING:
            raise RuntimeRejected("GATE_B_REQUIRED")
        candidate = dict((self._snapshot.raw_understanding or {}).get("candidate", {}))
        expected = (candidate.get("activity_id"), candidate.get("activity_version"), candidate.get("objective_id"), candidate.get("objective_version"))
        received = (approval.activity_id, approval.activity_version, approval.objective_id, approval.objective_version)
        if expected != received:
            raise RuntimeRejected("GATE_B_IDENTITY_MISMATCH")
        return self._apply(envelope, state=SessionState.CANDIDATES_READY, gate_b=approval)

    def attach_experience(self, envelope: CommandEnvelope, artifacts: tuple[ArtifactRef, ...]) -> SessionSnapshot:
        if (replay := self._replay(envelope)) is not None:
            return replay
        if self._snapshot.state is not SessionState.CANDIDATES_READY:
            raise RuntimeRejected("EXPERIENCE_COMPILE_NOT_ALLOWED")
        if not artifacts:
            raise RuntimeRejected("EXPERIENCE_ARTIFACT_REQUIRED")
        return self._apply(envelope, state=SessionState.EXPERIENCE_READY, experience_artifacts=artifacts)

    def complete_handoff(self, envelope: CommandEnvelope) -> SessionSnapshot:
        if (replay := self._replay(envelope)) is not None:
            return replay
        if self._snapshot.state is not SessionState.EXPERIENCE_READY:
            raise RuntimeRejected("HANDOFF_NOT_READY")
        return self._apply(envelope, state=SessionState.HANDOFF_READY, handoff_completed=True)

    def record_feedback(self, envelope: CommandEnvelope, feedback: Mapping[str, Any]) -> SessionSnapshot:
        if (replay := self._replay(envelope)) is not None:
            return replay
        if self._snapshot.state is not SessionState.HANDOFF_READY:
            raise RuntimeRejected("FEEDBACK_REQUIRES_HANDOFF")
        return self._apply(envelope, state=SessionState.FEEDBACK_RECORDED, feedback=dict(feedback))


