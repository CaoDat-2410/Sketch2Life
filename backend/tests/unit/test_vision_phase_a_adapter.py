from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import get_type_hints

import pytest
from pydantic import ValidationError

from sketch2life.application.ports.vision_understanding import VisionUnderstandingPort
from sketch2life.contracts.schemas.vision import (
    VisionErrorCode,
    VisionImageReferenceV1,
    VisionMediaValidationProvenanceV1,
    VisionNonPolicyErrorDetail,
    VisionProfileId,
    VisionProhibitedClaimCategory,
    VisionUnderstandingFailureV1,
    VisionUnderstandingRequestV1,
    VisionUnderstandingSuccessV1,
    vision_profile_catalog,
    vision_profile_catalog_hash,
    vision_profile_config_hash,
)
from sketch2life.infrastructure.ai.fake_vision import (
    DeterministicFixtureVisionAdapter,
    FakeVisionFixture,
    FakeVisionScenario,
)
from sketch2life.infrastructure.ai.vision_lexical_policy import (
    SYNTHETIC_LEXICON_TERMS,
    LexicalRegressionContentPolicy,
    synthetic_prohibited_lexicon,
)

_IMAGE_BYTES = b"synthetic-drawing-fixture-bytes-v1"


def _write_image(tmp_path: Path, name: str, data: bytes = _IMAGE_BYTES) -> tuple[Path, str]:
    path = tmp_path / name
    path.write_bytes(data)
    return path, sha256(data).hexdigest()


def _pass_validation() -> VisionMediaValidationProvenanceV1:
    return VisionMediaValidationProvenanceV1(
        validation_artifact_ref="fixture:validation:pass:v1",
        validation_artifact_sha256=sha256(b"validation:PASS").hexdigest(),
        decision="PASS",
        validator_policy_version="media-quality-policy-v1",
    )


def _recapture_validation() -> VisionMediaValidationProvenanceV1:
    return VisionMediaValidationProvenanceV1(
        validation_artifact_ref="fixture:validation:recapture:v1",
        validation_artifact_sha256=sha256(b"validation:RECAPTURE").hexdigest(),
        decision="RECAPTURE",
        validator_policy_version="media-quality-policy-v1",
    )


def _request(
    artifact_ref: str,
    sha256_value: str,
    *,
    media_validation: VisionMediaValidationProvenanceV1 | None,
) -> VisionUnderstandingRequestV1:
    return VisionUnderstandingRequestV1(
        correlation_id="phase-a-adapter-test",
        source_image_ref=VisionImageReferenceV1(artifact_ref=artifact_ref, sha256=sha256_value),
        media_validation=media_validation,
        requested_profile_id=VisionProfileId.FAKE_DETERMINISTIC_V1,
    )


def _adapter(fixtures: dict[str, FakeVisionFixture]) -> DeterministicFixtureVisionAdapter:
    return DeterministicFixtureVisionAdapter(
        fixtures, content_policy=LexicalRegressionContentPolicy(synthetic_prohibited_lexicon())
    )


def _text(value: str, status: str = "NOT_DETERMINED") -> dict:
    return {"value": value, "language": {"status": status, "tags": []}}


def _success_payload() -> dict:
    return {
        "entities": [
            {"observation_id": "entity-sun", "label": _text("sun"), "confidence": 0.9},
            {"observation_id": "entity-child", "label": _text("child"), "confidence": None},
        ],
        "actions": [
            {
                "observation_id": "action-smiling",
                "label": _text("smiling"),
                "actor_ref": "entity-child",
                "object_ref": None,
                "confidence": 0.7,
            }
        ],
        "relations": [
            {
                "observation_id": "relation-near",
                "predicate": _text("near"),
                "subject_ref": "entity-child",
                "object_ref": "entity-sun",
                "confidence": 0.5,
            }
        ],
        "themes": [
            {
                "observation_id": "theme-nature",
                "label": _text("nature"),
                "evidence_refs": ["entity-sun"],
                "confidence": 0.8,
            }
        ],
        "ambiguous_regions": [
            {"observation_id": "region-corner", "note": _text("unclear mark")}
        ],
    }


