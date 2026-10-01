from __future__ import annotations

import base64
from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from sketch2life.application.ports.activity_ranker import ActivityRankerPort
from sketch2life.application.ports.child_preference_classifier import (
    ChildPreferenceClassifierPort,
)
from sketch2life.application.services.auto_rig import AutoRigService
from sketch2life.application.services.ephemeral_sessions import EphemeralSessionService
from sketch2life.application.services.image_admission import Feat018ImageAdmission
from sketch2life.application.services.live_image_demo import LiveImageDemoService
from sketch2life.application.services.p1_experience import P1ExperienceCompiler
from sketch2life.application.services.supervised_flow import SupervisedFlowService
from sketch2life.contracts.schemas.activity_ranking import (
    ActivityRankingRequestV1,
    ActivityRankingResultV1,
)
from sketch2life.contracts.schemas.child_preference_classification import (
    ChildPreferenceClassificationRequestV1,
    ChildPreferenceClassificationV1,
    ChildPreferenceTagV1,
)
from sketch2life.contracts.schemas.vision import (
    VISION_POLICY_MATCH_VIEW_VERSION,
    EntityCandidateV1,
    ObservedTextV1,
    TextLanguageDeclarationV1,
)
from sketch2life.contracts.schemas.vision_v2 import (
    VisionUnderstandingRequestV2,
    VisionUnderstandingSuccessV2,
    vision_profile_catalog_hash_v2,
    vision_profile_catalog_v2,
    vision_profile_config_hash_v2,
)
from sketch2life.domain.understanding.image_admission import (
    DecodedFrameSignals,
    ImageMetadataSignals,
)
from sketch2life.infrastructure.ai.lightning_child_preference_classifier import (
    ChildPreferenceClassificationUnavailable,
)
from sketch2life.infrastructure.ai.vision_lexical_policy import synthetic_prohibited_lexicon
from sketch2life.infrastructure.catalog.activity_semantics import load_activity_semantic_catalog
from sketch2life.infrastructure.catalog.activity_semantics_v2 import (
    load_activity_semantic_catalog_v2,
)
from sketch2life.infrastructure.catalog.p1_catalog import load_p1_template_library
from sketch2life.infrastructure.catalog.workflow_metadata import FileWorkflowCatalogMetadata
from sketch2life.infrastructure.storage.in_memory import (
    InMemoryArtifactStore,
    InMemoryIdempotencyStore,
    InMemoryJobStore,
    InMemorySessionRepository,
)
from sketch2life.infrastructure.storage.in_memory_auto_rig_grants import (
    InMemoryRigPackageGrantStore,
)
from sketch2life.infrastructure.storage.in_memory_demo_workflow import (
    InMemoryDemoWorkflowStore,
)
from sketch2life.infrastructure.storage.in_memory_renderer_source_grants import (
    InMemoryRendererSourceGrantStore,
)
from sketch2life.interfaces.http.app import create_app

_IMAGE = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAA"
    "DUlEQVR4nGP4////fwAJ+wP9KobjigAAAABJRU5ErkJggg=="
)
_SOURCE_WEBP = (
    b"RIFF" + (16).to_bytes(4, "little") + b"WEBPVP8 "
    + (4).to_bytes(4, "little") + b"test"
)


class _TestActivityRanker(ActivityRankerPort):
    def __init__(self) -> None:
        self.requests: list[ActivityRankingRequestV1] = []

    def rank(self, request: ActivityRankingRequestV1) -> ActivityRankingResultV1:
        self.requests.append(request)
        return ActivityRankingResultV1(
            request_id=request.request_id,
            ranked_activity_ids=tuple(item.activity_id for item in request.candidates[:3]),
        )


class _TestPreferenceClassifier(ChildPreferenceClassifierPort):
    def __init__(self) -> None:
        self.requests: list[ChildPreferenceClassificationRequestV1] = []

    def classify(
        self, request: ChildPreferenceClassificationRequestV1
    ) -> ChildPreferenceClassificationV1:
        self.requests.append(request)
        return ChildPreferenceClassificationV1(
            request_id=request.request_id,
            interest_tags=(
                ChildPreferenceTagV1(
                    concept_id="ANIMAL_GENERIC",
                    label_vi="Động vật",
                    confidence=0.82,
                ),
            ),
        )


class _FailingPreferenceClassifier(ChildPreferenceClassifierPort):
    def classify(
        self, request: ChildPreferenceClassificationRequestV1
    ) -> ChildPreferenceClassificationV1:
        raise RuntimeError(f"synthetic upstream failure for {request.interest_text}")


class _MissingPreferenceEndpointClassifier(ChildPreferenceClassifierPort):
    def classify(
        self, request: ChildPreferenceClassificationRequestV1
    ) -> ChildPreferenceClassificationV1:
        del request
        raise ChildPreferenceClassificationUnavailable(
            "CLASSIFIER_ENDPOINT_UNAVAILABLE", False
        )


