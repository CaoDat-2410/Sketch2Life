from __future__ import annotations

import dataclasses
import json
import shutil
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from sketch2life.benchmark import vision_v3_quality_benchmark as quality_benchmark
from sketch2life.benchmark.vision_b3_mapping_study import (
    B3RawOutputCollector,
    B3RawOutputMode,
)
from sketch2life.benchmark.vision_c1_prompt_mapping_study import C1_PROMPT_V3
from sketch2life.benchmark.vision_v3_quality_benchmark import (
    V3QualityAcceptanceThresholds,
    V3QualityBlockingReason,
    V3QualityCollectionScore,
    V3QualityCollectionThreshold,
    V3QualityDecisionRequiredError,
    V3QualityExecutionDecisions,
    V3QualityFixtureIntegrityError,
    V3QualityLocalFakeAdapterFactory,
    V3QualityLocalOnlyBoundaryError,
    V3QualityRawOutputHookNotWiredError,
    V3QualityRawOutputMode,
    V3QualityRepeatGate,
    evaluate_v3_quality_pair,
    load_and_verify_v3_quality_fixture_package,
    quality_pass_report_to_dict,
    run_v3_quality_pass,
    score_v3_quality_success,
)
from sketch2life.contracts.schemas.vision import (
    ActionCandidateV1,
    AmbiguousRegionCandidateV1,
    EntityCandidateV1,
    ObservedTextV1,
    RelationCandidateV1,
    TextLanguageDeclarationV1,
    ThemeCandidateV1,
    VisionErrorCode,
    VisionImageReferenceV1,
    VisionMediaValidationProvenanceV1,
)
from sketch2life.contracts.schemas.vision_v2 import (
    VisionNonPolicyErrorDetailV2,
    VisionUnderstandingFailureV2,
    VisionUnderstandingRequestV2,
    VisionUnderstandingResultV2,
    VisionUnderstandingSuccessV2,
    vision_profile_catalog_hash_v2,
    vision_profile_catalog_v2,
    vision_profile_config_hash_v2,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_FIXTURE_SOURCE = (
    _REPO_ROOT / "features/FEAT-003-multimodal-understanding/fixtures/vision-v3-quality"
)
_EXECUTED_AT = datetime(2026, 9, 9, 12, 0, tzinfo=UTC)


def _text(value: str) -> ObservedTextV1:
    return ObservedTextV1(
        value=value,
        language=TextLanguageDeclarationV1(status="NOT_DETERMINED"),
    )


def _entity(identifier: str, label: str) -> EntityCandidateV1:
    return EntityCandidateV1(observation_id=identifier, label=_text(label), confidence=None)


def _action(
    identifier: str, label: str, actor_ref: str | None, object_ref: str | None
) -> ActionCandidateV1:
    return ActionCandidateV1(
        observation_id=identifier,
        label=_text(label),
        actor_ref=actor_ref,
        object_ref=object_ref,
        confidence=None,
    )


def _relation(
    identifier: str, predicate: str, subject_ref: str, object_ref: str
) -> RelationCandidateV1:
    return RelationCandidateV1(
        observation_id=identifier,
        predicate=_text(predicate),
        subject_ref=subject_ref,
        object_ref=object_ref,
        confidence=None,
    )


def _theme(identifier: str, label: str, evidence_refs: list[str]) -> ThemeCandidateV1:
    return ThemeCandidateV1(
        observation_id=identifier,
        label=_text(label),
        evidence_refs=evidence_refs,
        confidence=None,
    )


def _ambiguous(identifier: str, note: str) -> AmbiguousRegionCandidateV1:
    return AmbiguousRegionCandidateV1(observation_id=identifier, note=_text(note))


def _success(
    request: VisionUnderstandingRequestV2,
    **overrides: Any,
) -> VisionUnderstandingSuccessV2:
    profile = vision_profile_catalog_v2().profiles[0]
    values: dict[str, Any] = {
        "correlation_id": request.correlation_id,
        "executed_at": _EXECUTED_AT,
        "source_image_ref": request.source_image_ref,
        "profile_id": profile.profile_id,
        "profile_catalog_hash": vision_profile_catalog_hash_v2(vision_profile_catalog_v2()),
        "attempt_number": 1,
        "repair_attempted": False,
        "content_policy_version": "vision-prohibited-lexicon-fixture-v1",
        "policy_match_view_version": "vision-policy-match-view-v2",
        "policy_execution_state": "PASSED",
        "entities": (),
        "actions": (),
        "relations": (),
        "themes": (),
        "ambiguous_regions": (),
        "adapter_version": profile.adapter_version,
        "config_hash": vision_profile_config_hash_v2(profile),
        "model_provenance": profile.model_provenance,
    }
    values.update(overrides)
    return VisionUnderstandingSuccessV2(**values)


def _validation(
    _fixture_id: str, _image_path: Path, _audio_path: Path
) -> VisionMediaValidationProvenanceV1:
    return VisionMediaValidationProvenanceV1(
        validation_artifact_ref="test-p2t1",
        validation_artifact_sha256="b" * 64,
        decision="PASS",
        validator_policy_version="test-policy",
    )


def _request(correlation_id: str = "test-request") -> VisionUnderstandingRequestV2:
    return VisionUnderstandingRequestV2(
        correlation_id=correlation_id,
        source_image_ref=VisionImageReferenceV1(artifact_ref="test-image", sha256="a" * 64),
        requested_profile_id=vision_profile_catalog_v2().profiles[0].profile_id,
    )


def _mapping_failure(request: VisionUnderstandingRequestV2) -> VisionUnderstandingFailureV2:
    profile = vision_profile_catalog_v2().profiles[0]
    return VisionUnderstandingFailureV2(
        correlation_id=request.correlation_id,
        executed_at=_EXECUTED_AT,
        source_image_ref=request.source_image_ref,
        profile_id=profile.profile_id,
        profile_catalog_hash=vision_profile_catalog_hash_v2(vision_profile_catalog_v2()),
        attempt_number=1,
        repair_attempted=False,
        content_policy_version="vision-prohibited-lexicon-fixture-v1",
        policy_match_view_version="vision-policy-match-view-v2",
        policy_execution_state="NOT_EXECUTED",
        error_code=VisionErrorCode.VISION_SCHEMA_INVALID,
        error_detail=VisionNonPolicyErrorDetailV2.OUTPUT_MAPPING_FAILED,
        retryable=False,
        model_provenance=profile.model_provenance,
    )


def _static_outcomes(success_count: int = 8) -> tuple[VisionUnderstandingResultV2, ...]:
    return tuple(
        (
            _success(_request(f"success-{index}"))
            if index < success_count
            else _mapping_failure(_request(f"failure-{index}"))
        )
        for index in range(8)
    )


class _ModelLikeFactory:
    def __init__(self) -> None:
        self.calls = 0

    def __call__(self, _prompt: str, _hook: Callable[[str], None]) -> object:
        self.calls += 1
        raise AssertionError("model-like factory must never be invoked")


def _copy_fixture_package(tmp_path: Path, *, owner_approved: bool) -> Path:
    root = tmp_path / "vision-v3-quality"
    shutil.copytree(_FIXTURE_SOURCE, root)
    if owner_approved:
        manifest_path = root / "manifest-v1.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["status"] = "OWNER_REVIEW_APPROVED"
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return root


def _decisions(*, ambiguous_maximum: float | None = None) -> V3QualityExecutionDecisions:
    thresholds = V3QualityAcceptanceThresholds(
        collections=(
            V3QualityCollectionThreshold("entities", 0.0, None, None),
            V3QualityCollectionThreshold("actions", 0.0, None, None),
            V3QualityCollectionThreshold("relations", 0.0, None, None),
            V3QualityCollectionThreshold("themes", 0.0, None, None),
            V3QualityCollectionThreshold(
                "ambiguous_regions",
                None,
                None,
                1.0 if ambiguous_maximum is not None else 0.0,
                maximum_count_rate=ambiguous_maximum,
            ),
        )
    )
    gate = V3QualityRepeatGate(
        expected_attempted_runs=8,
        expected_run_records=8,
        minimum_schema_valid_runs=8,
        systemic_truncation_threshold=2,
        repeat_window=timedelta(minutes=15),
        require_same_session=True,
        block_on_input_integrity_failure=True,
        block_on_runtime_or_device_failure=True,
    )
    return V3QualityExecutionDecisions(
        d5_acceptance_thresholds=thresholds,
        d6_repeat_gate=gate,
        d7_raw_output_mode=V3QualityRawOutputMode.CLASSIFY_ONLY,
    )


def _clock_pair(start: datetime) -> Callable[[], datetime]:
    values = [start, start + timedelta(seconds=1)]

    def clock() -> datetime:
        return values.pop(0)

    return clock


def _run_fake_pass(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    run_label: Any = "V3_QUALITY_PASS_1",
    start: datetime = _EXECUTED_AT,
    emit_raw_output: bool = True,
    success_count: int = 8,
) -> tuple[Any, V3QualityLocalFakeAdapterFactory, Path]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    monkeypatch.chdir(tmp_path)
    root = _copy_fixture_package(tmp_path, owner_approved=True)
    factory = V3QualityLocalFakeAdapterFactory(
        _static_outcomes(success_count),
        emit_raw_output=emit_raw_output,
    )
    collector = B3RawOutputCollector(mode=B3RawOutputMode.CLASSIFY_ONLY)
    report = run_v3_quality_pass(
        factory,
        collector,
        run_label=run_label,
        decisions=_decisions(),
        fixture_root=root,
        runtime_dir=Path("scratch"),
        sample_vram=False,
        validate_media=_validation,
        clock=_clock_pair(start),
    )
    return report, factory, root


def test_loader_remains_closed_until_owner_approval(tmp_path: Path) -> None:
    root = _copy_fixture_package(tmp_path, owner_approved=False)

    with pytest.raises(V3QualityFixtureIntegrityError, match="owner-approved"):
        load_and_verify_v3_quality_fixture_package(root)


def test_unresolved_decisions_block_before_package_or_factory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)

    with pytest.raises(V3QualityDecisionRequiredError, match="D-5, D-6, D-7"):
        run_v3_quality_pass(
            object(),
            B3RawOutputCollector(),
            run_label="V3_QUALITY_PASS_1",
            decisions=V3QualityExecutionDecisions(),
            fixture_root=tmp_path / "missing-package",
            runtime_dir=Path("scratch"),
        )