def _empty_payload() -> dict:
    return {"entities": [], "actions": [], "relations": [], "themes": [], "ambiguous_regions": []}


def _raw(payload: dict, *, fence: bool = False) -> str:
    text = json.dumps(payload)
    return f"```json\n{text}\n```" if fence else text


# ---------------------------------------------------------------------------
# Success and all-empty success
# ---------------------------------------------------------------------------


def test_adapter_success_is_schema_valid_and_preserves_source(tmp_path: Path) -> None:
    path, digest = _write_image(tmp_path, "drawing.bin")
    request = _request("fixture:vision:v1", digest, media_validation=_pass_validation())
    adapter = _adapter(
        {
            "fixture:vision:v1": FakeVisionFixture(
                FakeVisionScenario.RAW_OUTPUT, path, _raw(_success_payload())
            )
        }
    )

    result = adapter.understand(request)

    assert isinstance(result, VisionUnderstandingSuccessV1)
    assert result.source_image_ref == request.source_image_ref
    assert len(result.entities) == 2
    assert result.attempt_number == 1
    assert result.repair_attempted is False
    assert result.policy_execution_state == "PASSED"


def test_adapter_all_empty_collections_is_a_valid_technical_success(tmp_path: Path) -> None:
    path, digest = _write_image(tmp_path, "drawing.bin")
    request = _request("fixture:vision:v1", digest, media_validation=_pass_validation())
    adapter = _adapter(
        {
            "fixture:vision:v1": FakeVisionFixture(
                FakeVisionScenario.RAW_OUTPUT, path, _raw(_empty_payload())
            )
        }
    )

    result = adapter.understand(request)

    assert isinstance(result, VisionUnderstandingSuccessV1)
    assert result.entities == ()
    assert result.ambiguous_regions == ()
    assert result.policy_execution_state == "PASSED"


# ---------------------------------------------------------------------------
# Input-integrity failures (adapter-owned, before any inference attempt)
# ---------------------------------------------------------------------------


def test_missing_media_validation_is_input_not_validated(tmp_path: Path) -> None:
    path, digest = _write_image(tmp_path, "drawing.bin")
    request = _request("fixture:vision:v1", digest, media_validation=None)
    adapter = _adapter(
        {
            "fixture:vision:v1": FakeVisionFixture(
                FakeVisionScenario.RAW_OUTPUT, path, _raw(_empty_payload())
            )
        }
    )

    result = adapter.understand(request)

    assert isinstance(result, VisionUnderstandingFailureV1)
    assert result.error_code is VisionErrorCode.INPUT_NOT_VALIDATED
    assert result.error_detail is VisionNonPolicyErrorDetail.MEDIA_VALIDATION_PROVENANCE_MISSING
    assert result.attempt_number == 0
    assert result.repair_attempted is False
    assert result.policy_execution_state == "NOT_EXECUTED"


def test_media_validation_not_passed_is_input_not_validated(tmp_path: Path) -> None:
    path, digest = _write_image(tmp_path, "drawing.bin")
    request = _request("fixture:vision:v1", digest, media_validation=_recapture_validation())
    adapter = _adapter(
        {
            "fixture:vision:v1": FakeVisionFixture(
                FakeVisionScenario.RAW_OUTPUT, path, _raw(_empty_payload())
            )
        }
    )

    result = adapter.understand(request)

    assert isinstance(result, VisionUnderstandingFailureV1)
    assert result.error_detail is VisionNonPolicyErrorDetail.MEDIA_VALIDATION_NOT_PASSED
    assert result.attempt_number == 0


