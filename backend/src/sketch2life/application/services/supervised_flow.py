"""Adult-gated FEAT-018 workflow steps after image understanding."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import replace
from datetime import UTC, datetime
from hashlib import sha256
from threading import RLock
from typing import Any, Literal
from uuid import uuid4

from pydantic import TypeAdapter, ValidationError

from sketch2life.application.ports.session_storage import IdempotencyReceipt, IdempotencyStore
from sketch2life.application.ports.workflow_dependencies import (
    ActivityCatalogMetadataPort,
    SemanticCatalogPort,
    SemanticCatalogV2Port,
)
from sketch2life.application.services.ephemeral_sessions import (
    DEMO_ACTOR_REF,
    EphemeralSessionService,
    SessionWorkflowError,
)
from sketch2life.application.services.learning_media_fallback import LearningMediaFallback
from sketch2life.application.services.learning_media_resolver import (
    InMemoryLearningMediaStore,
    LearningMediaResolver,
)
from sketch2life.application.services.p1_experience import P1ExperienceCompiler
from sketch2life.application.services.pixi_topic_asset_candidates import (
    build_topic_asset_candidate_context,
)
from sketch2life.application.services.scene_exploration import (
    build_scene_exploration_plan,
    build_scene_focus_plan,
    build_subject_candidates,
)
from sketch2life.application.services.semantic_activity_resolver import (
    ActivityRecommendation,
    resolve_activity_options,
    resolve_activity_options_v2,
)
from sketch2life.application.services.topic_semantics import (
    claims_from_raw,
    compose_topic_vi,
    display_label_vi,
    enrich_anchor_set,
    semantic_tags_for_label,
)
from sketch2life.contracts.schemas.gate_a import GateAConfirmationV1
from sketch2life.contracts.schemas.learning_media import (
    LearningMediaRequestV1,
    LearningMediaResultV1,
)
from sketch2life.contracts.schemas.mobile_workflow import (
    ActivityRecommendationCardV1,
    ActivityRecommendationSetV1,
    MobileWorkflowCommandV1,
    MobileWorkflowResultV1,
    WorkflowResultProvenanceV1,
)
from sketch2life.contracts.schemas.p1_experience import (
    ActivityHandoffV1,
    AnchorProvenanceV1,
    ExperienceSpecV1,
    IntegrationGateDecisionV1,
    P1ContextOptionsV1,
    P1ContextV1,
    P1FilterResultV1,
    SemanticAnchorSetV1,
    SemanticAnchorV1,
    SemanticMatchEvidenceV1,
    VersionedRefV1,
)
from sketch2life.contracts.schemas.pixi_topic_asset_selection import (
    AdultConfirmedTopicV1,
    TopicAssetDescriptorV1,
)
from sketch2life.contracts.schemas.raw_understanding import (
    RawUnderstandingResultV1,
    RawUnderstandingSuccessV1,
)
from sketch2life.contracts.schemas.renderer import (
    ArtAnimationPlanV1,
    PixiArtAssetManifestV1,
    PixiRendererLaunchV1,
)
from sketch2life.contracts.schemas.vision import vision_label_normalize
from sketch2life.contracts.schemas.workflow_records import (
    FeedbackV1,
    SessionGalleryV1,
    SessionJourneyEntryV1,
)

_RAW_RESULT_ADAPTER: TypeAdapter[RawUnderstandingResultV1] = TypeAdapter(RawUnderstandingResultV1)
_FLOW_PROVENANCE = WorkflowResultProvenanceV1(
    producer="APPLICATION",
    component="feat018-supervised-flow",
    component_version="1.0",
    source_contracts=("GateAConfirmationV1", "P1ContextV1", "ExperienceSpecV1"),
)


def _narration_text(value: object) -> str:
    if not isinstance(value, dict):
        return ""
    transcript = value.get("transcript")
    return transcript.strip() if isinstance(transcript, str) else ""


def _recommendation_set(
    *,
    recommendation: ActivityRecommendation,
    metadata: ActivityCatalogMetadataPort,
    topic_label_vi: str,
) -> ActivityRecommendationSetV1:
    cards: list[ActivityRecommendationCardV1] = []
    for priority, option in enumerate(recommendation.options[:3], start=1):
        display = metadata.recommendation_display(option.activity_ref.id)
        match = recommendation.v2_match_for(option.activity_ref.id)
        if display is None or match is None:
            continue
        reason = (
            f"Tiếp nối trực tiếp từ {topic_label_vi.lower()}."
            if match.continuity_mode == "DIRECT_CONTINUATION"
            else f"Mở rộng nhẹ từ {topic_label_vi.lower()} sang một kỹ năng liên quan."
        )
        cards.append(
            ActivityRecommendationCardV1(
                priority=priority,
                activity_id=option.activity_ref.id,
                activity_version=option.activity_ref.version,
                title_vi=str(display["title_vi"]),
                summary_vi=str(display["summary_vi"]),
                match_reason_vi=reason,
                duration_minutes=int(display["duration_minutes"]),
                age_label_vi=str(display["age_label_vi"]),
                supervision_label_vi=str(display["supervision_label_vi"]),
                material_labels_vi=tuple(display.get("material_labels_vi", ())),
                fit_source=(
                    "DIRECT"
                    if match.continuity_mode == "DIRECT_CONTINUATION"
                    else "RELATED"
                ),
            )
        )
    return ActivityRecommendationSetV1(
        topic_label_vi=topic_label_vi,
        options=tuple(cards),
    )


class SupervisedFlowService:
    """Own the explicit human gates and deterministic workflow progression."""

    def __init__(
        self,
        *,
        sessions: EphemeralSessionService,
        idempotency: IdempotencyStore,
        p1_compiler: P1ExperienceCompiler,
        topic_assets: tuple[TopicAssetDescriptorV1, ...] = (),
        semantic_catalog: SemanticCatalogPort | None = None,
        semantic_catalog_v2: SemanticCatalogV2Port | None = None,
        catalog_metadata: ActivityCatalogMetadataPort | None = None,
        renderer_source_capability_issuer: Callable[..., tuple[str, datetime]] | None = None,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._sessions = sessions
        self._idempotency = idempotency
        self._compiler = p1_compiler
        self._topic_assets = topic_assets
        self._semantic_catalog = semantic_catalog
        self._semantic_catalog_v2 = semantic_catalog_v2
        self._catalog_metadata = catalog_metadata
        self._renderer_source_capability_issuer = renderer_source_capability_issuer
        self._now = now
        self._lock = RLock()
        self._media_resolver = LearningMediaResolver(InMemoryLearningMediaStore())
        self._media_fallback = LearningMediaFallback()

    def confirm_gate_a(
        self, command: MobileWorkflowCommandV1
    ) -> tuple[MobileWorkflowResultV1, bool]:
        operation = "CONFIRM_GATE_A"
        required = {"operation", "user_initiated", "confirmation", "primary_anchor_id"}
        fingerprint = self._validate_command(command, operation, required)
        scope = f"{command.session_id}:{operation}"
        with self._lock:
            if replay := self._replay(scope, command.idempotency_key, fingerprint):
                return replay, True
            snapshot = self._sessions.snapshot(command.session_id)
            self._expect_version(snapshot.version, command.expected_session_version)
            if snapshot.state != "GATE_A_PENDING":
                raise _workflow_error(
                    "GATE_A_REQUIRED", 409, "Image understanding must finish first."
                )
            values = self._sessions.workflow_record(command.session_id).values
            raw_value = values.get("raw_understanding")
            if not isinstance(raw_value, dict):
                raise _workflow_error(
                    "UNDERSTANDING_RESULT_MISSING", 409, "No image proposal is available."
                )
            raw = _RAW_RESULT_ADAPTER.validate_python(raw_value)
            if not isinstance(raw, RawUnderstandingSuccessV1):
                raise _workflow_error(
                    "UNDERSTANDING_FAILED", 409, "The image proposal is unavailable."
                )
            claims = _selectable_claims(raw)
            primary_id = command.payload.get("primary_anchor_id")
            try:
                confirmation = GateAConfirmationV1.model_validate(
                    {
                        **_require_mapping(command.payload.get("confirmation")),
                        "session_id": command.session_id,
                        "expected_session_version": command.expected_session_version,
                        "actor_ref": command.actor_ref,
                    }
                )
            except ValidationError as exc:
                raise _workflow_error(
                    "GATE_A_CONFIRMATION_INVALID",
                    422,
                    "Review and confirm one visible image claim.",
                ) from exc
            if confirmation.confirmed_claim_ids != tuple(
                dict.fromkeys(confirmation.confirmed_claim_ids)
            ):
                raise _workflow_error(
                    "GATE_A_CLAIMS_DUPLICATED", 422, "A claim can be confirmed only once."
                )
            if not set(confirmation.confirmed_claim_ids).issubset(claims):
                raise _workflow_error(
                    "GATE_A_CLAIM_NOT_FOUND",
                    422,
                    "The selected claim is not part of this image proposal.",
                )
            if (
                not isinstance(primary_id, str)
                or primary_id not in confirmation.confirmed_claim_ids
            ):
                raise _workflow_error(
                    "PRIMARY_ANCHOR_NOT_CONFIRMED",
                    422,
                    "Choose the main subject from confirmed claims.",
                )
            original_label, kind, confidence = claims[primary_id]
            correction = confirmation.correction.strip() if confirmation.correction else None
            anchor_label = correction or original_label
            if not anchor_label:
                raise _workflow_error(
                    "GATE_A_CORRECTION_EMPTY", 422, "The correction cannot be empty."
                )
            confirmed_claim_ids = tuple(confirmation.confirmed_claim_ids)
            ranked_claims = tuple(
                claim
                for claim in claims_from_raw(raw)
                if claim.observation_id in confirmed_claim_ids
            )
            primary_claim = next(
                (claim for claim in ranked_claims if claim.observation_id == primary_id),
                None,
            )
            if primary_claim is None:
                raise _workflow_error(
                    "GATE_A_CLAIM_NOT_FOUND",
                    422,
                    "The selected claim is not part of this image proposal.",
            )
            if correction:
                primary_claim = replace(
                    primary_claim,
                    label=correction,
                    display_label=display_label_vi(correction),
                )
            topic_claims = (primary_claim,) + tuple(
                claim for claim in ranked_claims if claim.observation_id != primary_id
            )
            topic_label_vi = compose_topic_vi(topic_claims)
            semantic_tags = tuple(
                dict.fromkeys(
                    tag
                    for claim in topic_claims
                    for tag in semantic_tags_for_label(claim.label)
                )
            )
            secondary_anchors = tuple(
                SemanticAnchorV1(
                    anchor_id=f"anchor-{claim.observation_id}",
                    kind=claim.kind,
                    original_label=claim.label,
                    normalized_label=vision_label_normalize(display_label_vi(claim.label)),
                    semantic_tags=semantic_tags_for_label(claim.label),
                    confidence=claim.confidence,
                    adult_confirmed=True,
                    provenance=AnchorProvenanceV1(
                        source_artifact_id=raw.source_image_ref.artifact_ref,
                        source_artifact_sha256=raw.source_image_ref.sha256,
                        source_contract_name=raw.contract_name,
                        source_contract_version=raw.contract_version,
                        source_claim_ids=(claim.observation_id,),
                    ),
                )
                for claim in topic_claims
                if claim.observation_id != primary_id
            )
            anchor = SemanticAnchorV1(
                anchor_id=f"anchor-{primary_id}",
                kind=kind,
                original_label=original_label,
                normalized_label=vision_label_normalize(display_label_vi(anchor_label)),
                semantic_tags=semantic_tags,
                confidence=confidence,
                adult_confirmed=True,
                provenance=AnchorProvenanceV1(
                    source_artifact_id=raw.source_image_ref.artifact_ref,
                    source_artifact_sha256=raw.source_image_ref.sha256,
                    source_contract_name=raw.contract_name,
                    source_contract_version=raw.contract_version,
                    source_claim_ids=confirmed_claim_ids,
                ),
            )
            anchor_set = enrich_anchor_set(
                raw=raw,
                confirmed_claim_ids=confirmed_claim_ids,
                anchor_set=SemanticAnchorSetV1(
                    anchor_set_id=f"anchors-{command.session_id}-{snapshot.version + 1}",
                    source_artifact_id=raw.source_image_ref.artifact_ref,
                    source_artifact_sha256=raw.source_image_ref.sha256,
                    gate_a_status="CONFIRMED",
                    adult_confirmation_actor="PROJECT_OWNER",
                    primary_anchor=anchor,
                    secondary_anchors=secondary_anchors,
                    adult_correction_label=correction,
                ),
            )
            topic = AdultConfirmedTopicV1.model_validate(
                {
                    "gateAConfirmed": True,
                    "topicLabels": tuple(
                        dict.fromkeys(
                            (topic_label_vi, *(claim.display_label for claim in topic_claims))
                        )
                    )[:5],
                    "topicTags": semantic_tags[:20],
                    "locale": "vi",
                    "styleProfileId": "flat-childlike-doodle-v1",
                    "requestedRoles": (),
                    "maxCandidates": 8,
                }
            )
            asset_context = build_topic_asset_candidate_context(
                query=topic,
                assets=self._topic_assets,
            )
            updated = self._sessions.advance(
                session_id=command.session_id,
                expected_version=snapshot.version,
                allowed_states=("GATE_A_PENDING",),
                next_state="UNDERSTANDING_PROPOSED",
                workflow_updates={
                    "gate_a_confirmation": confirmation.model_dump(mode="json"),
                    "anchor_set": anchor_set.model_dump(mode="json"),
                    "topic_asset_context": asset_context.model_dump(mode="json", by_alias=True),
                    "topic_label_vi": topic_label_vi,
                    "topic_claim_ids": list(confirmed_claim_ids),
                    "p1_context": None,
                    "p1_filter": None,
                    "experience_spec": None,
                    "gate_b": None,
                    "learning_media": None,
                    "handoff": None,
                    "feedback": None,
                    "journey": _append_journey(
                        values.get("journey"),
                        "GATE_A",
                        "COMPLETED",
                        artifact_refs=(raw.source_image_ref.artifact_ref,),
                    ),
                },
            )
            result = _result(
                status="SUCCEEDED",
                command=command,
                observed_version=updated.version,
                payload={
                    "gate_a_confirmation": confirmation.model_dump(mode="json"),
                    "anchor_set": anchor_set.model_dump(mode="json"),
                    "primary_anchor_choices": [
                        {
                            "claim_id": claim_id,
                            "label": display_label_vi(claim[0]),
                            "raw_label": claim[0],
                            "kind": claim[1],
                            "confidence": claim[2],
                        }
                        for claim_id, claim in claims.items()
                        if claim_id in confirmation.confirmed_claim_ids
                    ],
                    "topic_asset_context": asset_context.model_dump(mode="json", by_alias=True),
                },
            )
            self._remember(scope, command.idempotency_key, fingerprint, result)
            return result, False

    def request_retake(
        self, command: MobileWorkflowCommandV1
    ) -> tuple[MobileWorkflowResultV1, bool]:
        operation = "REQUEST_RETAKE"
        fingerprint = self._validate_command(command, operation, {"operation", "user_initiated"})
        scope = f"{command.session_id}:{operation}"
        with self._lock:
            if replay := self._replay(scope, command.idempotency_key, fingerprint):
                return replay, True
            snapshot = self._sessions.snapshot(command.session_id)
            self._expect_version(snapshot.version, command.expected_session_version)
            values = self._sessions.workflow_record(command.session_id).values
            if snapshot.state != "GATE_A_PENDING":
                raise _workflow_error(
                    "RETAKE_NOT_ALLOWED", 409, "Retake is available while reviewing Gate A."
                )
            raw_value = values.get("raw_understanding")
            artifact_refs: tuple[str, ...] = ()
            if isinstance(raw_value, dict):
                raw = _RAW_RESULT_ADAPTER.validate_python(raw_value)
                artifact_refs = (raw.source_image_ref.artifact_ref,)
            updated = self._sessions.advance(
                session_id=command.session_id,
                expected_version=snapshot.version,
                allowed_states=("GATE_A_PENDING",),
                next_state="MEDIA_RECAPTURE",
                workflow_updates={
                    "source_image_ref": None,
                    "media_validation": None,
                    "raw_understanding": None,
                    "gate_a_confirmation": None,
                    "anchor_set": None,
                    "topic_asset_context": None,
                    "p1_context": None,
                    "p1_filter": None,
                    "experience_spec": None,
                    "gate_b": None,
                    "learning_media": None,
                    "handoff": None,
                    "feedback": None,
                    "journey": _append_journey(
                        values.get("journey"),
                        "MEDIA",
                        "BLOCKED",
                        reason_codes=("USER_REQUESTED_RETAKE",),
                        artifact_refs=artifact_refs,
                    ),
                },
            )
            result = _result(
                status="SUCCEEDED",
                command=command,
                observed_version=updated.version,
                payload={"state": updated.state, "downstream_invalidated": True},
            )
            self._remember(scope, command.idempotency_key, fingerprint, result)
            return result, False

    def set_p1_context(
        self, command: MobileWorkflowCommandV1
    ) -> tuple[MobileWorkflowResultV1, bool]:
        operation = "SET_P1_CONTEXT"
        required = {"operation", "user_initiated", "context"}
        fingerprint = self._validate_command(command, operation, required)
        scope = f"{command.session_id}:{operation}"
        with self._lock:
            if replay := self._replay(scope, command.idempotency_key, fingerprint):
                return replay, True
            snapshot = self._sessions.snapshot(command.session_id)
            self._expect_version(snapshot.version, command.expected_session_version)
            if snapshot.state not in {"UNDERSTANDING_PROPOSED", "CONTEXT_REQUIRED"}:
                raise _workflow_error(
                    "GATE_A_REQUIRED", 409, "Confirm Gate A before entering adult context."
                )
            values = self._sessions.workflow_record(command.session_id).values
            if not isinstance(values.get("anchor_set"), dict):
                raise _workflow_error(
                    "GATE_A_REQUIRED", 409, "Confirm Gate A before entering adult context."
                )
            try:
                context = P1ContextV1.model_validate(
                    _require_mapping(command.payload.get("context"))
                )
            except ValidationError as exc:
                raise _workflow_error(
                    "P1_CONTEXT_INVALID", 422, "Complete the requested adult context fields."
                ) from exc
            if (
                context.session_id != command.session_id
                or context.expected_session_version != command.expected_session_version
                or not context.gate_a_confirmed
            ):
                raise _workflow_error(
                    "P1_CONTEXT_IDENTITY_MISMATCH",
                    422,
                    "Context must belong to this Gate-A-confirmed session.",
                )
            missing = context.missing_fields()
            next_state = "CONTEXT_REQUIRED" if missing else "UNDERSTANDING_PROPOSED"
            updated = self._sessions.advance(
                session_id=command.session_id,
                expected_version=snapshot.version,
                allowed_states=("UNDERSTANDING_PROPOSED", "CONTEXT_REQUIRED"),
                next_state=next_state,
                workflow_updates={
                    "p1_context": context.model_dump(mode="json"),
                    "p1_filter": None,
                    "experience_spec": None,
                    "gate_b": None,
                    "learning_media": None,
                    "handoff": None,
                    "feedback": None,
                    "journey": _append_journey(
                        values.get("journey"),
                        "P1",
                        "BLOCKED" if missing else "COMPLETED",
                        reason_codes=tuple(f"MISSING_CONTEXT:{field}" for field in missing),
                    ),
                },
            )
            result = _result(
                status="BLOCKED" if missing else "SUCCEEDED",
                command=command,
                observed_version=updated.version,
                payload={
                    "context": context.model_dump(mode="json"),
                    "missing_fields": list(missing),
                },
            )
            self._remember(scope, command.idempotency_key, fingerprint, result)
            return result, False

    def read_p1_context_options(
        self,
        *,
        session_id: str,
        request_id: str,
        expected_version: int,
        actor_ref: str,
        age_months: int,
    ) -> MobileWorkflowResultV1:
        if actor_ref != DEMO_ACTOR_REF:
            raise _workflow_error(
                "DEMO_ACTOR_INVALID", 422, "The local demo actor marker is invalid."
            )
        snapshot = self._sessions.snapshot(session_id)
        self._expect_version(snapshot.version, expected_version)
        if snapshot.state not in {"UNDERSTANDING_PROPOSED", "CONTEXT_REQUIRED"}:
            raise _workflow_error(
                "GATE_A_REQUIRED", 409, "Confirm Gate A before requesting P1 options."
            )
        values = self._sessions.workflow_record(session_id).values
        anchor_value = values.get("anchor_set")
        if not isinstance(anchor_value, dict):
            raise _workflow_error("GATE_A_REQUIRED", 409, "A confirmed image topic is required.")
        anchor_set = SemanticAnchorSetV1.model_validate(anchor_value)
        recommendation: ActivityRecommendation | None = None
        narration_text = _narration_text(values.get("narration_result"))
        if self._semantic_catalog_v2 is not None:
            recommendation = resolve_activity_options_v2(
                anchor_set=anchor_set,
                age_months=age_months,
                catalog=self._semantic_catalog_v2,
                compiler=self._compiler,
                narration_text=narration_text,
            )
            context_options = recommendation.options
        elif self._semantic_catalog is not None:
            recommendation = resolve_activity_options(
                anchor_set=anchor_set,
                age_months=age_months,
                catalog=self._semantic_catalog,
                compiler=self._compiler,
            )
            context_options = recommendation.options
        else:
            context_options = self._compiler.context_options(anchor_set, age_months)
        options = P1ContextOptionsV1(
            session_id=session_id,
            expected_session_version=snapshot.version,
            age_months=age_months,
            confirmed_anchor_label=anchor_set.primary_anchor.normalized_label,
            options=context_options,
        )
        payload = options.model_dump(mode="json")
        if recommendation is not None:
            payload["recommendation"] = recommendation.metadata()
        topic_label = self._sessions.workflow_record(session_id).values.get("topic_label_vi")
        if isinstance(topic_label, str) and topic_label:
            payload["topic_label_vi"] = topic_label
            if recommendation is not None and self._catalog_metadata is not None:
                payload["activity_recommendations"] = _recommendation_set(
                    recommendation=recommendation,
                    metadata=self._catalog_metadata,
                    topic_label_vi=topic_label,
                ).model_dump(mode="json")
        return MobileWorkflowResultV1(
            status="SUCCEEDED",
            request_id=request_id,
            session_id=session_id,
            expected_session_version=expected_version,
            observed_session_version=snapshot.version,
            provenance=_FLOW_PROVENANCE,
            payload=payload,
        )

    def run_p1_filter(
        self, command: MobileWorkflowCommandV1
    ) -> tuple[MobileWorkflowResultV1, bool]:
        operation = "RUN_P1_FILTER"
        fingerprint = self._validate_command(command, operation, {"operation", "user_initiated"})
        scope = f"{command.session_id}:{operation}"
        with self._lock:
            if replay := self._replay(scope, command.idempotency_key, fingerprint):
                return replay, True
            snapshot = self._sessions.snapshot(command.session_id)
            self._expect_version(snapshot.version, command.expected_session_version)
            if snapshot.state not in {"UNDERSTANDING_PROPOSED", "CONTEXT_REQUIRED"}:
                raise _workflow_error(
                    "P1_FILTER_NOT_ALLOWED", 409, "Submit adult context after Gate A first."
                )
            values = self._sessions.workflow_record(command.session_id).values
            anchor_value, context_value = values.get("anchor_set"), values.get("p1_context")
            if not isinstance(anchor_value, dict) or not isinstance(context_value, dict):
                raise _workflow_error(
                    "P1_CONTEXT_REQUIRED", 409, "Enter all required adult context before filtering."
                )
            anchor_set = SemanticAnchorSetV1.model_validate(anchor_value)
            context = P1ContextV1.model_validate(context_value).model_copy(
                update={"expected_session_version": snapshot.version}
            )
            semantic_match: SemanticMatchEvidenceV1 | None = None
            preferred_template_id: str | None = None
            if context.age_months is None:
                filtered = self._compiler.select(anchor_set, context)
            elif self._semantic_catalog_v2 is not None:
                recommendation = resolve_activity_options_v2(
                    anchor_set=anchor_set,
                    age_months=context.age_months,
                    catalog=self._semantic_catalog_v2,
                    compiler=self._compiler,
                    narration_text=_narration_text(values.get("narration_result")),
                )
                if context.selected_activity_id is not None:
                    preferred_template_id = recommendation.template_for(
                        context.selected_activity_id
                    )
                    semantic_match = recommendation.evidence_for(context.selected_activity_id)
                if preferred_template_id is None or semantic_match is None:
                    filtered = P1FilterResultV1(
                        status="NO_ELIGIBLE_ACTIVITY",
                        reason_codes=("ACTIVITY_NOT_IN_SEMANTIC_SHORTLIST",),
                    )
                else:
                    filtered = self._compiler.select(
                        anchor_set,
                        context,
                        preferred_template_id=preferred_template_id,
                    )
            elif self._semantic_catalog is not None:
                recommendation = resolve_activity_options(
                    anchor_set=anchor_set,
                    age_months=context.age_months,
                    catalog=self._semantic_catalog,
                    compiler=self._compiler,
                )
                if context.selected_activity_id is not None:
                    preferred_template_id = recommendation.template_for(
                        context.selected_activity_id
                    )
                    semantic_match = recommendation.evidence_for(context.selected_activity_id)
                if preferred_template_id is None or semantic_match is None:
                    filtered = P1FilterResultV1(
                        status="NO_ELIGIBLE_ACTIVITY",
                        reason_codes=("ACTIVITY_NOT_IN_SEMANTIC_SHORTLIST",),
                    )
                else:
                    filtered = self._compiler.select(
                        anchor_set,
                        context,
                        preferred_template_id=preferred_template_id,
                    )
            else:
                filtered = self._compiler.select(anchor_set, context)
            valid = filtered.status == "VALID_CANDIDATE"
            if valid:
                next_state = "CANDIDATES_READY"
            elif filtered.status == "MISSING_CONTEXT":
                next_state = "CONTEXT_REQUIRED"
            else:
                next_state = "UNDERSTANDING_PROPOSED"
            updated = self._sessions.advance(
                session_id=command.session_id,
                expected_version=snapshot.version,
                allowed_states=("UNDERSTANDING_PROPOSED", "CONTEXT_REQUIRED"),
                next_state=next_state,
                workflow_updates={
                    "p1_context": context.model_dump(mode="json"),
                    "p1_filter": filtered.model_dump(mode="json"),
                    "semantic_match": (
                        semantic_match.model_dump(mode="json")
                        if semantic_match is not None
                        else None
                    ),
                    "journey": _append_journey(
                        values.get("journey"),
                        "P1",
                        "COMPLETED" if valid else "BLOCKED",
                        reason_codes=filtered.reason_codes,
                    ),
                },
            )
            result = _result(
                status="SUCCEEDED" if valid else "BLOCKED",
                command=command,
                observed_version=updated.version,
                payload={"filter_result": filtered.model_dump(mode="json")},
            )
            self._remember(scope, command.idempotency_key, fingerprint, result)
            return result, False

    def prepare_experience(
        self, command: MobileWorkflowCommandV1
    ) -> tuple[MobileWorkflowResultV1, bool]:
        operation = "PREPARE_EXPERIENCE"
        fingerprint = self._validate_command(command, operation, {"operation", "user_initiated"})
        scope = f"{command.session_id}:{operation}"
        with self._lock:
            if replay := self._replay(scope, command.idempotency_key, fingerprint):
                return replay, True
            snapshot = self._sessions.snapshot(command.session_id)
            self._expect_version(snapshot.version, command.expected_session_version)
            if snapshot.state != "CANDIDATES_READY":
                raise _workflow_error(
                    "P1_CANDIDATE_REQUIRED", 409, "A valid P1 candidate is required."
                )
            values = self._sessions.workflow_record(command.session_id).values
            anchor_value = values.get("anchor_set")
            context_value = values.get("p1_context")
            filter_value = values.get("p1_filter")
            if not all(
                isinstance(item, dict) for item in (anchor_value, context_value, filter_value)
            ):
                raise _workflow_error("P1_RESULT_MISSING", 409, "The P1 selection is unavailable.")
            anchor_set = SemanticAnchorSetV1.model_validate(anchor_value)
            context = P1ContextV1.model_validate(context_value).model_copy(
                update={"expected_session_version": snapshot.version}
            )
            filtered = P1FilterResultV1.model_validate(filter_value)
            if filtered.template_ref is None:
                raise _workflow_error(
                    "P1_TEMPLATE_MISSING", 409, "The selected template is unavailable."
                )
            semantic_match: SemanticMatchEvidenceV1 | None = None
            semantic_match_value = values.get("semantic_match")
            if isinstance(semantic_match_value, dict):
                semantic_match = SemanticMatchEvidenceV1.model_validate(semantic_match_value)
            compilation = self._compiler.compile(
                anchor_set,
                context,
                preferred_template_id=filtered.template_ref.id,
                semantic_match=semantic_match,
            )
            if compilation.spec is None:
                result = _result(
                    status="BLOCKED",
                    command=command,
                    observed_version=snapshot.version,
                    payload={
                        "filter_result": compilation.filter_result.model_dump(mode="json"),
                        "fit_evaluation": (
                            compilation.fit_evaluation.model_dump(mode="json")
                            if compilation.fit_evaluation is not None
                            else None
                        ),
                        "reason_codes": list(compilation.gate_b.reason_codes),
                    },
                )
                self._remember(scope, command.idempotency_key, fingerprint, result)
                return result, False
            updated = self._sessions.advance(
                session_id=command.session_id,
                expected_version=snapshot.version,
                allowed_states=("CANDIDATES_READY",),
                next_state="GATE_B_PENDING",
                workflow_updates={
                    "p1_context": context.model_dump(mode="json"),
                    "experience_spec": compilation.spec.model_dump(mode="json"),
                    "gate_b": None,
                    "learning_media": None,
                    "handoff": None,
                    "journey": _append_journey(
                        values.get("journey"),
                        "GATE_B",
                        "BLOCKED",
                        reason_codes=("AWAITING_ADULT_REVIEW",),
                    ),
                },
            )
            result = _result(
                status="SUCCEEDED",
                command=command,
                observed_version=updated.version,
                payload={
                    "status": "AWAITING_ADULT_GATE_B",
                    "experience_spec": compilation.spec.model_dump(mode="json"),
                    "fit_evaluation": compilation.fit_evaluation.model_dump(mode="json")
                    if compilation.fit_evaluation is not None
                    else None,
                    "generation_called": False,
                },
            )
            self._remember(scope, command.idempotency_key, fingerprint, result)
            return result, False

    def approve_gate_b(
        self, command: MobileWorkflowCommandV1
    ) -> tuple[MobileWorkflowResultV1, bool]:
        operation = "APPROVE_GATE_B"
        required = {"operation", "user_initiated", "approved"}
        fingerprint = self._validate_command(command, operation, required)
        scope = f"{command.session_id}:{operation}"
        with self._lock:
            if replay := self._replay(scope, command.idempotency_key, fingerprint):
                return replay, True
            snapshot = self._sessions.snapshot(command.session_id)
            self._expect_version(snapshot.version, command.expected_session_version)
            if snapshot.state != "GATE_B_PENDING":
                raise _workflow_error(
                    "GATE_B_REQUIRED", 409, "Review the exact activity before approval."
                )
            approved_by_adult = command.payload.get("approved") is True
            if not approved_by_adult:
                result = _result(
                    status="BLOCKED",
                    command=command,
                    observed_version=snapshot.version,
                    payload={"status": "ADULT_DECLINED", "state": snapshot.state},
                )
                self._remember(scope, command.idempotency_key, fingerprint, result)
                return result, False
            values = self._sessions.workflow_record(command.session_id).values
            spec_value, context_value = values.get("experience_spec"), values.get("p1_context")
            if not isinstance(spec_value, dict) or not isinstance(context_value, dict):
                raise _workflow_error(
                    "EXPERIENCE_SPEC_MISSING", 409, "The prepared experience is unavailable."
                )
            spec = ExperienceSpecV1.model_validate(spec_value)
            context = P1ContextV1.model_validate(context_value).model_copy(
                update={"expected_session_version": snapshot.version}
            )
            gate_b = self._compiler.approve_gate_b(spec, context)
            if gate_b.status != "APPROVED":
                result = _result(
                    status="BLOCKED",
                    command=command,
                    observed_version=snapshot.version,
                    payload={"gate_b": gate_b.model_dump(mode="json")},
                )
                self._remember(scope, command.idempotency_key, fingerprint, result)
                return result, False
            media_request = _learning_media_request(command, spec, snapshot.version)
            cache_result = self._media_resolver.resolve(media_request)
            learning_media = (
                cache_result
                if cache_result.status == "READY"
                else self._media_fallback.resolve(
                    media_request, cache_result.reason_code or "CACHE_MISS"
                )
            )
            updated = self._sessions.advance(
                session_id=command.session_id,
                expected_version=snapshot.version,
                allowed_states=("GATE_B_PENDING",),
                next_state="EXPERIENCE_READY",
                workflow_updates={
                    "p1_context": context.model_dump(mode="json"),
                    "gate_b": gate_b.model_dump(mode="json"),
                    "learning_media": learning_media.model_dump(mode="json"),
                    "journey": _append_journey(
                        values.get("journey"),
                        "GATE_B",
                        "COMPLETED",
                        artifact_refs=(spec.spec_id,),
                    )
                    + _append_journey((), "EXPERIENCE", "COMPLETED", artifact_refs=(spec.spec_id,)),
                },
            )
            result = _result(
                status="SUCCEEDED",
                command=command,
                observed_version=updated.version,
                payload={
                    "gate_b": gate_b.model_dump(mode="json"),
                    "learning_media": learning_media.model_dump(mode="json"),
                    "generation_called": learning_media.generation_called,
                },
            )
            self._remember(scope, command.idempotency_key, fingerprint, result)
            return result, False

    def complete_handoff(
        self, command: MobileWorkflowCommandV1
    ) -> tuple[MobileWorkflowResultV1, bool]:
        operation = "COMPLETE_HANDOFF"
        fingerprint = self._validate_command(command, operation, {"operation", "user_initiated"})
        scope = f"{command.session_id}:{operation}"
        with self._lock:
            if replay := self._replay(scope, command.idempotency_key, fingerprint):
                return replay, True
            snapshot = self._sessions.snapshot(command.session_id)
            self._expect_version(snapshot.version, command.expected_session_version)
            if snapshot.state != "EXPERIENCE_READY":
                raise _workflow_error(
                    "HANDOFF_NOT_READY", 409, "Gate B and P4 resolution must finish first."
                )
            values = self._sessions.workflow_record(command.session_id).values
            spec_value = values.get("experience_spec")
            gate_value = values.get("gate_b")
            media_value = values.get("learning_media")
            if (
                not isinstance(spec_value, dict)
                or not isinstance(gate_value, dict)
                or not isinstance(media_value, dict)
            ):
                raise _workflow_error(
                    "HANDOFF_IDENTITY_MISSING",
                    409,
                    "The approved activity identity is unavailable.",
                )
            spec = ExperienceSpecV1.model_validate(spec_value)
            gate = IntegrationGateDecisionV1.model_validate(gate_value)
            media = _validate_learning_media(media_value)
            if gate.status != "APPROVED" or media.status == "BLOCKED":
                raise _workflow_error(
                    "HANDOFF_BLOCKED", 409, "The approved activity is not ready for handoff."
                )
            assert gate.spec_ref and gate.activity_ref and gate.objective_ref and gate.template_ref
            handoff = ActivityHandoffV1(
                status="READY",
                session_id=command.session_id,
                spec_ref=gate.spec_ref,
                activity_ref=gate.activity_ref,
                objective_ref=gate.objective_ref,
                template_ref=gate.template_ref,
            )
            updated = self._sessions.advance(
                session_id=command.session_id,
                expected_version=snapshot.version,
                allowed_states=("EXPERIENCE_READY",),
                next_state="HANDOFF_READY",
                workflow_updates={
                    "handoff": handoff.model_dump(mode="json"),
                    "journey": _append_journey(
                        values.get("journey"), "HANDOFF", "COMPLETED", artifact_refs=(spec.spec_id,)
                    ),
                },
            )
            result = _result(
                status="SUCCEEDED",
                command=command,
                observed_version=updated.version,
                payload={
                    "handoff": handoff.model_dump(mode="json"),
                    "learning_media": media.model_dump(mode="json"),
                },
            )
            self._remember(scope, command.idempotency_key, fingerprint, result)
            return result, False

    def prepare_renderer(
        self, command: MobileWorkflowCommandV1
    ) -> tuple[MobileWorkflowResultV1, bool]:
        operation = "PREPARE_RENDERER"
        fingerprint = self._validate_command(command, operation, {"operation", "user_initiated"})
        scope = f"{command.session_id}:{operation}"
        with self._lock:
            if replay := self._replay(scope, command.idempotency_key, fingerprint):
                return replay, True
            snapshot = self._sessions.snapshot(command.session_id)
            self._expect_version(snapshot.version, command.expected_session_version)
            if snapshot.state not in {"EXPERIENCE_READY", "HANDOFF_READY", "FEEDBACK_RECORDED"}:
                raise _workflow_error(
                    "RENDERER_NOT_READY", 409, "Approve the exact experience before opening Pixi."
                )
            if self._renderer_source_capability_issuer is None:
                raise _workflow_error(
                    "RENDERER_NOT_CONFIGURED",
                    503,
                    "The approved-source renderer is not configured.",
                )
            workflow = self._sessions.workflow_record(command.session_id)
            spec_value = workflow.values.get("experience_spec")
            if not isinstance(spec_value, dict):
                raise _workflow_error(
                    "EXPERIENCE_SPEC_MISSING", 409, "The approved experience is unavailable."
                )
            spec = ExperienceSpecV1.model_validate(spec_value)
            raw_value = workflow.values.get("raw_understanding")
            anchor_value = workflow.values.get("anchor_set")
            if not isinstance(raw_value, dict) or not isinstance(anchor_value, dict):
                raise _workflow_error(
                    "UNDERSTANDING_RESULT_MISSING",
                    409,
                    "The approved drawing understanding is unavailable.",
                )
            raw = _RAW_RESULT_ADAPTER.validate_python(raw_value)
            if not isinstance(raw, RawUnderstandingSuccessV1):
                raise _workflow_error(
                    "UNDERSTANDING_FAILED", 409, "The drawing understanding is unavailable."
                )
            anchor_set = SemanticAnchorSetV1.model_validate(anchor_value)
            subject_candidates = build_subject_candidates(
                session_id=command.session_id,
                raw=raw,
                anchor_set=anchor_set,
            )
            scene_exploration = build_scene_exploration_plan(
                session_id=command.session_id,
                experience_spec_ref=VersionedRefV1(id=spec.spec_id, version=spec.spec_version),
                raw=raw,
                candidates=subject_candidates,
                learning_bridge_vi=spec.bridge_sentence.sentence_vi,
            )
            region_hints = workflow.values.get("scene_focus_regions")
            focus_plan = build_scene_focus_plan(
                session_id=command.session_id,
                experience_spec_ref=VersionedRefV1(id=spec.spec_id, version=spec.spec_version),
                raw=raw,
                candidates=subject_candidates,
                region_hints=region_hints if isinstance(region_hints, dict) else None,
            )
            capability, expires_at = self._renderer_source_capability_issuer(
                session_id=command.session_id,
                expected_session_version=snapshot.version,
                actor_ref=command.actor_ref,
                experience_spec_id=spec.spec_id,
                experience_spec_version=spec.spec_version,
            )
            spec_ref = VersionedRefV1(id=spec.spec_id, version=spec.spec_version)
            source_artifact_ref = spec.source_artifact_id
            source_sha256 = spec.source_artifact_sha256
            renderer_objects: list[dict[str, object]] = [
                {
                    "id": "original-art",
                    "label": subject_candidates.items[0].label_vi,
                    "asset": {
                        "source_asset_id": "source-original-art",
                        "source_asset_version": "1",
                        "uri": "source:original-art",
                        "asset_kind": "WHOLE_DRAWING",
                        "source_sha256": source_sha256,
                    },
                    "extraction_status": "READY",
                    "interactive": False,
                    "initial_transform": {
                        "position": {"x": 0.5, "y": 0.5},
                        "scale": 0.92,
                        "rotation_degrees": -1.5,
                        "opacity": 1,
                    },
                }
            ]
            renderer_motions: list[dict[str, object]] = [
                {
                    "id": "original-art-reveal",
                    "scene_id": "whole-image-reveal",
                    "kind": "DRAW_REVEAL",
                    "target_id": "original-art",
                    "duration_seconds": 1.6,
                },
                {
                    "id": "original-art-focus",
                    "scene_id": "story-focus",
                    "kind": "SCALE",
                    "target_id": "original-art",
                    "duration_seconds": 2.2,
                    "scale": 1.08,
                },
                {
                    "id": "original-art-drift",
                    "scene_id": "story-motion",
                    "kind": "MOVE_TO",
                    "target_id": "original-art",
                    "duration_seconds": 2.4,
                    "to": {"x": 0.53, "y": 0.48},
                },
                {
                    "id": "original-art-settle",
                    "scene_id": "story-settle",
                    "kind": "ROTATE",
                    "target_id": "original-art",
                    "duration_seconds": 1.5,
                    "rotation_degrees": 1.5,
                },
            ]
            if focus_plan.extraction_status == "READY":
                for target in focus_plan.targets:
                    assert target.source_region is not None
                    object_id = f"focus-{target.target_ref}"
                    center_x = target.source_region.x + target.source_region.width / 2
                    center_y = target.source_region.y + target.source_region.height / 2
                    renderer_objects.append(
                        {
                            "id": object_id,
                            "label": target.label_vi,
                            "asset": {
                                "source_asset_id": "source-original-art",
                                "source_asset_version": "1",
                                "uri": "source:original-art",
                                "asset_kind": target.asset_kind,
                                "crop_version": target.extraction_version,
                                "source_region": target.source_region.model_dump(mode="python"),
                                "source_sha256": source_sha256,
                            },
                            "extraction_status": "READY",
                            "interactive": True,
                            "initial_transform": {
                                "position": {"x": center_x, "y": center_y},
                                "scale": 0.82 + target.depth_layer * 0.06,
                                "rotation_degrees": 0,
                                "opacity": 0,
                            },
                        }
                    )
                    renderer_motions.extend(
                        [
                            {
                                "id": f"{object_id}-reveal",
                                "scene_id": "focus-reveal",
                                "kind": "DRAW_REVEAL",
                                "target_id": object_id,
                                "duration_seconds": 0.8,
                            },
                            {
                                "id": f"{object_id}-float",
                                "scene_id": "focus-parallax",
                                "kind": "MOVE_TO",
                                "target_id": object_id,
                                "duration_seconds": 1.4,
                                "to": {
                                    "x": min(0.92, max(0.08, center_x + 0.02)),
                                    "y": min(0.92, max(0.08, center_y - 0.015)),
                                },
                            },
                        ]
                    )

            renderer_plan = ArtAnimationPlanV1.model_validate(
                {
                    "contract_name": "ArtAnimationPlanV1",
                    "contract_version": "1.0",
                    "session_id": command.session_id,
                    "experience_spec_ref": spec_ref.model_dump(mode="python"),
                    "source_artifact_ref": source_artifact_ref,
                    "source_artifact_sha256": source_sha256,
                    "plan": {
                        "contract_version": "1",
                        "plan_id": spec.spec_id,
                        "plan_version": str(spec.spec_version),
                        "stage": {"width": 800, "height": 600},
                        "objects": renderer_objects,
                        "motions": renderer_motions,
                    },
                    "original_art_preserved": True,
                    "video_executed": False,
                }
            )
            manifest = PixiArtAssetManifestV1.model_validate(
                {
                    "contract_name": "PixiArtAssetManifestV1",
                    "contract_version": "1.0",
                    "session_id": command.session_id,
                    "experience_spec_ref": spec_ref.model_dump(mode="python"),
                    "source_artifact_ref": source_artifact_ref,
                    "source_artifact_sha256": source_sha256,
                    "assets": [
                        {
                            "asset_id": "original-art-source",
                            "asset_version": "1",
                            "asset_ref": source_artifact_ref,
                            "sha256": source_sha256,
                            "role": "ORIGINAL_ART",
                            "review_status": "SOURCE_ORIGINAL",
                            "rights_status": "NOT_APPLICABLE",
                        }
                    ],
                    "original_art_preserved": True,
                    "provider_generation_called": False,
                }
            )
            launch = PixiRendererLaunchV1.model_validate(
                {
                    "contract_name": "PixiRendererLaunchV1",
                    "contract_version": "1.0",
                    "session_id": command.session_id,
                    "expected_session_version": snapshot.version,
                    "experience_spec_ref": spec_ref.model_dump(mode="python"),
                    "asset_manifest": manifest.model_dump(mode="python"),
                    "animation_plan": renderer_plan.model_dump(mode="python"),
                    "scene_exploration_plan": scene_exploration.model_dump(
                        mode="python", by_alias=True, exclude_none=True
                    ),
                    "scene_focus_plan": focus_plan.model_dump(
                        mode="python", by_alias=True, exclude_none=True
                    ),
                    "source_read_endpoint": "/v1/renderer/source",
                    "source_read_capability": capability,
                    "source_read_expires_at": expires_at,
                }
            )
            result = _result(
                status="SUCCEEDED",
                command=command,
                observed_version=snapshot.version,
                payload={
                    "renderer_launch": launch.model_dump(
                        mode="json", by_alias=True, exclude_none=True
                    ),
                    "subject_candidates": subject_candidates.model_dump(
                        mode="json", by_alias=True, exclude_none=True
                    ),
                    "scene_exploration_plan": scene_exploration.model_dump(
                        mode="json", by_alias=True, exclude_none=True
                    ),
                    "scene_focus_plan": focus_plan.model_dump(
                        mode="json", by_alias=True, exclude_none=True
                    ),
                    "pixi_intro_storyboard": {
                        "contract_name": "PixiIntroStoryboardV1",
                        "contract_version": "1.0",
                        "session_id": command.session_id,
                        "experience_spec_ref": spec_ref.model_dump(mode="json"),
                        "source_artifact_ref": source_artifact_ref,
                        "beats": [
                            {
                                "beat_id": beat.beat_id,
                                "start_seconds": beat.start_seconds,
                                "end_seconds": beat.end_seconds,
                                "caption_vi": beat.caption_vi,
                                "label_vi": beat.label_vi,
                                "target_ref": beat.target_ref,
                                "effect": beat.effect,
                                "tap_enabled": beat.tap_enabled,
                            }
                            for beat in scene_exploration.beats
                        ],
                        "subject_candidates": subject_candidates.model_dump(
                            mode="json", by_alias=True, exclude_none=True
                        ),
                        "scene_focus_plan": focus_plan.model_dump(
                            mode="json", by_alias=True, exclude_none=True
                        ),
                        "original_art_preserved": True,
                        "video_placeholder_only": True,
                    },
                },
            )
            self._remember(scope, command.idempotency_key, fingerprint, result)
            return result, False

    def record_feedback(
        self, command: MobileWorkflowCommandV1
    ) -> tuple[MobileWorkflowResultV1, bool]:
        operation = "RECORD_FEEDBACK"
        required = {"operation", "user_initiated", "feedback"}
        fingerprint = self._validate_command(command, operation, required)
        scope = f"{command.session_id}:{operation}"
        with self._lock:
            if replay := self._replay(scope, command.idempotency_key, fingerprint):
                return replay, True
            snapshot = self._sessions.snapshot(command.session_id)
            self._expect_version(snapshot.version, command.expected_session_version)
            if snapshot.state != "HANDOFF_READY":
                raise _workflow_error(
                    "FEEDBACK_REQUIRES_HANDOFF", 409, "Complete the activity handoff first."
                )
            values = self._sessions.workflow_record(command.session_id).values
            spec_value = values.get("experience_spec")
            if not isinstance(spec_value, dict):
                raise _workflow_error(
                    "EXPERIENCE_SPEC_MISSING", 409, "The approved activity identity is unavailable."
                )
            spec = ExperienceSpecV1.model_validate(spec_value)
            feedback_input = _require_mapping(command.payload.get("feedback"))
            allowed = {
                "completion_status",
                "interest_score",
                "independence_score",
                "observation_tags",
            }
            if set(feedback_input) - allowed:
                raise _workflow_error(
                    "FEEDBACK_FIELDS_NOT_ALLOWED",
                    422,
                    "Feedback cannot contain personal details or notes.",
                )
            try:
                feedback = FeedbackV1.model_validate(
                    {
                        **feedback_input,
                        "session_id": command.session_id,
                        "expected_session_version": command.expected_session_version,
                        "actor_ref": command.actor_ref,
                        "activity_ref": spec.activity_template.activity_ref.model_dump(
                            mode="python"
                        ),
                        "objective_ref": spec.learning_focus.objective_ref.model_dump(
                            mode="python"
                        ),
                        "template_ref": {
                            "id": spec.activity_template.template_id,
                            "version": spec.activity_template.template_version,
                        },
                        "spec_ref": {"id": spec.spec_id, "version": spec.spec_version},
                        "recorded_at": self._now(),
                    }
                )
            except ValidationError as exc:
                raise _workflow_error(
                    "FEEDBACK_INVALID", 422, "Feedback values are not valid."
                ) from exc
            updated = self._sessions.advance(
                session_id=command.session_id,
                expected_version=snapshot.version,
                allowed_states=("HANDOFF_READY",),
                next_state="FEEDBACK_RECORDED",
                workflow_updates={
                    "feedback": feedback.model_dump(mode="json"),
                    "journey": _append_journey(
                        values.get("journey"),
                        "FEEDBACK",
                        "COMPLETED",
                        artifact_refs=(spec.spec_id,),
                    ),
                },
            )
            result = _result(
                status="SUCCEEDED",
                command=command,
                observed_version=updated.version,
                payload={"feedback": feedback.model_dump(mode="json"), "durable": False},
            )
            self._remember(scope, command.idempotency_key, fingerprint, result)
            return result, False

    def read_gallery(
        self,
        *,
        session_id: str,
        request_id: str,
        expected_version: int,
        actor_ref: str,
    ) -> MobileWorkflowResultV1:
        if actor_ref != DEMO_ACTOR_REF:
            raise _workflow_error(
                "DEMO_ACTOR_INVALID", 422, "The local demo actor marker is invalid."
            )
        snapshot = self._sessions.snapshot(session_id)
        workflow = self._sessions.workflow_record(session_id)
        raw_entries = workflow.values.get("journey")
        entries = (
            tuple(
                SessionJourneyEntryV1.model_validate(item)
                for item in raw_entries
                if isinstance(item, dict)
            )
            if isinstance(raw_entries, (list, tuple))
            else ()
        )
        gallery = SessionGalleryV1(
            session_id=session_id,
            session_version=snapshot.version,
            status=snapshot.status,
            entries=entries,
        )
        return MobileWorkflowResultV1(
            status="SUCCEEDED",
            request_id=request_id,
            session_id=session_id,
            expected_session_version=expected_version,
            observed_session_version=snapshot.version,
            provenance=_FLOW_PROVENANCE,
            payload=gallery.model_dump(mode="json"),
        )

    def _validate_command(
        self,
        command: MobileWorkflowCommandV1,
        operation: str,
        required_keys: set[str],
    ) -> str:
        if command.actor_ref != DEMO_ACTOR_REF:
            raise _workflow_error(
                "DEMO_ACTOR_INVALID", 422, "The local demo actor marker is invalid."
            )
        if set(command.payload) != required_keys or command.payload.get("operation") != operation:
            raise _workflow_error(
                "WORKFLOW_COMMAND_INVALID",
                422,
                "This action requires an explicit, versioned user command.",
            )
        if command.payload.get("user_initiated") is not True:
            raise _workflow_error(
                "EXPLICIT_USER_ACTION_REQUIRED", 422, "Start this step from its on-screen action."
            )
        return sha256(
            json.dumps(
                command.model_dump(mode="json", exclude={"created_at"}),
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()

    def _expect_version(self, actual: int, expected: int) -> None:
        if actual != expected:
            raise _workflow_error(
                "STALE_SESSION_VERSION", 409, "Refresh the session before continuing."
            )

    def _replay(self, scope: str, key: str, fingerprint: str) -> MobileWorkflowResultV1 | None:
        receipt = self._idempotency.get(scope=scope, key=key)
        if receipt is None:
            return None
        if receipt.request_sha256 != fingerprint:
            raise _workflow_error(
                "IDEMPOTENCY_KEY_CONFLICT", 409, "This retry key was used for different input."
            )
        return MobileWorkflowResultV1.model_validate_json(receipt.response_body)

    def _remember(
        self, scope: str, key: str, fingerprint: str, result: MobileWorkflowResultV1
    ) -> None:
        self._idempotency.record(
            IdempotencyReceipt(
                scope=scope,
                key=key,
                request_sha256=fingerprint,
                response_body=result.model_dump_json().encode("utf-8"),
            )
        )


SelectableAnchorKind = Literal["subject", "action", "story"]


def _selectable_claims(
    raw: RawUnderstandingSuccessV1,
) -> dict[str, tuple[str, SelectableAnchorKind, float]]:
    return {
        claim.observation_id: (claim.label, claim.kind, claim.confidence)
        for claim in claims_from_raw(raw)
    }


def _learning_media_request(
    command: MobileWorkflowCommandV1, spec: ExperienceSpecV1, session_version: int
) -> LearningMediaRequestV1:
    activity = spec.activity_template.activity_ref
    objective = spec.learning_focus.objective_ref
    renderer_id = spec.spec_id
    identity = {
        "activity_id": activity.id,
        "activity_version": f"v{activity.version}",
        "objective_id": objective.id,
        "objective_version": f"v{objective.version}",
        "renderer_plan_id": renderer_id,
        "renderer_plan_version": "v1",
    }
    cache_key = sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return LearningMediaRequestV1(
        session_id=command.session_id,
        expected_session_version=command.expected_session_version,
        request_id=command.request_id,
        idempotency_key=command.idempotency_key,
        activity_id=activity.id,
        activity_version=f"v{activity.version}",
        objective_id=objective.id,
        objective_version=f"v{objective.version}",
        renderer_plan_id=renderer_id,
        renderer_plan_version="v1",
        source_session_version=session_version,
        cache_key=cache_key,
    )


def _validate_learning_media(value: dict[str, object]) -> LearningMediaResultV1:
    return LearningMediaResultV1.model_validate(value)


def _append_journey(
    current: object,
    stage: str,
    status: str,
    *,
    reason_codes: tuple[str, ...] = (),
    artifact_refs: tuple[str, ...] = (),
) -> list[object]:
    entries = list(current) if isinstance(current, (list, tuple)) else []
    entries.append(
        {
            "entry_id": f"journey-{uuid4()}",
            "stage": stage,
            "status": status,
            "occurred_at": datetime.now(UTC).isoformat(),
            "artifact_refs": list(artifact_refs),
            "reason_codes": list(reason_codes),
        }
    )
    return entries[-64:]


def _require_mapping(value: object) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise _workflow_error(
            "WORKFLOW_PAYLOAD_INVALID", 422, "The workflow action payload is invalid."
        )
    return value


def _workflow_error(code: str, status_code: int, message: str) -> SessionWorkflowError:
    return SessionWorkflowError(code=code, status_code=status_code, safe_message=message)


def _result(
    *,
    status: str,
    command: MobileWorkflowCommandV1,
    observed_version: int,
    payload: dict[str, object],
) -> MobileWorkflowResultV1:
    return MobileWorkflowResultV1(
        status=status,  # type: ignore[arg-type]
        request_id=command.request_id,
        session_id=command.session_id,
        expected_session_version=command.expected_session_version,
        observed_session_version=observed_version,
        provenance=_FLOW_PROVENANCE,
        payload=payload,
    )


__all__ = ["SupervisedFlowService"]
