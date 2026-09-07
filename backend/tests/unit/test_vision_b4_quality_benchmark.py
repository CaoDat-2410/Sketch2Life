from __future__ import annotations

import dataclasses
import json
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from struct import pack
from typing import Any
from zlib import compress

import pytest

from sketch2life.application.services.media_validation import (
    DeterministicMediaValidator,
    MediaValidationRequest,
)
from sketch2life.benchmark.vision_b3_mapping_study import (
    B3RawOutputCollector,
    B3RawOutputMode,
)
from sketch2life.benchmark.vision_b4_quality_benchmark import (
    B4FixtureIntegrityError,
    B4InvalidRunLabelError,
    B4PromptBindingError,
    B4RawOutputHookNotWiredError,
    _maximum_matching,
    _score_success,
    _write_companion_audio,
    run_b4_quality_pass,
)
from sketch2life.benchmark.vision_c1_prompt_mapping_study import C1_PROMPT_V2
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
    VisionUnderstandingRequestV2,
    VisionUnderstandingResultV2,
    VisionUnderstandingSuccessV2,
    vision_profile_catalog_hash_v2,
    vision_profile_catalog_v2,
    vision_profile_config_hash_v2,
)
from sketch2life.domain.understanding.media_quality import MediaDecision
from sketch2life.infrastructure.media_validation.file_inspector import FileMediaSignalInspector

_EXECUTED_AT = datetime(2026, 9, 7, 12, 0, tzinfo=UTC)
_SOURCE_REF = VisionImageReferenceV1(artifact_ref="test-b4-image", sha256="a" * 64)
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
        "correlation_id": "b4-test",
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


def _write_valid_png(path: Path) -> None:
    """A real, decodable PNG earning a P2-T1 image PASS (unlike this file's fake fixture bytes)."""

    width = height = 160
    raw = b"".join(
        b"\x00"
        + b"".join(
            bytes((20, 20, 20) if 30 < x < 130 and y % 7 < 3 else (255, 255, 255))
            for x in range(width)
        )
        for y in range(height)
    )
    header = pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)

    def chunk(tag: bytes, data: bytes) -> bytes:
        return pack(">I", len(data)) + tag + data + pack(">I", 0)

    payload = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", compress(raw))
        + chunk(b"IEND", b"")
    )
    path.write_bytes(payload)


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


def _outcomes() -> list[VisionUnderstandingSuccessV2]:
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


def test_generated_companion_audio_earns_a_real_p2t1_pass(tmp_path: Path) -> None:
    """Regression for B4's zero-padded companion WAV: it must earn a real P2-T1 PASS.

    Exercises the actual DeterministicMediaValidator/FileMediaSignalInspector pair with the
    module's own ``_write_companion_audio`` output and a real, decodable image -- the same
    path the Lightning run took before it raised ``B4FixtureIntegrityError``. This fails with
    the prior zero-padded waveform, which earns zero adjacent-sign-change zero crossings and
    is rejected as ``AUDIO_NO_SPEECH_SIGNAL``.
    """

    image_path = tmp_path / "b4-fixture-01.png"
    audio_path = tmp_path / "b4-companion.wav"
    _write_valid_png(image_path)
    _write_companion_audio(audio_path)

    result = DeterministicMediaValidator(FileMediaSignalInspector()).validate(
        MediaValidationRequest(
            image_path=image_path,
            audio_path=audio_path,
            image_artifact_ref="vision-b4-b4-fixture-01-synthetic-image",
            audio_artifact_ref="vision-b4-synthetic-audio",
        )
    )

    assert result.decision is MediaDecision.PASS
    assert result.recapture_reasons == ()


