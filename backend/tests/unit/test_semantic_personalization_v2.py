from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from sketch2life.application.services.backend_ai_workflow import (
    BackendAiWorkflow,
    BackendWorkflowRequest,
)
from sketch2life.application.services.scene_understanding import (
    SceneCandidateV2Input,
    build_confirmed_scene_understanding,
)
from sketch2life.application.services.semantic_personalization_v2 import (
    to_backend_workflow_result_v2,
)
from sketch2life.contracts.schemas.asr import (
    AsrAudioReferenceV1,
    AsrProfileId,
    AsrQualityMetadataV1,
    AsrSegmentV1,
    AsrSpeechDiagnostic,
    AsrSuccessV1,
)
from sketch2life.contracts.schemas.vision import VisionImageReferenceV1
from sketch2life.contracts.schemas.vision_v2 import (
    VisionUnderstandingSuccessV2,
    vision_profile_catalog_hash_v2,
    vision_profile_catalog_v2,
    vision_profile_config_hash_v2,
)
from sketch2life.infrastructure.catalog.activity_coverage import (
    build_activity_coverage_report,
)
from sketch2life.infrastructure.catalog.activity_semantics_v2 import (
    load_activity_semantic_catalog_v2,
)
from sketch2life.interfaces.cli.workflow_demo import (
    _error_manifest,
    build_real_workflow_dependencies,
)


def _scene(*labels: str, transcript: str = ""):
    candidates = tuple(
        SceneCandidateV2Input(
            label_vi=label,
            kind="subject",
            confidence=0.8,
            claim_ids=(f"vision:{index}",),
            source_kind="VLM",
        )
        for index, label in enumerate(labels)
    )
    return build_confirmed_scene_understanding(
        scene_understanding_id="",
        image_artifact_ref="input.png",
        image_sha256="a" * 64,
        audio_artifact_ref="narration.wav",
        audio_sha256="b" * 64,
        candidates=candidates,
        asr_transcript_vi=transcript,
    )


def test_v2_catalog_preserves_100_unique_curated_activity_profiles() -> None:
    catalog = load_activity_semantic_catalog_v2(Path.cwd())
    assert len(catalog.profiles) == 100
    assert len({profile.activity_id for profile in catalog.profiles}) == 100
    assert all(profile.production_eligible is False for profile in catalog.profiles)


def test_catalog_uses_canonical_template_activity_version() -> None:
    catalog = load_activity_semantic_catalog_v2(Path.cwd())

    assert catalog.profile_for("ACT-0023").activity_version == 2
    assert catalog.profile_for("ACT-0091").activity_version == 2


def test_activity_coverage_report_exposes_catalog_gaps_without_creating_records() -> None:
    catalog = load_activity_semantic_catalog_v2(Path.cwd())

    report = build_activity_coverage_report(catalog, minimum_candidates_per_concept_age=3)

    assert report.profile_count == 100
    assert report.gaps
    assert 0.0 <= report.coverage_ratio <= 1.0
    assert report.model_dump()["profile_count"] == 100


def test_scene_understanding_is_stable_and_age_invariant() -> None:
    first = _scene("con bướm", "bông hoa", transcript="Đây là con bướm")
    second = _scene("con bướm", "bông hoa", transcript="Đây là con bướm")
    assert first.scene_sha256 == second.scene_sha256
    assert first.scene_understanding_id == second.scene_understanding_id
    assert first.primary_concept.concept_id == "ANIMAL_BUTTERFLY"
    assert tuple(concept.concept_id for concept in first.secondary_concepts) == ("PLANT_FLOWER",)


def test_asr_child_interest_beats_visual_route_order() -> None:
    scene = _scene(
        "con bướm",
        "mặt trời",
        transcript="Con đang kể về mặt trời",
    )

    assert scene.primary_concept.concept_id == "SUN_LIGHT"
    assert scene.primary_concept.concept_role == "PRIMARY_CHILD_INTEREST"
    assert scene.child_interest_concept_id == "SUN_LIGHT"
    assert scene.asr_vlm_resolution == "ASR_AND_VLM_AGREE"
    assert all(concept.concept_id != "SUN_LIGHT" for concept in scene.secondary_concepts)


