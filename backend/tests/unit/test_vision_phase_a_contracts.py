from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256

import pytest
from pydantic import TypeAdapter, ValidationError

from sketch2life.contracts.schemas.vision import (
    VISION_POLICY_MATCH_VIEW_VERSION,
    AmbiguousRegionCandidateV1,
    EntityCandidateV1,
    ImageDerivationProvenanceV1,
    ObservedTextV1,
    RelationCandidateV1,
    TextLanguageDeclarationV1,
    ThemeCandidateV1,
    VisionErrorCode,
    VisionImageReferenceV1,
    VisionNonPolicyErrorDetail,
    VisionProfileCatalogV1,
    VisionProfileId,
    VisionProfileV1,
    VisionProhibitedClaimCategory,
    VisionUnderstandingFailureV1,
    VisionUnderstandingRequestV1,
    VisionUnderstandingResultV1,
    VisionUnderstandingSuccessV1,
    vision_profile_catalog,
    vision_profile_catalog_hash,
    vision_profile_config_hash,
)


def _hash(data: bytes) -> str:
    return sha256(data).hexdigest()


def _image_ref(artifact_ref: str = "fixture:vision:image:v1") -> VisionImageReferenceV1:
    return VisionImageReferenceV1(artifact_ref=artifact_ref, sha256=_hash(artifact_ref.encode()))


def _envelope_kwargs(**overrides: object) -> dict[str, object]:
    catalog = vision_profile_catalog()
    profile = catalog.resolve(VisionProfileId.FAKE_DETERMINISTIC_V1)
    kwargs: dict[str, object] = {
        "correlation_id": "phase-a-test-correlation",
        "executed_at": datetime(2026, 8, 31, tzinfo=UTC),
        "source_image_ref": _image_ref(),
        "profile_id": profile.profile_id,
        "profile_catalog_hash": vision_profile_catalog_hash(catalog),
        "attempt_number": 1,
        "repair_attempted": False,
        "content_policy_version": "vision-prohibited-lexicon-fixture-v1",
        "policy_match_view_version": VISION_POLICY_MATCH_VIEW_VERSION,
        "policy_execution_state": "PASSED",
    }
    kwargs.update(overrides)
    return kwargs


def _success_kwargs(**overrides: object) -> dict[str, object]:
    catalog = vision_profile_catalog()
    profile = catalog.resolve(VisionProfileId.FAKE_DETERMINISTIC_V1)
    kwargs: dict[str, object] = {
        **_envelope_kwargs(),
        "entities": (),
        "actions": (),
        "relations": (),
        "themes": (),
        "ambiguous_regions": (),
        "adapter_version": profile.adapter_version,
        "config_hash": vision_profile_config_hash(profile),
    }
    kwargs.update(overrides)
    return kwargs


def _failure_kwargs(**overrides: object) -> dict[str, object]:
    kwargs: dict[str, object] = {
        **_envelope_kwargs(
            policy_execution_state="NOT_EXECUTED", attempt_number=0, repair_attempted=False
        ),
        "error_code": VisionErrorCode.INPUT_NOT_VALIDATED,
        "error_detail": VisionNonPolicyErrorDetail.MEDIA_VALIDATION_PROVENANCE_MISSING,
        "retryable": False,
    }
    kwargs.update(overrides)
    return kwargs


def _observed_text(value: str, status: str = "NOT_DETERMINED", tags: tuple[str, ...] = ()) -> dict:
    return {"value": value, "language": {"status": status, "tags": list(tags)}}


def _not_determined_text(value: str) -> ObservedTextV1:
    return ObservedTextV1(value=value, language=TextLanguageDeclarationV1(status="NOT_DETERMINED"))


# ---------------------------------------------------------------------------
# Image reference and derivation provenance
# ---------------------------------------------------------------------------


