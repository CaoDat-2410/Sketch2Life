"""Versioned contracts for the FEAT-020 backend-only workflow demo.

The workflow result is deliberately a sanitized manifest. Provider SDK objects, prompts,
credentials, raw model output and local absolute paths never cross this boundary.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from hashlib import sha256
from json import dumps
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

WorkflowStatus = Literal["SUCCEEDED", "FAILED"]
WorkflowTerminalStatus = Literal[
    "BACKEND_CONTEXT_READY",
    "RUNTIME_NOT_READY",
    "MEDIA_RECAPTURE",
    "ASR_FAILED",
    "AI_FAILED",
    "CONTENT_UNSAFE",
    "GATE_A_REQUIRED",
    "GATE_B_REQUIRED",
    "NO_ELIGIBLE_ACTIVITY",
    "ASSET_CATALOG_MISS",
    "STORY_PLAN_FAILED",
    "SCENE_PLAN_FAILED",
    "ART_OUTPUT_INVALID",
    "VIDEO_DEFERRED",
    "HANDOFF_INVALID",
]


class WorkflowStageV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    stage: str = Field(min_length=1, max_length=80)
    status: Literal["SUCCEEDED", "DEFERRED", "BLOCKED", "FAILED"]
    reason_code: str | None = Field(default=None, min_length=1, max_length=120)
    details: dict[str, Any] = Field(default_factory=dict)

    @field_validator("details")
    @classmethod
    def reject_sensitive_detail_keys(cls, value: dict[str, Any]) -> dict[str, Any]:
        forbidden = {"prompt", "raw_output", "token", "secret", "credential"}

        def walk(item: object) -> None:
            if isinstance(item, dict):
                if any(str(key).casefold() in forbidden for key in item):
                    raise ValueError("workflow stage details contain a forbidden sensitive key")
                for child in item.values():
                    walk(child)
            elif isinstance(item, (list, tuple)):
                for child in item:
                    walk(child)

        walk(value)
        return value


class DemoDecisionV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    gate: Literal["A", "B", "FEEDBACK"]
    actor: Literal["DEMO_OPERATOR"]
    mode: Literal["DEMO_AUTOPILOT"]
    decision: Literal["CONFIRMED", "APPROVED", "RECORDED"]
    reason: str = Field(min_length=1, max_length=240)
    decided_at: datetime

    @field_validator("decided_at")
    @classmethod
    def require_timezone_aware_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("demo decision timestamp must be timezone aware")
        return value


class PixiAssetSelectionV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    catalog_version: str = Field(min_length=1, max_length=40)
    catalog_status: Literal["GENERATED_PENDING_REVIEW", "APPROVED", "APPLIED"]
    asset_ids: tuple[str, ...]
    render_intents: tuple[str, ...] = ()
    runtime_generation: Literal[False] = False
    original_art_preserved: Literal[True] = True


class DeferredVideoV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["DEFERRED"] = "DEFERRED"
    reason: Literal["VIDEO_GENERATION_DEFERRED_FOR_FIRST_BACKEND_DEMO"] = (
        "VIDEO_GENERATION_DEFERRED_FOR_FIRST_BACKEND_DEMO"
    )
    target_duration_seconds: tuple[int, int] = (5, 10)
    generated_asset_ref: None = None


class FeedbackHistoryV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source: Literal["DEMO_AUTOPILOT"] = "DEMO_AUTOPILOT"
    feedback_status: Literal["NOT_ATTEMPTED", "COMPLETED", "PARTIALLY_COMPLETED"]
    observation_record_status: Literal["DEMO_GENERATED"] = "DEMO_GENERATED"
    history_update_status: Literal["DEMO_GENERATED"] = "DEMO_GENERATED"


class WorkflowBandResultV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    age_band: Literal["0-3", "3-6", "6-9", "9-12"]
    age_months: int = Field(ge=0, le=155)
    run_seed: int
    seed_fingerprint: str = Field(pattern=r"^[a-f0-9]{16}$")
    status: WorkflowStatus
    terminal_status: WorkflowTerminalStatus
    selection_vector: tuple[str, ...] = ()
    stages: tuple[WorkflowStageV1, ...] = Field(min_length=1)
    decisions: tuple[DemoDecisionV1, ...] = ()
    asr_summary: dict[str, Any] | None = None
    vision_summary: dict[str, Any] | None = None
    fusion_summary: dict[str, Any] | None = None
    anchor_set: dict[str, Any] | None = None
    experience_spec: dict[str, Any] | None = None
    activity_handoff: dict[str, Any] | None = None
    story_scene: dict[str, Any] | None = None
    art_render_intent: PixiAssetSelectionV1 | None = None
    video: DeferredVideoV1 | None = None
    feedback_history: FeedbackHistoryV1 | None = None
    warnings: tuple[str, ...] = ()


class BackendWorkflowResultV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_name: Literal["BackendWorkflowResultV1"] = "BackendWorkflowResultV1"
    contract_version: Literal["1.0"] = "1.0"
    workflow_run_id: str = Field(min_length=1, max_length=120)
    status: WorkflowStatus
    terminal_status: WorkflowTerminalStatus
    input_mode: Literal["MULTIMODAL"] = "MULTIMODAL"
    image_artifact_ref: str = Field(min_length=1, max_length=500)
    image_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    audio_artifact_ref: str = Field(min_length=1, max_length=500)
    audio_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    run_seed: int
    age_bands: tuple[WorkflowBandResultV1, ...] = Field(min_length=1)
    stages: tuple[WorkflowStageV1, ...] = Field(min_length=1)
    warnings: tuple[str, ...] = ()
    created_at: datetime
    manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @field_validator("created_at")
    @classmethod
    def require_timezone_aware_created_at(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("workflow created_at must be timezone aware")
        return value

    @model_validator(mode="after")
    def validate_manifest_hash(self) -> BackendWorkflowResultV1:
        payload = self.model_dump(mode="json")
        recorded = payload.pop("manifest_sha256")
        expected = _canonical_hash(payload)
        if recorded != expected:
            raise ValueError("manifest_sha256 does not match the sanitized workflow manifest")
        return self


def _canonical_hash(value: object) -> str:
    encoded = dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=_json_default,
    ).encode()
    return sha256(encoded).hexdigest()


def _json_default(value: object) -> object:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    raise TypeError(f"unsupported manifest value: {type(value).__name__}")


def finalize_workflow_result(payload: dict[str, Any]) -> BackendWorkflowResultV1:
    """Create a result after computing its content hash over every other field."""

    unsigned = dict(payload)
    unsigned.pop("manifest_sha256", None)
    normalized = dict(unsigned)
    normalized["age_bands"] = tuple(
        band
        if isinstance(band, WorkflowBandResultV1)
        else WorkflowBandResultV1.model_validate(band)
        for band in unsigned["age_bands"]
    )
    normalized["stages"] = tuple(
        stage if isinstance(stage, WorkflowStageV1) else WorkflowStageV1.model_validate(stage)
        for stage in unsigned["stages"]
    )
    normalized = BackendWorkflowResultV1.model_construct(
        **normalized,
        manifest_sha256="0" * 64,
    ).model_dump(mode="json")
    normalized.pop("manifest_sha256", None)
    digest = _canonical_hash(normalized)
    return BackendWorkflowResultV1.model_validate({**normalized, "manifest_sha256": digest})


__all__ = [
    "BackendWorkflowResultV1",
    "DemoDecisionV1",
    "DeferredVideoV1",
    "FeedbackHistoryV1",
    "PixiAssetSelectionV1",
    "WorkflowBandResultV1",
    "WorkflowStageV1",
    "finalize_workflow_result",
]