def test_concept_matching_restores_nature_and_sun_routes() -> None:
    catalog = load_activity_semantic_catalog_v2(Path.cwd())
    butterfly_flower = _scene("con bướm", "bông hoa", transcript="Con bướm bay tới bông hoa")
    sun = _scene("mặt trời", transcript="Đây là mặt trời")
    flower_match = catalog.match_scene(butterfly_flower, catalog.profile_for("ACT-0055"))
    sun_match = catalog.match_scene(sun, catalog.profile_for("ACT-0091"))
    assert flower_match is not None
    assert flower_match.match_mode == "PERSONALIZED_CONCEPT"
    assert "PLANT_FLOWER" in flower_match.matched_concept_ids
    assert sun_match is not None
    assert sun_match.match_mode == "PERSONALIZED_CONCEPT"
    assert sun_match.semantic_relevance >= 90


def test_variant_objective_identity_is_carried_into_semantic_match() -> None:
    catalog = load_activity_semantic_catalog_v2(Path.cwd(), include_expansion=True)
    profile = catalog.profile_for("ACT-0123")
    match = catalog.match_scene(
        _scene("bông hoa", transcript="Con đang quan sát bông hoa"),
        profile,
    )

    assert profile.primary_objective_id == "OBJ_SCIENTIFIC_OBSERVATION"
    assert profile.secondary_objective_ids == ("OBJ_INDEPENDENCE_SELF_CARE",)
    assert match is not None
    assert match.selected_objective_id == "OBJ_SCIENTIFIC_OBSERVATION"
    assert match.matched_objective_ids == (
        "OBJ_SCIENTIFIC_OBSERVATION",
        "OBJ_INDEPENDENCE_SELF_CARE",
    )
    assert match.objective_activity_alignment == 1.0


def test_butterfly_variants_encode_age_objective_and_continuity_policy() -> None:
    catalog = load_activity_semantic_catalog_v2(Path.cwd(), include_expansion=True)
    scene = _scene("con bướm", transcript="Con bướm đang bay")

    infant = catalog.profile_for("ACT-0113")
    extension = catalog.profile_for("ACT-0116")
    infant_match = catalog.match_scene(scene, infant)
    extension_match = catalog.match_scene(scene, extension)

    assert infant.primary_objective_id == "OBJ_MOVEMENT_COORDINATION"
    assert infant.secondary_objective_ids == ("OBJ_SENSORIAL_DISCRIMINATION",)
    assert infant_match is not None
    assert infant_match.continuity_mode == "DIRECT_CONTINUATION"
    assert infant_match.planned_video_continuity_score > 0.8
    assert extension_match is not None
    assert extension_match.continuity_mode == "RELATED_EXPANSION"
    assert extension_match.expansion_bridge_required is True
    assert extension_match.semantic_relevance < infant_match.semantic_relevance
    assert "RELATED_EXPANSION" in extension_match.reason_codes
    assert "TOPIC_NOT_DIRECTLY_OBSERVED" in extension_match.reason_codes


def test_unrelated_activity_uses_explicit_age_baseline_fallback() -> None:
    catalog = load_activity_semantic_catalog_v2(Path.cwd())
    scene = _scene("con bướm", transcript="Con bướm đang bay")
    match = catalog.match_scene(scene, catalog.profile_for("ACT-0058"))
    assert match is None
    baseline = catalog.match_scene(scene, catalog.profile_for("ACT-0001"))
    assert baseline is not None
    assert baseline.match_mode == "AGE_BASELINE_FALLBACK"
    assert baseline.fallback_reason


def test_v2_result_bridge_keeps_failed_age_bands_explicit() -> None:
    legacy = _error_manifest(
        Path.cwd(),
        "missing-image.png",
        "missing-audio.wav",
        ("0-3", "3-6", "6-9", "9-12"),
        "RUNTIME_NOT_READY",
        ("TEST_PRELIGHT_FAILURE",),
    )
    result = to_backend_workflow_result_v2(legacy)
    assert result.contract_name == "BackendWorkflowResultV2"
    assert result.status == "FAILED"
    assert result.personalized_band_count == 0
    assert result.fallback_band_count == 0
    assert result.unavailable_age_bands == ("0-3", "3-6", "6-9", "9-12")
    assert result.scene_understanding.primary_concept.concept_id == "UNCLASSIFIED_OBSERVATION"
    assert result.scene_understanding.gate_a_status == "UNAVAILABLE"
    assert result.scene_understanding.adult_confirmation_actor is None
    assert result.manifest_sha256
