"""Bounded FEAT-030 package preparation with deterministic graceful degradation."""

from __future__ import annotations

import json
import secrets
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from threading import RLock

from sketch2life.application.ports.auto_rig_storage import (
    RigPackageGrant,
    RigPackageGrantStore,
)
from sketch2life.application.ports.segmentation import (
    SubjectSegmentationPort,
    SubjectSegmentationRequest,
    SubjectSegmentationResult,
)
from sketch2life.application.ports.session_storage import ArtifactStore, JobStore
from sketch2life.application.services.auto_rig.rig_builder import (
    build_animation_plan,
    build_template_rig,
    classify_archetype,
    validate_rig_geometry,
)
from sketch2life.contracts.schemas.auto_rig import (
    AutoRigJobV1,
    RigDeliveryTier,
    RiggedArtworkPackageV1,
    RigJobStage,
    RigJobStatus,
    RigTargetV1,
    RigValidationResultV1,
)
from sketch2life.contracts.schemas.p1_experience import VersionedRefV1
from sketch2life.contracts.schemas.renderer_v2 import VisualAnimationPlanV2
from sketch2life.contracts.schemas.scene_exploration import SourceRegionV1


class AutoRigPackageUnavailable(ValueError):
    pass


class AutoRigService:
    """Creates safe template packages now and accepts a future segmentation adapter."""

    def __init__(
        self,
        *,
        artifacts: ArtifactStore,
        grants: RigPackageGrantStore,
        jobs: JobStore[AutoRigJobV1],
        segmenter: SubjectSegmentationPort | None = None,
        now: Callable[[], datetime] | None = None,
        capability_ttl_seconds: int = 90,
    ) -> None:
        self._artifacts = artifacts
        self._grants = grants
        self._jobs = jobs
        self._segmenter = segmenter
        self._prepared_regions: dict[str, SubjectSegmentationResult] = {}
        self._lock = RLock()
        self._now = now or (lambda: datetime.now(UTC))
        self._capability_ttl_seconds = capability_ttl_seconds

    def start_gate_a_preparation(
        self,
        *,
        session_id: str,
        request_id: str,
        source_artifact_ref: str | None = None,
        source_sha256: str | None = None,
        target_id: str | None = None,
        target_label: str | None = None,
        target_confidence: float | None = None,
        semantic_tags: tuple[str, ...] = (),
    ) -> AutoRigJobV1:
        """Register bounded preprocessing immediately after Gate A.

        The current local adapter has no benchmark-approved segmentation model, so it
        finishes as PARTIAL_SUCCESS and selects cutout micro-motion. A future worker can
        replace this implementation without changing the job contract.
        """
        job_id = f"auto-rig-{session_id}"
        existing = self._jobs.get(job_id)
        if existing is not None:
            return existing
        now = self._aware_now()
        segmentation: SubjectSegmentationResult | None = None
        if (
            self._segmenter is not None
            and source_artifact_ref is not None
            and source_sha256 is not None
            and target_id is not None
            and target_label is not None
            and target_confidence is not None
        ):
            try:
                segmentation = self._segmenter.segment(
                    SubjectSegmentationRequest(
                        session_id=session_id,
                        source_artifact_ref=source_artifact_ref,
                        source_sha256=source_sha256,
                        target_id=target_id,
                        target_label=target_label,
                        target_confidence=target_confidence,
                        semantic_tags=semantic_tags,
                    )
                )
            except Exception:
                segmentation = None
        if segmentation is not None:
            with self._lock:
                self._prepared_regions[session_id] = segmentation
        succeeded = segmentation is not None
        job = AutoRigJobV1(
            contractName="AutoRigJobV1",
            contractVersion="1.0",
            jobId=job_id,
            sessionId=session_id,
            requestId=request_id,
            status=RigJobStatus.SUCCEEDED if succeeded else RigJobStatus.PARTIAL_SUCCESS,
            stage=RigJobStage.PACKAGING,
            progress=100,
            displayMessageKey=(
                "RIG_SUBJECT_PREPARED" if succeeded else "RIG_PREPARED_WITH_SAFE_FALLBACK"
            ),
            attempt=1,
            selectedTier=(
                RigDeliveryTier.FULL_AUTO_RIG if succeeded else RigDeliveryTier.CUTOUT_MICRO_MOTION
            ),
            failureCode=None if succeeded else "SEGMENTATION_ADAPTER_UNAVAILABLE",
            retryable=False,
            createdAt=now,
            updatedAt=now,
        )
        self._jobs.create(job_id, job)
        return job

    def current_job(self, session_id: str) -> AutoRigJobV1 | None:
        return self._jobs.get(f"auto-rig-{session_id}")

    def prepare_template_package(
        self,
        *,
        session_id: str,
        source_artifact_ref: str,
        source_sha256: str,
        target_id: str,
        target_label: str,
        target_confidence: float,
        semantic_tags: tuple[str, ...],
        experience_spec_ref: VersionedRefV1,
        learning_bridge_vi: str,
    ) -> tuple[RiggedArtworkPackageV1, VisualAnimationPlanV2, str, datetime, str]:
        archetype = classify_archetype(target_label, semantic_tags)
        with self._lock:
            prepared = self._prepared_regions.get(session_id)
        # Without a benchmark-approved segmentation adapter, use a source-derived
        # transparent foreground over the complete canvas and remain at the cutout tier.
        region = (
            prepared.source_region
            if prepared is not None
            else SourceRegionV1(x=0, y=0, width=1, height=1)
        )
        rig = build_template_rig(archetype=archetype, source_region=region)
        geometry_reasons = validate_rig_geometry(rig)
        tier = (
            RigDeliveryTier.FULL_AUTO_RIG
            if prepared is not None
            else RigDeliveryTier.CUTOUT_MICRO_MOTION
        )
        reasons = (
            geometry_reasons
            if prepared is not None
            else ("SEGMENTATION_ADAPTER_UNAVAILABLE", *geometry_reasons)
        )
        valid = not geometry_reasons
        if not valid:
            tier = RigDeliveryTier.BBOX_VISUAL_FOCUS
        target = RigTargetV1(
            canonicalEntityId=target_id,
            normalizedLabel=target_label,
            confidence=target_confidence,
            semanticTags=semantic_tags,
        )
        package_id = f"rig-{session_id}-{experience_spec_ref.version}"
        validation = RigValidationResultV1(
            contractName="RigValidationResultV1",
            contractVersion="1.0",
            valid=valid,
            selectedTier=tier,
            reasonCodes=reasons,
            validatorVersion="1",
        )
        package = RiggedArtworkPackageV1(
            contractName="RiggedArtworkPackageV1",
            contractVersion="1.0",
            packageId=package_id,
            sessionId=session_id,
            sourceArtifactRef=source_artifact_ref,
            sourceSha256=source_sha256,
            target=target,
            archetype=archetype,
            tier=tier,
            rig=rig if valid else None,
            derivedArtifacts=(),
            validation=validation,
            pipelineVersion="1",
            createdAt=self._aware_now(),
            originalArtPreserved=True,
        )
        plan = build_animation_plan(
            plan_id=f"visual-{experience_spec_ref.id}-{experience_spec_ref.version}",
            session_id=session_id,
            experience_spec_ref=experience_spec_ref,
            package_id=package_id,
            archetype=archetype,
            learning_bridge_vi=learning_bridge_vi,
            tier=tier,
        )
        body = json.dumps(
            package.model_dump(mode="json", by_alias=True),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        descriptor = self._artifacts.put(
            session_id=session_id,
            content_type="application/vnd.sketch2life.rig-package+json",
            body=body,
        )
        capability = secrets.token_urlsafe(48)
        expires_at = self._aware_now() + timedelta(seconds=self._capability_ttl_seconds)
        self._grants.put(
            RigPackageGrant(
                capability_sha256=sha256(capability.encode("utf-8")).hexdigest(),
                session_id=session_id,
                artifact_ref=descriptor.artifact_ref,
                package_sha256=descriptor.sha256,
                expires_at=expires_at,
                remaining_reads=2,
            )
        )
        return package, plan, capability, expires_at, descriptor.sha256

    def read_package(self, capability: str) -> tuple[str, bytes, str]:
        grant = self._grants.consume(
            sha256(capability.encode("utf-8")).hexdigest(), now=self._aware_now()
        )
        if grant is None:
            raise AutoRigPackageUnavailable("rig package capability is unavailable")
        stored = self._artifacts.get(grant.artifact_ref)
        if stored is None:
            raise AutoRigPackageUnavailable("rig package artifact is unavailable")
        descriptor, body = stored
        if descriptor.session_id != grant.session_id or descriptor.sha256 != grant.package_sha256:
            raise AutoRigPackageUnavailable("rig package identity mismatch")
        return descriptor.content_type, body, descriptor.sha256

    def _aware_now(self) -> datetime:
        value = self._now()
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("auto-rig clock must be timezone-aware")
        return value


__all__ = ["AutoRigPackageUnavailable", "AutoRigService"]
