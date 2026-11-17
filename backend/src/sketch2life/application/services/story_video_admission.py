"""Read-only Gate A/B evidence used before admitting a narrated story job."""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import ValidationError

from sketch2life.application.ports.demo_workflow_storage import DemoWorkflowRecord
from sketch2life.contracts.schemas.gate_a import GateAConfirmationV1
from sketch2life.contracts.schemas.p1_experience import (
    ExperienceSpecV1,
    IntegrationGateDecisionV1,
    SemanticAnchorSetV1,
    VersionedRefV1,
)
from sketch2life.contracts.schemas.story_video import stable_model_hash


@dataclass(frozen=True, slots=True)
class StoryGateEvidence:
    session_id: str
    session_version: int
    source_image_ref: str
    source_image_sha256: str
    experience_spec_ref: str
    experience_spec_sha256: str
    confirmed_anchor_ids: frozenset[str]

    @classmethod
    def from_workflow(cls, record: DemoWorkflowRecord) -> StoryGateEvidence:
        """Reject missing or divergent workflow records rather than trusting job JSON."""

        values = record.values
        try:
            confirmation = GateAConfirmationV1.model_validate(values["gate_a_confirmation"])
            anchors = SemanticAnchorSetV1.model_validate(values["anchor_set"])
            spec = ExperienceSpecV1.model_validate(values["experience_spec"])
            gate_b = IntegrationGateDecisionV1.model_validate(values["gate_b"])
        except (KeyError, ValidationError, TypeError, ValueError) as error:
            raise ValueError("STORY_GATE_EVIDENCE_INVALID") from error

        if (
            confirmation.session_id != record.session_id
            or spec.session_id != record.session_id
            or gate_b.session_id != record.session_id
            or gate_b.status != "APPROVED"
            or gate_b.spec_ref != VersionedRefV1(id=spec.spec_id, version=spec.spec_version)
            or gate_b.activity_ref != spec.activity_plan.activity_ref
            or gate_b.objective_ref != spec.learning_focus.objective_ref
            or gate_b.template_ref
            != VersionedRefV1(
                id=spec.activity_template.template_id,
                version=spec.activity_template.template_version,
            )
            or spec.spec_sha256 != stable_model_hash(spec, exclude={"spec_sha256"})
            or spec.anchor_set != anchors
            or spec.source_artifact_id != anchors.source_artifact_id
            or spec.source_artifact_sha256 != anchors.source_artifact_sha256
        ):
            raise ValueError("STORY_GATE_EVIDENCE_INVALID")

        approved_anchors = (anchors.primary_anchor, *anchors.secondary_anchors)
        if any(
            not set(anchor.provenance.source_claim_ids).issubset(
                confirmation.confirmed_claim_ids
            )
            for anchor in approved_anchors
        ):
            raise ValueError("STORY_GATE_EVIDENCE_INVALID")
        return cls(
            session_id=record.session_id,
            session_version=record.version,
            source_image_ref=spec.source_artifact_id,
            source_image_sha256=spec.source_artifact_sha256,
            experience_spec_ref=spec.spec_id,
            experience_spec_sha256=spec.spec_sha256,
            confirmed_anchor_ids=frozenset(anchor.anchor_id for anchor in approved_anchors),
        )


__all__ = ["StoryGateEvidence"]