@pytest.mark.parametrize(
    ("decision_mode", "collector_mode"),
    [
        (V3QualityRawOutputMode.EPHEMERAL_CAPTURE, B3RawOutputMode.CLASSIFY_ONLY),
        (V3QualityRawOutputMode.CLASSIFY_ONLY, B3RawOutputMode.EPHEMERAL_CAPTURE),
        (V3QualityRawOutputMode.EPHEMERAL_CAPTURE, B3RawOutputMode.EPHEMERAL_CAPTURE),
    ],
)
def test_phase8_ephemeral_capture_is_rejected_before_any_side_effect(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    decision_mode: V3QualityRawOutputMode,
    collector_mode: B3RawOutputMode,
) -> None:
    monkeypatch.chdir(tmp_path)

    def package_must_not_load(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("invalid Phase 8 D-7 reached package loading")

    def scratch_must_not_resolve(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("invalid Phase 8 D-7 reached scratch creation")

    monkeypatch.setattr(
        quality_benchmark,
        "load_and_verify_v3_quality_fixture_package",
        package_must_not_load,
    )
    monkeypatch.setattr(
        quality_benchmark,
        "_require_safe_scratch_target",
        scratch_must_not_resolve,
    )

    factory = V3QualityLocalFakeAdapterFactory(_static_outcomes(), emit_raw_output=True)
    capture_dir = Path("raw-capture")
    collector = B3RawOutputCollector(mode=collector_mode, capture_dir=capture_dir)
    decisions = dataclasses.replace(_decisions(), d7_raw_output_mode=decision_mode)

    with pytest.raises(V3QualityDecisionRequiredError, match="CLASSIFY_ONLY"):
        run_v3_quality_pass(
            factory,
            collector,
            run_label="V3_QUALITY_PASS_1",
            decisions=decisions,
            fixture_root=Path("missing-package"),
            runtime_dir=Path("scratch"),
            validate_media=_validation,
        )

    assert factory.calls == 0
    assert not (tmp_path / "scratch").exists()
    assert not (tmp_path / capture_dir).exists()


def test_local_only_boundary_rejects_model_like_factory_before_invocation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    model_like_factory = _ModelLikeFactory()

    with pytest.raises(V3QualityLocalOnlyBoundaryError, match="local preparation accepts only"):
        run_v3_quality_pass(
            model_like_factory,  # type: ignore[arg-type]
            B3RawOutputCollector(),
            run_label="V3_QUALITY_PASS_1",
            decisions=_decisions(),
            fixture_root=_copy_fixture_package(tmp_path, owner_approved=True),
            runtime_dir=Path("scratch"),
            validate_media=_validation,
        )

    assert model_like_factory.calls == 0
    assert not (tmp_path / "scratch").exists()


def test_local_only_runner_rejects_gpu_sampling(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    factory = V3QualityLocalFakeAdapterFactory(_static_outcomes())

    with pytest.raises(V3QualityLocalOnlyBoundaryError, match="cannot sample GPU"):
        run_v3_quality_pass(
            factory,
            B3RawOutputCollector(),
            run_label="V3_QUALITY_PASS_1",
            decisions=_decisions(),
            fixture_root=_copy_fixture_package(tmp_path, owner_approved=True),
            runtime_dir=Path("scratch"),
            sample_vram=True,
            validate_media=_validation,
        )

    assert factory.calls == 0
    assert not (tmp_path / "scratch").exists()


def test_schema_failures_cannot_produce_quality_ready(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pass_report, _, pass_root = _run_fake_pass(
        tmp_path / "pass", monkeypatch, success_count=1
    )
    repeat_report, _, _ = _run_fake_pass(
        tmp_path / "repeat",
        monkeypatch,
        run_label="V3_QUALITY_REPEAT_1",
        start=_EXECUTED_AT + timedelta(minutes=2),
        success_count=1,
    )

    verdict = evaluate_v3_quality_pair(
        pass_report,
        repeat_report,
        decisions=_decisions(),
        same_lightning_session=True,
        fixture_root=pass_root,
    )

    assert verdict.overall == "QUALITY_NOT_READY"
    assert V3QualityBlockingReason.SCHEMA_VALIDITY_REQUIREMENT_NOT_MET in verdict.blocking_reasons
    assert verdict.pass_1.schema_valid_count == 1
    assert verdict.repeat_1.schema_valid_count == 1

    forged_summary_verdict = evaluate_v3_quality_pair(
        dataclasses.replace(pass_report, schema_valid_count=8),
        dataclasses.replace(repeat_report, schema_valid_count=8),
        decisions=_decisions(),
        same_lightning_session=True,
        fixture_root=pass_root,
    )
    assert forged_summary_verdict.overall == "QUALITY_NOT_READY"


def test_forged_equal_experiment_identity_cannot_produce_quality_ready(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pass_report, _, pass_root = _run_fake_pass(tmp_path / "pass", monkeypatch)
    repeat_report, _, _ = _run_fake_pass(
        tmp_path / "repeat",
        monkeypatch,
        run_label="V3_QUALITY_REPEAT_1",
        start=_EXECUTED_AT + timedelta(minutes=2),
    )
    forged_values = {
        "manifest_version": "forged-manifest",
        "ground_truth_sha256": "a" * 64,
        "matching_rule_id": "forged-matching-rule",
        "matching_rule_sha256": "b" * 64,
        "prompt_protocol_id": "forged-prompt",
        "prompt_sha256": "e" * 64,
        "profile_id": "FORGED_PROFILE",
        "profile_catalog_hash": "c" * 64,
    }

    verdict = evaluate_v3_quality_pair(
        dataclasses.replace(pass_report, **forged_values),
        dataclasses.replace(repeat_report, **forged_values),
        decisions=_decisions(),
        same_lightning_session=True,
        fixture_root=pass_root,
    )

    assert verdict.overall == "NON_COMPARABLE"
    assert V3QualityBlockingReason.CONFIG_DRIFT in verdict.blocking_reasons
    assert V3QualityBlockingReason.FIXTURE_PACKAGE_MISMATCH in verdict.blocking_reasons


@pytest.mark.parametrize("mutation", ["reordered", "wrong_hash"])
def test_wrong_or_reordered_fixture_identity_cannot_produce_quality_ready(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    pass_report, _, pass_root = _run_fake_pass(tmp_path / "pass", monkeypatch)
    repeat_report, _, _ = _run_fake_pass(
        tmp_path / "repeat",
        monkeypatch,
        run_label="V3_QUALITY_REPEAT_1",
        start=_EXECUTED_AT + timedelta(minutes=2),
    )
    if mutation == "reordered":
        forged_pass = dataclasses.replace(pass_report, runs=tuple(reversed(pass_report.runs)))
    else:
        forged_runs = list(pass_report.runs)
        forged_runs[0] = dataclasses.replace(forged_runs[0], fixture_sha256="d" * 64)
        forged_pass = dataclasses.replace(pass_report, runs=tuple(forged_runs))

    verdict = evaluate_v3_quality_pair(
        forged_pass,
        repeat_report,
        decisions=_decisions(),
        same_lightning_session=True,
        fixture_root=pass_root,
    )

    assert verdict.overall == "NON_COMPARABLE"
    assert V3QualityBlockingReason.FIXTURE_PACKAGE_MISMATCH in verdict.blocking_reasons


def test_ambiguous_overprediction_fails_explicit_upper_bound(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pass_report, _, pass_root = _run_fake_pass(tmp_path / "pass", monkeypatch)
    repeat_report, _, _ = _run_fake_pass(
        tmp_path / "repeat",
        monkeypatch,
        run_label="V3_QUALITY_REPEAT_1",
        start=_EXECUTED_AT + timedelta(minutes=2),
    )

    def overpredicted(report: Any) -> Any:
        scores = dict(report.aggregate_collection_scores)
        scores["ambiguous_regions"] = V3QualityCollectionScore(
            ground_truth_count=1,
            predicted_count=10,
            matched_count=1,
            coverage=1.0,
            accuracy=None,
            count_rate=10.0,
        )
        return dataclasses.replace(report, aggregate_collection_scores=scores)

    verdict = evaluate_v3_quality_pair(
        overpredicted(pass_report),
        overpredicted(repeat_report),
        decisions=_decisions(ambiguous_maximum=1.0),
        same_lightning_session=True,
        fixture_root=pass_root,
    )

    assert verdict.overall == "QUALITY_NOT_READY"
    assert V3QualityBlockingReason.QUALITY_BELOW_THRESHOLD in verdict.blocking_reasons


def test_quality_matching_scores_endpoints_and_case_hyphen_normalization() -> None:
    ground_truth = {
        "entities": [
            {"ground_truth_id": "gt-e1", "label": "circle"},
            {"ground_truth_id": "gt-e2", "label": "square"},
        ],
        "actions": [
            {
                "ground_truth_id": "gt-a1",
                "label": "points",
                "actor_ref": "gt-e1",
                "object_ref": "gt-e2",
            }
        ],
        "relations": [
            {
                "ground_truth_id": "gt-r1",
                "predicate": "left of",
                "subject_ref": "gt-e1",
                "object_ref": "gt-e2",
            }
        ],
        "themes": [
            {"ground_truth_id": "gt-t1", "label": "shape group", "evidence_refs": ["gt-e1"]}
        ],
        "ambiguous_regions": [],
    }
    source = VisionImageReferenceV1(artifact_ref="test-image", sha256="a" * 64)
    request = VisionUnderstandingRequestV2(
        correlation_id="test-quality",
        source_image_ref=source,
        requested_profile_id=vision_profile_catalog_v2().profiles[0].profile_id,
    )
    result = _success(
        request,
        entities=(_entity("e1", "CIRCLE"), _entity("e2", "square")),
        actions=(_action("a1", "points", "e1", "e2"),),
        relations=(_relation("r1", "left-of", "e1", "e2"),),
        themes=(_theme("t1", "shape-group", ["e1"]),),
    )

    score = score_v3_quality_success(result, ground_truth)

    assert score.collection_scores["entities"].matched_count == 2
    assert score.collection_scores["actions"].matched_count == 1
    assert score.collection_scores["relations"].matched_count == 1
    assert score.collection_scores["themes"].matched_count == 1
    assert score.diagnostic_category_counts == {}


def test_quality_empty_collection_diagnostics_are_closed_tokens() -> None:
    ground_truth = {
        "entities": [
            {"ground_truth_id": "gt-e1", "label": "circle"},
            {"ground_truth_id": "gt-e2", "label": "square"},
            {"ground_truth_id": "gt-e3", "label": "triangle"},
        ],
        "actions": [],
        "relations": [
            {
                "ground_truth_id": "gt-r1",
                "predicate": "left of",
                "subject_ref": "gt-e1",
                "object_ref": "gt-e2",
            },
            {
                "ground_truth_id": "gt-r2",
                "predicate": "left of",
                "subject_ref": "gt-e2",
                "object_ref": "gt-e3",
            },
        ],
        "themes": [
            {
                "ground_truth_id": "gt-t1",
                "label": "sequence",
                "evidence_refs": ["gt-r1", "gt-r2"],
            }
        ],
        "ambiguous_regions": [],
    }
    request = VisionUnderstandingRequestV2(
        correlation_id="test-empty",
        source_image_ref=VisionImageReferenceV1(artifact_ref="test-image", sha256="a" * 64),
        requested_profile_id=vision_profile_catalog_v2().profiles[0].profile_id,
    )

    score = score_v3_quality_success(_success(request), ground_truth)

    assert score.diagnostic_category_counts["EXPECTED_COLLECTION_PREDICTED_EMPTY"] == 6


def test_ambiguous_region_scoring_is_count_only() -> None:
    ground_truth = {
        "entities": [{"ground_truth_id": "gt-e1", "label": "circle"}],
        "actions": [],
        "relations": [],
        "themes": [],
        "ambiguous_regions": [{"ground_truth_id": "gt-ar1"}],
    }
    request = VisionUnderstandingRequestV2(
        correlation_id="test-ambiguous",
        source_image_ref=VisionImageReferenceV1(artifact_ref="test-image", sha256="a" * 64),
        requested_profile_id=vision_profile_catalog_v2().profiles[0].profile_id,
    )

    score = score_v3_quality_success(
        _success(
            request,
            entities=(_entity("e1", "circle"),),
            ambiguous_regions=(_ambiguous("u1", "unrelated note"),),
        ),
        ground_truth,
    )

    ambiguous_score = score.collection_scores["ambiguous_regions"]
    assert ambiguous_score.ground_truth_count == 1
    assert ambiguous_score.predicted_count == 1
    assert ambiguous_score.matched_count == 1
    assert ambiguous_score.coverage == 1.0
    assert ambiguous_score.count_rate == 1.0
    assert ambiguous_score.accuracy is None


def test_fake_quality_pass_is_cleaned_and_serializes_only_safe_values(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    report, factory, _ = _run_fake_pass(tmp_path, monkeypatch)

    assert report.attempted_runs == 8
    assert report.schema_valid_count == 8
    assert len(report.runs) == 8
    assert factory.calls == 1
    assert factory.received_prompts == [C1_PROMPT_V3.prompt_text_provider()]
    assert not (tmp_path / "scratch").exists()
    assert factory.adapter is not None
    assert all(
        not Path(request.source_image_ref.artifact_ref).is_absolute()
        for request in factory.adapter.requests
    )

    payload = quality_pass_report_to_dict(report)
    serialized = json.dumps(payload)
    assert "MAPPING_READY" not in serialized
    assert "B4_PASS" not in serialized
    assert "raw provider output" not in serialized
    assert str(tmp_path) not in serialized
    assert all(run["collection_scores"] is not None for run in payload["runs"])


def test_raw_output_hook_is_required_and_scratch_is_cleaned(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    root = _copy_fixture_package(tmp_path, owner_approved=True)
    factory = V3QualityLocalFakeAdapterFactory(
        _static_outcomes(), emit_raw_output=False
    )

    with pytest.raises(V3QualityRawOutputHookNotWiredError, match="safe raw-output classification"):
        run_v3_quality_pass(
            factory,
            B3RawOutputCollector(),
            run_label="V3_QUALITY_PASS_1",
            decisions=_decisions(),
            fixture_root=root,
            runtime_dir=Path("scratch"),
            validate_media=_validation,
        )

    assert not (tmp_path / "scratch").exists()


def test_two_fake_passes_produce_quality_verdict_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pass_report, _, pass_root = _run_fake_pass(
        tmp_path / "pass", monkeypatch, start=_EXECUTED_AT
    )
    repeat_report, _, _ = _run_fake_pass(
        tmp_path / "repeat",
        monkeypatch,
        run_label="V3_QUALITY_REPEAT_1",
        start=_EXECUTED_AT + timedelta(minutes=2),
    )

    verdict = evaluate_v3_quality_pair(
        pass_report,
        repeat_report,
        decisions=_decisions(),
        same_lightning_session=True,
        fixture_root=pass_root,
    )

    assert verdict.overall == "QUALITY_READY"
    assert verdict.blocking_reasons == ()
    assert "MAPPING_READY" not in verdict.overall
