from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from io import BytesIO

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from sketch2life.application.ports.segmentation import (
    SubjectPartSegmentationResult,
    SubjectSegmentationRequest,
    SubjectSegmentationResult,
)
from sketch2life.application.services.auto_rig import (
    AutoRigPackageUnavailable,
    AutoRigService,
    build_animation_plan,
    build_template_rig,
    classify_archetype,
    validate_rig_geometry,
)
from sketch2life.contracts.schemas.auto_rig import RigArchetype, RigDeliveryTier
from sketch2life.contracts.schemas.p1_experience import VersionedRefV1
from sketch2life.contracts.schemas.renderer_v2 import PixiRendererLaunchV2
from sketch2life.contracts.schemas.scene_exploration import SourceRegionV1
from sketch2life.infrastructure.storage.in_memory import InMemoryArtifactStore, InMemoryJobStore
from sketch2life.infrastructure.storage.in_memory_auto_rig_grants import (
    InMemoryRigPackageGrantStore,
)
from sketch2life.interfaces.http.routers.supervised_flow import renderer_source_router


def _small_fixture_png(*, mask: bool) -> bytes:
    image = Image.new("L" if mask else "RGB", (8, 8), 0 if mask else "white")
    if mask:
        ImageDraw.Draw(image).rectangle((3, 3, 4, 4), fill=255)
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


_TINY_PNG = _small_fixture_png(mask=True)
_SOURCE_PNG = _small_fixture_png(mask=False)


@pytest.mark.parametrize(
    ("label", "expected"),
    [
        ("con bướm", RigArchetype.BUTTERFLY),
        ("con chim", RigArchetype.BIRD),
        ("bông hoa", RigArchetype.FLOWER),
        ("cành cây", RigArchetype.TREE_BRANCH),
        ("con cá", RigArchetype.FISH),
        ("bé gái", RigArchetype.BIPED),
        ("ngôi nhà", RigArchetype.RIGID),
        ("vật thể lạ", RigArchetype.UNKNOWN),
        ("chú chó corgi", RigArchetype.GENERIC_ORGANIC),
        ("con mèo", RigArchetype.GENERIC_ORGANIC),
    ],
)
def test_archetype_registry_covers_named_and_unknown_topics(
    label: str, expected: RigArchetype
) -> None:
    assert classify_archetype(label) is expected


def test_template_rig_has_valid_bounded_geometry_and_weights() -> None:
    rig = build_template_rig(
        archetype=RigArchetype.BUTTERFLY,
        source_region=SourceRegionV1(x=0.1, y=0.1, width=0.8, height=0.8),
    )

    assert len(rig.vertices) == 25
    assert len(rig.triangles) == 32
    assert validate_rig_geometry(rig) == ()
    assert all(
        abs(sum(item.weight for item in weights.influences) - 1) < 1e-5 for weights in rig.weights
    )


def test_motion_plan_targets_only_known_archetype_bones() -> None:
    rig = build_template_rig(
        archetype=RigArchetype.BIRD,
        source_region=SourceRegionV1(x=0, y=0, width=1, height=1),
    )
    plan = build_animation_plan(
        plan_id="visual-spec-1",
        session_id="session-1",
        experience_spec_ref=VersionedRefV1(id="spec-1", version=1),
        package_id="rig-session-1-1",
        archetype=RigArchetype.BIRD,
        learning_bridge_vi="Chim chọn nơi nào để sống nhỉ?",
        tier=RigDeliveryTier.CUTOUT_MICRO_MOTION,
    )

    assert {track.bone_id for track in plan.tracks}.issubset({bone.bone_id for bone in rig.bones})
    assert plan.max_motion_level == 2
    assert plan.duration_seconds == 20
    assert all(track.keyframes[-1].at_seconds == 14.4 for track in plan.tracks)


@pytest.mark.parametrize("archetype", tuple(RigArchetype))
def test_every_archetype_has_a_twenty_second_intro_and_still_rest(archetype: RigArchetype) -> None:
    plan = build_animation_plan(
        plan_id=f"visual-{archetype}",
        session_id="session-1",
        experience_spec_ref=VersionedRefV1(id="spec-1", version=1),
        package_id=f"rig-{archetype}",
        archetype=archetype,
        learning_bridge_vi="Mình cùng khám phá tiếp nhé.",
    )

    assert plan.duration_seconds == 20
    assert all(track.keyframes[-1].at_seconds == 14.4 for track in plan.tracks)