def test_image_reference_round_trips_and_has_no_flat_hash_sibling() -> None:
    success = VisionUnderstandingSuccessV1(**_success_kwargs())
    dumped = success.model_dump(mode="json")

    assert dumped["source_image_ref"] == {
        "artifact_ref": "fixture:vision:image:v1",
        "sha256": _hash(b"fixture:vision:image:v1"),
    }
    assert "source_image_sha256" not in dumped
    assert set(dumped["source_image_ref"].keys()) == {"artifact_ref", "sha256"}


@pytest.mark.parametrize(
    ("artifact_ref", "sha256_value"),
    (
        ("", "a" * 64),
        ("fixture:vision:image:v1", "A" * 64),
        ("fixture:vision:image:v1", "a" * 63),
        ("fixture:vision:image:v1", "a" * 65),
    ),
)
def test_invalid_image_reference_is_rejected(artifact_ref: str, sha256_value: str) -> None:
    with pytest.raises(ValidationError):
        VisionImageReferenceV1(artifact_ref=artifact_ref, sha256=sha256_value)


@pytest.mark.parametrize(
    "artifact_ref",
    (
        "/etc/passwd",
        "/var/data/drawing.png",
        "C:\\temp\\drawing.png",
        "C:/temp/drawing.png",
        "D:\\drawing.png",
        "\\\\server\\share\\drawing.png",
        "//server/share/drawing.png",
        "\\temp\\drawing.png",
        "\\Windows\\Temp\\drawing.png",
    ),
)
def test_absolute_machine_paths_are_rejected(artifact_ref: str) -> None:
    with pytest.raises(ValidationError):
        VisionImageReferenceV1(artifact_ref=artifact_ref, sha256="a" * 64)


def test_relative_artifact_reference_is_accepted() -> None:
    reference = VisionImageReferenceV1(artifact_ref="fixture:vision:v1", sha256="a" * 64)
    assert reference.artifact_ref == "fixture:vision:v1"

    relative_path_reference = VisionImageReferenceV1(
        artifact_ref="fixtures/drawings/sample.png", sha256="a" * 64
    )
    assert relative_path_reference.artifact_ref == "fixtures/drawings/sample.png"


def test_derivation_pairing_rules_are_enforced() -> None:
    source = _image_ref("fixture:vision:source:v1")
    processing = _image_ref("fixture:vision:processed:v1")
    base = dict(
        contract_name="VisionUnderstandingRequestV1",
        contract_version="1.0",
        correlation_id="corr-1",
        source_image_ref=source,
        media_validation=None,
        requested_profile_id=VisionProfileId.FAKE_DETERMINISTIC_V1,
    )

    with pytest.raises(ValidationError):
        VisionUnderstandingRequestV1(**base, processing_image_ref=processing)

    with pytest.raises(ValidationError):
        VisionUnderstandingRequestV1(
            **base,
            derivation_provenance=ImageDerivationProvenanceV1(
                transform_name="crop",
                transform_config_version="v1",
                source_image_sha256=source.sha256,
                processing_image_sha256=processing.sha256,
            ),
        )

    with pytest.raises(ValidationError):
        VisionUnderstandingRequestV1(
            **base,
            processing_image_ref=processing,
            derivation_provenance=ImageDerivationProvenanceV1(
                transform_name="crop",
                transform_config_version="v1",
                source_image_sha256=_hash(b"wrong"),
                processing_image_sha256=processing.sha256,
            ),
        )

    valid = VisionUnderstandingRequestV1(
        **base,
        processing_image_ref=processing,
        derivation_provenance=ImageDerivationProvenanceV1(
            transform_name="crop",
            transform_config_version="v1",
            source_image_sha256=source.sha256,
            processing_image_sha256=processing.sha256,
        ),
    )
    assert valid.processing_image_ref == processing


def test_unknown_profile_string_is_rejected_at_request_construction() -> None:
    payload = {
        "contract_name": "VisionUnderstandingRequestV1",
        "contract_version": "1.0",
        "correlation_id": "corr-1",
        "source_image_ref": _image_ref().model_dump(mode="json"),
        "media_validation": None,
        "requested_profile_id": "FAKE_UNKNOWN_PROFILE",
    }
    with pytest.raises(ValidationError):
        VisionUnderstandingRequestV1.model_validate(payload)


