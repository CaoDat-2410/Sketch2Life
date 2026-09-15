"""Connected backend-only FEAT-020 workflow orchestrator.

The service owns ordering and workflow policy but knows nothing about FastAPI, PixiJS,
provider SDKs, SQL or HTTP. Real ASR/VLM implementations are injected through ports.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from secrets import randbits
from typing import Any, Literal, Protocol
from uuid import uuid4

from sketch2life.application.ports.asr import AsrPort
from sketch2life.application.ports.vision_understanding_v2 import VisionUnderstandingPortV2
from sketch2life.application.ports.workflow_dependencies import (
    ActivityCatalogMetadataPort,
    AssetCatalogPort,
    SemanticCatalogPort,
    SemanticCatalogV2Port,
    TemplateLibraryPort,
    WorkflowDependencies,
)
from sketch2life.application.services.media_validation import MediaValidationRequest
from sketch2life.application.services.p1_experience import P1ExperienceCompiler
from sketch2life.application.services.scene_understanding import (
    SceneCandidateV2Input,
    build_confirmed_scene_understanding,
)
from sketch2life.contracts.schemas.asr import (
    AsrAudioReferenceV1,
    AsrFailureV1,
    AsrProfileId,
    AsrRequestV1,
    AsrSuccessV1,
    LanguageHintV1,
    MediaValidationProvenanceV1,
)
from sketch2life.contracts.schemas.media_validation import MediaValidationResultV1
from sketch2life.contracts.schemas.p1_experience import (
    AnchorProvenanceV1,
    P1ContextV1,
    SemanticAnchorSetV1,
    SemanticAnchorV1,
    SemanticMatchEvidenceV1,
)
from sketch2life.contracts.schemas.semantic_personalization_v2 import (
    BackendWorkflowResultV2,
    ConfirmedSceneUnderstandingV2,
    RankingDebugEvidenceV2,
    RankingTraceEntryV2,
    RejectedCandidateEvidenceV2,
    SemanticActivityMatchV2,
)
from sketch2life.contracts.schemas.vision import (
    VisionImageReferenceV1,
    VisionMediaValidationProvenanceV1,
    vision_label_normalize,
)
from sketch2life.contracts.schemas.vision_v2 import (
    VisionProfileIdV2,
    VisionUnderstandingFailureV2,
    VisionUnderstandingRequestV2,
    VisionUnderstandingSuccessV2,
)
from sketch2life.contracts.schemas.workflow_demo import (
    AgeBand,
    AgeMatrixSummaryV1,
    BackendWorkflowResultV1,
    DeferredVideoV1,
    DemoDecisionV1,
    FeedbackHistoryV1,
    WorkflowBandResultV1,
    WorkflowStageV1,
    finalize_workflow_result,
)


class WorkflowRuntimeError(RuntimeError):
    """Typed orchestration failure which is safe to display as a terminal status."""

    def __init__(self, terminal_status: str, message: str) -> None:
        super().__init__(message)
        self.terminal_status = terminal_status


class _AsrRequestFactory(Protocol):
    def __call__(self, request: AsrRequestV1) -> object: ...


@dataclass(frozen=True, slots=True)
class BackendWorkflowRequest:
    image_path: Path
    narration_audio_path: Path
    repo_root: Path
    age_bands: tuple[AgeBand, ...] = ("0-3", "3-6", "6-9", "9-12")
    seed: int | None = None
    demo_autopilot: bool = False
    report_partial_test_only: bool = False
    emit_debug_evidence: bool = False
    asr_profile_id: AsrProfileId = AsrProfileId.WHISPER_TURBO_INT8_AUTO_V1


@dataclass(frozen=True, slots=True)
class _AnchorCandidate:
    label: str
    kind: str
    confidence: float
    tags: tuple[str, ...]
    claim_ids: tuple[str, ...]
    source_kind: Literal["ASR", "VLM"]


_AGE_MONTHS = {"0-3": 24, "3-6": 54, "6-9": 84, "9-12": 132}
_SUPPORTED_AGE_BANDS = tuple(_AGE_MONTHS)
_VIETNAMESE_WORDS = re.compile(r"[\wÀ-ỹ-]+", flags=re.UNICODE)


class BackendAiWorkflow:
    """Runs the real-AI path once for understanding and once per selected age band."""

    def __init__(
        self,
        *,
        asr: AsrPort,
        vision: VisionUnderstandingPortV2,
        dependencies: WorkflowDependencies,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._asr = asr
        self._vision = vision
        self._dependencies = dependencies
        self._clock = clock
        self._media_validator = dependencies.media_validator

    def run(self, request: BackendWorkflowRequest) -> BackendWorkflowResultV1:
        return self._run_legacy(request, v2=False)

    def run_v2(self, request: BackendWorkflowRequest) -> BackendWorkflowResultV2:
        legacy_result = self._run_legacy(request, v2=True)
        from sketch2life.application.services.semantic_personalization_v2 import (
            to_backend_workflow_result_v2,
        )

        return to_backend_workflow_result_v2(legacy_result)

    def _run_legacy(
        self, request: BackendWorkflowRequest, *, v2: bool
    ) -> BackendWorkflowResultV1:
        run_seed = request.seed if request.seed is not None else randbits(63)
        created_at = self._clock()
        if created_at.tzinfo is None or created_at.utcoffset() is None:
            raise ValueError("workflow clock must return a timezone-aware timestamp")
        workflow_run_id = f"workflow-{uuid4().hex[:16]}"
        image_ref = _relative_artifact_ref(request.image_path, Path.cwd())
        audio_ref = _relative_artifact_ref(request.narration_audio_path, Path.cwd())
        media = self._media_validator.validate(
            MediaValidationRequest(
                image_path=request.image_path,
                audio_path=request.narration_audio_path,
                image_artifact_ref=image_ref,
                audio_artifact_ref=audio_ref,
            )
        )
        if media.decision.value != "PASS":
            return self._failure_result(
                workflow_run_id,
                run_seed,
                created_at,
                media,
                request,
                "MEDIA_RECAPTURE",
                "media validation did not pass",
            )

        image_sha = _require_hash(media.image.sha256)
        audio_sha = _require_hash(media.audio.sha256)
        validation_hash = _hash_json(media.model_dump(mode="json"))
        asr_result = self._run_asr(
            request,
            audio_ref,
            audio_sha,
            validation_hash,
            workflow_run_id,
        )
        vision_result = self._run_vision(
            request,
            image_ref,
            image_sha,
            validation_hash,
            workflow_run_id,
        )
        if not isinstance(vision_result, VisionUnderstandingSuccessV2):
            return self._failure_result(
                workflow_run_id,
                run_seed,
                created_at,
                media,
                request,
                "AI_FAILED",
                "real ASR/VLM returned a typed failure",
                asr_result=asr_result,
                vision_result=vision_result,
            )

        semantic_catalog_v2: SemanticCatalogV2Port | None = None
        scene_understanding: ConfirmedSceneUnderstandingV2 | None = None
        try:
            library = self._dependencies.template_library
            semantic_catalog = self._dependencies.semantic_catalog
            semantic_catalog_v2 = self._dependencies.semantic_catalog_v2
            asset_catalog = self._dependencies.asset_catalog
            if v2 and semantic_catalog_v2 is None:
                raise ValueError("V2 semantic catalog dependency is not configured")
            asset_catalog.validate_all_age_bands()
        except (OSError, ValueError) as exc:
            return self._failure_result(
                workflow_run_id,
                run_seed,
                created_at,
                media,
                request,
                "ASSET_CATALOG_MISS",
                f"catalog preflight failed: {type(exc).__name__}",
                asr_result=asr_result,
                vision_result=vision_result,
            )
        anchor_candidates = _fused_anchor_candidates(asr_result, vision_result)
        if not anchor_candidates:
            return self._failure_result(
                workflow_run_id,
                run_seed,
                created_at,
                media,
                request,
                "AI_FAILED",
                "real understanding returned no usable observable anchors",
                asr_result=asr_result,
                vision_result=vision_result,
            )

        if v2:
            scene_understanding = build_confirmed_scene_understanding(
                scene_understanding_id="",
                image_artifact_ref=image_ref,
                image_sha256=image_sha,
                audio_artifact_ref=audio_ref,
                audio_sha256=audio_sha,
                candidates=tuple(
                    _scene_candidate_input(candidate) for candidate in anchor_candidates
                ),
                asr_transcript_vi=(
                    asr_result.transcript_raw
                    if isinstance(asr_result, AsrSuccessV1)
                    else ""
                ),
            )
        bands: list[WorkflowBandResultV1] = []
        previous_activity_ids: set[str] = set()
        previous_activity_family_ids: set[str] = set()
        for age_band in request.age_bands:
            if v2 and scene_understanding is not None and semantic_catalog_v2 is not None:
                band = self._run_age_band_v2(
                    request=request,
                    age_band=age_band,
                    run_seed=run_seed,
                    workflow_run_id=workflow_run_id,
                    media=media,
                    asr=asr_result,
                    vision=vision_result,
                    library=library,
                    semantic_catalog=semantic_catalog_v2,
                    asset_catalog=asset_catalog,
                    anchor_candidates=anchor_candidates,
                    previous_activity_ids=previous_activity_ids,
                    previous_activity_family_ids=previous_activity_family_ids,
                    scene_understanding=scene_understanding,
                )
            else:
                band = self._run_age_band(
                    request=request,
                    age_band=age_band,
                    run_seed=run_seed,
                    workflow_run_id=workflow_run_id,
                    media=media,
                    asr=asr_result,
                    vision=vision_result,
                    library=library,
                    semantic_catalog=semantic_catalog,
                    asset_catalog=asset_catalog,
                    anchor_candidates=anchor_candidates,
                    previous_activity_ids=previous_activity_ids,
                )
            bands.append(band)
            if band.activity_handoff is not None:
                activity_id = str(band.activity_handoff.get("activity_ref", {}).get("id", ""))
                if activity_id:
                    previous_activity_ids.add(activity_id)
                activity_identity = band.activity_handoff.get("activity_identity", {})
                activity_family_id = str(
                    activity_identity.get("activity_family_id", "")
                    if isinstance(activity_identity, dict)
                    else ""
                )
                if activity_family_id:
                    previous_activity_family_ids.add(activity_family_id)

        ready_age_bands = tuple(band.age_band for band in bands if band.status == "SUCCEEDED")
        unavailable_age_bands = tuple(band.age_band for band in bands if band.status != "SUCCEEDED")
        strict_success = len(unavailable_age_bands) == 0
        partial_success = (
            request.report_partial_test_only
            and bool(ready_age_bands)
            and bool(unavailable_age_bands)
        )
        result_status = (
            "SUCCEEDED"
            if strict_success
            else "PARTIAL_SUCCESS"
            if partial_success
            else "FAILED"
        )
        terminal_status = (
            "BACKEND_CONTEXT_READY"
            if strict_success
            else "BACKEND_CONTEXT_PARTIAL"
            if partial_success
            else _first_failure_status(bands)
        )
        matrix_summary = AgeMatrixSummaryV1(
            matrix_policy="REPORT_PARTIAL_TEST_ONLY"
            if request.report_partial_test_only
            else "STRICT",
            requested_age_bands=tuple(request.age_bands),
            ready_age_bands=ready_age_bands,
            unavailable_age_bands=unavailable_age_bands,
        )
        workflow_warnings = ["VIDEO_DEFERRED", "DEMO_AUTOPILOT_DECISIONS"]
        if not isinstance(asr_result, AsrSuccessV1):
            workflow_warnings.append("ASR_UNAVAILABLE_VLM_ONLY")
        if partial_success:
            workflow_warnings.append("AGE_MATRIX_PARTIAL_TEST_ONLY")
        result_payload: dict[str, Any] = {
            "workflow_run_id": workflow_run_id,
            "status": result_status,
            "terminal_status": terminal_status,
            "input_mode": "MULTIMODAL",
            "image_artifact_ref": image_ref,
            "image_sha256": image_sha,
            "audio_artifact_ref": audio_ref,
            "audio_sha256": audio_sha,
            "run_seed": run_seed,
            "age_matrix_summary": matrix_summary,
            "age_bands": [band.model_dump(mode="json") for band in bands],
            "stages": [
                WorkflowStageV1(
                    stage="MEDIA_VALIDATION",
                    status="SUCCEEDED",
                    details={"policy_version": media.validator_policy_version},
                ),
                WorkflowStageV1(
                    stage="REAL_ASR",
                    status=("SUCCEEDED" if isinstance(asr_result, AsrSuccessV1) else "DEFERRED"),
                    details=(
                        {"language": asr_result.detected_language}
                        if isinstance(asr_result, AsrSuccessV1)
                        else {
                            "status": asr_result.status,
                            "error_code": asr_result.error_code.value,
                            "error_detail": asr_result.error_detail.value,
                            "path": "VLM_ONLY",
                        }
                    ),
                    reason_code=(
                        None if isinstance(asr_result, AsrSuccessV1) else "ASR_UNAVAILABLE"
                    ),
                ),
                WorkflowStageV1(
                    stage="REAL_VLM",
                    status="SUCCEEDED",
                    details={"entity_count": len(vision_result.entities)},
                ),
                WorkflowStageV1(
                    stage="AGE_MATRIX",
                    status="SUCCEEDED" if strict_success or partial_success else "FAILED",
                    reason_code=None if strict_success or partial_success else terminal_status,
                    details={
                        "requested_age_bands": list(request.age_bands),
                        "ready_age_bands": list(ready_age_bands),
                        "unavailable_age_bands": list(unavailable_age_bands),
                        "matrix_policy": matrix_summary.matrix_policy,
                    },
                ),
                WorkflowStageV1(
                    stage="RESULT",
                    status="SUCCEEDED" if strict_success or partial_success else "FAILED",
                    reason_code=None if strict_success or partial_success else terminal_status,
                    details={"band_count": len(bands), "result_status": result_status},
                ),
            ],
            "warnings": tuple(workflow_warnings) if strict_success or partial_success else (),
            "created_at": created_at,
        }
        return finalize_workflow_result(result_payload)

    def _run_asr(
        self,
        request: BackendWorkflowRequest,
        audio_ref: str,
        audio_sha: str,
        validation_hash: str,
        run_id: str,
    ) -> AsrSuccessV1 | AsrFailureV1:
        asr_request = AsrRequestV1(
            correlation_id=f"{run_id}:asr",
            source_audio_ref=AsrAudioReferenceV1(artifact_ref=audio_ref, sha256=audio_sha),
            media_validation=MediaValidationProvenanceV1(
                validation_artifact_ref=f"runtime:{run_id}:media-validation",
                validation_artifact_sha256=validation_hash,
                decision="PASS",
                validator_policy_version="media-quality-policy-v1",
            ),
            requested_profile_id=request.asr_profile_id,
            language_hint=LanguageHintV1(value="vi", source="workflow_operator"),
        )
        return self._asr.transcribe(asr_request)

    def _run_vision(
        self,
        request: BackendWorkflowRequest,
        image_ref: str,
        image_sha: str,
        validation_hash: str,
        run_id: str,
    ) -> VisionUnderstandingSuccessV2 | VisionUnderstandingFailureV2:
        vision_request = VisionUnderstandingRequestV2(
            correlation_id=f"{run_id}:vision",
            source_image_ref=VisionImageReferenceV1(
                artifact_ref=image_ref,
                sha256=image_sha,
            ),
            media_validation=VisionMediaValidationProvenanceV1(
                validation_artifact_ref=f"runtime:{run_id}:media-validation",
                validation_artifact_sha256=validation_hash,
                decision="PASS",
                validator_policy_version="media-quality-policy-v1",
            ),
            requested_profile_id=VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1,
        )
        return self._vision.understand(vision_request)

    def _run_age_band_v2(
        self,
        *,
        request: BackendWorkflowRequest,
        age_band: AgeBand,
        run_seed: int,
        workflow_run_id: str,
        media: MediaValidationResultV1,
        asr: AsrSuccessV1 | AsrFailureV1,
        vision: VisionUnderstandingSuccessV2,
        library: TemplateLibraryPort,
        semantic_catalog: SemanticCatalogV2Port,
        asset_catalog: AssetCatalogPort,
        anchor_candidates: tuple[_AnchorCandidate, ...],
        previous_activity_ids: set[str],
        previous_activity_family_ids: set[str],
        scene_understanding: ConfirmedSceneUnderstandingV2,
    ) -> WorkflowBandResultV1:
        if age_band not in _SUPPORTED_AGE_BANDS:
            return _failed_band(age_band, run_seed, "NO_ELIGIBLE_ACTIVITY", "unsupported age band")
        band_seed = _derive_band_seed(run_seed, age_band)
        compiler = P1ExperienceCompiler(library.templates, library.objective_titles_vi)
        context = _demo_context(library, age_band, workflow_run_id)
        canonical_candidate = _canonical_scene_candidate(scene_understanding, anchor_candidates)
        compiled: list[
            tuple[
                _AnchorCandidate,
                Any,
                SemanticAnchorSetV1,
                SemanticMatchEvidenceV1,
                SemanticActivityMatchV2,
            ]
        ] = []
        rejected_candidates: list[RejectedCandidateEvidenceV2] = []
        for template in library.templates:
            if not template.age_months_min <= _AGE_MONTHS[age_band] <= template.age_months_max:
                if request.emit_debug_evidence:
                    rejected_candidates.append(
                        _debug_rejection(
                            template.activity_ref.id,
                            template.template_id,
                            "AGE_OUT_OF_RANGE",
                        )
                    )
                continue
            profile = semantic_catalog.profile_for(template.activity_ref.id)
            semantic_match_v2 = semantic_catalog.match_scene(scene_understanding, profile)
            if semantic_match_v2 is None:
                if request.emit_debug_evidence:
                    rejected_candidates.append(
                        _debug_rejection(
                            template.activity_ref.id,
                            template.template_id,
                            "NO_SEMANTIC_MATCH",
                        )
                    )
                continue
            if semantic_match_v2.match_mode == "AGE_BASELINE_FALLBACK":
                # FEAT-021 is fail-closed for semantic personalization. A baseline
                # candidate is not a personalized recommendation and must be
                # reported as unavailable instead of being silently selected.
                if request.emit_debug_evidence:
                    rejected_candidates.append(
                        _debug_rejection(
                            template.activity_ref.id,
                            template.template_id,
                            "BASELINE_FALLBACK_NOT_PERSONALIZED",
                        )
                    )
                continue
            candidate = _candidate_for_semantic_match(
                semantic_match_v2,
                canonical_candidate,
                anchor_candidates,
            )
            anchor_set = _anchor_set_for_candidate(
                candidate,
                anchor_candidates,
                media.image.artifact_ref,
                _require_hash(media.image.sha256),
            )
            semantic_match = semantic_catalog.to_legacy_evidence(semantic_match_v2)
            compilation = compiler.compile(
                anchor_set,
                context,
                preferred_template_id=template.template_id,
                semantic_match=semantic_match,
            )
            if compilation.spec is not None and compilation.handoff is not None:
                if (
                    compilation.spec.activity_template.activity_ref.id
                    != semantic_match_v2.activity_id
                    or compilation.spec.activity_template.activity_ref.version
                    != semantic_match_v2.activity_version
                ):
                    if request.emit_debug_evidence:
                        rejected_candidates.append(
                            _debug_rejection(
                                template.activity_ref.id,
                                template.template_id,
                                "ACTIVITY_IDENTITY_MISMATCH",
                            )
                        )
                    continue
                compiled.append(
                    (candidate, compilation, anchor_set, semantic_match, semantic_match_v2)
                )
            elif request.emit_debug_evidence:
                reason_codes = list(compilation.filter_result.reason_codes)
                if compilation.fit_evaluation is not None:
                    reason_codes.extend(compilation.fit_evaluation.reason_codes)
                rejected_candidates.append(
                    _debug_rejection(
                        template.activity_ref.id,
                        template.template_id,
                        *(reason_codes or ("COMPILER_HARD_RULE_REJECTED",)),
                    )
                )
        if not compiled:
            return _unavailable_band(
                age_band,
                band_seed,
                "NO_SAFE_ACTIVITY_FOR_AGE_BAND",
                "no catalog activity satisfied child-interest, age, identity and hard-rule checks",
            )

        rng = random.Random(band_seed)
        strongest_priority = max(_selection_rank_v2(item[4]) for item in compiled)
        strongest = [
            item
            for item in compiled
            if _selection_rank_v2(item[4]) == strongest_priority
        ]
        rng.shuffle(strongest)
        non_repeating = [
            item
            for item in strongest
            if (
                item[1].spec.activity_template.activity_ref.id not in previous_activity_ids
                and item[4].activity_family_id not in previous_activity_family_ids
            )
        ]
        chosen = (non_repeating or strongest)[0]
        _candidate, compilation, anchor_set, semantic_match, semantic_match_v2 = chosen
        assert compilation.spec is not None
        assert compilation.handoff is not None
        spec = compilation.spec
        activity_id = spec.activity_template.activity_ref.id
        objective_id = spec.learning_focus.objective_ref.id
        template_id = spec.activity_template.template_id
        assets = asset_catalog.resolve(age_band)
        experience_mode = (
            "AGE_BASELINE_FALLBACK"
            if semantic_match_v2.match_mode == "AGE_BASELINE_FALLBACK"
            else "PERSONALIZED"
        )
        age_adaptation = _age_adaptation_payload(
            self._dependencies.catalog_metadata,
            age_band,
            spec,
            experience_mode,
        )
        now = self._clock()
        decisions = (
            DemoDecisionV1(
                gate="A",
                actor="DEMO_OPERATOR",
                mode="DEMO_AUTOPILOT",
                decision="CONFIRMED",
                reason=(
                    "workflow demo uses one shared multimodal scene understanding "
                    "for every age band"
                ),
                decided_at=now,
            ),
            DemoDecisionV1(
                gate="B",
                actor="DEMO_OPERATOR",
                mode="DEMO_AUTOPILOT",
                decision=(
                    "BASELINE_APPROVED"
                    if experience_mode == "AGE_BASELINE_FALLBACK"
                    else "APPROVED"
                ),
                reason=(
                    "personalized semantic route passed compiler and identity checks"
                    if experience_mode == "PERSONALIZED"
                    else "no safe personalized route passed; explicit age baseline selected"
                ),
                decided_at=now,
            ),
            DemoDecisionV1(
                gate="FEEDBACK",
                actor="DEMO_OPERATOR",
                mode="DEMO_AUTOPILOT",
                decision="PLACEHOLDER_CREATED",
                reason="no real caregiver observation is claimed by the backend demo",
                decided_at=now,
            ),
        )
        primary_materials = self._dependencies.catalog_metadata.primary_material_ids(activity_id)
        duration_spec = self._dependencies.catalog_metadata.duration_spec(activity_id)
        story_scene = _story_scene_context(
            anchor_set,
            spec,
            asr,
            vision,
            primary_materials,
            assets.asset_ids,
            semantic_match,
            scene_understanding=scene_understanding,
            semantic_match_v2=semantic_match_v2,
            experience_mode=experience_mode,
            age_adaptation=age_adaptation,
        )
        handoff = {
            **compilation.handoff.model_dump(mode="json"),
            "selected_material_option_ids": list(primary_materials),
            "duration_minutes": _duration_minutes(duration_spec),
            "duration_spec": duration_spec,
            "supervision": spec.activity_template.minimum_supervision,
            "safety_rule_ids": list(spec.activity_template.safety_rule_ids),
            "accessibility": ["spoken_vi", "text_vi", "no_color_only_meaning", "reduced_motion"],
            "experience_mode": experience_mode,
            "semantic_relevance": semantic_match_v2.semantic_relevance,
            "selected_concept_id": semantic_match_v2.selected_concept_id,
            "selected_concept_role": semantic_match_v2.selected_concept_role,
            "child_interest_alignment": semantic_match_v2.child_interest_alignment,
            "personalization_scores": {
                "concept_match_confidence": semantic_match_v2.concept_match_confidence,
                "child_interest_alignment": semantic_match_v2.child_interest_alignment,
                "age_fit_score": semantic_match_v2.age_fit_score,
                "activity_safety_score": semantic_match_v2.activity_safety_score,
                "catalog_quality_score": semantic_match_v2.catalog_quality_score,
                "objective_activity_alignment": semantic_match_v2.objective_activity_alignment,
                "overall_personalization_score": semantic_match_v2.overall_personalization_score,
                "continuity_mode": semantic_match_v2.continuity_mode,
                "planned_video_continuity_score": semantic_match_v2.planned_video_continuity_score,
            },
            "activity_identity": {
                "activity_family_id": semantic_match_v2.activity_family_id,
                "activity_id": semantic_match_v2.activity_id,
                "activity_version": semantic_match_v2.activity_version,
                "variant_id": semantic_match_v2.variant_id,
                "catalog_revision": semantic_match_v2.catalog_revision,
            },
            "semantic_match_v2": semantic_match_v2.model_dump(mode="json"),
            "age_adaptation_v2": age_adaptation,
        }
        stage_details = {
            "selection_vector": [activity_id, objective_id, template_id],
            "candidate_count": len(compiled),
            "semantic_candidate_count": len(compiled),
            "selected_match_mode": semantic_match.match_mode,
            "selected_semantic_score": semantic_match.score,
            "selected_concept_id": semantic_match_v2.selected_concept_id,
            "selected_concept_role": semantic_match_v2.selected_concept_role,
            "child_interest_alignment": semantic_match_v2.child_interest_alignment,
            "objective_activity_alignment": semantic_match_v2.objective_activity_alignment,
            "overall_personalization_score": semantic_match_v2.overall_personalization_score,
            "continuity_mode": semantic_match_v2.continuity_mode,
            "planned_video_continuity_score": semantic_match_v2.planned_video_continuity_score,
            "activity_identity": {
                "activity_id": semantic_match_v2.activity_id,
                "activity_version": semantic_match_v2.activity_version,
                "variant_id": semantic_match_v2.variant_id,
                "catalog_revision": semantic_match_v2.catalog_revision,
            },
            "experience_mode": experience_mode,
            "semantic_match_v2": semantic_match_v2.model_dump(mode="json"),
            "scene_understanding_id": scene_understanding.scene_understanding_id,
            "variation_unavailable_reason": (
                "ONLY_ONE_ELIGIBLE_CANDIDATE" if len(compiled) == 1 else None
            ),
        }
        if request.emit_debug_evidence:
            debug_evidence = _ranking_debug_evidence(
                compiled,
                chosen,
                rejected_candidates,
            )
            debug_payload = debug_evidence.model_dump(mode="json")
            handoff["debug_evidence"] = debug_payload
            stage_details["debug_evidence"] = debug_payload
        stages = (
            WorkflowStageV1(
                stage="UNDERSTANDING_PROPOSED",
                status="SUCCEEDED",
                details=_understanding_details(asr, vision),
            ),
            WorkflowStageV1(
                stage="FUSION_READY", status="SUCCEEDED", details=_fusion_details(asr, vision)
            ),
            WorkflowStageV1(
                stage="GATE_A_CONFIRMED",
                status="SUCCEEDED",
                details={
                    "actor": "DEMO_OPERATOR",
                    "scene_understanding_id": scene_understanding.scene_understanding_id,
                    "primary_concept": scene_understanding.primary_concept.concept_id,
                },
            ),
            WorkflowStageV1(stage="CONTEXT_READY", status="SUCCEEDED", details=stage_details),
            WorkflowStageV1(
                stage="GATE_B_CONFIRMED",
                status="SUCCEEDED",
                details={"actor": "DEMO_OPERATOR", "experience_mode": experience_mode},
            ),
            WorkflowStageV1(
                stage="EXPERIENCE_READY", status="SUCCEEDED", details={"spec_id": spec.spec_id}
            ),
            WorkflowStageV1(
                stage="STORY_SCENE_READY",
                status="SUCCEEDED",
                details={
                    "story_id": story_scene["story_id"],
                    "story_mode": story_scene["story_mode"],
                },
            ),
            WorkflowStageV1(
                stage="ART_PLAN_READY",
                status="SUCCEEDED",
                details={"asset_count": len(assets.asset_ids)},
            ),
            WorkflowStageV1(
                stage="VIDEO_DEFERRED",
                status="DEFERRED",
                reason_code="VIDEO_GENERATION_DEFERRED_FOR_FIRST_BACKEND_DEMO",
                details={"target_duration_seconds": [5, 10]},
            ),
            WorkflowStageV1(
                stage="HANDOFF_READY", status="SUCCEEDED", details={"activity_id": activity_id}
            ),
            WorkflowStageV1(
                stage="DEMO_FEEDBACK_PLACEHOLDER_READY",
                status="SUCCEEDED",
                details={"source": "DEMO_AUTOPILOT", "feedback_status": "NOT_ATTEMPTED"},
            ),
        )
        return WorkflowBandResultV1(
            age_band=age_band,
            age_months=_AGE_MONTHS[age_band],
            run_seed=band_seed,
            seed_fingerprint=_seed_fingerprint(band_seed),
            status="SUCCEEDED",
            terminal_status="BACKEND_CONTEXT_READY",
            selection_vector=(activity_id, objective_id, template_id),
            stages=stages,
            decisions=decisions,
            asr_summary=_asr_summary(asr),
            vision_summary=_vision_summary(vision),
            fusion_summary=_fusion_details(asr, vision),
            anchor_set=anchor_set.model_dump(mode="json"),
            experience_spec=spec.model_dump(mode="json"),
            activity_handoff=handoff,
            story_scene=story_scene,
            art_render_intent=assets,
            video=DeferredVideoV1(),
            feedback_history=FeedbackHistoryV1(feedback_status="NOT_ATTEMPTED"),
        )

    def _run_age_band(
        self,
        *,
        request: BackendWorkflowRequest,
        age_band: AgeBand,
        run_seed: int,
        workflow_run_id: str,
        media: MediaValidationResultV1,
        asr: AsrSuccessV1 | AsrFailureV1,
        vision: VisionUnderstandingSuccessV2,
        library: TemplateLibraryPort,
        semantic_catalog: SemanticCatalogPort,
        asset_catalog: AssetCatalogPort,
        anchor_candidates: tuple[_AnchorCandidate, ...],
        previous_activity_ids: set[str],
    ) -> WorkflowBandResultV1:
        if age_band not in _SUPPORTED_AGE_BANDS:
            return _failed_band(age_band, run_seed, "NO_ELIGIBLE_ACTIVITY", "unsupported age band")
        band_seed = _derive_band_seed(run_seed, age_band)
        compiler = P1ExperienceCompiler(library.templates, library.objective_titles_vi)
        context = _demo_context(library, age_band, workflow_run_id)
        compiled: list[
            tuple[_AnchorCandidate, Any, SemanticAnchorSetV1, SemanticMatchEvidenceV1]
        ] = []
        for candidate in anchor_candidates:
            anchor_set = _anchor_set_for_candidate(
                candidate,
                anchor_candidates,
                media.image.artifact_ref,
                _require_hash(media.image.sha256),
            )
            for template in library.templates:
                if not template.age_months_min <= _AGE_MONTHS[age_band] <= template.age_months_max:
                    continue
                profile = semantic_catalog.profile_for(template.activity_ref.id)
                semantic_match = semantic_catalog.match(anchor_set, profile)
                if semantic_match is None:
                    continue
                compilation = compiler.compile(
                    anchor_set,
                    context,
                    preferred_template_id=template.template_id,
                    semantic_match=semantic_match,
                )
                if compilation.spec is not None and compilation.handoff is not None:
                    compiled.append((candidate, compilation, anchor_set, semantic_match))
        if not compiled:
            return _failed_band(
                age_band,
                band_seed,
                "NO_ELIGIBLE_ACTIVITY",
                "no golden activity satisfied observable-anchor and hard-rule checks",
            )

        rng = random.Random(band_seed)
        strongest_priority = max(_match_priority(item[3].match_mode) for item in compiled)
        strongest = [
            item for item in compiled if _match_priority(item[3].match_mode) == strongest_priority
        ]
        rng.shuffle(strongest)
        non_repeating = [
            item
            for item in strongest
            if item[1].spec.activity_template.activity_ref.id not in previous_activity_ids
        ]
        chosen = (non_repeating or strongest)[0]
        candidate, compilation, anchor_set, semantic_match = chosen
        assert compilation.spec is not None
        assert compilation.handoff is not None
        spec = compilation.spec
        activity_id = spec.activity_template.activity_ref.id
        objective_id = spec.learning_focus.objective_ref.id
        template_id = spec.activity_template.template_id
        assets = asset_catalog.resolve(age_band)
        now = self._clock()
        decisions = (
            DemoDecisionV1(
                gate="A",
                actor="DEMO_OPERATOR",
                mode="DEMO_AUTOPILOT",
                decision="CONFIRMED",
                reason="workflow demo uses the real ASR/VLM proposal without an interactive UI",
                decided_at=now,
            ),
            DemoDecisionV1(
                gate="B",
                actor="DEMO_OPERATOR",
                mode="DEMO_AUTOPILOT",
                decision="APPROVED",
                reason="selected catalog activity passed the P1 compiler and identity checks",
                decided_at=now,
            ),
            DemoDecisionV1(
                gate="FEEDBACK",
                actor="DEMO_OPERATOR",
                mode="DEMO_AUTOPILOT",
                decision="RECORDED",
                reason="no real caregiver observation is claimed by the backend demo",
                decided_at=now,
            ),
        )
        primary_materials = self._dependencies.catalog_metadata.primary_material_ids(activity_id)
        duration_spec = self._dependencies.catalog_metadata.duration_spec(activity_id)
        story_scene = _story_scene_context(
            anchor_set,
            spec,
            asr,
            vision,
            primary_materials,
            assets.asset_ids,
            semantic_match,
        )
        handoff = {
            **compilation.handoff.model_dump(mode="json"),
            "selected_material_option_ids": list(primary_materials),
            "duration_minutes": _duration_minutes(duration_spec),
            "duration_spec": duration_spec,
            "supervision": spec.activity_template.minimum_supervision,
            "safety_rule_ids": list(spec.activity_template.safety_rule_ids),
            "accessibility": ["spoken_vi", "text_vi", "no_color_only_meaning", "reduced_motion"],
        }
        stage_details = {
            "selection_vector": [activity_id, objective_id, template_id],
            "candidate_count": len(compiled),
            "semantic_candidate_count": len(compiled),
            "selected_match_mode": semantic_match.match_mode,
            "selected_semantic_score": semantic_match.score,
            "variation_unavailable_reason": (
                "ONLY_ONE_ELIGIBLE_CANDIDATE" if len(compiled) == 1 else None
            ),
        }
        stages = (
            WorkflowStageV1(
                stage="UNDERSTANDING_PROPOSED",
                status="SUCCEEDED",
                details=_understanding_details(asr, vision),
            ),
            WorkflowStageV1(
                stage="FUSION_READY", status="SUCCEEDED", details=_fusion_details(asr, vision)
            ),
            WorkflowStageV1(
                stage="GATE_A_CONFIRMED", status="SUCCEEDED", details={"actor": "DEMO_OPERATOR"}
            ),
            WorkflowStageV1(stage="CONTEXT_READY", status="SUCCEEDED", details=stage_details),
            WorkflowStageV1(
                stage="GATE_B_CONFIRMED", status="SUCCEEDED", details={"actor": "DEMO_OPERATOR"}
            ),
            WorkflowStageV1(
                stage="EXPERIENCE_READY", status="SUCCEEDED", details={"spec_id": spec.spec_id}
            ),
            WorkflowStageV1(
                stage="STORY_SCENE_READY",
                status="SUCCEEDED",
                details={"story_id": story_scene["story_id"]},
            ),
            WorkflowStageV1(
                stage="ART_PLAN_READY",
                status="SUCCEEDED",
                details={"asset_count": len(assets.asset_ids)},
            ),
            WorkflowStageV1(
                stage="VIDEO_DEFERRED",
                status="DEFERRED",
                reason_code="VIDEO_GENERATION_DEFERRED_FOR_FIRST_BACKEND_DEMO",
                details={"target_duration_seconds": [5, 10]},
            ),
            WorkflowStageV1(
                stage="HANDOFF_READY", status="SUCCEEDED", details={"activity_id": activity_id}
            ),
            WorkflowStageV1(
                stage="DEMO_FEEDBACK_PLACEHOLDER_READY",
                status="SUCCEEDED",
                details={"source": "DEMO_AUTOPILOT", "feedback_status": "NOT_ATTEMPTED"},
            ),
        )
        return WorkflowBandResultV1(
            age_band=age_band,
            age_months=_AGE_MONTHS[age_band],
            run_seed=band_seed,
            seed_fingerprint=_seed_fingerprint(band_seed),
            status="SUCCEEDED",
            terminal_status="BACKEND_CONTEXT_READY",
            selection_vector=(activity_id, objective_id, template_id),
            stages=stages,
            decisions=decisions,
            asr_summary=_asr_summary(asr),
            vision_summary=_vision_summary(vision),
            fusion_summary=_fusion_details(asr, vision),
            anchor_set=anchor_set.model_dump(mode="json"),
            experience_spec=spec.model_dump(mode="json"),
            activity_handoff=handoff,
            story_scene=story_scene,
            art_render_intent=assets,
            video=DeferredVideoV1(),
            feedback_history=FeedbackHistoryV1(feedback_status="NOT_ATTEMPTED"),
        )

    def _failure_result(
        self,
        workflow_run_id: str,
        run_seed: int,
        created_at: datetime,
        media: MediaValidationResultV1,
        request: BackendWorkflowRequest,
        terminal_status: str,
        reason: str,
        *,
        asr_result: object | None = None,
        vision_result: object | None = None,
    ) -> BackendWorkflowResultV1:
        image_sha = media.image.sha256 or _empty_hash()
        audio_sha = media.audio.sha256 or _empty_hash()
        image_ref = media.image.artifact_ref
        audio_ref = media.audio.artifact_ref
        bands = tuple(
            _failed_band(age_band, _derive_band_seed(run_seed, age_band), terminal_status, reason)
            for age_band in request.age_bands
        )
        return finalize_workflow_result(
            {
                "workflow_run_id": workflow_run_id,
                "status": "FAILED",
                "terminal_status": terminal_status,
                "input_mode": "MULTIMODAL",
                "image_artifact_ref": image_ref,
                "image_sha256": image_sha,
                "audio_artifact_ref": audio_ref,
                "audio_sha256": audio_sha,
                "run_seed": run_seed,
                "age_matrix_summary": AgeMatrixSummaryV1(
                    matrix_policy=(
                        "REPORT_PARTIAL_TEST_ONLY"
                        if request.report_partial_test_only
                        else "STRICT"
                    ),
                    requested_age_bands=tuple(request.age_bands),
                    ready_age_bands=(),
                    unavailable_age_bands=tuple(request.age_bands),
                ),
                "age_bands": [band.model_dump(mode="json") for band in bands],
                "stages": [
                    WorkflowStageV1(
                        stage="MEDIA_VALIDATION",
                        status="SUCCEEDED" if media.decision.value == "PASS" else "FAILED",
                        reason_code=None if media.decision.value == "PASS" else "MEDIA_RECAPTURE",
                        details={"decision": media.decision.value},
                    ),
                    WorkflowStageV1(
                        stage="WORKFLOW",
                        status="FAILED",
                        reason_code=terminal_status,
                        details=_workflow_failure_details(reason, asr_result, vision_result),
                    ),
                ],
                "warnings": (),
                "created_at": created_at,
            }
        )


def _scene_candidate_input(candidate: _AnchorCandidate) -> SceneCandidateV2Input:
    kind: Literal["subject", "action", "visual_feature", "story"] = (
        "subject"
        if candidate.kind == "subject"
        else "action"
        if candidate.kind == "action"
        else "story"
    )
    return SceneCandidateV2Input(
        label_vi=candidate.label,
        kind=kind,
        confidence=candidate.confidence,
        claim_ids=candidate.claim_ids,
        source_kind=candidate.source_kind,
    )


def _canonical_scene_candidate(
    scene: ConfirmedSceneUnderstandingV2,
    candidates: tuple[_AnchorCandidate, ...],
) -> _AnchorCandidate:
    primary = vision_label_normalize(scene.primary_anchor_label_vi).casefold()
    matching = tuple(
        candidate
        for candidate in candidates
        if primary in vision_label_normalize(candidate.label).casefold()
        or vision_label_normalize(candidate.label).casefold() in primary
    )
    if matching:
        return sorted(matching, key=lambda item: (-item.confidence, item.label.casefold()))[0]
    return sorted(
        candidates,
        key=lambda item: (-item.confidence, -len(item.label.split()), item.label.casefold()),
    )[0]


def _candidate_for_semantic_match(
    match: SemanticActivityMatchV2,
    canonical: _AnchorCandidate,
    candidates: tuple[_AnchorCandidate, ...],
) -> _AnchorCandidate:
    labels = tuple(
        vision_label_normalize(label).casefold() for label in match.matched_anchor_labels_vi
    )
    phrases = tuple(phrase.casefold() for phrase in match.matched_phrases_vi)
    matching = tuple(
        candidate
        for candidate in candidates
        if any(
            label in vision_label_normalize(candidate.label).casefold()
            or vision_label_normalize(candidate.label).casefold() in label
            for label in labels
        )
        or any(phrase in candidate.label.casefold() for phrase in phrases)
    )
    return (
        sorted(matching, key=lambda item: (-item.confidence, item.label.casefold()))[0]
        if matching
        else canonical
    )


def _age_adaptation_payload(
    catalog_metadata: ActivityCatalogMetadataPort,
    age_band: AgeBand,
    spec: Any,
    experience_mode: str,
) -> dict[str, Any]:
    abstraction = {
        "0-3": "FOUNDATION",
        "3-6": "FOUNDATION",
        "6-9": "CONCRETE",
        "9-12": "ABSTRACT",
    }[age_band]
    complexity = {
        "0-3": "FOUNDATION",
        "3-6": "FOUNDATION",
        "6-9": "STANDARD",
        "9-12": "EXTENSION",
    }[age_band]
    objective_id = spec.learning_focus.objective_ref.id
    anchor_label = spec.anchor_set.primary_anchor.normalized_label
    objective_text = {
        "0-3": (
            f"Trẻ phối hợp tay-mắt khi quan sát {anchor_label} và thực hiện một thao tác ngắn"
        ),
        "3-6": (
            f"Trẻ thực hiện theo trình tự và thu dọn sau khi khám phá {anchor_label}"
        ),
        "6-9": (
            f"Trẻ quan sát, phân loại hoặc so sánh đặc điểm của {anchor_label}"
        ),
        "9-12": (
            f"Trẻ giải thích mối quan hệ, ghi nhận quan sát và nêu giới hạn "
            f"của mô hình {anchor_label}"
        ),
    }[age_band]
    if experience_mode == "AGE_BASELINE_FALLBACK":
        objective_text = f"Trẻ thực hiện hoạt động nền tảng phù hợp lứa tuổi với {anchor_label}"
    duration_spec = catalog_metadata.duration_spec(spec.activity_template.activity_ref.id)
    return {
        "age_band": age_band,
        "age_months": _AGE_MONTHS[age_band],
        "abstraction_level": abstraction,
        "objective_adaptation_vi": f"{objective_text}; mục tiêu {objective_id}.",
        "complexity_level": complexity,
        "supervision_level": spec.activity_template.minimum_supervision,
        "duration_minutes": _duration_minutes(duration_spec),
        "duration_spec": duration_spec,
    }


def _match_priority_v2(mode: str) -> int:
    return {
        "PERSONALIZED_EXACT": 4,
        "PERSONALIZED_ALIAS": 3,
        "PERSONALIZED_CONCEPT": 2,
        "AGE_BASELINE_FALLBACK": 1,
    }.get(mode, 0)


def _selection_rank_v2(match: SemanticActivityMatchV2) -> tuple[float, float, int, int]:
    """Rank by child interest before match mode so VLM-only background wins less often."""

    return (
        match.child_interest_alignment,
        match.overall_personalization_score,
        _match_priority_v2(match.match_mode),
        match.semantic_relevance,
    )


def _debug_rejection(
    activity_id: str,
    template_id: str,
    *reason_codes: str,
) -> RejectedCandidateEvidenceV2:
    return RejectedCandidateEvidenceV2(
        activity_id=activity_id,
        template_id=template_id,
        reason_codes=tuple(dict.fromkeys(code for code in reason_codes if code))
        or ("UNSPECIFIED_SAFE_REJECTION",),
    )


def _ranking_debug_evidence(
    compiled: list[tuple[Any, Any, Any, Any, SemanticActivityMatchV2]],
    chosen: tuple[Any, Any, Any, Any, SemanticActivityMatchV2],
    rejected_candidates: list[RejectedCandidateEvidenceV2],
) -> RankingDebugEvidenceV2:
    selected_match = chosen[4]
    selected_rank = _selection_rank_v2(selected_match)
    ranked = sorted(
        compiled,
        key=lambda item: (
            _selection_rank_v2(item[4]),
            item[4].activity_family_id,
            item[4].activity_id,
        ),
        reverse=True,
    )
    top_k: list[RankingTraceEntryV2] = []
    for rank, item in enumerate(ranked[:5], start=1):
        match = item[4]
        is_selected = match.activity_id == selected_match.activity_id
        lost_to_selected: Literal[
            "LOWER_SELECTION_RANK",
            "SAME_SELECTION_RANK_RANDOMIZED_OR_NON_REPEAT_POLICY",
        ] | None = None
        if not is_selected:
            lost_to_selected = (
                "LOWER_SELECTION_RANK"
                if _selection_rank_v2(match) < selected_rank
                else "SAME_SELECTION_RANK_RANDOMIZED_OR_NON_REPEAT_POLICY"
            )
        top_k.append(
            RankingTraceEntryV2(
                rank=rank,
                activity_id=match.activity_id,
                activity_version=match.activity_version,
                activity_family_id=match.activity_family_id,
                variant_id=match.variant_id,
                catalog_revision=match.catalog_revision,
                selected_concept_id=match.selected_concept_id,
                semantic_score=match.semantic_relevance,
                child_interest_alignment=match.child_interest_alignment,
                objective_activity_alignment=match.objective_activity_alignment,
                age_fit_score=match.age_fit_score,
                activity_safety_score=match.activity_safety_score,
                catalog_quality_score=match.catalog_quality_score,
                diversity_recency_penalty=0.0,
                final_score=match.overall_personalization_score,
                score_breakdown={
                    "concept_match_confidence": match.concept_match_confidence,
                    "child_interest_alignment": match.child_interest_alignment,
                    "objective_activity_alignment": match.objective_activity_alignment,
                    "age_fit_score": match.age_fit_score,
                    "activity_safety_score": match.activity_safety_score,
                    "catalog_quality_score": match.catalog_quality_score,
                    "diversity_recency_penalty": 0.0,
                    "final_score": match.overall_personalization_score,
                },
                reason_codes=match.reason_codes,
                selected=is_selected,
                lost_to_selected_because=lost_to_selected,
            )
        )
    return RankingDebugEvidenceV2(
        selected_activity_id=selected_match.activity_id,
        selected_activity_family_id=selected_match.activity_family_id,
        ranking_trace=tuple(top_k),
        rejected_candidates=tuple(rejected_candidates[:20]),
    )


def _match_priority(mode: str) -> int:
    return {"EXACT": 3, "ALIAS": 2, "SAFE_FALLBACK": 1}.get(mode, 0)


def _relative_artifact_ref(path: Path, cwd: Path) -> str:
    resolved = path.expanduser().resolve()
    try:
        relative = os.path.relpath(resolved, cwd.resolve())
    except ValueError as exc:
        raise WorkflowRuntimeError(
            "RUNTIME_NOT_READY", "input path must be on the runtime volume"
        ) from exc
    normalized = Path(relative).as_posix()
    if normalized in {"", "."} or normalized.startswith("/"):
        raise WorkflowRuntimeError("RUNTIME_NOT_READY", "input artifact reference is invalid")
    return normalized


def _require_hash(value: str | None) -> str:
    if value is None or len(value) != 64:
        raise WorkflowRuntimeError("MEDIA_RECAPTURE", "validated source is missing a SHA-256 hash")
    return value


def _hash_json(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _empty_hash() -> str:
    return hashlib.sha256(b"").hexdigest()


def _derive_band_seed(run_seed: int, age_band: str) -> int:
    digest = hashlib.sha256(f"{run_seed}:{age_band}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


def _seed_fingerprint(seed: int) -> str:
    return hashlib.sha256(str(seed).encode()).hexdigest()[:16]


def _fused_anchor_candidates(
    asr: AsrSuccessV1 | AsrFailureV1, vision: VisionUnderstandingSuccessV2
) -> tuple[_AnchorCandidate, ...]:
    candidates: list[_AnchorCandidate] = []
    for entity in vision.entities:
        candidates.append(
            _AnchorCandidate(
                label=entity.label.value,
                kind="subject",
                confidence=entity.confidence or 0.5,
                tags=_tokens(entity.label.value),
                claim_ids=(f"vision:{entity.observation_id}",),
                source_kind="VLM",
            )
        )
    for action in vision.actions:
        candidates.append(
            _AnchorCandidate(
                label=action.label.value,
                kind="action",
                confidence=action.confidence or 0.5,
                tags=_tokens(action.label.value),
                claim_ids=(f"vision:{action.observation_id}",),
                source_kind="VLM",
            )
        )
    for theme in vision.themes:
        candidates.append(
            _AnchorCandidate(
                label=theme.label.value,
                kind="story",
                confidence=theme.confidence or 0.5,
                tags=_tokens(theme.label.value),
                claim_ids=tuple(f"vision:{ref}" for ref in theme.evidence_refs)
                or (f"vision:{theme.observation_id}",),
                source_kind="VLM",
            )
        )
    if isinstance(asr, AsrSuccessV1) and asr.transcript_raw.strip():
        transcript_words = _tokens(asr.transcript_raw)
        candidates.append(
            _AnchorCandidate(
                label=asr.transcript_raw.strip(),
                kind="story",
                confidence=asr.language_probability or 0.5,
                tags=transcript_words,
                claim_ids=("asr:transcript",),
                source_kind="ASR",
            )
        )
        candidates.extend(
            _AnchorCandidate(
                label=word,
                kind="story",
                confidence=asr.language_probability or 0.5,
                tags=(word,),
                claim_ids=("asr:transcript",),
                source_kind="ASR",
            )
            for word in transcript_words
        )
    unique: dict[tuple[str, str], _AnchorCandidate] = {}
    for candidate in candidates:
        normalized = vision_label_normalize(candidate.label)
        if normalized:
            unique.setdefault((candidate.kind, normalized.casefold()), candidate)
    return tuple(unique.values())


def _tokens(*values: str) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        for token in _VIETNAMESE_WORDS.findall(value.casefold()):
            if len(token) > 1 and token not in result:
                result.append(token)
    return tuple(result)


def _anchor_set_for_candidate(
    candidate: _AnchorCandidate,
    candidates: tuple[_AnchorCandidate, ...],
    artifact_ref: str,
    artifact_sha256: str,
) -> SemanticAnchorSetV1:
    primary = _anchor_from_candidate(candidate, artifact_ref, artifact_sha256, "primary")

    secondary = tuple(
        _anchor_from_candidate(item, artifact_ref, artifact_sha256, f"secondary-{index}")
        for index, item in enumerate(candidates)
        if not (
            item.kind == candidate.kind
            and vision_label_normalize(item.label).casefold()
            == vision_label_normalize(candidate.label).casefold()
        )
    )[:8]
    digest = _hash_json(
        {
            "artifact": artifact_sha256,
            "primary": primary.model_dump(mode="json"),
            "secondary": [item.model_dump(mode="json") for item in secondary],
        }
    )
    return SemanticAnchorSetV1(
        anchor_set_id=f"ANCHORSET-{digest[:16]}",
        source_artifact_id=artifact_ref,
        source_artifact_sha256=artifact_sha256,
        gate_a_status="CONFIRMED",
        adult_confirmation_actor="PROJECT_OWNER",
        primary_anchor=primary,
        secondary_anchors=secondary,
    )


def _anchor_from_candidate(
    candidate: _AnchorCandidate,
    artifact_ref: str,
    artifact_sha256: str,
    anchor_id: str,
) -> SemanticAnchorV1:
    normalized = vision_label_normalize(candidate.label)
    return SemanticAnchorV1(
        anchor_id=f"{anchor_id}-{hashlib.sha256(normalized.encode()).hexdigest()[:10]}",
        kind=candidate.kind,  # type: ignore[arg-type]
        original_label=candidate.label,
        normalized_label=normalized,
        semantic_tags=candidate.tags,
        confidence=max(0.0, min(1.0, candidate.confidence)),
        adult_confirmed=True,
        provenance=AnchorProvenanceV1(
            source_artifact_id=artifact_ref,
            source_artifact_sha256=artifact_sha256,
            source_contract_name="WorkflowFusionV1",
            source_contract_version="1.0",
            source_claim_ids=candidate.claim_ids,
        ),
    )


def _demo_context(library: TemplateLibraryPort, age_band: str, session_id: str) -> P1ContextV1:
    age = _AGE_MONTHS[age_band]
    age_templates = tuple(
        item for item in library.templates if item.age_months_min <= age <= item.age_months_max
    )
    readiness = tuple(sorted({value for item in age_templates for value in item.readiness_ids}))
    completed = tuple(item.activity_ref.id for item in library.templates)
    materials = tuple(
        sorted({value for item in age_templates for value in item.material_option_ids})
    )
    policies = tuple(
        sorted(
            {value for item in age_templates for value in item.policy_constraints}
            | {"CAREGIVER_PRESENT"}
        )
    )
    return P1ContextV1(
        session_id=session_id,
        expected_session_version=1,
        age_months=age,
        readiness_ids=readiness,
        completed_activity_ids=completed,
        available_material_option_ids=materials,
        supervision_level="DIRECT",
        policy_flags=policies,
        candidate_status="ACTIVE_FIXTURE",
        gate_a_confirmed=True,
    )


def _duration_minutes(duration: dict[str, Any] | None) -> dict[str, int] | None:
    if duration is None:
        return None
    if duration["duration_type"] == "MULTI_DAY":
        initial = duration["initial_session_minutes"]
        assert isinstance(initial, int)
        return {"min_minutes": initial, "max_minutes": initial}
    minimum = duration["min_minutes"]
    maximum = duration["max_minutes"]
    assert isinstance(minimum, int) and isinstance(maximum, int)
    return {"min_minutes": minimum, "max_minutes": maximum}


def _story_scene_context(
    anchor_set: SemanticAnchorSetV1,
    spec: Any,
    asr: AsrSuccessV1 | AsrFailureV1,
    vision: VisionUnderstandingSuccessV2,
    primary_materials: tuple[str, ...],
    asset_ids: tuple[str, ...],
    semantic_match: SemanticMatchEvidenceV1,
    scene_understanding: ConfirmedSceneUnderstandingV2 | None = None,
    semantic_match_v2: SemanticActivityMatchV2 | None = None,
    experience_mode: str | None = None,
    age_adaptation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    story_hash = _hash_json(
        {
            "source": spec.source_artifact_sha256,
            "anchor": anchor_set.primary_anchor.anchor_id,
            "objective": spec.learning_focus.objective_ref.model_dump(mode="json"),
            "template": spec.activity_template.template_id,
        }
    )
    story_mode = "AGE_BASELINE" if experience_mode == "AGE_BASELINE_FALLBACK" else "SCENE_GROUNDED"
    scene_anchor = (
        semantic_match_v2.matched_anchor_labels_vi[0]
        if semantic_match_v2 is not None and semantic_match_v2.matched_anchor_labels_vi
        else anchor_set.primary_anchor.normalized_label
    )
    narration = (
        semantic_match_v2.video_handoff_prompt_vi
        if semantic_match_v2 is not None
        else f"Cùng khám phá {scene_anchor}, rồi thực hành hoạt động ngoài màn hình với người lớn."
        if story_mode == "SCENE_GROUNDED"
        else "Từ bức tranh, cùng người lớn thực hành hoạt động nền tảng phù hợp lứa tuổi."
    )
    activity_bridge = None
    if semantic_match_v2 is not None and age_adaptation is not None:
        activity_bridge = {
            "age_band": age_adaptation.get("age_band"),
            "continuity_mode": semantic_match_v2.continuity_mode,
            "setup_instruction_vi": semantic_match_v2.video_setup_vi,
            "focus_cues_vi": list(semantic_match_v2.video_focus_cues_vi),
            "handoff_prompt_vi": semantic_match_v2.video_handoff_prompt_vi,
            "offscreen_instruction_vi": semantic_match_v2.offscreen_instruction_vi,
            "bridge_status": (
                "REQUIRES_HUMAN_SETUP"
                if semantic_match_v2.expansion_bridge_required
                else "READY"
            ),
        }
    return {
        "story_id": f"STORY-{story_hash[:16]}",
        "scene_id": f"SCENE-{story_hash[16:32]}",
        "language": "vi-VN",
        "grounding": (
            "REAL_ASR_VLM_OBSERVATIONS"
            if isinstance(asr, AsrSuccessV1)
            else "REAL_VLM_OBSERVATIONS"
        ),
        "source_artifact_id": spec.source_artifact_id,
        "source_artifact_sha256": spec.source_artifact_sha256,
        "anchor_id": anchor_set.primary_anchor.anchor_id,
        "anchor_label_vi": anchor_set.primary_anchor.normalized_label,
        "semantic_match_mode": semantic_match.match_mode,
        "semantic_profile_id": semantic_match.profile_id,
        "semantic_match_score": semantic_match.score,
        "experience_mode": experience_mode or (
            "PERSONALIZED"
            if semantic_match.match_mode in {"EXACT", "ALIAS"}
            else "AGE_BASELINE_FALLBACK"
        ),
        "story_mode": story_mode,
        "scene_understanding_id": (
            scene_understanding.scene_understanding_id if scene_understanding is not None else None
        ),
        "scene_understanding_v2": (
            scene_understanding.model_dump(mode="json") if scene_understanding is not None else None
        ),
        "semantic_match_v2": (
            semantic_match_v2.model_dump(mode="json") if semantic_match_v2 is not None else None
        ),
        "age_adaptation_v2": age_adaptation,
        "activity_bridge_v2": activity_bridge,
        "continuity_v2": (
            {
                "continuity_mode": semantic_match_v2.continuity_mode,
                "planned_video_continuity_score": semantic_match_v2.planned_video_continuity_score,
                "actual_video_continuity_score": None,
                "actual_video_status": "NOT_RENDERED",
                "actual_video_artifact_ref": None,
                "bridge_required": semantic_match_v2.expansion_bridge_required,
            }
            if semantic_match_v2 is not None
            else None
        ),
        "narration_transcript_vi": (
            asr.transcript_raw if isinstance(asr, AsrSuccessV1) else ""
        ),
        "visual_entity_labels_vi": [item.label.value for item in vision.entities],
        "learning_objective": spec.learning_focus.objective_ref.model_dump(mode="json"),
        "primary_material_option_ids": list(primary_materials),
        "asset_ids": list(asset_ids),
        "narration_vi": narration,
    }


def _asr_summary(result: AsrSuccessV1 | AsrFailureV1) -> dict[str, Any]:
    if isinstance(result, AsrFailureV1):
        return {
            "status": result.status,
            "error_code": result.error_code.value,
            "error_detail": result.error_detail.value,
            "retryable": result.retryable,
            "attempt_number": result.attempt_number,
            "repair_attempted": result.repair_attempted,
            "transcript_vi": "",
        }
    return {
        "status": result.status,
        "transcript_vi": result.transcript_raw,
        "detected_language": result.detected_language,
        "language_probability": result.language_probability,
        "segment_count": len(result.segments),
        "input_duration_seconds": result.input_duration_seconds,
        "model_identifier": result.model_identifier,
        "model_revision": result.model_revision,
        "adapter_version": result.adapter_version,
        "runtime_version": result.runtime_version,
        "config_hash": result.config_hash,
    }


def _vision_summary(result: VisionUnderstandingSuccessV2) -> dict[str, Any]:
    return {
        "status": result.status,
        "entity_labels_vi": [item.label.value for item in result.entities],
        "action_labels_vi": [item.label.value for item in result.actions],
        "theme_labels_vi": [item.label.value for item in result.themes],
        "uncertainty": len(result.ambiguous_regions),
        "profile_id": result.profile_id,
        "model_provenance": result.model_provenance.model_dump(mode="json"),
        "adapter_version": result.adapter_version,
        "config_hash": result.config_hash,
    }


def _workflow_failure_details(
    reason: str, asr_result: object | None, vision_result: object | None
) -> dict[str, Any]:
    """Expose typed provider outcomes without leaking prompts, output, or runtime paths."""

    details: dict[str, Any] = {"reason": reason}
    if isinstance(asr_result, AsrFailureV1):
        details["asr"] = {
            "status": asr_result.status,
            "error_code": asr_result.error_code.value,
            "error_detail": asr_result.error_detail.value,
            "retryable": asr_result.retryable,
            "attempt_number": asr_result.attempt_number,
            "repair_attempted": asr_result.repair_attempted,
        }
    if isinstance(vision_result, VisionUnderstandingFailureV2):
        details["vision"] = {
            "status": vision_result.status,
            "error_code": vision_result.error_code.value,
            "error_detail": vision_result.error_detail.value,
            "retryable": vision_result.retryable,
            "attempt_number": vision_result.attempt_number,
            "repair_attempted": vision_result.repair_attempted,
            "policy_execution_state": vision_result.policy_execution_state,
            "mapping_diagnostics": list(vision_result.mapping_diagnostics),
        }
    return details


def _understanding_details(
    asr: AsrSuccessV1 | AsrFailureV1, vision: VisionUnderstandingSuccessV2
) -> dict[str, Any]:
    return {
        "asr_status": asr.status,
        "vision_status": vision.status,
        "transcript_language": (
            asr.detected_language if isinstance(asr, AsrSuccessV1) else None
        ),
        "resolution": "ASR_AND_VLM" if isinstance(asr, AsrSuccessV1) else "VLM_ONLY",
        "visual_entity_count": len(vision.entities),
    }


def _fusion_details(
    asr: AsrSuccessV1 | AsrFailureV1, vision: VisionUnderstandingSuccessV2
) -> dict[str, Any]:
    transcript_terms = set(_tokens(asr.transcript_raw)) if isinstance(asr, AsrSuccessV1) else set()
    visual_terms = set(
        _tokens(
            *(item.label.value for item in vision.entities),
            *(item.label.value for item in vision.themes),
        )
    )
    return {
        "modality_count": 2 if isinstance(asr, AsrSuccessV1) else 1,
        "asr_status": asr.status,
        "transcript_terms": sorted(transcript_terms),
        "visual_terms": sorted(visual_terms),
        "unmatched_transcript_terms": sorted(transcript_terms - visual_terms),
        "conflict_preserved": True,
    }


def _failed_band(
    age_band: AgeBand, seed: int, terminal_status: str, reason: str
) -> WorkflowBandResultV1:
    safe_status = (
        terminal_status
        if terminal_status
        in {
            "RUNTIME_NOT_READY",
            "MEDIA_RECAPTURE",
            "ASR_FAILED",
            "AI_FAILED",
            "NO_ELIGIBLE_ACTIVITY",
            "ASSET_CATALOG_MISS",
        }
        else "AI_FAILED"
    )
    return WorkflowBandResultV1(
        age_band=age_band,
        age_months=_AGE_MONTHS.get(age_band, 0),
        run_seed=seed,
        seed_fingerprint=_seed_fingerprint(seed),
        status="FAILED",
        terminal_status=safe_status,  # type: ignore[arg-type]
        stages=(
            WorkflowStageV1(
                stage="AGE_BAND",
                status="FAILED",
                reason_code=safe_status,
                details={"reason": reason},
            ),
        ),
        warnings=(reason,),
    )


def _unavailable_band(
    age_band: AgeBand,
    seed: int,
    reason_code: str,
    reason: str,
) -> WorkflowBandResultV1:
    return WorkflowBandResultV1(
        age_band=age_band,
        age_months=_AGE_MONTHS.get(age_band, 0),
        run_seed=seed,
        seed_fingerprint=_seed_fingerprint(seed),
        status="UNAVAILABLE",
        terminal_status="UNAVAILABLE_AGE_BAND",
        stages=(
            WorkflowStageV1(
                stage="AGE_BAND",
                status="BLOCKED",
                reason_code=reason_code,
                details={"reason": reason},
            ),
        ),
        warnings=(reason_code, reason),
    )


def _first_failure_status(bands: list[WorkflowBandResultV1]) -> str:
    return next(
        (band.terminal_status for band in bands if band.status != "SUCCEEDED"),
        "AI_FAILED",
    )


__all__ = [
    "BackendAiWorkflow",
    "BackendWorkflowRequest",
    "WorkflowRuntimeError",
]
