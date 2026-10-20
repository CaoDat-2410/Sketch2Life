"""Approved FEAT-018 P2-T4 synthetic diagnostics; never a provider/model run.

Only the explicit CLI writes evidence. A missing required Pillow dependency leaves
the primary B2/B3 observations unexecuted and fails the dependency preflight;
standalone matcher probes are supplemental.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from copy import deepcopy
from datetime import UTC, datetime
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from sketch2life.application.services.raw_understanding_mapper import (
    RawUnderstandingMappingError,
    map_vision_result_to_raw,
)
from sketch2life.application.services.semantic_activity_resolver import confirmed_topic_scene
from sketch2life.application.services.topic_semantics import claims_from_raw
from sketch2life.contracts.schemas.gate_a import GateAConfirmationV1, GateAConfirmationV2
from sketch2life.contracts.schemas.mobile_workflow import MobileWorkflowCommandV1
from sketch2life.contracts.schemas.p1_experience import SemanticAnchorSetV1
from sketch2life.contracts.schemas.raw_understanding import RawUnderstandingSuccessV1
from sketch2life.contracts.schemas.vision_v2 import (
    VisionUnderstandingSuccessV2,
    vision_profile_catalog_hash_v2,
    vision_profile_catalog_v2,
    vision_profile_config_hash_v2,
)
from sketch2life.infrastructure.catalog.activity_semantics import (
    load_activity_semantic_catalog,
)
from sketch2life.infrastructure.catalog.activity_semantics_v2 import (
    load_activity_semantic_catalog_v2,
)

ROOT = Path(__file__).resolve().parents[3]
MANIFEST_PATH = ROOT / "tests/fixtures/feat018-p2-t4-mapping/manifest.v1.json"
REPORT_PATH = ROOT / (
    "features/FEAT-018-live-image-canvas-flow/evidence/metrics/"
    "P2_T4_MAPPING_DIAGNOSTICS_20261020.json"
)
NOW = datetime(2026, 10, 20, 0, 0, tzinfo=UTC)
TEST_REF = "backend/tests/unit/test_feat018_p2_t4_mapping_diagnostics.py"
DISABLED_DEPENDENCIES = (
    "auto_rig_service", "scene_localizer", "activity_ranker", "pixi_show_planner",
    "pixi_show_crop_provider", "pixi_show_asset_issuer",
    "pixi_show_candidate_preview_provider", "pixi_motion_cycle_issuer",
    "renderer_source_capability_issuer",
)


def _digest(value: Any) -> str:
    return sha256(json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()


def _text_digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def load_manifest() -> dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def build_raw(case: dict[str, Any]) -> RawUnderstandingSuccessV1:
    catalog = vision_profile_catalog_v2()
    profile = catalog.profiles[0]
    return RawUnderstandingSuccessV1.model_validate({
        "correlation_id": case["correlation_id"],
        "session_id": case["session_id"],
        "source_image_ref": case["source_image_ref"],
        "entities": [{
            **entity,
            "label": {"value": entity["label"], "language": {"status": "NOT_DETERMINED"}},
            "source": "VISION",
        } for entity in case["entities"]],
        "actions": [], "relations": [], "themes": [], "ambiguous_regions": [],
        "asr_claims": case["asr_claims"], "fused_claims": [],
        "conflicts": case["conflicts"],
        "uncertainty": None, "uncertainty_status": "NOT_PROVIDED",
        "narration_status": case["narration_status"],
        "provenance": {
            "upstream_contract": "VisionUnderstandingResultV2",
            "upstream_contract_version": "2.0",
            "profile_id": profile.profile_id,
            "profile_catalog_hash": vision_profile_catalog_hash_v2(catalog),
            "adapter_version": profile.adapter_version,
            "config_hash": vision_profile_config_hash_v2(profile),
            "model_provenance": profile.model_provenance,
        },
    })


def _b1(raw: RawUnderstandingSuccessV1, case: dict[str, Any]) -> dict[str, Any]:
    claims = claims_from_raw(raw)
    assert raw.source_image_ref.model_dump(mode="json") == case["source_image_ref"]
    assert raw.session_id == case["session_id"]
    assert raw.correlation_id == case["correlation_id"]
    assert [
        {
            "observation_id": item.observation_id,
            "label": item.label.value,
            "confidence": item.confidence,
            "source": item.source,
        }
        for item in raw.entities
    ] == [
        {**entity, "source": "VISION"} for entity in case["entities"]
    ]
    assert [item.model_dump(mode="json") for item in raw.asr_claims] == case["asr_claims"]
    assert [item.model_dump(mode="json") for item in raw.conflicts] == case["conflicts"]
    expected_claim_ids = {entity["observation_id"] for entity in case["entities"]}
    assert {claim.observation_id for claim in claims} == expected_claim_ids
    assert RawUnderstandingSuccessV1.model_validate_json(raw.model_dump_json()) == raw
    if case["family"] == "CONFLICT":
        assert case["narration_text"] == raw.asr_claims[0].text
        assert case["narration_text"]
        assert raw.entities[0].observation_id in raw.conflicts[0].claim_refs
        assert raw.asr_claims[0].claim_id in raw.conflicts[0].claim_refs
        assert raw.asr_claims[0].source == case["asr_claims"][0]["source"] == "ASR"
        assert raw.narration_status == case["narration_status"]
    return {
        "execution_status": "COMPLETE", "requirement_status": "SATISFIED",
        "raw_contract": [raw.contract_name, raw.contract_version],
        "raw_sha256": _digest(raw.model_dump(mode="json")),
        "source_image_ref": raw.source_image_ref.model_dump(mode="json"),
        "session_id": raw.session_id, "correlation_id": raw.correlation_id,
        "entities": [{
            "claim_id": item.observation_id, "label_sha256": _text_digest(item.label.value),
            "confidence": item.confidence, "source": item.source,
        } for item in raw.entities],
        "asr_claims": [{
            "claim_id": item.claim_id, "text_sha256": _text_digest(item.text),
            "confidence": item.confidence, "source": item.source,
        } for item in raw.asr_claims],
        "selectable_claim_ids": [claim.observation_id for claim in claims],
        "conflicts": [conflict.model_dump(mode="json") for conflict in raw.conflicts],
        "narration_status": raw.narration_status,
        "narration_text_sha256": _text_digest(case["narration_text"]),
        "uncertainty_status": raw.uncertainty_status, "uncertainty": raw.uncertainty,
        "provenance_sha256": _digest(raw.provenance.model_dump(mode="json")),
    }


@lru_cache(maxsize=1)
def gate_a_prerequisite() -> tuple[Any, dict[str, str] | None]:
    try:
        from sketch2life.application.services.supervised_flow import SupervisedFlowService
    except ModuleNotFoundError as exc:
        if exc.name != "PIL":
            raise
        return None, {
            "code": "REQUIRED_DEPENDENCY_MISSING",
            "distribution": "Pillow>=11,<13",
            "module": exc.name,
        }
    return SupervisedFlowService, None


class CountingCompilerSentinel:
    def __init__(self) -> None:
        self.calls = 0

    def compile(self, *_args: Any, **_kwargs: Any) -> Any:
        self.calls += 1
        raise AssertionError("P1 compilation is outside this diagnostic boundary")


class CountingAutoRigStub:
    def __init__(self) -> None:
        self.calls = 0

    def start_gate_a_preparation(self, **_kwargs: Any) -> Any:
        self.calls += 1
        raise RuntimeError("FEAT018_T4_CONTROLLED_LOCAL_STUB_FAILURE")


def _command(case: dict[str, Any], version: int, operation: str,
             payload: dict[str, Any], *, suffix: str = "") -> MobileWorkflowCommandV1:
    return MobileWorkflowCommandV1(
        request_id=f"{case['case_id']}-{operation.lower()}{suffix}",
        idempotency_key=f"{case['case_id']}:{operation}:{version}{suffix}",
        session_id=case["session_id"], expected_session_version=version,
        actor_ref="demo:local", created_at=NOW, payload=payload,
    )


def _confirmation(case: dict[str, Any], version: int) -> dict[str, Any]:
    recipe = case["confirmation"]
    common = {
        "session_id": case["session_id"], "expected_session_version": version,
        "actor_ref": recipe.get("actor_ref", "demo:local"),
        "meaning_version": recipe["meaning_version"],
        "confirmed_claim_ids": recipe["confirmed_claim_ids"],
    }
    if recipe["version"] == 2:
        result = GateAConfirmationV2(
            **common, adult_subject_label=recipe["adult_subject_label"]
        )
    else:
        result = GateAConfirmationV1(**common, correction=recipe["correction"])
    return result.model_dump(mode="json")


def _seed_gate_a(case: dict[str, Any], raw: RawUnderstandingSuccessV1,
                 *, auto_rig: CountingAutoRigStub | None = None) -> tuple[Any, Any, Any]:
    service_type, missing = gate_a_prerequisite()
    assert missing is None
    from sketch2life.application.services.ephemeral_sessions import EphemeralSessionService
    from sketch2life.infrastructure.storage.in_memory import (
        InMemoryArtifactStore,
        InMemoryIdempotencyStore,
        InMemorySessionRepository,
    )
    from sketch2life.infrastructure.storage.in_memory_demo_workflow import (
        InMemoryDemoWorkflowStore,
    )

    idempotency = InMemoryIdempotencyStore()
    sessions = EphemeralSessionService(
        sessions=InMemorySessionRepository(), idempotency=idempotency,
        artifacts=InMemoryArtifactStore(), workflow_data=InMemoryDemoWorkflowStore(),
        now=lambda: NOW,
    )
    created, replay = sessions.create(_command(
        case, 0, "CREATE_SESSION", {"operation": "CREATE_SESSION"}
    ))
    assert not replay
    updates = {
        "source_image_ref": raw.source_image_ref.model_dump(mode="json"),
        "raw_understanding": raw.model_dump(mode="json"),
    }
    if case["narration_text"]:
        updates["narration_result"] = {"transcript": case["narration_text"]}
    seeded = sessions.advance(
        session_id=case["session_id"], expected_version=created.observed_session_version,
        allowed_states=("CREATED",), next_state="GATE_A_PENDING", workflow_updates=updates,
    )
    assert seeded.version == sessions.workflow_record(case["session_id"]).version == 1
    assert sessions.snapshot(case["session_id"]).state == "GATE_A_PENDING"
    compiler = CountingCompilerSentinel()
    service = service_type(
        sessions=sessions, idempotency=idempotency, p1_compiler=compiler,
        auto_rig_service=auto_rig, scene_localizer=None, activity_ranker=None,
        pixi_show_planner=None, pixi_show_crop_provider=None, pixi_show_asset_issuer=None,
        pixi_show_candidate_preview_provider=None, pixi_motion_cycle_issuer=None,
        renderer_source_capability_issuer=None, now=lambda: NOW,
    )
    return service, sessions, compiler


def _gate_command(case: dict[str, Any], version: int) -> MobileWorkflowCommandV1:
    return _command(case, version, "CONFIRM_GATE_A", {
        "operation": "CONFIRM_GATE_A", "user_initiated": True,
        "confirmation": _confirmation(case, version),
        "primary_anchor_id": case["confirmation"]["primary_anchor_id"],
    })


def _anchor_observation(anchor: Any) -> dict[str, Any]:
    return {
        "anchor_id": anchor.anchor_id, "kind": anchor.kind,
        "original_label_sha256": _text_digest(anchor.original_label),
        "normalized_label_sha256": _text_digest(anchor.normalized_label),
        "semantic_tags": list(anchor.semantic_tags), "confidence": anchor.confidence,
        "provenance": anchor.provenance.model_dump(mode="json"),
    }


def _execute_gate_a(case: dict[str, Any], raw: RawUnderstandingSuccessV1,
                    *, auto_rig: CountingAutoRigStub | None = None) -> tuple[Any, dict[str, Any]]:
    service, sessions, compiler = _seed_gate_a(case, raw, auto_rig=auto_rig)
    before = sessions.snapshot(case["session_id"])
    command = _gate_command(case, before.version)
    result, replay = service.confirm_gate_a(command)
    assert not replay and result.status == "SUCCEEDED"
    assert compiler.calls == 0
    after = sessions.snapshot(case["session_id"])
    values = sessions.workflow_record(case["session_id"]).values
    assert values["raw_understanding"] == raw.model_dump(mode="json")
    assert after.version == before.version + 1 == result.observed_session_version
    assert after.state == "UNDERSTANDING_PROPOSED"
    assert values["gate_a_confirmation"] == result.payload["gate_a_confirmation"]
    if case["narration_text"]:
        assert values["narration_result"]["transcript"] == case["narration_text"]
    anchors = SemanticAnchorSetV1.model_validate(result.payload["anchor_set"])
    assert anchors.source_artifact_sha256 == raw.source_image_ref.sha256
    confirmation = values["gate_a_confirmation"]
    return anchors, {
        "execution_status": "COMPLETE", "session_version_before": before.version,
        "session_version_after": after.version, "session_state_after": after.state,
        "raw_sha256_before": _digest(raw.model_dump(mode="json")),
        "raw_sha256_after": _digest(values["raw_understanding"]),
        "confirmation_sha256": _digest(confirmation),
        "confirmation_contract": confirmation["contract_name"],
        "actor_ref": confirmation["actor_ref"],
        "meaning_version": confirmation["meaning_version"],
        "confirmed_claim_ids": confirmation["confirmed_claim_ids"],
        "primary_anchor_id_input": command.payload["primary_anchor_id"],
        "anchor_set_id": anchors.anchor_set_id,
        "anchor_set_version": anchors.anchor_set_version,
        "adult_confirmation_actor": anchors.adult_confirmation_actor,
        "primary_anchor": _anchor_observation(anchors.primary_anchor),
        "secondary_anchors": [_anchor_observation(a) for a in anchors.secondary_anchors],
        "compiler_calls": compiler.calls,
        "dependencies": {name: "NOT_INSTALLED" for name in DISABLED_DEPENDENCIES
                         if name != "auto_rig_service" or auto_rig is None},
        "narration_fixture_sha256": _text_digest(case["narration_text"]),
    }


@lru_cache(maxsize=1)
def _catalogs() -> tuple[Any, Any]:
    legacy = load_activity_semantic_catalog(ROOT)
    effective = load_activity_semantic_catalog_v2(ROOT, include_expansion=False)
    assert len(legacy.profiles) == len(effective.profiles) == 100
    return legacy, effective


def _match_observation(match: Any, profile: Any, *, boundary: str) -> dict[str, Any]:
    return {
        "boundary": boundary, "activity_id": profile.activity_id,
        "activity_version": profile.activity_version,
        "profile_id": profile.profile_id, "profile_version": profile.profile_version,
        "provenance_sha256": profile.provenance_sha256,
        "profile_sha256": _digest(profile.model_dump(mode="json")),
        "variant_id": getattr(profile, "variant_id", None),
        "match_mode": match.match_mode,
        "evidence_claim_ids": list(match.evidence_claim_ids),
        "evidence_adult_assertion_ids": list(match.evidence_adult_assertion_ids),
        "matched_phrases_sha256": [_text_digest(p) for p in match.matched_phrases_vi],
        "concept_match_confidence": getattr(match, "concept_match_confidence", None),
        "reason_codes": list(match.reason_codes),
        "fallback_observed": match.match_mode in {"SAFE_FALLBACK", "AGE_BASELINE_FALLBACK"},
    }


def _b3(anchors: SemanticAnchorSetV1, narration_text: str) -> tuple[Any, dict[str, Any]]:
    legacy, effective = _catalogs()
    scene = confirmed_topic_scene(anchors, narration_text=narration_text)
    matches = []
    for catalog, boundary in ((legacy, "V1_MATCH"), (effective, "V2_MATCH_SCENE")):
        for profile in catalog.profiles:
            match = (catalog.match(anchors, profile) if boundary == "V1_MATCH"
                     else catalog.match_scene(scene, profile))
            if match is not None:
                matches.append(_match_observation(match, profile, boundary=boundary))
    concepts = (scene.primary_concept, *scene.secondary_concepts)
    return scene, {
        "execution_status": "COMPLETE", "base_profile_count": len(effective.profiles),
        "include_expansion": False, "p1_matches": matches,
        "scene_sha256": scene.scene_sha256,
        "source_image_sha256": scene.source_image_sha256,
        "source_audio_artifact_ref": scene.source_audio_artifact_ref,
        "source_audio_sha256": scene.source_audio_sha256,
        "narration_text_sha256": _text_digest(scene.asr_transcript_vi),
        "asr_vlm_resolution": scene.asr_vlm_resolution,
        "supported_modalities": list(scene.supported_modalities),
        "conflict_preserved_projection": {
            "value": scene.conflict_preserved,
            "explicitly_set_by_projection": "conflict_preserved" in scene.model_fields_set,
            "interpretation": "schema field value; not an observation that Raw conflicts survived",
        },
        "concepts": [{
            "concept_id": c.concept_id, "label_sha256": _text_digest(c.label_vi),
            "confidence": c.confidence, "source_kinds": list(c.source_kinds),
            "evidence_claim_ids": list(c.evidence_claim_ids),
            "evidence_adult_assertion_ids": list(c.evidence_adult_assertion_ids),
        } for c in concepts],
    }


def _target_match_mode(matches: list[dict[str, Any]], boundary: str,
                       activity_id: str) -> str:
    match = next((item for item in matches
                  if item["boundary"] == boundary and item["activity_id"] == activity_id), None)
    if match is None or match["fallback_observed"]:
        return "NO_PERSONALIZED_MATCH"
    return match["match_mode"]


def run_case(case: dict[str, Any]) -> dict[str, Any]:
    raw = build_raw(case)
    row = {
        "case_id": case["case_id"], "family": case["family"],
        "activity_id": case["activity_id"], "activity_version": case["activity_version"],
        "fixture_sha256": _digest(case), "profile": {
            key: value for key, value in case["profile"].items() if key != "exact_phrase"
        },
        "intended": {
            "target_v1_mode": case["expected"]["target_v1_mode"],
            "target_v2_mode": case["expected"]["target_v2_mode"],
        },
        "test_references": {
            "B1": TEST_REF + "::test_primary_b1",
            "B2_B3": TEST_REF + "::test_primary_gate_a_and_matcher",
        },
        "B1": _b1(raw, case), "boundary_findings": [],
        "static_review_hypotheses": [],
    }
    service_type, missing = gate_a_prerequisite()
    if missing is not None:
        row.update({
            "execution_status": "NOT_RUN", "requirement_status": "UNRESOLVED",
            "B2": {"execution_status": "NOT_RUN", "prerequisite": missing},
            "B3": {"execution_status": "NOT_RUN", "code": "B2_ANCHOR_UNAVAILABLE"},
            "boundary_findings": [missing["code"], "DOWNSTREAM_REQUIREMENTS_UNMEASURED"],
        })
        return row
    assert service_type is not None
    anchors, row["B2"] = _execute_gate_a(case, raw)
    scene, row["B3"] = _b3(anchors, case["narration_text"])
    findings = row["boundary_findings"]
    primary = anchors.primary_anchor
    target_id = raw.entities[0].observation_id
    family = case["family"]
    matches = row["B3"]["p1_matches"]
    target_modes = {m["boundary"]: m["match_mode"] for m in matches
                    if m["activity_id"] == case["activity_id"]}
    expected_v1 = case["expected"]["target_v1_mode"]
    if expected_v1 != "OBSERVE" and target_modes.get("V1_MATCH", "NONE") != expected_v1:
        findings.append("TARGET_V1_EXPECTATION_MISMATCH")
    expected_v2 = case["expected"]["target_v2_mode"]
    observed_v2 = _target_match_mode(matches, "V2_MATCH_SCENE", case["activity_id"])
    if expected_v2 != "OBSERVE_ONLY" and observed_v2 != expected_v2:
        findings.append("TARGET_V2_EXPECTATION_MISMATCH")
    if (family != "ADULT_CORRECTION"
            and (primary.original_label != raw.entities[0].label.value
                 or target_id not in primary.provenance.source_claim_ids)):
        findings.append("TARGET_SOURCE_PRESERVATION_FAILED")
    if family == "AMBIGUOUS":
        if {ref for a in anchors.secondary_anchors for ref in a.provenance.source_claim_ids} != {
            entity.observation_id for entity in raw.entities[1:]
        }:
            findings.append("AMBIGUOUS_SECONDARY_PRESERVATION_FAILED")
        scene_fields = set(scene.model_dump(mode="json"))
        if not {"gate_a_confirmation", "meaning_version"} <= scene_fields:
            row["static_review_hypotheses"].append(
                "AMBIGUITY_DECISION_PROVENANCE_NOT_PROJECTED"
            )
    elif family == "NO_MATCH":
        if primary.semantic_tags:
            findings.append("NO_MATCH_EMPTY_TAG_PRECONDITION_FAILED")
        if any(not m["fallback_observed"] for m in matches):
            findings.append("NO_MATCH_RECIPE_HAS_NON_FALLBACK_MATCH")
        if not findings:
            row["p2_diagnostic"] = "NO_REVIEWED_VOCABULARY_MATCH"
    elif family == "CONFLICT":
        scene_fields = set(scene.model_dump(mode="json"))
        if not scene_fields.intersection({"conflicts", "raw_conflicts", "source_conflicts"}):
            row["static_review_hypotheses"].append("RAW_CONFLICT_REFERENCES_NOT_PROJECTED")
        if scene.asr_vlm_resolution == "ASR_AND_VLM_AGREE":
            findings.append("SOURCE_DISAGREEMENT_PROJECTED_AS_AGREEMENT")
        if scene.source_audio_artifact_ref == "none:narration":
            findings.append("NARRATION_PROJECTION_HAS_ABSENT_AUDIO_MARKER")
    elif family == "LOW":
        linked = [c for c in (scene.primary_concept, *scene.secondary_concepts)
                  if target_id in c.evidence_claim_ids]
        if primary.confidence != 0.05 or not linked or any(c.confidence != 0.05 for c in linked):
            findings.append("LOW_SOURCE_CONFIDENCE_PRESERVATION_FAILED")
    elif family == "ADULT_CORRECTION":
        if not primary.provenance.source_adult_assertion_id or primary.provenance.source_claim_ids:
            findings.append("ADULT_ASSERTION_PROVENANCE_FAILED")
        if not any(target_id in a.provenance.source_claim_ids for a in anchors.secondary_anchors):
            findings.append("RETAINED_VISION_SECONDARY_MISSING")
        if primary.confidence == 1.0:
            row["static_review_hypotheses"].append(
                "ADULT_CONFIDENCE_CONVENTION_REQUIRES_REVIEW"
            )
        if "source_adult_assertion_id" in primary.provenance.model_fields_set:
            row["static_review_hypotheses"].append(
                "PROVENANCE_CONTRACT_REGISTRATION_NOT_ESTABLISHED"
            )
        if not {"meaning_version", "actor_ref"} <= set(scene.model_dump(mode="json")):
            row["static_review_hypotheses"].append(
                "ACTOR_MEANING_AND_ANCHOR_VERSION_PROJECTION_REQUIRES_REVIEW"
            )
    row.update({"execution_status": "COMPLETE",
                "requirement_status": (
                    "UNRESOLVED" if findings or row["static_review_hypotheses"] else "SATISFIED"
                )})
    return row


def _upstream(raw: RawUnderstandingSuccessV1, *, null_confidence: bool = False) -> Any:
    values = raw.model_dump(mode="json")
    provenance = values["provenance"]
    entities = [
        {key: value for key, value in entity.items() if key != "source"}
        for entity in values["entities"]
    ]
    result = VisionUnderstandingSuccessV2.model_validate({
        "correlation_id": raw.correlation_id, "executed_at": NOW,
        "source_image_ref": values["source_image_ref"],
        **{key: provenance[key] for key in (
            "profile_id", "profile_catalog_hash", "adapter_version", "config_hash",
            "model_provenance",
        )},
        "attempt_number": 1, "repair_attempted": False,
        "content_policy_version": "feat018-t4-fixture-v1",
        "policy_match_view_version": "feat018-t4-fixture-v1", "policy_execution_state": "PASSED",
        "entities": entities, "actions": [], "relations": [], "themes": [],
        "ambiguous_regions": [],
    })
    if null_confidence:
        malformed_entity = result.entities[0].model_copy(update={"confidence": None})
        result = result.model_copy(update={"entities": (malformed_entity, *result.entities[1:])})
    return result


def _standalone_anchors(case: dict[str, Any], label: str) -> SemanticAnchorSetV1:
    """Explicit supplemental input; this does not substitute for primary B2."""
    return SemanticAnchorSetV1.model_validate({
        "anchor_set_id": f"supp-{case['activity_id'].lower()}",
        "source_artifact_id": case["source_image_ref"]["artifact_ref"],
        "source_artifact_sha256": case["source_image_ref"]["sha256"],
        "gate_a_status": "CONFIRMED", "adult_confirmation_actor": "PROJECT_OWNER",
        "primary_anchor": {
            "anchor_id": "anchor-supplemental", "kind": "subject",
            "original_label": label, "normalized_label": label, "semantic_tags": [],
            "confidence": 0.9, "adult_confirmed": True,
            "provenance": {
                "source_artifact_id": case["source_image_ref"]["artifact_ref"],
                "source_artifact_sha256": case["source_image_ref"]["sha256"],
                "source_contract_name": "RawUnderstandingResultV1",
                "source_contract_version": "1.0", "source_claim_ids": ["vision-supplemental"],
            },
        },
    })


def _apply_supplemental_expectation(item: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    if row["execution_status"] != "COMPLETE":
        return row
    expected_status = item["expected"]["requirement_status"]
    if row["requirement_status"] != expected_status:
        row["requirement_status"] = "UNRESOLVED"
        row["boundary_findings"].append("MANIFEST_REQUIREMENT_EXPECTATION_MISMATCH")
    return row


def run_supplemental(item: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    scenario = item["scenario"]
    activity_id = item.get("activity_id", "ACT-0004")
    base = deepcopy(next(c for c in manifest["primary_cases"]
                         if c["activity_id"] == activity_id and c["family"] == "EXACT"))
    raw = build_raw(base)
    payload = raw.model_dump(mode="json")
    row = {
        "case_id": item["case_id"], "scenario": scenario,
        "fixture_sha256": _digest(item), "base_case_id": base["case_id"],
        "execution_status": "COMPLETE", "requirement_status": "SATISFIED",
        "test_reference": TEST_REF + "::test_supplemental_observation",
        "observed": {}, "boundary_findings": [],
    }
    observed = row["observed"]
    if scenario in {"VISION_NULL_CONFIDENCE", "SOURCE_HASH_MISMATCH", "CORRELATION_MISMATCH"}:
        kwargs = {
            "session_id": raw.session_id, "expected_source_sha256": raw.source_image_ref.sha256,
            "expected_correlation_id": raw.correlation_id,
        }
        expected = {"VISION_NULL_CONFIDENCE": "missing confidence",
                    "SOURCE_HASH_MISMATCH": "source image hash mismatch",
                    "CORRELATION_MISMATCH": "stale correlation id"}[scenario]
        if scenario == "SOURCE_HASH_MISMATCH":
            kwargs["expected_source_sha256"] = "f" * 64
        elif scenario == "CORRELATION_MISMATCH":
            kwargs["expected_correlation_id"] = "stale-fixture-correlation"
        try:
            map_vision_result_to_raw(
                _upstream(raw, null_confidence=scenario == "VISION_NULL_CONFIDENCE"), **kwargs
            )
        except RawUnderstandingMappingError as exc:
            assert expected in str(exc)
            observed["code"] = scenario + "_REJECTED"
            row["requirement_status"] = "EXPECTED_BLOCKED"
        else:
            raise AssertionError(f"mapper accepted invalid fixture {scenario}")
    elif scenario in {
        "ASR_NULL_CONFIDENCE", "TEXT_TYPED_CONFLICT", "NARRATION_SOURCE_STATUS_MISMATCH"
    }:
        payload = build_raw(next(c for c in manifest["primary_cases"]
                                 if c["activity_id"] == activity_id
                                 and c["family"] == "CONFLICT")).model_dump(mode="json")
        if scenario != "ASR_NULL_CONFIDENCE":
            payload["asr_claims"][0]["source"] = "TEXT_TYPED"
            if scenario == "TEXT_TYPED_CONFLICT":
                payload["narration_status"] = "TEXT_SUPPLIED"
        value = RawUnderstandingSuccessV1.model_validate(payload)
        assert value.asr_claims[0].confidence is None
        observed.update({"asr_confidence": None, "source": value.asr_claims[0].source,
                         "narration_status": value.narration_status,
                         "conflicts": [c.model_dump(mode="json") for c in value.conflicts]})
        if scenario == "NARRATION_SOURCE_STATUS_MISMATCH":
            row["requirement_status"] = "UNRESOLVED"
            row["boundary_findings"] = ["RAW_ACCEPTS_NARRATION_SOURCE_STATUS_MISMATCH"]
    elif scenario in {"UNCERTAINTY_NOT_PROVIDED", "UNCERTAINTY_UPSTREAM_PROVIDED",
                      "UNCERTAINTY_STATUS_MISMATCH", "DUPLICATE_CLAIM_ID",
                      "DANGLING_CONFLICT_REF", "AMBIGUOUS_REGION_ONLY"}:
        rejection = scenario in {"UNCERTAINTY_STATUS_MISMATCH", "DUPLICATE_CLAIM_ID",
                                 "DANGLING_CONFLICT_REF"}
        if scenario == "UNCERTAINTY_UPSTREAM_PROVIDED":
            payload.update(uncertainty_status="UPSTREAM_PROVIDED", uncertainty=0.05)
        elif scenario == "UNCERTAINTY_STATUS_MISMATCH":
            payload["uncertainty"] = 0.05
        elif scenario == "DUPLICATE_CLAIM_ID":
            payload["entities"].append(deepcopy(payload["entities"][0]))
        elif scenario == "DANGLING_CONFLICT_REF":
            payload["conflicts"] = [{"conflict_id": "conflict-dangling",
                "claim_refs": [raw.entities[0].observation_id, "missing-claim"],
                "code": "SOURCE_DISAGREEMENT"}]
        elif scenario == "AMBIGUOUS_REGION_ONLY":
            payload["entities"] = []
            payload["ambiguous_regions"] = [{"observation_id": "ambiguous-only",
                "note": {"value": "fixture", "language": {"status": "NOT_DETERMINED"}},
                "source": "VISION"}]
        if rejection:
            with pytest.raises(ValidationError):
                RawUnderstandingSuccessV1.model_validate(payload)
            observed["code"] = scenario + "_REJECTED"
            row["requirement_status"] = "EXPECTED_BLOCKED"
        else:
            value = RawUnderstandingSuccessV1.model_validate(payload)
            observed.update(uncertainty=value.uncertainty,
                            uncertainty_status=value.uncertainty_status,
                            selectable_claim_ids=[c.observation_id for c in claims_from_raw(value)])
            if scenario == "AMBIGUOUS_REGION_ONLY":
                assert not claims_from_raw(value)
                assert "confidence" not in type(value.ambiguous_regions[0]).model_fields
    elif scenario in {"REVIEWED_ALIAS", "V2_WORD_BOUNDARY", "V2_WHITESPACE"}:
        phrase = base["profile"]["exact_phrase"]
        label = (item["label"] if scenario == "REVIEWED_ALIAS" else
                 f"x{phrase}x" if scenario == "V2_WORD_BOUNDARY" else
                 "fixture-anchor-without-reviewed-phrase")
        anchors = _standalone_anchors(base, label)
        narration = "  ".join(phrase.split()) if scenario == "V2_WHITESPACE" else ""
        _, observation = _b3(anchors, narration)
        observed.update(observation)
        observed["input_origin"] = (
            "SUPPLEMENTAL_NARRATION_TEXT_NOT_B2_OUTPUT" if narration else
            "EXPLICIT_SUPPLEMENTAL_ANCHOR_NOT_B2_OUTPUT"
        )
        modes = {m["boundary"]: m["match_mode"] for m in observation["p1_matches"]
                 if m["activity_id"] == activity_id}
        observed["target_modes"] = modes
        expected_modes = item["expected"]["target_modes"]
        mismatched = {
            boundary: mode for boundary, allowed in expected_modes.items()
            if (mode := modes.get(boundary, "NO_PERSONALIZED_MATCH")) not in allowed
        }
        if scenario == "V2_WORD_BOUNDARY":
            # V1 substring behavior is recorded; B3 V2 must not accept a phrase
            # embedded inside a larger token as a reviewed exact phrase.
            observed["v1_substring_behavior_is_design"] = modes.get("V1_MATCH") == "EXACT"
        if mismatched:
            row["requirement_status"] = "UNRESOLVED"
            row["boundary_findings"] = [scenario + "_MATCHER_EXPECTATION_MISMATCH"]
            observed["expectation_mismatches"] = mismatched
    else:
        return _run_gate_supplemental(item, manifest, base, row)
    return _apply_supplemental_expectation(item, row)


def _run_gate_supplemental(item: dict[str, Any], manifest: dict[str, Any],
                           base: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    scenario = item["scenario"]
    allowed = {"UNKNOWN_CONFIRMED_CLAIM", "STALE_SESSION_VERSION", "V1_ADULT_CORRECTION",
               "SUCCESSIVE_MEANING_VERSIONS", "V2_MISSING_ADULT_LABEL", "NON_DEMO_ACTOR",
               "AMBIGUOUS_TARGET_ONLY", "ADULT_EMPTY_CONFIRMED", "SWALLOWED_AUTORIG_CALL"}
    assert scenario in allowed, f"unimplemented supplemental scenario {scenario}"
    _, missing = gate_a_prerequisite()
    if missing is not None:
        row.update(execution_status="NOT_RUN", requirement_status="UNRESOLVED",
                   observed={"prerequisite": missing},
                   boundary_findings=["B2_PREREQUISITE_UNAVAILABLE"])
        return row
    from sketch2life.application.services.ephemeral_sessions import SessionWorkflowError

    if scenario in {"AMBIGUOUS_TARGET_ONLY", "ADULT_EMPTY_CONFIRMED", "V2_MISSING_ADULT_LABEL"}:
        family = "AMBIGUOUS" if scenario == "AMBIGUOUS_TARGET_ONLY" else "ADULT_CORRECTION"
        base = deepcopy(next(c for c in manifest["primary_cases"]
                             if c["activity_id"] == base["activity_id"] and c["family"] == family))
    if scenario == "AMBIGUOUS_TARGET_ONLY":
        base["confirmation"]["confirmed_claim_ids"] = [base["entities"][0]["observation_id"]]
    elif scenario == "ADULT_EMPTY_CONFIRMED":
        base["confirmation"]["confirmed_claim_ids"] = []
    elif scenario == "V2_MISSING_ADULT_LABEL":
        base["confirmation"]["adult_subject_label"] = None
    elif scenario == "V1_ADULT_CORRECTION":
        base["confirmation"]["correction"] = "nhãn người lớn thử nghiệm ACT-0004"
    elif scenario == "UNKNOWN_CONFIRMED_CLAIM":
        base["confirmation"]["confirmed_claim_ids"] = ["missing-claim"]
        base["confirmation"]["primary_anchor_id"] = "missing-claim"
    raw = build_raw(base)
    stub = CountingAutoRigStub() if scenario == "SWALLOWED_AUTORIG_CALL" else None
    service, sessions, compiler = _seed_gate_a(base, raw, auto_rig=stub)
    version = sessions.snapshot(base["session_id"]).version
    command = _gate_command(base, version)
    if scenario == "STALE_SESSION_VERSION":
        command = command.model_copy(update={"expected_session_version": version + 1})
    elif scenario == "NON_DEMO_ACTOR":
        command = command.model_copy(update={"actor_ref": "fixture:other-adult"})
    expected_error = {
        "UNKNOWN_CONFIRMED_CLAIM": "GATE_A_CLAIM_NOT_FOUND",
        "STALE_SESSION_VERSION": "STALE_SESSION_VERSION",
        "V2_MISSING_ADULT_LABEL": "GATE_A_CORRECTION_EMPTY",
        "NON_DEMO_ACTOR": "DEMO_ACTOR_INVALID",
    }.get(scenario)
    try:
        result, replay = service.confirm_gate_a(command)
    except SessionWorkflowError as exc:
        assert expected_error == exc.code
        row["observed"] = {"code": exc.code, "compiler_calls": compiler.calls}
        row["requirement_status"] = "EXPECTED_BLOCKED"
    else:
        assert expected_error is None, f"expected typed failure {expected_error}"
        assert not replay and result.status == "SUCCEEDED"
        anchors = SemanticAnchorSetV1.model_validate(result.payload["anchor_set"])
        row["observed"] = {
            "primary_anchor": _anchor_observation(anchors.primary_anchor),
            "secondary_anchors": [_anchor_observation(a) for a in anchors.secondary_anchors],
            "meaning_version": result.payload["gate_a_confirmation"]["meaning_version"],
            "anchor_set_version": anchors.anchor_set_version,
            "actor_ref": result.payload["gate_a_confirmation"]["actor_ref"],
            "adult_confirmation_actor": anchors.adult_confirmation_actor,
            "raw_preserved": sessions.workflow_record(base["session_id"]).values[
                "raw_understanding"] == raw.model_dump(mode="json"),
        }
        assert row["observed"]["raw_preserved"]
        if scenario == "SWALLOWED_AUTORIG_CALL":
            assert stub is not None and stub.calls == 1
            row["observed"]["auto_rig_stub_calls"] = stub.calls
        elif scenario == "SUCCESSIVE_MEANING_VERSIONS":
            first_version = sessions.snapshot(base["session_id"]).version
            sessions.advance(session_id=base["session_id"], expected_version=first_version,
                             allowed_states=("UNDERSTANDING_PROPOSED",),
                             next_state="GATE_A_PENDING", workflow_updates={})
            base["confirmation"]["meaning_version"] = 2
            second, _ = service.confirm_gate_a(_gate_command(base, first_version + 1))
            newer = SemanticAnchorSetV1.model_validate(second.payload["anchor_set"])
            assert newer.anchor_set_id != anchors.anchor_set_id
            assert second.payload["gate_a_confirmation"]["meaning_version"] == 2
            row["observed"].update(second_anchor_set_id=newer.anchor_set_id,
                                   second_anchor_set_version=newer.anchor_set_version,
                                   second_meaning_version=2)
            row["requirement_status"] = "UNRESOLVED"
            row["boundary_findings"] = ["MEANING_AND_ANCHOR_VERSION_PROJECTION_REQUIRES_REVIEW"]
        elif scenario == "V1_ADULT_CORRECTION":
            row["requirement_status"] = "UNRESOLVED"
            row["boundary_findings"] = ["V1_CORRECTION_REUSES_VISION_PROVENANCE"]
    assert compiler.calls == 0
    row["observed"]["compiler_calls"] = compiler.calls
    return _apply_supplemental_expectation(item, row)


def build_report(manifest: dict[str, Any]) -> dict[str, Any]:
    primary = [run_case(case) for case in manifest["primary_cases"]]
    supplemental = [run_supplemental(item, manifest) for item in manifest["supplemental_cases"]]
    _, missing = gate_a_prerequisite()
    return {
        "schema_name": "FEAT018P2T4MappingDiagnosticReport", "schema_version": 1,
        "diagnostic_only": True, "full_p2_t4_acceptance": "OPEN",
        "provenance_kind": manifest["provenance_kind"],
        "provider_execution": manifest["provider_execution"],
        "construction_revision": manifest["construction_revision"],
        "approved_source_commit": manifest["approval"]["source_commit"],
        "manifest_sha256": sha256(MANIFEST_PATH.read_bytes()).hexdigest(),
        "source_files": manifest["source_files"],
        "gate_a_prerequisite": missing or {"code": "AVAILABLE"},
        "summary": {
            "primary_count": len(primary), "supplemental_count": len(supplemental),
            "primary_execution": dict(Counter(r["execution_status"] for r in primary)),
            "primary_requirements": dict(Counter(r["requirement_status"] for r in primary)),
            "supplemental_execution": dict(Counter(r["execution_status"] for r in supplemental)),
            "supplemental_requirements": dict(Counter(
                r["requirement_status"] for r in supplemental
            )),
            "boundary_execution": {
                boundary: dict(Counter(r[boundary]["execution_status"] for r in primary))
                for boundary in ("B1", "B2", "B3")
            },
        },
        "primary_cases": primary, "supplemental_cases": supplemental,
    }


def test_primary_b1(case: dict[str, Any]) -> None:
    observation = _b1(build_raw(case), case)
    assert observation["execution_status"] == "COMPLETE"
    assert observation["entities"][0]["confidence"] == (
        0.05 if case["family"] == "LOW" else 0.9
    )


def test_no_match_recipe_has_no_personalized_match() -> None:
    manifest = load_manifest()
    _, v2 = _catalogs()
    cases = [case for case in manifest["primary_cases"] if case["family"] == "NO_MATCH"]
    assert len(cases) == 20
    for case in cases:
        anchors = _standalone_anchors(case, case["entities"][0]["label"])
        scene, _ = _b3(anchors, case["narration_text"])
        personalized = [
            profile.activity_id for profile in v2.profiles
            if (match := v2.match_scene(scene, profile)) is not None
            and match.match_mode != "AGE_BASELINE_FALLBACK"
        ]
        assert not personalized, (
            f"{case['case_id']} unexpectedly matched reviewed profiles: {personalized}"
        )


def test_primary_gate_a_and_matcher(case: dict[str, Any]) -> None:
    _, missing = gate_a_prerequisite()
    if missing is not None:
        pytest.skip(
            "B2/B3 NOT_RUN: required project dependency "
            f"{missing['distribution']} is missing ({missing['module']})"
        )
    row = run_case(case)
    assert row["execution_status"] == "COMPLETE"
    assert row["B2"]["raw_sha256_before"] == row["B2"]["raw_sha256_after"]
    assert row["B2"]["compiler_calls"] == 0
    assert row["B3"]["base_profile_count"] == 100
    primary_modes = {
        item["boundary"]: item["match_mode"] for item in row["B3"]["p1_matches"]
        if item["activity_id"] == case["activity_id"]
    }
    actual_modes = {
        "V1_MATCH": primary_modes.get("V1_MATCH", "NONE"),
        "V2_MATCH_SCENE": _target_match_mode(
            row["B3"]["p1_matches"], "V2_MATCH_SCENE", case["activity_id"]
        ),
    }
    expectations = {
        "V1_MATCH": case["expected"]["target_v1_mode"],
        "V2_MATCH_SCENE": case["expected"]["target_v2_mode"],
    }
    for boundary, expected in expectations.items():
        if expected in {"OBSERVE", "OBSERVE_ONLY"}:
            continue
        mismatch_code = {
            "V1_MATCH": "TARGET_V1_EXPECTATION_MISMATCH",
            "V2_MATCH_SCENE": "TARGET_V2_EXPECTATION_MISMATCH",
        }[boundary]
        assert (mismatch_code in row["boundary_findings"]) == (
            actual_modes[boundary] != expected
        )
    if case["family"] == "NO_MATCH":
        _, v2 = _catalogs()
        non_fallback = []
        anchors = _standalone_anchors(case, case["entities"][0]["label"])
        scene, _ = _b3(anchors, case["narration_text"])
        for profile in v2.profiles:
            match = v2.match_scene(scene, profile)
            if match is not None and match.match_mode != "AGE_BASELINE_FALLBACK":
                non_fallback.append(profile.activity_id)
        assert not non_fallback, "NO_MATCH recipe must not match any of the 100 reviewed profiles"


def test_supplemental_observation(supplemental: dict[str, Any]) -> None:
    row = run_supplemental(supplemental, load_manifest())
    if row["execution_status"] == "NOT_RUN":
        prerequisite = row["observed"]["prerequisite"]
        pytest.skip(
            "B2 NOT_RUN: required project dependency "
            f"{prerequisite['distribution']} is missing ({prerequisite['module']})"
        )
    assert row["execution_status"] == "COMPLETE"
    if supplemental["expected"]["boundary"] == "B3":
        actual_modes = row["observed"]["target_modes"]
        expected_modes = supplemental["expected"]["target_modes"]
        expected_mismatches = {
            boundary: mode for boundary, allowed in expected_modes.items()
            if (mode := actual_modes.get(boundary, "NO_PERSONALIZED_MATCH")) not in allowed
        }
        mismatch_code = supplemental["scenario"] + "_MATCHER_EXPECTATION_MISMATCH"
        assert row["observed"].get("expectation_mismatches", {}) == expected_mismatches
        assert (mismatch_code in row["boundary_findings"]) == bool(expected_mismatches)


def test_gate_a_required_dependency_preflight() -> None:
    _, missing = gate_a_prerequisite()
    assert missing is None, (
        "B2/B3 require the declared backend dependency Pillow>=11,<13; "
        f"active test environment cannot import {missing['module'] if missing else ''}"
    )


def pytest_generate_tests(metafunc: Any) -> None:
    if "case" in metafunc.fixturenames:
        cases = load_manifest()["primary_cases"]
        metafunc.parametrize("case", cases, ids=[c["case_id"] for c in cases])
    if "supplemental" in metafunc.fixturenames:
        cases = load_manifest()["supplemental_cases"]
        metafunc.parametrize("supplemental", cases, ids=[c["case_id"] for c in cases])


def test_report_integrity_and_sanitization() -> None:
    manifest = load_manifest()
    report = build_report(manifest)
    assert report["summary"]["primary_count"] == 120
    assert report["summary"]["supplemental_count"] == len(manifest["supplemental_cases"])
    assert len({row["case_id"] for row in report["primary_cases"]}) == 120
    assert sum(report["summary"]["primary_requirements"].values()) == 120
    for case, row in zip(manifest["primary_cases"], report["primary_cases"], strict=True):
        assert row["fixture_sha256"] == _digest(case)
        assert row["B1"]["raw_sha256"] == _digest(build_raw(case).model_dump(mode="json"))
        if row["B2"]["execution_status"] == "NOT_RUN":
            assert row["execution_status"] == "NOT_RUN"
            assert row["requirement_status"] == "UNRESOLVED"
            assert row["B3"]["execution_status"] == "NOT_RUN"
            assert row["B2"]["prerequisite"]["distribution"] == "Pillow>=11,<13"
        if row["requirement_status"] == "SATISFIED":
            assert not row["boundary_findings"]
            assert not row["static_review_hypotheses"]
    serialized = json.dumps(report, ensure_ascii=False)
    for case in (*manifest["primary_cases"], *manifest["supplemental_cases"]):
        for secret_field in ("label", "narration_text"):
            secret = case.get(secret_field)
            if secret:
                assert secret not in serialized
        for entity in case.get("entities", []):
            assert entity["label"] not in serialized
    assert "raw_understanding" not in serialized


def _main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    report = build_report(load_manifest())
    if args.write_report:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with REPORT_PATH.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"summary": report["summary"],
                      "gate_a_prerequisite": report["gate_a_prerequisite"],
                      "report_written": args.write_report}, sort_keys=True))


if __name__ == "__main__":
    _main()
