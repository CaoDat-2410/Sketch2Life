"""P2-T3 Phase B B3 "C3" schema-path diagnostic tests.

Self-contained (duplicates small helpers from ``test_qwen_vision_adapter.py`` rather than
importing its module-private names, matching this repository's standing precedent for keeping
each focused test module independent -- e.g. ``vision_b3_mapping_study.py``'s ``_VramSampler``
docstring).

Covers, per the owner-approved ``P2_T3_PHASE_B_B3_C3_SCHEMA_PATH_DECISION_RECORD.md``:
- every one of the 45 known normalized paths maps deterministically to its exact token;
- unknown/version-drifted shapes map only to the single fallback token;
- adversarial extra-key names never appear in an emitted diagnostic or its string form;
- golden pinned ``loc`` shapes for the installed Pydantic version;
- hook-exception isolation;
- the existing public typed-failure classification is unaffected;
- no path token ever reaches serialized V1/V2 result JSON.
"""

from __future__ import annotations

import copy
import json
from hashlib import sha256
from pathlib import Path
from typing import Any, cast

import pytest
from pydantic import ValidationError

from sketch2life.contracts.schemas.vision import (
    VisionErrorCode,
    VisionImageReferenceV1,
    VisionMediaValidationProvenanceV1,
)
from sketch2life.contracts.schemas.vision_v2 import (
    VisionNonPolicyErrorDetailV2,
    VisionUnderstandingFailureV2,
    VisionUnderstandingRequestV2,
    VisionUnderstandingSuccessV2,
    vision_profile_catalog_hash_v2,
    vision_profile_catalog_v2,
    vision_profile_config_hash_v2,
)
from sketch2life.infrastructure.ai import qwen_vision
from sketch2life.infrastructure.ai.qwen_vision import (
    QwenOutputMappingDiagnostic,
    QwenSchemaPathDiagnostic,
    QwenVisionAdapter,
)
from sketch2life.infrastructure.ai.qwen_vision_runtime_config import QwenVisionRuntimeConfig
from sketch2life.infrastructure.ai.vision_lexical_policy import (
    LexicalRegressionContentPolicy,
    synthetic_prohibited_lexicon,
)

# Private helpers accessed via the module object (matches this repository's existing style in
# test_qwen_vision_adapter.py, e.g. `qwen_vision._default_prompt_builder`).
_classify_schema_error = qwen_vision._classify_schema_error
_mapping_diagnostics_for_schema_error = qwen_vision._mapping_diagnostics_for_schema_error
_normalize_schema_error_loc = qwen_vision._normalize_schema_error_loc
_schema_path_diagnostics_for_schema_error = qwen_vision._schema_path_diagnostics_for_schema_error
_SCHEMA_PATH_TABLE = qwen_vision._SCHEMA_PATH_TABLE

_IMAGE_BYTES = b"synthetic-qwen-vision-c3-image"
_EXECUTED_AT = "2026-09-06T00:00:00+00:00"


# --- shared, self-contained test helpers (duplicated, not imported; see module docstring) ---


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


def _text(value: str = "fox") -> dict[str, object]:
    return {"value": value, "language": {"status": "DECLARED", "tags": ["en"]}}


def _raw(payload: object) -> str:
    return json.dumps(payload)


def _write_source(tmp_path: Path) -> tuple[str, str]:
    path = tmp_path / "drawing.bin"
    path.write_bytes(_IMAGE_BYTES)
    return path.name, sha256(_IMAGE_BYTES).hexdigest()


def _pass_validation() -> VisionMediaValidationProvenanceV1:
    return VisionMediaValidationProvenanceV1(
        validation_artifact_ref="fixture:vision:c3:validation-pass",
        validation_artifact_sha256="c" * 64,
        decision="PASS",
        validator_policy_version="media-quality-policy-v1",
    )


def _request(artifact_ref: str, digest: str) -> VisionUnderstandingRequestV2:
    return VisionUnderstandingRequestV2(
        correlation_id="qwen-vision-c3-test",
        source_image_ref=VisionImageReferenceV1(artifact_ref=artifact_ref, sha256=digest),
        media_validation=_pass_validation(),
        requested_profile_id=vision_profile_catalog_v2().profiles[0].profile_id,
    )


