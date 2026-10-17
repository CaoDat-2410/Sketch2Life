"""BE2-02 C2 typed-context contracts and the typed golden example (C2-A01/A07/A14).

image_only 0.1-candidate DTOs keep their bytes and reject typed records; the sibling
0.2-candidate DTOs accept them. Provenance stays truthful: offline only, never live.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from sketch2life.contracts.schemas.analysis_context_results import (
    AnalysisRecordV2,
    AnalysisWorkerCandidateV2,
    TypedProvenanceV2,
)
from sketch2life.contracts.schemas.analysis_results import (
    AnalysisRecordV1,
    AnalysisWorkerCandidateV1,
)
from sketch2life.contracts.schemas.vision_context import (
    LightningVisionContextRequestV1,
    LightningVisionContextResultV1,
    VisionTypedContextV1,
)
from sketch2life.domain.ai_jobs.completion import canonical_sha256
from sketch2life.domain.vision_analysis import (
    AnalysisRuleViolation,
    EvidenceKind,
    ObservationEvidence,
    ProviderContextMode,
    TypedContextBinding,
)
from sketch2life.domain.vision_context import FIXTURE_AGE_BAND_POLICY, pin_context
from sketch2life.infrastructure.vision_analysis.harness import (
    TEACHER,
    build_analysis_harness,
    build_context_harness,
    build_typed_context_example,
)

FIXTURES = (
    Path(__file__).resolve().parents[3]
    / "features/FEAT-048-be2-vision-correction/fixtures/h_ai_review"
)
NOW = datetime(2026, 10, 17, 4, 0, tzinfo=UTC)


def _typed_document() -> dict[str, Any]:
    h = build_analysis_harness()
    snapshot = h.context_sources.resolve(h.pin, h.snapshot)
    assert snapshot is not None
    return pin_context(snapshot, FIXTURE_AGE_BAND_POLICY).projection.canonical()


def _typed_record() -> dict[str, Any]:
    h = build_context_harness()
    analysis_id = h.accepted_analysis()
    record: dict[str, Any] = json.loads(json.dumps(h.service.analysis_record(TEACHER,
                                                                              analysis_id)))
    return record


def _image_only_record() -> dict[str, Any]:
    h = build_analysis_harness()
    analysis_id = h.accepted_analysis()
    record: dict[str, Any] = json.loads(json.dumps(h.service.analysis_record(TEACHER,
                                                                              analysis_id)))
    return record


# --------------------------------------------------------- C2-A01 DTO/domain agreement
def test_c2_a01_domain_projection_and_wire_contract_agree_exactly() -> None:
    document = _typed_document()
    parsed = VisionTypedContextV1.model_validate_json(json.dumps(document))
    assert parsed.model_dump(mode="json") == document


@pytest.mark.parametrize(
    "change",
    [
        {"child_explanation": "It has stripes"},
        {"teacher_feedback": "Nice"},
        {"action_summaries": ["drew"]},
        {"participant_ids": ["participant_fx_a"]},
        {"audience_age_months": [60]},
        {"consent_record_ref": "consent-record:participant_fx_a"},
        {"narration_context": "a cat"},
        {"context_revision": True},
        {"context_revision": "3"},
        {"context_revision": -1},
        {"teacher_topic": ""},
        {"teacher_topic": "Ani\u0007mals"},
        {"audience_age_bands": []},
        {"audience_age_bands": ["completed-years-5", "completed-years-3"]},
        {"audience_age_bands": ["Participant_FX_A"]},
        {"request_reason": "free text"},
        {"contract_version": "0.2-candidate"},
        {"source_image_sha256": "A" * 64},
    ],
)
def test_c2_a01_a04_typed_context_rejects_extras_coercion_and_unbounded_values(
    change: dict[str, object]
) -> None:
    document = {**_typed_document(), **change}
    with pytest.raises(ValidationError):
        VisionTypedContextV1.model_validate_json(json.dumps(document))


def test_c2_a01_topic_key_is_required_even_when_null() -> None:
    document = _typed_document()
    VisionTypedContextV1.model_validate_json(json.dumps({**document, "teacher_topic": None}))
    missing = {k: v for k, v in document.items() if k != "teacher_topic"}
    with pytest.raises(ValidationError):
        VisionTypedContextV1.model_validate_json(json.dumps(missing))


# -------------------------------------------- C2-A14 versioned siblings, truthful evidence
def test_c2_a14_typed_records_are_0_2_and_old_strict_dtos_reject_them() -> None:
    typed = _typed_record()
    record = AnalysisRecordV2.model_validate_json(json.dumps(typed))
    assert record.candidate.provenance.evidence_kind == "offline_context_adapter"
    assert record.context_binding == record.candidate.provenance.context_binding
    AnalysisWorkerCandidateV2.model_validate_json(json.dumps(typed["candidate"]))
    with pytest.raises(ValidationError):
        AnalysisRecordV1.model_validate_json(json.dumps(typed))
    with pytest.raises(ValidationError):
        AnalysisWorkerCandidateV1.model_validate_json(json.dumps(typed["candidate"]))
    # And the sibling never accepts an image_only record.
    image_only = _image_only_record()
    AnalysisRecordV1.model_validate_json(json.dumps(image_only))
    with pytest.raises(ValidationError):
        AnalysisRecordV2.model_validate_json(json.dumps(image_only))
    assert "context_binding" not in json.dumps(image_only)


def test_c2_a14_head_binding_must_equal_the_evidence_copy() -> None:
    typed = _typed_record()
    typed["context_binding"]["context_digest"] = "d" * 64
    with pytest.raises(ValidationError):
        AnalysisRecordV2.model_validate_json(json.dumps(typed))
    candidate = _typed_record()["candidate"]
    candidate["provenance"]["context_binding"]["context_revision"] = 4
    with pytest.raises(ValidationError):
        AnalysisWorkerCandidateV2.model_validate_json(json.dumps(candidate))


@pytest.mark.parametrize(
    "change",
    [
        {"evidence_kind": "live"},
        {"evidence_kind": "offline_legacy_bridge"},
        {"provider_context_mode": "image_only"},
        {"transport_attempts": 2},
        {"model_revision": None},
        {"context_binding": None},
    ],
)
def test_c2_a14_typed_provenance_is_truthful(change: dict[str, object]) -> None:
    provenance = {**_typed_record()["candidate"]["provenance"], **change}
    with pytest.raises(ValidationError):
        TypedProvenanceV2.model_validate_json(json.dumps(provenance))


def test_c2_a14_domain_evidence_kind_and_mode_stay_truthful() -> None:
    binding = _typed_record()["context_binding"]
    pinned = TypedContextBinding(**binding)
    identity = dict(profile_id="p", profile_catalog_hash="a" * 64, config_hash="b" * 64,
                    adapter_version="v", model_identifier="m", model_revision="c" * 40,
                    content_policy_version="c", policy_match_view_version="v")
    ObservationEvidence(EvidenceKind.OFFLINE_CONTEXT_ADAPTER,
                        ProviderContextMode.TYPED_CONTEXT, "a", "R", "e" * 64, NOW, 1,
                        **identity, context_binding=pinned)
    for kind, mode, kept in (
        (EvidenceKind.OFFLINE_CONTEXT_ADAPTER, ProviderContextMode.IMAGE_ONLY, None),
        (EvidenceKind.OFFLINE_LEGACY_BRIDGE, ProviderContextMode.TYPED_CONTEXT, pinned),
        (EvidenceKind.OFFLINE_LEGACY_BRIDGE, ProviderContextMode.IMAGE_ONLY, pinned),
        (EvidenceKind.SYNTHETIC_FAKE, ProviderContextMode.TYPED_CONTEXT, None),
    ):
        with pytest.raises(AnalysisRuleViolation):
            ObservationEvidence(kind, mode, "a", "R", "e" * 64, NOW, 1, **identity,
                                context_binding=kept)


# --------------------------------------------------------------- typed golden example
def test_c2_typed_golden_example_matches_the_deterministic_build() -> None:
    committed = json.loads((FIXTURES / "typed_context_example.json").read_text(encoding="utf-8"))
    assert committed == json.loads(json.dumps(build_typed_context_example()))


def test_c2_typed_golden_example_validates_and_binds_end_to_end() -> None:
    example = json.loads((FIXTURES / "typed_context_example.json").read_text(encoding="utf-8"))
    assert example["endpoint_path"] == "/v1/vision/context"
    request = example["provider_context_request"]
    assert request["source_image"]["content_base64"].startswith("<elided")
    request_ok = {**request, "source_image": {**request["source_image"],
                                              "content_base64": "iVBORw0KGgo="}}
    LightningVisionContextRequestV1.model_validate_json(json.dumps(request_ok))
    assert canonical_sha256(request["typed_context"]) == request["payload_digest"]
    record = AnalysisRecordV2.model_validate_json(json.dumps(example["analysis_record"]))
    retained = example["provider_result_record"]
    wrapper = LightningVisionContextResultV1.model_validate_json(retained["canonical_json"])
    assert sha256(retained["canonical_json"].encode("utf-8")).hexdigest() == (
        retained["result_sha256"])
    ref = next(r for r in record.candidate.evidence_refs if r.kind == "provider_result")
    assert (ref.ref, ref.sha256) == (retained["result_ref"], retained["result_sha256"])
    assert wrapper.payload_digest == record.context_binding.payload_digest
    assert wrapper.context_digest == record.context_binding.context_digest
    text = (FIXTURES / "typed_context_example.json").read_text(encoding="utf-8")
    assert not re.search(r"\b[A-Za-z]:\\\\", text) and "/Users/" not in text
    for internal in ("participant_fx", "consent-record", "profile-age"):
        assert internal not in json.dumps(request), internal


def test_c2_a14_image_only_goldens_are_still_the_0_1_build() -> None:
    # The C1 handoff test pins the bytes; here only the version/provenance stay image_only.
    record = json.loads((FIXTURES / "analysis_record.json").read_text(encoding="utf-8"))
    assert record["candidate"]["contract_version"] == "0.1-candidate"
    assert record["candidate"]["provenance"]["provider_context_mode"] == "image_only"
    assert "context_binding" not in json.dumps(record)
