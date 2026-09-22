"""Offline P2-T5 fixture evaluator composed from the existing T1-T4 public boundaries."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from sketch2life.application.services.media_validation import (
    MediaValidationRequest,
)
from sketch2life.application.services.p2_t4_fusion import validate_and_fuse
from sketch2life.application.services.p2_t5_scoring import score_asr
from sketch2life.contracts.schemas.asr import (
    AsrAudioReferenceV1,
    AsrProfileId,
    AsrRequestV1,
    AsrSuccessV1,
    MediaValidationProvenanceV1,
)
from sketch2life.contracts.schemas.p2_t4_fusion import (
    P2T4FusedResultV1,
    P2T4FusionInputRejectionV2,
    P2T4FusionPolicyConfigV1,
    fusion_policy_config_hash,
)
from sketch2life.contracts.schemas.p2_t4_fusion import (
    canonical_sha256 as t4_canonical_sha256,
)
from sketch2life.contracts.schemas.p2_t5_evaluation import (
    P2T5_POLICY_HASH,
    CaseRunStatus,
    P2T5CommandEnvelopeV1,
    P2T5EvaluationReportV1,
    P2T5FixtureCaseResultV1,
    P2T5FixtureManifestEntryV1,
    P2T5FixtureManifestV1,
    P2T5MeasurementV1,
    P2T5RunRecordV1,
    P2T5StageStateV1,
    Split,
    StageExecutionState,
    canonical_sha256,
    format_utc,
    report_model,
)
from sketch2life.contracts.schemas.vision import (
    VisionImageReferenceV1,
    VisionMediaValidationProvenanceV1,
    VisionProfileId,
    VisionUnderstandingRequestV1,
    VisionUnderstandingSuccessV1,
)
from sketch2life.domain.understanding.media_quality import MediaDecision

_EXECUTED_AT = datetime(2026, 9, 20, 12, 0, 0, tzinfo=UTC)


def _stage(
    state: StageExecutionState,
    *,
    identity: str | None = None,
    status: str | None = None,
    **fields: str | None,
) -> P2T5StageStateV1:
    return P2T5StageStateV1(state=state, identity=identity, status=status, **fields)


def _vision_payload(shape: str) -> str:
    def text(value: str) -> dict[str, Any]:
        return {"value": value, "language": {"status": "DECLARED", "tags": ["en"]}}

    entity = {"observation_id": "entity-1", "label": text("tree"), "confidence": 0.9}
    action = {
        "observation_id": "action-1",
        "label": text("holds"),
        "actor_ref": "entity-1",
        "object_ref": None,
        "confidence": 0.9,
    }
    relation = {
        "observation_id": "relation-1",
        "predicate": text("near"),
        "subject_ref": "entity-1",
        "object_ref": "entity-2",
        "confidence": 0.9,
    }
    theme = {
        "observation_id": "theme-1",
        "label": text("nature"),
        "evidence_refs": ["entity-1"],
        "confidence": 0.9,
    }
    entity_two = {"observation_id": "entity-2", "label": text("house"), "confidence": 0.9}
    if shape == "EMPTY_SUCCESS":
        payload: dict[str, Any] = {
            "entities": [],
            "actions": [],
            "relations": [],
            "themes": [],
            "ambiguous_regions": [],
        }
    elif shape in {"ENTITIES_ONLY", "VISION_ONLY_OBSERVATIONS"}:
        payload = {
            "entities": [entity],
            "actions": [],
            "relations": [],
            "themes": [],
            "ambiguous_regions": [],
        }
    elif shape in {"ALL_COLLECTIONS", "ALL_SCORED_COLLECTIONS"}:
        payload = {
            "entities": [entity, entity_two],
            "actions": [action],
            "relations": [relation],
            "themes": [theme],
            "ambiguous_regions": [],
        }
    else:
        payload = {
            "entities": [entity],
            "actions": [],
            "relations": [],
            "themes": [],
            "ambiguous_regions": [],
        }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


class P2T5EvaluationHarness:
    """Deterministic fixture-only harness; no provider or model import is performed."""

    def __init__(
        self,
        repository_root: Path,
        *,
        validator: Any,
        loader: Callable[[Path, str, str], Any],
        asr_factory: Callable[[str, str], Any],
        vision_factory: Callable[[str, str, Path, str], Any],
        vision_policy: Any,
    ) -> None:
        self.repository_root = repository_root.resolve()
        self._validator = validator
        self._loader = loader
        self._asr_factory = asr_factory
        self._vision_factory = vision_factory
        self._policy = P2T4FusionPolicyConfigV1(
            config_version="p2-t4-fusion-policy-fixture-v1",
            confidence_floor=0.5,
            corroboration_increment="0.10",
        )
        if fusion_policy_config_hash(self._policy) != P2T5_POLICY_HASH:
            raise RuntimeError("T4_POLICY_INTEGRITY_FAILURE")
        self._vision_policy = vision_policy

    def load(self, manifest: str, fixture_root: str) -> Any:
        return self._loader(self.repository_root, manifest, fixture_root)

    def validate(self, manifest: str, fixture_root: str) -> P2T5CommandEnvelopeV1:
        package = self.load(manifest, fixture_root)
        payload = {
            "contract_name": "P2T5ValidationSummaryV1",
            "contract_version": "1.0",
            "manifest_id": package.manifest.manifest_id,
            "entry_count": len(package.cases),
            "development_count": len(package.selected("DEVELOPMENT")),
            "held_out_count": len(package.selected("HELD_OUT")),
        }
        return P2T5CommandEnvelopeV1(command="validate", success=True, payload=payload)

    def evaluate(
        self,
        manifest: str,
        fixture_root: str,
        split: Split,
        run_id: str,
        executed_at: datetime,
    ) -> P2T5EvaluationReportV1:
        package = self.load(manifest, fixture_root)
        if executed_at.tzinfo is None or executed_at.utcoffset() is None:
            raise ValueError("INVALID_ARGUMENT")
        selected = package.selected(split.value)
        if not selected:
            raise ValueError("INVALID_ARGUMENT")
        run = P2T5RunRecordV1(
            run_id=run_id,
            manifest_id=package.manifest.manifest_id,
            manifest_version=package.manifest.manifest_version,
            manifest_sha256=package.manifest_sha256,
            oracle_sha256=package.oracle_sha256,
            fixture_split=split,
            executed_at=format_utc(executed_at),
        )
        results: list[P2T5FixtureCaseResultV1] = []
        failure_counts: dict[str, int] = {}
        measurements: list[P2T5MeasurementV1] = []
        for case in selected:
            result = self._evaluate_case(package, case, run)
            results.append(result)
            for code in result.typed_failure_codes:
                failure_counts[code] = failure_counts.get(code, 0) + 1
            measurements.extend(result.measurements)
        return report_model(
            run=run,
            manifest=package.manifest,
            cases=tuple(results),
            measurements=tuple(measurements),
            typed_failure_summary=failure_counts,
        )

    def _evaluate_case(
        self, package: Any, case: Any, run: P2T5RunRecordV1
    ) -> P2T5FixtureCaseResultV1:
        entry = next(
            item for item in package.manifest.entries if item.fixture_id == case.fixture_id
        )
        correlation = _correlation(package.manifest, entry)
        t1 = self._validator.validate(
            MediaValidationRequest(
                image_path=case.image_path,
                audio_path=case.audio_path,
                image_artifact_ref=entry.image_ref,
                audio_artifact_ref=entry.audio_ref,
            )
        )
        source_hashes = (entry.image_sha256, entry.audio_sha256)
        if t1.decision is not MediaDecision.PASS:
            return P2T5FixtureCaseResultV1(
                fixture_id=case.fixture_id,
                split=entry.split,
                case_status=CaseRunStatus.EXPECTED_TERMINAL,
                correlation_id=correlation,
                t1=_stage(
                    StageExecutionState.EXECUTED,
                    identity="MediaValidationResultV1@1.0",
                    status=t1.decision.value,
                ),
                asr=_stage(StageExecutionState.NOT_EXECUTED),
                vision=_stage(StageExecutionState.NOT_EXECUTED),
                fusion=_stage(StageExecutionState.NOT_EXECUTED),
                source_media_sha256=source_hashes,
                t1_result_sha256=canonical_sha256(t1.model_dump(mode="json")),
            )
        validation_sha = canonical_sha256(t1.model_dump(mode="json"))
        asr_request = AsrRequestV1(
            correlation_id=correlation,
            source_audio_ref=AsrAudioReferenceV1(
                artifact_ref=entry.audio_ref,
                sha256=entry.audio_sha256,
            ),
            media_validation=MediaValidationProvenanceV1(
                validation_artifact_ref=f"p2t5:{case.fixture_id}:t1",
                validation_artifact_sha256=validation_sha,
                decision="PASS",
                validator_policy_version=t1.validator_policy_version,
            ),
            requested_profile_id=AsrProfileId.FAKE_DETERMINISTIC_V1,
        )
        asr = self._asr_factory(entry.audio_ref, entry.asr_scenario).transcribe(asr_request)
        vision_request = VisionUnderstandingRequestV1(
            correlation_id=correlation,
            source_image_ref=VisionImageReferenceV1(
                artifact_ref=entry.image_ref,
                sha256=entry.image_sha256,
            ),
            media_validation=VisionMediaValidationProvenanceV1(
                validation_artifact_ref=f"p2t5:{case.fixture_id}:t1",
                validation_artifact_sha256=validation_sha,
                decision="PASS",
                validator_policy_version=t1.validator_policy_version,
            ),
            requested_profile_id=VisionProfileId.FAKE_DETERMINISTIC_V1,
        )
        vision = self._vision_factory(
            entry.image_ref,
            entry.vision_scenario,
            case.image_path,
            _vision_payload(str(case.descriptor.get("vision_shape", "ORDINARY_SUCCESS")))
            if entry.vision_scenario == "RAW_OUTPUT"
            else "{}",
        ).understand(vision_request)
        t4_asr: object = asr
        t4_vision: object = vision
        if entry.t4_input_mutation == "WRONG_FAMILY_ASR" and isinstance(asr, BaseModel):
            t4_asr = asr.model_dump(mode="json")
            t4_asr["contract_name"] = "FEAT018.LiveAsrResultV1"
        elif entry.t4_input_mutation == "DUPLICATE_ASR_SEGMENT_INDEX" and isinstance(
            asr, AsrSuccessV1
        ):
            if asr.segments:
                t4_asr = asr.model_copy(update={"segments": (asr.segments[0], asr.segments[0])})
        elif entry.t4_input_mutation == "NONCANONICAL_VISION_MATCH_VIEW" and isinstance(
            vision, VisionUnderstandingSuccessV1
        ):
            t4_vision = vision.model_copy(
                update={"policy_match_view_version": "vision_policy_match_view-v2"}
            )
        elif entry.t4_input_mutation == "CORRELATION_MISMATCH":
            if isinstance(asr, BaseModel):
                t4_asr = asr.model_copy(update={"correlation_id": "p2t5-correlation-mismatch"})
        outcome = validate_and_fuse(
            t4_asr, t4_vision, self._policy, executed_at=_parse_utc(run.executed_at)
        )
        asr_state = _result_stage(asr, "P2.AsrResultV1@1.0")
        vision_state = _result_stage(vision, "P2.VisionUnderstandingResultV1@1.0")
        typed_codes = tuple(
            code
            for code in (
                getattr(asr, "error_code", None),
                getattr(vision, "error_code", None),
            )
            if code is not None
        )
        if isinstance(outcome, P2T4FusionInputRejectionV2):
            fusion_state = _stage(
                StageExecutionState.EXECUTED,
                identity="P2T4.P2T4FusionInputRejectionV2@2.0",
                status="REJECTED",
                rejection_phase=outcome.phase.value,
                rejection_code=outcome.code.value,
                field_code=outcome.field_code.value,
            )
            status = CaseRunStatus.EXPECTED_TERMINAL
            rejection_hash = t4_canonical_sha256(outcome)
            result_hash = None
        else:
            assert isinstance(outcome, P2T4FusedResultV1)
            fusion_state = _stage(
                StageExecutionState.EXECUTED,
                identity="P2T4.P2T4FusedResultV1@1.0",
                status=outcome.status.value,
                result_sha256=t4_canonical_sha256(outcome),
            )
            result_hash = t4_canonical_sha256(outcome)
            rejection_hash = None
            status = (
                CaseRunStatus.COMPLETED_WITH_TYPED_FAILURES
                if outcome.status.value == "UPSTREAM_FAILURE"
                else CaseRunStatus.COMPLETED
            )
        asr_hash = (
            canonical_sha256(asr.model_dump(mode="json")) if isinstance(asr, BaseModel) else None
        )
        vision_hash = (
            canonical_sha256(vision.model_dump(mode="json"))
            if isinstance(vision, BaseModel)
            else None
        )
        measurements = score_asr(None, None)
        return P2T5FixtureCaseResultV1(
            fixture_id=case.fixture_id,
            split=entry.split,
            case_status=status,
            correlation_id=correlation,
            t1=_stage(
                StageExecutionState.EXECUTED, identity="MediaValidationResultV1@1.0", status="PASS"
            ),
            asr=asr_state,
            vision=vision_state,
            fusion=fusion_state,
            source_media_sha256=source_hashes,
            t1_result_sha256=validation_sha,
            asr_result_sha256=asr_hash,
            vision_result_sha256=vision_hash,
            t4_result_sha256=result_hash,
            t4_rejection_sha256=rejection_hash,
            measurements=measurements,
            typed_failure_codes=tuple(str(code) for code in typed_codes),
        )


def _correlation(manifest: P2T5FixtureManifestV1, entry: P2T5FixtureManifestEntryV1) -> str:
    from sketch2life.contracts.schemas.p2_t5_evaluation import correlation_id

    return correlation_id(
        manifest_id=manifest.manifest_id,
        manifest_version=manifest.manifest_version,
        fixture_id=entry.fixture_id,
        split=entry.split,
    )


def _parse_utc(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=UTC)


def _result_stage(result: object, identity: str) -> P2T5StageStateV1:
    if isinstance(result, BaseModel):
        status = getattr(result, "status", None)
        code = getattr(result, "error_code", None)
        digest = canonical_sha256(result.model_dump(mode="json"))
        return P2T5StageStateV1(
            state=StageExecutionState.EXECUTED,
            identity=identity,
            status=str(status) if status is not None else None,
            error_code=str(code) if code is not None else None,
            result_sha256=digest,
        )
    return P2T5StageStateV1(state=StageExecutionState.FAILED)


def atomic_write_json(path: Path, value: BaseModel | dict[str, Any]) -> None:
    """Write a validated command result without leaving a partial output."""

    path.parent.mkdir(parents=True, exist_ok=True)
    payload = value.model_dump(mode="json") if isinstance(value, BaseModel) else value
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_bytes(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    )
    temporary.replace(path)