class _SequenceRunner:
    def __init__(self, *outcomes: object) -> None:
        self.outcomes = list(outcomes)
        self.calls = 0

    def generate(self, profile: Any, runtime_config: Any, image_path: Path, prompt: str) -> str:
        del profile, runtime_config, image_path, prompt
        self.calls += 1
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return cast(str, outcome)


def _adapter(
    runner: _SequenceRunner,
    *,
    on_mapping_diagnostic: Any = None,
) -> QwenVisionAdapter:
    return QwenVisionAdapter(
        QwenVisionRuntimeConfig(model_dir=Path("local-model")),
        content_policy=_policy(),
        prompt="",
        generation_runner=runner,
        on_mapping_diagnostic=on_mapping_diagnostic,
    )


# --- payload construction for the 45-row path table ---


def _valid_candidate(collection: str) -> dict[str, Any]:
    if collection == "entities":
        return {"observation_id": "e1", "label": _text(), "confidence": None}
    if collection == "actions":
        return {
            "observation_id": "a1",
            "label": _text(),
            "actor_ref": None,
            "object_ref": None,
            "confidence": None,
        }
    if collection == "relations":
        return {
            "observation_id": "r1",
            "predicate": _text(),
            "subject_ref": "e1",
            "object_ref": "a1",
            "confidence": None,
        }
    if collection == "themes":
        return {
            "observation_id": "t1",
            "label": _text(),
            "evidence_refs": ["e1"],
            "confidence": None,
        }
    assert collection == "ambiguous_regions"
    return {"observation_id": "g1", "note": _text()}


def _payload_with_one_item(collection: str, item: dict[str, Any]) -> dict[str, object]:
    payload = _empty_payload()
    payload[collection] = [item]
    return payload


def _delete(item: dict[str, Any], *path: str) -> dict[str, Any]:
    mutated = copy.deepcopy(item)
    target = mutated
    for key in path[:-1]:
        target = target[key]
    del target[path[-1]]
    return mutated


def _replace(item: dict[str, Any], value: Any, *path: str) -> dict[str, Any]:
    mutated = copy.deepcopy(item)
    target = mutated
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    return mutated


def _text_field_cases(
    collection: str, field: str
) -> list[tuple[str, dict[str, Any], QwenSchemaPathDiagnostic]]:
    """The six mechanically-identical cases every collection's one text field shares."""

    token = lambda suffix: getattr(  # noqa: E731
        QwenSchemaPathDiagnostic, f"SCHEMA_PATH_{collection.upper()}_{field.upper()}{suffix}"
    )
    base = _valid_candidate(collection)
    return [
        (f"{collection}.{field}", _delete(base, field), token("")),
        (f"{collection}.{field}.value", _delete(base, field, "value"), token("_VALUE")),
        (f"{collection}.{field}.language", _delete(base, field, "language"), token("_LANGUAGE")),
        (
            f"{collection}.{field}.language.status",
            _delete(base, field, "language", "status"),
            token("_LANGUAGE_STATUS"),
        ),
        (
            f"{collection}.{field}.language.tags",
            _replace(base, "not-a-list", field, "language", "tags"),
            token("_LANGUAGE_TAGS"),
        ),
        (
            f"{collection}.{field}.language.is_ground_truth",
            _replace(base, True, field, "language", "is_ground_truth"),
            token("_LANGUAGE_IS_GROUND_TRUTH"),
        ),
    ]


