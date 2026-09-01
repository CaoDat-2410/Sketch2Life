from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any, cast

import pytest

from sketch2life.contracts.schemas.vision import (
    ImageDerivationProvenanceV1,
    VisionErrorCode,
    VisionImageReferenceV1,
    VisionMediaValidationProvenanceV1,
    VisionProhibitedClaimCategory,
)
from sketch2life.contracts.schemas.vision_v2 import (
    VisionNonPolicyErrorDetailV2,
    VisionProfileCatalogV2,
    VisionProfileV2,
    VisionUnderstandingFailureV2,
    VisionUnderstandingRequestV2,
    VisionUnderstandingSuccessV2,
    vision_profile_catalog_hash_v2,
    vision_profile_catalog_v2,
)
from sketch2life.infrastructure.ai import qwen_vision
from sketch2life.infrastructure.ai.qwen_vision import (
    QwenDeviceUnavailableError,
    QwenModelBundle,
    QwenPermanentRuntimeError,
    QwenTimeoutError,
    QwenTransientRuntimeError,
    QwenVisionAdapter,
    TransformersQwenGenerationRunner,
)
from sketch2life.infrastructure.ai.qwen_vision_runtime_config import (
    QwenVisionRuntimeConfig,
)
from sketch2life.infrastructure.ai.vision_lexical_policy import (
    LexicalRegressionContentPolicy,
    synthetic_prohibited_lexicon,
)

_IMAGE_BYTES = b"synthetic-qwen-vision-b1-image"


class _SequenceRunner:
    def __init__(self, *outcomes: object) -> None:
        self.outcomes = list(outcomes)
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
        if not self.outcomes:
            raise AssertionError("test runner was called more times than expected")
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return cast(str, outcome)


def _policy() -> LexicalRegressionContentPolicy:
    return LexicalRegressionContentPolicy(synthetic_prohibited_lexicon())


def _empty_payload() -> dict[str, object]:
    return {
        "entities": [],
        "actions": [],
        "relations": [],
        "themes": [],
        "ambiguous_regions": [],
    }


def _text(value: str) -> dict[str, object]:
    return {"value": value, "language": {"status": "NOT_DETERMINED", "tags": []}}


def _raw(payload: object, *, fenced: bool = False) -> str:
    encoded = json.dumps(payload)
    return f"```json\n{encoded}\n```" if fenced else encoded


_TRUNCATED_FENCED = "```json\n" + json.dumps(_empty_payload()) + "\n"


def _pass_validation() -> VisionMediaValidationProvenanceV1:
    return VisionMediaValidationProvenanceV1(
        validation_artifact_ref="fixture:vision:b1:validation-pass",
        validation_artifact_sha256="c" * 64,
        decision="PASS",
        validator_policy_version="media-quality-policy-v1",
    )


_DEFAULT_MEDIA_VALIDATION = _pass_validation()


def _recapture_validation() -> VisionMediaValidationProvenanceV1:
    return VisionMediaValidationProvenanceV1(
        validation_artifact_ref="fixture:vision:b1:validation-recapture",
        validation_artifact_sha256="d" * 64,
        decision="RECAPTURE",
        validator_policy_version="media-quality-policy-v1",
    )


def _request(
    artifact_ref: str,
    digest: str,
    *,
    media_validation: VisionMediaValidationProvenanceV1 | None = _DEFAULT_MEDIA_VALIDATION,
    processing_image_ref: VisionImageReferenceV1 | None = None,
    derivation_provenance: ImageDerivationProvenanceV1 | None = None,
) -> VisionUnderstandingRequestV2:
    return VisionUnderstandingRequestV2(
        correlation_id="qwen-vision-b1-adapter-test",
        source_image_ref=VisionImageReferenceV1(artifact_ref=artifact_ref, sha256=digest),
        processing_image_ref=processing_image_ref,
        derivation_provenance=derivation_provenance,
        media_validation=media_validation,
        requested_profile_id=vision_profile_catalog_v2().profiles[0].profile_id,
    )


def _adapter(
    runner: _SequenceRunner | None = None,
    *,
    model_factory: Any = None,
    prompt: str = "",
) -> QwenVisionAdapter:
    return QwenVisionAdapter(
        QwenVisionRuntimeConfig(model_dir=Path("local-model")),
        content_policy=_policy(),
        prompt=prompt,
        generation_runner=runner,
        model_factory=model_factory,
    )