def test_source_image_unreadable_is_input_not_validated(tmp_path: Path) -> None:
    missing_path = tmp_path / "does-not-exist.bin"
    digest = sha256(_IMAGE_BYTES).hexdigest()
    request = _request("fixture:vision:v1", digest, media_validation=_pass_validation())
    adapter = _adapter(
        {
            "fixture:vision:v1": FakeVisionFixture(
                FakeVisionScenario.RAW_OUTPUT, missing_path, _raw(_empty_payload())
            )
        }
    )

    result = adapter.understand(request)

    assert isinstance(result, VisionUnderstandingFailureV1)
    assert result.error_detail is VisionNonPolicyErrorDetail.SOURCE_IMAGE_UNREADABLE
    assert result.attempt_number == 0
    assert result.repair_attempted is False


def test_source_image_hash_mismatch_is_input_not_validated(tmp_path: Path) -> None:
    path, _real_digest = _write_image(tmp_path, "drawing.bin")
    wrong_digest = sha256(b"different-bytes").hexdigest()
    request = _request("fixture:vision:v1", wrong_digest, media_validation=_pass_validation())
    adapter = _adapter(
        {
            "fixture:vision:v1": FakeVisionFixture(
                FakeVisionScenario.RAW_OUTPUT, path, _raw(_empty_payload())
            )
        }
    )

    result = adapter.understand(request)

    assert isinstance(result, VisionUnderstandingFailureV1)
    assert result.error_detail is VisionNonPolicyErrorDetail.SOURCE_IMAGE_HASH_MISMATCH
    assert result.attempt_number == 0


@pytest.mark.parametrize(
    "media_validation_factory",
    (lambda: None, lambda: _recapture_validation()),
    ids=("missing-provenance", "not-passed"),
)
def test_input_failure_envelope_carries_every_shared_envelope_field(
    tmp_path: Path, media_validation_factory: object
) -> None:
    path, digest = _write_image(tmp_path, "drawing.bin")
    media_validation = media_validation_factory()  # type: ignore[operator]
    request = _request("fixture:vision:v1", digest, media_validation=media_validation)
    adapter = _adapter(
        {
            "fixture:vision:v1": FakeVisionFixture(
                FakeVisionScenario.RAW_OUTPUT, path, _raw(_empty_payload())
            )
        }
    )

    result = adapter.understand(request)

    assert isinstance(result, VisionUnderstandingFailureV1)
    catalog_hash = vision_profile_catalog_hash(vision_profile_catalog())
    assert result.profile_id == VisionProfileId.FAKE_DETERMINISTIC_V1
    assert result.profile_catalog_hash == catalog_hash
    assert result.content_policy_version
    assert result.policy_match_view_version
    assert result.source_image_ref == request.source_image_ref


def test_unknown_profile_string_never_reaches_the_port() -> None:
    payload = {
        "contract_name": "VisionUnderstandingRequestV1",
        "contract_version": "1.0",
        "correlation_id": "corr-1",
        "source_image_ref": {
            "artifact_ref": "fixture:vision:v1",
            "sha256": sha256(_IMAGE_BYTES).hexdigest(),
        },
        "media_validation": None,
        "requested_profile_id": "FAKE_UNKNOWN_PROFILE",
    }
    with pytest.raises(ValidationError):
        VisionUnderstandingRequestV1.model_validate(payload)


def test_port_is_interface_only_and_exposes_no_file_or_hash_operation() -> None:
    hints = get_type_hints(VisionUnderstandingPort.understand)
    assert set(hints.keys()) == {"request", "return"}
    assert not hasattr(VisionUnderstandingPort, "read_bytes")
    assert not hasattr(VisionUnderstandingPort, "sha256")


# ---------------------------------------------------------------------------
# Runtime failures: model/device unavailable, timeout, transient/permanent
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("scenario", "detail"),
    (
        (FakeVisionScenario.MODEL_UNAVAILABLE, VisionNonPolicyErrorDetail.MODEL_LOAD_FAILED),
        (FakeVisionScenario.DEVICE_UNAVAILABLE, VisionNonPolicyErrorDetail.DEVICE_UNAVAILABLE),
    ),
)
def test_model_and_device_unavailable_never_retry(
    tmp_path: Path, scenario: FakeVisionScenario, detail: VisionNonPolicyErrorDetail
) -> None:
    path, digest = _write_image(tmp_path, "drawing.bin")
    request = _request("fixture:vision:v1", digest, media_validation=_pass_validation())
    adapter = _adapter({"fixture:vision:v1": FakeVisionFixture(scenario, path)})

    result = adapter.understand(request)

    assert isinstance(result, VisionUnderstandingFailureV1)
    assert result.error_code is VisionErrorCode.VISION_MODEL_UNAVAILABLE
    assert result.error_detail is detail
    assert result.attempt_number == 1
    assert result.retryable is False