def _known_path_cases() -> list[tuple[str, dict[str, Any], QwenSchemaPathDiagnostic]]:
    cases: list[tuple[str, dict[str, Any], QwenSchemaPathDiagnostic]] = []

    for collection in ("entities", "actions", "relations", "themes", "ambiguous_regions"):
        base = _valid_candidate(collection)
        cases.append(
            (
                f"{collection}.observation_id",
                _delete(base, "observation_id"),
                getattr(
                    QwenSchemaPathDiagnostic,
                    f"SCHEMA_PATH_{collection.upper()}_OBSERVATION_ID",
                ),
            )
        )

    cases += _text_field_cases("entities", "label")
    cases.append(
        (
            "entities.confidence",
            _delete(_valid_candidate("entities"), "confidence"),
            QwenSchemaPathDiagnostic.SCHEMA_PATH_ENTITIES_CONFIDENCE,
        )
    )

    cases += _text_field_cases("actions", "label")
    cases.append(
        (
            "actions.actor_ref",
            _replace(_valid_candidate("actions"), 123, "actor_ref"),
            QwenSchemaPathDiagnostic.SCHEMA_PATH_ACTIONS_ACTOR_REF,
        )
    )
    cases.append(
        (
            "actions.object_ref",
            _replace(_valid_candidate("actions"), 123, "object_ref"),
            QwenSchemaPathDiagnostic.SCHEMA_PATH_ACTIONS_OBJECT_REF,
        )
    )
    cases.append(
        (
            "actions.confidence",
            _delete(_valid_candidate("actions"), "confidence"),
            QwenSchemaPathDiagnostic.SCHEMA_PATH_ACTIONS_CONFIDENCE,
        )
    )

    cases += _text_field_cases("relations", "predicate")
    cases.append(
        (
            "relations.subject_ref",
            _delete(_valid_candidate("relations"), "subject_ref"),
            QwenSchemaPathDiagnostic.SCHEMA_PATH_RELATIONS_SUBJECT_REF,
        )
    )
    cases.append(
        (
            "relations.object_ref",
            _delete(_valid_candidate("relations"), "object_ref"),
            QwenSchemaPathDiagnostic.SCHEMA_PATH_RELATIONS_OBJECT_REF,
        )
    )
    cases.append(
        (
            "relations.confidence",
            _delete(_valid_candidate("relations"), "confidence"),
            QwenSchemaPathDiagnostic.SCHEMA_PATH_RELATIONS_CONFIDENCE,
        )
    )

    cases += _text_field_cases("themes", "label")
    cases.append(
        (
            "themes.evidence_refs",
            _delete(_valid_candidate("themes"), "evidence_refs"),
            QwenSchemaPathDiagnostic.SCHEMA_PATH_THEMES_EVIDENCE_REFS,
        )
    )
    cases.append(
        (
            "themes.evidence_refs[*]",
            _replace(_valid_candidate("themes"), ["BAD REF!"], "evidence_refs"),
            QwenSchemaPathDiagnostic.SCHEMA_PATH_THEMES_EVIDENCE_REFS_ITEM,
        )
    )
    cases.append(
        (
            "themes.confidence",
            _delete(_valid_candidate("themes"), "confidence"),
            QwenSchemaPathDiagnostic.SCHEMA_PATH_THEMES_CONFIDENCE,
        )
    )

    cases += _text_field_cases("ambiguous_regions", "note")

    return cases


_KNOWN_PATH_CASES = _known_path_cases()


def test_known_path_case_count_matches_the_approved_45_row_table() -> None:
    """Guards this test module itself against silently covering fewer than 45 rows."""

    assert len(_KNOWN_PATH_CASES) == 45
    assert len(_SCHEMA_PATH_TABLE) == 45


def test_schema_path_diagnostic_is_never_a_public_module_export() -> None:
    """C3 is private/internal-only, per the owner-approved decision record's privacy boundary.

    ``QwenSchemaPathDiagnostic`` must never appear in ``qwen_vision.__all__`` -- it is not a
    public API or V1/V2 contract token, only an in-memory diagnostic-hook refinement. Tests reach
    it through a direct module import (as this file does) or the module object, never via
    re-adding it to ``__all__`` for convenience.
    """

    assert "QwenSchemaPathDiagnostic" not in qwen_vision.__all__
    # Still a real, importable module attribute -- just not part of the public export surface.
    assert qwen_vision.QwenSchemaPathDiagnostic is QwenSchemaPathDiagnostic


