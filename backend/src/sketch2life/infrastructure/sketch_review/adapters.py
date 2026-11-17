"""BE2-05 adapters over the BE2-04 public API (plan §4.5, §7).

The target reader calls only ``SketchGenerationService.revalidate`` (system-level) and, for the
Teacher queue, ``get_record`` with a real Teacher principal. It never touches the producer's
repository, unit of work, store or ``peek``. Artifact metadata and quarantine go through the
coordinated artifact port; quarantine is called only after a 05 commit.
"""

from __future__ import annotations

from collections.abc import Mapping

from sketch2life.application.ports.ai_jobs import (
    ArtifactDescriptor,
    Principal,
    PrincipalRole,
    QuarantineIntent,
)
from sketch2life.application.services.sketch_generation import SketchGenerationService
from sketch2life.domain.sketch_proposal import AssetRef, SketchProposal, content_sha256
from sketch2life.domain.sketch_review import ReviewTarget, TargetAsset
from sketch2life.infrastructure.sketch_generation.adapters import CoordinatedSketchArtifactPort


class TargetIntegrityError(RuntimeError):
    """The producer's promoted content does not match its own content hash."""


def _asset(ref: AssetRef | None) -> TargetAsset | None:
    if ref is None:
        return None
    return TargetAsset(ref.artifact_ref, ref.sha256, ref.media_type, ref.byte_size)


def to_review_target(proposal: SketchProposal) -> ReviewTarget:
    """Map one producer snapshot (public return value) into ``SketchReviewTargetV1``."""

    binding, version = proposal.binding, proposal.current
    promoted = version.promoted
    if promoted is not None:
        expected = content_sha256(proposal, version, text=promoted.text, asset=promoted.asset,
                                  producer=promoted.producer)
        if expected != promoted.content_sha256:
            raise TargetIntegrityError(proposal.proposal_id)
    return ReviewTarget(
        proposal_id=proposal.proposal_id,
        organization_id=proposal.organization_id,
        record_version=proposal.record_version,
        review_revision=proposal.review_revision,
        proposal_version=version.version,
        pipeline_state=str(version.pipeline_state),
        moderation_state=str(version.moderation_state),
        status_reason=None if version.status_reason is None else str(version.status_reason),
        level=version.level,
        display_mode=str(version.rule.display_mode),
        text=None if promoted is None else promoted.text,
        asset=None if promoted is None else _asset(promoted.asset),
        result_document=None if promoted is None else _asset(promoted.result_document),
        content_sha256=None if promoted is None else promoted.content_sha256,
        producer={} if promoted is None else {k: str(v) for k, v in
                                              promoted.producer.canonical().items()},
        job_id=None if promoted is None else promoted.job_id,
        attempt_id=None if promoted is None else promoted.attempt_id,
        session_id=binding.session_id,
        class_id=binding.class_id,
        canvas_id=binding.canvas_id,
        group_id=binding.group_id,
        audience=binding.audience,
        contributor=binding.contributor_participant_id,
        purpose_code=binding.purpose_code,
        context_revision=binding.context_revision,
        roster_revision=binding.roster_revision,
        analysis_id=binding.analysis_id,
        analysis_revision=binding.analysis_revision,
        meaning_digest=binding.meaning.digest(),
        source_snapshot_ref=binding.source.snapshot_ref,
        source_input_hash=binding.source.input_hash,
        policy_ref={"policy_id": version.policy_id, "version": version.policy_version,
                    "status": version.policy_status},
    )


class SketchServiceReviewTargetReader:
    """Public-API reader of BE2-04 (allowlisted calls: ``revalidate``, ``get_record``)."""

    def __init__(self, service: SketchGenerationService) -> None:
        self._service = service

    def read(self, proposal_id: str) -> ReviewTarget | None:
        proposal = self._service.revalidate(proposal_id)
        return None if proposal is None else to_review_target(proposal)

    def queue_record(self, teacher: Principal, proposal_id: str) -> Mapping[str, object] | None:
        if teacher.role is not PrincipalRole.TEACHER:  # never a device or a derived Teacher
            return None
        try:
            return self._service.get_record(teacher, proposal_id)
        except Exception:  # noqa: BLE001 - producer refusal maps to "not found" for 05
            return None


class CoordinatedReviewArtifacts:
    """Artifact metadata (coordinated read) and the after-commit quarantine sink (§4.4)."""

    caller = "be2-05"

    def __init__(self, port: CoordinatedSketchArtifactPort) -> None:
        self._port = port

    def describe(self, artifact_ref: str) -> ArtifactDescriptor | None:
        return self._port.describe(artifact_ref)

    def quarantine(self, intent: QuarantineIntent) -> None:
        self._port.quarantine(intent, caller=self.caller)


__all__ = [
    "CoordinatedReviewArtifacts",
    "SketchServiceReviewTargetReader",
    "TargetIntegrityError",
    "to_review_target",
]