def _contains_none(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, dict):
        return any(_contains_none(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_none(item) for item in value)
    return False


def test_profile_context_validation_returns_safe_typed_failure(caplog) -> None:
    client = TestClient(create_app())
    response = client.post(
        "/v1/sessions/synthetic-session/p1/context-options",
        headers={
            "X-Request-ID": "profile-invalid-1",
            "X-Expected-Session-Version": "2",
            "X-Actor-Ref": "demo:local",
        },
        json={
            "contract_name": "P1ContextOptionsRequestV1",
            "contract_version": "1.0",
            "age_months": 60,
            "child_profile": {
                "contract_name": "ChildLearningProfileContextV1",
                "contract_version": "1.0",
                "profile_declared_by": "CAREGIVER",
                "profile_recorded_at": datetime.now(UTC).isoformat(),
                "interests": ["private free text must never leak"],
                "dislikes": [],
            },
        },
    )

    assert response.status_code == 422
    body = response.json()
    assert body["contract_name"] == "MobileWorkflowResultV1"
    assert body["status"] == "FAILED"
    assert body["failure"]["code"] == "REQUEST_VALIDATION_FAILED"
    assert "private free text must never leak" not in response.text
    assert "child_profile.interests" in caplog.text
    assert "private free text must never leak" not in caplog.text


def test_context_options_query_validation_returns_safe_typed_failure(caplog) -> None:
    client = TestClient(create_app())
    response = client.get(
        "/v1/sessions/synthetic-session/p1/context-options",
        params={"age_months": 156},
        headers={
            "X-Request-ID": "query-invalid-1",
            "X-Expected-Session-Version": "2",
            "X-Actor-Ref": "demo:local",
        },
    )

    assert response.status_code == 422
    body = response.json()
    assert body["contract_name"] == "MobileWorkflowResultV1"
    assert body["status"] == "FAILED"
    assert body["failure"]["code"] == "REQUEST_VALIDATION_FAILED"
    assert body["provenance"]["source_contracts"] == ["P1ContextOptionsQueryV1"]
    assert "age_months" in caplog.text
    assert "156" not in caplog.text


def test_preference_classifier_is_backend_owned_bounded_and_does_not_log_text(caplog) -> None:
    classifier = _TestPreferenceClassifier()
    client, _ = _client(child_preference_classifier=classifier)
    private_synthetic_phrase = "synthetic private phrase that must not appear in logs"
    response = client.post(
        "/v1/profile/preferences/classify",
        headers={"X-Actor-Ref": "demo:local"},
        json={
            "contract_name": "ChildPreferenceClassificationRequestV1",
            "contract_version": "1.0",
            "request_id": "preference-test-1",
            "interest_text": private_synthetic_phrase,
            "avoid_text": "",
        },
    )

    assert response.status_code == 200
    assert response.json()["interest_tags"][0]["concept_id"] == "ANIMAL_GENERIC"
    assert len(classifier.requests) == 1
    assert classifier.requests[0].interest_text == private_synthetic_phrase
    assert private_synthetic_phrase not in caplog.text


def test_preference_classifier_upstream_exception_returns_safe_typed_failure(caplog) -> None:
    client, _ = _client(child_preference_classifier=_FailingPreferenceClassifier())
    private_synthetic_phrase = "synthetic preference must not leak"
    response = client.post(
        "/v1/profile/preferences/classify",
        headers={"X-Actor-Ref": "demo:local"},
        json={
            "contract_name": "ChildPreferenceClassificationRequestV1",
            "contract_version": "1.0",
            "request_id": "preference-upstream-failure",
            "interest_text": private_synthetic_phrase,
            "avoid_text": "",
        },
    )

    assert response.status_code == 500
    body = response.json()
    assert body["status"] == "FAILED"
    assert body["failure"]["code"] == "CLASSIFIER_INTERNAL_ERROR"
    assert isinstance(body["failure"]["safe_message"], str)
    assert private_synthetic_phrase not in response.text
    assert private_synthetic_phrase not in caplog.text


def test_missing_lightning_classifier_route_has_actionable_safe_failure(caplog) -> None:
    client, _ = _client(
        child_preference_classifier=_MissingPreferenceEndpointClassifier()
    )
    private_synthetic_phrase = "synthetic preference must not appear in logs"
    response = client.post(
        "/v1/profile/preferences/classify",
        headers={"X-Actor-Ref": "demo:local"},
        json={
            "contract_name": "ChildPreferenceClassificationRequestV1",
            "contract_version": "1.0",
            "request_id": "preference-endpoint-missing",
            "interest_text": private_synthetic_phrase,
            "avoid_text": "",
        },
    )

    assert response.status_code == 503
    assert response.json()["failure"]["code"] == "CLASSIFIER_ENDPOINT_UNAVAILABLE"
    assert response.json()["failure"]["retryable"] is False
    assert "cập nhật" in response.json()["failure"]["safe_message"]
    assert "khởi động lại" in response.json()["failure"]["safe_message"]
    assert private_synthetic_phrase not in response.text
    assert private_synthetic_phrase not in caplog.text


def test_context_candidates_and_v2_finalization_keep_profile_and_supervision_session_scoped() -> (
    None
):
    preference_classifier = _TestPreferenceClassifier()
    client, _ = _client(
        vision=_CountingVision(label="con chim"),
        child_preference_classifier=preference_classifier,
    )
    classified = client.post(
        "/v1/profile/preferences/classify",
        headers={"X-Actor-Ref": "demo:local"},
        json={
            "contract_name": "ChildPreferenceClassificationRequestV1",
            "contract_version": "1.0",
            "request_id": "v2-context-preference-classification",
            "interest_text": "synthetic interest in birds",
            "avoid_text": "",
        },
    )
    assert classified.status_code == 200
    assert len(preference_classifier.requests) == 1
    assert classified.json()["interest_tags"][0]["concept_id"] == "ANIMAL_GENERIC"
    session_id, version = _create_session(client)
    uploaded = client.post(
        f"/v1/sessions/{session_id}/media/image",
        headers=_headers(session_id, version, "v2-context-upload"),
        files={"image": ("synthetic.png", _IMAGE, "image/png")},
    )
    assert uploaded.status_code == 200
    version = uploaded.json()["observed_session_version"]
    inferred = _command(
        client,
        session_id=session_id,
        version=version,
        key="v2-context-understanding",
        route="/understanding",
        payload={"operation": "RUN_UNDERSTANDING", "user_initiated": True},
    )
    version = inferred.json()["observed_session_version"]
    confirmed = _command(
        client,
        session_id=session_id,
        version=version,
        key="v2-context-gate-a",
        route="/gate-a/confirm",
        payload={
            "operation": "CONFIRM_GATE_A",
            "user_initiated": True,
            "primary_anchor_id": "subject-1",
            "confirmation": {
                "contract_name": "GateAConfirmationV1",
                "contract_version": "1.0",
                "meaning_version": 1,
                "confirmed_claim_ids": ["subject-1"],
                "correction": None,
            },
        },
    )
    version = confirmed.json()["observed_session_version"]
    headers = {
        "X-Request-ID": "v2-context-candidates",
        "X-Expected-Session-Version": str(version),
        "X-Actor-Ref": "demo:local",
    }
    candidates_response = client.get(
        f"/v1/sessions/{session_id}/p1/context-candidates",
        params={"age_months": 60},
        headers=headers,
    )
    assert candidates_response.status_code == 200
    candidates = candidates_response.json()["payload"]["candidates"]
    assert 1 <= len(candidates) <= 3
    candidate_ids = [item["activity_ref"]["id"] for item in candidates]
    assert candidate_ids == sorted(candidate_ids)
    material_ids = sorted(
        {material_id for item in candidates for material_id in item["material_option_ids"]}
    )

    classified_tags = classified.json()["interest_tags"]
    readiness_ids = sorted({
        readiness_id
        for candidate in candidates
        for readiness_id in candidate["readiness_ids"]
    })
    profile = {
        "contract_name": "ChildLearningProfileContextV2",
        "contract_version": "2.0",
        "profile_declared_by": "CAREGIVER",
        "profile_recorded_at": datetime.now(UTC).isoformat(),
        "preference_tags_confirmed": True,
        "interests": [tag["concept_id"] for tag in classified_tags],
        "dislikes": [],
        "readiness_ids": readiness_ids,
        "available_material_option_ids": material_ids,
        "learning_support_ids": [],
    }
    body = {
        "contract_name": "P1ContextOptionsRequestV2",
        "contract_version": "2.0",
        "age_months": 60,
        "child_profile": profile,
        "adult_participating": True,
        "candidate_activity_ids": candidate_ids,
        "supervision_confirmed_activity_ids": candidate_ids,
    }
    finalized = client.post(
        f"/v1/sessions/{session_id}/p1/context-options/finalize",
        headers={**headers, "X-Request-ID": "v2-context-finalize"},
        json=body,
    )
    assert finalized.status_code == 200, (material_ids, finalized.text)
    final_payload = finalized.json()["payload"]
    assert final_payload["contract_name"] == "P1ContextOptionsV1"
    assert "personalization_comparison" not in final_payload
    assert "baseline_activity_recommendations" not in final_payload

    unconfirmed_profile = {**profile, "preference_tags_confirmed": False}
    unconfirmed_tags = client.post(
        f"/v1/sessions/{session_id}/p1/context-options/finalize",
        headers={**headers, "X-Request-ID": "v2-context-unconfirmed-preference"},
        json={**body, "child_profile": unconfirmed_profile},
    )
    assert unconfirmed_tags.status_code == 422
    assert unconfirmed_tags.json()["failure"]["code"] == "REQUEST_VALIDATION_FAILED"
    assert "ANIMAL_GENERIC" not in unconfirmed_tags.text

    injected_activity = "ACT-9999"
    injected = client.post(
        f"/v1/sessions/{session_id}/p1/context-options/finalize",
        headers={**headers, "X-Request-ID": "v2-context-injected-candidate"},
        json={
            **body,
            "candidate_activity_ids": [injected_activity],
            "supervision_confirmed_activity_ids": [injected_activity],
        },
    )
    assert injected.status_code == 409
    assert injected.json()["failure"]["code"] == "CONTEXT_CANDIDATE_SET_STALE"

    invalid_profile = {**profile, "adult_supervision_available": "DIRECT"}
    rejected = client.post(
        f"/v1/sessions/{session_id}/p1/context-options/finalize",
        headers={**headers, "X-Request-ID": "v2-context-legacy-supervision"},
        json={**body, "child_profile": invalid_profile},
    )
    assert rejected.status_code == 422
    assert rejected.json()["failure"]["code"] == "REQUEST_VALIDATION_FAILED"
    assert rejected.json()["provenance"]["source_contracts"] == [
        "P1ContextOptionsRequestV2"
    ]
    assert "adult_supervision_available" not in rejected.text

    eligible_option = next(
        (
            option
            for option in final_payload["options"]
            if not option["prerequisite_activity_ids"]
        ),
        None,
    )
    assert eligible_option is not None, (
        "V2 finalization must keep an eligible no-history alternative"
    )
    context = _command(
        client,
        session_id=session_id,
        version=version,
        key="v2-context-set-p1-context",
        route="/p1-context",
        method="put",
        payload={
            "operation": "SET_P1_CONTEXT",
            "user_initiated": True,
            "context": {
                "contract_name": "P1ContextV3",
                "contract_version": "3.0",
                "candidate_selection_mode": "CONTEXTUAL_SHORTLIST",
                "session_id": session_id,
                "expected_session_version": version,
                "age_months": 60,
                "readiness_ids": readiness_ids,
                "completed_activity_ids": [],
                "available_material_option_ids": material_ids,
                "supervision_level": eligible_option["minimum_supervision"],
                "policy_flags": eligible_option["policy_constraints"],
                "candidate_status": "ACTIVE_FIXTURE",
                "gate_a_confirmed": True,
                "selected_activity_id": eligible_option["activity_ref"]["id"],
                "selected_activity_version": eligible_option["activity_ref"]["version"],
            },
        },
    )
    assert context.status_code == 200, context.text
    version = context.json()["observed_session_version"]
    filtered = _command(
        client,
        session_id=session_id,
        version=version,
        key="v2-context-run-p1-filter",
        route="/p1-filter",
        payload={"operation": "RUN_P1_FILTER", "user_initiated": True},
    )
    assert filtered.status_code == 200, filtered.text
    filter_result = filtered.json()["payload"]["filter_result"]
    assert filter_result["status"] == "VALID_CANDIDATE", filter_result["reason_codes"]
    version = filtered.json()["observed_session_version"]
    prepared = _command(
        client,
        session_id=session_id,
        version=version,
        key="v2-context-prepare-experience",
        route="/experience/prepare",
        payload={"operation": "PREPARE_EXPERIENCE", "user_initiated": True},
    )
    assert prepared.status_code == 200, prepared.text
    assert prepared.json()["payload"]["status"] == "AWAITING_ADULT_GATE_B"
    version = prepared.json()["observed_session_version"]
    approved = _command(
        client,
        session_id=session_id,
        version=version,
        key="v2-context-approve-gate-b",
        route="/gate-b/approve",
        payload={"operation": "APPROVE_GATE_B", "user_initiated": True, "approved": True},
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["payload"]["generation_called"] is False


def test_empty_activity_list_explains_unmapped_topic() -> None:
    client, _ = _client(vision=_CountingVision(label="spaceship"))
    session_id, version = _create_session(client)
    uploaded = client.post(
        f"/v1/sessions/{session_id}/media/image",
        headers=_headers(session_id, version, "unmapped-topic-upload"),
        files={"image": ("synthetic.png", _IMAGE, "image/png")},
    )
    version = uploaded.json()["observed_session_version"]
    understood = _command(
        client,
        session_id=session_id,
        version=version,
        key="unmapped-topic-understanding",
        route="/understanding",
        payload={"operation": "RUN_UNDERSTANDING", "user_initiated": True},
    )
    version = understood.json()["observed_session_version"]
    confirmed = _command(
        client,
        session_id=session_id,
        version=version,
        key="unmapped-topic-confirm",
        route="/gate-a/confirm",
        payload={
            "operation": "CONFIRM_GATE_A",
            "user_initiated": True,
            "primary_anchor_id": "subject-1",
            "confirmation": {
                "contract_name": "GateAConfirmationV1",
                "contract_version": "1.0",
                "meaning_version": 1,
                "confirmed_claim_ids": ["subject-1"],
                "correction": None,
            },
        },
    )
    version = confirmed.json()["observed_session_version"]
    suggestions = client.post(
        f"/v1/sessions/{session_id}/p1/activity-suggestions",
        headers={
            "X-Request-ID": "unmapped-topic-suggestions",
            "X-Expected-Session-Version": str(version),
            "X-Actor-Ref": "demo:local",
        },
        json={
            "contract_name": "P1ActivitySuggestionsRequestV1",
            "contract_version": "1.0",
            "age_months": 60,
            "child_profile": {
                "contract_name": "ConfirmedChildPreferencesV1",
                "contract_version": "1.0",
                "profile_declared_by": "CAREGIVER",
                "profile_recorded_at": datetime.now(UTC).isoformat(),
                "preference_tags_confirmed": True,
                "interests": [],
                "dislikes": [],
            },
            "adult_participating": True,
            "caregiver_participating": False,
        },
    )

    assert suggestions.status_code == 200, suggestions.text
    payload = suggestions.json()["payload"]
    assert payload["contract_name"] == "ActivityRecommendationSetV3"
    assert payload["total_count"] == 0
    assert payload["options"] == []
    assert payload["empty_reason"] == "TOPIC_UNMAPPED"


def test_complete_activity_suggestions_and_p1_v4_ignore_readiness_material_and_history() -> None:
    ranker = _TestActivityRanker()
    client, _ = _client(vision=_CountingVision(label="con chim"), activity_ranker=ranker)
    session_id, version = _create_session(client)
    uploaded = client.post(
        f"/v1/sessions/{session_id}/media/image",
        headers=_headers(session_id, version, "v4-discovery-upload"),
        files={"image": ("synthetic.png", _IMAGE, "image/png")},
    )
    assert uploaded.status_code == 200
    version = uploaded.json()["observed_session_version"]
    inferred = _command(
        client,
        session_id=session_id,
        version=version,
        key="v4-discovery-understanding",
        route="/understanding",
        payload={"operation": "RUN_UNDERSTANDING", "user_initiated": True},
    )
    version = inferred.json()["observed_session_version"]
    confirmed = _command(
        client,
        session_id=session_id,
        version=version,
        key="v4-discovery-gate-a",
        route="/gate-a/confirm",
        payload={
            "operation": "CONFIRM_GATE_A",
            "user_initiated": True,
            "primary_anchor_id": "subject-1",
            "confirmation": {
                "contract_name": "GateAConfirmationV1",
                "contract_version": "1.0",
                "meaning_version": 1,
                "confirmed_claim_ids": ["subject-1"],
                "correction": None,
            },
        },
    )
    version = confirmed.json()["observed_session_version"]
    headers = {
        "X-Request-ID": "v4-discovery-read-all",
        "X-Expected-Session-Version": str(version),
        "X-Actor-Ref": "demo:local",
    }
    suggestions_response = client.post(
        f"/v1/sessions/{session_id}/p1/activity-suggestions",
        headers=headers,
        json={
            "contract_name": "P1ActivitySuggestionsRequestV1",
            "contract_version": "1.0",
            "age_months": 60,
            "child_profile": {
                "contract_name": "ConfirmedChildPreferencesV1",
                "contract_version": "1.0",
                "profile_declared_by": "CAREGIVER",
                "profile_recorded_at": datetime.now(UTC).isoformat(),
                "preference_tags_confirmed": True,
                "interests": ["ANIMAL_GENERIC"],
                "dislikes": [],
            },
            "adult_participating": True,
            "caregiver_participating": False,
        },
    )
    assert suggestions_response.status_code == 200, suggestions_response.text
    suggestions = suggestions_response.json()["payload"]
    assert suggestions["contract_name"] == "ActivityRecommendationSetV3"
    assert suggestions["empty_reason"] is None
    assert suggestions["total_count"] == len(suggestions["options"]) > 3
    suggested_ids = {item["activity_id"] for item in suggestions["options"]}
    assert "ACT-0102" in suggested_ids
    assert "ACT-0043" not in suggested_ids
    assert "ACT-0114" not in suggested_ids
    assert any("Khớp sở thích" in item["match_reason_vi"] for item in suggestions["options"])
    ranking_response = client.post(
        f"/v1/sessions/{session_id}/p1/activity-suggestions/rank",
        headers={
            "X-Request-ID": "v4-discovery-rank",
            "X-Expected-Session-Version": str(version),
            "X-Actor-Ref": "demo:local",
        },
        json={
            "contract_name": "P1ActivitySuggestionsRequestV1",
            "contract_version": "1.0",
            "age_months": 60,
            "child_profile": {
                "contract_name": "ConfirmedChildPreferencesV1",
                "contract_version": "1.0",
                "profile_declared_by": "CAREGIVER",
                "profile_recorded_at": datetime.now(UTC).isoformat(),
                "preference_tags_confirmed": True,
                "interests": ["ANIMAL_GENERIC"],
                "dislikes": [],
            },
            "adult_participating": True,
            "caregiver_participating": False,
        },
    )
    assert ranking_response.status_code == 200, ranking_response.text
    ranked = ranking_response.json()["payload"]
    assert ranked["contract_name"] == "ActivityRankingResultV1"
    assert len(ranked["ranked_activity_ids"]) == 3
    assert set(ranked["ranked_activity_ids"]) <= suggested_ids
    assert len(ranker.requests) == 1
    assert {item.activity_id for item in ranker.requests[0].candidates} == suggested_ids
    selected = suggestions["options"][0]

    context = _command(
        client,
        session_id=session_id,
        version=version,
        key="v4-discovery-set-context",
        route="/p1-context",
        method="put",
        payload={
            "operation": "SET_P1_CONTEXT",
            "user_initiated": True,
            "context": {
                "contract_name": "P1ContextV4",
                "contract_version": "4.0",
                "candidate_selection_mode": "COMPLETE_TOPIC_AGE_LIST",
                "discovery_policy": "TOPIC_AGE_SAFETY_DISCOVERY_V1",
                "session_id": session_id,
                "expected_session_version": version,
                "age_months": 60,
                "readiness_ids": None,
                "completed_activity_ids": None,
                "available_material_option_ids": None,
                "supervision_level": None,
                "policy_flags": None,
                "candidate_status": None,
                "gate_a_confirmed": True,
                "selected_activity_id": selected["activity_id"],
                "selected_activity_version": selected["activity_version"],
                "caregiver_participating": False,
                "adult_participating": True,
            },
        },
    )
    assert context.status_code == 200, context.text
    version = context.json()["observed_session_version"]
    filtered = _command(
        client,
        session_id=session_id,
        version=version,
        key="v4-discovery-filter",
        route="/p1-filter",
        payload={"operation": "RUN_P1_FILTER", "user_initiated": True},
    )
    assert filtered.status_code == 200, filtered.text
    assert filtered.json()["payload"]["filter_result"]["status"] == "VALID_CANDIDATE"
    version = filtered.json()["observed_session_version"]
    prepared = _command(
        client,
        session_id=session_id,
        version=version,
        key="v4-discovery-prepare",
        route="/experience/prepare",
        payload={"operation": "PREPARE_EXPERIENCE", "user_initiated": True},
    )
    assert prepared.status_code == 200, prepared.text
    assert prepared.json()["payload"]["status"] == "AWAITING_ADULT_GATE_B"


class _TestImageDecoder:
    def read_metadata(self, snapshot: bytes) -> ImageMetadataSignals | None:
        if not snapshot.startswith(b"\x89PNG\r\n\x1a\n"):
            return None
        return ImageMetadataSignals("png_pipe", "png", "rgb24", 64, 64)

    def probe_frame_count(self, snapshot: bytes) -> int:
        return 1

    def decode_one_frame(self, snapshot: bytes) -> DecodedFrameSignals:
        return DecodedFrameSignals(64, 64, "rgb24")


class _CountingVision:
    def __init__(self, *, label: str = "cây", empty: bool = False) -> None:
        self.calls = 0
        self.label = label
        self.empty = empty

    def understand(self, request: VisionUnderstandingRequestV2) -> VisionUnderstandingSuccessV2:
        self.calls += 1
        catalog = vision_profile_catalog_v2()
        profile = catalog.resolve(request.requested_profile_id)
        policy = synthetic_prohibited_lexicon()
        return VisionUnderstandingSuccessV2(
            correlation_id=request.correlation_id,
            executed_at=datetime(2026, 9, 18, tzinfo=UTC),
            source_image_ref=request.source_image_ref,
            profile_id=profile.profile_id,
            profile_catalog_hash=vision_profile_catalog_hash_v2(catalog),
            attempt_number=1,
            repair_attempted=False,
            content_policy_version=policy.lexicon_version,
            policy_match_view_version=VISION_POLICY_MATCH_VIEW_VERSION,
            policy_execution_state="PASSED",
            status="SUCCEEDED",
            entities=()
            if self.empty
            else (
                EntityCandidateV1(
                    observation_id="subject-1",
                    label=ObservedTextV1(
                        value=self.label,
                        language=TextLanguageDeclarationV1(status="DECLARED", tags=("vi",)),
                    ),
                    confidence=0.96,
                ),
            ),
            actions=(),
            relations=(),
            themes=(),
            ambiguous_regions=(),
            adapter_version=profile.adapter_version,
            config_hash=vision_profile_config_hash_v2(profile),
            model_provenance=profile.model_provenance,
        )


class _CountingLocalizer:
    def __init__(self) -> None:
        self.calls = 0

    def localize(self, request: object) -> dict[str, dict[str, float]]:
        self.calls += 1
        return {
            "subject-1": {"x": 0.1, "y": 0.1, "width": 0.2, "height": 0.2},
        }


def _client(
    *,
    vision: _CountingVision | None = None,
    scene_localizer: _CountingLocalizer | None = None,
    child_preference_classifier: ChildPreferenceClassifierPort | None = None,
    activity_ranker: ActivityRankerPort | None = None,
) -> tuple[TestClient, _CountingVision]:
    artifacts = InMemoryArtifactStore()
    idempotency = InMemoryIdempotencyStore()
    sessions = EphemeralSessionService(
        sessions=InMemorySessionRepository(),
        idempotency=idempotency,
        artifacts=artifacts,
        workflow_data=InMemoryDemoWorkflowStore(),
    )
    actual_vision = vision or _CountingVision()
    demo = LiveImageDemoService(
        sessions=sessions,
        artifacts=artifacts,
        idempotency=idempotency,
        admission=Feat018ImageAdmission(_TestImageDecoder()),
        vision=actual_vision,
        renderer_source_grants=InMemoryRendererSourceGrantStore(),
        scene_localizer=scene_localizer,
    )
    repo_root = Path(__file__).resolve().parents[3]
    p1_library = load_p1_template_library(repo_root, include_mvp=True, include_expansion=True)
    semantic_catalog = load_activity_semantic_catalog(repo_root)
    semantic_catalog_v2 = load_activity_semantic_catalog_v2(repo_root, include_expansion=True)
    auto_rig = AutoRigService(
        artifacts=artifacts,
        grants=InMemoryRigPackageGrantStore(),
        jobs=InMemoryJobStore(),
    )
    supervised_flow = SupervisedFlowService(
        sessions=sessions,
        idempotency=idempotency,
        p1_compiler=P1ExperienceCompiler(
            p1_library.templates,
            p1_library.objective_titles_vi,
        ),
        semantic_catalog=semantic_catalog,
        semantic_catalog_v2=semantic_catalog_v2,
        catalog_metadata=FileWorkflowCatalogMetadata(repo_root),
        renderer_source_capability_issuer=demo.issue_renderer_source_capability,
        auto_rig_service=auto_rig,
        activity_ranker=activity_ranker,
    )
    return TestClient(
        create_app(
            session_service=sessions,
            live_image_demo_service=demo,
            supervised_flow_service=supervised_flow,
            auto_rig_service=auto_rig,
            child_preference_classifier=child_preference_classifier,
            activity_ranker=activity_ranker,
        )
    ), actual_vision


def _create_session(client: TestClient) -> tuple[str, int]:
    session_id = "d5f439fa-3065-4a5e-a06e-52a57514781f"
    response = client.post(
        "/v1/sessions",
        json={
            "request_id": "create-request-1",
            "idempotency_key": "create-key-1",
            "session_id": session_id,
            "expected_session_version": 0,
            "actor_ref": "demo:local",
            "payload": {"operation": "CREATE_SESSION"},
        },
    )
    assert response.status_code == 201
    return session_id, response.json()["observed_session_version"]


def _headers(session_id: str, version: int, key: str) -> dict[str, str]:
    return {
        "X-Request-ID": f"request-{key}",
        "X-Expected-Session-Version": str(version),
        "Idempotency-Key": key,
        "X-Actor-Ref": "demo:local",
        "X-Synthetic-Non-Child-Confirmed": "true",
    }


def test_image_normalization_keeps_original_and_derived_artifact_provenance() -> None:
    client, _ = _client()
    session_id, version = _create_session(client)
    response = client.post(
        f"/v1/sessions/{session_id}/media/image",
        headers=_headers(session_id, version, "normalized-upload"),
        data={
            "source_media_type": "image/webp",
            "normalization_policy": "EXPO_IMAGE_MANIPULATOR_PNG_V1",
        },
        files={
            "image": ("drawing.png", _IMAGE, "image/png"),
            "source_image": ("source.webp", _SOURCE_WEBP, "image/webp"),
        },
    )

    assert response.status_code == 200, response.text
    receipt = response.json()["payload"]
    assert receipt["contract_name"] == "ImageAdmissionReceiptV2"
    assert receipt["normalization_policy"] == "EXPO_IMAGE_MANIPULATOR_PNG_V1"
    assert receipt["source_content_type"] == "image/webp"
    assert receipt["source_byte_length"] == len(_SOURCE_WEBP)
    assert receipt["content_type"] == "image/png"
    assert receipt["original_image_ref"]["sha256"] != receipt["source_image_ref"]["sha256"]


def test_image_upload_rejects_animated_and_conflicting_source_metadata() -> None:
    client, _ = _client()
    session_id, version = _create_session(client)
    animated_png = b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\x08acTL" + bytes(12)
    animated = client.post(
        f"/v1/sessions/{session_id}/media/image",
        headers=_headers(session_id, version, "animated-upload"),
        files={"image": ("animated.png", animated_png, "image/png")},
    )
    assert animated.status_code == 422
    assert animated.json()["failure"]["code"] == "IMAGE_ANIMATED_UNSUPPORTED"

    conflict = client.post(
        f"/v1/sessions/{session_id}/media/image",
        headers=_headers(session_id, version, "conflicting-upload"),
        data={"source_media_type": "image/jpeg"},
        files={"image": ("drawing.png", _IMAGE, "image/png")},
    )
    assert conflict.status_code == 422
    assert conflict.json()["failure"]["code"] == "IMAGE_METADATA_CONFLICT"


def _command(
    client: TestClient,
    *,
    session_id: str,
    version: int,
    key: str,
    route: str,
    payload: dict[str, object],
    method: str = "post",
):
    return getattr(client, method)(
        f"/v1/sessions/{session_id}{route}",
        json={
            "request_id": f"request-{key}",
            "idempotency_key": f"idempotency-{key}",
            "session_id": session_id,
            "expected_session_version": version,
            "actor_ref": "demo:local",
            "payload": payload,
        },
    )


def test_session_image_upload_is_admitted_then_requires_an_explicit_understanding_command() -> None:
    localizer = _CountingLocalizer()
    client, vision = _client(scene_localizer=localizer)
    session_id, version = _create_session(client)

    uploaded = client.post(
        f"/v1/sessions/{session_id}/media/image",
        headers=_headers(session_id, version, "upload-1"),
        files={"image": ("synthetic.png", _IMAGE, "image/png")},
    )

    assert uploaded.status_code == 200
    uploaded_body = uploaded.json()
    assert uploaded_body["status"] == "SUCCEEDED"
    assert uploaded_body["payload"]["decision"] == "ADMITTED"
    assert uploaded_body["payload"]["narration_status"] == "NOT_SUPPLIED"
    assert vision.calls == 0
    session_version = uploaded_body["observed_session_version"]

    rejected_implicit = client.post(
        f"/v1/sessions/{session_id}/understanding",
        json={
            "request_id": "understanding-request-implicit",
            "idempotency_key": "understanding-key-implicit",
            "session_id": session_id,
            "expected_session_version": session_version,
            "actor_ref": "demo:local",
            "payload": {"operation": "RUN_UNDERSTANDING", "user_initiated": False},
        },
    )
    assert rejected_implicit.status_code == 422
    assert vision.calls == 0

    started = client.post(
        f"/v1/sessions/{session_id}/understanding",
        json={
            "request_id": "understanding-request-explicit",
            "idempotency_key": "understanding-key-explicit",
            "session_id": session_id,
            "expected_session_version": session_version,
            "actor_ref": "demo:local",
            "payload": {"operation": "RUN_UNDERSTANDING", "user_initiated": True},
        },
    )

    assert started.status_code == 200
    assert started.json()["status"] == "SUCCEEDED"
    assert started.json()["payload"]["narration_status"] == "NOT_SUPPLIED"
    directions = started.json()["payload"]["topic_directions"]
    assert 1 <= len(directions) <= 3
    assert directions[0]["title_vi"].startswith("Cùng khám phá")
    assert directions[0]["source_claim_ids"]
    assert all("chi tiết trong tranh" not in item["title_vi"] for item in directions)
    assert vision.calls == 1
    assert localizer.calls == 0


def test_image_upload_requires_synthetic_non_child_confirmation_and_is_idempotent() -> None:
    client, vision = _client()
    session_id, version = _create_session(client)
    headers = _headers(session_id, version, "upload-once")

    first = client.post(
        f"/v1/sessions/{session_id}/media/image",
        headers=headers,
        files={"image": ("synthetic.png", _IMAGE, "image/png")},
    )
    replay = client.post(
        f"/v1/sessions/{session_id}/media/image",
        headers=headers,
        files={"image": ("synthetic.png", _IMAGE, "image/png")},
    )

    assert first.status_code == 200
    assert replay.status_code == 200
    assert replay.headers["Idempotency-Replayed"] == "true"
    assert replay.json() == first.json()
    assert vision.calls == 0

    missing_confirmation = client.post(
        f"/v1/sessions/{session_id}/media/image",
        headers={
            **_headers(session_id, version, "upload-no-confirmation"),
            "X-Synthetic-Non-Child-Confirmed": "false",
        },
        files={"image": ("synthetic.png", _IMAGE, "image/png")},
    )
    assert missing_confirmation.status_code == 422
    assert missing_confirmation.json()["failure"]["code"] == (
        "SYNTHETIC_NON_CHILD_CONFIRMATION_REQUIRED"
    )


def test_typed_narration_is_forwarded_as_text_without_an_asr_call() -> None:
    client, vision = _client()
    session_id, version = _create_session(client)
    uploaded = client.post(
        f"/v1/sessions/{session_id}/media/image",
        headers=_headers(session_id, version, "typed-image"),
        files={"image": ("synthetic.png", _IMAGE, "image/png")},
    )
    version = uploaded.json()["observed_session_version"]
    started = client.post(
        f"/v1/sessions/{session_id}/understanding",
        json={
            "request_id": "typed-understanding",
            "idempotency_key": "typed-understanding-key",
            "session_id": session_id,
            "expected_session_version": version,
            "actor_ref": "demo:local",
            "payload": {
                "operation": "RUN_UNDERSTANDING",
                "user_initiated": True,
                "narration": {
                    "kind": "TEXT",
                    "text": "Con mèo đang tìm bông hoa.",
                    "language": "vi",
                    "provenance": "TEXT_TYPED",
                },
            },
        },
    )

    assert started.status_code == 200
    body = started.json()
    assert body["status"] == "SUCCEEDED"
    assert body["payload"]["narration_status"] == "TEXT_SUPPLIED"
    assert body["payload"]["narration"]["transcript"] == "Con mèo đang tìm bông hoa."
    assert body["payload"]["asr_claims"][0]["source"] == "TEXT_TYPED"
    assert vision.calls == 1


def test_empty_vision_result_can_requery_once_then_confirm_an_adult_subject() -> None:
    client, vision = _client(vision=_CountingVision(empty=True))
    session_id, version = _create_session(client)
    uploaded = client.post(
        f"/v1/sessions/{session_id}/media/image",
        headers=_headers(session_id, version, "empty-image"),
        files={"image": ("synthetic.png", _IMAGE, "image/png")},
    )
    version = uploaded.json()["observed_session_version"]

    result = client.post(
        f"/v1/sessions/{session_id}/understanding",
        json={
            "request_id": "empty-understanding",
            "idempotency_key": "empty-understanding-key",
            "session_id": session_id,
            "expected_session_version": version,
            "actor_ref": "demo:local",
            "payload": {"operation": "RUN_UNDERSTANDING", "user_initiated": True},
        },
    )

    assert result.status_code == 200
    body = result.json()
    assert body["status"] == "BLOCKED"
    assert body["payload"]["reason_codes"] == ["NO_GROUNDED_CLAIMS"]
    assert body["payload"]["understanding_progress"]["gate_a_ready"] is False
    assert body["payload"]["understanding_progress"]["stage"] == "BLOCKED_NO_GROUNDED_CLAIMS"
    version = body["observed_session_version"]

    requery = client.post(
        f"/v1/sessions/{session_id}/understanding",
        json={
            "request_id": "empty-subject-requery",
            "idempotency_key": "empty-subject-requery-key",
            "session_id": session_id,
            "expected_session_version": version,
            "actor_ref": "demo:local",
            "payload": {
                "operation": "REQUERY_UNDERSTANDING",
                "user_initiated": True,
                "prior_run_id": "empty-understanding",
                "direction_revision": 1,
                "selected_direction": "con chim",
                "correction": "con chim",
            },
        },
    )
    assert requery.status_code == 200
    assert requery.json()["status"] == "BLOCKED"
    assert requery.json()["payload"]["understanding_progress"]["direction_revision"] == 1
    assert requery.json()["payload"]["reason_codes"] == ["NO_GROUNDED_CLAIMS"]

    confirmed = client.post(
        f"/v1/sessions/{session_id}/gate-a/confirm",
        json={
            "request_id": "adult-bird-confirmation",
            "idempotency_key": "adult-bird-confirmation-key",
            "session_id": session_id,
            "expected_session_version": requery.json()["observed_session_version"],
            "actor_ref": "demo:local",
            "payload": {
                "operation": "CONFIRM_GATE_A",
                "user_initiated": True,
                "primary_anchor_id": None,
                "confirmation": {
                    "contract_name": "GateAConfirmationV2",
                    "contract_version": "2.0",
                    "meaning_version": 2,
                    "confirmed_claim_ids": [],
                    "adult_subject_label": "con chim",
                },
            },
        },
    )
    assert confirmed.status_code == 200
    confirmed_payload = confirmed.json()["payload"]
    anchor = confirmed_payload["anchor_set"]["primary_anchor"]
    assert confirmed.json()["status"] == "SUCCEEDED"
    assert confirmed_payload["primary_subject_origin"] == "ADULT_ENTERED"
    assert anchor["provenance"]["source_claim_ids"] == []
    assert anchor["provenance"]["source_contract_name"] == "AdultSubjectConfirmationV1"
    assert anchor["provenance"]["source_adult_assertion_id"].startswith("adult-assertion-")
    assert vision.calls == 2


def test_typed_narration_is_fused_with_matching_visual_claim_and_topic_is_bounded() -> None:
    client, vision = _client(vision=_CountingVision(label="butterfly"))
    session_id, version = _create_session(client)
    uploaded = client.post(
        f"/v1/sessions/{session_id}/media/image",
        headers=_headers(session_id, version, "fusion-image"),
        files={"image": ("synthetic.png", _IMAGE, "image/png")},
    )
    version = uploaded.json()["observed_session_version"]
    result = client.post(
        f"/v1/sessions/{session_id}/understanding",
        json={
            "request_id": "fusion-understanding",
            "idempotency_key": "fusion-understanding-key",
            "session_id": session_id,
            "expected_session_version": version,
            "actor_ref": "demo:local",
            "payload": {
                "operation": "RUN_UNDERSTANDING",
                "user_initiated": True,
                "narration": {
                    "kind": "TEXT",
                    "text": "Con bướm đang bay trên bãi cỏ.",
                    "language": "vi",
                    "provenance": "TEXT_TYPED",
                },
            },
        },
    )

    assert result.status_code == 200
    body = result.json()
    assert body["status"] == "SUCCEEDED"
    assert body["payload"]["fused_claims"]
    topic = body["payload"]["understanding_progress"]["topic"]
    assert 10 <= topic["word_count"] <= 18
    assert "con bướm" in topic["text"]
    assert vision.calls == 1


def test_direction_requery_rechecks_the_admitted_image_and_exposes_progress() -> None:
    client, vision = _client()
    session_id, version = _create_session(client)
    uploaded = client.post(
        f"/v1/sessions/{session_id}/media/image",
        headers=_headers(session_id, version, "requery-image"),
        files={"image": ("synthetic.png", _IMAGE, "image/png")},
    )
    version = uploaded.json()["observed_session_version"]
    first = client.post(
        f"/v1/sessions/{session_id}/understanding",
        json={
            "request_id": "requery-first",
            "idempotency_key": "requery-first-key",
            "session_id": session_id,
            "expected_session_version": version,
            "actor_ref": "demo:local",
            "payload": {"operation": "RUN_UNDERSTANDING", "user_initiated": True},
        },
    )
    version = first.json()["observed_session_version"]
    second = client.post(
        f"/v1/sessions/{session_id}/understanding",
        json={
            "request_id": "requery-second",
            "idempotency_key": "requery-second-key",
            "session_id": session_id,
            "expected_session_version": version,
            "actor_ref": "demo:local",
            "payload": {
                "operation": "REQUERY_UNDERSTANDING",
                "user_initiated": True,
                "prior_run_id": "requery-first",
                "direction_revision": 1,
                "selected_direction": "một hướng quan sát khác",
                "correction": "",
            },
        },
    )

    assert second.status_code == 200, second.text
    assert second.json()["status"] == "SUCCEEDED"
    assert second.json()["payload"]["understanding_progress"]["direction_revision"] == 1
    assert second.json()["payload"]["understanding_progress"]["stage"] == "TOPIC_READY"
    assert vision.calls == 2

    progress = client.get(
        f"/v1/sessions/{session_id}/understanding/progress",
        headers={"X-Expected-Session-Version": str(second.json()["observed_session_version"])},
    )
    assert progress.status_code == 200
    assert progress.json()["payload"]["understanding_progress"]["run_id"] == "requery-second"


def test_subject_selection_replaces_topic_without_rendering_direction_cards() -> None:
    client, vision = _client(vision=_CountingVision(label="bird"))
    session_id, version = _create_session(client)
    uploaded = client.post(
        f"/v1/sessions/{session_id}/media/image",
        headers=_headers(session_id, version, "subject-image"),
        files={"image": ("synthetic.png", _IMAGE, "image/png")},
    )
    version = uploaded.json()["observed_session_version"]
    started = client.post(
        f"/v1/sessions/{session_id}/understanding",
        json={
            "request_id": "subject-understanding",
            "idempotency_key": "subject-understanding-key",
            "session_id": session_id,
            "expected_session_version": version,
            "actor_ref": "demo:local",
            "payload": {"operation": "RUN_UNDERSTANDING", "user_initiated": True},
        },
    )
    version = started.json()["observed_session_version"]
    selected = client.post(
        f"/v1/sessions/{session_id}/understanding",
        json={
            "request_id": "subject-select",
            "idempotency_key": "subject-select-key",
            "session_id": session_id,
            "expected_session_version": version,
            "actor_ref": "demo:local",
            "payload": {
                "operation": "SELECT_SUBJECT",
                "user_initiated": True,
                "selected_subject_id": "subject-1",
                "selected_subject_label": "con chim",
            },
        },
    )

    assert selected.status_code == 200
    body = selected.json()
    assert body["status"] == "SUCCEEDED"
    assert body["payload"]["subject_selection"]["selected_subject_id"] == "subject-1"
    assert "con chim" in body["payload"]["subject_selection"]["sentence_vi"]
    assert body["payload"]["understanding_progress"]["stage"] == "SUBJECT_SELECTED"
    assert vision.calls == 1


def test_audio_is_stored_after_image_and_never_sent_without_configured_asr() -> None:
    client, vision = _client()
    session_id, version = _create_session(client)
    uploaded = client.post(
        f"/v1/sessions/{session_id}/media/image",
        headers=_headers(session_id, version, "audio-image"),
        files={"image": ("synthetic.png", _IMAGE, "image/png")},
    )
    version = uploaded.json()["observed_session_version"]
    audio = b"RIFF" + b"\x00" * 4 + b"WAVE" + b"synthetic-wav"
    audio_upload = client.post(
        f"/v1/sessions/{session_id}/media/audio",
        headers={
            "X-Request-ID": "audio-upload",
            "X-Expected-Session-Version": str(version),
            "Idempotency-Key": "audio-upload-key",
            "X-Actor-Ref": "demo:local",
        },
        files={"audio": ("narration.wav", audio, "audio/wav")},
    )
    assert audio_upload.status_code == 200
    receipt = audio_upload.json()["payload"]
    assert receipt["content_type"] == "audio/wav"

    run = client.post(
        f"/v1/sessions/{session_id}/understanding",
        json={
            "request_id": "audio-understanding",
            "idempotency_key": "audio-understanding-key",
            "session_id": session_id,
            "expected_session_version": audio_upload.json()["observed_session_version"],
            "actor_ref": "demo:local",
            "payload": {
                "operation": "RUN_UNDERSTANDING",
                "user_initiated": True,
                "narration": {
                    "kind": "AUDIO",
                    "artifact_ref": receipt["artifact_ref"],
                    "sha256": receipt["sha256"],
                    "content_type": receipt["content_type"],
                    "byte_length": receipt["byte_length"],
                    "provenance": "RECORDED_AUDIO",
                },
            },
        },
    )
    assert run.status_code == 503
    assert run.json()["failure"]["code"] == "LIGHTNING_ASR_NOT_CONFIGURED"
    assert vision.calls == 0


def test_openapi_exposes_image_and_optional_narration_routes_but_not_video() -> None:
    client, _vision = _client()
    paths = client.get("/openapi.json").json()["paths"]
    assert "/v1/sessions/{session_id}/media/image" in paths
    assert "/v1/sessions/{session_id}/media/audio" in paths
    assert "/v1/sessions/{session_id}/understanding" in paths
    assert not any("video" in path for path in paths)
    assert "/v1/live-understanding" not in paths


def test_image_upload_transport_enforces_a_hard_multipart_body_cap() -> None:
    client, _vision = _client()
    response = client.post(
        "/v1/sessions/not-created/media/image",
        content=b"x" * 20_100_001,
        headers={"Content-Type": "multipart/form-data; boundary=unused"},
    )
    assert response.status_code == 413
    assert response.json()["failure"]["code"] == "UPLOAD_TOO_LARGE"


def test_under_three_p1_options_require_caregiver_and_candidates_show_direct_supervision() -> None:
    client, vision = _client()
    session_id, version = _create_session(client)
    uploaded = client.post(
        f"/v1/sessions/{session_id}/media/image",
        headers=_headers(session_id, version, "options-upload"),
        files={"image": ("synthetic.png", _IMAGE, "image/png")},
    )
    version = uploaded.json()["observed_session_version"]
    inferred = client.post(
        f"/v1/sessions/{session_id}/understanding",
        json={
            "request_id": "options-understanding",
            "idempotency_key": "options-understanding-key",
            "session_id": session_id,
            "expected_session_version": version,
            "actor_ref": "demo:local",
            "payload": {"operation": "RUN_UNDERSTANDING", "user_initiated": True},
        },
    )
    version = inferred.json()["observed_session_version"]
    confirmed = client.post(
        f"/v1/sessions/{session_id}/gate-a/confirm",
        json={
            "request_id": "options-gate-a",
            "idempotency_key": "options-gate-a-key",
            "session_id": session_id,
            "expected_session_version": version,
            "actor_ref": "demo:local",
            "payload": {
                "operation": "CONFIRM_GATE_A",
                "user_initiated": True,
                "primary_anchor_id": "subject-1",
                "confirmation": {
                    "contract_name": "GateAConfirmationV1",
                    "contract_version": "1.0",
                    "meaning_version": 1,
                    "confirmed_claim_ids": ["subject-1"],
                    "correction": None,
                },
            },
        },
    )
    assert confirmed.status_code == 200
    version = confirmed.json()["observed_session_version"]

    blocked_options = client.get(
        f"/v1/sessions/{session_id}/p1/context-options",
        params={"age_months": 30},
        headers={
            "X-Request-ID": "p1-options",
            "X-Expected-Session-Version": str(version),
            "X-Actor-Ref": "demo:local",
        },
    )
    assert blocked_options.status_code == 422
    assert blocked_options.json()["failure"]["code"] == "UNDER_THREE_CAREGIVER_REQUIRED"

    candidates = client.get(
        f"/v1/sessions/{session_id}/p1/context-candidates",
        params={"age_months": 30},
        headers={
            "X-Request-ID": "p1-under-three-candidates",
            "X-Expected-Session-Version": str(version),
            "X-Actor-Ref": "demo:local",
        },
    )
    assert candidates.status_code == 200
    for candidate in candidates.json()["payload"]["candidates"]:
        assert candidate["minimum_supervision"] == "DIRECT"
        assert candidate["supervision_label_vi"] == "Người chăm sóc ở bên và giám sát trực tiếp"

    legacy_context = _command(
        client,
        session_id=session_id,
        version=version,
        key="p1-under-three-legacy-context",
        route="/p1-context",
        method="put",
        payload={
            "operation": "SET_P1_CONTEXT",
            "user_initiated": True,
            "context": {
                "contract_name": "P1ContextV1",
                "contract_version": "1.0",
                "session_id": session_id,
                "expected_session_version": version,
                "age_months": 30,
                "readiness_ids": [],
                "completed_activity_ids": [],
                "available_material_option_ids": [],
                "supervision_level": "DIRECT",
                "policy_flags": [],
                "candidate_status": "ACTIVE_FIXTURE",
                "gate_a_confirmed": True,
            },
        },
    )
    assert legacy_context.status_code == 422
    assert legacy_context.json()["failure"]["code"] == "UNDER_THREE_CAREGIVER_REQUIRED"

    options = client.get(
        f"/v1/sessions/{session_id}/p1/context-options",
        params={"age_months": 30, "caregiver_participating": True},
        headers={
            "X-Request-ID": "p1-options-caregiver-confirmed",
            "X-Expected-Session-Version": str(version),
            "X-Actor-Ref": "demo:local",
        },
    )

    assert options.status_code == 200
    payload = options.json()["payload"]
    assert payload["contract_name"] == "P1ContextOptionsV1"
    assert payload["age_months"] == 30
    assert payload["confirmed_anchor_label"] == "cây"
    assert 1 <= len(payload["options"]) <= 3
    assert payload["activity_recommendations"]["options"]
    assert payload["activity_recommendations"]["options"][0]["title_vi"]
    assert options.json()["observed_session_version"] == version

    personalized = client.post(
        f"/v1/sessions/{session_id}/p1/context-options",
        headers={
            "X-Request-ID": "p1-options-profile",
            "X-Expected-Session-Version": str(version),
            "X-Actor-Ref": "demo:local",
        },
        json={
            "contract_name": "P1ContextOptionsRequestV1",
            "contract_version": "1.0",
            "age_months": 72,
            "child_profile": {
                "contract_name": "ChildLearningProfileContextV1",
                "contract_version": "1.0",
                "profile_declared_by": "CAREGIVER",
                "profile_recorded_at": datetime.now(UTC).isoformat(),
                "interests": ["PLANT_STRUCTURE"],
                "dislikes": [],
                "adult_confirmed_progress": [
                    {
                        "activity_id": "ACT-0055",
                        "objective_id": "OBJ_SCIENTIFIC_OBSERVATION",
                        "confirmed_at": datetime.now(UTC).date().isoformat(),
                        "confirmed_by": "GUIDE",
                    }
                ],
                "readiness_ids": ["READY_HANDLES_PLANT_SAMPLE"],
                "available_material_option_ids": [
                    "GMAT-0055-PRIMARY",
                    "GMAT-0055-SUBSTITUTE",
                ],
                "learning_support_ids": [],
            },
        },
    )
    assert personalized.status_code == 200
    personalized_payload = personalized.json()["payload"]
    comparison = personalized_payload["personalization_comparison"]
    assert comparison["contract_name"] == "P1PersonalizationComparisonV1"
    assert comparison["baseline_activity_ids"]
    assert comparison["personalized_activity_ids"] == [
        item["activity_ref"]["id"] for item in personalized_payload["options"]
    ]
    assert personalized_payload["baseline_activity_recommendations"]["options"]
    assert (
        personalized_payload["personalization_comparison"]["profile_provenance"]["declared_by"]
        == "CAREGIVER"
    )
    assert any(
        "Guide xác nhận OBJ_SCIENTIFIC_OBSERVATION ngày" in item["match_reason_vi"]
        for item in personalized_payload["activity_recommendations"]["options"]
    ), {
        "recommendations": personalized_payload["activity_recommendations"],
        "options": personalized_payload["options"],
    }
    assert personalized.json()["observed_session_version"] == version
    assert vision.calls == 1

    option = payload["options"][0]
    under_three_context = _command(
        client,
        session_id=session_id,
        version=version,
        key="p1-under-three-context-v2",
        route="/p1-context",
        method="put",
        payload={
            "operation": "SET_P1_CONTEXT",
            "user_initiated": True,
            "context": {
                "contract_name": "P1ContextV2",
                "contract_version": "2.0",
                "session_id": session_id,
                "expected_session_version": version,
                "age_months": 30,
                "caregiver_participating": True,
                "readiness_ids": option["readiness_ids"],
                "completed_activity_ids": option["prerequisite_activity_ids"],
                "available_material_option_ids": option["material_option_ids"],
                "supervision_level": "DIRECT",
                "policy_flags": option["policy_constraints"],
                "candidate_status": "ACTIVE_FIXTURE",
                "gate_a_confirmed": True,
                "selected_activity_id": option["activity_ref"]["id"],
                "selected_activity_version": option["activity_ref"]["version"],
            },
        },
    )
    assert under_three_context.status_code == 200, under_three_context.text
    filter_result = _command(
        client,
        session_id=session_id,
        version=under_three_context.json()["observed_session_version"],
        key="p1-under-three-filter-v2",
        route="/p1-filter",
        payload={"operation": "RUN_P1_FILTER", "user_initiated": True},
    )
    assert filter_result.status_code == 200, filter_result.text
    assert filter_result.json()["payload"]["filter_result"]["status"] == "VALID_CANDIDATE"


def test_gate_a_never_uses_age_only_fallback_for_background_only_raw_label() -> None:
    client, _vision = _client(vision=_CountingVision(label="grass"))
    session_id, version = _create_session(client)
    uploaded = client.post(
        f"/v1/sessions/{session_id}/media/image",
        headers=_headers(session_id, version, "fallback-upload"),
        files={"image": ("synthetic.png", _IMAGE, "image/png")},
    )
    version = uploaded.json()["observed_session_version"]
    inferred = client.post(
        f"/v1/sessions/{session_id}/understanding",
        json={
            "request_id": "fallback-understanding",
            "idempotency_key": "fallback-understanding-key",
            "session_id": session_id,
            "expected_session_version": version,
            "actor_ref": "demo:local",
            "payload": {"operation": "RUN_UNDERSTANDING", "user_initiated": True},
        },
    )
    version = inferred.json()["observed_session_version"]
    confirmed = client.post(
        f"/v1/sessions/{session_id}/gate-a/confirm",
        json={
            "request_id": "fallback-gate-a",
            "idempotency_key": "fallback-gate-a-key",
            "session_id": session_id,
            "expected_session_version": version,
            "actor_ref": "demo:local",
            "payload": {
                "operation": "CONFIRM_GATE_A",
                "user_initiated": True,
                "primary_anchor_id": "subject-1",
                "confirmation": {
                    "contract_name": "GateAConfirmationV1",
                    "contract_version": "1.0",
                    "meaning_version": 1,
                    "confirmed_claim_ids": ["subject-1"],
                    "correction": None,
                },
            },
        },
    )
    assert confirmed.status_code == 200

    options = client.get(
        f"/v1/sessions/{session_id}/p1/context-options",
        params={"age_months": 60},
        headers={
            "X-Request-ID": "fallback-options",
            "X-Expected-Session-Version": str(confirmed.json()["observed_session_version"]),
            "X-Actor-Ref": "demo:local",
        },
    )

    assert options.status_code == 200
    payload = options.json()["payload"]
    assert payload["options"]
    assert len(payload["options"]) <= 3
    assert all(item["activity_ref"]["id"] != "ACT-0026" for item in payload["options"])
    assert payload["activity_recommendations"]["options"]


def test_butterfly_non_primary_activity_option_is_strict_fit_without_rerunning_vision() -> None:
    client, vision = _client(vision=_CountingVision(label="butterfly"))
    session_id, version = _create_session(client)
    uploaded = client.post(
        f"/v1/sessions/{session_id}/media/image",
        headers=_headers(session_id, version, "butterfly-upload"),
        files={"image": ("synthetic.png", _IMAGE, "image/png")},
    )
    version = uploaded.json()["observed_session_version"]
    inferred = _command(
        client,
        session_id=session_id,
        version=version,
        key="butterfly-understanding",
        route="/understanding",
        payload={"operation": "RUN_UNDERSTANDING", "user_initiated": True},
    )
    version = inferred.json()["observed_session_version"]
    gate_a = _command(
        client,
        session_id=session_id,
        version=version,
        key="butterfly-gate-a",
        route="/gate-a/confirm",
        payload={
            "operation": "CONFIRM_GATE_A",
            "user_initiated": True,
            "primary_anchor_id": "subject-1",
            "confirmation": {
                "contract_name": "GateAConfirmationV1",
                "contract_version": "1.0",
                "meaning_version": 1,
                "confirmed_claim_ids": ["subject-1"],
                "correction": None,
            },
        },
    )
    version = gate_a.json()["observed_session_version"]
    options_response = client.get(
        f"/v1/sessions/{session_id}/p1/context-options",
        params={"age_months": 60},
        headers={
            "X-Request-ID": "butterfly-options",
            "X-Expected-Session-Version": str(version),
            "X-Actor-Ref": "demo:local",
        },
    )
    payload = options_response.json()["payload"]
    assert len(payload["options"]) >= 2
    option = payload["options"][1]
    assert option["activity_ref"]["id"].startswith("ACT-01")
    assert len(payload["options"]) <= 3
    assert payload["activity_recommendations"]["options"][0]["title_vi"]
    assert all(item["activity_ref"]["id"] != "ACT-0026" for item in payload["options"])
    assert all(item["activity_ref"]["id"] != "ACT-0029" for item in payload["options"])
    assert vision.calls == 1

    context = _command(
        client,
        session_id=session_id,
        version=version,
        key="butterfly-context",
        route="/p1-context",
        method="put",
        payload={
            "operation": "SET_P1_CONTEXT",
            "user_initiated": True,
            "context": {
                "contract_name": "P1ContextV1",
                "contract_version": "1.0",
                "session_id": session_id,
                "expected_session_version": version,
                "age_months": 60,
                "readiness_ids": option["readiness_ids"],
                "completed_activity_ids": option["prerequisite_activity_ids"],
                "available_material_option_ids": option["material_option_ids"],
                "supervision_level": option["minimum_supervision"],
                "policy_flags": option["policy_constraints"],
                "candidate_status": "ACTIVE_FIXTURE",
                "gate_a_confirmed": True,
                "selected_activity_id": option["activity_ref"]["id"],
                "selected_activity_version": option["activity_ref"]["version"],
            },
        },
    )
    filtered = _command(
        client,
        session_id=session_id,
        version=context.json()["observed_session_version"],
        key="butterfly-filter",
        route="/p1-filter",
        payload={"operation": "RUN_P1_FILTER", "user_initiated": True},
    )
    prepared = _command(
        client,
        session_id=session_id,
        version=filtered.json()["observed_session_version"],
        key="butterfly-prepare",
        route="/experience/prepare",
        payload={"operation": "PREPARE_EXPERIENCE", "user_initiated": True},
    )

    assert filtered.json()["status"] == "SUCCEEDED"
    assert prepared.json()["status"] == "SUCCEEDED"
    assert prepared.json()["payload"]["status"] == "AWAITING_ADULT_GATE_B"
    assert (
        prepared.json()["payload"]["experience_spec"]["activity_template"]["activity_ref"]
        == option["activity_ref"]
    )


def test_fake_only_image_session_completes_p1_gate_b_p4_handoff_feedback_and_gallery() -> None:
    client, vision = _client()
    session_id, version = _create_session(client)
    uploaded = client.post(
        f"/v1/sessions/{session_id}/media/image",
        headers=_headers(session_id, version, "full-upload"),
        files={"image": ("synthetic.png", _IMAGE, "image/png")},
    )
    assert uploaded.status_code == 200
    version = uploaded.json()["observed_session_version"]

    inferred = _command(
        client,
        session_id=session_id,
        version=version,
        key="full-understanding",
        route="/understanding",
        payload={"operation": "RUN_UNDERSTANDING", "user_initiated": True},
    )
    assert inferred.status_code == 200
    version = inferred.json()["observed_session_version"]

    gate_a = _command(
        client,
        session_id=session_id,
        version=version,
        key="full-gate-a",
        route="/gate-a/confirm",
        payload={
            "operation": "CONFIRM_GATE_A",
            "user_initiated": True,
            "primary_anchor_id": "subject-1",
            "confirmation": {
                "contract_name": "GateAConfirmationV1",
                "contract_version": "1.0",
                "meaning_version": 1,
                "confirmed_claim_ids": ["subject-1"],
                "correction": None,
            },
        },
    )
    assert gate_a.status_code == 200
    version = gate_a.json()["observed_session_version"]

    options = client.get(
        f"/v1/sessions/{session_id}/p1/context-options",
        params={"age_months": 60},
        headers={
            "X-Request-ID": "full-options",
            "X-Expected-Session-Version": str(version),
            "X-Actor-Ref": "demo:local",
        },
    )
    assert options.status_code == 200
    option = options.json()["payload"]["options"][0]
    context = _command(
        client,
        session_id=session_id,
        version=version,
        key="full-context",
        route="/p1-context",
        method="put",
        payload={
            "operation": "SET_P1_CONTEXT",
            "user_initiated": True,
            "context": {
                "contract_name": "P1ContextV1",
                "contract_version": "1.0",
                "session_id": session_id,
                "expected_session_version": version,
                "age_months": 60,
                "readiness_ids": option["readiness_ids"],
                "completed_activity_ids": option["prerequisite_activity_ids"],
                "available_material_option_ids": option["material_option_ids"],
                "supervision_level": option["minimum_supervision"],
                "policy_flags": option["policy_constraints"],
                "candidate_status": "ACTIVE_FIXTURE",
                "gate_a_confirmed": True,
                "selected_activity_id": option["activity_ref"]["id"],
                "selected_activity_version": option["activity_ref"]["version"],
            },
        },
    )
    assert context.status_code == 200
    version = context.json()["observed_session_version"]

    filtered = _command(
        client,
        session_id=session_id,
        version=version,
        key="full-filter",
        route="/p1-filter",
        payload={"operation": "RUN_P1_FILTER", "user_initiated": True},
    )
    assert filtered.status_code == 200
    assert filtered.json()["payload"]["filter_result"]["status"] == "VALID_CANDIDATE"
    version = filtered.json()["observed_session_version"]

    prepared = _command(
        client,
        session_id=session_id,
        version=version,
        key="full-prepare",
        route="/experience/prepare",
        payload={"operation": "PREPARE_EXPERIENCE", "user_initiated": True},
    )
    assert prepared.status_code == 200
    assert prepared.json()["payload"]["status"] == "AWAITING_ADULT_GATE_B"
    assert prepared.json()["payload"]["generation_called"] is False
    assert vision.calls == 1
    version = prepared.json()["observed_session_version"]

    approved = _command(
        client,
        session_id=session_id,
        version=version,
        key="full-gate-b",
        route="/gate-b/approve",
        payload={"operation": "APPROVE_GATE_B", "user_initiated": True, "approved": True},
    )
    assert approved.status_code == 200
    assert approved.json()["payload"]["generation_called"] is False
    assert approved.json()["payload"]["learning_media"]["fallback_type"] == "WHOLE_IMAGE_REVEAL"
    version = approved.json()["observed_session_version"]

    renderer = _command(
        client,
        session_id=session_id,
        version=version,
        key="full-renderer",
        route="/renderer/launch",
        payload={"operation": "PREPARE_RENDERER", "user_initiated": True},
    )
    assert renderer.status_code == 200
    launch = renderer.json()["payload"]["renderer_launch"]
    launch_v2 = renderer.json()["payload"]["renderer_launch_v2"]
    assert launch["assetManifest"]["providerGenerationCalled"] is False
    assert not _contains_none(launch)
    assert launch["assetManifest"]["assets"][0]["role"] == "ORIGINAL_ART"
    assert (
        launch["animationPlan"]["plan"]["planId"]
        == approved.json()["payload"]["learning_media"]["renderer_plan_id"]
    )
    assert (
        launch["animationPlan"]["experienceSpecRef"] == launch["assetManifest"]["experienceSpecRef"]
    )
    assert [motion["kind"] for motion in launch["animationPlan"]["plan"]["motions"]] == [
        "DRAW_REVEAL",
        "SCALE",
        "MOVE_TO",
        "ROTATE",
    ]
    assert launch_v2["contractName"] == "PixiRendererLaunchV2"
    assert launch_v2["animationPlan"]["tier"] == "CUTOUT_MICRO_MOTION"
    assert launch_v2["fallbackLaunch"] == {}
    assert renderer.json()["payload"]["renderer_mode"] == "PIXI_V2"
    package = client.get(
        launch_v2["packageReadEndpoint"],
        headers={"X-Rig-Package-Capability": launch_v2["packageReadCapability"]},
    )
    assert package.status_code == 200
    assert package.headers["X-Content-SHA256"] == launch_v2["packageSha256"]
    assert package.json()["originalArtPreserved"] is True
    storyboard = renderer.json()["payload"]["pixi_intro_storyboard"]
    assert storyboard["original_art_preserved"] is True
    assert storyboard["video_placeholder_only"] is True
    assert len(storyboard["beats"]) == 4
    assert renderer.json()["observed_session_version"] == version

    source_headers = {"X-Render-Source-Capability": launch["sourceReadCapability"]}
    source = client.get("/v1/renderer/source", headers=source_headers)
    assert source.status_code == 200
    assert source.headers["Cache-Control"].startswith("no-store")
    assert source.content == _IMAGE
    assert client.get("/v1/renderer/source", headers=source_headers).content == _IMAGE
    assert client.get("/v1/renderer/source", headers=source_headers).status_code == 404

    refreshed_renderer = _command(
        client,
        session_id=session_id,
        version=version,
        key="full-renderer-retry",
        route="/renderer/launch",
        payload={"operation": "PREPARE_RENDERER", "user_initiated": True},
    )
    assert refreshed_renderer.status_code == 200
    refreshed_v1 = refreshed_renderer.json()["payload"]["renderer_launch"]
    refreshed_v2 = refreshed_renderer.json()["payload"]["renderer_launch_v2"]
    assert refreshed_v1["sourceReadCapability"] != launch["sourceReadCapability"]
    assert refreshed_v2["packageReadCapability"] != launch_v2["packageReadCapability"]
    refreshed_source = client.get(
        refreshed_v1["sourceReadEndpoint"],
        headers={"X-Render-Source-Capability": refreshed_v1["sourceReadCapability"]},
    )
    refreshed_package = client.get(
        refreshed_v2["packageReadEndpoint"],
        headers={"X-Rig-Package-Capability": refreshed_v2["packageReadCapability"]},
    )
    assert refreshed_source.status_code == 200
    assert refreshed_source.content == _IMAGE
    assert refreshed_package.status_code == 200
    assert refreshed_renderer.json()["observed_session_version"] == version
    assert vision.calls == 1

    handoff = _command(
        client,
        session_id=session_id,
        version=version,
        key="full-handoff",
        route="/handoff",
        payload={"operation": "COMPLETE_HANDOFF", "user_initiated": True},
    )
    assert handoff.status_code == 200
    identity = handoff.json()["payload"]["handoff"]
    version = handoff.json()["observed_session_version"]

    recorded = _command(
        client,
        session_id=session_id,
        version=version,
        key="full-feedback",
        route="/feedback",
        payload={
            "operation": "RECORD_FEEDBACK",
            "user_initiated": True,
            "feedback": {
                "completion_status": "COMPLETED",
                "interest_score": 4,
                "independence_score": 3,
                "observation_tags": [],
            },
        },
    )
    assert recorded.status_code == 200
    assert recorded.json()["payload"]["durable"] is False
    assert recorded.json()["payload"]["feedback"]["activity_ref"] == identity["activity_ref"]
    version = recorded.json()["observed_session_version"]

    gallery = client.get(
        f"/v1/sessions/{session_id}/gallery",
        headers={
            "X-Request-ID": "full-gallery",
            "X-Expected-Session-Version": str(version),
            "Idempotency-Key": "full-gallery-key",
            "X-Actor-Ref": "demo:local",
        },
    )
    assert gallery.status_code == 200
    assert gallery.json()["payload"]["media_bytes_included"] is False
    assert gallery.json()["payload"]["durable"] is False
    assert len(gallery.json()["payload"]["entries"]) >= 5
    assert vision.calls == 1


def test_vision_runtime_failure_is_recoverable_without_exposing_exception_text() -> None:
    class _FailingVision:
        calls = 0

        def understand(self, request: VisionUnderstandingRequestV2):
            del request
            self.calls += 1
            raise RuntimeError("synthetic private provider detail")

    vision = _FailingVision()
    client, _ = _client(vision=vision)  # type: ignore[arg-type]
    session_id, version = _create_session(client)
    uploaded = client.post(
        f"/v1/sessions/{session_id}/media/image",
        headers=_headers(session_id, version, "provider-failure-image"),
        files={"image": ("synthetic.png", _IMAGE, "image/png")},
    )
    version = uploaded.json()["observed_session_version"]
    first = _command(
        client,
        session_id=session_id,
        version=version,
        key="provider-failure-first",
        route="/understanding",
        payload={"operation": "RUN_UNDERSTANDING", "user_initiated": True},
    )
    assert first.status_code == 200
    assert first.json()["status"] == "BLOCKED"
    assert first.json()["payload"]["reason_codes"] == ["VISION_REQUEST_FAILED"]
    assert first.json()["payload"]["understanding_progress"]["stage"] == "FAILED"
    assert "synthetic private provider detail" not in first.text

    second = _command(
        client,
        session_id=session_id,
        version=first.json()["observed_session_version"],
        key="provider-failure-requery",
        route="/understanding",
        payload={
            "operation": "REQUERY_UNDERSTANDING",
            "user_initiated": True,
            "prior_run_id": "request-provider-failure-first",
            "direction_revision": 1,
            "selected_direction": "con chim",
            "correction": "con chim",
        },
    )
    assert second.status_code == 200, second.text
    assert second.json()["status"] == "BLOCKED"

    confirmed = _command(
        client,
        session_id=session_id,
        version=second.json()["observed_session_version"],
        key="provider-failure-adult-subject",
        route="/gate-a/confirm",
        payload={
            "operation": "CONFIRM_GATE_A",
            "user_initiated": True,
            "primary_anchor_id": None,
            "confirmation": {
                "contract_name": "GateAConfirmationV2",
                "contract_version": "2.0",
                "meaning_version": 2,
                "confirmed_claim_ids": [],
                "adult_subject_label": "con chim",
            },
        },
    )
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["payload"]["primary_subject_origin"] == "ADULT_ENTERED"
    assert (
        confirmed.json()["payload"]["anchor_set"]["primary_anchor"]["provenance"]["source_claim_ids"]
        == []
    )
    assert vision.calls == 2
