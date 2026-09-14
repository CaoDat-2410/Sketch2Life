"""Translate the backward-compatible V1 workflow payload into the V2 contract."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Literal, cast

from sketch2life.contracts.schemas.semantic_personalization_v2 import (
    AgeAdaptationV2,
    BackendWorkflowResultV2,
    ConfirmedSceneUnderstandingV2,
    ExperienceSpecV2,
    SceneConceptV2,
    SemanticActivityMatchV2,
    WorkflowBandResultV2,
    finalize_backend_workflow_result_v2,
)
from sketch2life.contracts.schemas.workflow_demo import (
    AgeBand,
    AgeMatrixSummaryV1,
    BackendWorkflowResultV1,
    WorkflowBandResultV1,
)


def to_backend_workflow_result_v2(
    legacy: BackendWorkflowResultV1,
) -> BackendWorkflowResultV2:
    scene = _scene_from_legacy(legacy)
    v2_bands: list[WorkflowBandResultV2] = []
    for legacy_band in legacy.age_bands:
        story = legacy_band.story_scene or {}
        semantic_match_payload = story.get("semantic_match_v2")
        mode = story.get("experience_mode")
        spec = _experience_spec_from_legacy(
            legacy_band,
            scene,
            semantic_match_payload,
            mode,
        )
        relevance: int | None = None
        if spec is not None:
            mode = spec.experience_mode
            relevance = spec.semantic_match.semantic_relevance
        else:
            relevance = (
                int(semantic_match_payload.get("semantic_relevance", 0))
                if isinstance(semantic_match_payload, dict)
                else None
            )
        v2_bands.append(
            WorkflowBandResultV2(
                age_band=legacy_band.age_band,
                age_months=legacy_band.age_months,
                status=legacy_band.status,
                terminal_status=legacy_band.terminal_status,
                experience_mode=mode,
                scene_understanding_id=scene.scene_understanding_id,
                semantic_relevance=relevance,
                experience_spec=spec,
                legacy_band=legacy_band.model_dump(mode="json"),
                warnings=legacy_band.warnings,
            )
        )

    matrix = legacy.age_matrix_summary or _derive_matrix_summary(legacy.age_bands)
    personalized_count = sum(
        band.experience_mode == "PERSONALIZED" for band in v2_bands
    )
    fallback_count = sum(
        band.experience_mode == "AGE_BASELINE_FALLBACK" for band in v2_bands
    )
    payload = {
        "workflow_run_id": legacy.workflow_run_id,
        "status": legacy.status,
        "terminal_status": legacy.terminal_status,
        "input_mode": legacy.input_mode,
        "scene_understanding": scene.model_dump(mode="json"),
        "age_matrix_summary": matrix.model_dump(mode="json"),
        "age_bands": [band.model_dump(mode="json") for band in v2_bands],
        "personalized_band_count": personalized_count,
        "fallback_band_count": fallback_count,
        "unavailable_age_bands": tuple(
            band.age_band for band in v2_bands if band.status != "SUCCEEDED"
        ),
        "legacy_result": legacy,
        "created_at": legacy.created_at,
    }
    return finalize_backend_workflow_result_v2(payload)


def _scene_from_legacy(legacy: BackendWorkflowResultV1) -> ConfirmedSceneUnderstandingV2:
    for band in legacy.age_bands:
        story = band.story_scene or {}
        candidate = story.get("scene_understanding_v2")
        if isinstance(candidate, dict):
            try:
                return ConfirmedSceneUnderstandingV2.model_validate(candidate)
            except ValueError:
                continue
    first_anchor = "bức tranh của con"
    first_band = legacy.age_bands[0]
    if first_band.anchor_set:
        first_anchor = str(
            first_band.anchor_set.get("primary_anchor", {}).get(
                "normalized_label", first_anchor
            )
        )
    concept = SceneConceptV2(
        concept_id="UNCLASSIFIED_OBSERVATION",
        label_vi=first_anchor,
        confidence=0.5,
        evidence_claim_ids=("legacy:anchor",),
        source_kinds=("FUSION",),
    )
    digest = _hash(
        {
            "image": legacy.image_sha256,
            "audio": legacy.audio_sha256,
            "anchor": first_anchor,
        }
    )
    return ConfirmedSceneUnderstandingV2(
        scene_understanding_id=f"SCENE-{digest[:16]}",
        source_image_artifact_ref=legacy.image_artifact_ref,
        source_image_sha256=legacy.image_sha256,
        source_audio_artifact_ref=legacy.audio_artifact_ref,
        source_audio_sha256=legacy.audio_sha256,
        gate_a_status="UNAVAILABLE",
        adult_confirmation_actor=None,
        primary_anchor_label_vi=first_anchor,
        primary_concept=concept,
        observed_anchor_labels_vi=(first_anchor,),
        asr_transcript_vi=_first_transcript(legacy),
        supported_modalities=("VLM",),
        normalization_policy_version="LEGACY_RESULT_BRIDGE_V2",
        scene_sha256=digest,
    )


def _experience_spec_from_legacy(
    band: WorkflowBandResultV1,
    scene: ConfirmedSceneUnderstandingV2,
    semantic_match_payload: object,
    mode: object,
) -> ExperienceSpecV2 | None:
    if not isinstance(band.experience_spec, dict):
        return None
    legacy_spec = band.experience_spec
    activity = _nested_dict(legacy_spec, "activity_template", "activity_ref")
    objective = _nested_dict(legacy_spec, "learning_focus", "objective_ref")
    if not activity or not objective:
        return None
    match = _match_from_legacy(legacy_spec, scene, semantic_match_payload)
    resolved_mode = cast(Literal["PERSONALIZED", "AGE_BASELINE_FALLBACK"], (
        mode
        if mode in {"PERSONALIZED", "AGE_BASELINE_FALLBACK"}
        else (
            "AGE_BASELINE_FALLBACK"
            if match.match_mode == "AGE_BASELINE_FALLBACK"
            else "PERSONALIZED"
        )))
    adaptation_payload = (
        band.story_scene or {}
    ).get("age_adaptation_v2")
    adaptation = (
        AgeAdaptationV2.model_validate(adaptation_payload)
        if isinstance(adaptation_payload, dict)
        else _default_age_adaptation(band.age_band, objective, band.activity_handoff)
    )
    story = band.story_scene or {}
    story_mode: Literal["SCENE_GROUNDED", "AGE_BASELINE"] = (
        "AGE_BASELINE"
        if resolved_mode == "AGE_BASELINE_FALLBACK"
        else "SCENE_GROUNDED"
    )
    unsigned = {
        "contract_name": "ExperienceSpecV2",
        "contract_version": "2.0",
        "spec_id": f"SPEC2-{_hash({'legacy_spec': legacy_spec, 'scene': scene.scene_sha256})[:16]}",
        "session_id": str(legacy_spec.get("session_id", "legacy-session")),
        "scene_understanding_id": scene.scene_understanding_id,
        "activity_ref": activity,
        "objective_ref": objective,
        "experience_mode": resolved_mode,
        "semantic_match": match.model_dump(mode="json"),
        "age_adaptation": adaptation.model_dump(mode="json"),
        "gate_b_status": (
            "BASELINE_APPROVED"
            if resolved_mode == "AGE_BASELINE_FALLBACK"
            else "PERSONALIZED_APPROVED"
        ),
        "bridge_sentence_vi": str(
            story.get("narration_vi")
            or "Từ bức tranh, cùng người lớn thực hành hoạt động phù hợp lứa tuổi."
        ),
        "story_mode": story_mode,
        "legacy_spec": legacy_spec,
    }
    return ExperienceSpecV2(
        contract_name="ExperienceSpecV2",
        contract_version="2.0",
        spec_id=str(unsigned["spec_id"]),
        session_id=str(unsigned["session_id"]),
        scene_understanding_id=scene.scene_understanding_id,
        activity_ref=activity,
        objective_ref=objective,
        experience_mode=resolved_mode,
        semantic_match=match,
        age_adaptation=adaptation,
        gate_b_status=cast(
            Literal["PERSONALIZED_APPROVED", "BASELINE_APPROVED", "BLOCKED"],
            unsigned["gate_b_status"],
        ),
        bridge_sentence_vi=str(unsigned["bridge_sentence_vi"]),
        story_mode=story_mode,
        legacy_spec=legacy_spec,
        spec_sha256=_hash(unsigned),
    )


def _match_from_legacy(
    legacy_spec: dict[str, Any],
    scene: ConfirmedSceneUnderstandingV2,
    payload: object,
) -> SemanticActivityMatchV2:
    if isinstance(payload, dict):
        try:
            return SemanticActivityMatchV2.model_validate(payload)
        except ValueError:
            pass
    legacy_match = legacy_spec.get("semantic_match", {})
    legacy_mode = str(legacy_match.get("match_mode", "SAFE_FALLBACK"))
    mode = cast(Literal[
        "PERSONALIZED_EXACT",
        "PERSONALIZED_ALIAS",
        "PERSONALIZED_CONCEPT",
        "AGE_BASELINE_FALLBACK",
    ], {
        "EXACT": "PERSONALIZED_EXACT",
        "ALIAS": "PERSONALIZED_ALIAS",
        "SAFE_FALLBACK": "AGE_BASELINE_FALLBACK",
    }.get(legacy_mode, "AGE_BASELINE_FALLBACK"))
    activity = _nested_dict(legacy_spec, "activity_template", "activity_ref")
    phrases = tuple(legacy_match.get("matched_phrases_vi", ()))
    score = int(legacy_match.get("score", 55))
    return SemanticActivityMatchV2(
        match_mode=mode,
        profile_id=str(legacy_match.get("profile_id", "LEGACY_PROFILE")),
        profile_version=int(legacy_match.get("profile_version", 1)),
        activity_id=str(activity.get("id", "ACT-0001")),
        activity_version=int(activity.get("version", 1)),
        semantic_relevance=score,
        matched_concept_ids=tuple(legacy_match.get("matched_concept_ids", ())),
        matched_phrases_vi=phrases,
        matched_anchor_labels_vi=(scene.primary_anchor_label_vi,),
        evidence_claim_ids=tuple(
            legacy_match.get("evidence_claim_ids", ("legacy:semantic-match",))
        ),
        reason_codes=tuple(legacy_match.get("reason_codes", ("LEGACY_RESULT_BRIDGE",))),
        fallback_reason=(
            str(
                legacy_match.get(
                    "fallback_reason",
                    "legacy V1 result was bridged into V2",
                )
            )
            if mode == "AGE_BASELINE_FALLBACK"
            else None
        ),
    )


def _default_age_adaptation(
    age_band: AgeBand,
    objective: dict[str, Any],
    handoff: dict[str, Any] | None,
) -> AgeAdaptationV2:
    complexity = cast(Literal["FOUNDATION", "STANDARD", "EXTENSION"], {
        "0-3": "FOUNDATION",
        "3-6": "FOUNDATION",
        "6-9": "STANDARD",
        "9-12": "EXTENSION",
    }[age_band])
    supervision = str((handoff or {}).get("supervision", "DIRECT"))
    if supervision not in {"NONE", "NEARBY", "DIRECT"}:
        supervision = "DIRECT"
    supervision_value = cast(Literal["NONE", "NEARBY", "DIRECT"], supervision)
    return AgeAdaptationV2(
        age_band=age_band,
        age_months={"0-3": 24, "3-6": 54, "6-9": 84, "9-12": 132}[age_band],
        abstraction_level=(
            "FOUNDATION"
            if age_band in {"0-3", "3-6"}
            else "CONCRETE"
            if age_band == "6-9"
            else "ABSTRACT"
        ),
        objective_adaptation_vi=(
            f"Mục tiêu {objective.get('id', 'chưa định danh')}: điều chỉnh theo lứa tuổi."
        ),
        complexity_level=complexity,
        supervision_level=supervision_value,
        duration_minutes=None,
    )


def _derive_matrix_summary(
    bands: tuple[WorkflowBandResultV1, ...],
) -> AgeMatrixSummaryV1:
    return AgeMatrixSummaryV1(
        matrix_policy="STRICT",
        requested_age_bands=tuple(band.age_band for band in bands),
        ready_age_bands=tuple(band.age_band for band in bands if band.status == "SUCCEEDED"),
        unavailable_age_bands=tuple(band.age_band for band in bands if band.status != "SUCCEEDED"),
    )


def _nested_dict(value: dict[str, Any], *keys: str) -> dict[str, Any]:
    current: object = value
    for key in keys:
        if not isinstance(current, dict):
            return {}
        current = current.get(key)
    return current if isinstance(current, dict) else {}


def _first_transcript(result: BackendWorkflowResultV1) -> str:
    for band in result.age_bands:
        if band.asr_summary:
            return str(band.asr_summary.get("transcript_vi", ""))
    return ""


def _hash(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


__all__ = ["to_backend_workflow_result_v2"]