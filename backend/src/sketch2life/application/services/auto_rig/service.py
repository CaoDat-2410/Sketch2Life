"""Bounded FEAT-030 package preparation with deterministic graceful degradation."""

from __future__ import annotations

import json
import logging
import secrets
from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from threading import RLock

from sketch2life.application.ports.auto_rig_storage import (
    RigArtifactGrant,
    RigArtifactGrantStore,
)
from sketch2life.application.ports.segmentation import (
    SubjectPartSegmentationResult,
    SubjectSegmentationPort,
    SubjectSegmentationRequest,
    SubjectSegmentationResult,
)
from sketch2life.application.ports.session_storage import ArtifactStore, JobStore
from sketch2life.application.services.auto_rig.mask_validation import subject_mask_rejection
from sketch2life.application.services.auto_rig.part_masks import (
    derive_part_masks_from_subject_mask,
)
from sketch2life.application.services.auto_rig.rig_builder import (
    build_animation_plan,
    build_template_rig,
    classify_archetype,
    validate_rig_geometry,
)
from sketch2life.contracts.schemas.auto_rig import (
    AutoRigJobV1,
    DerivedArtifactRefV1,
    RigArchetype,
    RigDeliveryTier,
    RiggedArtworkPackageV1,
    RigJobStage,
    RigJobStatus,
    RigPartV1,
    RigTargetV1,
    RigValidationResultV1,
)
from sketch2life.contracts.schemas.p1_experience import VersionedRefV1
from sketch2life.contracts.schemas.renderer_v2 import PartMaskReadV1, VisualAnimationPlanV2
from sketch2life.contracts.schemas.scene_exploration import SourceRegionV1

LOGGER = logging.getLogger(__name__)


class AutoRigPackageUnavailable(ValueError):
    pass