def _write_source(tmp_path: Path) -> tuple[str, str]:
    path = tmp_path / "drawing.bin"
    path.write_bytes(_IMAGE_BYTES)
    return path.name, sha256(_IMAGE_BYTES).hexdigest()


def test_adapter_success_validates_source_before_generation_and_emits_v2_provenance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    artifact_ref, digest = _write_source(tmp_path)
    runner = _SequenceRunner(_raw(_empty_payload()))

    result = _adapter(runner).understand(_request(artifact_ref, digest))

    assert isinstance(result, VisionUnderstandingSuccessV2)
    assert result.attempt_number == 1
    assert result.policy_execution_state == "PASSED"
    assert result.model_provenance is not None
    assert runner.calls == 1


def test_complete_json_fence_is_the_only_repair_and_preserves_valid_content(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    artifact_ref, digest = _write_source(tmp_path)
    result = _adapter(_SequenceRunner(_raw(_empty_payload(), fenced=True))).understand(
        _request(artifact_ref, digest)
    )

    assert isinstance(result, VisionUnderstandingSuccessV2)
    assert result.repair_attempted is True


@pytest.mark.parametrize(
    "raw_output",
    (
        _TRUNCATED_FENCED,
        '{"entities": []',
    ),
)
def test_truncated_fence_or_json_never_sets_repair_attempted(
    raw_output: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    artifact_ref, digest = _write_source(tmp_path)
    result = _adapter(_SequenceRunner(raw_output)).understand(_request(artifact_ref, digest))

    assert isinstance(result, VisionUnderstandingFailureV2)
    assert result.error_code is VisionErrorCode.VISION_SCHEMA_INVALID
    assert result.error_detail is VisionNonPolicyErrorDetailV2.OUTPUT_MAPPING_FAILED
    assert result.repair_attempted is False


@pytest.mark.parametrize("json_root", ("[]", "42", "null"))
def test_fenced_non_object_json_is_schema_failure_without_repair(
    json_root: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    artifact_ref, digest = _write_source(tmp_path)
    raw_output = f"```json\n{json_root}\n```"

    result = _adapter(_SequenceRunner(raw_output)).understand(_request(artifact_ref, digest))

    assert isinstance(result, VisionUnderstandingFailureV2)
    assert result.error_code is VisionErrorCode.VISION_SCHEMA_INVALID
    assert result.error_detail is VisionNonPolicyErrorDetailV2.OUTPUT_MAPPING_FAILED
    assert result.repair_attempted is False
    assert raw_output not in result.model_dump_json()


def test_complete_fenced_schema_invalid_output_records_repair_without_salvage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    artifact_ref, digest = _write_source(tmp_path)
    invalid_payload = {**_empty_payload(), "unexpected": "no passthrough"}

    result = _adapter(_SequenceRunner(_raw(invalid_payload, fenced=True))).understand(
        _request(artifact_ref, digest)
    )

    assert isinstance(result, VisionUnderstandingFailureV2)
    assert result.error_detail is VisionNonPolicyErrorDetailV2.OUTPUT_MAPPING_FAILED
    assert result.repair_attempted is True


@pytest.mark.parametrize(
    "payload",
    (
        {"entities": [], "actions": [], "relations": [], "themes": []},
        {
            **_empty_payload(),
            "entities": [
                {
                    "observation_id": "entity-a",
                    "label": _text("a fox"),
                    "confidence": None,
                    "unknown_candidate_field": "rejected",
                }
            ],
        },
    ),
)
def test_missing_or_nested_extra_fields_map_to_typed_schema_failure(
    payload: dict[str, object], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    artifact_ref, digest = _write_source(tmp_path)
    result = _adapter(_SequenceRunner(_raw(payload))).understand(_request(artifact_ref, digest))

    assert isinstance(result, VisionUnderstandingFailureV2)
    assert result.error_detail is VisionNonPolicyErrorDetailV2.OUTPUT_MAPPING_FAILED
    assert result.repair_attempted is False


def test_duplicate_and_reference_errors_have_distinct_typed_details(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    artifact_ref, digest = _write_source(tmp_path)
    duplicate = {
        **_empty_payload(),
        "entities": [
            {"observation_id": "same-id", "label": _text("fox"), "confidence": None}
        ],
        "themes": [
            {
                "observation_id": "same-id",
                "label": _text("nature"),
                "evidence_refs": ["same-id"],
                "confidence": None,
            }
        ],
    }
    reference = {
        **_empty_payload(),
        "relations": [
            {
                "observation_id": "relation-a",
                "predicate": _text("near"),
                "subject_ref": "missing-id",
                "object_ref": "missing-id",
                "confidence": None,
            }
        ],
    }

    duplicate_result = _adapter(_SequenceRunner(_raw(duplicate))).understand(
        _request(artifact_ref, digest)
    )
    reference_result = _adapter(_SequenceRunner(_raw(reference))).understand(
        _request(artifact_ref, digest)
    )

    assert isinstance(duplicate_result, VisionUnderstandingFailureV2)
    assert duplicate_result.error_detail is VisionNonPolicyErrorDetailV2.DUPLICATE_OBSERVATION_ID
    assert isinstance(reference_result, VisionUnderstandingFailureV2)
    assert (
        reference_result.error_detail
        is VisionNonPolicyErrorDetailV2.REFERENCE_INTEGRITY_VIOLATION
    )


def test_policy_block_is_structural_and_does_not_leak_raw_observed_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    artifact_ref, digest = _write_source(tmp_path)
    marker = "synthetic personality claim marker"
    payload = {
        **_empty_payload(),
        "entities": [
            {"observation_id": "entity-a", "label": _text(marker), "confidence": None}
        ],
    }

    result = _adapter(_SequenceRunner(_raw(payload))).understand(_request(artifact_ref, digest))

    assert isinstance(result, VisionUnderstandingFailureV2)
    assert result.error_code is VisionErrorCode.PROHIBITED_CLAIM_DETECTED
    assert result.error_detail is VisionProhibitedClaimCategory.PERSONALITY_CLAIM
    assert result.policy_execution_state == "BLOCKED"
    assert marker not in result.model_dump_json()


@pytest.mark.parametrize("validation", (None, _recapture_validation()))
def test_p2_t1_media_validation_gate_runs_before_any_generation(
    validation: VisionMediaValidationProvenanceV1 | None,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    artifact_ref, digest = _write_source(tmp_path)
    runner = _SequenceRunner(_raw(_empty_payload()))

    result = _adapter(runner).understand(
        _request(artifact_ref, digest, media_validation=validation)
    )

    assert isinstance(result, VisionUnderstandingFailureV2)
    assert result.error_code is VisionErrorCode.INPUT_NOT_VALIDATED
    assert result.attempt_number == 0
    assert result.model_provenance is None
    assert runner.calls == 0


@pytest.mark.parametrize(
    ("artifact_ref", "digest", "detail"),
    (
        ("missing.bin", "a" * 64, VisionNonPolicyErrorDetailV2.SOURCE_IMAGE_UNREADABLE),
        ("drawing.bin", "b" * 64, VisionNonPolicyErrorDetailV2.SOURCE_IMAGE_HASH_MISMATCH),
    ),
)
def test_source_integrity_failures_are_typed_and_pre_inference(
    artifact_ref: str,
    digest: str,
    detail: VisionNonPolicyErrorDetailV2,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    _write_source(tmp_path)
    runner = _SequenceRunner(_raw(_empty_payload()))

    result = _adapter(runner).understand(_request(artifact_ref, digest))

    assert isinstance(result, VisionUnderstandingFailureV2)
    assert result.error_detail is detail
    assert result.attempt_number == 0
    assert runner.calls == 0


def test_processing_image_hash_is_verified_when_a_derived_image_is_selected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    source_ref, source_digest = _write_source(tmp_path)
    processed_path = tmp_path / "processed.bin"
    processed_bytes = b"processed-image"
    processed_path.write_bytes(processed_bytes)
    processed_digest = sha256(processed_bytes).hexdigest()
    processed_ref = VisionImageReferenceV1(
        artifact_ref=processed_path.name,
        sha256=processed_digest,
    )
    provenance = ImageDerivationProvenanceV1(
        transform_name="fixture-transform",
        transform_config_version="fixture-transform-v1",
        source_image_sha256=source_digest,
        processing_image_sha256=processed_digest,
    )
    runner = _SequenceRunner(_raw(_empty_payload()))

    result = _adapter(runner).understand(
        _request(
            source_ref,
            source_digest,
            processing_image_ref=processed_ref,
            derivation_provenance=provenance,
        )
    )

    assert isinstance(result, VisionUnderstandingSuccessV2)
    assert runner.calls == 1


def test_adapter_resolve_miss_is_typed_input_failure_at_attempt_zero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    artifact_ref, digest = _write_source(tmp_path)
    runner = _SequenceRunner(_raw(_empty_payload()))
    incomplete_catalog = VisionProfileCatalogV2(profiles=())
    request = _request(artifact_ref, digest)
    monkeypatch.setattr(qwen_vision, "vision_profile_catalog_v2", lambda: incomplete_catalog)

    result = _adapter(runner).understand(request)

    assert isinstance(result, VisionUnderstandingFailureV2)
    assert result.error_code is VisionErrorCode.INPUT_NOT_VALIDATED
    assert result.error_detail is VisionNonPolicyErrorDetailV2.PROFILE_NOT_RESOLVABLE
    assert result.profile_catalog_hash == vision_profile_catalog_hash_v2(incomplete_catalog)
    assert result.model_provenance is None
    assert runner.calls == 0


def test_missing_optional_runtime_is_a_sanitized_model_unavailable_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    artifact_ref, digest = _write_source(tmp_path)

    def missing_factory(
        profile: VisionProfileV2, config: QwenVisionRuntimeConfig
    ) -> QwenModelBundle:
        del profile, config
        raise ModuleNotFoundError("transformers PRIVATE_MODEL_PATH")

    result = _adapter(model_factory=missing_factory).understand(_request(artifact_ref, digest))

    assert isinstance(result, VisionUnderstandingFailureV2)
    assert result.error_code is VisionErrorCode.VISION_MODEL_UNAVAILABLE
    assert result.error_detail is VisionNonPolicyErrorDetailV2.MODEL_LOAD_FAILED
    assert result.model_provenance is not None
    assert "PRIVATE_MODEL_PATH" not in result.model_dump_json()


def test_unavailable_device_is_a_sanitized_typed_model_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    artifact_ref, digest = _write_source(tmp_path)

    def unavailable_device_factory(
        profile: VisionProfileV2, config: QwenVisionRuntimeConfig
    ) -> QwenModelBundle:
        del profile, config
        raise QwenDeviceUnavailableError("PRIVATE_DEVICE_DETAIL")

    result = _adapter(model_factory=unavailable_device_factory).understand(
        _request(artifact_ref, digest)
    )

    assert isinstance(result, VisionUnderstandingFailureV2)
    assert result.error_code is VisionErrorCode.VISION_MODEL_UNAVAILABLE
    assert result.error_detail is VisionNonPolicyErrorDetailV2.DEVICE_UNAVAILABLE
    assert result.model_provenance is not None
    assert "PRIVATE_DEVICE_DETAIL" not in result.model_dump_json()


def test_provider_exception_text_never_crosses_the_v2_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    artifact_ref, digest = _write_source(tmp_path)
    secret = "PRIVATE_RAW_PROVIDER_EXCEPTION"

    result = _adapter(_SequenceRunner(RuntimeError(secret))).understand(
        _request(artifact_ref, digest)
    )

    assert isinstance(result, VisionUnderstandingFailureV2)
    assert result.error_detail is VisionNonPolicyErrorDetailV2.PERMANENT_RUNTIME_FAILURE
    assert secret not in result.model_dump_json()
    assert secret not in str(result)


def test_raw_transient_exception_can_use_the_injected_sanitized_classifier(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    artifact_ref, digest = _write_source(tmp_path)
    runner = _SequenceRunner(RuntimeError("PRIVATE_TRANSIENT"), _raw(_empty_payload()))
    adapter = QwenVisionAdapter(
        QwenVisionRuntimeConfig(model_dir=Path("local-model")),
        content_policy=_policy(),
        prompt="",
        generation_runner=runner,
        classify_transient=lambda _exc: True,
    )

    result = adapter.understand(_request(artifact_ref, digest))

    assert isinstance(result, VisionUnderstandingSuccessV2)
    assert result.attempt_number == 2
    assert runner.calls == 2


def test_transient_retry_trace_timeout_and_permanent_failure_are_typed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    artifact_ref, digest = _write_source(tmp_path)

    timeout_runner = _SequenceRunner(QwenTransientRuntimeError(), QwenTimeoutError())
    timeout_result = _adapter(timeout_runner).understand(_request(artifact_ref, digest))
    permanent_runner = _SequenceRunner(QwenTransientRuntimeError(), QwenPermanentRuntimeError())
    permanent_result = _adapter(permanent_runner).understand(_request(artifact_ref, digest))

    assert isinstance(timeout_result, VisionUnderstandingFailureV2)
    assert timeout_result.error_code is VisionErrorCode.VISION_TIMEOUT
    assert timeout_result.attempt_number == 2
    assert timeout_result.retryable is False
    assert isinstance(permanent_result, VisionUnderstandingFailureV2)
    assert permanent_result.error_code is VisionErrorCode.VISION_PROVIDER_FAILURE
    assert permanent_result.error_detail is VisionNonPolicyErrorDetailV2.PERMANENT_RUNTIME_FAILURE
    assert permanent_result.attempt_number == 2
    assert permanent_result.retryable is False


def test_transformers_runner_can_be_tested_without_importing_optional_packages(
    tmp_path: Path,
) -> None:
    profile = vision_profile_catalog_v2().profiles[0]
    config = QwenVisionRuntimeConfig(model_dir=Path("local-model"))

    class FakeInputs(dict[str, object]):
        def to(self, device: object) -> FakeInputs:
            self["moved_to"] = device
            return self

    class FakeProcessor:
        def __init__(self) -> None:
            self.messages: Any = None
            self.template_kwargs: dict[str, object] = {}
            self.decoded_ids: Any = None

        def apply_chat_template(self, messages: Any, **kwargs: Any) -> FakeInputs:
            self.messages = messages
            self.template_kwargs = kwargs
            return FakeInputs({"input_ids": [[1, 2]]})

        def batch_decode(self, token_ids: Any, **kwargs: Any) -> list[str]:
            self.decoded_ids = token_ids
            assert kwargs["skip_special_tokens"] is True
            return [_raw(_empty_payload())]

    class FakeModel:
        device = "cuda:0"

        def __init__(self) -> None:
            self.generate_kwargs: dict[str, object] = {}

        def generate(self, **kwargs: Any) -> list[list[int]]:
            self.generate_kwargs = kwargs
            return [[1, 2, 3]]

    processor = FakeProcessor()
    model = FakeModel()

    def factory(_profile: VisionProfileV2, _config: QwenVisionRuntimeConfig) -> QwenModelBundle:
        return QwenModelBundle(model=model, processor=processor)

    raw_output = TransformersQwenGenerationRunner(factory).generate(
        profile, config, tmp_path / "drawing.bin", ""
    )

    assert json.loads(raw_output) == _empty_payload()
    assert processor.messages[0]["content"][0]["image"].endswith("drawing.bin")
    assert processor.messages[0]["content"][1]["text"] == ""
    assert processor.template_kwargs["add_generation_prompt"] is True
    assert processor.decoded_ids == [[3]]
    assert model.generate_kwargs["do_sample"] is False
    assert model.generate_kwargs["num_beams"] == 1
    assert model.generate_kwargs["max_new_tokens"] == profile.decoding.max_new_tokens
    assert "temperature" not in model.generate_kwargs


def test_default_factory_lazily_imports_optional_runtime_and_sanitizes_missing_import(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_import(_module_name: str) -> object:
        raise ModuleNotFoundError("PRIVATE_OPTIONAL_DEPENDENCY")

    monkeypatch.setattr(qwen_vision.importlib, "import_module", fail_import)
    profile = vision_profile_catalog_v2().profiles[0]

    with pytest.raises(qwen_vision.QwenModelLoadError) as error:
        qwen_vision._default_model_factory(
            profile, QwenVisionRuntimeConfig(model_cache_dir=Path("qwen-vl-cache"))
        )
    assert "PRIVATE_OPTIONAL_DEPENDENCY" not in str(error.value)
