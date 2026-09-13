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
from typing import Any, Protocol
from uuid import uuid4

from sketch2life.application.ports.asr import AsrPort
from sketch2life.application.ports.vision_understanding_v2 import VisionUnderstandingPortV2
from sketch2life.application.services.media_validation import (
    DeterministicMediaValidator,
    MediaValidationRequest,
)
from sketch2life.application.services.p1_experience import P1ExperienceCompiler
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
from sketch2life.infrastructure.catalog.activity_semantics import (
    ActivitySemanticCatalog,
    SemanticCatalogError,
    load_activity_semantic_catalog,
)
from sketch2life.infrastructure.catalog.p1_catalog import (
    CatalogLoadError,
    P1TemplateLibrary,
    load_p1_template_library,
)
from sketch2life.infrastructure.catalog.pixi_assets import AssetCatalogError, PixiAssetCatalog
from sketch2life.infrastructure.media_validation.file_inspector import FileMediaSignalInspector


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
    asr_profile_id: AsrProfileId = AsrProfileId.WHISPER_TURBO_INT8_AUTO_V1


@dataclass(frozen=True, slots=True)
class _AnchorCandidate:
    label: str
    kind: str
    confidence: float
    tags: tuple[str, ...]
    claim_ids: tuple[str, ...]


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
        repo_root: Path,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._asr = asr
        self._vision = vision
        self._repo_root = repo_root.resolve()
        self._clock = clock
        self._media_validator = DeterministicMediaValidator(FileMediaSignalInspector())

    def run(self, request: BackendWorkflowRequest) -> BackendWorkflowResultV1:
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
        if not isinstance(asr_result, AsrSuccessV1) or not isinstance(
            vision_result, VisionUnderstandingSuccessV2
        ):
            terminal = "ASR_FAILED" if not isinstance(asr_result, AsrSuccessV1) else "AI_FAILED"
            return self._failure_result(
                workflow_run_id,
                run_seed,
                created_at,
                media,
                request,
                terminal,
                "real ASR/VLM returned a typed failure",
                asr_result=asr_result,
                vision_result=vision_result,
            )

        try:
            library = load_p1_template_library(self._repo_root, include_mvp=True)
            semantic_catalog = load_activity_semantic_catalog(self._repo_root)
            asset_catalog = PixiAssetCatalog(
                self._repo_root / "features" / "FEAT-020-backend-ai-workflow-demo"
            )
            asset_catalog.validate_all_age_bands()
        except (
            CatalogLoadError,
            SemanticCatalogError,
            AssetCatalogError,
            OSError,
            ValueError,
        ) as exc:
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

        bands: list[WorkflowBandResultV1] = []
        previous_activity_ids: set[str] = set()
        for age_band in request.age_bands:
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
                    status="SUCCEEDED",
                    details={"language": asr_result.detected_language},
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
            "warnings": (
                "VIDEO_DEFERRED",
                "DEMO_AUTOPILOT_DECISIONS",
                "AGE_MATRIX_PARTIAL_TEST_ONLY",
            )
            if partial_success
            else ("VIDEO_DEFERRED", "DEMO_AUTOPILOT_DECISIONS")
            if strict_success
            else (),
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
    ) -> object:
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
    ) -> object:
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

    def _run_age_band(
        self,
        *,
        request: BackendWorkflowRequest,
        age_band: AgeBand,
        run_seed: int,
        workflow_run_id: str,
        media: MediaValidationResultV1,
        asr: AsrSuccessV1,
        vision: VisionUnderstandingSuccessV2,
        library: P1TemplateLibrary,
        semantic_catalog: ActivitySemanticCatalog,
        asset_catalog: PixiAssetCatalog,
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
        primary_materials = _primary_material_ids(self._repo_root, activity_id)
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
            "duration_minutes": _duration_minutes(self._repo_root, activity_id),
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
            age_band=age_band,  # type: ignore[arg-type]
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
    asr: AsrSuccessV1, vision: VisionUnderstandingSuccessV2
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
            )
        )
    if asr.transcript_raw.strip():
        transcript_words = _tokens(asr.transcript_raw)
        candidates.append(
            _AnchorCandidate(
                label=asr.transcript_raw.strip(),
                kind="story",
                confidence=asr.language_probability or 0.5,
                tags=transcript_words,
                claim_ids=("asr:transcript",),
            )
        )
        candidates.extend(
            _AnchorCandidate(
                label=word,
                kind="story",
                confidence=asr.language_probability or 0.5,
                tags=(word,),
                claim_ids=("asr:transcript",),
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


def _demo_context(library: P1TemplateLibrary, age_band: str, session_id: str) -> P1ContextV1:
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


def _primary_material_ids(repo_root: Path, activity_id: str) -> tuple[str, ...]:
    golden_path = (
        repo_root
        / "data"
        / "activity-catalog"
        / "golden"
        / "v1"
        / "material-registry.v1.json"
    )
    try:
        document = json.loads(golden_path.read_text(encoding="utf-8"))
        option_kinds = {item["id"]: item.get("kind") for item in document.get("options", [])}
        groups = [
            item for item in document.get("groups", []) if item.get("activity_id") == activity_id
        ]
        primary_ids = tuple(
            option_id
            for group in groups
            for option_id in group.get("any_of", [])
            if option_kinds.get(option_id) == "PRIMARY"
        )
        if primary_ids:
            return primary_ids
    except (OSError, json.JSONDecodeError, TypeError, KeyError):
        pass

    mvp_path = repo_root / "data" / "activity-catalog" / "mvp" / "activities.v1.json"
    try:
        document = json.loads(mvp_path.read_text(encoding="utf-8"))
        record = next(item for item in document["activities"] if item["id"] == activity_id)
        return tuple(
            group["any_of"][0]
            for group in record.get("material_groups", [])
            if group.get("any_of")
        )
    except (OSError, json.JSONDecodeError, StopIteration, KeyError, TypeError, IndexError):
        return ()


def _duration_minutes(repo_root: Path, activity_id: str) -> dict[str, int] | None:
    records: list[dict[str, Any]] = []
    for path in (
        repo_root / "data" / "activity-catalog" / "golden" / "v1" / "activities.v2.json",
        repo_root / "data" / "activity-catalog" / "mvp" / "activities.v1.json",
    ):
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
            records.extend(document.get("activities", []))
        except (OSError, json.JSONDecodeError, TypeError):
            continue
    try:
        record = next(item for item in records if item.get("id") == activity_id)
        value = record.get("duration_minutes")
        if isinstance(value, int):
            return {"min_minutes": value, "max_minutes": value}
        if isinstance(value, dict):
            minimum = int(value["min"])
            maximum = int(value["max"])
            if minimum <= maximum:
                return {"min_minutes": minimum, "max_minutes": maximum}
    except (StopIteration, KeyError, TypeError, ValueError):
        pass
    return None


def _story_scene_context(
    anchor_set: SemanticAnchorSetV1,
    spec: Any,
    asr: AsrSuccessV1,
    vision: VisionUnderstandingSuccessV2,
    primary_materials: tuple[str, ...],
    asset_ids: tuple[str, ...],
    semantic_match: SemanticMatchEvidenceV1,
) -> dict[str, Any]:
    story_hash = _hash_json(
        {
            "source": spec.source_artifact_sha256,
            "anchor": anchor_set.primary_anchor.anchor_id,
            "objective": spec.learning_focus.objective_ref.model_dump(mode="json"),
            "template": spec.activity_template.template_id,
        }
    )
    return {
        "story_id": f"STORY-{story_hash[:16]}",
        "scene_id": f"SCENE-{story_hash[16:32]}",
        "language": "vi-VN",
        "grounding": "REAL_ASR_VLM_OBSERVATIONS",
        "source_artifact_id": spec.source_artifact_id,
        "source_artifact_sha256": spec.source_artifact_sha256,
        "anchor_id": anchor_set.primary_anchor.anchor_id,
        "anchor_label_vi": anchor_set.primary_anchor.normalized_label,
        "semantic_match_mode": semantic_match.match_mode,
        "semantic_profile_id": semantic_match.profile_id,
        "semantic_match_score": semantic_match.score,
        "narration_transcript_vi": asr.transcript_raw,
        "visual_entity_labels_vi": [item.label.value for item in vision.entities],
        "learning_objective": spec.learning_focus.objective_ref.model_dump(mode="json"),
        "primary_material_option_ids": list(primary_materials),
        "asset_ids": list(asset_ids),
        "narration_vi": (
            (
                f"Cùng khám phá {anchor_set.primary_anchor.normalized_label}, "
                "rồi thực hành hoạt động ngoài màn hình với người lớn."
            )
            if semantic_match.match_mode in {"EXACT", "ALIAS"}
            else "Từ bức tranh, cùng người lớn thực hành hoạt động nền tảng phù hợp lứa tuổi."
        ),
    }


def _asr_summary(result: AsrSuccessV1) -> dict[str, Any]:
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
        }
    return details


def _understanding_details(
    asr: AsrSuccessV1, vision: VisionUnderstandingSuccessV2
) -> dict[str, Any]:
    return {
        "asr_status": asr.status,
        "vision_status": vision.status,
        "transcript_language": asr.detected_language,
        "visual_entity_count": len(vision.entities),
    }


def _fusion_details(asr: AsrSuccessV1, vision: VisionUnderstandingSuccessV2) -> dict[str, Any]:
    transcript_terms = set(_tokens(asr.transcript_raw))
    visual_terms = set(
        _tokens(
            *(item.label.value for item in vision.entities),
            *(item.label.value for item in vision.themes),
        )
    )
    return {
        "modality_count": 2,
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
        age_band=age_band,  # type: ignore[arg-type]
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


def _first_failure_status(bands: list[WorkflowBandResultV1]) -> str:
    return next(
        (band.terminal_status for band in bands if band.status == "FAILED"),
        "AI_FAILED",
    )


__all__ = [
    "BackendAiWorkflow",
    "BackendWorkflowRequest",
    "WorkflowRuntimeError",
]