@pytest.mark.parametrize("archetype", tuple(RigArchetype))
def test_every_cutout_plan_has_visible_root_translation_without_zoom_or_rotation(
    archetype: RigArchetype,
) -> None:
    plan = build_animation_plan(
        plan_id="cutout-motion", session_id="session-cutout",
        experience_spec_ref=VersionedRefV1(id="spec-cutout", version=1),
        package_id="package-cutout", archetype=archetype,
        learning_bridge_vi="Cùng xem bức tranh nhé.", tier=RigDeliveryTier.CUTOUT_MICRO_MOTION,
    )
    assert len(plan.tracks) == 1
    assert plan.tracks[0].bone_id == "root"
    assert any(abs(frame.pose.translate_y) >= 0.018 for frame in plan.tracks[0].keyframes)
    assert all(
        frame.pose.scale_x == frame.pose.scale_y == 1 and frame.pose.rotation_degrees == 0
        for frame in plan.tracks[0].keyframes
    )
    assert plan.tracks[0].keyframes[-1].pose.translate_y == 0


def test_package_capability_is_bounded_and_returns_hash_bound_json() -> None:
    artifacts = InMemoryArtifactStore()
    service = AutoRigService(
        artifacts=artifacts,
        grants=InMemoryRigPackageGrantStore(),
        jobs=InMemoryJobStore(),
        now=lambda: datetime(2026, 9, 25, 6, 0, tzinfo=UTC),
    )

    package, plan, capability, expires_at, digest, mask_capability, part_mask_reads = (
        service.prepare_template_package(
            session_id="session-1",
            source_artifact_ref="artifact:source",
            source_sha256="a" * 64,
            target_id="anchor-bird",
            target_label="con chim",
            target_confidence=0.94,
            semantic_tags=("animal",),
            experience_spec_ref=VersionedRefV1(id="spec-1", version=1),
            learning_bridge_vi="Chim chọn nơi nào để sống nhỉ?",
        )
    )

    content_type, body, observed_digest = service.read_package(capability)
    decoded = json.loads(body)
    assert content_type == "application/vnd.sketch2life.rig-package+json"
    assert observed_digest == digest
    assert decoded["packageId"] == package.package_id
    assert decoded["originalArtPreserved"] is True
    assert package.tier is RigDeliveryTier.CUTOUT_MICRO_MOTION
    assert plan.package_id == package.package_id
    assert expires_at > datetime(2026, 9, 25, 6, 0, tzinfo=UTC)
    assert mask_capability is None
    assert part_mask_reads == ()

    service.read_package(capability)
    with pytest.raises(AutoRigPackageUnavailable):
        service.read_package(capability)


def test_gate_a_preparation_is_idempotent_and_uses_safe_partial_tier() -> None:
    service = AutoRigService(
        artifacts=InMemoryArtifactStore(),
        grants=InMemoryRigPackageGrantStore(),
        jobs=InMemoryJobStore(),
        now=lambda: datetime(2026, 9, 25, 6, 0, tzinfo=UTC),
    )

    first = service.start_gate_a_preparation(session_id="session-1", request_id="request-1")
    replay = service.start_gate_a_preparation(session_id="session-1", request_id="request-2")

    assert replay == first
    assert first.status == "PARTIAL_SUCCESS"
    assert first.selected_tier is RigDeliveryTier.CUTOUT_MICRO_MOTION
    assert first.failure_code == "SEGMENTATION_ADAPTER_UNAVAILABLE"


class _FixtureSegmenter:
    def __init__(
        self,
        mask_artifact_ref: str | None = None,
        mask_sha256: str | None = None,
    ) -> None:
        self.mask_artifact_ref = mask_artifact_ref
        self.mask_sha256 = mask_sha256

    def segment(self, request: SubjectSegmentationRequest) -> SubjectSegmentationResult:
        assert request.target_label == "con chim"
        return SubjectSegmentationResult(
            source_region=SourceRegionV1(x=0.2, y=0.1, width=0.5, height=0.7),
            confidence=0.92,
            adapter_id="fixture-segmenter",
            adapter_version="1",
            mask_artifact_ref=self.mask_artifact_ref,
            mask_sha256=self.mask_sha256,
            parts=(
                SubjectPartSegmentationResult(
                    part_id="body",
                    role="body",
                    source_region=SourceRegionV1(x=0.25, y=0.15, width=0.4, height=0.5),
                    confidence=0.9,
                ),
            ),
        )