@pytest.mark.parametrize(
    ("case_id", "corrupted_item", "expected_token"),
    _KNOWN_PATH_CASES,
    ids=[case[0] for case in _KNOWN_PATH_CASES],
)
def test_every_known_normalized_path_maps_deterministically(
    case_id: str,
    corrupted_item: dict[str, Any],
    expected_token: QwenSchemaPathDiagnostic,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    collection = case_id.split(".", 1)[0]
    monkeypatch.chdir(tmp_path)
    artifact_ref, digest = _write_source(tmp_path)
    payload = _payload_with_one_item(collection, corrupted_item)
    received: list[tuple[QwenOutputMappingDiagnostic | QwenSchemaPathDiagnostic, ...]] = []

    result = _adapter(
        _SequenceRunner(_raw(payload)), on_mapping_diagnostic=received.append
    ).understand(_request(artifact_ref, digest))

    assert isinstance(result, VisionUnderstandingFailureV2)
    assert result.error_detail is VisionNonPolicyErrorDetailV2.OUTPUT_MAPPING_FAILED
    assert len(received) == 1
    assert expected_token in received[0]
    # Exactly one category token (missing or type/constraint) precedes the path token; never both
    # categories on a single-field corruption, and never a duplicate/reference/extra-field token.
    category_tokens = [d for d in received[0] if isinstance(d, QwenOutputMappingDiagnostic)]
    assert category_tokens in (
        [QwenOutputMappingDiagnostic.SCHEMA_MISSING_REQUIRED_FIELD],
        [QwenOutputMappingDiagnostic.SCHEMA_TYPE_OR_CONSTRAINT_INVALID],
    )


# --- unknown / version-drifted shapes map only to the single fallback token ---


def test_unrecognized_normalized_shapes_map_only_to_the_fallback_token() -> None:
    """Simulates version drift directly against the table -- no live Pydantic error needed.

    A shape absent from the finite table (an extra nesting level, an unknown collection, a
    differently-shaped tuple a future Pydantic version might produce) must resolve to exactly
    one token: the fallback. This never touches production code's control flow -- it exercises
    the same lookup production code performs.
    """

    drifted_shapes = [
        ("entities", "*", "label", "language", "tags", "*"),  # a future per-tag-item path
        ("entities", "*", "made_up_field"),
        ("unknown_collection", "*", "observation_id"),
        (),
        ("entities",),
        ("entities", "*"),
        ("entities", "*", "label", "language", "status", "extra_level"),
    ]
    for shape in drifted_shapes:
        assert (
            _SCHEMA_PATH_TABLE.get(shape, QwenSchemaPathDiagnostic.SCHEMA_PATH_UNRECOGNIZED)
            is QwenSchemaPathDiagnostic.SCHEMA_PATH_UNRECOGNIZED
        )


def test_normalize_schema_error_loc_replaces_only_integer_segments() -> None:
    assert _normalize_schema_error_loc(("entities", 0, "label", "value")) == (
        "entities",
        "*",
        "label",
        "value",
    )
    assert _normalize_schema_error_loc(("themes", 3, "evidence_refs", 7)) == (
        "themes",
        "*",
        "evidence_refs",
        "*",
    )
    assert _normalize_schema_error_loc(()) == ()


def test_missing_top_level_collection_is_an_unrecognized_shape_end_to_end(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A whole top-level collection missing is a real, reachable "drifted" shape (length 1)."""

    monkeypatch.chdir(tmp_path)
    artifact_ref, digest = _write_source(tmp_path)
    payload = {"entities": [], "actions": [], "relations": [], "themes": []}  # no ambiguous_regions
    received: list[tuple[QwenOutputMappingDiagnostic | QwenSchemaPathDiagnostic, ...]] = []

    result = _adapter(
        _SequenceRunner(_raw(payload)), on_mapping_diagnostic=received.append
    ).understand(_request(artifact_ref, digest))

    assert isinstance(result, VisionUnderstandingFailureV2)
    assert received == [
        (
            QwenOutputMappingDiagnostic.SCHEMA_MISSING_REQUIRED_FIELD,
            QwenSchemaPathDiagnostic.SCHEMA_PATH_UNRECOGNIZED,
        )
    ]


# --- adversarial extra-key names never appear in any emitted diagnostic or its string form ---


@pytest.mark.parametrize(
    "adversarial_key",
    (
        "ssn_123-45-6789",
        "arbitrary_secret_field",
        "SCHEMA_PATH_ENTITIES_CONFIDENCE",  # even a key that looks like a real token name
        "../../etc/passwd",
    ),
)
def test_extra_forbidden_never_exposes_the_adversarial_key_anywhere(
    adversarial_key: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    artifact_ref, digest = _write_source(tmp_path)
    entity = {**_valid_candidate("entities"), adversarial_key: "attacker-controlled value"}
    payload = _payload_with_one_item("entities", entity)
    received: list[tuple[QwenOutputMappingDiagnostic | QwenSchemaPathDiagnostic, ...]] = []

    result = _adapter(
        _SequenceRunner(_raw(payload)), on_mapping_diagnostic=received.append
    ).understand(_request(artifact_ref, digest))

    assert isinstance(result, VisionUnderstandingFailureV2)
    assert result.error_detail is VisionNonPolicyErrorDetailV2.OUTPUT_MAPPING_FAILED
    # extra_forbidden must never get a path token -- only the existing category token.
    assert received == [(QwenOutputMappingDiagnostic.SCHEMA_EXTRA_FIELD,)]
    assert adversarial_key not in str(received)
    assert adversarial_key not in result.model_dump_json()


def test_extra_key_nested_in_language_never_exposes_the_key_or_gains_a_path_token(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    artifact_ref, digest = _write_source(tmp_path)
    adversarial_key = "patient_diagnosis_code"
    entity = _valid_candidate("entities")
    entity["label"]["language"][adversarial_key] = "value"
    payload = _payload_with_one_item("entities", entity)
    received: list[tuple[QwenOutputMappingDiagnostic | QwenSchemaPathDiagnostic, ...]] = []

    result = _adapter(
        _SequenceRunner(_raw(payload)), on_mapping_diagnostic=received.append
    ).understand(_request(artifact_ref, digest))

    assert isinstance(result, VisionUnderstandingFailureV2)
    assert received == [(QwenOutputMappingDiagnostic.SCHEMA_EXTRA_FIELD,)]
    assert adversarial_key not in str(received)
    assert adversarial_key not in result.model_dump_json()


# --- golden tests: pin the exact real Pydantic `loc` shapes for the installed version ---


def _valid_success_kwargs() -> dict[str, Any]:
    profile = vision_profile_catalog_v2().profiles[0]
    return {
        "correlation_id": "c3-golden-test",
        "executed_at": _EXECUTED_AT,
        "source_image_ref": VisionImageReferenceV1(
            artifact_ref="fixture:vision:c3:golden", sha256="a" * 64
        ),
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


def _golden_validation_error(**overrides: Any) -> ValidationError:
    kwargs = {**_valid_success_kwargs(), **overrides}
    with pytest.raises(ValidationError) as excinfo:
        VisionUnderstandingSuccessV2.model_validate(kwargs)
    return excinfo.value


def test_golden_loc_shape_missing_nested_field() -> None:
    error = _golden_validation_error(
        entities=[{"observation_id": "e1", "confidence": None}]  # label omitted
    )
    items = error.errors(include_url=False, include_context=False, include_input=False)
    assert any(
        item["type"] == "missing" and tuple(item["loc"]) == ("entities", 0, "label")
        for item in items
    )


def test_golden_loc_shape_missing_deeply_nested_field() -> None:
    error = _golden_validation_error(
        entities=[
            {
                "observation_id": "e1",
                "label": {"language": {"status": "DECLARED", "tags": ["en"]}},
                "confidence": None,
            }
        ]
    )
    items = error.errors(include_url=False, include_context=False, include_input=False)
    assert any(
        item["type"] == "missing" and tuple(item["loc"]) == ("entities", 0, "label", "value")
        for item in items
    )


def test_golden_loc_shape_optional_field_wrong_type() -> None:
    error = _golden_validation_error(
        actions=[
            {
                "observation_id": "a1",
                "label": _text(),
                "actor_ref": 123,
                "object_ref": None,
                "confidence": None,
            }
        ]
    )
    items = error.errors(include_url=False, include_context=False, include_input=False)
    assert any(tuple(item["loc"]) == ("actions", 0, "actor_ref") for item in items)


def test_golden_loc_shape_item_level_list_index() -> None:
    error = _golden_validation_error(
        themes=[
            {
                "observation_id": "t1",
                "label": _text(),
                "evidence_refs": ["BAD REF!"],
                "confidence": None,
            }
        ]
    )
    items = error.errors(include_url=False, include_context=False, include_input=False)
    assert any(
        tuple(item["loc"]) == ("themes", 0, "evidence_refs", 0) for item in items
    )


def test_golden_loc_shape_extra_forbidden_terminal_segment() -> None:
    error = _golden_validation_error(
        entities=[
            {
                "observation_id": "e1",
                "label": _text(),
                "confidence": None,
                "totally_arbitrary_key": "value",
            }
        ]
    )
    items = error.errors(include_url=False, include_context=False, include_input=False)
    matching = [item for item in items if item["type"] == "extra_forbidden"]
    assert len(matching) == 1
    assert tuple(matching[0]["loc"]) == ("entities", 0, "totally_arbitrary_key")


# --- hook/classifier exceptions never alter the typed result ---


def test_raising_hook_does_not_alter_result_on_a_type_or_constraint_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    artifact_ref, digest = _write_source(tmp_path)
    entity = _replace(_valid_candidate("entities"), "not-a-number", "confidence")
    payload = _payload_with_one_item("entities", entity)

    def _raise(_diagnostics: tuple[Any, ...]) -> None:
        raise RuntimeError("schema-path diagnostic boom")

    result = _adapter(_SequenceRunner(_raw(payload)), on_mapping_diagnostic=_raise).understand(
        _request(artifact_ref, digest)
    )

    assert isinstance(result, VisionUnderstandingFailureV2)
    assert result.error_code is VisionErrorCode.VISION_SCHEMA_INVALID
    assert result.error_detail is VisionNonPolicyErrorDetailV2.OUTPUT_MAPPING_FAILED


# --- existing public typed-failure classification is unaffected by the new path logic ---


def test_classify_schema_error_is_unaffected_by_the_new_path_classifier() -> None:
    duplicate_error = _golden_validation_error(
        entities=[{"observation_id": "same-id", "label": _text(), "confidence": None}],
        themes=[
            {
                "observation_id": "same-id",
                "label": _text(),
                "evidence_refs": ["same-id"],
                "confidence": None,
            }
        ],
    )
    assert (
        _classify_schema_error(duplicate_error)
        is VisionNonPolicyErrorDetailV2.DUPLICATE_OBSERVATION_ID
    )

    type_error = _golden_validation_error(
        entities=[
            {"observation_id": "e1", "label": _text(), "confidence": "not-a-number"}
        ]
    )
    assert (
        _classify_schema_error(type_error) is VisionNonPolicyErrorDetailV2.OUTPUT_MAPPING_FAILED
    )
    # The category classifier's own output is untouched by path-token computation.
    assert _mapping_diagnostics_for_schema_error(type_error) == (
        QwenOutputMappingDiagnostic.SCHEMA_TYPE_OR_CONSTRAINT_INVALID,
    )
    assert _schema_path_diagnostics_for_schema_error(type_error) == (
        QwenSchemaPathDiagnostic.SCHEMA_PATH_ENTITIES_CONFIDENCE,
    )


# --- no path token ever reaches serialized V1/V2 result JSON, or any benchmark report ---


def test_no_path_token_ever_appears_in_serialized_result_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    artifact_ref, digest = _write_source(tmp_path)
    entity = _replace(_valid_candidate("entities"), "not-a-number", "confidence")
    payload = _payload_with_one_item("entities", entity)

    result = _adapter(_SequenceRunner(_raw(payload))).understand(_request(artifact_ref, digest))

    assert isinstance(result, VisionUnderstandingFailureV2)
    serialized = result.model_dump_json()
    assert "SCHEMA_PATH_" not in serialized
    assert "schema_path" not in serialized.lower()


@pytest.mark.parametrize(
    "module_path",
    (
        "src/sketch2life/benchmark/vision_b3_mapping_study.py",
        "src/sketch2life/benchmark/vision_c1_prompt_mapping_study.py",
    ),
)
def test_benchmark_modules_never_reference_schema_path_diagnostics_or_validation_error(
    module_path: str,
) -> None:
    """Architecture boundary: the benchmark layer only ever receives closed tokens via the hook.

    It must never import ``QwenSchemaPathDiagnostic`` (or reference ``SCHEMA_PATH_`` at all) and
    must never import ``pydantic.ValidationError`` -- all Pydantic-error handling stays private to
    ``qwen_vision.py``.
    """

    # qwen_vision.py lives at <backend>/src/sketch2life/infrastructure/ai/qwen_vision.py
    backend_root = Path(qwen_vision.__file__).resolve().parents[4]
    source = (backend_root / module_path).read_text(encoding="utf-8")
    assert "QwenSchemaPathDiagnostic" not in source
    assert "SCHEMA_PATH_" not in source
    assert "ValidationError" not in source