class AutoRigService:
    """Creates safe template packages now and accepts a future segmentation adapter."""

    def __init__(
        self,
        *,
        artifacts: ArtifactStore,
        grants: RigArtifactGrantStore,
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

        Segmentation parts are accepted only after independent-mask validation. When SAM returns
        only a subject mask, the bounded deterministic part processor may derive masks from that
        exact silhouette; unsupported shapes remain a safe partial result.
        """
        job_id = f"auto-rig-{session_id}"
        existing = self._jobs.get(job_id)
        if existing is not None:
            return existing
        now = self._aware_now()
        mask_failure: str | None = None
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
                        requested_part_roles=_requested_roles(
                            classify_archetype(target_label, semantic_tags)
                        ),
                    )
                )
            except Exception:
                segmentation = None
        if (
            segmentation is not None
            and source_artifact_ref is not None
            and source_sha256 is not None
        ):
            mask_failure = self._subject_mask_failure(
                session_id, source_artifact_ref, source_sha256, segmentation
            )
            if mask_failure is not None:
                LOGGER.info("auto_rig_subject_mask_rejected reason=%s", mask_failure)
                segmentation = replace(
                    segmentation, mask_artifact_ref=None, mask_sha256=None, parts=()
                )
            segmentation = self._ensure_part_masks(
                session_id=session_id,
                source_artifact_ref=source_artifact_ref,
                source_sha256=source_sha256,
                archetype=classify_archetype(target_label or "", semantic_tags),
                segmentation=segmentation,
            )
        if segmentation is not None:
            with self._lock:
                self._prepared_regions[session_id] = segmentation
        has_renderable_parts = segmentation is not None and len(segmentation.parts) >= 2
        succeeded = (
            segmentation is not None
            and segmentation.mask_artifact_ref is not None
            and has_renderable_parts
        )
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
            failureCode=(
                None
                if succeeded
                else mask_failure
                if mask_failure is not None
                else (
                    (
                        "SEGMENTATION_PART_MASKS_NOT_RENDERABLE"
                        if segmentation is not None and segmentation.parts
                        else "SEGMENTATION_PARTS_UNAVAILABLE"
                    )
                    if segmentation is not None
                    else "SEGMENTATION_ADAPTER_UNAVAILABLE"
                )
            ),
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
    ) -> tuple[
        RiggedArtworkPackageV1,
        VisualAnimationPlanV2,
        str,
        datetime,
        str,
        str | None,
        tuple[PartMaskReadV1, ...],
    ]:
        archetype = classify_archetype(target_label, semantic_tags)
        with self._lock:
            prepared = self._prepared_regions.get(session_id)
        # A full rig is eligible only when independently verified part masks are available.
        region = (
            prepared.source_region
            if prepared is not None
            else SourceRegionV1(x=0, y=0, width=1, height=1)
        )
        rig = build_template_rig(archetype=archetype, source_region=region)
        geometry_reasons = validate_rig_geometry(rig)
        valid = not geometry_reasons
        target = RigTargetV1(
            canonicalEntityId=target_id,
            normalizedLabel=target_label,
            confidence=target_confidence,
            semanticTags=semantic_tags,
        )
        package_id = f"rig-{session_id}-{experience_spec_ref.version}"
        stored_mask = None
        derived_artifacts: list[DerivedArtifactRefV1] = []
        rig_parts: list[RigPartV1] = []
        if prepared is not None and prepared.mask_artifact_ref is not None:
            candidate_mask = self._artifacts.get(prepared.mask_artifact_ref)
            if (
                candidate_mask is not None
                and candidate_mask[0].session_id == session_id
                and candidate_mask[0].sha256 == prepared.mask_sha256
                and candidate_mask[0].content_type == "image/png"
                and candidate_mask[1].startswith(b"\x89PNG\r\n\x1a\n")
                and self._subject_mask_failure(
                    session_id, source_artifact_ref, source_sha256, prepared
                ) is None
            ):
                stored_mask = candidate_mask
                # A mask is source-derived media, so its own digest is not expected to equal
                # the source digest. The source identity is carried by the contract below.
                derived_artifacts.append(
                    DerivedArtifactRefV1(
                        artifactRef=stored_mask[0].artifact_ref,
                        sha256=stored_mask[0].sha256,
                        contentType=stored_mask[0].content_type,
                        byteLength=stored_mask[0].byte_length,
                        role="ORIGINAL_DERIVED_MASK",
                        sourceSha256=source_sha256,
                        operation="SAM2.1 prompt-bounded subject segmentation",
                        operationVersion=prepared.adapter_version,
                    )
                )
        has_valid_subject_mask = stored_mask is not None and prepared is not None
        if has_valid_subject_mask and prepared is not None:
            bones = {bone.bone_id for bone in rig.bones}
            for part in prepared.parts:
                part_mask = self._artifacts.get(part.mask_artifact_ref or "")
                bone_id = _bone_for_part(part.role, archetype)
                if (
                    part_mask is None
                    or part_mask[0].session_id != session_id
                    or part_mask[0].sha256 != part.mask_sha256
                    or part_mask[0].content_type != "image/png"
                    or not part_mask[1].startswith(b"\x89PNG\r\n\x1a\n")
                    or bone_id not in bones
                ):
                    continue
                rig_parts.append(
                    RigPartV1(
                        partId=part.part_id,
                        role=part.role,
                        boneId=bone_id,
                        sourceRegion=part.source_region,
                        confidence=part.confidence,
                        maskArtifactRef=part_mask[0].artifact_ref,
                        maskSha256=part_mask[0].sha256,
                    )
                )
                derived_artifacts.append(
                    DerivedArtifactRefV1(
                        artifactRef=part_mask[0].artifact_ref,
                        sha256=part_mask[0].sha256,
                        contentType=part_mask[0].content_type,
                        byteLength=part_mask[0].byte_length,
                        role="ORIGINAL_DERIVED_PART_MASK",
                        sourceSha256=source_sha256,
                        operation=part.operation,
                        operationVersion=part.operation_version,
                    )
                )
        has_valid_parts = has_valid_subject_mask and len(rig_parts) >= 2
        tier = (
            RigDeliveryTier.FULL_AUTO_RIG
            if has_valid_parts
            else RigDeliveryTier.CUTOUT_MICRO_MOTION
        )
        reasons = (
            geometry_reasons
            if has_valid_parts
            else (
                (
                    "SEGMENTATION_PART_MASKS_NOT_RENDERABLE"
                    if prepared is not None and prepared.parts
                    else "SEGMENTATION_PARTS_UNAVAILABLE"
                )
                if prepared is not None
                else "SEGMENTATION_ADAPTER_UNAVAILABLE",
                *geometry_reasons,
            )
        )
        if not valid:
            tier = RigDeliveryTier.BBOX_VISUAL_FOCUS
        if not has_valid_subject_mask:
            derived_artifacts = []
            rig_parts = []
        if tier is not RigDeliveryTier.FULL_AUTO_RIG:
            rig_parts = []
            derived_artifacts = [
                artifact
                for artifact in derived_artifacts
                if artifact.role != "ORIGINAL_DERIVED_PART_MASK"
            ]
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
            parts=tuple(rig_parts),
            derivedArtifacts=tuple(derived_artifacts),
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
            RigArtifactGrant(
                capability_sha256=sha256(capability.encode("utf-8")).hexdigest(),
                session_id=session_id,
                artifact_ref=descriptor.artifact_ref,
                artifact_sha256=descriptor.sha256,
                expires_at=expires_at,
                remaining_reads=2,
            )
        )
        mask_capability = None
        if stored_mask is not None and derived_artifacts:
            mask_capability = secrets.token_urlsafe(48)
            self._grants.put(
                RigArtifactGrant(
                    capability_sha256=sha256(mask_capability.encode("utf-8")).hexdigest(),
                    session_id=session_id,
                    artifact_ref=stored_mask[0].artifact_ref,
                    artifact_sha256=stored_mask[0].sha256,
                    expires_at=expires_at,
                    remaining_reads=2,
                )
            )
        part_mask_reads: list[PartMaskReadV1] = []
        for rig_part in rig_parts:
            part_capability = secrets.token_urlsafe(48)
            self._grants.put(
                RigArtifactGrant(
                    capability_sha256=sha256(part_capability.encode("utf-8")).hexdigest(),
                    session_id=session_id,
                    artifact_ref=rig_part.mask_artifact_ref,
                    artifact_sha256=rig_part.mask_sha256,
                    expires_at=expires_at,
                    remaining_reads=2,
                )
            )
            part_mask_reads.append(
                PartMaskReadV1(
                    partId=rig_part.part_id,
                    boneId=rig_part.bone_id,
                    sourceRegion=rig_part.source_region,
                    readEndpoint="/v1/renderer/rig-mask",
                    readCapability=part_capability,
                    sha256=rig_part.mask_sha256,
                )
            )
        return (
            package,
            plan,
            capability,
            expires_at,
            descriptor.sha256,
            mask_capability,
            tuple(part_mask_reads),
        )

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
        if (
            descriptor.session_id != grant.session_id
            or descriptor.sha256 != grant.artifact_sha256
            or descriptor.content_type != "application/vnd.sketch2life.rig-package+json"
        ):
            raise AutoRigPackageUnavailable("rig package identity mismatch")
        return descriptor.content_type, body, descriptor.sha256

    def _subject_mask_failure(
        self,
        session_id: str,
        source_artifact_ref: str,
        source_sha256: str,
        segmentation: SubjectSegmentationResult,
    ) -> str | None:
        source = self._artifacts.get(source_artifact_ref)
        mask = self._artifacts.get(segmentation.mask_artifact_ref or "")
        if (
            source is None
            or source[0].session_id != session_id
            or source[0].sha256 != source_sha256
            or sha256(source[1]).hexdigest() != source_sha256
            or mask is None
            or mask[0].session_id != session_id
            or mask[0].content_type != "image/png"
            or mask[0].sha256 != segmentation.mask_sha256
            or sha256(mask[1]).hexdigest() != segmentation.mask_sha256
        ):
            return "MASK_PROVENANCE_INVALID"
        return subject_mask_rejection(source[1], mask[1])

    def _ensure_part_masks(
        self,
        *,
        session_id: str,
        source_artifact_ref: str,
        source_sha256: str,
        archetype: RigArchetype,
        segmentation: SubjectSegmentationResult,
    ) -> SubjectSegmentationResult:
        if segmentation.mask_artifact_ref is None or segmentation.mask_sha256 is None:
            LOGGER.info(
                "auto_rig_part_masks_unavailable reason=SUBJECT_MASK_MISSING archetype=%s",
                archetype.value,
            )
            return replace(segmentation, parts=())
        parent = self._artifacts.get(segmentation.mask_artifact_ref)
        source = self._artifacts.get(source_artifact_ref)
        if (
            parent is None
            or parent[0].session_id != session_id
            or parent[0].sha256 != segmentation.mask_sha256
            or parent[0].content_type != "image/png"
            or source is None
            or source[0].session_id != session_id
            or source[0].sha256 != source_sha256
        ):
            LOGGER.info(
                "auto_rig_part_masks_unavailable reason=PARENT_MASK_INVALID archetype=%s",
                archetype.value,
            )
            return replace(segmentation, parts=())

        verified = _validate_part_masks(
            self._artifacts,
            session_id=session_id,
            parent_mask=parent[1],
            parts=segmentation.parts,
            archetype=archetype,
        )
        if len(verified) >= 2:
            LOGGER.info(
                "auto_rig_part_masks_resolved source=sam21 archetype=%s count=%s",
                archetype.value,
                len(verified),
            )
            return replace(segmentation, parts=verified)

        derived = derive_part_masks_from_subject_mask(source[1], parent[1], archetype)
        generated: list[SubjectPartSegmentationResult] = []
        for part in derived:
            descriptor = self._artifacts.put(
                session_id=session_id,
                content_type="image/png",
                body=part.mask_png,
            )
            generated.append(
                SubjectPartSegmentationResult(
                    part_id=part.part_id,
                    role=part.role,
                    source_region=part.source_region,
                    confidence=part.confidence,
                    mask_artifact_ref=descriptor.artifact_ref,
                    mask_sha256=descriptor.sha256,
                    operation="deterministic source-image part processing",
                    operation_version="1",
                )
            )
        verified_generated = _validate_part_masks(
            self._artifacts,
            session_id=session_id,
            parent_mask=parent[1],
            parts=tuple(generated),
            archetype=archetype,
        )
        if len(verified_generated) >= 2:
            LOGGER.info(
                "auto_rig_part_masks_resolved source=image_processing archetype=%s count=%s",
                archetype.value,
                len(verified_generated),
            )
        else:
            LOGGER.warning(
                "auto_rig_part_masks_unavailable reason=NO_RENDERABLE_PARTITION "
                "archetype=%s sam_candidates=%s derived_candidates=%s",
                archetype.value,
                len(segmentation.parts),
                len(derived),
            )
        return replace(segmentation, parts=verified_generated)

    def read_mask(self, capability: str) -> tuple[str, bytes, str]:
        grant = self._grants.consume(
            sha256(capability.encode("utf-8")).hexdigest(), now=self._aware_now()
        )
        if grant is None:
            raise AutoRigPackageUnavailable("derived mask capability is unavailable")
        stored = self._artifacts.get(grant.artifact_ref)
        if stored is None:
            raise AutoRigPackageUnavailable("derived mask artifact is unavailable")
        descriptor, body = stored
        if (
            descriptor.session_id != grant.session_id
            or descriptor.sha256 != grant.artifact_sha256
            or descriptor.content_type != "image/png"
            or not body.startswith(b"\x89PNG\r\n\x1a\n")
        ):
            raise AutoRigPackageUnavailable("derived mask identity mismatch")
        return descriptor.content_type, body, descriptor.sha256

    def _aware_now(self) -> datetime:
        value = self._now()
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("auto-rig clock must be timezone-aware")
        return value


def _requested_roles(archetype: RigArchetype) -> tuple[str, ...]:
    return {
        RigArchetype.BUTTERFLY: ("left-wing", "body", "right-wing"),
        RigArchetype.BIRD: ("head", "body", "wing"),
        RigArchetype.FLOWER: ("crown", "stem"),
        RigArchetype.TREE_BRANCH: ("crown", "stem"),
        RigArchetype.FISH: ("tail", "body", "head"),
        RigArchetype.BIPED: ("head", "torso", "left-leg", "right-leg"),
    }.get(archetype, ())


def _bone_for_part(role: str, archetype: RigArchetype) -> str | None:
    if role in {"body", "torso"}:
        return "root"
    if role == "wing" and archetype is RigArchetype.BIRD:
        return "wing"
    if role in {
        "left-wing",
        "right-wing",
        "head",
        "crown",
        "stem",
        "tail",
        "left-leg",
        "right-leg",
    }:
        return role
    return None


def _validate_part_masks(
    artifacts: ArtifactStore,
    *,
    session_id: str,
    parent_mask: bytes,
    parts: tuple[SubjectPartSegmentationResult, ...],
    archetype: RigArchetype,
) -> tuple[SubjectPartSegmentationResult, ...]:
    if len(parts) < 2:
        return ()
    try:
        import io

        from PIL import Image, ImageChops

        with Image.open(io.BytesIO(parent_mask)) as parent_source:
            parent = parent_source.convert("L")
        parent_count = sum(parent.histogram()[128:])
        if parent_count <= 0:
            return ()
        combined = Image.new("L", parent.size, 0)
        accepted: list[SubjectPartSegmentationResult] = []
        seen: set[str] = set()
        requested = set(_requested_roles(archetype))
        for part in parts[:4]:
            if (
                part.role not in requested
                or part.part_id in seen
                or part.confidence < 0.5
                or _bone_for_part(part.role, archetype) is None
                or part.mask_artifact_ref is None
                or part.mask_sha256 is None
            ):
                continue
            stored = artifacts.get(part.mask_artifact_ref)
            if (
                stored is None
                or stored[0].session_id != session_id
                or stored[0].sha256 != part.mask_sha256
                or stored[0].content_type != "image/png"
            ):
                continue
            with Image.open(io.BytesIO(stored[1])) as part_source:
                mask = part_source.convert("L")
            if mask.size != parent.size:
                continue
            within_parent = ImageChops.darker(mask, parent)
            part_count = sum(within_parent.histogram()[128:])
            mask_count = sum(mask.histogram()[128:])
            if (
                part_count < max(12, round(parent_count * 0.025))
                or part_count > parent_count * 0.75
                or mask_count == 0
                or (mask_count - part_count) / mask_count > 0.08
            ):
                continue
            overlap = ImageChops.darker(within_parent, combined)
            overlap_count = sum(overlap.histogram()[128:])
            if overlap_count / part_count > 0.08:
                continue
            combined = ImageChops.lighter(combined, within_parent)
            accepted.append(part)
            seen.add(part.part_id)
        coverage = sum(combined.histogram()[128:]) / parent_count
        # A part rig replaces the original silhouette with separately transformable sprites.
        # Require near-complete coverage, otherwise missing anatomy would be erased from the
        # backing image and the resulting holes would be visible during playback.
        if len(accepted) < 2 or coverage < 0.85:
            return ()
        return tuple(accepted)
    except (ImportError, OSError, ValueError):
        return ()


__all__ = ["AutoRigPackageUnavailable", "AutoRigService"]