def test_part_metadata_without_renderer_mask_handoff_stays_at_cutout_tier() -> None:
    artifacts = InMemoryArtifactStore()
    source = artifacts.put(session_id="session-1", content_type="image/png", body=_SOURCE_PNG)
    mask = artifacts.put(session_id="session-1", content_type="image/png", body=_TINY_PNG)
    service = AutoRigService(
        artifacts=artifacts,
        grants=InMemoryRigPackageGrantStore(),
        jobs=InMemoryJobStore(),
        segmenter=_FixtureSegmenter(mask.artifact_ref, mask.sha256),
        now=lambda: datetime(2026, 9, 25, 6, 0, tzinfo=UTC),
    )
    job = service.start_gate_a_preparation(
        session_id="session-1",
        request_id="request-1",
        source_artifact_ref=source.artifact_ref,
        source_sha256=source.sha256,
        target_id="anchor-bird",
        target_label="con chim",
        target_confidence=0.94,
        semantic_tags=("animal",),
    )
    package, plan, *_ = service.prepare_template_package(
        session_id="session-1",
        source_artifact_ref=source.artifact_ref,
        source_sha256=source.sha256,
        target_id="anchor-bird",
        target_label="con chim",
        target_confidence=0.94,
        semantic_tags=("animal",),
        experience_spec_ref=VersionedRefV1(id="spec-1", version=1),
        learning_bridge_vi="Chim chọn nơi nào để sống nhỉ?",
    )

    assert job.status == "PARTIAL_SUCCESS"
    assert job.failure_code == "SEGMENTATION_PARTS_UNAVAILABLE"
    assert package.tier is RigDeliveryTier.CUTOUT_MICRO_MOTION
    assert package.rig is not None
    assert package.rig.source_region.x == 0.2
    assert plan.tier is RigDeliveryTier.CUTOUT_MICRO_MOTION


class _SubjectOnlySegmenter:
    def __init__(self, mask_artifact_ref: str, mask_sha256: str) -> None:
        self.mask_artifact_ref = mask_artifact_ref
        self.mask_sha256 = mask_sha256

    def segment(self, request: SubjectSegmentationRequest) -> SubjectSegmentationResult:
        return SubjectSegmentationResult(
            source_region=SourceRegionV1(x=0.2, y=0.1, width=0.5, height=0.7),
            confidence=0.92,
            adapter_id="fixture-sam21",
            adapter_version="1",
            mask_artifact_ref=self.mask_artifact_ref,
            mask_sha256=self.mask_sha256,
        )


def _png_bytes(image: Image.Image) -> bytes:
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def test_oversized_subject_mask_never_gets_a_renderer_capability() -> None:
    artifacts = InMemoryArtifactStore()
    source = artifacts.put(session_id="session-invalid", content_type="image/png", body=_SOURCE_PNG)
    invalid_mask = _png_bytes(Image.new("L", (8, 8), 255))
    parent = artifacts.put(
        session_id="session-invalid", content_type="image/png", body=invalid_mask
    )
    service = AutoRigService(
        artifacts=artifacts,
        grants=InMemoryRigPackageGrantStore(),
        jobs=InMemoryJobStore(),
        segmenter=_SubjectOnlySegmenter(parent.artifact_ref, parent.sha256),
    )
    job = service.start_gate_a_preparation(
        session_id="session-invalid", request_id="request-invalid",
        source_artifact_ref=source.artifact_ref, source_sha256=source.sha256,
        target_id="butterfly", target_label="con bướm", target_confidence=0.9,
    )
    package, _plan, _cap, _expires, _sha, mask_cap, part_reads = service.prepare_template_package(
        session_id="session-invalid", source_artifact_ref=source.artifact_ref,
        source_sha256=source.sha256, target_id="butterfly", target_label="con bướm",
        target_confidence=0.9, semantic_tags=(),
        experience_spec_ref=VersionedRefV1(id="spec-invalid", version=1),
        learning_bridge_vi="Cùng xem đôi cánh nhé.",
    )
    assert job.failure_code == "MASK_AREA_INVALID"
    assert job.status != "SUCCEEDED"
    assert mask_cap is None
    assert part_reads == ()
    assert package.parts == ()
    assert package.derived_artifacts == ()
    assert artifacts.get(source.artifact_ref)[1] == _SOURCE_PNG