def test_run_v2_shares_scene_and_reports_personalized_or_fallback_modes() -> None:
    root = Path(__file__).resolve().parents[3]
    image = root / "features/FEAT-020-backend-ai-workflow-demo/test-assets/input-image.png"
    audio = root / "features/FEAT-020-backend-ai-workflow-demo/test-assets/narration.wav"
    now = datetime(2026, 9, 13, 12, tzinfo=UTC)
    digest = "a" * 64
    asr_result = AsrSuccessV1(
        correlation_id="unit-v2",
        executed_at=now,
        source_audio_ref=AsrAudioReferenceV1(artifact_ref="narration.wav", sha256=digest),
        profile_id=AsrProfileId.WHISPER_TURBO_INT8_AUTO_V1,
        attempt_number=1,
        repair_attempted=False,
        transcript_raw="Đây là mặt trời",
        speech_diagnostic=AsrSpeechDiagnostic.DETECTED,
        detected_language="vi",
        language_probability=0.99,
        segments=(
            AsrSegmentV1(
                index=0,
                start_seconds=0,
                end_seconds=1,
                text="Đây là mặt trời",
            ),
        ),
        input_duration_seconds=1.1,
        vad_enabled=False,
        model_identifier="unit-model",
        model_revision="unit-revision",
        adapter_version="unit-adapter",
        runtime_version="unit-runtime",
        config_hash=digest,
        quality_metadata=AsrQualityMetadataV1(
            media_validation_artifact_ref="unit:validation",
            media_validation_artifact_sha256=digest,
        ),
    )
    profile = vision_profile_catalog_v2().profiles[0]
    vision_result = VisionUnderstandingSuccessV2(
        correlation_id="unit-v2",
        executed_at=now,
        source_image_ref=VisionImageReferenceV1(artifact_ref="input.png", sha256=digest),
        profile_id=profile.profile_id,
        profile_catalog_hash=vision_profile_catalog_hash_v2(vision_profile_catalog_v2()),
        attempt_number=1,
        repair_attempted=False,
        content_policy_version="unit-policy",
        policy_match_view_version="unit-view",
        policy_execution_state="PASSED",
        entities=(),
        actions=(),
        relations=(),
        themes=(),
        ambiguous_regions=(),
        adapter_version=profile.adapter_version,
        config_hash=vision_profile_config_hash_v2(profile),
        model_provenance=profile.model_provenance,
    )

    class FakeAsr:
        def transcribe(self, _request: object) -> AsrSuccessV1:
            return asr_result

    class FakeVision:
        def understand(self, _request: object) -> VisionUnderstandingSuccessV2:
            return vision_result

    result = BackendAiWorkflow(
        asr=FakeAsr(),
        vision=FakeVision(),
        dependencies=build_real_workflow_dependencies(root, include_expansion=True),
        clock=lambda: now,
    ).run_v2(
        BackendWorkflowRequest(
            image_path=image,
            narration_audio_path=audio,
            repo_root=root,
            age_bands=("0-3", "3-6", "6-9", "9-12"),
            seed=123,
            demo_autopilot=True,
            report_partial_test_only=True,
            emit_debug_evidence=True,
        )
    )

    assert result.status == "SUCCEEDED"
    assert result.terminal_status == "BACKEND_CONTEXT_READY"
    assert result.scene_understanding.primary_concept.concept_id == "SUN_LIGHT"
    assert {
        band.scene_understanding_id for band in result.age_bands
    } == {result.scene_understanding.scene_understanding_id}
    assert result.personalized_band_count == 4
    assert result.fallback_band_count == 0
    assert result.unavailable_age_bands == ()
    assert all(
        band.status == "SUCCEEDED"
        and band.experience_spec is not None
        for band in result.age_bands
    )
    for band in result.age_bands:
        assert band.experience_spec is not None
        assert band.experience_spec.continuity is not None
        assert band.experience_spec.continuity.actual_video_status == "NOT_RENDERED"
        assert band.experience_spec.continuity.actual_video_continuity_score is None
        assert band.experience_spec.activity_bridge is not None
        assert band.experience_spec.activity_bridge.age_band == band.age_band
    for band in result.legacy_result.age_bands:
        context_stage = next(stage for stage in band.stages if stage.stage == "CONTEXT_READY")
        debug = context_stage.details["debug_evidence"]
        assert debug["visibility"] == "BACKEND_DEBUG_ONLY"
        assert debug["top_k"] == 5
        assert 1 <= len(debug["ranking_trace"]) <= 5
        assert all("score_breakdown" in item for item in debug["ranking_trace"])
        assert all("reason_codes" in item for item in debug["rejected_candidates"])
    for band in result.age_bands:
        if band.experience_spec is None:
            continue
        payload = band.experience_spec.model_dump(mode="json")
        payload["semantic_match"]["activity_version"] += 1
        with pytest.raises(ValueError, match="activity versions must match"):
            type(band.experience_spec).model_validate(payload)