# ---------------------------------------------------------------------------
# Profile catalog and hashes
# ---------------------------------------------------------------------------


def test_catalog_rejects_duplicate_profile_ids() -> None:
    profile = VisionProfileV1(
        profile_id=VisionProfileId.FAKE_DETERMINISTIC_V1,
        timeout_seconds=10.0,
        adapter_version="v1",
    )
    with pytest.raises(ValidationError):
        VisionProfileCatalogV1(profiles=(profile, profile))


def test_resolve_raises_for_a_catalog_missing_the_requested_entry() -> None:
    empty_catalog = VisionProfileCatalogV1(profiles=())
    with pytest.raises(ValueError, match="absent from catalog"):
        empty_catalog.resolve(VisionProfileId.FAKE_DETERMINISTIC_V1)


def test_profile_config_hash_is_deterministic_and_field_sensitive() -> None:
    profile = VisionProfileV1(
        profile_id=VisionProfileId.FAKE_DETERMINISTIC_V1,
        timeout_seconds=10.0,
        adapter_version="v1",
    )
    other = profile.model_copy(update={"timeout_seconds": 20.0})

    assert vision_profile_config_hash(profile) == vision_profile_config_hash(profile)
    assert vision_profile_config_hash(profile) != vision_profile_config_hash(other)


def test_catalog_hash_is_deterministic_and_sensitive_to_profile_and_membership_changes() -> None:
    profile_a = VisionProfileV1(
        profile_id=VisionProfileId.FAKE_DETERMINISTIC_V1,
        timeout_seconds=10.0,
        adapter_version="v1",
    )
    catalog = VisionProfileCatalogV1(profiles=(profile_a,))
    same_again = VisionProfileCatalogV1(profiles=(profile_a,))
    changed_profile = VisionProfileCatalogV1(
        profiles=(profile_a.model_copy(update={"timeout_seconds": 99.0}),)
    )
    empty_catalog = VisionProfileCatalogV1(profiles=())

    assert vision_profile_catalog_hash(catalog) == vision_profile_catalog_hash(same_again)
    assert vision_profile_catalog_hash(catalog) != vision_profile_catalog_hash(changed_profile)
    assert vision_profile_catalog_hash(catalog) != vision_profile_catalog_hash(empty_catalog)
    assert "profile_catalog_hash" not in catalog.model_dump(mode="json")


# ---------------------------------------------------------------------------
# Language declaration
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("status", "tags"),
    (
        ("DECLARED", ("en",)),
        ("MIXED", ("en", "vi")),
        ("NOT_DETERMINED", ()),
    ),
)
def test_valid_language_declarations(status: str, tags: tuple[str, ...]) -> None:
    declaration = TextLanguageDeclarationV1(status=status, tags=tags)
    assert declaration.is_ground_truth is False


@pytest.mark.parametrize(
    ("status", "tags"),
    (
        ("DECLARED", ()),
        ("DECLARED", ("en", "vi")),
        ("MIXED", ("en",)),
        ("NOT_DETERMINED", ("en",)),
    ),
)
def test_invalid_language_declaration_tag_counts_are_rejected(
    status: str, tags: tuple[str, ...]
) -> None:
    with pytest.raises(ValidationError):
        TextLanguageDeclarationV1(status=status, tags=tags)


def test_duplicate_language_tags_are_rejected_including_case_variants() -> None:
    with pytest.raises(ValidationError):
        TextLanguageDeclarationV1(status="MIXED", tags=("en", "EN"))


def test_language_tag_order_is_canonicalized_and_serializes_byte_identically() -> None:
    forward = TextLanguageDeclarationV1(status="MIXED", tags=("vi", "en"))
    reversed_input = TextLanguageDeclarationV1(status="MIXED", tags=("en", "vi"))
    assert forward.model_dump_json() == reversed_input.model_dump_json()