def test_timeout_never_retries_and_has_no_retry_branch(tmp_path: Path) -> None:
    path, digest = _write_image(tmp_path, "drawing.bin")
    request = _request("fixture:vision:v1", digest, media_validation=_pass_validation())
    adapter = _adapter(
        {"fixture:vision:v1": FakeVisionFixture(FakeVisionScenario.TIMEOUT, path)}
    )

    result = adapter.understand(request)

    assert isinstance(result, VisionUnderstandingFailureV1)
    assert result.error_code is VisionErrorCode.VISION_TIMEOUT
    assert result.error_detail is VisionNonPolicyErrorDetail.TIMEOUT_BUDGET_EXCEEDED
    assert result.attempt_number == 1
    assert result.retryable is False


def test_transient_failure_can_retry_once_and_then_succeed(tmp_path: Path) -> None:
    path, digest = _write_image(tmp_path, "drawing.bin")
    request = _request("fixture:vision:v1", digest, media_validation=_pass_validation())
    adapter = _adapter(
        {
            "fixture:vision:v1": FakeVisionFixture(
                FakeVisionScenario.PROVIDER_TRANSIENT_SUCCESS, path, _raw(_empty_payload())
            )
        }
    )

    result = adapter.understand(request)

    assert isinstance(result, VisionUnderstandingSuccessV1)
    assert result.attempt_number == 2
    assert result.repair_attempted is False


def test_transient_failure_can_retry_once_and_still_fail(tmp_path: Path) -> None:
    path, digest = _write_image(tmp_path, "drawing.bin")
    request = _request("fixture:vision:v1", digest, media_validation=_pass_validation())
    adapter = _adapter(
        {
            "fixture:vision:v1": FakeVisionFixture(
                FakeVisionScenario.PROVIDER_TRANSIENT_FAILURE, path
            )
        }
    )

    result = adapter.understand(request)

    assert isinstance(result, VisionUnderstandingFailureV1)
    assert result.error_code is VisionErrorCode.VISION_PROVIDER_FAILURE
    assert result.error_detail is VisionNonPolicyErrorDetail.TRANSIENT_RUNTIME_FAILURE
    assert result.attempt_number == 2
    assert result.retryable is True


def test_permanent_provider_failure_does_not_retry(tmp_path: Path) -> None:
    path, digest = _write_image(tmp_path, "drawing.bin")
    request = _request("fixture:vision:v1", digest, media_validation=_pass_validation())
    adapter = _adapter(
        {
            "fixture:vision:v1": FakeVisionFixture(
                FakeVisionScenario.PROVIDER_PERMANENT_FAILURE, path
            )
        }
    )

    result = adapter.understand(request)

    assert isinstance(result, VisionUnderstandingFailureV1)
    assert result.error_code is VisionErrorCode.VISION_PROVIDER_FAILURE
    assert result.error_detail is VisionNonPolicyErrorDetail.PERMANENT_RUNTIME_FAILURE
    assert result.attempt_number == 1
    assert result.retryable is False


# ---------------------------------------------------------------------------
# Lossless-fence-unwrap-only repair rule
# ---------------------------------------------------------------------------