def test_subject_only_butterfly_mask_is_partitioned_and_promoted_with_part_capabilities() -> None:
    source_image = Image.new("RGB", (100, 100), "white")
    source_draw = ImageDraw.Draw(source_image)
    source_draw.ellipse((10, 20, 45, 68), fill=(235, 120, 30))
    source_draw.ellipse((55, 20, 90, 68), fill=(235, 120, 30))
    source_draw.rectangle((44, 32, 56, 82), fill=(20, 130, 240))
    source_png = _png_bytes(source_image)
    mask = Image.new("L", (100, 100), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((10, 20, 45, 68), fill=255)
    mask_draw.ellipse((55, 20, 90, 68), fill=255)
    mask_draw.rectangle((44, 32, 56, 82), fill=255)
    mask_png = _png_bytes(mask)

    artifacts = InMemoryArtifactStore()
    source = artifacts.put(session_id="session-parts", content_type="image/png", body=source_png)
    parent = artifacts.put(session_id="session-parts", content_type="image/png", body=mask_png)
    service = AutoRigService(
        artifacts=artifacts,
        grants=InMemoryRigPackageGrantStore(),
        jobs=InMemoryJobStore(),
        segmenter=_SubjectOnlySegmenter(parent.artifact_ref, parent.sha256),
        now=lambda: datetime(2026, 9, 25, 6, 0, tzinfo=UTC),
    )

    job = service.start_gate_a_preparation(
        session_id="session-parts",
        request_id="request-parts",
        source_artifact_ref=source.artifact_ref,
        source_sha256=hashlib.sha256(source_png).hexdigest(),
        target_id="anchor-butterfly",
        target_label="con bướm",
        target_confidence=0.94,
        semantic_tags=("animal",),
    )
    package, plan, _package_cap, _expires, _package_sha, _parent_cap, part_reads = (
        service.prepare_template_package(
            session_id="session-parts",
            source_artifact_ref=source.artifact_ref,
            source_sha256=hashlib.sha256(source_png).hexdigest(),
            target_id="anchor-butterfly",
            target_label="con bướm",
            target_confidence=0.94,
            semantic_tags=("animal",),
            experience_spec_ref=VersionedRefV1(id="spec-parts", version=1),
            learning_bridge_vi="Cùng xem đôi cánh chuyển động nhé.",
        )
    )

    assert job.status == "SUCCEEDED"
    assert package.tier is RigDeliveryTier.FULL_AUTO_RIG
    assert {part.part_id for part in package.parts} == {"left-wing", "body", "right-wing"}
    assert len(part_reads) == 3
    assert plan.duration_seconds == 20
    for part_read in part_reads:
        content_type, body, digest = service.read_mask(part_read.read_capability)
        assert content_type == "image/png"
        assert hashlib.sha256(body).hexdigest() == digest == part_read.sha256


def test_successful_subject_only_mask_gets_separate_bounded_renderer_capability() -> None:
    artifacts = InMemoryArtifactStore()
    source = artifacts.put(session_id="session-1", content_type="image/png", body=_SOURCE_PNG)
    mask = artifacts.put(session_id="session-1", content_type="image/png", body=_TINY_PNG)
    service = AutoRigService(
        artifacts=artifacts,
        grants=InMemoryRigPackageGrantStore(),
        jobs=InMemoryJobStore(),
        segmenter=_SubjectOnlySegmenter(mask.artifact_ref, mask.sha256),
        now=lambda: datetime(2026, 9, 25, 6, 0, tzinfo=UTC),
    )
    job = service.start_gate_a_preparation(
        session_id="session-1",
        request_id="request-1",
        source_artifact_ref=source.artifact_ref,
        source_sha256=source.sha256,
        target_id="anchor-butterfly",
        target_label="con bướm",
        target_confidence=0.94,
        semantic_tags=("animal",),
    )
    package, plan, package_capability, package_expires_at, package_digest, mask_capability, _ = (
        service.prepare_template_package(
            session_id="session-1",
            source_artifact_ref=source.artifact_ref,
            source_sha256=source.sha256,
            target_id="anchor-butterfly",
            target_label="con bướm",
            target_confidence=0.94,
            semantic_tags=("animal",),
            experience_spec_ref=VersionedRefV1(id="spec-1", version=1),
            learning_bridge_vi="Mình cùng khám phá đôi cánh nhé.",
        )
    )

    assert job.status == "PARTIAL_SUCCESS"
    assert package.tier is RigDeliveryTier.CUTOUT_MICRO_MOTION
    assert mask_capability is not None
    launch = PixiRendererLaunchV2(
        contractName="PixiRendererLaunchV2",
        contractVersion="2.0",
        sessionId="session-1",
        expectedSessionVersion=4,
        experienceSpecRef={"id": "spec-1", "version": 1},
        sourceReadEndpoint="/v1/renderer/source",
        sourceReadCapability="s" * 48,
        sourceSha256=source.sha256,
        packageReadEndpoint="/v1/renderer/rig-package",
        packageReadCapability=package_capability,
        packageSha256=package_digest,
        packageReadExpiresAt=package_expires_at,
        maskReadEndpoint="/v1/renderer/rig-mask",
        maskReadCapability=mask_capability,
        maskSha256=package.derived_artifacts[0].sha256,
        animationPlan=plan,
        fallbackLaunch={"contractName": "PixiRendererLaunchV1"},
    )
    assert launch.mask_read_capability == mask_capability
    app = FastAPI()
    app.state.auto_rig_service = service
    app.include_router(renderer_source_router)
    response = TestClient(app).get(
        "/v1/renderer/rig-mask",
        headers={"X-Rig-Mask-Capability": mask_capability},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.headers["x-content-sha256"] == mask.sha256
    assert response.content == _TINY_PNG
    service.read_mask(mask_capability)  # bounded explicit renderer retry
    with pytest.raises(AutoRigPackageUnavailable):
        service.read_mask(mask_capability)