def test_language_tags_never_alter_the_static_profile_config_hash() -> None:
    profile = vision_profile_catalog().resolve(VisionProfileId.FAKE_DETERMINISTIC_V1)
    baseline = vision_profile_config_hash(profile)

    ObservedTextV1(
        value="a fox", language=TextLanguageDeclarationV1(status="DECLARED", tags=("en",))
    )
    ObservedTextV1(
        value="a fox", language=TextLanguageDeclarationV1(status="MIXED", tags=("en", "vi"))
    )

    assert vision_profile_config_hash(profile) == baseline


def test_observed_text_value_is_normalized_and_never_empty() -> None:
    text = _not_determined_text("  a   fox  ")
    assert text.value == "a fox"

    with pytest.raises(ValidationError):
        _not_determined_text("   ")


# ---------------------------------------------------------------------------
# Candidate confidence
# ---------------------------------------------------------------------------


def test_entity_confidence_missing_key_and_explicit_null_are_distinguishable() -> None:
    label = _observed_text("a fox")
    with pytest.raises(ValidationError):
        EntityCandidateV1.model_validate({"observation_id": "entity-a", "label": label})

    entity = EntityCandidateV1.model_validate(
        {"observation_id": "entity-a", "label": label, "confidence": None}
    )
    assert entity.confidence is None


@pytest.mark.parametrize("confidence", (0.0, 0.5, 1.0, None))
def test_entity_confidence_accepts_boundary_and_null_values(confidence: float | None) -> None:
    entity = EntityCandidateV1(
        observation_id="entity-a",
        label=_not_determined_text("a fox"),
        confidence=confidence,
    )
    assert entity.confidence == confidence


@pytest.mark.parametrize("confidence", (-0.1, 1.1))
def test_entity_confidence_rejects_out_of_range_values(confidence: float) -> None:
    with pytest.raises(ValidationError):
        EntityCandidateV1(
            observation_id="entity-a",
            label=_not_determined_text("a fox"),
            confidence=confidence,
        )


def test_ambiguous_region_has_no_confidence_field() -> None:
    with pytest.raises(ValidationError):
        AmbiguousRegionCandidateV1.model_validate(
            {
                "observation_id": "region-a",
                "note": _observed_text("unclear mark"),
                "confidence": 0.5,
            }
        )


# ---------------------------------------------------------------------------
# Success: required collections, duplicate IDs, reference integrity
# ---------------------------------------------------------------------------


def test_all_five_collections_present_and_empty_is_a_valid_success() -> None:
    success = VisionUnderstandingSuccessV1(**_success_kwargs())
    assert success.entities == ()
    assert success.ambiguous_regions == ()
    assert success.policy_execution_state == "PASSED"


@pytest.mark.parametrize(
    "missing_key", ("entities", "actions", "relations", "themes", "ambiguous_regions")
)
def test_a_missing_required_collection_is_schema_invalid_not_an_implicit_empty_tuple(
    missing_key: str,
) -> None:
    payload = _success_kwargs()
    del payload[missing_key]
    with pytest.raises(ValidationError):
        VisionUnderstandingSuccessV1.model_validate(_json_safe(payload))


def test_duplicate_observation_id_across_candidate_kinds_is_rejected() -> None:
    payload = _success_kwargs(
        entities=(
            EntityCandidateV1(
                observation_id="shared-id",
                label=_not_determined_text("a fox"),
                confidence=None,
            ),
        ),
        themes=(
            ThemeCandidateV1(
                observation_id="shared-id",
                label=_not_determined_text("nature"),
                evidence_refs=("shared-id",),
                confidence=None,
            ),
        ),
    )
    with pytest.raises(ValidationError, match="DUPLICATE_OBSERVATION_ID"):
        VisionUnderstandingSuccessV1(**payload)