def test_fenced_complete_json_succeeds_with_repair_attempted_true(tmp_path: Path) -> None:
    path, digest = _write_image(tmp_path, "drawing.bin")
    request = _request("fixture:vision:v1", digest, media_validation=_pass_validation())
    adapter = _adapter(
        {
            "fixture:vision:v1": FakeVisionFixture(
                FakeVisionScenario.RAW_OUTPUT, path, _raw(_empty_payload(), fence=True)
            )
        }
    )

    result = adapter.understand(request)

    assert isinstance(result, VisionUnderstandingSuccessV1)
    assert result.repair_attempted is True
    assert result.attempt_number == 1


def test_plain_complete_json_succeeds_with_repair_attempted_false(tmp_path: Path) -> None:
    path, digest = _write_image(tmp_path, "drawing.bin")
    request = _request("fixture:vision:v1", digest, media_validation=_pass_validation())
    adapter = _adapter(
        {
            "fixture:vision:v1": FakeVisionFixture(
                FakeVisionScenario.RAW_OUTPUT, path, _raw(_empty_payload(), fence=False)
            )
        }
    )

    result = adapter.understand(request)

    assert isinstance(result, VisionUnderstandingSuccessV1)
    assert result.repair_attempted is False


@pytest.mark.parametrize("fence", (True, False))
def test_truncated_json_is_schema_invalid_with_repair_attempted_false(
    tmp_path: Path, fence: bool
) -> None:
    path, digest = _write_image(tmp_path, "drawing.bin")
    request = _request("fixture:vision:v1", digest, media_validation=_pass_validation())
    truncated = _raw(_empty_payload(), fence=False)[:-5]
    raw_output = f"```json\n{truncated}\n```" if fence else truncated
    adapter = _adapter(
        {"fixture:vision:v1": FakeVisionFixture(FakeVisionScenario.RAW_OUTPUT, path, raw_output)}
    )

    result = adapter.understand(request)

    assert isinstance(result, VisionUnderstandingFailureV1)
    assert result.error_code is VisionErrorCode.VISION_SCHEMA_INVALID
    assert result.error_detail is VisionNonPolicyErrorDetail.OUTPUT_MAPPING_FAILED
    assert result.repair_attempted is False


def test_fenced_complete_json_failing_schema_has_repair_attempted_true(tmp_path: Path) -> None:
    path, digest = _write_image(tmp_path, "drawing.bin")
    request = _request("fixture:vision:v1", digest, media_validation=_pass_validation())
    payload = _empty_payload()
    payload["entities"] = [
        {"observation_id": "entity-a", "label": _text("a"), "confidence": None}
    ]
    payload["relations"] = [
        {
            "observation_id": "relation-a",
            "predicate": _text("near"),
            "subject_ref": "entity-a",
            "object_ref": "does-not-exist",
            "confidence": None,
        }
    ]
    adapter = _adapter(
        {
            "fixture:vision:v1": FakeVisionFixture(
                FakeVisionScenario.RAW_OUTPUT, path, _raw(payload, fence=True)
            )
        }
    )

    result = adapter.understand(request)

    assert isinstance(result, VisionUnderstandingFailureV1)
    assert result.error_code is VisionErrorCode.VISION_SCHEMA_INVALID
    assert result.error_detail is VisionNonPolicyErrorDetail.REFERENCE_INTEGRITY_VIOLATION
    assert result.repair_attempted is True


def test_unknown_top_level_field_in_raw_output_is_schema_invalid(tmp_path: Path) -> None:
    path, digest = _write_image(tmp_path, "drawing.bin")
    request = _request("fixture:vision:v1", digest, media_validation=_pass_validation())
    payload = _empty_payload()
    payload["commentary"] = "unstructured provider narration"
    adapter = _adapter(
        {"fixture:vision:v1": FakeVisionFixture(FakeVisionScenario.RAW_OUTPUT, path, _raw(payload))}
    )

    result = adapter.understand(request)

    assert isinstance(result, VisionUnderstandingFailureV1)
    assert result.error_code is VisionErrorCode.VISION_SCHEMA_INVALID
    assert result.error_detail is VisionNonPolicyErrorDetail.OUTPUT_MAPPING_FAILED


