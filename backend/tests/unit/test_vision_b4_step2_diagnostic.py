"""No-GPU unit tests for the local B4 Step 2 diagnostic runner.

Every string used as "raw output" here is an artificial static test constant authored in this
file. No real provider output, prompt body, or model observation appears anywhere.
"""

from __future__ import annotations

import dataclasses
import inspect
import json
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest

from sketch2life.benchmark import vision_b4_step2_diagnostic
from sketch2life.benchmark.vision_b3_mapping_study import B3RawOutputCollector, B3RawOutputMode
from sketch2life.benchmark.vision_b4_quality_benchmark import (
    B4CollectionScore,
    run_b4_quality_pass,
)
from sketch2life.benchmark.vision_b4_step2_diagnostic import (
    B4DiagnosticCategory,
    B4DiagnosticRawOutputNotReviewedError,
    B4DiagnosticReviewGateError,
    B4DiagnosticReviewGateRequiredError,
    _diagnostic_categories,
    run_b4_step2_diagnostic,
)
from sketch2life.benchmark.vision_c1_prompt_mapping_study import (
    C1_PROMPT_V2,
    qwen_c1_adapter_factory,
)
from sketch2life.contracts.schemas.vision import (
    ActionCandidateV1,
    AmbiguousRegionCandidateV1,
    EntityCandidateV1,
    RelationCandidateV1,
    ThemeCandidateV1,
    VisionImageReferenceV1,
    VisionMediaValidationProvenanceV1,
)
from sketch2life.contracts.schemas.vision_v2 import (
    VisionProfileV2,
    VisionUnderstandingRequestV2,
    VisionUnderstandingResultV2,
    VisionUnderstandingSuccessV2,
    vision_profile_catalog_hash_v2,
    vision_profile_catalog_v2,
    vision_profile_config_hash_v2,
)
from sketch2life.infrastructure.ai.qwen_vision_runtime_config import QwenVisionRuntimeConfig
from sketch2life.infrastructure.ai.vision_lexical_policy import (
    LexicalRegressionContentPolicy,
    synthetic_prohibited_lexicon,
)

_EXECUTED_AT = datetime(2026, 9, 7, 12, 0, tzinfo=UTC)
_SOURCE_REF = VisionImageReferenceV1(artifact_ref="test-b4-step2-image", sha256="a" * 64)
_TAXONOMY = (
    "simple_entity",
    "multi_entity",
    "action_complete_endpoints",
    "action_null_endpoint",
    "entity_relation",
    "theme_evidence_refs",
    "ambiguous_region",
    "mixed_multi_collection",
)
_RAW_MARKER = "UNMISTAKABLE_B4S2_RAW_MARKER"
_GROUND_TRUTH_TEXTS = ("circle", "square", "triangle", "points", "moves", "left of", "shapes")
_EMPTY_PAYLOAD_RAW = json.dumps(
    {"entities": [], "actions": [], "relations": [], "themes": [], "ambiguous_regions": []}
)
_MARKER_ENTITY_RAW = json.dumps(
    {
        "entities": [
            {
                "observation_id": "e1",
                "label": {
                    "value": _RAW_MARKER,
                    "language": {"status": "NOT_DETERMINED", "tags": []},
                },
                "confidence": None,
            }
        ],
        "actions": [],
        "relations": [],
        "themes": [],
        "ambiguous_regions": [],
    }
)


def _text(value: str) -> dict[str, object]:
    return {"value": value, "language": {"status": "DECLARED", "tags": ["en"]}}


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


