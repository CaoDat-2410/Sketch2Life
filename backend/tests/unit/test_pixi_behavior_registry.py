from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

from sketch2life.domain.experience.pixi_behavior_registry import (
    BEHAVIOR_REGISTRY_V1,
    BehaviorClassId,
    MotionReadiness,
    NoMotionOutcomeId,
    SubjectFamilyId,
    behavior_is_compatible,
    is_behavior_runtime_selectable,
    supported_behavior_ids,
    topic_subject_profile,
)

_ROOT = Path(__file__).resolve().parents[3]
_CATALOG = (
    _ROOT
    / "features"
    / "FEAT-028-pixi-topic-asset-library"
    / "assets"
    / "generated"
    / "asset-catalog.v2.json"
)
_MOTION_MANIFEST = (
    _ROOT
    / "features"
    / "FEAT-028-pixi-topic-asset-library"
    / "assets"
    / "generated"
    / "motion-cycle-review-manifest.rev1.json"
)


def test_every_current_topic_has_a_closed_family_and_truthful_motion_or_static_outcome() -> None:
    catalog = json.loads(_CATALOG.read_text(encoding="utf-8"))
    assets = catalog["assets"]

    assert len(assets) == 144
    for asset in assets:
        profile = topic_subject_profile(asset["assetId"])
        assert profile.subject_family_id is not SubjectFamilyId.UNKNOWN, asset["assetId"]
        assert profile.static_only is (not profile.behavior_capability_ids), asset["assetId"]
        for behavior in profile.behavior_capability_ids:
            assert behavior_is_compatible(profile.subject_family_id, behavior), (
                asset["assetId"],
                profile.subject_family_id,
                behavior,
            )


def test_registry_has_closed_motion_classes_and_cycle_ids_but_enables_none_before_gates() -> None:
    assert len(BEHAVIOR_REGISTRY_V1) == len(BehaviorClassId)
    assert len({item.behavior_class_id for item in BEHAVIOR_REGISTRY_V1}) == len(
        BEHAVIOR_REGISTRY_V1
    )
    assert all(item.cycle_ids for item in BEHAVIOR_REGISTRY_V1)
    assert all(
        item.readiness is not MotionReadiness.RUNTIME_ELIGIBLE for item in BEHAVIOR_REGISTRY_V1
    )
    assert len({cycle_id for item in BEHAVIOR_REGISTRY_V1 for cycle_id in item.cycle_ids}) == 37
    assert supported_behavior_ids() == ()
    assert not is_behavior_runtime_selectable("topic.animal.songbird.v1", BehaviorClassId.FLYER)


def test_every_behavior_cycle_has_a_provenance_record_and_remains_gated() -> None:
    manifest = json.loads(_MOTION_MANIFEST.read_text(encoding="utf-8"))
    cycles = {item["cycleId"]: item for item in manifest["cycles"]}
    expected = {cycle_id for item in BEHAVIOR_REGISTRY_V1 for cycle_id in item.cycle_ids}

    assert expected == set(cycles)
    assert len(cycles) == len(manifest["cycles"])
    assert manifest["runtimeEligible"] is False
    assert manifest["catalogIntegration"] is False
    assert manifest["commonGates"]["alphaChannelPresent"] is True
    assert manifest["commonGates"]["transparentCanvasCornersVerified"] is True
    assert manifest["commonGates"]["generationPromptRecordStatus"].startswith("SUMMARY_ONLY")
    assert manifest["commonGates"]["runtimeEligible"] is False
    for cycle_id in expected:
        record = cycles[cycle_id]
        definition = next(item for item in BEHAVIOR_REGISTRY_V1 if cycle_id in item.cycle_ids)
        assert record["behaviorClassId"] == definition.behavior_class_id.value
        image_path = _MOTION_MANIFEST.parent / record["assetFile"]
        content = image_path.read_bytes()
        assert hashlib.sha256(content).hexdigest().upper() == record["sha256"].upper(), cycle_id
        assert record["frameCount"] == 4
        assert struct.unpack(">II", content[16:24]) == tuple(record["canvas"]), cycle_id
        assert content[25] == 6, cycle_id  # PNG truecolor + alpha (RGBA)


def test_topic_taxonomy_uses_distinct_morphologies_and_people_have_motion_capabilities() -> None:
    child = topic_subject_profile("topic.person.child-a.v1")
    assert child.behavior_capability_ids == (
        BehaviorClassId.WALKER_BIPED,
        BehaviorClassId.RUNNER_BIPED,
        BehaviorClassId.WAVER,
        BehaviorClassId.REACHER,
        BehaviorClassId.DANCER,
        BehaviorClassId.TURNER,
    )

    snail = topic_subject_profile("topic.insects-small-creatures.snail.v1")
    assert snail.subject_family_id is SubjectFamilyId.MOLLUSK
    assert snail.rig_archetype_id.value == "generic_organic"
    assert snail.behavior_capability_ids == (BehaviorClassId.CRAWLER,)

    whale = topic_subject_profile("topic.ocean-life.whale.v1")
    assert whale.rig_archetype_id.value == "aquatic_mammal"

    pteranodon = topic_subject_profile("topic.dinosaurs-prehistory.pteranodon.v1")
    assert pteranodon.subject_family_id.value == "animal.reptile_amphibian"
    assert pteranodon.behavior_capability_ids == (BehaviorClassId.FLYER, BehaviorClassId.GLIDER)


def test_subjects_keep_multiple_capabilities_and_unknown_topics_fail_closed() -> None:
    bird = topic_subject_profile("topic.animal.songbird.v1")
    assert bird.behavior_capability_ids == (
        BehaviorClassId.FLYER,
        BehaviorClassId.GLIDER,
        BehaviorClassId.WALKER_AVIAN,
    )
    assert topic_subject_profile("topic.unknown.new-creature.v9").subject_family_id is (
        SubjectFamilyId.UNKNOWN
    )


def test_static_companions_do_not_gain_a_motion_capability_from_their_labels() -> None:
    profile = topic_subject_profile("topic.place.school.v1")
    assert profile.static_only is True
    assert profile.behavior_capability_ids == ()
    assert profile.no_motion_outcome_id is NoMotionOutcomeId.STILL
    assert topic_subject_profile("topic.unknown.new-creature.v9").no_motion_outcome_id is (
        NoMotionOutcomeId.UNKNOWN
    )


def test_domain_registry_does_not_import_application_or_contract_layers() -> None:
    source = (
        _ROOT
        / "backend"
        / "src"
        / "sketch2life"
        / "domain"
        / "experience"
        / "pixi_behavior_registry.py"
    ).read_text(encoding="utf-8")
    assert "sketch2life.application" not in source
    assert "sketch2life.contracts" not in source
