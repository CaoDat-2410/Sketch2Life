"""Deterministic semantic projection for the FEAT-018 Pixi exploration stage."""

from __future__ import annotations

from collections.abc import Mapping

from pydantic import ValidationError

from sketch2life.application.services.topic_semantics import display_label_vi
from sketch2life.contracts.schemas.p1_experience import SemanticAnchorSetV1, VersionedRefV1
from sketch2life.contracts.schemas.raw_understanding import RawUnderstandingSuccessV1
from sketch2life.contracts.schemas.scene_exploration import (
    SceneExplorationBeatV1,
    SceneExplorationPlanV1,
    SceneFocusPlanV1,
    SceneFocusTargetV1,
    SourceRegionV1,
    SubjectCandidateSetV1,
    SubjectCandidateV1,
)


def confidence_band(value: float) -> str:
    if value >= 0.8:
        return "HIGH"
    if value >= 0.55:
        return "MEDIUM"
    return "LOW"


def build_subject_candidates(
    *,
    session_id: str,
    raw: RawUnderstandingSuccessV1,
    anchor_set: SemanticAnchorSetV1,
) -> SubjectCandidateSetV1:
    """Project at most three confirmed concrete entities into short Vietnamese labels."""

    entity_by_id = {item.observation_id: item for item in raw.entities}
    ordered_refs = [
        anchor_set.primary_anchor.provenance.source_claim_ids[0]
    ] + [
        anchor.provenance.source_claim_ids[0]
        for anchor in anchor_set.secondary_anchors
        if anchor.provenance.source_claim_ids
    ]
    relation_refs_by_subject: dict[str, list[str]] = {}
    for relation in raw.relations:
        relation_refs_by_subject.setdefault(relation.subject_ref, []).append(
            relation.observation_id
        )
        relation_refs_by_subject.setdefault(relation.object_ref, []).append(
            relation.observation_id
        )

    narration_covered = bool(raw.asr_claims) or raw.narration_status.value == "TEXT_SUPPLIED"
    items: list[SubjectCandidateV1] = []
    seen: set[str] = set()
    for ref in ordered_refs:
        entity = entity_by_id.get(ref)
        if entity is None or ref in seen:
            continue
        label_vi = display_label_vi(entity.label.value)
        if not label_vi or label_vi == "chi tiết trong tranh":
            continue
        seen.add(ref)
        items.append(
            SubjectCandidateV1(
                candidate_id=ref,
                label_vi=label_vi,
                source_claim_ids=(ref,),
                confidence=entity.confidence,
                confidence_band=confidence_band(entity.confidence),
                image_covered=True,
                narration_covered=narration_covered,
                relation_refs=tuple(relation_refs_by_subject.get(ref, ()))[:8],
            )
        )
        if len(items) == 3:
            break

    if not items:
        primary = anchor_set.primary_anchor
        items.append(
            SubjectCandidateV1(
                candidate_id=primary.anchor_id.removeprefix("anchor-"),
                label_vi=display_label_vi(primary.normalized_label),
                source_claim_ids=primary.provenance.source_claim_ids[:1],
                confidence=primary.confidence,
                confidence_band=confidence_band(primary.confidence),
                image_covered=True,
                narration_covered=narration_covered,
            )
        )

    return SubjectCandidateSetV1(
        session_id=session_id,
        source_artifact_ref=raw.source_image_ref.artifact_ref,
        source_artifact_sha256=raw.source_image_ref.sha256,
        items=tuple(items),
    )