def test_relation_endpoints_must_resolve_to_entity_or_action_and_not_self_reference() -> None:
    entity = EntityCandidateV1(
        observation_id="entity-a",
        label=_not_determined_text("a fox"),
        confidence=None,
    )
    theme = ThemeCandidateV1(
        observation_id="theme-a",
        label=_not_determined_text("nature"),
        evidence_refs=("entity-a",),
        confidence=None,
    )

    with pytest.raises(ValidationError, match="REFERENCE_INTEGRITY_VIOLATION"):
        VisionUnderstandingSuccessV1(
            **_success_kwargs(
                entities=(entity,),
                themes=(theme,),
                relations=(
                    RelationCandidateV1(
                        observation_id="relation-a",
                        predicate=_not_determined_text("near"),
                        subject_ref="entity-a",
                        object_ref="theme-a",
                        confidence=None,
                    ),
                ),
            )
        )

    with pytest.raises(ValidationError, match="REFERENCE_INTEGRITY_VIOLATION"):
        RelationCandidateV1(
            observation_id="relation-a",
            predicate=_not_determined_text("near"),
            subject_ref="entity-a",
            object_ref="entity-a",
            confidence=None,
        )


def test_theme_evidence_refs_reject_ambiguous_region_and_theme_targets() -> None:
    region = AmbiguousRegionCandidateV1(
        observation_id="region-a",
        note=_not_determined_text("unclear"),
    )
    with pytest.raises(ValidationError, match="REFERENCE_INTEGRITY_VIOLATION"):
        VisionUnderstandingSuccessV1(
            **_success_kwargs(
                ambiguous_regions=(region,),
                themes=(
                    ThemeCandidateV1(
                        observation_id="theme-a",
                        label=_not_determined_text("nature"),
                        evidence_refs=("region-a",),
                        confidence=None,
                    ),
                ),
            )
        )


# ---------------------------------------------------------------------------
# Strict schema and no-fabricated-provenance
# ---------------------------------------------------------------------------


def test_unknown_top_level_field_is_rejected() -> None:
    payload = _json_safe(_success_kwargs())
    payload["commentary"] = "unstructured"
    with pytest.raises(ValidationError):
        VisionUnderstandingSuccessV1.model_validate(payload)


def test_unknown_nested_candidate_and_observed_text_field_is_rejected() -> None:
    payload = _json_safe(
        _success_kwargs(
            entities=(
                EntityCandidateV1(
                    observation_id="entity-a",
                    label=_not_determined_text("a fox"),
                    confidence=None,
                ),
            )
        )
    )
    payload["entities"][0]["extra_candidate_field"] = "unexpected"
    with pytest.raises(ValidationError):
        VisionUnderstandingSuccessV1.model_validate(payload)

    payload_two = _json_safe(
        _success_kwargs(
            entities=(
                EntityCandidateV1(
                    observation_id="entity-a",
                    label=_not_determined_text("a fox"),
                    confidence=None,
                ),
            )
        )
    )
    payload_two["entities"][0]["label"]["extra_text_field"] = "unexpected"
    with pytest.raises(ValidationError):
        VisionUnderstandingSuccessV1.model_validate(payload_two)


def test_success_never_carries_fabricated_model_provenance_fields() -> None:
    success = VisionUnderstandingSuccessV1(**_success_kwargs())
    dumped = success.model_dump(mode="json")
    assert "model_identifier" not in dumped
    assert "model_revision" not in dumped
    assert "runtime_version" not in dumped

    payload = _json_safe(_success_kwargs())
    payload["model_identifier"] = "not-allowed"
    with pytest.raises(ValidationError):
        VisionUnderstandingSuccessV1.model_validate(payload)


def test_failure_excludes_success_only_provenance_fields() -> None:
    payload = _json_safe(_failure_kwargs())
    payload["adapter_version"] = "not-allowed"
    with pytest.raises(ValidationError):
        VisionUnderstandingFailureV1.model_validate(payload)

    failure = VisionUnderstandingFailureV1(**_failure_kwargs())
    dumped = failure.model_dump(mode="json")
    assert "adapter_version" not in dumped
    assert "config_hash" not in dumped