def test_missing_collection_in_raw_output_is_schema_invalid(tmp_path: Path) -> None:
    path, digest = _write_image(tmp_path, "drawing.bin")
    request = _request("fixture:vision:v1", digest, media_validation=_pass_validation())
    payload = _empty_payload()
    del payload["entities"]
    adapter = _adapter(
        {"fixture:vision:v1": FakeVisionFixture(FakeVisionScenario.RAW_OUTPUT, path, _raw(payload))}
    )

    result = adapter.understand(request)

    assert isinstance(result, VisionUnderstandingFailureV1)
    assert result.error_code is VisionErrorCode.VISION_SCHEMA_INVALID
    assert result.error_detail is VisionNonPolicyErrorDetail.OUTPUT_MAPPING_FAILED


def test_duplicate_observation_id_in_raw_output_is_schema_invalid(tmp_path: Path) -> None:
    path, digest = _write_image(tmp_path, "drawing.bin")
    request = _request("fixture:vision:v1", digest, media_validation=_pass_validation())
    payload = _empty_payload()
    payload["entities"] = [
        {"observation_id": "dup-id", "label": _text("a"), "confidence": None}
    ]
    payload["themes"] = [
        {
            "observation_id": "dup-id",
            "label": _text("nature"),
            "evidence_refs": ["dup-id"],
            "confidence": None,
        }
    ]
    adapter = _adapter(
        {"fixture:vision:v1": FakeVisionFixture(FakeVisionScenario.RAW_OUTPUT, path, _raw(payload))}
    )

    result = adapter.understand(request)

    assert isinstance(result, VisionUnderstandingFailureV1)
    assert result.error_detail is VisionNonPolicyErrorDetail.DUPLICATE_OBSERVATION_ID


def test_dangling_reference_in_raw_output_is_schema_invalid(tmp_path: Path) -> None:
    path, digest = _write_image(tmp_path, "drawing.bin")
    request = _request("fixture:vision:v1", digest, media_validation=_pass_validation())
    payload = _empty_payload()
    payload["actions"] = [
        {
            "observation_id": "action-a",
            "label": _text("running"),
            "actor_ref": "no-such-entity",
            "object_ref": None,
            "confidence": None,
        }
    ]
    adapter = _adapter(
        {"fixture:vision:v1": FakeVisionFixture(FakeVisionScenario.RAW_OUTPUT, path, _raw(payload))}
    )

    result = adapter.understand(request)

    assert isinstance(result, VisionUnderstandingFailureV1)
    assert result.error_detail is VisionNonPolicyErrorDetail.REFERENCE_INTEGRITY_VIOLATION


# ---------------------------------------------------------------------------
# Policy layer: block per category, provenance, non-disclosure
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("term", "category"), SYNTHETIC_LEXICON_TERMS)
def test_policy_blocks_each_prohibited_claim_category_and_never_discloses_the_text(
    tmp_path: Path, term: str, category: VisionProhibitedClaimCategory
) -> None:
    path, digest = _write_image(tmp_path, "drawing.bin")
    request = _request("fixture:vision:v1", digest, media_validation=_pass_validation())
    payload = _empty_payload()
    payload["entities"] = [
        {"observation_id": "entity-a", "label": _text(term), "confidence": None}
    ]
    adapter = _adapter(
        {"fixture:vision:v1": FakeVisionFixture(FakeVisionScenario.RAW_OUTPUT, path, _raw(payload))}
    )

    result = adapter.understand(request)

    assert isinstance(result, VisionUnderstandingFailureV1)
    assert result.error_code is VisionErrorCode.PROHIBITED_CLAIM_DETECTED
    assert result.error_detail is category
    assert result.policy_execution_state == "BLOCKED"
    assert result.retryable is False

    serialized = result.model_dump_json()
    assert term not in serialized