def _success(**overrides: Any) -> VisionUnderstandingSuccessV2:
    profile = vision_profile_catalog_v2().profiles[0]
    values: dict[str, Any] = {
        "correlation_id": "b4-step2-test",
        "executed_at": _EXECUTED_AT,
        "source_image_ref": _SOURCE_REF,
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


def _ground_truth() -> list[dict[str, object]]:
    return [
        {
            "fixture_id": "b4-fixture-01",
            "entities": [{"ground_truth_id": "gt-e1", "label": "circle"}],
            "actions": [],
            "relations": [],
            "themes": [],
            "ambiguous_regions": [],
        },
        {
            "fixture_id": "b4-fixture-02",
            "entities": [
                {"ground_truth_id": "gt-e1", "label": "circle"},
                {"ground_truth_id": "gt-e2", "label": "square"},
            ],
            "actions": [],
            "relations": [
                {
                    "ground_truth_id": "gt-r1",
                    "predicate": "left of",
                    "subject_ref": "gt-e1",
                    "object_ref": "gt-e2",
                }
            ],
            "themes": [],
            "ambiguous_regions": [],
        },
        {
            "fixture_id": "b4-fixture-03",
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
            "themes": [],
            "ambiguous_regions": [],
        },
        {
            "fixture_id": "b4-fixture-04",
            "entities": [{"ground_truth_id": "gt-e1", "label": "circle"}],
            "actions": [
                {
                    "ground_truth_id": "gt-a1",
                    "label": "moves",
                    "actor_ref": "gt-e1",
                    "object_ref": None,
                }
            ],
            "relations": [],
            "themes": [],
            "ambiguous_regions": [],
        },
        {
            "fixture_id": "b4-fixture-05",
            "entities": [
                {"ground_truth_id": "gt-e1", "label": "circle"},
                {"ground_truth_id": "gt-e2", "label": "square"},
            ],
            "actions": [],
            "relations": [
                {
                    "ground_truth_id": "gt-r1",
                    "predicate": "left of",
                    "subject_ref": "gt-e1",
                    "object_ref": "gt-e2",
                }
            ],
            "themes": [],
            "ambiguous_regions": [],
        },
        {
            "fixture_id": "b4-fixture-06",
            "entities": [
                {"ground_truth_id": "gt-e1", "label": "circle"},
                {"ground_truth_id": "gt-e2", "label": "square"},
                {"ground_truth_id": "gt-e3", "label": "triangle"},
            ],
            "actions": [],
            "relations": [],
            "themes": [
                {
                    "ground_truth_id": "gt-t1",
                    "label": "shapes",
                    "evidence_refs": ["gt-e1", "gt-e2", "gt-e3"],
                }
            ],
            "ambiguous_regions": [],
        },
        {
            "fixture_id": "b4-fixture-07",
            "entities": [
                {"ground_truth_id": "gt-e1", "label": "circle"},
                {"ground_truth_id": "gt-e2", "label": "square"},
            ],
            "actions": [],
            "relations": [],
            "themes": [],
            "ambiguous_regions": [{"ground_truth_id": "gt-u1", "note": "overlap"}],
        },
        {
            "fixture_id": "b4-fixture-08",
            "entities": [
                {"ground_truth_id": "gt-e1", "label": "circle"},
                {"ground_truth_id": "gt-e2", "label": "square"},
                {"ground_truth_id": "gt-e3", "label": "triangle"},
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
                {
                    "ground_truth_id": "gt-t1",
                    "label": "shapes",
                    "evidence_refs": ["gt-e1", "gt-e2", "gt-e3", "gt-a1", "gt-r1"],
                }
            ],
            "ambiguous_regions": [],
        },
    ]


def _write_package(tmp_path: Path) -> Path:
    root = tmp_path / "vision-b4"
    image_dir = root / "images"
    image_dir.mkdir(parents=True)
    ground_truth_text = json.dumps(
        {"ground_truth_version": "vision-b4-ground-truth-v1", "fixtures": _ground_truth()},
        indent=2,
    )
    ground_truth_path = root / "ground-truth-v1.json"
    ground_truth_path.write_text(ground_truth_text, encoding="utf-8")
    rule_path = root / "matching-rule-v1.md"
    rule_path.write_text("fixed matching rule", encoding="utf-8")
    fixture_rows: list[dict[str, str]] = []
    for index, taxonomy in enumerate(_TAXONOMY, start=1):
        image_path = image_dir / f"b4-fixture-{index:02d}.png"
        image_path.write_bytes(f"synthetic-{index}".encode())
        fixture_rows.append(
            {
                "fixture_id": f"b4-fixture-{index:02d}",
                "image_ref": f"images/{image_path.name}",
                "image_sha256": sha256(image_path.read_bytes()).hexdigest(),
                "taxonomy": taxonomy,
            }
        )
    manifest = {
        "manifest_version": "vision-b4-manifest-v1",
        "status": "OWNER_REVIEW_APPROVED",
        "prompt_protocol": {
            "protocol_id": C1_PROMPT_V2.protocol_id,
            "sha256": C1_PROMPT_V2.prompt_sha256,
            "schema_target": "VisionUnderstandingResultV2",
        },
        "ground_truth": {
            "ref": "ground-truth-v1.json",
            "sha256": sha256(ground_truth_path.read_bytes()).hexdigest(),
        },
        "matching_rule": {
            "rule_id": "vision-b4-matching-rule-v1",
            "ref": "matching-rule-v1.md",
            "sha256": sha256(rule_path.read_bytes()).hexdigest(),
        },
        "fixtures": fixture_rows,
    }
    (root / "manifest-v1.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return root


def _validation(_fixture_id: str, _image: Path, _audio: Path) -> VisionMediaValidationProvenanceV1:
    return VisionMediaValidationProvenanceV1(
        validation_artifact_ref="test-p2t1",
        validation_artifact_sha256="b" * 64,
        decision="PASS",
        validator_policy_version="test-policy",
    )


class _Adapter:
    def __init__(
        self, outcomes: list[VisionUnderstandingResultV2], hook: Any, raw_outputs: list[str]
    ) -> None:
        self._outcomes = outcomes
        self._hook = hook
        self._raw_outputs = raw_outputs
        self.calls = 0
        self.requests: list[VisionUnderstandingRequestV2] = []

    def understand(self, request: VisionUnderstandingRequestV2) -> VisionUnderstandingResultV2:
        self.requests.append(request)
        self._hook(self._raw_outputs[self.calls])
        outcome = self._outcomes[self.calls]
        self.calls += 1
        return outcome


class _Factory:
    def __init__(self, outcomes: list[VisionUnderstandingResultV2], raw_outputs: list[str]) -> None:
        self._outcomes = outcomes
        self._raw_outputs = raw_outputs
        self.calls = 0
        self.received_prompts: list[str] = []
        self.adapter: _Adapter | None = None

    def __call__(self, prompt: str, hook: Any) -> _Adapter:
        self.calls += 1
        self.received_prompts.append(prompt)
        self.adapter = _Adapter(self._outcomes, hook, self._raw_outputs)
        return self.adapter


def _matching_outcomes() -> list[VisionUnderstandingSuccessV2]:
    """Predictions that exactly match this file's artificial ground truth."""

    circle = _entity("e1", "circle")
    square = _entity("e2", "square")
    triangle = _entity("e3", "triangle")
    relation = _relation("r1", "left of", "e1", "e2")
    action = _action("a1", "points", "e1", "e2")
    return [
        _success(entities=(circle,)),
        _success(entities=(circle, square), relations=(relation,)),
        _success(entities=(circle, square), actions=(action,), relations=(relation,)),
        _success(entities=(circle,), actions=(_action("a1", "moves", "e1", None),)),
        _success(entities=(circle, square), relations=(relation,)),
        _success(
            entities=(circle, square, triangle),
            themes=(_theme("t1", "shapes", ["e1", "e2", "e3"]),),
        ),
        _success(entities=(circle, square), ambiguous_regions=(_ambiguous("u1", "overlap"),)),
        _success(
            entities=(circle, square, triangle),
            actions=(action,),
            relations=(relation,),
            themes=(_theme("t1", "shapes", ["e1", "e2", "e3", "a1", "r1"]),),
        ),
    ]


def _unmatched_outcomes() -> list[VisionUnderstandingSuccessV2]:
    """One entity that matches no authored label, and every other collection left empty."""

    return [_success(entities=(_entity("e1", "shape-alpha"),)) for _ in range(8)]


def _raw_outputs(marker: str = "{}") -> list[str]:
    return [marker for _ in range(8)]


def _gate(seen: list[Path]) -> Any:
    def review(path: Path) -> None:
        seen.append(path)

    return review


class _RepeatingGenerationRunner:
    """No-GPU stand-in for the real killable-subprocess generation runner.

    Always returns the same artificial static string passed at construction -- never real
    provider output -- so tests can exercise the real ``QwenVisionAdapter`` seam (including its
    own ``contextlib.suppress(Exception)`` around ``on_raw_output``) without a model or GPU.
    """

    def __init__(self, raw_output: str) -> None:
        self._raw_output = raw_output
        self.calls = 0

    def generate(
        self,
        profile: VisionProfileV2,
        runtime_config: QwenVisionRuntimeConfig,
        image_path: Path,
        prompt: str,
    ) -> str:
        del profile, runtime_config, image_path, prompt
        self.calls += 1
        return self._raw_output


def _real_adapter_factory(runner: _RepeatingGenerationRunner) -> Any:
    """The real production ``C1AdapterFactory``, wired to a fake generation runner only."""

    return qwen_c1_adapter_factory(
        QwenVisionRuntimeConfig(model_dir=Path("local-model")),
        LexicalRegressionContentPolicy(synthetic_prohibited_lexicon()),
        generation_runner=runner,
    )


def test_diagnostic_calls_each_of_the_eight_fixtures_exactly_once_without_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    root = _write_package(tmp_path)
    factory = _Factory(_matching_outcomes(), _raw_outputs())
    seen: list[Path] = []

    report = run_b4_step2_diagnostic(
        factory,
        review_gate=_gate(seen),
        fixture_root=root,
        runtime_dir=Path("b4-step2-scratch"),
        validate_media=_validation,
    )

    assert factory.calls == 1
    assert factory.received_prompts == [C1_PROMPT_V2.prompt_text_provider()]
    assert factory.adapter is not None and factory.adapter.calls == 8
    assert [request.correlation_id for request in factory.adapter.requests] == [
        f"vision-b4-step2-diagnostic-b4-fixture-{index:02d}" for index in range(1, 9)
    ]
    assert report.attempted_runs == 8
    assert len(report.runs) == 8
    assert [run.fixture_id for run in report.runs] == [
        f"b4-fixture-{index:02d}" for index in range(1, 9)
    ]
    assert all(run.attempt_number == 1 and not run.repair_attempted for run in report.runs)
    assert report.schema_valid_count == 8
    assert report.reviewed_raw_output_count == 8
    assert len(seen) == 8
    assert not (tmp_path / "b4-step2-scratch").exists()


def test_diagnostic_can_never_be_labelled_as_a_b4_quality_pass_or_repeat(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    root = _write_package(tmp_path)
    factory = _Factory(_matching_outcomes(), _raw_outputs())

    report = run_b4_step2_diagnostic(
        factory,
        review_gate=_gate([]),
        fixture_root=root,
        runtime_dir=Path("scratch"),
        validate_media=_validation,
    )

    assert report.run_label == "B4_STEP2_DIAGNOSTIC_1"
    assert report.quality_score_authority == "NONE_DIAGNOSTIC_ONLY"
    assert report.raw_output_mode == "EPHEMERAL_REVIEW_GATE"
    assert "run_label" not in inspect.signature(run_b4_step2_diagnostic).parameters


def test_missing_review_gate_fails_closed_before_factory_or_any_package_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The gate check precedes even the fixture-package read, so no provider action can occur."""

    monkeypatch.chdir(tmp_path)
    factory = _Factory(_matching_outcomes(), _raw_outputs())

    with pytest.raises(B4DiagnosticReviewGateRequiredError):
        run_b4_step2_diagnostic(
            factory,
            fixture_root=tmp_path / "package-that-does-not-exist",
            runtime_dir=Path("scratch"),
            validate_media=_validation,
        )

    assert factory.calls == 0
    assert not (tmp_path / "scratch").exists()


def test_capture_file_exists_only_while_the_review_gate_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    root = _write_package(tmp_path)
    factory = _Factory(_matching_outcomes(), _raw_outputs(json.dumps({"marker": _RAW_MARKER})))
    observed: list[tuple[Path, bool, bool]] = []

    def review(path: Path) -> None:
        observed.append((path, path.is_file(), _RAW_MARKER in path.read_text(encoding="utf-8")))

    run_b4_step2_diagnostic(
        factory,
        review_gate=review,
        fixture_root=root,
        runtime_dir=Path("scratch"),
        validate_media=_validation,
    )

    assert len(observed) == 8
    assert all(exists and has_marker for _path, exists, has_marker in observed)
    assert all(not path.exists() for path, _exists, _has_marker in observed)
    assert not (tmp_path / "scratch").exists()


@pytest.mark.parametrize("failure_mode", ["none", "review_gate", "adapter", "classifier"])
def test_capture_file_and_scratch_are_removed_on_success_and_every_failure_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure_mode: str
) -> None:
    monkeypatch.chdir(tmp_path)
    root = _write_package(tmp_path)
    captured_paths: list[Path] = []

    def review(path: Path) -> None:
        captured_paths.append(path)
        if failure_mode == "review_gate":
            raise RuntimeError("synthetic review-gate failure")

    class _FailingAdapter(_Adapter):
        def understand(
            self, request: VisionUnderstandingRequestV2
        ) -> VisionUnderstandingResultV2:
            self._hook(self._raw_outputs[self.calls])
            self.calls += 1
            raise RuntimeError("synthetic adapter failure")

    class _FailingFactory(_Factory):
        def __call__(self, prompt: str, hook: Any) -> _Adapter:
            self.calls += 1
            self.adapter = _FailingAdapter(self._outcomes, hook, self._raw_outputs)
            return self.adapter

    if failure_mode == "classifier":

        def failing_classifier(_raw_output: str) -> Any:
            raise RuntimeError("synthetic classifier failure")

        monkeypatch.setattr(
            vision_b4_step2_diagnostic, "classify_raw_output", failing_classifier
        )

    factory: _Factory = (
        _FailingFactory(_matching_outcomes(), _raw_outputs())
        if failure_mode == "adapter"
        else _Factory(_matching_outcomes(), _raw_outputs())
    )

    def run() -> None:
        run_b4_step2_diagnostic(
            factory,
            review_gate=review,
            fixture_root=root,
            runtime_dir=Path("scratch"),
            validate_media=_validation,
        )

    if failure_mode == "none":
        run()
    else:
        with pytest.raises(RuntimeError):
            run()

    assert captured_paths
    assert all(not path.exists() for path in captured_paths)
    assert not (tmp_path / "scratch").exists()


def test_review_gate_failure_never_carries_raw_text_or_the_capture_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    root = _write_package(tmp_path)
    factory = _Factory(_matching_outcomes(), _raw_outputs(json.dumps({"marker": _RAW_MARKER})))

    def review(path: Path) -> None:
        raise RuntimeError(f"{_RAW_MARKER} leaked via {path}")

    with pytest.raises(B4DiagnosticReviewGateError) as error_info:
        run_b4_step2_diagnostic(
            factory,
            review_gate=review,
            fixture_root=root,
            runtime_dir=Path("scratch"),
            validate_media=_validation,
        )

    error = error_info.value
    assert error.__cause__ is None
    assert error.__context__ is None
    rendered = f"{error!r} {error}"
    assert _RAW_MARKER not in rendered
    assert "scratch" not in rendered
    assert str(tmp_path) not in rendered


def test_report_and_serialization_never_carry_raw_prompt_ground_truth_or_path_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    root = _write_package(tmp_path)
    factory = _Factory(_matching_outcomes(), _raw_outputs(json.dumps({"marker": _RAW_MARKER})))

    report = run_b4_step2_diagnostic(
        factory,
        review_gate=_gate([]),
        fixture_root=root,
        runtime_dir=Path("scratch"),
        validate_media=_validation,
    )

    serialized = json.dumps(dataclasses.asdict(report), default=str)
    assert _RAW_MARKER not in serialized
    for ground_truth_text in _GROUND_TRUTH_TEXTS:
        assert f'"{ground_truth_text}"' not in serialized
    assert "Return exactly one compact JSON object" not in serialized
    assert C1_PROMPT_V2.prompt_text_provider() not in serialized
    assert str(tmp_path) not in serialized
    assert "scratch" not in serialized
    assert "images/" not in serialized
    assert C1_PROMPT_V2.prompt_sha256 in serialized


def test_run_reports_safe_categories_for_controlled_unmatched_and_empty_collections(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Eight fixtures each predict one unmatched entity and nothing else."""

    monkeypatch.chdir(tmp_path)
    root = _write_package(tmp_path)
    factory = _Factory(_unmatched_outcomes(), _raw_outputs())

    report = run_b4_step2_diagnostic(
        factory,
        review_gate=_gate([]),
        fixture_root=root,
        runtime_dir=Path("scratch"),
        validate_media=_validation,
    )

    assert report.aggregate_category_counts == {
        B4DiagnosticCategory.ENTITY_NO_EXACT_CANONICAL_LABEL_MATCH: 8,
        B4DiagnosticCategory.EXPECTED_COLLECTION_PREDICTED_EMPTY: 10,
    }
    assert report.runs[0].category_counts == {
        B4DiagnosticCategory.ENTITY_NO_EXACT_CANONICAL_LABEL_MATCH: 1
    }
    assert report.runs[7].category_counts == {
        B4DiagnosticCategory.ENTITY_NO_EXACT_CANONICAL_LABEL_MATCH: 1,
        B4DiagnosticCategory.EXPECTED_COLLECTION_PREDICTED_EMPTY: 3,
    }


def test_fully_matching_predictions_emit_no_diagnostic_category(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    root = _write_package(tmp_path)
    factory = _Factory(_matching_outcomes(), _raw_outputs())

    report = run_b4_step2_diagnostic(
        factory,
        review_gate=_gate([]),
        fixture_root=root,
        runtime_dir=Path("scratch"),
        validate_media=_validation,
    )

    assert report.aggregate_category_counts == {}
    assert all(run.category_counts == {} for run in report.runs)


def _score(ground_truth: int, predicted: int, matched: int) -> B4CollectionScore:
    return B4CollectionScore(
        ground_truth_count=ground_truth,
        predicted_count=predicted,
        matched_count=matched,
        coverage=None,
        accuracy=None,
    )


def test_diagnostic_categories_cover_each_collection_and_exclude_ambiguous_match_verdicts() -> None:
    every_token = _diagnostic_categories(
        {
            "entities": _score(2, 3, 1),
            "actions": _score(1, 2, 0),
            "relations": _score(1, 2, 0),
            "themes": _score(1, 1, 0),
            "ambiguous_regions": _score(1, 0, 0),
        }
    )

    assert every_token == {
        B4DiagnosticCategory.ENTITY_NO_EXACT_CANONICAL_LABEL_MATCH: 2,
        B4DiagnosticCategory.ACTION_NO_FULL_LABEL_OR_ENDPOINT_MATCH: 2,
        B4DiagnosticCategory.RELATION_NO_FULL_PREDICATE_OR_ENDPOINT_MATCH: 2,
        B4DiagnosticCategory.THEME_NO_FULL_LABEL_OR_EVIDENCE_REF_MATCH: 1,
        B4DiagnosticCategory.EXPECTED_COLLECTION_PREDICTED_EMPTY: 1,
    }

    unmatched_ambiguous_only = _diagnostic_categories(
        {
            "entities": _score(0, 0, 0),
            "actions": _score(0, 0, 0),
            "relations": _score(0, 0, 0),
            "themes": _score(0, 0, 0),
            "ambiguous_regions": _score(1, 2, 0),
        }
    )

    assert unmatched_ambiguous_only == {}


def test_missing_raw_output_classification_fails_closed_and_cleans_scratch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    root = _write_package(tmp_path)

    class _SilentAdapter(_Adapter):
        def understand(
            self, request: VisionUnderstandingRequestV2
        ) -> VisionUnderstandingResultV2:
            outcome = self._outcomes[self.calls]
            self.calls += 1
            return outcome

    class _SilentFactory(_Factory):
        def __call__(self, prompt: str, hook: Any) -> _Adapter:
            self.calls += 1
            self.adapter = _SilentAdapter(self._outcomes, hook, self._raw_outputs)
            return self.adapter

    factory = _SilentFactory(_matching_outcomes(), _raw_outputs())

    with pytest.raises(B4DiagnosticRawOutputNotReviewedError):
        run_b4_step2_diagnostic(
            factory,
            review_gate=_gate([]),
            fixture_root=root,
            runtime_dir=Path("scratch"),
            validate_media=_validation,
        )

    assert factory.adapter is not None and factory.adapter.calls == 1
    assert not (tmp_path / "scratch").exists()


def test_existing_b4_quality_runner_and_b3_collector_behaviour_is_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The diagnostic module is additive: it neither rescores B4 nor changes B3 collection."""

    monkeypatch.chdir(tmp_path)
    root = _write_package(tmp_path)
    factory = _Factory(_matching_outcomes(), _raw_outputs())

    quality_report = run_b4_quality_pass(
        factory,
        B3RawOutputCollector(),
        run_label="B4_PASS_1",
        fixture_root=root,
        runtime_dir=Path("quality-scratch"),
        sample_vram=False,
        validate_media=_validation,
    )

    assert quality_report.run_label == "B4_PASS_1"
    assert quality_report.schema_valid_count == 8
    assert quality_report.aggregate_collection_scores["entities"].coverage == 1.0
    assert quality_report.aggregate_collection_scores["relations"].coverage == 1.0
    assert not (tmp_path / "quality-scratch").exists()

    collector = B3RawOutputCollector()
    assert collector.mode is B3RawOutputMode.CLASSIFY_ONLY
    collector.hook(json.dumps({"entities": []}))
    classification = collector.take_latest()
    assert classification is not None and not classification.fenced
    assert collector.take_latest() is None
    assert not any(path.name.endswith(".txt") for path in tmp_path.rglob("*"))


# --- Real-adapter regression coverage -------------------------------------------------------
#
# Everything above drives the diagnostic through a fake VisionUnderstandingPortV2 whose
# ``.understand`` calls ``self._hook(...)`` directly and lets any hook exception propagate. The
# real ``QwenVisionAdapter`` does not: it runs ``on_raw_output`` under
# ``contextlib.suppress(Exception)`` (qwen_vision.py, ``understand``), so a hook that raised would
# have that failure silently swallowed and ``understand`` would return its normal typed result
# regardless. The tests below build the real adapter (via the real production
# ``qwen_c1_adapter_factory``) with a fake, no-GPU generation runner, to prove the fix holds under
# that real suppression boundary rather than only under a fake port that happens not to suppress.


def test_real_qwen_adapter_review_gate_failure_surfaces_as_sanitized_error_with_no_leak(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A gate failure must reach this diagnostic even though the real adapter swallows it."""

    monkeypatch.chdir(tmp_path)
    root = _write_package(tmp_path)
    runner = _RepeatingGenerationRunner(_EMPTY_PAYLOAD_RAW)

    def failing_gate(path: Path) -> None:
        raise RuntimeError(f"synthetic gate failure naming {path} and {_RAW_MARKER}")

    with pytest.raises(B4DiagnosticReviewGateError) as error_info:
        run_b4_step2_diagnostic(
            _real_adapter_factory(runner),
            review_gate=failing_gate,
            fixture_root=root,
            runtime_dir=Path("scratch"),
            validate_media=_validation,
        )

    error = error_info.value
    assert error.__cause__ is None
    assert error.__context__ is None
    rendered = f"{error!r} {error}"
    assert _RAW_MARKER not in rendered
    assert "scratch" not in rendered
    assert str(tmp_path) not in rendered
    assert runner.calls == 1
    assert not (tmp_path / "scratch").exists()


def test_real_qwen_adapter_classification_failure_surfaces_as_not_reviewed_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Classification failing after a successful gate call must also reach this diagnostic."""

    monkeypatch.chdir(tmp_path)
    root = _write_package(tmp_path)
    runner = _RepeatingGenerationRunner(_EMPTY_PAYLOAD_RAW)

    def failing_classifier(_raw_output: str) -> Any:
        raise RuntimeError("synthetic classifier failure")

    monkeypatch.setattr(vision_b4_step2_diagnostic, "classify_raw_output", failing_classifier)

    with pytest.raises(B4DiagnosticRawOutputNotReviewedError):
        run_b4_step2_diagnostic(
            _real_adapter_factory(runner),
            review_gate=_gate([]),
            fixture_root=root,
            runtime_dir=Path("scratch"),
            validate_media=_validation,
        )

    assert runner.calls == 1
    assert not (tmp_path / "scratch").exists()


def test_real_qwen_adapter_cleans_capture_file_and_scratch_after_review_gate_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    root = _write_package(tmp_path)
    runner = _RepeatingGenerationRunner(_EMPTY_PAYLOAD_RAW)
    seen: list[Path] = []

    def failing_gate(path: Path) -> None:
        seen.append(path)
        assert path.is_file()
        raise RuntimeError("synthetic gate failure")

    with pytest.raises(B4DiagnosticReviewGateError):
        run_b4_step2_diagnostic(
            _real_adapter_factory(runner),
            review_gate=failing_gate,
            fixture_root=root,
            runtime_dir=Path("scratch"),
            validate_media=_validation,
        )

    assert len(seen) == 1
    assert not seen[0].exists()
    assert not (tmp_path / "scratch").exists()


def test_real_qwen_adapter_success_path_report_never_leaks_predicted_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A real, schema-valid predicted label reaches the adapter but never the diagnostic report."""

    monkeypatch.chdir(tmp_path)
    root = _write_package(tmp_path)
    runner = _RepeatingGenerationRunner(_MARKER_ENTITY_RAW)

    report = run_b4_step2_diagnostic(
        _real_adapter_factory(runner),
        review_gate=_gate([]),
        fixture_root=root,
        runtime_dir=Path("scratch"),
        validate_media=_validation,
    )

    assert runner.calls == 8
    assert report.schema_valid_count == 8
    assert report.reviewed_raw_output_count == 8
    serialized = json.dumps(dataclasses.asdict(report), default=str)
    assert _RAW_MARKER not in serialized
    assert str(tmp_path) not in serialized
    assert "scratch" not in serialized
    assert not (tmp_path / "scratch").exists()