def test_success_carries_no_canonical_meaning_or_gate_a_field() -> None:
    fields = set(VisionUnderstandingSuccessV1.model_fields.keys())
    forbidden = {"canonical", "gate_a_approved", "gate_a_decision", "user_facing_summary"}
    assert fields.isdisjoint(forbidden)


# ---------------------------------------------------------------------------
# Policy execution state and detail-set disjointness invariants
# ---------------------------------------------------------------------------


def test_succeeded_requires_passed_policy_state() -> None:
    with pytest.raises(ValidationError):
        VisionUnderstandingSuccessV1(**_success_kwargs(policy_execution_state="NOT_EXECUTED"))


@pytest.mark.parametrize(
    ("error_code", "state"),
    (
        (VisionErrorCode.PROHIBITED_CLAIM_DETECTED, "PASSED"),
        (VisionErrorCode.PROHIBITED_CLAIM_DETECTED, "NOT_EXECUTED"),
        (VisionErrorCode.VISION_TIMEOUT, "PASSED"),
        (VisionErrorCode.VISION_TIMEOUT, "BLOCKED"),
    ),
)
def test_failure_policy_execution_state_must_match_the_outcome_table(
    error_code: VisionErrorCode, state: str
) -> None:
    detail: object = (
        VisionProhibitedClaimCategory.PSYCHOLOGICAL_INFERENCE_CLAIM
        if error_code is VisionErrorCode.PROHIBITED_CLAIM_DETECTED
        else VisionNonPolicyErrorDetail.TIMEOUT_BUDGET_EXCEEDED
    )
    with pytest.raises(ValidationError):
        VisionUnderstandingFailureV1(
            **_failure_kwargs(
                policy_execution_state=state, error_code=error_code, error_detail=detail
            )
        )


def test_prohibited_claim_detected_rejects_a_non_policy_detail_token() -> None:
    with pytest.raises(ValidationError):
        VisionUnderstandingFailureV1(
            **_failure_kwargs(
                policy_execution_state="BLOCKED",
                error_code=VisionErrorCode.PROHIBITED_CLAIM_DETECTED,
                error_detail=VisionNonPolicyErrorDetail.OUTPUT_MAPPING_FAILED,
            )
        )


def test_non_policy_error_code_rejects_a_prohibited_claim_category_detail() -> None:
    with pytest.raises(ValidationError):
        VisionUnderstandingFailureV1(
            **_failure_kwargs(
                policy_execution_state="NOT_EXECUTED",
                error_code=VisionErrorCode.VISION_SCHEMA_INVALID,
                error_detail=VisionProhibitedClaimCategory.TRAUMA_CLAIM,
            )
        )


def test_detail_token_sets_are_disjoint() -> None:
    policy_values = set(VisionProhibitedClaimCategory)
    non_policy_values = set(VisionNonPolicyErrorDetail)
    assert policy_values.isdisjoint(non_policy_values)


# ---------------------------------------------------------------------------
# Full typed failure matrix: structural enforcement
# ---------------------------------------------------------------------------

_EC = VisionErrorCode
_ED = VisionNonPolicyErrorDetail

_VALID_FAILURE_ROWS = (
    (_EC.INPUT_NOT_VALIDATED, _ED.SOURCE_IMAGE_UNREADABLE, False, 0, False),
    (_EC.VISION_MODEL_UNAVAILABLE, _ED.MODEL_LOAD_FAILED, False, 1, False),
    (_EC.VISION_MODEL_UNAVAILABLE, _ED.DEVICE_UNAVAILABLE, False, 1, False),
    (_EC.VISION_TIMEOUT, _ED.TIMEOUT_BUDGET_EXCEEDED, False, 1, False),
    (_EC.VISION_PROVIDER_FAILURE, _ED.TRANSIENT_RUNTIME_FAILURE, True, 2, False),
    (_EC.VISION_PROVIDER_FAILURE, _ED.PERMANENT_RUNTIME_FAILURE, False, 1, False),
    (_EC.VISION_SCHEMA_INVALID, _ED.OUTPUT_MAPPING_FAILED, False, 1, False),
)