def test_default_media_validation_blocks_factory_and_cleans_scratch_on_a_real_p2t1_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The runner's default ``validate_media`` still fails closed on a real P2-T1 failure.

    Uses this file's fake fixture image bytes (not a real PNG), so the real inspector reports
    ``IMAGE_UNREADABLE`` regardless of the now-fixed companion audio -- proving the fixed audio
    path did not weaken the runner's fail-closed preflight or its scratch cleanup.
    """

    monkeypatch.chdir(tmp_path)
    root = _write_package(tmp_path)
    factory = _Factory(_outcomes(), ["{}"] * 8)

    with pytest.raises(B4FixtureIntegrityError, match="did not earn a real P2-T1 PASS"):
        run_b4_quality_pass(
            factory,
            B3RawOutputCollector(),
            run_label="B4_PASS_1",
            fixture_root=root,
            runtime_dir=Path("scratch"),
            sample_vram=False,
        )

    assert factory.calls == 0
    assert not (tmp_path / "scratch").exists()


def test_run_scores_all_eight_owner_approved_fixtures_once_without_raw_output_persistence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    root = _write_package(tmp_path)
    marker = "UNMISTAKABLE_B4_RAW_MARKER"
    factory = _Factory(_outcomes(), [json.dumps({"marker": marker}) for _ in range(8)])
    collector = B3RawOutputCollector(mode=B3RawOutputMode.CLASSIFY_ONLY)
    validated_fixture_ids: list[str] = []

    def validation(fixture_id: str, image: Path, audio: Path) -> VisionMediaValidationProvenanceV1:
        validated_fixture_ids.append(fixture_id)
        return _validation(fixture_id, image, audio)

    report = run_b4_quality_pass(
        factory,
        collector,
        run_label="B4_PASS_1",
        fixture_root=root,
        runtime_dir=Path("b4-scratch"),
        sample_vram=False,
        validate_media=validation,
    )

    assert factory.calls == 1
    assert validated_fixture_ids == [f"b4-fixture-{index:02d}" for index in range(1, 9)]
    assert factory.received_prompts == [C1_PROMPT_V2.prompt_text_provider()]
    assert factory.adapter is not None and factory.adapter.calls == 8
    assert report.attempted_runs == 8
    assert report.schema_valid_count == 8
    assert report.aggregate_collection_scores["entities"].coverage == 1.0
    assert report.aggregate_collection_scores["actions"].accuracy == 1.0
    assert report.aggregate_collection_scores["relations"].coverage == 1.0
    assert report.aggregate_collection_scores["themes"].accuracy == 1.0
    assert report.aggregate_collection_scores["ambiguous_regions"].accuracy is None
    assert report.extra_key_count == 8
    assert marker not in json.dumps(dataclasses.asdict(report), default=str)
    assert not (tmp_path / "b4-scratch").exists()


def test_manifest_integrity_failure_happens_before_factory_or_adapter_call(tmp_path: Path) -> None:
    root = _write_package(tmp_path)
    manifest_path = root / "manifest-v1.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["fixtures"][0]["image_sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    factory = _Factory(_outcomes(), ["{}"] * 8)

    with pytest.raises(B4FixtureIntegrityError, match="SHA-256 mismatch"):
        run_b4_quality_pass(
            factory,
            B3RawOutputCollector(),
            run_label="B4_PASS_1",
            fixture_root=root,
            runtime_dir=tmp_path / "scratch",
            sample_vram=False,
            validate_media=_validation,
        )

    assert factory.calls == 0


def test_manifest_without_owner_approval_is_rejected_before_factory_call(tmp_path: Path) -> None:
    root = _write_package(tmp_path)
    manifest_path = root / "manifest-v1.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["status"] = "OWNER_REVIEW_REQUIRED"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    factory = _Factory(_outcomes(), ["{}"] * 8)

    with pytest.raises(B4FixtureIntegrityError, match="owner review approval"):
        run_b4_quality_pass(
            factory,
            B3RawOutputCollector(),
            run_label="B4_PASS_1",
            fixture_root=root,
            runtime_dir=Path("scratch"),
            sample_vram=False,
            validate_media=_validation,
        )

    assert factory.calls == 0


@pytest.mark.parametrize("invalid_reference", ["duplicate", "action", "relation", "theme"])
def test_invalid_authored_ground_truth_is_rejected_before_factory_construction(
    tmp_path: Path, invalid_reference: str
) -> None:
    root = _write_package(tmp_path)
    ground_truth_path = root / "ground-truth-v1.json"
    ground_truth = json.loads(ground_truth_path.read_text(encoding="utf-8"))
    fixture = ground_truth["fixtures"][0]
    if invalid_reference == "duplicate":
        fixture["entities"].append({"ground_truth_id": "gt-e1", "label": "square"})
    elif invalid_reference == "action":
        fixture["actions"] = [
            {
                "ground_truth_id": "gt-a1",
                "label": "points",
                "actor_ref": "unknown",
                "object_ref": None,
            }
        ]
    elif invalid_reference == "relation":
        fixture["relations"] = [
            {
                "ground_truth_id": "gt-r1",
                "predicate": "left of",
                "subject_ref": "gt-e1",
                "object_ref": "unknown",
            }
        ]
    else:
        fixture["themes"] = [
            {
                "ground_truth_id": "gt-t1",
                "label": "shapes",
                "evidence_refs": ["unknown"],
            }
        ]
    ground_truth_path.write_text(json.dumps(ground_truth), encoding="utf-8")
    manifest_path = root / "manifest-v1.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["ground_truth"]["sha256"] = sha256(ground_truth_path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    factory = _Factory(_outcomes(), ["{}"] * 8)

    with pytest.raises(B4FixtureIntegrityError):
        run_b4_quality_pass(
            factory,
            B3RawOutputCollector(),
            run_label="B4_PASS_1",
            fixture_root=root,
            runtime_dir=Path("scratch"),
            sample_vram=False,
            validate_media=_validation,
        )

    assert factory.calls == 0


def test_invalid_run_label_is_rejected_before_prompt_or_factory_work(tmp_path: Path) -> None:
    root = _write_package(tmp_path)
    factory = _Factory(_outcomes(), ["{}"] * 8)

    with pytest.raises(B4InvalidRunLabelError):
        run_b4_quality_pass(
            factory,
            B3RawOutputCollector(),
            run_label="B4_UNREGISTERED",  # type: ignore[arg-type]
            fixture_root=root,
            runtime_dir=Path("scratch"),
            sample_vram=False,
            validate_media=_validation,
        )

    assert factory.calls == 0


def test_unapproved_or_forged_prompt_never_reaches_factory(tmp_path: Path) -> None:
    root = _write_package(tmp_path)
    factory = _Factory(_outcomes(), ["{}"] * 8)
    forged = dataclasses.replace(C1_PROMPT_V2, prompt_text_provider=lambda: "")

    with pytest.raises(B4PromptBindingError):
        run_b4_quality_pass(
            factory,
            B3RawOutputCollector(),
            run_label="B4_PASS_1",
            fixture_root=root,
            runtime_dir=tmp_path / "scratch",
            prompt=forged,
            sample_vram=False,
            validate_media=_validation,
        )

    assert factory.calls == 0


def test_runtime_scratch_cannot_escape_the_current_working_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    root = _write_package(tmp_path)
    factory = _Factory(_outcomes(), ["{}"] * 8)

    with pytest.raises(B4FixtureIntegrityError, match="strictly nested"):
        run_b4_quality_pass(
            factory,
            B3RawOutputCollector(),
            run_label="B4_PASS_1",
            fixture_root=root,
            runtime_dir=Path("../outside"),
            sample_vram=False,
            validate_media=_validation,
        )

    assert factory.calls == 0


def test_media_validation_failure_prevents_factory_construction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    root = _write_package(tmp_path)
    factory = _Factory(_outcomes(), ["{}"] * 8)

    def failing_validation(
        fixture_id: str, image: Path, audio: Path
    ) -> VisionMediaValidationProvenanceV1:
        if fixture_id == "b4-fixture-08":
            raise B4FixtureIntegrityError("synthetic P2-T1 failure")
        return _validation(fixture_id, image, audio)

    with pytest.raises(B4FixtureIntegrityError, match="synthetic P2-T1 failure"):
        run_b4_quality_pass(
            factory,
            B3RawOutputCollector(),
            run_label="B4_PASS_1",
            fixture_root=root,
            runtime_dir=Path("scratch"),
            sample_vram=False,
            validate_media=failing_validation,
        )

    assert factory.calls == 0


def test_missing_raw_output_classification_fails_closed_and_cleans_runtime_scratch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    root = _write_package(tmp_path)

    class AdapterWithoutHook(_Adapter):
        def understand(self, request: VisionUnderstandingRequestV2) -> VisionUnderstandingResultV2:
            self.requests.append(request)
            outcome = self._outcomes[self.calls]
            self.calls += 1
            return outcome

    class FactoryWithoutHook(_Factory):
        def __call__(self, prompt: str, hook: Any) -> AdapterWithoutHook:
            self.calls += 1
            self.received_prompts.append(prompt)
            self.adapter = AdapterWithoutHook(self._outcomes, hook, self._raw_outputs)
            return self.adapter

    factory = FactoryWithoutHook(_outcomes(), ["{}"] * 8)
    with pytest.raises(B4RawOutputHookNotWiredError):
        run_b4_quality_pass(
            factory,
            B3RawOutputCollector(),
            run_label="B4_PASS_1",
            fixture_root=root,
            runtime_dir=Path("scratch"),
            sample_vram=False,
            validate_media=_validation,
        )

    assert factory.adapter is not None and factory.adapter.calls == 1
    assert not (tmp_path / "scratch").exists()


def test_incorrect_action_endpoint_receives_no_match_credit() -> None:
    ground_truth = _ground_truth()[2]
    result = _success(
        entities=(_entity("e1", "circle"), _entity("e2", "square")),
        actions=(_action("a1", "points", "e2", "e1"),),
        relations=(_relation("r1", "left of", "e1", "e2"),),
    )

    scores = _score_success(result, ground_truth)

    assert scores["entities"].matched_count == 2
    assert scores["actions"].matched_count == 0
    assert scores["relations"].matched_count == 1


def test_relation_note_is_not_a_scoring_override() -> None:
    ground_truth = _ground_truth()[5]
    result = _success(
        entities=(
            _entity("e1", "circle"),
            _entity("e2", "square"),
            _entity("e3", "triangle"),
        ),
        relations=(_relation("r1", "left of", "e2", "e3"),),
    )

    scores = _score_success(result, ground_truth)

    assert scores["relations"].ground_truth_count == 0
    assert scores["relations"].predicted_count == 1
    assert scores["relations"].accuracy == 0.0
    assert scores["relations"].coverage is None


def test_theme_evidence_reference_order_does_not_change_the_exact_set_match() -> None:
    ground_truth = _ground_truth()[5]
    result = _success(
        entities=(
            _entity("e1", "circle"),
            _entity("e2", "square"),
            _entity("e3", "triangle"),
        ),
        themes=(_theme("t1", "shapes", ["e3", "e1", "e2"]),),
    )

    scores = _score_success(result, ground_truth)

    assert scores["themes"].matched_count == 1


def test_large_schema_valid_candidate_set_uses_bounded_matching_without_changing_score() -> None:
    ground_truth: dict[str, object] = {
        "entities": [
            {"ground_truth_id": "gt-e1", "label": "circle"},
            {"ground_truth_id": "gt-e2", "label": "circle"},
            {"ground_truth_id": "gt-e3", "label": "circle"},
        ],
        "actions": [],
        "relations": [],
        "themes": [],
        "ambiguous_regions": [],
    }
    result = _success(entities=tuple(_entity(f"e{index:02d}", "circle") for index in range(60)))

    scores = _score_success(result, ground_truth)

    assert scores["entities"].matched_count == 3
    assert scores["entities"].accuracy == pytest.approx(3 / 60)


def test_tie_break_prefers_ascending_ground_truth_then_prediction_identifiers() -> None:
    ground_truth = [
        {"ground_truth_id": "gt-e2", "label": "circle"},
        {"ground_truth_id": "gt-e1", "label": "circle"},
    ]
    predicted = (_entity("e3", "circle"), _entity("e1", "circle"), _entity("e2", "circle"))

    matches = _maximum_matching(predicted, ground_truth, lambda _predicted, _expected: True)

    assert matches == {"e1": "gt-e1", "e2": "gt-e2"}


def test_endpoint_and_evidence_eligibility_outrank_lower_prediction_identifiers() -> None:
    ground_truth: dict[str, object] = {
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
        "relations": [],
        "themes": [
            {"ground_truth_id": "gt-t1", "label": "shapes", "evidence_refs": ["gt-e1", "gt-e2"]}
        ],
        "ambiguous_regions": [],
    }
    result = _success(
        entities=(_entity("e1", "circle"), _entity("e2", "square")),
        actions=(
            _action("a1", "points", "e2", "e1"),
            _action("a2", "points", "e1", "e2"),
        ),
        themes=(
            _theme("t1", "shapes", ["e1"]),
            _theme("t2", "shapes", ["e1", "e2"]),
        ),
    )

    scores = _score_success(result, ground_truth)

    assert scores["entities"].matched_count == 2
    assert scores["actions"].matched_count == 1
    assert scores["actions"].accuracy == pytest.approx(0.5)
    assert scores["themes"].matched_count == 1
    assert scores["themes"].accuracy == pytest.approx(0.5)


def test_pass_and_repeat_are_separate_calls_with_no_collector_state_leak(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    root = _write_package(tmp_path)
    factory = _Factory(_outcomes(), ["{}"] * 8)

    pass_1 = run_b4_quality_pass(
        factory,
        B3RawOutputCollector(),
        run_label="B4_PASS_1",
        fixture_root=root,
        runtime_dir=Path("pass"),
        sample_vram=False,
        validate_media=_validation,
    )
    repeat_1 = run_b4_quality_pass(
        factory,
        B3RawOutputCollector(),
        run_label="B4_REPEAT_1",
        fixture_root=root,
        runtime_dir=Path("repeat"),
        sample_vram=False,
        validate_media=_validation,
    )

    assert factory.calls == 2
    assert pass_1.run_label == "B4_PASS_1"
    assert repeat_1.run_label == "B4_REPEAT_1"
    assert pass_1.fenced_raw_output_count == 0
    assert repeat_1.fenced_raw_output_count == 0
    for report in (pass_1, repeat_1):
        assert report.attempted_runs == 8
        assert len(report.runs) == 8
        assert report.schema_valid_count == 8
        assert report.aggregate_collection_scores["entities"].ground_truth_count == 16
        assert report.aggregate_collection_scores["entities"].predicted_count == 16
    assert pass_1 is not repeat_1
    assert pass_1.aggregate_collection_scores == repeat_1.aggregate_collection_scores
    assert not (tmp_path / "pass").exists()
    assert not (tmp_path / "repeat").exists()