def test_compliant_text_passes_the_policy_layer(tmp_path: Path) -> None:
    path, digest = _write_image(tmp_path, "drawing.bin")
    request = _request("fixture:vision:v1", digest, media_validation=_pass_validation())
    payload = _empty_payload()
    payload["entities"] = [
        {"observation_id": "entity-a", "label": _text("a friendly dog"), "confidence": None}
    ]
    adapter = _adapter(
        {"fixture:vision:v1": FakeVisionFixture(FakeVisionScenario.RAW_OUTPUT, path, _raw(payload))}
    )

    result = adapter.understand(request)

    assert isinstance(result, VisionUnderstandingSuccessV1)
    assert result.policy_execution_state == "PASSED"


def test_schema_invalid_output_never_reaches_the_policy_layer(tmp_path: Path) -> None:
    path, digest = _write_image(tmp_path, "drawing.bin")
    request = _request("fixture:vision:v1", digest, media_validation=_pass_validation())
    term, _category = SYNTHETIC_LEXICON_TERMS[0]
    payload = _empty_payload()
    del payload["entities"]
    payload["policy_bait"] = term
    adapter = _adapter(
        {"fixture:vision:v1": FakeVisionFixture(FakeVisionScenario.RAW_OUTPUT, path, _raw(payload))}
    )

    result = adapter.understand(request)

    assert isinstance(result, VisionUnderstandingFailureV1)
    assert result.error_code is VisionErrorCode.VISION_SCHEMA_INVALID
    assert result.policy_execution_state == "NOT_EXECUTED"


# ---------------------------------------------------------------------------
# Provenance: profile/catalog/config hash, and source-hash preservation
# ---------------------------------------------------------------------------


def test_success_provenance_matches_the_resolved_profile(tmp_path: Path) -> None:
    path, digest = _write_image(tmp_path, "drawing.bin")
    request = _request("fixture:vision:v1", digest, media_validation=_pass_validation())
    adapter = _adapter(
        {
            "fixture:vision:v1": FakeVisionFixture(
                FakeVisionScenario.RAW_OUTPUT, path, _raw(_empty_payload())
            )
        }
    )

    result = adapter.understand(request)

    assert isinstance(result, VisionUnderstandingSuccessV1)
    profile = vision_profile_catalog().resolve(VisionProfileId.FAKE_DETERMINISTIC_V1)
    assert result.adapter_version == profile.adapter_version
    assert result.config_hash == vision_profile_config_hash(profile)


def test_catalog_snapshot_hash_is_present_on_both_success_and_failure(tmp_path: Path) -> None:
    path, digest = _write_image(tmp_path, "drawing.bin")
    expected_hash = vision_profile_catalog_hash(vision_profile_catalog())

    success_request = _request("fixture:vision:v1", digest, media_validation=_pass_validation())
    success_adapter = _adapter(
        {
            "fixture:vision:v1": FakeVisionFixture(
                FakeVisionScenario.RAW_OUTPUT, path, _raw(_empty_payload())
            )
        }
    )
    success = success_adapter.understand(success_request)
    assert success.profile_catalog_hash == expected_hash

    failure_request = _request("fixture:vision:v1", digest, media_validation=None)
    failure_adapter = _adapter(
        {
            "fixture:vision:v1": FakeVisionFixture(
                FakeVisionScenario.RAW_OUTPUT, path, _raw(_empty_payload())
            )
        }
    )
    failure = failure_adapter.understand(failure_request)
    assert failure.profile_catalog_hash == expected_hash


def test_source_image_reference_is_preserved_on_success_and_every_failure(tmp_path: Path) -> None:
    path, digest = _write_image(tmp_path, "drawing.bin")

    success_request = _request("fixture:vision:v1", digest, media_validation=_pass_validation())
    adapter = _adapter(
        {
            "fixture:vision:v1": FakeVisionFixture(
                FakeVisionScenario.RAW_OUTPUT, path, _raw(_empty_payload())
            )
        }
    )
    success = adapter.understand(success_request)
    assert success.source_image_ref == success_request.source_image_ref

    failure_request = _request("fixture:vision:v1", digest, media_validation=None)
    failure = adapter.understand(failure_request)
    assert failure.source_image_ref == failure_request.source_image_ref
