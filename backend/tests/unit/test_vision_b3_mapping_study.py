from __future__ import annotations

import dataclasses
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from sketch2life.benchmark import vision_b3_mapping_study as _module
from sketch2life.benchmark.vision_b3_mapping_study import (
    B3RawOutputClassification,
    B3RawOutputCollector,
    B3RawOutputHookNotWiredError,
    B3RawOutputMode,
    NoRealP2T1PassAvailableError,
    UnexpectedFixtureCountError,
    UnsafeFixturePathError,
    UnsafeScratchDirectoryError,
    _default_fixture_builder,
    _detect_missing_required_field,
    classify_raw_output,
    run_b3_mapping_study,
)
from sketch2life.contracts.schemas.vision import (
    VisionErrorCode,
    VisionImageReferenceV1,
    VisionProhibitedClaimCategory,
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
from sketch2life.domain.understanding.media_quality import MediaDecision
from sketch2life.infrastructure.media_validation.file_inspector import inspect_image

_SOURCE_REF = VisionImageReferenceV1(artifact_ref="fixture:vision:b3:drawing.bin", sha256="a" * 64)
_EXECUTED_AT = datetime(2026, 9, 3, 12, 0, tzinfo=UTC)


def _success(**overrides: Any) -> VisionUnderstandingSuccessV2:
    profile = vision_profile_catalog_v2().profiles[0]
    values: dict[str, Any] = {
        "correlation_id": "b3-mapping-study-test",
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


def _failure(**overrides: Any) -> VisionUnderstandingFailureV2:
    profile = vision_profile_catalog_v2().profiles[0]
    values: dict[str, Any] = {
        "correlation_id": "b3-mapping-study-test",
        "executed_at": _EXECUTED_AT,
        "source_image_ref": _SOURCE_REF,
        "profile_id": profile.profile_id,
        "profile_catalog_hash": vision_profile_catalog_hash_v2(vision_profile_catalog_v2()),
        "attempt_number": 1,
        "repair_attempted": False,
        "content_policy_version": "vision-prohibited-lexicon-fixture-v1",
        "policy_match_view_version": "vision-policy-match-view-v2",
        "policy_execution_state": "NOT_EXECUTED",
        "error_code": VisionErrorCode.VISION_SCHEMA_INVALID,
        "error_detail": VisionNonPolicyErrorDetailV2.OUTPUT_MAPPING_FAILED,
        "retryable": False,
        "model_provenance": profile.model_provenance,
    }
    values.update(overrides)
    return VisionUnderstandingFailureV2(**values)


class _ScriptedAdapter:
    """A fake ``VisionUnderstandingPortV2`` wired to a caller-supplied hook.

    Mirrors how the real ``QwenVisionAdapter`` invokes ``on_raw_output`` -- once, with the raw
    string, only when a call actually reached generation -- without needing the real adapter's
    model-loading machinery.
    """

    def __init__(
        self,
        outcomes: list[VisionUnderstandingResultV2],
        raw_outputs: list[str | None],
        hook: Any,
    ) -> None:
        assert len(outcomes) == len(raw_outputs)
        self._outcomes = outcomes
        self._raw_outputs = raw_outputs
        self._hook = hook
        self.calls = 0
        self.requests: list[VisionUnderstandingRequestV2] = []

    def understand(self, request: VisionUnderstandingRequestV2) -> VisionUnderstandingResultV2:
        index = self.calls
        self.calls += 1
        self.requests.append(request)
        raw = self._raw_outputs[index]
        if raw is not None:
            self._hook(raw)
        return self._outcomes[index]


def _all_success_scripted(mode: B3RawOutputMode, capture_dir: Path | None = None) -> Any:
    collector = (
        B3RawOutputCollector(mode=mode, capture_dir=capture_dir)
        if capture_dir is not None
        else B3RawOutputCollector(mode=mode)
    )
    outcomes = [_success() for _ in range(8)]
    raw_outputs: list[str | None] = [json.dumps({}) for _ in range(8)]
    adapter = _ScriptedAdapter(outcomes, raw_outputs, collector.hook)
    return adapter, collector


# ---------------------------------------------------------------------------
# classify_raw_output
# ---------------------------------------------------------------------------


def _payload_text(payload: dict[str, object], *, fenced: bool = False) -> str:
    encoded = json.dumps(payload)
    return f"```json\n{encoded}\n```" if fenced else encoded


def _valid_text(value: str) -> dict[str, object]:
    """A fully valid ``ObservedTextV1``/``TextLanguageDeclarationV1``-shaped nested value."""

    return {
        "value": value,
        "language": {"status": "NOT_DETERMINED", "tags": [], "is_ground_truth": False},
    }


def _valid_entity(observation_id: str = "e1") -> dict[str, object]:
    return {"observation_id": observation_id, "label": _valid_text("fox"), "confidence": 0.9}


def test_plain_valid_payload_classifies_as_no_flags() -> None:
    classification = classify_raw_output(_payload_text({}))

    assert classification == B3RawOutputClassification(
        fenced=False, truncated=False, extra_key=False, invalid_enum=False
    )


def test_fenced_valid_payload_sets_only_fenced() -> None:
    classification = classify_raw_output(_payload_text({}, fenced=True))

    assert classification.fenced is True
    assert classification.truncated is False
    assert classification.extra_key is False
    assert classification.invalid_enum is False


def test_unclosed_fence_sets_both_fenced_and_truncated() -> None:
    """Flags may overlap: an opened-but-never-closed fence is fenced AND truncated."""

    raw = "```json\n" + json.dumps({"entities": []}) + "\n"  # no closing fence
    classification = classify_raw_output(raw)

    assert classification.fenced is True
    assert classification.truncated is True


def test_unbalanced_plain_json_sets_truncated() -> None:
    classification = classify_raw_output('{"entities": []')

    assert classification.truncated is True


def test_extra_top_level_key_is_flagged() -> None:
    classification = classify_raw_output(_payload_text({"entities": [], "unexpected": True}))

    assert classification.extra_key is True


def test_invalid_language_status_enum_is_flagged() -> None:
    payload = {
        "entities": [
            {
                "observation_id": "e1",
                "label": {"value": "fox", "language": {"status": "SPANISH", "tags": []}},
                "confidence": None,
            }
        ]
    }
    classification = classify_raw_output(_payload_text(payload))

    assert classification.invalid_enum is True


def test_fenced_and_extra_key_flags_overlap_on_one_run() -> None:
    classification = classify_raw_output(_payload_text({"unexpected": True}, fenced=True))

    assert classification.fenced is True
    assert classification.extra_key is True


def test_unknown_candidate_level_key_is_flagged() -> None:
    """V2 candidate objects are ``extra=\"forbid\"``; an unknown key nested inside one raw
    candidate dict must be caught, not only an unknown top-level collection key."""

    entity = {**_valid_entity(), "unexpected_candidate_field": True}
    classification = classify_raw_output(_payload_text({"entities": [entity]}))

    assert classification.extra_key is True


def test_unknown_nested_language_key_is_flagged() -> None:
    """An unknown key inside ``label.language`` (``TextLanguageDeclarationV1``) must be caught,
    two levels below the top-level collection."""

    entity = _valid_entity()
    label = entity["label"]
    assert isinstance(label, dict)
    language = label["language"]
    assert isinstance(language, dict)
    language["unexpected_language_field"] = True

    classification = classify_raw_output(_payload_text({"entities": [entity]}))

    assert classification.extra_key is True


def test_unknown_nested_text_key_is_flagged() -> None:
    """An unknown key directly on the ``ObservedTextV1``-shaped ``label`` dict itself (sibling
    of ``value``/``language``) must also be caught."""

    entity = _valid_entity()
    label = entity["label"]
    assert isinstance(label, dict)
    label["unexpected_text_field"] = True

    classification = classify_raw_output(_payload_text({"entities": [entity]}))

    assert classification.extra_key is True


def test_fully_valid_nested_payload_across_all_five_collections_is_not_flagged() -> None:
    payload = {
        "entities": [_valid_entity("e1")],
        "actions": [
            {
                "observation_id": "a1",
                "label": _valid_text("jumps"),
                "actor_ref": "e1",
                "object_ref": None,
                "confidence": None,
            }
        ],
        "relations": [
            {
                "observation_id": "r1",
                "predicate": _valid_text("near"),
                "subject_ref": "e1",
                "object_ref": "a1",
                "confidence": None,
            }
        ],
        "themes": [
            {
                "observation_id": "t1",
                "label": _valid_text("nature"),
                "evidence_refs": ["e1"],
                "confidence": None,
            }
        ],
        "ambiguous_regions": [{"observation_id": "u1", "note": _valid_text("unclear mark")}],
    }

    classification = classify_raw_output(_payload_text(payload))

    assert classification.extra_key is False
    assert classification.invalid_enum is False
    assert classification.truncated is False


def test_missing_or_wrong_type_field_is_never_treated_as_an_extra_key() -> None:
    """A missing required field, or a field of the wrong type, is not an *unknown* key."""

    missing_confidence = {"observation_id": "e1", "label": _valid_text("fox")}
    wrong_type_label = {"observation_id": "e1", "label": "not-an-object", "confidence": None}

    assert classify_raw_output(_payload_text({"entities": [missing_confidence]})).extra_key is False
    assert classify_raw_output(_payload_text({"entities": [wrong_type_label]})).extra_key is False


def test_classification_never_carries_a_missing_field_attribute() -> None:
    fields = {field.name for field in dataclasses.fields(B3RawOutputClassification)}

    assert fields == {"fenced", "truncated", "extra_key", "invalid_enum"}
    assert not hasattr(classify_raw_output(_payload_text({})), "missing_field")
    assert not hasattr(classify_raw_output(_payload_text({})), "missing_required_field")


def test_missing_required_field_helper_is_directly_testable_but_never_wired_in() -> None:
    incomplete = {"entities": [{"observation_id": "e1", "label": {}}]}
    complete = {"entities": [{"observation_id": "e1", "label": {}, "confidence": None}]}

    assert _detect_missing_required_field(incomplete) is True
    assert _detect_missing_required_field(complete) is False


# ---------------------------------------------------------------------------
# B3RawOutputCollector
# ---------------------------------------------------------------------------


def test_classify_only_mode_never_writes_a_capture_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    collector = B3RawOutputCollector(
        mode=B3RawOutputMode.CLASSIFY_ONLY, capture_dir=Path("capture")
    )

    collector.hook(json.dumps({"entities": []}))

    assert not (tmp_path / "capture").exists()
    assert collector.take_latest() is not None


def test_ephemeral_capture_mode_deletes_the_file_after_classification(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    collector = B3RawOutputCollector(
        mode=B3RawOutputMode.EPHEMERAL_CAPTURE, capture_dir=Path("capture")
    )

    collector.hook(json.dumps({"entities": []}))

    assert not (tmp_path / "capture" / "b3-raw-output.txt").exists()
    assert collector.take_latest() is not None


def test_ephemeral_capture_mode_deletes_the_file_even_when_classification_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    collector = B3RawOutputCollector(
        mode=B3RawOutputMode.EPHEMERAL_CAPTURE, capture_dir=Path("capture")
    )

    def _raise(_raw_output: str) -> B3RawOutputClassification:
        raise RuntimeError("classifier boom")

    monkeypatch.setattr(_module, "classify_raw_output", _raise)

    with pytest.raises(RuntimeError, match="classifier boom"):
        collector.hook("anything")

    assert not (tmp_path / "capture" / "b3-raw-output.txt").exists()


def test_take_latest_clears_state_so_stale_classification_cannot_leak() -> None:
    collector = B3RawOutputCollector()
    collector.hook(json.dumps({"entities": []}))

    first = collector.take_latest()
    second = collector.take_latest()

    assert first is not None
    assert second is None


# ---------------------------------------------------------------------------
# fixture generation
# ---------------------------------------------------------------------------


def test_default_fixture_builder_writes_eight_distinct_geometric_images(
    tmp_path: Path,
) -> None:
    image_paths, audio_path = _default_fixture_builder(tmp_path / "scratch")

    assert len(image_paths) == 8
    payloads = {path.read_bytes() for path in image_paths}
    assert len(payloads) == 8, "all eight recipes must be distinct"
    assert audio_path.exists()


def test_every_b3_fixture_image_earns_a_real_p2t1_pass(tmp_path: Path) -> None:
    from sketch2life.application.services.media_validation import (
        DeterministicMediaValidator,
        MediaValidationRequest,
    )
    from sketch2life.infrastructure.media_validation.file_inspector import (
        FileMediaSignalInspector,
    )

    image_paths, audio_path = _default_fixture_builder(tmp_path / "scratch")
    validator = DeterministicMediaValidator(FileMediaSignalInspector())

    for index, image_path in enumerate(image_paths):
        result = validator.validate(
            MediaValidationRequest(
                image_path=image_path,
                audio_path=audio_path,
                image_artifact_ref=f"b3-fixture-{index}",
                audio_artifact_ref="b3-audio",
            )
        )
        assert result.decision is MediaDecision.PASS, (index, result)
        # Sanity: this is really a synthetic geometric image, not a blank canvas.
        signals = inspect_image(image_path)
        assert signals.width == 160
        assert signals.height == 160


# ---------------------------------------------------------------------------
# run_b3_mapping_study
# ---------------------------------------------------------------------------


def test_run_calls_the_adapter_exactly_once_for_each_of_eight_fixtures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    adapter, collector = _all_success_scripted(B3RawOutputMode.CLASSIFY_ONLY)

    report = run_b3_mapping_study(
        adapter, collector, fixtures_dir=Path("scratch"), sample_vram=False
    )

    assert adapter.calls == 8
    assert len(report.runs) == 8
    assert report.attempted_runs == 8
    assert report.schema_valid_count == 8


def test_no_retry_on_repeated_mapping_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    collector = B3RawOutputCollector(mode=B3RawOutputMode.CLASSIFY_ONLY)
    outcomes: list[VisionUnderstandingResultV2] = [_failure() for _ in range(8)]
    raw_outputs: list[str | None] = ['{"entities": []' for _ in range(8)]
    adapter = _ScriptedAdapter(outcomes, raw_outputs, collector.hook)

    report = run_b3_mapping_study(
        adapter, collector, fixtures_dir=Path("scratch"), sample_vram=False
    )

    assert adapter.calls == 8
    assert report.schema_valid_count == 0
    assert report.typed_failure_counts == {"OUTPUT_MAPPING_FAILED": 8}
    assert report.truncated_count == 8


def test_classification_flags_overlap_and_denominator_is_attempted_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    collector = B3RawOutputCollector(mode=B3RawOutputMode.CLASSIFY_ONLY)
    never_reached_generation = _failure(
        error_code=VisionErrorCode.VISION_MODEL_UNAVAILABLE,
        error_detail=VisionNonPolicyErrorDetailV2.MODEL_LOAD_FAILED,
        attempt_number=1,
        retryable=False,
        repair_attempted=False,
    )
    outcomes: list[VisionUnderstandingResultV2] = [
        _success(),
        _success(),
        *[never_reached_generation for _ in range(6)],
    ]
    raw_outputs: list[str | None] = [
        _payload_text({"unexpected": True}, fenced=True),  # fenced + extra_key
        _payload_text({}),  # clean
        None,  # never reached generation (MODEL_LOAD_FAILED)
        None,
        None,
        None,
        None,
        None,
    ]
    adapter = _ScriptedAdapter(outcomes, raw_outputs, collector.hook)

    report = run_b3_mapping_study(
        adapter, collector, fixtures_dir=Path("scratch"), sample_vram=False
    )

    assert report.attempted_runs == 8
    assert report.fenced_count == 1
    assert report.extra_key_count == 1
    assert report.runs[0].fenced is True
    assert report.runs[0].extra_key is True
    assert report.runs[1].fenced is False
    for run in report.runs[2:]:
        assert run.fenced is None
        assert run.truncated is None
        assert run.extra_key is None
        assert run.invalid_enum is None


def test_report_never_carries_the_raw_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    marker = "UNMISTAKABLE_RAW_MARKER_STRING"
    collector = B3RawOutputCollector(mode=B3RawOutputMode.CLASSIFY_ONLY)
    outcomes: list[VisionUnderstandingResultV2] = [_success() for _ in range(8)]
    raw_outputs: list[str | None] = [
        _payload_text({"note_marker": marker}) for _ in range(8)
    ]
    adapter = _ScriptedAdapter(outcomes, raw_outputs, collector.hook)

    report = run_b3_mapping_study(
        adapter, collector, fixtures_dir=Path("scratch"), sample_vram=False
    )

    serialized = json.dumps(dataclasses.asdict(report), default=str)
    assert marker not in serialized


def test_known_policy_trigger_rate_is_always_not_applicable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    adapter, collector = _all_success_scripted(B3RawOutputMode.CLASSIFY_ONLY)

    report = run_b3_mapping_study(
        adapter, collector, fixtures_dir=Path("scratch"), sample_vram=False
    )

    assert report.known_policy_trigger_rate == "NOT_APPLICABLE"


def test_fixtures_are_deleted_after_a_successful_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    adapter, collector = _all_success_scripted(B3RawOutputMode.CLASSIFY_ONLY)

    run_b3_mapping_study(adapter, collector, fixtures_dir=Path("scratch"), sample_vram=False)

    assert not (tmp_path / "scratch").exists()


def test_fixtures_and_capture_dir_are_deleted_even_when_the_adapter_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    collector = B3RawOutputCollector(
        mode=B3RawOutputMode.EPHEMERAL_CAPTURE, capture_dir=Path("capture")
    )

    class _RaisingAdapter:
        def understand(
            self, request: VisionUnderstandingRequestV2
        ) -> VisionUnderstandingResultV2:
            collector.hook(json.dumps({"entities": []}))
            raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        run_b3_mapping_study(
            _RaisingAdapter(), collector, fixtures_dir=Path("scratch"), sample_vram=False
        )

    assert not (tmp_path / "scratch").exists()
    assert not (tmp_path / "capture").exists()


def test_ephemeral_capture_end_to_end_run_deletes_capture_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    adapter, collector = _all_success_scripted(
        B3RawOutputMode.EPHEMERAL_CAPTURE, capture_dir=Path("capture")
    )

    report = run_b3_mapping_study(
        adapter, collector, fixtures_dir=Path("scratch"), sample_vram=False
    )

    assert report.raw_output_mode == "EPHEMERAL_CAPTURE"
    assert not (tmp_path / "capture").exists()


def test_no_real_p2t1_pass_available_refuses_to_call_the_adapter(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    adapter, collector = _all_success_scripted(B3RawOutputMode.CLASSIFY_ONLY)

    def _build_bad_fixtures(fixtures_dir: Path) -> tuple[tuple[Path, ...], Path]:
        from struct import pack
        from wave import open as wave_open

        fixtures_dir.mkdir(parents=True, exist_ok=True)
        image_paths = tuple(
            fixtures_dir / f"b3-fixture-{index + 1:02d}.png" for index in range(8)
        )
        for image_path in image_paths:
            _module._write_b3_fixture_image(image_path, 0)
        audio_path = fixtures_dir / "b3-companion.wav"
        with wave_open(str(audio_path), "wb") as output:
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(16000)
            output.writeframes(pack("<h", 0) * 3200)
        return image_paths, audio_path

    with pytest.raises(NoRealP2T1PassAvailableError):
        run_b3_mapping_study(
            adapter,
            collector,
            fixtures_dir=Path("scratch"),
            sample_vram=False,
            build_fixtures=_build_bad_fixtures,
        )

    assert adapter.calls == 0


def test_absolute_fixtures_dir_is_rejected_before_any_fixture_is_written(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    adapter, collector = _all_success_scripted(B3RawOutputMode.CLASSIFY_ONLY)
    unsafe_dir = tmp_path / "elsewhere" / "scratch"

    with pytest.raises(UnsafeScratchDirectoryError):
        run_b3_mapping_study(adapter, collector, fixtures_dir=unsafe_dir, sample_vram=False)

    assert adapter.calls == 0
    assert not unsafe_dir.exists()


def test_fixtures_dir_that_escapes_cwd_via_dotdot_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "workdir").mkdir()
    monkeypatch.chdir(tmp_path / "workdir")
    adapter, collector = _all_success_scripted(B3RawOutputMode.CLASSIFY_ONLY)

    with pytest.raises(UnsafeScratchDirectoryError):
        run_b3_mapping_study(
            adapter, collector, fixtures_dir=Path("../sibling-scratch"), sample_vram=False
        )

    assert adapter.calls == 0
    assert not (tmp_path / "sibling-scratch").exists()


def test_capture_dir_escaping_cwd_is_rejected_at_collector_construction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    unsafe_dir = tmp_path / "elsewhere" / "capture"

    with pytest.raises(UnsafeScratchDirectoryError):
        B3RawOutputCollector(mode=B3RawOutputMode.EPHEMERAL_CAPTURE, capture_dir=unsafe_dir)


def test_builder_returning_a_non_file_path_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    adapter, collector = _all_success_scripted(B3RawOutputMode.CLASSIFY_ONLY)

    def _build_missing(fixtures_dir: Path) -> tuple[tuple[Path, ...], Path]:
        fixtures_dir.mkdir(parents=True, exist_ok=True)
        missing = tuple(fixtures_dir / f"never-written-{i}.png" for i in range(8))
        audio_path = fixtures_dir / "audio.wav"
        _module._write_b3_companion_audio(audio_path)
        return missing, audio_path

    with pytest.raises(UnsafeFixturePathError):
        run_b3_mapping_study(
            adapter,
            collector,
            fixtures_dir=Path("scratch"),
            sample_vram=False,
            build_fixtures=_build_missing,
        )

    assert adapter.calls == 0


# ---------------------------------------------------------------------------
# Fix 1 — exact fixture-count invariant
# ---------------------------------------------------------------------------


def _build_n_fixtures(fixtures_dir: Path, count: int) -> tuple[tuple[Path, ...], Path]:
    fixtures_dir.mkdir(parents=True, exist_ok=True)
    image_paths = tuple(
        fixtures_dir / f"b3-fixture-{index + 1:02d}.png" for index in range(count)
    )
    for index, image_path in enumerate(image_paths):
        _module._write_b3_fixture_image(image_path, index % 8)
    audio_path = fixtures_dir / "b3-companion.wav"
    _module._write_b3_companion_audio(audio_path)
    return image_paths, audio_path


def test_fewer_than_eight_fixture_paths_is_rejected_before_any_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    adapter, collector = _all_success_scripted(B3RawOutputMode.CLASSIFY_ONLY)

    with pytest.raises(UnexpectedFixtureCountError):
        run_b3_mapping_study(
            adapter,
            collector,
            fixtures_dir=Path("scratch"),
            sample_vram=False,
            build_fixtures=lambda fixtures_dir: _build_n_fixtures(fixtures_dir, 7),
        )

    assert adapter.calls == 0
    assert not (tmp_path / "scratch").exists()


def test_more_than_eight_fixture_paths_is_rejected_before_any_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    adapter, collector = _all_success_scripted(B3RawOutputMode.CLASSIFY_ONLY)

    with pytest.raises(UnexpectedFixtureCountError):
        run_b3_mapping_study(
            adapter,
            collector,
            fixtures_dir=Path("scratch"),
            sample_vram=False,
            build_fixtures=lambda fixtures_dir: _build_n_fixtures(fixtures_dir, 9),
        )

    assert adapter.calls == 0
    assert not (tmp_path / "scratch").exists()


def test_wrong_fixture_count_cleans_up_capture_dir_too(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    adapter, collector = _all_success_scripted(
        B3RawOutputMode.EPHEMERAL_CAPTURE, capture_dir=Path("capture")
    )

    with pytest.raises(UnexpectedFixtureCountError):
        run_b3_mapping_study(
            adapter,
            collector,
            fixtures_dir=Path("scratch"),
            sample_vram=False,
            build_fixtures=lambda fixtures_dir: _build_n_fixtures(fixtures_dir, 3),
        )

    assert adapter.calls == 0
    assert not (tmp_path / "scratch").exists()
    assert not (tmp_path / "capture").exists()


# ---------------------------------------------------------------------------
# Fix 2 — fail closed if the raw hook is not wired
# ---------------------------------------------------------------------------


def test_missing_classification_for_a_success_result_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Simulates the adapter being built without ``on_raw_output=collector.hook``."""

    monkeypatch.chdir(tmp_path)
    collector = B3RawOutputCollector(mode=B3RawOutputMode.CLASSIFY_ONLY)
    outcomes: list[VisionUnderstandingResultV2] = [_success() for _ in range(8)]
    raw_outputs: list[str | None] = [None for _ in range(8)]  # hook never invoked
    adapter = _ScriptedAdapter(outcomes, raw_outputs, collector.hook)

    with pytest.raises(B3RawOutputHookNotWiredError):
        run_b3_mapping_study(
            adapter, collector, fixtures_dir=Path("scratch"), sample_vram=False
        )

    assert adapter.calls == 1
    assert not (tmp_path / "scratch").exists()


def test_missing_classification_for_a_schema_invalid_mapping_failure_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    collector = B3RawOutputCollector(mode=B3RawOutputMode.CLASSIFY_ONLY)
    outcomes: list[VisionUnderstandingResultV2] = [_failure() for _ in range(8)]
    raw_outputs: list[str | None] = [None for _ in range(8)]
    adapter = _ScriptedAdapter(outcomes, raw_outputs, collector.hook)

    with pytest.raises(B3RawOutputHookNotWiredError):
        run_b3_mapping_study(
            adapter, collector, fixtures_dir=Path("scratch"), sample_vram=False
        )

    assert adapter.calls == 1
    assert not (tmp_path / "scratch").exists()


def test_missing_classification_for_a_legitimately_raw_output_free_failure_is_allowed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """INPUT_NOT_VALIDATED / model-unavailable / timeout / provider failure never reach
    generation, so having no classification for them must never fail closed."""

    monkeypatch.chdir(tmp_path)
    collector = B3RawOutputCollector(mode=B3RawOutputMode.CLASSIFY_ONLY)
    never_reached_generation = _failure(
        error_code=VisionErrorCode.VISION_MODEL_UNAVAILABLE,
        error_detail=VisionNonPolicyErrorDetailV2.MODEL_LOAD_FAILED,
        attempt_number=1,
        retryable=False,
        repair_attempted=False,
    )
    outcomes: list[VisionUnderstandingResultV2] = [never_reached_generation for _ in range(8)]
    raw_outputs: list[str | None] = [None for _ in range(8)]
    adapter = _ScriptedAdapter(outcomes, raw_outputs, collector.hook)

    report = run_b3_mapping_study(
        adapter, collector, fixtures_dir=Path("scratch"), sample_vram=False
    )

    assert adapter.calls == 8
    assert report.attempted_runs == 8
    assert all(run.fenced is None for run in report.runs)


def test_missing_classification_failure_still_cleans_up_ephemeral_capture_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    collector = B3RawOutputCollector(
        mode=B3RawOutputMode.EPHEMERAL_CAPTURE, capture_dir=Path("capture")
    )
    outcomes: list[VisionUnderstandingResultV2] = [_success() for _ in range(8)]
    raw_outputs: list[str | None] = [None for _ in range(8)]
    adapter = _ScriptedAdapter(outcomes, raw_outputs, collector.hook)

    with pytest.raises(B3RawOutputHookNotWiredError):
        run_b3_mapping_study(
            adapter, collector, fixtures_dir=Path("scratch"), sample_vram=False
        )

    assert not (tmp_path / "scratch").exists()
    assert not (tmp_path / "capture").exists()


def test_missing_classification_for_a_prohibited_claim_result_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    collector = B3RawOutputCollector(mode=B3RawOutputMode.CLASSIFY_ONLY)
    prohibited = _failure(
        error_code=VisionErrorCode.PROHIBITED_CLAIM_DETECTED,
        error_detail=VisionProhibitedClaimCategory.PSYCHOLOGICAL_INFERENCE_CLAIM,
        policy_execution_state="BLOCKED",
        attempt_number=1,
        retryable=False,
        repair_attempted=False,
    )
    outcomes: list[VisionUnderstandingResultV2] = [prohibited for _ in range(8)]
    raw_outputs: list[str | None] = [None for _ in range(8)]
    adapter = _ScriptedAdapter(outcomes, raw_outputs, collector.hook)

    with pytest.raises(B3RawOutputHookNotWiredError):
        run_b3_mapping_study(
            adapter, collector, fixtures_dir=Path("scratch"), sample_vram=False
        )

    assert adapter.calls == 1
    assert not (tmp_path / "scratch").exists()


def test_missing_classification_for_a_duplicate_observation_id_result_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    collector = B3RawOutputCollector(mode=B3RawOutputMode.CLASSIFY_ONLY)
    duplicate_id = _failure(
        error_code=VisionErrorCode.VISION_SCHEMA_INVALID,
        error_detail=VisionNonPolicyErrorDetailV2.DUPLICATE_OBSERVATION_ID,
        attempt_number=1,
        retryable=False,
        repair_attempted=False,
    )
    outcomes: list[VisionUnderstandingResultV2] = [duplicate_id for _ in range(8)]
    raw_outputs: list[str | None] = [None for _ in range(8)]
    adapter = _ScriptedAdapter(outcomes, raw_outputs, collector.hook)

    with pytest.raises(B3RawOutputHookNotWiredError):
        run_b3_mapping_study(
            adapter, collector, fixtures_dir=Path("scratch"), sample_vram=False
        )

    assert adapter.calls == 1
    assert not (tmp_path / "scratch").exists()


def test_missing_classification_for_a_reference_integrity_violation_result_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    collector = B3RawOutputCollector(
        mode=B3RawOutputMode.EPHEMERAL_CAPTURE, capture_dir=Path("capture")
    )
    reference_violation = _failure(
        error_code=VisionErrorCode.VISION_SCHEMA_INVALID,
        error_detail=VisionNonPolicyErrorDetailV2.REFERENCE_INTEGRITY_VIOLATION,
        attempt_number=1,
        retryable=False,
        repair_attempted=False,
    )
    outcomes: list[VisionUnderstandingResultV2] = [reference_violation for _ in range(8)]
    raw_outputs: list[str | None] = [None for _ in range(8)]
    adapter = _ScriptedAdapter(outcomes, raw_outputs, collector.hook)

    with pytest.raises(B3RawOutputHookNotWiredError):
        run_b3_mapping_study(
            adapter, collector, fixtures_dir=Path("scratch"), sample_vram=False
        )

    assert adapter.calls == 1
    assert not (tmp_path / "scratch").exists()
    assert not (tmp_path / "capture").exists()