def build_scene_exploration_plan(
    *,
    session_id: str,
    experience_spec_ref: VersionedRefV1,
    raw: RawUnderstandingSuccessV1,
    candidates: SubjectCandidateSetV1,
    learning_bridge_vi: str,
) -> SceneExplorationPlanV1:
    primary = candidates.items[0]
    entity_labels = {
        item.observation_id: display_label_vi(item.label.value) for item in raw.entities
    }
    relation = next(
        (
            item
            for item in raw.relations
            if primary.candidate_id in {item.subject_ref, item.object_ref}
        ),
        None,
    )
    relation_label = display_label_vi(relation.predicate.value) if relation else None
    beats = [
        SceneExplorationBeatV1(
            beat_id="drawing-reveal",
            order=1,
            effect="REVEAL",
            label_vi="bức tranh",
            caption_vi="Bức vẽ của con đang mở ra.",
            start_seconds=0,
            end_seconds=1.4,
        ),
        SceneExplorationBeatV1(
            beat_id="subject-focus",
            order=2,
            effect="FOCUS",
            target_ref=primary.candidate_id,
            label_vi=primary.label_vi,
            caption_vi=f"Con đã vẽ {primary.label_vi}.",
            start_seconds=1.4,
            end_seconds=3.5,
            tap_enabled=True,
        ),
    ]
    if relation is not None:
        other_ref = (
            relation.object_ref
            if relation.subject_ref == primary.candidate_id
            else relation.subject_ref
        )
        other_label = entity_labels.get(other_ref, "chi tiết trong tranh")
        if other_label != "chi tiết trong tranh":
            beats.append(
                SceneExplorationBeatV1(
                    beat_id="relation-focus",
                    order=3,
                    effect="TRACE_RELATION",
                    target_ref=other_ref,
                    label_vi=other_label,
                    caption_vi=f"{primary.label_vi} và {other_label} đang kể cùng một câu chuyện.",
                    start_seconds=3.5,
                    end_seconds=5.7,
                    tap_enabled=True,
                )
            )
    else:
        beats.append(
            SceneExplorationBeatV1(
                beat_id="whole-scene-context",
                order=3,
                effect="ZOOM_OUT",
                label_vi="bức tranh",
                caption_vi="Con cùng nhìn lại cả bức tranh nhé.",
                start_seconds=3.5,
                end_seconds=5.2,
            )
        )
    beats.append(
        SceneExplorationBeatV1(
            beat_id="learning-bridge",
            order=len(beats) + 1,
            effect="ZOOM_OUT",
            label_vi="bức tranh",
            caption_vi=learning_bridge_vi[:180],
            start_seconds=5.2 if len(beats) == 3 else 5.7,
            end_seconds=7.3,
        )
    )
    return SceneExplorationPlanV1(
        session_id=session_id,
        experience_spec_ref=experience_spec_ref,
        source_artifact_ref=raw.source_image_ref.artifact_ref,
        primary_subject_ref=primary.candidate_id,
        primary_label_vi=primary.label_vi,
        relation_label_vi=relation_label,
        learning_bridge_vi=learning_bridge_vi[:240],
        beats=tuple(beats),
    )


def build_scene_focus_plan(
    *,
    session_id: str,
    experience_spec_ref: VersionedRefV1,
    raw: RawUnderstandingSuccessV1,
    candidates: SubjectCandidateSetV1,
    region_hints: Mapping[str, Mapping[str, float]] | None = None,
) -> SceneFocusPlanV1:
    """Accept only explicitly localized regions; otherwise expose a safe fallback."""

    if not region_hints:
        return SceneFocusPlanV1(
            session_id=session_id,
            experience_spec_ref=experience_spec_ref,
            source_artifact_ref=raw.source_image_ref.artifact_ref,
            source_artifact_sha256=raw.source_image_ref.sha256,
            extraction_status="FALLBACK_REQUIRED",
            fallback_reason="NO_LOCALIZER",
        )

    candidate_ids = {candidate.candidate_id for candidate in candidates.items}
    if len(region_hints) > 3 or any(ref not in candidate_ids for ref in region_hints):
        return SceneFocusPlanV1(
            session_id=session_id,
            experience_spec_ref=experience_spec_ref,
            source_artifact_ref=raw.source_image_ref.artifact_ref,
            source_artifact_sha256=raw.source_image_ref.sha256,
            extraction_status="FALLBACK_REQUIRED",
            fallback_reason="REGION_INVALID",
        )

    targets: list[SceneFocusTargetV1] = []
    for candidate in candidates.items:
        hint = region_hints.get(candidate.candidate_id)
        if hint is None:
            continue
        try:
            region = SourceRegionV1.model_validate(hint)
            targets.append(
                SceneFocusTargetV1(
                    target_ref=candidate.candidate_id,
                    label_vi=candidate.label_vi,
                    source_region=region,
                    region_confidence=candidate.confidence,
                    depth_layer=min(len(targets), 2),
                    asset_kind="CROP",
                    extraction_version="1",
                )
            )
        except ValidationError:
            return SceneFocusPlanV1(
                session_id=session_id,
                experience_spec_ref=experience_spec_ref,
                source_artifact_ref=raw.source_image_ref.artifact_ref,
                source_artifact_sha256=raw.source_image_ref.sha256,
                extraction_status="FALLBACK_REQUIRED",
                fallback_reason="REGION_INVALID",
            )
    if not targets:
        return SceneFocusPlanV1(
            session_id=session_id,
            experience_spec_ref=experience_spec_ref,
            source_artifact_ref=raw.source_image_ref.artifact_ref,
            source_artifact_sha256=raw.source_image_ref.sha256,
            extraction_status="FALLBACK_REQUIRED",
            fallback_reason="NO_LOCALIZER",
        )
    return SceneFocusPlanV1(
        session_id=session_id,
        experience_spec_ref=experience_spec_ref,
        source_artifact_ref=raw.source_image_ref.artifact_ref,
        source_artifact_sha256=raw.source_image_ref.sha256,
        extraction_status="READY",
        targets=tuple(targets),
    )


__all__ = [
    "build_scene_exploration_plan",
    "build_scene_focus_plan",
    "build_subject_candidates",
    "confidence_band",
]