def _non_policy_failure_kwargs(
    error_code: VisionErrorCode,
    detail: VisionNonPolicyErrorDetail,
    retryable: bool,
    attempt_number: int,
    repair_attempted: bool,
) -> dict[str, object]:
    return _failure_kwargs(
        error_code=error_code,
        error_detail=detail,
        retryable=retryable,
        attempt_number=attempt_number,
        repair_attempted=repair_attempted,
        policy_execution_state="NOT_EXECUTED",
    )


@pytest.mark.parametrize(
    ("error_code", "detail", "retryable", "attempt", "repair"), _VALID_FAILURE_ROWS
)
def test_each_matrix_row_valid_combination_constructs(
    error_code: VisionErrorCode,
    detail: VisionNonPolicyErrorDetail,
    retryable: bool,
    attempt: int,
    repair: bool,
) -> None:
    failure = VisionUnderstandingFailureV1(
        **_non_policy_failure_kwargs(error_code, detail, retryable, attempt, repair)
    )
    assert failure.error_code is error_code
    assert failure.error_detail is detail


def test_schema_invalid_permits_repair_attempted_true_for_any_of_its_three_details() -> None:
    for detail in (
        _ED.OUTPUT_MAPPING_FAILED,
        _ED.DUPLICATE_OBSERVATION_ID,
        _ED.REFERENCE_INTEGRITY_VIOLATION,
    ):
        failure = VisionUnderstandingFailureV1(
            **_non_policy_failure_kwargs(_EC.VISION_SCHEMA_INVALID, detail, False, 1, True)
        )
        assert failure.repair_attempted is True


@pytest.mark.parametrize(
    ("error_code", "detail", "retryable", "attempt", "repair"),
    (
        # retryable perturbations
        (_EC.INPUT_NOT_VALIDATED, _ED.SOURCE_IMAGE_UNREADABLE, True, 0, False),
        (_EC.VISION_MODEL_UNAVAILABLE, _ED.MODEL_LOAD_FAILED, True, 1, False),
        (_EC.VISION_TIMEOUT, _ED.TIMEOUT_BUDGET_EXCEEDED, True, 1, False),
        (_EC.VISION_PROVIDER_FAILURE, _ED.TRANSIENT_RUNTIME_FAILURE, False, 2, False),
        (_EC.VISION_PROVIDER_FAILURE, _ED.PERMANENT_RUNTIME_FAILURE, True, 1, False),
        (_EC.VISION_SCHEMA_INVALID, _ED.OUTPUT_MAPPING_FAILED, True, 1, False),
        # attempt_number perturbations
        (_EC.INPUT_NOT_VALIDATED, _ED.SOURCE_IMAGE_UNREADABLE, False, 1, False),
        (_EC.VISION_MODEL_UNAVAILABLE, _ED.MODEL_LOAD_FAILED, False, 0, False),
        (_EC.VISION_MODEL_UNAVAILABLE, _ED.MODEL_LOAD_FAILED, False, 2, False),
        (_EC.VISION_TIMEOUT, _ED.TIMEOUT_BUDGET_EXCEEDED, False, 2, False),
        (_EC.VISION_PROVIDER_FAILURE, _ED.TRANSIENT_RUNTIME_FAILURE, True, 1, False),
        (_EC.VISION_PROVIDER_FAILURE, _ED.PERMANENT_RUNTIME_FAILURE, False, 2, False),
        (_EC.VISION_SCHEMA_INVALID, _ED.OUTPUT_MAPPING_FAILED, False, 2, False),
        # repair_attempted perturbations (rows where repair must be fixed false)
        (_EC.INPUT_NOT_VALIDATED, _ED.SOURCE_IMAGE_UNREADABLE, False, 0, True),
        (_EC.VISION_MODEL_UNAVAILABLE, _ED.MODEL_LOAD_FAILED, False, 1, True),
        (_EC.VISION_TIMEOUT, _ED.TIMEOUT_BUDGET_EXCEEDED, False, 1, True),
        (_EC.VISION_PROVIDER_FAILURE, _ED.TRANSIENT_RUNTIME_FAILURE, True, 2, True),
        (_EC.VISION_PROVIDER_FAILURE, _ED.PERMANENT_RUNTIME_FAILURE, False, 1, True),
        # cross-code detail mismatches: a detail token used with a foreign error_code
        (_EC.INPUT_NOT_VALIDATED, _ED.MODEL_LOAD_FAILED, False, 0, False),
        (_EC.VISION_TIMEOUT, _ED.TRANSIENT_RUNTIME_FAILURE, False, 1, False),
        (_EC.VISION_PROVIDER_FAILURE, _ED.TIMEOUT_BUDGET_EXCEEDED, False, 1, False),
        (_EC.VISION_SCHEMA_INVALID, _ED.MEDIA_VALIDATION_NOT_PASSED, False, 1, False),
        (_EC.VISION_MODEL_UNAVAILABLE, _ED.PERMANENT_RUNTIME_FAILURE, False, 1, False),
    ),
)
def test_invalid_failure_matrix_combinations_are_rejected(
    error_code: VisionErrorCode,
    detail: VisionNonPolicyErrorDetail,
    retryable: bool,
    attempt: int,
    repair: bool,
) -> None:
    with pytest.raises(ValidationError):
        VisionUnderstandingFailureV1(
            **_non_policy_failure_kwargs(error_code, detail, retryable, attempt, repair)
        )


