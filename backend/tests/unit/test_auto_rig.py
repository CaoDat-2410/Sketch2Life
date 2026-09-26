from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

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
from sketch2life.contracts.schemas.scene_exploration import SourceRegionV1
from sketch2life.infrastructure.storage.in_memory import InMemoryArtifactStore, InMemoryJobStore
from sketch2life.infrastructure.storage.in_memory_auto_rig_grants import (
    InMemoryRigPackageGrantStore,
)


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
    assert plan.duration_seconds == 12
    assert all(track.keyframes[-1].at_seconds == 12 for track in plan.tracks)


@pytest.mark.parametrize("archetype", tuple(RigArchetype))
def test_every_archetype_has_a_twelve_second_bounded_intro(archetype: RigArchetype) -> None:
    plan = build_animation_plan(
        plan_id=f"visual-{archetype}",
        session_id="session-1",
        experience_spec_ref=VersionedRefV1(id="spec-1", version=1),
        package_id=f"rig-{archetype}",
        archetype=archetype,
        learning_bridge_vi="Mình cùng khám phá tiếp nhé.",
    )

    assert plan.duration_seconds == 12
    assert all(track.keyframes[-1].at_seconds == 12 for track in plan.tracks)


def test_package_capability_is_bounded_and_returns_hash_bound_json() -> None:
    artifacts = InMemoryArtifactStore()
    service = AutoRigService(
        artifacts=artifacts,
        grants=InMemoryRigPackageGrantStore(),
        jobs=InMemoryJobStore(),
        now=lambda: datetime(2026, 9, 25, 6, 0, tzinfo=UTC),
    )

    package, plan, capability, expires_at, digest = service.prepare_template_package(
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

    content_type, body, observed_digest = service.read_package(capability)
    decoded = json.loads(body)
    assert content_type == "application/vnd.sketch2life.rig-package+json"
    assert observed_digest == digest
    assert decoded["packageId"] == package.package_id
    assert decoded["originalArtPreserved"] is True
    assert package.tier is RigDeliveryTier.CUTOUT_MICRO_MOTION
    assert plan.package_id == package.package_id
    assert expires_at > datetime(2026, 9, 25, 6, 0, tzinfo=UTC)

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


def test_successful_gate_a_segmentation_promotes_full_rig_tier() -> None:
    artifacts = InMemoryArtifactStore()
    mask = artifacts.put(session_id="session-1", content_type="image/png", body=b"mask")
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
        source_artifact_ref="artifact:source",
        source_sha256="a" * 64,
        target_id="anchor-bird",
        target_label="con chim",
        target_confidence=0.94,
        semantic_tags=("animal",),
    )
    package, plan, *_ = service.prepare_template_package(
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

    assert job.status == "SUCCEEDED"
    assert package.tier is RigDeliveryTier.FULL_AUTO_RIG
    assert package.rig is not None
    assert package.rig.source_region.x == 0.2
    assert plan.tier is RigDeliveryTier.FULL_AUTO_RIG