def test_prohibited_claim_detected_valid_combination_constructs() -> None:
    failure = VisionUnderstandingFailureV1(
        **_failure_kwargs(
            policy_execution_state="BLOCKED",
            error_code=VisionErrorCode.PROHIBITED_CLAIM_DETECTED,
            error_detail=VisionProhibitedClaimCategory.PERSONALITY_CLAIM,
            attempt_number=1,
            repair_attempted=False,
            retryable=False,
        )
    )
    assert failure.error_code is VisionErrorCode.PROHIBITED_CLAIM_DETECTED


@pytest.mark.parametrize(
    ("attempt_number", "repair_attempted", "retryable"),
    (
        (2, False, False),
        (0, False, False),
        (1, True, False),
        (1, False, True),
    ),
)
def test_prohibited_claim_detected_rejects_invalid_attempt_repair_retry_combinations(
    attempt_number: int, repair_attempted: bool, retryable: bool
) -> None:
    with pytest.raises(ValidationError):
        VisionUnderstandingFailureV1(
            **_failure_kwargs(
                policy_execution_state="BLOCKED",
                error_code=VisionErrorCode.PROHIBITED_CLAIM_DETECTED,
                error_detail=VisionProhibitedClaimCategory.PERSONALITY_CLAIM,
                attempt_number=attempt_number,
                repair_attempted=repair_attempted,
                retryable=retryable,
            )
        )


# ---------------------------------------------------------------------------
# Discriminated union round-trip
# ---------------------------------------------------------------------------


def test_result_union_round_trips_both_branches() -> None:
    success = VisionUnderstandingSuccessV1(**_success_kwargs())
    failure = VisionUnderstandingFailureV1(**_failure_kwargs())

    parsed_success = TypeAdapter(VisionUnderstandingResultV1).validate_python(
        success.model_dump(mode="json")
    )
    parsed_failure = TypeAdapter(VisionUnderstandingResultV1).validate_python(
        failure.model_dump(mode="json")
    )

    assert isinstance(parsed_success, VisionUnderstandingSuccessV1)
    assert isinstance(parsed_failure, VisionUnderstandingFailureV1)


def _json_safe(payload: dict[str, object]) -> dict[str, object]:
    """Round-trip through model_dump(mode="json") equivalents for direct dict mutation."""

    def convert(value: object) -> object:
        if hasattr(value, "model_dump"):
            return value.model_dump(mode="json")
        if isinstance(value, tuple):
            return [convert(item) for item in value]
        if isinstance(value, datetime):
            return value.isoformat()
        return value

    return {key: convert(value) for key, value in payload.items()}
